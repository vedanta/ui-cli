"""Integration tests for Site Manager API (require real API credentials)."""

import pytest

from ui_cli.client import UniFiClient


@pytest.mark.integration
class TestSiteManagerAPIIntegration:
    """Integration tests for Site Manager API."""

    @pytest.fixture
    def client(self, integration_env_vars):
        """Create a real API client."""
        return UniFiClient()

    @pytest.mark.asyncio
    async def test_list_hosts(self, client):
        """Test listing hosts from real API."""
        hosts = await client.list_hosts()

        assert isinstance(hosts, list)
        if hosts:
            host = hosts[0]
            assert "id" in host
            assert "reportedState" in host

    @pytest.mark.asyncio
    async def test_list_sites(self, client):
        """Test listing sites from real API."""
        sites = await client.list_sites()

        assert isinstance(sites, list)
        if sites:
            site = sites[0]
            assert "siteId" in site or "siteName" in site

    @pytest.mark.asyncio
    async def test_list_devices(self, client):
        """Test listing devices from real API."""
        devices = await client.list_devices()

        assert isinstance(devices, list)
        if devices:
            device = devices[0]
            # Check for common device fields
            assert "id" in device or "mac" in device

    @pytest.mark.asyncio
    async def test_get_single_host(self, client):
        """Test getting a single host from real API."""
        hosts = await client.list_hosts()

        if hosts:
            host_id = hosts[0]["id"]
            host = await client.get_host(host_id)

            assert host is not None
            assert host["id"] == host_id
