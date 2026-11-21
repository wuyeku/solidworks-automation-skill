# SolidWorks MCP 活动文档定位修复与真机验收报告

日期：2026-11-20

SolidWorks：2025，Revision `33.0.0`

MCP 服务：`<USER_HOME>\.codex\skills\solidworks-automation\mcp-server\server.py`

## 结论

已修复活动文档获取问题。MCP 现在能够按已打开文档路径定位并激活 SolidWorks 文档，`solidworks_connect`、`solidworks_bounding_box`、
`solidworks_mass_properties` 和 `solidworks_inspect_native_geometry` 可以在同一 SolidWorks 实例、同一活动文档上正确工作，
不再出现 `Active document target mismatch`。

## 根因

`solidworks_open_document` 在目标文档已经打开时会直接复用 `GetOpenDocumentByName()` 返回的对象，
但没有调用 `ISldWorks.ActivateDoc3()`。因此工具虽然返回 `status: ok`，SolidWorks 的实际活动文档仍可能是另一个零件。
后续 `solidworks_inspect_native_geometry` 只检查 `ActiveDoc`，便会报目标不匹配。

本次诊断同时确认：

- SolidWorks 文档枚举正常，同一实例可枚举到已打开文档。
- `ActiveDoc` 为空来自文档激活状态，不是 MCP 连接了错误的 SolidWorks PID。
- 真机验证期间系统只有一个 `SLDWORKS.exe`，MCP 实际连接 PID `52412`。
- 同时存在多个 MCP Python 传输进程，但当前工具调用连接到同一个 SolidWorks COM 实例。

## 源码修改

- `scripts\sw_connect.py`
  - 新增 `find_open_document()`，按规范化绝对路径定位已打开文档。
  - 新增 `activate_document()`，通过 `ActivateDoc3` 激活并回读目标文档；保留 `ActivateDoc2` 兼容回退。
  - `open_document()` 的“复用已打开文档”和“新打开文档”路径均会激活并校验目标。
- `scripts\sw_native_wire.py`
  - `invoke_native()` 在调用原生检查前按 `expected_document_path` 定位并激活目标文档。
- `mcp-server\document_identity.py`
  - 新增只读访问器 `get_bound_document()`。
- `mcp-server\server.py`
  - `_active_model_required()` 在存在 `document_target` 时按绑定路径恢复并激活目标文档。
  - 仅有一个已打开文档时，可无歧义地恢复该文档。
- `mcp-server\policy.py`
  - 允许 `solidworks_mass_properties`、`solidworks_bounding_box`、
    `solidworks_inspect_native_geometry` 接受显式 `document_target`。

修改前备份：

`<USER_HOME>\Documents\Codex\2026-11-18\1\work\solidworks_com_active_doc_backup_20261119_233901`

## 测试结果

相关单元测试：

```text
34 passed in 5.29s
```

测试范围：

- `tests/test_sw_connect_open_document.py`
- `tests/test_native_wire_transport.py`
- `tests/test_mcp_document_binding_integration.py`
- `tests/test_mcp_document_identity.py`
- `tests/test_read_active_document.py`

## 真实 MCP 调用证据

测试文件：

`<USER_HOME>\Documents\Codex\2026-11-18\1\outputs\solidworks_mcp_full_workflow_20261118_231842\workflow_part_A.SLDPRT`

1. `solidworks_open_document`：返回 `status: ok`，文档为 `workflow_part_A.SLDPRT`。
2. `solidworks_connect`：返回 PID `52412`，活动文档标题 `workflow_part_A.SLDPRT`，类型 `1`（零件）。
3. `solidworks_health_check`：返回 `status: ok`，活动文档同样是 `workflow_part_A.SLDPRT`。
4. `solidworks_bounding_box`：
   - 尺寸 `100 × 60 × 20 mm`
   - 范围 `[-50,-30,-20]` 至 `[50,30,0]`
   - 文档路径与测试零件一致
5. `solidworks_mass_properties`：
   - 质量 `936.0 g`
   - 体积 `120000.0 mm³`
   - 表面积 `18400.0 mm²`
   - 密度 `7800 kg/m³`
   - 文档路径与测试零件一致
6. `solidworks_inspect_native_geometry`：
   - 返回 `status: ok`
   - PID `52412`
   - `save_requested: false`
   - 实体 `凸台-拉伸1`
   - 体积约 `119999.99999999999 mm³`
   - 边界 `[-50,-30,-20, 50,30,0] mm`
   - 面数 `6`
   - 文档路径与测试零件一致

另外将 `document_target` 指向零件 A，在活动文档为其他零件的情况下，三个只读工具均正确返回零件 A；
说明目标绑定、重新激活和路径校验链路均生效。

## 文件安全

- 原始零件只读打开，未调用保存命令。
- `solidworks_inspect_native_geometry` 明确返回 `save_requested: false`。
- `workflow_part_A.SLDPRT` 的磁盘修改时间仍为 `2026-11-18T23:18:50.9533103+08:00`。
- 未修改生产文件、Router、代理或 API Key。
