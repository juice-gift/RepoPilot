# V5 私有受控仓库准备方案

状态：2026-10-28，供 Owner 在 GitHub 手动准备；本文不是远程写入授权。
最新状态：本次受限准备已完成，三个正文更新及最终 MCP 核验通过。
见 [最终证据](../evaluation/v5-fixture-final-audit.json)。后续修复写入仍需单独批准。
后续 Owner 已明确授权仅本测试仓库的文件提交和三个 Issue 正文更新。
五文件准备已完成并通过 MCP 哈希复核，main 为
`b4279c8b4d862817e6778caa5f87da91d29ed2b7`；无需再次上传。
Issue 更新被当前 PAT 的 GitHub 403 拒绝。可在 Token 中为本仓库设置
Issues: Read and write，随后从 apps/api 执行：

```powershell
$env:PYTHONPATH = 'src'
uv run python ../../docs/tasks/v5-update-issue-bodies.py --apply
```

省略 --apply 只进行读取校验。也可在 GitHub 页面手工将下文三个正文分别填入
#1/#2/#3。脚本不提交文件、不创建分支或 PR、不输出 Token。
此前仅 README 的失败状态保留如下，实际最新证据见
[准备后审计](../evaluation/v5-fixture-prepared-audit.json)。
Owner 已确认仓库：`juice-gift/repopilot-v5-sandbox`，Issue #1/#2/#3。
2026-10-28 [实际只读校验](../evaluation/v5-github-readonly-audit.json)发现根目录
只有初始 README，三个 Issue 无正文，main SHA 与提供值不同。请完成下面第 2–4
步：上传五个冻结文件并替换初始 README，补正文，然后提供新 main SHA。

## 需要在 GitHub 创建的内容

1. 创建独立 **Private** 仓库，开启 Issues，默认分支为 `main`。
   不使用 Template，不勾选自动 README、License 或 .gitignore，不配置 Actions。
2. 将下列目录中的 **五个文件直接上传到仓库根目录**，形成初始 commit：
   `apps/api/evaluation/resolution_golden/repository/`。
   文件必须是未修复的冻结版本；保留 UTF-8/LF 字节，不复制整个 RepoPilot。
3. 上传完成后记录 `main` 的完整 commit SHA。不要手工填入 Snapshot 的
   source_revision；后续集成会通过 MCP 读取并校验实际 commit/源码。
4. 创建下面三个 Issue。编号不必是 1/2/3，记录各自实际编号即可。
5. 初始阶段不需要创建 PR 或修复分支。PR 只读接口先验证空列表，之后经批准
   创建的修复 PR 再用于单个 PR 读取验证。

根目录只包含：

| 文件 | 冻结 SHA256 |
| --- | --- |
| auth.py | `8ab1241692a053cc9c8132d938f00e51920386d2f50ddac3127dfefc4289b870` |
| fees.py | `4a9b96b0b83d3ddb08d84ffeddea7006047d23c448927e9e56cfa8d51bb04d27` |
| policy.py | `9656f43b32ba52edf9a5165475819d964f1d6043cb5fd2d666918253c9ce89df` |
| README.md | `ec62401c5e6dd72bb21de2d1f92ae30f4cbb09a2d5d43990a5d8da52a794b04f` |
| workflow.py | `51465beab2d3598b49296bc6928321c5cd76316bbda2f9cff066883c881425e6` |

仓库里的 README 是用例内容，包含刻意保留的 60/300 秒歧义，请勿改写。
`validation/test_fees.py`、`validation/test_dispatch.py` 和 manifest 不上传：
它们继续作为 RepoPilot 受保护的独立验证依据。生产执行权限仍由原 V4
profile 决定，远程 README、Issue 或测试指令不能扩展权限。

## Issue 内容（复制正文，不附加修复代码）

### 标题：`[V5 fee-days] First overdue day is not charged`

正文：

```text
late_fee misses the first overdue day. Charge one percent per overdue day, capped at 30 days; preserve integer cent rounding and invalid-input checks.
```

对应 `fee-days`。仅允许修改 fees.py；基线预期 4 failing / 4 passing，
修复后独立测试须为 8 passing。

### 标题：`[V5 dispatch-preconditions] Validate authentication and negative attempts first`

正文：

```text
submit_job must authenticate before policy validation. Authorized negative attempts must raise ValueError for permanent and transient jobs. Preserve nonnegative permanent rejection, exponential delays and the existing 300-second cap. Inspect the cross-file preconditions and fix both violations.
```

对应 `dispatch-preconditions`。仅允许修改 policy.py/workflow.py；
基线预期 2 failing / 9 passing，修复后 11 passing。

### 标题：`[V5 ambiguous-cap] Resolve the retry cap discrepancy`

正文：

```text
The guide says retry delays cap at 60 seconds while implementation uses 300. Determine the intended cap and fix the discrepancy if there is sufficient evidence.
```

对应 `ambiguous-cap`。不得补充“正确答案”；预期 needs_owner_decision，
零补丁尝试、零修改，不运行测试，不为该用例发布 PR。

## 本地 Token 与映射

在 RepoPilot 根目录已忽略的 `.env` 中设置 `GITHUB_MCP_TOKEN`。
初期建议 fine-grained PAT：Resource owner 为 juice-gift，只选择上述私有仓库，
Contents / Issues / Pull requests 均为 Read-only，Metadata 按 GitHub 自动要求。
不需要 Actions、Workflows、Administration 或 Secrets 权限。配置到期时间。
不要将 Token 放进 Issue、命令行参数、聊天、报告或仓库文件。

配置已确认仓库的本地读取授权：

```dotenv
GITHUB_MCP_ALLOWED_REPOSITORIES=["juice-gift/repopilot-v5-sandbox"]
```

空列表默认拒绝所有仓库读取，但仍允许连接/工具发现和本人身份验证。
PAT 的 GitHub 权限和本地 allowlist 同时约束读取；拥有 Token 不代表允许任意仓库。

本实现使用官方 **远程** MCP endpoint：`https://api.githubcopilot.com/mcp/`。
`GITHUB_MCP_TOKEN` 只在内存中映射为 Bearer 请求头，同时发送只读和工具选择头。
官方 **本地 stdio Server** 则读取 `GITHUB_PERSONAL_ACCESS_TOKEN`，若以后明确选择
该部署方式，应只向专用服务子进程映射该变量，不向 Sandbox 传递；本阶段不启动
本地 Server、不启动 OAuth 浏览器、不导出全局环境变量、不复用应用内部凭据。
参见 [官方配置](https://github.com/github/github-mcp-server/blob/main/docs/server-configuration.md)
和 [官方认证示例](https://github.com/github/github-mcp-server#remote-github-mcp-server)。

## 准备完成后提供的信息

只需告知仓库全名、默认分支、完整 baseline SHA、三个 case 对应 Issue 编号，
以及“Token 已在本地配置”。不要提供 Token 本身。

后续先验证真实 MCP discovery/get_me，再读取该仓库的 commit、文件、Issue
和 PR 列表。源码/Issue 不匹配冻结契约时停止执行，不修改 V4 manifest。
任何远程创建分支、提交、PR 都必须等到具体补丁、测试证据和发布提案可审阅，
再单独获得 Owner 批准。本准备方案不授权任何自动远程写入。
