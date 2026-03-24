#!/usr/bin/env python3
"""用WSAPI查看TM/TB"""
import sys
sys.path.insert(0, ".")
from memoq_cli.config import Config
from memoq_cli.wsapi.client import WSAPIClient
from zeep.helpers import serialize_object

config = Config()
config.load("config.json")

client = WSAPIClient(
    host=config.server_host,
    port=config.wsapi_port,
    api_key=config.api_key,
)

# 先看ServerProject service有哪些操作
sp = client.get_client("ServerProject")
print("ServerProject operations:")
for op in sorted(sp.service._binding._operations.keys()):
    if 'tm' in op.lower() or 'tb' in op.lower() or 'term' in op.lower() or 'memory' in op.lower() or 'resource' in op.lower():
        print(f"  {op}")

print("\n所有操作:")
for op in sorted(sp.service._binding._operations.keys()):
    print(f"  {op}")
