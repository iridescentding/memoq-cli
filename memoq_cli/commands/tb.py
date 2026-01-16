# -*- coding: utf-8 -*-
"""
memoQ CLI - TB Commands
"""

import sys
import click

from ..rsapi import TBManager
from ..utils import output_json, handle_api_error


@click.group()
def tb():
    """Terminology Base (TB) management commands"""
    pass


@tb.command("list")
@click.option("--filter", "-f", "filter_text", help="Filter by name")
@click.option("--limit", "-n", type=int, help="Limit number of results")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def tb_list(ctx, filter_text, limit, as_json):
    """List all TBs"""
    try:
        tbm = TBManager()
        tbs = tbm.list_tbs(filter_text)

        if limit:
            tbs = tbs[:limit]

        if as_json:
            output_json(tbs)
            return

        if not tbs:
            click.echo("No TBs found")
            return

        click.echo(f"\nFound {len(tbs)} TB(s):\n")
        click.echo("=" * 70)

        for t in tbs:
            name = t.get("FriendlyName", "Unknown")
            guid = t.get("TBGuid", "")
            langs = t.get("Languages", [])
            entries = t.get("NumEntries", "N/A")

            if isinstance(langs, list):
                lang_display = ", ".join(langs[:5])
                if len(langs) > 5:
                    lang_display += f" (+{len(langs) - 5})"
            else:
                lang_display = str(langs)

            click.echo(f"  {name}")
            click.echo(f"     GUID:      {guid}")
            click.echo(f"     Languages: {lang_display}")
            click.echo(f"     Entries:   {entries}")
            click.echo("-" * 70)

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False))


@tb.command("info")
@click.argument("tb_guid")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def tb_info(ctx, tb_guid, as_json):
    """Get TB details"""
    try:
        tbm = TBManager()
        info = tbm.get_tb_info(tb_guid)

        if as_json:
            output_json(info)
            return

        click.echo(f"\nTB Info:\n")
        click.echo(f"  Name:      {info.get('FriendlyName', 'N/A')}")
        click.echo(f"  GUID:      {info.get('TBGuid', 'N/A')}")
        click.echo(f"  Languages: {info.get('Languages', 'N/A')}")
        click.echo(f"  Entries:   {info.get('NumEntries', 'N/A')}")
        click.echo(f"  Created:   {info.get('CreationTime', 'N/A')}")
        click.echo(f"  Description: {info.get('Description', 'N/A')}")

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False))


@tb.command("create")
@click.option("--name", "-n", required=True, prompt="TB name", help="TB name")
@click.option("--lang", "-l", multiple=True, required=True,
              help="Language code(s), e.g., -l en-US -l zh-CN")
@click.option("--desc", "-d", default="", help="Description")
@click.pass_context
def tb_create(ctx, name, lang, desc):
    """Create a new TB"""
    try:
        tbm = TBManager()
        languages = list(lang)

        click.echo(f"\nCreating TB")
        click.echo(f"   Name:      {name}")
        click.echo(f"   Languages: {', '.join(languages)}")
        if desc:
            click.echo(f"   Description: {desc}")
        click.echo()

        result = tbm.create_tb(name, languages, desc)
        click.echo(f"Done: TB created!")
        click.echo(f"   GUID: {result.get('TBGuid', 'N/A')}")

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False))


@tb.command("delete")
@click.argument("tb_guid")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def tb_delete(ctx, tb_guid, yes):
    """Delete a TB (irreversible!)"""
    if not yes:
        click.confirm(f"Delete TB {tb_guid}? This cannot be undone!", abort=True)

    try:
        tbm = TBManager()
        tbm.delete_tb(tb_guid)
        click.echo(f"Done: TB deleted: {tb_guid}")

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False))


@tb.command("search")
@click.argument("tb_guid")
@click.argument("text")
@click.option("--source-lang", "-s", help="Source language filter")
@click.option("--limit", "-n", type=int, help="Limit number of results")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def tb_search(ctx, tb_guid, text, source_lang, limit, as_json):
    """Search TB for terms"""
    try:
        tbm = TBManager()
        results = tbm.search_tb(tb_guid, text, source_lang)

        if limit:
            results = results[:limit]

        if as_json:
            output_json(results)
            return

        if not results:
            click.echo("No terms found")
            return

        click.echo(f"\nFound {len(results)} term(s):\n")

        for i, r in enumerate(results, 1):
            terms = r.get("Terms", [])
            definition = r.get("Definition", "")
            domain = r.get("Domain", "")

            click.echo(f"  {i}. Terms:")
            for t in terms:
                click.echo(f"       [{t.get('LangCode')}] {t.get('Term')}")

            if definition:
                click.echo(f"     Definition: {definition}")
            if domain:
                click.echo(f"     Domain: {domain}")
            click.echo()

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False))


@tb.command("add")
@click.argument("tb_guid")
@click.option("--term", "-t", multiple=True, required=True,
              help="Term in format lang:term (e.g., -t en-US:computer -t zh-CN:computer)")
@click.option("--definition", "-d", default="", help="Term definition")
@click.option("--domain", default="", help="Domain/subject")
@click.pass_context
def tb_add(ctx, tb_guid, term, definition, domain):
    """Add a term entry to TB"""
    try:
        tbm = TBManager()

        # Parse terms
        terms = {}
        for t in term:
            if ":" not in t:
                click.echo(f"Error: Invalid term format: {t}", err=True)
                click.echo("   Format: lang:term (e.g., en-US:computer)", err=True)
                sys.exit(1)

            parts = t.split(":", 1)
            lang, text = parts[0], parts[1]
            terms[lang] = text

        click.echo(f"\nAdding Term")
        click.echo(f"   TB: {tb_guid}")
        click.echo(f"   Terms:")
        for lang, text in terms.items():
            click.echo(f"     [{lang}] {text}")
        if definition:
            click.echo(f"   Definition: {definition}")
        if domain:
            click.echo(f"   Domain: {domain}")
        click.echo()

        result = tbm.add_entry(tb_guid, terms, definition, domain)
        click.echo("Done: Term added!")

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False))


@tb.command("import")
@click.argument("tb_guid")
@click.option("--path", "-p", required=True, type=click.Path(exists=True),
              help="CSV file path")
@click.option("--wait/--no-wait", default=True, help="Wait for import to complete")
@click.pass_context
def tb_import(ctx, tb_guid, path, wait):
    """Import terms from CSV"""
    try:
        tbm = TBManager()

        click.echo(f"\nImporting CSV")
        click.echo(f"   File: {path}")
        click.echo(f"   TB:   {tb_guid}")
        click.echo()

        if wait:
            click.echo("Importing (please wait)...")
            result = tbm.import_csv(tb_guid, path)
            click.echo("Done: CSV import successful!")
        else:
            result = tbm.import_csv(tb_guid, path, wait_for_completion=False)
            click.echo("Done: Import task submitted!")

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False))


@tb.command("export")
@click.argument("tb_guid")
@click.option("--output", "-o", required=True, type=click.Path(), help="Output file path")
@click.pass_context
def tb_export(ctx, tb_guid, output):
    """Export TB as CSV"""
    try:
        tbm = TBManager()

        click.echo(f"\nExporting TB")
        click.echo(f"   TB:     {tb_guid}")
        click.echo(f"   Output: {output}")
        click.echo()

        click.echo("Exporting...")
        result = tbm.export_csv(tb_guid, output)
        click.echo(f"Done: Exported to {result}")

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False))
