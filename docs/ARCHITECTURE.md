# Architecture

本文是项目架构总入口。作者已有的详细设计继续保存在 `docs/architecture/`，本文件不复制那些内容。

## 系统边界

| 层 | 责任 | 位置 |
|---|---|---|
| Agent | 理解用户意图、选择 Skill 和工具、验证结果 | Codex 或其他宿主 |
| Skill | 保存可重复的工程工作流和领域规则 | 根 `SKILL.md`、`subskills/`、`.agents/skills/` |
| MCP Gateway | 工具发现、Schema 描述、副作用策略、审批和目标绑定 | `mcp-server/` |
| 执行核心 | 参数校验、SolidWorks COM、文件导出、证据收集 | `scripts/` |
| CAD | SolidWorks 2025 和开放格式工具 | 本机 D 盘安装和 Python 依赖 |
| 本机数据 | 模型、预览、导出、报告和备份 | `D:\Projects\SolidWorks-MCP-Data` |

## 工具调用链

```text
用户请求
  -> Agent 读取 AGENTS.md 与相关 Skill
  -> sw_search_tools 检索候选
  -> sw_describe_tool 读取真实 Schema
  -> sw_call_tool 执行
  -> ToolGate 检查副作用、审批和目标文档
  -> Python 执行核心调用 SolidWorks COM
  -> 特征、几何、属性和文件证据回读
  -> 预览与报告审查
  -> 交付或 blocked/review_required
```

## 工具面

- 业务工具 93 个。
- 发现入口 3 个。
- 默认发现模式只在 `tools/list` 显示三个入口。
- 完整模式可显示全部命名工具，但默认不作为长期运行模式。

## 目录结构

```text
SolidWorks-MCP/
├── mcp-server/       MCP 服务、工具注册、策略、文档身份
├── scripts/          SolidWorks COM 与开放格式执行核心
├── subskills/        领域工作流
├── tests/            离线契约测试与真机验收脚本
├── docs/             架构、能力、决策和验收摘要
└── .agents/skills/   项目级 AI 工作流
```

保留作者原有包布局，避免把 `mcp-server/` 或 `scripts/` 搬到新的 `src/` 后破坏导入路径和现有启动命令。

## 文档目标绑定

只读活动文档工具允许调用方传入 `document_target`，未传入时保持原有活动文档行为。写操作在服务端审批模式下必须绑定已保存文档的进程 ID 和绝对路径。执行前再次核对活动文档，防止窗口切换后操作错误文件。

## 运行环境和数据隔离

- 开发源码和本机证据分仓。
- 源代码、文档和脱敏摘要可进入 Git。
- 原生 SolidWorks 文件、PDF、BMP、DXF、DWG 和大型输出进入本机数据目录。
- Router、代理、API Key、MCP 配置和审批账本位于项目目录之外。

## 相关但独立的项目

- `codex-router` 是模型路由服务，和 SolidWorks MCP 使用不同仓库和进程。
- `solidworks-agent` 是另一个 Codex 插件项目，可参考其长期规则和双远端治理，但不得把代码或 Git 历史直接合并到本项目。
- Codex 插件缓存属于运行产物，不作为源码主线。

## Codex Skill 加载

官方文档说明，Repository Skill 从当前工作目录向仓库根目录扫描 `.agents/skills`。修改 Skill 后 Codex 可自动识别，未识别时重启 Codex。

当前环境还实际加载了 `%USERPROFILE%\.codex\skills\solidworks-automation`。官方文档声明的个人 Skill 标准路径是 `%USERPROFILE%\.agents\skills`，本机当前尚未创建该标准目录。在正式切换前，C 盘 Skill 和 MCP 配置保持不变。D 盘开发时使用仓库内 `.agents/skills`，待用户确认后再通过新线程从 D 盘仓库启动，并检查 Skill 列表。若需禁用旧路径，可在用户批准后使用 `[[skills.config]]` 的绝对 `path` 设置；本轮不修改配置。

官方参考：

- https://learn.chatgpt.com/docs/build-skills
