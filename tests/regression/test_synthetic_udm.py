"""Synthetic regression tests against a fake UDM controller.

Runs the real UniFiLocalClient end-to-end over HTTP against an in-process
fake UDM controller: controller-type detection, login (with and without
MFA/TOTP), session caching, session expiry with automatic re-login, and
authenticated data fetches. No real hardware or network access required.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from ui_cli.local_client import LocalAuthenticationError, UniFiLocalClient

FAKE_CLIENTS = [
    {"mac": "aa:bb:cc:11:22:33", "hostname": "laptop", "is_wired": False},
    {"mac": "dd:ee:ff:44:55:66", "hostname": "nas", "is_wired": True},
]

FAKE_DEVICES = [
    {"mac": "11:22:33:44:55:66", "name": "Fake Gateway", "model": "UDMPRO", "state": 1},
]


class FakeUDMController:
    """In-process fake UDM controller speaking the real HTTP protocol."""

    def __init__(self):
        self.mfa_enabled = False
        self.valid_totp = "424242"
        self.password = "secret"
        self.sessions: set[str] = set()
        self.login_requests: list[dict] = []
        self.api_requests: list[dict] = []
        self._session_counter = 0
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

    def revoke_sessions(self) -> None:
        """Simulate the controller invalidating all sessions."""
        self.sessions.clear()

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
                # UDM detection probe: UDMs answer 401 here, Cloud Keys 404
                if self.path == "/api/users/self":
                    self._json(401, {"error": "unauthorized"})
                    return

                if self.path.startswith("/proxy/network/api/s/"):
                    controller.api_requests.append(
                        {
                            "path": self.path,
                            "csrf": self.headers.get("X-CSRF-Token"),
                            "authenticated": self._session_ok(),
                        }
                    )
                    if not self._session_ok():
                        self._json(401, {})
                    elif self.path.endswith("/stat/sta"):
                        self._json(200, {"data": FAKE_CLIENTS})
                    elif self.path.endswith("/stat/device"):
                        self._json(200, {"data": FAKE_DEVICES})
                    else:
                        self._json(404, {})
                    return

                self._json(404, {})

            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                payload = json.loads(self.rfile.read(length) or b"{}")

                if self.path != "/api/auth/login":
                    self._json(404, {})
                    return

                controller.login_requests.append(payload)

                if payload.get("password") != controller.password:
                    self._json(403, {})
                    return

                if controller.mfa_enabled and payload.get("token") != controller.valid_totp:
                    self._json(499, {"errors": ["MFA_AUTH_REQUIRED"]})
                    return

                controller._session_counter += 1
                token = f"sess-{controller._session_counter}"
                controller.sessions.add(token)
                self._json(
                    200,
                    {},
                    headers={
                        "Set-Cookie": f"TOKEN={token}; Path=/",
                        "X-CSRF-Token": "csrf-token-123",
                    },
                )

        return Handler


@pytest.fixture
def fake_udm():
    server = FakeUDMController()
    server.start()
    yield server
    server.stop()


@pytest.fixture(autouse=True)
def isolated_session(monkeypatch, tmp_path):
    """Keep the session cache in a per-test directory and clear env TOTP."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr("ui_cli.config.settings.controller_totp", "")
    return tmp_path


def make_client(server: FakeUDMController, **kwargs) -> UniFiLocalClient:
    return UniFiLocalClient(
        controller_url=server.url,
        username="admin",
        password=kwargs.pop("password", "secret"),
        verify_ssl=False,
        timeout=5,
        **kwargs,
    )


class TestSyntheticLogin:
    """End-to-end login flows against the fake controller."""

    async def test_full_login_and_data_fetch_without_mfa(self, fake_udm, isolated_session):
        client = make_client(fake_udm)

        clients = await client.list_clients()
        devices = await client.get_devices()

        assert [c["mac"] for c in clients] == [c["mac"] for c in FAKE_CLIENTS]
        assert devices[0]["name"] == "Fake Gateway"
        # Detection probe classified the fake controller as UDM
        assert client._is_udm is True
        # Session was persisted for reuse
        session_file = isolated_session / ".config" / "ui-cli" / "session.json"
        assert session_file.exists()
        assert json.loads(session_file.read_text())["is_udm"] is True

    async def test_login_payload_omits_token_without_totp(self, fake_udm):
        client = make_client(fake_udm)
        await client.ensure_authenticated()

        assert len(fake_udm.login_requests) == 1
        assert "token" not in fake_udm.login_requests[0]

    async def test_wrong_password_raises_auth_error(self, fake_udm):
        client = make_client(fake_udm, password="wrong")

        with pytest.raises(LocalAuthenticationError, match="Invalid username or password"):
            await client.login()


class TestSyntheticMFA:
    """MFA/TOTP flows against the fake controller."""

    async def test_mfa_required_without_totp(self, fake_udm):
        fake_udm.mfa_enabled = True
        client = make_client(fake_udm)

        with pytest.raises(LocalAuthenticationError, match="MFA token required"):
            await client.login()

    async def test_mfa_with_stale_totp(self, fake_udm):
        fake_udm.mfa_enabled = True
        client = make_client(fake_udm, totp="000000")

        with pytest.raises(LocalAuthenticationError, match="invalid or expired"):
            await client.login()

    async def test_mfa_with_valid_totp_full_flow(self, fake_udm):
        fake_udm.mfa_enabled = True
        client = make_client(fake_udm, totp=fake_udm.valid_totp)

        clients = await client.list_clients()

        assert len(clients) == 2
        assert fake_udm.login_requests[0]["token"] == fake_udm.valid_totp
        # CSRF token from login is echoed on authenticated requests
        assert fake_udm.api_requests[-1]["csrf"] == "csrf-token-123"


class TestSyntheticSessionCache:
    """Session caching and expiry behavior."""

    async def test_cached_session_reused_by_new_client(self, fake_udm):
        fake_udm.mfa_enabled = True
        first = make_client(fake_udm, totp=fake_udm.valid_totp)
        assert await first.ensure_authenticated() is True

        # A brand-new client (no TOTP) rides the cached session: no new login
        second = make_client(fake_udm)
        assert await second.ensure_authenticated() is False
        clients = await second.list_clients()

        assert len(clients) == 2
        assert len(fake_udm.login_requests) == 1

    async def test_revoked_session_triggers_automatic_relogin(self, fake_udm):
        client = make_client(fake_udm)
        await client.ensure_authenticated()
        assert len(fake_udm.login_requests) == 1

        fake_udm.revoke_sessions()
        clients = await client.list_clients()

        assert len(clients) == 2
        assert len(fake_udm.login_requests) == 2
