"""Unit tests for Site Manager API client."""

from unittest.mock import AsyncMock, patch

import pytest

from ui_cli.client import UniFiClient, AuthenticationError


class TestUniFiClient:
    """Tests for the Site Manager API client."""

    def test_client_initialization_with_params(self):
        """Test client initializes with explicit parameters."""
        client = UniFiClient(
            api_key="test-api-key",
            base_url="https://api.ui.com",
            timeout=30,
        )
        assert client.api_key == "test-api-key"
        assert client.base_url == "https://api.ui.com"
        assert client.timeout == 30

    def test_client_without_api_key_raises_error(self):
        """Test client raises error when API key is missing."""
        with patch("ui_cli.client.settings") as mock_settings:
            mock_settings.api_key = None
            mock_settings.api_url = "https://api.ui.com"
            mock_settings.timeout = 30
            with pytest.raises(AuthenticationError, match="API key not configured"):
                UniFiClient()

    @pytest.mark.asyncio
    async def test_list_hosts(self, mock_hosts_response):
        """Test listing hosts."""
        client = UniFiClient(api_key="test-key", base_url="https://api.ui.com")

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"data": mock_hosts_response}

            hosts = await client.list_hosts()

            assert len(hosts) == 2
            assert hosts[0]["id"] == "host-001"
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_sites(self, mock_sites_response):
        """Test listing sites."""
        client = UniFiClient(api_key="test-key", base_url="https://api.ui.com")

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"data": mock_sites_response}

            sites = await client.list_sites()

            assert len(sites) == 2
            assert sites[0]["siteId"] == "site-001"

    @pytest.mark.asyncio
    async def test_list_devices(self, mock_devices_response):
        """Test listing devices."""
        client = UniFiClient(api_key="test-key", base_url="https://api.ui.com")

        # list_devices returns flattened devices, so mock list_devices_raw
        with patch.object(client, "list_devices_raw", new_callable=AsyncMock) as mock_raw:
            # Raw response is grouped by host
            mock_raw.return_value = [
                {"hostId": "host-001", "devices": mock_devices_response}
            ]

            devices = await client.list_devices()

            assert len(devices) == 2
            assert devices[0]["name"] == "Living Room AP"

    @pytest.mark.asyncio
    async def test_get_host_by_id(self, mock_hosts_response):
        """Test getting a specific host."""
        client = UniFiClient(api_key="test-key", base_url="https://api.ui.com")

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"data": mock_hosts_response[0]}

            host = await client.get_host("host-001")

            assert host["id"] == "host-001"

    def test_get_headers(self):
        """Test that headers include API key."""
        client = UniFiClient(api_key="test-api-key", base_url="https://api.ui.com")
        headers = client._get_headers()

        assert headers["X-API-Key"] == "test-api-key"
        assert "Accept" in headers
        assert "Content-Type" in headers


class TestHostsFormatting:
    """Tests for hosts data formatting."""

    def test_extract_host_name(self, mock_hosts_response):
        """Test extracting host name from response."""
        host = mock_hosts_response[0]
        name = host.get("userData", {}).get("name", host.get("reportedState", {}).get("hostname", ""))
        assert name == "Home Gateway"

    def test_extract_host_ip(self, mock_hosts_response):
        """Test extracting host IP from response."""
        host = mock_hosts_response[0]
        ip = host.get("reportedState", {}).get("ip", "")
        assert ip == "192.168.1.1"

    def test_extract_host_state(self, mock_hosts_response):
        """Test extracting host state from response."""
        host = mock_hosts_response[0]
        state = host.get("reportedState", {}).get("state", "unknown")
        assert state == "connected"


class TestSitesFormatting:
    """Tests for sites data formatting."""

    def test_extract_site_name(self, mock_sites_response):
        """Test extracting site name."""
        site = mock_sites_response[0]
        assert site["siteName"] == "Home Network"

    def test_extract_device_counts(self, mock_sites_response):
        """Test extracting device counts."""
        site = mock_sites_response[0]
        stats = site.get("statistics", {}).get("counts", {})
        assert stats.get("totalDevice") == 10
        assert stats.get("offlineDevice") == 1

    def test_extract_owner_status(self, mock_sites_response):
        """Test extracting owner status."""
        assert mock_sites_response[0]["isOwner"] is True
        assert mock_sites_response[1]["isOwner"] is False
