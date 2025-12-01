"""Network configuration commands for local controller."""

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
)

app = typer.Typer(name="networks", help="Network configuration", no_args_is_help=True)


def format_dhcp_range(network: dict[str, Any]) -> str:
    """Format DHCP range for display."""
    if not network.get("dhcpd_enabled", False):
        return "Disabled"

    start = network.get("dhcpd_start", "")
    stop = network.get("dhcpd_stop", "")

    if start and stop:
        # Extract last octet for compact display
        start_last = start.split(".")[-1] if "." in start else start
        stop_last = stop.split(".")[-1] if "." in stop else stop
        return f".{start_last} - .{stop_last}"

    return "Enabled"


def format_subnet(network: dict[str, Any]) -> str:
    """Format subnet for display."""
    subnet = network.get("ip_subnet", "")
    if subnet:
        return subnet
    return "-"


def get_network_purpose(network: dict[str, Any]) -> str:
    """Get network purpose/type."""
    purpose = network.get("purpose", "")
    if purpose:
        return purpose
    # Fallback to network type
    return network.get("networkgroup", "LAN")


@app.command("list")
def list_networks(
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Show additional details"),
    ] = False,
) -> None:
    """List all networks."""

    async def _list():
        client = UniFiLocalClient()
        return await client.get_networks()

    try:
        networks = asyncio.run(_list())
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if not networks:
        console.print("[dim]No networks found[/dim]")
        return

    if output == OutputFormat.JSON:
        output_json(networks)
    elif output == OutputFormat.CSV:
        columns = [
            ("_id", "ID"),
            ("name", "Name"),
            ("vlan", "VLAN"),
            ("ip_subnet", "Subnet"),
            ("purpose", "Purpose"),
            ("dhcpd_enabled", "DHCP"),
        ]
        csv_data = []
        for n in networks:
            csv_data.append({
                "_id": n.get("_id", ""),
                "name": n.get("name", ""),
                "vlan": n.get("vlan", "1"),
                "ip_subnet": n.get("ip_subnet", ""),
                "purpose": get_network_purpose(n),
                "dhcpd_enabled": "Yes" if n.get("dhcpd_enabled") else "No",
            })
        output_csv(csv_data, columns)
    else:
        from rich.table import Table

        table = Table(title="Networks", show_header=True, header_style="bold cyan")
        table.add_column("ID", style="dim")
        table.add_column("Name")
        table.add_column("VLAN")
        table.add_column("Subnet")
        table.add_column("DHCP")
        table.add_column("Purpose")
        if verbose:
            table.add_column("Gateway")
            table.add_column("Domain")

        for n in networks:
            network_id = n.get("_id", "")
            name = n.get("name", "")
            vlan = str(n.get("vlan", "1"))
            subnet = format_subnet(n)
            dhcp = format_dhcp_range(n)
            purpose = get_network_purpose(n)

            if verbose:
                gateway = n.get("dhcpd_gateway", n.get("ip_subnet", "").split("/")[0] if n.get("ip_subnet") else "")
                domain = n.get("domain_name", "-")
                table.add_row(network_id, name, vlan, subnet, dhcp, purpose, gateway, domain)
            else:
                table.add_row(network_id, name, vlan, subnet, dhcp, purpose)

        console.print(table)
        console.print(f"\n[dim]{len(networks)} network(s)[/dim]")


@app.command("get")
def get_network(
    network_id: Annotated[str, typer.Argument(help="Network ID or name")],
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
) -> None:
    """Get network details."""

    async def _get():
        client = UniFiLocalClient()
        networks = await client.get_networks()

        # Find by ID or name
        for n in networks:
            if n.get("_id") == network_id or n.get("name", "").lower() == network_id.lower():
                return n

        # Partial name match
        for n in networks:
            if network_id.lower() in n.get("name", "").lower():
                return n

        return None

    try:
        network = asyncio.run(_get())
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if not network:
        print_error(f"Network '{network_id}' not found")
        raise typer.Exit(1)

    if output == OutputFormat.JSON:
        output_json(network)
        return

    # Table output
    from rich.table import Table

    name = network.get("name", "Unknown")
    console.print()
    console.print(f"[bold cyan]Network: {name}[/bold cyan]")
    console.print("─" * 40)
    console.print()

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="dim")
    table.add_column("Value")

    table.add_row("ID:", network.get("_id", ""))
    table.add_row("VLAN:", str(network.get("vlan", "1")))
    table.add_row("Purpose:", get_network_purpose(network))
    table.add_row("", "")

    # Subnet info
    subnet = network.get("ip_subnet", "")
    if subnet:
        table.add_row("Subnet:", subnet)
        gateway = subnet.split("/")[0] if "/" in subnet else ""
        if gateway:
            # Replace last octet with .1 for gateway
            parts = gateway.rsplit(".", 1)
            if len(parts) == 2:
                gateway = f"{parts[0]}.1"
            table.add_row("Gateway:", network.get("dhcpd_gateway", gateway))

    table.add_row("", "")

    # DHCP info
    if network.get("dhcpd_enabled"):
        table.add_row("DHCP:", "[green]Enabled[/green]")
        start = network.get("dhcpd_start", "")
        stop = network.get("dhcpd_stop", "")
        if start and stop:
            table.add_row("Range:", f"{start} - {stop}")
        lease = network.get("dhcpd_leasetime", 86400)
        table.add_row("Lease:", f"{lease // 3600}h")

        # DNS
        dns1 = network.get("dhcpd_dns1", "")
        dns2 = network.get("dhcpd_dns2", "")
        if dns1:
            dns_str = dns1
            if dns2:
                dns_str += f", {dns2}"
            table.add_row("DNS:", dns_str)
    else:
        table.add_row("DHCP:", "[dim]Disabled[/dim]")

    table.add_row("", "")

    # Additional settings
    if network.get("igmp_snooping"):
        table.add_row("IGMP Snooping:", "Yes")

    if network.get("dhcpguard_enabled"):
        table.add_row("DHCP Guard:", "Yes")

    domain = network.get("domain_name")
    if domain:
        table.add_row("Domain:", domain)

    # Network isolation
    if network.get("purpose") == "guest":
        table.add_row("Guest Network:", "Yes")
        if network.get("networkgroup") == "LAN":
            table.add_row("Internet Only:", "Yes")

    console.print(table)
    console.print()
