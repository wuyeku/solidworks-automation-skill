# SolidWorks 完整机械设计自动化 MCP 操作说明

- 当前注册工具数：**93**
- 原有 69 个工具全部保留
- 本说明对应本机 SolidWorks 2025 真机验证版本

## 调用方式

MCP 默认发现模式只暴露三个入口：

1. `sw_search_tools`：按中英文设计术语检索少量候选。
2. `sw_describe_tool`：读取真实参数 Schema，禁止猜参数。
3. `sw_call_tool`：按名称和结构化参数执行工具。

完整模式下可直接调用下列原生工具。所有长度输入均为毫米，SolidWorks COM 内部自动换算为米。

安全约定：覆盖已有输出、关闭文档、批量处理、Pack and Go 等高风险操作必须提供明确输出路径和覆盖确认。活动文档写入在服务端审批模式下可能要求绑定 `document_target`。

## 推荐完整工作流

1. `solidworks_connect` 检查实例，`solidworks_health_check` 检查 COM。
2. `solidworks_new_document` 新建零件，`solidworks_create_sketch_polyline` 或草图/拉伸工具建立几何。
3. `solidworks_create_hole_feature`、圆角、倒角、抽壳、阵列、筋和配置工具完善零件。
4. `solidworks_set_custom_properties` 写入图号、名称、材料和规格。
5. `solidworks_new_document` 新建装配体，`solidworks_add_component` 插入零件和子装配。
6. 使用重合、距离、同心、平行、垂直和角度配合工具建立约束，再调用 `solidworks_inspect_assembly` 回读组件、变换和 Mate。
7. `solidworks_collect_bom` 或 `solidworks_export_bom_excel` 生成可配置 BOM。
8. `solidworks_generate_drawing` 按 DrawingSpec 生成三视图、尺寸、注释、BOM 和 PDF。
9. `solidworks_review_active`、`solidworks_inspect_hole_features`、质量、边界框、干涉和重建工具完成验收。
10. 使用 STEP、IGES、STL、Parasolid、PDF、DXF、DWG 导出和 Pack and Go 完成交付。

## 工具分类

### CAD Studio / 开放格式与分析

共 16 个工具。

| 工具 | 必需参数 | 说明 |
|---|---|---|
| `cadstudio_build_dxf_preview_scene` | 无必需参数或使用默认值 | Convert an existing DXF into a whitelisted PreviewScene JSON without running scripts. |
| `cadstudio_check_dfm` | 无必需参数或使用默认值 | Run whitelisted DFM checks for machining, sheet metal, laser cutting, or 3D printing. |
| `cadstudio_check_drc` | 无必需参数或使用默认值 | Check supplied design evidence; missing evidence requires review. Writes a versioned JSON report. |
| `cadstudio_check_routing` | 无必需参数或使用默认值 | Review neutral routing topology, bend radius, clearance, supports, and BOM evidence. |
| `cadstudio_create_ocp_loft` | 无必需参数或使用默认值 | Create and reopen a real parameterized OCP loft without arbitrary geometry code execution. |
| `cadstudio_create_ocp_surface` | 无必需参数或使用默认值 | Create smooth loft, sweep, knit, or thicken geometry through a strict structured whitelist. |
| `cadstudio_fea_preflight` | 无必需参数或使用默认值 | Discover approved CalculiX or Elmer solver executables without running arbitrary commands. |
| `cadstudio_list_drc_rules` | 无必需参数或使用默认值 | List design audit rules and available declarative rule packs. |
| `cadstudio_prepare_fea` | 无必需参数或使用默认值 | Generate a versioned CalculiX .inp file from a structured FEA 1.0 request. |
| `cadstudio_read_artifact` | 无必需参数或使用默认值 | Return an in-protocol PNG preview or a hashed file chunk for an issued artifact ID. |
| `cadstudio_resolve_backend` | 无必需参数或使用默认值 | Select Python, C#, C++, SWBasic, OCCT, AutoCAD .NET, or an external solver. |
| `cadstudio_review_advanced_geometry` | 无必需参数或使用默认值 | Validate advanced surface/mold plans and return pilot/blocked preflight evidence. |
| `cadstudio_routing_preflight` | 无必需参数或使用默认值 | Probe SolidWorks Routing type library, add-in registration, and license evidence. |
| `cadstudio_run_fea` | 无必需参数或使用默认值 | Run a structured FEA 1.0 request through an approved local solver without arbitrary command execution. |
| `cadstudio_run_fea_convergence` | 无必需参数或使用默认值 | Run 3-8 approved CalculiX meshes and compare displacement/stress convergence. |
| `cadstudio_write_open_format` | 无必需参数或使用默认值 | Write STEP/IGES/BREP/STL/OBJ/GLB/DXF/SVG/PDF/PNG without SolidWorks or AutoCAD. |

### 零件建模与通用设计

共 25 个工具。

| 工具 | 必需参数 | 说明 |
|---|---|---|
| `design_spec_build` | 无必需参数或使用默认值 | Build a SolidWorks part from a validated design spec file. This is the reproducible-design entry point: the spec file is the version-controlled source of truth, and each run produces the same feature structure and rep... |
| `design_spec_validate` | 无必需参数或使用默认值 | Validate a design spec JSON file without touching SolidWorks. Returns every problem at once (not just the first) plus manufacturing warnings such as a fillet radius exceeding half the plate thickness. |
| `solidworks_addin_host_status` | 无必需参数或使用默认值 | Inspect the Add-in assembly, exact registration scopes, diagnostics, and blockers. |
| `solidworks_build_round_sweeps` | 无必需参数或使用默认值 | 创建原生方程路径圆截面扫描及矩形拉伸；严格规格，无任意表达式，不保存。 |
| `solidworks_chamfer` | 无必需参数或使用默认值 | Chamfer the edges that match geometric filters (axis, convexity). |
| `solidworks_connect` | 无必需参数或使用默认值 | Connect to a running SolidWorks instance or start one; return the SolidWorks version (revision) and active document status. |
| `solidworks_create_basic_part` | 无必需参数或使用默认值 | Create a simple cylinder or box part with optional color and save path. |
| `solidworks_create_hole_feature` | 无必需参数或使用默认值 | Create a constrained blind/through/compound hole or semicircular slot on the active part. |
| `solidworks_create_rib` | 无必需参数或使用默认值 | Create a native rib feature from an existing sketch in the active part. |
| `solidworks_create_sketch_polyline` | 无必需参数或使用默认值 | Create an ordered line sketch on a standard or named reference plane. |
| `solidworks_exclude_reviewed_bodies` | 无必需参数或使用默认值 | 通过原生删除实体特征排除明确指定的实体，保留可编辑历史，不保存。 |
| `solidworks_fillet` | 无必需参数或使用默认值 | Round the edges that match geometric filters (axis, length, convexity). Use dry_run=True first to confirm which edges match. Edge names produced by SelectByID2 are coordinate-based and break as soon as the model is ed... |
| `solidworks_import_step_part` | 无必需参数或使用默认值 | 导入 STEP 为新多实体零件，保存到新文件并恢复导入选项；不改源文件。 |
| `solidworks_list_edges` | 无必需参数或使用默认值 | List model edges with geometry (length, midpoint, direction, diameter, convexity). Use this before fillet/chamfer to find out what edge filters will match. Do not guess edge names: SelectByID2 edge names depend on coo... |
| `solidworks_lookup_api` | 无必需参数或使用默认值 | 按接口或自然语言任务查证目标版本 API；默认按需配置依赖，可关闭自动安装和联网。 |
| `solidworks_mirror_feature` | 无必需参数或使用默认值 | Mirror an existing feature about a reference plane. |
| `solidworks_new_document` | 无必需参数或使用默认值 | Create a new part, assembly, or drawing document from a SolidWorks template. |
| `solidworks_pattern` | 无必需参数或使用默认值 | Create a linear or circular pattern of an existing feature (e.g. a hole or boss). |
| `solidworks_recover` | 无必需参数或使用默认值 | Diagnose a blocked SolidWorks session and optionally dismiss blocking modal dialogs. |
| `solidworks_review_active` | 无必需参数或使用默认值 | Export preview BMPs and a JSON review report for the active SolidWorks document. |
| `solidworks_revolve` | 无必需参数或使用默认值 | Revolve a sketch profile about an axis to create a solid of revolution. |
| `solidworks_set_appearance` | 无必需参数或使用默认值 | Set appearance color on the active document or an assembly component. |
| `solidworks_shell` | 无必需参数或使用默认值 | Hollow out the active part with a uniform wall thickness. |
| `solidworks_sketch_and_extrude` | 无必需参数或使用默认值 | Draw a circle, rectangle, slot, or polygon on a plane and extrude it as a boss or cut. This is the main modeling entry point: one call creates a sketch and the feature built from it, so the sketch object reference is ... |
| `solidworks_update_dimension` | 无必需参数或使用默认值 | Update an exact named dimension, rebuild, optionally save, and return before/after evidence. |

### 文件、属性与配置

共 8 个工具。

| 工具 | 必需参数 | 说明 |
|---|---|---|
| `solidworks_activate_configuration` | 无必需参数或使用默认值 | Activate an existing configuration and verify the active configuration by readback. |
| `solidworks_close_documents` | 无必需参数或使用默认值 | Close the active document or all documents in the current SolidWorks session. |
| `solidworks_create_configuration` | 无必需参数或使用默认值 | Create, optionally activate, rebuild, save, and read back a configuration. |
| `solidworks_document_units` | 无必需参数或使用默认值 | Read the active document's linear and angular units, and optionally change them. Mixed metric/imperial documents are a common source of 25.4x errors. Read the units before trusting any dimension value another tool rep... |
| `solidworks_export_active` | 无必需参数或使用默认值 | Export the active SolidWorks document to STEP, STL, IGES, Parasolid, PDF, DXF, or DWG. |
| `solidworks_open_document` | 无必需参数或使用默认值 | Open a SolidWorks document by absolute path and make it available for later MCP tools. |
| `solidworks_save_document` | 无必需参数或使用默认值 | Save the active SolidWorks document, optionally using Save As. |
| `solidworks_set_custom_properties` | 无必需参数或使用默认值 | Set and read back file-level or configuration-level custom properties. |

### 装配体

共 13 个工具。

| 工具 | 必需参数 | 说明 |
|---|---|---|
| `solidworks_add_angle_mate` | 无必需参数或使用默认值 | Add an angle mate between named planes/features in two components. |
| `solidworks_add_coincident_mate` | 无必需参数或使用默认值 | Add a coincident mate between named planes/features inside two assembly components. |
| `solidworks_add_component` | 无必需参数或使用默认值 | Add an existing part/subassembly to the active assembly, optionally fixing it. |
| `solidworks_add_concentric_mate` | 无必需参数或使用默认值 | Add a concentric mate between two components by locating matching cylinder faces. |
| `solidworks_add_distance_mate` | 无必需参数或使用默认值 | Add a distance mate between named planes/features inside two assembly components. |
| `solidworks_add_parallel_mate` | 无必需参数或使用默认值 | Add a parallel mate between named planes/features in two components. |
| `solidworks_add_perpendicular_mate` | 无必需参数或使用默认值 | Add a perpendicular mate between named planes/features in two components. |
| `solidworks_inspect_assembly` | 无必需参数或使用默认值 | Read hierarchy, component transforms, mates, health, and assembly measurements. |
| `solidworks_interference_check` | 无必需参数或使用默认值 | Run interference detection on the active assembly and report each interference volume. Always requires human review: zero interferences does not prove the assembly is correct (suppressed components are skipped), and n... |
| `solidworks_replace_component_preserving_transform` | 无必需参数或使用默认值 | 按精确实例名替换一个固定组件，保留变换并校验其余组件；不保存。 |
| `solidworks_set_component_fixed` | 无必需参数或使用默认值 | Fix or float a component in the active assembly by component name keyword. |
| `solidworks_set_component_suppression` | 无必需参数或使用默认值 | Reversibly suppress or unsuppress one component in the active assembly. |
| `solidworks_set_material` | 无必需参数或使用默认值 | Assign and verify a physical SolidWorks material on the active part. |

### 工程图

共 7 个工具。

| 工具 | 必需参数 | 说明 |
|---|---|---|
| `solidworks_add_detail_view` | 无必需参数或使用默认值 | Create a detail view using the currently selected native detail region. |
| `solidworks_add_drawing_view` | 无必需参数或使用默认值 | Add a standard or isometric model view to the active drawing sheet. |
| `solidworks_add_section_view` | 无必需参数或使用默认值 | Create a section view using the currently selected native section line. |
| `solidworks_generate_drawing` | 无必需参数或使用默认值 | 按 DrawingSpec 自动创建工程图、原生尺寸/基本尺寸、基准及单框/复合 GD&T（公共基准、投影公差带、轮廓偏置、CZ/SZ），保存重开核验并导出 PDF、预览和审视报告（原生标注限 SW2026，设计公差须明确）。 |
| `solidworks_insert_drawing_bom` | 无必需参数或使用默认值 | Insert a native BOM table into the active assembly drawing. |
| `solidworks_inspect_drawing` | 无必需参数或使用默认值 | 只读读取工程图页、视图、尺寸、注释和表格结构，并生成预览证据。 |
| `solidworks_review_drawing` | 无必需参数或使用默认值 | 打开工程图并执行 DrawingSpec、布局、尺寸、孔槽和 PDF 证据审视。 |

### 运动分析

共 3 个工具。

| 工具 | 必需参数 | 说明 |
|---|---|---|
| `solidworks_add_rotary_motor` | 无必需参数或使用默认值 | Create a Motion Study on the active assembly and add a constant-speed rotary motor by cylinder faces. |
| `solidworks_inspect_motion_studies` | 无必需参数或使用默认值 | Inspect Motion Study definitions, motor/force counts, and whether results are stale. |
| `solidworks_validate_motion_study` | 无必需参数或使用默认值 | Enforce Motion Study type, duration, motor count, result presence, and freshness requirements. |

### BOM 与交付

共 5 个工具。

| 工具 | 必需参数 | 说明 |
|---|---|---|
| `solidworks_batch_export_files` | 无必需参数或使用默认值 | Export multiple local SolidWorks files and verify every output was produced this run. |
| `solidworks_collect_bom` | 无必需参数或使用默认值 | Collect consolidated and occurrence-level BOM data from the active assembly. |
| `solidworks_export_assembly_bom` | 无必需参数或使用默认值 | Export a component/property BOM CSV; the result always requires native BOM review. |
| `solidworks_export_bom_excel` | 无必需参数或使用默认值 | Export consolidated and occurrence BOM sheets to an XLSX workbook. |
| `solidworks_pack_and_go` | 无必需参数或使用默认值 | Run the native Pack and Go API into a protected output directory. |

### 检查与分析

共 9 个工具。

| 工具 | 必需参数 | 说明 |
|---|---|---|
| `solidworks_bounding_box` | 无必需参数或使用默认值 | Read the active document's bounding box in millimetres. Useful for checking that a part fits a build envelope, pallet, or shipping box. |
| `solidworks_health_check` | 无必需参数或使用默认值 | Check Python dependencies, SolidWorks COM registration, optional live connection, and Motion typelib. |
| `solidworks_inspect_configurations` | 无必需参数或使用默认值 | Inspect configuration names and the active configuration without modifying the document. |
| `solidworks_inspect_feature_tree` | 无必需参数或使用默认值 | Read the active document's feature tree with native health evidence. |
| `solidworks_inspect_hole_features` | 无必需参数或使用默认值 | Read B-Rep holes, compound segments, slot arcs, and optional hole-position acceptance. |
| `solidworks_inspect_native_geometry` | 无必需参数或使用默认值 | 读取实体名称、包围盒、体积、错误和组件变换，不保存。 |
| `solidworks_mass_properties` | 无必需参数或使用默认值 | Read mass, volume, surface area, centre of mass, and inertia of the active document. If the document has no material assigned, SolidWorks falls back to its default density, so the reported mass is flagged as unreliabl... |
| `solidworks_read_custom_properties` | 无必需参数或使用默认值 | Read requested file-level or configuration-level custom properties. |
| `solidworks_rebuild_document` | 无必需参数或使用默认值 | Run a full native rebuild, report feature health, and optionally save. |

### 原生钣金

共 3 个工具。

| 工具 | 必需参数 | 说明 |
|---|---|---|
| `solidworks_create_sheet_metal_base_flange` | 无必需参数或使用默认值 | Create a native base flange from an ordered sketch polyline on the active part. |
| `solidworks_export_flat_pattern_dxf` | 无必需参数或使用默认值 | Export a saved native sheet-metal part to a flat-pattern DXF. |
| `solidworks_inspect_sheet_metal` | 无必需参数或使用默认值 | Read native sheet-metal features, parameters, and solid-body semantics. |

### 焊件

共 4 个工具。

| 工具 | 必需参数 | 说明 |
|---|---|---|
| `solidworks_create_weldment_profile` | 无必需参数或使用默认值 | Save a selected active-part sketch as a native .sldlfp weldment profile. |
| `solidworks_create_weldment_structural_member` | 无必需参数或使用默认值 | Create one native structural-member group from an ordered sketch polyline. |
| `solidworks_export_weldment_cut_list` | 无必需参数或使用默认值 | Export the active weldment's native cut-list properties to CSV. |
| `solidworks_inspect_weldment` | 无必需参数或使用默认值 | Read structural members, cut-list folders, properties, and native evidence. |

## 使用示例

### 查找并调用

```text
sw_search_tools(query="插入装配体零件并添加平行配合", limit=5)
sw_describe_tool(name="solidworks_add_parallel_mate")
sw_call_tool(name="solidworks_add_parallel_mate", arguments={...})
```

### 递归 BOM

```json
{
  "params": {
    "recursive": true,
    "include_excluded": false,
    "include_subassemblies": true,
    "columns": {"specification": ["Specification", "规格"]},
    "response_format": "json"
  }
}
```

### 原生钣金

先新建或打开一个空白零件，再使用 `solidworks_create_sheet_metal_base_flange`。该工具从有序草图点创建开放或闭合轮廓、原生 SheetMetal 父特征和 BaseFlange，并返回厚度、折弯半径、K 因子和实体语义。保存后使用 `solidworks_export_flat_pattern_dxf`。

### 焊件

`solidworks_create_sketch_polyline` → `solidworks_create_weldment_profile` → 新建零件 → `solidworks_create_weldment_structural_member` → `solidworks_inspect_weldment` → `solidworks_export_weldment_cut_list`。

## 使用限制

- `solidworks_add_section_view` 和 `solidworks_add_detail_view` 需要 SolidWorks UI 或原生选择先建立剖切线/局部区域。
- 通用 DrawingSpec 自动器当前验证三视图、模型尺寸、注释、GD&T 和 BOM；复杂剖视、局部放大和孔表仍需专项入口或人工复核。
- 装配删除、爆炸视图、组件阵列、Edwards/DimXpert 等高级接口尚未作为独立工具完成真机验收。
- 焊件工具支持用户提供 `.sldlfp` 型材和结构构件组，完整型材库浏览尚未封装。
- Sheet Metal 当前稳定支持 BaseFlange 和 Flat Pattern DXF；Edge Flange、Tab、Unfold/Fold 尚未完成 MCP 真机回归。
- 所有审查工具返回的 `review_required`、`pilot` 或 `blocked` 不得被模型改写为完成。
