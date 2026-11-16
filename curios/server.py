from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from . import providers, network

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WEB_ROOT = PROJECT_ROOT / "web"
MAX_BODY = 128 * 1024


class CURIOSServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class Handler(BaseHTTPRequestHandler):
    server_version = "CURIOS/0.1"

    def log_message(self, fmt: str, *args) -> None:
        # Keep terminal output quiet; do not log chat contents or credentials.
        return

    def _send(self, status: int, payload: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; connect-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:")
        self.end_headers()
        self.wfile.write(payload)

    def _json(self, status: int, data: dict) -> None:
        self._send(status, json.dumps(data).encode("utf-8"), "application/json; charset=utf-8")

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_BODY:
            raise ValueError("Invalid request size.")
        raw = self.rfile.read(length)
        data = json.loads(raw.decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Expected a JSON object.")
        return data

    def _same_origin(self) -> bool:
        host = self.headers.get("Host", "")
        origin = self.headers.get("Origin", "")

        return (
            host == "127.0.0.1:8765"
            and origin == "http://127.0.0.1:8765"
        )

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/network":
            self._json(200, {"online": network.is_online()})
            return
        if path == "/api/providers":
            self._json(200, {"providers": providers.list_providers()})
            return
        if path == "/api/health":
            self._json(200, {"status": "running", "name": "CURIOS"})
            return
        file_map = {
            "/": ("index.html", "text/html; charset=utf-8"),
            "/app.css": ("app.css", "text/css; charset=utf-8"),
            "/app.js": ("app.js", "text/javascript; charset=utf-8"),
        }
        if path not in file_map:
            self._json(404, {"error": "Not found"})
            return
        filename, content_type = file_map[path]
        try:
            content = (WEB_ROOT / filename).read_bytes()
            self._send(200, content, content_type)
        except OSError:
            self._json(500, {"error": "Interface file unavailable."})

    def do_POST(self) -> None:
        if not self._same_origin():
            self._json(403, {"error": "Cross-origin request blocked."})
            return
        path = urlparse(self.path).path
        try:
            data = self._read_json()
            if path == "/api/network":
                online = data.get("online")
                if type(online) is not bool:
                    raise ValueError("Connection state must be true or false.")
                network.set_online(online)
                self._json(200, {"online": network.is_online()})
            elif path == "/api/providers":
                providers.save_provider(data)
                self._json(200, {"ok": True})
            elif path == "/api/providers/remove":
                providers.remove_provider(str(data.get("id", "")))
                self._json(200, {"ok": True})
            elif path == "/api/chat":
                message_list = data.get("messages")
                if not isinstance(message_list, list):
                    raise ValueError("Messages must be a list.")
                reply = providers.chat(str(data.get("provider_id", "")), message_list)
                self._json(200, {"reply": reply})
            elif path == "/api/shutdown":
                # shutdown() must run on another thread, not the request thread.
                threading.Thread(target=self.server.shutdown, daemon=True).start()
                self._json(200, {"ok": True, "message": "CURIOS is shutting down."})
            else:
                self._json(404, {"error": "Not found"})
        except ValueError as exc:
            self._json(400, {"error": str(exc)})
        except PermissionError as exc:
            self._json(403, {"error": str(exc)})
        except RuntimeError as exc:
            self._json(502, {"error": str(exc)})
        except Exception:
            self._json(500, {"error": "Unexpected local application error."})


def run_server(host: str = "127.0.0.1", port: int = 8765) -> None:
    server = CURIOSServer((host, port), Handler)
    try:
        server.serve_forever(poll_interval=0.25)
    finally:
        server.server_close()
