#!/usr/bin/env python3
"""Serve the repository root for local preview and redirect / to the workbook."""
from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in {"", "/"}:
            self.send_response(302)
            self.send_header("Location", "/tax-workbook/site/index.html")
            self.end_headers()
            return
        super().do_GET()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--bind", default="0.0.0.0")
    args = parser.parse_args()
    handler = partial(Handler, directory=str(REPO_ROOT))
    server = ThreadingHTTPServer((args.bind, args.port), handler)
    print(f"Serving {REPO_ROOT} at http://{args.bind}:{args.port}/tax-workbook/site/index.html", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
