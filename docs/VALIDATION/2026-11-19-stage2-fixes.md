# SolidWorks MCP 第二阶段修复与真机验收

日期：2026-11-19

SolidWorks：2025 SP0.0（33.0.0.5050）

## 结论

- 修复了 `solidworks_mirror_feature` 的 SW2025 选择标记错误，并为基础拉伸、圆角、孔切除选择了正确的原生 Mirror 路径。
- 修复了 `solidworks_batch_export_files` 的 PDF 应用对象传递，并让 `.dwg` 走独立 DWG 导出器。
- 复验了装配体工程图审查。三视图、比例、BOM 数据均正确；审查因标题栏 PDF 文字重叠风险而保持 `blocked`。
- 修复了 `solidworks_add_section_view` 的排除组件 VARIANT 参数。
- 修复了 `solidworks_add_detail_view` 的 SW2025 12 参数签名和无效样式值；经真实 MCP 调用生成并保存 `2:1` 局部视图。
- 定向回归测试：59 passed；工程图子技能专项：32 passed。
- MCP 结构验证：完整模式 93 个工具、发现模式 3 个入口且 93 个工具均可检索和读取 Schema。
- 当前已连接 MCP 进程没有热重载源码。上述成功调用由从修改后源码启动的独立 MCP stdio 进程完成。下次正式使用前需要重载/重启该 MCP 连接；本轮没有修改 Router 或 MCP 配置。

## 源码修改

| 文件 | 修改 |
|---|---|
| `scripts/sw_part.py` | Feature=1、Plane=2；基础单实体拉伸走 body mirror；圆角/倒角走 Geometry Pattern；选择失败给出明确错误 |
| `scripts/sw_export.py` | 批量 PDF 显式传入 SolidWorks Application；DXF 与 DWG 分流 |
| `mcp-server/server.py` | 更新剖视/局部放大参数说明；无预选时提前阻断并返回前置条件错误 |
| `subskills/solidworks-engineering-drawing/scripts/drawing_workflow.py` | 剖视 ExcludedComponents 使用空 VARIANT；局部放大改用 SW2025 12 参数及 CONNECTED 样式 |
| `tests/test_sw_mirror_feature.py` | 新增镜像选择标记、实体镜像、圆角 Geometry Pattern、本地化基准面和错误诊断测试 |
| `tests/test_sw_batch_export.py` | 新增批量 PDF Application 透传测试 |
| `tests/test_drawing_subskill.py` | 新增 SW2025 剖视/局部视图签名测试 |

源码备份：

`<USER_HOME>\Documents\Codex\2026-11-18\1\work\solidworks_stage2_fix_backup_20261119_223441`

## solidworks_mirror_feature

根因：

- 原实现把源特征选择标记设为 `4`，镜像面设为 `1`。
- SW2025 官方要求源特征标记 `1`，镜像面标记 `2`。
- 首次基础拉伸不能按普通 feature mirror 复制；SW2025 会返回警告特征但不产生镜像几何。
- 圆角重建依赖无法在镜像侧自动重解，需 `BGeometryPattern=True`。

真机结果：

| 场景 | 结果 |
|---|---|
| 基础拉伸 | 实体数 1→2；体积 8000→16000 mm³；边界 100×20×10 mm；特征树为 `MirrorSolid`，健康 |
| R5 圆角 | 体积 59946.349541→59892.699082 mm³；去除 53.650459 mm³，与理论完全一致；圆柱圆角面 1→2 |
| Ø8 贯穿孔 | 两孔位置 (-50,20) 和 (50,20) mm；两孔轴向长度均为 2 mm；体积 39798.938070 mm³，与理论一致 |

更新后 MCP 调用证据：

`<USER_HOME>\Desktop\SW插件测试\第二阶段修复验证\mirror_mcp_updated\MCP_Mirror_Updated_Result.json`

独立真机报告：

`<USER_HOME>\Desktop\SW插件测试\第二阶段修复验证\mirror_final\Mirror_Final_Real_Tests.json`

## solidworks_batch_export_files

- 两个独立零件和一个独立装配体的 STEP 批量导出：3/3 成功。
- STEP 重开：两个零件各 1 个实体；装配体重开为 2 个组件。
- 工程图 PDF、DXF、DWG 批量导出（文件此前未以只读方式占用）：3/3 成功。
- PDF：PyMuPDF 可打开，1 页，A3 横向，可读 MCP-A-001 至 MCP-D-001。
- DXF：ezdxf 可解析，AC1015，210 个实体，11 个图层。
- DWG：AC1015 文件头、大小正常；本机没有 ODA/AutoCAD/LibreDWG，无法完成独立 DWG 内容重开验证。
- 边界问题：若源工程图已经在 SolidWorks 中以只读方式打开，PDF 仍成功，但 DXF/DWG 的 `SaveAs` 返回错误码 1。相同文件在未只读占用时可导出。

结果：

- `batch_export_20261119_224700\Batch_STEP_Result.json`
- `batch_export_20261119_224700\MCP_Updated_Batch_Result.json`
- `batch_export_20261119_224700\Export_Content_Validation.json`
- `batch_export_20261119_224700\DWG_Reopen_Validation.json`

## solidworks_review_drawing

使用 A3/GB-T/第一角装配图规格复验：

- 前视、俯视、右视：3/3 存在。
- 三视图比例均回读为 `1:2`。
- 三视图边界互不重叠。
- BOM 为原生表：1 行表头 + 4 行零件，数量合计 4。
- 图号与数据：MCP-A-001、MCP-B-001、MCP-C-001、MCP-D-001。
- 材料均为 Q235-A，名称和数量与装配体一致。
- 图纸没有尺寸实体，标题栏业务内容未完成结构化验证。
- PDF 检查发现 5 处标题栏模板文字框重叠风险，因此工具总状态为 `blocked`；不能把该图纸称为生产级完整工程图。

报告：

`<USER_HOME>\Desktop\SW插件测试\第二阶段修复验证\drawing_review_assembly_spec\stage2_assembly_drawing_review.json`

## 剖视图与局部放大

前置条件：

- 剖视：先在现有模型视图中选择原生剖切线，或选择可组成剖切线的连续草图线。
- 局部放大：先在现有模型视图中选择原生局部圆（Detail Circle）。
- 局部圆应使用视图草图局部坐标定义；直接用图纸坐标可能生成空内容。

真机结果：

- 剖视经更新后 MCP 成功生成 `剖面视图 A-A`，保存重开后视图类型为 2。
- 局部放大经更新后 MCP 成功生成 `局部视图 (2 : 1)`，保存重开后视图类型为 3，比例回读为 `[2.0, 1.0]`。
- 无预选对象时，两工具均返回明确的前置条件错误，不再执行空选择调用。

证据：

- `section_detail_mcp\MCP_Section_Success.json`
- `section_detail_mcp\MCP_Detail_Success.json`
- `section_detail_mcp\MCP_NoSelection_Errors.json`
- `section_detail_tests\Section_API_Test2.pdf`
- `section_detail_tests\Detail_API_Test_LocalCircle.pdf`

## 尚存问题

1. 当前已连接 MCP 进程需重载，才能让常规客户端加载本次源码修改。
2. DWG 缺少本机独立解析器，只有格式头和产物证据，未完成内容级重开验证。
3. 批量导出的只读已打开工程图 DXF/DWG 边界失败，错误码 1。
4. 现有装配图的标题栏模板存在 PDF 文字重叠风险，且没有尺寸实体。
