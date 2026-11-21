# SolidWorks MCP 功能域审计矩阵

分类口径：

- **A**：作者 GitHub 原版已有源码、MCP 已注册，并且已有真实 SolidWorks 成功证据。
- **B**：作者 GitHub 原版已有源码和 MCP 注册，但已知失败、仅部分可用或尚未完成真机闭环。
- **C**：已有底层源码或已验证 COM 路径，但尚未接入 MCP。
- **D**：作者原版和当前本地源码都没有完整实现。

本地新增的 24 个工具不强行计入作者原版的 A/B/C。它们单独标记为本地扩展，其中 17 个已有真机成功证据，7 个仅有源码/注册。

## 1. 零件建模与特征

| 功能 | 类别 | 当前入口/源码 | 依据与限制 |
|---|---|---|---|
| 新建零件 | A | `solidworks_new_document` | 多次真机创建成功 |
| 基础矩形、圆、槽、多边形轮廓 | A | `solidworks_sketch_and_extrude` | 矩形轮廓和拉伸已真机验证 |
| 独立折线草图 | A | `solidworks_create_sketch_polyline` | 焊件型材真机创建成功 |
| 拉伸凸台 | A | `solidworks_sketch_and_extrude` | 多个零件创建成功 |
| 通用拉伸切除 | B | `solidworks_sketch_and_extrude(cut=true)` | 有入口，本轮通过专用孔工具验证了切除 |
| 旋转凸台 | B | `solidworks_revolve` | 已注册，本轮未真机验证 |
| 旋转切除 | D | 无 MCP，`sw_part.py` 也无专门封装 | 可由 `FeatureRevolve2(IsCut=True)` 新开发 |
| 圆截面扫描 | B | `solidworks_build_round_sweeps` | 有严格规格实现，本轮未真机验证 |
| 放样 | C/B | `cadstudio_create_ocp_loft` 等 | 已有独立 OCP 后端工具，本轮未真机验证 |
| 贯穿孔 | A | `solidworks_create_hole_feature` | 双端 Through All 真机通过 |
| 盲孔、沉孔、沉头孔、端槽 | B | `solidworks_create_hole_feature` | 源码和离线测试存在，本轮未逐一真机复验 |
| 原生 Hole Wizard | D | `hole_wizard()` 为空函数 | 当前孔为受控草图切除 |
| 圆角 | A | `solidworks_fillet` | 矩形板 R5 真机成功 |
| 倒角 | B | `solidworks_chamfer` | 有入口，本轮未真机验证 |
| 抽壳 | B | `solidworks_shell` | 有入口，本轮未真机验证 |
| 镜像 | B | `solidworks_mirror_feature` | 真机对凸台、圆角和孔特征均返回未创建 |
| 线性/圆周阵列 | B | `solidworks_pattern` | 已注册，本轮未真机验证 |
| 筋 | B | `solidworks_create_rib` | 本轮新接入，未做专项真机模型 |
| 拔模 | D | 无 DraftFeatureData 封装 | 需新增源码 |

## 2. 草图、尺寸与约束

| 功能 | 类别 | 当前入口/源码 | 依据与限制 |
|---|---|---|---|
| 直线草图 | A | `solidworks_create_sketch_polyline` | 真机成功 |
| 圆、矩形、槽、多边形 | B | `solidworks_sketch_and_extrude` | 矩形已真机，其他形状仅源码/测试 |
| 草图圆弧 | C | `sw_part.sketch_arc` | 有底层函数，未接入独立 MCP |
| 草图样条 | C | `sw_part.sketch_spline` | 有底层函数，未接入独立 MCP |
| 自动尺寸 | C | `sw_part.auto_dimension_sketch` | 有底层函数，创建基础零件内部使用 |
| 手动尺寸 | C | `sw_part.add_dimension` | 未暴露独立工具 |
| 手动几何关系 | C | `sw_part.add_sketch_relation` | 未暴露独立工具 |
| 草图约束质量读取 | C | `sw_sketch_quality.inspect_model_sketches` | 由 `solidworks_review_active` 间接返回 |
| 已有命名尺寸修改 | B | `solidworks_update_dimension` | 有工具和测试，本轮未真机验证 |

## 3. 装配体

| 功能 | 类别 | 当前入口/源码 | 依据与限制 |
|---|---|---|---|
| 新建装配体 | A | `solidworks_new_document` | 多次真机成功 |
| 插入零件/子装配 | A | `solidworks_add_component` | 4 组件装配真机成功 |
| 替换组件 | B | `solidworks_replace_component_preserving_transform` | 有源码/注册，本轮未真机验证 |
| 删除组件 | D | 无安全 MCP 入口 | `IAssemblyDoc.DeleteSelections` 可新开发 |
| 插入时固定 | A | `solidworks_add_component(fix_component=true)` | 真机成功 |
| 固定/浮动切换 | B | `solidworks_set_component_fixed` | 有入口，本轮未独立调用 |
| 抑制/恢复 | B | `solidworks_set_component_suppression` | 本轮新接入，未真机验证 |
| 重合配合 | B | `solidworks_add_coincident_mate` | 有源码，本轮未真机验证 |
| 同心配合 | B | `solidworks_add_concentric_mate` | 有源码，本轮未真机验证 |
| 距离配合 | B | `solidworks_add_distance_mate` | 有源码，本轮未真机验证 |
| 平行配合 | A | `solidworks_add_parallel_mate` | 真机创建并通过回读 |
| 垂直配合 | A | `solidworks_add_perpendicular_mate` | 真机创建并通过回读 |
| 角度配合 | A | `solidworks_add_angle_mate` | 真机创建并通过回读 |
| 配合状态回读 | A | `solidworks_inspect_assembly` | 3 个 Mate 均回读为 healthy |
| 装配结构和父子关系 | A | `solidworks_inspect_assembly` | 返回层级、路径、配置和变换 |
| 组件坐标 | A | `solidworks_inspect_assembly` | 返回毫米平移和旋转矩阵 |
| 装配体质量/边界框 | A | `solidworks_inspect_assembly` | 真机返回 B-Rep 包围和测量数据 |
| 装配体干涉检查 | B | `solidworks_interference_check` | 有源码/注册，本轮未真机验证 |
| 组件阵列 | D | 无组件阵列 FeatureData 封装 | 需新增 |
| 爆炸视图 | D | 无 MCP 实现 | `IAssemblyDoc.CreateExplodedView` 可开发 |
| 齿轮配合 | C | `add_gear_mate_by_cylinders` | 已实现底层流程，未注册 |
| 旋转副 | C | `add_revolute_joint_by_cylinders` | 已实现底层流程，未注册 |

## 4. BOM

| 功能 | 类别 | 当前入口/源码 | 依据与限制 |
|---|---|---|---|
| 顶层 BOM 读取 | A | `solidworks_collect_bom` | 4 组件真机读取 |
| 递归/多级 BOM | B | `solidworks_collect_bom` | 递归算法存在，本轮装配全是顶层组件 |
| 父件/子件路径 | A/B | occurrence 字段 `parent_component`、`parent_path` | 顶层为空，深层结构本轮无样本 |
| 图号/名称/材料/数量 | A | `solidworks_collect_bom` | 4 行均正确 |
| 配置区分 | A | `configuration` 字段 | 返回 `默认<按加工>` |
| 相同文件/配置合并 | A | 路径+配置分组 | 4 个零件各 1 件 |
| 排除 `ExcludeFromBOM` | B | `include_excluded` | 有实现，本轮没有被排除样本 |
| 自定义 BOM 列 | B | `columns` 参数 | 有单元测试，本轮未提供额外有效属性 |
| BOM Excel | A | `solidworks_export_bom_excel` | 真机生成并打开 |
| BOM CSV | B | `solidworks_export_assembly_bom` | 原版工具，本轮未真机调用 |
| 工程图 BOM 表 | A | `solidworks_insert_drawing_bom` | 原生 BOM 表 5 列、4 数据行 |
| 自动序号气泡 | D | 无源码/MCP | 需新增 Balloon API |

## 5. 工程图

| 功能 | 类别 | 当前入口/源码 | 依据与限制 |
|---|---|---|---|
| 新建 A3 横向图纸 | A | `solidworks_generate_drawing` | GB A3 真机成功 |
| 主视/俯视/右视图 | A | `solidworks_generate_drawing` | 3 个关联视图真实存在，比例 1:2 |
| 单视图/等轴测视图 | B | `solidworks_add_drawing_view` | 有工具，本轮未独立调用 |
| 第一角投影 | A | DrawingSpec + `CreateFirstAngleViews2` | 图面位置已回读 |
| 投影视图 | A | 标准三视图链 | 正常 |
| 剖视图 | B | `solidworks_add_section_view` | 需要人工预选剖切线，未自动化选择 |
| 局部放大视图 | B | `solidworks_add_detail_view` | 需要人工预选局部区域 |
| 自动模型尺寸 | B | DrawingSpec / `insert_dimensions` | 框架存在，本轮未提供尺寸规格 |
| 手动尺寸 | C | `insert_dimensions` | 有底层实现，无独立 MCP 工具 |
| 孔标注/孔表 | D/B | 仅有部分结构化要求入口 | 无通用孔表/螺纹专项生成器 |
| 中心标记 | B | DrawingSpec `centerMarks` | 单元测试存在，本轮未真机调用 |
| 中心线/粗糙度/焊接符号 | C | 相关读取与专项代码 | 无通用稳定生成入口 |
| GD&T | B | DrawingSpec / 原生 GD&T 路径 | 有实现，限制 SW2026 原生上下文；本轮未验证 |
| 标题栏业务字段绑定 | D | 预检明确返回不支持 | 现有模板标题栏无法自动绑定图号/名称 |
| 工程图 BOM 表 | A | `solidworks_insert_drawing_bom` | 真机通过 |
| 图纸结构检查 | A | `solidworks_inspect_drawing` | 三视图和 BOM 表均回读 |
| 工程图完整审查 | B | `solidworks_review_drawing` | 工具存在，本轮只调用检查器 |
| PDF | A | `solidworks_export_active` | 修复后真机导出并用 PyMuPDF 打开 |

## 6. 原生钣金

| 功能 | 类别 | 当前入口/源码 | 依据与限制 |
|---|---|---|---|
| Base Flange | A | `solidworks_create_sheet_metal_base_flange` | 原生父特征和 BaseFlange 均真机存在 |
| 板厚/折弯半径/K 因子 | A | Base Flange 参数与证据回读 | 2 mm、2.5 mm、0.42 回读正确 |
| 钣金实体语义 | A | `solidworks_inspect_sheet_metal` | 所有实体均为 SheetMetal |
| FlatPattern 特征 | A | SolidWorks 原生生成并检查 | 真机存在 |
| 展开 DXF | A | `solidworks_export_flat_pattern_dxf` | 真机生成 |
| 折弯线输出 | A | DXF 导出选项 | 本次启用 |
| Edge Flange | D | 无底层封装 | 需实现 EdgeFlangeFeatureData |
| Tab | D | 无底层封装 | 需新增 |
| Unfold/Fold | D | 无底层封装 | 需实现 FoldsFeatureData |

## 7. 焊件

| 功能 | 类别 | 当前入口/源码 | 依据与限制 |
|---|---|---|---|
| 自定义 `.sldlfp` 型材 | A | `solidworks_create_weldment_profile` | 真机生成 |
| 外部型材路径 | A | structural member 输入 | 真机使用 |
| 型材库浏览 | D | 无 MCP | 需新增目录检索、预览和选择 |
| Structural Member | A | `solidworks_create_weldment_structural_member` | WeldMemberFeat 真机存在 |
| 切割清单 | A | `solidworks_inspect_weldment` | CutListFolder 和属性回读 |
| 长度与数量 | A | 切割清单属性 | 长度 200、数量 1 真机回读 |
| 切割清单 CSV | A | `solidworks_export_weldment_cut_list` | 真机生成 |
| 焊缝/焊珠 | D | 无 WeldmentBeadFeatureData 封装 | 需新增 |

## 8. 材料、属性和配置

| 功能 | 类别 | 当前入口/源码 | 依据与限制 |
|---|---|---|---|
| 物理材料设置 | A | `solidworks_set_material` | Q235A 真机回读 |
| 质量/体积/惯量 | A | `solidworks_mass_properties` | 多零件与装配体真机读取 |
| 自定义属性写入 | A | `solidworks_set_custom_properties` | 真机成功 |
| 自定义属性读取 | A | `solidworks_read_custom_properties` | 真机成功 |
| 配置检查 | B | `solidworks_inspect_configurations` | 有入口，本轮未调 |
| 创建/激活配置 | B | `solidworks_create_configuration`、`activate_configuration` | 有入口和测试，本轮未真机 |
| 材料库浏览 | D | 无 MCP | 需新增数据库枚举 |

## 9. 文件与批量

| 功能 | 类别 | 当前入口/源码 | 依据与限制 |
|---|---|---|---|
| 新建/打开/保存/另存 | A | 文档工具 | 均真机成功 |
| 关闭文档 | A | `solidworks_close_documents` | 多次成功 |
| STEP | A | `solidworks_export_active` | 真机成功 |
| STL | B | `solidworks_export_active` | 有实现，本轮未调用 |
| IGES | B | `solidworks_export_active` | 有实现，本轮未调用 |
| Parasolid | B | `solidworks_export_active` | 有实现，本轮未调用 |
| PDF | A | `solidworks_export_active` | 修复后成功并可打开 |
| DXF | A | `solidworks_export_active` | 工程图和展开图成功 |
| DWG | A | `solidworks_export_active` | 工程图真机成功 |
| 批量导出 | B | `solidworks_batch_export_files` | 有实现，PDF 修复后尚未单独复验 |
| Pack and Go | B | `solidworks_pack_and_go` | 有单元测试，未在本轮真机复验 |
| 批量打开/批量修改 | D | 无 MCP | 需任务队列和事务设计 |

## 最终分类数量

- 作者原版 A 类：19 个
- 作者原版 B 类：50 个
- 作者原版 C 类：10 个底层能力组
- 作者原版和当前源码均未实现：15 个功能项
- 本地扩展已真机成功：17 个
- 本地扩展已注册但尚未真机闭环：7 个

全部 93 个当前工具的逐项来源、注册、测试引用和真机状态见 `Tool_Status_Matrix.md`。
