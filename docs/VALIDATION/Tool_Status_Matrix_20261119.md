# SolidWorks MCP 93 工具只读审计矩阵

- 作者 GitHub 基线工具数：69
- 当前本地注册数：93
- 新增工具数：24
- 作者原版 A 类（真机成功）：19
- 作者原版 B 类（失败、部分或未验证）：50
- 本地新增已真机成功：17
- 本地新增已注册但未真机闭环：7
- SolidWorks：2025 / 33.0.0

> 表中 A/B 表示当前工具的真实可用状态；“作者原版”列用于区分作者 GitHub 原版与本地新增。仅能检索或读取 Schema 的工具不进入 A。

## 零件建模与配置（33）

| 类别 | 工具 | 作者原版 | 当前源码/MCP | 测试引用 | 真机状态 |
|---|---|---|---|---|---|
| B | `design_spec_build` | 是 | 原版 | tests/live_smoke_new_tools.py | 源码与注册存在，但缺少本轮真实调用证据 |
| B | `design_spec_validate` | 是 | 原版 | 无直接工具测试 | 源码与注册存在，但缺少本轮真实调用证据 |
| B | `solidworks_activate_configuration` | 是 | 原版 | tests/test_mcp_configuration_tools.py | 源码与注册存在，但缺少本轮真实调用证据 |
| B | `solidworks_addin_host_status` | 是 | 原版 | 无直接工具测试 | 源码与注册存在，但缺少本轮真实调用证据 |
| B | `solidworks_build_round_sweeps` | 是 | 原版 | tests/manual_native_wire_2026.py, tests/test_mcp_document_identity.py, tests/test_native_wire_mcp.py | 源码与注册存在，但缺少本轮真实调用证据 |
| B | `solidworks_chamfer` | 是 | 原版 | 无直接工具测试 | 源码与注册存在，但缺少本轮真实调用证据 |
| A | `solidworks_close_documents` | 是 | 原版 | tests/test_mcp_discovery.py, tests/test_mcp_document_identity.py | 本轮或本会话已完成真实 SolidWorks 调用 |
| A | `solidworks_connect` | 是 | 原版 | tests/test_mcp_discovery.py, tests/test_mcp_discovery_quality.py | 本轮或本会话已完成真实 SolidWorks 调用 |
| A | `solidworks_create_basic_part` | 是 | 原版 | tests/test_mcp_approval_capacity.py, tests/test_mcp_approval_security.py, tests/test_mcp_discovery.py | 本轮或本会话已完成真实 SolidWorks 调用 |
| B | `solidworks_create_configuration` | 是 | 原版 | tests/test_mcp_configuration_tools.py | 源码与注册存在，但缺少本轮真实调用证据 |
| A | `solidworks_create_hole_feature` | 是 | 升级 | tests/test_engineering_orchestrator.py | 本轮或本会话已完成真实 SolidWorks 调用 |
| B | `solidworks_create_rib` | 否 | 新增 | 无直接工具测试 | 源码与注册存在，但缺少本轮真实调用证据 |
| A | `solidworks_create_sketch_polyline` | 否 | 新增 | 无直接工具测试 | 本轮或本会话已完成真实 SolidWorks 调用 |
| B | `solidworks_document_units` | 是 | 原版 | tests/test_mcp_document_identity.py | 源码与注册存在，但缺少本轮真实调用证据 |
| B | `solidworks_exclude_reviewed_bodies` | 是 | 原版 | tests/manual_native_wire_2026.py, tests/test_mcp_document_identity.py, tests/test_native_wire_mcp.py | 源码与注册存在，但缺少本轮真实调用证据 |
| A | `solidworks_export_active` | 是 | 升级 | tests/test_engineering_orchestrator.py | 本轮或本会话已完成真实 SolidWorks 调用 |
| A | `solidworks_fillet` | 是 | 原版 | 无直接工具测试 | 本轮或本会话已完成真实 SolidWorks 调用 |
| B | `solidworks_import_step_part` | 是 | 原版 | tests/manual_native_wire_2026.py, tests/test_mcp_document_identity.py, tests/test_native_wire_mcp.py | 源码与注册存在，但缺少本轮真实调用证据 |
| B | `solidworks_list_edges` | 是 | 原版 | 无直接工具测试 | 源码与注册存在，但缺少本轮真实调用证据 |
| B | `solidworks_lookup_api` | 是 | 原版 | tests/test_mcp_discovery.py | 源码与注册存在，但缺少本轮真实调用证据 |
| B | `solidworks_mirror_feature` | 是 | 原版 | 无直接工具测试 | 已真机调用并观察到失败 |
| A | `solidworks_new_document` | 是 | 原版 | 无直接工具测试 | 本轮或本会话已完成真实 SolidWorks 调用 |
| A | `solidworks_open_document` | 是 | 原版 | 无直接工具测试 | 本轮或本会话已完成真实 SolidWorks 调用 |
| B | `solidworks_pattern` | 是 | 原版 | 无直接工具测试 | 源码与注册存在，但缺少本轮真实调用证据 |
| B | `solidworks_recover` | 是 | 原版 | 无直接工具测试 | 源码与注册存在，但缺少本轮真实调用证据 |
| A | `solidworks_review_active` | 是 | 原版 | tests/test_mcp_discovery.py, tests/test_mcp_document_identity.py | 本轮或本会话已完成真实 SolidWorks 调用 |
| B | `solidworks_revolve` | 是 | 原版 | 无直接工具测试 | 源码与注册存在，但缺少本轮真实调用证据 |
| A | `solidworks_save_document` | 是 | 原版 | tests/test_mcp_approval_security.py, tests/test_mcp_discovery.py, tests/test_mcp_discovery_quality.py | 本轮或本会话已完成真实 SolidWorks 调用 |
| B | `solidworks_set_appearance` | 是 | 原版 | 无直接工具测试 | 源码与注册存在，但缺少本轮真实调用证据 |
| A | `solidworks_set_custom_properties` | 是 | 原版 | 无直接工具测试 | 本轮或本会话已完成真实 SolidWorks 调用 |
| B | `solidworks_shell` | 是 | 原版 | 无直接工具测试 | 源码与注册存在，但缺少本轮真实调用证据 |
| A | `solidworks_sketch_and_extrude` | 是 | 原版 | tests/test_mcp_document_binding_integration.py | 本轮或本会话已完成真实 SolidWorks 调用 |
| B | `solidworks_update_dimension` | 是 | 原版 | 无直接工具测试 | 源码与注册存在，但缺少本轮真实调用证据 |

## 装配体（13）

| 类别 | 工具 | 作者原版 | 当前源码/MCP | 测试引用 | 真机状态 |
|---|---|---|---|---|---|
| A | `solidworks_add_angle_mate` | 否 | 新增 | 无直接工具测试 | 本轮或本会话已完成真实 SolidWorks 调用 |
| B | `solidworks_add_coincident_mate` | 是 | 原版 | 无直接工具测试 | 源码与注册存在，但缺少本轮真实调用证据 |
| A | `solidworks_add_component` | 是 | 原版 | tests/solidworks_add_component_regression.py, tests/test_engineering_orchestrator.py, tests/test_mcp_document_identity.py | 本轮或本会话已完成真实 SolidWorks 调用 |
| B | `solidworks_add_concentric_mate` | 是 | 原版 | tests/test_engineering_orchestrator.py | 源码与注册存在，但缺少本轮真实调用证据 |
| B | `solidworks_add_distance_mate` | 是 | 原版 | 无直接工具测试 | 源码与注册存在，但缺少本轮真实调用证据 |
| A | `solidworks_add_parallel_mate` | 否 | 新增 | 无直接工具测试 | 本轮或本会话已完成真实 SolidWorks 调用 |
| A | `solidworks_add_perpendicular_mate` | 否 | 新增 | 无直接工具测试 | 本轮或本会话已完成真实 SolidWorks 调用 |
| A | `solidworks_inspect_assembly` | 否 | 新增 | 无直接工具测试 | 本轮或本会话已完成真实 SolidWorks 调用 |
| B | `solidworks_interference_check` | 是 | 原版 | tests/test_mcp_discovery.py, tests/test_mcp_discovery_passthrough.py, tests/test_mcp_discovery_quality.py | 源码与注册存在，但缺少本轮真实调用证据 |
| B | `solidworks_replace_component_preserving_transform` | 是 | 原版 | tests/manual_native_wire_2026.py, tests/test_mcp_document_identity.py, tests/test_native_wire_mcp.py | 源码与注册存在，但缺少本轮真实调用证据 |
| B | `solidworks_set_component_fixed` | 是 | 原版 | 无直接工具测试 | 源码与注册存在，但缺少本轮真实调用证据 |
| B | `solidworks_set_component_suppression` | 否 | 新增 | 无直接工具测试 | 源码与注册存在，但缺少本轮真实调用证据 |
| A | `solidworks_set_material` | 否 | 新增 | 无直接工具测试 | 本轮或本会话已完成真实 SolidWorks 调用 |

## 工程图（7）

| 类别 | 工具 | 作者原版 | 当前源码/MCP | 测试引用 | 真机状态 |
|---|---|---|---|---|---|
| B | `solidworks_add_detail_view` | 否 | 新增 | 无直接工具测试 | 有实现/入口，但依赖选择条件或本轮未完成所需真机闭环 |
| B | `solidworks_add_drawing_view` | 否 | 新增 | 无直接工具测试 | 源码与注册存在，但缺少本轮真实调用证据 |
| B | `solidworks_add_section_view` | 否 | 新增 | 无直接工具测试 | 有实现/入口，但依赖选择条件或本轮未完成所需真机闭环 |
| A | `solidworks_generate_drawing` | 是 | 升级 | tests/solidworks_gdt_generation_live.py, tests/test_engineering_orchestrator.py, tests/test_mcp_drawing_tools.py | 本轮或本会话已完成真实 SolidWorks 调用 |
| A | `solidworks_insert_drawing_bom` | 否 | 新增 | 无直接工具测试 | 本轮或本会话已完成真实 SolidWorks 调用 |
| A | `solidworks_inspect_drawing` | 是 | 原版 | tests/test_engineering_orchestrator.py, tests/test_mcp_discovery.py, tests/test_mcp_drawing_tools.py | 本轮或本会话已完成真实 SolidWorks 调用 |
| B | `solidworks_review_drawing` | 是 | 原版 | tests/test_engineering_orchestrator.py, tests/test_mcp_drawing_tools.py | 有实现/入口，但依赖选择条件或本轮未完成所需真机闭环 |

## BOM 与交付（5）

| 类别 | 工具 | 作者原版 | 当前源码/MCP | 测试引用 | 真机状态 |
|---|---|---|---|---|---|
| B | `solidworks_batch_export_files` | 是 | 原版 | 无直接工具测试 | 有实现/入口，但依赖选择条件或本轮未完成所需真机闭环 |
| A | `solidworks_collect_bom` | 否 | 新增 | 无直接工具测试 | 本轮或本会话已完成真实 SolidWorks 调用 |
| B | `solidworks_export_assembly_bom` | 是 | 原版 | 无直接工具测试 | 源码与注册存在，但缺少本轮真实调用证据 |
| A | `solidworks_export_bom_excel` | 否 | 新增 | 无直接工具测试 | 本轮或本会话已完成真实 SolidWorks 调用 |
| B | `solidworks_pack_and_go` | 是 | 原版 | tests/test_mcp_document_identity.py | 源码与注册存在，但缺少本轮真实调用证据 |

## 钣金（3）

| 类别 | 工具 | 作者原版 | 当前源码/MCP | 测试引用 | 真机状态 |
|---|---|---|---|---|---|
| A | `solidworks_create_sheet_metal_base_flange` | 否 | 新增 | 无直接工具测试 | 本轮或本会话已完成真实 SolidWorks 调用 |
| A | `solidworks_export_flat_pattern_dxf` | 否 | 新增 | 无直接工具测试 | 本轮或本会话已完成真实 SolidWorks 调用 |
| A | `solidworks_inspect_sheet_metal` | 否 | 新增 | 无直接工具测试 | 本轮或本会话已完成真实 SolidWorks 调用 |

## 焊件（4）

| 类别 | 工具 | 作者原版 | 当前源码/MCP | 测试引用 | 真机状态 |
|---|---|---|---|---|---|
| A | `solidworks_create_weldment_profile` | 否 | 新增 | 无直接工具测试 | 本轮或本会话已完成真实 SolidWorks 调用 |
| A | `solidworks_create_weldment_structural_member` | 否 | 新增 | 无直接工具测试 | 本轮或本会话已完成真实 SolidWorks 调用 |
| A | `solidworks_export_weldment_cut_list` | 否 | 新增 | 无直接工具测试 | 本轮或本会话已完成真实 SolidWorks 调用 |
| A | `solidworks_inspect_weldment` | 否 | 新增 | 无直接工具测试 | 本轮或本会话已完成真实 SolidWorks 调用 |

## 检查与数据（9）

| 类别 | 工具 | 作者原版 | 当前源码/MCP | 测试引用 | 真机状态 |
|---|---|---|---|---|---|
| A | `solidworks_bounding_box` | 是 | 原版 | 无直接工具测试 | 本轮或本会话已完成真实 SolidWorks 调用 |
| B | `solidworks_health_check` | 是 | 原版 | tests/test_mcp_discovery.py, tests/test_mcp_discovery_passthrough.py | 源码与注册存在，但缺少本轮真实调用证据 |
| B | `solidworks_inspect_configurations` | 是 | 原版 | tests/test_mcp_configuration_tools.py | 源码与注册存在，但缺少本轮真实调用证据 |
| B | `solidworks_inspect_feature_tree` | 否 | 新增 | 无直接工具测试 | 源码与注册存在，但缺少本轮真实调用证据 |
| A | `solidworks_inspect_hole_features` | 是 | 原版 | tests/test_engineering_orchestrator.py | 本轮或本会话已完成真实 SolidWorks 调用 |
| A | `solidworks_inspect_native_geometry` | 是 | 原版 | tests/manual_native_wire_2026.py, tests/test_native_wire_mcp.py | 本轮或本会话已完成真实 SolidWorks 调用 |
| A | `solidworks_mass_properties` | 是 | 原版 | tests/test_mcp_discovery.py, tests/test_mcp_discovery_passthrough.py | 本轮或本会话已完成真实 SolidWorks 调用 |
| A | `solidworks_read_custom_properties` | 否 | 新增 | 无直接工具测试 | 本轮或本会话已完成真实 SolidWorks 调用 |
| B | `solidworks_rebuild_document` | 否 | 新增 | 无直接工具测试 | 源码与注册存在，但缺少本轮真实调用证据 |

## 运动分析（3）

| 类别 | 工具 | 作者原版 | 当前源码/MCP | 测试引用 | 真机状态 |
|---|---|---|---|---|---|
| B | `solidworks_add_rotary_motor` | 是 | 原版 | tests/test_engineering_orchestrator.py | 源码与注册存在，但缺少本轮真实调用证据 |
| B | `solidworks_inspect_motion_studies` | 是 | 原版 | 无直接工具测试 | 源码与注册存在，但缺少本轮真实调用证据 |
| B | `solidworks_validate_motion_study` | 是 | 原版 | tests/test_engineering_orchestrator.py | 源码与注册存在，但缺少本轮真实调用证据 |

## CAD Studio / 开放格式（16）

| 类别 | 工具 | 作者原版 | 当前源码/MCP | 测试引用 | 真机状态 |
|---|---|---|---|---|---|
| B | `cadstudio_build_dxf_preview_scene` | 是 | 原版 | tests/test_mcp_headless_open_format.py | 源码与注册存在，但缺少本轮真实调用证据 |
| B | `cadstudio_check_dfm` | 是 | 原版 | tests/test_mcp_discovery.py | 源码与注册存在，但缺少本轮真实调用证据 |
| B | `cadstudio_check_drc` | 是 | 原版 | tests/test_mcp_discovery.py | 源码与注册存在，但缺少本轮真实调用证据 |
| B | `cadstudio_check_routing` | 是 | 原版 | tests/test_mcp_discovery.py, tests/test_mcp_headless_open_format.py | 源码与注册存在，但缺少本轮真实调用证据 |
| B | `cadstudio_create_ocp_loft` | 是 | 原版 | tests/test_mcp_headless_open_format.py | 源码与注册存在，但缺少本轮真实调用证据 |
| B | `cadstudio_create_ocp_surface` | 是 | 原版 | tests/test_mcp_headless_open_format.py | 源码与注册存在，但缺少本轮真实调用证据 |
| B | `cadstudio_fea_preflight` | 是 | 原版 | 无直接工具测试 | 源码与注册存在，但缺少本轮真实调用证据 |
| B | `cadstudio_list_drc_rules` | 是 | 原版 | tests/test_mcp_discovery.py | 源码与注册存在，但缺少本轮真实调用证据 |
| B | `cadstudio_prepare_fea` | 是 | 原版 | tests/test_mcp_headless_open_format.py | 源码与注册存在，但缺少本轮真实调用证据 |
| B | `cadstudio_read_artifact` | 是 | 原版 | tests/test_mcp_http_transport.py | 源码与注册存在，但缺少本轮真实调用证据 |
| B | `cadstudio_resolve_backend` | 是 | 原版 | tests/test_mcp_backend_router.py | 源码与注册存在，但缺少本轮真实调用证据 |
| B | `cadstudio_review_advanced_geometry` | 是 | 原版 | tests/test_mcp_discovery.py | 源码与注册存在，但缺少本轮真实调用证据 |
| B | `cadstudio_routing_preflight` | 是 | 原版 | 无直接工具测试 | 源码与注册存在，但缺少本轮真实调用证据 |
| B | `cadstudio_run_fea` | 是 | 原版 | tests/test_mcp_headless_open_format.py | 源码与注册存在，但缺少本轮真实调用证据 |
| B | `cadstudio_run_fea_convergence` | 是 | 原版 | tests/test_mcp_headless_open_format.py | 源码与注册存在，但缺少本轮真实调用证据 |
| B | `cadstudio_write_open_format` | 是 | 原版 | tests/test_mcp_headless_open_format.py | 源码与注册存在，但缺少本轮真实调用证据 |

## C 类：已有底层实现但未接入 MCP

| 功能 | 现有源码/实现 | 接入方式 |
|---|---|---|
| 齿轮配合 | `scripts/sw_assembly.py::add_gear_mate_by_cylinders` | 新增组件+齿数/半径参数入口 |
| 旋转副 | `scripts/sw_assembly.py::add_revolute_joint_by_cylinders` | 新增组件+轴径范围参数入口 |
| 任意组件变换 | `apply_component_transform_x` | 新增 16 元素变换或位姿入口 |
| 草图弧/样条/手动尺寸/关系 | `sw_part.py` 的 `sketch_arc`、`sketch_spline`、`add_dimension`、`add_sketch_relation` | 新增曲线草图和约束编辑工具 |
| 草图质量检查 | `inspect_model_sketches` | 当前由 `solidworks_review_active` 间接返回，可增加直接入口 |
| 手动插入模型尺寸 | `insert_dimensions` | DrawingSpec 可间接执行，可增加当前视图直接调用入口 |
| 设置图纸格式 | `set_sheet_format` | 可通过生成器选择模板，可增加活动图纸格式修改入口 |
| 切割清单属性写入 | `set_cut_list_properties` | 焊件检查已读回，可增加受控写入入口 |
| 公差配合计算 | `check_tolerance_fit` | 纯计算函数，可增加无模型调用工具 |
| BOM 追溯报告 | `build_bom_traceability` | 可由现有 BOM/图纸报告结果组装 |

## D 类：当前源码没有实现

| 功能 | 判断依据 |
|---|---|
| 原生 Hole Wizard 特征 | `hole_wizard()` 为空实现，现有孔工具使用草图切除 |
| 旋转切除 | `sw_part.py` 只有旋转凸台 |
| 拔模 | 无 DraftFeatureData 封装 |
| 通用原生扫描/放样 | 只有受限圆截面扫描和 OCP 后端 |
| 装配体删除组件 | 无 MCP 删除入口，底层未完成安全封装 |
| 装配组件阵列 | 无新增源码入口 |
| 爆炸视图 | 无源码实现和 MCP 入口 |
| BOM 自动序号气泡 | 未发现 Balloon/StackedBalloon 封装或 MCP 工具 |
| 自动剖视/局部区域选择 | 仅能调用现成选中区域，未自动创建选择集 |
| 孔表、螺纹专项标注 | 无独立生成器 |
| 标题栏业务字段绑定 | 生成器明确标记不支持 |
| Edge Flange / Tab | 无底层封装 |
| Unfold / Fold | 无底层封装 |
| 焊珠/焊缝 | 无底层封装 |
| 批量打开和处理 | 只有批量导出/BOM/import 等单点能力 |
