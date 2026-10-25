"""Synthetic regression tests for self-hosted Network 10.x auth behavior."""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from ui_cli.local_client import UniFiLocalClient


class FakeSelfHosted10xController:
    """In-process fake self-hosted 10.x controller."""

    def __init__(self):
        self.password = "secret"
        self.sessions: set[str] = set()
        self.auth_calls: list[str] = []
        self._httpd = ThreadingHTTPServer(("127.0.0.1", 0), self._make_handler())
        self._thread = threading.Thread(
            target=lambda: self._httpd.serve_forever(poll_interval=0.05), daemon=True
        )

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self._httpd.server_address[1]}"

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._httpd.shutdown()
        self._httpd.server_close()

    def _make_handler(self):
        controller = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def _json(self, code, payload=None, headers=None):
                body = json.dumps(payload or {}).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                for key, value in (headers or {}).items():
                    self.send_header(key, value)
                self.end_headers()
                self.wfile.write(body)

            def _session_ok(self) -> bool:
                cookie = self.headers.get("Cookie", "")
                return any(f"TOKEN={s}" in cookie for s in controller.sessions)

            def do_GET(self):
                if self.path == "/api/users/self":
                    # Matches self-hosted 10.x probe behavior.
                    self._json(401, {"error": "unauthorized"})
                    return

                if self.path == "/api/s/default/stat/sta":
                    if self._session_ok():
                        self._json(
                            200,
                            {"data": [{"mac": "aa:bb:cc:11:22:33", "hostname": "laptop"}]},
                        )
                    else:
                        self._json(401, {})
                    return

                self._json(404, {})

            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                payload = json.loads(self.rfile.read(length) or b"{}")

                if self.path == "/api/auth/login":
                    # Endpoint absent on this fake self-hosted 10.x.
                    controller.auth_calls.append(self.path)
                    self._json(404, {})
                    return

                if self.path == "/api/login":
                    controller.auth_calls.append(self.path)
                    if payload.get("password") != controller.password:
                        self._json(401, {})
                        return
                    token = "sess-1"
                    controller.sessions.add(token)
                    self._json(200, {}, headers={"Set-Cookie": f"TOKEN={token}; Path=/"})
                    return

                self._json(404, {})

        return Handler


@pytest.fixture
def fake_self_hosted_10x():
    server = FakeSelfHosted10xController()
    server.start()
    yield server
    server.stop()


@pytest.fixture(autouse=True)
def isolated_session(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr("ui_cli.config.settings.controller_totp", "")
    return tmp_path


@pytest.mark.asyncio
async def test_probe_401_still_logs_in_via_api_login(fake_self_hosted_10x):
    """Probe 401 should not block self-hosted /api/login fallback."""
    client = UniFiLocalClient(
        fake_self_hosted_10x.url,
        "admin",
        fake_self_hosted_10x.password,
        verify_ssl=False,
        timeout=5,
    )

    clients = await client.list_clients()

    assert len(clients) == 1
    assert client._is_udm is False
    assert fake_self_hosted_10x.auth_calls == ["/api/auth/login", "/api/login"]
