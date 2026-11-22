---
name: sw-mcp-validation
description: 对 SolidWorks MCP 进行离线回归、运行时连接和 SolidWorks 2025 真机验收。用于迁移验证、工具注册检查、MCP 进程与 Schema 核对、独立模型建模、属性回读、BOM、工程图和文件导出验收。
---

# SolidWorks MCP 验收

## 环境检查

1. 确认 Windows、Python、依赖和 SolidWorks 2025 可用。
2. 确认 SolidWorks 进程和 MCP Server 路径。
3. 使用只读健康检查，不启动额外 CAD 实例。
4. 任何真机测试都使用独立模型和输出目录。

## MCP 检查

1. `sw_search_tools` 检索目标工具。
2. `sw_describe_tool` 确认输入 Schema 和副作用。
3. `sw_call_tool` 执行。
4. 对活动文档写操作提供并核对 `document_target`。

## 代码更新后的连接验收

1. 仅在获得授权时重启或重载 MCP，使用只读健康检查确认 Server、Python 和依赖路径。
2. 通过 `sw_describe_tool` 读取目标工具的实际 Schema，确认本次新增字段已经出现。
3. 只读核对 MCP 进程命令行、父进程和服务路径，确认 Codex 会话对应的是目标 Server。
4. 必要时比较进程启动时间与代码提交时间，排除旧进程或旧 Schema 缓存。
5. 任一路径或 Schema 与预期不符时停止，不根据源码内容推断连接成功。

## 离线与真机分离

- 离线测试证明代码和契约逻辑。
- 真机测试证明当前机器、当前 SolidWorks 版本和当前文档状态。
- 文件存在不代表文件可打开或工程内容正确。
- PDF、STEP、DXF 和 DWG 必须实际解析或重开。

## 证据

保存以下内容：

- MCP 调用结果 JSON。
- 模型边界框、体积、质量、实体数和特征树。
- 保存前后哈希。
- 重开结果。
- PDF/BMP 预览和人工目视结果。
- MCP 健康检查、工具 Schema、进程命令行和进程启动时间。
- 失败原因和复现条件。

## 输出

- 原始证据写入 `D:\Projects\SolidWorks-MCP-Data\validation`。
- 可公开摘要写入 `docs/VALIDATION`。
- 更新 `PROJECT_STATUS.md` 和 `CHANGELOG.md`。
