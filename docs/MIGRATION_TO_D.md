# 正式 MCP 切换到 D 盘的执行清单

本文是后续切换清单，当前尚未执行。

## 前提

- 用户明确批准切换。
- D 盘仓库、测试和 SolidWorks 2025 连接保持通过。
- 先备份 `%USERPROFILE%\.codex\config.toml`。
- 不修改 Router、API Key、代理和个人 GitHub 配置。

## 切换前验证

1. 使用 D 盘 `.venv\Scripts\python.exe` 启动 `mcp-server\server.py`。
2. 确认发现模式显示 3 个入口。
3. 确认完整模式显示 93 个业务工具。
4. 运行 `scripts\validate_mcp.py`。
5. 运行完整离线 pytest。
6. 连接 SolidWorks 2025 并读取独立测试零件。

## 正式配置

只更改 MCP 客户端的 Python 可执行文件和 Server 路径。

```text
Python  %PROJECT_ROOT%\.venv\Scripts\python.exe
Server  %PROJECT_ROOT%\mcp-server\server.py
```

不得同时修改模型 provider、Router 地址、API Key 或代理。

## 切换后验证

1. 在新的 Codex 任务中确认 MCP 成功连接。
2. 检查 `solidworks_health_check`。
3. 检查发现入口和 93 个业务工具。
4. 用独立测试零件执行边界框、质量和原生几何读取。
5. 检查目标文档路径、PID 和活动文档一致。
6. 保留 C 盘配置和源码至少一个稳定版本周期。

## Skill 验证

- 从 D 盘仓库启动新 Codex 任务。
- 确认仓库 `.agents/skills` 中三个项目级 Skill 被发现。
- 当前环境实际从 `%USERPROFILE%\.codex\skills` 加载原有 Skill。
- 官方标准个人路径为 `%USERPROFILE%\.agents\skills`。
- 如后续需要统一全局路径，先备份配置，再使用绝对 `skills.config.path` 或受支持的符号链接方案。
- 不在同一任务中同时保留同名的 C 盘和 D 盘 Skill，避免选择歧义。

## 回滚

1. 恢复切换前的 `config.toml`。
2. 重新加载 MCP。
3. 检查 C 盘 Server 路径和 93 工具面。
4. 不删除 D 盘项目、数据或备份。

## 完成条件

- D 盘 MCP 可独立启动。
- 93 个业务工具完整。
- SolidWorks 2025 真机连接和几何读取通过。
- 验证模型、工程图和导出文件可重开或解析。
- C 盘源码和 Git 历史未修改。
- 用户确认稳定。
