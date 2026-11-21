# SolidWorks MCP 完整升级报告

## 基线

- 本地基线提交：`36bc337357723b9763759ff06e4a1afab990b823`
- GitHub `main` 最新提交：`36bc337357723b9763759ff06e4a1afab990b823`
- 结论：本地基线与作者 GitHub 最新版一致。
- SolidWorks 真机版本：2025，Revision `33.0.0`

## 工具规模

- 升级前：69 个工具
- 升级后：93 个工具
- 新增或升级：24 个
- 原有工具保留：69/69
- 发现模式验证：93 个工具均能通过 `sw_search_tools` 搜索并通过 `sw_describe_tool` 读取 Schema

完整工具清单见 `solidworks_mcp_tool_catalog.json`。分类统计见 `tool_category_summary.json`。

## 新增/升级工具

### 装配体

- `solidworks_inspect_assembly`
- `solidworks_add_parallel_mate`
- `solidworks_add_perpendicular_mate`
- `solidworks_add_angle_mate`
- `solidworks_set_component_suppression`

### 工程图与 BOM

- `solidworks_add_drawing_view`
- `solidworks_add_section_view`
- `solidworks_add_detail_view`
- `solidworks_insert_drawing_bom`
- `solidworks_collect_bom`
- `solidworks_export_bom_excel`

### 钣金与焊件

- `solidworks_create_sheet_metal_base_flange`
- `solidworks_inspect_sheet_metal`
- `solidworks_export_flat_pattern_dxf`
- `solidworks_create_sketch_polyline`
- `solidworks_create_weldment_profile`
- `solidworks_create_weldment_structural_member`
- `solidworks_inspect_weldment`
- `solidworks_export_weldment_cut_list`

### 零件与检查

- `solidworks_inspect_feature_tree`
- `solidworks_rebuild_document`
- `solidworks_read_custom_properties`
- `solidworks_set_material`
- `solidworks_create_rib`

贯穿孔工具 `solidworks_create_hole_feature` 也在本轮升级：

- 增加 `cut_direction`
- 增加 `double_ended`
- 增加 `face_point_mm`
- Through All 默认双端切除
- 创建结果包含真实 B-Rep 孔测量

## 真机完整工作流

测试输出目录：`solidworks_mcp_full_workflow_20261118_231842`

### 零件

- 4 个独立测试零件创建成功
- 边界框尺寸、自定义属性写入和读取均成功
- 4 个零件均保存成功

### 装配体

- 4 个组件插入成功
- 创建平行、垂直、角度配合共 3 个
- 装配体结构检查成功
- 返回组件层级、路径、配置、旋转矩阵和毫米平移
- SLDASM 保存成功

### BOM

- 递归 BOM 收集成功
- 4 个顶层组件汇总为 4 个项目，数量合计 4
- 图号、描述、材料、板厚、配置和自定义列均成功读取
- XLSX 导出成功，包含 `BOM` 与 `Occurrences` 两个工作表

### 工程图

- 从真实零件生成 A4 工程图
- 主视图、俯视图、右视图创建成功
- 视图位置和投影关系检查成功
- SLDDRW 保存成功
- PDF 导出成功
- 工程图 DXF 导出成功
- 工程图 DWG 导出成功
- 工程图审查状态：`pass`

### 钣金

- 原生 BaseFlange 创建成功
- 厚度 2 mm、折弯半径 2.5 mm、K 因子 0.42
- 实体均被 SolidWorks 标记为 SheetMetal
- FlatPattern 原生特征存在
- 展开 DXF 导出成功

### 焊件

- 自定义 `.sldlfp` 型材创建成功
- 原生 StructuralMember 创建成功
- WeldmentFeature 存在
- 切割清单创建成功
- 切割清单 CSV 导出成功

### 材料

- 独立探针将真实零件材料设置为 `Q235A`
- 回读 `MaterialIdName` 为 `Q235-A|Q235A`
- 重建和保存成功

## 测试结果

| 测试 | 结果 |
|---|---|
| 定向与 MCP 回归测试 | 141 passed，1 skipped |
| MCP 完整模式 | 93 个工具可见 |
| MCP 发现模式 | 3 个入口，93 个工具可搜索、可读 Schema |
| 语法编译 | 通过 |
| 空白/格式检查 | `git diff --check` 通过 |
| SolidWorks 2025 完整工作流 | 5/5 阶段通过 |

阶段：Part、Assembly、Drawing、Sheet Metal、Weldment。

## 源码修改

核心文件：

- `mcp-server/server.py`
- `mcp-server/policy.py`
- `scripts/sw_assembly.py`
- `scripts/sw_delivery.py`
- `scripts/sw_document_data.py`
- `scripts/sw_export.py`
- `scripts/sw_hole_features.py`
- `scripts/validate_mcp.py`
- `requirements.txt`
- `pyproject.toml`

测试文件：

- `tests/test_sw_hole_features.py`
- `tests/test_sw_delivery.py`
- `tests/test_sw_document_data.py`
- `tests/test_mcp_discovery.py`

修改前备份：

`<USER_HOME>\Documents\Codex\2026-11-18\1\work\solidworks_mcp_full_upgrade_backup_20261118_225502`

贯穿孔专用备份：

`<USER_HOME>\Documents\Codex\2026-11-18\1\work\solidworks_mcp_hole_upgrade_backup_20261118_223758`

## 未完成项

- 原生通用旋转切除、拔模、通用扫描和放样。
- 装配组件删除、组件阵列、可配置爆炸视图。
- 全自动剖视/局部放大区域选择、孔表和螺纹专项标注。
- BOM 自动气泡和类别规则引擎。
- Edge Flange、Tab、Unfold/Fold、焊珠。
- 批量打开、批量修改和完整任务队列 MCP 入口。

这些项目已在能力矩阵中明确标记，不使用伪造成功结果替代。

## 使用说明

完整 93 工具参考与调用顺序见：

- `SolidWorks_MCP_Complete_User_Guide.md`
- `SolidWorks_MCP_Capability_Matrix.md`

## 运行状态说明

当前桌面端已经存在的 MCP 子进程在启动时加载旧工具表。新增源码和独立 MCP 进程已经通过验证。下一次 MCP 重新连接会加载 93 工具版本。此次没有修改 Router、API Key 或代理配置。
