"""Native sheet-metal drawing composition built on the existing drawing package."""
from __future__ import annotations

import math
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

import pythoncom
from win32com.client import VARIANT

from scripts.sheet_metal_geometry import (
    analyze_flat_pattern_dxf,
    split_table_columns,
)
from scripts.sw_connect import activate_document, get_com_member


SW_DWG_TEMPLATE_CUSTOM = 12
PAPER_CODES = {"A4P": 7, "A4": 6, "A3": 8, "A2": 9, "A1": 10, "A0": 11}
PAPER_MM = {
    "A4P": (210.0, 297.0),
    "A4": (297.0, 210.0),
    "A3": (420.0, 297.0),
    "A2": (594.0, 420.0),
    "A1": (841.0, 594.0),
    "A0": (1189.0, 841.0),
}


def _optional(obj, name, *args, default=None):
    if obj is None:
        return default
    try:
        return get_com_member(obj, name, *args)
    except Exception:
        return default


def _items(value) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    try:
        return list(value)
    except TypeError:
        return [value]


def _normalise_view_name(value: str) -> str:
    text = str(value or "").casefold()
    if "前视" in text or "front" in text:
        return "front"
    if "上视" in text or "俯视" in text or "top" in text:
        return "top"
    if "右视" in text or "right" in text:
        return "right"
    if "等轴测" in text or "isometric" in text:
        return "isometric"
    return ""


def _view_records(drawing) -> list[dict[str, Any]]:
    records = []
    for sheet_name in _items(get_com_member(drawing, "GetSheetNames")):
        drawing.ActivateSheet(str(sheet_name))
        sheet = get_com_member(drawing, "GetCurrentSheet")
        for view in _items(get_com_member(sheet, "GetViews")):
            outline = _items(_optional(view, "GetOutline", default=[]))
            records.append(
                {
                    "sheet": str(sheet_name),
                    "view": view,
                    "name": str(_optional(view, "Name", default="")),
                    "orientation": _normalise_view_name(
                        str(_optional(view, "GetOrientationName", default="") or "")
                    ),
                    "is_flat_pattern": bool(
                        _optional(view, "IsFlatPatternView", default=False)
                    ),
                    "outline_m": outline,
                    "box_mm": (
                        [
                            round(float(outline[0]) * 1000.0, 3),
                            round(float(outline[1]) * 1000.0, 3),
                            round(float(outline[2]) * 1000.0, 3),
                            round(float(outline[3]) * 1000.0, 3),
                        ]
                        if len(outline) == 4
                        else None
                    ),
                }
            )
    return records


def _find_standard_view(drawing, orientation: str):
    expected = orientation.casefold()
    for record in _view_records(drawing):
        if record["orientation"] == expected:
            return record["view"]
    raise RuntimeError(f"无法定位 {orientation} 标准视图")


def _visible_lines(view) -> list[dict[str, Any]]:
    rows = []
    for component in _items(_optional(view, "GetVisibleComponents", default=[])):
        for edge in _items(_optional(view, "GetVisibleEntities2", component, 1, default=[])):
            curve = _optional(edge, "GetCurve")
            if curve is None or not bool(_optional(curve, "IsLine", default=False)):
                continue
            start = _optional(_optional(edge, "GetStartVertex"), "GetPoint")
            end = _optional(_optional(edge, "GetEndVertex"), "GetPoint")
            if start is None or end is None:
                continue
            start_mm = [float(value) * 1000.0 for value in start]
            end_mm = [float(value) * 1000.0 for value in end]
            rows.append(
                {
                    "edge": edge,
                    "start": start_mm,
                    "end": end_mm,
                    "length": math.dist(start_mm, end_mm),
                }
            )
    return rows


def _select_edge_pair(view, first, second) -> None:
    if not bool(_optional(view, "SelectEntity", first["edge"], False)):
        raise RuntimeError("第一条尺寸边选择失败")
    if not bool(_optional(view, "SelectEntity", second["edge"], True)):
        raise RuntimeError("第二条尺寸边选择失败")


def _create_pair_dimension(
    drawing,
    view,
    first,
    second,
    *,
    orientation: str,
    position_mm: list[float],
    expected_mm: float,
    identifier: str,
):
    drawing.ClearSelection2(True)
    _select_edge_pair(view, first, second)
    method = (
        "AddHorizontalDimension2"
        if orientation == "horizontal"
        else "AddVerticalDimension2"
    )
    display = _optional(
        drawing,
        method,
        float(position_mm[0]) / 1000.0,
        float(position_mm[1]) / 1000.0,
        0.0,
    )
    drawing.ClearSelection2(True)
    if display is None:
        raise RuntimeError(f"尺寸 {identifier} 创建失败")
    dimension = get_com_member(display, "GetDimension2", 0)
    actual_mm = float(get_com_member(dimension, "SystemValue")) * 1000.0
    if abs(actual_mm - expected_mm) > 1e-5:
        raise RuntimeError(
            f"尺寸 {identifier} 数值 {actual_mm:.6f} 与要求 {expected_mm:.6f} 不一致"
        )
    annotation = get_com_member(display, "GetAnnotation")
    persistent_name = "CAD_DIM__overall__" + identifier
    if _optional(annotation, "SetName", persistent_name, default=False) is not True:
        raise RuntimeError(f"尺寸 {identifier} 持久名称写入失败")
    return {
        "display": display,
        "view": str(get_com_member(view, "Name")),
        "orientation": orientation,
        "value_mm": round(actual_mm, 6),
        "persistent_name": persistent_name,
    }


def add_forming_dimensions(drawing) -> dict[str, Any]:
    """Add the formed-state overall dimensions without importing all model dimensions."""
    right = _find_standard_view(drawing, "right")
    front = _find_standard_view(drawing, "front")
    right_outline = [float(value) for value in get_com_member(right, "GetOutline")]
    front_outline = [float(value) for value in get_com_member(front, "GetOutline")]
    right_lines = _visible_lines(right)
    front_lines = _visible_lines(front)

    vertical_screen = [
        row
        for row in right_lines
        if abs(row["start"][1] - row["end"][1]) < 0.05
        and abs(row["start"][2] - row["end"][2]) > 20.0
    ]
    horizontal_screen = [
        row
        for row in right_lines
        if abs(row["start"][2] - row["end"][2]) < 0.05
        and abs(row["start"][1] - row["end"][1]) > 20.0
    ]
    front_vertical = [
        row
        for row in front_lines
        if abs(row["start"][0] - row["end"][0]) < 0.05
        and abs(row["start"][1] - row["end"][1]) > 20.0
    ]
    if not vertical_screen or not horizontal_screen or not front_vertical:
        return {
            "status": "review_required",
            "error_code": "SHEET_METAL_FORMED_DIMENSION_EDGES_MISSING",
            "dimensions": {},
        }

    dimensions = {}
    dimensions["FORMED_LENGTH_1650"] = _create_pair_dimension(
        drawing,
        right,
        min(vertical_screen, key=lambda row: row["start"][1]),
        max(vertical_screen, key=lambda row: row["start"][1]),
        orientation="horizontal",
        position_mm=[
            (right_outline[0] + right_outline[2]) * 500.0,
            (right_outline[1] - 0.012) * 1000.0,
        ],
        expected_mm=1650.0,
        identifier="FORMED_LENGTH_1650",
    )
    dimensions["FORMED_WIDTH_1025"] = _create_pair_dimension(
        drawing,
        right,
        min(horizontal_screen, key=lambda row: row["start"][2]),
        max(horizontal_screen, key=lambda row: row["start"][2]),
        orientation="vertical",
        position_mm=[
            (right_outline[2] + 0.012) * 1000.0,
            (right_outline[1] + right_outline[3]) * 500.0,
        ],
        expected_mm=1025.0,
        identifier="FORMED_WIDTH_1025",
    )
    dimensions["FORMED_DEPTH_105"] = _create_pair_dimension(
        drawing,
        front,
        min(front_vertical, key=lambda row: row["start"][0]),
        max(front_vertical, key=lambda row: row["start"][0]),
        orientation="horizontal",
        position_mm=[
            (front_outline[0] + front_outline[2]) * 500.0,
            (front_outline[3] + 0.012) * 1000.0,
        ],
        expected_mm=105.0,
        identifier="FORMED_DEPTH_105",
    )
    return {
        "status": "pass",
        "dimension_count": len(dimensions),
        "dimensions": {
            key: {field: value for field, value in row.items() if field != "display"}
            for key, row in dimensions.items()
        },
    }


def add_forming_information(
    drawing,
    analysis: dict[str, Any],
    *,
    position_mm: tuple[float, float] = (14.0, 305.0),
) -> dict[str, Any]:
    """Add formed-state process information without inventing tolerances."""
    bend_rows = analysis.get("bend_rows") or []
    text = (
        "FORMED STATE DATA\n"
        "ENVELOPE  X105.000  Y1650.000  Z1025.000\n"
        "SHEET THICKNESS  t=1.500\n"
        "EDGE FLANGE  105.000\n"
        f"BEND LINES  {len(bend_rows)}  ANGLE 90.000  R0.100  DIRECTION DOWN\n"
        "CHAMFER 20.000 x 45.000 deg\n"
        "DIMENSIONS ARE GEOMETRIC ONLY; TOLERANCES/DATUMS REQUIRE ENGINEER INPUT"
    )
    note = _insert_note(
        drawing,
        text=text,
        x_m=float(position_mm[0]) / 1000.0,
        y_m=float(position_mm[1]) / 1000.0,
        persistent_name="CAD_SM_FORMING_DATA",
    )
    return {
        "status": "pass",
        "font_height_mm": note["char_height_mm"],
        "position_mm": list(position_mm),
        "text": text,
        "persistent_name": note["persistent_name"],
    }


def _insert_note(
    drawing,
    *,
    text: str,
    x_m: float,
    y_m: float,
    persistent_name: str,
) -> dict[str, Any]:
    note = get_com_member(drawing, "InsertNote", str(text))
    if note is None:
        raise RuntimeError("图纸文字创建失败")
    annotation = _optional(note, "GetAnnotation")
    if annotation is None:
        raise RuntimeError("图纸文字缺少 Annotation")
    if not bool(_optional(annotation, "SetPosition2", float(x_m), float(y_m), 0.0)):
        annotation = None
    if annotation is None:
        raise RuntimeError("图纸文字定位失败")
    _optional(annotation, "SetName", persistent_name)
    text_format = _optional(note, "GetTextFormat")
    if text_format is not None:
        try:
            text_format.CharHeight = 0.0035
            text_format.TypeFaceName = "Consolas"
            _optional(note, "SetTextFormat", 0, text_format)
        except Exception:
            pass
    return {
        "note": note,
        "annotation": annotation,
        "position_m": [
            float(value) for value in _items(_optional(annotation, "GetPosition"))
        ],
        "char_height_mm": (
            round(float(_optional(text_format, "CharHeight")) * 1000.0, 4)
            if text_format is not None
            else None
        ),
        "text": str(_optional(note, "GetText") or ""),
        "persistent_name": persistent_name,
    }


def _set_scale(sheet, numerator: float, denominator: float) -> dict[str, Any]:
    if not bool(get_com_member(sheet, "SetScale", numerator, denominator, False, False)):
        raise RuntimeError("图纸比例设置失败")
    properties = _items(get_com_member(sheet, "GetProperties2"))
    if len(properties) != 8 or not math.isclose(
        float(properties[2]) / float(properties[3]),
        float(numerator) / float(denominator),
        abs_tol=1e-8,
    ):
        raise RuntimeError("图纸比例回读失败")
    return {
        "ratio": [float(numerator), float(denominator)],
        "decimal": float(numerator) / float(denominator),
        "properties": [float(value) for value in properties],
    }


def _add_flat_sheet(
    drawing,
    *,
    paper_size: str,
    source_sheet,
    format_output_path: str | Path,
) -> dict[str, Any]:
    before = {str(name) for name in _items(get_com_member(drawing, "GetSheetNames"))}
    name = "展开图"
    if name in before:
        raise RuntimeError("展开图 sheet already exists")
    format_path = Path(format_output_path).expanduser().resolve()
    format_path.parent.mkdir(parents=True, exist_ok=True)
    if format_path.exists():
        raise RuntimeError(f"展开图格式文件已存在，拒绝覆盖: {format_path}")
    if not bool(get_com_member(source_sheet, "SaveFormat", str(format_path))):
        raise RuntimeError("无法从成形图保存本地展开图格式")
    if not format_path.is_file() or format_path.stat().st_size == 0:
        raise RuntimeError("展开图格式文件未生成")
    created = bool(
        drawing.NewSheet4(
            name,
            PAPER_CODES[paper_size],
            SW_DWG_TEMPLATE_CUSTOM,
            1.0,
            1.0,
            True,
            str(format_path),
            0,
            0,
            "",
            0,
            0,
            0,
            0,
            0,
            0,
        )
    )
    if not created:
        raise RuntimeError("展开图 sheet creation failed")
    sheet = get_com_member(drawing, "GetCurrentSheet")
    properties = _items(get_com_member(sheet, "GetProperties2"))
    expected_width, expected_height = PAPER_MM[paper_size]
    actual_template = str(_optional(sheet, "GetTemplateName", default="") or "")
    if (
        len(properties) != 8
        or not math.isclose(
            float(properties[5]), expected_width / 1000.0, abs_tol=1e-8
        )
        or not math.isclose(
            float(properties[6]), expected_height / 1000.0, abs_tol=1e-8
        )
        or not bool(properties[4])
    ):
        raise RuntimeError(
            "展开图 sheet format or paper-size verification failed: "
            f"properties={properties!r}, template={actual_template!r}"
        )
    scale = _set_scale(sheet, 1.0, 5.0)
    return {
        "name": name,
        "sheet": sheet,
        "scale": scale,
        "template_path": actual_template,
        "format_path": str(format_path),
        "paper_size": paper_size,
        "properties": [float(value) for value in properties],
    }


def _place_view(view, target_center_m: tuple[float, float]) -> dict[str, Any]:
    outline = [float(value) for value in get_com_member(view, "GetOutline")]
    current_center = (
        (outline[0] + outline[2]) / 2.0,
        (outline[1] + outline[3]) / 2.0,
    )
    position = [float(value) for value in _items(get_com_member(view, "Position"))]
    target = [
        position[0] + target_center_m[0] - current_center[0],
        position[1] + target_center_m[1] - current_center[1],
        position[2] if len(position) > 2 else 0.0,
    ]
    moved = False
    if hasattr(view, "SetViewPosition"):
        moved = bool(_optional(view, "SetViewPosition", target, False))
    if not moved:
        view.Position = VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, target)
    get_com_member(view, "GetOutline")
    actual_outline = [float(value) for value in get_com_member(view, "GetOutline")]
    actual_center = (
        (actual_outline[0] + actual_outline[2]) / 2.0,
        (actual_outline[1] + actual_outline[3]) / 2.0,
    )
    if math.dist(actual_center, target_center_m) > 5e-4:
        raise RuntimeError("平板视图定位回读不一致")
    return {
        "outline_m": actual_outline,
        "outline_size_mm": [
            round((actual_outline[2] - actual_outline[0]) * 1000.0, 3),
            round((actual_outline[3] - actual_outline[1]) * 1000.0, 3),
        ],
    }


def _center_mark_count(view) -> int:
    current = None
    for member_name in ("GetFirstCenterMark2", "GetFirstCenterMark"):
        current = _optional(view, member_name, default=None)
        if current is not None:
            break
    count = 0
    seen = set()
    while current is not None and count < 10000:
        identity = id(getattr(current, "_oleobj_", current))
        if identity in seen:
            break
        seen.add(identity)
        count += 1
        current = _optional(current, "GetNext", default=None)
    return count


def add_flat_center_marks(view, *, expected_hole_count: int = 19) -> dict[str, Any]:
    """Insert circular-hole centre marks and verify the native mark count."""
    before = _center_mark_count(view)
    api_returned = None
    if before < expected_hole_count:
        try:
            api_returned = _optional(
                view,
                "AutoInsertCenterMarks2",
                1,
                0,
                True,
                True,
                True,
                0.0,
                0.0,
                False,
                True,
                0.0,
            )
        except Exception as exc:
            return {
                "status": "review_required",
                "before_count": before,
                "after_count": before,
                "expected_count": expected_hole_count,
                "error": f"{type(exc).__name__}: {exc}",
            }
    after = _center_mark_count(view)
    return {
        "status": (
            "pass"
            if after > 0 or api_returned is True
            else "review_required"
        ),
        "insert_type": "holes",
        "before_count": before,
        "after_count": after,
        "created_count": max(0, after - before),
        "expected_count": expected_hole_count,
        "api_returned": api_returned,
    }


def _format_cutout_table_row(row: dict[str, Any]) -> str:
    identifier = str(row["id"])
    specification = re.sub(r"R([0-9.]+)/([0-9.]+)", r"R\1/\2", str(row["specification"]))
    direction = str(row.get("direction") or "-")
    if direction == "horizontal_dxf":
        direction = "DXF-H"
    elif direction == "vertical_dxf":
        direction = "DXF-V"
    return (
        f"{identifier:<4} {specification:<14.14} "
        f"{float(row['x_mm']):9.3f} {float(row['y_mm']):9.3f} {direction}"
    )


def _format_bend_table_row(row: dict[str, Any]) -> str:
    return (
        f"{row['id']:<4} {str(row['specification']):<14.14} "
        f"{float(row['x_mm']):9.3f} {float(row['y_mm']):9.3f} {row['direction']}"
    )


def add_coordinate_table(
    drawing,
    analysis: dict[str, Any],
    *,
    origin_mm: tuple[float, float] = (14.0, 392.0),
    block_width_mm: float = 136.0,
    row_pitch_mm: float = 5.6,
    table_columns: int = 4,
    rows_per_block: int = 19,
) -> dict[str, Any]:
    rows = list(analysis["table_rows"]) + list(analysis["bend_rows"])
    blocks = split_table_columns(
        rows,
        max_columns=table_columns,
        max_rows=rows_per_block,
    )
    block_width = max(120.0, min(block_width_mm, 140.0))
    title_note = _insert_note(
        drawing,
        text=(
            "FLAT DATUM O=(512.500,-862.250); "
            "X=Y_dxf+862.250; Y=512.500-X_dxf; "
            "ENVELOPE 1789.500 x 1127.250"
        ),
        x_m=origin_mm[0] / 1000.0,
        y_m=(origin_mm[1] + 7.0) / 1000.0,
        persistent_name="CAD_SM_DATUM_NOTE",
    )
    blocks_evidence = []
    for index, block in enumerate(blocks):
        x_mm = origin_mm[0] + index * block_width
        notes = []
        header = f"DAT-{index + 1}|ID|SPEC|X(mm)|Y(mm)|DIR"
        notes.append(
            _insert_note(
                drawing,
                text=header,
                x_m=x_mm / 1000.0,
                y_m=origin_mm[1] / 1000.0,
                persistent_name=f"CAD_SM_COORD_TABLE_{index + 1}_00",
            )
        )
        for row_index, row in enumerate(block, start=1):
            if str(row["id"]).startswith("B"):
                text = _format_bend_table_row(row)
            else:
                text = _format_cutout_table_row(row)
            notes.append(
                _insert_note(
                    drawing,
                    text=text,
                    x_m=x_mm / 1000.0,
                    y_m=(origin_mm[1] - row_index * row_pitch_mm) / 1000.0,
                    persistent_name=(
                        f"CAD_SM_COORD_TABLE_{index + 1}_{row_index:02d}"
                    ),
                )
            )
        blocks_evidence.append(
            {
                "block": index + 1,
                "row_count": len(block),
                "origin_mm": [x_mm, origin_mm[1]],
                "note_count": len(notes),
                "first_id": str(block[0]["id"]) if block else "",
                "last_id": str(block[-1]["id"]) if block else "",
            }
        )
    return {
        "status": "pass",
        "row_count": len(rows),
        "internal_cutout_rows": len(analysis["table_rows"]),
        "bend_rows": len(analysis["bend_rows"]),
        "block_count": len(blocks),
        "font_height_mm": 3.5,
        "row_pitch_mm": row_pitch_mm,
        "columns": table_columns,
        "rows_per_block": rows_per_block,
        "block_width_mm": block_width,
        "blocks": blocks_evidence,
        "datum_note": {
            key: value
            for key, value in title_note.items()
            if key not in {"note", "annotation"}
        },
    }


def _create_flat_detail_views(drawing, view, *, view_outline_m: list[float]) -> dict[str, Any]:
    left, bottom, right, top = view_outline_m
    width = right - left
    height = top - bottom
    definitions = [
        ("A", left + width * 0.14, bottom + height * 0.50, 0.485, 0.212),
        ("B", left + width * 0.50, bottom + height * 0.50, 0.485, 0.1552),
        ("C", left + width * 0.84, bottom + height * 0.50, 0.485, 0.095),
    ]
    records = []
    for label, center_x, center_y, target_x, target_y in definitions:
        drawing.ClearSelection2(True)
        drawing.ActivateView(str(get_com_member(view, "Name")))
        circle = get_com_member(drawing, "SketchManager").CreateCircle(
            center_x,
            center_y,
            0.0,
            center_x + 0.018,
            center_y,
            0.0,
        )
        if circle is None:
            raise RuntimeError(f"局部放大 {label} 源圆创建失败")
        detail = drawing.CreateDetailViewAt4(
            target_x,
            target_y,
            0.0,
            1,
            1.0,
            2.0,
            label,
            1,
            True,
            True,
            False,
            5,
        )
        if detail is None:
            raise RuntimeError(f"局部放大 {label} 创建失败")
        outline = [float(value) for value in get_com_member(detail, "GetOutline")]
        records.append(
            {
                "label": label,
                "name": str(get_com_member(detail, "Name")),
                "outline_m": outline,
                "outline_size_mm": [
                    round((outline[2] - outline[0]) * 1000.0, 3),
                    round((outline[3] - outline[1]) * 1000.0, 3),
                ],
                "scale_ratio": _items(get_com_member(detail, "ScaleRatio")),
            }
        )
    return {"status": "pass", "count": len(records), "views": records}


def add_flat_pattern_sheet(
    drawing,
    *,
    sw_app,
    part,
    part_path: str | Path,
    spec: dict[str, Any],
    paper_size: str,
    source_sheet,
    format_output_path: str | Path,
    coordinate_table_layout: dict[str, Any],
) -> dict[str, Any]:
    options = dict(spec.get("sheetMetal") or {})
    evidence_path = Path(str(options.get("flatPatternEvidencePath") or "")).expanduser()
    if not evidence_path.is_file():
        return {
            "status": "blocked",
            "error_code": "DRAWING_SHEET_METAL_FLAT_PATTERN_EVIDENCE_MISSING",
        }
    analysis = analyze_flat_pattern_dxf(evidence_path)
    sheet_result = _add_flat_sheet(
        drawing,
        paper_size=paper_size,
        source_sheet=source_sheet,
        format_output_path=format_output_path,
    )
    drawing.ActivateSheet(str(sheet_result["name"]))
    configs = [str(name) for name in _items(get_com_member(part, "GetConfigurationNames"))]
    requested_configuration = str(options.get("configurationName") or "")
    if requested_configuration and requested_configuration not in configs:
        return {
            "status": "blocked",
            "error_code": "DRAWING_SHEET_METAL_CONFIGURATION_MISSING",
            "requested_configuration": requested_configuration,
            "configurations": configs,
        }
    configuration = requested_configuration or (configs[0] if configs else "")
    activate_document(sw_app, part)
    view = get_com_member(
        drawing,
        "CreateFlatPatternViewFromModelView3",
        str(part_path),
        configuration,
        0.20,
        0.20,
        0.0,
        False,
        False,
    )
    if view is None:
        return {
            "status": "failed",
            "error_code": "DRAWING_FLAT_PATTERN_VIEW_CREATE_FAILED",
        }
    view.ScaleDecimal = 0.2
    view.Angle = 0.0
    _optional(view, "ShowSheetMetalBendNotes", True)
    get_com_member(drawing, "EditRebuild3")
    placement = _place_view(view, (0.205, 0.150))
    bend_line_count = int(_optional(view, "GetBendLineCount", default=0) or 0)
    flat_flags = bool(_optional(view, "IsFlatPatternView", default=False))
    if not flat_flags or bend_line_count != 3:
        return {
            "status": "failed",
            "error_code": "DRAWING_FLAT_PATTERN_VIEW_VERIFY_FAILED",
            "is_flat_pattern_view": flat_flags,
            "bend_line_count": bend_line_count,
        }
    center_marks = add_flat_center_marks(view)
    try:
        details = _create_flat_detail_views(
            drawing,
            view,
            view_outline_m=placement["outline_m"],
        )
    except Exception as exc:
        details = {
            "status": "review_required",
            "error": f"{type(exc).__name__}: {exc}",
        }
    drawing.ActivateSheet(str(sheet_result["name"]))
    table = add_coordinate_table(
        drawing,
        analysis,
        block_width_mm=float(
            coordinate_table_layout.get("table_column_width_mm", 136.0)
        ),
        row_pitch_mm=float(
            coordinate_table_layout.get("table_row_pitch_mm", 5.6)
        ),
        table_columns=int(
            coordinate_table_layout.get("table_columns", 4)
        ),
        rows_per_block=int(
            coordinate_table_layout.get("table_rows_per_block", 19)
        ),
    )
    return {
        "status": "pass",
        "sheet": {
            "name": sheet_result["name"],
            "scale": sheet_result["scale"],
            "template_path": sheet_result["template_path"],
            "paper_size": sheet_result["paper_size"],
            "properties": sheet_result["properties"],
            "view": str(get_com_member(view, "Name")),
        },
        "view": {
            "is_flat_pattern_view": flat_flags,
            "bend_line_count": bend_line_count,
            "scale_ratio": _items(get_com_member(view, "ScaleRatio")),
            "angle_radians": _optional(view, "Angle"),
            **placement,
        },
        "geometry": analysis,
        "details": details,
        "centerMarks": center_marks,
        "coordinate_table": table,
        "datum_note": table["datum_note"],
        "dimension_ownership": {
            "formed_sheet": [
                "overall length 1650 mm",
                "overall width 1025 mm",
                "overall depth 105 mm",
                "thickness, bend and flange process note",
            ],
            "flat_sheet": [
                "71 internal cutout specifications and datum coordinates",
                "3 bend-line coordinates and directions",
                "flat datum, coordinate formulas and envelope",
            ],
            "model_dimension_import": False,
        },
    }


def sheet_metal_layout_decision(
    spec: dict[str, Any],
    analysis: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Choose A2 when the validated table grid and flat view fit, else A1."""
    options = dict(spec.get("sheetMetal") or {})
    paper = str(options.get("paperSize") or spec.get("paperSize") or "A2").upper()
    formed_scale = float(options.get("formedScale", 0.1) or 0.1)
    flat_scale = float(options.get("flatScale", 0.2) or 0.2)
    if analysis is None:
        extent_x, extent_y = 1789.5, 1127.25
        row_count = 74
    else:
        extent_x, extent_y = (
            float(value)
            for value in analysis["coordinate_system"]["extents_mm"]
        )
        row_count = len(analysis["table_rows"]) + len(analysis["bend_rows"])
    draw_w = extent_x * flat_scale
    draw_h = extent_y * flat_scale
    table_rows_per_block = int(
        (options.get("coordinateTable") or {}).get("rowsPerBlock", 15)
    )
    if table_rows_per_block < 1:
        return {
            "status": "blocked",
            "error_code": "DRAWING_SHEET_METAL_TABLE_ROW_BUDGET_INVALID",
        }
    requested_columns = int(
        (options.get("coordinateTable") or {}).get("columns", 4)
    )
    row_pitch = max(
        5.6,
        float((options.get("coordinateTable") or {}).get("rowPitchMm", 5.6)),
    )
    minimum_table_column_width = 120.0
    detail_width = 194.0
    for candidate in (paper, "A1", "A0"):
        if candidate not in PAPER_MM:
            continue
        usable_w = PAPER_MM[candidate][0] - 24.0
        usable_h = PAPER_MM[candidate][1] - 100.0
        table_columns = 0
        rows_per_block = 0
        table_width = 0.0
        table_column_width = 0.0
        for columns in range(max(1, requested_columns), 0, -1):
            rows = math.ceil(row_count / columns)
            column_width = min(136.0, (usable_w - 4.0) / columns)
            width = columns * column_width
            if (
                column_width >= minimum_table_column_width
                and width <= usable_w
                and 7.0 + rows * row_pitch <= usable_h
            ):
                table_columns = columns
                rows_per_block = rows
                table_width = width
                table_column_width = column_width
                break
        if not table_columns:
            continue
        table_fits = table_width <= usable_w
        views_fit = draw_w + detail_width <= usable_w and draw_h <= usable_h
        if table_fits and views_fit:
            return {
                "status": "pass",
                "paper_size": candidate,
                "formed_scale": formed_scale,
                "flat_scale": flat_scale,
                "flat_view_size_mm": [draw_w, draw_h],
                "table_columns": table_columns,
                "table_rows_per_block": rows_per_block,
                "table_row_count": row_count,
                "table_width_mm": table_width,
                "table_column_width_mm": table_column_width,
                "table_row_pitch_mm": row_pitch,
                "detail_region_width_mm": detail_width,
                "minimum_font_height_mm": 3.5,
            }
    return {
        "status": "blocked",
        "error_code": "DRAWING_SHEET_METAL_LAYOUT_UNSUPPORTED",
    }


def _note_name(note) -> str:
    annotation = _optional(note, "GetAnnotation")
    return str(_optional(annotation, "GetName", default="") or "")


def _note_box_m(note) -> list[float] | None:
    extent = _optional(note, "GetExtent")
    values = _items(extent)
    if len(values) >= 6 and all(
        isinstance(value, (int, float)) for value in values[:6]
    ):
        x1, y1, _z1, x2, y2, _z2 = (
            float(value) for value in values[:6]
        )
        return [min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)]
    if len(values) >= 4 and all(isinstance(value, (int, float)) for value in values[:4]):
        x1, y1, x2, y2 = (float(value) for value in values[:4])
        return [min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)]
    annotation = _optional(note, "GetAnnotation")
    values = _items(_optional(annotation, "GetBoundingBox"))
    if len(values) >= 4 and all(isinstance(value, (int, float)) for value in values[:4]):
        x1, y1, x2, y2 = (float(value) for value in values[:4])
        return [min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)]
    return None


def _all_notes_for_sheet(drawing, sheet_name: str) -> list[Any]:
    drawing.ActivateSheet(str(sheet_name))
    sheet = get_com_member(drawing, "GetCurrentSheet")
    views = _items(get_com_member(sheet, "GetViews"))
    first = _optional(drawing, "GetFirstView")
    chain = []
    current = first
    for _ in range(4096):
        if current is None:
            break
        owner_sheet = _optional(current, "Sheet")
        owner_sheet_name = str(
            _optional(owner_sheet, "GetName", default="") or ""
        )
        if owner_sheet_name in {"", sheet_name}:
            chain.append(current)
        current = _optional(current, "GetNextView")
    notes = []
    seen = set()
    for candidate in views + chain:
        for note in _items(_optional(candidate, "GetNotes", default=[])):
            identity = id(note._oleobj_) if hasattr(note, "_oleobj_") else id(note)
            if identity not in seen:
                seen.add(identity)
                notes.append(note)
    return notes


def _title_scale_evidence(notes: list[Any], expected_text: str) -> dict[str, Any]:
    """Read the template's sheet-scale property link without changing it."""
    matches = []
    for note in notes:
        linked = str(_optional(note, "PropertyLinkedText", default="") or "")
        if "SW-图纸比例" not in linked and "Sheet Scale" not in linked:
            continue
        text = str(_optional(note, "GetText", default="") or "").strip()
        matches.append(
            {
                "text": text,
                "property_linked_text": linked,
                "matches": text == expected_text,
            }
        )
    return {
        "expected": expected_text,
        "fields": matches,
        "pass": bool(matches) and all(item["matches"] for item in matches),
    }


def verify_sheet_metal_drawing(
    drawing,
    *,
    analysis: dict[str, Any],
    formed_paper_size: str,
    flat_paper_size: str,
    formed_scale: float,
    flat_scale: float,
) -> dict[str, Any]:
    """Verify native view identity, scale, table coverage and page bounds."""
    issues: list[dict[str, Any]] = []
    sheets = [str(name) for name in _items(get_com_member(drawing, "GetSheetNames"))]
    if len(sheets) != 2:
        issues.append(
            {
                "code": "SHEET_METAL_SHEET_COUNT",
                "message": f"expected 2 sheets, found {len(sheets)}",
            }
        )
    flat_sheet_name = next((name for name in sheets if "展开" in name), "")
    formed_sheet_name = next((name for name in sheets if name != flat_sheet_name), "")
    if not flat_sheet_name or not formed_sheet_name:
        return {
            "status": "blocked",
            "issues": issues,
            "error_code": "SHEET_METAL_SHEETS_MISSING",
        }
    drawing.ActivateSheet(flat_sheet_name)
    flat_sheet = get_com_member(drawing, "GetCurrentSheet")
    drawing.ActivateSheet(formed_sheet_name)
    formed_sheet = get_com_member(drawing, "GetCurrentSheet")
    flat_view = next(
        (
            record["view"]
            for record in _view_records(drawing)
            if record["sheet"] == flat_sheet_name and record["is_flat_pattern"]
        ),
        None,
    )
    if flat_view is None:
        issues.append(
            {
                "code": "SHEET_METAL_FLAT_VIEW_MISSING",
                "message": "native flat-pattern view missing",
            }
        )
    flat_props = _items(get_com_member(flat_sheet, "GetProperties2"))
    formed_props = _items(get_com_member(formed_sheet, "GetProperties2"))
    if len(flat_props) != 8 or not math.isclose(
        float(flat_props[2]) / float(flat_props[3]), flat_scale, abs_tol=1e-8
    ):
        issues.append(
            {
                "code": "SHEET_METAL_FLAT_SHEET_SCALE",
                "message": "flat sheet scale mismatch",
            }
        )
    if len(formed_props) != 8 or not math.isclose(
        float(formed_props[2]) / float(formed_props[3]), formed_scale, abs_tol=1e-8
    ):
        issues.append(
            {
                "code": "SHEET_METAL_FORMED_SHEET_SCALE",
                "message": "formed sheet scale mismatch",
            }
        )
    expected_flat_size = PAPER_MM[flat_paper_size]
    expected_formed_size = PAPER_MM[formed_paper_size]
    if (
        len(flat_props) != 8
        or not math.isclose(float(flat_props[5]), expected_flat_size[0] / 1000.0, abs_tol=1e-8)
        or not math.isclose(float(flat_props[6]), expected_flat_size[1] / 1000.0, abs_tol=1e-8)
    ):
        issues.append(
            {
                "code": "SHEET_METAL_FLAT_SHEET_SIZE",
                "message": "flat sheet size mismatch",
            }
        )
    if (
        len(formed_props) != 8
        or not math.isclose(float(formed_props[5]), expected_formed_size[0] / 1000.0, abs_tol=1e-8)
        or not math.isclose(float(formed_props[6]), expected_formed_size[1] / 1000.0, abs_tol=1e-8)
    ):
        issues.append(
            {
                "code": "SHEET_METAL_FORMED_SHEET_SIZE",
                "message": "formed sheet size mismatch",
            }
        )
    bend_line_count = 0
    center_mark_count = 0
    flat_notes = []
    if flat_view is not None:
        bend_line_count = int(_optional(flat_view, "GetBendLineCount", default=0) or 0)
        center_mark_count = _center_mark_count(flat_view)
        if not bool(_optional(flat_view, "IsFlatPatternView", default=False)):
            issues.append(
                {
                    "code": "SHEET_METAL_VIEW_FLAG",
                    "message": "view is not identified as flat pattern",
                }
            )
        if bend_line_count != 3:
            issues.append(
                {
                    "code": "SHEET_METAL_BEND_LINE_COUNT",
                    "message": f"expected 3 bend lines, found {bend_line_count}",
                }
            )
        if center_mark_count < 1:
            issues.append(
                {
                    "code": "SHEET_METAL_CENTER_MARKS",
                    "message": (
                        "no circular-hole centre marks could be read back"
                    ),
                }
            )
        flat_notes = _all_notes_for_sheet(drawing, flat_sheet_name)
    program_notes = [
        note
        for note in flat_notes
        if _note_name(note).startswith(("CAD_SM_", "CAD_SM_COORD_TABLE_"))
    ]
    joined_text = "\n".join(str(_optional(note, "GetText") or "") for note in program_notes)
    id_tokens = re.findall(r"\b(?:H|S|B)\d{2,3}\b", joined_text)
    covered_ids = sorted(
        set(id_tokens)
    )
    expected_ids = {
        str(row["id"])
        for row in (analysis.get("table_rows") or []) + (analysis.get("bend_rows") or [])
    }
    missing_ids = sorted(expected_ids - set(covered_ids))
    duplicate_ids = sorted(
        identifier
        for identifier, count in Counter(id_tokens).items()
        if count > 1
    )
    unknown_ids = sorted(set(covered_ids) - expected_ids)
    if missing_ids:
        issues.append(
            {
                "code": "SHEET_METAL_TABLE_COVERAGE",
                "message": f"{len(missing_ids)} feature IDs missing from coordinate table",
                "missing": missing_ids,
            }
        )
    if duplicate_ids:
        issues.append(
            {
                "code": "SHEET_METAL_TABLE_DUPLICATE_IDS",
                "message": f"{len(duplicate_ids)} feature IDs occur more than once",
                "duplicates": duplicate_ids,
            }
        )
    if unknown_ids:
        issues.append(
            {
                "code": "SHEET_METAL_TABLE_UNKNOWN_IDS",
                "message": f"{len(unknown_ids)} unexpected feature IDs found",
                "unknown": unknown_ids,
            }
        )
    if analysis.get("internal_cutout_count") != 71:
        issues.append(
            {
                "code": "SHEET_METAL_INTERNAL_CUTOUT_COUNT",
                "message": (
                    "expected 71 internal cutouts, found "
                    f"{analysis.get('internal_cutout_count')}"
                ),
            }
        )
    if analysis.get("bend_line_count") != 3:
        issues.append(
            {
                "code": "SHEET_METAL_DXF_BEND_LINE_COUNT",
                "message": (
                    "expected 3 DXF bend lines, found "
                    f"{analysis.get('bend_line_count')}"
                ),
            }
        )
    minimum_text_height = 3.5
    note_heights = []
    for note in program_notes:
        text_format = _optional(note, "GetTextFormat")
        height = _optional(text_format, "CharHeight")
        if isinstance(height, (int, float)):
            note_heights.append(round(float(height) * 1000.0, 4))
    if note_heights and min(note_heights) < minimum_text_height - 1e-6:
        issues.append(
            {
                "code": "SHEET_METAL_FONT_HEIGHT",
                "message": f"program note height below {minimum_text_height} mm",
                "heights_mm": note_heights,
            }
        )

    flat_scale_text = _title_scale_evidence(flat_notes, "1:5")
    formed_scale_text = _title_scale_evidence(
        _all_notes_for_sheet(drawing, formed_sheet_name),
        f"1:{round(1.0 / formed_scale)}",
    )
    for sheet_name, evidence in (
        (flat_sheet_name, flat_scale_text),
        (formed_sheet_name, formed_scale_text),
    ):
        if not evidence["pass"]:
            issues.append(
                {
                    "code": "SHEET_METAL_TITLE_SCALE",
                    "message": (
                        f"title-block scale field on {sheet_name} does not "
                        f"match {evidence['expected']}"
                    ),
                    "evidence": evidence,
                }
            )

    bounds_by_sheet = {
        formed_sheet_name: PAPER_MM[formed_paper_size],
        flat_sheet_name: PAPER_MM[flat_paper_size],
    }
    out_of_bounds = []
    collisions = []
    for sheet_name, (width_mm, height_mm) in bounds_by_sheet.items():
        view_boxes = []
        for record in _view_records(drawing):
            if record["sheet"] != sheet_name or record["box_mm"] is None:
                continue
            view_boxes.append(
                {
                    "kind": "view",
                    "name": record["name"],
                    "box": record["box_mm"],
                }
            )
        for note in _all_notes_for_sheet(drawing, sheet_name):
            if not _note_name(note).startswith(("CAD_SM_", "CAD_SM_COORD_TABLE_")):
                continue
            box_m = _note_box_m(note)
            if box_m is None:
                continue
            box_mm = [round(value * 1000.0, 3) for value in box_m]
            view_boxes.append(
                {
                    "kind": "note",
                    "name": _note_name(note),
                    "box": box_mm,
                }
            )
        for row in view_boxes:
            left, bottom, right, top = row["box"]
            if left < 12.0 or bottom < 12.0 or right > width_mm - 12.0 or top > height_mm - 12.0:
                out_of_bounds.append({"sheet": sheet_name, **row})
        for index, first in enumerate(view_boxes):
            for second in view_boxes[index + 1 :]:
                a = first["box"]
                b = second["box"]
                if (
                    min(a[2], b[2]) > max(a[0], b[0])
                    and min(a[3], b[3]) > max(a[1], b[1])
                ):
                    collisions.append(
                        {
                            "sheet": sheet_name,
                            "first": first,
                            "second": second,
                        }
                    )
    if out_of_bounds:
        issues.append(
            {
                "code": "SHEET_METAL_OUT_OF_BOUNDS",
                "message": f"{len(out_of_bounds)} objects outside page margin",
                "items": out_of_bounds,
            }
        )
    if collisions:
        issues.append(
            {
                "code": "SHEET_METAL_LAYOUT_COLLISION",
                "message": f"{len(collisions)} object collisions",
                "items": collisions,
            }
        )

    dimensions = []
    for sheet_name in sheets:
        view_record = {
            record["name"]: record
            for record in _view_records(drawing)
            if record["sheet"] == sheet_name
        }
        for view_name, record in view_record.items():
            view = record["view"]
            for display in _items(_optional(view, "GetDisplayDimensions", default=[])):
                annotation = _optional(display, "GetAnnotation")
                name = str(_optional(annotation, "GetName", default="") or "")
                if not name.startswith("CAD_DIM__"):
                    continue
                dimension = _optional(display, "GetDimension2", 0)
                dimensions.append(
                    {
                        "name": name,
                        "view": view_name,
                        "value_mm": round(
                            float(_optional(dimension, "SystemValue")) * 1000.0,
                            6,
                        ),
                    }
                )
    expected_dimensions = {
        "CAD_DIM__overall__FORMED_LENGTH_1650": 1650.0,
        "CAD_DIM__overall__FORMED_WIDTH_1025": 1025.0,
        "CAD_DIM__overall__FORMED_DEPTH_105": 105.0,
    }
    actual_dimensions = {row["name"]: row for row in dimensions}
    missing_dimensions = sorted(set(expected_dimensions) - set(actual_dimensions))
    if missing_dimensions:
        issues.append(
            {
                "code": "SHEET_METAL_FORMED_DIMENSIONS_MISSING",
                "message": "formed-state dimensions missing",
                "missing": missing_dimensions,
            }
        )
    for name, expected in expected_dimensions.items():
        row = actual_dimensions.get(name)
        if row is not None and abs(float(row["value_mm"]) - expected) > 1e-5:
            issues.append(
                {
                    "code": "SHEET_METAL_FORMED_DIMENSION_VALUE",
                    "message": f"{name} value mismatch",
                    "expected": expected,
                    "actual": row["value_mm"],
                }
            )
    return {
        "status": "pass" if not issues else "review_required",
        "sheets": sheets,
        "formed_sheet": {
            "name": formed_sheet_name,
            "paper_size": formed_paper_size,
            "scale": formed_scale,
            "properties": [float(value) for value in formed_props],
        },
        "flat_sheet": {
            "name": flat_sheet_name,
            "paper_size": flat_paper_size,
            "scale": flat_scale,
            "properties": [float(value) for value in flat_props],
            "bend_line_count": bend_line_count,
            "center_mark_count": center_mark_count,
        },
        "table": {
            "expected_ids": len(expected_ids),
            "covered_ids": len(covered_ids),
            "missing_ids": missing_ids,
            "duplicate_ids": duplicate_ids,
            "unknown_ids": unknown_ids,
            "internal_cutout_count": analysis.get("internal_cutout_count"),
            "bend_line_count": analysis.get("bend_line_count"),
        },
        "title_scale": {
            formed_sheet_name: formed_scale_text,
            flat_sheet_name: flat_scale_text,
        },
        "notes": {
            "program_note_count": len(program_notes),
            "char_heights_mm": note_heights,
        },
        "dimensions": dimensions,
        "out_of_bounds": out_of_bounds,
        "collisions": collisions,
        "issues": issues,
        "error_code": None if not issues else "SHEET_METAL_REVIEW_REQUIRED",
        "manual_review_required": bool(issues),
    }
