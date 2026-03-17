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


@project.group("docs", invoke_without_command=True)
@click.argument("project_guid")
@click.option("--status", "-s", is_flag=True, help="Show document status")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def project_docs(ctx, project_guid, status, as_json):
    """List documents in a project, or manage document assignments"""
    ctx.ensure_object(dict)
    ctx.obj["project_guid"] = project_guid

    if ctx.invoked_subcommand is not None:
        return

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


@project_docs.command("assign")
@click.pass_context
def docs_assign(ctx):
    """Assign a user to a translation document"""
    project_guid = ctx.obj["project_guid"]

    try:
        pm = ProjectManager()

        # Step 1: List documents
        docs = pm.list_project_documents(project_guid)
        if not docs:
            click.echo("No documents in project")
            return

        click.echo(f"\n  Available documents ({len(docs)}):")
        for i, doc in enumerate(docs, 1):
            name = doc.get("DocumentName", "Unknown")
            target_lang = doc.get("TargetLangCode", "")
            click.echo(f"    {i}. {name} [{target_lang}]")

        doc_choice = click.prompt(
            "\n  Select document (enter number)",
            type=click.IntRange(1, len(docs))
        )
        selected_doc = docs[doc_choice - 1]
        doc_guid = selected_doc.get("DocumentGuid")

        # Step 2: List users
        users = pm.list_users(active_only=True)
        if not users:
            click.echo("No active users found")
            return

        click.echo(f"\n  Available users ({len(users)}):")
        for i, u in enumerate(users, 1):
            full_name = u.get("FullName", u.get("UserName", "N/A"))
            user_name = u.get("UserName", "")
            click.echo(f"    {i}. {full_name:<30} ({user_name})")

        user_choice = click.prompt(
            "\n  Select user (enter number)",
            type=click.IntRange(1, len(users))
        )
        selected_user = users[user_choice - 1]
        user_guid = str(selected_user.get("UserGuid"))

        # Step 3: Select role
        # DocumentAssignmentRole: 0=Translator, 1=Reviewer1, 2=Reviewer2
        roles = [
            ("Translator", 0),
            ("Reviewer 1", 1),
            ("Reviewer 2", 2),
        ]

        click.echo(f"\n  Available roles:")
        for i, (role_name, _) in enumerate(roles, 1):
            click.echo(f"    {i}. {role_name}")

        role_choice = click.prompt(
            "\n  Select role (enter number)",
            type=click.IntRange(1, len(roles))
        )
        role_name, role_id = roles[role_choice - 1]

        # Step 4: Confirm and execute
        click.echo(f"\n  Assignment summary:")
        click.echo(f"    Document:  {selected_doc.get('DocumentName')}")
        click.echo(f"    User:      {selected_user.get('FullName')}")
        click.echo(f"    Role:      {role_name}")

        if not click.confirm("\n  Confirm assignment?", default=True):
            click.echo("  Cancelled.")
            return

        pm.set_project_translation_document_user_assignments(
            project_guid=project_guid,
            document_guid=doc_guid,
            user_guid=user_guid,
            role=role_id,
        )

        click.echo(f"\n  ✓ Successfully assigned {selected_user.get('FullName')} "
                    f"as {role_name} to {selected_doc.get('DocumentName')}")

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False))


@project.group("users", invoke_without_command=True)
@click.argument("project_guid")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def project_users(ctx, project_guid, as_json):
    """List or manage project user assignments"""
    ctx.ensure_object(dict)
    ctx.obj["project_guid"] = project_guid

    if ctx.invoked_subcommand is not None:
        return

    try:
        pm = ProjectManager()
        users = pm.list_users(active_only=True)

        if as_json:
            output_json(users)
            return

        if not users:
            click.echo("No active users found")
            return

        click.echo(f"\n  Available users ({len(users)}):")
        for i, u in enumerate(users, 1):
            full_name = u.get("FullName", u.get("UserName", "N/A"))
            user_name = u.get("UserName", "")
            click.echo(f"    {i}. {full_name:<30} ({user_name})")

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False))


@project_users.command("assign")
@click.pass_context
def users_assign(ctx):
    """Assign a user to the project"""
    project_guid = ctx.obj["project_guid"]

    try:
        pm = ProjectManager()

        # Step 1: List users
        users = pm.list_users(active_only=True)
        if not users:
            click.echo("No active users found")
            return

        click.echo(f"\n  Available users ({len(users)}):")
        for i, u in enumerate(users, 1):
            full_name = u.get("FullName", u.get("UserName", "N/A"))
            user_name = u.get("UserName", "")
            click.echo(f"    {i}. {full_name:<30} ({user_name})")

        user_choice = click.prompt(
            "\n  Select user (enter number)",
            type=click.IntRange(1, len(users))
        )
        selected_user = users[user_choice - 1]
        user_guid = str(selected_user.get("UserGuid"))

        # Step 2: Select project role
        roles = [
            ("Project Manager", "ProjectManager"),
            ("Translator", "Translator"),
            ("Reviewer 1", "Reviewer1"),
            ("Reviewer 2", "Reviewer2"),
            ("External Translator", "ExternalTranslator"),
            ("External Reviewer 1", "ExternalReviewer1"),
            ("External Reviewer 2", "ExternalReviewer2"),
        ]

        click.echo(f"\n  Available project roles:")
        for i, (role_name, _) in enumerate(roles, 1):
            click.echo(f"    {i}. {role_name}")

        role_choice = click.prompt(
            "\n  Select role (enter number)",
            type=click.IntRange(1, len(roles))
        )
        role_name, role_value = roles[role_choice - 1]

        # Step 3: Confirm and execute
        click.echo(f"\n  Assignment summary:")
        click.echo(f"    User:  {selected_user.get('FullName')}")
        click.echo(f"    Role:  {role_name}")

        if not click.confirm("\n  Confirm assignment?", default=True):
            click.echo("  Cancelled.")
            return

        user_info = {
            "UserGuid": user_guid,
            "ProjectRoles": role_value,
        }

        pm.set_project_users(
            project_guid=project_guid,
            user_infos=[user_info]
        )

        click.echo(f"\n  ✓ Successfully assigned {selected_user.get('FullName')} "
                    f"as {role_name} to project")

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
