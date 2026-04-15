# -*- coding: utf-8 -*-
"""
memoQ CLI - TM Commands

Supported via RSAPI:
  list, info, concordance, lookup, metascheme,
  entry, entry-add, entry-update, entry-delete

NOT supported via RSAPI (need WSAPI):
  create, delete, import, export, search
"""

import click

from ..rsapi import TMManager
from ..utils import output_json, handle_api_error


@click.group()
def tm():
    """翻译记忆库 (TM) 管理命令 / Translation Memory (TM) management commands

    \b
    通过 RSAPI 支持 / Supported via RSAPI:
        list, info, concordance, lookup, metascheme,
        entry, entry-add, entry-update, entry-delete
    不支持 (需 WSAPI) / Not supported via RSAPI:
        create, delete, import, export, search
    """
    pass


@tm.command("list")
@click.option("--filter", "-f", "filter_text", help="Filter by name")
@click.option("--source", "-s", help="Filter by source language")
@click.option("--target", "-t", help="Filter by target language")
@click.option("--limit", "-n", type=int, help="Limit number of results")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def tm_list(ctx, filter_text, source, target, limit, as_json):
    """列出所有 TM / List all TMs

    \b
    示例 / Examples:
        memoq tm list
        memoq tm list -f "workingTM"
        memoq tm list -s zho-CN -t eng
        memoq tm list -n 20 --json
    """
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
        handle_api_error(e, ctx.obj.get("verbose", False) if ctx.obj else False)


@tm.command("info")
@click.argument("tm_guid")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def tm_info(ctx, tm_guid, as_json):
    """查看 TM 详情 / Get TM details

    \b
    示例 / Examples:
        memoq tm info <TM_GUID>
        memoq tm info <TM_GUID> --json
    """
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
        handle_api_error(e, ctx.obj.get("verbose", False) if ctx.obj else False)


@tm.command("concordance")
@click.argument("tm_guid")
@click.argument("expression", nargs=-1, required=True)
@click.option("--limit", "-n", type=int, default=64, help="Max results (default 64)")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def tm_concordance(ctx, tm_guid, expression, limit, as_json):
    """在 TM 中做 Concordance 搜索 / Concordance search in a TM

    \b
    参数 / Arguments:
        TM_GUID       TM GUID
        EXPRESSION    一个或多个搜索词 / One or more search terms

    \b
    示例 / Examples:
        memoq tm concordance <TM_GUID> "search term"
        memoq tm concordance <TM_GUID> term1 term2
        memoq tm concordance <TM_GUID> "term" -n 20 --json
    """
    try:
        tmm = TMManager()
        options = {"ResultsLimit": limit} if limit != 64 else None
        result = tmm.concordance(tm_guid, list(expression), options)

        if as_json:
            output_json(result)
            return

        # Try to display results based on actual response structure
        if isinstance(result, list):
            if not result:
                click.echo("No concordance matches found")
                return
            click.echo(f"\nFound {len(result)} concordance match(es):\n")
            for i, r in enumerate(result, 1):
                entry = r.get("TMEntry", r)
                source = entry.get("SourceSegment", "")
                target = entry.get("TargetSegment", "")
                click.echo(f"  {i}.")
                click.echo(f"     Source: {source}")
                click.echo(f"     Target: {target}")
                click.echo()
        elif isinstance(result, dict):
            conc_results = result.get("ConcResult") or []
            total = result.get("TotalConcResult") or len(conc_results)
            if not conc_results:
                click.echo("No concordance matches found")
                return
            click.echo(f"\nFound {total} concordance match(es):\n")
            for i, r in enumerate(conc_results, 1):
                entry = r.get("TMEntry", r)
                source = entry.get("SourceSegment", "")
                target = entry.get("TargetSegment", "")
                click.echo(f"  {i}.")
                click.echo(f"     Source: {source}")
                click.echo(f"     Target: {target}")
                click.echo()
        else:
            output_json(result)

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False) if ctx.obj else False)


@tm.command("lookup")
@click.argument("tm_guid")
@click.argument("segments", nargs=-1, required=True)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def tm_lookup(ctx, tm_guid, segments, as_json):
    """在 TM 中做段落查询 / Lookup segments in a TM

    \b
    段落格式 / Segment format:
        纯文本会自动用 <seg>...</seg> 包装。
        Plain text is auto-wrapped with <seg>...</seg>.

    \b
    示例 / Examples:
        memoq tm lookup <TM_GUID> "Hello world"
        memoq tm lookup <TM_GUID> "<seg>Hello world</seg>"
        memoq tm lookup <TM_GUID> "句一" "句二" --json
    """
    try:
        tmm = TMManager()
        # Wrap plain text in <seg> tags if not already
        wrapped = []
        for s in segments:
            if not s.startswith("<seg>"):
                s = f"<seg>{s}</seg>"
            wrapped.append(s)

        result = tmm.lookup_segments(tm_guid, wrapped)

        if as_json:
            output_json(result)
            return

        # Handle both possible response structures
        if isinstance(result, dict):
            results_list = result.get("Result", result.get("Results", []))
        elif isinstance(result, list):
            results_list = result
        else:
            click.echo("No lookup results")
            return

        if not results_list:
            click.echo("No lookup results")
            return

        for seg_idx, seg_result in enumerate(results_list):
            hits = seg_result.get("TMHits", [])
            click.echo(f"\nSegment {seg_idx + 1}: {segments[seg_idx]}")

            if not hits:
                click.echo("  No matches")
                continue

            for i, hit in enumerate(hits, 1):
                match_rate = hit.get("MatchRate", 0)
                tu = hit.get("TransUnit", hit)
                source = tu.get("SourceSegment", "")
                target = tu.get("TargetSegment", "")

                click.echo(f"  {i}. [{match_rate}%]")
                click.echo(f"     Source: {source}")
                click.echo(f"     Target: {target}")

        click.echo()

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False) if ctx.obj else False)


@tm.command("metascheme")
@click.argument("tm_guid")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def tm_metascheme(ctx, tm_guid, as_json):
    """查看 TM 自定义元数据方案 / Get custom metadata scheme of a TM

    \b
    示例 / Example:
        memoq tm metascheme <TM_GUID>
    """
    try:
        tmm = TMManager()
        result = tmm.get_custom_meta_scheme(tm_guid)

        output_json(result)

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False) if ctx.obj else False)


@tm.command("entry")
@click.argument("tm_guid")
@click.argument("entry_id", type=int)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def tm_entry_get(ctx, tm_guid, entry_id, as_json):
    """根据 ID 查询 TM 条目 / Get a specific TM entry by ID

    \b
    示例 / Examples:
        memoq tm entry <TM_GUID> 1
        memoq tm entry <TM_GUID> 42 --json
    """
    try:
        tmm = TMManager()
        entry = tmm.get_entry(tm_guid, entry_id)

        if as_json:
            output_json(entry)
            return

        click.echo(f"\nTM Entry (ID: {entry_id}):\n")
        click.echo(f"  Source:   {entry.get('SourceSegment', 'N/A')}")
        click.echo(f"  Target:   {entry.get('TargetSegment', 'N/A')}")
        click.echo(f"  Creator:  {entry.get('Creator', 'N/A')}")
        click.echo(f"  Created:  {entry.get('Created', 'N/A')}")
        click.echo(f"  Modifier: {entry.get('Modifier', 'N/A')}")
        click.echo(f"  Modified: {entry.get('Modified', 'N/A')}")
        click.echo(f"  Client:   {entry.get('Client', '')}")
        click.echo(f"  Domain:   {entry.get('Domain', '')}")
        click.echo(f"  Project:  {entry.get('Project', '')}")
        click.echo(f"  Subject:  {entry.get('Subject', '')}")

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False) if ctx.obj else False)


@tm.command("entry-add")
@click.argument("tm_guid")
@click.option("--source", "-s", required=True, prompt="Source segment", help="Source text")
@click.option("--target", "-t", required=True, prompt="Target segment", help="Target text")
@click.option("--modifier", "-m", default="", help="Modifier username")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def tm_entry_add(ctx, tm_guid, source, target, modifier, as_json):
    """向 TM 添加条目 / Add an entry to a TM

    \b
    参数 / Options:
        -s/--source    源语言文本 / Source text (自动包 <seg>)
        -t/--target    目标语言文本 / Target text (自动包 <seg>)
        -m/--modifier  修改人用户名 / Modifier username

    \b
    示例 / Examples:
        memoq tm entry-add <TM_GUID> -s "Hello" -t "你好"
        memoq tm entry-add <TM_GUID> -s "Project" -t "项目" -m jayding
    """
    try:
        tmm = TMManager()
        if not source.startswith("<seg>"):
            source = f"<seg>{source}</seg>"
        if not target.startswith("<seg>"):
            target = f"<seg>{target}</seg>"

        result = tmm.create_entry(tm_guid, source, target, modifier)

        if as_json:
            output_json(result)
            return

        click.echo("Done: Entry added to TM")

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False) if ctx.obj else False)


@tm.command("entry-update")
@click.argument("tm_guid")
@click.argument("entry_id", type=int)
@click.option("--source", "-s", required=True, prompt="Source segment", help="Source text")
@click.option("--target", "-t", required=True, prompt="Target segment", help="Target text")
@click.option("--modifier", "-m", default="", help="Modifier username")
@click.pass_context
def tm_entry_update(ctx, tm_guid, entry_id, source, target, modifier):
    """更新 TM 条目 / Update a TM entry

    \b
    示例 / Example:
        memoq tm entry-update <TM_GUID> 42 -s "Hello" -t "你好" -m jayding
    """
    try:
        tmm = TMManager()
        if not source.startswith("<seg>"):
            source = f"<seg>{source}</seg>"
        if not target.startswith("<seg>"):
            target = f"<seg>{target}</seg>"

        tmm.update_entry(tm_guid, entry_id, source, target, modifier)
        click.echo(f"Done: Entry {entry_id} updated")

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False) if ctx.obj else False)


@tm.command("entry-delete")
@click.argument("tm_guid")
@click.argument("entry_id", type=int)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def tm_entry_delete(ctx, tm_guid, entry_id, yes):
    """删除 TM 条目 / Delete a TM entry

    \b
    示例 / Examples:
        memoq tm entry-delete <TM_GUID> 42
        memoq tm entry-delete <TM_GUID> 42 -y      # 跳过确认 / skip confirm
    """
    if not yes:
        click.confirm(f"Delete entry {entry_id} from TM? This cannot be undone!", abort=True)

    try:
        tmm = TMManager()
        tmm.delete_entry(tm_guid, entry_id)
        click.echo(f"Done: Entry {entry_id} deleted")

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False) if ctx.obj else False)
