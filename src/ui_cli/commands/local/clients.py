"""Client commands for local controller."""

import asyncio
from typing import Annotated

import typer

from ui_cli.local_client import (
    LocalAPIError,
    LocalAuthenticationError,
    LocalConnectionError,
    UniFiLocalClient,
)
from ui_cli.output import OutputFormat, console, output_count_table, output_csv, output_json, output_table

app = typer.Typer(help="Manage connected clients")


# Column definitions for client output: (key, header)
CLIENT_COLUMNS = [
    ("name", "Name"),
    ("mac", "MAC"),
    ("ip", "IP"),
    ("network", "Network"),
    ("type", "Type"),
    ("signal", "Signal"),
    ("satisfaction", "Experience"),
]

CLIENT_COLUMNS_VERBOSE = [
    ("name", "Name"),
    ("mac", "MAC"),
    ("ip", "IP"),
    ("network", "Network"),
    ("type", "Type"),
    ("oui", "Vendor"),
    ("signal", "Signal"),
    ("satisfaction", "Experience"),
    ("tx_rate", "TX Rate"),
    ("rx_rate", "RX Rate"),
    ("uptime", "Uptime"),
]


def format_client(client: dict, verbose: bool = False) -> dict:
    """Format raw client data for display."""
    # Determine connection type
    is_wired = client.get("is_wired", False)
    conn_type = "Wired" if is_wired else "Wireless"

    # Get network name
    network = client.get("network", client.get("essid", ""))

    # Format signal strength (wireless only)
    signal = ""
    if not is_wired:
        rssi = client.get("rssi")
        if rssi is not None:
            signal = f"{rssi} dBm"

    # Format experience/satisfaction score
    satisfaction = client.get("satisfaction")
    if satisfaction is not None:
        satisfaction = f"{satisfaction}%"
    else:
        satisfaction = ""

    # Format uptime
    uptime_seconds = client.get("uptime", 0)
    if uptime_seconds:
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        uptime = f"{int(hours)}h {int(minutes)}m"
    else:
        uptime = ""

    # Format rates (in Mbps)
    tx_rate = client.get("tx_rate", 0)
    rx_rate = client.get("rx_rate", 0)
    tx_rate_str = f"{tx_rate / 1000:.0f} Mbps" if tx_rate else ""
    rx_rate_str = f"{rx_rate / 1000:.0f} Mbps" if rx_rate else ""

    result = {
        "name": client.get("name") or client.get("hostname") or "(unknown)",
        "mac": client.get("mac", "").upper(),
        "ip": client.get("ip", ""),
        "network": network,
        "type": conn_type,
        "oui": client.get("oui", ""),
        "signal": signal,
        "satisfaction": satisfaction,
        "tx_rate": tx_rate_str,
        "rx_rate": rx_rate_str,
        "uptime": uptime,
    }

    return result


def handle_error(e: Exception) -> None:
    """Handle and display API errors."""
    if isinstance(e, LocalAuthenticationError):
        console.print(f"[red]Authentication error:[/red] {e.message}")
    elif isinstance(e, LocalConnectionError):
        console.print(f"[red]Connection error:[/red] {e.message}")
    elif isinstance(e, LocalAPIError):
        console.print(f"[red]API error:[/red] {e.message}")
    else:
        console.print(f"[red]Error:[/red] {e}")
    raise typer.Exit(1)


def is_mac_address(value: str) -> bool:
    """Check if a string looks like a MAC address."""
    # MAC formats: AA:BB:CC:DD:EE:FF or AA-BB-CC-DD-EE-FF or AABBCCDDEEFF
    import re
    mac_patterns = [
        r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$',  # AA:BB:CC:DD:EE:FF
        r'^([0-9A-Fa-f]{2}-){5}[0-9A-Fa-f]{2}$',  # AA-BB-CC-DD-EE-FF
        r'^[0-9A-Fa-f]{12}$',                       # AABBCCDDEEFF
    ]
    return any(re.match(pattern, value) for pattern in mac_patterns)


async def resolve_client_identifier(
    api_client: UniFiLocalClient,
    identifier: str,
) -> tuple[str | None, str | None]:
    """Resolve a client name or MAC to (mac, name).

    Returns (mac, name) if found, (None, None) if not found.
    If identifier is a MAC, returns it directly with the name if found.
    If identifier is a name, searches for matching client.
    """
    if is_mac_address(identifier):
        # It's a MAC address - try to get the client to find its name
        client_data = await api_client.get_client(identifier)
        if client_data:
            name = client_data.get("name") or client_data.get("hostname") or identifier
            return identifier.lower().replace("-", ":"), name
        return identifier.lower().replace("-", ":"), None

    # It's a name - search for it in all clients
    clients = await api_client.list_all_clients()
    identifier_lower = identifier.lower()

    for client in clients:
        name = client.get("name") or client.get("hostname") or ""
        if name.lower() == identifier_lower:
            return client.get("mac", "").lower(), name

    # Try partial match if exact match not found
    matches = []
    for client in clients:
        name = client.get("name") or client.get("hostname") or ""
        if identifier_lower in name.lower():
            matches.append((client.get("mac", "").lower(), name))

    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        console.print(f"[yellow]Multiple clients match '{identifier}':[/yellow]")
        for mac, name in matches:
            console.print(f"  - {name} ({mac.upper()})")
        return None, None

    return None, None


@app.command("list")
def list_clients(
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
    network: Annotated[
        str | None,
        typer.Option("--network", "-n", help="Filter by network/SSID"),
    ] = None,
    wired: Annotated[
        bool,
        typer.Option("--wired", "-w", help="Show only wired clients"),
    ] = False,
    wireless: Annotated[
        bool,
        typer.Option("--wireless", "-W", help="Show only wireless clients"),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Show additional details"),
    ] = False,
) -> None:
    """List active (connected) clients."""
    try:
        client = UniFiLocalClient()
        clients = asyncio.run(client.list_clients())
    except Exception as e:
        handle_error(e)
        return

    # Apply filters
    if wired:
        clients = [c for c in clients if c.get("is_wired", False)]
    elif wireless:
        clients = [c for c in clients if not c.get("is_wired", False)]

    if network:
        network_lower = network.lower()
        clients = [
            c
            for c in clients
            if network_lower in (c.get("network", "") or c.get("essid", "")).lower()
        ]

    # Format for output
    formatted = [format_client(c, verbose=verbose) for c in clients]

    columns = CLIENT_COLUMNS_VERBOSE if verbose else CLIENT_COLUMNS

    if output == OutputFormat.JSON:
        output_json(formatted, verbose=verbose)
    elif output == OutputFormat.CSV:
        output_csv(formatted, columns)
    else:
        output_table(formatted, columns, title="Connected Clients")


@app.command("all")
def list_all_clients(
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Show additional details"),
    ] = False,
) -> None:
    """List all known clients (including offline)."""
    try:
        client = UniFiLocalClient()
        clients = asyncio.run(client.list_all_clients())
    except Exception as e:
        handle_error(e)
        return

    # Format for output
    formatted = [format_client(c, verbose=verbose) for c in clients]

    columns = CLIENT_COLUMNS_VERBOSE if verbose else CLIENT_COLUMNS

    if output == OutputFormat.JSON:
        output_json(formatted, verbose=verbose)
    elif output == OutputFormat.CSV:
        output_csv(formatted, columns)
    else:
        output_table(formatted, columns, title="All Known Clients")


@app.command("get")
def get_client(
    identifier: Annotated[
        str | None,
        typer.Argument(help="Client MAC address or name"),
    ] = None,
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
) -> None:
    """Get details for a specific client.

    Examples:
        ./ui lo clients get my-iPhone
        ./ui lo clients get AA:BB:CC:DD:EE:FF
    """
    if not identifier:
        console.print("[yellow]Usage:[/yellow] ./ui lo clients get <name or MAC>")
        console.print()
        console.print("Examples:")
        console.print("  ./ui lo clients get my-iPhone")
        console.print("  ./ui lo clients get AA:BB:CC:DD:EE:FF")
        raise typer.Exit(1)
    try:
        api_client = UniFiLocalClient()

        async def _get():
            mac, name = await resolve_client_identifier(api_client, identifier)
            if not mac:
                return None, None
            client_data = await api_client.get_client(mac)
            return client_data, name

        client_data, resolved_name = asyncio.run(_get())
    except Exception as e:
        handle_error(e)
        return

    if not client_data:
        console.print(f"[yellow]Client not found:[/yellow] {identifier}")
        raise typer.Exit(1)

    if output == OutputFormat.JSON:
        output_json(client_data)
    else:
        # Display as key-value pairs
        formatted = format_client(client_data, verbose=True)
        display_name = resolved_name or formatted.get("name", identifier)
        console.print()
        console.print(f"[bold]Client Details: {display_name}[/bold]")
        console.print("─" * 40)
        for key, value in formatted.items():
            if value:
                console.print(f"  [dim]{key}:[/dim] {value}")
        console.print()


@app.command("status")
def client_status(
    identifier: Annotated[
        str | None,
        typer.Argument(help="Client MAC address or name"),
    ] = None,
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
) -> None:
    """Show client connection and block status.

    Examples:
        ./ui lo clients status my-iPhone
        ./ui lo clients status AA:BB:CC:DD:EE:FF
    """
    if not identifier:
        console.print("[yellow]Usage:[/yellow] ./ui lo clients status <name or MAC>")
        console.print()
        console.print("Examples:")
        console.print("  ./ui lo clients status my-iPhone")
        console.print("  ./ui lo clients status AA:BB:CC:DD:EE:FF")
        raise typer.Exit(1)

    try:
        api_client = UniFiLocalClient()

        async def _get_status():
            mac, name = await resolve_client_identifier(api_client, identifier)
            if not mac:
                return None, None, None, None
            # Get from all clients (includes offline) for block status
            all_clients = await api_client.list_all_clients()
            client_info = None
            for c in all_clients:
                if c.get("mac", "").lower() == mac.lower():
                    client_info = c
                    break
            # Also check active clients for online status and live data
            active_clients = await api_client.list_clients()
            active_info = None
            for c in active_clients:
                if c.get("mac", "").lower() == mac.lower():
                    active_info = c
                    break
            is_online = active_info is not None
            return client_info, active_info, name, is_online

        client_info, active_info, resolved_name, is_online = asyncio.run(_get_status())
    except Exception as e:
        handle_error(e)
        return

    if not client_info:
        console.print(f"[yellow]Client not found:[/yellow] {identifier}")
        raise typer.Exit(1)

    # Build status info - use active_info for live data if online
    info = active_info if active_info else client_info

    name = resolved_name or info.get("name") or info.get("hostname") or "(unknown)"
    mac = info.get("mac", "").upper()
    is_blocked = client_info.get("blocked", False)
    is_guest = info.get("is_guest", False)
    ip = info.get("ip") or info.get("last_ip") or ""
    is_wired = info.get("is_wired", False)
    conn_type = "Wired" if is_wired else "Wireless"

    # Network and AP info
    network = info.get("network") or info.get("essid") or info.get("last_connection_network_name") or ""
    ap_name = info.get("last_uplink_name") or ""

    status_data = {
        "name": name,
        "mac": mac,
        "ip": ip,
        "online": is_online,
        "blocked": is_blocked,
        "guest": is_guest,
        "type": conn_type,
        "network": network,
        "ap": ap_name if not is_wired else None,
    }

    if output == OutputFormat.JSON:
        output_json(status_data)
    else:
        console.print()
        console.print(f"[bold]Client Status: {name}[/bold]")
        console.print("─" * 40)
        console.print(f"  [dim]MAC:[/dim]      {mac}")
        if ip:
            console.print(f"  [dim]IP:[/dim]       {ip}")
        console.print(f"  [dim]Type:[/dim]     {conn_type}")
        if network:
            console.print(f"  [dim]Network:[/dim]  {network}")
        if ap_name and not is_wired:
            console.print(f"  [dim]AP:[/dim]       {ap_name}")

        # Online status
        if is_online:
            console.print(f"  [dim]Online:[/dim]   [green]Yes[/green]")
        else:
            console.print(f"  [dim]Online:[/dim]   [dim]No[/dim]")

        # Block status
        if is_blocked:
            console.print(f"  [dim]Blocked:[/dim]  [red]Yes[/red]")
        else:
            console.print(f"  [dim]Blocked:[/dim]  [green]No[/green]")

        # Guest status
        if is_guest:
            console.print(f"  [dim]Guest:[/dim]    Yes")

        console.print()


@app.command("block")
def block_client(
    identifier: Annotated[
        str | None,
        typer.Argument(help="Client MAC address or name"),
    ] = None,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation prompt"),
    ] = False,
) -> None:
    """Block a client from connecting.

    Examples:
        ./ui lo clients block my-iPhone
        ./ui lo clients block AA:BB:CC:DD:EE:FF -y
    """
    if not identifier:
        console.print("[yellow]Usage:[/yellow] ./ui lo clients block <name or MAC>")
        console.print()
        console.print("Examples:")
        console.print("  ./ui lo clients block my-iPhone")
        console.print("  ./ui lo clients block AA:BB:CC:DD:EE:FF -y")
        raise typer.Exit(1)

    api_client = UniFiLocalClient()

    # Resolve identifier to MAC
    try:
        mac, name = asyncio.run(resolve_client_identifier(api_client, identifier))
    except Exception as e:
        handle_error(e)
        return

    if not mac:
        console.print(f"[yellow]Client not found:[/yellow] {identifier}")
        raise typer.Exit(1)

    display = f"{name} ({mac.upper()})" if name else mac.upper()

    # Confirm action
    if not yes:
        if not typer.confirm(f"Block client {display}?"):
            console.print("[dim]Cancelled[/dim]")
            raise typer.Exit(0)

    # Execute action
    try:
        success = asyncio.run(api_client.block_client(mac))
    except Exception as e:
        handle_error(e)
        return

    if success:
        console.print(f"[green]Blocked client:[/green] {display}")
    else:
        console.print(f"[red]Failed to block client:[/red] {display}")
        raise typer.Exit(1)


@app.command("unblock")
def unblock_client(
    identifier: Annotated[
        str | None,
        typer.Argument(help="Client MAC address or name"),
    ] = None,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation prompt"),
    ] = False,
) -> None:
    """Unblock a previously blocked client.

    Examples:
        ./ui lo clients unblock my-iPhone
        ./ui lo clients unblock AA:BB:CC:DD:EE:FF -y
    """
    if not identifier:
        console.print("[yellow]Usage:[/yellow] ./ui lo clients unblock <name or MAC>")
        console.print()
        console.print("Examples:")
        console.print("  ./ui lo clients unblock my-iPhone")
        console.print("  ./ui lo clients unblock AA:BB:CC:DD:EE:FF -y")
        raise typer.Exit(1)

    api_client = UniFiLocalClient()

    # Resolve identifier to MAC
    try:
        mac, name = asyncio.run(resolve_client_identifier(api_client, identifier))
    except Exception as e:
        handle_error(e)
        return

    if not mac:
        console.print(f"[yellow]Client not found:[/yellow] {identifier}")
        raise typer.Exit(1)

    display = f"{name} ({mac.upper()})" if name else mac.upper()

    # Confirm action
    if not yes:
        if not typer.confirm(f"Unblock client {display}?"):
            console.print("[dim]Cancelled[/dim]")
            raise typer.Exit(0)

    # Execute action
    try:
        success = asyncio.run(api_client.unblock_client(mac))
    except Exception as e:
        handle_error(e)
        return

    if success:
        console.print(f"[green]Unblocked client:[/green] {display}")
    else:
        console.print(f"[red]Failed to unblock client:[/red] {display}")
        raise typer.Exit(1)


@app.command("kick")
def kick_client(
    identifier: Annotated[
        str | None,
        typer.Argument(help="Client MAC address or name"),
    ] = None,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation prompt"),
    ] = False,
) -> None:
    """Kick (disconnect) a client, forcing reconnection.

    Examples:
        ./ui lo clients kick my-iPhone
        ./ui lo clients kick AA:BB:CC:DD:EE:FF -y
    """
    if not identifier:
        console.print("[yellow]Usage:[/yellow] ./ui lo clients kick <name or MAC>")
        console.print()
        console.print("Examples:")
        console.print("  ./ui lo clients kick my-iPhone")
        console.print("  ./ui lo clients kick AA:BB:CC:DD:EE:FF -y")
        raise typer.Exit(1)

    api_client = UniFiLocalClient()

    # Resolve identifier to MAC
    try:
        mac, name = asyncio.run(resolve_client_identifier(api_client, identifier))
    except Exception as e:
        handle_error(e)
        return

    if not mac:
        console.print(f"[yellow]Client not found:[/yellow] {identifier}")
        raise typer.Exit(1)

    display = f"{name} ({mac.upper()})" if name else mac.upper()

    # Confirm action
    if not yes:
        if not typer.confirm(f"Kick client {display}?"):
            console.print("[dim]Cancelled[/dim]")
            raise typer.Exit(0)

    # Execute action
    try:
        success = asyncio.run(api_client.kick_client(mac))
    except Exception as e:
        handle_error(e)
        return

    if success:
        console.print(f"[green]Kicked client:[/green] {display}")
    else:
        console.print(f"[red]Failed to kick client:[/red] {display}")
        raise typer.Exit(1)


class CountBy(str, typer.Typer):
    """Grouping options for count command."""

    TYPE = "type"
    NETWORK = "network"
    VENDOR = "vendor"
    AP = "ap"
    EXPERIENCE = "experience"


def get_experience_category(satisfaction: int | None) -> str:
    """Categorize experience score."""
    if satisfaction is None:
        return "Unknown"
    if satisfaction >= 80:
        return "Good (80%+)"
    if satisfaction >= 50:
        return "Fair (50-79%)"
    return "Poor (<50%)"


@app.command("count")
def count_clients(
    by: Annotated[
        str,
        typer.Option(
            "--by",
            "-b",
            help="Group by: type, network, vendor, ap, experience",
        ),
    ] = "type",
    include_offline: Annotated[
        bool,
        typer.Option(
            "--include-offline",
            "-a",
            help="Include offline clients in count",
        ),
    ] = False,
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
) -> None:
    """Count clients grouped by category (online only by default)."""
    try:
        api_client = UniFiLocalClient()
        if include_offline:
            clients = asyncio.run(api_client.list_all_clients())
        else:
            clients = asyncio.run(api_client.list_clients())
    except Exception as e:
        handle_error(e)
        return

    # Count by the specified grouping
    counts: dict[str, int] = {}
    by_lower = by.lower()

    for client in clients:
        if by_lower == "type":
            key = "Wired" if client.get("is_wired", False) else "Wireless"
        elif by_lower == "network":
            key = client.get("network") or client.get("essid") or "(none)"
        elif by_lower == "vendor":
            key = client.get("oui") or "(unknown)"
        elif by_lower == "ap":
            # Get AP name - wireless clients have ap_mac and last_uplink_name
            if client.get("is_wired", False):
                key = "(wired)"
            else:
                key = client.get("last_uplink_name") or client.get("ap_mac", "(unknown)")
        elif by_lower == "experience":
            satisfaction = client.get("satisfaction")
            key = get_experience_category(satisfaction)
        else:
            console.print(f"[red]Invalid grouping:[/red] {by}")
            console.print("Valid options: type, network, vendor, ap, experience")
            raise typer.Exit(1)

        counts[key] = counts.get(key, 0) + 1

    # Determine title and headers based on grouping
    titles = {
        "type": ("Client Count by Type", "Type"),
        "network": ("Client Count by Network", "Network"),
        "vendor": ("Client Count by Vendor", "Vendor"),
        "ap": ("Client Count by Access Point", "Access Point"),
        "experience": ("Client Count by Experience", "Experience"),
    }
    title, group_header = titles.get(by_lower, ("Client Count", "Group"))

    if output == OutputFormat.JSON:
        output_json({"counts": counts, "total": sum(counts.values())})
    elif output == OutputFormat.CSV:
        # Output as CSV
        rows = [{"group": k, "count": v} for k, v in sorted(counts.items())]
        rows.append({"group": "Total", "count": sum(counts.values())})
        output_csv(rows, [("group", group_header), ("count", "Count")])
    else:
        output_count_table(counts, group_header=group_header, title=title)
