"""Traffic statistics commands for local controller."""

import asyncio
from datetime import datetime, timezone
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

app = typer.Typer(name="stats", help="Traffic statistics", no_args_is_help=True)


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


def format_timestamp(ts: int | float | None, include_time: bool = False) -> str:
    """Format Unix timestamp to date/time string."""
    if not ts:
        return "-"
    try:
        # Convert milliseconds to seconds if needed
        if ts > 1e12:
            ts = ts / 1000
        dt = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone()
        if include_time:
            return dt.strftime("%Y-%m-%d %H:%M")
        return dt.strftime("%Y-%m-%d")
    except (ValueError, OSError):
        return str(ts)


def get_traffic_bytes(stat: dict[str, Any]) -> tuple[int, int]:
    """Extract download/upload bytes from stat record."""
    # Try WAN stats first (more accurate for internet traffic)
    rx = stat.get("wan-rx_bytes", 0) or stat.get("rx_bytes", 0)
    tx = stat.get("wan-tx_bytes", 0) or stat.get("tx_bytes", 0)
    return int(rx or 0), int(tx or 0)


@app.command("daily")
def daily_stats(
    days: Annotated[
        int,
        typer.Option("--days", "-d", help="Number of days to show"),
    ] = 30,
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
) -> None:
    """Show daily traffic statistics."""

    async def _stats():
        client = UniFiLocalClient()
        return await client.get_daily_stats(days=days)

    try:
        stats = asyncio.run(_stats())
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if not stats:
        console.print("[dim]No daily statistics available[/dim]")
        return

    # Sort by time (most recent first)
    stats.sort(key=lambda s: s.get("time", 0), reverse=True)

    if output == OutputFormat.JSON:
        output_json(stats)
    elif output == OutputFormat.CSV:
        columns = [
            ("date", "Date"),
            ("rx_bytes", "Download (bytes)"),
            ("tx_bytes", "Upload (bytes)"),
            ("total_bytes", "Total (bytes)"),
            ("num_sta", "Clients"),
        ]
        csv_data = []
        for s in stats:
            rx, tx = get_traffic_bytes(s)
            csv_data.append({
                "date": format_timestamp(s.get("time")),
                "rx_bytes": rx,
                "tx_bytes": tx,
                "total_bytes": rx + tx,
                "num_sta": s.get("num_sta", 0),
            })
        output_csv(csv_data, columns)
    else:
        from rich.table import Table

        table = Table(title="Daily Traffic Statistics", show_header=True, header_style="bold cyan")
        table.add_column("Date")
        table.add_column("Download", justify="right")
        table.add_column("Upload", justify="right")
        table.add_column("Total", justify="right")
        table.add_column("Clients", justify="right")

        total_rx = 0
        total_tx = 0

        for s in stats:
            date = format_timestamp(s.get("time"))
            rx, tx = get_traffic_bytes(s)
            total_rx += rx
            total_tx += tx
            total = rx + tx
            num_sta = s.get("num_sta", 0)

            table.add_row(
                date,
                format_bytes(rx),
                format_bytes(tx),
                format_bytes(total),
                str(num_sta) if num_sta else "-",
            )

        console.print(table)
        console.print()
        console.print(f"[dim]Total: {format_bytes(total_rx)} down, {format_bytes(total_tx)} up ({format_bytes(total_rx + total_tx)} total)[/dim]")
        console.print()


@app.command("hourly")
def hourly_stats(
    hours: Annotated[
        int,
        typer.Option("--hours", "-h", help="Number of hours to show"),
    ] = 24,
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
) -> None:
    """Show hourly traffic statistics."""

    async def _stats():
        client = UniFiLocalClient()
        return await client.get_hourly_stats(hours=hours)

    try:
        stats = asyncio.run(_stats())
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if not stats:
        console.print("[dim]No hourly statistics available[/dim]")
        return

    # Sort by time (most recent first)
    stats.sort(key=lambda s: s.get("time", 0), reverse=True)

    if output == OutputFormat.JSON:
        output_json(stats)
    elif output == OutputFormat.CSV:
        columns = [
            ("time", "Time"),
            ("rx_bytes", "Download (bytes)"),
            ("tx_bytes", "Upload (bytes)"),
            ("total_bytes", "Total (bytes)"),
            ("num_sta", "Clients"),
        ]
        csv_data = []
        for s in stats:
            rx, tx = get_traffic_bytes(s)
            csv_data.append({
                "time": format_timestamp(s.get("time"), include_time=True),
                "rx_bytes": rx,
                "tx_bytes": tx,
                "total_bytes": rx + tx,
                "num_sta": s.get("num_sta", 0),
            })
        output_csv(csv_data, columns)
    else:
        from rich.table import Table

        table = Table(title="Hourly Traffic Statistics", show_header=True, header_style="bold cyan")
        table.add_column("Time")
        table.add_column("Download", justify="right")
        table.add_column("Upload", justify="right")
        table.add_column("Total", justify="right")
        table.add_column("Clients", justify="right")

        total_rx = 0
        total_tx = 0

        for s in stats:
            time_str = format_timestamp(s.get("time"), include_time=True)
            rx, tx = get_traffic_bytes(s)
            total_rx += rx
            total_tx += tx
            total = rx + tx
            num_sta = s.get("num_sta", 0)

            table.add_row(
                time_str,
                format_bytes(rx),
                format_bytes(tx),
                format_bytes(total),
                str(num_sta) if num_sta else "-",
            )

        console.print(table)
        console.print()
        console.print(f"[dim]Total: {format_bytes(total_rx)} down, {format_bytes(total_tx)} up ({format_bytes(total_rx + total_tx)} total)[/dim]")
        console.print()
