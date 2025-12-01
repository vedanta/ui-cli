"""Voucher management commands for guest WiFi access."""

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
    output_table,
    print_error,
    print_success,
)

app = typer.Typer(name="vouchers", help="Guest WiFi voucher management", no_args_is_help=True)


def format_duration(minutes: int | None) -> str:
    """Format duration in human-readable form."""
    if not minutes:
        return "-"

    if minutes < 60:
        return f"{minutes}m"
    elif minutes < 1440:
        hours = minutes // 60
        return f"{hours}h"
    else:
        days = minutes // 1440
        return f"{days}d"


def format_quota(mb: int | None) -> str:
    """Format data quota in human-readable form."""
    if not mb or mb == 0:
        return "No limit"

    if mb >= 1024:
        gb = mb / 1024
        return f"{gb:.1f} GB"
    return f"{mb} MB"


def format_timestamp(ts: int | None) -> str:
    """Format Unix timestamp to date string."""
    if not ts:
        return "-"
    try:
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return dt.strftime("%Y-%m-%d")
    except (ValueError, OSError):
        return str(ts)


def format_code(code: str | None) -> str:
    """Format voucher code with dash for readability."""
    if not code:
        return "-"
    # Insert dash in middle if not present
    if "-" not in code and len(code) == 10:
        return f"{code[:5]}-{code[5:]}"
    return code


def is_voucher_expired(voucher: dict[str, Any]) -> bool:
    """Check if voucher is expired."""
    create_time = voucher.get("create_time", 0)
    duration = voucher.get("duration", 0)  # in minutes
    if create_time and duration:
        expires_at = create_time + (duration * 60)  # convert to seconds
        return datetime.now(timezone.utc).timestamp() > expires_at
    return False


def get_voucher_status(voucher: dict[str, Any]) -> tuple[str, str]:
    """Get voucher status and style."""
    used = voucher.get("used", 0)
    quota = voucher.get("quota", 1)  # multi-use count

    # Check if expired
    if is_voucher_expired(voucher):
        return "expired", "red"

    if used >= quota:
        return "used", "dim"
    elif used > 0:
        return "partial", "yellow"
    else:
        return "unused", "green"


@app.command("list")
def list_vouchers(
    unused: Annotated[
        bool,
        typer.Option("--unused", "-u", help="Show only unused vouchers"),
    ] = False,
    used: Annotated[
        bool,
        typer.Option("--used", help="Show only used vouchers"),
    ] = False,
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
) -> None:
    """List all vouchers."""

    async def _list():
        client = UniFiLocalClient()
        return await client.get_vouchers()

    try:
        vouchers = asyncio.run(_list())
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if not vouchers:
        console.print("[dim]No vouchers found[/dim]")
        return

    # Filter if requested
    if unused:
        vouchers = [v for v in vouchers if v.get("used", 0) == 0]
    elif used:
        vouchers = [v for v in vouchers if v.get("used", 0) > 0]

    if not vouchers:
        console.print("[dim]No matching vouchers[/dim]")
        return

    if output == OutputFormat.JSON:
        output_json(vouchers)
    elif output == OutputFormat.CSV:
        columns = [
            ("_id", "ID"),
            ("code", "Code"),
            ("duration", "Duration (min)"),
            ("quota", "Uses"),
            ("used", "Used"),
            ("qos_usage_quota", "Quota (MB)"),
            ("note", "Note"),
            ("create_time", "Created"),
        ]
        csv_data = []
        for v in vouchers:
            csv_data.append({
                "_id": v.get("_id", ""),
                "code": format_code(v.get("code")),
                "duration": v.get("duration", 0),
                "quota": v.get("quota", 1),
                "used": v.get("used", 0),
                "qos_usage_quota": v.get("qos_usage_quota", ""),
                "note": v.get("note", ""),
                "create_time": format_timestamp(v.get("create_time")),
            })
        output_csv(csv_data, columns)
    else:
        from rich.table import Table

        table = Table(title="Guest Vouchers", show_header=True, header_style="bold cyan")
        table.add_column("ID", style="dim")
        table.add_column("Code")
        table.add_column("Duration")
        table.add_column("Quota")
        table.add_column("Used")
        table.add_column("Status")
        table.add_column("Note", style="dim")

        for v in vouchers:
            voucher_id = v.get("_id", "")
            code = format_code(v.get("code"))
            duration = format_duration(v.get("duration", 0))
            quota = format_quota(v.get("qos_usage_quota"))
            multi_use = v.get("quota", 1)
            used_count = v.get("used", 0)
            used_str = f"{used_count}/{multi_use}"
            note = v.get("note", "") or ""
            status, style = get_voucher_status(v)

            table.add_row(
                voucher_id,
                code,
                duration,
                quota,
                used_str,
                f"[{style}]{status}[/{style}]",
                note[:20] + "..." if len(note) > 20 else note,
            )

        console.print(table)
        console.print(f"\n[dim]{len(vouchers)} voucher(s)[/dim]")


@app.command("create")
def create_voucher(
    count: Annotated[
        int,
        typer.Option("--count", "-c", help="Number of vouchers to create"),
    ] = 1,
    duration: Annotated[
        int,
        typer.Option("--duration", "-d", help="Duration in minutes (1440 = 24h)"),
    ] = 1440,
    quota: Annotated[
        int,
        typer.Option("--quota", "-q", help="Data quota in MB (0 = unlimited)"),
    ] = 0,
    up_limit: Annotated[
        int,
        typer.Option("--up", help="Upload limit in kbps (0 = unlimited)"),
    ] = 0,
    down_limit: Annotated[
        int,
        typer.Option("--down", help="Download limit in kbps (0 = unlimited)"),
    ] = 0,
    multi_use: Annotated[
        int,
        typer.Option("--multi-use", "-m", help="Number of uses per voucher"),
    ] = 1,
    note: Annotated[
        str | None,
        typer.Option("--note", "-n", help="Note/description"),
    ] = None,
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
) -> None:
    """Create new voucher(s)."""

    async def _create():
        client = UniFiLocalClient()
        return await client.create_voucher(
            count=count,
            duration=duration,
            quota=quota,
            up_limit=up_limit,
            down_limit=down_limit,
            multi_use=multi_use,
            note=note,
        )

    try:
        result = asyncio.run(_create())
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if not result:
        print_error("Failed to create vouchers")
        raise typer.Exit(1)

    # Create API returns minimal data, fetch full voucher list to get details
    # Filter by create_time from the result
    create_time = result[0].get("create_time", 0) if result else 0

    async def _fetch():
        client = UniFiLocalClient()
        vouchers = await client.get_vouchers()
        # Filter vouchers created at or after our create_time
        return [v for v in vouchers if v.get("create_time", 0) >= create_time][:count]

    try:
        created = asyncio.run(_fetch())
    except LocalAPIError:
        created = []

    if not created:
        print_success(f"Created {count} voucher(s)")
        console.print("[dim]Run 'ui lo vouchers list' to see them[/dim]")
        return

    if output == OutputFormat.JSON:
        output_json(created)
        return

    # Table output
    from rich.table import Table

    console.print()
    print_success(f"Created {len(created)} voucher(s):")
    console.print()

    table = Table(show_header=True, header_style="bold cyan", box=None)
    table.add_column("Code")
    table.add_column("Duration")
    table.add_column("Quota")
    if multi_use > 1:
        table.add_column("Uses")

    for v in created:
        code = format_code(v.get("code"))
        dur = format_duration(duration)
        q = format_quota(quota)

        if multi_use > 1:
            table.add_row(f"[green]{code}[/green]", dur, q, str(multi_use))
        else:
            table.add_row(f"[green]{code}[/green]", dur, q)

    console.print(table)
    console.print()
    console.print("[dim]Tip: Share these codes with guests for WiFi access[/dim]")
    console.print()


@app.command("revoke")
def revoke_voucher(
    voucher_id: Annotated[str, typer.Argument(help="Voucher ID to revoke")],
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation"),
    ] = False,
) -> None:
    """Revoke/delete a voucher."""

    if not yes:
        confirm = typer.confirm(f"Revoke voucher {voucher_id}?")
        if not confirm:
            console.print("[dim]Cancelled[/dim]")
            raise typer.Exit(0)

    async def _revoke():
        client = UniFiLocalClient()
        return await client.revoke_voucher(voucher_id)

    try:
        success = asyncio.run(_revoke())
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if success:
        print_success(f"Voucher {voucher_id} revoked")
    else:
        print_error(f"Failed to revoke voucher {voucher_id}")
        raise typer.Exit(1)


@app.command("delete-all")
def delete_all_vouchers(
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation"),
    ] = False,
    expired_only: Annotated[
        bool,
        typer.Option("--expired", "-e", help="Delete only expired vouchers"),
    ] = False,
) -> None:
    """Delete all vouchers."""

    async def _get_vouchers():
        client = UniFiLocalClient()
        return await client.get_vouchers()

    try:
        vouchers = asyncio.run(_get_vouchers())
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if not vouchers:
        console.print("[dim]No vouchers to delete[/dim]")
        return

    # Filter to expired only if requested
    if expired_only:
        vouchers = [v for v in vouchers if is_voucher_expired(v)]
        if not vouchers:
            console.print("[dim]No expired vouchers to delete[/dim]")
            return

    count = len(vouchers)
    label = "expired vouchers" if expired_only else "vouchers"

    if not yes:
        confirm = typer.confirm(f"Delete all {count} {label}?")
        if not confirm:
            console.print("[dim]Cancelled[/dim]")
            raise typer.Exit(0)

    async def _delete_all():
        client = UniFiLocalClient()
        deleted = 0
        for v in vouchers:
            voucher_id = v.get("_id")
            if voucher_id:
                try:
                    if await client.revoke_voucher(voucher_id):
                        deleted += 1
                except LocalAPIError:
                    pass
        return deleted

    try:
        deleted = asyncio.run(_delete_all())
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    print_success(f"Deleted {deleted}/{count} {label}")
