"""Integration tests for Local Controller API (require real controller access)."""

import pytest

from ui_cli.local_client import UniFiLocalClient


@pytest.mark.integration
class TestLocalControllerAPIIntegration:
    """Integration tests for Local Controller API."""

    @pytest.fixture
    def client(self, integration_env_vars):
        """Create a real Local Controller client."""
        return UniFiLocalClient()

    @pytest.mark.asyncio
    async def test_list_clients(self, client):
        """Test listing clients from real controller."""
        clients = await client.list_clients()

        assert isinstance(clients, list)
        if clients:
            c = clients[0]
            assert "mac" in c

    @pytest.mark.asyncio
    async def test_get_devices(self, client):
        """Test getting devices from real controller."""
        devices = await client.get_devices()

        assert isinstance(devices, list)
        assert len(devices) > 0  # Should have at least the controller itself

        device = devices[0]
        assert "mac" in device
        assert "model" in device

    @pytest.mark.asyncio
    async def test_get_events(self, client):
        """Test getting events from real controller."""
        events = await client.get_events(limit=10)

        assert isinstance(events, list)
        if events:
            event = events[0]
            assert "time" in event or "datetime" in event

    @pytest.mark.asyncio
    async def test_get_health(self, client):
        """Test getting health from real controller."""
        health = await client.get_health()

        assert isinstance(health, list)
        assert len(health) > 0

        # Should have subsystem info
        subsystems = [h.get("subsystem") for h in health]
        assert any(s in subsystems for s in ["wlan", "wan", "lan", "www"])

    @pytest.mark.asyncio
    async def test_get_networks(self, client):
        """Test getting networks from real controller."""
        networks = await client.get_networks()

        assert isinstance(networks, list)
        assert len(networks) > 0  # Should have at least default network

        network = networks[0]
        assert "name" in network

    @pytest.mark.asyncio
    async def test_get_vouchers(self, client):
        """Test getting vouchers from real controller."""
        vouchers = await client.get_vouchers()

        assert isinstance(vouchers, list)
        # May be empty if no vouchers exist

    @pytest.mark.asyncio
    async def test_get_daily_stats(self, client):
        """Test getting daily stats from real controller."""
        stats = await client.get_daily_stats(days=7)

        assert isinstance(stats, list)
        if stats:
            stat = stats[0]
            assert "time" in stat

    @pytest.mark.asyncio
    async def test_get_hourly_stats(self, client):
        """Test getting hourly stats from real controller."""
        stats = await client.get_hourly_stats(hours=24)

        assert isinstance(stats, list)
        if stats:
            stat = stats[0]
            assert "time" in stat

    @pytest.mark.asyncio
    async def test_get_firewall_rules(self, client):
        """Test getting firewall rules from real controller."""
        rules = await client.get_firewall_rules()

        assert isinstance(rules, list)
        # May be empty if no custom rules

    @pytest.mark.asyncio
    async def test_get_port_forwards(self, client):
        """Test getting port forwards from real controller."""
        forwards = await client.get_port_forwards()

        assert isinstance(forwards, list)
        # May be empty if no port forwards configured


@pytest.mark.integration
class TestLocalControllerReadOnlyActions:
    """Integration tests for read-only controller actions."""

    @pytest.fixture
    def client(self, integration_env_vars):
        """Create a real Local Controller client."""
        return UniFiLocalClient()

    @pytest.mark.asyncio
    async def test_get_site_dpi(self, client):
        """Test getting site DPI stats."""
        dpi = await client.get_site_dpi()

        assert isinstance(dpi, list)
        # May be empty if DPI not enabled

    @pytest.mark.asyncio
    async def test_get_alarms(self, client):
        """Test getting alarms."""
        alarms = await client.get_alarms()

        assert isinstance(alarms, list)
        # May be empty if no alarms
