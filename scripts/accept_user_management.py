#!/usr/bin/env python3
"""Opt-in live acceptance of the six user commands on an explicitly named server.

Reads an API key from stdin, keeps it in memory, and only mutates two unique
synthetic accounts created by this run. Passwords and other users' data are
excluded from saved evidence. Run from the repository with its Python runtime.
"""

import argparse
import hashlib
import json
import secrets
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from click.testing import CliRunner
from zeep.exceptions import Fault
from zeep.helpers import serialize_object

from memoq_cli.cli import cli
from memoq_cli.config import get_config
from memoq_cli.wsapi.client import WSAPIClient
from memoq_cli.wsapi.user import PM_GROUP_GUID, TRANSLATOR_GROUP_GUID


TZ = ZoneInfo("Asia/Shanghai")
ROOT = Path(__file__).resolve().parents[1]


def now():
    return datetime.now(TZ).isoformat(timespec="seconds")


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def public_user(info):
    return {k: v for k, v in info.items() if k not in {"Password", "PlainTextPassword"}}


class Acceptance:
    def __init__(self, host, port, api_key, output):
        require(bool(api_key.strip()), "API key is required on stdin")
        self.host, self.port, self.output = host.rstrip("/"), port, output
        self.started = now()
        stamp = datetime.now(TZ).strftime("%Y%m%d%H%M%S") + secrets.token_hex(2)
        self.names = [f"cli_uat_{stamp}", f"cli_uat2_{stamp}"]
        self.renamed = self.names[0]
        self.owned = {}
        self.cases = []
        self.current = None
        self.passwords = ["Aa9!" + secrets.token_urlsafe(20) for _ in range(3)]
        self.key = api_key.strip()
        self.output.mkdir(parents=True, exist_ok=False)
        self.config = get_config()
        self.config_path = self.config._config_path
        self.config_before = self.config_path.read_bytes() if self.config_path else None
        self.saved_config = self.config._config.copy()
        # Replace complete sub-dictionaries in memory. The user's file is never saved.
        self.config._config = {
            **self.config._config,
            "server": {"host": self.host, "wsapi_port": self.port},
            "auth": {"api_key": self.key},
            "logging": {"level": "ERROR", "log_file": ""},
        }
        self.client = WSAPIClient(host=self.host, port=self.port, api_key=self.key, timeout=30)
        self.security = None
        self.baseline = None
        self.version = None
        self.cleanup = {}

    def clean(self, text):
        for value in [self.key, *self.passwords]:
            text = text.replace(value, "<redacted>")
        return text

    def run_case(self, case_id, title, function):
        self.current = {"id": case_id, "title": title, "started": now(), "commands": [], "evidence": {}}
        started = time.monotonic()
        try:
            function()
            self.current["status"] = "PASS"
        except Exception as exc:
            self.current["status"] = "FAIL"
            self.current["error"] = self.clean(f"{type(exc).__name__}: {exc}")
        self.current["duration_seconds"] = round(time.monotonic() - started, 3)
        self.cases.append(self.current)
        with (self.output / "cases.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(self.current, ensure_ascii=False, default=str) + "\n")
        print(f"{case_id} {self.current['status']} {title}", flush=True)
        self.current = None

    def evidence(self, **facts):
        self.current["evidence"].update(facts)

    def users(self):
        return [dict(item) for item in (serialize_object(self.security.service.ListUsers()) or [])]

    def user(self, guid):
        require(guid in self.owned, "Refusing to inspect a non-fixture user")
        return dict(serialize_object(self.security.service.GetUser(userGuid=guid)))

    def groups(self, guid):
        require(guid in self.owned, "Refusing to inspect a non-fixture user's groups")
        return sorted(str(item["GroupGuid"]).lower() for item in
                      (serialize_object(self.security.service.ListGroupsOfUser(userGuid=guid)) or []))

    def invoke(self, args, input_text=None, expected=0):
        if args[0] == "add":
            username = args[args.index("--username") + 1]
            require(username in self.names, "Refusing to create a non-fixture user")
        elif args[0] in {"update", "delete", "setpm", "settm"}:
            require(args[1] in self.owned or args[1] == "not-a-guid", "Refusing to mutate a non-fixture user")
        safe_args = list(args)
        if "--password" in safe_args:
            safe_args[safe_args.index("--password") + 1] = "<redacted>"
        result = CliRunner().invoke(cli, ["--quiet", "user", *args], input=input_text)
        command = {"argv": ["memoq", "--quiet", "user", *safe_args], "exit_code": result.exit_code}
        if args[0] != "listusers":
            command["output"] = self.clean(result.output.strip())
        else:
            command["output_sha256"] = hashlib.sha256(result.output.encode()).hexdigest()
        if self.current:
            self.current["commands"].append(command)
        require(result.exit_code == expected,
                f"CLI exit {result.exit_code}, expected {expected}: {self.clean(result.output[:800])}")
        return result

    def login(self, username, password, expected=True):
        # Compute the documented wire hash independently of UserManager.
        password_hash = hashlib.sha1((password + "fgad s d f sgds g  sdg gfdg").encode()).hexdigest().upper()
        session = None
        try:
            session = self.security.service.Login(userName=username, passwordHash=password_hash)
        except Fault as exc:
            require(not expected, f"Valid credentials were rejected: {exc}")
            return False
        if not session:
            require(not expected, "Valid credentials returned an empty session")
            return False
        try:
            require(expected, "Credentials expected to be rejected were accepted")
            return True
        finally:
            self.security.service.Logout(sessionId=session)

    def create(self, secondary=False):
        name = self.names[1 if secondary else 0]
        args = ["add", "--username", name, "--json"]
        expected = {"UserName": name, "IsDisabled": secondary}
        if secondary:
            args += ["--password", self.passwords[0], "--disabled"]
            expected["FullName"] = name
            input_text = None
        else:
            profile = {"FullName": "CLI 用户管理验收", "EmailAddress": "cli-uat@example.invalid",
                       "LanguagePairs": "eng#zho-CN;eng#ger", "Address": "Acceptance address",
                       "PhoneNumber": "000-0000", "MobilePhoneNumber": "000-0001"}
            for flag, field in [("--full-name", "FullName"), ("--email", "EmailAddress"),
                                ("--language-pairs", "LanguagePairs"), ("--address", "Address"),
                                ("--phone", "PhoneNumber"), ("--mobile", "MobilePhoneNumber")]:
                args += [flag, profile[field]]
            expected.update(profile)
            input_text = self.passwords[0] + "\n" + self.passwords[0] + "\n"
        result = self.invoke(args, input_text=input_text)
        data = json.loads(result.output[result.output.index("{"):])
        guid = str(data["UserGuid"])
        self.owned[guid] = name
        if secondary:
            self.secondary = guid
        else:
            self.primary = guid
        require(guid not in self.baseline, "Create returned a pre-existing GUID")
        actual = self.user(guid)
        for field, value in expected.items():
            require(actual[field] == value, f"Created field {field} did not match")
        require(all(pw not in result.output for pw in self.passwords), "Password leaked in CLI output")
        self.evidence(user=public_user(actual), groups=self.groups(guid), password_hidden=True)

    def preflight(self):
        self.version = str(self.client.get_client("ServerProject").service.GetApiVersion())
        self.security = self.client.get_client("Security")
        endpoint = self.security.service._binding_options["address"]
        require(endpoint.startswith(f"{self.host}:{self.port}/"), "WSDL advertised a different server")
        self.endpoint = endpoint
        self.baseline = {str(item["UserGuid"]): public_user(item) for item in self.users()}
        require(not any(item.get("UserName") in self.names + [self.renamed]
                        for item in self.baseline.values()), "Fixture name collision")
        self.evidence(api_version=self.version, security_endpoint=endpoint, existing_user_count=len(self.baseline))

    def list_json(self):
        data = json.loads(self.invoke(["listusers", "--json"]).output)
        require(len(data) == len(self.users()), "List count differs from Security API")
        require(all("Password" not in item and "PlainTextPassword" not in item for item in data),
                "List exposed credential fields")
        fixture = [item for item in data if str(item["UserGuid"]) in self.owned]
        self.evidence(total_count=len(data), fixture_users=fixture, credential_fields_absent=True)

    def duplicate(self):
        before = {str(item["UserGuid"]) for item in self.users()}
        self.invoke(["add", "--username", self.names[0], "--password", self.passwords[0], "--json"], expected=1)
        require(before == {str(item["UserGuid"]) for item in self.users()}, "Duplicate attempt changed user list")
        self.evidence(user_list_unchanged=True)

    def update_profile(self):
        args = ["update", self.primary, "--full-name", "CLI 验收更新",
                "--email", "updated@example.invalid", "--language-pairs", "zho-CN#eng",
                "--address", "Updated address", "--phone", "000-0002", "--mobile", "000-0003", "--json"]
        self.invoke(args)
        actual = self.user(self.primary)
        expected = {"UserName": self.renamed, "FullName": "CLI 验收更新", "EmailAddress": "updated@example.invalid",
                    "LanguagePairs": "zho-CN#eng", "Address": "Updated address", "PhoneNumber": "000-0002",
                    "MobilePhoneNumber": "000-0003"}
        self.evidence(user=public_user(actual), expected_profile=expected)
        require(all(actual[key] == value for key, value in expected.items()), "Profile update mismatch")
        self.login(self.renamed, self.passwords[0])
        self.evidence(user=public_user(actual), original_password_login=True)

    def clear_email(self):
        before = self.user(self.primary)
        self.invoke(["update", self.primary, "--email", ""])
        after = self.user(self.primary)
        require(after["EmailAddress"] in ("", None), "Email was not cleared")
        require({k: v for k, v in before.items() if k != "EmailAddress"} ==
                {k: v for k, v in after.items() if k != "EmailAddress"}, "Unspecified fields changed")
        self.login(self.renamed, self.passwords[0])
        self.evidence(email_cleared=True, other_fields_unchanged=True, original_password_login=True)

    def set_enabled(self, enabled):
        self.invoke(["update", self.primary, "--enabled" if enabled else "--disabled", "--json"])
        require(self.user(self.primary)["IsDisabled"] is not enabled, "Disabled flag mismatch")
        self.login(self.renamed, self.passwords[0], expected=enabled)
        self.evidence(is_disabled=not enabled, login_accepted=enabled)

    def list_disabled(self):
        data = json.loads(self.invoke(["listusers", "--json"]).output)
        require(any(str(item["UserGuid"]) == self.primary and item["IsDisabled"] for item in data),
                "Disabled fixture was omitted")
        self.evidence(disabled_fixture_included=True)

    def list_text(self):
        result = self.invoke(["listusers"])
        fixture_line = next((line for line in result.output.splitlines() if self.primary in line), "")
        require(self.renamed in fixture_line and "disabled" in fixture_line, "Text list omitted disabled fixture")
        self.evidence(fixture_line=fixture_line)

    def reset_password(self, prompt):
        before = self.user(self.primary)
        index = 1 if prompt else 2
        old_index = 0 if prompt else 1
        args = ["update", self.primary, "--reset-password"] if prompt else [
            "update", self.primary, "--password", self.passwords[index], "--json"]
        input_text = self.passwords[index] + "\n" + self.passwords[index] + "\n" if prompt else None
        self.invoke(args, input_text=input_text)
        self.login(self.renamed, self.passwords[index])
        self.login(self.renamed, self.passwords[old_index], expected=False)
        after = self.user(self.primary)
        require(public_user(before) == public_user(after), "Password change altered profile")
        self.evidence(new_password_login=True, old_password_rejected=True, profile_unchanged=True)

    def role(self, command, target, repeat=False):
        before = self.groups(self.primary)
        self.invoke([command, self.primary, *( [] if command == "settm" and not repeat else ["--json"] )])
        after = self.groups(self.primary)
        require(target in after, "Target role group missing")
        require(set(before).issubset(after), "Existing group membership was lost")
        if repeat:
            require(before == after, "Repeated role assignment changed groups")
        self.evidence(groups_before=before, groups_after=after, existing_groups_preserved=True, repeat=repeat)

    def invalid_update(self):
        before = self.user(self.primary)
        self.invoke(["update", self.primary], expected=2)
        self.invoke(["update", self.primary, "--password", ""], expected=2)
        self.invoke(["update", self.primary, "--password", self.passwords[2], "--reset-password"], expected=2)
        require(self.user(self.primary) == before, "Invalid update changed the user")
        self.evidence(state_unchanged=True)

    def invalid_guids(self):
        for command in ["update", "delete", "setpm", "settm"]:
            self.invoke([command, "not-a-guid"], expected=2)
        self.evidence(invalid_guid_exit_code=2)

    def unsupported_rename(self):
        before = self.user(self.primary)
        self.invoke(["update", self.primary, "--username", self.names[0] + "r"], expected=2)
        require(self.user(self.primary) == before, "Unsupported rename changed the user")
        self.evidence(rename_option_rejected=True, state_unchanged=True)

    def cancelled_delete(self):
        before = self.user(self.primary)
        self.invoke(["delete", self.primary], input_text="n\n", expected=1)
        require(self.user(self.primary) == before, "Cancelled delete altered the user")
        self.evidence(user_retained=True)

    def delete(self, guid, confirmed):
        args = ["delete", guid, "--json"] + ([] if confirmed else ["-y"])
        self.invoke(args, input_text="y\n" if confirmed else None)
        require(not any(str(item["UserGuid"]) == guid for item in self.users()), "Deleted user still listed")
        self.evidence(user_guid=guid, absent_from_list=True)

    def missing_update(self):
        self.invoke(["update", self.primary, "--full-name", "deleted-user", "--json"], expected=1)
        self.evidence(deleted_user_update_rejected=True)

    def clean_up(self):
        # Recover a fixture if creation succeeded but its response was interrupted.
        for item in self.users():
            if item.get("UserName") in self.names + [self.renamed]:
                guid = str(item["UserGuid"])
                require(guid not in self.baseline, "Refusing to clean up a baseline user")
                self.owned[guid] = item["UserName"]
        remaining = {str(item["UserGuid"]) for item in self.users()} & set(self.owned)
        for guid in remaining:
            self.invoke(["delete", guid, "-y", "--json"])
        final = {str(item["UserGuid"]): public_user(item) for item in self.users()}
        changed = [guid for guid, item in self.baseline.items() if final.get(guid) != item]
        unexpected = set(final) - set(self.baseline)
        leftovers = set(final) & set(self.owned)
        self.cleanup = {"fixture_count": len(self.owned), "remaining_fixture_count": len(leftovers),
                        "baseline_user_count": len(self.baseline), "final_user_count": len(final),
                        "changed_or_missing_baseline_count": len(changed), "unexpected_new_user_count": len(unexpected),
                        "config_file_unchanged": not self.config_path or self.config_path.read_bytes() == self.config_before}
        self.evidence(**self.cleanup)
        require(not leftovers, "Fixture accounts remain")
        require(not changed and not unexpected, "Other users changed during acceptance; investigate concurrency")
        require(self.cleanup["config_file_unchanged"], "User's configuration file changed")

    def run(self):
        self.run_case("ENV01", "真实服务器版本、端点与用户基线", self.preflight)
        try:
            require(self.baseline is not None, "Preflight did not complete")
            self.run_case("LIST01", "listusers JSON 与 API 数量一致且无密码字段", self.list_json)
            self.run_case("ADD01", "隐藏输入密码创建用户，回读全部资料", self.create)
            require(hasattr(self, "primary"), "Primary fixture creation failed")
            self.run_case("PWD01", "创建密码可真实登录并退出会话",
                          lambda: self.evidence(login=self.login(self.names[0], self.passwords[0])))
            self.run_case("ADD02", "重复用户名被拒绝且用户列表不变", self.duplicate)
            self.run_case("UPD01", "更新全部资料，用户名与原密码保留", self.update_profile)
            self.run_case("UPD02", "清空邮箱，保留其余字段及密码", self.clear_email)
            self.run_case("UPD03", "禁用用户并验证登录被拒绝", lambda: self.set_enabled(False))
            self.run_case("LIST02", "JSON 列表包含禁用用户", self.list_disabled)
            self.run_case("LIST03", "文本列表展示禁用用户与状态", self.list_text)
            self.run_case("UPD04", "启用用户并验证登录恢复", lambda: self.set_enabled(True))
            self.run_case("UPD05", "隐藏输入重置密码，新密码成功、旧密码失败", lambda: self.reset_password(True))
            self.run_case("UPD06", "显式参数更新密码并验证登录", lambda: self.reset_password(False))
            self.run_case("UPD07", "无更新字段、空密码及冲突参数均被拒绝", self.invalid_update)
            self.run_case("UPD08", "不支持的用户名改名选项被拒绝且资料不变", self.unsupported_rename)
            self.run_case("PM01", "setpm 添加 PM 组并保留现有组", lambda: self.role("setpm", PM_GROUP_GUID))
            self.run_case("PM02", "重复 setpm 保持组成员关系不变", lambda: self.role("setpm", PM_GROUP_GUID, True))
            self.run_case("TM01", "settm 添加译员组并保留 PM 等组", lambda: self.role("settm", TRANSLATOR_GROUP_GUID))
            self.run_case("TM02", "重复 settm 保持组成员关系不变", lambda: self.role("settm", TRANSLATOR_GROUP_GUID, True))
            self.run_case("VAL01", "四个按 GUID 操作的命令拒绝无效 GUID", self.invalid_guids)
            self.run_case("DEL01", "取消删除保留账号", self.cancelled_delete)
            self.run_case("ADD03", "显式密码创建禁用用户，默认姓名正确", lambda: self.create(True))
            self.run_case("DEL02", "确认删除主账号并回读列表", lambda: self.delete(self.primary, True))
            if hasattr(self, "secondary"):
                self.run_case("DEL03", "-y 删除第二个账号并回读列表", lambda: self.delete(self.secondary, False))
            self.run_case("ERR01", "更新已删除账号返回错误退出码", self.missing_update)
        except Exception as exc:
            self.run_case("RUN_ERROR", "验收前置条件失败", lambda: require(False, self.clean(str(exc))))
        finally:
            if self.baseline is not None:
                self.run_case("CLEAN01", "临时账号清理、其他账号及原配置核对", self.clean_up)
            self.client.close()
            self.config._config = self.saved_config
        status = "PASS" if len(self.cases) == 26 and all(c["status"] == "PASS" for c in self.cases) else "FAIL"
        files = ["memoq_cli/commands/user.py", "memoq_cli/wsapi/user.py", "memoq_cli/cli.py",
                 "memoq_cli/commands/__init__.py", "scripts/accept_user_management.py"]
        summary = {"status": status, "started": self.started, "ended": now(),
                   "host": self.host, "port": self.port, "api_version": self.version,
                   "security_endpoint": getattr(self, "endpoint", None),
                   "passed": sum(c["status"] == "PASS" for c in self.cases), "total": len(self.cases),
                   "fixtures": self.owned, "cleanup": self.cleanup,
                   "source_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files},
                   "cases": self.cases}
        (self.output / "run.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str) + "\n")
        rows = [f"| {c['id']} | {c['title']} | {c['status']} | {c['duration_seconds']} |" for c in self.cases]
        report = f"""# memoQ CLI user 命令实机验收报告

结论：**{status}**，{summary['passed']}/{summary['total']} 项通过。

- 开始：{self.started}（Asia/Shanghai）
- 结束：{summary['ended']}（Asia/Shanghai）
- 服务器：{self.host}:{self.port}
- 实际 API 版本：{self.version}
- Security 端点：{summary['security_endpoint']}
- 范围：本次新增的 user add/delete/update/listusers/setpm/settm 及其参数、错误路径和清理。
- 方式：通过真实顶层 Click CLI 执行命令，无 API Mock；用独立 WSAPI 客户端 GetUser/ListUsers/ListGroupsOfUser 回读。密码通过 Security Login/Logout 校验。

| 编号 | 场景 | 结果 | 秒 |
|---|---|---|---|
{chr(10).join(rows)}

## 清理与影响核对

```json
{json.dumps(self.cleanup, ensure_ascii=False, indent=2)}
```

只创建并操作本次唯一命名的临时账号。密码及 API 密钥未写入报告，其他用户的资料仅在内存中比对。
setpm/settm 为增量加入服务器内置组；settm 保留已有 PM 权限，未测试撤销权限。
删除的验收标准为账号不再出现在 ListUsers；不代表服务器底层物理删除。
本报告不涵盖 memoQ Desktop/浏览器人工登录、项目文档分派或整套 CLI 的其他命令。
memoQ 登录用户名不可修改；update 更新资料、密码和启用状态，--username 仅用于 add。

原始场景证据：cases.jsonl；结构化汇总与源码 SHA256：run.json。
"""
        failures = [c for c in self.cases if c["status"] != "PASS"]
        if failures:
            report += "\n## 失败详情\n\n" + "\n".join(f"- {c['id']}: {c.get('error', '未完成')}" for c in failures) + "\n"
        (self.output / "report.md").write_text(report, encoding="utf-8")
        print(json.dumps({key: summary[key] for key in ["status", "passed", "total", "api_version", "cleanup"]}, ensure_ascii=False), flush=True)
        return 0 if status == "PASS" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True, help="Explicit target server, including https://")
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--output", required=True, type=Path, help="New evidence directory")
    args = parser.parse_args()
    require(args.host.startswith("https://"), "Acceptance requires an HTTPS server")
    warnings.filterwarnings("ignore", message="Unverified HTTPS request")
    run = Acceptance(args.host, args.port, sys.stdin.read(), args.output)
    return run.run()


if __name__ == "__main__":
    raise SystemExit(main())
