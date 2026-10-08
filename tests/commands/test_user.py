"""CLI validation, prompts, dispatch and failure output for server users."""

import json
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from memoq_cli.cli import cli
from memoq_cli.commands.user import user


USER_GUID = "11111111-1111-1111-1111-111111111111"


@pytest.fixture
def manager():
    with patch("memoq_cli.commands.user.UserManager") as manager_class:
        instance = manager_class.return_value
        instance.__enter__.return_value = instance
        instance.create_user.return_value = USER_GUID
        instance.list_users.return_value = []
        yield instance


def invoke(args, **kwargs):
    return CliRunner().invoke(user, args, obj={"verbose": False}, **kwargs)


def test_user_group_registered_at_top_level():
    assert cli.commands["user"] is user
    result = CliRunner().invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "user" in result.output


def test_add_prompts_for_password_and_outputs_guid(manager):
    result = invoke(["add", "-u", "alice", "--full-name", "Alice", "--json"],
                    input="secret\nsecret\n")
    assert result.exit_code == 0, result.output
    manager.create_user.assert_called_once_with(username="alice", password="secret", full_name="Alice")
    assert "secret" not in result.output
    assert USER_GUID in result.output
    manager.__exit__.assert_called_once()


def test_add_explicit_password_returns_machine_json(manager):
    result = invoke(["add", "-u", "alice", "--password", "secret", "--disabled", "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == {"UserGuid": USER_GUID, "UserName": "alice"}
    manager.create_user.assert_called_once_with(username="alice", password="secret", disabled=True)


@pytest.mark.parametrize("args", [
    ["add", "--password", "pw"],
    ["add", "-u", " ", "--password", "pw"],
    ["add", "-u", "alice", "--password", ""],
])
def test_invalid_add_does_not_write(manager, args):
    result = invoke(args)
    assert result.exit_code == 2
    manager.create_user.assert_not_called()


def test_delete_rejected_confirmation_never_calls_api(manager):
    result = invoke(["delete", USER_GUID], input="n\n")
    assert result.exit_code != 0
    manager.delete_user.assert_not_called()


@pytest.mark.parametrize("args,input_text", [(["delete", USER_GUID], "y\n"),
                                          (["delete", USER_GUID, "-y"], None)])
def test_delete_confirmed_or_yes_flag(manager, args, input_text):
    result = invoke(args, input=input_text)
    assert result.exit_code == 0, result.output
    manager.delete_user.assert_called_once_with(USER_GUID)


def test_update_sends_only_selected_fields_including_empty_and_false(manager):
    result = invoke(["update", USER_GUID, "--email", "", "--enabled", "--json"])
    assert result.exit_code == 0, result.output
    manager.update_user.assert_called_once_with(USER_GUID, email="", disabled=False)
    assert json.loads(result.output) == {"UserGuid": USER_GUID, "Updated": True}


def test_password_reset_uses_hidden_prompt(manager):
    result = invoke(["update", USER_GUID, "--reset-password"], input="new-secret\nnew-secret\n")
    assert result.exit_code == 0, result.output
    assert "new-secret" not in result.output
    manager.update_user.assert_called_once_with(USER_GUID, password="new-secret")


def test_update_does_not_advertise_unsupported_username_rename(manager):
    help_result = invoke(["update", "--help"])
    assert "--username" not in help_result.output
    result = invoke(["update", USER_GUID, "--username", "renamed", "--email", "new@example.com"])
    assert result.exit_code == 2
    manager.update_user.assert_not_called()


@pytest.mark.parametrize("args", [
    ["update", USER_GUID],
    ["update", USER_GUID, "--password", ""],
    ["update", USER_GUID, "--username", " "],
    ["update", USER_GUID, "--password", "pw", "--reset-password"],
])
def test_invalid_update_does_not_write(manager, args):
    result = invoke(args)
    assert result.exit_code == 2, result.output
    manager.update_user.assert_not_called()


def test_list_json_contains_disabled_users(manager):
    users = [{"UserGuid": USER_GUID, "UserName": "alice", "IsDisabled": True}]
    manager.list_users.return_value = users
    result = invoke(["listusers", "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == users


def test_list_text_and_empty_json(manager):
    manager.list_users.return_value = [{"UserGuid": USER_GUID, "UserName": "alice", "IsDisabled": True}]
    result = invoke(["listusers"])
    assert result.exit_code == 0
    assert "alice" in result.output and "disabled" in result.output
    manager.list_users.return_value = []
    assert json.loads(invoke(["listusers", "--json"]).output) == []


@pytest.mark.parametrize("command,method", [("setpm", "set_pm"), ("settm", "set_translator")])
def test_role_commands_dispatch(manager, command, method):
    result = invoke([command, USER_GUID, "--json"])
    assert result.exit_code == 0, result.output
    getattr(manager, method).assert_called_once_with(USER_GUID)
    assert json.loads(result.output)["UserGuid"] == USER_GUID


@pytest.mark.parametrize("command", ["delete", "update", "setpm", "settm"])
def test_invalid_guid_is_rejected_before_api(manager, command):
    result = invoke([command, "invalid-guid"])
    assert result.exit_code == 2
    manager.__enter__.assert_not_called()


@pytest.mark.parametrize("args,method", [
    (["add", "-u", "alice", "--password", "pw"], "create_user"),
    (["delete", USER_GUID, "-y"], "delete_user"),
    (["update", USER_GUID, "--email", "new@example.com"], "update_user"),
    (["listusers"], "list_users"),
    (["setpm", USER_GUID], "set_pm"),
    (["settm", USER_GUID], "set_translator"),
])
def test_api_failure_has_nonzero_exit_and_no_success_output(manager, args, method):
    getattr(manager, method).side_effect = RuntimeError("Server rejected request")
    result = invoke(args)
    assert result.exit_code == 1, result.output
    assert "Server rejected request" in result.output
    assert "Done:" not in result.output
    manager.__exit__.assert_called_once()
