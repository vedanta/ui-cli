"""Status command - check API connectivity and authentication."""

import asyncio
import time
from typing import Annotated

import httpx
import typer

from ui_cli import __version__
from ui_cli.config import settings
from ui_cli.local_client import (
    LocalAPIError,
    LocalAuthenticationError,
    LocalConnectionError,
    UniFiLocalClient,
)
from ui_cli.output import OutputFormat, console, output_json


app = typer.Typer(help="Check API connectivity and authentication status")


def mask_api_key(key: str, show_full: bool = False) -> str:
    """Mask API key for display."""
    if not key:
        return "(not configured)"
    if show_full:
        return key
    if len(key) <= 8:
        return "****"
    return f"****...{key[-6:]}"


async def check_site_manager_api(verbose: bool = False) -> dict:
    """Check Site Manager API connectivity and auth."""
    result = {
        "name": "Site Manager API",
        "url": settings.api_url,
        "api_key_configured": bool(settings.api_key),
        "api_key_display": mask_api_key(settings.api_key, show_full=verbose),
        "connection": None,
        "connection_time_ms": None,
        "authentication": None,
        "error": None,
        "hosts_count": None,
        "sites_count": None,
        "devices_count": None,
    }

    if not settings.api_key:
        result["error"] = "Set UNIFI_API_KEY in .env file"
        return result

    headers = {
        "X-API-Key": settings.api_key,
        "Accept": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Test connection and auth with hosts endpoint
            start = time.perf_counter()
            response = await client.get(
                f"{settings.api_url}/hosts",
                headers=headers,
            )
            elapsed_ms = (time.perf_counter() - start) * 1000

            result["connection"] = "OK"
            result["connection_time_ms"] = round(elapsed_ms, 1)

            if response.status_code == 200:
                result["authentication"] = "Valid"
                data = response.json()
                hosts = data.get("data", [])
                result["hosts_count"] = len(hosts)

                # Get sites count
                sites_resp = await client.get(
                    f"{settings.api_url}/sites",
                    headers=headers,
                )
                if sites_resp.status_code == 200:
                    sites_data = sites_resp.json()
                    result["sites_count"] = len(sites_data.get("data", []))

                # Get devices count
                devices_resp = await client.get(
                    f"{settings.api_url}/devices",
                    headers=headers,
                )
                if devices_resp.status_code == 200:
                    devices_data = devices_resp.json()
                    # Flatten devices from host groups
                    total_devices = 0
                    for host_group in devices_data.get("data", []):
                        total_devices += len(host_group.get("devices", []))
                    result["devices_count"] = total_devices

            elif response.status_code == 401:
                result["authentication"] = "FAILED"
                result["error"] = "Invalid API key"
            elif response.status_code == 429:
                result["authentication"] = "Valid"
                result["error"] = "Rate limit exceeded"
            else:
                result["authentication"] = "FAILED"
                result["error"] = f"HTTP {response.status_code}"

    except httpx.ConnectError:
        result["connection"] = "FAILED"
        result["error"] = "Could not connect to api.ui.com"
    except httpx.TimeoutException:
        result["connection"] = "FAILED"
        result["error"] = "Connection timeout"
    except Exception as e:
        result["connection"] = "FAILED"
        result["error"] = str(e)

    return result


async def check_local_controller(verbose: bool = False) -> dict:
    """Check Local Controller connectivity and auth."""
    result = {
        "name": "Local Controller",
        "url": settings.controller_url or "(not configured)",
        "username": settings.controller_username or "(not configured)",
        "site": settings.controller_site or "default",
        "configured": bool(settings.controller_url and settings.controller_username),
        "connection": None,
        "connection_time_ms": None,
        "authentication": None,
        "error": None,
        "controller_type": None,
        "clients_count": None,
        "devices_count": None,
    }

    if not settings.controller_url:
        result["error"] = "Set UNIFI_CONTROLLER_URL in .env file"
        return result

    if not settings.controller_username or not settings.controller_password:
        result["error"] = "Set UNIFI_CONTROLLER_USERNAME and UNIFI_CONTROLLER_PASSWORD in .env file"
        return result

    try:
        client = UniFiLocalClient()
        start = time.perf_counter()
        await client.login()
        elapsed_ms = (time.perf_counter() - start) * 1000

        result["connection"] = "OK"
        result["connection_time_ms"] = round(elapsed_ms, 1)
        result["authentication"] = "Valid"
        result["controller_type"] = "UDM" if client._is_udm else "Cloud Key/Self-hosted"

        # Get counts
        try:
            clients = await client.list_clients()
            result["clients_count"] = len(clients)
        except LocalAPIError:
            pass

        try:
            devices = await client.get_devices()
            result["devices_count"] = len(devices)
        except LocalAPIError:
            pass

    except LocalAuthenticationError as e:
        result["connection"] = "OK"
        result["authentication"] = "FAILED"
        result["error"] = str(e)
    except LocalConnectionError as e:
        result["connection"] = "FAILED"
        result["error"] = str(e)
    except Exception as e:
        result["connection"] = "FAILED"
        result["error"] = str(e)

    return result


def print_status_table(cloud_status: dict, local_status: dict | None = None) -> None:
    """Print status in formatted table."""
    from rich.table import Table

    console.print()
    console.print(f"[bold cyan]UniFi CLI v{__version__}[/bold cyan]")
    console.print("─" * 40)
    console.print()

    # Site Manager API section
    console.print("[bold]Site Manager API[/bold] (api.ui.com)")

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="dim")
    table.add_column("Value")

    table.add_row("URL:", cloud_status["url"])

    # API Key status
    if cloud_status["api_key_configured"]:
        table.add_row("API Key:", f"[green]{cloud_status['api_key_display']}[/green] (configured)")
    else:
        table.add_row("API Key:", f"[red]{cloud_status['api_key_display']}[/red]")

    # Connection status
    if cloud_status["connection"] == "OK":
        table.add_row(
            "Connection:",
            f"[green]OK[/green] ({cloud_status['connection_time_ms']}ms)"
        )
    elif cloud_status["connection"] == "FAILED":
        table.add_row("Connection:", "[red]FAILED[/red]")
    else:
        table.add_row("Connection:", "[dim]-[/dim]")

    # Authentication status
    if cloud_status["authentication"] == "Valid":
        table.add_row("Authentication:", "[green]Valid[/green]")
    elif cloud_status["authentication"] == "FAILED":
        table.add_row("Authentication:", "[red]FAILED[/red]")
    else:
        table.add_row("Authentication:", "[dim]-[/dim]")

    console.print(table)

    # Error message
    if cloud_status["error"]:
        console.print()
        console.print(f"  [red]Error:[/red] {cloud_status['error']}")

    # Account info (if authenticated)
    if cloud_status["authentication"] == "Valid" and cloud_status["hosts_count"] is not None:
        console.print()
        console.print("[bold]Account Summary:[/bold]")

        info_table = Table(show_header=False, box=None, padding=(0, 2))
        info_table.add_column("Key", style="dim")
        info_table.add_column("Value")

        info_table.add_row("Hosts:", str(cloud_status["hosts_count"]))
        info_table.add_row("Sites:", str(cloud_status["sites_count"]))
        info_table.add_row("Devices:", str(cloud_status["devices_count"]))

        console.print(info_table)

    # Local Controller section
    if local_status:
        console.print()
        console.print("[bold]Local Controller[/bold]")

        local_table = Table(show_header=False, box=None, padding=(0, 2))
        local_table.add_column("Key", style="dim")
        local_table.add_column("Value")

        local_table.add_row("URL:", local_status["url"])
        local_table.add_row("Site:", local_status["site"])

        if local_status["configured"]:
            local_table.add_row("Username:", f"[green]{local_status['username']}[/green]")
        else:
            local_table.add_row("Username:", f"[red]{local_status['username']}[/red]")

        # Connection status
        if local_status["connection"] == "OK":
            local_table.add_row(
                "Connection:",
                f"[green]OK[/green] ({local_status['connection_time_ms']}ms)"
            )
        elif local_status["connection"] == "FAILED":
            local_table.add_row("Connection:", "[red]FAILED[/red]")
        else:
            local_table.add_row("Connection:", "[dim]-[/dim]")

        # Authentication status
        if local_status["authentication"] == "Valid":
            local_table.add_row("Authentication:", "[green]Valid[/green]")
        elif local_status["authentication"] == "FAILED":
            local_table.add_row("Authentication:", "[red]FAILED[/red]")
        else:
            local_table.add_row("Authentication:", "[dim]-[/dim]")

        # Controller type
        if local_status["controller_type"]:
            local_table.add_row("Type:", local_status["controller_type"])

        console.print(local_table)

        # Error message
        if local_status["error"]:
            console.print()
            console.print(f"  [red]Error:[/red] {local_status['error']}")

        # Controller info (if authenticated)
        if local_status["authentication"] == "Valid":
            console.print()
            console.print("[bold]Controller Summary:[/bold]")

            ctrl_table = Table(show_header=False, box=None, padding=(0, 2))
            ctrl_table.add_column("Key", style="dim")
            ctrl_table.add_column("Value")

            if local_status["clients_count"] is not None:
                ctrl_table.add_row("Clients:", str(local_status["clients_count"]))
            if local_status["devices_count"] is not None:
                ctrl_table.add_row("Devices:", str(local_status["devices_count"]))

            console.print(ctrl_table)

    console.print()


async def check_all_status(verbose: bool = False) -> tuple[dict, dict]:
    """Check both Cloud API and Local Controller status."""
    cloud_status = await check_site_manager_api(verbose=verbose)
    local_status = await check_local_controller(verbose=verbose)
    return cloud_status, local_status


@app.callback(invoke_without_command=True)
def status(
    ctx: typer.Context,
    output: Annotated[
        OutputFormat,
        typer.Option(
            "--output",
            "-o",
            help="Output format: table or json",
        ),
    ] = OutputFormat.TABLE,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Show detailed information including full API key",
        ),
    ] = False,
) -> None:
    """Check API connectivity and authentication status."""

    # Run async checks
    cloud_status, local_status = asyncio.run(check_all_status(verbose=verbose))

    if output == OutputFormat.JSON:
        result = {
            "cloud_api": cloud_status,
            "local_controller": local_status,
        }
        output_json(result, verbose=verbose)
    else:
        print_status_table(cloud_status, local_status)

    # Exit with error code if neither is authenticated
    cloud_ok = cloud_status["authentication"] == "Valid"
    local_ok = local_status["authentication"] == "Valid"
    if not cloud_ok and not local_ok:
        raise typer.Exit(1)
