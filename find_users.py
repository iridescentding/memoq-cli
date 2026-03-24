#!/usr/bin/env python3
"""查找可用的用户"""
import sys
sys.path.insert(0, ".")
from memoq_cli.config import Config
from memoq_cli.wsapi.client import WSAPIClient

config = Config()
config.load("config.json")

client = WSAPIClient(
    host=config.server_host,
    port=config.wsapi_port,
    api_key=config.api_key,
)
soap_client = client.get_client("Security")
users = soap_client.service.ListUsers()

if users:
    for u in users:
        if not u.IsDisabled:
            print(f"  UserGuid: {u.UserGuid}  UserName: {u.UserName}  FullName: {u.FullName}  IsDisabled: {u.IsDisabled}")
