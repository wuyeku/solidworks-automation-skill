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

## 验证流程

1. 运行工具注册和 Schema 测试。
2. 运行相关 pytest。
3. 运行完整 `python -m pytest -q`，区分回归失败和环境失败。
4. 使用独立模型和真实 MCP 完成定向真机调用。
5. 回读特征树、几何、属性和导出文件。
6. 更新 `PROJECT_STATUS.md` 与 `CHANGELOG.md`。

## 禁止

- 伪造工具结果。
- 用返回 `success: true` 代替几何验证。
- 删除校验以隐藏失败。
- 擅自提交、推送或修改远端。
