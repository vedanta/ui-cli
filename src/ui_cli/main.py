"""UniFi Site Manager CLI - Main entry point."""

import typer

from ui_cli import __version__
from ui_cli.commands import devices, hosts, isp, sdwan, sites, speedtest, status, version
from ui_cli.commands import local

# Create main app
app = typer.Typer(
    name="ui",
    help="UniFi Site Manager CLI - Manage your UniFi infrastructure from the command line.",
    no_args_is_help=True,
    add_completion=True,
)

# Register command groups
app.add_typer(status.app, name="status")
app.add_typer(hosts.app, name="hosts")
app.add_typer(sites.app, name="sites")
app.add_typer(devices.app, name="devices")
app.add_typer(isp.app, name="isp")
app.add_typer(sdwan.app, name="sdwan")
app.add_typer(version.app, name="version")
app.add_typer(speedtest.app, name="speedtest")

# Local controller commands (with alias)
app.add_typer(local.app, name="local")
app.add_typer(local.app, name="lo")


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo(f"ui-cli version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-V",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """UniFi Site Manager CLI - Manage your UniFi infrastructure from the command line."""
    pass


if __name__ == "__main__":
    app()
