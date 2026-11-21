# SolidWorks MCP 第三阶段工程图质量修复报告

测试日期：2026-11-20

环境：SolidWorks 2025、Windows、SolidWorks MCP 1.30.0

工具注册：93 个，数量未变

## 结论

| 项目 | 结果 | 证据 |
|---|---|---|
| 重复尺寸 | 通过 | 原始圆柱测试工程图插入 5 个 DisplayDimension，其中 Ø20 出现 3 次、10 mm 出现 2 次；修复后按原生尺寸身份删除 3 个重复显示，仅保留 1 个 Ø20 和 1 个 10 mm |
| 四视图 | 通过 | 零件图和装配图均实际包含前、俯、右、等轴测 4 个视图 |
| 标题栏 | 通过 | 图号、名称、材料、日期从源模型自定义属性解析并写入；字段越界、字段间重叠、与模板文字碰撞均为 0 |
| BOM | 通过 | 原生 BOM 表 5 行（表头 + 4 个零件），4 个图号正确，数量合计 4 |
| SLDDRW 保存/重开 | 通过 | 生成、保存、关闭、重新打开并由 `solidworks_inspect_drawing` / `solidworks_review_drawing` 复核 |
| PDF | 通过 | 三份 PDF 均可由 PyMuPDF 打开，A3 横向单页，无已确认视觉重叠 |
| 序号气泡 | 不支持 | 搜索未发现 SolidWorks 原生 BOM 序号气泡工具，本轮没有伪造气泡 |
| Ø8 尺寸完整性 | 未完全通过 | 自动模型尺寸未包含 Ø8；尝试结构化添加 Ø8 时，SW2025 工程图可见边枚举未返回目标圆边，写文件前终止 |

## 重复尺寸前后对比

- 修复前：Ø20 有 3 个显示尺寸，10 mm 有 2 个显示尺寸。
- 修复后：原生尺寸身份统计为 5 → 2；删除 3 个重复显示，最终 Ø20 和 10 mm 各 1 个。
- 去重键使用 `IDimension.FullName` 或原生持久绑定，不以数值相等作为删除依据，因此两个不同尺寸即使同值也不会被误合并。
- 删除后执行重建并重新枚举视图，最终 `dimension_duplicate_count = 0`。

## 标题栏修复

- 从零件/装配体文件级或活动配置级自定义属性读取 `PartNumber`、`Description`、`Material`、`Date`。
- 支持显式字段覆盖，支持 `propertyMap` 和 `fieldPositionsMm`。
- 长文字按单元格宽度换行，SolidWorks 的 `CRLF` 回读差异按等价换行处理。
- 标题栏字段使用独立的 `CAD_TITLE__*` 持久名称，保存重开后可回读。
- 审查器区分图框模板文字和正文注释，只把确认的正文侵入、模板碰撞和视觉重叠计为失败。
- 最终零件图、装配图：`outside_fields=[]`、`overlapping_fields=[]`、`template_collisions=[]`。

## 等轴测视图

- 根因一：通用预检把 `isometric` 当作不支持字段。
- 根因二：`CreateDrawViewFromModelView3` 需要 SolidWorks 当前语言的模型视图名；本机名称为 `*等轴测`，不是英文 `*Isometric`。
- 修复后先从已打开源模型的 `GetModelViewNames` 获取本地化名称，并保留语言回退候选。
- 零件图和装配图均生成真实 `*Isometric` 视图，保存重开后仍存在。

## 装配图 / BOM

| 序号 | 图号 | 名称 | 材料 | 数量 |
|---:|---|---|---|---:|
| 1 | MCP-A-001 | Workflow Part A | Q235-A | 1 |
| 2 | MCP-B-001 | Workflow Part B | Q235-A | 1 |
| 3 | MCP-C-001 | Workflow Part C | Q235-A | 1 |
| 4 | MCP-D-001 | Workflow Part D | Q235-A | 1 |

零件数：4；数量合计：4。BOM 是 SolidWorks 原生表，不是文本框拼接。

## 源码修改

- `<USER_HOME>\.codex\skills\solidworks-automation\subskills\solidworks-engineering-drawing\scripts\drawing_workflow.py`
  - 原生尺寸身份去重。
  - 等轴测布局、本地化视图名解析及创建。
  - 标题栏属性解析、换行、定位、持久命名和边界检查。
  - 审查前重复尺寸、标题栏碰撞和 PDF 视觉重叠门禁。
- `<USER_HOME>\.codex\skills\solidworks-automation\subskills\solidworks-engineering-drawing\scripts\drawing_review.py`
  - 重复尺寸核验。
  - 标题栏模板内部文字与正文注释分层处理。
  - PDF 仅把 `confirmedVisualDefect=true` 的重叠判为失败。
- `<USER_HOME>\.codex\skills\solidworks-automation\scripts\sw_drawing_package.py`
  - 在打开源模型后解析标题栏自定义属性。
  - 普通结构化尺寸允许 SW2025；GD&T 仍要求 SW2026。
- `<USER_HOME>\.codex\skills\solidworks-automation\scripts\sw_drawing_native.py`
  - 增加等轴测方向别名，同时保持前、俯、右三视图必需。
- 以下说明/测试同步更新：
  - `<USER_HOME>\.codex\skills\solidworks-automation\subskills\solidworks-engineering-drawing\SKILL.md`
  - `<USER_HOME>\.codex\skills\solidworks-automation\capabilities.yaml`
  - `<USER_HOME>\.codex\skills\solidworks-automation\tests\test_drawing_stage3_quality.py`
  - `<USER_HOME>\.codex\skills\solidworks-automation\tests\test_drawing_subskill.py`
  - `<USER_HOME>\.codex\skills\solidworks-automation\tests\test_default_drawing_template.py`

## 备份

备份目录：

`<USER_HOME>\Documents\Codex\2026-11-18\1\work\solidworks_drawing_stage3_backup_20261120`

其中包含修改前文件、`pre_stage3.patch`，以及后补文件的重建前版本。

## 测试

- 相关单元测试：69 项通过。
- 真实 MCP 会话：`server.py` 通过 stdio 现场加载；
- SolidWorks 2025：建模、保存、重开、视图读取、PDF 导出均由真实 COM 执行。
- 工具清单复核：93 个工具仍注册，新增功能没有减少或替换既有工具。
- Router、API Key、代理配置未修改。

## 交付文件

### 零件图（四视图、无重复尺寸）

- `<USER_HOME>\Desktop\SW插件测试\工程图质量修复验证_20261120\part_drawing_final2\ST3_Cylinder_Quality_Final.SLDDRW`
- `<USER_HOME>\Desktop\SW插件测试\工程图质量修复验证_20261120\part_drawing_final2\ST3_Cylinder_Quality_Final.pdf`
- `<USER_HOME>\Desktop\SW插件测试\工程图质量修复验证_20261120\part_drawing_final2\ST3_Cylinder_Quality_Final_review_report.json`
- `<USER_HOME>\Desktop\SW插件测试\工程图质量修复验证_20261120\final_review2\part\ST3_Cylinder_FinalReview.json`

### 装配图（四视图 + 原生 BOM）

- `<USER_HOME>\Desktop\SW插件测试\工程图质量修复验证_20261120\assembly_drawing_final3\ST3_Assembly_Quality.SLDDRW`
- `<USER_HOME>\Desktop\SW插件测试\工程图质量修复验证_20261120\assembly_drawing_final3\ST3_Assembly_Quality.pdf`
- `<USER_HOME>\Desktop\SW插件测试\工程图质量修复验证_20261120\assembly_drawing_final3\ST3_Assembly_Quality_review_report.json`
- `<USER_HOME>\Desktop\SW插件测试\工程图质量修复验证_20261120\final_review2\assembly\ST3_Assembly_FinalReview.json`

### 原始重复问题专项复验

- `<USER_HOME>\Desktop\SW插件测试\工程图质量修复验证_20261120\duplicate_dimension_final\ST3_Duplicate_Dimension_Test.SLDDRW`
- `<USER_HOME>\Desktop\SW插件测试\工程图质量修复验证_20261120\duplicate_dimension_final\ST3_Duplicate_Dimension_Test.pdf`
- `<USER_HOME>\Desktop\SW插件测试\工程图质量修复验证_20261120\duplicate_dimension_final\ST3_Duplicate_Dimension_Test_review_report.json`

## 已知限制

1. 本轮完成的是尺寸去重，不是模型草图尺寸自动补全。含孔零件当前自动导入的模型尺寸只有厚度 20 mm 和 R1；Ø8 没有被模型标记为工程图尺寸。
2. 尝试用 `requiredDimensions` 直接添加 Ø20/Ø8 时，SW2025 的 `GetVisibleEntities2` 没有返回可选择的圆边，因此结构化尺寸创建在落盘前中止。未改用假尺寸或修改模型绕过。
3. 搜索未发现 BOM 自动序号气泡工具，因此未生成气泡。
4. 模板自身的扫描级字体、线型、标题栏分区仍需按企业标准进行最终人工签审。
5. 旧 MCP 常驻进程在加载新源码前被停止后，本聊天内置连接显示 `Transport closed`；本轮后续真机调用改用同一 `mcp-server/server.py` 的全新 MCP stdio 会话完成。未改动 Router、API Key 或代理配置；重新打开/重连 MCP 后即可恢复常驻工具入口。

## 图片证据

- 零件图：`<USER_HOME>\Desktop\SW插件测试\工程图质量修复验证_20261120\part_drawing_final2\ST3_Cylinder_Quality_Final_full.png`
- 装配图：`<USER_HOME>\Desktop\SW插件测试\工程图质量修复验证_20261120\assembly_drawing_final3\ST3_Assembly_Quality_full.png`
- 重复尺寸专项：`<USER_HOME>\Desktop\SW插件测试\工程图质量修复验证_20261120\duplicate_dimension_final\ST3_Duplicate_Dimension_Test_full.png`
