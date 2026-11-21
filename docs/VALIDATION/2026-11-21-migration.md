# 2026-11-21 D 盘迁移验收

## 结论

D 盘开发仓库已建立并通过源码迁移、完整历史、工具面、离线测试、SolidWorks 2025 连接和非空文档只读验收。

正式 MCP 配置已切换到 D 盘源码和 D 盘独立虚拟环境。当前 Codex 会话的真实 MCP 调用已经返回 D 盘 Python 和 Server 路径。C 盘源码、Skill 和切换前配置继续保留，作为回滚环境。Router、API Key、代理和其他模型 provider 配置未随迁移改变。

Codex 已在 2026-11-21 完成一次正常退出和重新启动。重启后旧 C 盘 MCP 连接和旧 D 盘 MCP 均已退出，新会话重新从正式配置加载 D 盘 MCP。重启后最终验收再次确认 D 盘正式运行、SolidWorks COM、3 个发现入口、93 个业务工具及 Schema、以及非空零件只读读取通过。

## 备份

备份目录：

`D:\Projects\SolidWorks-MCP-Data\backups\pre_migration_20261121_115829`

包括：

- 完整工作区快照，含 `.git`、已修改文件和未跟踪文件。
- 当前浅克隆 Git bundle。
- 作者完整历史 Git bundle。
- 相对作者基线的完整二进制差异补丁。
- 未跟踪文件 ZIP。
- 744 个源工作区文件的 SHA-256 清单。
- 恢复演练目录和逐文件哈希。

恢复验证：

- 完整工作区快照恢复后，773 个文件内容一致。
- 3 个未跟踪文件存在。
- Git 状态行数在源和恢复副本中均为 33。
- 作者完整历史共 350 个提交。
- 完整 bundle、差异补丁和未跟踪 ZIP 恢复后，639 个受管及未跟踪文件哈希全部一致。

## 源码迁移

- C 盘源工作区文件数：744。
- 纳入迁移的受 Git 管理文件：636。
- 未跟踪文件：3。
- 哈希比较文件：639。
- 哈希不一致：0。
- C 盘与 D 盘的完整 tracked diff SHA-256 均为：

`E867438F55C3CF8B032F99450B5C6E4FC47EB91E7D4FE7D3B6A0242EC7759F61`

原有 30 个修改文件和 3 个未跟踪文件全部存在。28 个修改文件与迁移源完全字节一致。`capabilities.yaml` 和 `drawing_review.py` 在迁移后按本轮验收要求增加了文档状态和 PDF 重叠阻断修正，原有内容仍保留。

## MCP 工具面

D 盘独立 stdio MCP 启动成功。

- 默认发现入口：3。
- 业务工具：93。
- 完整模式工具列表：93。
- `validate_mcp.py` 完整性校验通过。

2026-11-21 Codex 重启后的最终项目验证再次通过：

- 发现入口：3。
- 业务工具及 Schema：93 个全部通过。
- 93 是本次当前项目的验证结果，不作为永久固定数量承诺。

## SolidWorks 2025 真机

- 版本：2025，Revision 33.0.0。
- 连接状态：`ok`。
- 测试模型来自 D 盘本机验证目录，以只读方式打开。
- 边界框：`20 × 20 × 20 mm`。
- 体积：`5240.120931 mm³`。
- 质量：`40.872943 g`。
- 密度：`7800 kg/m³`。
- 材料：`Q235-A|Q235A`。
- 原生几何：1 个实体，8 个面。
- 边界框、质量和原生几何三项均返回 `ok`。
- 测试结束后已关闭测试副本。

## 正式切换后的非空文档只读验收

验收日期：2026-11-21。

测试文档由用户在 SolidWorks 2025 中手动打开。本轮全程调用只读工具，没有保存、重建或修改文档。

活动文档：

- 名称：`PropertyChain_Part_A.SLDPRT`
- 完整路径：`%USERPROFILE%\Desktop\SW插件测试\属性关联验证_20261120\PropertyChain_Part_A.SLDPRT`
- 文档类型：`1`，即零件
- SolidWorks 界面标题：`SOLIDWORKS 2025 SP0.0 - [PropertyChain_Part_A.SLDPRT]`
- 文件名与界面标题一致

基本模型信息：

- 包围盒最小角点：`[-60, -40, -5] mm`
- 包围盒最大角点：`[60, 40, 0] mm`
- 包围盒尺寸：`120 × 80 × 5 mm`
- 对角线：`144.308697 mm`
- 体积：`48000 mm³`
- 质量：`374.4 g`
- 表面积：`21200 mm²`
- 质心：`[-0, 0, -2.5] mm`
- 密度：`7800 kg/m³`
- 材料：`Q235-A|Q235A`
- 特征数量：`20`
- 特征错误：`0`
- 特征警告：`0`
- 原生实体数量：`1`
- 实体面数：`6`
- `save_requested`：`false`

重复调用：

- 连续 3 次 `solidworks_health_check` 均返回 `status: ok`
- 每次均返回相同活动文档名称、路径、类型、Python 路径和 Server 路径
- 连续 2 次 `solidworks_bounding_box` 返回完全相同的尺寸和误差状态
- `solidworks_inspect_feature_tree` 返回 `status: ok`
- `solidworks_inspect_native_geometry` 返回 `status: ok`

调用来源：

- 该阶段 D 盘 MCP 入口 PID：`58420`
- 该阶段 D 盘解释器 PID：`42800`
- 实际健康检查调用期间，D 盘 PID 42800 的 CPU 从约 `1.03 s` 增至 `1.625 s`
- 同一期间，C 盘 PID 35608、35648 和 58316 的 CPU 均保持不变
- MCP 返回的 Python 路径为 `D:\Projects\SolidWorks-MCP\.venv\Scripts\python.exe`
- MCP 返回的 Server 路径为 `D:\Projects\SolidWorks-MCP\mcp-server\server.py`
- `config.toml` 在第三阶段前后均为 4,940 bytes，SHA-256 均为 `D7D2C39B76A7531B205FF5798B152B12EA3ED902BBDEA266BC3671627A76F5A9`

文档未被修改的证据：

- 测试文件大小在调用前后均为 `81,560 bytes`
- 测试文件最后写入时间在调用前后均为 `2026-11-20 23:26:34`
- SolidWorks 窗口标题没有出现未保存标记
- `solidworks_inspect_native_geometry` 明确返回 `save_requested: false`
- 文件被 SolidWorks 独占锁定，磁盘 SHA-256 无法在打开状态下读取，因此内容哈希保持未验证

旧 C 盘连接：

- PID 35608 对应旧会话 `01a1eefd-7bce-76a3-bc02-7f54ddd9580e`，状态为 `systemError`
- PID 35648 对应旧会话 `01a1f2ed-0733-7d83-a78d-91604a928a60`，状态为 `idle`
- PID 58316 对应旧会话 `01a1f772-4df8-70d3-b616-47dd99bb96cd`，状态为 `idle`
- 三个旧进程在本阶段调用期间 CPU 均未增加
- 三个旧进程没有被结束

旧连接释放调查：

- [Codex App Server 文档](https://learn.chatgpt.com/docs/app-server)描述了 `thread/unsubscribe` 生命周期。最后一个订阅者退出后，线程默认空闲 60 秒再由 app-server 卸载，并发出 `thread/closed`
- `thread/archive` 只移动持久化线程日志，文档未说明它会直接卸载线程或 MCP 连接
- `config/mcpServer/reload` 会刷新已加载线程，影响范围可能包含当前 D 盘连接
- 直接结束 Python 进程不具备会话级安全性，本轮未采用
- 本轮没有执行卸载、归档、重载或进程结束操作，因此当前环境中的实际释放效果保持未验证

上述内容是迁移第三阶段的历史状态。2026-11-21 第五、第六阶段完成正常 Codex 重启后，PID `35608`、`35648` 和 `58316` 均已自然退出，C 盘 SolidWorks MCP 进程数已经归零，旧连接实际释放效果已由重启后进程表和 D 盘正式调用验收确认。

## Codex 重启后最终运行环境

旧进程已退出：

- ChatGPT PID `5380`
- 旧 App Server PID `50704`
- 旧 C 盘 SolidWorks MCP PID `35608`、`35648`、`58316`
- 旧 D 盘 MCP PID `58420`、`42800`

重启后的观察值：

- ChatGPT 主进程 PID：`11084`
- App Server PID：`61512`
- D 盘 MCP 入口 PID：`62848`
- D 盘 Python 解释器 PID：`61472`
- SolidWorks 2025 PID：`52412`
- C 盘 SolidWorks MCP 进程数：`0`
- D 盘 SolidWorks MCP 进程数：`2`

父子关系：

- App Server `61512` 的父进程为重启后的 ChatGPT `11084`。
- D 盘 MCP 入口 `62848` 的父进程为 App Server `61512`。
- D 盘 Python 解释器 `61472` 的父进程为 D 盘 MCP 入口 `62848`。
- 两个 D 盘 MCP Python 进程的命令行均指向：
  - `D:\Projects\SolidWorks-MCP\.venv\Scripts\python.exe`
  - `D:\Projects\SolidWorks-MCP\mcp-server\server.py`

重启后的正式功能验收结果：

- `solidworks_health_check` 实际调用成功。
- SolidWorks 2025 Revision `33.0.0`，COM 连接正常。
- 3 个发现入口正常。
- 93 个业务工具及 Schema 全部通过。
- `PropertyChain_Part_A.SLDPRT` 的活动文档名称、完整路径、文档类型、包围盒和质量属性读取通过。
- SolidWorks PID `52412` 在重启前后保持不变。

## 重启前后 config.toml 哈希核查

- 重启前记录 SHA-256：`D7D2C39B76A7531B205FF5798B152B12EA3ED902BBDEA266BC3671627A76F5A9`
- 重启后 SHA-256：`A7C55A2E17D9AE522B47467F4A3D38698B8A20D80F01E45660040EDA3F90E827`
- 当前大小：`4,940 bytes`
- 当前 `mcp_servers.solidworks.command`：`D:\Projects\SolidWorks-MCP\.venv\Scripts\python.exe`
- 当前 `mcp_servers.solidworks.args[0]`：`D:\Projects\SolidWorks-MCP\mcp-server\server.py`

在 `%USERPROFILE%\.codex`、`D:\Projects\SolidWorks-MCP-Data` 和项目目录内搜索 `config*` 候选文件后，没有找到 SHA-256 等于 `D7D2C39B...` 的完整重启前配置副本。因此不能通过二进制比较还原 `D7D2` 到 `A7C5` 的具体差异，也不能推断唯一写入原因。

可用的完整配置备份是切换前文件：

- 路径：`D:\Projects\SolidWorks-MCP-Data\backups\mcp_switch_20261121_160746\config.toml`
- 大小：`4,978 bytes`
- SHA-256：`004651F46E020C3C0E82030ABFE9FEC1F50357D82B526EFEDFD08F866E425B2A`

将当前配置与该完整备份进行脱敏逐层比较，只有以下不同字段：

- `mcp_servers.solidworks.command` 从 C 盘 Python 改为 D 盘虚拟环境 Python。
- `mcp_servers.solidworks.args[0]` 从 C 盘 Server 改为 D 盘 Server。
- `mcp_servers.node_repl.env.SKY_CUA_NATIVE_PIPE_DIRECTORY` 的运行时管道标识变化。

没有发现以下配置变化：

- 模型标识和模型 provider。
- Router 相关模型目录和基础地址。
- 代理配置。
- MCP 凭据字段或新增敏感字段。
- 其他 MCP Server 定义。

比较过程没有输出 API Key、Token、密码或其他敏感值。当前配置文件最后写入时间为 `2026-11-21 19:59:34`，新 Codex 主进程创建时间为 `19:59:27`。可确认重启期间发生写入，无法确认唯一写入者。

## Codex 退出监控脚本缺陷与修复

原始 v3 监控脚本位于：

`D:\Projects\SolidWorks-MCP-Data\backups\codex_restart_pre_20261121_194758_v3\monitor_codex_exit.ps1`

原始 SHA-256：

`215E491372D102666E01E6E1E6730425A302B66C3D3CA399A5B7EADEE78FD07B`

缺陷：

- 基线校验通过后，预期退出进程自然消失时，最终状态检查仍把“当前不存在”与敏感身份异常混在一起。
- 因此旧监控在 19 个预期进程均已退出后仍返回 exit 3，而不是正常成功。

独立修复版位于：

`D:\Projects\SolidWorks-MCP-Data\backups\monitor_script_fix_20261121_201013`

修复版 SHA-256：

`F82A3EFB00CCBD3C44981E0E1E074C01810C401CCA95B679E9C849197D232A55`

修复行为：

- 基线通过后，预期进程消失记录为自然退出。
- 基线 PID 被其他启动时间不同的进程复用时，识别为 `identity_mismatch` 并返回 exit 2。
- 监控期间预期或保护进程身份变化返回 exit 3。
- 超时返回 exit 3。
- 陈旧基线返回 exit 2。
- 只有全部预期进程退出且全部保护进程保持原身份时才返回 exit 0。
- 脚本不包含 `Stop-Process`、`taskkill`、`TerminateProcess` 或 `.Kill()`。

Windows PowerShell `5.1.26100.4768` 模拟测试：

- `ValidateOnly`：23 个目标、19 个预期退出目标、23 个启动时必须存在目标，exit `0`。
- 正常退出场景：exit `0`。
- 陈旧基线场景：exit `2`。
- 超时场景：exit `3`。
- PID 基线复用场景：exit `2`，身份不匹配被单独记录。
- 保护进程丢失场景：exit `3`。
- 测试驱动总退出码：`0`。

最新测试结果：

`D:\Projects\SolidWorks-MCP-Data\backups\monitor_script_fix_20261121_201013\tests\run-20261121_201538_187\simulation-results.json`

本轮没有再次运行真实 Codex 退出监控。原始 v3 脚本、原始目标和历史日志均保留。

## 离线测试

最终完整回归：

- `1751 passed`
- `18 skipped`
- `0 failed`

D 盘独立 `.venv` 还完成：

- 关键迁移回归 `6 passed`。
- 完整离线回归 `1751 passed, 18 skipped`。
- `validate_mcp.py` 完整模式 93 个工具通过。
- 发现模式 3 个入口、93 个工具可检索及 Schema 读取通过。
- 使用 D 盘虚拟环境连接 SolidWorks 2025 Revision `33.0.0` 成功。
- 使用 D 盘虚拟环境再次完成边界框、质量和原生几何读取，全程未调用 C 盘 Server。

首次迁移回归发现并修复了 4 项问题：

- 只读活动文档工具被错误要求必须提供 `document_target`。
- 两处打包测试仍硬编码 69 个业务工具。
- PDF 几何文字重叠只返回 `review_required`，没有进入 `blocked`。

## 运行环境保护

- 当前正式 `config.toml` 指向 D 盘虚拟环境 Python 和 D 盘 `mcp-server\server.py`。
- Codex 已按用户授权完成一次受控重启；本轮第七阶段没有再次重启。
- SolidWorks 2025 没有关闭或重启。
- C 盘 SolidWorks MCP 进程数为 0。
- 当前 D 盘 MCP 进程链为 PID `62848` 和 `61472`。
- 本轮没有结束任何进程、重载 MCP 或修改 `config.toml`。
- 没有修改生产 CAD 文件，没有处理根目录 `$null`。
- Git 分支为 `feature/stage5-93-tools`，HEAD 为 `fa294a5d80cd399dc5bb17ff4e77c286ed846177`。
- 三份收尾文档保持未提交修改。
- 未 commit、未 push，未执行 Git 写操作。

## 回滚位置

- C 盘回滚 Skill：`%USERPROFILE%\.codex\skills\solidworks-automation`
- 切换前完整配置：`D:\Projects\SolidWorks-MCP-Data\backups\mcp_switch_20261121_160746\config.toml`
- 重启前项目文档和进程基线：`D:\Projects\SolidWorks-MCP-Data\backups\codex_restart_pre_20261121_194758_v3`
- 原监控目标、脚本和运行日志继续保留，没有覆盖或删除。
- 未找到 `D7D2C39B...` 的完整重启前配置副本，不能声称可以逐字节恢复该时点配置。

## 尚未完成

- 修复版监控脚本尚未用于下一次真实 Codex 退出，只有模拟测试证据。
- `D7D2C39B...` 到 `A7C55A2E...` 的精确配置差异尚未验证，因为缺少重启前完整副本。
- 根目录 `$null` 当前缺失，现有 D 盘迁移备份中没有可恢复副本。
- 打开状态的 SolidWorks 文件被独占锁定，测试文档内容 SHA-256 尚未重算。
- 多配置 BOM、属性卡必填校验和工程图模板碰撞仍是独立遗留项。
