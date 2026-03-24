#!/usr/bin/env python3
"""通过RSAPI检查测试项目的TM/TB附加情况"""
import sys
sys.path.insert(0, ".")
from memoq_cli.config import Config
from memoq_cli.rsapi.client import RSAPIClient

config = Config()
config.load("config.json")

client = RSAPIClient(
    host=config.server_host,
    port=config.rsapi_port,
    api_path=config.get("server.rsapi_path"),
    api_key=config.api_key,
    username=config.username,
    password=config.password,
)

projects = [
    ("无metadata", "97c1898d-871c-f111-8c84-0050568df225"),
    ("仅Client", "adc1898d-871c-f111-8c84-0050568df225"),
    ("全部metadata", "05c2898d-871c-f111-8c84-0050568df225"),
]

for label, guid in projects:
    print(f"{'='*60}")
    print(f"项目: {label}")

    # 获取项目详细信息
    try:
        info = client.get(f"projects/{guid}")
        print(f"  Name: {info.get('Name')}")
        print(f"  Client: {info.get('Client')}")
        print(f"  Domain: {info.get('Domain')}")
        print(f"  Subject: {info.get('Subject')}")
        print(f"  Project: {info.get('Project')}")
    except Exception as e:
        print(f"  项目信息错误: {e}")

    # 获取项目TMs
    try:
        tms = client.get(f"projects/{guid}/translationmemories")
        if tms:
            print(f"  TM数量: {len(tms)}")
            for tm in tms:
                name = tm.get('TranslationMemoryGuid', tm.get('TMGuid', 'N/A'))
                role = tm.get('Role', 'N/A')
                master = tm.get('MasterTMGuid', 'N/A')
                print(f"    TM: {name} | Role: {role}")
        else:
            print(f"  TM数量: 0")
    except Exception as e:
        print(f"  TM错误: {e}")

    # 获取项目TBs
    try:
        tbs = client.get(f"projects/{guid}/termbases")
        if tbs:
            print(f"  TB数量: {len(tbs)}")
            for tb in tbs:
                print(f"    TB: {tb}")
        else:
            print(f"  TB数量: 0")
    except Exception as e:
        print(f"  TB错误: {e}")

    print()
