---
name: sw-mcp-development
description: 开发和维护本仓库的 SolidWorks MCP 工具。用于新增或修复 MCP 工具、修改工具 Schema、副作用策略、文档目标绑定、Python COM 执行核心或工具注册测试。
---

# SolidWorks MCP 开发

## 开始前

1. 读取仓库根目录 `AGENTS.md` 和 `PROJECT_STATUS.md`。
2. 检查当前分支和工作区，不覆盖未提交修改。
3. 搜索 `mcp-server/`、`scripts/` 和 `subskills/` 中是否已有实现。
4. 不修改 Router、API Key、代理或正式 MCP 配置。

## 开发流程

1. 先读取真实工具 Schema 和 `mcp-server/policy.py` 的副作用分级。
2. 优先复用现有 `scripts/sw_*.py` 和子技能。
3. 保持现有 93 个业务工具的向后兼容。
4. 写操作必须串行访问 SolidWorks COM。
5. 活动文档写操作必须校验真实 SolidWorks 进程和已保存文档路径。
6. 新增工具必须登记策略、发现元数据、Schema 和测试。
7. 修改失败路径时返回稳定错误码，不吞掉 COM 错误。
8. 新增或修改对外参数时必须贯通 MCP 输入模型、工具操作、底层包和兼容入口。例如 `drawing_template_path` 必须同时通过顶层工具和兼容入口传给出图包，不能只修改其中一层。

## 验证流程

1. 运行工具注册和 Schema 测试。
2. 运行相关 pytest。
3. 运行完整 `python -m pytest -q`，区分回归失败和环境失败。
4. 获得重启授权后，用实际 `sw_describe_tool` 核对新增 Schema 字段，并确认当前 MCP 进程使用最新源码。
5. 使用独立模型和真实 MCP 完成定向真机调用。
6. 回读特征树、几何、属性和导出文件。
7. 更新 `PROJECT_STATUS.md` 与 `CHANGELOG.md`。

## 完成与交付门禁

- 工程图功能开发完成前，必须由人审阅实际 PDF 和 SLDDRW。自动化生成成功、结构审查通过或 `GetSaveFlag=false` 均不能关闭人工制图缺陷。
- 审阅记录必须分别列明源码执行器、自动审查、正式 MCP 调用和人工工程图质量四类状态。
- 任一视图布局、必要尺寸、局部标注、文字阅读性或制造可用性存在明显缺陷时，阶段状态保持 `REVIEW_REQUIRED` 或 `FAIL`。
- 新增功能未被正式 MCP 当前进程加载时，应记录旧模块缓存问题。未获授权不得通过重启或改配置掩盖该缺口。

## 禁止

- 伪造工具结果。
- 用返回 `success: true` 代替几何验证。
- 删除校验以隐藏失败。
- 擅自提交、推送或修改远端。
