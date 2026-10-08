# RepoPilot — AI Codebase Intelligence & Issue Resolution Agent

## 一、项目目标

RepoPilot 是一个长期维护的 AI Developer Tool 项目。

我的求职目标是尽快获得：

- AI 应用工程
- AI 全栈
- Agent 工程
- Code Agent / AI Developer Tools

相关实习或岗位，优先考虑一线互联网和 AI 公司。

当前技术学习主线：

TypeScript / React
→ Python / FastAPI
→ HTTP 前后端通信
→ LLM API
→ RAG
→ Agent
→ MCP
→ Evaluation
→ Production Engineering

RepoPilot 的作用不是额外做一个独立 Demo。

它要成为一条长期工程主线，把这些能力逐渐连接起来。

---

# 二、最终产品目标

RepoPilot 最终允许用户连接或导入真实代码 Repository。

系统逐渐具备：

Repository Import
→ Repository Snapshot
→ Repository Indexing
→ Code Search
→ Codebase RAG
→ Source Citation
→ Code Intelligence
→ Issue Understanding
→ Agent Tool Calling
→ Issue Resolution
→ Code Modification
→ Test Execution
→ Result Verification
→ GitHub / MCP Integration
→ Evaluation
→ Production Deployment

最终用户可以给 RepoPilot 一个真实 GitHub Issue，例如：

> 登录接口偶尔返回 500，请定位问题。

RepoPilot 最终能够完成：

Issue
→ Understand Problem
→ Inspect Repository
→ Search Relevant Code
→ Read Files
→ Locate Symbols
→ Analyze Root Cause
→ Produce Plan
→ Modify Code
→ Run Tests
→ Observe Result
→ Repair Again If Necessary
→ Verify
→ Produce Patch + Explanation
→ Create PR

这些能力不能一次实现。

系统必须逐阶段演进。

---

# 三、产品定位

RepoPilot 不是：

- ChatGPT + 上传几个代码文件；
- 普通聊天机器人；
- 把 PDF RAG 简单换成代码 RAG；
- 为了简历堆技术关键词的 Demo。

RepoPilot 最终应该成为：

AI Full Stack
+
Code-aware RAG
+
Code Intelligence
+
Agent Engineering
+
MCP / External Tool Integration
+
Evaluation
+
Production Engineering

组合起来的一套 AI Developer Tool。

任何阶段都禁止为了显得“高级”加入没有实际价值的技术。

---

# 四、项目角色

## 1. ChatGPT — Tech Lead

ChatGPT 主要负责：

- 长期系统设计
- Architecture Boundary
- 技术选型
- Version Goal 设计
- 判断功能优先级
- 判断什么现在不应该做
- 必要时查询最新官方资料
- 必要时研究优秀开源项目
- Review 关键架构决策
- Review Version 级结果
- 帮我理解核心模块
- Debug
- Evaluation 设计
- 最终 README / 简历 / 面试材料整理

ChatGPT 不需要再为普通工程修改手工拆解每一个 Codex Task。

对于小型或特殊任务，仍然可以编写显式 Scoped Task。

对于 Stage / Version 级开发：

重点是定义：

- Goal
- Architecture Boundary
- Acceptance Criteria
- Forbidden Scope

而不是人工控制每一步代码修改。

如果我的设计不合理：

直接指出并说明原因。

---

## 2. Codex — 主力实现工程师

Codex 负责：

- 阅读 Repository
- 阅读 AGENTS.md
- 阅读 PROJECT.md
- 阅读当前 Goal / Task
- 分析已有实现
- 制定 Implementation Plan
- 自主拆解 Milestone / Engineering Task
- 创建文件
- 修改代码
- Refactor
- 编写测试
- 执行测试
- 分析失败
- 修复实现
- Review Diff
- 管理 Migration
- 创建有意义的 Git Commit
- 维护执行计划
- 输出 Completion Report

对于一个批准的 Stage 或 Version Goal：

Codex 可以在正常 Milestone 之间自主继续。

不要求每个小步骤都等待人工批准。

但遇到 AGENTS.md 定义的 escalation conditions 时必须停止。

允许 Codex 编写项目绝大部分代码。

RepoPilot 的目标不是训练我的代码打字速度。

---

## 3. 我 — Project Owner + Developer

我必须逐渐具备：

- 理解整体架构
- 理解模块职责
- 理解 Request / Data Flow
- 看懂核心代码
- 能 Review 关键 Diff
- 能发现明显设计问题
- 能 Debug
- 能解释技术选择
- 能解释 Architecture Trade-off
- 能在面试中独立讲清 RepoPilot

我不要求：

逐行手写所有代码。

但：

任何核心模块如果最终无法解释，就不能算真正转化成我的能力。

---

# 五、工程执行模式

RepoPilot 使用两种开发模式。

---

## Mode A — Scoped Task

适合：

- Bug Fix
- 小型 Feature
- 小范围 Refactor
- 独立工程修改
- 明确实验

Scoped Task 应尽量明确：

### Goal

这次解决什么。

### Context

它在 RepoPilot 中的位置。

### Scope

允许修改什么。

### Requirements

功能要求。

### Interfaces

重要输入输出。

### Constraints

禁止做什么。

### Acceptance Criteria

满足什么才完成。

### Tests

必须执行什么验证。

Scoped Task 应小、明确、可测试。

---

## Mode B — Autonomous Goal

适合：

- Stage
- Version
- 大型 Milestone

人工定义：

Goal
+
Architecture Boundary
+
Acceptance Criteria
+
Forbidden Scope

Codex 负责：

Goal
→ Inspect Repository
→ Create Plan
→ Decompose Milestones
→ Implement
→ Test
→ Self Review
→ Fix
→ Verify
→ Commit
→ Continue

不要求人工编写每一个内部 Task。

但每个实际工程修改仍然应该：

- 小而有意义；
- 可测试；
- 可 Review；
- 可通过 Git 恢复。

禁止：

一次产生几十个互不相关的修改，然后统一称为“完成”。

---

# 六、Autonomous Agent Harness

RepoPilot 的 Harness 不只是 Prompt。

完整开发 Harness 包括：

- PROJECT.md
- AGENTS.md
- Goal Specification
- Codex Agent Loop
- Repository State
- Git History
- Shell
- File Editing
- Tests
- Build
- Migrations
- Runtime Feedback
- Execution Plan
- Evaluation

Markdown 文档的作用是提供：

- 目标
- 上下文
- 约束
- 架构边界
- 工作规则

测试和运行结果负责提供：

真实反馈。

Git 负责：

状态持久化与可恢复性。

Codex 应该根据：

Implementation
→ Observation
→ Failure
→ Repair

不断循环。

Harness 强，不意味着任务应该无限大。

真正的目标是：

即使 Goal 很大，也能够拆成可验证的工程状态。

---

# 七、AGENTS.md

项目根目录维护：

`AGENTS.md`

它用于定义 Codex 的长期工程规则。

包括：

- Project Mission
- Current Stage
- Architecture Rules
- Coding Rules
- Testing Rules
- Git Rules
- Configuration Rules
- Dependency Rules
- Forbidden Scope
- Autonomous Execution
- Self Validation
- Escalation Conditions
- Version Boundary

AGENTS.md 不应该复制整个 PROJECT.md。

简单理解：

PROJECT.md
= RepoPilot 要去哪里

AGENTS.md
= Codex 在这里必须怎么工作

Goal
= 当前要达到哪里

Execution Plan
= Codex 决定怎么走过去

---

# 八、GitHub / 开源项目使用原则

效率优先。

不采用：

> 所有东西都必须自己实现。

也不采用：

> 看到成熟项目就整体复制。

---

## 可以直接使用成熟基础设施

例如：

- PostgreSQL
- pgvector
- Tree-sitter
- Docker
- Redis
- OpenTelemetry
- 官方 SDK
- 数据库 Driver
- Migration Tool

这些不是 RepoPilot 的核心创新点。

---

## 可以研究成熟开源项目

但必须按阶段研究。

### Code RAG / Search

可以研究：

- pgvector
- Tree-sitter
- Sourcegraph / Cody 等代码搜索产品和架构

重点：

- Code Chunk
- Search
- Symbol
- Context Retrieval
- Code Intelligence

---

### Agent

进入 Agent 阶段后研究：

- mini-SWE-agent
- SWE-agent
- OpenHands
- 其他成熟 Code Agent

重点：

- Agent Loop
- Tool Interface
- Repository Navigation
- File Read
- Search
- Edit
- Test
- Observation
- Sandbox

目标不是复制整个框架。

---

### Evaluation

Evaluation 阶段可以研究：

- SWE-bench
- 相关 Agent Benchmark
- Retrieval Evaluation 方法

重点：

- Dataset
- Task
- Ground Truth
- Execution Environment
- Pass / Fail
- Reproducibility

---

## 开源研究原则

只读取解决当前问题需要的：

- README
- Architecture
- Design Docs
- Relevant Module
- Relevant Implementation

不要为了“研究开源”停止 RepoPilot 几天去阅读几十万行代码。

---

# 九、技术栈方向

## Frontend

- TypeScript
- React
- Vite

---

## Backend

- Python
- FastAPI

---

## Database

- PostgreSQL
- pgvector

---

## AI

- LLM API
- Embedding API

---

## Parsing

前期：

简单 parser / language-specific implementation

逐渐根据实际需求升级：

- Tree-sitter
- AST / Syntax Tree
- Symbol Metadata

---

## Infrastructure

Stage 0：

Docker Compose
→ PostgreSQL + pgvector

这里只用于本地数据库基础设施。

Stage 0 不代表：

- React 容器化
- FastAPI 容器化
- Production Docker Architecture
- Kubernetes

后续根据真实需求加入：

- Redis
- Docker Application Packaging
- Sandbox
- OpenTelemetry
- GitHub API
- MCP
- Job Queue
- Deployment Infrastructure

禁止提前预埋。

---

# 十、项目生命周期

RepoPilot 按以下阶段演进：

Stage 0 — Project Inception

V1 — Codebase RAG

V2 — Code Intelligence

V3 — Repository Agent

V4 — Issue Resolution Agent

V5 — MCP + GitHub

V6 — Evaluation

V7 — Production Engineering

V8 — Final Product & Portfolio Release

每个 Version 都必须形成一个可验证稳定状态。

---

# 十一、Stage 0 — Project Inception

## 目标

把 RepoPilot 从：

Project Idea

升级成：

真正可运行、可测试、可继续扩展的工程项目。

---

## Stage 0 必须建立

- Project Scope
- Architecture Boundary
- Repository Structure
- Development Environment
- Git Repository
- AGENTS.md
- README
- Environment Configuration
- React
- FastAPI
- PostgreSQL
- pgvector
- Database Connection Foundation
- Migration
- Testing Foundation

最终建立最小闭环：

React
→ HTTP
→ FastAPI
→ PostgreSQL

---

## Stage 0 Task 1 — Completed

第一条运行链已经建立：

Browser
→ React
→ HTTP GET `/api/health`
→ FastAPI
→ JSON
→ React State
→ UI

Task 1 主要建立：

- React App
- FastAPI App
- Health API
- CORS
- frontend API client
- backend test
- README
- initial repository structure

Task 1 不包含数据库。

历史 Task Specification：

`docs/tasks/stage-0-task-1.md`

---

## Stage 0 剩余目标

后续 Stage 0 应建立：

Docker Compose
→ PostgreSQL
→ pgvector extension

以及：

FastAPI
→ Database Configuration
→ Database Engine / Session
→ Migration
→ Database Validation

最终：

React
→ FastAPI
→ PostgreSQL

能够真实运行。

---

## Stage 0 Docker Boundary

Stage 0 允许 Docker Compose。

目的：

提供可重复的本地 PostgreSQL + pgvector 环境。

当前不应该：

- Dockerize React
- Dockerize FastAPI
- 建 Production Container Architecture
- 使用 Kubernetes

应用容器化以后根据 Production Engineering 需求再做。

---

## Stage 0 pgvector Boundary

Stage 0 可以：

启用 `vector` extension。

但不要提前建立：

- embedding schema
- vector dimension
- embedding table
- HNSW
- ANN Index

原因：

Embedding Model 尚未在 V1 M3 正式确定。

不要让 Stage 0 的数据库设计提前锁死未来模型。

---

## Stage 0 Completion

Stage 0 完成以后：

必须执行一次最终 Validation。

检查：

- frontend build
- backend tests
- database startup
- database connectivity
- migration
- pgvector availability
- environment configuration
- Git status
- documentation accuracy

然后：

输出 Stage 0 Completion Report。

Codex 必须停止。

不得自动进入 V1。

---

# 十二、V1 — Codebase RAG

这是 Stage 0 完成后开发的第一个真正产品版本。

目标：

建立一套真正：

- 可 Debug
- 可 Evaluation
- 可引用真实源码

的 Repository-level Codebase RAG。

---

# 十三、V1 Index Pipeline

完整索引链：

Repository
→ Snapshot
→ File Scanner
→ File Filter
→ Parser
→ Code-aware Chunker
→ Embedding
→ PostgreSQL + pgvector
→ Index

每一层应逐渐拥有明确职责。

---

# 十四、V1 Query Pipeline

Question
→ Query Embedding
→ Retriever
→ Relevant Chunks
→ Context Builder
→ LLM
→ Answer
→ Citation

前端必须能够看到：

Retrieval Evidence。

系统不能只有最终 LLM Answer。

---

# 十五、V1 Milestones

## M0 — Foundation

确认 Stage 0 基础设施可支持 V1。

只做必要调整。

不要重建已经完成的基础工程。

---

## M1 — Repository Ingestion

解决：

如何把一个真实代码 Repository 安全地引入系统。

建立：

Repository
→ Snapshot
→ File Scanner
→ File Filter

---

## M2 — Code-aware Chunking

解决：

代码应该怎样切成适合 Retrieval 的结构单元。

建立：

Parser
→ Symbol Boundary
→ Chunk
→ Metadata

---

## M3 — Embedding + Vector Index

解决：

如何将代码 Chunk 转成向量并存入 PostgreSQL + pgvector。

建立：

Embedding Content
→ Embedding API
→ Vector Storage
→ Exact Search Foundation

---

## M4 — Retrieval Engine

解决：

用户问题如何找到真正相关的代码。

建立：

Question
→ Retriever
→ Ranked Chunks

Retriever 必须独立可 Debug。

---

## M5 — RAG Generation + Citation

解决：

如何基于真实 Evidence 生成 Answer。

建立：

Retriever
→ Context Builder
→ LLM
→ Answer
→ Source Citation

---

## M6 — React Product UI

将前面能力形成真正可用产品。

前端不仅显示 Answer。

还必须显示：

- Evidence
- File Path
- Symbol
- Line Range
- Chunk
- Score / Distance

---

## M7 — Retrieval Quality Improvement

建立 Retrieval Baseline 后：

观察 Bad Cases。

然后有证据地比较：

Fixed Chunk
vs
Code-aware Chunk

Vector-only
vs
Hybrid Retrieval

如果真实问题存在：

再加入：

- Lexical Retrieval
- Symbol Retrieval

禁止一开始全部实现。

---

# 十六、Repository Snapshot

Repository 必须有：

Repository Snapshot。

原因：

代码本身会变化。

如果只记录：

Repository ID

而不记录某个代码状态：

用户今天的问题与明天的 Repository 内容可能不同。

以后 GitHub 接入以后：

Snapshot 可以对应：

Commit SHA。

---

# 十七、File Scanner / Filter

默认过滤：

- `.git`
- `node_modules`
- `dist`
- `build`
- `.venv`
- binaries
- generated files
- very large files
- minified files

敏感文件默认排除：

- `.env`
- `*.pem`
- `*.key`
- credentials
- secrets

V1 不要求支持所有编程语言。

第一阶段主要支持：

- Python
- TypeScript
- JavaScript
- TSX
- JSX
- Markdown

---

# 十八、Code-aware Chunking

代码 Chunk 采用：

Semantic Boundary
+
Size Constraint

优先边界：

- class
- function
- method
- Markdown heading

但不能机械理解成：

一个 Function 永远等于一个 Chunk。

超大 Function：

允许继续拆分。

非常小 Symbol：

以后根据 Evaluation 决定是否组合。

---

# 十九、Chunk Metadata

Chunk Metadata 至少考虑：

- repository
- snapshot
- file path
- language
- chunk type
- symbol name
- qualified name
- parent symbol
- start line
- end line
- content hash
- chunking version

区分：

`raw_content`

与：

`embedding_content`

Embedding Content 可以加入：

- File Path
- Symbol
- Type
- Structural Context

但必须通过实际 Retrieval 表现决定。

---

# 二十、Vector Search

V1 Baseline 首先使用：

Exact Vector Search。

不要一开始使用：

- HNSW
- ANN tuning
- complex vector index optimization

如果真实 Repository 数据规模导致：

- latency
- memory
- throughput

出现问题：

再进行 ANN 实验。

---

# 二十一、Retriever

Retriever 必须作为独立模块存在。

接口概念：

Question
→ Retriever
→ Chunks

Retriever 不负责：

生成最终 Answer。

原因：

必须能够独立判断：

Retrieval 是否找对代码。

否则如果最终回答错误：

无法判断是：

Retrieval Error

还是：

Generation Error。

---

# 二十二、Retrieval Debug

系统至少应该能够观察：

- Query
- Top-K
- Score / Distance
- File Path
- Symbol
- Line Range
- Chunk Content

Retrieval 必须是：

Observable Pipeline。

不能隐藏在一个：

`ask_question()`

函数里。

---

# 二十三、Citation

Citation 不允许 LLM 自己编：

- file path
- symbol
- line range

Retriever 提供真实：

Evidence / Chunk ID。

LLM 只能引用这些 Evidence ID。

Backend 再把 Evidence ID 映射到：

- File Path
- Symbol
- Line Range
- Source Code

Citation 的真实性来自系统数据。

不是依赖 LLM 自觉。

---

# 二十四、Context Builder

Context Builder 必须独立存在。

负责：

- Chunk Formatting
- Ordering
- Deduplication
- Token Budget
- Evidence ID
- Context Construction

禁止简单使用：

`join(chunks)`

作为长期实现。

---

# 二十五、Repository Content Security

Repository Content 必须视为：

Untrusted Data。

不能因为代码文件里面写着：

> Ignore previous instructions

就把它当 System Instruction。

LLM Prompt 必须明确划分：

Instruction

和：

Repository Content。

这是后续 Prompt Injection 防护的基础。

---

# 二十六、V2 — Code Intelligence

V1 主要解决：

> 语义上哪些代码和问题相关？

V2 开始解决：

> 代码结构本身是什么？

逐渐加入：

- AST / Syntax Tree
- Symbol Index
- Definition
- Reference
- Import Relation
- Function Metadata
- Class Metadata
- Repository Structure

必要时使用：

Tree-sitter。

---

## V2 Retrieval

逐渐研究：

- Vector Retrieval
- Lexical Retrieval
- Symbol Retrieval
- Structural Retrieval

如何组合。

不要一开始承诺：

完整精确 Call Graph。

先根据真实需求逐步实验。

---

# 二十七、V3 — Repository Agent

进入 Agent 学习阶段后开始。

第一版：

Read-only Repository Agent。

允许 Tool：

- `list_files`
- `search_code`
- `search_symbol`
- `read_file`
- `retrieve_context`

流程：

Issue / Question
→ Decide Next Information
→ Tool Call
→ Observation
→ Decide Again

目标：

真正理解并实现：

Agent Loop。

第一版禁止：

Multi-Agent。

---

## Issue Analysis Agent

逐渐升级：

Issue
→ Inspect Repository
→ Search
→ Read
→ Analyze
→ Resolution Plan

这个阶段：

可以仍然不修改代码。

先把：

Repository Investigation

做好。

---

# 二十八、V4 — Issue Resolution Agent

在 Read-only Agent 稳定后才开放：

- `edit_file`
- `apply_patch`
- `run_tests`

完整流程：

Issue
→ Analyze
→ Plan
→ Modify
→ Test
→ Observe Failure
→ Modify Again
→ Verify

这里 RepoPilot 开始接近：

Software Engineering Agent。

---

# 二十九、Agent Sandbox

任何第三方 Repository 的代码：

不能直接无限制运行在宿主机。

Agent 获得执行能力以后：

必须逐步加入隔离环境。

至少考虑：

- File System
- Command Allowlist / Restriction
- Execution Time
- Network
- Secrets
- Resource Limits

后续可以使用：

Docker / Sandbox Runtime。

Stage 0 的数据库 Docker：

与 Agent Sandbox 是两个不同用途。

---

# 三十、V5 — MCP + GitHub

进入 MCP 阶段以后：

首先理解 MCP 解决什么问题。

不要为了简历硬加 MCP。

目标：

让 RepoPilot Agent 可以通过标准化 Tool Interface 接入外部系统。

优先：

GitHub。

逐渐支持：

- Repository
- Issue
- PR
- Branch
- Commit
- Create Branch
- Create PR

最终目标：

GitHub Issue
→ RepoPilot Agent
→ Repository Investigation
→ Patch
→ Tests
→ GitHub PR

实施 MCP 时：

必须重新查询当时最新官方 Specification。

禁止依赖过时教程。

---

# 三十一、V6 — Evaluation

Evaluation 不是最后：

“感觉效果不错”。

从 V1 开始就积累：

- Test Repository
- Golden Questions
- Expected Files
- Expected Symbols
- Expected Chunks

V6 再正式形成完整 Evaluation System。

---

# 三十二、Retrieval Evaluation

Dataset：

Query
+
Expected Evidence

可以研究指标：

- Hit@K
- Recall@K
- MRR

比较：

- Chunking Strategy
- Embedding Model
- Top-K
- Threshold
- Hybrid Retrieval
- Symbol Retrieval
- Structural Retrieval

所有提升必须有真实实验。

禁止：

编造数字。

---

# 三十三、RAG Evaluation

评估：

- Evidence 是否正确
- Citation 是否正确
- Answer 是否 Grounded
- 是否出现 Unsupported Claims

Generation Quality 必须和：

Retrieval Quality

分开分析。

---

# 三十四、Agent Evaluation

构建真实 Issue Tasks。

记录：

- Task Success Rate
- Patch Apply Success
- Test Pass Rate
- Tool Steps
- Token Usage
- Latency
- Cost

必要时参考：

SWE-bench

的：

- Task
- Ground Truth
- Execution Environment
- Reproducibility

思想。

不要求 RepoPilot 去刷完整 SWE-bench Leaderboard。

---

# 三十五、V7 — Production Engineering

只有核心 AI 能力稳定以后：

才逐渐进入生产工程。

根据真实需求加入：

- Authentication
- Users
- Repository Ownership
- Job Queue
- Redis
- Caching
- Async Indexing
- Retry
- Timeout
- Rate Limiting
- Structured Logging
- Tracing
- Metrics
- Error Tracking
- Configuration Management
- Docker Application Packaging
- CI
- Deployment
- Database Backup
- Production Migration

---

# 三十六、Observability

长期应能够追踪：

Request
→ Retrieval
→ LLM Call
→ Tool Call
→ Agent Step

不能长期依赖：

```python
print("error")
````

系统需要知道：

到底是哪一层出了问题。

---

# 三十七、Production Optimization

最后才开始优化真实瓶颈。

测量：

* Indexing Time
* Retrieval Latency
* LLM Latency
* Agent Runtime
* Token Usage
* Cost
* Cache Hit Rate
* Failure Rate

Latency 至少考虑：

* P50
* P95

只有测量以后才优化。

禁止：

先优化想象中的瓶颈。

---

# 三十八、V8 — Final Product & Portfolio Release

RepoPilot 1.0 最终应具备：

* 完整 GitHub Repository
* 高质量 README
* Architecture Diagram
* Data Flow Diagram
* Online Demo
* Demo Video
* Evaluation Dataset
* Evaluation Report
* 真实 Retrieval 指标
* 真实 Agent 指标
* Latency / Cost 数据
* Tests
* CI
* Docker
* Deployment
* Version Evolution
* Security Boundary
* Limitations

---

# 三十九、最终 UI 方向

RepoPilot 不应该长成普通 Chatbot。

长期 UI 可以采用：

左侧：

Repository / File Tree

中间：

Chat / Agent Task

右侧：

Evidence / Retrieval / Agent Trace

点击 Citation：

直接显示：

* File Path
* Symbol
* Line Range
* Source Code

Agent Task 页面可以显示：

* Plan
* Tool Call
* Observation
* Patch
* Test Result

目标：

让用户可以看到：

> AI 为什么得到这个结论。

---

# 四十、测试原则

从项目第一天开始测试。

---

## Unit Test

用于：

* File Filter
* Parser
* Chunker
* Utility
* Pure Transformations

---

## Integration Test

用于：

File
→ Chunk
→ Embedding
→ Database
→ Retrieval

---

## API Test

用于：

* Repository API
* Index API
* Retrieve API
* Chat API

后期增加：

* Agent Integration Test
* Evaluation Test
* End-to-End Test

---

# 四十一、Golden Repository

项目长期维护一个小型：

Golden Repository / Sample Repository。

它必须具有：

明确已知的：

* 文件
* Symbol
* 代码结构
* Query
* Expected Evidence

用于检查：

系统升级以后有没有悄悄破坏旧能力。

---

# 四十二、Git 工作方式

项目从第一天进入 Git。

保持：

小而有意义的 Commit。

例如：

```text
feat: add repository ingestion pipeline

feat: implement structure-aware Python chunking

test: add retrieval integration cases

fix: prevent cross-snapshot retrieval
```

不要：

```text
update

fix

changes

final
```

每个 Milestone 最好形成：

明确稳定节点。

必要时使用：

Git Tag。

Git History 最终应该能够看出：

Empty Project
→ Full Stack Foundation
→ Codebase RAG
→ Code Intelligence
→ Agent
→ Production AI System

的演进过程。

---

# 四十三、架构演进原则

加入任何新技术前必须回答：

1. 它解决什么真实问题？
2. 为什么现在需要？
3. 不用它会怎样？
4. 有没有更简单的方案？
5. 增加的复杂度值不值得？

如果回答不了：

暂时不加入。

---

# 四十四、Baseline-First

所有核心能力遵循：

Baseline
→ Observe Bad Cases
→ Improvement
→ Implementation
→ Evaluation
→ Keep / Remove

例如：

先：

Vector Retrieval。

如果真实出现 Symbol Query Bad Case：

再研究：

Lexical / Symbol Retrieval。

不是：

看到 Hybrid Search 很高级就直接加。

---

# 四十五、安全原则

Code Agent 安全必须随着能力增强同步升级。

长期重点：

* Repository Secrets
* Prompt Injection
* Path Traversal
* ZIP Bomb
* Malicious Repository
* Arbitrary Command Execution
* Shell Injection
* Agent Tool Permission
* GitHub Token Permission
* Network Access
* Sandbox Escape

V1 不需要一次解决所有 Production Security。

但设计不能完全忽视这些风险。

尤其 Agent 开始：

运行 Repository Code

以后：

必须使用隔离环境。

---

# 四十六、学习原则

RepoPilot 是求职项目。

不是大学课程。

遇到新概念：

只学习当前工程任务需要的部分。

例如需要 Tree-sitter：

先理解：

* Parser
* Syntax Tree
* Node
* Range
* Query

足够实现当前功能即可。

不要暂停 RepoPilot 两周：

系统学习完整编译原理。

需要 Docker：

先理解：

* Image
* Container
* Volume
* Network
* Command
* Isolation

够当前 RepoPilot 使用即可。

始终：

Project Driven Learning。

---

# 四十七、工程执行与学习分离

Codex 的工程执行：

不需要为了教学在每一个 Milestone 停止。

正常情况：

Milestone 1
→ Implement
→ Test
→ Commit
→ Milestone 2

可以自动继续。

我的学习：

在关键节点集中进行。

包括：

* Stage / Version 开始
* 关键架构决策
* 我主动要求学习
* Version Completion Review

---

# 四十八、核心模块学习验收

对于核心模块，我最终至少必须能够回答：

* 它是什么？
* 为什么存在？
* 输入是什么？
* 输出是什么？
* 谁调用它？
* 它调用谁？
* 数据下一步去哪？
* 哪里可能失败？
* 如何 Debug？
* 为什么这样设计？
* 为什么不用另一个方案？

如果答不上来：

需要重新建立系统模型。

但这不意味着：

Codex 必须暂停每一个正常工程 Milestone 等待教学。

---

# 四十九、Milestone Review 内容

对于重要 Milestone，我最终应该理解：

1. 解决什么问题；
2. 为什么现在需要；
3. 之前系统缺什么；
4. 架构发生什么变化；
5. 新增模块；
6. 每个模块职责；
7. Request / Data Flow；
8. 核心接口；
9. 测试方法；
10. Acceptance Criteria；
11. 常见 Bug；
12. 技术 Trade-off；
13. 面试可能如何提问。

---

# 五十、项目文档原则

禁止产生大量为了：

“显得正规”

而存在的文档。

长期维护真正有价值的：

* README.md
* AGENTS.md
* PROJECT.md
* architecture.md
* roadmap.md
* evaluation.md
* 必要 ADR / Design Decision
* Evaluation Report

以及开发期间真正需要的：

Execution Plan / Task Specification。

文档必须随着真实系统变化更新。

---

# 五十一、Execution Plan

对于 Stage / Version 级 Goal：

Codex 应维护一个简洁 Execution Plan。

例如：

`docs/tasks/stage-0-plan.md`

或：

`docs/tasks/v1-plan.md`

记录：

* Goal
* Milestones
* Current Milestone
* Completed Work
* Validation
* Important Decisions
* Blockers
* Remaining Work

Execution Plan 不是第二份 PROJECT.md。

它必须保持简洁。

真正的系统状态主要来自：

* Code
* Tests
* Git

---

# 五十二、Version Boundary

Codex 可以在：

同一个 Stage / Version

内部正常自主推进。

例如：

V1 M1
→ M2
→ M3
→ M4

正常情况下：

不需要人工批准。

但是：

跨 Version 不允许自动进行。

例如：

Stage 0
→ V1

V1
→ V2

V2
→ V3

必须存在一个明确的新 Goal。

---

# 五十三、Escalation

Codex 遇到以下情况必须停止：

* PROJECT.md 与 AGENTS.md 产生实质冲突
* Goal 存在影响架构的重大歧义
* 需要修改冻结的架构
* 需要改变关键技术选择
* 需要权限 / Credential
* Tests 无法在现有 Scope 内通过
* 发现可能导致大量返工的设计问题
* 需要执行破坏性操作
* 需要执行安全敏感操作
* 需要重写重要 Git History
* 即将进入未授权的下一个 Version

普通工程判断：

Codex 自己解决。

---

# 五十四、求职价值判断

每增加一个功能都要问：

> 它能证明招聘方真正需要的什么能力？

例如：

Code-aware Chunking

证明：

RAG Engineering。

Retrieval Debug

证明：

AI System Debugging。

Evaluation

证明：

不是靠感觉调 AI。

Agent Tools

证明：

Agent Engineering。

MCP

证明：

External Tool / Protocol Integration。

Docker Sandbox

证明：

Agent Runtime / Security Awareness。

Observability

证明：

Production AI Engineering。

如果一个功能：

既不增加产品能力，

也不增加工程证明力，

也不提高：

* Reliability
* Debuggability
* Safety
* Evaluation Quality

那么：

不要做。

---

# 五十五、最终简历标准

最终不能写：

> 基于 LangChain 实现 RAG，准确率显著提高。

必须能够写成真正的工程成果。

例如：

> 设计并实现真实代码仓库的结构感知 RAG Pipeline，通过 AST / Symbol Metadata、Hybrid Retrieval 和 Source-level Citation 支持 Repository-level Code QA。

> 构建可观测 Retrieval Pipeline，对不同 Chunking / Retrieval Strategy 建立 Evaluation Dataset，并使用真实指标进行比较。

> 构建 Tool-Calling Code Agent，实现 Repository Search、File Inspection、Patch Generation 与 Sandboxed Test Execution 的多步 Issue Resolution Loop。

> 通过 MCP 接入 GitHub，实现 Issue → Repository Analysis → Patch → Test → PR 的完整工程流程。

具体数字：

只能使用 RepoPilot 实际测量结果。

---

# 五十六、最终面试目标

最终我应该能够不用打开代码，从头讲清：

* 为什么做 RepoPilot
* 用户问题是什么
* 系统架构是什么
* Repository 如何 Index
* 为什么需要 Snapshot
* 如何 Chunk Code
* 为什么普通 Text Chunking 不够
* Embedding 如何工作
* pgvector 如何 Retrieval
* Vector Search 的局限
* 为什么加入 Lexical / Symbol Retrieval
* Citation 如何保证真实
* 如何区分 Retrieval Error 和 Generation Error
* Agent 如何调用 Tool
* Agent Loop 是什么
* 为什么不用 Multi-Agent
* MCP 在系统中解决什么问题
* Agent 如何修改代码
* 如何安全运行测试
* 如何设计 Evaluation
* 指标如何计算
* 系统哪里最慢
* 哪里最贵
* 哪里容易失败
* 如何监控
* 有哪些 Limitations
* 如果重新设计会改什么

只有达到这里：

RepoPilot 才真正成为我的简历项目。

---

# 五十七、当前执行状态

当前状态：

- Stage 0 — Project Inception 已完成
- V1 — Codebase RAG 已完成
- 当前停在 V1 / V2 Version Boundary
- V2 尚未授权开始

当前基础架构：

React
→ HTTP
→ FastAPI
→ SQLAlchemy / PostgreSQL
→ pgvector

并已建立：

- Docker Compose 本地 PostgreSQL + pgvector
- Environment Configuration
- Database Connection
- Alembic Migration
- Testing Foundation

V1 已完成以下 Milestone：

- M0 — Foundation Check：已完成
- M1 — Repository Ingestion：已完成
- M2 — Code-aware Chunking：已完成
- M3 — Embedding + Vector Index：已完成
- M4 — Retrieval Engine：已完成
- M5 — RAG Generation + Citation：已完成
- M6 — React Product UI：已完成
- M7 — Retrieval Quality Improvement / Evaluation：已完成

V1 的完成流程已执行：

Final Validation
→ Completion Report
→ Stop

RepoPilot 当前保持在此边界；没有单独授权的 Version Goal，不得自动进入 V2。

---

# 五十八、长期执行原则

RepoPilot 的长期方向已经冻结。

后续允许：

根据真实工程问题调整实现。

不允许：

频繁推翻长期产品方向。

开发流程：

Project Scope
→ Version / Stage Goal
→ Codex Inspect Repository
→ Implementation Plan
→ Milestones
→ Autonomous Agent Loop
→ Validation
→ Git Commits
→ Version Completion
→ Architecture / Evaluation / Learning Review
→ Next Goal

正常 Milestone：

Codex 自主执行。

重大问题：

升级人工决策。

Version 完成：

集中 Review。

然后：

再决定是否进入下一 Version。

---

# 五十九、最终原则

RepoPilot 不追求：

最多技术。

RepoPilot 追求：

真实能力
+
清晰架构
+
可 Debug
+
可测试
+
可 Evaluation
+
可解释
+
可演进
+
可证明

所有工程决策最终服务于两个目标：

1. 做出真正有意义的 AI Developer Tool。
2. 让我能够凭这个项目证明真实的 AI 应用 / Agent 工程能力。

