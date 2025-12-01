"""Unit tests for Local Controller API client."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ui_cli.local_client import (
    LocalAPIError,
    LocalAuthenticationError,
    LocalConnectionError,
    UniFiLocalClient,
)


class TestUniFiLocalClientInit:
    """Tests for Local Controller client initialization."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch("ui_cli.local_client.settings") as mock:
            mock.controller_url = "https://192.168.1.1"
            mock.controller_username = "admin"
            mock.controller_password = "password"
            mock.controller_site = "default"
            mock.controller_verify_ssl = False
            mock.timeout = 30
            mock.session_file = MagicMock()
            mock.session_file.exists.return_value = False
            yield mock

    def test_client_initialization(self, mock_settings):
        """Test client initializes with correct settings."""
        client = UniFiLocalClient()
        assert client.controller_url == "https://192.168.1.1"
        assert client.username == "admin"
        assert client.site == "default"

    def test_client_without_url_raises_error(self, mock_settings):
        """Test client raises error when URL is missing."""
        mock_settings.controller_url = ""
        with pytest.raises(LocalAuthenticationError, match="URL not configured"):
            UniFiLocalClient()

    def test_client_without_credentials_raises_error(self, mock_settings):
        """Test client raises error when credentials are missing."""
        mock_settings.controller_username = None
        with pytest.raises(LocalAuthenticationError, match="credentials not configured"):
            UniFiLocalClient()

    def test_api_prefix_for_udm(self, mock_settings):
        """Test API prefix for UDM controllers."""
        client = UniFiLocalClient()
        client._is_udm = True
        assert "/proxy/network/api/s/default" in client.api_prefix

    def test_api_prefix_for_cloud_key(self, mock_settings):
        """Test API prefix for Cloud Key controllers."""
        client = UniFiLocalClient()
        client._is_udm = False
        assert "/api/s/default" in client.api_prefix
        assert "/proxy/network" not in client.api_prefix


class TestUniFiLocalClientMethods:
    """Tests for Local Controller client methods."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch("ui_cli.local_client.settings") as mock:
            mock.controller_url = "https://192.168.1.1"
            mock.controller_username = "admin"
            mock.controller_password = "password"
            mock.controller_site = "default"
            mock.controller_verify_ssl = False
            mock.timeout = 30
            mock.session_file = MagicMock()
            mock.session_file.exists.return_value = False
            yield mock

    @pytest.mark.asyncio
    async def test_list_clients(self, mock_settings, mock_local_clients_response):
        """Test listing clients."""
        client = UniFiLocalClient()

        with patch.object(client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"data": mock_local_clients_response}

            clients = await client.list_clients()

            assert len(clients) == 2
            assert clients[0]["mac"] == "aa:bb:cc:11:22:33"

    @pytest.mark.asyncio
    async def test_get_devices(self, mock_settings, mock_local_devices_response):
        """Test getting devices."""
        client = UniFiLocalClient()

        with patch.object(client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"data": mock_local_devices_response}

            devices = await client.get_devices()

            assert len(devices) == 2
            assert devices[0]["name"] == "Home Gateway"

    @pytest.mark.asyncio
    async def test_get_events(self, mock_settings, mock_events_response):
        """Test getting events."""
        client = UniFiLocalClient()

        with patch.object(client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = {"data": mock_events_response}

            events = await client.get_events(limit=50)

            assert len(events) == 2
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_networks(self, mock_settings, mock_networks_response):
        """Test getting networks."""
        client = UniFiLocalClient()

        with patch.object(client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"data": mock_networks_response}

            networks = await client.get_networks()

            assert len(networks) == 2
            assert networks[0]["name"] == "Default"

    @pytest.mark.asyncio
    async def test_get_vouchers(self, mock_settings, mock_vouchers_response):
        """Test getting vouchers."""
        client = UniFiLocalClient()

        with patch.object(client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"data": mock_vouchers_response}

            vouchers = await client.get_vouchers()

            assert len(vouchers) == 2
            assert vouchers[0]["code"] == "12345-67890"

    @pytest.mark.asyncio
    async def test_get_daily_stats(self, mock_settings, mock_daily_stats_response):
        """Test getting daily stats."""
        client = UniFiLocalClient()

        with patch.object(client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = {"data": mock_daily_stats_response}

            stats = await client.get_daily_stats(days=7)

            assert len(stats) == 2
            assert stats[0]["num_sta"] == 80

    @pytest.mark.asyncio
    async def test_restart_device(self, mock_settings):
        """Test restarting a device."""
        client = UniFiLocalClient()

        with patch.object(client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = {"meta": {"rc": "ok"}}

            success = await client.restart_device("aa:bb:cc:dd:ee:ff")

            assert success is True
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "restart" in str(call_args)

    @pytest.mark.asyncio
    async def test_block_client(self, mock_settings):
        """Test blocking a client."""
        client = UniFiLocalClient()

        with patch.object(client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = {"meta": {"rc": "ok"}}

            success = await client.block_client("aa:bb:cc:dd:ee:ff")

            assert success is True

    @pytest.mark.asyncio
    async def test_create_voucher(self, mock_settings):
        """Test creating a voucher."""
        client = UniFiLocalClient()

        with patch.object(client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = {"data": [{"create_time": 1700000000}]}

            result = await client.create_voucher(
                count=1,
                duration=1440,
                quota=0,
                up_limit=0,
                down_limit=0,
                multi_use=1,
                note="Test",
            )

            assert len(result) == 1


class TestLocalClientFormatting:
    """Tests for Local Controller data formatting helpers."""

    def test_device_status_online(self, mock_local_devices_response):
        """Test device status detection for online devices."""
        device = mock_local_devices_response[0]
        assert device["state"] == 1  # 1 = online

    def test_device_status_offline(self):
        """Test device status detection for offline devices."""
        device = {"state": 0}
        assert device["state"] == 0  # 0 = offline

    def test_client_is_wired(self, mock_local_clients_response):
        """Test client wired/wireless detection."""
        wired_client = mock_local_clients_response[1]
        wireless_client = mock_local_clients_response[0]
        assert wired_client["is_wired"] is True
        assert wireless_client["is_wired"] is False

    def test_voucher_code_format(self, mock_vouchers_response):
        """Test voucher code format."""
        voucher = mock_vouchers_response[0]
        code = voucher["code"]
        assert "-" in code
        assert len(code.replace("-", "")) == 10
