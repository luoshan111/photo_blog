"""Serve only generated output; source files and unpublished drafts stay inaccessible."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import argparse
from build import Builder

parser=argparse.ArgumentParser();parser.add_argument('--preview',action='store_true');parser.add_argument('--port',type=int,default=4173);args=parser.parse_args()
builder=Builder(args.preview);builder.build();output=builder.out
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw): super().__init__(*a,directory=str(output),**kw)
    def end_headers(self):
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        super().end_headers()
    def send_error(self,code,message=None,explain=None):
        if code==404:
            data=(output/'404.html').read_bytes();self.send_response(404);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
        else: super().send_error(code,message,explain)
print(f'Listening on http://127.0.0.1:{args.port}/'+(' (draft preview)' if args.preview else ''))
ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
