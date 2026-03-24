#!/usr/bin/env python3
"""检查测试项目的TM/TB附加情况"""
import sys
sys.path.insert(0, ".")
from memoq_cli.config import Config
from memoq_cli.wsapi.project import ProjectManager

config = Config()
config.load("config.json")

pm = ProjectManager(
    host=config.server_host,
    port=config.wsapi_port,
    api_key=config.api_key,
)

projects = [
    ("无metadata", "97c1898d-871c-f111-8c84-0050568df225"),
    ("仅Client", "adc1898d-871c-f111-8c84-0050568df225"),
    ("仅Domain", "c3c1898d-871c-f111-8c84-0050568df225"),
    ("仅Subject", "d9c1898d-871c-f111-8c84-0050568df225"),
    ("仅Project", "efc1898d-871c-f111-8c84-0050568df225"),
    ("全部metadata", "05c2898d-871c-f111-8c84-0050568df225"),
]

soap_client = pm.get_client("ServerProject")

for label, guid in projects:
    print(f"{'='*60}")
    print(f"项目: {label} ({guid})")

    info = pm.get_project_info(guid)
    print(f"  Name: {info.get('Name')}")
    print(f"  Client: {info.get('Client')}")
    print(f"  Domain: {info.get('Domain')}")
    print(f"  Subject: {info.get('Subject')}")
    print(f"  Project: {info.get('Project')}")

    # 获取项目TM列表
    try:
        tms = soap_client.service.ListProjectTranslationMemories(serverProjectGuid=guid)
        if tms:
            print(f"  TM数量: {len(tms)}")
            for tm in tms:
                print(f"    - {tm.TMGuid} | {getattr(tm, 'TMName', 'N/A')} | Role: {getattr(tm, 'TMRole', 'N/A')}")
        else:
            print(f"  TM数量: 0")
    except Exception as e:
        print(f"  TM查询错误: {e}")

    # 获取项目TB列表
    try:
        tbs = soap_client.service.ListProjectTermBases(serverProjectGuid=guid)
        if tbs:
            print(f"  TB数量: {len(tbs)}")
            for tb in tbs:
                print(f"    - {tb.TBGuid} | {getattr(tb, 'TBName', 'N/A')}")
        else:
            print(f"  TB数量: 0")
    except Exception as e:
        print(f"  TB查询错误: {e}")

    print()
