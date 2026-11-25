# BP800 静态装配验收

- SolidWorks 2025 SP0.0 真机静态方案验证（L4）与用户视觉验收通过。总装包络为 800 × 868 × 804 mm，包含 31 个独立 SLDPRT、66 个组件实例和 65 个锁定配合。保存重开后引用完整，静态体积干涉为 0，最终活动总装重开后 `GetSaveFlag=false`。
- 实际工作入口为已安装的 SolidWorks Automation Skill 及其 `sw_preflight.py --no-install` 自检。实施时从项目 `.venv\Scripts\python.exe` 串行执行独立数据目录中的 `probe.py`、`build.py` 和 `show_final.py`，通过 pywin32 直连 COM。`finalize.py` 用 Pillow 处理截图并计算文件哈希与静态几何检查。MCP 调用链未执行，正式工具源码及运行配置未改动。
- `build.py` 通过 `engineering_orchestrator` 生成阶段计划，用 `sw_connect`、`sw_part`、`sw_sketch_quality`、`sw_appearance` 建立和检查零件，用 `AddComponents3` 与 `sw_assembly` 建立并核对总装，再用 `sw_measure` 和 `sw_review` 检查干涉和预览。[静态方案装配工作流](../../references/assembly.md#静态方案装配工作流)
- 原始证据位于数据目录下的 `validation/BeltPusher_800_20261125/Evidence`。主要证据为 `reopen_validation.json`、`final_active_document.json`、`stroke_geometry.json`、`BP800_Overview.png` 和 `sha256.txt`。交付总装为上一级的 `BP800_Belt_Conveyor_Pusher.SLDASM`。
- 本轮结论限于气缸缩回状态的静态方案。全行程尺寸为几何计算结果，真实运动、载荷、选型与生产可行性尚未验证。
