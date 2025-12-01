"""Firewall commands for local controller."""

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

app = typer.Typer(name="firewall", help="Firewall rules and groups", no_args_is_help=True)


# Ruleset display names
RULESET_NAMES = {
    "WAN_IN": "WAN In",
    "WAN_OUT": "WAN Out",
    "WAN_LOCAL": "WAN Local",
    "LAN_IN": "LAN In",
    "LAN_OUT": "LAN Out",
    "LAN_LOCAL": "LAN Local",
    "GUEST_IN": "Guest In",
    "GUEST_OUT": "Guest Out",
    "GUEST_LOCAL": "Guest Local",
}


def format_action(action: str) -> tuple[str, str]:
    """Format action with color."""
    action_lower = action.lower()
    if action_lower == "accept":
        return "accept", "green"
    elif action_lower == "drop":
        return "drop", "red"
    elif action_lower == "reject":
        return "reject", "yellow"
    return action, "white"


def format_protocol(rule: dict[str, Any]) -> str:
    """Format protocol for display."""
    protocol = rule.get("protocol", "all")
    if protocol == "all":
        return "any"
    return protocol.upper()


def format_address(rule: dict[str, Any], prefix: str) -> str:
    """Format source or destination address."""
    # Check for network type
    net_type = rule.get(f"{prefix}_network_type", "")
    if net_type == "ADDRv4":
        addr = rule.get(f"{prefix}_address", "")
        return addr if addr else "any"

    # Check for firewall group
    group = rule.get(f"{prefix}_firewallgroup_ids", [])
    if group:
        return f"group:{len(group)}"

    # Check for specific network
    network = rule.get(f"{prefix}_network", "")
    if network:
        return network

    return "any"


def format_port(rule: dict[str, Any], prefix: str) -> str:
    """Format port information."""
    port = rule.get(f"{prefix}_port", "")
    if port:
        return str(port)
    return "*"


def get_ruleset_order(ruleset: str) -> int:
    """Get sort order for rulesets."""
    order = ["WAN_IN", "WAN_OUT", "WAN_LOCAL", "LAN_IN", "LAN_OUT", "LAN_LOCAL", "GUEST_IN", "GUEST_OUT", "GUEST_LOCAL"]
    try:
        return order.index(ruleset)
    except ValueError:
        return 100


@app.command("list")
def list_rules(
    ruleset: Annotated[
        str | None,
        typer.Option("--ruleset", "-r", help="Filter by ruleset (e.g., WAN_IN, LAN_IN)"),
    ] = None,
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Show additional details"),
    ] = False,
) -> None:
    """List firewall rules."""

    async def _list():
        client = UniFiLocalClient()
        return await client.get_firewall_rules()

    try:
        rules = asyncio.run(_list())
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if not rules:
        console.print("[dim]No firewall rules found[/dim]")
        return

    # Filter by ruleset if specified
    if ruleset:
        ruleset_upper = ruleset.upper()
        rules = [r for r in rules if r.get("ruleset", "").upper() == ruleset_upper]
        if not rules:
            console.print(f"[dim]No rules found for ruleset '{ruleset}'[/dim]")
            return

    # Sort by ruleset then by rule index
    rules.sort(key=lambda r: (get_ruleset_order(r.get("ruleset", "")), r.get("rule_index", 0)))

    if output == OutputFormat.JSON:
        output_json(rules)
    elif output == OutputFormat.CSV:
        columns = [
            ("name", "Name"),
            ("ruleset", "Ruleset"),
            ("action", "Action"),
            ("protocol", "Protocol"),
            ("src_address", "Source"),
            ("dst_address", "Destination"),
            ("enabled", "Enabled"),
        ]
        csv_data = []
        for r in rules:
            csv_data.append({
                "name": r.get("name", ""),
                "ruleset": r.get("ruleset", ""),
                "action": r.get("action", ""),
                "protocol": format_protocol(r),
                "src_address": format_address(r, "src"),
                "dst_address": format_address(r, "dst"),
                "enabled": "Yes" if r.get("enabled", True) else "No",
            })
        output_csv(csv_data, columns)
    else:
        from rich.table import Table

        table = Table(title="Firewall Rules", show_header=True, header_style="bold cyan")
        table.add_column("Name")
        table.add_column("Ruleset")
        table.add_column("Action")
        table.add_column("Protocol")
        table.add_column("Source")
        table.add_column("Destination")
        if verbose:
            table.add_column("Src Port")
            table.add_column("Dst Port")
        table.add_column("Enabled")

        for r in rules:
            name = r.get("name", "(unnamed)")
            ruleset_name = RULESET_NAMES.get(r.get("ruleset", ""), r.get("ruleset", ""))
            action, action_style = format_action(r.get("action", ""))
            protocol = format_protocol(r)
            src = format_address(r, "src")
            dst = format_address(r, "dst")
            enabled = "[green]✓[/green]" if r.get("enabled", True) else "[dim]✗[/dim]"

            if verbose:
                src_port = format_port(r, "src")
                dst_port = format_port(r, "dst")
                table.add_row(
                    name,
                    ruleset_name,
                    f"[{action_style}]{action}[/{action_style}]",
                    protocol,
                    src,
                    dst,
                    src_port,
                    dst_port,
                    enabled,
                )
            else:
                table.add_row(
                    name,
                    ruleset_name,
                    f"[{action_style}]{action}[/{action_style}]",
                    protocol,
                    src,
                    dst,
                    enabled,
                )

        console.print(table)
        console.print(f"\n[dim]{len(rules)} rule(s)[/dim]")


@app.command("groups")
def list_groups(
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format"),
    ] = OutputFormat.TABLE,
) -> None:
    """List firewall groups (address and port groups)."""

    async def _list():
        client = UniFiLocalClient()
        return await client.get_firewall_groups()

    try:
        groups = asyncio.run(_list())
    except LocalAPIError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if not groups:
        console.print("[dim]No firewall groups found[/dim]")
        return

    # Sort by type then name
    groups.sort(key=lambda g: (g.get("group_type", ""), g.get("name", "")))

    if output == OutputFormat.JSON:
        output_json(groups)
    elif output == OutputFormat.CSV:
        columns = [
            ("_id", "ID"),
            ("name", "Name"),
            ("group_type", "Type"),
            ("members", "Members"),
        ]
        csv_data = []
        for g in groups:
            members = g.get("group_members", [])
            csv_data.append({
                "_id": g.get("_id", ""),
                "name": g.get("name", ""),
                "group_type": g.get("group_type", ""),
                "members": ", ".join(members) if members else "",
            })
        output_csv(csv_data, columns)
    else:
        from rich.table import Table

        table = Table(title="Firewall Groups", show_header=True, header_style="bold cyan")
        table.add_column("ID", style="dim")
        table.add_column("Name")
        table.add_column("Type")
        table.add_column("Members")

        for g in groups:
            group_id = g.get("_id", "")
            name = g.get("name", "")
            group_type = g.get("group_type", "")

            # Format type for display
            type_display = group_type.replace("-", " ").title()

            # Format members
            members = g.get("group_members", [])
            if len(members) <= 3:
                members_str = ", ".join(members) if members else "[dim]-[/dim]"
            else:
                members_str = f"{', '.join(members[:3])}... (+{len(members) - 3})"

            table.add_row(group_id, name, type_display, members_str)

        console.print(table)
        console.print(f"\n[dim]{len(groups)} group(s)[/dim]")
