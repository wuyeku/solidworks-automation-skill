# Changelog

本文件记录作者上游基线之外的本地维护内容。未提交或未推送的修改必须明确标记。

## 2026-11-22，工程图模板、标题栏与同源导出修复

修改内容：

- 修正 SolidWorks 2025 图幅枚举为 A4=6、A4P=7、A3=8、A2=9、A1=10、A0=11，自定义格式使用 12。
- 新增统一模板解析。未指定图幅时使用 SolidWorks 当前默认 `.drwdot`，指定图幅时选择实际尺寸匹配的标准模板，显式模板优先。
- 显式模板与请求图幅不一致时返回 `DRAWING_TEMPLATE_SIZE_MISMATCH`，并在创建 CAD 文档前阻断。
- DrawingSpec 的 `drawingTemplatePath` 和 MCP 的 `drawing_template_path` 均已接入同一解析和保存重开链路。
- 标题栏写入前读取模板已有属性链接，支持引号和花括号 `$PRPSHEET` 表达式。已有字段默认跳过，只有显式手动覆盖才允许重复插入。
- 标题栏字段语义检查和截断检查在写入前执行。字段截断返回 `review_required`。
- `SetupSheet6` 回退路径改用 `RemoveModifiedNotes=True`，验证实际模板、图幅、方向和投影，并保护普通用户注释。
- 出图包允许在已有 8 个文档时增加一个受控临时工程图，并在会话退出时只清理本轮自有文档。
- 修复 MCP 兼容入口未转发 `drawing_template_path` 的参数签名缺口。
- 修复标题栏已有字段扫描可能把图面其他位置同名字段误认为标题栏字段的问题。

修改文件：

- `mcp-server/server.py`
- `scripts/sw_connect.py`
- `scripts/sw_drawing_package.py`
- `subskills/solidworks-engineering-drawing/schemas/drawing_spec.schema.json`
- `subskills/solidworks-engineering-drawing/scripts/drawing_review.py`
- `subskills/solidworks-engineering-drawing/scripts/drawing_spec.py`
- `subskills/solidworks-engineering-drawing/scripts/drawing_workflow.py`
- `tests/test_default_drawing_template.py`
- `tests/test_drawing_subskill.py`
- `tests/test_mcp_drawing_tools.py`
- `tests/test_sw_drawing_native.py`
- `tests/test_sw_drawing_structure.py`
- `tests/test_sw_new_document.py`
- `tests/test_drawing_template_resolution.py`
- `tests/test_drawing_title_block_deduplication.py`
- `PROJECT_STATUS.md`
- `CHANGELOG.md`
- `docs/CAPABILITY_MATRIX.md`

验证结果：

- 完整离线回归：`1786 passed, 18 skipped`。
- SolidWorks 2025 真机验证覆盖 A0 至 A4 模板创建、默认 A4、显式 A3、尺寸不匹配阻断、标题栏已有字段跳过、字段截断阻断、保存重开和用户注释保护。
- 隔离 STDIO MCP 启动最新源码后，真实 Schema 包含 `drawing_template_path`，默认 A4、显式 A3、模板不一致阻断和标题栏语义去重均通过。
- 当前 Codex GUI 仍连接修复前启动的旧 MCP 进程。隔离新进程已验证，GUI 重连未执行。
- 同一张干净 A3 工程图完成手动 SolidWorks DXF 与 MCP DXF 对照。两份 DXF 均为 AC1015、毫米单位、147 个实体和 57 个 MTEXT。
- 两份 DXF 的实体、文字内容、插入坐标、字体样式、3.5 mm 字高、图层、图框、标题栏和 BOM 语义检查一致。去除指纹 GUID 和时间戳后，非易变内容完全相同。
- AutoCAD 2025 原生只读对照确认全图、横向图框、纵向图框和标题栏一致。未发现新增文字、缺失文字、重复程序字段或错位。
- 清洁 A3 源图为零件工程图，不含 BOM 表，因此 BOM 项标记为不适用。
- PDF 最小回归通过。PDF 为单页 A3 横向，57 个可提取文字片段均使用 `HYSWLongFangSong`。
- DWG 最小回归通过。AutoCAD 2025 只读读取到 147 个实体、90 条 `LINE`、57 个 `MTEXT`，与已验证 MCP DXF 的最大数值偏差为 `4.860112312599085e-11 mm`，低于 `1e-7 mm` 容差。
- PDF SHA-256：`5A8B647DA2EA057B7700684440E31A22DE53A63FD25D1F952B901A51396A248F`。
- DWG SHA-256：`6F194B19D344F21AF100A55D1F2C41E78532222DEB7B21064C07A34A4A67BD89`。
- 源工程图前后 SHA-256 均为 `0A32C68DA233DC9AF4E09B28C22A70D30491F7128B12E3EE5CC60BF46E5CF6CA`，`GetSaveFlag=false`，只读状态保持。

Git commit：无，等待审查和授权。

GitHub 推送：无。

## 2026-11-22，S2 复杂工程图导出专项收尾

修改内容：

- 汇总 S2.7 的未打开、正常打开、只读打开三状态正式 MCP 导出结果。
- 记录 S2.7.1 对完全未打开状态 DXF/DWG 的独立补测。
- 将 S2 阶段文档总状态同步到 `PROJECT_STATUS.md` 和 `docs/CAPABILITY_MATRIX.md`。
- 修正 `AGENTS.md` 和 `README.md` 中仍称正式运行环境保留在 C 盘的过期说明。
- 明确 `PROJECT_STATUS.md` 是正式阶段进度入口，`CHANGELOG.md` 是维护变更历史入口。

修改文件：

- `AGENTS.md`
- `README.md`
- `PROJECT_STATUS.md`
- `CHANGELOG.md`
- `docs/CAPABILITY_MATRIX.md`

S2.7 验证结果：

- 使用 S2.7 独立 A、B、C 三组 Pack and Go 副本完成 PDF、DXF、DWG 串行正式 MCP 导出，共 9/9 成功。
- A 组首次 PDF 调用为 `was_open=false`。A 组随后 DXF/DWG 和 B、C 全部调用为 `was_open=true`。
- 三份 PDF 均为单页 A3 横向，文本内容指纹一致，四组零件图号、名称和材料均可读取。
- 三份 DXF 均为 AC1015、毫米单位，实体、图层、文字和 BOM 语义结构一致，ezdxf 审计错误和自动修复均为 0。
- 三份 DWG 均由 AutoCAD 2025 `25.0s (LMS Tech)` 只读打开，实体、图层、文字、BOM 块和布局一致，读取前后哈希不变。
- Pack and Go 为各组写入了目标目录相关的绝对引用，四份零件哈希一致，但工程图和装配体跨组哈希不同。因此 S2.7 汇总保留 `review_required`，该状态不代表导出失败。

S2.7.1 验证结果：

- 使用 S2.7 A 组同一工程图，在完全未打开状态下分别调用正式 MCP 导出 DXF 和 DWG。
- 两次调用均设置 `overwrite=false`、`close_documents=true`，均返回 `was_open=false`、`success=true`、`api_success=true`、`exists=true`、`produced_this_run=true`。
- 两次调用后工程图、装配体和四个零件均完全卸载，用户原有 `PropertyChain_Part_A.SLDPRT` 未被关闭或保存。
- DXF 为 AC1015、毫米单位，ModelSpace 直接实体 210，展开后 295，均为 164 LINE、130 MTEXT、1 INSERT。图层、全部文字和 BOM 与 S2.7 A 组一致，审计错误和自动修复均为 0。
- DXF 有 71 个 MTEXT 仅发生 Y 向位置变化，最大 `0.088818 mm`，没有 X 位移，也没有 LINE、INSERT、图层或文字变化。最终排版仍需人工目视复核。
- DWG 经 AutoCAD 2025 只读打开，ModelSpace 直接实体 210，包含 104 Line、105 MText、1 BlockReference，图层、BOM 块、文字和 `Layout1`、`Layout2`、`Model` 均与 S2.7 A 组一致，读取前后 SHA-256 不变。
- 历史 2026-11-19 DXF/DWG `SaveAs` 错误码 1 未复现。复杂图首次打开 dirty、保存后重开 clean 的现象已确认，但历史错误的唯一根因仍未确认。
- S2.7.1 汇总的 `source_change_required=false`。基于当前已验证范围，正式源码无需修改；S2.7、S2.7.1 和本轮文档收尾均已避免修改功能源码。

测试结果：

- S2.7 正式 MCP 导出：9/9 成功。
- S2.7.1 正式 MCP 补测：2/2 成功。
- PDF、DXF、DWG 独立内容验证：通过。
- AutoCAD 2025 只读 DWG 检查：通过。
- S2.7.1 输入工程图、装配体和四个零件：前后哈希一致。
- `git diff --check`、Markdown 链接和敏感信息检查结果见任务收尾记录。

Git commit：无，等待用户审查和授权。

GitHub 推送：无。

## 2026-11-21，D 盘迁移最终收尾

修改内容：

- 复核 Codex 正常重启后的正式运行环境，确认旧 C 盘和旧 D 盘 MCP 进程已退出。
- 确认当前 C 盘 SolidWorks MCP 进程数为 0，新会话使用 D 盘 Python、D 盘 Server 和 D 盘虚拟环境。
- 记录重启后当前正式配置和项目文档结论，保留原有未提交文档修改。
- 创建独立修复版 Codex 退出监控脚本，不覆盖原 v3 脚本及其历史日志。
- 修复基线有效后预期进程消失被错误归类为身份异常的问题，并显式处理 PID 复用、保护进程丢失、陈旧基线和超时退出码。
- 使用模拟进程完成正向和负向测试，没有再次运行真实 Codex 退出监控。

修改文件：

- `PROJECT_STATUS.md`
- `CHANGELOG.md`
- `docs/VALIDATION/2026-11-21-migration.md`
- `D:\Projects\SolidWorks-MCP-Data\backups\monitor_script_fix_20261121_201013\monitor_codex_exit_fixed.ps1`
- `D:\Projects\SolidWorks-MCP-Data\backups\monitor_script_fix_20261121_201013\tests\run_monitor_simulation_tests.ps1`
- `D:\Projects\SolidWorks-MCP-Data\backups\monitor_script_fix_20261121_201013\README.md`
- `D:\Projects\SolidWorks-MCP-Data\backups\monitor_script_fix_20261121_201013\verification.json`
- `D:\Projects\SolidWorks-MCP-Data\backups\monitor_script_fix_20261121_201013\SHA256SUMS.txt`

正式运行验收结果：

- 重启后新 Codex 主进程 PID 为 `11084`，App Server PID 为 `61512`。
- 当前 D 盘 MCP 入口 PID 为 `62848`，Python 解释器 PID 为 `61472`。
- SolidWorks 2025 PID `52412` 在重启后继续存在。
- 当前 C 盘 SolidWorks MCP 进程数为 0，D 盘 MCP 进程数为 2。
- 正式配置继续使用 `D:\Projects\SolidWorks-MCP\.venv\Scripts\python.exe` 和 `D:\Projects\SolidWorks-MCP\mcp-server\server.py`。
- 2026-11-21 重启后验收再次确认 3 个发现入口和 93 个业务工具及 Schema 通过。93 是本次验证结果，不作为永久固定数量承诺。
- `PropertyChain_Part_A.SLDPRT` 的名称、路径、类型、包围盒、质量属性及基础模型读取通过。

配置哈希核查：

- 重启前记录 SHA-256：`D7D2C39B76A7531B205FF5798B152B12EA3ED902BBDEA266BC3671627A76F5A9`
- 当前 SHA-256：`A7C55A2E17D9AE522B47467F4A3D38698B8A20D80F01E45660040EDA3F90E827`
- 未找到与重启前哈希一致的完整配置副本，因此不能逐字节还原两个哈希之间的具体差异。
- 现有完整切换前备份 `mcp_switch_20261121_160746\config.toml` 的 SHA-256 为 `004651F46E020C3C0E82030ABFE9FEC1F50357D82B526EFEDFD08F866E425B2A`。
- 对新旧可读取配置进行脱敏逐项比较，仅发现 SolidWorks Python/Server 路径和 `node_repl` 运行时管道标识不同；没有发现模型、Router、代理或凭据字段变化。
- 当前配置在重启开始后发生写入，但由于缺少目标时点完整副本，不能推断唯一写入原因。

监控脚本修复与测试：

- 原 v3 脚本和全部运行日志保持不变，SHA-256 仍为 `215E491372D102666E01E6E1E6730425A302B66C3D3CA399A5B7EADEE78FD07B`。
- 修复版 SHA-256 为 `F82A3EFB00CCBD3C44981E0E1E074C01810C401CCA95B679E9C849197D232A55`。
- Windows PowerShell 版本：`5.1.26100.4768`。
- `ValidateOnly` 验证通过，23 个目标、19 个预期退出目标、23 个启动时必须存在目标，退出码 0。
- 正常退出模拟：exit `0`。
- 陈旧基线模拟：exit `2`。
- 超时模拟：exit `3`。
- PID 基线复用模拟：exit `2`，并单独识别身份不匹配。
- 保护进程丢失模拟：exit `3`。
- 模拟测试驱动退出码：`0`。
- 没有运行真实 Codex 退出监控，没有调用强制结束进程命令。

Git commit：无，等待用户审查和授权。

GitHub 推送：无。

## 2026-11-21，D 盘 MCP 正式切换与非空文档只读验收

修改内容：

- 将正式 MCP 的 Python 和 Server 路径切换至 D 盘环境。
- 通过当前 Codex 会话验证实际调用返回 D 盘虚拟环境和 D 盘 Server 路径。
- 完成非空测试零件 `PropertyChain_Part_A.SLDPRT` 的活动文档、包围盒、质量、材料、特征树和原生几何只读读取。
- 记录三次健康检查、两次包围盒读取和一次原生几何读取的重复调用稳定性。
- 调查三个旧 C 盘 MCP 进程对应的 Codex 会话和线程卸载生命周期。
- 更新迁移验收报告、项目状态和变更记录。

修改文件：

- `PROJECT_STATUS.md`
- `CHANGELOG.md`
- `docs/VALIDATION/2026-11-21-migration.md`

验证结果：

- 当前 Codex 会话的真实 Health Check 返回 D 盘 Python 和 Server 路径。
- SolidWorks 2025 Revision `33.0.0` 连接正常。
- 活动文档名称、完整路径和类型读取成功，文件名与 SolidWorks 界面一致。
- 包围盒为 `120 × 80 × 5 mm`，质量 `374.4 g`，体积 `48000 mm³`。
- 材料为 `Q235-A|Q235A`，特征错误和警告均为 0。
- 原生几何读取返回 1 个实体、6 个面，且 `save_requested` 为 `false`。
- 测试文件大小和最后写入时间在调用前后未变化。
- 测试文件被 SolidWorks 独占锁定，磁盘 SHA-256 无法重新计算。
- 三个 C 盘旧 MCP 进程在 D 盘调用期间 CPU 未增加。
- 没有结束 MCP 进程、重启 Codex、关闭 SolidWorks 或执行 Git 写操作。

Git commit：无，等待用户审查和授权。

GitHub 推送：无。

## 2026-11-21，建立通用 AI 工作协议

修改内容：

- 新增 `docs/AI_WORKFLOW.md`，统一新聊天接手、Git 检查、开发、测试分级、审查、收尾、交接和跨电脑流程。
- 在 `AGENTS.md` 强制要求所有 AI 在任务开始前完整阅读该协议。
- 更新项目状态和变更记录中的实际远程分支、noreply 重写哈希和已推送状态。

修改文件：

- `AGENTS.md`
- `PROJECT_STATUS.md`
- `CHANGELOG.md`
- `docs/AI_WORKFLOW.md`

验证结果：

- 文档 Markdown 相对链接全部可解析。
- `git diff --check` 通过。
- 敏感信息扫描未发现真实凭据。
- 本轮未修改功能源码、C 盘正式 MCP、Router、API Key 或代理配置。
- 本轮未执行 git add、commit 或 push。

Git commit：无，等待用户审查和授权。

GitHub 推送：无。

## 2026-11-21，首次本地提交完成

首次提交按 7 个已批准逻辑分组完成，全部只使用明确文件路径暂存。

| 顺序 | Commit | 内容 | 文件数 |
|---:|---|---|---:|
| 1 | `e4f801c279b92efe744cb057fe7e8fee34f80648` | 项目治理基础 | 10 |
| 2 | `af682a7cfb723c73e9cab58c6a4e12bcc5e2f121` | 原生执行器与建模修复 | 12 |
| 3 | `8b463016ccddc496d7d57ac9be4b5f4cd2998d51` | 工程图执行核心 | 8 |
| 4 | `62da4aabed50162b8ff114f74d5fbe5bf9f1e530` | 93 工具注册与领域执行器 | 14 |
| 5 | `2a74d8616158e822769f1a7a3da05a7da7af5fca` | 能力说明与用户文档 | 11 |
| 6 | `dc0891293565ac47bc5d38dd910938e73953c77c` | 阶段验收证据 | 14 |
| 7 | `2d450696b04dff25b7d86266b0919e6faa5b9f0d` | 迁移状态与首次提交快照 | 11 |
| 8 | `8d28e5b0711cba3864d9ce808f900dd172081339` | 最终状态固化 | 2 |

验证结果：

- 每组提交前都核对暂存清单，确认没有混入其他文件。
- 每组都通过 `git diff --cached --check`。
- 7 个提交合计覆盖 80 个批准文件。
- 异常文件 `$null` 没有进入任何提交。
- 本地分支当前领先 `origin/main` 和 `upstream/main`。
- 8 个提交的作者和提交者邮箱统一为 GitHub noreply 地址。
- 8 个提交已推送到个人 `origin/feature/stage5-93-tools`。
- `origin/main` 和 `upstream/main` 均保持作者基线 `36bc337`。

Git commit：7 个首次逻辑提交，另有 1 个状态固化提交。

GitHub 推送：8 个提交已推送到个人 `origin/feature/stage5-93-tools`。

## 2026-11-21，双远端配置与首次提交准备

修改内容：

- 配置个人 `origin` 为 `https://github.com/wuyeku/solidworks-automation-skill.git`。
- 保留作者 `upstream` 为 `https://github.com/wzyn20051216/solidworks-automation-skill.git`。
- 保持 `upstream` push URL 为 `DISABLED`。
- 执行 `git fetch origin` 和 `git fetch upstream`，确认双方 `main` 与当前开发分支均指向 `36bc337357723b9763759ff06e4a1afab990b823`。
- 审查 37 个已修改文件和 44 个未跟踪文件，准备 7 个逻辑提交分组。
- 更新项目状态、ADR 和 README 中的双远端及回归数量。
- 清除三份验收报告中 `git diff --check` 不接受的 5 行行尾空格，并同步更新报告哈希。

修改文件：

- `README.md`
- `PROJECT_STATUS.md`
- `CHANGELOG.md`
- `docs/decisions/0001-dual-remote-and-skill-loading.md`
- `docs/VALIDATION/2026-11-19-stage2-fixes.md`
- `docs/VALIDATION/2026-11-20-active-document-fix.md`
- `docs/VALIDATION/2026-11-20-stage3-drawing-quality.md`

验证结果：

- MCP 完整模式 93 个业务工具可见。
- 发现模式暴露 3 个入口，93 个工具均可检索并读取 Schema。
- 相关定向测试 `221 passed`。
- 80 个提交候选文件完成敏感信息、个人路径、JSON、Markdown 链接和空白检查。
- 异常文件 `$null` 继续排除，不删除。
- 准备阶段未执行 git add、commit 或 push，后续提交记录见“首次本地提交完成”。

Git commit：准备阶段无。

GitHub 推送：无。

## 2026-11-21，项目状态与交付证据收尾

修改内容：

- 为 `PROJECT_STATUS.md` 中重要功能补充阶段报告、验证日期和本机数据证据路径。
- 补充 DWG 内容级验证和只读工程图批量 DXF/DWG 导出的历史遗留问题。
- 核对异常未跟踪文件 `$null`，确认迁移备份中没有同文件或同哈希副本。
- 将当前 37 个已修改文件和 44 个未跟踪文件按源码、文档配置、测试代码、本地测试数据和禁止公开发布进行分类。
- 完成公开仓库凭据模式扫描和 `.gitignore` 边界检查。
- 本阶段完成时尚未 commit、尚未 push，`origin` 尚未配置。该状态后续已由“双远端配置与首次提交准备”替代。

修改文件：

- `PROJECT_STATUS.md`
- `CHANGELOG.md`

测试结果：

- 本轮未修改功能源码、C 盘运行环境、MCP 配置或 remote。
- 敏感信息扫描覆盖 680 个文本文件，未发现真实凭据。
- `.gitignore` 对 `.env`、本地配置、审批目录、SolidWorks 文件、导出文件、压缩包、补丁和测试输出目录均验证为有效，本轮未修改该文件。
- `$null` 当前为 61 bytes，SHA-256 为 `2DDA36D571566A5C6CA2438D971F7F7774DFD17985023E76679C3024A297CB13`。
- 修改前文档备份位于 `D:\Projects\SolidWorks-MCP-Data\backups\project_cleanup_20261121_131553`。

Git commit：无。

GitHub 推送：无。
## 2026-11-21，D 盘项目迁移与知识体系

修改内容：

- 从作者 GitHub 克隆完整 Git 历史到 `D:\Projects\SolidWorks-MCP`。
- 创建个人开发分支 `feature/stage5-93-tools`。
- 保留作者远端为只读 `upstream`，暂不创建个人 `origin`。
- 迁移当前 30 个修改文件和 3 个未跟踪测试文件。
- 建立 `D:\Projects\SolidWorks-MCP-Data` 本机验证数据根目录。
- 新增项目长期规则、状态、架构、能力矩阵、验收目录和项目级 Skill。
- 新增 D 盘独立 `.venv` 和 `requirements-dev.txt`。
- 修正活动文档只读工具的过度目标绑定。
- 更新打包测试中的工具数量基线为 93。
- 让最终 PDF 中几何重叠的尺寸文字进入阻断状态。

修改文件：

- `AGENTS.md`
- `PROJECT_STATUS.md`
- `CHANGELOG.md`
- `.gitignore`
- `.mcpbignore`
- `README.md`
- `capabilities.yaml`
- `mcp-server/README.md`
- `references/mcp-server.md`
- `requirements-dev.txt`
- `docs/ARCHITECTURE.md`
- `docs/CAPABILITY_MATRIX.md`
- `docs/MIGRATION_TO_D.md`
- `docs/USER_GUIDE.md`
- `docs/VALIDATION/`
- `.agents/skills/`
- `mcp-server/gate.py`
- `tests/test_mcp_smithery_bundle.py`
- `subskills/solidworks-engineering-drawing/scripts/drawing_review.py`
- 当前从 C 盘迁移的 30 个修改文件和 3 个未跟踪测试文件

测试结果：

- 完整离线回归 `1751 passed, 18 skipped`。
- 使用 D 盘独立 `.venv` 再次完成完整回归，结果同为 `1751 passed, 18 skipped`。
- D 盘 MCP 独立启动验证通过，发现入口 3 个、业务工具 93 个。
- SolidWorks 2025 连接、边界框、质量和原生几何回读通过。
- C 盘正式运行环境未修改。

Git commit：无，用户要求本轮不提交。

GitHub 推送：无。

## 2026-11-20，第五阶段属性数据链

修改内容：

- 属性卡模板支持零件和装配体。
- 支持文件级和配置特定自定义属性。
- 工程图标题栏使用 `$PRPSHEET` 链接模型属性。
- 原生 BOM 和 Excel BOM 增加板厚、表面处理等属性。

测试结果：

- 属性保存、重开、标题栏更新、原生 BOM、Excel BOM 和 PDF 验证通过。
- 仍有工程图模板碰撞和必填项校验问题。

Git commit：无。

GitHub 推送：无。

## 2026-11-19 至 2026-11-20，第二至第四阶段

修改内容：

- 修复镜像特征、批量导出、剖视图和局部视图。
- 修复重复尺寸、标题栏、原生 BOM 和 PDF 导出。
- 增加 Ø20 和 Ø8 自动直径标注。
- 增加原生 BOM 自动气泡。

测试结果：

- 对应阶段报告保存在 `D:\Projects\SolidWorks-MCP-Data\validation`。

Git commit：无。

GitHub 推送：无。

## 2026-11-18，第一阶段功能扩展

修改内容：

- 从作者原版 69 个业务工具升级到 93 个。
- 新增 24 个工具。
- 升级孔特征和导出相关工具。

测试结果：

- 零件、装配、工程图、BOM、钣金、焊件、导出和检查流程已进行真机验证。
- 后续阶段修复了部分未通过项。

Git commit：无。

GitHub 推送：无。
