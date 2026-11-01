"""Local recording workspace: show real source files and run the real importer.

Python 3.12 standard library only. Binds to loopback; never starts a recording,
uploads work, reads a vault, or changes student review/baseline evidence.
"""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
LOCK = threading.Lock()
STATE = {"running": False, "output": "", "summary": None, "run_directory": None,
         "exit_code": None, "performed_by": "Not recorded; starting a demo does not certify who ran it"}


def source_sections():
    text = (ROOT / "ingest/fetch.py").read_text(encoding="utf-8")
    lines = text.splitlines()
    wanted = {"load_key": "Optional authentication", "retry_delay": "429 and retry waits",
              "get_json": "Pacing, requests, and failures", "collect": "Pagination and relationships"}
    sections = []
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.FunctionDef) and node.name in wanted:
            # Include the real implementation, with actual source line numbers.
            sections.append({"name": node.name, "title": wanted[node.name], "line": node.lineno,
                             "code": "\n".join(f"{i + 1:3}  {lines[i]}" for i in range(node.lineno - 1, node.end_lineno))})
    return sorted(sections, key=lambda row: row["line"])


def record_from_run(folder):
    """Read one untouched source object from an original raw response page."""
    summary = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
    for page in sorted((folder / "catalog").glob("page-*.json")):
        payload = json.loads(page.read_text(encoding="utf-8"))
        row = next((item for item in payload.get("data", []) if item.get("id") == "openai/gpt-4.1"), None)
        if row is None:
            continue
        endpoints = json.loads((folder / "endpoints.json").read_text(encoding="utf-8"))["data"]
        return {"raw_file": page.relative_to(ROOT).as_posix(), "retrieved_at": summary["finished_at"],
                "record": row, "related_endpoints": [item for item in endpoints if item.get("model_id") == row["id"]],
                "summary": summary}
    raise ValueError("The selected run has no GPT-4.1 example; inspect its raw files directly")


def evidence():
    with LOCK:
        folder_name = STATE["run_directory"] if STATE["summary"] else None
    folder = ROOT / folder_name if folder_name else ROOT / "data/raw/milestone1-clean-2026-11-01"
    return {"source_sections": source_sections(), "example": record_from_run(folder),
            "example_origin": "Current recording-room run" if folder_name else "Saved assistant verification run, November 1",
            "dictionary": (ROOT / "docs/data_dictionary.md").read_text(encoding="utf-8"),
            "review_log": (ROOT / "docs/ai_review_log.md").read_text(encoding="utf-8")}


def run_importer():
    stamp = datetime.now(timezone.utc).strftime("recording-%Y%m%dT%H%M%S%fZ")
    folder = ROOT / "data/raw" / stamp
    relative = folder.relative_to(ROOT).as_posix()
    with LOCK:
        STATE.update(run_directory=relative, summary=None, exit_code=None,
                     output=f"$ python ingest/fetch.py --output-dir {relative}\n\nNew output folder. Retrieving live catalog metadata...\n")
    try:
        result = subprocess.run([sys.executable, "-u", "ingest/fetch.py", "--output-dir", relative],
                                cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
        with LOCK:
            STATE["output"] += result.stdout + result.stderr
            STATE["exit_code"] = result.returncode
            if (folder / "summary.json").is_file():
                STATE["summary"] = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        with LOCK:
            STATE.update(exit_code=1, output="Local demo could not finish. No successful run is claimed.\n")
    finally:
        with LOCK:
            STATE["running"] = False


HTML = r'''<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Milestone 1 · Recording workspace</title>
<style>
:root{font-family:Segoe UI,Arial,sans-serif;color:#182a34;background:#f5f4ef;font-size:18px}*{box-sizing:border-box}body{margin:0}header{background:#173e40;color:#fff;padding:23px 34px;display:flex;justify-content:space-between;align-items:center}h1{font-size:25px;letter-spacing:-.5px;margin:4px 0}header small{color:#c2d7cf;font-size:13px;letter-spacing:1.2px;text-transform:uppercase}.pill{font-size:13px;border:1px solid #8ba8a0;padding:7px 12px;border-radius:24px}nav{display:flex;gap:6px;padding:16px 28px;border-bottom:1px solid #d8ddd5;background:#fff;flex-wrap:wrap}button{font:inherit;cursor:pointer;border:1px solid #b5c4bc;border-radius:7px;padding:10px 15px;background:#fff;color:#173e40}nav button{font-size:15px;border-color:transparent}nav button.active,.primary{background:#173e40;color:#fff}button:disabled{opacity:.5;cursor:wait}main{max-width:1240px;margin:28px auto;padding:0 32px 30px}h2{font-size:30px;letter-spacing:-.7px;margin:8px 0 16px}h3{font-size:19px}p,li{line-height:1.6}p{max-width:900px}.muted{color:#59706d;font-size:15px}.grid{display:grid;grid-template-columns:2fr 1fr;gap:22px}.card{background:white;border:1px solid #dce1d8;border-radius:12px;padding:24px;margin:16px 0}.note{border-left:4px solid #bb8a40;padding:12px 18px;background:#fff9ea;font-size:15px}.steps{counter-reset:steps;list-style:none;padding:0}.steps li{padding:16px 0;border-bottom:1px solid #e1e5de}.time{display:inline-block;color:#25726b;font-size:14px;font-weight:700;min-width:100px}pre{font:15px/1.55 Consolas,monospace;white-space:pre-wrap;overflow-wrap:anywhere;background:#122a33;color:#edf4ed;border-radius:9px;padding:22px;max-height:61vh;overflow:auto}code{font-family:Consolas,monospace;font-size:.9em}.stats{display:flex;gap:12px;flex-wrap:wrap}.stat{background:white;border:1px solid #dae1d6;min-width:160px;border-radius:10px;padding:18px}.stat strong{font-size:30px;display:block;color:#173e40}.stat span{font-size:13px;color:#536a66}.tag{color:#267266;font-size:14px;font-weight:600}.links a{display:inline-block;margin:8px 18px 6px 0;color:#155e67}.source-buttons{display:flex;gap:8px;flex-wrap:wrap}.source-buttons button{font-size:14px}.status{min-height:28px;font-weight:600}.checklist label{display:block;padding:8px 0}.checklist input{margin-right:10px}.hidden{display:none!important}table{width:100%;border-collapse:collapse;font-size:14px;background:#fff}td,th{padding:10px;border-bottom:1px solid #dce3d8;text-align:left;vertical-align:top}#clock{font-variant-numeric:tabular-nums}footer{font-size:12px;color:#687b73;margin-top:26px}@media(max-width:800px){.grid{grid-template-columns:1fr}main{padding:0 18px}header{padding:18px}nav{padding:10px}pre{font-size:13px}.stat{min-width:130px}}
</style>
<header><div><small>BSAD 6153 · David Michaud</small><h1>OpenRouter catalog · Milestone 1</h1></div><span class="pill">Local demo • no paid model calls</span></header>
<nav id="nav"><button data-tab="start" class="active">1 · Before recording</button><button data-tab="run">2 · Clean run</button><button data-tab="code">3 · Code</button><button data-tab="raw">4 · Raw record</button><button data-tab="dictionary">5 · Dictionary</button><button data-tab="finish">Turn-in checklist</button></nav>
<main>
<section id="start"><div class="tag">3–5 minute screencast · aim for about 4 minutes</div><h2>Your recording is staged.</h2>
<div class="grid"><div><p>Record this browser window with your microphone. This workspace shows the actual importer source, runs it into a fresh folder, and opens a real source record.</p>
<ol class="steps"><li><span class="time">0:00–0:25</span> Explain the daily model-choice decision and why catalog metadata helps.</li><li><span class="time">0:25–1:20</span> Open <b>Clean run</b> and start a new run on camera. Explain the output counts after it finishes.</li><li><span class="time">1:20–2:45</span> Open <b>Code</b>. Explain the optional key, next-page links, request spacing, and 429 retry logic.</li><li><span class="time">2:45–3:45</span> Open <b>Raw record</b>. Describe one catalog entry and its related provider offering. Explain a price and a missing/conflicting field.</li><li><span class="time">3:45–4:15</span> Briefly show <b>Dictionary</b> and state a real limitation.</li></ol>
<button class="primary" onclick="show('code')">Read the code first</button> <button onclick="timer()" id="timerButton">Start rehearsal timer</button> <span id="clock">00:00</span>
</div><aside><div class="card"><h3>Before pressing Record</h3><ul><li>Read the source sections and explain them in your own words.</li><li>Choose this window, turn the microphone on, and check its input.</li><li>Keep passwords, your vault, and unrelated windows outside the capture.</li><li>Camera is optional unless your instructor separately requires it.</li></ul><div class="links"><a href="https://www.loom.com/" target="_blank" rel="noreferrer">Open Loom</a><a href="https://newmanu.instructure.com/courses/14628/assignments/241963" target="_blank" rel="noreferrer">Canvas instructions</a></div></div><div class="note">This page does not record or upload anything. Its outline is an aid; your narration should reflect your own understanding.</div></aside></div></section>
<section id="run" class="hidden"><div class="tag">Demonstrate a clean start</div><h2>Run the real importer.</h2><p>Each click uses a new timestamped folder under <code>data/raw/</code>. Earlier evidence is preserved. Start this after your recording begins.</p><button id="runButton" class="primary" onclick="runDemo()">Run a fresh live collection</button><p id="runStatus" class="status">Ready. No recording-room run has started.</p><div id="runStats" class="stats"></div><pre id="runOutput">The command and real importer output will appear here.</pre><p class="muted">The run may take a minute. Explain the project while it works. Counts can change as OpenRouter changes its catalog. An incomplete run is shown as incomplete.</p></section>
<section id="code" class="hidden"><div class="tag">Actual source · ingest/fetch.py</div><h2>Explain how access works.</h2><div class="source-buttons" id="sourceButtons"></div><div class="card"><h3 id="codeTitle"></h3><p id="codeCue"></p></div><pre id="sourceCode"></pre><div class="links"><a target="_blank" rel="noreferrer" href="https://openrouter.ai/docs/api_reference/authentication">Authentication docs</a><a target="_blank" rel="noreferrer" href="https://openrouter.ai/docs/api/api-reference/models/list-all-models-and-their-properties">Catalog / pagination docs</a><a target="_blank" rel="noreferrer" href="https://openrouter.ai/docs/api_reference/limits">429 / limits docs</a></div><p class="muted">These are excerpts read directly from the current source file, with its real line numbers. Student review is not automatically marked complete.</p></section>
<section id="raw" class="hidden"><div class="tag">Real source data · unchanged object</div><h2>What does one record mean?</h2><p id="rawProvenance" class="muted"></p><div class="stats" id="rawStats"></div><div class="card"><p>One model record describes an OpenRouter catalog entry. Its <code>id</code> is the request identity; <code>canonical_slug</code> can identify a version. Related provider offerings join their <code>model_id</code> to this <code>id</code>.</p><p>Explain the price units and choose a quirk you understand: a null request limit, an alias, or different advertised endpoint limits. Source metadata does not measure coding quality.</p></div><button onclick="rawView(false)">Original model object</button> <button onclick="rawView(true)">Related provider objects</button><pre id="rawCode"></pre></section>
<section id="dictionary" class="hidden"><div class="tag">docs/data_dictionary.md</div><h2>Meanings, relationships, and limits.</h2><div class="card"><p>The dictionary covers 20 important fields, meanings and null handling, identity and joins, update behavior, observed quirks, and data-use ethics. The source terms and public-display question remain documented for review.</p></div><div id="dictionaryBody"></div></section>
<section id="finish" class="hidden"><div class="tag">Before actual turn-in</div><h2>Recording prep is complete. Personal evidence is still required.</h2><div class="card checklist"><label><input type="checkbox">I reviewed the code, documentation, proposal, and dictionary.</label><label><input type="checkbox">I supplied at least five genuine baseline entries and the reflections.</label><label><input type="checkbox">I recorded my own Read / Verify / Decide evidence.</label><label><input type="checkbox">The API approval and delivery location are confirmed.</label><label><input type="checkbox">I recorded 3–5 minutes, checked playback/audio, and saved the screencast link.</label><label><input type="checkbox">I reviewed the final PR and authorized turn-in.</label></div><p>The saved baseline currently has one reconstructed entry. This tool does not create entries or claim student actions. Checkboxes here are temporary reminders, not a completed submission log.</p><p>Assignment 1.4 is separate and requires your own written case brief and replies. It has no screencast requirement.</p><details><summary>Current AI review log</summary><pre id="reviewLog"></pre></details></section>
<footer>Local recording aid. No screen capture, credential display, submissions, or student sign-offs occur automatically.</footer></main>
<script>
let data, active='start', clockStart=null, pollBusy=false;
const cues={load_key:'Find where the optional key comes from. Documented authentication uses a bearer header; the tested public catalog calls succeeded without a key. Do not show a real key.',retry_delay:'Explain Retry-After when supplied, otherwise 2/4/8/16-second backoff. The script stops if the server asks for more than its wait budget, instead of retrying early.',get_json:'Point to the one-second spacing, the Authorization header, the 30-second timeout, transient-error retries, and original raw-response save. Real live runs did not encounter a 429; error cases were tested offline.',collect:'Point to limit/offset with output_modalities=all, returned links.next, repeated-page checks, unique model IDs, related endpoint lookups, and the explicit completeness summary.'};
function show(name){active=name;document.querySelectorAll('main>section').forEach(s=>s.classList.toggle('hidden',s.id!==name));document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('active',b.dataset.tab===name));window.scrollTo(0,0)}
document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>show(b.dataset.tab));
function stat(parent,value,label){const d=document.createElement('div');d.className='stat';const v=document.createElement('strong'),l=document.createElement('span');v.textContent=value;l.textContent=label;d.append(v,l);parent.append(d)}
function stats(parent,summary){parent.replaceChildren();stat(parent,summary.unique_catalog_ids,'distinct catalog IDs');stat(parent,summary.unique_canonical_slugs,'canonical identities');stat(parent,summary.related_endpoints,'related endpoints');stat(parent,summary.catalog_pages,'catalog pages')}
function section(index){const s=data.source_sections[index];document.getElementById('codeTitle').textContent=s.title+' · line '+s.line;document.getElementById('codeCue').textContent=cues[s.name];document.getElementById('sourceCode').textContent=s.code}
function rawView(related){document.getElementById('rawCode').textContent=JSON.stringify(related?data.example.related_endpoints:data.example.record,null,2)}
function markdown(text){const box=document.getElementById('dictionaryBody');box.replaceChildren();let table=null;for(const line of text.split('\n')){if(line.startsWith('|')){if(/^\|[-| ]+\|$/.test(line))continue;if(!table){table=document.createElement('table');box.append(table)}const tr=document.createElement('tr');for(const cell of line.split('|').slice(1,-1)){const td=document.createElement('td');td.textContent=cell.trim().replaceAll('`','');tr.append(td)}table.append(tr)}else{table=null;if(!line.trim())continue;const e=document.createElement(line.startsWith('## ')?'h3':'p');e.textContent=line.replace(/^#+ /,'').replaceAll('`','');box.append(e)}}}
async function refreshEvidence(){const response=await fetch('/api/evidence');if(!response.ok)throw Error('Evidence not available');data=await response.json();const buttons=document.getElementById('sourceButtons');buttons.replaceChildren();data.source_sections.forEach((s,i)=>{const b=document.createElement('button');b.textContent=s.title;b.onclick=()=>section(i);buttons.append(b)});section(0);rawView(false);stats(document.getElementById('rawStats'),data.example.summary);document.getElementById('rawProvenance').textContent=data.example_origin+' · '+data.example.raw_file+' · '+data.example.retrieved_at;markdown(data.dictionary);document.getElementById('reviewLog').textContent=data.review_log}
async function runDemo(){const b=document.getElementById('runButton');b.disabled=true;try{const r=await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});if(!r.ok)throw Error('Could not start a new run');await poll()}catch(e){document.getElementById('runStatus').textContent=e.message;b.disabled=false}}
let previousFinished=null;
async function poll(){if(pollBusy)return;pollBusy=true;try{const r=await fetch('/api/status');const s=await r.json();document.getElementById('runButton').disabled=s.running;document.getElementById('runOutput').textContent=s.output||'The command and real importer output will appear here.';document.getElementById('runStatus').textContent=s.running?'Collecting live data…':s.exit_code===null?'Ready. No recording-room run has started.':s.summary?.complete?'Complete — fresh live output saved.':'Run incomplete — inspect the actual output below.';if(s.summary){stats(document.getElementById('runStats'),s.summary);if(s.summary.finished_at!==previousFinished){previousFinished=s.summary.finished_at;await refreshEvidence()}}}catch(e){document.getElementById('runStatus').textContent='Local workspace disconnected. Reopen the launcher.'}finally{pollBusy=false}}
function timer(){clockStart=clockStart?null:Date.now();document.getElementById('timerButton').textContent=clockStart?'Stop rehearsal timer':'Start rehearsal timer'}
setInterval(()=>{if(clockStart){const s=Math.floor((Date.now()-clockStart)/1000);document.getElementById('clock').textContent=String(Math.floor(s/60)).padStart(2,'0')+':'+String(s%60).padStart(2,'0')}},500);
refreshEvidence().catch(e=>document.getElementById('rawProvenance').textContent=e.message);poll();setInterval(poll,1200);
</script></html>'''


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send(self, status, body, content_type="application/json; charset=utf-8"):
        body = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def valid_host(self):
        return self.headers.get("Host") == f"127.0.0.1:{self.server.server_port}"

    def do_GET(self):
        if not self.valid_host():
            return self.send(403, '{"error":"Local access only"}')
        if self.path == "/":
            return self.send(200, HTML, "text/html; charset=utf-8")
        if self.path == "/api/status":
            with LOCK:
                return self.send(200, json.dumps(STATE))
        if self.path == "/api/evidence":
            try:
                return self.send(200, json.dumps(evidence()))
            except (OSError, ValueError):
                return self.send(500, '{"error":"Saved evidence could not be loaded"}')
        return self.send(404, '{"error":"Not found"}')

    def do_POST(self):
        origin = f"http://127.0.0.1:{self.server.server_port}"
        if (not self.valid_host() or self.headers.get("Origin") != origin
                or self.headers.get("Content-Type") != "application/json"
                or self.headers.get("Content-Length") != "2"):
            return self.send(403, '{"error":"Only this local recording page may start a run"}')
        if self.path != "/api/run" or self.rfile.read(2) != b"{}":
            return self.send(404, '{"error":"Not found"}')
        with LOCK:
            if STATE["running"]:
                return self.send(409, '{"error":"A run is already active"}')
            STATE["running"] = True
        threading.Thread(target=run_importer, daemon=True).start()
        return self.send(202, '{"started":true}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--port", type=int, default=8767)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        value = evidence()
        print(json.dumps({"code_sections": len(value["source_sections"]),
                          "raw_model_id": value["example"]["record"]["id"],
                          "saved_run_complete": value["example"]["summary"]["complete"]}))
        return
    try:
        server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    except OSError:
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    url = f"http://127.0.0.1:{server.server_port}/"
    info = ROOT / "data/raw/recording-workspace.json"
    info.parent.mkdir(parents=True, exist_ok=True)
    info.write_text(json.dumps({"url": url, "pid": os.getpid()}, indent=2), encoding="utf-8")
    print("Recording workspace:", url, flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
