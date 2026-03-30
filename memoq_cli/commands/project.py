# -*- coding: utf-8 -*-
"""
memoQ CLI - Project Commands
"""

import sys
from datetime import datetime, timedelta
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
@click.option("--detailed", "-d", is_flag=True,
              help="Show detailed info with assignments (uses ListProjectTranslationDocuments2)")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def project_docs(ctx, project_guid, status, detailed, as_json):
    """List documents in a project, or manage document assignments"""
    ctx.ensure_object(dict)
    ctx.obj["project_guid"] = project_guid

    if ctx.invoked_subcommand is not None:
        return

    # If -d flag is used, delegate to the detailed subcommand logic
    if detailed:
        ctx.invoke(docs_detailed, no_assignments=False, as_json=as_json)
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


@project_docs.command("detailed")
@click.option("--no-assignments", "-n", is_flag=True,
              help="Skip assignment info (faster)")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def docs_detailed(ctx, no_assignments, as_json):
    """List documents with detailed status and assignment info"""
    project_guid = ctx.obj["project_guid"]

    try:
        pm = ProjectManager()
        docs = pm.list_project_translation_documents2(
            project_guid,
            fill_in_assignment_info=not no_assignments,
        )

        if as_json:
            output_json(docs)
            return

        if not docs:
            click.echo("No documents in project")
            return

        click.echo(f"\nFound {len(docs)} document(s):\n")

        role_map = {0: "Translator", 1: "Reviewer1", 2: "Reviewer2"}

        for i, doc in enumerate(docs, 1):
            name = doc.get("DocumentName", "Unknown")
            guid = doc.get("DocumentGuid", "")
            status_name = doc.get("DocumentStatus", "N/A")
            workflow_status = doc.get("WorkflowStatus", "")
            word_count = doc.get("TotalWordCount", "N/A")
            target_lang = doc.get("TargetLangCode", "N/A")

            click.echo(f"  {i}. {name}")
            click.echo(f"     GUID:      {guid}")
            click.echo(f"     Status:    {status_name}")
            if workflow_status and workflow_status != "Unknown":
                click.echo(f"     Workflow:  {workflow_status}")
            click.echo(f"     Words:     {word_count}")
            click.echo(f"     Target:    {target_lang}")

            # Show assignment info if available
            if not no_assignments:
                assignments_data = doc.get("UserAssignments") or {}
                if isinstance(assignments_data, dict):
                    assign_list = assignments_data.get(
                        "TranslationDocumentDetailedAssignmentInfo", []
                    ) or []
                else:
                    assign_list = assignments_data
                if assign_list:
                    click.echo(f"     Assignments:")
                    for assign in assign_list:
                        role_id = assign.get("RoleId", -1)
                        role_name = role_map.get(role_id, f"Role({role_id})")
                        user = assign.get("User") or {}
                        user_name = user.get("AssigneeName", "N/A")
                        deadline = assign.get("Deadline")
                        deadline_str = ""
                        if deadline:
                            if hasattr(deadline, "strftime"):
                                deadline_str = deadline.strftime("%Y-%m-%d %H:%M")
                            else:
                                deadline_str = str(deadline)[:16]
                        click.echo(f"       - {role_name}: {user_name}"
                                   + (f"  (deadline: {deadline_str})" if deadline_str else ""))
                else:
                    click.echo(f"     Assignments: (none)")

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

        # Step 2: List project users first, with option to add new user
        project_users = pm.list_project_users(project_guid)
        project_user_guids = set()
        selectable_users = []

        if project_users:
            click.echo(f"\n  Project members ({len(project_users)}):")
            for i, pu in enumerate(project_users, 1):
                user_info = pu.get("User", {})
                full_name = user_info.get("FullName", "N/A")
                user_name = user_info.get("UserName", "")
                user_guid = str(user_info.get("UserGuid", ""))
                project_user_guids.add(user_guid)
                selectable_users.append(user_info)
                click.echo(f"    {i}. {full_name:<30} ({user_name})")
        else:
            click.echo(f"\n  No members in this project yet.")

        add_option = len(selectable_users) + 1
        click.echo(f"    {add_option}. [+ Add user from server]")

        user_choice = click.prompt(
            "\n  Select user (enter number)",
            type=click.IntRange(1, add_option)
        )

        if user_choice == add_option:
            # List all server users not already in the project
            all_users = pm.list_users(active_only=True)
            non_project_users = [
                u for u in all_users
                if str(u.get("UserGuid", "")) not in project_user_guids
            ]

            if not non_project_users:
                click.echo("  All users are already in this project.")
                return

            click.echo(f"\n  Available users to add ({len(non_project_users)}):")
            for i, u in enumerate(non_project_users, 1):
                full_name = u.get("FullName", u.get("UserName", "N/A"))
                user_name = u.get("UserName", "")
                click.echo(f"    {i}. {full_name:<30} ({user_name})")

            new_user_choice = click.prompt(
                "\n  Select user to add (enter number)",
                type=click.IntRange(1, len(non_project_users))
            )
            selected_user = non_project_users[new_user_choice - 1]
            user_guid = str(selected_user.get("UserGuid"))

            # Add user to project first
            pm.set_project_users(
                project_guid=project_guid,
                user_infos=[{
                    "UserGuid": user_guid,
                    "ProjectRoles": {"ProjectManager": False, "Terminologist": False},
                }]
            )
            click.echo(f"  ✓ Added {selected_user.get('FullName')} to project")
        else:
            selected_user = selectable_users[user_choice - 1]
            user_guid = str(selected_user.get("UserGuid"))

        # Step 3: Select role
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

        # Step 4: Set deadline
        default_deadline = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
        deadline_str = click.prompt(
            f"\n  Deadline (YYYY-MM-DD)",
            default=default_deadline,
        )
        try:
            deadline_dt = datetime.strptime(deadline_str, "%Y-%m-%d").replace(hour=9, minute=0, second=0)
        except ValueError:
            click.echo("  Invalid date format. Use YYYY-MM-DD.")
            return

        # Step 5: Confirm and execute
        full_name = selected_user.get("FullName", selected_user.get("UserName", "N/A"))
        click.echo(f"\n  Assignment summary:")
        click.echo(f"    Document:  {selected_doc.get('DocumentName')}")
        click.echo(f"    User:      {full_name}")
        click.echo(f"    Role:      {role_name}")
        click.echo(f"    Deadline:  {deadline_dt.strftime('%Y-%m-%d %H:%M')}")

        if not click.confirm("\n  Confirm assignment?", default=True):
            click.echo("  Cancelled.")
            return

        pm.set_project_translation_document_user_assignments(
            project_guid=project_guid,
            document_guid=doc_guid,
            user_guid=user_guid,
            role=role_id,
            deadline=deadline_dt,
        )

        click.echo(f"\n  ✓ Successfully assigned {full_name} "
                    f"as {role_name} to {selected_doc.get('DocumentName')} "
                    f"(deadline: {deadline_dt.strftime('%Y-%m-%d %H:%M')})")

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False))


@project_docs.command("userassign")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def docs_userassign(ctx, as_json):
    """List document user assignments in a table"""
    project_guid = ctx.obj["project_guid"]

    try:
        pm = ProjectManager()

        # Get documents for name lookup
        docs = pm.list_project_documents(project_guid)
        doc_name_map = {
            str(d.get("DocumentGuid", "")): d.get("DocumentName", "Unknown")
            for d in docs
        }

        # Get assignments
        assignments = pm.list_translation_document_assignments(project_guid)

        if as_json:
            output_json(assignments)
            return

        if not assignments:
            click.echo("No document assignments found")
            return

        role_map = {0: "Translator", 1: "Reviewer1", 2: "Reviewer2"}

        # Build table data: one row per document
        rows = []
        for doc_assign in assignments:
            doc_guid = str(doc_assign.get("DocumentGuid", ""))
            doc_name = doc_name_map.get(doc_guid, doc_guid[:8] + "...")

            row = {
                "doc_guid": doc_guid,
                "doc_name": doc_name,
                "Translator": "",
                "Deadline(T)": "",
                "Reviewer1": "",
                "Deadline(R1)": "",
                "Reviewer2": "",
                "Deadline(R2)": "",
            }

            assignments_data = doc_assign.get("Assignments") or {}
            if isinstance(assignments_data, dict):
                assign_list = assignments_data.get("TranslationDocumentDetailedAssignmentInfo") or []
            else:
                assign_list = assignments_data
            for assign_info in assign_list:
                role_id = assign_info.get("RoleId", -1)
                role_name = role_map.get(role_id)
                if not role_name:
                    continue

                deadline = assign_info.get("Deadline")
                deadline_str = ""
                if deadline:
                    if hasattr(deadline, "strftime"):
                        deadline_str = deadline.strftime("%Y-%m-%d %H:%M")
                    else:
                        deadline_str = str(deadline)[:16]

                # Get user info from single user assignment
                user = assign_info.get("User")
                user_name = ""
                if user:
                    user_name = user.get("AssigneeName", "")

                if role_name == "Translator":
                    row["Translator"] = user_name
                    row["Deadline(T)"] = deadline_str
                elif role_name == "Reviewer1":
                    row["Reviewer1"] = user_name
                    row["Deadline(R1)"] = deadline_str
                elif role_name == "Reviewer2":
                    row["Reviewer2"] = user_name
                    row["Deadline(R2)"] = deadline_str

            rows.append(row)

        # Print table
        headers = [
            ("Document", "doc_name", 28),
            ("Translator", "Translator", 18),
            ("Deadline(T)", "Deadline(T)", 18),
            ("Reviewer1", "Reviewer1", 18),
            ("Deadline(R1)", "Deadline(R1)", 18),
            ("Reviewer2", "Reviewer2", 18),
            ("Deadline(R2)", "Deadline(R2)", 18),
        ]

        # Header line
        header_line = "  ".join(h.ljust(w) for h, _, w in headers)
        click.echo(f"\n  {header_line}")
        click.echo(f"  {'=' * len(header_line)}")

        for row in rows:
            line = "  ".join(
                str(row.get(key, "")).ljust(w)
                for _, key, w in headers
            )
            click.echo(f"  {line}")

        click.echo()

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

        # Show current project users
        project_users = pm.list_project_users(project_guid)
        project_user_guids = set()
        if project_users:
            click.echo(f"\n  Current project members ({len(project_users)}):")
            for pu in project_users:
                user_info = pu.get("User", {})
                full_name = user_info.get("FullName", "N/A")
                user_name = user_info.get("UserName", "")
                roles = pu.get("ProjectRoles", {})
                role_str = "PM" if roles.get("ProjectManager") else "Member"
                project_user_guids.add(str(user_info.get("UserGuid", "")))
                click.echo(f"    - {full_name:<30} ({user_name}) [{role_str}]")

        # List users not yet in the project
        all_users = pm.list_users(active_only=True)
        non_project_users = [
            u for u in all_users
            if str(u.get("UserGuid", "")) not in project_user_guids
        ]

        if not non_project_users:
            click.echo("\n  All users are already in this project.")
            return

        click.echo(f"\n  Users not in project ({len(non_project_users)}):")
        for i, u in enumerate(non_project_users, 1):
            full_name = u.get("FullName", u.get("UserName", "N/A"))
            user_name = u.get("UserName", "")
            click.echo(f"    {i}. {full_name:<30} ({user_name})")

        user_choice = click.prompt(
            "\n  Select user to add (enter number)",
            type=click.IntRange(1, len(non_project_users))
        )
        selected_user = non_project_users[user_choice - 1]
        user_guid = str(selected_user.get("UserGuid"))

        # Step 2: Select project role
        roles = [
            ("Project Manager", {"ProjectManager": True, "Terminologist": False}),
            ("Member", {"ProjectManager": False, "Terminologist": False}),
            ("Terminologist", {"ProjectManager": False, "Terminologist": True}),
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

        pm.set_project_users(
            project_guid=project_guid,
            user_infos=[{
                "UserGuid": user_guid,
                "ProjectRoles": role_value,
            }]
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
