# -*- coding: utf-8 -*-
"""
memoQ CLI - Project Commands
"""

import sys
import click

from ..wsapi import ProjectManager
from ..utils import output_json, output_error, handle_api_error


@click.group()
def project():
    """Project management commands"""
    pass


@project.command("list")
@click.option("--filter", "-f", "filter_text", help="Filter by name")
@click.option("--archived", "-a", is_flag=True, help="Include archived projects")
@click.option("--limit", "-n", type=int, help="Limit number of results")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def project_list(ctx, filter_text, archived, limit, as_json):
    """List all projects"""
    try:
        pm = ProjectManager()
        projects = pm.list_projects(filter_text=filter_text, include_archived=archived)

        if limit:
            projects = projects[:limit]

        if as_json:
            output_json(projects)
            return

        if not projects:
            click.echo("No projects found")
            return

        click.echo(f"\nFound {len(projects)} project(s):\n")
        click.echo("=" * 70)

        for p in projects:
            name = p.get("Name", "Unknown")
            guid = p.get("ServerProjectGuid", "")
            status = p.get("ProjectStatus", "")
            src_lang = p.get("SourceLanguageCode", "")
            tgt_langs = p.get("TargetLanguageCodes", [])

            if isinstance(tgt_langs, list):
                tgt_display = ", ".join(tgt_langs[:3])
                if len(tgt_langs) > 3:
                    tgt_display += f" (+{len(tgt_langs) - 3})"
            else:
                tgt_display = str(tgt_langs)

            click.echo(f"  {name}")
            click.echo(f"     GUID:     {guid}")
            click.echo(f"     Status:   {status}")
            click.echo(f"     Languages: {src_lang} -> {tgt_display}")
            click.echo("-" * 70)

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False))


@project.command("info")
@click.argument("project_guid")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def project_info(ctx, project_guid, as_json):
    """Get project details"""
    try:
        pm = ProjectManager()
        info = pm.get_project_info(project_guid)

        if as_json:
            output_json(info)
            return

        click.echo(f"\nProject Info:\n")
        click.echo(f"  Name:        {info.get('Name', 'N/A')}")
        click.echo(f"  GUID:        {info.get('ServerProjectGuid', 'N/A')}")
        click.echo(f"  Status:      {info.get('ProjectStatus', 'N/A')}")
        click.echo(f"  Source:      {info.get('SourceLanguageCode', 'N/A')}")
        click.echo(f"  Targets:     {info.get('TargetLanguageCodes', 'N/A')}")
        click.echo(f"  Created:     {info.get('CreationTime', 'N/A')}")
        click.echo(f"  Deadline:    {info.get('Deadline', 'N/A')}")
        click.echo(f"  Creator:     {info.get('CreatorUser', 'N/A')}")
        click.echo(f"  Description: {info.get('Description', 'N/A')}")

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False))


@project.command("docs")
@click.argument("project_guid")
@click.option("--status", "-s", is_flag=True, help="Show document status")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def project_docs(ctx, project_guid, status, as_json):
    """List documents in a project"""
    try:
        pm = ProjectManager()

        if status:
            docs = pm.get_document_status(project_guid)
        else:
            docs = pm.list_project_documents(project_guid)

        if as_json:
            output_json(docs)
            return

        if not docs:
            click.echo("No documents in project")
            return

        click.echo(f"\nFound {len(docs)} document(s):\n")

        for i, doc in enumerate(docs, 1):
            name = doc.get("DocumentName", "Unknown")
            guid = doc.get("DocumentGuid", "")
            status_name = doc.get("StatusName", doc.get("DocumentStatus", "N/A"))
            word_count = doc.get("TotalWordCount", "N/A")
            target_lang = doc.get("TargetLangCode", "N/A")

            click.echo(f"  {i}. {name}")
            click.echo(f"     GUID:    {guid}")
            click.echo(f"     Status:  {status_name}")
            click.echo(f"     Words:   {word_count}")
            click.echo(f"     Target:  {target_lang}")
            click.echo()

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False))


@project.command("stats")
@click.argument("project_guid")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def project_stats(ctx, project_guid, as_json):
    """Get project statistics"""
    try:
        pm = ProjectManager()
        stats = pm.get_project_statistics(project_guid)

        if as_json:
            output_json(stats)
            return

        click.echo(f"\nProject Statistics:\n")
        output_json(stats)

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False))
