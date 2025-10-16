"""
Passeur CLI.

Usage:
    passeur bridge start [--config CONFIG]
    passeur bridge stop
    passeur bridge status
    passeur cleanup [--config CONFIG]
"""

import sys

import click


@click.group()
def cli():
    """Passeur - Solana Bridge Management."""


@cli.group()
def bridge():
    """Bridge management commands."""


@bridge.command()
@click.option("--config", "-c", default="passeur.yaml", help="Config file")
def start(config):
    """Start bridge server."""
    from cli.bridge import start_bridge

    click.echo(f"Starting bridge (config: {config})...")
    if start_bridge(config):
        click.echo("Bridge started")
    else:
        click.echo("Failed to start bridge", err=True)
        sys.exit(1)


@bridge.command()
def stop():
    """Stop bridge server."""
    from cli.bridge import stop_bridge

    click.echo("🛑 Stopping bridge...")
    if stop_bridge():
        click.echo("Bridge stopped")
    else:
        click.echo("Failed to stop bridge", err=True)
        sys.exit(1)


@bridge.command()
def status():
    """Check bridge status."""
    from cli.bridge import check_bridge_status

    is_running, url = check_bridge_status()
    if is_running:
        click.echo(f"Running: {url}")
    else:
        click.echo("Not running")
        sys.exit(1)


@cli.command()
@click.option("--config", "-c", default="test.yaml", help="Config file")
def cleanup(config):
    """Cleanup test escrows."""
    from cli.cleanup import cleanup_escrows

    click.echo("Cleaning up escrows...")
    if cleanup_escrows(config):
        click.echo("Cleanup complete")
    else:
        click.echo("Cleanup failed", err=True)
        sys.exit(1)


def main():
    """Entry point."""
    cli()


if __name__ == "__main__":
    main()
