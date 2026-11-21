# SolidWorks MCP 通用 AI 工作协议

最后更新：2026-11-21

本文是 SolidWorks MCP 项目跨聊天、跨 AI、跨电脑接手工作的统一流程。它规定任务如何开始、执行、验证、收尾和交接。具体建模、工程图或验证细节继续由项目 Skill、能力矩阵和验收报告提供。

## 1. 强制约束

以下约束适用于 Codex、Claude、Cursor、DeepSeek 及其他 AI 工具。

- 源码目录固定为 `D:\Projects\SolidWorks-MCP`。
- 本机数据目录固定为 `D:\Projects\SolidWorks-MCP-Data`。
- `origin` 是个人 GitHub 仓库，地址为 `https://github.com/wuyeku/solidworks-automation-skill.git`。
- `upstream` 是作者仓库，地址为 `https://github.com/wzyn20051216/solidworks-automation-skill.git`。
- `upstream` 只允许 fetch。其 push URL 必须保持为 `DISABLED`。
- 未获得当前任务明确授权，不得 commit、push、reset、clean、rebase 或修改 remote。
- 不得修改 C 盘正式 MCP、Router、API Key、代理或 MCP 客户端配置，除非任务明确要求且用户已完成单独授权。
- 不得覆盖、移动或删除生产 CAD 文件。写入测试必须使用独立副本和独立输出目录。
- 根目录异常文件 `$null` 永远排除在源码、测试、文档和提交之外。不得删除、覆盖、忽略或提交。
- 单元测试、Schema 测试和静态检查不能替代 MCP 实际调用与 SolidWorks 2025 真机验收。
- 任何失败、缺失能力和人工复核项必须如实记录，不得用模拟结果或推断替代实际结果。

## 2. 阅读顺序

每个新任务开始后按以下顺序读取项目上下文。

1. `AGENTS.md`。
2. `docs/AI_WORKFLOW.md`。
3. `PROJECT_STATUS.md`。
4. `CHANGELOG.md` 最近的相关记录。
5. `docs/ARCHITECTURE.md`。
6. 与任务匹配的 `.agents/skills/*/SKILL.md` 或 `subskills/*/SKILL.md`。
7. 相关能力矩阵、验收报告和待修改源码。

不要从旧聊天中假设当前状态。聊天记录只能提供任务背景，以当前 Git 状态、项目文件和真机证据为准。

## 3. 新聊天接手流程

### 3.1 建立环境基线

首先确认工作目录和 Git 状态。

```powershell
Set-Location -LiteralPath 'D:\Projects\SolidWorks-MCP'
git branch --show-current
git rev-parse HEAD
git status --short --branch
git remote -v
git branch -vv
```

然后记录远端关系。

```powershell
git rev-list --left-right --count upstream/main...HEAD
git rev-list --left-right --count origin/main...HEAD
```

如果当前分支有远程跟踪，再检查与个人远程开发分支的差异。

```powershell
git rev-list --left-right --count '@{u}...HEAD'
```

### 3.2 核对项目约束

必须确认以下事实。

- 当前分支和 HEAD 与 `PROJECT_STATUS.md` 或用户给定基线一致，或差异已被用户说明。
- 不存在未知的已暂存修改。
- 所有非 `$null` 的工作区修改属于当前任务或已获用户授权。
- `$null` 仍为未跟踪状态，且未进入暂存区。
- `upstream` push URL 仍为 `DISABLED`。
- C 盘正式运行环境没有被当前任务修改。

任何一项不一致时，先报告差异并停止可能改变状态的步骤。

### 3.3 选择相关能力资料

- 开发工具和修复实现时，先读 `sw-mcp-development`。
- 离线或 SolidWorks 2025 验收时，先读 `sw-mcp-validation`。
- 工程图、BOM、标题栏和 PDF 任务时，先读 `sw-drawing-automation`，再进入工程图子技能。
- 先查 `docs/CAPABILITY_MATRIX.md` 和现有源码，确认能力状态。
- 不得把 Skill 中的命令、Schema 或 API 参数当成永久有效，执行前应以当前源码和真实 Schema 为准。

## 4. 任务分类与授权边界

开始修改前，把任务归入以下一类或多类。

| 类型 | 允许的默认操作 | 必须额外授权 |
|---|---|---|
| 只读盘点 | 读取源码、Git、日志和文档 | 修改文件、运行写测试 |
| 文档整理 | 修改项目说明和状态文件 | commit、push |
| 功能开发 | 修改已确认的源码和测试 | commit、push、历史重写 |
| 真机验收 | 使用独立测试文件调用 SolidWorks | 保存或覆盖生产文件 |
| Git 操作 | 只读检查分支和远端 | add、commit、push、rebase、reset、clean |
| 环境切换 | 准备方案和回滚步骤 | 修改 C 盘配置或重启正式 MCP |

任务授权只覆盖用户明确列出的范围。某项操作未提及，不自动推定已授权。

## 5. 开发前 Git 检查

在任何写操作前执行以下检查。

```powershell
git branch --show-current
git rev-parse HEAD
git status --porcelain=v1 --untracked-files=all
git remote -v
git branch -vv
git config --local --get remote.upstream.pushurl
```

检查要求：

1. 当前分支明确，不能处于 detached HEAD，除非用户要求只读检查。
2. 暂存区必须符合当前任务。
3. 未暂存修改必须能够归属。
4. `origin` 指向个人仓库。
5. `upstream` push 必须为 `DISABLED`。
6. `$null` 不得进入暂存区。
7. 不上游同步时，不主动修改 `upstream/main` 的本地跟踪引用之外的状态。

新功能使用 `feature/*`，修复使用 `fix/*`，上游同步使用 `sync/upstream-YYYYMMDD`。创建、切换分支或合并必须先获得任务授权。

## 6. 开发流程

### 6.1 定义任务合同

开工前写清以下内容。

- 目标和明确不做的范围。
- 需要修改的文件或模块。
- 需要保持兼容的接口和行为。
- 测试等级和验收证据。
- Git、远端、正式运行环境是否允许改变。

### 6.2 先复用再开发

- 搜索 `mcp-server/`、`scripts/`、`subskills/` 和测试中的现有实现。
- 优先修复原作者已有逻辑。
- 优先复用现有工具、Schema、错误码和验证函数。
- 不对无关模块重构。
- 不创建重复工具或重复工作流。

### 6.3 修改原则

- 功能源码、测试和文档按最小必要范围修改。
- 保持现有 93 个业务工具以及 3 个发现入口的向后兼容。
- 新增或修改工具必须同步检查注册、Schema、策略、审批、文档目标绑定和错误路径。
- SolidWorks COM 写操作必须串行。
- 使用独立测试文件、独立副本和独立输出目录。
- 过程失败先诊断原因，不通过删除校验或伪造结果绕过。

## 7. 测试与验收分级

每项结果必须标明实际达到的等级，不得跨级宣称。

### L0，静态检查

- Python AST 或语法解析。
- JSON/YAML 格式检查。
- Markdown 链接、空白、冲突标记和敏感信息检查。
- `git diff --check` 和必要的文件哈希。

用途：发现格式、结构和明显安全问题。不能证明功能可用。

### L1，单元与离线测试

- 相关 pytest。
- 契约测试、Schema 模型测试和错误路径测试。
- 必要时运行项目允许的完整离线回归。

用途：证明代码逻辑和接口契约。不能证明 SolidWorks COM 或真实文件可用。

### L2，MCP 进程与工具表面验证

- 启动当前源码的独立 MCP 进程。
- 检查发现模式只暴露 3 个入口。
- 检查完整模式业务工具数量。
- 通过 `sw_search_tools` 检索工具。
- 通过 `sw_describe_tool` 读取真实参数 Schema。

用途：证明 MCP 注册、发现和 Schema 可读。不能证明几何正确。

### L3，MCP 实际调用

- 使用真实 MCP 调用链执行目标工具。
- 使用独立测试文件，不修改生产模型。
- 检查返回状态、错误码和实际输出。

用途：证明工具被真实调用。仍不能仅凭 `success: true` 证明几何或交付正确。

### L4，SolidWorks 2025 真机验证

- 确认目标 SolidWorks 实例、文档路径和进程 ID。
- 使用 SolidWorks 2025 实际生成或读取文档。
- 回读边界框、质量、体积、实体数、特征树、孔和材料等真实证据。
- 对目标文档执行重建和必要的保存重开检查。

用途：证明当前机器、当前版本和当前测试文件上的实际 CAD 行为。

### L5，交付验收

- 保存并重新打开模型、装配体或工程图。
- 导出 STEP、PDF、DXF、DWG 等交付文件。
- 实际解析、重开或目视检查输出内容。
- 检查几何、BOM、标题栏、尺寸、文件哈希和错误状态。

用途：证明交付链路闭环。任何一项未完成时，状态只能是 `partial`、`review_required` 或 `blocked`。

## 8. 代码审查

提交前或任务交付前至少检查：

1. 修改文件与任务范围一致。
2. 没有混入 `$null`、密钥、个人路径、生产模型或大型测试产物。
3. 功能源码和测试保持向后兼容。
4. 新参数有真实 Schema 和默认值。
5. 写操作有目标校验、覆盖保护和合理错误信息。
6. 测试证明与声明等级一致。
7. 文档中的工具数量、能力和遗留问题没有矛盾。
8. `git diff --check` 通过。

需要暂存时，只使用明确文件路径执行 `git add -- <path...>`。禁止 `git add .` 和 `git add -A`。

## 9. 任务收尾

### 9.1 状态核对

```powershell
git branch --show-current
git rev-parse HEAD
git status --porcelain=v1 --untracked-files=all
git diff --check
git log -8 --format='%h %ae %ce %s'
```

确认：

- 工作区只包含本轮预期修改和明确排除的 `$null`。
- 暂存状态符合授权。
- 提交、推送和远端变化符合授权。
- 测试文件、报告和输出路径均已记录。

### 9.2 更新项目文档

- `PROJECT_STATUS.md` 更新当前 HEAD、分支、远端、工作区、已完成项、遗留项和下一步。
- `CHANGELOG.md` 更新日期、范围、修改文件、测试结果、commit 和 push 状态。
- 验收原始证据写入 `D:\Projects\SolidWorks-MCP-Data\validation`。
- 可公开脱敏摘要写入 `docs/VALIDATION/`。
- 重要经验写入相关 Skill，不把全部聊天记录复制进仓库。

如果任务只做只读盘点，也要记录没有修改文件和未执行 Git 写操作。

### 9.3 生成下一聊天交接指令

每次任务结束必须生成一段可以直接粘贴到新聊天的交接指令，至少包含：

```text
从 D:\Projects\SolidWorks-MCP 接手 SolidWorks MCP 项目。
先完整阅读 AGENTS.md 和 docs/AI_WORKFLOW.md，再读取 PROJECT_STATUS.md、
CHANGELOG.md 和任务相关 Skill。检查 Git、远端和工作区后开始。

当前目标：<下一任务>
当前分支：<branch>
当前 HEAD：<hash>
上游基线：<upstream/main>
上次完成：<完成项>
未完成或失败项：<列表>
本轮限制：<不修改 C/DOC/GIT 等>
验收等级：<L0-L5>
交付要求：<文件、证据、状态文档>
```

不得只写“继续上次工作”。交接内容必须让一个没有旧聊天记录的 AI 能独立继续。

## 10. 跨 AI 和跨电脑接手

### 10.1 跨 AI

- 所有 AI 使用同一仓库、同一 `AGENTS.md` 和同一工作协议。
- 模型不得依赖自身记忆判断项目状态。
- 工具名和参数必须通过当前 MCP Schema 确认。
- Claude、Cursor、DeepSeek 等客户端只要可读仓库和调用 MCP，就按相同等级记录证据。

### 10.2 新电脑

1. 克隆个人 `origin`。
2. 添加或确认作者 `upstream` 的 fetch URL。
3. 将 `upstream` push URL 设置为 `DISABLED`。
4. 检出正确的个人分支或 commit。
5. 读取 `AGENTS.md`、`docs/AI_WORKFLOW.md`、`PROJECT_STATUS.md` 和相关 Skill。
6. 创建独立的 `.venv`，安装版本化依赖。
7. 确认 `SolidWorks-MCP-Data` 或新的本机数据目录。
8. 检查 `.gitignore`、敏感配置边界和 `$null`。
9. 运行 L0、L1，再进行 L2。
10. 只有目标机器具备 SolidWorks 2025 时才能声明 L4 和 L5。

不得从旧电脑直接复制 Router、API Key、代理、审批账本或私密客户端配置。

## 11. Git 与发布流程

### 11.1 本地提交

- 只暂存用户明确批准的文件。
- 暂存后执行 `git diff --cached --check` 和暂存清单比对。
- 一组失败时停止，不跳过失败继续提交。
- 禁止把 `$null` 纳入提交。

### 11.2 推送

- 默认只推送到个人 `origin`。
- 禁止向 `upstream` 推送。
- 禁止 force push，除非用户对具体分支和原因作出明确授权。
- 推送前核对本地 HEAD、远程分支和 `main` 引用。
- 推送后核对远程分支 HEAD。
- 推送成功后再更新项目状态中的 commit、push 和跟踪关系。

### 11.3 上游同步

- 先 fetch `upstream`。
- 在独立 `sync/upstream-YYYYMMDD` 分支审查差异。
- 不直接覆盖个人分支。
- 冲突逐文件分析。
- 测试通过并获得授权后再合并或提交。

## 12. 最短启动与收尾指令

开始新聊天时使用：

```text
从 D:\Projects\SolidWorks-MCP 接手。先完整阅读 AGENTS.md 和
docs/AI_WORKFLOW.md，按协议核验 Git 与项目状态。本次任务：<任务内容>。
```

结束本轮时使用：

```text
按 docs/AI_WORKFLOW.md 完成任务收尾，更新 PROJECT_STATUS.md、
CHANGELOG.md 和必要的验收证据，并生成下一聊天可直接使用的交接指令。
未经我明确授权，不要 commit 或 push。
```

## 13. 相关文档

- [长期项目规则](../AGENTS.md)
- [当前项目状态](../PROJECT_STATUS.md)
- [变更记录](../CHANGELOG.md)
- [项目架构](ARCHITECTURE.md)
- [能力矩阵](CAPABILITY_MATRIX.md)
- [用户操作说明](USER_GUIDE.md)
- [D 盘迁移与切换清单](MIGRATION_TO_D.md)
- [验收证据说明](VALIDATION/README.md)
