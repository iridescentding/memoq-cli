"""Security WSAPI payload and preservation tests (no server mutations)."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from zeep.exceptions import Fault

from memoq_cli.wsapi.user import (
    GUID_ARRAY_TYPE, PM_GROUP_GUID, TRANSLATOR_GROUP_GUID, USER_INFO_TYPE, UserManager,
)


USER_GUID = "11111111-1111-1111-1111-111111111111"
EVERYONE_GUID = "00000000-0000-0000-0000-100000000000"
CUSTOM_GROUP_GUID = "22222222-2222-2222-2222-222222222222"


@pytest.fixture
def manager_and_client():
    config = SimpleNamespace(server_host="https://test.invalid", wsapi_port=8080, api_key="test")
    with patch("memoq_cli.wsapi.client.get_config", return_value=config):
        with UserManager() as manager:
            client = MagicMock()
            client.get_type.side_effect = lambda name: lambda **kwargs: kwargs
            manager.get_client = MagicMock(return_value=client)
            yield manager, client


def test_create_uses_password_protocol_and_returns_guid(manager_and_client):
    manager, client = manager_and_client
    client.service.CreateUser.return_value = USER_GUID
    result = manager.create_user("alice", "test-password", email="alice@example.com")
    assert result == USER_GUID
    manager.get_client.assert_called_once_with("Security")
    client.get_type.assert_called_once_with(USER_INFO_TYPE)
    info = client.service.CreateUser.call_args.kwargs["userInfo"]
    assert info["UserName"] == "alice"
    assert info["FullName"] == "alice"
    assert info["EmailAddress"] == "alice@example.com"
    assert info["IsDisabled"] is False
    assert info["Password"] == "73A456B1E0BE639B6E5F8B7BFC7A11BBF64442ED"
    assert "PlainTextPassword" not in info


@pytest.mark.parametrize("result", [None, "", "00000000-0000-0000-0000-000000000000"])
def test_create_does_not_report_success_without_guid(manager_and_client, result):
    manager, client = manager_and_client
    client.service.CreateUser.return_value = result
    with pytest.raises(RuntimeError, match="no user GUID"):
        manager.create_user("alice", "test-password")


@pytest.mark.parametrize("username,password", [("", "pw"), ("  ", "pw"), ("alice", "")])
def test_create_rejects_empty_credentials_before_network(manager_and_client, username, password):
    manager, client = manager_and_client
    with pytest.raises(ValueError, match="cannot be empty"):
        manager.create_user(username, password)
    manager.get_client.assert_not_called()


def test_list_includes_disabled_users_and_strips_credentials(manager_and_client):
    manager, client = manager_and_client
    client.service.ListUsers.return_value = [
        {"UserGuid": USER_GUID, "IsDisabled": False, "Password": "hash"},
        {"UserGuid": "disabled", "IsDisabled": True, "PlainTextPassword": "secret"},
    ]
    users = manager.list_users()
    assert len(users) == 2
    assert users[1]["IsDisabled"] is True
    assert all("Password" not in user and "PlainTextPassword" not in user for user in users)
    # Never alter the original response object.
    assert client.service.ListUsers.return_value[0]["Password"] == "hash"


def test_empty_list_returns_empty_array(manager_and_client):
    manager, client = manager_and_client
    client.service.ListUsers.return_value = None
    assert manager.list_users() == []


def test_update_preserves_omitted_fields_password_and_false_values(manager_and_client):
    manager, client = manager_and_client
    original = {
        "UserGuid": USER_GUID, "UserName": "alice", "FullName": "Alice",
        "Password": "existing-hash", "PlainTextPassword": None,
        "EmailAddress": "old@example.com", "IsDisabled": True,
        "LanguagePairs": "eng#zho-CN", "PackageWorkflowType": "Both",
        "SecondarySID": CUSTOM_GROUP_GUID,
    }
    client.service.GetUser.return_value = original
    manager.update_user(USER_GUID, email="", disabled=False, full_name=None)
    info = client.service.UpdateUser.call_args.kwargs["userInfo"]
    assert info == {**original, "EmailAddress": "", "IsDisabled": False}
    assert original["EmailAddress"] == "old@example.com"
    client.service.GetUser.assert_called_once_with(userGuid=USER_GUID)


def test_password_update_clears_plaintext_and_preserves_profile(manager_and_client):
    manager, client = manager_and_client
    client.service.GetUser.return_value = {
        "UserGuid": USER_GUID, "FullName": "Alice", "Password": "old",
        "PlainTextPassword": "old-plaintext",
    }
    manager.update_user(USER_GUID, password="test-password")
    info = client.service.UpdateUser.call_args.kwargs["userInfo"]
    assert info["Password"] == "73A456B1E0BE639B6E5F8B7BFC7A11BBF64442ED"
    assert info["PlainTextPassword"] is None
    assert info["FullName"] == "Alice"


@pytest.mark.parametrize("changes", [{}, {"email": None}, {"password": ""}, {"username": " "}, {"bogus": "x"}])
def test_invalid_update_never_calls_server(manager_and_client, changes):
    manager, client = manager_and_client
    with pytest.raises(ValueError):
        manager.update_user(USER_GUID, **changes)
    manager.get_client.assert_not_called()


def test_missing_user_is_not_updated(manager_and_client):
    manager, client = manager_and_client
    client.service.GetUser.return_value = None
    with pytest.raises(ValueError, match="User not found"):
        manager.update_user(USER_GUID, email="new@example.com")
    client.service.UpdateUser.assert_not_called()


def test_username_rename_is_rejected_before_any_partial_update(manager_and_client):
    manager, client = manager_and_client
    with pytest.raises(ValueError, match="login usernames cannot be changed"):
        manager.update_user(USER_GUID, username="renamed", email="new@example.com")
    manager.get_client.assert_not_called()


def test_delete_passes_guid_and_propagates_server_fault(manager_and_client):
    manager, client = manager_and_client
    client.service.DeleteUser.side_effect = Fault("Cannot delete admin")
    with pytest.raises(Fault, match="Cannot delete admin"):
        manager.delete_user(USER_GUID)
    client.service.DeleteUser.assert_called_once_with(userGuid=USER_GUID)


@pytest.mark.parametrize("method,target,other", [
    ("set_pm", PM_GROUP_GUID, TRANSLATOR_GROUP_GUID),
    ("set_translator", TRANSLATOR_GROUP_GUID, PM_GROUP_GUID),
])
def test_role_addition_preserves_all_groups(manager_and_client, method, target, other):
    manager, client = manager_and_client
    client.service.ListGroupsOfUser.return_value = [
        {"GroupGuid": EVERYONE_GUID}, {"GroupGuid": CUSTOM_GROUP_GUID}, {"GroupGuid": other},
    ]
    getattr(manager, method)(USER_GUID)
    client.service.ListGroupsOfUser.assert_called_once_with(userGuid=USER_GUID)
    client.get_type.assert_called_once_with(GUID_ARRAY_TYPE)
    client.service.SetGroupsOfUser.assert_called_once_with(
        userGuid=USER_GUID,
        groupGuids={"guid": [EVERYONE_GUID, CUSTOM_GROUP_GUID, other, target]},
    )


@pytest.mark.parametrize("method,target", [
    ("set_pm", PM_GROUP_GUID), ("set_translator", TRANSLATOR_GROUP_GUID),
])
def test_existing_role_does_not_write(manager_and_client, method, target):
    manager, client = manager_and_client
    client.service.ListGroupsOfUser.return_value = [{"GroupGuid": target}]
    getattr(manager, method)(USER_GUID)
    client.service.SetGroupsOfUser.assert_not_called()


def test_role_read_failure_cannot_clear_memberships(manager_and_client):
    manager, client = manager_and_client
    client.service.ListGroupsOfUser.side_effect = Fault("Read failed")
    with pytest.raises(Fault, match="Read failed"):
        manager.set_pm(USER_GUID)
    client.service.SetGroupsOfUser.assert_not_called()
