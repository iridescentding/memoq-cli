#!/usr/bin/env python3
"""测试模板创建项目时metadata是否必填"""
import sys
import json
import time
sys.path.insert(0, ".")

from memoq_cli.config import Config
from memoq_cli.wsapi.project import ProjectManager
from memoq_cli.wsapi.project_template import ProjectTemplateManager

config = Config()
config.load("config.json")

TEMPLATE_GUID = "814e5e47-e96c-4b09-b038-316736b8f40a"
# 从模板信息获取的creator user
CREATOR_USER = "3eae8152-a9d4-f011-b521-9c65eba8f196"  # 贾利云-管理员

pm = ProjectManager(
    host=config.server_host,
    port=config.wsapi_port,
    api_key=config.api_key,
)

tmpl_mgr = ProjectTemplateManager(
    host=config.server_host,
    port=config.wsapi_port,
    api_key=config.api_key,
)

# 先获取模板信息
print("=" * 60)
print("模板信息:")
tmpl = tmpl_mgr.get_template(TEMPLATE_GUID)
print(f"  Name: {tmpl.get('Name')}")
print(f"  SourceLangCode: {tmpl.get('SourceLangCode')}")
targets = tmpl.get('TargetLangCodes', {})
if isinstance(targets, dict):
    target_list = targets.get('string', [])
else:
    target_list = targets if isinstance(targets, list) else []
print(f"  TargetLangCodes: {target_list}")
print()

# 定义测试用例
test_cases = [
    {
        "name": "测试1: 无metadata (仅必需字段)",
        "kwargs": {
            "template_guid": TEMPLATE_GUID,
            "name": f"TEST-无metadata-{int(time.time())}",
            "creator_user": CREATOR_USER,
        }
    },
    {
        "name": "测试2: 仅Client",
        "kwargs": {
            "template_guid": TEMPLATE_GUID,
            "name": f"TEST-仅Client-{int(time.time())}",
            "creator_user": CREATOR_USER,
            "client_attr": "TestClient",
        }
    },
    {
        "name": "测试3: 仅Domain",
        "kwargs": {
            "template_guid": TEMPLATE_GUID,
            "name": f"TEST-仅Domain-{int(time.time())}",
            "creator_user": CREATOR_USER,
            "domain": "TestDomain",
        }
    },
    {
        "name": "测试4: 仅Subject",
        "kwargs": {
            "template_guid": TEMPLATE_GUID,
            "name": f"TEST-仅Subject-{int(time.time())}",
            "creator_user": CREATOR_USER,
            "subject": "TestSubject",
        }
    },
    {
        "name": "测试5: 仅Project",
        "kwargs": {
            "template_guid": TEMPLATE_GUID,
            "name": f"TEST-仅Project-{int(time.time())}",
            "creator_user": CREATOR_USER,
            "project_attr": "TestProject",
        }
    },
    {
        "name": "测试6: 全部metadata",
        "kwargs": {
            "template_guid": TEMPLATE_GUID,
            "name": f"TEST-全部metadata-{int(time.time())}",
            "creator_user": CREATOR_USER,
            "client_attr": "TestClient",
            "domain": "TestDomain",
            "subject": "TestSubject",
            "project_attr": "TestProject",
            "description": "测试描述",
        }
    },
]

created_projects = []

for tc in test_cases:
    print("=" * 60)
    print(f"{tc['name']}")
    print(f"  参数: { {k:v for k,v in tc['kwargs'].items() if k != 'template_guid'} }")
    try:
        result = pm.create_project_from_template(**tc['kwargs'])
        status = result.get("ResultStatus")
        project_guid = result.get("ProjectGuid")
        print(f"  结果: {status}")
        print(f"  ProjectGuid: {project_guid}")
        if project_guid:
            created_projects.append(project_guid)

        # 如果创建成功，获取项目详情看看metadata
        if status == "Success" and project_guid:
            info = pm.get_project_info(project_guid)
            print(f"  项目名称: {info.get('Name')}")
            print(f"  Client: {info.get('Client', 'N/A')}")
            print(f"  Domain: {info.get('Domain', 'N/A')}")
            print(f"  Subject: {info.get('Subject', 'N/A')}")
            print(f"  Project: {info.get('Project', 'N/A')}")
            print(f"  Description: {info.get('Description', 'N/A')}")
    except Exception as e:
        print(f"  错误: {e}")
    print()

print("=" * 60)
print(f"共创建 {len(created_projects)} 个测试项目:")
for guid in created_projects:
    print(f"  {guid}")
print("\n注意: 请手动删除这些测试项目!")
