# -*- coding: utf-8 -*-
"""
memoQ CLI - Light Resource Service Commands
"""

import os
import tempfile
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
    """轻量级资源服务命令 / Light Resource Service commands

    \b
    子命令 / Subcommands:
        list              列出轻量级资源 / List light resources
        listall           列出所有轻量级资源 / List all light resources
        importnewfilter   导入过滤器配置为新资源 / Import filter config as resource

    \b
    已支持的资源类型 / Supported resource types:
        FilterConfigs, FontSubstitution, IgnoreLists, MTSettings,
        PathRules, ProjectTemplate, QASettings, SegRules
    """
    pass


def _list_resources(client, resource_types):
    """Fetch light resources for each requested memoQ resource type."""
    all_results = {}
    for rt in resource_types:
        try:
            result = client.service.ListResources(rt, None)
            all_results[rt] = serialize_object(result) or []
        except Exception:
            all_results[rt] = []
    return all_results


def _resource_name(item):
    return item.get("Name", item.get("FriendlyName", "Unknown"))


def _resource_guid(item):
    return item.get("Guid", "N/A")


def _short_filter_type(filter_name):
    if not filter_name:
        return "Unknown"
    return str(filter_name).rsplit(".", 1)[-1]


def _with_filter_type(items):
    enriched = []
    for item in items:
        row = dict(item)
        row["Type"] = _short_filter_type(row.get("FilterName"))
        enriched.append(row)
    return enriched


def _filter_by_type(items, filter_type):
    needle = filter_type.casefold()
    return [
        item for item in items
        if needle in str(item.get("Type", "")).casefold()
        or needle in str(item.get("FilterName", "")).casefold()
    ]


def _export_file_guid(result):
    if isinstance(result, dict):
        result = (
            result.get("ExportResourceResult")
            or result.get("FileGuid")
            or result.get("Guid")
        )
    elif hasattr(result, "ExportResourceResult"):
        result = result.ExportResourceResult
    elif hasattr(result, "FileGuid"):
        result = result.FileGuid
    if not result:
        raise click.ClickException("ExportResource did not return a file GUID.")
    return str(result)


def _decode_xml_file(path):
    raw = open(path, "rb").read()
    for encoding in ("utf-8-sig", "utf-16", "utf-8"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _print_all_resources_table(all_results):
    total = sum(len(items) for items in all_results.values())
    click.echo(f"{'ResourceType':<20} {'Name':<50} Guid")
    click.echo("-" * 110)
    for resource_type, items in all_results.items():
        if not items:
            continue
        for item in items:
            click.echo(
                f"{resource_type:<20} {_resource_name(item):<50} {_resource_guid(item)}"
            )
    click.echo(f"\nTotal: {total} resources across {len(all_results)} types")


def _print_grouped_resources(all_results):
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
            click.echo(f"  {_resource_name(item):<50} {_resource_guid(item)}")

    click.echo(f"\nTotal: {total} resources across {len(all_results)} types")


def _print_filter_resources(items):
    click.echo(f"{'Type':<28} {'Name':<50} Guid")
    click.echo("-" * 110)
    if not items:
        click.echo("  (none)")
        return
    for item in items:
        click.echo(
            f"{item.get('Type', 'Unknown'):<28} "
            f"{_resource_name(item):<50} "
            f"{_resource_guid(item)}"
        )


@resource.command("importnewfilter")
@click.argument("file_path")
@click.option("--name", "-n", "resource_name", help="Name for the new filter resource")
@click.pass_context
def import_new_filter(ctx, file_path, resource_name):
    """导入过滤器配置为新资源 / Import a filter config file as a new resource

    \b
    说明 / Note:
        先分块上传文件, 再调用 ImportNewAndPublish 创建 FilterConfigs 资源。
        Uploads file in chunks, then calls ImportNewAndPublish to create a
        FilterConfigs resource.
        未指定 --name 时自动生成 `{basename}_{timestamp}`。
        Without --name, generates `{basename}_{timestamp}` automatically.

    \b
    示例 / Examples:
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


@resource.group("list", invoke_without_command=True)
@click.option("--all", "-a", "list_all_resources", is_flag=True,
              help="List all supported light resource types")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def resource_list(ctx, list_all_resources, as_json):
    """列出轻量级资源 / List light resources."""
    if ctx.invoked_subcommand is not None:
        return

    if not list_all_resources:
        raise click.ClickException("Use --all/-a or a subcommand such as filter.")

    try:
        ws_client = WSAPIClient()
        client = ws_client.get_client("Resource")
        all_results = _list_resources(client, SUPPORTED_RESOURCE_TYPES)

        if as_json:
            output_json(all_results)
            return

        _print_all_resources_table(all_results)

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False))


@resource_list.group("filter", invoke_without_command=True)
@click.option("--details", "-d", "detail_guid", default=None,
              help="Export and print the XML for a filter resource GUID")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def resource_list_filter(ctx, detail_guid, as_json):
    """只列出过滤器配置 / List filter configurations."""
    if ctx.invoked_subcommand is not None:
        return

    try:
        ws_client = WSAPIClient()
        client = ws_client.get_client("Resource")

        if detail_guid:
            file_guid = _export_file_guid(
                client.service.ExportResource(
                    resourceType="FilterConfigs",
                    resourceGuid=detail_guid,
                )
            )
            with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tmp:
                output_path = tmp.name
            try:
                FileManager().download_file_chunked(file_guid, output_path)
                click.echo(_decode_xml_file(output_path))
            finally:
                if os.path.exists(output_path):
                    os.unlink(output_path)
            return

        all_results = _list_resources(client, ["FilterConfigs"])
        filters = _with_filter_type(all_results["FilterConfigs"])

        if as_json:
            output_json(filters)
            return

        _print_filter_resources(filters)

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False))


@resource_list_filter.command("type")
@click.option("--filter-type", "-f", required=True,
              help="Filter converter type, e.g. ChainedConverter")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def resource_list_filter_type(ctx, filter_type, as_json):
    """按过滤器类型筛选 / Filter configs by converter type."""
    try:
        ws_client = WSAPIClient()
        client = ws_client.get_client("Resource")
        all_results = _list_resources(client, ["FilterConfigs"])
        filters = _filter_by_type(
            _with_filter_type(all_results["FilterConfigs"]),
            filter_type,
        )

        if as_json:
            output_json(filters)
            return

        _print_filter_resources(filters)

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False))


@resource.command("listall")
@click.option("--type", "-t", "resource_type", help="Only list a specific resource type")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def list_all(ctx, resource_type, as_json):
    """列出服务器上所有轻量级资源 / List all light resources on the server

    \b
    参数 / Options:
        -t/--type    仅列出指定类型 / Only list a specific resource type

    \b
    示例 / Examples:
        memoq resource listall
        memoq resource listall -t FilterConfigs
        memoq resource listall -t QASettings --json
    """
    try:
        ws_client = WSAPIClient()
        client = ws_client.get_client("Resource")

        types_to_query = [resource_type] if resource_type else SUPPORTED_RESOURCE_TYPES
        all_results = _list_resources(client, types_to_query)

        if as_json:
            output_json(all_results)
            return

        _print_grouped_resources(all_results)

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False))
