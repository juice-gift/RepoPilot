# RepoPilot — V7 to Pre-V8 Autonomous Engineering Goal

## 0. Authorization

本次明确授权 Codex 连续完成 RepoPilot 在 V8 之前的剩余工程工作。

授权范围：

1. V7 Production Engineering
2. 真实 Python 仓库通用化
3. 真实 Issue Resolution 端到端集成
4. 最终工程验收与稳定化

本 Goal 明确授权上述连续工程阶段，覆盖历史文档中相应的 Version Stop Boundary，但不授权进入 V8。

使用 `AGENTS.md` 定义的 Autonomous Goal 执行模式。

你可以自主检查、规划、实现、测试、修复、审查并创建本地 Git Commit。正常 Milestone 之间不需要等待人工确认。

**不要只输出计划就停止。必须持续执行实际工程工作，直到所有已授权验收项完成，或出现真正需要人工决策的阻塞。**

所有真实远程写入、公开部署、破坏性操作和重大安全边界变更仍需单独授权。

## 1. Project Context

Repository：`juice-gift/RepoPilot`

基于已经完成的 V1–V6 开发。

当前主要技术架构：

- React + TypeScript + Vite
- Python + FastAPI
- PostgreSQL + pgvector + SQLAlchemy + Alembic
- RAG、AST、Tree-sitter
- LLM Responses API、Tool Calling、Agent Loop
- Docker Sandbox
- MCP + GitHub Integration
- Evaluation Harness

V6 已完成，但当前资料不能替代真实代码检查。

现有 V5 已经具有 GitHub Issue 导入、Commit/Snapshot 绑定、受控修复、持久化执行结果、精确人工审批、Draft PR 发布及恢复能力。

**必须复用并扩展既有模块，不得未经证据就重建它们。**

### Preflight

开发前：

1. 读取 `AGENTS.md`、`docs/PROJECT.md`、相关 Goal、Plan、Completion Report。
2. 检查当前分支、HEAD、工作区、Git 历史及最新远程状态（只读）。
3. 核验 V4、V5、V6 的真实功能、测试和限制。
4. 识别旧版本文档中已过时的状态或禁令。
5. 执行可用的基线测试、构建、迁移及 Docker 检查。
6. 创建独立开发分支，例如 `codex/pre-v8-engineering`。
7. 将本 Goal 保存到 `docs/goals/pre-v8-engineering.md`。
8. 创建 `docs/tasks/pre-v8-plan.md`，记录里程碑、验收、进度、风险及阻塞。

历史 Version Stop Notice 可以被本次明确授权覆盖；其他实质性架构、安全冲突不能擅自忽略。

## 2. Phase A — V7 Production Engineering

### Goal

让 RepoPilot 从开发环境可运行，升级为可以在受控本地环境中可靠构建、启动、运行、排障和恢复的工程系统。

### Scope

**A1. Application Containerization**

- 为 FastAPI 和 React 应用建立可复现的容器构建。
- 扩展现有 Docker Compose，支持完整应用栈启动。
- 保留原有本地开发方式。
- 正确处理依赖锁定、镜像构建、容器网络、健康检查、持久化存储和启动顺序。
- 保持数据库迁移流程明确且可验证。
- Docker 构建不得包含真实 `.env`、Token、密钥或其他敏感文件。
- 区分应用容器和 Agent 测试 Sandbox，禁止无控制地共享 Docker daemon 权限。

**A2. Configuration Management**

- 统一梳理开发、测试、受控部署环境的配置要求。
- 为配置提供明确类型、默认值、合法性检查和启动失败信息。
- 更新 `.env.example`。
- 明确数据库、LLM、Embedding、GitHub MCP 和 Sandbox 的配置边界。
- 不允许生产或部署配置依赖隐式开发默认值。

**A3. CI**

建立适度、可维护的 GitHub Actions CI。

至少覆盖：

- Python 测试与 Ruff
- TypeScript 检查和前端构建
- PostgreSQL/pgvector 相关集成测试
- Alembic 迁移一致性
- Docker 镜像构建检查
- 关键安全和配置检查

采用最小权限和合理的依赖版本固定策略。

不在 CI 中运行未经许可的真实远程写操作，不要求公开模型密钥。

**A4. Observability**

建立足以排查真实问题的轻量可观测性。

至少支持：

- Structured Logging
- Request / Correlation ID
- API 错误与延迟
- Retrieval 和 LLM 调用诊断
- Agent Step、Tool Call、Sandbox Test 的结果和耗时
- 关键失败分类

优先复用现有 Trace 和 Evaluation 数据。

避免重复记录敏感数据、完整源码、模型密钥或内部推理内容。

没有真实需求时，不引入独立监控集群、复杂消息系统或外部商业可观测平台。

**A5. Reliability**

围绕实际故障点建立：

- 明确的 Timeout 和资源上限
- 合理的 Retry 与失败处理
- 防止非幂等操作重复执行
- Sandbox 生命周期和残留资源清理
- 数据库与外部服务不可用时的安全失败
- 重启后的持久化状态一致性

优先解决已确认的故障模式。

**A6. Deployment**

提供经过实际验证的受控部署方式。

至少应完成：

- 全栈 Compose 启动
- 数据库迁移
- API / Web / Database 健康检查
- 关键用户流程 Smoke Test
- 停止、重启、备份和恢复说明
- 单机部署及现有单用户安全边界的限制说明

禁止未经授权公开互联网部署。

如果缺乏适用于公网环境的认证、授权和隔离机制，必须明确限制服务只能在可信本地环境使用。

### Acceptance Criteria

- 使用文档化步骤可从干净环境启动完整应用。
- 关键容器具备正确的健康状态。
- 迁移和重启能够保留所需数据。
- 核心 API 和 UI 流程正常。
- CI 定义具备可验证的实际执行结果；未经远程执行的 Workflow 不能宣称已在 GitHub CI 通过。
- 日志足以定位关键失败，同时不会泄漏秘密。
- 不破坏 V1–V6 已有能力。

完成后执行测试、自审、提交，并直接进入 Phase B。

## 3. Phase B — Trusted Python Repository Generalization

### Goal

将 V4 从固定 Golden Case / Frozen Profile 扩展为支持明确受信任、显式允许的真实 Python Repository。

不能为了通用化取消安全约束。

### Scope

**B1. Repository Support**

- 检查现有 Snapshot、Workspace、Patch、Test Profile 和 GitHub Binding 结构。
- 区分可检索 Snapshot 与可执行仓库工作树。
- 支持在明确授权的 Python 仓库、固定 Commit SHA 上创建可复现的私有工作区。
- 保持原始仓库和不可变 Snapshot 不受修改。
- 通过实际需求确定最小的受支持仓库布局范围。

**B2. Configurable Test Profiles**

- 将测试配置从固定 Golden Case 解耦。
- 支持受信任 Python 项目采用明确审核的测试 Profile。
- 测试命令、镜像、工作目录和依赖准备方式由受信任配置控制，不由 Issue 文本或 LLM 自由生成。
- 不允许任意 Shell、未经审核的依赖安装或容器运行选项。
- 不支持的仓库明确拒绝并解释原因。

**B3. Safe Repair Workflow**

保留：

Issue → Investigation → Plan → Patch → Sandbox Tests → Observation → Repair → Verify。

要求：

- 每轮修改有准确的工作区 Revision。
- Patch 只作用于允许的路径和文件。
- 禁止修改敏感文件或越界路径。
- 真实 Diff 从实际文件变化计算。
- 测试使用与 Patch 对应的准确代码 Revision。
- 记录测试命令、结果、退出码、超时和重要诊断。
- 对失败、歧义、无足够证据的任务可以安全拒绝。

**B4. Sandbox Isolation**

维持和验证：

- 非特权用户
- 默认网络隔离
- 必要的 CPU / 内存 / 时间 / 进程资源限制
- 受控文件系统挂载
- 不暴露 API、数据库或 GitHub 凭证
- 不暴露 Docker Socket
- 不允许模型指定任意容器参数
- 失败时强制清理

受信任仓库的注册或选择，不意味着其代码在宿主机执行是安全的。

如果现有隔离能力无法安全支持某类仓库，拒绝该类仓库，而不是降低安全标准。

### Acceptance Criteria

- 至少使用两个不同的真实 Python 仓库验证通用化能力，不只复用现有 Golden Repository。
- 展示可配置的受信任测试 Profile。
- 验证成功修复、测试失败、安全拒绝和越界阻断等场景。
- 保留现有 V4 Golden Regression。
- 未支持的 Python 项目明确标记为不支持，不宣称支持所有 Python 仓库。
- 不引入不必要的新 Agent Framework 或复杂任务调度基础设施。

完成后测试、提交并进入 Phase C。

## 4. Phase C — End-to-End Issue Resolution Integration

### Goal

将现有 V3–V6 能力与 Phase B 的真实仓库支持连接为完整、可观察、可审批的 Issue Resolution 工作流。

目标数据流：

GitHub Issue  
→ Authorized Repository + Immutable Commit  
→ Snapshot / Workspace  
→ Agent Investigation  
→ Patch Generation  
→ Sandboxed Tests  
→ Independent Verification  
→ Persisted Result  
→ Human Review  
→ Approved Publication Proposal  
→ GitHub Draft PR

### Scope

**C1. Integration**

- 复用现有 GitHub MCP Client、Issue Binding、V4 Agent、Docker Sandbox 和 V5 Publication Pipeline。
- 补齐真实 Python 仓库路径中的缺失连接。
- 不维护第二套重叠的审批系统或发布系统。
- 清楚绑定 Issue、Commit、Snapshot、Workspace Revision、Patch、Test Result 和 Approval。
- 在不同 Revision 之间不能错误复用验证结果。

**C2. Human Approval**

人工审批必须展示：

- 目标 Repository 与 Issue
- 固定 Baseline SHA
- Agent 修改计划
- 真实完整 Diff
- 测试及独立验证结果
- 拟创建的 Branch、Commit 和 Draft PR 信息
- 失败、限制及残余风险

审批绑定精确内容及目标身份。

代码、测试结果、目标分支、基线或其他关键内容变化，应使原审批失效。

**C3. Publication**

扩展并复用 V5 已有的受控 Draft PR 机制。

必须继续遵守：

- 真实远程写入需要本次 Goal 之外的单独授权。
- 具体发布仍必须经过 V5 的精确方案人工审批。
- 不直接写默认分支。
- 不自动 Merge。
- 不自动删除有歧义的远程状态。
- 不在超时后盲目重复创建远程资源。
- 保留幂等与恢复验证。

在没有新授权时：

实现和验证完整的本地发布前流程、Mock/Fake Remote 合约与状态恢复逻辑；可以使用已有允许的 GitHub 只读能力。

准备可供独立审批的真实发布方案，但**不能实际 Push、创建远程 Branch 或创建 Draft PR**。

不得沿用旧 Proposal 的批准来授权新的远程写入。

### Acceptance Criteria

- 至少一个真实 Python Issue 能完成完整修复、独立测试和审批方案生成。
- 同时验证失败任务与需要人工判断的任务。
- 使用确定性集成测试证明本地端到端流程及模拟发布结果。
- 如有可用模型凭证，进行受控真实 LLM Agent 尝试，保存完整、可审查的执行证据。
- 不得用 Scripted Agent 的成功冒充真实 LLM 能力。
- 不得用 Mock GitHub 成功冒充真实远程发布成功。
- 如果真实发布尚未授权，明确报告远程阶段未执行。

完成后测试、提交并进入 Phase D。

## 5. Phase D — Final Engineering Acceptance

### Goal

对 V1–V7 和所有 V8 前的集成能力完成最终工程验收。

### D1. Regression

实际执行：

- 完整 Backend Unit / Integration Tests
- PostgreSQL + pgvector 实时数据库测试
- Alembic Current / Check / Clean Migration Replay
- Frontend Build / Type Check / 现有前端测试
- Ruff
- Docker Build / Compose Startup / Smoke Tests
- Sandbox Isolation 与资源清理测试
- GitHub MCP / Publication 合约及权限测试
- 既有 V1–V6 Frozen Evaluation Regression

不得将 skipped、未执行、模拟运行或使用旧代码 Revision 的结果宣称为 PASS。

### D2. Security Review

重点检查：

- Secrets Exposure
- Prompt Injection
- Path Traversal / Symlink Escape
- Repository / Snapshot Isolation
- Arbitrary Command Execution
- Sandbox Configuration
- Docker Daemon Access
- GitHub Credential Scope
- Approval Bypass
- Concurrent Publication / Retry
- Untrusted Dependency Execution
- CI Workflow Permissions
- Public Network Exposure

区分已测试的安全保证、静态审查结果和仍然存在的风险。

### D3. Real-World Evaluation

复用并适度扩展 V6 Evaluation Harness。

在独立于现有 Golden Case 的真实 Python 仓库场景上记录：

- Issue Task Success
- Patch Apply Success
- Independent Test Pass
- Safe Rejection
- Agent Tool Steps
- Latency
- Token / Cost（可获得时）
- Failure Reasons

分别报告确定性测试与真实 LLM 执行结果。

保留失败案例，不允许选择性删除失败记录或把未知结果算作成功。

不要编造提升幅度或通用成功率。

### D4. Documentation and Scope Audit

同步更新：

- README
- AGENTS.md 的当前阶段
- docs/PROJECT.md 的实际项目状态
- 必要的架构与部署说明
- Evaluation 使用说明与真实结果
- Known Limitations
- 本次执行计划和最终验收报告

不要改写历史 Goal 的验收事实。

文档必须严格区分：

- 已实现
- 已自动验证
- 已真实运行验证
- 尚未执行
- 未授权
- 已知失败
- 未来 V8 工作

检查代码与文档、API 与前端类型、配置与容器、迁移与数据库结构是否一致。

## 6. Execution Rules

采用以下循环：

Inspect → Plan → Implement → Test → Self-Review → Fix → Verify → Commit → Next Milestone。

要求：

1. 每个 Milestone 形成可验收状态。
2. 必须运行适当的真实验证，而非只声称测试通过。
3. 尽量使用有意义的小型本地 Commit。
4. 不重写无关 Git 历史。
5. 不修改无关功能来减少测试失败。
6. 不为了架构美观引入不必要的层、依赖或服务。
7. 不为潜在瓶颈提前实施 Redis、队列、Kubernetes、多 Agent 等复杂组件。
8. 对必要技术决定，优先采用现有架构下最简单、可靠、可维护的实现。
9. 不需要在普通 Milestone 之间等待用户确认。
10. 如果遭遇环境或凭证阻塞，先完成所有不依赖该条件的安全工作，再清楚报告阻塞；不能伪造验收。

### Mandatory Escalation

遇到以下情况必须停止相关操作并请求决策：

- 需要改变重大安全信任边界
- 需要真实 GitHub 或其他远程写入授权
- 需要公开部署或暴露当前单用户系统
- 需要破坏性数据库或 Git 操作
- 需要变更冻结的重要技术选型
- 发现影响架构的实质冲突
- 必需的安全隔离无法建立
- 必需验收无法在授权范围内完成

不得为了推进开发而绕过这些条件。

## 7. Final Deliverables

完成后输出一份包含以下内容的最终报告：

1. **Implemented**：每个 Phase / Milestone 的完成情况。
2. **Architecture**：最终架构与端到端数据流。
3. **Changed Files**：主要代码、测试、迁移及配置。
4. **Dependencies**：新增依赖及其必要性。
5. **Validation**：真实执行命令、测试数量、成功、失败及跳过情况。
6. **Evaluation**：真实数据集、Agent 运行结果与限制。
7. **Security**：已验证边界、未解决风险。
8. **Git History**：各里程碑本地 Commit SHA。
9. **Outstanding Work**：未完成、未授权或阻塞的工作。
10. **V8 Readiness**：是否已达到进入 V8 的工程前置条件。

保存完成报告到 `docs/evaluation/pre-v8-engineering-completion.md` 或现有规范下更合适的位置。

最终审查工作区和 Git 状态，确保成果可复查、可恢复。

## 8. Final Stop Boundary

全部已授权工程验收完成后：

**STOP BEFORE V8.**

不得自行开展：

- V8 产品展示与包装
- 在线公开 Demo
- 未授权的 GitHub Push / PR
- 生产环境公开发布
- 与当前目标无关的扩展功能

提交最终工程报告，由 Project Owner 审核后决定 V8 的具体 Goal。

**立即从真实 Repository Preflight 开始，然后自主连续实施，不要仅停留在方案设计。**