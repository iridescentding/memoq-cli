# -*- coding: utf-8 -*-
"""
memoQ CLI - Light Resource Service Commands
"""

import os
from datetime import datetime

import click
from zeep.helpers import serialize_object

from ..wsapi.client import WSAPIClient
from ..wsapi.file_manager import FileManager
from ..utils import output_json, handle_api_error

RESOURCE_NS = "http://kilgray.com/memoqservices/2007"

# Resource types known to work with ListResources
SUPPORTED_RESOURCE_TYPES = [
    "FilterConfigs",
    "FontSubstitution",
    "IgnoreLists",
    "MTSettings",
    "PathRules",
    "ProjectTemplate",
    "QASettings",
    "SegRules",
]


@click.group()
def resource():
    """Light Resource Service commands"""
    pass


@resource.command("importnewfilter")
@click.argument("file_path")
@click.option("--name", "-n", "resource_name", help="Name for the new filter resource")
@click.pass_context
def import_new_filter(ctx, file_path, resource_name):
    """Import a filter config file as a new resource

    \b
    Examples:
        memoq resource importnewfilter ./myfilter.xml
        memoq resource importnewfilter ./myfilter.xml --name "My Custom Filter"
    """
    try:
        # Auto-generate name if not provided
        if not resource_name:
            basename = os.path.splitext(os.path.basename(file_path))[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            resource_name = f"{basename}_{timestamp}"

        # Step 1: Upload file
        click.echo(f"Uploading {file_path}...")
        fm = FileManager()
        file_guid = fm.upload_file_chunked(file_path)

        if not file_guid:
            click.echo("Error: File upload failed", err=True)
            ctx.exit(1)
            return

        click.echo(f"  File uploaded: {file_guid}")

        # Step 2: ImportNewAndPublish
        click.echo(f"Creating filter resource '{resource_name}'...")
        ws_client = WSAPIClient()
        resource_client = ws_client.get_client("Resource")

        resource_info_type = resource_client.get_type(
            f'{{{RESOURCE_NS}}}LightResourceInfo'
        )
        resource_info = resource_info_type(
            Name=resource_name,
            Description=f"Imported via memoq-cli at {datetime.now().isoformat()}",
            Readonly=False,
        )

        new_guid = resource_client.service.ImportNewAndPublish(
            resourceType="FilterConfigs",
            fileGuid=file_guid,
            resourceInfo=resource_info,
        )

        click.echo(f"  Filter created successfully!")
        click.echo(f"  Name: {resource_name}")
        click.echo(f"  GUID: {new_guid}")

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False))


@resource.command("listall")
@click.option("--type", "-t", "resource_type", help="Only list a specific resource type")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def list_all(ctx, resource_type, as_json):
    """List all light resources on the server

    \b
    Examples:
        memoq resource listall
        memoq resource listall --type FilterConfigs
        memoq resource listall --json
    """
    try:
        ws_client = WSAPIClient()
        client = ws_client.get_client("Resource")

        types_to_query = [resource_type] if resource_type else SUPPORTED_RESOURCE_TYPES
        all_results = {}

        for rt in types_to_query:
            try:
                result = client.service.ListResources(rt, None)
                data = serialize_object(result) or []
                all_results[rt] = data
            except Exception:
                all_results[rt] = []

        if as_json:
            output_json(all_results)
            return

        total = 0
        for rt, items in all_results.items():
            count = len(items)
            total += count
            click.echo(f"\n{rt} ({count})")
            click.echo("-" * 80)
            if not items:
                click.echo("  (none)")
                continue
            for item in items:
                name = item.get("Name", item.get("FriendlyName", "Unknown"))
                guid = item.get("Guid", "N/A")
                click.echo(f"  {name:<50} {guid}")

        click.echo(f"\nTotal: {total} resources across {len(all_results)} types")

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False))
