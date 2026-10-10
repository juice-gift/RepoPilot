# RepoPilot V2 — Code Intelligence Version Goal

## 0. 任务性质

这是一个 **Version-level Autonomous Goal（版本级自主目标）**。

你可以在本 Version 内：

- 检查当前 Repository；
- 创建并维护 `docs/tasks/v2-plan.md`；
- 自主拆解 Milestone；
- 实现；
- 编写测试；
- 执行验证；
- 修复失败；
- Review Diff；
- 创建有意义的 Git Commit；
- 在满足继续条件时进入下一个 V2 Milestone。

不需要在正常 Milestone 之间等待人工批准。

但是：

- 不得跨越本 Goal 定义的 V2 Architecture Boundary；
- 不得自动进入 V3；
- 遇到 `AGENTS.md` 定义的 Escalation Condition 时必须停止并报告。

---

# 1. Source of Truth

开始任何修改之前，必须按优先级读取并核对：

1. 根目录 `AGENTS.md`
2. `docs/PROJECT.md`
3. 本 V2 Version Goal
4. `docs/tasks/v1-plan.md`
5. 当前 Git 状态与 Git History
6. 当前实际代码
7. 当前测试、Migration 与 Evaluation 状态

不要根据聊天记录或历史假设推断当前实现。

如果：

- 文档与代码冲突；
- 文档之间发生影响架构或 Scope 的实质冲突；
- 当前 Git 状态表明 V2 已存在未说明实现；
- 需要改变冻结的架构或关键技术选择；

必须停止并报告，不得自行猜测。

---

# 2. 当前已确认基线

当前 RepoPilot 已完成：

- Stage 0 — Project Inception
- V1 — Codebase RAG
- V1 M0–M7

当前停在：

```text
V1 / V2 Version Boundary
```

V1 当前已经建立：

```text
Repository
→ Snapshot
→ Snapshot File
→ Code-aware Chunking
→ Embedding
→ PostgreSQL / pgvector
→ Vector / Hybrid Retrieval
→ Context Builder
→ Grounded Generation
→ Backend-resolved Citation
→ Evidence-first React UI
→ Retrieval Evaluation
```

V1 已经存在一定结构信息，但主要服务于 Chunking：

- Python 使用标准库 AST 获取函数 / 类 / 方法边界；
- JS / TS / JSX / TSX 使用轻量 declaration + brace-aware parsing；
- CodeChunk 已保存部分：
  - `symbol_name`
  - `qualified_name`
  - `parent_symbol`
  - source line range

当前尚不存在独立 Repository-level：

- Symbol Index
- Definition Index
- Reference Index
- Import Relation Index
- Symbol Retrieval
- Structural Retrieval

V2 不得重新实现已经稳定完成的 V1 能力，除非发现有具体且可证明的问题。

---

# 3. V2 Goal

将 RepoPilot 从：

> 可以通过 Vector / Hybrid Retrieval 找到“语义上相关代码”的 Codebase RAG

升级为：

> 可以确定性理解并查询 Repository 中重要代码结构的 Code Intelligence System。

V2 最终必须能够回答一类不应该依赖 Embedding 或 LLM 猜测的问题，例如：

```text
仓库里有哪些重要 Symbol？

Symbol X 定义在哪里？

某个文件中定义了哪些 Symbol？

文件 A import 了哪些本地模块？

哪些文件 import 了文件 B？

某个 Symbol 在哪些位置被明确引用？

某个 Reference 是否能够可靠解析到具体 Definition？
```

V2 必须建立：

```text
Repository Snapshot
→ File
→ Symbol
→ Definition
→ Reference
→ Import Relation
```

形成可测试、可 Debug、可 Evaluation 的确定性代码导航层。

这套能力将在未来 V3 被 Repository Agent 使用。

但 V2 不实现 Agent。

---

# 4. 核心原则

## 4.1 Baseline-First

所有核心改进继续遵守：

```text
Baseline
→ Observe Problems
→ Improvement
→ Evaluation
→ Keep / Remove
```

禁止因为某种技术看起来先进就直接加入。

尤其是：

- Symbol Retrieval
- Structural Retrieval
- Retrieval Fusion
- Ranking Weight
- Reference Resolution Enhancement

必须建立 Baseline、观察真实 Bad Case 后再决定是否保留。

---

## 4.2 Deterministic First

以下结构能力必须优先依赖确定性程序逻辑：

- Symbol
- Definition
- Import
- Reference
- Source Location
- Repository Structure

不得使用 LLM 来猜：

- Symbol 属于哪个文件；
- Definition 在哪里；
- 某 Reference 指向哪个 Symbol；
- 某 Import 的真实 Source Location。

LLM 可以在未来消费这些数据。

不能成为这些数据真实性的来源。

---

## 4.3 Snapshot Scoped

所有 Code Intelligence 数据必须属于明确的：

```text
RepositorySnapshot
```

禁止：

```text
Snapshot A 的源码
+
Snapshot B 的 Symbol / Reference / Import
```

混合返回。

Snapshot Isolation 必须通过自动化测试验证。

---

# 5. Architecture Boundary

V2 从已经持久化的 V1 `SnapshotFile.content` 开始。

推荐整体数据流：

```text
RepositorySnapshot
        ↓
SnapshotFile.content
        ↓
Language Analyzer
        ↓
Syntax Structure
        ↓
Structural Extraction
├── Symbol Definitions
├── Import Occurrences
└── Reference Occurrences
        ↓
Conservative Resolver
        ↓
Snapshot-scoped Structural Index
├── CodeSymbol
├── CodeReference
└── ImportRelation
        ↓
Code Intelligence Service
        ↓
Typed Read-only API
```

不得将 Parser-specific Tree Node 大量泄漏到系统其他层。

Parser 的职责是：

```text
Source Code
→ Syntax Structure
```

RepoPilot 自己的结构模型才是：

```text
CodeSymbol
CodeReference
ImportRelation
```

---

# 6. AST / Syntax Tree

V2 需要真正的语法结构分析。

## AST / Syntax Tree

含义：

> 将源代码从普通字符串解析成带有函数、类、调用、Import 等语法结构的树形表示。

在 RepoPilot 中的作用：

```text
Source Code
→ 判断什么是真正的代码结构
→ 提取 Definition / Reference / Import
```

AST / Syntax Tree 是解析过程中的工具。

默认不要将完整 Syntax Tree 持久化进 PostgreSQL。

数据库应主要保存 RepoPilot 真正需要查询的结构信息。

---

# 7. Language Analyzer

建立一个足够简单、职责明确的 Language Analyzer Boundary。

推荐 Baseline：

```text
Python
→ Python standard library ast

JavaScript / JSX
→ Tree-sitter JavaScript

TypeScript / TSX
→ Tree-sitter TypeScript
```

Markdown 可以继续参与 V1 RAG，但 V2 不要求建立 Code Intelligence Index。

---

# 8. Tree-sitter

允许在 V2 正式引入 Tree-sitter。

它当前解决的真实问题是：

> V1 对 JavaScript / TypeScript family 的 regex + brace-aware 实现足够支持 Chunking，但不足以作为可靠的 Code Intelligence Parser。

不要为了“技术统一”把已经工作的 Python AST 强行全部改成 Tree-sitter。

如果没有真实需求，不要重写稳定的 V1 Chunker。

Tree-sitter 及必要语言 Grammar 应保持最小依赖集合。

如果增加 Dependency：

Completion Report 中必须明确：

- Dependency 名称；
- 为什么需要；
- 解决什么具体问题。

---

# 9. Structural Index

建立版本化、Snapshot-scoped、可重复生成的 Structural Index。

同一个：

```text
Snapshot
+
Code Intelligence Version
```

重复执行结构索引时：

- 不得无限重复插入数据；
- 结果必须等价；
- 必须具有 Idempotency。

Structural Index 必须能够从已经持久化的 `SnapshotFile.content` 重建。

不要依赖当前 Working Directory 中可能已经变化的源码。

---

# 10. Symbol Index

## Symbol

Symbol 指 Repository 中有意义的命名代码实体，例如：

```text
UserService
verify_token
calculate_total
AuthMiddleware.check
ReportStatus
```

V2 必须建立独立的：

```text
CodeSymbol
```

不能继续只依赖 CodeChunk 上的 `symbol_name`。

---

## Python Baseline

至少考虑：

- function
- async function
- class
- method
- 有实际导航价值的 module-level named definition

---

## JavaScript / TypeScript Family Baseline

至少考虑：

- function
- class
- method
- top-level named variable
- named arrow function
- TypeScript interface
- TypeScript type alias
- TypeScript enum

不要默认把所有以下对象都建立 Repository-level Symbol：

- local variable
- loop variable
- function parameter
- every object property
- every syntax node

除非真实 Evaluation 表明需要。

---

## CodeSymbol Metadata

根据实际实现至少应能够表达：

- snapshot
- source file
- language
- symbol kind
- name
- qualified name
- parent symbol
- start line
- end line
- structural-index version

具体 Schema 由 Repository 实际状态决定。

不要为了“未来可能需要”加入大量无使用方字段。

---

# 11. Definition

## Definition

含义：

> Symbol 真正被声明或定义的位置。

例如：

```python
def verify_token(...):
```

这里是 `verify_token` 的 Definition。

V2 必须提供确定性 Definition Lookup：

```text
Symbol
→ Snapshot File
→ Start Line
→ End Line
```

Definition Location 必须来自 Parser / Structural Index。

不得由 LLM 生成。

---

# 12. Repository Structure

利用现有 Snapshot File 数据提供可查询 Repository Structure。

至少能够：

```text
Repository Snapshot
→ Files

File
→ Symbols
```

如果现有 `SnapshotFile` 已足够表达文件结构：

不要为了 V2 新增重复 Directory Tree Database Model。

只有出现真实需求时才增加新的持久化模型。

---

# 13. Import Relation

## Import Relation

含义：

> 某个 Source File 静态依赖另一个 Module / File 的关系。

例如：

```python
from auth.service import verify_token
```

应能够形成类似：

```text
api/routes.py
→ imports
auth/service.py
```

V2 必须支持 Import Relation。

---

## Baseline Scope

优先支持：

### Python

- `import x`
- `from x import y`

### JavaScript / TypeScript Family

- static ECMAScript import
- repository-local relative imports

对于能够确定的 Repository-local Import：

解析到实际 target file。

同时保留必要的原始 import 信息。

---

## Import Metadata

根据实际需要可包括：

- source file
- imported module text
- imported symbol
- alias
- source location
- resolved target file
- external / unresolved status

---

## Import Navigation

至少支持两个方向：

```text
File
→ imports
→ dependencies
```

以及：

```text
File
← imported by
← dependents
```

---

## 当前禁止提前解决

V2 Baseline 不要求完整支持：

- dynamic import
- runtime module loading
- arbitrary module loader
- framework dependency injection
- complex monorepo workspace semantics
- complete tsconfig alias resolution

如果 Golden Repository 或真实 RepoPilot Repository 暴露具体问题：

再按 Baseline-First 处理。

---

# 14. Reference

## Reference

含义：

> 某个位置对一个 Symbol 的使用。

例如：

```python
verify_token(token)
```

这里的 `verify_token` 是一个 Reference。

V2 应建立：

```text
CodeReference
```

但 Reference Resolution 必须保守。

---

# 15. Conservative Resolution

## Conservative Resolution

含义：

> 只有拥有足够确定证据时，才将某个 Reference 连接到具体 CodeSymbol。

Reference 必须能够明确区分：

```text
resolved
unresolved
ambiguous
```

绝对禁止：

```text
找不到确定 Target
→ 猜一个最像的 Symbol
→ 当成真实关系
```

False Confident Resolution 比 Unresolved 更严重。

---

## Baseline Resolution Priority

优先处理真正可以可靠解析的情况，例如：

- same-file unambiguous symbol
- lexical scope 内可以确定的 definition
- unambiguous repository-local imported symbol
- 可以确定的 module-level reference

遇到以下情况可以明确保持 unresolved / ambiguous：

- complex dynamic dispatch
- runtime monkey patching
- difficult type-dependent method resolution
- framework magic
- ambiguous same-name candidates

V2 不追求 Reference Recall 100%。

优先保证 Precision。

---

# 16. Symbol Retrieval

增加独立：

```text
Symbol Retrieval
```

它必须：

- 不需要 Embedding；
- 不需要 LLM；
- Snapshot scoped；
- independently debuggable。

Baseline 至少支持：

- exact name
- qualified name
- normalized symbol name

如果需要：

- prefix
- fuzzy matching
- ranking

必须先观察 Evaluation Bad Case。

不要提前加入复杂 Fuzzy Search。

---

# 17. Structural Retrieval

建立独立的 Structural Navigation / Retrieval 能力。

至少应能够实现等价于：

```text
list_files
list_symbols(file)
search_symbol(query)
get_definition(symbol)
find_references(symbol)
get_imports(file)
get_importers(file)
```

这里描述的是：

> Code Intelligence Capability

不是 Agent Tool System。

函数、Service 或 HTTP API 的最终命名由当前 Repository 架构决定。

不要为了迎合上述名称创建不必要抽象。

---

# 18. Retrieval Integration

V1 当前：

```text
Vector Retrieval
Hybrid Retrieval
```

必须继续保持稳定 Baseline。

不要一开始就修改 Retriever 为：

```text
vector
+
lexical
+
symbol
+
structural
```

也不要预先发明 Ranking Weight。

正确流程：

```text
V1 Baseline
→ V2 Structural Query Dataset
→ Observe Bad Cases
→ Symbol / Structural Capability
→ Evaluation
→ 决定是否整合
```

如果最终证明：

```text
Structural Retrieval
```

作为独立 Navigation System 比强行混进 General Retriever 更合理：

允许保持独立。

**V2 Completion 不要求必须修改现有 `/api/retrieve` Ranking。**

只有当真实指标证明融合能够提高结果，并且不破坏 V1 Regression 时才保留融合方案。

---

# 19. Evaluation

V2 必须建立独立的：

```text
Structural Evaluation Dataset
```

现有 V1 Golden Dataset 必须保留并继续作为 Regression Dataset。

禁止修改历史 Ground Truth 只是为了让新实现得到更漂亮指标。

---

# 20. V2 Golden Repository

可以扩展或新增一个小型、人工可验证的 Structural Golden Repository。

数据必须能够明确知道正确答案。

至少覆盖：

- exact symbol definition
- duplicate symbol names
- qualified-name distinction
- same-file reference
- cross-file imported reference
- unresolved reference
- ambiguous reference
- Python imports
- JavaScript / TypeScript imports
- importers
- cross-file dependency
- snapshot isolation

Golden Repository 应保持：

- 小；
- 明确；
- 可人工检查；
- 可重复；
- 不依赖外部服务。

不要为了“更真实”建立巨大测试仓库。

---

# 21. Evaluation Metrics

不同能力使用适合自己的指标。

## Symbol Retrieval

可以使用：

- Hit@K
- MRR@K

---

## Definition

评估：

```text
Expected Definition
vs
Actual Definition
```

至少检查：

- file path
- symbol
- source location

---

## Import Relation

评估：

- Precision
- Recall

---

## Reference Resolution

评估：

- Precision
- Recall
- resolved count
- unresolved count
- ambiguous count

优先避免 False Positive。

---

## Regression

必须重新运行 V1 Frozen Retrieval Evaluation。

V2 不得让已完成 V1 的：

- indexing
- vector retrieval
- hybrid retrieval
- context builder
- generation
- citation

因为无关结构修改而发生回退。

只允许记录真实测试数字。

禁止编造。

---

# 22. Expected Architecture

预计最终形成类似：

```text
apps/api/src/repopilot/

existing V1 modules
├── ingestion/
├── chunking/
├── embeddings/
├── indexing/
├── retrieval/
├── rag/
└── evaluation/

V2 responsibilities
└── code intelligence related modules
    ├── language analysis
    ├── structural extraction
    ├── symbol indexing
    ├── import extraction / resolution
    ├── reference extraction / resolution
    └── structural query/navigation
```

具体目录和模块名称：

由检查实际 Repository 后决定。

不要为了让架构“看起来正规”创建：

```text
domain/
services/
repositories/
managers/
engines/
providers/
adapters/
```

等大量没有真实职责的抽象层。

遵守 `AGENTS.md`：

> Concrete responsibility 才允许创建 abstraction。

HTTP Route 必须保持 thin。

Parsing / Extraction / Resolution / Persistence / Query 应在有真实职责时保持可独立测试。

---

# 23. Database

所有 Schema Change 必须通过 Alembic。

预计可能增加类似：

```text
code_symbols
code_references
import_relations
```

但最终 Schema 必须根据实际数据流设计。

不要机械照抄名称。

结构数据必须满足：

- Snapshot scoped
- Referential Integrity
- Reproducible
- Idempotent indexing
- Source locations explicit
- Clean migration
- Snapshot deletion 时能够正确清理
- 不依赖 manual database operation

禁止手工修改数据库作为完成条件。

---

# 24. UI Boundary

V2 重点是：

> Backend Code Intelligence correctness + Evaluation

不是 UI 重构。

如果为了 Debug / Demo 有真实价值：

允许加入最小可检查 UI，例如：

- 搜索 Symbol；
- 查看 Definition；
- 查看 Reference；
- 查看 imports / importers。

但是禁止把 V2 做成：

- IDE
- Source Editor
- VS Code Clone
- Code Modification UI
- Agent UI
- GitHub UI

如果后端 API + Evaluation 已能充分验证 V2：

复杂前端不是 Version Completion 必需条件。

---

# 25. Tests

## Unit Tests

至少覆盖重要的：

- Python Symbol Extraction
- JavaScript / TypeScript Symbol Extraction
- qualified name
- parent relationship
- source range
- Import Extraction
- Reference Extraction
- Conservative Resolution
- resolved
- unresolved
- ambiguous
- deterministic output
- Symbol Lookup

---

## Integration Tests

覆盖完整链路：

```text
Repository Snapshot
→ Snapshot Files
→ Structural Analysis
→ Structural Index
→ PostgreSQL
→ Structural Query
```

至少证明：

- Structural Index idempotency
- Snapshot Isolation
- Cross-file Import
- Importer Reverse Lookup
- Cross-file resolved Reference
- unresolved behavior
- ambiguous behavior
- database persistence

---

## API Tests

如果新增 HTTP API：

必须验证：

- typed request / response contract
- repository / snapshot scoping
- missing resource
- invalid input
- empty result
- ambiguity behavior

---

## Migration Tests

如果新增 Migration：

验证：

- V1 current head → V2 head
- `alembic check`
- clean database migration when practical
- application ORM 与 migration schema 一致

---

## Regression

至少必须保证：

- Existing backend tests pass
- Existing live database tests pass when required
- Ruff pass
- frontend production build pass
- existing V1 evaluation remains reproducible

---

# 26. Acceptance Criteria

只有全部满足以下条件，V2 才可以声明完成。

### A. Structural Parsing

1. Python 能够通过批准的 Analyzer 提取 V2 需要的结构信息。
2. JS / TS family 能够通过可靠 Syntax Tree Parser 提取 V2 需要的结构信息。
3. Parser Failure 不得静默制造虚假结构。

### B. Structural Index

4. 存在 Snapshot-scoped Structural Index。
5. Index 可重复生成。
6. 同版本重复 Index 具有 Idempotency。
7. Snapshot Isolation 有自动化测试证明。

### C. Symbol / Definition

8. 支持的 Repository-level Symbol 可以独立查询。
9. Definition Location 来自真实 Structural Index。
10. 可以从 File 查询 Symbols。
11. 可以从 Symbol 导航到 Definition。

### D. Import

12. 支持范围内的 Static Import 可以提取。
13. Repository-local Import 在能够确定时解析到 Target File。
14. 支持 imports 查询。
15. 支持 importers 查询。

### E. Reference

16. Reference 可以提取。
17. Reference Resolution 能明确区分：
    - resolved
    - unresolved
    - ambiguous
18. 不存在将不确定关系静默报告成确定关系的行为。

### F. Retrieval

19. Symbol Retrieval 不依赖 Embedding / LLM。
20. Structural Navigation 可以独立调用和 Debug。
21. 如果修改现有 General Retriever，必须有 Evaluation 数据证明收益。

### G. Evaluation

22. 存在冻结的 V2 Structural Dataset。
23. Ground Truth 可人工检查。
24. 记录真实 Symbol / Definition / Import / Reference Evaluation。
25. 原 V1 Frozen Dataset 继续作为 Regression Dataset。

### H. Engineering

26. Relevant backend tests pass。
27. Relevant live database tests pass。
28. Ruff pass。
29. Alembic validation pass。
30. Frontend production build pass。
31. Documentation 与真实实现一致。
32. 没有无用 Dependency。
33. 没有与 V2 无关的大规模 Refactor。

### I. Version Boundary

34. 没有实现 V3 Repository Agent。
35. 没有实现 Agent Loop。
36. 没有实现 MCP / GitHub。
37. 没有实现 Code Modification Agent。
38. 没有实现 Agent Test Execution。
39. 没有提前跨入后续 Version。

---

# 27. Forbidden Scope

V2 明确禁止实现或预埋：

- Complete Call Graph
- Control Flow Graph
- Data Flow Analysis
- Full Type Inference
- IDE-grade Semantic Analysis
- Language Server Platform
- 完整 LSP 集成
- Framework-specific semantic engine
- Neo4j
- Graph Database
- 为了关键词而加入 GraphRAG
- Agent Loop
- Tool-calling Repository Agent
- Issue Analysis Agent
- Issue Resolution Agent
- `edit_file`
- `apply_patch`
- Agent `run_tests`
- Repository Code Execution
- Agent Sandbox
- MCP
- GitHub Integration
- Issue / PR Integration
- Branch / Commit Automation
- Pull Request Creation
- Multi-Agent
- Authentication
- Redis
- Queue
- Production Deployment
- Kubernetes
- 无关的 V1 Rewrite
- Speculative V3 Directory / Interface / Placeholder

允许记录“某处存在函数调用 Reference”。

但不得声称：

> RepoPilot V2 已建立完整精确 Call Graph。

---

# 28. V3 Readiness Boundary

V2 最终应该提供足够可靠的 Code Navigation Primitive，使未来 V3 可以把它们包装为 Agent Tool，例如：

```text
list_files
search_symbol
get_definition
find_references
inspect_imports
inspect_importers
retrieve_context
```

但这里只是说明未来 Consumer。

V2 不得实现：

```text
LLM
→ Decide Tool
→ Tool Call
→ Observation
→ Decide Again
```

这个 Agent Loop 属于 V3。

不要提前为 V3 设计复杂 Tool Framework。

V3 应在自己的 Version Goal 中决定 Tool Interface。

---

# 29. 推荐执行顺序

以下只是推荐工程顺序。

可以根据实际 Repository 状态调整 Milestone，但不得改变 Version Scope。

```text
M0 — V2 Baseline / Repository Inspection
        ↓
M1 — Language Analysis + Structural Index Foundation
        ↓
M2 — Symbol + Definition
        ↓
M3 — Import Relations
        ↓
M4 — Conservative Reference Resolution
        ↓
M5 — Symbol / Structural Navigation
        ↓
M6 — Structural Evaluation + Optional Retrieval Experiment
        ↓
Final Validation
```

不要为了完全遵循这个顺序而做不合理修改。

真正的 Execution Plan 应在读取当前 Repository 后生成。

---

# 30. Execution Plan

开始 V2 后创建：

```text
docs/tasks/v2-plan.md
```

保持简洁。

至少记录：

- V2 Goal
- Milestones
- Current Milestone
- Completed Work
- Validation Results
- Important Decisions
- Dependencies Added
- Evaluation Results
- Blockers
- Remaining Work

不要复制整个 `PROJECT.md` 或本 Goal。

真正的系统状态仍然来自：

```text
Code
Tests
Git
```

---

# 31. Git Boundary

V2 应产生若干有意义的 Milestone Commit。

例如：

```text
feat: add structural code analysis foundation

feat: add snapshot-scoped symbol index

feat: index repository import relations

feat: add conservative symbol reference resolution

feat: expose structural code navigation

test: add code intelligence evaluation
```

Commit 名称根据真实实现决定。

禁止：

```text
update
changes
final
final2
fix stuff
```

不要把整个 V2 压成一个巨大 Commit。

不要重写无关 Git History。

---

# 32. Version Completion Verification

声明 V2 完成前，必须：

1. 重新阅读：
   - `AGENTS.md`
   - `docs/PROJECT.md`
   - 本 V2 Goal

2. 对每项 Acceptance Criteria 明确核对。

3. 执行所有 relevant：
   - backend tests
   - live database tests
   - Ruff
   - Alembic checks
   - frontend build
   - Structural Evaluation
   - V1 Retrieval Regression Evaluation

4. Review Final Diff：

检查：

- Scope Violation
- V3 Leakage
- Speculative Abstraction
- Unused Dependency
- Dead Code
- Duplicated Logic
- Unrelated Refactor
- Documentation Drift

5. 检查 Security Boundary。

6. 检查 Git History。

7. 更新：
   - README
   - PROJECT current state
   - AGENTS current stage
   - V2 execution plan
   - 必要 Evaluation Documentation

只更新真实发生变化的文档。

---

# 33. Completion Report

完成 V2 后输出明确 Completion Report。

包括：

## Files Changed

重要新增 / 修改文件。

## Implementation

V2 实现了什么。

## Architecture

新的：

```text
Source
→ Parser
→ Structural Extraction
→ Structural Index
→ Navigation
```

数据流是什么。

## Dependencies

新增 Dependency 及原因。

## Database

Migration 与 Schema Change。

## Evaluation

真实：

- Symbol
- Definition
- Import
- Reference

评估结果。

同时报告 V1 Regression Evaluation。

## Validation

只列实际执行过的 Command 与真实结果。

未执行的检查不能写成 PASS。

## Git

V2 Commit 列表。

## Remaining Issues

已知 Limitations。

特别说明：

- unresolved references
- ambiguous references
- unsupported language semantics

## Risks

真实维护 / Correctness 风险。

## Scope Check

明确说明是否出现：

- Agent
- MCP
- GitHub
- Code Modification
- Test Execution Agent
- Complete Call Graph

如果没有，明确写：

```text
No V3 or later-version functionality was introduced.
```

---

# 34. V2 Completion State

V2 完成后，RepoPilot 应同时拥有两条独立且清晰的 Repository Understanding Path。

## Semantic Path

```text
Question
→ Vector / Hybrid Retrieval
→ Relevant Code Evidence
→ Context Builder
→ Grounded Answer
→ Citation
```

## Structural Path

```text
Repository Snapshot
→ File
→ Symbol
→ Definition
→ Reference
→ Import Relation
→ Deterministic Navigation
```

V2 的核心成果不是：

> 加了 Tree-sitter。

而是：

> RepoPilot 已经能够基于真实 Repository Snapshot 建立可验证的 Code Structure Index，并提供不依赖 LLM 猜测的确定性代码导航能力。

---

# 35. Version Boundary

完成全部 V2 验证后：

```text
Final Validation
→ Completion Report
→ Commit
→ Stop
```

此时项目进入：

```text
V2 / V3 Version Boundary
```

不得自动开始：

```text
V3 — Repository Agent
```

V3 必须等待新的、明确批准的 Version Goal。