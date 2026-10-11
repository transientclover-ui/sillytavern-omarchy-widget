#!/usr/bin/env python3
"""Health fixture, never an inference implementation."""
import argparse
import http.server
import json
import time
ap = argparse.ArgumentParser()
ap.add_argument('--port', type=int, required=True)
ap.add_argument('--host')
ap.add_argument('--model')
a = ap.parse_args()
started = time.monotonic()
class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        loading = time.monotonic() - started < 4
        self.send_response(503 if loading else 200)
        self.end_headers()
        self.wfile.write(json.dumps({'status': 'loading' if loading else 'ok'}).encode())
    def log_message(self, *args):
        pass
http.server.HTTPServer(('127.0.0.1', a.port), Handler).serve_forever()
