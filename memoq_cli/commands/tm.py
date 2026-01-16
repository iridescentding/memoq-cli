# -*- coding: utf-8 -*-
"""
memoQ CLI - TM Commands
"""

import sys
import click

from ..rsapi import TMManager
from ..utils import output_json, handle_api_error


@click.group()
def tm():
    """Translation Memory (TM) management commands"""
    pass


@tm.command("list")
@click.option("--filter", "-f", "filter_text", help="Filter by name")
@click.option("--source", "-s", help="Filter by source language")
@click.option("--target", "-t", help="Filter by target language")
@click.option("--limit", "-n", type=int, help="Limit number of results")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def tm_list(ctx, filter_text, source, target, limit, as_json):
    """List all TMs"""
    try:
        tmm = TMManager()
        tms = tmm.list_tms(filter_text, source, target)

        if limit:
            tms = tms[:limit]

        if as_json:
            output_json(tms)
            return

        if not tms:
            click.echo("No TMs found")
            return

        click.echo(f"\nFound {len(tms)} TM(s):\n")
        click.echo("=" * 70)

        for t in tms:
            name = t.get("FriendlyName", "Unknown")
            guid = t.get("TMGuid", "")
            src = t.get("SourceLangCode", "N/A")
            tgt = t.get("TargetLangCode", "N/A")
            entries = t.get("NumEntries", "N/A")

            click.echo(f"  {name}")
            click.echo(f"     GUID:      {guid}")
            click.echo(f"     Languages: {src} -> {tgt}")
            click.echo(f"     Entries:   {entries}")
            click.echo("-" * 70)

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False))


@tm.command("info")
@click.argument("tm_guid")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def tm_info(ctx, tm_guid, as_json):
    """Get TM details"""
    try:
        tmm = TMManager()
        info = tmm.get_tm_info(tm_guid)

        if as_json:
            output_json(info)
            return

        click.echo(f"\nTM Info:\n")
        click.echo(f"  Name:     {info.get('FriendlyName', 'N/A')}")
        click.echo(f"  GUID:     {info.get('TMGuid', 'N/A')}")
        click.echo(f"  Source:   {info.get('SourceLangCode', 'N/A')}")
        click.echo(f"  Target:   {info.get('TargetLangCode', 'N/A')}")
        click.echo(f"  Entries:  {info.get('NumEntries', 'N/A')}")
        click.echo(f"  Created:  {info.get('CreationTime', 'N/A')}")
        click.echo(f"  Description: {info.get('Description', 'N/A')}")

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False))


@tm.command("create")
@click.option("--name", "-n", required=True, prompt="TM name", help="TM name")
@click.option("--source", "-s", required=True, prompt="Source language", help="Source language code")
@click.option("--target", "-t", required=True, prompt="Target language", help="Target language code")
@click.option("--desc", "-d", default="", help="Description")
@click.pass_context
def tm_create(ctx, name, source, target, desc):
    """Create a new TM"""
    try:
        tmm = TMManager()

        click.echo(f"\nCreating TM")
        click.echo(f"   Name:      {name}")
        click.echo(f"   Languages: {source} -> {target}")
        if desc:
            click.echo(f"   Description: {desc}")
        click.echo()

        result = tmm.create_tm(name, source, target, desc)
        click.echo(f"Done: TM created!")
        click.echo(f"   GUID: {result.get('TMGuid', 'N/A')}")

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False))


@tm.command("delete")
@click.argument("tm_guid")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def tm_delete(ctx, tm_guid, yes):
    """Delete a TM (irreversible!)"""
    if not yes:
        click.confirm(f"Delete TM {tm_guid}? This cannot be undone!", abort=True)

    try:
        tmm = TMManager()
        tmm.delete_tm(tm_guid)
        click.echo(f"Done: TM deleted: {tm_guid}")

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False))


@tm.command("import")
@click.argument("tm_guid")
@click.option("--path", "-p", required=True, type=click.Path(exists=True),
              help="TMX file path")
@click.option("--wait/--no-wait", default=True, help="Wait for import to complete")
@click.pass_context
def tm_import(ctx, tm_guid, path, wait):
    """Import TMX into a TM"""
    try:
        tmm = TMManager()

        click.echo(f"\nImporting TMX")
        click.echo(f"   File: {path}")
        click.echo(f"   TM:   {tm_guid}")
        click.echo()

        if wait:
            click.echo("Importing (please wait)...")
            result = tmm.import_tmx(tm_guid, path, wait_for_completion=True)
            click.echo("Done: TMX import successful!")
        else:
            result = tmm.import_tmx(tm_guid, path, wait_for_completion=False)
            click.echo("Done: Import task submitted!")
            if "TaskId" in result:
                click.echo(f"   Task ID: {result['TaskId']}")

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False))


@tm.command("export")
@click.argument("tm_guid")
@click.option("--output", "-o", required=True, type=click.Path(), help="Output file path")
@click.option("--wait/--no-wait", default=True, help="Wait for export to complete")
@click.pass_context
def tm_export(ctx, tm_guid, output, wait):
    """Export TM as TMX"""
    try:
        tmm = TMManager()

        click.echo(f"\nExporting TM")
        click.echo(f"   TM:     {tm_guid}")
        click.echo(f"   Output: {output}")
        click.echo()

        if wait:
            click.echo("Exporting (please wait)...")
            result = tmm.export_tmx(tm_guid, output)
            click.echo(f"Done: Exported to {result}")
        else:
            result = tmm.export_tmx(tm_guid, output)
            click.echo("Done: Export task submitted!")

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False))


@tm.command("search")
@click.argument("tm_guid")
@click.argument("text")
@click.option("--threshold", "-t", default=75, type=int,
              help="Match threshold (0-100), default 75")
@click.option("--limit", "-n", type=int, help="Limit number of results")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def tm_search(ctx, tm_guid, text, threshold, limit, as_json):
    """Search TM for matches"""
    try:
        tmm = TMManager()
        results = tmm.search_tm(tm_guid, text, threshold)

        if limit:
            results = results[:limit]

        if as_json:
            output_json(results)
            return

        if not results:
            click.echo("No matches found")
            return

        click.echo(f"\nFound {len(results)} match(es):\n")

        for i, r in enumerate(results, 1):
            source = r.get("SourceSegment", "")
            target = r.get("TargetSegment", "")
            match = r.get("MatchRate", 0)

            click.echo(f"  {i}. [{match}%]")
            click.echo(f"     Source: {source}")
            click.echo(f"     Target: {target}")
            click.echo()

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False))
