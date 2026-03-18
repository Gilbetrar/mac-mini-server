#!/usr/bin/env python3
"""
Lightweight deploy webhook for Mac Mini services.

Receives a tarball via POST, validates a bearer token, and extracts
the contents to a target directory. Used by GitHub Actions to deploy
built artifacts after CI passes.

Usage:
    DEPLOY_SECRET=<token> python3 deploy-webhook.py

Environment:
    DEPLOY_SECRET  - Required. Bearer token for authentication.
    DEPLOY_PORT    - Optional. Port to listen on (default: 9001).
"""

import http.server
import io
import os
import shutil
import sys
import tarfile
import time

DEPLOY_DIR = os.path.expanduser("~/services/anki-renderer/dist")
DEPLOY_SECRET = os.environ.get("DEPLOY_SECRET", "")
PORT = int(os.environ.get("DEPLOY_PORT", "9001"))
MAX_PAYLOAD = 50 * 1024 * 1024  # 50MB limit


def safe_extract(tar, dest):
    """Extract tarball with path traversal protection."""
    abs_dest = os.path.abspath(dest)
    for member in tar.getmembers():
        member_path = os.path.abspath(os.path.join(dest, member.name))
        if not member_path.startswith(abs_dest + os.sep) and member_path != abs_dest:
            raise ValueError(f"Path traversal detected: {member.name}")
    tar.extractall(dest)


class DeployHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path not in ("/deploy", "/_deploy"):
            self.send_response(404)
            self.end_headers()
            return

        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Bearer ") or auth[7:] != DEPLOY_SECRET:
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b"Forbidden")
            return

        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > MAX_PAYLOAD:
            self.send_response(413)
            self.end_headers()
            self.wfile.write(b"Payload too large")
            return

        body = self.rfile.read(content_length)

        try:
            tmp_dir = DEPLOY_DIR + ".tmp"
            old_dir = DEPLOY_DIR + ".old"

            # Clean up any leftover temp dirs
            for d in (tmp_dir, old_dir):
                if os.path.exists(d):
                    shutil.rmtree(d)

            os.makedirs(tmp_dir)

            # Extract tarball to temp directory
            with tarfile.open(fileobj=io.BytesIO(body), mode="r:gz") as tar:
                safe_extract(tar, tmp_dir)

            # Atomic-ish swap: current → old, tmp → current, delete old
            if os.path.exists(DEPLOY_DIR):
                os.rename(DEPLOY_DIR, old_dir)
            os.rename(tmp_dir, DEPLOY_DIR)
            if os.path.exists(old_dir):
                shutil.rmtree(old_dir)

            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] Deploy successful ({content_length} bytes)", flush=True)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Deployed successfully")

        except Exception as e:
            # Restore from old if swap failed
            if not os.path.exists(DEPLOY_DIR) and os.path.exists(old_dir):
                os.rename(old_dir, DEPLOY_DIR)
            for d in (tmp_dir, old_dir):
                if os.path.exists(d):
                    shutil.rmtree(d)

            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] Deploy failed: {e}", flush=True)
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Deploy failed: {e}".encode())

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {args[0]}", flush=True)


if __name__ == "__main__":
    if not DEPLOY_SECRET:
        print("ERROR: DEPLOY_SECRET environment variable required", file=sys.stderr)
        sys.exit(1)

    server = http.server.HTTPServer(("127.0.0.1", PORT), DeployHandler)
    print(f"Deploy webhook listening on 127.0.0.1:{PORT}", flush=True)
    server.serve_forever()
