"""Events and alarms commands for local controller."""

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

app = typer.Typer(name="events", help="Events and alarms management", no_args_is_help=True)
alarms_app = typer.Typer(name="alarms", help="Alarm management", no_args_is_help=True)
app.add_typer(alarms_app, name="alarms")


def format_timestamp(ts: int | None) -> str:
    """Format Unix timestamp to readable string."""
    if not ts:
        return ""
    try:
        dt = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, OSError):
        return str(ts)


def format_event_message(event: dict[str, Any]) -> str:
    """Format event into human-readable message."""
    key = event.get("key", "")
    msg = event.get("msg", "")

    # If there's a direct message, use it
    if msg:
        return msg

    # Build message from event data
    parts = []

    # Client events
    if "user" in event or "client" in event:
        client_name = event.get("user", event.get("client", ""))
        if client_name:
            parts.append(client_name)

    # Network/SSID
    if "ssid" in event:
        parts.append(f"on {event['ssid']}")

    # AP name
    if "ap_name" in event:
        parts.append(f"via {event['ap_name']}")

    # Device events
    if "sw_name" in event:
        parts.append(event["sw_name"])
    elif "gw_name" in event:
        parts.append(event["gw_name"])

    if parts:
        return " ".join(parts)

    # Fallback to key
    return key.replace("EVT_", "").replace("_", " ").title()


def get_event_type(event: dict[str, Any]) -> str:
    """Extract event type from event key."""
    key = event.get("key", "unknown")
    # Remove EVT_ prefix and clean up
    if key.startswith("EVT_"):
        key = key[4:]
    return key.lower()


def get_alarm_severity(alarm: dict[str, Any]) -> tuple[str, str]:
    """Get severity display and style for alarm."""
    # Check for severity hints in the alarm
    key = alarm.get("key", "").lower()

    if any(x in key for x in ["critical", "disconnect", "lost", "down", "offline"]):
        return "critical", "red"
    elif any(x in key for x in ["warning", "rogue", "radar", "high"]):
        return "warning", "yellow"
    else:
        return "info", "cyan"


# ========== Events Commands ==========

@app.command("list")
def list_events(
    limit: Annotated[
        int,
        typer.Option("--limit", "-l", help="Number of events to retrieve"),
    ] = 50,
    event_type: Annotated[
        str | None,
        typer.Option("--type", "-t", help="Filter by event type"),
    ] = None,
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
) -> None:
    """List recent events."""

    async def _list():
        client = UniFiLocalClient()
        return await client.get_events(limit=limit)

    try:
        events = asyncio.run(_list())
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if not events:
        console.print("[dim]No events found[/dim]")
        return

    # Filter by type if specified
    if event_type:
        event_type_lower = event_type.lower()
        events = [e for e in events if event_type_lower in get_event_type(e)]

    if output == OutputFormat.JSON:
        output_json(events)
    elif output == OutputFormat.CSV:
        columns = [
            ("time", "Time"),
            ("key", "Type"),
            ("msg", "Message"),
        ]
        # Transform for CSV
        csv_data = []
        for e in events:
            csv_data.append({
                "time": format_timestamp(e.get("time")),
                "key": get_event_type(e),
                "msg": format_event_message(e),
            })
        output_csv(csv_data, columns)
    else:
        from rich.table import Table

        table = Table(title="Recent Events", show_header=True, header_style="bold cyan")
        table.add_column("Time", style="dim")
        table.add_column("Type")
        table.add_column("Message")

        for event in events:
            time_str = format_timestamp(event.get("time"))
            evt_type = get_event_type(event)
            message = format_event_message(event)
            table.add_row(time_str, evt_type, message)

        console.print(table)
        console.print(f"\n[dim]{len(events)} event(s)[/dim]")


# ========== Alarms Commands ==========

@alarms_app.command("list")
def list_alarms(
    include_archived: Annotated[
        bool,
        typer.Option("--all", "-a", help="Include archived alarms"),
    ] = False,
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
) -> None:
    """List alarms."""

    async def _list():
        client = UniFiLocalClient()
        return await client.get_alarms(archived=include_archived)

    try:
        alarms = asyncio.run(_list())
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if not alarms:
        console.print("[green]No active alarms[/green]")
        return

    if output == OutputFormat.JSON:
        output_json(alarms)
    elif output == OutputFormat.CSV:
        columns = [
            ("_id", "ID"),
            ("time", "Time"),
            ("key", "Type"),
            ("msg", "Message"),
            ("archived", "Archived"),
        ]
        csv_data = []
        for a in alarms:
            csv_data.append({
                "_id": a.get("_id", ""),
                "time": format_timestamp(a.get("time")),
                "key": get_event_type(a),
                "msg": format_event_message(a),
                "archived": "Yes" if a.get("archived") else "No",
            })
        output_csv(csv_data, columns)
    else:
        from rich.table import Table

        title = "All Alarms" if include_archived else "Active Alarms"
        table = Table(title=title, show_header=True, header_style="bold cyan")
        table.add_column("ID", style="dim")
        table.add_column("Time", style="dim")
        table.add_column("Severity")
        table.add_column("Message")
        if include_archived:
            table.add_column("Status")

        for alarm in alarms:
            alarm_id = alarm.get("_id", "")
            time_str = format_timestamp(alarm.get("time"))
            severity, style = get_alarm_severity(alarm)
            message = format_event_message(alarm)

            severity_display = f"[{style}]{severity}[/{style}]"

            if include_archived:
                status = "[dim]archived[/dim]" if alarm.get("archived") else "[green]active[/green]"
                table.add_row(alarm_id, time_str, severity_display, message, status)
            else:
                table.add_row(alarm_id, time_str, severity_display, message)

        console.print(table)

        active_count = sum(1 for a in alarms if not a.get("archived"))
        if include_archived:
            archived_count = sum(1 for a in alarms if a.get("archived"))
            console.print(f"\n[dim]{active_count} active, {archived_count} archived[/dim]")
        else:
            console.print(f"\n[dim]{active_count} active alarm(s)[/dim]")


@alarms_app.command("archive")
def archive_alarm(
    alarm_id: Annotated[str, typer.Argument(help="Alarm ID to archive")],
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation"),
    ] = False,
) -> None:
    """Archive an alarm."""

    if not yes:
        confirm = typer.confirm(f"Archive alarm {alarm_id}?")
        if not confirm:
            console.print("[dim]Cancelled[/dim]")
            raise typer.Exit(0)

    async def _archive():
        client = UniFiLocalClient()
        return await client.archive_alarm(alarm_id)

    try:
        success = asyncio.run(_archive())
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if success:
        print_success(f"Alarm {alarm_id} archived")
    else:
        print_error(f"Failed to archive alarm {alarm_id}")
        raise typer.Exit(1)
