"""Loopback-only HTTP fixture. All payloads and credentials are synthetic."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
from urllib.parse import parse_qs, urlsplit, urlencode
from fixtures import snapshot

class FixtureServer:
    def __init__(self,statuses=None,unauthorized=False):
        self.data=snapshot(); self.statuses=list(statuses or []); self.unauthorized=unauthorized
        self.requests=[]
    def __enter__(self):
        fixture=self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args): pass
            def do_GET(self):
                parts=urlsplit(self.path)
                fixture.requests.append(dict(path=parts.path,query=parse_qs(parts.query)))
                code=401 if fixture.unauthorized else (fixture.statuses.pop(0) if fixture.statuses and parts.path=='/api/v1/models' else 200)
                if code!=200:
                    self.send_response(code);self.send_header('Retry-After','0');self.end_headers()
                    self.wfile.write(b'{"error":"SYNTHETIC-KEY-MUST-NOT-LOG"}')
                    return
                if parts.path=='/api/v1/models':
                    query=parse_qs(parts.query);offset=int(query['offset'][0]);limit=int(query['limit'][0])
                    models=fixture.data['models'];next_offset=offset+limit
                    next_url='/api/v1/models?'+urlencode(dict(output_modalities='all',limit=limit,offset=next_offset)) if next_offset<len(models) else None
                    payload=dict(data=models[offset:next_offset],total_count=len(models),links={'next':next_url})
                else:
                    mid='/'.join(parts.path.split('/')[4:6])
                    payload=dict(data=dict(endpoints=[r for r in fixture.data['endpoints'] if r['model_id']==mid]))
                self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers()
                self.wfile.write(json.dumps(payload).encode())
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.url='http://127.0.0.1:'+str(self.server.server_port)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        return self
    def __exit__(self,*args):
        self.server.shutdown();self.server.server_close();self.thread.join()
