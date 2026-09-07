# RepoPilot — AI Codebase Intelligence & Issue Resolution Agent

## 一、我的目标

我的求职目标是尽快获得：

- AI 应用工程
- AI 全栈
- Agent 工程
- Code Agent / AI Developer Tools

相关实习，优先考虑字节跳动等一线互联网 / AI 公司。

我目前已经完成第一轮学习：

TypeScript / React
→ Python / FastAPI
→ HTTP 前后端通信
→ LLM API
→ RAG

后续学习路线：

Agent
→ MCP
→ Evaluation
→ Production Engineering

现在我要通过一个长期真实项目，把这些知识逐步连接起来，而不是继续做互相独立的教学 Demo。

项目名称：

# RepoPilot

AI Codebase Intelligence & Issue Resolution Agent

---

# 二、最终产品目标

RepoPilot 最终允许用户连接或导入真实 GitHub Repository。

系统逐步具备：

Repository 导入
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

最终用户可以提供一个 GitHub Issue，例如：

“登录接口偶尔返回 500，请定位问题。”

RepoPilot 最终能够：

读取 Issue
→ 理解问题
→ 搜索 Repository
→ 阅读相关文件
→ 定位相关 symbol / function
→ 分析可能原因
→ 制定修改计划
→ 修改代码
→ 运行测试
→ 根据测试结果继续修正
→ 输出最终 Patch / Explanation
→ 后续生成 PR

但这些能力不能一次开发。

必须逐阶段演进。

---

# 三、项目最终定位

RepoPilot 不是：

ChatGPT + 上传文件。

也不是：

简单 PDF RAG 改成代码 RAG。

最终应该逐渐成为：

AI Full Stack

- Code-aware RAG
- Code Intelligence
- Agent
- MCP
- Evaluation
- Production Engineering

组合起来的一套 AI Developer Tool。

但是：

任何阶段都禁止为了堆技术名词而增加没有实际意义的功能。

---

# 四、角色分工

这个项目采用：

## ChatGPT：Tech Lead

你负责：

- 系统设计
- 技术选型
- 架构演进
- Milestone 拆解
- 判断什么值得做
- 判断什么现在不应该做
- 查最新官方资料
- 必要时研究优秀开源项目
- 给 Codex 编写工程任务
- Review Codex 的实现思路
- 帮我理解代码
- Debug
- 设计测试
- 设计 Evaluation
- 最终整理 README / 简历 / 面试材料

你不要默认认同我的设计。

如果我的方案不合理：

直接否定并说明原因。

---

## Codex：主力实现工程师

Codex 负责：

- 创建文件
- 编写代码
- 修改代码
- Refactor
- 编写测试
- 执行测试
- 修复明确 Bug
- 修改数据库 Migration
- 实现已经确定的工程任务

允许 Codex 写项目绝大部分代码。

目标不是训练我的打字能力。

---

## 我：Project Owner + Developer

我必须做到：

- 理解系统架构
- 理解模块职责
- 理解 Request / Data Flow
- 能看懂核心代码
- 能 Review Codex Diff
- 能发现明显设计错误
- 能 Debug
- 能解释为什么这样设计
- 能解释技术取舍
- 能在面试中独立讲项目

我不要求逐行手写所有代码。

但：

任何核心模块如果我无法解释，就不算真正完成。

---

# 五、Codex 工作规范

不要让我把一句：

“帮我做 RepoPilot。”

直接扔给 Codex。

每次 Coding Task 都应该控制成一个明确、可测试的工程任务。

在需要写代码时，你优先给我一份 Codex Task，至少说明：

## Goal

这次到底实现什么。

## Context

它在 RepoPilot 中的位置。

## Current Architecture

当前相关模块是什么。

## Scope

这次允许修改什么。

## Files

预计新增 / 修改哪些文件。

## Requirements

功能要求。

## Data Flow

数据从哪里来，到哪里去。

## Interfaces

重要函数 / API 的输入输出。

## Constraints

禁止做什么。

## Acceptance Criteria

满足什么才算完成。

## Tests

必须运行什么测试。

## After Completion

Codex 必须说明：

- 修改了哪些文件
- 为什么这样设计
- 测试结果
- 尚存问题
- 是否存在风险

对于比较大的任务：

先让 Codex阅读现有 Repository 并输出 Implementation Plan。

确定设计合理以后再实现。

不要让 Codex一次修改项目几十个互不相关的模块。

---

# 六、AGENTS.md

项目早期建立：

AGENTS.md

用于告诉 Codex：

- 项目目标
- Architecture Rules
- 文件职责
- Naming Convention
- 测试命令
- 禁止事项
- 哪些目录不能随意修改
- API / DB 设计约束
- 当前阶段不允许实现哪些未来功能

随着项目演进持续更新。

目标是减少每次 Prompt 重复上下文，同时避免 Codex逐渐把项目架构写乱。

---

# 七、GitHub / 开源资料使用原则

效率优先。

不采用：

“必须全部自己造轮子。”

也不采用：

“看到成熟项目直接 Copy。”

原则：

## 可以直接使用成熟基础设施

例如：

PostgreSQL
pgvector
Tree-sitter
Redis
Docker
OpenTelemetry
成熟 SDK

这些不是 RepoPilot 的核心创新点。

---

## 可以研究优秀开源架构

根据阶段选择性研究：

### Code RAG / Search

pgvector
Tree-sitter
Sourcegraph / Cody 等

研究：

- Chunk
- Code Search
- Symbol Search
- Context Retrieval
- Code Intelligence

---

### Agent

进入 Agent 阶段后再研究：

mini-SWE-agent / SWE-agent
OpenHands 等

重点研究：

- Agent Loop
- Tool Interface
- Repository Navigation
- File Read
- Search
- Edit
- Test
- Observation
- Sandbox

不是复制整个框架。

---

### Evaluation

进入 Evaluation 阶段再研究：

SWE-bench 等成熟 benchmark。

重点学习：

- Dataset
- Task
- Ground Truth
- Execution Environment
- Pass / Fail
- Reproducibility

---

## 开源项目研究原则

只读取解决当前问题所需要的：

README
Architecture
关键模块
相关实现

不要为了“学习开源”花几天读几十万行源码。

---

# 八、技术栈基本方向

Frontend：

TypeScript
React

Backend：

Python
FastAPI

Database：

PostgreSQL
pgvector

AI：

LLM API
Embedding API

Parsing：

前期简单 parser
逐渐升级 Tree-sitter 等结构化解析方案

以后按需要加入：

Redis
Docker
OpenTelemetry
GitHub API / MCP

是否增加其他技术，由实际工程需求决定。

不要提前预埋所有未来技术。

---

# 九、项目生命周期

整个 RepoPilot 按以下版本演进。

---

# Stage 0 — Project Inception

目的：

正式立项，而不是马上写 RAG。

完成：

项目 Scope
Architecture Boundary
Repository Structure
Development Environment
Git Repository
AGENTS.md
基本 README
Environment Variables
React
FastAPI
PostgreSQL
pgvector
Migration
Testing Foundation

建立最小：

React
→ HTTP
→ FastAPI
→ PostgreSQL

闭环。

同时确定：

哪些功能属于当前版本。

哪些明确不属于当前版本。

---

# V1 — Codebase RAG

这是现在立即开发的版本。

目标：

建立一套真正可 Debug、可引用源码的 Codebase RAG。

完整 Index Pipeline：

Repository
→ Snapshot
→ File Scanner
→ File Filter
→ Parser
→ Code-aware Chunker
→ Embedding
→ PostgreSQL + pgvector
→ Index

完整 Query Pipeline：

Question
→ Query Embedding
→ Retrieval
→ Relevant Chunks
→ Context Builder
→ LLM
→ Answer
→ Citation

前端必须可以看到 Retrieval Evidence。

V1 Milestones：

M0 Foundation

M1 Repository Ingestion

M2 Code-aware Chunking

M3 Embedding + Vector Index

M4 Retrieval Engine

M5 RAG Generation + Citation

M6 React Product UI

M7 Retrieval Quality Improvement

---

# V1 的重要设计

Repository 必须有：

Repository Snapshot

因为代码会变化。

以后 GitHub 接入以后 Snapshot 可以对应：

Commit SHA。

---

File Scanner 必须过滤：

.git
node\_modules
dist
build
.venv
binary
generated files
large files
minified files

敏感文件默认排除：

.env
\*.pem
\*.key
credentials
secrets

---

第一阶段主要支持：

Python
TypeScript
JavaScript
TSX
JSX
Markdown

不要一开始承诺所有语言。

---

Chunking 采用：

代码语义边界
\+
大小约束

优先：

class
function
method
Markdown heading

但：

超大 Function 允许继续切分。

非常小的 Symbol 后续允许组合。

Chunk metadata 至少考虑：

repository
snapshot
file path
language
chunk type
symbol name
qualified name
parent symbol
start line
end line
content hash
chunking version

区分：

raw\_content

和：

embedding\_content

允许 Embedding Content 加入：

File Path
Symbol
Type

等结构上下文。

---

V1 pgvector 首先使用：

Exact Vector Search

不要因为“高级”一开始就使用 HNSW。

以后数据规模真的需要时再实验 ANN。

---

Retrieval 必须作为独立模块存在：

Question
→ Retriever
→ Chunks

Retriever 不负责生成 Answer。

必须能够单独 Debug。

---

Retrieval Debug UI 至少展示：

Query
Top-K
Score / Distance
File Path
Symbol
Line Range
Chunk Content

---

Citation 不允许 LLM 自己编文件路径。

Retriever 提供真实 Chunk ID。

LLM 只能引用这些 Evidence ID。

Backend 再把 ID 映射到：

真实路径
Symbol
Line Range
Code

---

Context Builder 独立存在。

负责：

Chunk formatting
排序
去重
Token Budget
Citation ID

不能简单使用：

join(chunks)

完成所有工作。

---

Prompt 必须把 Repository Content 当作：

Untrusted Data

而不是 instruction。

为后面防止 Prompt Injection 建立正确边界。

---

V1 后半段建立 Retrieval baseline。

逐步比较：

Fixed Chunk
vs
Code-aware Chunk

Vector-only
vs
Hybrid Retrieval

Hybrid 可以结合：

Vector Semantic Search
\+
Lexical / Symbol Search

但必须先有 Vector baseline。

---

# V2 — Code Intelligence

V1 解决：

“语义上哪些代码相关？”

V2 开始解决：

“代码结构到底是什么？”

逐渐加入：

AST / Syntax Tree
Symbol Index
Definition
Reference
Import Relation
Function / Class Metadata
Repository Structure

必要时使用 Tree-sitter 等成熟 parser。

目标：

让 RepoPilot 从单纯：

Semantic Code Search

升级成：

Code-aware Retrieval。

这阶段研究：

Vector Retrieval
Lexical Retrieval
Symbol Retrieval
Structural Retrieval

如何组合。

不要直接承诺完整精确 Call Graph。

逐步实验。

---

# V3 — Repository Agent

学完 Agent 后进入。

第一版 Agent：

Read-only Agent。

它只能：

list\_files
search\_code
search\_symbol
read\_file
retrieve\_context

Agent 根据用户 Issue：

思考下一步需要什么信息
→ 调 Tool
→ 查看 Observation
→ 再决定下一步

目标：

理解真正的：

Agent Loop。

不要上 Multi-Agent。

---

随后升级：

Issue Analysis Agent

完成：

Issue
→ Inspect Repository
→ Search
→ Read
→ Analyze
→ Produce Resolution Plan

此阶段仍然可以不修改代码。

---

# V4 — Issue Resolution Agent

在 Read-only Agent 稳定后再开放：

edit\_file
apply\_patch
run\_tests

流程：

Issue
→ Analyze
→ Plan
→ Modify
→ Test
→ Observe Failure
→ Modify Again
→ Verify

这里开始接近真正 Software Engineering Agent。

重要：

任何第三方 Repository 的代码执行不得直接运行在宿主机。

需要逐步引入：

Docker / Sandbox

并限制：

文件系统
Command
Execution Time
Network
Secrets

---

# V5 — MCP + GitHub

进入 MCP 学习阶段后再做。

首先理解：

MCP 到底解决什么问题。

不要为了简历硬加 MCP。

目标：

让 RepoPilot 的 Agent 可以通过标准 Tool Interface 接入外部系统。

优先：

GitHub。

逐渐支持：

读取 Repository
读取 Issue
读取 PR
获取 Branch / Commit 信息
后续创建 Branch / PR

最终：

GitHub Issue
↓
RepoPilot Agent
↓
Repository Investigation
↓
Patch
↓
Tests
↓
GitHub PR

实施 MCP 时必须重新查询当时最新官方 specification，不依赖过时教程。

---

# V6 — Evaluation

Evaluation 不是项目最后“测一下”。

从 V1 开始就不断积累：

Test Repository
Golden Questions
Expected Files
Expected Symbols
Expected Chunks

但直到 Evaluation 阶段才建设正式体系。

---

## Retrieval Evaluation

建立 Dataset：

Query
Expected Evidence

指标可以研究：

Hit\@K
Recall\@K
MRR

比较：

Chunking Strategy
Vector Model
Top-K
Threshold
Hybrid Retrieval
Symbol Retrieval
Structural Retrieval

所有性能提升必须有真实实验。

禁止编数字。

---

## RAG Evaluation

评估：

Evidence 是否正确
Citation 是否正确
Answer 是否 Grounded
是否出现 Unsupported Claims

---

## Agent Evaluation

构建真实 Issue Tasks。

记录：

Task Success Rate
Patch Apply Success
Test Pass Rate
Tool Steps
Token Usage
Latency
Cost

必要时参考：

SWE-bench

的可复现测试思想。

不要求 RepoPilot 去刷完整 SWE-bench leaderboard。

---

# V7 — Production Engineering

只有核心 AI 能力稳定后才进入。

逐渐加入真正需要的：

Authentication
Users
Repository Ownership
Job Queue
Redis
Caching
Async Indexing
Retry
Timeout
Rate Limiting
Structured Logging
Tracing
Metrics
Error Tracking
Configuration Management
Docker
CI
Deployment
Database Backup / Migration

Observability 应该能够追踪：

Request

→ Retrieval

→ LLM Call

→ Tool Call

→ Agent Step

而不是只打印：

print("error")

---

# Production Optimization

最后开始测量真实：

Indexing Time
Retrieval Latency
LLM Latency
Agent Runtime
Token Usage
Cost
Cache Hit Rate
Failure Rate

延迟至少考虑：

P50
P95

只有测量以后才做优化。

禁止先优化假想瓶颈。

---

# V8 — Final Product & Portfolio Release

到这里完成 RepoPilot 1.0。

最终 Repository 必须具有：

完整 GitHub Repository

高质量 README

Architecture Diagram

Data Flow Diagram

Online Demo

Demo Video

Evaluation Dataset

Evaluation Report

真实 Retrieval 指标

真实 Agent 指标

真实 Latency / Cost 数据

测试

CI

Docker

Deployment

版本演进记录

安全边界说明

项目 Limitations

---

# 十、最终 UI 方向

RepoPilot 不要长成普通聊天机器人。

长期 UI 可以采用：

左：

Repository / File Tree

中：

Chat / Agent Task

右：

Evidence / Retrieval / Agent Trace

用户点击 Citation：

直接显示真实文件：

File Path
Symbol
Line Range
Source Code

Agent Task 页面还可以显示：

Plan
Tool Call
Observation
Patch
Test Result

让产品视觉本身就能展示：

“这个 AI 为什么得到这个结论。”

---

# 十一、测试原则

从项目第一天开始测试。

至少分：

Unit Test

用于：

File Filter
Parser
Chunker
Utilities

Integration Test

用于：

File
→ Chunk
→ Embedding
→ DB
→ Retrieval

API Test

用于：

Repository API
Index API
Retrieve API
Chat API

后期增加：

Agent Integration Test
Evaluation Test
End-to-End Test

项目里长期维护一个小型：

Golden Repository / Sample Repository

它的代码结构和答案都是我们明确知道的。

用它保证系统迭代不会悄悄破坏旧功能。

---

# 十二、Git 工作方式

项目从第一天进入 GitHub。

保持：

小而有意义的 Commit。

不要：

一天一个“update”。

Commit 应表达工程变化，例如：

feat: add repository ingestion pipeline

feat: implement structure-aware Python chunking

test: add retrieval integration cases

fix: prevent cross-snapshot retrieval

每个 Milestone 完成后形成一个明确稳定节点。

必要时使用版本 Tag。

Git 历史最终应该能看出：

RepoPilot 是如何从：

Empty Project

逐渐成长为：

Production AI Agent System。

---

# 十三、架构演进原则

每次准备加入新技术前必须回答：

它解决什么真实问题？

为什么现在需要？

不用它会怎样？

有没有更简单的方案？

增加的复杂度值不值得？

如果回答不了：

暂时不加入。

---

任何未来功能都遵守：

先 Baseline
→ 找 Bad Case
→ 提出 Improvement
→ 实现
→ Evaluation
→ 决定是否保留

例如：

Vector Retrieval

出现 Symbol 查询问题以后：

才增加 Lexical Retrieval。

而不是一开始看到“Hybrid Search 很高级”就加入。

---

# 十四、安全原则

Code Agent 的安全问题必须随着能力增强同步升级。

重点关注：

Repository Secrets

Prompt Injection

Path Traversal

ZIP Bomb

Malicious Repository

Arbitrary Command Execution

Shell Injection

Agent Tool Permission

GitHub Token Permission

Network Access

Sandbox Escape

V1 不需要解决所有生产安全问题。

但不能在设计上完全忽略。

尤其 Agent 开始运行 Repository Code 以后：

必须使用隔离环境。

---

# 十五、学习原则

这是一个求职项目，不是一门大学课程。

遇到一个新概念时：

只学习完成当前工程任务所需要的知识。

例如需要 Tree-sitter：

先理解：

Parser
Syntax Tree
Node
Range
Query

足够实现当前功能即可。

不要暂停项目两周“系统学习编译原理”。

需要 Docker：

先理解：

Image
Container
Volume
Network
Command
Isolation

够 RepoPilot 使用即可。

始终采用：

Project Driven Learning。

---

# 十六、每个 Milestone 的教学格式

以后每进入一个 Milestone，你必须先告诉我：

1. 这一阶段解决什么问题；
2. 为什么现在做；
3. 当前系统存在什么缺口；
4. 做完以后架构发生什么变化；
5. 新增 / 修改哪些模块；
6. 每个模块职责；
7. Request / Data Flow；
8. 核心接口输入输出；
9. 最小实现步骤；
10. 给 Codex 的任务；
11. 如何测试；
12. 验收标准；
13. 常见 Bug 从哪里排查；
14. 我必须能解释什么；
15. 面试官可能怎么问。

完成验收前：

不要随意进入下一阶段。

---

# 十七、我的学习验收

我不需要记住所有代码。

但是每个核心模块完成后，我必须至少能够回答：

它是什么？

为什么存在？

输入是什么？

输出是什么？

谁调用它？

它调用谁？

数据去了哪里？

失败会发生在哪里？

为什么不用另一种设计？

如果出现 Bug 应该从哪里开始查？

如果答不上来：

你需要重新给我建立系统模型。

---

# 十八、项目文档原则

不要产生大量为了“正规”而存在的文档。

长期只维护真正有价值的：

README.md

AGENTS.md

docs/architecture.md

docs/roadmap.md

docs/evaluation.md

必要的重要 ADR / Design Decision

以及最终 Demo 和 Evaluation Report。

文档必须随项目变化更新。

---

# 十九、求职价值判断

每增加一个功能都要问：

它是否证明了一项招聘方真正需要的能力？

例如：

Code-aware Chunking

证明：

RAG Engineering。

Retrieval Debug

证明：

AI System Debugging。

Evaluation

证明：

不是靠 Demo 感觉调 AI。

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

如果一个功能无法增加产品能力，也无法增加工程证明力：

不要做。

---

# 二十、最终简历标准

最后不能写：

“基于 LangChain 实现 RAG，准确率显著提高。”

必须能够写出有证据的内容，例如：

设计并实现真实代码仓库的结构感知 RAG pipeline，通过 AST / symbol metadata、hybrid retrieval 和 source-level citation 支持 repository-level code QA。

构建可观测 Retrieval Pipeline，对不同 chunking / retrieval strategies 建立评测数据集并使用真实指标进行比较。

构建 Tool-Calling Code Agent，实现 repository search、file inspection、patch generation 与 sandboxed test execution 的多步 Issue Resolution Loop。

通过 MCP 接入 GitHub，实现 Issue → Repository Analysis → Patch → Test → PR 的完整工程流程。

具体数字只能使用 RepoPilot 实际测量的数据。

---

# 二十一、最终面试目标

最终我应该能够不用打开代码，从头讲清：

为什么做 RepoPilot

用户问题是什么

系统架构是什么

Repository 如何 Index

为什么需要 Snapshot

如何 Chunk Code

为什么普通 Text Chunking 不够

Embedding 如何工作

pgvector 如何 Retrieval

Vector Search 的局限

为什么加入 Lexical / Symbol Retrieval

Citation 怎么保证真实

如何区分 Retrieval Error 和 Generation Error

Agent 如何调用 Tool

Agent Loop 是什么

为什么不用 Multi-Agent

MCP 在系统里解决什么问题

Agent 如何修改代码

如何安全运行测试

如何设计 Evaluation

指标如何计算

系统哪里最慢

哪里最贵

哪里最容易失败

如何监控

有哪些 Limitations

如果重新设计会改什么

只有做到这里：

RepoPilot 才算真正成为我的简历项目。

---

# 二十二、执行原则

从现在开始：

不要再继续无限扩展设计。

整个长期方向已经确定。

后续允许根据真实开发问题调整架构，但不能频繁推翻重做。

第一阶段正式开始：

# Stage 0 — Project Inception

你现在首先作为 Tech Lead：

1. 检查这份项目章程是否存在必须立即修改的问题；
2. 如果没有重大问题，冻结长期 Scope；
3. 设计 Stage 0；
4. 给出 RepoPilot 第一版 Repository Structure；
5. 定义开发环境；
6. 定义 Git / AGENTS.md / 配置管理方式；
7. 给出第一个 Codex Coding Task。

不要提前实现 V1 后面的功能。

我们从第一步正式开始开发。