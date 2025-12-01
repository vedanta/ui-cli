"""DPI (Deep Packet Inspection) commands for local controller."""

import asyncio
from typing import Annotated, Any

import typer

from ui_cli.local_client import LocalAPIError, UniFiLocalClient
from ui_cli.output import (
    OutputFormat,
    console,
    output_csv,
    output_json,
    print_error,
    print_warning,
)

app = typer.Typer(name="dpi", help="Deep Packet Inspection statistics", no_args_is_help=True)


async def check_dpi_enabled(client: UniFiLocalClient) -> bool:
    """Check if DPI is enabled in site settings."""
    try:
        settings = await client.get_site_settings()
        for setting in settings:
            if setting.get("key") == "dpi":
                return setting.get("dpi_enabled", False)
        return False
    except LocalAPIError:
        # Can't determine, assume it might be enabled
        return True


# DPI category mapping (UniFi uses numeric codes)
DPI_CATEGORIES = {
    0: "Instant Messaging",
    1: "P2P",
    2: "File Transfer",
    3: "Streaming Media",
    4: "Mail & Collaboration",
    5: "VoIP",
    6: "Database",
    7: "Games",
    8: "Network Management",
    9: "Remote Access",
    10: "Bypass Proxies",
    11: "Stock Market",
    12: "Web",
    13: "Security Update",
    14: "E-Commerce",
    15: "Social Network",
    16: "News",
    18: "Business",
    19: "Network Protocol",
    20: "VPN & Tunneling",
    21: "IoT",
}

# Common application names
DPI_APPS = {
    # Streaming
    "youtube": "YouTube",
    "netflix": "Netflix",
    "amazonvideo": "Amazon Video",
    "hulu": "Hulu",
    "twitch": "Twitch",
    "spotify": "Spotify",
    "appletv": "Apple TV+",
    "disneyplus": "Disney+",
    # Social
    "facebook": "Facebook",
    "instagram": "Instagram",
    "twitter": "Twitter/X",
    "tiktok": "TikTok",
    "snapchat": "Snapchat",
    "whatsapp": "WhatsApp",
    "discord": "Discord",
    "telegram": "Telegram",
    # Productivity
    "microsoft": "Microsoft",
    "office365": "Office 365",
    "teams": "MS Teams",
    "zoom": "Zoom",
    "slack": "Slack",
    "dropbox": "Dropbox",
    "gdrive": "Google Drive",
    # Cloud
    "aws": "AWS",
    "azure": "Azure",
    "googlecloud": "Google Cloud",
    "icloud": "iCloud",
    # Other
    "apple": "Apple",
    "google": "Google",
    "amazon": "Amazon",
}


def format_bytes(bytes_val: int | float | None) -> str:
    """Format bytes to human-readable form."""
    if not bytes_val or bytes_val == 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    value = float(bytes_val)

    while value >= 1024 and unit_index < len(units) - 1:
        value /= 1024
        unit_index += 1

    if unit_index == 0:
        return f"{int(value)} {units[unit_index]}"
    return f"{value:.1f} {units[unit_index]}"


def get_category_name(cat_id: int) -> str:
    """Get category name from ID."""
    return DPI_CATEGORIES.get(cat_id, f"Category {cat_id}")


def get_app_name(app_key: str) -> str:
    """Get friendly app name."""
    # Try direct lookup
    key_lower = app_key.lower()
    if key_lower in DPI_APPS:
        return DPI_APPS[key_lower]

    # Check partial matches
    for k, v in DPI_APPS.items():
        if k in key_lower:
            return v

    # Fallback: title case the key
    return app_key.replace("_", " ").title()


def aggregate_dpi_data(dpi_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate DPI data by category or app."""
    aggregated = {}

    for item in dpi_data:
        # Try to get app name or category
        app = item.get("app")
        cat = item.get("cat")

        if app:
            key = f"app_{app}"
            name = get_app_name(str(app))
        elif cat is not None:
            key = f"cat_{cat}"
            name = get_category_name(cat)
        else:
            continue

        if key not in aggregated:
            aggregated[key] = {
                "name": name,
                "rx_bytes": 0,
                "tx_bytes": 0,
                "clients": set(),
            }

        aggregated[key]["rx_bytes"] += item.get("rx_bytes", 0)
        aggregated[key]["tx_bytes"] += item.get("tx_bytes", 0)

        # Track unique clients if available
        mac = item.get("mac")
        if mac:
            aggregated[key]["clients"].add(mac)

    # Convert to list and sort by total bytes
    result = []
    for key, data in aggregated.items():
        result.append({
            "name": data["name"],
            "rx_bytes": data["rx_bytes"],
            "tx_bytes": data["tx_bytes"],
            "total_bytes": data["rx_bytes"] + data["tx_bytes"],
            "client_count": len(data["clients"]),
        })

    result.sort(key=lambda x: x["total_bytes"], reverse=True)
    return result


@app.command("site")
def site_dpi(
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
    limit: Annotated[
        int,
        typer.Option("--limit", "-l", help="Limit number of results"),
    ] = 20,
) -> None:
    """Show site-level DPI statistics."""

    async def _dpi():
        client = UniFiLocalClient()
        dpi_enabled = await check_dpi_enabled(client)
        dpi_data = await client.get_site_dpi()
        return dpi_data, dpi_enabled

    try:
        dpi_data, dpi_enabled = asyncio.run(_dpi())
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    # Aggregate the data
    aggregated = aggregate_dpi_data(dpi_data)[:limit] if dpi_data else []

    if not aggregated:
        if not dpi_enabled:
            print_warning("DPI is not enabled on this controller")
            console.print("[dim]Enable Traffic Identification in Network Settings to use DPI.[/dim]")
        else:
            console.print("[dim]No DPI data collected yet.[/dim]")
        return

    if output == OutputFormat.JSON:
        output_json(aggregated)
    elif output == OutputFormat.CSV:
        columns = [
            ("name", "Application"),
            ("rx_bytes", "Download (bytes)"),
            ("tx_bytes", "Upload (bytes)"),
            ("client_count", "Clients"),
        ]
        output_csv(aggregated, columns)
    else:
        from rich.table import Table

        table = Table(title="Site DPI Statistics", show_header=True, header_style="bold cyan")
        table.add_column("Application")
        table.add_column("Download", justify="right")
        table.add_column("Upload", justify="right")
        table.add_column("Clients", justify="right")

        total_rx = 0
        total_tx = 0

        for item in aggregated:
            rx = item["rx_bytes"]
            tx = item["tx_bytes"]
            total_rx += rx
            total_tx += tx

            table.add_row(
                item["name"],
                format_bytes(rx),
                format_bytes(tx),
                str(item["client_count"]) if item["client_count"] > 0 else "-",
            )

        console.print(table)
        console.print()
        console.print(f"[dim]Total: {format_bytes(total_rx)} down, {format_bytes(total_tx)} up[/dim]")
        console.print()


@app.command("client")
def client_dpi(
    identifier: Annotated[str, typer.Argument(help="Client MAC address or name")],
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
    limit: Annotated[
        int,
        typer.Option("--limit", "-l", help="Limit number of results"),
    ] = 15,
) -> None:
    """Show DPI statistics for a specific client."""

    async def _dpi():
        client = UniFiLocalClient()
        dpi_enabled = await check_dpi_enabled(client)

        # If not a MAC address, try to find by name
        mac = identifier
        if ":" not in identifier and "-" not in identifier:
            # Search for client by name
            clients = await client.list_clients()
            all_clients = await client.list_all_clients()
            all_clients.extend(clients)

            found = None
            for c in all_clients:
                name = c.get("name", c.get("hostname", ""))
                if name.lower() == identifier.lower():
                    found = c
                    break
                if identifier.lower() in name.lower():
                    found = c

            if found:
                mac = found.get("mac", identifier)
            else:
                return None, identifier, dpi_enabled

        dpi_data = await client.get_client_dpi(mac)
        return dpi_data, mac, dpi_enabled

    try:
        dpi_data, mac, dpi_enabled = asyncio.run(_dpi())
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if dpi_data is None:
        print_error(f"Client '{identifier}' not found")
        raise typer.Exit(1)

    # Aggregate the data
    aggregated = aggregate_dpi_data(dpi_data)[:limit] if dpi_data else []

    if not aggregated:
        if not dpi_enabled:
            print_warning("DPI is not enabled on this controller")
            console.print("[dim]Enable Traffic Identification in Network Settings to use DPI.[/dim]")
        else:
            console.print(f"[dim]No DPI data collected for {mac}.[/dim]")
        return

    if output == OutputFormat.JSON:
        output_json(aggregated)
    elif output == OutputFormat.CSV:
        columns = [
            ("name", "Application"),
            ("rx_bytes", "Download (bytes)"),
            ("tx_bytes", "Upload (bytes)"),
        ]
        output_csv(aggregated, columns)
    else:
        from rich.table import Table

        console.print()
        console.print(f"[bold cyan]DPI Statistics: {mac}[/bold cyan]")
        console.print("─" * 40)
        console.print()

        table = Table(show_header=True, header_style="bold")
        table.add_column("Application")
        table.add_column("Download", justify="right")
        table.add_column("Upload", justify="right")

        total_rx = 0
        total_tx = 0

        for item in aggregated:
            rx = item["rx_bytes"]
            tx = item["tx_bytes"]
            total_rx += rx
            total_tx += tx

            table.add_row(
                item["name"],
                format_bytes(rx),
                format_bytes(tx),
            )

        console.print(table)
        console.print()
        console.print(f"[dim]Total: {format_bytes(total_rx)} down, {format_bytes(total_tx)} up[/dim]")
        console.print()
