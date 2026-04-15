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
    """项目管理命令 / Project management commands

    \b
    子命令 / Subcommands:
        list     列出所有项目 / List all projects
        info     查看项目详情 / Show project details
        update   更新项目头信息 / Update project header
        docs     列出/管理项目文档 / List/manage project documents
        users    列出/管理项目成员 / List/manage project members
        stats    获取项目统计 / Get project statistics (async)
    """
    pass


@project.command("list")
@click.option("--filter", "-f", "filter_text", help="Filter by name")
@click.option("--archived", "-a", is_flag=True, help="Include archived projects")
@click.option("--limit", "-n", type=int, help="Limit number of results")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def project_list(ctx, filter_text, archived, limit, as_json):
    """列出所有项目 / List all projects

    \b
    示例 / Examples:
        memoq project list
        memoq project list -f "translation"
        memoq project list --archived -n 10
        memoq project list --json
    """
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
    """查看项目详情 / Get project details

    \b
    参数 / Arguments:
        PROJECT_GUID   项目 GUID / Project GUID

    \b
    示例 / Examples:
        memoq project info <GUID>
        memoq project info <GUID> --json
    """
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


@project.command("update")
@click.argument("project_guid")
@click.option("--desc", "-d", default=None, help="Description")
@click.option("--deadline", default=None, help="Deadline (YYYY-MM-DD)")
@click.option("--client", default=None, help="Client attribute")
@click.option("--domain", default=None, help="Domain attribute")
@click.option("--project-attr", default=None, help="Project attribute")
@click.option("--subject", default=None, help="Subject attribute")
@click.option("--callback-url", default=None, help="Callback web service URL")
@click.option("--source-editing-off/--source-editing-on", default=None,
              help="Disable/enable source editing")
@click.pass_context
def project_update(ctx, project_guid, desc, deadline, client, domain,
                   project_attr, subject, callback_url, source_editing_off):
    """更新项目头信息 / Update project header information

    \b
    可更新字段 / Updatable fields:
        --desc / --deadline / --client / --domain / --project-attr / --subject
        --callback-url / --source-editing-off|--source-editing-on

    \b
    示例 / Examples:
        memoq project update <GUID> --desc "新描述 / New description"
        memoq project update <GUID> --deadline 2026-06-01
        memoq project update <GUID> --client ACME --domain Tech
        memoq project update <GUID> --callback-url http://localhost:8088/memoq-callback.asmx
        memoq project update <GUID> --callback-url ""   # 清空回调 / clear callback
        memoq project update <GUID> --source-editing-off
    """
    try:
        pm = ProjectManager()

        deadline_dt = None
        if deadline:
            try:
                deadline_dt = datetime.strptime(deadline, "%Y-%m-%d")
            except ValueError:
                click.echo("Error: Invalid date format. Use YYYY-MM-DD.", err=True)
                return

        kwargs = {}
        if desc is not None:
            kwargs["description"] = desc
        if deadline_dt is not None:
            kwargs["deadline"] = deadline_dt
        if client is not None:
            kwargs["client"] = client
        if domain is not None:
            kwargs["domain"] = domain
        if project_attr is not None:
            kwargs["project_attr"] = project_attr
        if subject is not None:
            kwargs["subject"] = subject
        if callback_url is not None:
            kwargs["callback_url"] = callback_url
        if source_editing_off is not None:
            kwargs["source_editing_turned_off"] = source_editing_off

        if not kwargs:
            click.echo("No updates specified. Use --help for options.")
            return

        click.echo(f"\nUpdating project {project_guid}")
        for k, v in kwargs.items():
            click.echo(f"   {k}: {v}")
        click.echo()

        pm.update_project(project_guid, **kwargs)
        click.echo("Done: Project updated!")

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
    """列出/管理项目文档 / List documents or manage document assignments

    \b
    ⚠ 参数顺序 / Argument ordering (重要 / IMPORTANT):
        组级选项 -s / -d / --json 必须放在 PROJECT_GUID 之前, 否则 click 会
        把它当作子命令参数, 报 "Missing argument 'PROJECT_GUID'".
        Group-level flags (-s / -d / --json) MUST come BEFORE PROJECT_GUID,
        otherwise click treats them as subcommand args and errors out with
        "Missing argument 'PROJECT_GUID'".

    \b
        ✓ memoq project docs -d <PROJECT_GUID>
        ✗ memoq project docs <PROJECT_GUID> -d   (错 / wrong)

    \b
    子命令 / Subcommands:
        detailed    显示详细状态与分派信息 / Detailed status + assignments
        assign      交互式分派用户到文档 / Interactively assign user to document
        userassign  以表格形式列出文档分派 / List assignments in table view
        stats       文档级别统计 (异步) / Document-level statistics (async)

    \b
    示例 / Examples:
        memoq project docs <PROJECT_GUID>                # 列出文档 / list docs
        memoq project docs -s <PROJECT_GUID>             # 含状态 / with status
        memoq project docs -d <PROJECT_GUID>             # 含分派 / with assignments
        memoq project docs <PROJECT_GUID> detailed
        memoq project docs <PROJECT_GUID> assign
        memoq project docs <PROJECT_GUID> userassign
        memoq project docs <PROJECT_GUID> stats <DOC_GUID>
    """
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
    """详细文档列表（含分派）/ List documents with detailed status & assignments

    \b
    使用 ListProjectTranslationDocuments2。
    Uses ListProjectTranslationDocuments2 under the hood.

    \b
    示例 / Examples:
        memoq project docs <GUID> detailed
        memoq project docs <GUID> detailed --no-assignments
        memoq project docs <GUID> detailed --json
    """
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
    """交互式分派用户到文档 / Interactively assign a user to a document

    \b
    流程 / Flow:
        1) 选择文档 / pick document
        2) 选择项目成员 或 从服务器添加新用户 / pick member or add server user
        3) 选择角色 Translator / Reviewer1 / Reviewer2
        4) 设置截止日期 (默认 +14 天) / set deadline (default +14 days)

    \b
    示例 / Example:
        memoq project docs <GUID> assign
    """
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
    """以表格形式列出文档分派 / List document assignments in a table

    \b
    示例 / Examples:
        memoq project docs <GUID> userassign
        memoq project docs <GUID> userassign --json
    """
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
    """列出/管理项目成员 / List or manage project user assignments

    \b
    子命令 / Subcommands:
        assign   交互式添加用户到项目 / Interactively add user to project

    \b
    示例 / Examples:
        memoq project users <GUID>            # 列出服务器活跃用户 / list active server users
        memoq project users <GUID> --json
        memoq project users <GUID> assign     # 添加成员 / add member
    """
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
    """交互式添加用户到项目 / Interactively assign a user to the project

    \b
    角色 / Roles:
        1. Project Manager
        2. Member
        3. Terminologist

    \b
    示例 / Example:
        memoq project users <GUID> assign
    """
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


RESULT_FORMATS = ["Html", "CSV_WithTable", "CSV_Trados", "CSV_MemoQ"]


def _decode_result_data(raw):
    """Decode WSAPI StatisticsResultForLang.ResultData (bytes/str) to unicode text."""
    if raw is None:
        return ""
    if isinstance(raw, (bytes, bytearray)):
        data = bytes(raw)
    elif isinstance(raw, str):
        # zeep often returns bytes rendered as a "b'...\\xff...'" repr string
        if raw.startswith("b'") or raw.startswith('b"'):
            try:
                import ast
                data = ast.literal_eval(raw)
                if not isinstance(data, (bytes, bytearray)):
                    return raw
            except Exception:
                return raw
        else:
            return raw
    else:
        return str(raw)

    for enc in ("utf-16", "utf-16-le", "utf-8-sig", "utf-8"):
        try:
            return data.decode(enc).lstrip("\ufeff")
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


_STATS_SUBCOLS = ("Segments", "Words", "Characters", "Asian characters", "Tags")
_STATS_BAND_WIDTH = 8


def _parse_memoq_stats_csv(text):
    """Parse memoQ CSV_* statistics payload into structured dict.

    Raises ValueError if the shape doesn't match expectations; callers
    should fall back to raw echo.
    """
    import csv
    import io
    import re

    rows = list(csv.reader(io.StringIO(text), delimiter=";"))
    if not rows:
        raise ValueError("empty stats csv")

    # memoQ wraps header lines; coalesce rows until we find the sub-header
    # row that starts with "File","Char/Word". Track the immediately
    # preceding coalesced row as the band header.
    flat = []  # list of (row_index, cells) after coalescing
    buf = []
    for r in rows:
        buf.extend(r)
        # Heuristic: a coalesced row ends when we hit "File" followed by
        # "Char/Word" within the buffer (sub-header) OR the buffer grows
        # wide enough to look complete. We just keep appending and detect
        # the sub-header by scanning.
        if len(buf) >= 2 and buf[0] == "File" and buf[1] == "Char/Word":
            flat.append(buf)
            buf = []
        elif r == [] or (r and r[-1] == "" and len(buf) >= 82):
            flat.append(buf)
            buf = []
    if buf:
        flat.append(buf)

    # Find sub-header row and the band header that precedes it.
    sub_idx = None
    for i, row in enumerate(flat):
        if row and row[0] == "File" and len(row) > 1 and row[1] == "Char/Word":
            sub_idx = i
            break
    if sub_idx is None or sub_idx == 0:
        raise ValueError("sub-header not found")

    band_row = flat[sub_idx - 1]
    # Bands live at columns 2, 10, 18, ... (every 8 cols after offset 2).
    bands = []
    i = 2
    while i < len(band_row):
        name = band_row[i].strip()
        if name:
            bands.append(name)
        i += _STATS_BAND_WIDTH
    if not bands:
        raise ValueError("no bands parsed")

    sub_row = flat[sub_idx]
    # Verify sub-columns of first band match expected order (defensive).
    first_band_sub = sub_row[2:2 + _STATS_BAND_WIDTH]
    for want in _STATS_SUBCOLS:
        if want not in first_band_sub:
            raise ValueError(f"sub-column {want!r} missing")

    files = []
    lang_prefix = re.compile(r"^\[[^\]]+\]\s*")
    for row in flat[sub_idx + 1:]:
        if not row or not row[0].strip():
            continue
        name = row[0].strip().strip('"')
        name = lang_prefix.sub("", name)
        # Strip Windows path prefix for cleaner display.
        name = name.split("\\")[-1]
        try:
            char_word = float(row[1]) if row[1] else 0.0
        except ValueError:
            char_word = 0.0

        band_map = {}
        for b_idx, band_name in enumerate(bands):
            start = 2 + b_idx * _STATS_BAND_WIDTH
            chunk = row[start:start + _STATS_BAND_WIDTH]
            if len(chunk) < _STATS_BAND_WIDTH:
                chunk = chunk + [""] * (_STATS_BAND_WIDTH - len(chunk))
            sub = {}
            for s_idx, s_name in enumerate(first_band_sub):
                if s_name not in _STATS_SUBCOLS:
                    continue
                val = chunk[s_idx].strip()
                try:
                    sub[s_name] = int(val) if val else 0
                except ValueError:
                    try:
                        sub[s_name] = int(float(val))
                    except ValueError:
                        sub[s_name] = 0
            band_map[band_name] = sub

        files.append({"name": name, "char_word": char_word, "bands": band_map})

    if not files:
        raise ValueError("no data rows")

    return {"bands": bands, "subcols": list(_STATS_SUBCOLS), "files": files}


def _format_stats_table(parsed, lang):
    """Render a parsed stats dict into a human-friendly aligned table."""
    lines = []
    files = parsed["files"]
    bands = parsed["bands"]
    subcols = parsed["subcols"]

    # Display labels (shorter) while keeping lookup keys intact.
    display = {"Asian characters": "Asian"}
    headers = ["Category"] + [display.get(s, s) for s in subcols]

    def render_table(rows, title=None):
        # rows: list of (label, [values...]) with values as ints
        cells = [headers] + [
            [label] + [f"{v:,}" for v in vals] for label, vals in rows
        ]
        widths = [max(len(r[c]) for r in cells) for c in range(len(headers))]

        def fmt(row):
            parts = [row[0].ljust(widths[0])]
            parts += [row[c].rjust(widths[c]) for c in range(1, len(row))]
            return "  " + "   ".join(parts)

        ruler = "  " + "   ".join("-" * w for w in widths)
        if title:
            lines.append(title)
        lines.append(fmt(headers))
        lines.append(ruler)
        # Non-total rows
        for row in cells[1:-1]:
            lines.append(fmt(row))
        if len(cells) > 2:
            lines.append(ruler)
        # Total row (always last)
        lines.append(fmt(cells[-1]))

    def band_rows_for(band_source):
        # band_source: dict[band -> dict[subcol -> int]]
        out = []
        for b in bands:
            sub = band_source.get(b, {})
            vals = [sub.get(s, 0) for s in subcols]
            if b == "Total":
                continue
            if any(v != 0 for v in vals[:3]):  # Segments/Words/Characters
                out.append((b, vals))
        total_sub = band_source.get("Total", {})
        out.append(("Total", [total_sub.get(s, 0) for s in subcols]))
        return out

    lines.append(f"Target: {lang}  ({len(files)} file(s))")
    lines.append("")

    for f in files:
        cw = f.get("char_word") or 0.0
        lines.append(f"File: {f['name']}  (char/word {cw:.2f})")
        render_table(band_rows_for(f["bands"]))
        lines.append("")

    if len(files) > 1:
        combined = {b: {s: 0 for s in subcols} for b in bands}
        for f in files:
            for b, sub in f["bands"].items():
                for s in subcols:
                    combined.setdefault(b, {}).setdefault(s, 0)
                    combined[b][s] += sub.get(s, 0)
        render_table(band_rows_for(combined), title="All files combined")
        lines.append("")

    return "\n".join(lines)


def _render_stats_result(stats, output_path=None, result_format=None):
    """Pretty-print StatisticsTaskResult; optionally write per-lang files."""
    results = (stats or {}).get("ResultsForTargetLangs") or {}
    items = results.get("StatisticsResultForLang") if isinstance(results, dict) else results
    items = items or []

    pretty = (
        output_path is None
        and isinstance(result_format, str)
        and result_format.startswith("CSV_")
    )

    click.echo(f"\nStatistics ({len(items)} language(s)):\n")
    for item in items:
        lang = item.get("TargetLangCode", "?")
        text = _decode_result_data(item.get("ResultData"))

        rendered = None
        if pretty and text.strip():
            try:
                rendered = _format_stats_table(_parse_memoq_stats_csv(text), lang)
            except Exception:
                rendered = None

        if rendered is not None:
            click.echo(rendered)
        else:
            click.echo(f"--- Target: {lang} ---")
            click.echo(text if text.strip() else "(empty)")
            click.echo()

        if output_path:
            from pathlib import Path
            out = Path(output_path)
            out.mkdir(parents=True, exist_ok=True)
            fname = out / f"stats_{lang}.csv"
            fname.write_text(text, encoding="utf-8")
            click.echo(f"  saved: {fname}")


@project.command("stats")
@click.argument("project_guid")
@click.option("--target-lang", "-l", multiple=True,
              help="目标语言过滤 / Target language filter (可重复 / repeatable)")
@click.option("--format", "-F", "result_format",
              type=click.Choice(RESULT_FORMATS), default="CSV_MemoQ",
              help="结果格式 / Result format (默认 CSV_MemoQ)")
@click.option("--output", "-o", type=click.Path(),
              help="保存到目录, 每个目标语言一个文件 / Save per-language files here")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON (原始响应 / raw)")
@click.pass_context
def project_stats(ctx, project_guid, target_lang, result_format, output, as_json):
    """获取项目统计 / Get project statistics (async)

    \b
    使用异步接口 StartStatisticsOnProjectTask2 + TasksService 轮询。
    Uses StartStatisticsOnProjectTask2 + TasksService polling.

    \b
    结果格式 / Result format:
        Html | CSV_WithTable | CSV_Trados | CSV_MemoQ   (默认 / default: CSV_MemoQ)

    \b
    示例 / Examples:
        memoq project stats <PROJECT_GUID>
        memoq project stats <PROJECT_GUID> -l kor -l por -F CSV_MemoQ
        memoq project stats <PROJECT_GUID> -o ./stats_out
        memoq project stats <PROJECT_GUID> --json
    """
    try:
        pm = ProjectManager()
        stats = pm.get_project_statistics(
            project_guid,
            target_lang_codes=list(target_lang) if target_lang else None,
            result_format=result_format,
        )

        if as_json:
            output_json(stats)
            return

        _render_stats_result(stats, output, result_format=result_format)

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False))


@project_docs.command("stats")
@click.argument("document_guid", nargs=-1, required=True)
@click.option("--format", "-F", "result_format",
              type=click.Choice(RESULT_FORMATS), default="CSV_MemoQ",
              help="结果格式 / Result format (默认 CSV_MemoQ)")
@click.option("--output", "-o", type=click.Path(),
              help="保存到目录 / Save per-language files here")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON (原始响应 / raw)")
@click.pass_context
def docs_stats(ctx, document_guid, result_format, output, as_json):
    """获取指定文档的统计 / Get statistics on specific document(s) (async)

    \b
    使用 StartStatisticsOnTranslationDocumentsTask2 + TasksService 轮询。
    Uses StartStatisticsOnTranslationDocumentsTask2 + TasksService polling.

    \b
    参数 / Arguments:
        DOCUMENT_GUID   一个或多个文档 GUID / One or more document GUIDs
                        (memoq project docs <PROJECT_GUID> 可查看)

    \b
    示例 / Examples:
        memoq project docs <PROJECT_GUID> stats <DOC_GUID>
        memoq project docs <PROJECT_GUID> stats <DOC_GUID_1> <DOC_GUID_2>
        memoq project docs <PROJECT_GUID> stats <DOC_GUID> -F CSV_MemoQ -o ./out
        memoq project docs <PROJECT_GUID> stats <DOC_GUID> --json
    """
    project_guid = ctx.obj["project_guid"]
    try:
        pm = ProjectManager()
        stats = pm.get_document_statistics(
            project_guid,
            list(document_guid),
            result_format=result_format,
        )

        if as_json:
            output_json(stats)
            return

        _render_stats_result(stats, output, result_format=result_format)

    except Exception as e:
        handle_api_error(e, ctx.obj.get("verbose", False))
