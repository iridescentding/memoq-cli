# -*- coding: utf-8 -*-
"""
memoQ callback commands.
"""

import click

from ..callback_server import CALLBACK_PATH, build_callback_url, start_callback_server
from ..utils import handle_api_error
from ..wsapi import ProjectManager


@click.group()
def callback():
    """memoQ callback receiver and project callback configuration."""
    pass


@callback.command("configure")
@click.argument("project_guid")
@click.option(
    "--base-url",
    default=None,
    help="Public base URL; /memoq-callback.asmx will be appended",
)
@click.option(
    "--callback-url",
    default=None,
    help="Full public callback URL ending in /memoq-callback.asmx",
)
@click.option("--path", default=CALLBACK_PATH, help="Callback path")
@click.pass_context
def configure_callback(ctx, project_guid, base_url, callback_url, path):
    """Set CallbackWebServiceUrl for an existing memoQ server project."""
    try:
        if bool(base_url) == bool(callback_url):
            raise click.ClickException(
                "Pass exactly one of --base-url or --callback-url."
            )

        final_url = callback_url or build_callback_url(base_url, path)

        pm = ProjectManager()
        pm.update_project(project_guid, callback_url=final_url)

        click.echo("Done: Project callback URL configured.")
        click.echo(f"  Project GUID: {project_guid}")
        click.echo(f"  Callback URL: {final_url}")

    except click.ClickException:
        raise
    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False))


@callback.command("serve")
@click.option("--host", default="0.0.0.0", show_default=True, help="Bind host")
@click.option("--port", default=8088, show_default=True, type=int, help="Bind port")
@click.option(
    "--events-path",
    default="memoq_callback_events.jsonl",
    show_default=True,
    help="JSONL file where received callbacks are appended",
)
@click.option("--forward-url", default=None, help="Optional JSON forwarding endpoint")
@click.option("--api-key-header", default=None, help="Optional forwarding API key header")
@click.option("--api-key", default=None, help="Optional forwarding API key value")
@click.option(
    "--timeout",
    "timeout_seconds",
    default=10,
    show_default=True,
    type=int,
    help="Forwarding timeout in seconds",
)
def serve_callback(
    host,
    port,
    events_path,
    forward_url,
    api_key_header,
    api_key,
    timeout_seconds,
):
    """Run a local memoQ SOAP callback endpoint."""
    click.echo(f"Starting memoQ callback endpoint on http://{host}:{port}{CALLBACK_PATH}")
    click.echo(f"Events JSONL: {events_path}")
    if forward_url:
        click.echo(f"Forwarding parsed callbacks to: {forward_url}")

    try:
        start_callback_server(
            host=host,
            port=port,
            events_path=events_path,
            forward_url=forward_url,
            api_key_header=api_key_header,
            api_key=api_key,
            timeout_seconds=timeout_seconds,
        )
    except KeyboardInterrupt:
        click.echo("\nStopped.")
