# 2026-11-20 第五阶段属性数据链

## 属性卡

已建立两个 Property Tab Builder 模板。

- 零件模板 `MCP_PropertyCard_Part.prtprp`
- 装配体模板 `MCP_PropertyCard_Assembly.asmprp`

字段：

- 文件级属性：`PartNumber`、`Description`、`Material`、`Thickness`、`Date`
- 配置特定属性：`SurfaceTreatment`
- 表面处理下拉值：本色、喷砂、阳极氧化、镀锌、喷粉

零件 A、零件 B、复杂零件和装配体保存重开后，模板关联与属性值均保留。

## 工程图标题栏

标题栏使用原生属性链接：

- `$PRPSHEET:"PartNumber"`
- `$PRPSHEET:"Description"`
- `$PRPSHEET:"Material"`
- `$PRPSHEET:"Date"`

零件 A 修改为 `Mounting Plate A Rev B / Q235-B` 后，重新生成的工程图和 PDF 同步显示新值。

## BOM

原生装配 BOM 包含：

- 序号
- 图号
- 名称
- 材料
- 板厚
- 表面处理
- 数量

实测两个零件数量各 1，合计 2。Excel BOM 的字段与数据一致。

## 复杂测试零件

独立复杂零件包含圆柱外形、Ø8 孔和圆角。

- 边界框 `20 × 20 × 20 mm`
- 体积 `5240.120931 mm³`
- 质量 `40.872943 g`
- 密度 `7800 kg/m³`
- 材料 `Q235-A|Q235A`
- 特征树 0 错误、0 警告

## 尚未解决

- 属性卡必填星号是否真正阻止空值尚未验证。
- 任务窗格人工点击填写尚未作为自动化证据。
- 多配置 BOM 分组和合并尚未专项测试。
- 模板路径参数当前必须使用绝对路径。
- 工程图模板文字碰撞提示仍在审查器中存在。

原始模型、图纸、PDF、BOM 和完整 JSON 证据保存在本机验证数据目录。
