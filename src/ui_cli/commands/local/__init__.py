"""Local controller commands - ./ui local or ./ui lo."""

import typer

from ui_cli.commands.local import clients, config, devices, dpi, events, firewall, health, networks, portfwd, stats, vouchers

app = typer.Typer(
    name="local",
    help="Local UniFi Controller commands (UDM, Cloud Key, self-hosted)",
    no_args_is_help=True,
)

# Register subcommands
app.add_typer(clients.app, name="clients")
app.add_typer(config.app, name="config")
app.add_typer(devices.app, name="devices")
app.add_typer(dpi.app, name="dpi")
app.add_typer(events.app, name="events")
app.add_typer(firewall.app, name="firewall")
app.add_typer(health.app, name="health")
app.add_typer(networks.app, name="networks")
app.add_typer(portfwd.app, name="portfwd")
app.add_typer(stats.app, name="stats")
app.add_typer(vouchers.app, name="vouchers")
