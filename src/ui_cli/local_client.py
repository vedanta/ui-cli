"""Async HTTP client for UniFi Local Controller API.

Supports both UDM-based controllers (using /proxy/network/api/) and
Cloud Key / self-hosted controllers (using /api/).
"""

import json
from datetime import datetime, timezone
from typing import Any

import httpx

from ui_cli.config import settings


class LocalAPIError(Exception):
    """Base exception for local API errors."""

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class LocalAuthenticationError(LocalAPIError):
    """Raised when authentication fails."""

    pass


class LocalConnectionError(LocalAPIError):
    """Raised when connection to controller fails."""

    pass


class SessionExpiredError(LocalAPIError):
    """Raised when session has expired."""

    pass


class UniFiLocalClient:
    """Async client for UniFi Local Controller API."""

    def __init__(
        self,
        controller_url: str | None = None,
        username: str | None = None,
        password: str | None = None,
        site: str | None = None,
        verify_ssl: bool | None = None,
    ):
        self.controller_url = (controller_url or settings.controller_url).rstrip("/")
        self.username = username or settings.controller_username
        self.password = password or settings.controller_password
        self.site = site or settings.controller_site
        self.verify_ssl = verify_ssl if verify_ssl is not None else settings.controller_verify_ssl
        self.timeout = settings.timeout

        # Session state
        self._cookies: dict[str, str] = {}
        self._csrf_token: str | None = None
        self._is_udm: bool | None = None  # None = not detected yet

        if not self.controller_url:
            raise LocalAuthenticationError(
                "Controller URL not configured. Set UNIFI_CONTROLLER_URL in .env file."
            )
        if not self.username or not self.password:
            raise LocalAuthenticationError(
                "Controller credentials not configured. Set UNIFI_CONTROLLER_USERNAME and UNIFI_CONTROLLER_PASSWORD in .env file."
            )

    @property
    def api_prefix(self) -> str:
        """Get API prefix based on controller type."""
        if self._is_udm:
            return f"{self.controller_url}/proxy/network/api/s/{self.site}"
        return f"{self.controller_url}/api/s/{self.site}"

    @property
    def auth_url(self) -> str:
        """Get authentication URL based on controller type."""
        if self._is_udm:
            return f"{self.controller_url}/api/auth/login"
        return f"{self.controller_url}/api/login"

    def _load_session(self) -> bool:
        """Load session from file. Returns True if valid session loaded."""
        session_file = settings.session_file
        if not session_file.exists():
            return False

        try:
            data = json.loads(session_file.read_text())

            # Check if session is for same controller
            if data.get("controller_url") != self.controller_url:
                return False

            # Check if session has expired (sessions typically last 24h)
            expires_at = data.get("expires_at")
            if expires_at:
                expires = datetime.fromisoformat(expires_at)
                if datetime.now(timezone.utc) >= expires:
                    return False

            self._cookies = data.get("cookies", {})
            self._csrf_token = data.get("csrf_token")
            self._is_udm = data.get("is_udm")
            return bool(self._cookies)

        except (json.JSONDecodeError, KeyError, ValueError):
            return False

    def _save_session(self) -> None:
        """Save session to file."""
        # Session expires in 24 hours
        expires_at = datetime.now(timezone.utc).replace(
            hour=23, minute=59, second=59
        ).isoformat()

        data = {
            "controller_url": self.controller_url,
            "cookies": self._cookies,
            "csrf_token": self._csrf_token,
            "is_udm": self._is_udm,
            "expires_at": expires_at,
        }

        settings.session_file.write_text(json.dumps(data, indent=2))

    def _clear_session(self) -> None:
        """Clear stored session."""
        self._cookies = {}
        self._csrf_token = None
        session_file = settings.session_file
        if session_file.exists():
            session_file.unlink()

    async def _detect_controller_type(self, client: httpx.AsyncClient) -> None:
        """Detect if this is a UDM-based controller or Cloud Key/self-hosted."""
        # Check if UDM by trying to access a UDM-specific endpoint
        try:
            # UDM has /api/auth/login, Cloud Key has /api/login
            # We check without credentials first to avoid wasting auth attempts
            response = await client.get(
                f"{self.controller_url}/api/users/self",
            )
            # UDM returns 401, Cloud Key returns 404 for this endpoint
            if response.status_code == 401:
                self._is_udm = True
                return
        except httpx.RequestError:
            pass

        # Try the status endpoint which doesn't require auth
        try:
            response = await client.get(f"{self.controller_url}/status")
            # If we get here, likely Cloud Key or self-hosted
            self._is_udm = False
            return
        except httpx.RequestError:
            pass

        # Default to trying UDM first (more common now)
        self._is_udm = True

    async def login(self) -> bool:
        """Authenticate with the controller. Returns True on success."""
        async with httpx.AsyncClient(
            timeout=self.timeout,
            verify=self.verify_ssl,
        ) as client:
            # Detect controller type if not known
            if self._is_udm is None:
                await self._detect_controller_type(client)

            try:
                # Try UDM-style auth first
                if self._is_udm:
                    response = await client.post(
                        f"{self.controller_url}/api/auth/login",
                        json={
                            "username": self.username,
                            "password": self.password,
                            "remember": True,
                        },
                    )

                    if response.status_code == 200:
                        self._cookies = dict(response.cookies)
                        self._csrf_token = response.headers.get("X-CSRF-Token")
                        self._save_session()
                        return True
                    elif response.status_code == 403:
                        # 403 on UDM often means wrong credentials
                        raise LocalAuthenticationError(
                            "Invalid username or password (or account lacks API access)"
                        )
                    elif response.status_code == 401:
                        raise LocalAuthenticationError("Invalid username or password")

                # Try Cloud Key / self-hosted style auth
                response = await client.post(
                    f"{self.controller_url}/api/login",
                    json={
                        "username": self.username,
                        "password": self.password,
                        "remember": True,
                    },
                )

                if response.status_code == 200:
                    self._cookies = dict(response.cookies)
                    self._is_udm = False  # Confirmed not UDM
                    self._save_session()
                    return True
                elif response.status_code == 400:
                    # Check response for more details
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("meta", {}).get("msg", "")
                        if "Invalid" in error_msg:
                            raise LocalAuthenticationError("Invalid username or password")
                    except Exception:
                        pass
                    raise LocalAuthenticationError(
                        "Authentication failed - check credentials"
                    )
                elif response.status_code in (401, 403):
                    raise LocalAuthenticationError("Invalid username or password")
                else:
                    raise LocalAuthenticationError(
                        f"Authentication failed: HTTP {response.status_code}"
                    )

            except LocalAuthenticationError:
                raise
            except httpx.ConnectError as e:
                raise LocalConnectionError(
                    f"Could not connect to controller at {self.controller_url}: {e}"
                )
            except httpx.TimeoutException:
                raise LocalConnectionError(
                    f"Connection timeout to {self.controller_url}"
                )

    async def ensure_authenticated(self) -> None:
        """Ensure we have a valid session, logging in if needed."""
        if not self._load_session():
            await self.login()

    def _get_headers(self) -> dict[str, str]:
        """Get request headers with CSRF token if available."""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self._csrf_token:
            headers["X-CSRF-Token"] = self._csrf_token
        return headers

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        retry_auth: bool = True,
    ) -> dict[str, Any]:
        """Make an authenticated request to the local API."""
        await self.ensure_authenticated()

        url = f"{self.api_prefix}/{endpoint.lstrip('/')}"

        async with httpx.AsyncClient(
            timeout=self.timeout,
            verify=self.verify_ssl,
            cookies=self._cookies,
        ) as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self._get_headers(),
                    json=data,
                )

                # Handle session expiry
                if response.status_code == 401:
                    if retry_auth:
                        self._clear_session()
                        await self.login()
                        return await self._request(
                            method, endpoint, data, retry_auth=False
                        )
                    raise SessionExpiredError("Session expired and re-login failed")

                if response.status_code >= 400:
                    raise LocalAPIError(
                        f"API error: {response.text}",
                        status_code=response.status_code,
                    )

                return response.json()

            except httpx.ConnectError as e:
                raise LocalConnectionError(f"Connection error: {e}")
            except httpx.TimeoutException:
                raise LocalConnectionError("Request timeout")

    async def get(self, endpoint: str) -> dict[str, Any]:
        """Make a GET request."""
        return await self._request("GET", endpoint)

    async def post(
        self, endpoint: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Make a POST request."""
        return await self._request("POST", endpoint, data=data)

    # ========== Clients ==========

    async def list_clients(self) -> list[dict[str, Any]]:
        """List active (connected) clients."""
        response = await self.get("/stat/sta")
        return response.get("data", [])

    async def list_all_clients(self) -> list[dict[str, Any]]:
        """List all known clients (including offline)."""
        response = await self.get("/rest/user")
        return response.get("data", [])

    async def get_client(self, mac: str) -> dict[str, Any] | None:
        """Get details for a specific client by MAC address."""
        mac = mac.lower().replace("-", ":")
        response = await self.get(f"/stat/user/{mac}")
        data = response.get("data", [])
        return data[0] if data else None

    async def block_client(self, mac: str) -> bool:
        """Block a client by MAC address."""
        mac = mac.lower().replace("-", ":")
        response = await self.post("/cmd/stamgr", data={"cmd": "block-sta", "mac": mac})
        return response.get("meta", {}).get("rc") == "ok"

    async def unblock_client(self, mac: str) -> bool:
        """Unblock a client by MAC address."""
        mac = mac.lower().replace("-", ":")
        response = await self.post(
            "/cmd/stamgr", data={"cmd": "unblock-sta", "mac": mac}
        )
        return response.get("meta", {}).get("rc") == "ok"

    async def kick_client(self, mac: str) -> bool:
        """Kick (disconnect) a client by MAC address."""
        mac = mac.lower().replace("-", ":")
        response = await self.post("/cmd/stamgr", data={"cmd": "kick-sta", "mac": mac})
        return response.get("meta", {}).get("rc") == "ok"

    # ========== Configuration ==========

    async def get_networks(self) -> list[dict[str, Any]]:
        """Get all network configurations (VLANs, subnets)."""
        response = await self.get("/rest/networkconf")
        return response.get("data", [])

    async def get_wlans(self) -> list[dict[str, Any]]:
        """Get all wireless network (SSID) configurations."""
        response = await self.get("/rest/wlanconf")
        return response.get("data", [])

    async def get_firewall_rules(self) -> list[dict[str, Any]]:
        """Get all firewall rules."""
        response = await self.get("/rest/firewallrule")
        return response.get("data", [])

    async def get_firewall_groups(self) -> list[dict[str, Any]]:
        """Get all firewall groups."""
        response = await self.get("/rest/firewallgroup")
        return response.get("data", [])

    async def get_port_forwards(self) -> list[dict[str, Any]]:
        """Get all port forwarding rules."""
        response = await self.get("/rest/portforward")
        return response.get("data", [])

    async def get_devices(self) -> list[dict[str, Any]]:
        """Get all device configurations and status."""
        response = await self.get("/stat/device")
        return response.get("data", [])

    async def get_device(self, mac: str) -> dict[str, Any] | None:
        """Get a specific device by MAC address."""
        mac = mac.lower().replace("-", ":")
        devices = await self.get_devices()
        for device in devices:
            if device.get("mac", "").lower() == mac:
                return device
        return None

    async def restart_device(self, mac: str) -> bool:
        """Restart/reboot a device."""
        mac = mac.lower().replace("-", ":")
        response = await self.post("/cmd/devmgr", data={"cmd": "restart", "mac": mac})
        return response.get("meta", {}).get("rc") == "ok"

    async def upgrade_device(self, mac: str) -> bool:
        """Upgrade device firmware."""
        mac = mac.lower().replace("-", ":")
        response = await self.post("/cmd/devmgr", data={"cmd": "upgrade", "mac": mac})
        return response.get("meta", {}).get("rc") == "ok"

    async def locate_device(self, mac: str, enabled: bool = True) -> bool:
        """Enable/disable locate LED on device."""
        mac = mac.lower().replace("-", ":")
        response = await self.post(
            "/cmd/devmgr",
            data={"cmd": "set-locate", "mac": mac, "locate_enable": enabled},
        )
        return response.get("meta", {}).get("rc") == "ok"

    async def adopt_device(self, mac: str) -> bool:
        """Adopt a device."""
        mac = mac.lower().replace("-", ":")
        response = await self.post("/cmd/devmgr", data={"cmd": "adopt", "mac": mac})
        return response.get("meta", {}).get("rc") == "ok"

    async def get_dhcp_reservations(self) -> list[dict[str, Any]]:
        """Get DHCP reservations (clients with fixed IPs)."""
        # Fixed IPs are stored in user records with use_fixedip=True
        response = await self.get("/rest/user")
        users = response.get("data", [])
        return [u for u in users if u.get("use_fixedip", False)]

    async def get_traffic_rules(self) -> list[dict[str, Any]]:
        """Get traffic rules/schedules."""
        response = await self.get("/rest/trafficrule")
        return response.get("data", [])

    async def get_routing(self) -> list[dict[str, Any]]:
        """Get static routes."""
        response = await self.get("/rest/routing")
        return response.get("data", [])

    async def get_site_settings(self) -> list[dict[str, Any]]:
        """Get site settings."""
        response = await self.get("/rest/setting")
        return response.get("data", [])

    async def get_running_config(self) -> dict[str, Any]:
        """Get full running configuration."""
        config: dict[str, Any] = {}

        # Fetch each section, handling errors gracefully
        async def safe_fetch(name: str, func):
            try:
                config[name] = await func()
            except LocalAPIError:
                config[name] = []  # Empty list on error

        await safe_fetch("networks", self.get_networks)
        await safe_fetch("wireless", self.get_wlans)
        await safe_fetch("firewall_rules", self.get_firewall_rules)
        await safe_fetch("firewall_groups", self.get_firewall_groups)
        await safe_fetch("port_forwards", self.get_port_forwards)
        await safe_fetch("devices", self.get_devices)
        await safe_fetch("dhcp_reservations", self.get_dhcp_reservations)
        await safe_fetch("traffic_rules", self.get_traffic_rules)
        await safe_fetch("routing", self.get_routing)

        return config

    # ========== Monitoring ==========

    async def get_events(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get recent events."""
        response = await self.post("/stat/event", data={"_limit": limit, "_sort": "-time"})
        return response.get("data", [])

    async def get_alarms(self, archived: bool = False) -> list[dict[str, Any]]:
        """Get alarms. Set archived=True to include archived alarms."""
        response = await self.get("/stat/alarm")
        alarms = response.get("data", [])
        if not archived:
            alarms = [a for a in alarms if not a.get("archived", False)]
        return alarms

    async def archive_alarm(self, alarm_id: str) -> bool:
        """Archive an alarm by ID."""
        response = await self.post(
            "/cmd/evtmgr", data={"cmd": "archive-alarm", "_id": alarm_id}
        )
        return response.get("meta", {}).get("rc") == "ok"

    async def get_health(self) -> list[dict[str, Any]]:
        """Get site health information."""
        response = await self.get("/stat/health")
        return response.get("data", [])

    # ========== Vouchers ==========

    async def get_vouchers(self) -> list[dict[str, Any]]:
        """Get all vouchers."""
        response = await self.get("/stat/voucher")
        return response.get("data", [])

    async def create_voucher(
        self,
        count: int = 1,
        duration: int = 1440,  # minutes (24h default)
        quota: int = 0,  # MB (0 = unlimited)
        up_limit: int = 0,  # kbps (0 = unlimited)
        down_limit: int = 0,  # kbps (0 = unlimited)
        multi_use: int = 1,  # number of uses
        note: str | None = None,
    ) -> list[dict[str, Any]]:
        """Create voucher(s).

        Args:
            count: Number of vouchers to create
            duration: Duration in minutes
            quota: Data quota in MB (0 = unlimited)
            up_limit: Upload limit in kbps (0 = unlimited)
            down_limit: Download limit in kbps (0 = unlimited)
            multi_use: Number of uses per voucher
            note: Optional note/description

        Returns:
            List of created voucher data
        """
        data: dict[str, Any] = {
            "cmd": "create-voucher",
            "n": count,
            "expire": duration,
            "quota": multi_use,  # quota field is actually multi-use count
        }

        if quota > 0:
            data["bytes"] = quota  # MB

        if up_limit > 0:
            data["up"] = up_limit

        if down_limit > 0:
            data["down"] = down_limit

        if note:
            data["note"] = note

        response = await self.post("/cmd/hotspot", data=data)
        return response.get("data", [])

    async def revoke_voucher(self, voucher_id: str) -> bool:
        """Revoke/delete a voucher by ID."""
        response = await self.post(
            "/cmd/hotspot", data={"cmd": "delete-voucher", "_id": voucher_id}
        )
        return response.get("meta", {}).get("rc") == "ok"

    # ========== DPI (Deep Packet Inspection) ==========

    async def get_site_dpi(self) -> list[dict[str, Any]]:
        """Get site-level DPI statistics."""
        response = await self.get("/stat/sitedpi")
        return response.get("data", [])

    async def get_client_dpi(self, mac: str) -> list[dict[str, Any]]:
        """Get DPI statistics for a specific client."""
        mac = mac.lower().replace("-", ":")
        response = await self.get(f"/stat/stadpi/{mac}")
        return response.get("data", [])

    # ========== Statistics ==========

    async def get_daily_stats(self, days: int = 30) -> list[dict[str, Any]]:
        """Get daily site statistics."""
        response = await self.post(
            "/stat/report/daily.site",
            data={
                "attrs": ["time", "rx_bytes", "tx_bytes", "num_sta", "wan-rx_bytes", "wan-tx_bytes"],
                "n": days,
            },
        )
        return response.get("data", [])

    async def get_hourly_stats(self, hours: int = 24) -> list[dict[str, Any]]:
        """Get hourly site statistics."""
        response = await self.post(
            "/stat/report/hourly.site",
            data={
                "attrs": ["time", "rx_bytes", "tx_bytes", "num_sta", "wan-rx_bytes", "wan-tx_bytes"],
                "n": hours,
            },
        )
        return response.get("data", [])
