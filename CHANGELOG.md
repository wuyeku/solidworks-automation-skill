# Changelog

本文件记录作者上游基线之外的本地维护内容。未提交或未推送的修改必须明确标记。

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
