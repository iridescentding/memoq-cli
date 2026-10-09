# -*- coding: utf-8 -*-
"""memoQ Server user management through the Security WSAPI."""

import hashlib
from typing import Any, Dict, List, Optional

from zeep.helpers import serialize_object

from .client import WSAPIClient


USER_INFO_TYPE = "{http://kilgray.com/memoqservices/2007}UserInfo"
GUID_ARRAY_TYPE = "{http://schemas.microsoft.com/2003/10/Serialization/Arrays}ArrayOfguid"
# Built-in group identifiers documented by memoQ; independent of display names.
PM_GROUP_GUID = "00000000-0000-0000-0000-000000000002"
TRANSLATOR_GROUP_GUID = "00000000-0000-0000-0000-000000000003"
EMPTY_GUID = "00000000-0000-0000-0000-000000000000"
USER_FIELDS = {
    "full_name": "FullName",
    "email": "EmailAddress",
    "language_pairs": "LanguagePairs",
    "disabled": "IsDisabled",
    "address": "Address",
    "phone": "PhoneNumber",
    "mobile": "MobilePhoneNumber",
}


def _hash_password(password: str) -> str:
    """Encode the password using memoQ's documented salted SHA1 protocol."""
    if not password:
        raise ValueError("Password cannot be empty")
    salt = "fgad s d f sgds g  sdg gfdg"
    return hashlib.sha1((password + salt).encode("utf-8")).hexdigest().upper()


class UserManager(WSAPIClient):
    """Create, update, delete, list and assign server users to built-in groups.

    Credential-bearing Security calls are not dumped with log_soap_debug.
    """

    def list_users(self) -> List[Dict[str, Any]]:
        """List all users, including disabled users, without password fields."""
        client = self.get_client("Security")
        users = serialize_object(client.service.ListUsers()) or []
        return [
            {key: value for key, value in user.items()
             if key not in ("Password", "PlainTextPassword")}
            for user in users
        ]

    def create_user(
        self,
        username: str,
        password: str,
        full_name: Optional[str] = None,
        email: str = "",
        language_pairs: str = "",
        disabled: bool = False,
        address: str = "",
        phone: str = "",
        mobile: str = "",
    ) -> str:
        if not username or not username.strip():
            raise ValueError("Username cannot be empty")
        password_hash = _hash_password(password)
        client = self.get_client("Security")
        user_type = client.get_type(USER_INFO_TYPE)
        info = user_type(
            UserGuid=EMPTY_GUID,
            UserName=username,
            FullName=full_name if full_name is not None else username,
            EmailAddress=email,
            LanguagePairs=language_pairs,
            IsDisabled=disabled,
            Address=address,
            PhoneNumber=phone,
            MobilePhoneNumber=mobile,
            Password=password_hash,
            IsSubvendorManager=False,
            MergeType=0,
            PackageWorkflowType="Online",
        )
        result = client.service.CreateUser(userInfo=info)
        if not result or str(result) == EMPTY_GUID:
            raise RuntimeError("CreateUser returned no user GUID")
        return str(result)

    def delete_user(self, user_guid: str) -> None:
        client = self.get_client("Security")
        client.service.DeleteUser(userGuid=user_guid)

    def update_user(self, user_guid: str, **changes) -> None:
        """Read the full UserInfo and change only explicitly supplied fields."""
        if changes.get("username") is not None:
            raise ValueError("memoQ login usernames cannot be changed; update full_name instead")
        unknown = set(changes) - set(USER_FIELDS) - {"password"}
        if unknown:
            raise ValueError(f"Unknown user fields: {', '.join(sorted(unknown))}")
        changes = {key: value for key, value in changes.items() if value is not None}
        if not changes:
            raise ValueError("Specify at least one user field to update")
        password_hash = (
            _hash_password(changes["password"]) if "password" in changes else None
        )

        client = self.get_client("Security")
        info = serialize_object(client.service.GetUser(userGuid=user_guid))
        if not info:
            raise ValueError(f"User not found: {user_guid}")
        info = dict(info)
        info["UserGuid"] = user_guid
        for field, value in changes.items():
            if field != "password":
                info[USER_FIELDS[field]] = value
        if password_hash is not None:
            info["Password"] = password_hash
            info["PlainTextPassword"] = None

        user_type = client.get_type(USER_INFO_TYPE)
        client.service.UpdateUser(userInfo=user_type(**info))

    def _add_to_group(self, user_guid: str, group_guid: str) -> None:
        """SetGroupsOfUser replaces all memberships, so merge before writing."""
        client = self.get_client("Security")
        groups = serialize_object(client.service.ListGroupsOfUser(userGuid=user_guid)) or []
        group_guids = list(dict.fromkeys(str(group["GroupGuid"]).lower() for group in groups))
        if group_guid in group_guids:
            return
        group_guids.append(group_guid)
        array_type = client.get_type(GUID_ARRAY_TYPE)
        client.service.SetGroupsOfUser(
            userGuid=user_guid,
            groupGuids=array_type(guid=group_guids),
        )

    def set_pm(self, user_guid: str) -> None:
        """Add the user to ProjectManagers, preserving other memberships."""
        self._add_to_group(user_guid, PM_GROUP_GUID)

    def set_translator(self, user_guid: str) -> None:
        """Add the user to Translators, preserving other memberships."""
        self._add_to_group(user_guid, TRANSLATOR_GROUP_GUID)
