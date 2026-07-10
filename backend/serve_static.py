"""Offline static server for the workbench. Serves frontend/ AND answers
GET /api/health with {"ok":true,"mode":"offline"} so the single frontend can
detect its mode and disable live-only controls without a 404 in the console.
No live API here — that is backend/api/server.py (./run.sh api).
"""

from __future__ import annotations

import json
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from backend import config


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.split("?")[0] == "/api/health":
            body = json.dumps({"ok": True, "mode": "offline"}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        return super().do_GET()

    def log_message(self, *args):
        pass  # quiet


def main(port=8791):
    directory = str(config.REPO_ROOT / "frontend")
    handler = partial(Handler, directory=directory)
    httpd = ThreadingHTTPServer(("127.0.0.1", port), handler)
    print(f"offline workbench at http://127.0.0.1:{port}/index.html (Ctrl-C to stop)")
    httpd.serve_forever()


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 8791)
