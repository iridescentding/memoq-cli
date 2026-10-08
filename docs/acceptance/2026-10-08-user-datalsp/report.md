# memoQ CLI user 命令实机验收报告

结论：**PASS**，26/26 项通过。

- 开始：2026-10-08T21:36:40+08:00（Asia/Shanghai）
- 结束：2026-10-08T21:38:20+08:00（Asia/Shanghai）
- 服务器：https://memoq.datalsp.com:8081
- 实际 API 版本：12.5.20
- Security 端点：https://memoq.datalsp.com:8081/memoqservices/Security/SecurityService
- 范围：本次新增的 user add/delete/update/listusers/setpm/settm 及其参数、错误路径和清理。
- 方式：通过真实顶层 Click CLI 执行命令，无 API Mock；用独立 WSAPI 客户端 GetUser/ListUsers/ListGroupsOfUser 回读。密码通过 Security Login/Logout 校验。

| 编号 | 场景 | 结果 | 秒 |
|---|---|---|---|
| ENV01 | 真实服务器版本、端点与用户基线 | PASS | 7.853 |
| LIST01 | listusers JSON 与 API 数量一致且无密码字段 | PASS | 3.912 |
| ADD01 | 隐藏输入密码创建用户，回读全部资料 | PASS | 3.974 |
| PWD01 | 创建密码可真实登录并退出会话 | PASS | 0.531 |
| ADD02 | 重复用户名被拒绝且用户列表不变 | PASS | 4.164 |
| UPD01 | 更新全部资料，用户名与原密码保留 | PASS | 8.031 |
| UPD02 | 清空邮箱，保留其余字段及密码 | PASS | 3.219 |
| UPD03 | 禁用用户并验证登录被拒绝 | PASS | 4.795 |
| LIST02 | JSON 列表包含禁用用户 | PASS | 3.408 |
| LIST03 | 文本列表展示禁用用户与状态 | PASS | 4.521 |
| UPD04 | 启用用户并验证登录恢复 | PASS | 4.036 |
| UPD05 | 隐藏输入重置密码，新密码成功、旧密码失败 | PASS | 4.477 |
| UPD06 | 显式参数更新密码并验证登录 | PASS | 5.389 |
| UPD07 | 无更新字段、空密码及冲突参数均被拒绝 | PASS | 1.0 |
| UPD08 | 不支持的用户名改名选项被拒绝且资料不变 | PASS | 0.25 |
| PM01 | setpm 添加 PM 组并保留现有组 | PASS | 5.54 |
| PM02 | 重复 setpm 保持组成员关系不变 | PASS | 3.704 |
| TM01 | settm 添加译员组并保留 PM 等组 | PASS | 3.529 |
| TM02 | 重复 settm 保持组成员关系不变 | PASS | 2.858 |
| VAL01 | 四个按 GUID 操作的命令拒绝无效 GUID | PASS | 0.006 |
| DEL01 | 取消删除保留账号 | PASS | 0.849 |
| ADD03 | 显式密码创建禁用用户，默认姓名正确 | PASS | 3.993 |
| DEL02 | 确认删除主账号并回读列表 | PASS | 5.777 |
| DEL03 | -y 删除第二个账号并回读列表 | PASS | 5.918 |
| ERR01 | 更新已删除账号返回错误退出码 | PASS | 5.772 |
| CLEAN01 | 临时账号清理、其他账号及原配置核对 | PASS | 2.09 |

## 本地回归

待上传的 origin/main 隔离分支执行 `python -m pytest -m "not integration" -q`：**105 passed, 1 deselected**。真实服务器集成场景由本报告的 26 项实机用例覆盖。运行版本和基础提交见 [regression.json](regression.json)。

## 清理与影响核对

```json
{
  "fixture_count": 2,
  "remaining_fixture_count": 0,
  "baseline_user_count": 133,
  "final_user_count": 133,
  "changed_or_missing_baseline_count": 0,
  "unexpected_new_user_count": 0,
  "config_file_unchanged": true
}
```

只创建并操作本次唯一命名的临时账号。密码及 API 密钥未写入报告，其他用户的资料仅在内存中比对。基线核对范围为用户 GUID 集合及不含密码的 UserInfo 资料字段。
setpm/settm 为增量加入服务器内置组；settm 保留已有 PM 权限，未测试撤销权限。
删除的验收标准为账号不再出现在 ListUsers；不代表服务器底层物理删除。
本报告不涵盖 memoQ Desktop/浏览器人工登录、项目文档分派或整套 CLI 的其他命令。
memoQ 登录用户名不可修改；update 更新资料、密码和启用状态，--username 仅用于 add。

原始场景证据：cases.jsonl；结构化汇总与源码 SHA256：run.json。

## 首轮失败与修正

首轮 25 项中 18 项通过，原始结果保留在 [initial-run/report.md](initial-run/report.md)。当时误将登录用户名改名当成可支持功能，UpdateUser 返回成功却保留原用户名，导致依赖新用户名的登录和列表用例连带失败。

[单独诊断证据](initial-run/update-diagnostic.json)对比了真实发送字段与回读字段：FullName、EmailAddress 正常变化，UserName 不变；诊断账号已删除。该行为与 [memoQ 官方说明](https://docs.memoq.com/11-1/en/memoQWeb-help/mqw-add_edit-user.html)一致。现已移除 update 的 --username 选项，并在 WSAPI 管理层拒绝改名，避免其他资料先被部分更新后再报错。

另外，datalsp 对错误密码和禁用账号的 Security Login 会返回空会话，首轮验收脚本只接受 SOAP Fault 作为拒绝登录证据。现已同时识别空会话和 SOAP Fault。二轮在待上传源码上重新跑完整流程，26 项全部通过。密码验证为 Security API 登录，未声称完成 Desktop 或浏览器人工登录。

## 证据文件

- [cases.jsonl](cases.jsonl)：逐场景命令、退出码、回读与耗时。
- [run.json](run.json)：整体结果、临时账号 GUID、清理结果和源码 SHA256。
- [regression.json](regression.json)：本地回归结果、依赖版本和基础提交。
- [initial-run/](initial-run/)：首轮失败和单独诊断，均不包含实际凭据。

报告对应未提交的功能源码，由 run.json 中的源码 SHA256 精确标识；提交后的相同文件保持这些哈希。
