"""Synthetic process-control tests for the recording shell; not database evidence."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

SOURCE=Path(__file__).resolve().parents[1]/'scripts/record_milestone2.sh'

class RecordingEntrypointTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SOURCE.is_file(), 'recording must have one server entrypoint, not multiline remote-shell pasting')
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        (self.root/'scripts').mkdir();shutil.copyfile(SOURCE,self.root/'scripts/record_milestone2.sh')
        raw=self.root/'data/raw/milestone2-verified-20261107';raw.mkdir(parents=True)
        for name in ['summary.json','models.json','endpoints.json']:(raw/name).write_text('{}')
        binary=self.root/'.venv/bin/python';binary.parent.mkdir(parents=True)
        fake=r"""import json,os,signal,sys,time
from pathlib import Path
p=Path(os.environ['PROBE_LOG'])
try:controlling_tty=os.tcgetpgrp(0)==os.getpgrp()
except OSError:controlling_tty=False
with p.open('a') as f:f.write(json.dumps({'args':sys.argv[1:],'stale_url':'DATABASE_URL' in os.environ,'stale_options':'PGOPTIONS' in os.environ,'controlling_tty':controlling_tty})+'\n')
if 'scripts/check_db.py' in sys.argv:
 mode=os.environ.get('CHECK_MODE')
 if mode == 'interrupt':
  signal.signal(signal.SIGINT,signal.SIG_DFL)
  os.kill(os.getpid(),signal.SIGINT)
 if mode in ('blocked','ignore-int'):
  def interrupted(signum,frame):
   p.with_name('checker-interrupted').write_text('SIGINT received')
   if mode == 'blocked':raise SystemExit(130)
  signal.signal(signal.SIGINT,interrupted)
  p.with_name('checker-pid').write_text(str(os.getpid()))
  p.with_name('checker-established').write_text('synthetic established fixture, not a database connection')
  print('Synthetic checker fixture established; blocking after setup.',flush=True)
  time.sleep(23)
 print('[ok] synthetic checker, not a real connection')
 raise SystemExit(int(os.environ.get('CHECK_STATUS','0')))
print('synthetic loader result, not real rows')
raise SystemExit(int(os.environ.get('LOAD_STATUS','0')))
"""
        binary.write_text('#!'+sys.executable+'\n'+fake);binary.chmod(0o700)
        self.log=self.root/'probe.jsonl'
        self.env={'PATH':os.defpath,'HOME':str(self.root),'PROBE_LOG':str(self.log),
                  'DATABASE_URL':'synthetic-stale-url-must-not-be-forwarded','PGOPTIONS':'synthetic-stale-options'}

    def run_entry(self,stdin='',*,process_timeout=15,**changes):
        env=dict(self.env,**changes)
        p=subprocess.run(['bash',str(self.root/'scripts/record_milestone2.sh')],
                         cwd=self.root.parent,env=env,input=stdin,capture_output=True,text=True,timeout=process_timeout)
        calls=[json.loads(x) for x in self.log.read_text().splitlines()] if self.log.exists() else []
        return p,calls

    def probe_timeout_path(self,*,shorten_checker=False):
        """Observe real timeout argv; optionally shorten ONLY this test fixture."""
        real_timeout=shutil.which('timeout',path=os.defpath)
        assert real_timeout is not None, 'existing timeout utility is required'
        private_bin=self.root/'timeout-probe';private_bin.mkdir()
        shim=private_bin/'timeout'
        shim.write_text('#!'+sys.executable+'\n'+f"""import json,os,sys
from pathlib import Path
args=sys.argv[1:]
with Path(os.environ['PROBE_LOG']).with_name('timeout.jsonl').open('a') as f:
 f.write(json.dumps(args)+'\\n')
# TEST ONLY: force-kill coverage uses 1s + 0.3s, never production overrides.
if {shorten_checker!r} and 'scripts/check_db.py' in args:
 args=['--kill-after=0.3s' if x=='--kill-after=5s' else '1s' if x=='20s' else x for x in args]
os.execv({real_timeout!r},[{real_timeout!r},*args])
""")
        shim.chmod(0o700)
        return str(private_bin)+os.pathsep+os.defpath

    def test_blocked_checker_uses_production_20_second_wall_bound(self):
        """Real 20-second deadline, not a shortened test-only timeout."""
        started=time.monotonic()
        p,calls=self.run_entry('\n',process_timeout=32,CHECK_MODE='blocked',
                               CHECK_TIMEOUT_SECONDS='0.01',CHECKER_TIMEOUT_SECONDS='99')
        elapsed=time.monotonic()-started
        output=p.stdout+p.stderr
        self.assertTrue((self.root/'checker-established').is_file(),output)
        self.assertIn('fixture established; blocking after setup',output)
        self.assertEqual(p.returncode,124,output)
        self.assertTrue((self.root/'checker-interrupted').is_file(),output)
        self.assertGreaterEqual(elapsed,19)
        self.assertLess(elapsed,25)
        self.assertEqual(len(calls),1,output)
        self.assertIn('scripts/check_db.py',calls[0]['args'])
        self.assertIn('STOP: connection check failed (exit 124). No replay started.',output)
        for forbidden in ['READY FOR RECORDING','Starting the actual loader',
                          'synthetic loader result','Replay finished successfully','Loader exit code:']:
            self.assertNotIn(forbidden,output)

    def test_missing_timeout_stops_before_checker_or_ready(self):
        private_bin=self.root/'without-timeout';private_bin.mkdir()
        for name in ['bash','dirname']:
            executable=shutil.which(name,path=os.defpath)
            assert executable is not None, name+' is required by the test fixture'
            (private_bin/name).symlink_to(executable)
        for stdin in ['\n','']:
            with self.subTest(stdin=repr(stdin)):
                p,calls=self.run_entry(stdin,PATH=str(private_bin))
                output=p.stdout+p.stderr
                self.assertEqual(p.returncode,2,output)
                self.assertEqual(calls,[])
                self.assertIn('STOP: the server timeout command is unavailable. No replay started.',output)
                self.assertNotIn('checking the real database connection',output)
                self.assertNotIn('READY FOR RECORDING',output)
                self.assertNotIn('Replay finished successfully',output)

    def test_fixed_checker_deadlines_and_unchanged_loader_deadlines(self):
        p,calls=self.run_entry('\n',PATH=self.probe_timeout_path(),
                               CHECK_TIMEOUT_SECONDS='0.01',CHECKER_TIMEOUT_SECONDS='99')
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        self.assertEqual(len(calls),2)
        deadlines=[json.loads(x) for x in (self.root/'timeout.jsonl').read_text().splitlines()]
        self.assertEqual(deadlines,[
            ['--foreground','--signal=INT','--kill-after=5s','20s',
             '.venv/bin/python','-I','-B','scripts/check_db.py'],
            ['--foreground','--signal=INT','--kill-after=10s','120s',
             '.venv/bin/python','-I','-B','ingest/load.py','--run-dir',
             'data/raw/milestone2-verified-20261107']])

    def test_only_shortened_deadlines_force_kill_uncooperative_checker(self):
        """TEST ONLY: 1s wall + 0.3s grace exercise real timeout SIGKILL."""
        started=time.monotonic()
        p,calls=self.run_entry('\n',PATH=self.probe_timeout_path(shorten_checker=True),
                               process_timeout=8,CHECK_MODE='ignore-int')
        elapsed=time.monotonic()-started
        output=p.stdout+p.stderr
        self.assertTrue((self.root/'checker-established').is_file(),output)
        self.assertTrue((self.root/'checker-interrupted').is_file(),output)
        self.assertEqual(p.returncode,137,output)
        self.assertGreaterEqual(elapsed,1.2)
        self.assertLess(elapsed,6)
        self.assertEqual(len(calls),1,output)
        pid=int((self.root/'checker-pid').read_text())
        with self.assertRaises(ProcessLookupError):os.kill(pid,0)
        deadlines=[json.loads(x) for x in (self.root/'timeout.jsonl').read_text().splitlines()]
        self.assertEqual(deadlines,[['--foreground','--signal=INT','--kill-after=5s','20s',
                                    '.venv/bin/python','-I','-B','scripts/check_db.py']])
        self.assertIn('STOP: connection check failed (exit 137). No replay started.',output)
        for forbidden in ['READY FOR RECORDING','Starting the actual loader',
                          'synthetic loader result','Replay finished successfully','Loader exit code:']:
            self.assertNotIn(forbidden,output)

    def test_interrupted_checker_preserves_status_and_never_starts_replay(self):
        p,calls=self.run_entry('\n',CHECK_MODE='interrupt')
        output=p.stdout+p.stderr
        self.assertEqual(p.returncode,130,output)
        self.assertEqual(len(calls),1)
        self.assertIn('STOP: connection check failed (exit 130). No replay started.',output)
        self.assertNotIn('READY FOR RECORDING',output)
        self.assertNotIn('Replay finished successfully',output)

    def test_eof_cannot_start_replay_and_stale_environment_is_not_forwarded(self):
        p,calls=self.run_entry()
        self.assertEqual(p.returncode,130)
        self.assertEqual(len(calls),1)
        self.assertIn('scripts/check_db.py',calls[0]['args'])
        self.assertFalse(calls[0]['stale_url'])
        self.assertFalse(calls[0]['stale_options'])
        self.assertIn('no replay started',p.stdout.lower())


    def test_enter_runs_actual_loader_once_and_prints_its_real_exit_status(self):
        p,calls=self.run_entry('\n')
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(len(calls),2, 'Enter must execute loader once after checker, not a simulated success')
        self.assertIn('ingest/load.py',calls[1]['args'])
        self.assertIn('--run-dir',calls[1]['args'])
        self.assertIn('data/raw/milestone2-verified-20261107',calls[1]['args'])
        self.assertIn('Loader exit code: 0',p.stdout)
        self.assertIn('synthetic loader result',p.stdout)


    def test_failed_loader_is_nonzero_and_explicit_stop_not_success(self):
        p,calls=self.run_entry('\n',LOAD_STATUS='4')
        self.assertEqual(p.returncode,4)
        self.assertEqual(len(calls),2)
        self.assertIn('Loader exit code: 4',p.stdout)
        self.assertIn('STOP:',p.stdout+p.stderr)
        self.assertNotIn('Replay finished successfully',p.stdout+p.stderr)

    def test_failed_checker_never_starts_replay_even_with_enter(self):
        p,calls=self.run_entry('\n',CHECK_STATUS='9')
        self.assertEqual(p.returncode,9)
        self.assertEqual(len(calls),1)
        self.assertNotIn('READY FOR RECORDING',p.stdout)
        self.assertIn('STOP: connection check failed (exit 9). No replay started.',p.stdout+p.stderr)
        self.assertNotIn('Replay finished successfully',p.stdout+p.stderr)

    def test_nonempty_answer_cancels_without_replay(self):
        p,calls=self.run_entry('q\n')
        self.assertEqual(p.returncode,130)
        self.assertEqual(len(calls),1)


    @unittest.skipUnless(os.name == 'posix', 'server terminal requires POSIX PTY')
    def test_real_terminal_waits_before_replay_and_keeps_result_visible_afterward(self):
        import fcntl
        import pty
        import select
        import termios
        master,slave=pty.openpty()
        process=subprocess.Popen(['bash',str(self.root/'scripts/record_milestone2.sh')],
            cwd=self.root.parent,env=self.env,stdin=slave,stdout=slave,stderr=slave,start_new_session=True,
            preexec_fn=lambda:fcntl.ioctl(0,termios.TIOCSCTTY,0))
        os.close(slave)
        output=b''
        def until(marker):
            nonlocal output
            deadline=time.monotonic()+5
            while marker not in output and time.monotonic()<deadline:
                if select.select([master],[],[],0.1)[0]:
                    try:chunk=os.read(master,65536)
                    except OSError:break
                    if not chunk:break
                    output+=chunk
            self.assertIn(marker,output,'recording terminal did not reach the expected live state')
        try:
            until(b'READY FOR RECORDING')
            self.assertIsNone(process.poll())
            self.assertEqual(len(self.log.read_text().splitlines()),1)
            self.assertTrue(json.loads(self.log.read_text().splitlines()[0])['controlling_tty'])
            os.write(master,b'\n')
            until(b'Keep this result visible')
            time.sleep(0.05)
            self.assertIsNone(process.poll(),'SSH must not close before the student shows the result')
            self.assertEqual(len(self.log.read_text().splitlines()),2)
            self.assertTrue(json.loads(self.log.read_text().splitlines()[1])['controlling_tty'])
            os.write(master,b'\n')
            self.assertEqual(process.wait(timeout=5),0)
        finally:
            if process.poll() is None:process.kill();process.wait(timeout=5)
            os.close(master)
