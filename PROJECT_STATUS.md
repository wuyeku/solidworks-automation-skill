# Project Status

最后更新：2026-11-22

## 当前定位

本项目是 `wzyn20051216/solidworks-automation-skill` 的个人长期维护分支。正式 MCP 配置已切换到 D 盘源码和 D 盘独立虚拟环境，C 盘环境保留为回滚方案。工程图模板、图幅、标题栏和图纸格式切换修复已完成离线与 SolidWorks 2025 真机验证，隔离启动的新代码 MCP 也已完成同源 DXF、PDF 和 DWG 回归。当前 Codex GUI 仍连接修复前启动的旧 MCP 进程，正式 GUI 重连尚未执行。

## 当前路径

| 用途 | 路径 |
|---|---|
| 正式运行 MCP 源码 | `D:\Projects\SolidWorks-MCP` |
| C 盘回滚 MCP 源码 | `%USERPROFILE%\.codex\skills\solidworks-automation` |
| D 盘本机验证数据 | `D:\Projects\SolidWorks-MCP-Data` |
| 正式 MCP 配置 | `%USERPROFILE%\.codex\config.toml` |
| Router 源码 | `%LOCALAPPDATA%\codex-router` |

## AI 工作入口

- 跨聊天、跨 AI、跨电脑的统一流程为 `docs/AI_WORKFLOW.md`。
- 任何新任务必须先阅读 `AGENTS.md` 和 `docs/AI_WORKFLOW.md`。
- 开发、测试、审查、收尾和交接以该协议为准，具体领域步骤继续由 Skill 和能力矩阵提供。

## Git 状态

- 上游声明版本：v2.1.1
- 本地维护标识：`2.1.1+local.93-tools`
- 作者上游：`https://github.com/wzyn20051216/solidworks-automation-skill.git`
- 上游最新基线：`36bc337357723b9763759ff06e4a1afab990b823`
- D 盘开发分支：`feature/stage5-93-tools`
- 当前 HEAD：`239280de8dfd9ed257733eb210ca108200b5798f`
- 个人 `origin`：`https://github.com/wuyeku/solidworks-automation-skill.git`
- 作者 `upstream`：`https://github.com/wzyn20051216/solidworks-automation-skill.git`
- `upstream` push URL：`DISABLED`
- 首次本地逻辑提交：7 个
- 状态固化提交：1 个
- 首次 Git 版本：8 个提交，均已推送；其后新增 AI 工作协议和 D 盘迁移收尾提交
- 当前分支跟踪：`origin/feature/stage5-93-tools`
- 当前本地 HEAD 与 `origin/feature/stage5-93-tools` 一致，提交差异为 `0 / 0`
- 当前工作区包含钣金工程图源码、测试和项目知识更新
- 当前未提交文件：10 个已跟踪修改文件
- 当前暂存文件：0
- 当前未跟踪文件：3 个，分别是 `scripts/sheet_metal_geometry.py`、`scripts/sw_drawing_sheet_metal.py` 和 `tests/test_sheet_metal_drawing.py`
- 当前提交已与个人远程开发分支同步，工作区修改和 3 个新文件尚未提交或推送
- 当前远端状态：双远端已配置，两个远端均已完成 fetch
- `origin/main` 和 `upstream/main` 当前均为 `36bc337`
- 当前开发分支相对两个 `main` 继续保持本地领先，具体差异以当前 Git 只读命令为准
- 2026-11-21 迁移验证：639 个受管及未跟踪文件哈希一致
- 作者完整历史：350 个提交
- 2026-11-21 第七阶段以只读 Git 命令重新核验了当前分支、HEAD、远端、跟踪关系和工作区状态
- 2026-11-22 S2 收尾再次以只读 Git 命令核验了当前分支、HEAD、远端跟踪和工作区状态
- 2026-11-22 工程图模板专项完成两个本地提交，并按已审核清单执行提交前检查，尚未推送

## 首次本地提交

| 顺序 | Commit | 内容 |
|---:|---|---|
| 1 | `e4f801c279b92efe744cb057fe7e8fee34f80648` | 项目治理基础 |
| 2 | `af682a7cfb723c73e9cab58c6a4e12bcc5e2f121` | 原生执行器、文档定位和建模修复 |
| 3 | `8b463016ccddc496d7d57ac9be4b5f4cd2998d51` | 工程图自动化 |
| 4 | `62da4aabed50162b8ff114f74d5fbe5bf9f1e530` | 93 工具 MCP 工具面 |
| 5 | `2a74d8616158e822769f1a7a3da05a7da7af5fca` | 93 工具能力说明 |
| 6 | `dc0891293565ac47bc5d38dd910938e73953c77c` | 阶段和真机验收证据 |
| 7 | `2d450696b04dff25b7d86266b0919e6faa5b9f0d` | 迁移状态和首次提交项目快照 |
| 8 | `8d28e5b0711cba3864d9ce808f900dd172081339` | 固化首次提交状态并统一 noreply 邮箱后推送 |

以上 8 个提交均仅包含预先批准的明确文件路径。异常文件 `$null` 未进入任何提交。全部提交的作者和提交者邮箱均为 GitHub noreply 地址。

## 工具状态

- 业务工具：93
- 发现入口：3
- 默认模式：`SW_MCP_DISCOVERY=search`
- 历史基线：作者原版 69 个业务工具
- 本地新增：24 个工具
- 本地升级：3 个已有工具
- 原有功能：66 个工具

## 已完成阶段

### 第一阶段，功能扩展

完成了零件、装配、工程图、BOM、钣金、焊件、检查和交付工具扩展，业务工具数量由 69 增加到 93。

### 第二阶段，基础修复

完成了镜像特征、批量导出、剖视图和局部放大相关的源码修复与定向真机验证。

### 第三阶段，工程图质量

完成了重复尺寸去重、标题栏属性关联、四视图、原生 BOM 和 PDF 导出的修复与验证。

### 第四阶段，工程图自动化

完成了 Ø20 外形和 Ø8 孔的自动尺寸标注，以及 SolidWorks 原生 BOM 自动序号气泡验证。

### 第五阶段，属性数据链

完成了零件和装配体属性卡模板、文件级与配置特定属性、工程图 `$PRPSHEET` 标题栏链接、原生 BOM 表面处理列和 Excel BOM 属性关联。

### 第六阶段，Codex 受控重启与旧连接释放

Codex 已正常重启。旧 ChatGPT、App Server、三个 C 盘 SolidWorks MCP 和旧 D 盘 MCP 进程均已退出，SolidWorks 2025 没有被关闭或重启。重启后的新会话重新从正式配置加载 D 盘 MCP。

重启后正式验收观察到：

- ChatGPT 主进程：`11084`
- App Server：`61512`
- D 盘 MCP 入口：`62848`
- D 盘 MCP Python 解释器：`61472`
- SolidWorks：`52412`
- C 盘 SolidWorks MCP 进程数：`0`
- D 盘 SolidWorks MCP 进程数：`2`

### 第七阶段，D 盘迁移最终收尾

- 正式 `config.toml` 仍指向 `D:\Projects\SolidWorks-MCP\.venv\Scripts\python.exe` 和 `D:\Projects\SolidWorks-MCP\mcp-server\server.py`。
- 重启后 D 盘 MCP 的健康检查、3 个发现入口、93 个业务工具及 Schema 验证通过。93 是本次验收结果，不作为永久固定数量承诺。
- 实际 `PropertyChain_Part_A.SLDPRT` 只读读取通过。
- 原 v3 监控脚本错误地把基线有效后消失的预期进程继续视为异常身份，导致旧重启监控返回 exit 3。修复版已独立保存在 `D:\Projects\SolidWorks-MCP-Data\backups\monitor_script_fix_20261121_201013`，原始脚本和日志未覆盖。
- Windows PowerShell 5.1 模拟测试全部通过：正常退出 `0`、陈旧基线 `2`、超时 `3`、PID 复用 `2`、保护进程丢失 `3`。
- 本轮没有再次运行真实 Codex 退出监控。

### S2 阶段，复杂工程图导出专项

- S2.3 使用最小独立工程图验证了正常打开和只读打开下的 DXF/DWG 直接 COM 导出。
- S2.4 通过正式 D 盘 MCP 完成最小工程图 PDF、DXF、DWG 三状态批量导出，9/9 成功。
- S2.5 定位了 2026-11-19 的历史复杂工程图失败证据。历史结果中 PDF 成功，DXF/DWG 的 `SaveAs` 失败，历史记录为错误码 1。
- S2.6 使用 SolidWorks 原生 Pack and Go 建立复杂工程图独立副本。闭态引用闭包通过，但正常打开后立即出现 `GetSaveFlag=true`，按安全规则停止导出。
- S2.6.1 确认测试工程图为一页 A3、三个模型视图和一个原生 BOM，全部引用位于独立 Pack 目录。应用 `IModelDocExtension.NeedsRebuild2` 后，工程图和依赖均为 `0`。
- S2.6.2 对照确认原始复杂工程图副本在正常和只读首次打开时都会出现 dirty。执行一次 `Save3(1)` 后 `GetSaveFlag=false`，随后正常和只读重开均为 clean。保存只改变工程图文件，装配体和四个零件哈希不变。
- S2.7 使用三套独立 Pack and Go 副本完成未打开、正常打开和只读打开状态的正式 MCP 导出，共 9/9 成功。PDF、DXF、DWG 均完成独立内容验证，DWG 已通过 AutoCAD 2025 只读重开。
- S2.7 中 A 组首次 PDF 为 `was_open=false`，随后 DXF/DWG 因 `close_documents=false` 为 `was_open=true`。这形成了未打开状态 DXF/DWG 的独立覆盖缺口。
- S2.7 的三套 Pack and Go 副本中，四份零件哈希一致。工程图和装配体因各自目录的绝对引用被原生重写而哈希不同，因此 S2.7 汇总保留 `review_required`，但九次导出本身全部成功。
- S2.7.1 使用 A 组同一复杂工程图补测完全未打开状态，DXF 和 DWG 的正式 MCP 调用均为 `was_open=false`、`api_success=true`、`produced_this_run=true`，两次调用均使用 `close_documents=true`。
- S2.7.1 两次调用后目标工程图、装配体和四个零件均完全卸载，用户原有文档未关闭。
- S2.7.1 DXF 与 S2.7 A 组的版本、毫米单位、图层、实体计数、文字和 BOM 一致。71 个 MTEXT 插入点存在仅 Y 方向的最大 `0.088818 mm` 位移，没有 X 位移或其他实体差异，仍需人工目视复核。
- S2.7.1 DWG 与 S2.7 A 组的实体、图层、文字、BOM 块和布局一致，AutoCAD 2025 只读检查前后哈希一致。
- S2.7.1 汇总的 `source_change_required=false`。基于当前已完成的验证范围，正式源码无需修改；S2.7 和 S2.7.1 也未修改功能源码。
- 本轮未复现历史 DXF/DWG `SaveAs` 错误码 1，也未找到其唯一根因。

### 工程图模板与标题栏修复专项

- 修正 SolidWorks 2025 图幅枚举为 A4=6、A4P=7、A3=8、A2=9、A1=10、A0=11，用户自定义格式使用 12。
- 未指定图幅时读取 SolidWorks 当前默认 `.drwdot`。指定图幅时从已配置模板目录选择实际尺寸匹配的标准模板，并阻断文件名与真实尺寸不一致的模板。
- 显式模板优先，同时验证实际图幅。A4 请求搭配 A3 模板会返回 `DRAWING_TEMPLATE_SIZE_MISMATCH`，不会创建工程图。
- 标题栏写入前读取模板已有属性链接，支持 `$PRPSHEET:"PartNumber"` 和 `$PRPSHEET:{PartNumber}` 等表达式。模板已提供对应字段时不再重复插入。
- 标题栏字段语义匹配限制在目标标题栏区域内，图面其他位置的同名属性不会阻止标题栏写入。
- 只有 `overwriteExistingFields=true` 或 `manualOverride=true` 才允许额外插入字段。字段截断返回 `review_required`。
- `SetupSheet6` 回退路径使用 `RemoveModifiedNotes=True`，并回读实际模板路径、图幅、方向和投影法。普通用户注释在切换、保存和重开前后均有身份快照保护。
- 出图包在用户已有 8 个文档时允许增加一个受控临时工程图，并在会话退出时只关闭该临时文档。
- MCP 的 `solidworks_generate_drawing` 参数已完整传递至兼容入口和出图包，消除了兼容层未转发显式模板的问题。
- 完整离线回归最新结果为 `1786 passed, 18 skipped`。
- SolidWorks 2025 真机验证覆盖 A0、A1、A2、A3、A4 模板创建，默认 A4，显式 A3，标题栏跳过插入，长字段阻断，保存重开和用户注释保护。
- 以一次性隔离 STDIO MCP 启动最新源码后，默认 A4、显式 A3、模板尺寸不一致阻断、标题栏跳过、属性链接和保存重开均通过。
- Codex 重启后 GUI 新 MCP 连接验收通过。实际健康检查返回 D 盘 Python、D 盘 `server.py`，实际 `solidworks_generate_drawing` Schema 包含 `drawing_template_path`，当前进程命令行指向 D 盘 Server，进程启动时间晚于两个本地提交。
- 使用同一张干净 A3 工程图完成手动 SolidWorks DXF 与隔离 MCP DXF 对照。两份文件均为 AC1015、毫米单位、147 个实体和 57 个 MTEXT。
- 两份 DXF 的全部实体、文字内容、插入坐标、图层、样式、3.5 mm 字高、宽度、旋转、对齐、图框和标题栏一致。去除指纹 GUID 和时间戳后，DXF 非易变内容完全相同。
- AutoCAD 2025 原生只读对照确认全图、横向图框、纵向图框和标题栏一致。未发现新增文字、缺失文字、重复程序字段或错位。
- PDF/DWG 最小回归通过。PDF 为单页 A3 横向，57 个可提取文字片段均使用 `HYSWLongFangSong` 字体样式。DWG 的 147 个实体与已验证 MCP DXF 在 `1e-7 mm` 容差内一致，最大数值偏差为 `4.860112312599085e-11 mm`。
- 干净 A3 零件图不含 BOM 表，因此本次 PDF/DWG 与 DXF 的 BOM 内容检查标记为不适用，不以标题栏代替 BOM 验收。

### FC702033-A 钣金工程图专项，暂停开发

- 当前阶段标记为 **暂停开发 / REVIEW_REQUIRED，人工制图质量未通过**。现有 PDF 和 SLDDRW 是自动化测试产物，不能作为已完成的制造放行图纸。
- 本轮新增了原生平板展开视图、DXF 几何识别、多图纸、展开坐标表、局部视图和成形/展开尺寸所有权等源码能力。
- 展开页使用 A2 横向、1:5 原生平板视图，按 4×19 分块写入 19 个圆孔、52 个非圆形切口和 3 条折弯线，共 74 个唯一 ID。缺失、重复和未知 ID 均为 0。
- 程序文字为 3.5 mm，表内行距 5.6 mm，列距 136 mm。内部越界、结构化碰撞和 PDF 矢量文字重叠检查为 0。
- 独立副本仅写入来自图纸规格的图号和名称属性，未修改原件，未添加公差、基准、形位公差、粗糙度或未确认材料。
- 源码执行器和部分自动审查通过，最终测试目录为 `D:\Projects\SolidWorks-MCP-Data\validation\FC702033-A_sheet_metal_development_20261122_223454`。完整离线回归为 `1792 passed, 18 skipped`。
- 人工制图质量未通过。实际问题是成形状态视图布局差、总体和结构尺寸标注不足、展开图阅读性差、局部放大区域缺少有效加工标注。
- 当前成形页只有 3 个原生总体尺寸，不能视为完整成形状态工程图。展开信息主要依赖坐标表，不能仅因表格覆盖完整就宣称工程图标注完整。
- 两页标题栏虽然显示 `FC702033-A` 和正确比例，但材料仍为 `<未指定>`。第一页模板仍保留 `v:\updated cs\a2 - gb.slddrt` 名称引用。
- 当前 Codex 常驻 MCP 仍加载旧模块，调用新钣金规格返回 `DRAWING_SHEET_METAL_OPTIONS_UNSUPPORTED`。按限制未重启服务。
- 隔离 MCP 已加载本轮源码并运行到生成 SLDDRW 和 PDF，但 PDF 后的跨进程稳定化在 MCP 子进程环境中超时。正式 MCP 端到端尚未通过。
- 源码、测试、FAIL 证据和上述未提交状态全部保留。本次暂停不改变 Git 跟踪关系。

## 重要功能与验收证据

证据等级依次区分源码注册、Schema 可读、离线通过、SolidWorks 2025 真机通过和交付文件重开验证。完整机器证据保存在 `D:\Projects\SolidWorks-MCP-Data`，目录中的模型、图纸、图片和大型 JSON 不作为公开仓库内容。

| 重要功能 | 验证日期 | 可公开验收报告 | 数据证据 |
|---|---|---|---|
| 93 个业务工具和 3 个发现入口 | 2026-11-18、2026-11-21 | `docs/VALIDATION/2026-11-18-stage1-upgrade.md`、`docs/VALIDATION/validate-mcp-20261121.json` | `docs/VALIDATION/mcp-inventory-20261121.json` |
| 零件、装配、工程图、BOM、钣金和焊件完整工作流 | 2026-11-18 | `docs/VALIDATION/2026-11-18-stage1-upgrade.md` | `D:\Projects\SolidWorks-MCP-Data\validation\legacy_20261121\codex_outputs\solidworks_mcp_full_workflow_20261118_231842\full_mcp_workflow_result.json` |
| 活动文档定位和三个只读检查工具 | 2026-11-20 | `docs/VALIDATION/2026-11-20-active-document-fix.md` | 报告内记录 `workflow_part_A.SLDPRT` 的真实 MCP 回读结果 |
| 镜像特征 | 2026-11-19 | `docs/VALIDATION/2026-11-19-stage2-fixes.md` | `D:\Projects\SolidWorks-MCP-Data\validation\legacy_20261121\desktop_sw_tests\第二阶段修复验证\mirror_mcp_updated\MCP_Mirror_Updated_Result.json`、`...\mirror_final\Mirror_Final_Real_Tests.json` |
| 批量 STEP/PDF/DXF/DWG 导出 | 2026-11-19 | `docs/VALIDATION/2026-11-19-stage2-fixes.md` | `D:\Projects\SolidWorks-MCP-Data\validation\legacy_20261121\desktop_sw_tests\第二阶段修复验证\batch_export_20261119_224700\MCP_Updated_Batch_Result.json`、`Export_Content_Validation.json`、`DWG_Reopen_Validation.json` |
| 装配工程图审查 | 2026-11-19 | `docs/VALIDATION/2026-11-19-stage2-fixes.md` | `D:\Projects\SolidWorks-MCP-Data\validation\legacy_20261121\desktop_sw_tests\第二阶段修复验证\drawing_review_assembly_spec\stage2_assembly_drawing_review.json` |
| 剖视图和局部放大 | 2026-11-19 | `docs/VALIDATION/2026-11-19-stage2-fixes.md` | `D:\Projects\SolidWorks-MCP-Data\validation\legacy_20261121\desktop_sw_tests\第二阶段修复验证\section_detail_mcp\MCP_Section_Success.json`、`MCP_Detail_Success.json`、`MCP_NoSelection_Errors.json` |
| 重复尺寸、标题栏、四视图和原生 BOM | 2026-11-20 | `docs/VALIDATION/2026-11-20-stage3-drawing-quality.md` | `D:\Projects\SolidWorks-MCP-Data\validation\legacy_20261121\desktop_sw_tests\工程图质量修复验证_20261120\part_drawing_final2\ST3_Cylinder_Quality_Final_review_report.json`、`...\assembly_drawing_final3\ST3_Assembly_Quality_review_report.json`、`...\duplicate_dimension_final\ST3_Duplicate_Dimension_Test_review_report.json` |
| Ø20 外形和 Ø8 孔自动尺寸 | 2026-11-20 | `docs/VALIDATION/2026-11-20-stage4-drawing-automation.md` | `D:\Projects\SolidWorks-MCP-Data\validation\legacy_20261121\desktop_sw_tests\工程图质量修复验证_20261120\diameter_dimension_final2\ST3_Diameter_Final_review_report.json` |
| 原生 BOM 自动序号气泡 | 2026-11-20 | `docs/VALIDATION/2026-11-20-stage4-drawing-automation.md` | `D:\Projects\SolidWorks-MCP-Data\validation\legacy_20261121\desktop_sw_tests\工程图质量修复验证_20261120\bom_balloons_final2\ST3_Assembly_Balloons_Final_review_report.json` |
| 属性卡、标题栏、原生 BOM 和 Excel BOM 属性链 | 2026-11-20 | `docs/VALIDATION/2026-11-20-stage5-property-chain.md` | `D:\Projects\SolidWorks-MCP-Data\validation\legacy_20261121\desktop_sw_tests\属性关联验证_20261120\partA_card_association.json`、`...\assembly_drawing_final5\PropertyChain_Assembly_Final_review_report.json`、`...\assembly_bom\PropertyChain_BOM_Final.xlsx` |
| D 盘离线回归 | 2026-11-21 | `docs/VALIDATION/offline-tests-20261121.json`、`docs/VALIDATION/venv-offline-tests-20261121.json` | 1751 passed、18 skipped、0 failed |
| SolidWorks 2025 真机连接和几何回读 | 2026-11-21 | `docs/VALIDATION/live-sw2025-20261121.json`、`docs/VALIDATION/venv-live-geometry-20261121.json` | 连接、边界框、质量、材料和特征树回读通过 |
| D 盘迁移和恢复演练 | 2026-11-21 | `docs/VALIDATION/2026-11-21-migration.md`、`docs/VALIDATION/full-bundle-restore-proof-20261121.json` | `backup-summary-20261121.json`、`source-migration-proof-20261121.json`、`final-project-state-20261121.json` |
| S2.7 复杂工程图三状态正式 MCP 导出 | 2026-11-22 | 本文件 | `D:\Projects\SolidWorks-MCP-Data\validation\S2.7-20261122_010514_796344` |
| S2.7.1 未打开状态 DXF/DWG 独立补测 | 2026-11-22 | 本文件 | `D:\Projects\SolidWorks-MCP-Data\validation\S2.7.1-20261122_105430_834589` |
| 模板、图幅和标题栏修复及隔离 MCP 验收 | 2026-11-22 | 本文件 | `D:\Projects\SolidWorks-MCP-Data\validation\SW-MCP-integration-template-20261122_150705` |
| 同源 DXF 手动与 MCP 对照 | 2026-11-22 | 本文件 | `D:\Projects\SolidWorks-MCP-Data\validation\SW-MCP-DXF-same-source-20261122_152112` |
| PDF/DWG 最小回归 | 2026-11-22 | 本文件 | `D:\Projects\SolidWorks-MCP-Data\validation\SW-MCP-final-pdf-dwg-20261122_153725` |

公开摘要文件当前 SHA-256：

| 文件 | SHA-256 |
|---|---|
| `docs/VALIDATION/2026-11-18-stage1-upgrade.md` | `A933984D967D984442F002688221B9B29A6CE02E987AEFDF98D810BC2AE4664B` |
| `docs/VALIDATION/2026-11-19-stage2-fixes.md` | `AD087BFFDA9154F33C01F1441B725AE3980613857B3C48FF8AD4E393752602F8` |
| `docs/VALIDATION/2026-11-20-active-document-fix.md` | `717F80A36199FB7F6F522E2F32B7AFC2FF6C283C7106B02E0C821AA434CDF517` |
| `docs/VALIDATION/2026-11-20-stage3-drawing-quality.md` | `6D6B07E0561CA223D91E4A30AD1FFEC2D40AFAEA7A720BA8D699CD19B31A354F` |
| `docs/VALIDATION/2026-11-20-stage4-drawing-automation.md` | `9D7456CCB1B9DA0D09695F3B51159411A0308DC1E03C8375B6FC4B93363ECBA7` |
| `docs/VALIDATION/2026-11-20-stage5-property-chain.md` | `3E894703D7B339CE108C84F3912F4215319E1CF6427E1134C59A0D1C4A936CAC` |
| `docs/VALIDATION/validate-mcp-20261121.json` | `DA0F74EEB8F66D448864A76B69B698C333EF2E49E0E0E107F381E720C2B438A1` |
| `docs/VALIDATION/mcp-inventory-20261121.json` | `D99A109F26420400C717E640561D5309F202A0C6C72B9E934ABD125415A61D4E` |
| `docs/VALIDATION/offline-tests-20261121.json` | `FDCC4637519BBFF58EF5DCBC45FC1451F6DB9816AF374DCD33D81997038117B5` |
| `docs/VALIDATION/live-sw2025-20261121.json` | `759C2CF5291350D2E65A6D3645B9EEAD3F3538FCAF729BB2DBF2D687F3AC519A` |
| `docs/VALIDATION/venv-offline-tests-20261121.json` | `57A1EBEAC8A1708B37B0D00FB629FA40F324C22AAE5177A919B6697BC9D4C656` |
| `docs/VALIDATION/venv-live-geometry-20261121.json` | `94A9F038D538DF36238336EE4ECA9DB6EEBB58D515784EF944B7BAE149298576` |

文件内容修改后必须重新计算 SHA-256。机器证据路径只用于本机追溯，原始模型和大型输出不进入公开仓库。

## 当前已验证

- 当前 Codex 会话的真实 MCP 调用返回 D 盘 Python 和 Server 路径。
- D 盘 MCP 健康检查正常。
- SolidWorks 2025 Revision 33.0.0 可连接。
- 93 个业务工具与 3 个发现入口可从源码注册结构中确认。
- 第五阶段零件 A、零件 B 和装配体属性在保存重开后存在。
- 属性卡模板与三个测试文档的关联在重开后保留。
- 最终零件图和装配图可保存、重开并导出 PDF。
- 原生 BOM 包含图号、名称、材料、板厚、表面处理和数量。
- 原生气泡项目号与 BOM 项目号对应。
- D 盘 MCP 可独立启动，发现模式 3 个入口，完整模式 93 个业务工具。
- D 盘 MCP 已连接 SolidWorks 2025，边界框、质量和原生几何回读通过。
- 非空测试零件 `PropertyChain_Part_A.SLDPRT` 的活动文档名称、路径和类型读取通过。
- 非空测试零件的包围盒、质量、材料、特征树和原生几何只读读取通过。
- 连续多次 D 盘 MCP 健康检查、包围盒读取和原生几何读取结果稳定。
- Codex 正常重启后，旧三个 C 盘 MCP 连接已经释放，当前 C 盘 SolidWorks MCP 进程数为 0。
- 重启后的正式会话只观察到新 D 盘 MCP 进程链，未观察到 C 盘 MCP 进程。
- 2026-11-21 的完整离线回归为 1751 passed、18 skipped。
- 2026-11-22 工程图模板修复后的完整离线回归为 1786 passed、18 skipped。
- 重启后项目验证脚本再次确认 93 个业务工具及 Schema 通过。
- 修复版退出监控脚本的 5 类模拟场景全部通过，且脚本中不存在强制结束进程的命令。
- S2.7 的正式 D 盘 MCP 三状态导出为 9/9 成功，PDF、DXF、DWG 均通过独立内容验证。
- S2.7 的三份 PDF 均为单页 A3 横向，文本内容指纹一致。
- S2.7 的三份 DXF 均为 AC1015、毫米单位，实体、图层、文字和 BOM 语义结构一致，ezdxf 审计错误和自动修复均为 0。
- S2.7 的三份 DWG 均已由 AutoCAD 2025 只读打开，实体、图层、文字、BOM 块和布局一致，读取前后哈希不变。
- S2.7.1 在工程图完全未打开时，DXF 和 DWG 的正式 MCP 调用均为 `was_open=false`，两次均成功并自动关闭测试文档。
- S2.7.1 新 DXF 与 S2.7 A 组的实体、图层、文字和 BOM 一致，只有 MTEXT 插入点存在最大 `0.088818 mm` 的 Y 向位置变化。
- S2.7.1 新 DWG 与 S2.7 A 组的模型空间结构、图层、文字、BOM 和布局完全一致，AutoCAD 2025 只读检查前后哈希不变。
- 模板解析已按“默认模板、指定图幅标准模板、显式模板”三条路径验证，并在实际尺寸不匹配时阻断。
- 标题栏语义去重、属性链接读取、字段截断阻断和默认 A3 模板保存重开均通过。
- `RemoveModifiedNotes=True` 的真机对照中，旧标题栏残留数为 0，普通用户注释在保存重开后仍存在。
- 隔离启动的新代码 MCP 已完成真实工具发现、Schema、模板创建、标题栏、DXF、PDF 和 DWG 调用。
- 手动 SolidWorks DXF 与隔离 MCP DXF 的实体、文字、坐标、字体、图框和标题栏一致。
- PDF 为有效单页 A3 横向文件，57 个文字片段可提取。
- DWG 经 AutoCAD 2025 只读打开，147 个实体与 MCP DXF 在设定容差内一致，文件哈希在读取前后不变。

## 尚未解决

- Property Tab Builder 模板中的 `*` 是否能阻止空值保存尚未验证。
- 多配置 BOM 的配置分组和合并尚未专项验证。
- 工程图审查器已区分多图纸页和模板标题栏文字；其他复杂模板仍需持续回归。
- FC702033-A 成形图布局、尺寸充分性、展开图可读性和局部放大标注仍需人工重做或重新规划。
- FC702033-A 的人工工程图审核未通过，不能进入制造放行或宣布出图 PASS。
- 当前常驻 MCP 尚未加载本轮新增的钣金展开模块，MCP 端到端需在获准重载后补验。
- 隔离 MCP 的跨进程 PDF 后稳定化存在超时，需要另行定位进程协调方式。
- `property_tab_template` 当前需要绝对路径，传入单纯文件名会在服务端工作目录查找并失败。
- Edge Flange、折弯参数和完整展开链尚未开发。
- Router 和正式 MCP 配置仍需保持独立。
- 修复版监控脚本仅完成模拟测试，尚未再次用于下一次真实 Codex 退出。
- 没有找到哈希为 `D7D2C39B76A7531B205FF5798B152B12EA3ED902BBDEA266BC3671627A76F5A9` 的重启前 `config.toml` 完整副本，因此无法逐字节还原该哈希到当前 `A7C55A2E...` 的具体差异。
- 根目录 `$null` 当前缺失，现有 D 盘迁移备份中没有可恢复副本。
- S2.7.1 旧复杂工程图 DXF 中部分 MTEXT 存在仅 Y 方向、最大 `0.088818 mm` 的排版位置变化。该历史记录保留，新的 S2.7.1 干净 A3 同源对照已通过。
- S2.7 的三套 Pack and Go 副本中，工程图和装配体因目标目录引用不同而不具备跨组相同 SHA-256。这是原生引用重写造成的可解释差异，仍需在审阅时明确区分“文件字节一致”和“内容语义一致”。
- 2026-11-19 的历史 DXF/DWG `SaveAs` 错误码 1 未在当前清洗后的复杂工程图样件上复现。尚不能确认唯一根因，不能将只读打开、文件 dirty、旧路径或 Pack and Go 中的任一项单独认定为已证实根因。
- 当前 Codex GUI 的 MCP 仍是修复前旧连接。最新源码已通过隔离 MCP 进程验证，但 GUI 正式重连尚未执行。
- DXF 原始文件哈希仍不同，差异仅来自 DXF 指纹 GUID 和时间戳。非易变内容已经验证完全一致。
- 当前干净 A3 零件图不含 BOM，装配图 BOM 的 PDF/DWG 最小回归不在本轮结论范围内。

## 当前环境

- Windows 11，版本 10.0.26100。
- SolidWorks 2025 SP0.0，主版本 33。
- Python 3.14.10。
- Node.js 26.13.0。
- Git 2.56.0。
- D 盘剩余空间约 331 GB。
- 正式 MCP 配置指向 D 盘虚拟环境 Python 和 D 盘 Server。
- C 盘 SolidWorks MCP 进程数为 `0`。
- 2026-11-22 观察到两条 D 盘 MCP 进程链，均连接到 Codex App Server PID `61512`。当前 GUI 会话的叶子进程为 PID `69688`，另一条为 PID `70616`，运行期 PID 不作为长期配置值。
- SolidWorks 2025 进程 PID `52412` 在隔离 MCP、DXF、PDF 和 DWG 验证期间持续运行。用户原有 8 个文档未关闭，A3 干净测试工程图以只读方式作为第 9 个文档保留。
- AutoCAD 2025 可执行文件为 `D:\CAD\AutoCAD 2025\acad.exe`。手动 DXF、MCP DXF 和 MCP DWG 均以只读方式打开检查，两个测试 DXF 的读取前后哈希不变。
- D 盘独立虚拟环境位于 `D:\Projects\SolidWorks-MCP\.venv`。

## 正式配置哈希核查

- 重启前记录的 SHA-256：`D7D2C39B76A7531B205FF5798B152B12EA3ED902BBDEA266BC3671627A76F5A9`
- 当前 SHA-256：`A7C55A2E17D9AE522B47467F4A3D38698B8A20D80F01E45660040EDA3F90E827`
- 当前大小：`4,940 bytes`
- 未找到与重启前哈希一致的完整 `config.toml` 副本。
- 现有最早完整切换前配置备份：`D:\Projects\SolidWorks-MCP-Data\backups\mcp_switch_20261121_160746\config.toml`，SHA-256 为 `004651F46E020C3C0E82030ABFE9FEC1F50357D82B526EFEDFD08F866E425B2A`。
- 对新旧两份可读取配置进行脱敏逐层比较，只发现 SolidWorks Python、Server 路径和 `node_repl` 运行时管道标识不同。未发现模型、Router、代理或其他 MCP 配置差异，也未发现新增凭据字段。
- 当前配置文件的最后写入时间为 `2026-11-21 19:59:34`，新 Codex 主进程创建时间为 `19:59:27`。这只能证明重启期间发生了写入，不能证明写入者或 `D7D2` 到 `A7C5` 的精确内容差异。

## 回滚位置

- C 盘回滚 Skill：`%USERPROFILE%\.codex\skills\solidworks-automation`
- 切换前完整配置备份：`D:\Projects\SolidWorks-MCP-Data\backups\mcp_switch_20261121_160746\config.toml`
- 重启前项目文档与进程基线：`D:\Projects\SolidWorks-MCP-Data\backups\codex_restart_pre_20261121_194758_v3`
- 原 v3 监控脚本和日志继续保留在上述目录。
- 不存在已验证的 `D7D2C39B...` 完整配置副本，因此不能声称可以逐字节恢复重启前配置。

## 异常未跟踪文件 `$null`

2026-11-21 第三阶段核查时，仓库根目录的 `$null` 已不存在。

历史记录中的原始属性：

- 文件名字：`$null`
- 大小：61 bytes
- SHA-256：`2DDA36D571566A5C6CA2438D971F7F7774DFD17985023E76679C3024A297CB13`
- 最后写入时间：`2026-11-21T13:02:08+08:00`
- 内容：一条由 PowerShell 转义错误产生的 CP936 文本错误信息，首段为 `'$p' 不是内部或外部命令`

已核对迁移备份：

- `D:\Projects\SolidWorks-MCP-Data\backups\pre_migration_20261121_115829\untracked-files.txt` 只列出 3 个测试文件。
- `untracked-files.zip` 只有同样的 3 个测试文件条目。
- `workspace-sha256.csv` 有 744 条记录，没有 `$null`。
- 对整个 `D:\Projects\SolidWorks-MCP-Data\backups` 按 SHA-256 搜索，同哈希副本数量为 0。
- 对整个 `D:\Projects\SolidWorks-MCP-Data\backups` 搜索 61 字节文件，结果为空。
- `D:\Projects\SolidWorks-MCP-Data` 和 C 盘正式 Skill 目录中均没有 61 字节匹配文件。

结论：迁移备份目录没有保存这个异常文件，当前 D 盘迁移备份无法恢复 `$null`。文档中的原始 SHA-256 只能作为历史记录，因没有对应字节副本，本轮不能重新计算验证。没有执行恢复或创建操作。

## 文件分类

以下为首次提交前的基线，共 37 个已修改跟踪文件和 44 个未跟踪文件，总计 81 个状态条目。

首次提交完成后，80 个批准候选文件已进入 7 个本地提交，只有异常文件 `$null` 继续保持未跟踪。

| 分类 | 37 个已修改文件 | 44 个未跟踪文件 | 合计 |
|---|---:|---:|---:|
| 源码 | 17 | 0 | 17 |
| 项目文档与开发配置 | 9 | 22 | 31 |
| 测试代码 | 11 | 3 | 14 |
| 本地测试数据 | 0 | 18 | 18 |
| 不应公开上传 | 0 | 1 | 1 |

源码 17 个：

- MCP 核心 4 个：`mcp-server/document_identity.py`、`gate.py`、`policy.py`、`server.py`。
- 执行核心 11 个：`scripts/sw_assembly.py`、`sw_connect.py`、`sw_delivery.py`、`sw_document_data.py`、`sw_drawing_native.py`、`sw_drawing_package.py`、`sw_export.py`、`sw_hole_features.py`、`sw_native_wire.py`、`sw_part.py`、`validate_mcp.py`。
- 工程图子技能源码 2 个：`drawing_review.py`、`drawing_workflow.py`。

已修改的项目文档与开发配置 9 个：

- `.gitignore`、`.mcpbignore`、`README.md`、`capabilities.yaml`、`mcp-server/README.md`、`pyproject.toml`、`references/mcp-server.md`、`requirements.txt`。
- `subskills/solidworks-engineering-drawing/SKILL.md`。

已修改的测试代码 11 个：

- `tests/test_drawing_subskill.py`
- `tests/test_mcp_discovery.py`
- `tests/test_mcp_document_binding_integration.py`
- `tests/test_mcp_document_identity.py`
- `tests/test_mcp_smithery_bundle.py`
- `tests/test_native_wire_transport.py`
- `tests/test_sw_batch_export.py`
- `tests/test_sw_connect_open_document.py`
- `tests/test_sw_delivery.py`
- `tests/test_sw_document_data.py`
- `tests/test_sw_hole_features.py`

未跟踪的项目文档与开发配置 22 个：

- 根目录项目知识 3 个：`AGENTS.md`、`CHANGELOG.md`、`PROJECT_STATUS.md`。
- 项目级 Skill 3 个：`sw-mcp-development`、`sw-mcp-validation`、`sw-drawing-automation`。
- 项目说明 4 个：`docs/ARCHITECTURE.md`、`docs/CAPABILITY_MATRIX.md`、`docs/MIGRATION_TO_D.md`、`docs/USER_GUIDE.md`。
- 阶段、迁移报告及矩阵 10 个：`docs/VALIDATION/README.md`、`2026-11-18-stage1-upgrade.md`、`2026-11-19-stage2-fixes.md`、`2026-11-20-active-document-fix.md`、`2026-11-20-stage3-drawing-quality.md`、`2026-11-20-stage4-drawing-automation.md`、`2026-11-20-stage5-property-chain.md`、`2026-11-21-migration.md`、`Capability_Domain_Matrix_20261119.md`、`Tool_Status_Matrix_20261119.md`。
- 架构决策 1 个：`docs/decisions/0001-dual-remote-and-skill-loading.md`。
- 开发依赖配置 1 个：`requirements-dev.txt`。

未跟踪的测试代码 3 个：

- `tests/test_default_drawing_template.py`
- `tests/test_drawing_stage3_quality.py`
- `tests/test_sw_mirror_feature.py`

未跟踪的本地测试数据 18 个：

- `backup-summary-20261121.json`
- `c-runtime-unchanged-20261121.json`
- `final-project-state-20261121.json`
- `full-bundle-restore-proof-20261121.json`
- `legacy-backup-copy-proof-20261121.json`
- `live-sw2025-20261121.json`
- `mcp-inventory-20261121.json`
- `offline-tests-20261121.json`
- `original-work-preservation-20261121.json`
- `source-migration-proof-20261121.json`
- `tool_catalog_20261118.json`
- `tool_status_matrix_20261119.json`
- `validate-mcp-20261121.json`
- `validation-data-copy-proof-20261121.json`
- `venv-environment-20261121.json`
- `venv-live-geometry-20261121.json`
- `venv-mcp-sw2025-20261121.json`
- `venv-offline-tests-20261121.json`

上述 18 个文件都位于 `docs/VALIDATION`。

这些文件已经经过占位符脱敏，可作为候选公开摘要，但在首次提交前仍需逐项确认。大型 SolidWorks、PDF、图片和原始 JSON 继续保存在 `D:\Projects\SolidWorks-MCP-Data`。

不应公开上传的文件 1 个：

- 仓库根目录 `$null`。

## 公开仓库敏感信息检查

本轮对 680 个文本源码和文档文件执行了常见凭据模式扫描，覆盖 OpenAI、GitHub、AWS、Slack、Google、Bearer Token、URL 凭据、代理变量和私钥头。

- 未发现真实 API Key、Token、密码、私钥或代理凭据。
- `tests/test_cad_ci_guard.cjs` 中的 GitHub Token 是测试夹具。
- `tests/test_http_boundary.py` 中的 URL 凭据是边界测试输入。
- `.github/workflows/windows-release.yml` 使用 GitHub Actions Secrets 引用，没有明文签名密钥。
- 公开文档只使用 `%USERPROFILE%`、`<USER_HOME>` 或 `<LOCAL_VALIDATION_ROOT>` 占位符。

`.gitignore` 已验证以下边界均生效：

- `.env`、`.env.*`、`*.local.json`、`approvals/`、`*.private.pem`。
- SLDPRT、SLDASM、SLDDRW、STEP、STL、IGES、PDF、DXF、DWG。
- `validation/`、`.local-validation/`、`artifacts/`、`test-artifacts/`。
- `*.bundle`、`*.patch` 和日志文件。

当前 `.gitignore` 已覆盖主要敏感和大型输出边界。`$null` 保持可见未跟踪状态，便于后续人工处理，没有通过忽略规则掩盖。

## 下一步

1. GPT 总负责人审核工程图模板修复、隔离 MCP、同源 DXF 和 PDF/DWG 最小回归报告。
2. 审核源码、测试和项目文档 diff 后，由 GPT 总负责人决定逻辑提交拆分和提交授权。
3. 如需让当前 Codex GUI 使用修复后的 MCP，应在不影响另一 Codex 会话的前提下安排正式重连，并再次检查真实 Schema。
4. 如继续追查历史 DXF/DWG `SaveAs` 错误码 1，应另行授权针对清洗前复杂工程图设计最小对照实验。
5. 根目录 `$null` 的处理方案仍待批准，现有迁移备份没有可恢复副本。
6. 下一开发阶段尚未确定，由 GPT 总负责人安排。
