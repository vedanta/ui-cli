"""Port forwarding commands for local controller."""

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

app = typer.Typer(name="portfwd", help="Port forwarding rules", no_args_is_help=True)


def format_protocol(rule: dict[str, Any]) -> str:
    """Format protocol for display."""
    proto = rule.get("proto", "tcp_udp")
    if proto == "tcp_udp":
        return "TCP/UDP"
    return proto.upper()


def format_source(rule: dict[str, Any]) -> str:
    """Format source (WAN) side."""
    port = rule.get("dst_port", "")
    src = rule.get("src", "any")

    if src and src != "any":
        return f"{src}:{port}"
    return f"*:{port}"


def format_destination(rule: dict[str, Any]) -> str:
    """Format destination (LAN) side."""
    fwd_ip = rule.get("fwd", "")
    fwd_port = rule.get("fwd_port", rule.get("dst_port", ""))

    if fwd_ip:
        return f"{fwd_ip}:{fwd_port}"
    return f"*:{fwd_port}"


def format_interface(rule: dict[str, Any]) -> str:
    """Format WAN interface."""
    pfwd_interface = rule.get("pfwd_interface", "")
    if pfwd_interface == "all":
        return "All WANs"
    elif pfwd_interface:
        return pfwd_interface
    return "WAN"


@app.command("list")
def list_port_forwards(
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
    all_rules: Annotated[
        bool,
        typer.Option("--all", "-a", help="Show disabled rules too"),
    ] = True,
) -> None:
    """List port forwarding rules."""

    async def _list():
        client = UniFiLocalClient()
        return await client.get_port_forwards()

    try:
        rules = asyncio.run(_list())
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if not rules:
        console.print("[dim]No port forwarding rules found[/dim]")
        return

    # Filter disabled if not showing all
    if not all_rules:
        rules = [r for r in rules if r.get("enabled", True)]
        if not rules:
            console.print("[dim]No enabled port forwarding rules[/dim]")
            return

    # Sort by name
    rules.sort(key=lambda r: r.get("name", "").lower())

    if output == OutputFormat.JSON:
        output_json(rules)
    elif output == OutputFormat.CSV:
        columns = [
            ("_id", "ID"),
            ("name", "Name"),
            ("enabled", "Enabled"),
            ("proto", "Protocol"),
            ("dst_port", "WAN Port"),
            ("fwd", "LAN IP"),
            ("fwd_port", "LAN Port"),
            ("pfwd_interface", "Interface"),
        ]
        csv_data = []
        for r in rules:
            csv_data.append({
                "_id": r.get("_id", ""),
                "name": r.get("name", ""),
                "enabled": "Yes" if r.get("enabled", True) else "No",
                "proto": format_protocol(r),
                "dst_port": r.get("dst_port", ""),
                "fwd": r.get("fwd", ""),
                "fwd_port": r.get("fwd_port", r.get("dst_port", "")),
                "pfwd_interface": format_interface(r),
            })
        output_csv(csv_data, columns)
    else:
        from rich.table import Table

        table = Table(title="Port Forwarding Rules", show_header=True, header_style="bold cyan")
        table.add_column("Name")
        table.add_column("Protocol")
        table.add_column("WAN Port")
        table.add_column("→", style="dim")
        table.add_column("LAN Destination")
        table.add_column("Interface")
        table.add_column("Enabled")

        for r in rules:
            name = r.get("name", "(unnamed)")
            protocol = format_protocol(r)
            wan_port = str(r.get("dst_port", ""))
            destination = format_destination(r)
            interface = format_interface(r)
            enabled = "[green]✓[/green]" if r.get("enabled", True) else "[dim]✗[/dim]"

            table.add_row(
                name,
                protocol,
                wan_port,
                "→",
                destination,
                interface,
                enabled,
            )

        console.print(table)
        console.print(f"\n[dim]{len(rules)} rule(s)[/dim]")
