# -*- coding: utf-8 -*-
"""
memoQ CLI - Project Template Commands
"""

import sys
import click

from ..wsapi import WSAPIClient
from ..wsapi.project_template import ProjectTemplateManager
from ..utils import output_json, handle_api_error


@click.group()
def template():
    """Project Template management commands"""
    pass


@template.command("list")
@click.option("--filter", "-f", "filter_text", help="Filter by name")
@click.option("--limit", "-n", type=int, help="Limit number of results")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def template_list(ctx, filter_text, limit, as_json):
    """List all project templates

    \b
    Examples:
        memoq template list
        memoq template list --filter "Translation"
        memoq template list --json
    """
    try:
        manager = ProjectTemplateManager()
        templates = manager.list_templates()

        # Filter if needed
        if filter_text:
            filter_lower = filter_text.lower()
            templates = [
                t for t in templates
                if filter_lower in t.get("Name", t.get("FriendlyName", "")).lower()
                or filter_lower in t.get("Guid", "").lower()
            ]

        if limit:
            templates = templates[:limit]

        if as_json:
            output_json(templates)
            return

        if not templates:
            click.echo("No project templates found")
            return

        # Display templates
        click.echo(f"\nFound {len(templates)} project template(s):\n")
        click.echo("=" * 100)
        click.echo(f"{'Name':<40} {'GUID':<38} {'Source':<10}")
        click.echo("=" * 100)

        for t in templates:
            # Use "Name" key (not "FriendlyName") for Light Resource API
            name = t.get("Name", t.get("FriendlyName", "Unknown")) or "Unknown"
            if len(name) > 38:
                name = name[:35] + "..."

            guid = t.get("Guid") or "N/A"
            source = t.get("SourceLangCode") or "N/A"

            click.echo(f"{name:<40} {guid:<38} {source:<10}")

        click.echo("=" * 100)

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False))


@template.command("info")
@click.argument("template_guid")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def template_info(ctx, template_guid, as_json):
    """Get project template details

    \b
    Examples:
        memoq template info <guid>
        memoq template info <guid> --json
    """
    try:
        manager = ProjectTemplateManager()
        template = manager.get_template(template_guid)

        if as_json:
            output_json(template)
            return

        # Display detailed info
        # Use "Name" key (not "FriendlyName") for Light Resource API
        name = template.get("Name", template.get("FriendlyName", "N/A"))

        click.echo(f"\nProject Template Info:\n")
        click.echo(f"  Name:        {name}")
        click.echo(f"  GUID:        {template.get('Guid', 'N/A')}")
        click.echo(f"  Source:      {template.get('SourceLangCode', 'N/A')}")
        click.echo(f"  Description: {template.get('Description', 'N/A')}")
        click.echo(f"  Read-only:   {template.get('Readonly', False)}")
        click.echo(f"  Is Default:  {template.get('IsDefault', False)}")

        # TargetLangCodes is an object with "string" array
        targets = template.get("TargetLangCodes", {})
        if isinstance(targets, dict):
            target_list = targets.get("string", [])
        elif isinstance(targets, list):
            target_list = targets
        else:
            target_list = []

        if target_list:
            click.echo(f"  Targets:     {', '.join(target_list)}")

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False))
