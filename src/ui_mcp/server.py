"""UI-CLI MCP Server.

FastMCP server that exposes UniFi management tools to Claude Desktop.
"""

import json
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from mcp.server.fastmcp import FastMCP

from ui_cli.client import UniFiClient, AuthenticationError, APIError
from ui_cli.local_client import (
    UniFiLocalClient,
    LocalAuthenticationError,
    LocalAPIError,
    LocalConnectionError,
)

from ui_mcp.helpers import resolve_client_mac, resolve_device_mac

# Initialize FastMCP server
# structured_output=False forces text-only output which displays better in Claude Desktop
# See: https://github.com/anthropics/claude-code/issues/9962
server = FastMCP(
    "ui-cli",
    instructions="Manage UniFi infrastructure - controllers, devices, clients, and networks",
)

# Lazy client initialization
_cloud_client: UniFiClient | None = None
_local_client: UniFiLocalClient | None = None


def get_cloud_client() -> UniFiClient:
    """Get or create Cloud API client."""
    global _cloud_client
    if _cloud_client is None:
        _cloud_client = UniFiClient()
    return _cloud_client


def get_local_client() -> UniFiLocalClient:
    """Get or create Local Controller client."""
    global _local_client
    if _local_client is None:
        _local_client = UniFiLocalClient()
    return _local_client


# =============================================================================
# Cloud API Tools
# =============================================================================


@server.tool()
async def unifi_status() -> str:
    """Check UniFi Cloud API connection status.

    Returns connection status and account information.
    """
    try:
        client = get_cloud_client()
        hosts = await client.list_hosts()
        return json.dumps({
            "status": "connected",
            "api": "cloud",
            "hosts_count": len(hosts),
            "message": f"Connected to UniFi Cloud API with {len(hosts)} controller(s)",
        }, indent=2)
    except AuthenticationError as e:
        return json.dumps({"status": "error", "error": "authentication_failed", "message": str(e)}, indent=2)
    except APIError as e:
        return json.dumps({"status": "error", "error": "api_error", "message": str(e)}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "error": "unknown", "message": str(e)}, indent=2)


@server.tool()
async def unifi_list_hosts() -> str:
    """List all UniFi controllers (hosts) associated with the account.

    Returns a list of controllers with their IDs, names, and status.
    """
    try:
        client = get_cloud_client()
        hosts = await client.list_hosts()
        return json.dumps({"hosts": hosts, "count": len(hosts)}, indent=2)
    except AuthenticationError as e:
        return json.dumps({"error": "authentication_failed", "message": str(e)}, indent=2)
    except APIError as e:
        return json.dumps({"error": "api_error", "message": str(e)}, indent=2)


@server.tool()
async def unifi_list_sites() -> str:
    """List all UniFi sites.

    Returns a list of sites with their IDs and names.
    """
    try:
        client = get_cloud_client()
        sites = await client.list_sites()
        return json.dumps({"sites": sites, "count": len(sites)}, indent=2)
    except AuthenticationError as e:
        return json.dumps({"error": "authentication_failed", "message": str(e)}, indent=2)
    except APIError as e:
        return json.dumps({"error": "api_error", "message": str(e)}, indent=2)


@server.tool()
async def unifi_list_devices(host_id: str | None = None) -> str:
    """List all UniFi devices across controllers.

    Args:
        host_id: Optional controller ID to filter devices by specific host

    Returns a list of devices with model, status, IP, and firmware info.
    """
    try:
        client = get_cloud_client()
        host_ids = [host_id] if host_id else None
        devices = await client.list_devices(host_ids=host_ids)
        return json.dumps({"devices": devices, "count": len(devices)}, indent=2)
    except AuthenticationError as e:
        return json.dumps({"error": "authentication_failed", "message": str(e)}, indent=2)
    except APIError as e:
        return json.dumps({"error": "api_error", "message": str(e)}, indent=2)


@server.tool()
async def unifi_isp_metrics(
    interval: str = "1h",
    hours: int = 168,
) -> str:
    """Get ISP performance metrics (latency, speeds, uptime).

    Args:
        interval: Data interval - '5m' (last 24h only) or '1h' (default, up to 30 days)
        hours: Hours of data to retrieve (default: 168 = 7 days)

    Returns ISP metrics including latency, download/upload speeds, and uptime.
    """
    try:
        client = get_cloud_client()
        metrics = await client.get_isp_metrics(metric_type=interval, duration_hours=hours)
        return json.dumps({"metrics": metrics, "count": len(metrics), "interval": interval, "hours": hours}, indent=2)
    except AuthenticationError as e:
        return json.dumps({"error": "authentication_failed", "message": str(e)}, indent=2)
    except APIError as e:
        return json.dumps({"error": "api_error", "message": str(e)}, indent=2)


# =============================================================================
# Local Controller Tools - Clients
# =============================================================================


# DISABLED: Response too large for Claude Desktop
# @server.tool()
# async def unifi_lo_list_clients(
#     filter: str | None = None,
#     limit: int = 20,
# ) -> str:
#     """List connected clients on the local UniFi controller.
#
#     Args:
#         filter: Optional filter - 'wired', 'wireless', or a network/SSID name
#         limit: Max clients to return in detail (default: 20, use 0 for all)
#
#     Returns connected clients with IP, MAC, hostname, and connection details.
#     """
#     try:
#         client = get_local_client()
#         clients = await client.list_clients()
#
#         if filter:
#             filter_lower = filter.lower()
#             if filter_lower == "wired":
#                 clients = [c for c in clients if c.get("is_wired")]
#             elif filter_lower == "wireless":
#                 clients = [c for c in clients if not c.get("is_wired")]
#             else:
#                 # Filter by network/SSID name
#                 clients = [
#                     c for c in clients
#                     if filter_lower in c.get("network", "").lower()
#                     or filter_lower in c.get("essid", "").lower()
#                 ]
#
#         # Build summary for Claude to use in response
#         wired_count = sum(1 for c in clients if c.get("is_wired"))
#         wireless_count = len(clients) - wired_count
#         total_count = len(clients)
#
#         # Create compact client list (just key fields)
#         compact_clients = []
#         for c in clients:
#             compact_clients.append({
#                 "name": c.get("name") or c.get("hostname") or c.get("mac", "unknown"),
#                 "ip": c.get("ip", "N/A"),
#                 "mac": c.get("mac", ""),
#                 "type": "wired" if c.get("is_wired") else "wireless",
#                 "network": c.get("network") or c.get("essid", ""),
#             })
#
#         # Apply limit (0 means no limit)
#         if limit > 0 and len(compact_clients) > limit:
#             returned_clients = compact_clients[:limit]
#             truncated = True
#         else:
#             returned_clients = compact_clients
#             truncated = False
#
#         summary = f"Found {total_count} connected client(s): {wired_count} wired, {wireless_count} wireless."
#         if filter:
#             summary += f" (filtered by: {filter})"
#         if truncated:
#             summary += f" Showing first {limit} of {total_count}. Use limit=0 for all."
#
#         return json.dumps({
#             "summary": summary,
#             "total_count": total_count,
#             "returned_count": len(returned_clients),
#             "wired_count": wired_count,
#             "wireless_count": wireless_count,
#             "filter": filter,
#             "truncated": truncated,
#             "clients": returned_clients,
#         }, indent=2)
#     except LocalAuthenticationError as e:
#         return json.dumps({"error": "authentication_failed", "message": str(e)}, indent=2)
#     except LocalConnectionError as e:
#         return json.dumps({"error": "connection_failed", "message": str(e)}, indent=2)
#     except LocalAPIError as e:
#         return json.dumps({"error": "api_error", "message": str(e)}, indent=2)


@server.tool()
async def unifi_lo_all_clients(limit: int = 20) -> str:
    """List all known clients including offline ones.

    Args:
        limit: Max clients to return (default: 20, use 0 for all)

    Returns all clients that have ever connected, with their last seen time.
    """
    try:
        client = get_local_client()
        clients = await client.list_all_clients()
        total_count = len(clients)

        # Create compact client list
        compact_clients = []
        for c in clients:
            compact_clients.append({
                "name": c.get("name") or c.get("hostname") or c.get("mac", "unknown"),
                "mac": c.get("mac", ""),
                "last_seen": c.get("last_seen", ""),
                "is_online": c.get("is_online", False),
            })

        # Apply limit
        if limit > 0 and len(compact_clients) > limit:
            returned_clients = compact_clients[:limit]
            truncated = True
        else:
            returned_clients = compact_clients
            truncated = False

        online_count = sum(1 for c in compact_clients if c.get("is_online"))
        summary = f"Found {total_count} known client(s): {online_count} online, {total_count - online_count} offline."
        if truncated:
            summary += f" Showing first {limit}. Use limit=0 for all."

        return json.dumps({
            "summary": summary,
            "total_count": total_count,
            "returned_count": len(returned_clients),
            "truncated": truncated,
            "clients": returned_clients,
        }, indent=2)
    except LocalAuthenticationError as e:
        return json.dumps({"error": "authentication_failed", "message": str(e)}, indent=2)
    except LocalConnectionError as e:
        return json.dumps({"error": "connection_failed", "message": str(e)}, indent=2)
    except LocalAPIError as e:
        return json.dumps({"error": "api_error", "message": str(e)}, indent=2)


@server.tool()
async def unifi_lo_get_client(identifier: str) -> str:
    """Get detailed information about a specific client.

    Args:
        identifier: Client name, hostname, or MAC address

    Returns detailed client info including IP, signal strength, traffic stats.
    """
    try:
        client = get_local_client()
        mac = await resolve_client_mac(client, identifier)
        client_data = await client.get_client(mac)
        if client_data:
            return json.dumps({"client": client_data, "found": True}, indent=2)
        return json.dumps({"found": False, "message": f"Client {identifier} not found"}, indent=2)
    except ValueError as e:
        return json.dumps({"error": "not_found", "message": str(e)}, indent=2)
    except LocalAuthenticationError as e:
        return json.dumps({"error": "authentication_failed", "message": str(e)}, indent=2)
    except LocalConnectionError as e:
        return json.dumps({"error": "connection_failed", "message": str(e)}, indent=2)
    except LocalAPIError as e:
        return json.dumps({"error": "api_error", "message": str(e)}, indent=2)


@server.tool()
async def unifi_lo_block_client(identifier: str) -> str:
    """Block a client from the network.

    Args:
        identifier: Client name, hostname, or MAC address to block

    Blocked clients cannot connect to the network until unblocked.
    """
    try:
        client = get_local_client()
        mac = await resolve_client_mac(client, identifier)
        success = await client.block_client(mac)
        return json.dumps({
            "success": success,
            "action": "blocked",
            "identifier": identifier,
            "mac": mac,
        }, indent=2)
    except ValueError as e:
        return json.dumps({"error": "not_found", "message": str(e)}, indent=2)
    except LocalAuthenticationError as e:
        return json.dumps({"error": "authentication_failed", "message": str(e)}, indent=2)
    except LocalConnectionError as e:
        return json.dumps({"error": "connection_failed", "message": str(e)}, indent=2)
    except LocalAPIError as e:
        return json.dumps({"error": "api_error", "message": str(e)}, indent=2)


@server.tool()
async def unifi_lo_unblock_client(identifier: str) -> str:
    """Unblock a previously blocked client.

    Args:
        identifier: Client name, hostname, or MAC address to unblock
    """
    try:
        client = get_local_client()
        mac = await resolve_client_mac(client, identifier)
        success = await client.unblock_client(mac)
        return json.dumps({
            "success": success,
            "action": "unblocked",
            "identifier": identifier,
            "mac": mac,
        }, indent=2)
    except ValueError as e:
        return json.dumps({"error": "not_found", "message": str(e)}, indent=2)
    except LocalAuthenticationError as e:
        return json.dumps({"error": "authentication_failed", "message": str(e)}, indent=2)
    except LocalConnectionError as e:
        return json.dumps({"error": "connection_failed", "message": str(e)}, indent=2)
    except LocalAPIError as e:
        return json.dumps({"error": "api_error", "message": str(e)}, indent=2)


@server.tool()
async def unifi_lo_kick_client(identifier: str) -> str:
    """Disconnect (kick) a client from the network.

    Args:
        identifier: Client name, hostname, or MAC address to disconnect

    The client will be disconnected but can reconnect immediately.
    """
    try:
        client = get_local_client()
        mac = await resolve_client_mac(client, identifier)
        success = await client.kick_client(mac)
        return json.dumps({
            "success": success,
            "action": "kicked",
            "identifier": identifier,
            "mac": mac,
        }, indent=2)
    except ValueError as e:
        return json.dumps({"error": "not_found", "message": str(e)}, indent=2)
    except LocalAuthenticationError as e:
        return json.dumps({"error": "authentication_failed", "message": str(e)}, indent=2)
    except LocalConnectionError as e:
        return json.dumps({"error": "connection_failed", "message": str(e)}, indent=2)
    except LocalAPIError as e:
        return json.dumps({"error": "api_error", "message": str(e)}, indent=2)


# =============================================================================
# Local Controller Tools - Devices
# =============================================================================


@server.tool()
async def unifi_lo_list_devices() -> str:
    """List all network devices (APs, switches, gateways) on the controller.

    Returns devices with model, IP, firmware version, and status.
    """
    try:
        client = get_local_client()
        devices = await client.get_devices()

        # Build summary
        device_types = {}
        for d in devices:
            dtype = d.get("type", "unknown")
            device_types[dtype] = device_types.get(dtype, 0) + 1
        type_summary = ", ".join(f"{v} {k}(s)" for k, v in device_types.items())
        summary = f"Found {len(devices)} device(s): {type_summary}" if devices else "No devices found."

        return json.dumps({"summary": summary, "devices": devices, "count": len(devices)}, indent=2)
    except LocalAuthenticationError as e:
        return json.dumps({"error": "authentication_failed", "message": str(e)}, indent=2)
    except LocalConnectionError as e:
        return json.dumps({"error": "connection_failed", "message": str(e)}, indent=2)
    except LocalAPIError as e:
        return json.dumps({"error": "api_error", "message": str(e)}, indent=2)


@server.tool()
async def unifi_lo_restart_device(identifier: str) -> str:
    """Restart a network device.

    Args:
        identifier: Device name or MAC address

    The device will reboot and be offline for 1-3 minutes.
    """
    try:
        client = get_local_client()
        mac = await resolve_device_mac(client, identifier)
        success = await client.restart_device(mac)
        return json.dumps({
            "success": success,
            "action": "restarting",
            "identifier": identifier,
            "mac": mac,
            "message": "Device will be offline for 1-3 minutes",
        }, indent=2)
    except ValueError as e:
        return json.dumps({"error": "not_found", "message": str(e)}, indent=2)
    except LocalAuthenticationError as e:
        return json.dumps({"error": "authentication_failed", "message": str(e)}, indent=2)
    except LocalConnectionError as e:
        return json.dumps({"error": "connection_failed", "message": str(e)}, indent=2)
    except LocalAPIError as e:
        return json.dumps({"error": "api_error", "message": str(e)}, indent=2)


@server.tool()
async def unifi_lo_locate_device(identifier: str, enabled: bool = True) -> str:
    """Toggle the locate LED on a device for physical identification.

    Args:
        identifier: Device name or MAC address
        enabled: True to turn on locate LED, False to turn off
    """
    try:
        client = get_local_client()
        mac = await resolve_device_mac(client, identifier)
        success = await client.locate_device(mac, enabled=enabled)
        action = "locate_on" if enabled else "locate_off"
        return json.dumps({
            "success": success,
            "action": action,
            "identifier": identifier,
            "mac": mac,
        }, indent=2)
    except ValueError as e:
        return json.dumps({"error": "not_found", "message": str(e)}, indent=2)
    except LocalAuthenticationError as e:
        return json.dumps({"error": "authentication_failed", "message": str(e)}, indent=2)
    except LocalConnectionError as e:
        return json.dumps({"error": "connection_failed", "message": str(e)}, indent=2)
    except LocalAPIError as e:
        return json.dumps({"error": "api_error", "message": str(e)}, indent=2)


@server.tool()
async def unifi_lo_upgrade_device(identifier: str) -> str:
    """Upgrade device firmware to the latest version.

    Args:
        identifier: Device name or MAC address

    The device will download and install firmware, then reboot.
    """
    try:
        client = get_local_client()
        mac = await resolve_device_mac(client, identifier)
        success = await client.upgrade_device(mac)
        return json.dumps({
            "success": success,
            "action": "upgrading",
            "identifier": identifier,
            "mac": mac,
            "message": "Firmware upgrade initiated",
        }, indent=2)
    except ValueError as e:
        return json.dumps({"error": "not_found", "message": str(e)}, indent=2)
    except LocalAuthenticationError as e:
        return json.dumps({"error": "authentication_failed", "message": str(e)}, indent=2)
    except LocalConnectionError as e:
        return json.dumps({"error": "connection_failed", "message": str(e)}, indent=2)
    except LocalAPIError as e:
        return json.dumps({"error": "api_error", "message": str(e)}, indent=2)


# =============================================================================
# Local Controller Tools - Networks & Firewall
# =============================================================================


@server.tool()
async def unifi_lo_list_networks() -> str:
    """List all networks and VLANs configured on the controller.

    Returns networks with VLAN ID, subnet, DHCP settings, and purpose.
    """
    try:
        client = get_local_client()
        networks = await client.get_networks()

        # Build summary
        network_names = [n.get("name", "unnamed") for n in networks]
        summary = f"Found {len(networks)} network(s): {', '.join(network_names)}" if networks else "No networks found."

        return json.dumps({"summary": summary, "networks": networks, "count": len(networks)}, indent=2)
    except LocalAuthenticationError as e:
        return json.dumps({"error": "authentication_failed", "message": str(e)}, indent=2)
    except LocalConnectionError as e:
        return json.dumps({"error": "connection_failed", "message": str(e)}, indent=2)
    except LocalAPIError as e:
        return json.dumps({"error": "api_error", "message": str(e)}, indent=2)


@server.tool()
async def unifi_lo_firewall_rules(ruleset: str | None = None) -> str:
    """List firewall rules.

    Args:
        ruleset: Optional filter by ruleset (e.g., 'WAN_IN', 'WAN_OUT', 'LAN_IN')

    Returns firewall rules with action, protocol, ports, and source/destination.
    """
    try:
        client = get_local_client()
        rules = await client.get_firewall_rules()

        if ruleset:
            rules = [r for r in rules if r.get("ruleset", "").upper() == ruleset.upper()]

        return json.dumps({"rules": rules, "count": len(rules), "ruleset": ruleset}, indent=2)
    except LocalAuthenticationError as e:
        return json.dumps({"error": "authentication_failed", "message": str(e)}, indent=2)
    except LocalConnectionError as e:
        return json.dumps({"error": "connection_failed", "message": str(e)}, indent=2)
    except LocalAPIError as e:
        return json.dumps({"error": "api_error", "message": str(e)}, indent=2)


@server.tool()
async def unifi_lo_port_forwards() -> str:
    """List port forwarding rules.

    Returns port forwards with name, ports, destination IP, and enabled status.
    """
    try:
        client = get_local_client()
        forwards = await client.get_port_forwards()
        return json.dumps({"port_forwards": forwards, "count": len(forwards)}, indent=2)
    except LocalAuthenticationError as e:
        return json.dumps({"error": "authentication_failed", "message": str(e)}, indent=2)
    except LocalConnectionError as e:
        return json.dumps({"error": "connection_failed", "message": str(e)}, indent=2)
    except LocalAPIError as e:
        return json.dumps({"error": "api_error", "message": str(e)}, indent=2)


# =============================================================================
# Local Controller Tools - Monitoring
# =============================================================================


@server.tool()
async def unifi_lo_health() -> str:
    """Get site health summary.

    Returns health status for WAN, LAN, WLAN, and VPN subsystems.
    """
    try:
        client = get_local_client()
        health = await client.get_health()

        # Build summary from health data
        subsystems = []
        for h in health if isinstance(health, list) else []:
            name = h.get("subsystem", "unknown")
            status = h.get("status", "unknown")
            subsystems.append(f"{name}: {status}")
        summary = f"Health status: {', '.join(subsystems)}" if subsystems else "Health data retrieved."

        return json.dumps({"summary": summary, "health": health}, indent=2)
    except LocalAuthenticationError as e:
        return json.dumps({"error": "authentication_failed", "message": str(e)}, indent=2)
    except LocalConnectionError as e:
        return json.dumps({"error": "connection_failed", "message": str(e)}, indent=2)
    except LocalAPIError as e:
        return json.dumps({"error": "api_error", "message": str(e)}, indent=2)


@server.tool()
async def unifi_lo_events(limit: int = 50) -> str:
    """Get recent events from the controller.

    Args:
        limit: Maximum number of events to return (default: 50)

    Returns recent events like client connections, device status changes, etc.
    """
    try:
        client = get_local_client()
        events = await client.get_events(limit=limit)
        return json.dumps({"events": events, "count": len(events)}, indent=2)
    except LocalAuthenticationError as e:
        return json.dumps({"error": "authentication_failed", "message": str(e)}, indent=2)
    except LocalConnectionError as e:
        return json.dumps({"error": "connection_failed", "message": str(e)}, indent=2)
    except LocalAPIError as e:
        return json.dumps({"error": "api_error", "message": str(e)}, indent=2)


@server.tool()
async def unifi_lo_dpi_stats() -> str:
    """Get Deep Packet Inspection (DPI) statistics.

    Returns application-level traffic breakdown by category.
    """
    try:
        client = get_local_client()
        stats = await client.get_site_dpi()
        return json.dumps({"dpi_stats": stats}, indent=2)
    except LocalAuthenticationError as e:
        return json.dumps({"error": "authentication_failed", "message": str(e)}, indent=2)
    except LocalConnectionError as e:
        return json.dumps({"error": "connection_failed", "message": str(e)}, indent=2)
    except LocalAPIError as e:
        return json.dumps({"error": "api_error", "message": str(e)}, indent=2)


@server.tool()
async def unifi_lo_daily_stats(days: int = 30) -> str:
    """Get daily traffic statistics.

    Args:
        days: Number of days of data to retrieve (default: 30)

    Returns daily bandwidth usage and client counts.
    """
    try:
        client = get_local_client()
        stats = await client.get_daily_stats(days=days)
        return json.dumps({"stats": stats, "count": len(stats), "days": days}, indent=2)
    except LocalAuthenticationError as e:
        return json.dumps({"error": "authentication_failed", "message": str(e)}, indent=2)
    except LocalConnectionError as e:
        return json.dumps({"error": "connection_failed", "message": str(e)}, indent=2)
    except LocalAPIError as e:
        return json.dumps({"error": "api_error", "message": str(e)}, indent=2)


# =============================================================================
# Local Controller Tools - Vouchers
# =============================================================================


@server.tool()
async def unifi_lo_list_vouchers() -> str:
    """List all guest vouchers.

    Returns vouchers with code, duration, quota, and usage status.
    """
    try:
        client = get_local_client()
        vouchers = await client.get_vouchers()
        return json.dumps({"vouchers": vouchers, "count": len(vouchers)}, indent=2)
    except LocalAuthenticationError as e:
        return json.dumps({"error": "authentication_failed", "message": str(e)}, indent=2)
    except LocalConnectionError as e:
        return json.dumps({"error": "connection_failed", "message": str(e)}, indent=2)
    except LocalAPIError as e:
        return json.dumps({"error": "api_error", "message": str(e)}, indent=2)


@server.tool()
async def unifi_lo_create_voucher(
    count: int = 1,
    duration_minutes: int = 1440,
    quota_mb: int = 0,
    upload_kbps: int = 0,
    download_kbps: int = 0,
    note: str | None = None,
) -> str:
    """Create guest WiFi voucher(s).

    Args:
        count: Number of vouchers to create (default: 1)
        duration_minutes: Voucher duration in minutes (default: 1440 = 24 hours)
        quota_mb: Data quota in MB, 0 for unlimited (default: 0)
        upload_kbps: Upload speed limit in kbps, 0 for unlimited (default: 0)
        download_kbps: Download speed limit in kbps, 0 for unlimited (default: 0)
        note: Optional note/description for the voucher(s)

    Returns the created voucher codes.
    """
    try:
        client = get_local_client()
        vouchers = await client.create_voucher(
            count=count,
            duration=duration_minutes,
            quota=quota_mb,
            up_limit=upload_kbps,
            down_limit=download_kbps,
            note=note,
        )
        return json.dumps({
            "success": True,
            "vouchers": vouchers,
            "count": len(vouchers),
            "duration_minutes": duration_minutes,
        }, indent=2)
    except LocalAuthenticationError as e:
        return json.dumps({"error": "authentication_failed", "message": str(e)}, indent=2)
    except LocalConnectionError as e:
        return json.dumps({"error": "connection_failed", "message": str(e)}, indent=2)
    except LocalAPIError as e:
        return json.dumps({"error": "api_error", "message": str(e)}, indent=2)


# =============================================================================
# Entry Point
# =============================================================================


def main():
    """Run the MCP server."""
    server.run()


if __name__ == "__main__":
    main()
