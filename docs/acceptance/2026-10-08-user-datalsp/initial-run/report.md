# memoQ CLI user 命令实机验收报告

结论：**FAIL**，18/25 项通过。

- 开始：2026-10-08T21:29:30+08:00（Asia/Shanghai）
- 结束：2026-10-08T21:31:41+08:00（Asia/Shanghai）
- 服务器：https://memoq.datalsp.com:8081
- 实际 API 版本：12.5.20
- Security 端点：https://memoq.datalsp.com:8081/memoqservices/Security/SecurityService
- 范围：本次新增的 user add/delete/update/listusers/setpm/settm 及其参数、错误路径和清理。
- 方式：通过真实顶层 Click CLI 执行命令，无 API Mock；用独立 WSAPI 客户端 GetUser/ListUsers/ListGroupsOfUser 回读。密码通过 Security Login/Logout 校验。

| 编号 | 场景 | 结果 | 秒 |
|---|---|---|---|
| ENV01 | 真实服务器版本、端点与用户基线 | PASS | 14.247 |
| LIST01 | listusers JSON 与 API 数量一致且无密码字段 | PASS | 7.681 |
| ADD01 | 隐藏输入密码创建用户，回读全部资料 | PASS | 5.946 |
| PWD01 | 创建密码可真实登录并退出会话 | PASS | 1.647 |
| ADD02 | 重复用户名被拒绝且用户列表不变 | PASS | 8.093 |
| UPD01 | 更新用户名与全部资料，原密码仍可登录 | FAIL | 6.065 |
| UPD02 | 清空邮箱，保留其余字段及密码 | FAIL | 6.0 |
| UPD03 | 禁用用户并验证登录被拒绝 | FAIL | 6.523 |
| LIST02 | JSON 列表包含禁用用户 | PASS | 6.821 |
| LIST03 | 文本列表展示禁用用户与状态 | FAIL | 6.514 |
| UPD04 | 启用用户并验证登录恢复 | FAIL | 8.266 |
| UPD05 | 隐藏输入重置密码，新密码成功、旧密码失败 | FAIL | 7.225 |
| UPD06 | 显式参数更新密码并验证登录 | FAIL | 6.045 |
| UPD07 | 无更新字段、空密码及冲突参数均被拒绝 | PASS | 0.58 |
| PM01 | setpm 添加 PM 组并保留现有组 | PASS | 5.935 |
| PM02 | 重复 setpm 保持组成员关系不变 | PASS | 5.087 |
| TM01 | settm 添加译员组并保留 PM 等组 | PASS | 5.426 |
| TM02 | 重复 settm 保持组成员关系不变 | PASS | 5.214 |
| VAL01 | 四个按 GUID 操作的命令拒绝无效 GUID | PASS | 0.003 |
| DEL01 | 取消删除保留账号 | PASS | 0.239 |
| ADD03 | 显式密码创建禁用用户，默认姓名正确 | PASS | 3.558 |
| DEL02 | 确认删除主账号并回读列表 | PASS | 5.697 |
| DEL03 | -y 删除第二个账号并回读列表 | PASS | 3.198 |
| ERR01 | 更新已删除账号返回错误退出码 | PASS | 2.498 |
| CLEAN01 | 临时账号清理、其他账号及原配置核对 | PASS | 2.932 |

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

只创建并操作本次唯一命名的临时账号。密码及 API 密钥未写入报告，其他用户的资料仅在内存中比对。
setpm/settm 为增量加入服务器内置组；settm 保留已有 PM 权限，未测试撤销权限。
删除的验收标准为账号不再出现在 ListUsers；不代表服务器底层物理删除。
本报告不涵盖 memoQ Desktop/浏览器人工登录、项目文档分派或整套 CLI 的其他命令。

原始场景证据：cases.jsonl；结构化汇总与源码 SHA256：run.json。

## 失败详情

- UPD01: AssertionError: Profile update mismatch
- UPD02: AssertionError: Login returned an empty session
- UPD03: AssertionError: Login returned an empty session
- LIST03: AssertionError: Text list omitted disabled fixture
- UPD04: AssertionError: Login returned an empty session
- UPD05: AssertionError: Login returned an empty session
- UPD06: AssertionError: Login returned an empty session
