"""Device management commands for local controller."""

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
    print_success,
)

app = typer.Typer(name="devices", help="Manage UniFi devices", no_args_is_help=True)


# Device type display names
DEVICE_TYPES = {
    "ugw": "Gateway",
    "usw": "Switch",
    "uap": "Access Point",
    "udm": "Dream Machine",
    "uxg": "Next-Gen Gateway",
    "ubb": "Building Bridge",
    "uck": "Cloud Key",
    "uph": "Phone",
    "ulte": "LTE Backup",
}


def get_device_type(device: dict[str, Any]) -> str:
    """Get human-readable device type."""
    dev_type = device.get("type", "")
    return DEVICE_TYPES.get(dev_type, dev_type.upper() if dev_type else "Unknown")


def get_device_status(device: dict[str, Any]) -> tuple[str, str]:
    """Get device status with color."""
    state = device.get("state", 0)
    # UniFi states: 0=offline, 1=connected, 2=pending, 4=upgrading, 5=provisioning
    if state == 1:
        return "online", "green"
    elif state == 0:
        return "offline", "red"
    elif state == 2:
        return "pending", "yellow"
    elif state == 4:
        return "upgrading", "cyan"
    elif state == 5:
        return "provisioning", "yellow"
    elif state == 6:
        return "heartbeat missed", "yellow"
    return f"state:{state}", "dim"


def get_uptime(device: dict[str, Any]) -> str:
    """Format device uptime."""
    uptime = device.get("uptime", 0)
    if not uptime:
        return "-"

    days = uptime // 86400
    hours = (uptime % 86400) // 3600
    minutes = (uptime % 3600) // 60

    if days > 0:
        return f"{days}d {hours}h"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def get_load(device: dict[str, Any]) -> str:
    """Get system load average."""
    load = device.get("sys_stats", {}).get("loadavg_1", "")
    if load:
        return f"{float(load):.2f}"
    return "-"


def format_version(device: dict[str, Any]) -> str:
    """Format firmware version."""
    version = device.get("version", "")
    if version:
        return version
    return "-"


def find_device(devices: list[dict[str, Any]], identifier: str) -> dict[str, Any] | None:
    """Find device by ID, MAC, name, or IP."""
    identifier_lower = identifier.lower()

    # First try exact ID match
    for d in devices:
        device_id = d.get("_id", "")
        if device_id == identifier:
            return d

    # Try exact MAC match
    for d in devices:
        mac = d.get("mac", "").lower()
        if mac == identifier_lower or mac.replace(":", "") == identifier_lower.replace(":", ""):
            return d

    # Try name match (exact then partial)
    for d in devices:
        name = d.get("name", "").lower()
        if name == identifier_lower:
            return d

    for d in devices:
        name = d.get("name", "").lower()
        if identifier_lower in name:
            return d

    # Try IP match
    for d in devices:
        ip = d.get("ip", "")
        if ip == identifier:
            return d

    return None


@app.command("list")
def list_devices(
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
    device_type: Annotated[
        str | None,
        typer.Option("--type", "-t", help="Filter by device type (uap, usw, ugw, udm)"),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Show additional details"),
    ] = False,
) -> None:
    """List all UniFi devices."""

    async def _list():
        client = UniFiLocalClient()
        return await client.get_devices()

    try:
        devices = asyncio.run(_list())
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if not devices:
        console.print("[dim]No devices found[/dim]")
        return

    # Filter by type if specified
    if device_type:
        type_lower = device_type.lower()
        devices = [d for d in devices if d.get("type", "").lower() == type_lower]
        if not devices:
            console.print(f"[dim]No {device_type} devices found[/dim]")
            return

    # Sort by type then name
    devices.sort(key=lambda d: (d.get("type", ""), d.get("name", "").lower()))

    if output == OutputFormat.JSON:
        output_json(devices)
    elif output == OutputFormat.CSV:
        columns = [
            ("_id", "ID"),
            ("mac", "MAC"),
            ("name", "Name"),
            ("model", "Model"),
            ("type", "Type"),
            ("ip", "IP"),
            ("version", "Version"),
            ("state", "State"),
            ("uptime", "Uptime"),
        ]
        csv_data = []
        for d in devices:
            status, _ = get_device_status(d)
            csv_data.append({
                "_id": d.get("_id", ""),
                "mac": d.get("mac", ""),
                "name": d.get("name", ""),
                "model": d.get("model", ""),
                "type": get_device_type(d),
                "ip": d.get("ip", ""),
                "version": format_version(d),
                "state": status,
                "uptime": get_uptime(d),
            })
        output_csv(csv_data, columns)
    else:
        from rich.table import Table

        table = Table(title="UniFi Devices", show_header=True, header_style="bold cyan")
        table.add_column("ID", style="dim")
        table.add_column("Name")
        table.add_column("Model")
        table.add_column("Type")
        table.add_column("IP")
        table.add_column("MAC", style="dim")
        table.add_column("Version")
        table.add_column("Status")
        table.add_column("Uptime", justify="right")
        if verbose:
            table.add_column("Load")
            table.add_column("Clients", justify="right")

        for d in devices:
            device_id = d.get("_id", "")
            name = d.get("name", "(unnamed)")
            model = d.get("model", "")
            dev_type = get_device_type(d)
            ip = d.get("ip", "")
            mac = d.get("mac", "")
            version = format_version(d)
            status, status_style = get_device_status(d)
            uptime = get_uptime(d)

            if verbose:
                load = get_load(d)
                # Client count varies by device type
                num_sta = d.get("num_sta", d.get("user-num_sta", 0))
                clients = str(num_sta) if num_sta else "-"

                table.add_row(
                    device_id,
                    name,
                    model,
                    dev_type,
                    ip,
                    mac,
                    version,
                    f"[{status_style}]{status}[/{status_style}]",
                    uptime,
                    load,
                    clients,
                )
            else:
                table.add_row(
                    device_id,
                    name,
                    model,
                    dev_type,
                    ip,
                    mac,
                    version,
                    f"[{status_style}]{status}[/{status_style}]",
                    uptime,
                )

        console.print(table)
        console.print(f"\n[dim]{len(devices)} device(s)[/dim]")


@app.command("get")
def get_device(
    identifier: Annotated[str, typer.Argument(help="Device MAC, name, or IP")],
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
) -> None:
    """Get detailed device information."""

    async def _get():
        client = UniFiLocalClient()
        devices = await client.get_devices()
        return find_device(devices, identifier)

    try:
        device = asyncio.run(_get())
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if not device:
        print_error(f"Device '{identifier}' not found")
        raise typer.Exit(1)

    if output == OutputFormat.JSON:
        output_json(device)
        return

    # Table output
    from rich.table import Table

    name = device.get("name", "Unknown")
    console.print()
    console.print(f"[bold cyan]Device: {name}[/bold cyan]")
    console.print("─" * 50)
    console.print()

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="dim")
    table.add_column("Value")

    table.add_row("ID:", device.get("_id", ""))
    table.add_row("MAC:", device.get("mac", ""))
    table.add_row("Model:", device.get("model", ""))
    table.add_row("Type:", get_device_type(device))
    table.add_row("IP:", device.get("ip", ""))
    table.add_row("", "")

    status, status_style = get_device_status(device)
    table.add_row("Status:", f"[{status_style}]{status}[/{status_style}]")
    table.add_row("Uptime:", get_uptime(device))
    table.add_row("Version:", format_version(device))

    # Check for upgrade
    upgradable = device.get("upgradable", False)
    if upgradable:
        upgrade_to = device.get("upgrade_to_firmware", "")
        table.add_row("Upgrade:", f"[yellow]{upgrade_to} available[/yellow]")

    table.add_row("", "")

    # System stats
    sys_stats = device.get("sys_stats", {})
    if sys_stats:
        load = sys_stats.get("loadavg_1", "")
        mem = sys_stats.get("mem_used", 0)
        mem_total = sys_stats.get("mem_total", 0)
        if load:
            table.add_row("Load:", f"{float(load):.2f}")
        if mem_total:
            mem_pct = (mem / mem_total) * 100 if mem_total else 0
            table.add_row("Memory:", f"{mem_pct:.0f}%")

    # Network stats for APs
    num_sta = device.get("num_sta", device.get("user-num_sta", 0))
    if num_sta:
        table.add_row("Clients:", str(num_sta))

    # Port info for switches
    port_table = device.get("port_table", [])
    if port_table:
        active_ports = sum(1 for p in port_table if p.get("up", False))
        table.add_row("Ports:", f"{active_ports}/{len(port_table)} active")

    # Radio info for APs
    radio_table = device.get("radio_table", [])
    if radio_table:
        radios = []
        for r in radio_table:
            band = "5G" if r.get("radio") == "na" else "2.4G"
            channel = r.get("channel", "")
            if channel:
                radios.append(f"{band}:ch{channel}")
        if radios:
            table.add_row("Radios:", ", ".join(radios))

    console.print(table)
    console.print()


@app.command("restart")
def restart_device(
    identifier: Annotated[str, typer.Argument(help="Device MAC, name, or IP")],
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation"),
    ] = False,
) -> None:
    """Restart/reboot a device."""

    async def _get_device():
        client = UniFiLocalClient()
        devices = await client.get_devices()
        return find_device(devices, identifier)

    try:
        device = asyncio.run(_get_device())
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if not device:
        print_error(f"Device '{identifier}' not found")
        raise typer.Exit(1)

    name = device.get("name", device.get("mac", identifier))
    mac = device.get("mac", "")

    if not yes:
        confirm = typer.confirm(f"Restart device '{name}'?")
        if not confirm:
            console.print("[dim]Cancelled[/dim]")
            raise typer.Exit(0)

    async def _restart():
        client = UniFiLocalClient()
        return await client.restart_device(mac)

    try:
        success = asyncio.run(_restart())
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if success:
        print_success(f"Restart command sent to '{name}'")
        console.print("[dim]Device will reboot shortly[/dim]")
    else:
        print_error(f"Failed to restart '{name}'")
        raise typer.Exit(1)


@app.command("upgrade")
def upgrade_device(
    identifier: Annotated[str, typer.Argument(help="Device MAC, name, or IP")],
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation"),
    ] = False,
) -> None:
    """Upgrade device firmware."""

    async def _get_device():
        client = UniFiLocalClient()
        devices = await client.get_devices()
        return find_device(devices, identifier)

    try:
        device = asyncio.run(_get_device())
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if not device:
        print_error(f"Device '{identifier}' not found")
        raise typer.Exit(1)

    name = device.get("name", device.get("mac", identifier))
    mac = device.get("mac", "")
    current_version = device.get("version", "unknown")

    # Check if upgrade is available
    if not device.get("upgradable", False):
        console.print(f"[dim]'{name}' is already on the latest firmware ({current_version})[/dim]")
        return

    upgrade_to = device.get("upgrade_to_firmware", "latest")

    if not yes:
        confirm = typer.confirm(f"Upgrade '{name}' from {current_version} to {upgrade_to}?")
        if not confirm:
            console.print("[dim]Cancelled[/dim]")
            raise typer.Exit(0)

    async def _upgrade():
        client = UniFiLocalClient()
        return await client.upgrade_device(mac)

    try:
        success = asyncio.run(_upgrade())
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if success:
        print_success(f"Upgrade started for '{name}'")
        console.print(f"[dim]Upgrading to {upgrade_to}. Device will reboot when complete.[/dim]")
    else:
        print_error(f"Failed to start upgrade for '{name}'")
        raise typer.Exit(1)


@app.command("locate")
def locate_device(
    identifier: Annotated[str, typer.Argument(help="Device MAC, name, or IP")],
    off: Annotated[
        bool,
        typer.Option("--off", help="Turn off locate LED"),
    ] = False,
) -> None:
    """Flash LED to locate a device."""

    async def _get_device():
        client = UniFiLocalClient()
        devices = await client.get_devices()
        return find_device(devices, identifier)

    try:
        device = asyncio.run(_get_device())
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if not device:
        print_error(f"Device '{identifier}' not found")
        raise typer.Exit(1)

    name = device.get("name", device.get("mac", identifier))
    mac = device.get("mac", "")

    async def _locate():
        client = UniFiLocalClient()
        return await client.locate_device(mac, enabled=not off)

    try:
        success = asyncio.run(_locate())
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if success:
        if off:
            print_success(f"Locate LED turned off for '{name}'")
        else:
            print_success(f"Locate LED flashing on '{name}'")
            console.print("[dim]Run with --off to stop[/dim]")
    else:
        print_error(f"Failed to set locate LED for '{name}'")
        raise typer.Exit(1)


@app.command("adopt")
def adopt_device(
    identifier: Annotated[str, typer.Argument(help="Device MAC address")],
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation"),
    ] = False,
) -> None:
    """Adopt a pending device."""

    if not yes:
        confirm = typer.confirm(f"Adopt device '{identifier}'?")
        if not confirm:
            console.print("[dim]Cancelled[/dim]")
            raise typer.Exit(0)

    async def _adopt():
        client = UniFiLocalClient()
        return await client.adopt_device(identifier)

    try:
        success = asyncio.run(_adopt())
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if success:
        print_success(f"Adoption started for '{identifier}'")
        console.print("[dim]Device will provision and appear in device list[/dim]")
    else:
        print_error(f"Failed to adopt '{identifier}'")
        raise typer.Exit(1)
