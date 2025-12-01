"""Speed test command - run speed test on gateway."""

import asyncio
import time
from typing import Annotated

import typer

from ui_cli.local_client import LocalAPIError, UniFiLocalClient
from ui_cli.output import OutputFormat, console, output_json, print_error

app = typer.Typer(help="Run speed test on gateway", invoke_without_command=True)


async def run_speedtest(client: UniFiLocalClient) -> dict:
    """Trigger speed test and wait for results."""
    # Trigger the speed test
    response = await client.post("/cmd/devmgr", data={"cmd": "speedtest"})

    if response.get("meta", {}).get("rc") != "ok":
        raise LocalAPIError("Failed to start speed test")

    return response


async def get_speedtest_status(client: UniFiLocalClient) -> dict | None:
    """Get current speed test status."""
    response = await client.post("/cmd/devmgr", data={"cmd": "speedtest-status"})
    data = response.get("data", [])
    return data[0] if data else None


async def get_latest_speedtest(client: UniFiLocalClient) -> dict | None:
    """Get most recent speed test result from health endpoint."""
    # Speed test data is in the www (Internet) subsystem of health
    response = await client.get("/stat/health")
    data = response.get("data", [])

    for subsystem in data:
        if subsystem.get("subsystem") == "www":
            return subsystem

    return None


def format_speed(bps: float | None) -> str:
    """Format speed in appropriate units."""
    if bps is None or bps == 0:
        return "-"

    mbps = bps / 1_000_000
    if mbps >= 1000:
        return f"{mbps / 1000:.1f} Gbps"
    elif mbps >= 1:
        return f"{mbps:.1f} Mbps"
    else:
        kbps = bps / 1000
        return f"{kbps:.0f} Kbps"


def format_latency(ms: float | None) -> str:
    """Format latency."""
    if ms is None:
        return "-"
    return f"{ms:.0f} ms"


@app.callback(invoke_without_command=True)
def speedtest(
    ctx: typer.Context,
    run: Annotated[
        bool,
        typer.Option("--run", "-r", help="Run a new speed test"),
    ] = False,
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
) -> None:
    """Show last speed test result or run a new test."""
    if ctx.invoked_subcommand is not None:
        return

    async def _speedtest():
        client = UniFiLocalClient()

        if run:
            from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

            # Run a new speed test
            await run_speedtest(client)

            # Poll for completion using health endpoint with progress bar
            max_wait = 90  # seconds (speed tests can take a while)
            start = time.time()

            with Progress(
                SpinnerColumn(),
                TextColumn("[cyan]Running speed test..."),
                BarColumn(bar_width=30),
                TimeElapsedColumn(),
                console=console,
                transient=True,
            ) as progress:
                task = progress.add_task("speedtest", total=max_wait)

                while time.time() - start < max_wait:
                    await asyncio.sleep(2)
                    elapsed = time.time() - start
                    progress.update(task, completed=min(elapsed, max_wait))

                    # Check www subsystem for speedtest_status
                    health = await client.get("/stat/health")
                    for subsystem in health.get("data", []):
                        if subsystem.get("subsystem") == "www":
                            status = subsystem.get("speedtest_status", "")
                            if status.lower() != "running":
                                progress.update(task, completed=max_wait)
                                break
                    else:
                        continue
                    break

        # Get the latest result
        return await get_latest_speedtest(client)

    try:
        result = asyncio.run(_speedtest())
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if not result:
        console.print("[dim]No speed test results found. Run with --run to start a test.[/dim]")
        return

    if output == OutputFormat.JSON:
        output_json(result)
        return

    # Table output
    from datetime import datetime, timezone
    from rich.table import Table

    console.print()
    console.print("[bold cyan]Speed Test Results[/bold cyan]")
    console.print("─" * 40)
    console.print()

    # Format timestamp (speedtest_lastrun is in seconds)
    ts = result.get("speedtest_lastrun", 0)
    if ts:
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        time_str = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    else:
        time_str = "-"

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="dim")
    table.add_column("Value")

    # Status
    status = result.get("speedtest_status", "")
    if status:
        if status.lower() == "running":
            table.add_row("Status:", f"[yellow]{status}[/yellow]")
        else:
            table.add_row("Status:", f"[green]{status}[/green]")

    table.add_row("Last Run:", time_str)
    table.add_row("", "")

    # Download (xput_down is in Mbps)
    download = result.get("xput_down", 0)
    if download:
        table.add_row("Download:", f"[green]{download} Mbps[/green]")
    else:
        table.add_row("Download:", "-")

    # Upload (xput_up is in Mbps)
    upload = result.get("xput_up", 0)
    if upload:
        table.add_row("Upload:", f"[blue]{upload} Mbps[/blue]")
    else:
        table.add_row("Upload:", "-")

    # Latency
    latency = result.get("speedtest_ping", result.get("latency", 0))
    table.add_row("Latency:", format_latency(latency))

    console.print(table)
    console.print()
