# SolidWorks MCP 长期项目规则

本文件保存仓库级长期规则。用户在当前任务中的明确指令优先于本文件。新的 AI 或新的聊天应先读取本文件，再读取 `PROJECT_STATUS.md`、`docs/ARCHITECTURE.md` 和当前任务涉及的 Skill。

## 项目定位

本项目是基于作者的 `solidworks-automation-skill` 建立的个人长期维护分支，目标是把 SolidWorks 零件、装配、工程图、BOM、检查、钣金、焊件和文件交付能力稳定接入 MCP。

当前正式运行仍使用 C 盘副本。D 盘仓库先作为唯一开发源码，只有用户明确批准并完成切换验收后，D 盘版本才能成为正式运行版本。

## 目录边界

- 本仓库根目录保存源码、测试、文档和项目级 Skill。
- `mcp-server/` 是 MCP 入口、工具注册、策略和文档目标绑定。
- `scripts/` 是 SolidWorks COM 与开放格式执行核心。
- `subskills/` 保存已有领域工作流。
- `docs/MIGRATION_TO_D.md` 保存正式切换和回滚步骤。
- `tests/` 同时包含 pytest 单元测试和需要真机执行的验收脚本。
- 本机验证模型、BMP、PDF、SLDPRT、SLDASM、SLDDRW 和大型报告保存在 `D:\Projects\SolidWorks-MCP-Data`，不提交到公开 Git。
- Codex Router、API Key、代理和 MCP 客户端配置均位于本仓库之外，不得随项目迁移。

## 当前运行关系

- 当前正式 MCP 配置仍指向 `%USERPROFILE%\.codex\skills\solidworks-automation\mcp-server\server.py`。
- 当前开发源码位于 `D:\Projects\SolidWorks-MCP`。
- 在用户明确批准切换前，不得修改 MCP 客户端配置，不得重启当前 MCP。
- D 盘仓库当前分支为 `feature/stage5-93-tools`。

## 工具与能力口径

- 当前源码静态注册 93 个业务工具。
- 默认发现模式另外注册 3 个入口，即 `sw_search_tools`、`sw_describe_tool`、`sw_call_tool`。
- “已注册”“Schema 可读”“离线测试通过”“SolidWorks 真机通过”和“交付验收通过”是不同证据等级，报告时必须分开。
- 不得仅凭工具返回 `success: true` 宣称几何正确。
- 新增或修改工具后必须检查工具注册、输入 Schema、副作用策略、目标文档绑定和错误路径。

## 开发前检查

每次开始工作依次执行：

1. 读取本文件、`PROJECT_STATUS.md` 和任务相关 Skill。
2. 检查当前分支、HEAD、暂存区、工作区和远端。
3. 确认没有覆盖用户未提交修改。
4. 确认测试文件和测试模型位于独立目录。
5. 确认不会修改 Router、API Key、代理或正式 MCP 配置。

## 开发规则

- 优先修复作者已有源码，重复开发前先搜索现有函数和子技能。
- 不修改与当前问题无关的文件。
- 更新已有函数时保持现有 93 个工具的向后兼容。
- 所有 SolidWorks COM 写操作必须串行执行。
- 活动文档操作必须能定位真实 SolidWorks 实例和文档。只读工具允许显式 `document_target`，未提供时保持原有活动文档行为。服务端审批模式下的写操作必须绑定已保存文档路径和进程 ID。
- 用户模型默认只读。需要修改时使用明确命名的副本。
- 禁止使用伪造返回、硬编码测量值或删除校验绕过失败。

## Git 安全规则

- 当前不允许 commit、push、rebase、reset、clean 或修改远端，除非用户在当前任务中明确授权。
- `upstream` 是作者仓库，push URL 必须保持 `DISABLED`。
- 在用户提供个人 Fork URL 前不得创建 `origin`。
- 不重新初始化已有仓库。
- 不覆盖或丢弃未提交修改。
- 不把作者的更新直接覆盖个人分支。
- 上游同步前要求工作区可追踪且已有完整备份。
- 上游同步使用独立 `sync/upstream-YYYYMMDD` 分支，先审查差异，再合并且不自动提交。
- 冲突必须逐文件分析，禁止整仓选择 ours 或 theirs。
- 默认不向作者仓库推送。向个人 `origin` 推送必须由用户另行授权。

## 上游同步流程

1. 确认 `upstream` 地址正确且 push URL 为 `DISABLED`。
2. 从个人稳定分支建立同步分支。
3. 获取作者更新，列出新增提交和变更文件。
4. 检查对本地 MCP、工程图、BOM、孔特征和文档目标绑定的影响。
5. 在同步分支合并，不直接改写公开历史。
6. 运行完整离线测试和必要的 SolidWorks 2025 定向真机测试。
7. 用户确认后再创建提交或合并到稳定分支。

## 测试规则

离线测试默认命令：

```powershell
$env:SW_AUTO_INSTALL_DEPENDENCIES='off'
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

真机测试要求：

- 使用本机 SolidWorks 2025。
- 先确认只有一个目标 SolidWorks 实例。
- 使用独立测试文件和输出目录。
- 通过真实 MCP 发现、Schema 描述和调用链执行。
- 回读特征树、几何、属性、保存文件和导出文件。
- 检查 PDF、STEP、DXF、DWG 等文件能够实际打开或解析。
- 将离线通过、真机通过和人工目视复核分别记录。

## 敏感信息

以下内容不得进入 Git 或公开文档：

- API Key、Token、密码和私钥。
- `.codex/config.toml`、代理配置和 Router 密钥。
- MCP 审批账本和会话日志。
- 企业图纸、客户资料和未经授权的生产模型。
- 本机临时输出、大型 BMP、PDF、SLDPRT、SLDASM 和 SLDDRW。

## 任务结束

每次任务结束前：

1. 检查 `git status` 和关键文件哈希。
2. 运行与修改范围匹配的测试。
3. 更新 `PROJECT_STATUS.md`。
4. 在 `CHANGELOG.md` 记录修改日期、范围、测试、提交和推送状态。
5. 把验收证据保存到本地验证目录，并在 `docs/VALIDATION/` 保存可公开的摘要。
6. 明确列出未验证内容、失败项和回滚方法。
