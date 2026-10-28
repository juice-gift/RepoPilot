# V5 远程发布集中审批方案

状态：待 Owner 单独批准；本文件不是授权，也不是 V5 Completion Report。

目标仅限私有仓库 `juice-gift/repopilot-v5-sandbox`，GitHub 仓库 ID `1436602856`。
两份独立修复均以远程 main `b4279c8b4d862817e6778caa5f87da91d29ed2b7` 为唯一父提交，
对应已保存的 Snapshot 414。两条分支互不包含另一项修复。

申请的完整操作：为下列每份精确方案创建 Git tree 和 commit、创建一条新的独立分支，
并经官方 GitHub MCP Server 创建一个指向 main 的 **Draft PR**。
仅允许按同一方案核对并补做缺失步骤，以及重复调用验证幂等性。
不得更新/覆盖已有分支、改写 main、修改 Issue、请求额外 reviewer、合并或清理远程对象。
Issue #3 的歧义用例保持零修改，不创建修复 PR。

Git tree/commit/ref 使用固定 Git Data API，因为官方 MCP create_branch/push_files 缺少
expected-parent SHA 参数；PR 的创建、发现及读取使用真实 MCP。无新依赖。
Token 只从本地忽略的 .env 读取，不进入命令参数、模型、Sandbox、报告或 Git。
批准后仅对这两份 digest 调用产品审批/发布流程，临时授予该仓库的写 allowlist；
验证结束恢复空写 allowlist。不会对 RepoPilot 源码仓库执行任何远程写入。

## Issue #1 — fee-days

- Proposal：`ac87b554e57e4a9181116fb36cf66811`
- 审批 SHA256：`a9226eacdab8fc949a604f291f4d63c4022f4cab75f3a70b8b9d76828cc4161b`
- 分支：`codex/issue-1-ac87b554e57e4a9181116fb36cf66811`
- Commit：`1abc169665e9a6b6d6e56a2e096f251eefe46bd2`
- Tree：`d536b419d771851c609625cef7e595f2ce8ca80c`
- 唯一父提交：`b4279c8b4d862817e6778caa5f87da91d29ed2b7`
- 已保存结果 SHA256：`14c79da3dfdd5a26c92b176f49a376961f1bdc9d9eb519350c8a98bac7f443dc`
- 独立 Docker 测试：修复后 8 项通过，revision 1；原始基线存在预期失败。
- PR 标题：Fix issue #1: fee-days
- PR 状态：Draft；maintainer_can_modify 请求值为 false；不合并。

Diff 展示（原始可应用补丁保存在机器可读方案中）：

```diff
--- a/fees.py
+++ b/fees.py
@@ -4,4 +4,4 @@
 def late_fee(balance_cents: int, overdue_days: int) -> int:
     if balance_cents < 0 or overdue_days < 0:
         raise ValueError("Values must be nonnegative")
-    return balance_cents * min(max(overdue_days - 1, 0), 30) // 100
+    return balance_cents * min(max(overdue_days, 0), 30) // 100
```

PR 正文：

```text
Controlled repair for #1.

Base: `b4279c8b4d862817e6778caa5f87da91d29ed2b7`
Snapshot: `414`
Result: `14c79da3dfdd5a26c92b176f49a376961f1bdc9d9eb519350c8a98bac7f443dc`
Independent tests: 8 passed at revision 1.

RepoPilot-Proposal: ac87b554e57e4a9181116fb36cf66811

Human review required. No merge is authorized.
```

## Issue #2 — dispatch-preconditions

- Proposal：`c37153f84a904aa09cb1228f30f7f298`
- 审批 SHA256：`f382eda4a3d97a97693868c9135e5f083fd505e7a27e4e4c897b8da46309cce0`
- 分支：`codex/issue-2-c37153f84a904aa09cb1228f30f7f298`
- Commit：`114a173431c0ff68f1368615096c24284a5af25d`
- Tree：`55162c85dab76096402500d1d091725993830586`
- 唯一父提交：`b4279c8b4d862817e6778caa5f87da91d29ed2b7`
- 已保存结果 SHA256：`16d3b8ab11d65a869421e948572400899e921bbe097f2dcac2ad6f2d4ac77546`
- 独立 Docker 测试：修复后 11 项通过，revision 1；原始基线存在预期失败。
- PR 标题：Fix issue #2: dispatch-preconditions
- PR 状态：Draft；maintainer_can_modify 请求值为 false；不合并。

Diff 展示（原始可应用补丁保存在机器可读方案中）：

```diff
--- a/workflow.py
+++ b/workflow.py
@@ -3,8 +3,10 @@


 def submit_job(token: str, attempt: int, transient: bool) -> dict:
+    verify_token(token)
+    if not transient and attempt < 0:
+        raise ValueError("Attempt must be nonnegative")
     delay = retry_delay(attempt, transient)
-    verify_token(token)
     if delay is None:
         return {"status": "rejected"}
     return {"status": "scheduled", "delay": delay}
```

PR 正文：

```text
Controlled repair for #2.

Base: `b4279c8b4d862817e6778caa5f87da91d29ed2b7`
Snapshot: `414`
Result: `16d3b8ab11d65a869421e948572400899e921bbe097f2dcac2ad6f2d4ac77546`
Independent tests: 11 passed at revision 1.

RepoPilot-Proposal: c37153f84a904aa09cb1228f30f7f298

Human review required. No merge is authorized.
```

## 已核验与具体风险

本次最终发布前验证：真实 PostgreSQL / Docker / 官方 MCP 全量测试 **329 passed，零跳过**；
Ruff、Alembic 0008 迁移和 drift 检查、TypeScript / Vite 生产构建均通过。
V1–V4 冻结回归保持原结果；安全与范围审查见
[发布前审查](../evaluation/v5-prepublication-security-review.md)。

真实 Qwen 决策和独立 Docker 测试的完整记录见
[修复结果](../evaluation/v5-bound-qwen-resolution.json)及[补丁自审](../evaluation/v5-bound-qwen-reviews.json)。
发布前真实 MCP 读取、工具 schema digest、Git API 只读基线核验和完整方案见
[机器可读方案](../evaluation/v5-publication-proposals.json)。
基线 tree 为 `24256b0719543d6711d4b5c019b9297a1859e3ac`，五个文件的字节、路径、
Git mode 和三个原始 Issue 契约已验证；两条目标分支不存在，未发现对应 PR。
独立测试文件继续留在 RepoPilot，不上传测试仓库。

- 修复仅针对 V4 冻结测试场景，不能推广为任意仓库修复能力。
- dispatch 模型说明有一处已保留的不准确表述：无效 Token 实际仍先触发 PermissionError；
  补丁符合冻结契约，发布正文由服务端根据证据生成，不采用该错误解释。
- main 若在检查之间被外部修改，GitHub PR API 没有 expected-base CAS；系统在各写入前后
  检查 SHA，检测变化即停止并撤销审批。已创建的对象/分支/PR 可能保留供人工检查。
- 网络超时可能意味着远程操作已成功；恢复先按精确对象 SHA、分支、PR marker 核对，
  不盲目重复写入。不可证明归属或内容时停止，不覆盖、不删除。
- 需要 PAT 对该私有仓库有 Contents 和 Pull requests 的 Read and write。
  现有只读成功和 reported push role 不能证明 PAT 的 PR 写 scope；授权后实际调用验证。
  403 等权限失败将保存部分状态并停止，不自行扩权。
- 远程最终 Commit SHA 必须与上文完全一致；若 GitHub 返回不同身份，不创建对应分支或 PR。

授权后继续：真实发布→精确父提交/tree/PR 核验→重复请求核验→最终全量回归、
安全与 Scope Audit→V5 Completion Report→停在 V5/V6。
