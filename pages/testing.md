# Testing

UI-CLI has three tiers of tests, each answering a different question:

| Tier | Location | Question it answers | Needs | Speed |
|------|----------|--------------------|-------|-------|
| **Unit** | `tests/unit/` | Does each function behave correctly in isolation? | Nothing | < 1s |
| **Synthetic regression** | `tests/regression/` | Does the real client work end-to-end over HTTP? | Nothing | < 1s |
| **Integration** | `tests/integration/` | Does it work against real UniFi hardware and the cloud API? | Real credentials | Network-bound |

## Running Tests

```bash
# Unit + synthetic regression (the default local loop — no setup needed)
pytest tests/unit tests/regression

# Everything, including integration (skips integration if credentials are missing)
pytest

# Integration only (requires a real controller / API key in .env)
pytest tests/integration

# With coverage
pytest --cov=ui_cli
```

!!! tip "No credentials, no problem"
    Unit and synthetic regression tests require **no configuration** — no
    `.env`, no controller, no network beyond localhost. Integration tests
    auto-skip when `UNIFI_API_KEY`, `UNIFI_CONTROLLER_URL`,
    `UNIFI_CONTROLLER_USERNAME`, or `UNIFI_CONTROLLER_PASSWORD` are unset.

## Unit Tests

`tests/unit/` covers individual components with mocked boundaries:

| File | Covers |
|------|--------|
| `test_local_client.py` | Local controller client: init, API prefixes, login payloads, MFA/TOTP error paths, session reuse |
| `test_site_manager_client.py` | Cloud (Site Manager) API client |
| `test_groups.py` | Client group management and auto-group rules |
| `test_formatting.py` | Data formatting helpers |
| `test_output.py` | Table/JSON/CSV output |

HTTP calls are mocked with `unittest.mock` (`AsyncMock` for async methods),
and settings are patched per-test, so nothing touches your real
configuration. Shared fixtures — canned API responses like
`mock_local_clients_response` — live in `tests/conftest.py`.

## Synthetic Regression Tests

`tests/regression/test_synthetic_udm.py` is the middle tier: it exercises the
**real, unmocked** `UniFiLocalClient` end-to-end against a **fake UDM
controller** running in-process.

### How it works

```
┌──────────────────────┐   real HTTP over    ┌──────────────────────────┐
│  UniFiLocalClient    │   localhost socket  │  FakeUDMController       │
│  (production code,   │ ◄─────────────────► │  (stdlib http.server on  │
│   nothing mocked)    │                     │   a random port)         │
└──────────────────────┘                     └──────────────────────────┘
```

`FakeUDMController` is a `ThreadingHTTPServer` bound to `127.0.0.1` on a
random port, speaking the actual UDM wire protocol:

- Answers the `/api/users/self` detection probe with `401` (how real UDMs
  identify themselves)
- Implements `/api/auth/login` — checks the password, and when MFA mode is
  on, returns `499 MFA_AUTH_REQUIRED` unless the correct TOTP `token` is in
  the payload
- Issues session cookies and an `X-CSRF-Token` header on successful login
- Serves authenticated data endpoints (`/stat/sta`, `/stat/device`) behind
  cookie validation
- **Records every login payload and API request**, so tests assert on what
  actually went over the wire

Because the real client runs unmodified, these tests catch regressions that
unit tests structurally cannot: wrong URL construction, cookie handling,
header propagation, session file round-trips, and retry logic.

### Covered scenarios

| Class | Scenario |
|-------|----------|
| `TestSyntheticLogin` | Full login + data fetch with UDM auto-detection and session persistence |
| | Login payload omits `token` when no TOTP is configured |
| | Wrong password → `403` → clear "Invalid username or password" error |
| `TestSyntheticMFA` | MFA enabled, no TOTP → "MFA token required" |
| | MFA enabled, stale TOTP → "invalid or expired" |
| | MFA enabled, valid TOTP → full flow; token on the wire, CSRF echoed |
| `TestSyntheticSessionCache` | New client instance reuses the cached session without re-login (TOTP needed only once) |
| | Server revokes sessions → client re-logins automatically on `401` |

### Isolation guarantees

An autouse fixture keeps every test hermetic:

- `HOME` is pointed at a per-test temp directory, so the session cache goes
  to a throwaway path — your real `~/.config/ui-cli/session.json` is never
  read or written
- `UNIFI_CONTROLLER_TOTP` from your local `.env` is neutralized, so results
  don't depend on your environment

### Adding a scenario

1. Give `FakeUDMController` any new behavior it needs (a new endpoint in the
   handler, or a toggle like `mfa_enabled`)
2. Build a client with the `make_client(fake_udm, ...)` helper — it points
   the real client at the fake server
3. Assert on the outcome **and** on the recorded traffic
   (`fake_udm.login_requests`, `fake_udm.api_requests`) to pin the wire
   behavior, not just the return value

```python
async def test_my_new_scenario(self, fake_udm):
    fake_udm.mfa_enabled = True
    client = make_client(fake_udm, totp="424242")

    clients = await client.list_clients()

    assert len(clients) == 2
    assert fake_udm.login_requests[0]["token"] == "424242"
```

## Integration Tests

`tests/integration/` runs the same clients against **real** infrastructure:
a live UniFi controller on your network and the cloud Site Manager API.
They are marked `@pytest.mark.integration` and skip automatically unless the
required environment variables are set (see
[Configuration](configuration.md)).

Use these before a release or after changes to request/response handling —
they are the only tier that can catch changes in UniFi's actual API
behavior.

!!! warning "Integration tests touch real systems"
    They authenticate against your actual controller and read live data.
    Read-only endpoints are used, but run them against a controller you own.
