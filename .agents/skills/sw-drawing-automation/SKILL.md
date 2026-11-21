---
name: sw-drawing-automation
description: 规划和验收 SolidWorks 工程图、BOM、标题栏、尺寸、属性关联和 PDF 输出。用于工程图自动生成、DrawingSpec、原生 BOM、气泡、制图审查和交付文件验证。
---

# SolidWorks 工程图自动化

## 入口

工程图执行细节以现有 `subskills/solidworks-engineering-drawing/SKILL.md` 为准。本 Skill 负责项目级路由和验收，不复制底层实现。

## 工作流

1. 确认源零件或装配体只读。
2. 读取图纸标准、图幅、投影法、模板和业务属性。
3. 建立 DrawingSpec。
4. 调用 `solidworks_generate_drawing` 或专项工程图工具。
5. 保存 `.SLDDRW` 后重新打开。
6. 导出 PDF。
7. 运行 `solidworks_review_drawing`。
8. 检查视图、尺寸、BOM、气泡、标题栏、文字重叠和 PDF 内容。

## 属性链

- 图号使用 `PartNumber`。
- 名称使用 `Description`。
- 材料使用 `Material`。
- 板厚使用 `Thickness`。
- 表面处理使用 `SurfaceTreatment`。
- 标题栏使用 `$PRPSHEET` 链接，不写死业务值。

## 验收边界

- 原生 BOM 必须是 SolidWorks BOM 表。
- 气泡必须与 BOM 项目号对应。
- 普通文字表不能冒充原生 BOM。
- 模板文字碰撞检查结果必须保留，不能只看顶层 `pass`。
- PDF 必须实际打开或解析，并核对标题栏和表格文字。
