#!/usr/bin/env python3
"""Tiny local server for the take picker: static files + POST /save -> picks.json.
Serves with HTTP Range support so the browser can seek inside clips."""
import sys as _sys
if len(_sys.argv) < 2 or _sys.argv[1] in ("-h", "--help"):
    print(__doc__); _sys.exit(0 if _sys.argv[1:2] in (["-h"], ["--help"]) else 1)
import http.server, json, os, sys, re

ROOT = os.path.abspath(sys.argv[1]); PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8765
os.chdir(ROOT)

class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
    def end_headers(self):
        self.send_header("Cache-Control", "no-store"); self.send_header("Accept-Ranges", "bytes")
        super().end_headers()
    def do_GET(self):
        rng = self.headers.get("Range")
        path = self.translate_path(self.path.split("?")[0])
        if rng and os.path.isfile(path):
            size = os.path.getsize(path)
            m = re.match(r"bytes=(\d*)-(\d*)", rng)
            a = int(m.group(1) or 0); b = int(m.group(2)) if m.group(2) else size - 1
            b = min(b, size - 1)
            self.send_response(206)
            self.send_header("Content-Type", self.guess_type(path))
            self.send_header("Content-Range", f"bytes {a}-{b}/{size}")
            self.send_header("Content-Length", str(b - a + 1)); self.end_headers()
            with open(path, "rb") as f:
                f.seek(a); self.wfile.write(f.read(b - a + 1))
            return
        return super().do_GET()
    def do_POST(self):
        if self.path != "/save":
            self.send_error(404); return
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        data = json.loads(body)
        with open(os.path.join(ROOT, "picks.json"), "w") as f: json.dump(data, f, indent=1)
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
        self.wfile.write(b'{"ok":true}')

print(f"take picker on http://localhost:{PORT}/  (root {ROOT})", flush=True)
http.server.ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
