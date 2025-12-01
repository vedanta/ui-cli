"""Site health command for local controller."""

import asyncio
from typing import Annotated, Any

import typer

from ui_cli.local_client import LocalAPIError, UniFiLocalClient
from ui_cli.output import OutputFormat, console, output_json, print_error

app = typer.Typer(name="health", help="Site health status", invoke_without_command=True)


def get_status_indicator(status: str, score: int | None = None) -> tuple[str, str]:
    """Get status indicator and style based on status/score."""
    status_lower = status.lower() if status else ""

    if status_lower == "ok" or (score is not None and score >= 90):
        return "🟢", "green"
    elif status_lower in ("warning", "warn") or (score is not None and score >= 70):
        return "🟡", "yellow"
    elif status_lower in ("error", "critical", "unhealthy") or (score is not None and score < 70):
        return "🔴", "red"
    else:
        return "⚪", "dim"


def format_subsystem_name(subsystem: str) -> str:
    """Format subsystem name for display."""
    name_map = {
        "www": "Internet",
        "wan": "WAN",
        "lan": "LAN",
        "wlan": "WLAN",
        "vpn": "VPN",
        "speedtest": "Speed Test",
        "dhcp": "DHCP",
        "dns": "DNS",
    }
    return name_map.get(subsystem.lower(), subsystem.upper())


def extract_issues(health_data: list[dict[str, Any]]) -> list[str]:
    """Extract issues from health data."""
    issues = []

    for subsystem in health_data:
        name = format_subsystem_name(subsystem.get("subsystem", ""))
        status = subsystem.get("status", "").lower()
        sub_name = subsystem.get("subsystem", "")

        # Check for disconnected devices (common across subsystems)
        num_disconnected = subsystem.get("num_disconnected", 0)
        if num_disconnected > 0:
            if sub_name == "lan":
                issues.append(f"{name}: {num_disconnected} switch(es) disconnected")
            elif sub_name == "wlan":
                issues.append(f"{name}: {num_disconnected} AP(s) disconnected")
            elif sub_name == "wan":
                issues.append(f"{name}: {num_disconnected} gateway(s) disconnected")
            else:
                issues.append(f"{name}: {num_disconnected} device(s) disconnected")

        # Check for pending devices
        num_pending = subsystem.get("num_pending", 0)
        if num_pending > 0:
            issues.append(f"{name}: {num_pending} device(s) pending adoption")

        # WLAN specific checks
        if sub_name == "wlan":
            num_disabled = subsystem.get("num_disabled", 0)
            if num_disabled > 0:
                issues.append(f"WLAN: {num_disabled} AP(s) disabled")

        # WAN specific checks
        if sub_name == "wan":
            if subsystem.get("gw_wan_uptime", float("inf")) < 3600:
                uptime = subsystem.get("gw_wan_uptime", 0)
                issues.append(f"WAN: Connection recently restored ({uptime // 60} min ago)")

        # LAN specific checks
        if sub_name == "lan":
            num_sw = subsystem.get("num_sw", 0)
            num_adopted = subsystem.get("num_adopted", 0)
            if num_sw > 0 and num_adopted < num_sw:
                pending = num_sw - num_adopted
                issues.append(f"LAN: {pending} switch(es) not adopted")

    return issues


@app.callback(invoke_without_command=True)
def health(
    ctx: typer.Context,
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Show additional details"),
    ] = False,
) -> None:
    """Show site health summary."""
    if ctx.invoked_subcommand is not None:
        return

    async def _health():
        client = UniFiLocalClient()
        return await client.get_health()

    try:
        health_data = asyncio.run(_health())
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if not health_data:
        console.print("[dim]No health data available[/dim]")
        return

    if output == OutputFormat.JSON:
        output_json(health_data)
        return

    # Table output
    from rich.table import Table

    console.print()
    console.print("[bold cyan]Site Health[/bold cyan]")
    console.print("─" * 40)
    console.print()

    table = Table(show_header=True, header_style="bold", box=None)
    table.add_column("Subsystem", style="cyan")
    table.add_column("Status")
    if verbose:
        table.add_column("Details", style="dim")

    overall_ok = True
    overall_warning = False

    for subsystem in health_data:
        name = format_subsystem_name(subsystem.get("subsystem", "unknown"))
        status = subsystem.get("status", "unknown")
        indicator, style = get_status_indicator(status)

        if status.lower() not in ("ok", ""):
            if style == "red":
                overall_ok = False
            elif style == "yellow":
                overall_warning = True

        status_display = f"{indicator} [{style}]{status.upper()}[/{style}]"

        if verbose:
            # Build details string
            details = []
            if "num_user" in subsystem:
                details.append(f"{subsystem['num_user']} users")
            if "num_sta" in subsystem:
                details.append(f"{subsystem['num_sta']} clients")
            if "num_ap" in subsystem:
                details.append(f"{subsystem['num_ap']} APs")
            if "tx_bytes-r" in subsystem:
                tx = subsystem.get("tx_bytes-r", 0) / 1024 / 1024
                rx = subsystem.get("rx_bytes-r", 0) / 1024 / 1024
                details.append(f"↑{tx:.1f} ↓{rx:.1f} MB/s")
            if "latency" in subsystem:
                details.append(f"{subsystem['latency']}ms latency")

            table.add_row(name, status_display, ", ".join(details) if details else "-")
        else:
            table.add_row(name, status_display)

    console.print(table)

    # Overall status
    console.print()
    if overall_ok and not overall_warning:
        console.print("  Overall: [green]🟢 Healthy[/green]")
    elif overall_warning:
        console.print("  Overall: [yellow]🟡 Warning[/yellow]")
    else:
        console.print("  Overall: [red]🔴 Issues Detected[/red]")

    # Show issues if any
    issues = extract_issues(health_data)
    if issues:
        console.print()
        console.print("  [bold]Notes:[/bold]")
        for issue in issues:
            console.print(f"  • {issue}")

    console.print()
