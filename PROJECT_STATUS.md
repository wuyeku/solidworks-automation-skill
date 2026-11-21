# Project Status

最后更新：2026-11-21

## 当前定位

本项目是 `wzyn20051216/solidworks-automation-skill` 的个人长期维护分支。当前已完成 D 盘项目的首次本地提交，正式运行环境仍保留在 C 盘。

## 当前路径

| 用途 | 路径 |
|---|---|
| 正式运行 MCP 源码 | `%USERPROFILE%\.codex\skills\solidworks-automation` |
| D 盘开发源码 | `D:\Projects\SolidWorks-MCP` |
| D 盘本机验证数据 | `D:\Projects\SolidWorks-MCP-Data` |
| 正式 MCP 配置 | `%USERPROFILE%\.codex\config.toml` |
| Router 源码 | `%LOCALAPPDATA%\codex-router` |

## Git 状态

- 上游声明版本：v2.1.1
- 本地维护标识：`2.1.1+local.93-tools`
- 作者上游：`https://github.com/wzyn20051216/solidworks-automation-skill.git`
- 上游最新基线：`36bc337357723b9763759ff06e4a1afab990b823`
- D 盘开发分支：`feature/stage5-93-tools`
- 状态固化提交前的 HEAD：`2809a8359d0f49e773d8333ebdbf212622fc2dc9`
- 个人 `origin`：`https://github.com/wuyeku/solidworks-automation-skill.git`
- 作者 `upstream`：`https://github.com/wzyn20051216/solidworks-automation-skill.git`
- `upstream` push URL：`DISABLED`
- 首次本地逻辑提交：7 个，已全部完成
- 状态固化提交：本文件所在的后继文档提交
- 状态固化提交完成后：暂存文件 0，已修改跟踪文件 0，未跟踪文件 1
- 当前未跟踪文件：仓库根目录 `$null`
- 当前提交状态：7 个首次逻辑提交完成，状态固化提交紧随记录
- 当前推送状态：尚未 push
- 当前远端状态：双远端已配置，两个远端均已完成 fetch
- `origin/main` 和 `upstream/main` 当前均为 `36bc337`
- 7 个逻辑提交完成时，本地分支相对两个 `main` 为 `0 / 7`，即远端原地 0 个提交，本地领先 7 个提交
- 状态固化提交完成后，本地分支将领先 `origin/main` 和 `upstream/main` 共 8 个提交
- 2026-11-21 迁移验证：639 个受管及未跟踪文件哈希一致
- 作者完整历史：350 个提交

## 首次本地提交

| 顺序 | Commit | 内容 |
|---:|---|---|
| 1 | `a9555c12d2f9e98a86613edc3ebd11d0af57f653` | 项目治理基础 |
| 2 | `d79f26656ce1760659ad76f72e91580c0a7e11a2` | 原生执行器、文档定位和建模修复 |
| 3 | `574ea71f5a41abbc5a070fc4a23a722a8e130cf2` | 工程图自动化 |
| 4 | `8753a4df6510cc5de85195593bf84382a4bb0487` | 93 工具 MCP 工具面 |
| 5 | `78ed30b04a4801f1c744972d79ccf9ba54bc6844` | 93 工具能力说明 |
| 6 | `0d3f1321cd71929a1e78d5ed12a220d147ce3ec6` | 阶段和真机验收证据 |
| 7 | `2809a8359d0f49e773d8333ebdbf212622fc2dc9` | 迁移状态和首次提交项目快照 |

以上 7 个提交均仅包含预先批准的明确文件路径。异常文件 `$null` 未进入任何提交。

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

- C 盘正式 MCP 健康检查正常。
- C 盘 MCP 实际加载路径正确。
- SolidWorks 2025 可连接。
- 93 个业务工具与 3 个发现入口可从源码注册结构中确认。
- 第五阶段零件 A、零件 B 和装配体属性在保存重开后存在。
- 属性卡模板与三个测试文档的关联在重开后保留。
- 最终零件图和装配图可保存、重开并导出 PDF。
- 原生 BOM 包含图号、名称、材料、板厚、表面处理和数量。
- 原生气泡项目号与 BOM 项目号对应。
- D 盘 MCP 可独立启动，发现模式 3 个入口，完整模式 93 个业务工具。
- D 盘 MCP 已连接 SolidWorks 2025，边界框、质量和原生几何回读通过。
- 完整离线回归通过，结果为 1751 passed、18 skipped、0 failed。
- D 盘独立虚拟环境的完整回归为 1751 passed、18 skipped，MCP 完整与发现模式验证通过。

## 尚未解决

- Property Tab Builder 模板中的 `*` 是否能阻止空值保存尚未验证。
- 多配置 BOM 的配置分组和合并尚未专项验证。
- 工程图审查器仍可能把图纸模板文字计入碰撞提示。
- `property_tab_template` 当前需要绝对路径，传入单纯文件名会在服务端工作目录查找并失败。
- Edge Flange、折弯参数和完整展开链尚未开发。
- Router 和正式 MCP 配置仍需保持独立。
- DWG 导出尚未完成独立内容级重开验证。现有证据只有 AC1015 文件头、文件大小和成功导出结果，本机没有 ODA、AutoCAD 或 LibreDWG 解析器。证据见 `docs/VALIDATION/2026-11-19-stage2-fixes.md` 和 `DWG_Reopen_Validation.json`。
- 工程图已经在 SolidWorks 中只读打开时，批量导出的 PDF 可以成功，DXF/DWG 的 `SaveAs` 返回错误码 1。相同工程图未被只读占用时可以导出。证据见 `docs/VALIDATION/2026-11-19-stage2-fixes.md` 和 `MCP_Updated_Batch_Result.json`。

## 当前环境

- Windows 11，版本 10.0.26100。
- SolidWorks 2025 SP0.0，主版本 33。
- Python 3.14.10。
- Node.js 26.13.0。
- Git 2.56.0。
- D 盘剩余空间约 331 GB。
- C 盘正式 MCP 进程和配置在本轮验证后保持原状。
- D 盘独立虚拟环境位于 `D:\Projects\SolidWorks-MCP\.venv`。

## 异常未跟踪文件 `$null`

当前文件位于仓库根目录。

- 文件名字：`$null`
- 大小：61 bytes
- SHA-256：`2DDA36D571566A5C6CA2438D971F7F7774DFD17985023E76679C3024A297CB13`
- 最后写入时间：`2026-11-21T13:02:08+08:00`
- 内容：一条由 PowerShell 转义错误产生的 CP936 文本错误信息，首段为 `'$p' 不是内部或外部命令`
- Git 状态：未跟踪

已核对迁移备份：

- `D:\Projects\SolidWorks-MCP-Data\backups\pre_migration_20261121_115829\untracked-files.txt` 只列出 3 个测试文件。
- `untracked-files.zip` 只有同样的 3 个测试文件条目。
- `workspace-sha256.csv` 有 744 条记录，没有 `$null`。
- 对整个 `D:\Projects\SolidWorks-MCP-Data\backups` 按 SHA-256 搜索，同哈希副本数量为 0。

结论：迁移备份目录没有保存这个异常文件，因此不能声称迁移备份提供了独立的字节级对照。当前 61 字节版本来自验收前已记录状态。收尾复核过程中一次错误命令曾短暂覆盖该文件，已再次恢复为 61 字节、原 SHA-256 和原时间戳。该文件不得删除，也不得提交到公开仓库。

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

1. 用户验收 7 个首次逻辑提交、状态固化提交和最终工作区。
2. 等待用户单独授权 `git push` 到个人 `origin`。
3. 推送后验证 `origin/main`、远程分支和个人 Fork 页面。
4. 用户确认后决定何时将正式 MCP 切换到 D 盘。
5. 明确 DWG 内容级验证和只读工程图批量 DXF/DWG 导出的关闭条件。
6. 未完成遗留项确认后再开始 Edge Flange。
