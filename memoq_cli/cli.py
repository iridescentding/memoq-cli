# -*- coding: utf-8 -*-
"""
memoQ CLI - Command Line Interface

memoQ Server CLI tool supporting WSAPI and RSAPI for project management,
file import/export, TM/TB management, and more.
"""

import sys
import json
from pathlib import Path
import click

from .config import get_config, Config, reset_config
from .utils import setup_logging
from .commands import project, file, tm, tb, template, resource


def _mask_secret(value: str) -> str:
    """Return a short masked representation for terminal summaries."""
    if not value:
        return ""
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


@click.group()
@click.option("--config", "-c", type=click.Path(), help="Configuration file path")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output (DEBUG level)")
@click.option("--quiet", "-q", is_flag=True, help="Quiet mode (errors only)")
@click.option("--soap-debug", is_flag=True, help="Log SOAP request/response XML for debugging")
@click.version_option(version="1.0.0", prog_name="memoq-cli")
@click.pass_context
def cli(ctx, config, verbose, quiet, soap_debug):
    """memoQ CLI - memoQ Server command line tool

    Supports WSAPI and RSAPI for project management, file import/export,
    TM/TB management, and more.

    \b
    Quick Start:
        1. Run 'memoq init' to create config file
        2. Run 'memoq project list' to list projects
        3. Run 'memoq --help' for all commands

    \b
    Config file locations (by priority):
        1. ./config.json (current directory)
        2. ~/.memoq/config.json
        3. ~/.config/memoq/config.json
    """
    ctx.ensure_object(dict)

    # Determine log level
    if quiet:
        log_level = "ERROR"
    elif verbose:
        log_level = "DEBUG"
    else:
        log_level = "INFO"

    # Load configuration
    try:
        if config:
            reset_config()
        cfg = get_config(config)
        log_level = log_level if verbose or quiet else cfg.log_level
    except FileNotFoundError:
        if ctx.invoked_subcommand not in ["init", None]:
            click.echo("Warning: Config file not found. Run 'memoq init' first.", err=True)
            sys.exit(1)
        cfg = Config.__new__(Config)
        cfg._config = {}

    # Setup logging
    log_file = getattr(cfg, 'log_file', None) if hasattr(cfg, 'log_file') else None
    setup_logging(level=log_level, log_file=log_file if log_file else None)

    # Enable SOAP debug logging if requested
    if soap_debug:
        from .wsapi.client import set_soap_debug
        set_soap_debug(True)

    ctx.obj["config"] = cfg
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    ctx.obj["soap_debug"] = soap_debug


# Register command groups
cli.add_command(project)
cli.add_command(file)
cli.add_command(tm)
cli.add_command(tb)
cli.add_command(template)
cli.add_command(resource)


@cli.command()
@click.option("--host", prompt="memoQ Server host (e.g., https://memoq.example.com)",
              help="Server address (without port)")
@click.option("--wsapi-port", default=8080, prompt="WSAPI port",
              help="WSAPI port", type=int)
@click.option("--rsapi-port", default=8082, prompt="RSAPI port",
              help="RSAPI port", type=int)
@click.option("--rsapi-path", default="memoqserverhttpapi/v1", prompt="RSAPI path",
              help="RSAPI API path")
@click.option("--api-key", prompt="API Key (for WSAPI)",
              help="API Key for WSAPI authentication")
@click.option("--username", prompt="RSAPI Username (memoQ user with API access)",
              help="Username for RSAPI authentication")
@click.option("--password", prompt="RSAPI Password", hide_input=True,
              help="Password for RSAPI authentication")
@click.option("--output", "-o", default="config.json", help="Output config file path")
def init(host, wsapi_port, rsapi_port, rsapi_path, api_key, username, password, output):
    """Initialize configuration file

    \b
    Example:
        memoq init
        memoq init -o ~/.memoq/config.json
    """
    config_data = {
        "server": {
            "host": host.rstrip("/"),
            "wsapi_port": wsapi_port,
            "rsapi_port": rsapi_port,
            "rsapi_path": rsapi_path.strip("/")
        },
        "auth": {
            "api_key": api_key,
            "username": username,
            "password": password
        },
        "export": {
            "default_path": "./exports",
            "xliff_version": "1.2"
        },
        "import": {
            "default_path": "./imports",
            "filter_system_files": True
        },
        "logging": {
            "level": "INFO",
            "log_file": "memoq_cli.log"
        }
    }

    config_path = Path(output)
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=4, ensure_ascii=False)

    click.echo(f"\nDone: Config file created at {config_path.absolute()}")
    click.echo(f"\nSummary:")
    click.echo(f"   Server:        {host}")
    click.echo(f"   WSAPI:         {host}:{wsapi_port}")
    click.echo(f"   RSAPI:         {host}:{rsapi_port}/{rsapi_path}")
    click.echo(f"   API Key:       {_mask_secret(api_key)}")
    click.echo(f"   RSAPI User:    {username}")
    click.echo(f"\nTip: Edit the config file to modify settings")


@cli.command("config")
@click.option("--show", "-s", is_flag=True, help="Show current config")
@click.option("--path", "-p", is_flag=True, help="Show config file path")
@click.option("--set", "-S", "set_value", nargs=2, multiple=True,
              metavar="KEY VALUE", help="Set config value (e.g., --set server.host https://new.com)")
@click.option("--get", "-g", "get_key", help="Get config value")
@click.pass_context
def config_cmd(ctx, show, path, set_value, get_key):
    """View or modify configuration

    \b
    Examples:
        memoq config --show
        memoq config --path
        memoq config --get server.host
        memoq config --set server.host https://new.com
    """
    cfg = ctx.obj.get("config")

    if path:
        if hasattr(cfg, '_config_path') and cfg._config_path:
            click.echo(f"Config file: {cfg._config_path}")
        else:
            click.echo("Config file not loaded")
        return

    if get_key:
        value = cfg.get(get_key) if hasattr(cfg, 'get') else None
        if value is not None:
            if isinstance(value, (dict, list)):
                click.echo(json.dumps(value, indent=2, ensure_ascii=False))
            else:
                click.echo(value)
        else:
            click.echo(f"Config key '{get_key}' not found", err=True)
        return

    if set_value:
        for key, value in set_value:
            try:
                parsed_value = json.loads(value)
            except json.JSONDecodeError:
                parsed_value = value

            cfg.set(key, parsed_value)
            click.echo(f"Set {key} = {parsed_value}")

        cfg.save()
        click.echo("Config saved")
        return

    # Default: show config
    if hasattr(cfg, 'to_dict'):
        click.echo(json.dumps(cfg.to_dict(), indent=2, ensure_ascii=False))
    else:
        click.echo("Config not loaded")


@cli.command("test")
@click.option("--wsapi", is_flag=True, help="Test WSAPI connection")
@click.option("--rsapi", is_flag=True, help="Test RSAPI connection")
@click.pass_context
def test_connection(ctx, wsapi, rsapi):
    """Test server connections

    \b
    Examples:
        memoq test --wsapi
        memoq test --rsapi
        memoq test --wsapi --rsapi
    """
    from .wsapi import WSAPIClient
    from .rsapi import RSAPIClient

    cfg = ctx.obj.get("config")

    if not wsapi and not rsapi:
        wsapi = rsapi = True

    click.echo("\nConnection Test\n")

    if wsapi:
        click.echo(f"WSAPI: {cfg.wsapi_base_url}")
        try:
            client = WSAPIClient()
            # Just test WSDL loading (connectivity check)
            soap_client = client.get_client("ServerProject")
            # Check if services are available
            services = list(soap_client.wsdl.services.keys())
            click.echo(f"  OK: WSDL loaded, services: {services}")
            client.close()
        except Exception as e:
            click.echo(f"  FAILED: {e}", err=True)

    if rsapi:
        click.echo(f"RSAPI: {cfg.rsapi_base_url}")
        try:
            client = RSAPIClient()
            # Just test endpoint connectivity
            response = client.session.get(
                f"{client.base_url}",
                timeout=10,
                verify=client.verify_ssl
            )
            click.echo(f"  OK: RSAPI reachable (HTTP {response.status_code})")
        except Exception as e:
            click.echo(f"  FAILED: {e}", err=True)


def main():
    """Main entry point"""
    cli()


if __name__ == "__main__":
    main()
