# -*- coding: utf-8 -*-
"""
memoQ CLI - TB Commands

Supported via RSAPI:
  list, info, search, lookup, metadefs,
  add, entry, entry-update, entry-delete,
  entry-meta, language-meta, term-meta

NOT supported via RSAPI (need WSAPI):
  create, delete, import, export
"""

import sys
import click

from ..rsapi import TBManager
from ..utils import output_json, handle_api_error


@click.group()
def tb():
    """术语库 (TB) 管理命令 / Terminology Base (TB) management commands

    \b
    通过 RSAPI 支持 / Supported via RSAPI:
        list, info, search, lookup, metadefs, add,
        entry, entry-update, entry-delete,
        entry-meta, language-meta, term-meta
    不支持 (需 WSAPI) / Not supported via RSAPI:
        create, delete, import, export
    """
    pass


@tb.command("list")
@click.option("--filter", "-f", "filter_text", help="Filter by name")
@click.option("--lang0", help="First language filter")
@click.option("--lang1", help="Second language filter")
@click.option("--limit", "-n", type=int, help="Limit number of results")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def tb_list(ctx, filter_text, lang0, lang1, limit, as_json):
    """列出所有 TB / List all TBs

    \b
    示例 / Examples:
        memoq tb list
        memoq tb list -f "Kalcium"
        memoq tb list --lang0 eng --lang1 zho-CN
        memoq tb list -n 20 --json
    """
    try:
        tbm = TBManager()
        tbs = tbm.list_tbs(filter_text, lang0, lang1)

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
        handle_api_error(e, ctx.obj.get("verbose", False) if ctx.obj else False)


@tb.command("info")
@click.argument("tb_guid")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def tb_info(ctx, tb_guid, as_json):
    """查看 TB 详情 / Get TB details

    \b
    示例 / Examples:
        memoq tb info <TB_GUID>
        memoq tb info <TB_GUID> --json
    """
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
        handle_api_error(e, ctx.obj.get("verbose", False) if ctx.obj else False)


@tb.command("search")
@click.argument("tb_guid")
@click.argument("text")
@click.option("--target-lang", "-t", required=True, help="Target language code (required)")
@click.option("--condition", "-c", type=click.Choice(["begins", "contains", "ends", "exact"]),
              default="contains", help="Match condition (default: contains)")
@click.option("--limit", "-n", type=int, help="Limit number of results")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def tb_search(ctx, tb_guid, text, target_lang, condition, limit, as_json):
    """在 TB 中搜索术语 / Search TB for terms

    \b
    参数 / Options:
        -t/--target-lang   目标语言 (必填) / Target language (required)
        -c/--condition     匹配条件 begins | contains | ends | exact
                           默认 contains / default: contains
        -n/--limit         返回数量上限 / Result limit

    \b
    示例 / Examples:
        memoq tb search <TB_GUID> "computer" -t eng
        memoq tb search <TB_GUID> "test" -t eng-US -c exact
        memoq tb search <TB_GUID> "电" -t eng -c begins -n 10 --json
    """
    condition_map = {"begins": 0, "contains": 1, "ends": 2, "exact": 3}
    cond_value = condition_map[condition]

    try:
        tbm = TBManager()
        results = tbm.search_tb(tb_guid, text, target_lang, cond_value, limit)

        if as_json:
            output_json(results)
            return

        if not results:
            click.echo("No terms found")
            return

        # Handle both list and dict response
        if isinstance(results, dict):
            entries = results.get("Entries", results.get("Result", [results]))
        elif isinstance(results, list):
            entries = results
        else:
            click.echo("No terms found")
            return

        click.echo(f"\nFound {len(entries)} entry(ies):\n")

        for i, entry in enumerate(entries, 1):
            click.echo(f"  {i}. [ID: {entry.get('Id', 'N/A')}]")

            languages = entry.get("Languages", [])
            for lang_item in languages:
                lang_code = lang_item.get("Language", "")
                term_items = lang_item.get("TermItems", [])
                definition = lang_item.get("Definition", "")

                for ti in term_items:
                    forbidden = " [FORBIDDEN]" if ti.get("IsForbidden") else ""
                    click.echo(f"       [{lang_code}] {ti.get('Text', '')}{forbidden}")

                if definition:
                    click.echo(f"       Definition ({lang_code}): {definition}")

            domain = entry.get("Domain", "")
            if domain:
                click.echo(f"     Domain: {domain}")
            click.echo()

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False) if ctx.obj else False)


@tb.command("add")
@click.argument("tb_guid")
@click.option("--term", "-t", multiple=True, required=True,
              help="Term in format lang:term (e.g., -t en-US:computer -t zh-CN:电脑)")
@click.option("--definition", "-d", default="", help="Term definition")
@click.option("--domain", default="", help="Domain/subject")
@click.pass_context
def tb_add(ctx, tb_guid, term, definition, domain):
    """向 TB 添加术语条目 / Add a term entry to TB

    \b
    参数 / Options:
        -t/--term         多次使用, 格式 lang:term / Repeat, format lang:term
        -d/--definition   定义 / Definition
        --domain          领域/主题 / Domain

    \b
    示例 / Examples:
        memoq tb add <TB_GUID> -t eng-US:computer -t zho-CN:电脑
        memoq tb add <TB_GUID> -t eng:test -t zho-CN:测试 -d "a trial run" --domain Tech
    """
    try:
        tbm = TBManager()

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

        result = tbm.create_entry(tb_guid, terms, definition, domain)
        click.echo("Done: Term added!")

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False) if ctx.obj else False)


@tb.command("lookup")
@click.argument("tb_guid")
@click.argument("segments", nargs=-1, required=True)
@click.option("--source-lang", "-s", required=True, help="Source language code (required)")
@click.option("--target-lang", "-t", help="Target language code")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def tb_lookup(ctx, tb_guid, segments, source_lang, target_lang, as_json):
    """在 TB 中查找术语 / Lookup terms in a TB

    \b
    参数 / Options:
        -s/--source-lang   源语言 (必填) / Source language (required)
        -t/--target-lang   目标语言 / Target language

    \b
    示例 / Examples:
        memoq tb lookup <TB_GUID> "Hello world" -s eng
        memoq tb lookup <TB_GUID> "计算机网络" -s zho-CN -t eng-US --json
    """
    try:
        tbm = TBManager()
        wrapped = []
        for s in segments:
            if not s.startswith("<seg>"):
                s = f"<seg>{s}</seg>"
            wrapped.append(s)

        result = tbm.lookup_terms(tb_guid, wrapped, source_lang, target_lang)

        if as_json:
            output_json(result)
            return

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
            click.echo(f"\nSegment {seg_idx + 1}: {segments[seg_idx]}")
            tb_hits = seg_result.get("TBHits", [])

            if not tb_hits:
                click.echo("  No matches")
                continue

            hit_num = 0
            for hit in tb_hits:
                if isinstance(hit, list):
                    for h in hit:
                        hit_num += 1
                        source_term = h.get("SourceTerm", "")
                        target_term = h.get("TargetTerm", "")
                        match_rate = h.get("MatchRate", 0)
                        click.echo(f"  {hit_num}. [{match_rate}%] {source_term} -> {target_term}")
                else:
                    hit_num += 1
                    source_term = hit.get("SourceTerm", "")
                    target_term = hit.get("TargetTerm", "")
                    match_rate = hit.get("MatchRate", 0)
                    click.echo(f"  {hit_num}. [{match_rate}%] {source_term} -> {target_term}")

        click.echo()

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False) if ctx.obj else False)


@tb.command("metadefs")
@click.argument("tb_guid")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def tb_metadefs(ctx, tb_guid, as_json):
    """查看 TB 的元数据定义 / Get metadata definitions of a TB

    \b
    示例 / Example:
        memoq tb metadefs <TB_GUID>
    """
    try:
        tbm = TBManager()
        result = tbm.get_meta_definitions(tb_guid)
        output_json(result)

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False) if ctx.obj else False)


@tb.command("entry")
@click.argument("tb_guid")
@click.argument("entry_id", type=int)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def tb_entry_get(ctx, tb_guid, entry_id, as_json):
    """根据 ID 查询 TB 条目 / Get a specific TB entry by ID

    \b
    示例 / Examples:
        memoq tb entry <TB_GUID> 4
        memoq tb entry <TB_GUID> 4 --json
    """
    try:
        tbm = TBManager()
        entry = tbm.get_entry(tb_guid, entry_id)

        if as_json:
            output_json(entry)
            return

        click.echo(f"\nTB Entry (ID: {entry_id}):\n")

        languages = entry.get("Languages", [])
        if languages:
            click.echo("  Terms:")
            for lang_item in languages:
                lang_code = lang_item.get("Language", "")
                definition = lang_item.get("Definition", "")
                for ti in lang_item.get("TermItems", []):
                    forbidden = " [FORBIDDEN]" if ti.get("IsForbidden") else ""
                    click.echo(f"    [{lang_code}] {ti.get('Text', '')}{forbidden}")
                if definition:
                    click.echo(f"    Definition ({lang_code}): {definition}")

        click.echo(f"  Domain:     {entry.get('Domain') or ''}")
        click.echo(f"  Client:     {entry.get('Client') or ''}")
        click.echo(f"  Project:    {entry.get('Project') or ''}")
        click.echo(f"  Note:       {entry.get('Note') or ''}")
        click.echo(f"  Creator:    {entry.get('Creator') or ''}")
        click.echo(f"  Created:    {entry.get('Created') or ''}")
        click.echo(f"  Modifier:   {entry.get('Modifier') or ''}")
        click.echo(f"  Modified:   {entry.get('Modified') or ''}")

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False) if ctx.obj else False)


@tb.command("entry-update")
@click.argument("tb_guid")
@click.argument("entry_id", type=int)
@click.option("--term", "-t", multiple=True,
              help="Term in format lang:term (e.g., -t en-US:computer)")
@click.option("--definition", "-d", default="", help="Term definition")
@click.option("--domain", default="", help="Domain/subject")
@click.pass_context
def tb_entry_update(ctx, tb_guid, entry_id, term, definition, domain):
    """更新 TB 条目 / Update a TB entry

    \b
    示例 / Examples:
        memoq tb entry-update <TB_GUID> 4 -t eng-US:computer -t zho-CN:电脑
        memoq tb entry-update <TB_GUID> 4 -d "new definition" --domain Tech
    """
    try:
        tbm = TBManager()

        terms = {}
        for t in term:
            if ":" not in t:
                click.echo(f"Error: Invalid term format: {t}", err=True)
                sys.exit(1)
            parts = t.split(":", 1)
            terms[parts[0]] = parts[1]

        result = tbm.update_entry(tb_guid, entry_id, terms, definition, domain)
        click.echo(f"Done: Entry {entry_id} updated")

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False) if ctx.obj else False)


@tb.command("entry-delete")
@click.argument("tb_guid")
@click.argument("entry_id", type=int)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def tb_entry_delete(ctx, tb_guid, entry_id, yes):
    """删除 TB 条目 / Delete a TB entry

    \b
    示例 / Examples:
        memoq tb entry-delete <TB_GUID> 4
        memoq tb entry-delete <TB_GUID> 4 -y       # 跳过确认 / skip confirm
    """
    if not yes:
        click.confirm(f"Delete entry {entry_id} from TB? This cannot be undone!", abort=True)

    try:
        tbm = TBManager()
        tbm.delete_entry(tb_guid, entry_id)
        click.echo(f"Done: Entry {entry_id} deleted")

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False) if ctx.obj else False)


@tb.command("entry-meta")
@click.argument("tb_guid")
@click.argument("entry_id", type=int)
@click.argument("meta_name")
@click.option("--set", "set_value", default=None, help="Value to set")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def tb_entry_meta(ctx, tb_guid, entry_id, meta_name, set_value, as_json):
    """读取/设置条目级元数据 / Get or set entry-level metadata

    \b
    参数 / Arguments:
        TB_GUID, ENTRY_ID, META_NAME   需先在 metadefs 中定义 / META_NAME must be defined in metadefs

    \b
    示例 / Examples:
        memoq tb entry-meta <TB_GUID> 4 MyField                 # 读取 / get
        memoq tb entry-meta <TB_GUID> 4 MyField --set "value"   # 写入 / set
    """
    try:
        tbm = TBManager()

        if set_value is not None:
            result = tbm.set_entry_meta(tb_guid, entry_id, meta_name, set_value)
            click.echo(f"Done: Entry metadata '{meta_name}' set")
        else:
            result = tbm.get_entry_meta(tb_guid, entry_id, meta_name)
            if as_json:
                output_json(result)
            else:
                click.echo(f"\nEntry Metadata '{meta_name}':")
                click.echo(f"  {result}")

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False) if ctx.obj else False)


@tb.command("language-meta")
@click.argument("tb_guid")
@click.argument("entry_id", type=int)
@click.argument("meta_name")
@click.option("--language", "-l", default=None, help="Language code")
@click.option("--set", "set_value", default=None, help="Value to set")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def tb_language_meta(ctx, tb_guid, entry_id, meta_name, language, set_value, as_json):
    """读取/设置语言级元数据 / Get or set language-level metadata

    \b
    示例 / Examples:
        memoq tb language-meta <TB_GUID> 4 MyField -l eng-US
        memoq tb language-meta <TB_GUID> 4 MyField -l eng-US --set "value"
    """
    try:
        tbm = TBManager()

        if set_value is not None:
            result = tbm.set_language_meta(tb_guid, entry_id, meta_name, set_value, language)
            click.echo(f"Done: Language metadata '{meta_name}' set")
        else:
            result = tbm.get_language_meta(tb_guid, entry_id, meta_name, language)
            if as_json:
                output_json(result)
            else:
                click.echo(f"\nLanguage Metadata '{meta_name}':")
                click.echo(f"  {result}")

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False) if ctx.obj else False)


@tb.command("term-meta")
@click.argument("tb_guid")
@click.argument("entry_id", type=int)
@click.argument("meta_name")
@click.option("--term-id", default=None, help="Term ID")
@click.option("--set", "set_value", default=None, help="Value to set")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def tb_term_meta(ctx, tb_guid, entry_id, meta_name, term_id, set_value, as_json):
    """读取/设置术语级元数据 / Get or set term-level metadata

    \b
    示例 / Examples:
        memoq tb term-meta <TB_GUID> 4 MyField --term-id 1
        memoq tb term-meta <TB_GUID> 4 MyField --term-id 1 --set "value"
    """
    try:
        tbm = TBManager()

        if set_value is not None:
            result = tbm.set_term_meta(tb_guid, entry_id, meta_name, set_value, term_id)
            click.echo(f"Done: Term metadata '{meta_name}' set")
        else:
            result = tbm.get_term_meta(tb_guid, entry_id, meta_name, term_id)
            if as_json:
                output_json(result)
            else:
                click.echo(f"\nTerm Metadata '{meta_name}':")
                click.echo(f"  {result}")

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False) if ctx.obj else False)
