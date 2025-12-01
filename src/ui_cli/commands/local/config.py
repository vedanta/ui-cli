"""Running configuration commands for local controller."""

import asyncio
from datetime import datetime, timezone
from enum import Enum
from typing import Annotated

import typer

from ui_cli.local_client import (
    LocalAPIError,
    LocalAuthenticationError,
    LocalConnectionError,
    UniFiLocalClient,
)
from ui_cli.output import OutputFormat, console, output_json

app = typer.Typer(help="View running configuration")


class ConfigSection(str, Enum):
    """Configuration sections."""
    ALL = "all"
    NETWORKS = "networks"
    WIRELESS = "wireless"
    FIREWALL = "firewall"
    DEVICES = "devices"
    PORTFWD = "portfwd"
    DHCP = "dhcp"
    ROUTING = "routing"


def handle_error(e: Exception) -> None:
    """Handle and display API errors."""
    if isinstance(e, LocalAuthenticationError):
        console.print(f"[red]Authentication error:[/red] {e.message}")
    elif isinstance(e, LocalConnectionError):
        console.print(f"[red]Connection error:[/red] {e.message}")
    elif isinstance(e, LocalAPIError):
        console.print(f"[red]API error:[/red] {e.message}")
    else:
        console.print(f"[red]Error:[/red] {e}")
    raise typer.Exit(1)


def format_uptime(seconds: int) -> str:
    """Format uptime seconds to human-readable string."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}m"
    elif seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{days}d {hours}h"


# ============================================================
# Formatting Functions for Each Section
# ============================================================

def format_networks_section(networks: list[dict], verbose: bool = False) -> None:
    """Format and print networks section."""
    if not networks:
        console.print("  [dim](no networks configured)[/dim]")
        return

    for net in sorted(networks, key=lambda x: x.get("vlan_enabled", False) and x.get("vlan", 0) or 0):
        name = net.get("name", "Unnamed")
        purpose = net.get("purpose", "unknown")

        # VLAN info
        vlan = net.get("vlan", "")
        vlan_str = f" (VLAN {vlan})" if net.get("vlan_enabled") and vlan else ""

        console.print(f"  [bold]{name}[/bold]{vlan_str}")
        console.print(f"    [dim]Purpose:[/dim]       {purpose}")

        # Subnet info
        subnet = net.get("ip_subnet", "")
        if subnet:
            console.print(f"    [dim]Subnet:[/dim]        {subnet}")

        # Gateway
        gateway = net.get("ipv4_gateway", "") or net.get("gateway", "")
        if not gateway and subnet:
            # Derive gateway from subnet (usually .1)
            parts = subnet.split("/")
            if parts:
                ip_parts = parts[0].split(".")
                if len(ip_parts) == 4:
                    gateway = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.1"
        if gateway:
            console.print(f"    [dim]Gateway:[/dim]       {gateway}")

        # DHCP
        dhcp_enabled = net.get("dhcpd_enabled", False)
        if dhcp_enabled:
            dhcp_start = net.get("dhcpd_start", "")
            dhcp_stop = net.get("dhcpd_stop", "")
            if dhcp_start and dhcp_stop:
                console.print(f"    [dim]DHCP:[/dim]          Enabled ({dhcp_start} - {dhcp_stop})")
            else:
                console.print(f"    [dim]DHCP:[/dim]          Enabled")
        else:
            console.print(f"    [dim]DHCP:[/dim]          Disabled")

        # DNS
        dns1 = net.get("dhcpd_dns_1", "")
        dns2 = net.get("dhcpd_dns_2", "")
        if dns1 or dns2:
            dns_list = [d for d in [dns1, dns2] if d]
            console.print(f"    [dim]DNS:[/dim]           {', '.join(dns_list)}")

        # Domain
        domain = net.get("domain_name", "")
        if domain:
            console.print(f"    [dim]Domain:[/dim]        {domain}")

        # Isolation
        if net.get("network_isolation", False):
            console.print(f"    [dim]Isolation:[/dim]     [yellow]Yes[/yellow]")

        # Internet access
        if net.get("internet_access_enabled") is False:
            console.print(f"    [dim]Internet:[/dim]      [red]Blocked[/red]")

        if verbose:
            net_id = net.get("_id", "")
            if net_id:
                console.print(f"    [dim]ID:[/dim]            {net_id}")

        console.print()


def format_wireless_section(wlans: list[dict], networks: list[dict], verbose: bool = False) -> None:
    """Format and print wireless section."""
    if not wlans:
        console.print("  [dim](no wireless networks configured)[/dim]")
        return

    # Build network ID to name mapping
    net_map = {n.get("_id"): n.get("name", "Unknown") for n in networks}

    for wlan in sorted(wlans, key=lambda x: x.get("name", "")):
        name = wlan.get("name", "Unnamed")
        enabled = wlan.get("enabled", True)

        status = "" if enabled else " [red](disabled)[/red]"
        console.print(f"  [bold]{name}[/bold]{status}")

        # Network mapping
        network_id = wlan.get("networkconf_id", "")
        network_name = net_map.get(network_id, "Default")
        console.print(f"    [dim]Network:[/dim]       {network_name}")

        # Security
        security = wlan.get("security", "open")
        wpa_mode = wlan.get("wpa_mode", "")
        wpa3 = wlan.get("wpa3_support", False)

        if security == "wpapsk":
            if wpa3:
                sec_str = "WPA2/WPA3 Personal"
            elif wpa_mode == "wpa2":
                sec_str = "WPA2 Personal"
            else:
                sec_str = "WPA Personal"
        elif security == "wpaeap":
            sec_str = "WPA Enterprise"
        elif security == "open":
            sec_str = "Open"
        else:
            sec_str = security
        console.print(f"    [dim]Security:[/dim]      {sec_str}")

        # Bands
        wlan_band = wlan.get("wlan_band", "both")
        if wlan_band == "2g":
            band_str = "2.4 GHz only"
        elif wlan_band == "5g":
            band_str = "5 GHz only"
        else:
            band_str = "2.4 GHz + 5 GHz"
        console.print(f"    [dim]Band:[/dim]          {band_str}")

        # Hidden SSID
        if wlan.get("hide_ssid", False):
            console.print(f"    [dim]Hidden:[/dim]        Yes")

        # Guest network
        if wlan.get("is_guest", False):
            console.print(f"    [dim]Guest:[/dim]         Yes")

        # Client isolation
        if wlan.get("ap_group_isolation", False) or wlan.get("l2_isolation", False):
            console.print(f"    [dim]Isolation:[/dim]     Yes")

        # Fast roaming
        if wlan.get("fast_roaming_enabled", False):
            console.print(f"    [dim]Fast Roaming:[/dim] Yes")

        # PMF
        pmf = wlan.get("pmf_mode", "")
        if pmf:
            console.print(f"    [dim]PMF:[/dim]           {pmf}")

        if verbose:
            wlan_id = wlan.get("_id", "")
            if wlan_id:
                console.print(f"    [dim]ID:[/dim]            {wlan_id}")

        console.print()


def format_firewall_section(rules: list[dict], groups: list[dict], verbose: bool = False) -> None:
    """Format and print firewall section."""
    # Build group ID to name mapping
    group_map = {g.get("_id"): g.get("name", "Unknown") for g in groups}

    # Group rules by ruleset
    rulesets: dict[str, list] = {}
    for rule in rules:
        ruleset = rule.get("ruleset", "unknown")
        if ruleset not in rulesets:
            rulesets[ruleset] = []
        rulesets[ruleset].append(rule)

    # Sort rulesets in logical order
    ruleset_order = ["WAN_IN", "WAN_OUT", "WAN_LOCAL", "LAN_IN", "LAN_OUT", "LAN_LOCAL", "GUEST_IN", "GUEST_OUT"]
    sorted_rulesets = sorted(rulesets.keys(), key=lambda x: ruleset_order.index(x) if x in ruleset_order else 99)

    if not rules:
        console.print("  [dim](no custom firewall rules)[/dim]")
    else:
        for ruleset in sorted_rulesets:
            ruleset_rules = sorted(rulesets[ruleset], key=lambda x: x.get("rule_index", 0))
            console.print(f"  [bold]{ruleset}[/bold] ({len(ruleset_rules)} rules)")

            for rule in ruleset_rules:
                idx = rule.get("rule_index", "")
                name = rule.get("name", "Unnamed")
                action = rule.get("action", "").upper()
                enabled = rule.get("enabled", True)

                # Color code action
                if action == "DROP" or action == "REJECT":
                    action_str = f"[red]{action}[/red]"
                elif action == "ACCEPT":
                    action_str = f"[green]{action}[/green]"
                else:
                    action_str = action

                status = "" if enabled else " [dim](disabled)[/dim]"

                # Source/destination
                src = rule.get("src_firewallgroup_ids", [])
                dst = rule.get("dst_firewallgroup_ids", [])
                src_str = ", ".join([group_map.get(s, s) for s in src]) if src else "Any"
                dst_str = ", ".join([group_map.get(d, d) for d in dst]) if dst else "Any"

                # Protocol/port
                protocol = rule.get("protocol", "all")
                dst_port = rule.get("dst_port", "")
                proto_str = protocol.upper()
                if dst_port:
                    proto_str += f" {dst_port}"

                console.print(f"    {idx:4} {name[:25]:<25} {action_str:<8} {src_str[:12]:<12} → {dst_str[:12]:<12} {proto_str}{status}")

            console.print()

    # Firewall groups
    if groups:
        console.print(f"  [bold]Firewall Groups[/bold] ({len(groups)} groups)")
        for group in sorted(groups, key=lambda x: x.get("name", "")):
            name = group.get("name", "Unnamed")
            group_type = group.get("group_type", "unknown")
            members = group.get("group_members", [])

            type_str = {"address-group": "Address", "port-group": "Port", "network-group": "Network"}.get(group_type, group_type)
            members_str = ", ".join(members[:5])
            if len(members) > 5:
                members_str += f" (+{len(members) - 5} more)"

            console.print(f"    {name:<20} [{type_str}] {members_str}")
        console.print()


def format_port_forwards_section(forwards: list[dict], verbose: bool = False) -> None:
    """Format and print port forwarding section."""
    if not forwards:
        console.print("  [dim](no port forwards configured)[/dim]")
        return

    console.print(f"  {'Name':<20} {'Protocol':<10} {'WAN Port':<12} {'LAN IP':<16} {'LAN Port':<10} {'Enabled'}")
    console.print(f"  {'-' * 20} {'-' * 10} {'-' * 12} {'-' * 16} {'-' * 10} {'-' * 7}")

    for fwd in sorted(forwards, key=lambda x: x.get("name", "")):
        name = fwd.get("name", "Unnamed")[:20]
        proto = fwd.get("proto", "tcp_udp").upper()
        dst_port = fwd.get("dst_port", "")
        fwd_ip = fwd.get("fwd", "")
        fwd_port = fwd.get("fwd_port", dst_port)
        enabled = fwd.get("enabled", True)

        enabled_str = "[green]Yes[/green]" if enabled else "[red]No[/red]"

        console.print(f"  {name:<20} {proto:<10} {dst_port:<12} {fwd_ip:<16} {fwd_port:<10} {enabled_str}")

    console.print()


def format_devices_section(devices: list[dict], verbose: bool = False) -> None:
    """Format and print devices section."""
    if not devices:
        console.print("  [dim](no devices)[/dim]")
        return

    # Sort by type then name
    type_order = {"ugw": 0, "udm": 0, "usw": 1, "uap": 2, "uph": 3}
    sorted_devices = sorted(devices, key=lambda x: (type_order.get(x.get("type", ""), 99), x.get("name", "")))

    for dev in sorted_devices:
        name = dev.get("name", "Unnamed")
        model = dev.get("model", "Unknown")
        dev_type = dev.get("type", "")
        ip = dev.get("ip", "")
        mac = dev.get("mac", "").upper()
        version = dev.get("version", "")
        state = dev.get("state", 0)
        uptime = dev.get("uptime", 0)

        # Device type label
        type_labels = {"ugw": "Gateway", "udm": "Gateway", "usw": "Switch", "uap": "AP", "uph": "Phone"}
        type_label = type_labels.get(dev_type, dev_type.upper())

        # State
        state_str = ""
        if state == 1:
            state_str = "[green]online[/green]"
        elif state == 0:
            state_str = "[red]offline[/red]"
        else:
            state_str = f"[yellow]state:{state}[/yellow]"

        console.print(f"  [bold]{name}[/bold] ({model}) {state_str}")
        console.print(f"    [dim]Type:[/dim]          {type_label}")
        console.print(f"    [dim]IP:[/dim]            {ip}")
        console.print(f"    [dim]MAC:[/dim]           {mac}")
        if version:
            console.print(f"    [dim]Firmware:[/dim]      {version}")
        if uptime:
            console.print(f"    [dim]Uptime:[/dim]        {format_uptime(uptime)}")

        # AP-specific: radio info
        if dev_type == "uap":
            radio_table = dev.get("radio_table", [])
            for radio in radio_table:
                radio_type = radio.get("radio", "")
                channel = radio.get("channel", "")
                ht = radio.get("ht", "")
                tx_power = radio.get("tx_power", "")

                if radio_type == "ng":
                    band = "2.4G"
                elif radio_type == "na":
                    band = "5G"
                else:
                    band = radio_type

                ht_str = f" ({ht})" if ht else ""
                power_str = f", {tx_power}dBm" if tx_power else ""
                console.print(f"    [dim]Channel {band}:[/dim]   {channel}{ht_str}{power_str}")

        # Switch-specific: port info
        if dev_type == "usw" and verbose:
            port_table = dev.get("port_table", [])
            if port_table:
                up_ports = [p for p in port_table if p.get("up", False)]
                console.print(f"    [dim]Ports:[/dim]         {len(up_ports)}/{len(port_table)} up")

        if verbose:
            dev_id = dev.get("_id", "")
            if dev_id:
                console.print(f"    [dim]ID:[/dim]            {dev_id}")

        console.print()


def format_dhcp_reservations_section(reservations: list[dict], networks: list[dict], verbose: bool = False) -> None:
    """Format and print DHCP reservations section."""
    if not reservations:
        console.print("  [dim](no DHCP reservations)[/dim]")
        return

    # Build network ID to name mapping
    net_map = {n.get("_id"): n.get("name", "Unknown") for n in networks}

    console.print(f"  {'Name':<20} {'MAC':<18} {'IP':<16} {'Network'}")
    console.print(f"  {'-' * 20} {'-' * 18} {'-' * 16} {'-' * 15}")

    for res in sorted(reservations, key=lambda x: x.get("name", "") or x.get("hostname", "")):
        name = (res.get("name") or res.get("hostname") or "Unknown")[:20]
        mac = res.get("mac", "").upper()
        ip = res.get("fixed_ip", "")
        network_id = res.get("network_id", "")
        network_name = net_map.get(network_id, "Default")

        console.print(f"  {name:<20} {mac:<18} {ip:<16} {network_name}")

    console.print()


def format_routing_section(routes: list[dict], verbose: bool = False) -> None:
    """Format and print static routing section."""
    if not routes:
        console.print("  [dim](no static routes configured)[/dim]")
        return

    console.print(f"  {'Name':<20} {'Destination':<20} {'Gateway/Interface':<20} {'Enabled'}")
    console.print(f"  {'-' * 20} {'-' * 20} {'-' * 20} {'-' * 7}")

    for route in sorted(routes, key=lambda x: x.get("name", "")):
        name = route.get("name", "Unnamed")[:20]
        dest = route.get("static_route_network", "")
        gateway = route.get("static_route_nexthop", "") or route.get("static_route_interface", "")
        enabled = route.get("enabled", True)

        enabled_str = "[green]Yes[/green]" if enabled else "[red]No[/red]"

        console.print(f"  {name:<20} {dest:<20} {gateway:<20} {enabled_str}")

    console.print()


def to_yaml(config: dict, hide_secrets: bool = True) -> str:
    """Convert config to YAML format."""
    lines = []
    lines.append("# UniFi Running Configuration")
    lines.append(f"# Exported: {datetime.now(timezone.utc).isoformat()}")
    lines.append("")

    def yaml_value(v, indent=0):
        """Convert a value to YAML string."""
        prefix = "  " * indent
        if v is None:
            return "null"
        elif isinstance(v, bool):
            return "true" if v else "false"
        elif isinstance(v, (int, float)):
            return str(v)
        elif isinstance(v, str):
            # Hide passwords/secrets
            if hide_secrets and any(s in v.lower() for s in ["password", "secret", "key", "x_passphrase"]):
                return '"********"'
            if "\n" in v or ":" in v or '"' in v:
                return f'"{v}"'
            return v if v else '""'
        elif isinstance(v, list):
            if not v:
                return "[]"
            if all(isinstance(i, (str, int, float, bool)) for i in v):
                return "[" + ", ".join(yaml_value(i) for i in v) + "]"
            return v  # Complex list, handle separately
        elif isinstance(v, dict):
            return v  # Handle separately
        return str(v)

    def write_dict(d, indent=0):
        """Write a dict as YAML."""
        prefix = "  " * indent
        for k, v in d.items():
            # Skip internal fields
            if k.startswith("_") and k != "_id":
                continue
            # Hide secret fields
            if hide_secrets and any(s in k.lower() for s in ["password", "secret", "x_passphrase", "wpa_psk"]):
                lines.append(f"{prefix}{k}: \"********\"")
                continue

            val = yaml_value(v, indent)
            if isinstance(val, dict):
                lines.append(f"{prefix}{k}:")
                write_dict(val, indent + 1)
            elif isinstance(val, list) and val and isinstance(val[0], dict):
                lines.append(f"{prefix}{k}:")
                for item in val:
                    lines.append(f"{prefix}  -")
                    write_dict(item, indent + 2)
            else:
                lines.append(f"{prefix}{k}: {val}")

    # Networks
    if config.get("networks"):
        lines.append("networks:")
        for net in config["networks"]:
            lines.append(f"  - name: {net.get('name', 'Unknown')}")
            for k, v in net.items():
                if k == "name" or k.startswith("_"):
                    continue
                val = yaml_value(v)
                if not isinstance(val, (dict, list)) or (isinstance(val, list) and isinstance(val, str)):
                    lines.append(f"    {k}: {val}")
        lines.append("")

    # Wireless
    if config.get("wireless"):
        lines.append("wireless:")
        for wlan in config["wireless"]:
            lines.append(f"  - name: {wlan.get('name', 'Unknown')}")
            for k, v in wlan.items():
                if k == "name" or k.startswith("_"):
                    continue
                if hide_secrets and any(s in k.lower() for s in ["password", "x_passphrase", "wpa_psk"]):
                    lines.append(f"    {k}: \"********\"")
                    continue
                val = yaml_value(v)
                if not isinstance(val, (dict, list)) or (isinstance(val, list) and isinstance(val, str)):
                    lines.append(f"    {k}: {val}")
        lines.append("")

    # Firewall rules
    if config.get("firewall_rules"):
        lines.append("firewall_rules:")
        for rule in config["firewall_rules"]:
            lines.append(f"  - name: {rule.get('name', 'Unknown')}")
            lines.append(f"    ruleset: {rule.get('ruleset', '')}")
            lines.append(f"    action: {rule.get('action', '')}")
            lines.append(f"    enabled: {yaml_value(rule.get('enabled', True))}")
        lines.append("")

    # Port forwards
    if config.get("port_forwards"):
        lines.append("port_forwards:")
        for fwd in config["port_forwards"]:
            lines.append(f"  - name: {fwd.get('name', 'Unknown')}")
            lines.append(f"    dst_port: {fwd.get('dst_port', '')}")
            lines.append(f"    fwd: {fwd.get('fwd', '')}")
            lines.append(f"    fwd_port: {fwd.get('fwd_port', '')}")
            lines.append(f"    proto: {fwd.get('proto', 'tcp_udp')}")
            lines.append(f"    enabled: {yaml_value(fwd.get('enabled', True))}")
        lines.append("")

    # DHCP reservations
    if config.get("dhcp_reservations"):
        lines.append("dhcp_reservations:")
        for res in config["dhcp_reservations"]:
            name = res.get("name") or res.get("hostname") or "Unknown"
            lines.append(f"  - name: {name}")
            lines.append(f"    mac: {res.get('mac', '')}")
            lines.append(f"    fixed_ip: {res.get('fixed_ip', '')}")
        lines.append("")

    # Devices
    if config.get("devices"):
        lines.append("devices:")
        for dev in config["devices"]:
            lines.append(f"  - name: {dev.get('name', 'Unknown')}")
            lines.append(f"    model: {dev.get('model', '')}")
            lines.append(f"    mac: {dev.get('mac', '').upper()}")
            lines.append(f"    ip: {dev.get('ip', '')}")
            lines.append(f"    type: {dev.get('type', '')}")
        lines.append("")

    return "\n".join(lines)


# ============================================================
# Commands
# ============================================================

@app.command("show")
def show_config(
    section: Annotated[
        ConfigSection,
        typer.Option("--section", "-s", help="Section to show"),
    ] = ConfigSection.ALL,
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format (table, json, yaml)"),
    ] = OutputFormat.TABLE,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Show additional details (IDs, etc)"),
    ] = False,
    hide_secrets: Annotated[
        bool,
        typer.Option("--hide-secrets/--show-secrets", help="Hide passwords and keys"),
    ] = True,
) -> None:
    """Show running configuration.

    Displays the current active configuration of your UniFi network
    including networks, wireless, firewall, devices, and more.

    Examples:
        ./ui lo config show                    # Full config
        ./ui lo config show -s networks        # Just networks
        ./ui lo config show -s firewall        # Just firewall
        ./ui lo config show -o yaml            # Export as YAML
        ./ui lo config show -o json            # Export as JSON
        ./ui lo config show --show-secrets     # Include passwords
    """
    try:
        client = UniFiLocalClient()

        async def _fetch_config():
            # Fetch only what we need based on section
            if section == ConfigSection.ALL:
                return await client.get_running_config()
            elif section == ConfigSection.NETWORKS:
                return {"networks": await client.get_networks()}
            elif section == ConfigSection.WIRELESS:
                return {
                    "wireless": await client.get_wlans(),
                    "networks": await client.get_networks(),  # For network name mapping
                }
            elif section == ConfigSection.FIREWALL:
                return {
                    "firewall_rules": await client.get_firewall_rules(),
                    "firewall_groups": await client.get_firewall_groups(),
                }
            elif section == ConfigSection.DEVICES:
                return {"devices": await client.get_devices()}
            elif section == ConfigSection.PORTFWD:
                return {"port_forwards": await client.get_port_forwards()}
            elif section == ConfigSection.DHCP:
                return {
                    "dhcp_reservations": await client.get_dhcp_reservations(),
                    "networks": await client.get_networks(),
                }
            elif section == ConfigSection.ROUTING:
                return {"routing": await client.get_routing()}
            return {}

        config = asyncio.run(_fetch_config())
    except Exception as e:
        handle_error(e)
        return

    # Handle different output formats
    if output == OutputFormat.JSON:
        # For JSON, optionally hide secrets
        if hide_secrets:
            def redact_secrets(obj):
                if isinstance(obj, dict):
                    return {
                        k: "********" if any(s in k.lower() for s in ["password", "secret", "x_passphrase", "wpa_psk"]) else redact_secrets(v)
                        for k, v in obj.items()
                    }
                elif isinstance(obj, list):
                    return [redact_secrets(i) for i in obj]
                return obj
            config = redact_secrets(config)
        output_json(config)
        return

    if output.value == "yaml" or str(output) == "yaml":
        console.print(to_yaml(config, hide_secrets=hide_secrets))
        return

    # Table output
    controller_url = client.controller_url
    site = client.site
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    console.print()
    console.print("[bold]UniFi Running Configuration[/bold]")
    console.print("═" * 70)
    console.print(f"Controller: {controller_url}")
    console.print(f"Site: {site}")
    console.print(f"Exported: {timestamp}")
    console.print("═" * 70)
    console.print()

    # Networks section
    if section in (ConfigSection.ALL, ConfigSection.NETWORKS):
        networks = config.get("networks", [])
        console.print("┌─ [bold]NETWORKS[/bold] " + "─" * 58 + "┐")
        console.print()
        format_networks_section(networks, verbose)
        console.print("└" + "─" * 70 + "┘")
        console.print()

    # Wireless section
    if section in (ConfigSection.ALL, ConfigSection.WIRELESS):
        wlans = config.get("wireless", [])
        networks = config.get("networks", [])
        console.print("┌─ [bold]WIRELESS[/bold] " + "─" * 58 + "┐")
        console.print()
        format_wireless_section(wlans, networks, verbose)
        console.print("└" + "─" * 70 + "┘")
        console.print()

    # Firewall section
    if section in (ConfigSection.ALL, ConfigSection.FIREWALL):
        rules = config.get("firewall_rules", [])
        groups = config.get("firewall_groups", [])
        console.print("┌─ [bold]FIREWALL[/bold] " + "─" * 58 + "┐")
        console.print()
        format_firewall_section(rules, groups, verbose)
        console.print("└" + "─" * 70 + "┘")
        console.print()

    # Port forwarding section
    if section in (ConfigSection.ALL, ConfigSection.PORTFWD):
        forwards = config.get("port_forwards", [])
        console.print("┌─ [bold]PORT FORWARDING[/bold] " + "─" * 51 + "┐")
        console.print()
        format_port_forwards_section(forwards, verbose)
        console.print("└" + "─" * 70 + "┘")
        console.print()

    # DHCP reservations section
    if section in (ConfigSection.ALL, ConfigSection.DHCP):
        reservations = config.get("dhcp_reservations", [])
        networks = config.get("networks", [])
        console.print("┌─ [bold]DHCP RESERVATIONS[/bold] " + "─" * 49 + "┐")
        console.print()
        format_dhcp_reservations_section(reservations, networks, verbose)
        console.print("└" + "─" * 70 + "┘")
        console.print()

    # Routing section
    if section in (ConfigSection.ALL, ConfigSection.ROUTING):
        routes = config.get("routing", [])
        console.print("┌─ [bold]STATIC ROUTES[/bold] " + "─" * 53 + "┐")
        console.print()
        format_routing_section(routes, verbose)
        console.print("└" + "─" * 70 + "┘")
        console.print()

    # Devices section
    if section in (ConfigSection.ALL, ConfigSection.DEVICES):
        devices = config.get("devices", [])
        console.print("┌─ [bold]DEVICES[/bold] " + "─" * 59 + "┐")
        console.print()
        format_devices_section(devices, verbose)
        console.print("└" + "─" * 70 + "┘")
        console.print()

    # Summary
    if section == ConfigSection.ALL:
        networks_count = len(config.get("networks", []))
        wlans_count = len(config.get("wireless", []))
        rules_count = len(config.get("firewall_rules", []))
        forwards_count = len(config.get("port_forwards", []))
        devices_count = len(config.get("devices", []))
        dhcp_count = len(config.get("dhcp_reservations", []))

        console.print(f"[dim]Summary: {networks_count} networks, {wlans_count} SSIDs, {rules_count} firewall rules, {forwards_count} port forwards, {devices_count} devices, {dhcp_count} DHCP reservations[/dim]")
        console.print()
