# -*- coding: utf-8 -*-
"""Server user administration commands."""

import click

from ..utils import handle_api_error, output_json
from ..wsapi.user import PM_GROUP_GUID, TRANSLATOR_GROUP_GUID, UserManager


def _nonempty(ctx, param, value):
    if value is not None and not value.strip():
        raise click.BadParameter("must not be empty", ctx=ctx, param=param)
    return value


def _profile_options(command):
    """Shared editable profile fields; None means keep the current value."""
    for args, kwargs in [
        (("--full-name",), {"help": "Full name / 姓名"}),
        (("--email",), {"help": "Email address / 邮箱"}),
        (("--language-pairs",), {"help": "Language pairs, e.g. eng#zho-CN;eng#ger"}),
        (("--disabled/--enabled",), {"default": None, "help": "Disable/enable login"}),
        (("--address",), {"help": "Postal address"}),
        (("--phone",), {"help": "Phone number"}),
        (("--mobile",), {"help": "Mobile phone number"}),
    ]:
        command = click.option(*args, **kwargs)(command)
    return command


@click.group()
def user():
    """服务器用户管理 / Server user management.

    \b
    add         创建用户 / Create user
    delete      删除用户 / Delete user
    update      更新用户 / Update user
    listusers   列出所有用户 / List all users
    setpm       将用户加入 PM 组 / Add user to ProjectManagers
    settm       将用户加入译员组 / Add user to Translators
    """


@user.command("add")
@click.option("--username", "-u", required=True, callback=_nonempty, help="Login username")
@click.option("--password", hide_input=True, help="Password; prompts securely if omitted")
@_profile_options
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def user_add(ctx, username, password, as_json, **profile):
    """创建用户 / Create user.

    \b
    Examples:
        memoq user add --username alice --full-name "Alice Zhang"
        memoq user add -u alice --email alice@example.com --json
    """
    if password is None:
        password = click.prompt("Password", hide_input=True, confirmation_prompt=True)
    if not password:
        raise click.BadParameter("must not be empty", param_hint="--password")
    profile = {key: value for key, value in profile.items() if value is not None}
    try:
        with UserManager() as manager:
            user_guid = manager.create_user(username=username, password=password, **profile)
        if as_json:
            output_json({"UserGuid": user_guid, "UserName": username})
        else:
            click.echo(f"Done: User created: {username} ({user_guid})")
    except Exception as exc:
        handle_api_error(exc, (ctx.obj or {}).get("verbose", False))


@user.command("delete")
@click.argument("user_guid", type=click.UUID)
@click.option("--yes", "-y", is_flag=True, help="Skip deletion confirmation")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def user_delete(ctx, user_guid, yes, as_json):
    """删除用户 / Delete user: memoq user delete <USER_GUID> [-y]."""
    user_guid = str(user_guid)
    if not yes:
        click.confirm(f"Delete user {user_guid}?", default=False, abort=True)
    try:
        with UserManager() as manager:
            manager.delete_user(user_guid)
        if as_json:
            output_json({"UserGuid": user_guid, "Deleted": True})
        else:
            click.echo(f"Done: User deleted: {user_guid}")
    except Exception as exc:
        handle_api_error(exc, (ctx.obj or {}).get("verbose", False))


@user.command("update")
@click.argument("user_guid", type=click.UUID)
@click.option("--password", hide_input=True, help="New password (omitted = unchanged)")
@click.option("--reset-password", is_flag=True, help="Prompt securely for a new password")
@_profile_options
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def user_update(ctx, user_guid, password, reset_password, as_json, **profile):
    """更新指定字段，保留其他资料 / Update only specified fields.

    \b
    Examples:
        memoq user update <USER_GUID> --full-name "Alice Zhang" --email alice@example.com
        memoq user update <USER_GUID> --disabled
        memoq user update <USER_GUID> --reset-password
    """
    if reset_password and password is not None:
        raise click.UsageError("Use either --password or --reset-password")
    if reset_password:
        password = click.prompt("New password", hide_input=True, confirmation_prompt=True)
    if password == "":
        raise click.BadParameter("must not be empty", param_hint="--password")
    changes = {key: value for key, value in profile.items() if value is not None}
    if password is not None:
        changes["password"] = password
    if not changes:
        raise click.UsageError("Specify at least one user field to update")
    user_guid = str(user_guid)
    try:
        with UserManager() as manager:
            manager.update_user(user_guid, **changes)
        if as_json:
            output_json({"UserGuid": user_guid, "Updated": True})
        else:
            click.echo(f"Done: User updated: {user_guid}")
    except Exception as exc:
        handle_api_error(exc, (ctx.obj or {}).get("verbose", False))


@user.command("listusers")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def user_list(ctx, as_json):
    """列出所有用户（包括禁用用户）/ List all users, including disabled users."""
    try:
        with UserManager() as manager:
            users = manager.list_users()
        if as_json:
            output_json(users)
        elif not users:
            click.echo("No users found")
        else:
            click.echo(f"Found {len(users)} user(s):\n")
            for info in users:
                status = "disabled" if info.get("IsDisabled") else "enabled"
                click.echo(f"{info.get('UserGuid', '')}  {info.get('UserName', '')}  "
                           f"{info.get('FullName', '')}  {info.get('EmailAddress') or ''}  [{status}]")
    except Exception as exc:
        handle_api_error(exc, (ctx.obj or {}).get("verbose", False))


def _set_role(ctx, user_guid, as_json, role):
    user_guid = str(user_guid)
    try:
        with UserManager() as manager:
            if role == "PM":
                manager.set_pm(user_guid)
            else:
                manager.set_translator(user_guid)
        if as_json:
            output_json({"UserGuid": user_guid, "Role": role,
                         "GroupGuid": PM_GROUP_GUID if role == "PM" else TRANSLATOR_GROUP_GUID})
        else:
            click.echo(f"Done: User {user_guid} is a {role} (other groups preserved)")
    except Exception as exc:
        handle_api_error(exc, (ctx.obj or {}).get("verbose", False))


@user.command("setpm")
@click.argument("user_guid", type=click.UUID)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def user_setpm(ctx, user_guid, as_json):
    """将用户加入 PM 组，保留其他组 / Add user to ProjectManagers."""
    _set_role(ctx, user_guid, as_json, "PM")


@user.command("settm")
@click.argument("user_guid", type=click.UUID)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def user_settm(ctx, user_guid, as_json):
    """将用户加入译员组，保留其他组 / Add user to Translators."""
    _set_role(ctx, user_guid, as_json, "Translator")
