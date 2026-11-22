"""
SolidWorks 工程图操作工具
"""
import math
import os
import re
import xml.etree.ElementTree as ET
from fractions import Fraction
from pathlib import Path

try:
    from scripts.sw_preflight import import_com_dependencies
    from scripts.sw_connect import create_empty_dispatch_variant, get_com_member
except ImportError:
    from sw_preflight import import_com_dependencies
    from sw_connect import create_empty_dispatch_variant, get_com_member

pythoncom, _win32com, VARIANT = import_com_dependencies()


PAPER_SIZES = {
    # SolidWorks.Interop.swconst.swDwgPaperSizes_e
    "A4": {"code": 6, "width_m": 0.297, "height_m": 0.210},
    "A4P": {"code": 7, "width_m": 0.210, "height_m": 0.297},
    "A3": {"code": 8, "width_m": 0.420, "height_m": 0.297},
    "A2": {"code": 9, "width_m": 0.594, "height_m": 0.420},
    "A1": {"code": 10, "width_m": 0.841, "height_m": 0.594},
    "A0": {"code": 11, "width_m": 1.189, "height_m": 0.841},
}

SW_DEFAULT_DRAWING_TEMPLATE_PREFERENCE = 10
SW_DWG_TEMPLATE_CUSTOM = 12

STANDARD_DRAWING_SCALES = (10.0, 5.0, 2.0, 1.0, 0.5, 0.2, 0.1, 0.05, 0.02, 0.01)

TITLE_BLOCK_FIELDS = ("drawingNumber", "name", "material", "scale", "date")
TITLE_BLOCK_CONTROL_FIELDS = {
    "required",
    "format",
    "propertyMap",
    "configurationName",
    "fieldPositionsMm",
    "linkToModelProperties",
    "overwriteExistingFields",
    "manualOverride",
}
TITLE_FIELD_PROPERTY_ALIASES = {
    "drawingNumber": (
        "PartNumber",
        "Part Number",
        "DrawingNumber",
        "图纸编号",
        "图号",
        "零件代号",
        "代号",
    ),
    "name": ("Description", "Title", "Name", "名称", "零件名称"),
    "material": ("Material", "材料"),
    "scale": ("Scale", "比例", "SW-图纸比例(Sheet Scale)", "图纸比例"),
    "date": (
        "Date",
        "日期",
        "设计日期",
        "校核日期",
        "审核日期",
        "批准日期",
        "审查日期",
        "工艺日期",
        "标准日期",
        "主管设计日期",
    ),
}
# The shipped SW2025 A3 GB format reserves the lower-right title block. These
# anchors deliberately sit in separate cells and are overridable in DrawingSpec.
DEFAULT_A3_GB_TITLE_FIELD_CELLS_MM = {
    "drawingNumber": {"positionMm": [290.0, 64.0], "maxWidthMm": 24.0, "maxLines": 1},
    "name": {"positionMm": [362.0, 65.0], "maxWidthMm": 38.0, "maxLines": 2},
    "material": {"positionMm": [318.0, 64.0], "maxWidthMm": 16.0, "maxLines": 1},
    "scale": {"positionMm": [334.0, 56.0], "maxWidthMm": 18.0, "maxLines": 1},
    "date": {"positionMm": [337.0, 64.0], "maxWidthMm": 20.0, "maxLines": 1},
}

# SolidWorks.Interop.swconst.swAlignDimensionType_e（SW2026 Interop 反射确认）。
ALIGN_DIMENSION_TYPES = {
    "auto_arrange": 0,
    "space_evenly": 1,
    "colinear": 2,
    "stagger": 3,
    "top_align_text": 4,
    "bottom_align_text": 5,
    "left_align_text": 6,
    "right_align_text": 7,
}

# SolidWorks.Interop.swconst.swAutoInsertCenterMarkTypes_e
# （SW2026 Interop 反射与官方 API 帮助交叉确认）。
AUTO_CENTER_MARK_TARGETS = {
    "holes": 1,
    "fillets": 2,
    "slots": 4,
}


def _safe_member(obj, name, *args, default=None):
    """@brief 读取工程图 COM 成员，失败时返回默认值。"""
    if obj is None:
        return default
    try:
        value = get_com_member(obj, name, *args)
        return default if value is None else value
    except Exception:
        return default


def _as_sequence(value):
    """@brief 统一 COM 数组、元组和单对象返回值。"""
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _normalise_box(value):
    """@brief 将 COM Outline/GetBox 数组统一为二维边界框。"""
    if isinstance(value, dict) and {"left", "bottom", "right", "top"} <= set(value):
        try:
            x1, y1, x2, y2 = (float(value[key]) for key in ("left", "bottom", "right", "top"))
        except (TypeError, ValueError):
            return None
        return {"left": min(x1, x2), "bottom": min(y1, y2), "right": max(x1, x2), "top": max(y1, y2)}
    values = _as_sequence(value)
    try:
        if len(values) >= 6:
            x1, y1, x2, y2 = float(values[0]), float(values[1]), float(values[3]), float(values[4])
        elif len(values) >= 4:
            x1, y1, x2, y2 = map(float, values[:4])
        else:
            return None
    except (TypeError, ValueError):
        return None
    return {
        "left": min(x1, x2),
        "bottom": min(y1, y2),
        "right": max(x1, x2),
        "top": max(y1, y2),
    }


def _annotation_box(owner):
    """@brief 读取尺寸、注释或表格注解的二维包围盒。"""
    annotation = _safe_member(owner, "GetAnnotation") or owner
    return _normalise_box(_safe_member(annotation, "GetBox"))


def _view_display_dimensions(view):
    """@brief 兼容数组接口与链式接口，返回视图中的真实 DisplayDimension。"""
    dimensions = _as_sequence(_safe_member(view, "GetDisplayDimensions", default=[]))
    if dimensions:
        return dimensions
    current = _safe_member(view, "GetFirstDisplayDimension5") or _safe_member(view, "GetFirstDisplayDimension")
    while current is not None:
        dimensions.append(current)
        current = _safe_member(view, "GetNextDisplayDimension", current)
    return dimensions


def _display_dimension_native_name(display_dimension):
    """Return the persistent model-dimension identity, never a value-only key."""
    native = (
        _safe_member(display_dimension, "GetDimension2", 0)
        or _safe_member(display_dimension, "GetDimension")
    )
    name = str(_safe_member(native, "FullName", default="") or "").strip()
    annotation = _safe_member(display_dimension, "GetAnnotation")
    annotation_name = str(_safe_member(annotation, "GetName", default="") or "").strip()
    return name, annotation_name


def _display_dimension_signature(display_dimension):
    """Build a deduplication key from native geometry identity and type/value."""
    full_name, annotation_name = _display_dimension_native_name(display_dimension)
    identity = full_name or annotation_name
    if not identity:
        return None
    native_type = _safe_member(display_dimension, "Type2", default=None)
    native = (
        _safe_member(display_dimension, "GetDimension2", 0)
        or _safe_member(display_dimension, "GetDimension")
    )
    value = _safe_member(native, "SystemValue", default=None)
    try:
        value = round(float(value), 9)
    except (TypeError, ValueError):
        value = None
    return (identity.casefold(), native_type, value)


def deduplicate_drawing_dimensions(drawing_model) -> dict:
    """Remove duplicate display dimensions that reference the same native dimension.

    Numeric equality alone is deliberately insufficient: two independent model
    dimensions may share a value. Only one DisplayDimension for the same
    SolidWorks dimension identity is retained, preferring the active view and
    then the front/top/right semantic views.
    """
    records = []
    for sheet_name in _as_sequence(_safe_member(drawing_model, "GetSheetNames", default=[])) or [""]:
        sheet = _safe_member(drawing_model, "GetSheet", sheet_name) or _safe_member(drawing_model, "GetCurrentSheet")
        for view in _as_sequence(_safe_member(sheet, "GetViews", default=[])):
            semantic = _normalise_orientation(_safe_member(view, "GetOrientationName", default=""))
            active_name = str(_safe_member(drawing_model, "GetActiveViewName", default="") or "")
            view_name = str(_safe_member(view, "Name", default="") or "")
            for dimension in _view_display_dimensions(view):
                records.append({
                    "sheet": str(sheet_name),
                    "view": view,
                    "view_name": view_name,
                    "semantic_view": semantic,
                    "active": bool(active_name and view_name == active_name),
                    "dimension": dimension,
                    "signature": _display_dimension_signature(dimension),
                })

    groups = {}
    unverified_count = 0
    for record in records:
        if record["signature"] is None:
            unverified_count += 1
            continue
        groups.setdefault(record["signature"], []).append(record)

    preference = {"front": 0, "top": 1, "right": 2}
    removed = []
    unresolved = []
    deletion_attempts = []

    for signature, group in groups.items():
        if len(group) < 2:
            continue
        group.sort(key=lambda item: (
            0 if item["active"] else 1,
            preference.get(item["semantic_view"], 9),
            item["sheet"].casefold(),
            item["view_name"].casefold(),
        ))
        keep = group[0]
        for duplicate in group[1:]:
            annotation = _safe_member(duplicate["dimension"], "GetAnnotation")
            _safe_member(drawing_model, "ClearSelection2", True)
            selected = bool(_safe_member(annotation, "Select2", False, 0, default=False))
            if not selected:
                selected = bool(_safe_member(annotation, "Select", False, default=False))
            if not selected:
                unresolved.append({
                    "signature": list(signature),
                    "view": duplicate["view_name"],
                    "reason": "annotation_selection_failed",
                })
                continue
            delete_requested = False
            delete_error = None
            try:
                delete_requested = bool(_safe_member(drawing_model, "EditDelete", default=False))
            except Exception as exc:
                delete_error = str(exc)
            if not delete_requested:
                extension = _safe_member(drawing_model, "Extension")
                try:
                    result = get_com_member(extension, "DeleteSelection2", 0)
                    delete_requested = result is not False and result is not None
                except Exception as exc:
                    delete_error = str(exc)
            _safe_member(drawing_model, "ClearSelection2", True)
            deletion_attempts.append({
                "signature": signature,
                "keep_view": keep["view_name"],
                "removed_view": duplicate["view_name"],
                "delete_requested": delete_requested,
                "delete_error": delete_error,
                "original_count": len(group),
            })
    if deletion_attempts:
        _safe_member(drawing_model, "ForceRebuild3", False)
        _safe_member(drawing_model, "GraphicsRedraw2")
    final_counts = {}
    for sheet_name in _as_sequence(_safe_member(drawing_model, "GetSheetNames", default=[])) or [""]:
        sheet = _safe_member(drawing_model, "GetSheet", sheet_name) or _safe_member(drawing_model, "GetCurrentSheet")
        for view in _as_sequence(_safe_member(sheet, "GetViews", default=[])):
            for dimension in _view_display_dimensions(view):
                signature = _display_dimension_signature(dimension)
                if signature is not None:
                    final_counts[signature] = final_counts.get(signature, 0) + 1
    for attempt in deletion_attempts:
        if final_counts.get(attempt["signature"], 0) <= 1:
            removed.append({
                "signature": list(attempt["signature"]),
                "kept_view": attempt["keep_view"],
                "removed_view": attempt["removed_view"],
            })
        else:
            unresolved.append({
                "signature": list(attempt["signature"]),
                "view": attempt["removed_view"],
                "reason": attempt["delete_error"] or "duplicate_still_present_after_rebuild",
            })
    duplicate_groups = sum(1 for count in final_counts.values() if count > 1)
    return {
        "status": "pass" if not unresolved else "review_required",
        "method": "solidworks_native_dimension_identity",
        "dimension_count": len(records),
        "unique_dimension_identities": len(groups),
        "duplicate_group_count": duplicate_groups,
        "removed_count": len(removed),
        "removed": removed,
        "unresolved": unresolved,
        "unverifiable_identity_count": unverified_count,
        "error_code": None if not unresolved else "DRAWING_DIMENSION_DEDUP_INCOMPLETE",
        "manual_review_required": bool(unresolved or unverified_count),
    }


def auto_arrange_drawing_dimensions(drawing_model, *, spacing_m=0.01, mode="auto_arrange") -> dict:
    """@brief 使用 SolidWorks 官方 AlignDimensions 对每个视图的尺寸自动排列。

    该接口只负责 SolidWorks 自身的尺寸布局，不提供尺寸文字包围盒，也不能证明最终
    图面无重叠。调用后仍必须导出 PDF/BMP 做视觉复核。
    """
    spacing, spacing_valid = _finite_positive(spacing_m, 0.01)
    if not spacing_valid or spacing > 0.1:
        raise ValueError("spacing_m 必须是 (0, 0.1] 米范围内的有限数值。")
    if mode not in ALIGN_DIMENSION_TYPES:
        raise ValueError(f"未知尺寸排列模式: {mode}")
    extension = _safe_member(drawing_model, "Extension")
    if extension is None or not hasattr(extension, "AlignDimensions"):
        return {
            "status": "blocked",
            "stage": "arrange",
            "method": "IModelDocExtension.AlignDimensions",
            "mode": mode,
            "spacing_m": spacing,
            "views": [],
            "selected_dimension_count": 0,
            "manual_review_required": True,
            "retryable": False,
            "error_code": "DRAWING_ALIGN_DIMENSIONS_API_UNAVAILABLE",
        }

    results = []
    total_selected = 0
    sheets = _as_sequence(_safe_member(drawing_model, "GetSheetNames", default=[]))
    for sheet_name in sheets or [""]:
        sheet = _safe_member(drawing_model, "GetSheet", sheet_name) or _safe_member(drawing_model, "GetCurrentSheet")
        for view in _as_sequence(_safe_member(sheet, "GetViews", default=[])):
            dimensions = _view_display_dimensions(view)
            _safe_member(drawing_model, "ClearSelection2", True)
            selected = 0
            for dimension in dimensions:
                annotation = _safe_member(dimension, "GetAnnotation")
                if annotation is None:
                    continue
                selected_ok = _safe_member(annotation, "Select2", selected > 0, 0, default=False)
                if not selected_ok:
                    selected_ok = _safe_member(annotation, "Select", selected > 0, default=False)
                if selected_ok:
                    selected += 1
            attempted = selected >= 2
            aligned = False
            error = None
            if attempted:
                try:
                    aligned = bool(get_com_member(extension, "AlignDimensions", ALIGN_DIMENSION_TYPES[mode], spacing))
                except Exception as exc:
                    error = str(exc)
            results.append({
                "sheet": str(sheet_name),
                "view": str(_safe_member(view, "Name", default="") or ""),
                "dimension_count": len(dimensions),
                "selected_count": selected,
                "attempted": attempted,
                "aligned": aligned,
                "error": error,
            })
            total_selected += selected
    _safe_member(drawing_model, "ClearSelection2", True)
    _safe_member(drawing_model, "ForceRebuild3", False)
    _safe_member(drawing_model, "GraphicsRedraw2")
    attempted_results = [item for item in results if item["attempted"]]
    failed_results = [item for item in attempted_results if not item["aligned"]]
    if not attempted_results:
        status = "review_required"
        error_code = "DRAWING_ALIGN_DIMENSIONS_NOT_ENOUGH_PER_VIEW"
    elif failed_results:
        status = "review_required"
        error_code = "DRAWING_ALIGN_DIMENSIONS_PARTIAL"
    else:
        status = "pass"
        error_code = None
    return {
        "status": status,
        "stage": "arrange",
        "method": "IModelDocExtension.AlignDimensions",
        "mode": mode,
        "enum_value": ALIGN_DIMENSION_TYPES[mode],
        "spacing_m": spacing,
        "views": results,
        "selected_dimension_count": total_selected,
        "aligned_view_count": sum(1 for item in results if item["aligned"]),
        "manual_review_required": True,
        "retryable": bool(failed_results),
        "error_code": error_code,
        "limitations": ["官方排列接口不返回文字包围盒；排列后仍需 PDF/BMP 目视复核。"],
    }


def _finite_positive(value, default):
    """@brief 将 COM 数值转成有限正数，否则使用保守默认值。"""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return float(default), False
    if not math.isfinite(number) or number <= 0:
        return float(default), False
    return number, True


def _dimension_text_evidence(display_dimension) -> dict:
    """@brief 收集尺寸文字片段；不伪造 SolidWorks 最终格式化文本。"""
    parts = []
    for index, label in ((0, "all"), (1, "prefix"), (2, "suffix"), (3, "callout_above"), (4, "callout_below")):
        value = str(_safe_member(display_dimension, "GetText", index, default="") or "")
        if value:
            parts.append({"index": index, "kind": label, "text": value})
    all_text = next((item["text"] for item in parts if item["kind"] == "all"), "")
    if all_text:
        lines = all_text.splitlines() or [all_text]
        source = "display_dimension_get_text_all"
        rendered_value_available = True
    else:
        explicit = [item["text"] for item in parts if item["kind"] != "all"]
        # GetText() 在 SW2026 常只返回用户前后缀，不返回格式化后的主尺寸值。
        # 用 8 个等宽字符作为主值占位，避免把空字符串估成零宽度。
        lines = ["".join(explicit) + "0000.000"]
        source = "explicit_parts_plus_conservative_value_placeholder" if explicit else "conservative_value_placeholder"
        rendered_value_available = False
    return {
        "parts": parts,
        "estimation_lines": lines,
        "source": source,
        "rendered_value_available": rendered_value_available,
    }


def estimate_dimension_text_box(display_dimension, *, padding_m=None) -> dict:
    """@brief 用 IAnnotation 锚点和 ITextFormat 保守估算尺寸文字边界。

    SW2026 没有尺寸文字的原生 bounding-box API。本函数输出任意旋转文字都能
    被覆盖的轴对齐外接方框，并明确标记 ``source=estimated``；不能作为原生几何证据。
    """
    annotation = _safe_member(display_dimension, "GetAnnotation")
    position = _as_sequence(_safe_member(annotation, "GetPosition", default=[]))
    try:
        x, y = float(position[0]), float(position[1])
        position_available = math.isfinite(x) and math.isfinite(y)
    except (IndexError, TypeError, ValueError):
        x = y = 0.0
        position_available = False

    text_format = _safe_member(annotation, "GetTextFormat", 0)
    format_source = "IAnnotation.GetTextFormat(0)"
    if text_format is None:
        text_format = _safe_member(display_dimension, "GetTextFormat")
        format_source = "IDisplayDimension.GetTextFormat()"
    char_height, char_height_available = _finite_positive(
        _safe_member(text_format, "CharHeight"),
        0.0035,
    )
    width_factor, width_factor_available = _finite_positive(
        _safe_member(text_format, "WidthFactor"),
        1.0,
    )
    spacing_factor, spacing_factor_available = _finite_positive(
        _safe_member(text_format, "CharSpacingFactor"),
        1.0,
    )
    text = _dimension_text_evidence(display_dimension)
    lines = text["estimation_lines"] or ["0000.000"]

    def line_units(line):
        """@brief 估算单行字宽；中文和全角字符按一个字高计。"""
        units = 0.0
        for character in line or " ":
            units += 1.0 if ord(character) > 0xFF else 0.62
        return max(units, 0.62)

    max_units = max(line_units(line) for line in lines)
    line_count = max(1, len(lines))
    estimated_width = max_units * char_height * width_factor * spacing_factor
    estimated_height = line_count * char_height * 1.25
    padding = max(0.001, char_height * 0.4) if padding_m is None else max(0.0, float(padding_m))
    # 尺寸文字角度未由 API 暴露；使用矩形对角线作为任意旋转下的方形包络。
    half_extent = math.hypot(estimated_width, estimated_height) / 2.0 + padding
    box = None
    if position_available:
        box = {
            "left": x - half_extent,
            "bottom": y - half_extent,
            "right": x + half_extent,
            "top": y + half_extent,
        }

    available_fields = sum((position_available, char_height_available, width_factor_available, spacing_factor_available))
    if position_available and available_fields == 4 and text["rendered_value_available"]:
        confidence = "medium"
    elif position_available:
        confidence = "low"
    else:
        confidence = "unavailable"
    return {
        "box": box,
        "source": "estimated",
        "confidence": confidence,
        "method": "annotation_position_text_format_arbitrary_rotation_envelope",
        "native_bounding_box_available": False,
        "position_m": [x, y] if position_available else None,
        "text_evidence": text,
        "text_format": {
            "source": format_source if text_format is not None else "conservative_defaults",
            "char_height_m": char_height,
            "width_factor": width_factor,
            "char_spacing_factor": spacing_factor,
            "char_height_available": char_height_available,
            "width_factor_available": width_factor_available,
            "char_spacing_factor_available": spacing_factor_available,
        },
        "estimated_unrotated_size_m": {"width": estimated_width, "height": estimated_height},
        "padding_m": padding,
        "orientation_assumption": "unknown_angle_conservative_square_envelope",
        "limitations": [
            "SolidWorks 2026 IAnnotation 不提供尺寸文字原生包围盒",
            "主尺寸格式化值可能不由 GetText 返回，缺失时使用保守占位宽度",
            "估算只能用于碰撞风险筛查，最终交付仍需 PDF/BMP 目视复核",
        ],
    }


def _normalise_paper_size(paper_size):
    """Return a supported canonical paper-size name or None for the default."""
    if paper_size is None or not str(paper_size).strip():
        return None
    value = re.sub(r"[\s_-]+", "", str(paper_size).strip().upper())
    aliases = {
        "A0": "A0",
        "A1": "A1",
        "A2": "A2",
        "A3": "A3",
        "A4": "A4",
        "A4P": "A4P",
        "A4PORTRAIT": "A4P",
        "A4纵向": "A4P",
    }
    result = aliases.get(value)
    if result is None:
        raise ValueError(f"不支持的图幅: {paper_size}")
    return result


def _paper_size_from_dimensions(width_m, height_m):
    """Map actual template dimensions to a canonical standard paper size."""
    try:
        width_m = float(width_m)
        height_m = float(height_m)
    except (TypeError, ValueError):
        return None
    if not (math.isfinite(width_m) and math.isfinite(height_m)):
        return None
    for name, spec in PAPER_SIZES.items():
        if (
            math.isclose(width_m, spec["width_m"], abs_tol=1e-6, rel_tol=0)
            and math.isclose(height_m, spec["height_m"], abs_tol=1e-6, rel_tol=0)
        ):
            return name
    return None


def _template_name_is_gbt(path):
    """Return whether a template's file name is an explicit GB/T candidate."""
    name = Path(str(path or "")).stem.casefold()
    compact = re.sub(r"[^a-z0-9\u4e00-\u9fff]", "", name)
    return (
        "gbt" in compact
        or "国标" in compact
        or bool(re.search(r"(?:^|[^a-z0-9])gb(?:t)?(?:[^a-z0-9]|$)", name, re.IGNORECASE))
    )


def _inspect_drawing_template(sw, template_path):
    """Read the actual sheet size of a ``.drwdot`` template."""
    path = Path(os.path.abspath(os.path.expandvars(os.path.expanduser(str(template_path))))).resolve()
    result = {
        "path": str(path),
        "exists": path.is_file(),
        "is_drawing_template": path.suffix.casefold() == ".drwdot",
    }
    if not result["exists"]:
        result.update({"status": "blocked", "error_code": "DRAWING_TEMPLATE_MISSING"})
        return result
    if not result["is_drawing_template"]:
        result.update({"status": "blocked", "error_code": "DRAWING_TEMPLATE_NOT_DRWDOT"})
        return result
    try:
        values = get_com_member(sw, "GetTemplateSizes", str(path), default=None)
    except Exception as exc:
        result.update({
            "status": "blocked",
            "error_code": "DRAWING_TEMPLATE_SIZE_UNAVAILABLE",
            "error": str(exc),
        })
        return result
    values = _as_sequence(values)
    if len(values) < 3:
        result.update({"status": "blocked", "error_code": "DRAWING_TEMPLATE_SIZE_UNAVAILABLE"})
        return result
    try:
        width_m = float(values[1])
        height_m = float(values[2])
    except (TypeError, ValueError):
        result.update({"status": "blocked", "error_code": "DRAWING_TEMPLATE_SIZE_UNAVAILABLE"})
        return result
    if not (math.isfinite(width_m) and math.isfinite(height_m) and width_m > 0 and height_m > 0):
        result.update({"status": "blocked", "error_code": "DRAWING_TEMPLATE_SIZE_UNAVAILABLE"})
        return result
    paper_size = _paper_size_from_dimensions(width_m, height_m)
    if paper_size is None:
        result.update({
            "status": "blocked",
            "error_code": "DRAWING_TEMPLATE_CUSTOM_SIZE_UNSUPPORTED",
            "width_m": width_m,
            "height_m": height_m,
        })
        return result
    result.update({
        "status": "pass",
        "paper_size": paper_size,
        "width_m": width_m,
        "height_m": height_m,
        "orientation": "landscape" if width_m > height_m else "portrait",
        "gbt_candidate": _template_name_is_gbt(path),
        "error_code": None,
    })
    return result


def _drawing_template_preference_paths(sw):
    """Read configured drawing-template paths without changing preferences."""
    raw = str(get_com_member(
        sw,
        "GetUserPreferenceStringValue",
        SW_DEFAULT_DRAWING_TEMPLATE_PREFERENCE,
        default="",
    ) or "")
    return [
        Path(os.path.abspath(os.path.expandvars(os.path.expanduser(item.strip().strip('"')))))
        for item in raw.split(";")
        if item.strip()
    ]


def resolve_drawing_template(
    sw,
    *,
    paper_size=None,
    explicit_template=None,
    template_candidates=(),
    standard="GB_T",
):
    """Resolve and verify a whole drawing template according to user policy.

    An explicit template wins. A requested paper size otherwise selects a
    dimension-verified ``.drwdot`` from the configured template directory. With
    no paper size, the active SolidWorks default drawing template is used.
    """
    requested = _normalise_paper_size(paper_size)
    explicit = str(explicit_template or "").strip()
    if explicit:
        inspected = _inspect_drawing_template(sw, explicit)
        if inspected["status"] != "pass":
            return {
                **inspected,
                "mode": "explicit",
                "requested_paper_size": requested,
                "selected": None,
                "manual_review_required": True,
            }
        if requested is not None and inspected["paper_size"] != requested:
            return {
                **inspected,
                "status": "blocked",
                "mode": "explicit",
                "requested_paper_size": requested,
                "selected": None,
                "error_code": "DRAWING_TEMPLATE_SIZE_MISMATCH",
                "manual_review_required": True,
            }
        return {
            **inspected,
            "mode": "explicit",
            "requested_paper_size": requested,
            "selected": inspected["path"],
            "manual_review_required": False,
        }

    configured_paths = _drawing_template_preference_paths(sw)
    default_file = next((path for path in configured_paths if path.is_file()), None)
    if requested is None:
        if len(configured_paths) != 1 or default_file is None:
            return {
                "status": "blocked",
                "mode": "default",
                "requested_paper_size": None,
                "selected": None,
                "error_code": "DRAWING_DEFAULT_TEMPLATE_MISSING",
                "manual_review_required": True,
            }
        inspected = _inspect_drawing_template(sw, default_file)
        return {
            **inspected,
            "mode": "default",
            "requested_paper_size": None,
            "selected": inspected["path"] if inspected["status"] == "pass" else None,
        }

    default_inspection = _inspect_drawing_template(sw, default_file) if default_file is not None else None
    if (
        default_inspection
        and default_inspection.get("status") == "pass"
        and default_inspection.get("paper_size") == requested
    ):
        return {
            **default_inspection,
            "mode": "default",
            "requested_paper_size": requested,
            "selected": default_inspection["path"],
            "manual_review_required": False,
        }

    explicit_candidates = []
    for raw_path in _as_sequence(template_candidates):
        path = Path(os.path.abspath(os.path.expandvars(os.path.expanduser(str(raw_path)))))
        if path.suffix.casefold() == ".drwdot":
            explicit_candidates.append(path.resolve())
    directory_paths = []
    for configured in configured_paths:
        directory = configured if configured.is_dir() else configured.parent
        if directory.is_dir():
            directory_paths.append(directory)
    candidates = list(dict.fromkeys(explicit_candidates + [
        path.resolve()
        for directory in directory_paths
        for path in sorted(directory.glob("*.drwdot"), key=lambda item: item.name.casefold())
    ]))
    inspected_candidates = [_inspect_drawing_template(sw, path) for path in candidates]
    eligible = [
        item for item in inspected_candidates
        if item.get("status") == "pass"
        and item.get("paper_size") == requested
        and (str(standard).upper() != "GB_T" or item.get("gbt_candidate"))
    ]
    if not eligible:
        format_selection = select_drawing_template(
            template_candidates,
            paper_size=requested,
            require_gbt=str(standard).upper() == "GB_T",
        )
        base_template = default_file or next(
            (
                Path(item["path"])
                for item in inspected_candidates
                if item.get("status") == "pass"
            ),
            None,
        )
        if format_selection.get("selected") and base_template is not None:
            return {
                **format_selection,
                "status": "pass",
                "mode": "sheet_format",
                "requested_paper_size": requested,
                "paper_size": requested,
                "selected": str(base_template),
                "sheet_format_path": format_selection["selected"],
                "manual_review_required": True,
            }
        return {
            "status": "blocked",
            "mode": "paper_size",
            "requested_paper_size": requested,
            "paper_size": None,
            "selected": None,
            "candidates": inspected_candidates,
            "error_code": "DRAWING_STANDARD_TEMPLATE_MISSING",
            "manual_review_required": True,
        }
    paper_token = requested.casefold()
    explicit_keys = {str(path).casefold() for path in explicit_candidates}

    def rank(item):
        path = Path(item["path"])
        compact = re.sub(r"[^a-z0-9\u4e00-\u9fff]", "", path.stem.casefold())
        exact = compact in {f"gb{paper_token}", f"gbt{paper_token}", f"gb{paper_token}模板"}
        contains = paper_token in compact
        return (
            int(exact),
            int(item.get("gbt_candidate", False)),
            int(contains),
            int(str(path).casefold() in explicit_keys),
            item["path"].casefold(),
        )

    selected = max(eligible, key=rank)
    return {
        **selected,
        "mode": "paper_size",
        "requested_paper_size": requested,
        "selected": selected["path"],
        "candidates": inspected_candidates,
        "manual_review_required": False,
    }


def select_drawing_template(candidates, *, paper_size="A3", require_gbt=True) -> dict:
    """@brief 从本机候选中选择图幅匹配且具有 GB/T 标识的图框模板。

    仅把文件名和扩展名作为候选证据，不把命名匹配宣称为模板内容已合规。
    """
    paper_size = str(paper_size).upper()
    if paper_size not in PAPER_SIZES:
        raise ValueError(f"不支持的图幅: {paper_size}")
    inspected = []
    for raw_path in _as_sequence(candidates):
        path = Path(raw_path).expanduser().resolve()
        name = path.stem.casefold()
        is_format = path.suffix.casefold() == ".slddrt"
        paper_match = bool(re.search(
            rf"(?:^|[^a-z0-9]){re.escape(paper_size.casefold())}(?:[^a-z0-9]|$)",
            name,
        ))
        gbt_match = _template_name_is_gbt(path)
        path_text = str(path).casefold()
        localized_candidate = any(token in path_text for token in ("chinese-simplified", "chinese_simplified", "简体中文"))
        score = int(path.is_file()) * 8 + int(is_format) * 4 + int(paper_match) * 2 + int(gbt_match) + int(localized_candidate) * 2
        inspected.append({
            "path": str(path),
            "exists": path.is_file(),
            "is_sheet_format": is_format,
            "paper_match": paper_match,
            "gbt_candidate": gbt_match,
            "localized_candidate": localized_candidate,
            "score": score,
        })
    eligible = [item for item in inspected if item["exists"] and item["is_sheet_format"] and item["paper_match"]]
    if require_gbt:
        eligible = [item for item in eligible if item["gbt_candidate"]]
    selected = max(eligible, key=lambda item: (item["score"], item["path"].casefold()), default=None)
    return {
        "status": "pass" if selected else "blocked",
        "paper_size": paper_size,
        "selected": selected["path"] if selected else None,
        "candidates": inspected,
        "gbt_content_verified": False,
        "manual_review_required": True,
        "error_code": None if selected else "DRAWING_GBT_TEMPLATE_MISSING" if require_gbt else "DRAWING_TEMPLATE_MISSING",
    }


def plan_standard_view_layout(
    model_size_m,
    *,
    paper_size="A3",
    projection="third_angle",
    requested_scale=None,
    margin_m=0.012,
    gap_m=0.018,
    title_block_width_m=0.180,
    title_block_height_m=0.055,
    sheet_size_m=None,
    include_isometric=False,
) -> dict:
    """@brief 为标准三视图和可选等轴测视图规划互不侵入的布局。"""
    paper_size = str(paper_size).upper()
    projection = str(projection).lower()
    if projection not in {"first_angle", "third_angle"}:
        raise ValueError("projection 必须是 first_angle 或 third_angle")
    spec = PAPER_SIZES.get(paper_size)
    if spec is None:
        raise ValueError(f"不支持的图幅: {paper_size}")
    try:
        width, height, depth = (float(item) for item in model_size_m)
    except (TypeError, ValueError) as exc:
        raise ValueError("model_size_m 必须包含三个米制外形尺寸") from exc
    if min(width, height, depth) <= 0 or not all(math.isfinite(item) for item in (width, height, depth)):
        raise ValueError("模型外形尺寸必须为有限正数")

    sheet_width = spec["width_m"]
    sheet_height = spec["height_m"]
    if sheet_size_m is not None:
        try:
            sheet_width, sheet_height = map(float, sheet_size_m)
        except (TypeError, ValueError) as exc:
            raise ValueError("sheet_size_m must contain width and height in metres") from exc
        if not all(math.isfinite(value) and value > 0 for value in (sheet_width, sheet_height)):
            raise ValueError("sheet_size_m must contain finite positive dimensions")
    working_left = margin_m
    working_bottom = margin_m + title_block_height_m + gap_m
    working_right = sheet_width - margin_m
    working_top = sheet_height - margin_m
    available_width = working_right - working_left
    available_height = working_top - working_bottom
    isometric = bool(include_isometric)
    iso_estimate_width = (width + depth) * 0.90 if isometric else 0.0
    iso_estimate_height = (height + min(width, depth) * 0.5) if isometric else 0.0
    standard_width = width + depth
    standard_height = height + depth
    scale_width = standard_width + iso_estimate_width + (2.0 * gap_m if isometric else gap_m)
    scale_height = max(standard_height + gap_m, iso_estimate_height + gap_m if isometric else 0.0)
    raw_scale = min(
        (available_width - gap_m) / scale_width,
        (available_height - gap_m) / scale_height,
    )
    if raw_scale <= 0:
        return {
            "status": "blocked",
            "paper_size": paper_size,
            "sheet": {"width_m": sheet_width, "height_m": sheet_height},
            "views": [],
            "manual_review_required": True,
            "retryable": True,
            "error_code": "DRAWING_LAYOUT_WORKING_AREA_INVALID",
        }
    if requested_scale is None:
        scale = next((item for item in STANDARD_DRAWING_SCALES if item <= raw_scale + 1e-12), raw_scale)
    else:
        try:
            if isinstance(requested_scale, str):
                numerator_text, denominator_text = requested_scale.split(":", 1)
                scale = float(numerator_text.strip()) / float(denominator_text.strip())
            else:
                scale = float(requested_scale)
        except (TypeError, ValueError, ZeroDivisionError):
            return {
                "status": "blocked",
                "paper_size": paper_size,
                "views": [],
                "manual_review_required": True,
                "retryable": False,
                "error_code": "DRAWING_SCALE_INVALID",
            }
        if scale <= 0 or not math.isfinite(scale):
            return {
                "status": "blocked",
                "paper_size": paper_size,
                "views": [],
                "manual_review_required": True,
                "retryable": False,
                "error_code": "DRAWING_SCALE_INVALID",
            }
        if scale > raw_scale + 1e-12:
            return {
                "status": "blocked",
                "paper_size": paper_size,
                "requested_scale": requested_scale,
                "maximum_fit_scale": raw_scale,
                "views": [],
                "manual_review_required": True,
                "retryable": True,
                "error_code": "DRAWING_SCALE_DOES_NOT_FIT",
            }

    front_w, front_h = width * scale, height * scale
    top_w, top_h = width * scale, depth * scale
    right_w, right_h = depth * scale, height * scale
    layout_w = front_w + gap_m + right_w
    layout_h = front_h + gap_m + top_h
    iso_w = iso_estimate_width * scale
    iso_h = iso_estimate_height * scale
    standard_available_width = available_width - (iso_w + gap_m if isometric else 0.0)
    origin_x = working_left + max(0.0, (standard_available_width - layout_w) / 2.0)
    origin_y = working_bottom + max(0.0, (available_height - layout_h) / 2.0)

    def view_record(name, left, bottom, view_width, view_height):
        """@brief 创建单个视图的中心点与边界框记录。"""
        return {
            "name": name,
            "center": [left + view_width / 2.0, bottom + view_height / 2.0],
            "box": {"left": left, "bottom": bottom, "right": left + view_width, "top": bottom + view_height},
        }

    if projection == "first_angle":
        # GB/T 第一角投影：俯视在主视下方，右视在主视左侧。
        views = [
            view_record("*Front", origin_x + right_w + gap_m, origin_y + top_h + gap_m, front_w, front_h),
            view_record("*Top", origin_x + right_w + gap_m, origin_y, top_w, top_h),
            view_record("*Right", origin_x, origin_y + top_h + gap_m, right_w, right_h),
        ]
    else:
        views = [
            view_record("*Front", origin_x, origin_y, front_w, front_h),
            view_record("*Top", origin_x, origin_y + front_h + gap_m, top_w, top_h),
            view_record("*Right", origin_x + front_w + gap_m, origin_y, right_w, right_h),
        ]
    if isometric:
        iso_left = working_right - iso_w
        iso_bottom = working_top - iso_h
        iso_record = view_record("*Isometric", iso_left, iso_bottom, iso_w, iso_h)
        iso_record["kind"] = "isometric"
        views.append(iso_record)
        for standard_view in views[:-1]:
            standard_view["kind"] = "standard"
    collision_pairs = []
    for index, first in enumerate(views):
        first_box = first["box"]
        for second in views[index + 1:]:
            second_box = second["box"]
            if (
                min(first_box["right"], second_box["right"]) > max(first_box["left"], second_box["left"])
                and min(first_box["top"], second_box["top"]) > max(first_box["bottom"], second_box["bottom"])
            ):
                collision_pairs.append([first["name"], second["name"]])
    if collision_pairs:
        return {
            "status": "blocked",
            "paper_size": paper_size,
            "sheet": {"width_m": sheet_width, "height_m": sheet_height},
            "views": views,
            "collision_pairs": collision_pairs,
            "manual_review_required": True,
            "retryable": True,
            "error_code": "DRAWING_VIEW_LAYOUT_OVERLAP",
        }
    title_box = {
        "left": sheet_width - margin_m - title_block_width_m,
        "bottom": margin_m,
        "right": sheet_width - margin_m,
        "top": margin_m + title_block_height_m,
    }
    return {
        "status": "pass",
        "paper_size": paper_size,
        "projection": projection,
        "gap_m": gap_m,
        "sheet": {"width_m": sheet_width, "height_m": sheet_height},
        "working_area": {"left": working_left, "bottom": working_bottom, "right": working_right, "top": working_top},
        "title_block_box": title_box,
        "scale": scale,
        "scale_ratio": list(_scale_ratio(scale)),
        "views": views,
        "include_isometric": isometric,
        "view_collision_free": True,
        "manual_review_required": True,
    }


def _scale_ratio(scale):
    """@brief 将浮点比例转换为 SolidWorks 可接受的整数比。"""
    ratio = Fraction(float(scale)).limit_denominator(1000)
    return ratio.numerator, ratio.denominator


def _apply_view_layout(view, item, numerator, denominator) -> dict:
    """@brief 将已创建视图移动到规划中心并设置独立比例。"""
    center = [float(item["center"][0]), float(item["center"][1])]
    if hasattr(view, "UseParentScale"):
        view.UseParentScale = False
    if hasattr(view, "UseSheetScale"):
        view.UseSheetScale = 0  # swView 使用独立比例，避免首次保存时模板自动比例改变视图。
    if hasattr(view, "PositionLocked"):
        view.PositionLocked = False
    view.ScaleRatio = (int(numerator), int(denominator))
    actual_scale = _as_sequence(_safe_member(view, "ScaleRatio", default=[]))
    if actual_scale != [int(numerator), int(denominator)]:
        view.ScaleRatio = VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(numerator), float(denominator)])
        actual_scale = _as_sequence(_safe_member(view, "ScaleRatio", default=[]))
    if len(actual_scale) != 2 or abs(actual_scale[0] / actual_scale[1] - numerator / denominator) > 1e-8:
        raise RuntimeError("标准视图实际比例与计划不一致")
    position = VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, center)
    method = getattr(view, "SetViewPosition", None)
    if method is not None:
        moved = bool(get_com_member(view, "SetViewPosition", position, False))
        if not moved:
            raise RuntimeError(f"SetViewPosition 返回失败: {center}")
    else:
        view.Position = position
    actual_position = _view_position(view)
    position_verified = bool(
        actual_position
        and abs(actual_position[0] - center[0]) <= 1e-5
        and abs(actual_position[1] - center[1]) <= 1e-5
    )
    if not position_verified:
        raise RuntimeError(f"视图位置回读不一致: requested={center}, actual={actual_position}")
    return {
        "name": item["name"],
        "actual_name": str(_safe_member(view, "Name", default="")),
        "orientation": str(_safe_member(view, "GetOrientationName", default="")),
        "center": center,
        "actual_center": list(actual_position),
        "position_verified": True,
        "scale_ratio": [int(numerator), int(denominator)],
    }


def _normalise_orientation(value):
    """@brief 将 SolidWorks 视图方向统一为 front/top/right/isometric 键。"""
    compact = re.sub(r"[^a-z\u4e00-\u9fff]", "", str(value or "").casefold())
    aliases = {
        "front": "front",
        "top": "top",
        "right": "right",
        "isometric": "isometric",
        "isometricview": "isometric",
        "等轴测": "isometric",
        "轴测": "isometric",
        "frontview": "front",
        "topview": "top",
        "rightview": "right",
        "前视": "front",
        "主视": "front",
        "上视": "top",
        "俯视": "top",
        "右视": "right",
    }
    return aliases.get(compact)


def _view_position(view):
    """@brief 读取工程图视图中心位置。"""
    values = _as_sequence(_safe_member(view, "Position", default=[]))
    try:
        if len(values) < 2:
            return None
        return float(values[0]), float(values[1])
    except (IndexError, TypeError, ValueError):
        return None


def _set_view_center(view, center) -> list[float]:
    """@brief 移动视图并回读中心点，供真实包围盒二次排布复用。"""
    target = [float(center[0]), float(center[1])]
    position = VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, target)
    method = getattr(view, "SetViewPosition", None)
    if method is not None:
        moved = bool(get_com_member(view, "SetViewPosition", position, False))
        if not moved:
            raise RuntimeError(f"SetViewPosition 返回失败: {target}")
    else:
        view.Position = position
    actual = _view_position(view)
    if actual is None or abs(actual[0] - target[0]) > 1e-5 or abs(actual[1] - target[1]) > 1e-5:
        raise RuntimeError(f"视图位置回读不一致: requested={target}, actual={actual}")
    return [float(actual[0]), float(actual[1])]


def _refine_standard_view_spacing(view_objects, view_records, projection, gap_m=0.018) -> dict:
    """@brief 根据 SolidWorks 实际视图边界消除三视图之间的确认重叠。"""
    required = {"front", "top", "right"}
    if set(view_objects) < required:
        return {"status": "review_required", "method": "native_outline", "adjustments": [], "error_code": "DRAWING_VIEW_OUTLINES_INCOMPLETE"}
    boxes = {key: _normalise_box(_safe_member(view, "GetOutline")) for key, view in view_objects.items()}
    if any(box is None for box in boxes.values()):
        return {"status": "review_required", "method": "native_outline", "adjustments": [], "error_code": "DRAWING_VIEW_OUTLINES_INCOMPLETE"}
    try:
        gap = max(0.001, float(gap_m))
    except (TypeError, ValueError):
        gap = 0.018
    records = {item["name"]: item for item in view_records}
    names = {"front": "*Front", "top": "*Top", "right": "*Right"}
    adjustments = []

    def move_if_needed(axis, orientation, target_value):
        current_box = boxes[orientation]
        current_center = _view_position(view_objects[orientation])
        if current_center is None:
            return
        delta = float(target_value) - current_center[axis]
        if abs(delta) <= 1e-7:
            return
        new_center = list(current_center)
        new_center[axis] = float(target_value)
        actual_center = _set_view_center(view_objects[orientation], new_center)
        moved_box = _normalise_box(_safe_member(view_objects[orientation], "GetOutline"))
        boxes[orientation] = moved_box or current_box
        record = records.get(names[orientation])
        if record is not None:
            record["center"] = list(actual_center)
            record["actual_center"] = list(actual_center)
            record["layout_refined_from_native_outline"] = True
        adjustments.append({"view": names[orientation], "axis": "x" if axis == 0 else "y", "delta_m": delta, "center": list(actual_center)})

    front = boxes["front"]
    right = boxes["right"]
    top = boxes["top"]
    right_width = right["right"] - right["left"]
    top_height = top["top"] - top["bottom"]
    if projection == "first_angle":
        right_target_x = front["left"] - gap - right_width / 2.0
        top_target_y = front["bottom"] - gap - top_height / 2.0
    else:
        right_target_x = front["right"] + gap + right_width / 2.0
        top_target_y = front["top"] + gap + top_height / 2.0
    move_if_needed(0, "right", right_target_x)
    move_if_needed(1, "top", top_target_y)
    return {
        "status": "pass",
        "method": "native_outline",
        "projection": projection,
        "gap_m": gap,
        "adjustments": adjustments,
        "error_code": None,
        "manual_review_required": True,
    }


def _collect_drawing_views(drawing_model):
    """@brief 同时尝试 Sheet.GetViews 与 GetFirstView 链读取真实模型视图。"""
    sheet = _safe_member(drawing_model, "GetCurrentSheet")
    views = _as_sequence(_safe_member(sheet, "GetViews", default=[]))
    if len(views) >= 3:
        return views
    traversed = []
    sheet_view = _safe_member(drawing_model, "GetFirstView")
    current = _safe_member(sheet_view, "GetNextView")
    guard = 0
    while current is not None and guard < 1000:
        traversed.append(current)
        current = _safe_member(current, "GetNextView")
        guard += 1
    return traversed if len(traversed) >= len(views) else views


def _model_view_name_candidates(drawing_model, part_path, requested_name, sw_app=None):
    """Resolve API standard-view aliases against the installed UI language.

    SolidWorks returns localized model-view names (for example ``*等轴测``)
    and CreateDrawViewFromModelView3 requires the installed-language string.
    """
    requested = str(requested_name or "").strip()
    requested_semantic = _normalise_orientation(requested)
    app = sw_app or _safe_member(drawing_model, "GetApp")
    source_model = _safe_member(app, "GetOpenDocumentByName", str(part_path), default=None)
    if source_model is None:
        documents = _as_sequence(_safe_member(app, "GetDocuments", default=[]))
        source_model = next(
            (
                document for document in documents
                if str(_safe_member(document, "GetPathName", default="") or "").casefold()
                == str(part_path).casefold()
            ),
            None,
        )
    names = [
        str(item)
        for item in _as_sequence(_safe_member(source_model, "GetModelViewNames", default=[]))
    ]
    if requested in names:
        return [requested, *[name for name in names if name != requested]]
    if requested_semantic:
        match = next(
            (name for name in names if _normalise_orientation(name) == requested_semantic),
            None,
        )
        if match:
            return [match, *[name for name in names if name != match]]
    localized = {
        "front": "*前视",
        "top": "*上视",
        "right": "*右视",
        "isometric": "*等轴测",
    }
    semantic_local = localized.get(requested_semantic)
    return list(dict.fromkeys(
        item for item in (requested, semantic_local, *names) if item
    ))


def _resolve_model_view_name(drawing_model, part_path, requested_name, sw_app=None):
    """Return the preferred localized model-view name."""
    return _model_view_name_candidates(
        drawing_model,
        part_path,
        requested_name,
        sw_app=sw_app,
    )[0]


def _map_native_standard_views(views):
    """@brief 依据方向名及与主视图的轴对齐关系识别第一角/第三角三视图。"""
    by_orientation = {}
    diagnostics = []
    for view in views:
        orientation_name = str(_safe_member(view, "GetOrientationName", default=""))
        orientation = _normalise_orientation(orientation_name)
        base_view = _safe_member(view, "GetBaseView")
        position = _view_position(view)
        diagnostics.append({
            "name": str(_safe_member(view, "Name", default="")),
            "orientation": orientation_name,
            "position": list(position) if position else None,
            "has_base_view": base_view is not None,
            "referenced_model": str(_safe_member(view, "GetReferencedModelName", default="")),
        })
        if orientation and orientation not in by_orientation:
            by_orientation[orientation] = view
    if set(by_orientation) >= {"front", "top", "right"}:
        return by_orientation, diagnostics, "orientation_name"

    positioned = [(view, _view_position(view), _safe_member(view, "GetBaseView")) for view in views]
    positioned = [item for item in positioned if item[1] is not None]
    if len(positioned) >= 3:
        base_candidates = [item for item in positioned if item[2] is None]
        known_front = by_orientation.get("front")
        front = next((item for item in positioned if item[0] is known_front), None)
        front = front or min(base_candidates or positioned, key=lambda item: item[1][0] + item[1][1])
        remaining = [item for item in positioned if item[0] is not front[0]]
        # 第一角俯视图在下、右视图在左；不能以最大 y/x 判定方向。
        tops = [item for item in remaining if abs(item[1][0] - front[1][0]) <= 1e-5 and abs(item[1][1] - front[1][1]) > 1e-5]
        rights = [item for item in remaining if abs(item[1][1] - front[1][1]) <= 1e-5 and abs(item[1][0] - front[1][0]) > 1e-5]
        if len(tops) == len(rights) == 1:
            top, right = tops[0], rights[0]
            return {"front": front[0], "top": top[0], "right": right[0]}, diagnostics, "base_and_position"
    return by_orientation, diagnostics, "unresolved"


def _map_standard_views_from_sheet_views(sheet_views):
    """@brief 从整张图纸视图中筛出并映射前、俯、右三个标准视图。"""
    oriented_fronts = [
        view for view in sheet_views
        if _normalise_orientation(_safe_member(view, "GetOrientationName", default="")) == "front"
    ]
    base_candidates = oriented_fronts or [
        view for view in sheet_views
        if _safe_member(view, "Type", default=None) == 7 and _safe_member(view, "GetBaseView") is None
    ]
    standard_candidates = [*base_candidates, *[
        view for view in sheet_views
        if _safe_member(view, "Type", default=None) == 4
        or _normalise_orientation(_safe_member(view, "GetOrientationName", default="")) == "isometric"
    ]]
    return _map_native_standard_views(standard_candidates)


def create_adaptive_standard_views(drawing_model, part_path, layout, *, sw_app=None) -> dict:
    """@brief 按预先计算的布局创建前、俯、右三个真实工程图视图。"""
    created = []
    view_objects = {}
    numerator, denominator = layout.get("scale_ratio") or _scale_ratio(layout["scale"])
    for item in layout.get("views", []):
        center = item["center"]
        native_view_name = _resolve_model_view_name(
            drawing_model,
            part_path,
            item["name"],
            sw_app=sw_app,
        )
        view = drawing_model.CreateDrawViewFromModelView3(part_path, native_view_name, center[0], center[1], 0)
        if view is None:
            if not created:
                projection = str(layout.get("projection", "third_angle")).lower()
                # 部分 SolidWorks 版本（包括当前 SW2026 COM 代理）没有
                # CreateFirstAngleViews2。先用可用的原生三视图 API 建立视图，
                # 再按 DrawingSpec 的第一角/第三角布局重新定位并回读位置。
                method_candidates = (
                    ("CreateFirstAngleViews2", "Create3rdAngleViews2")
                    if projection == "first_angle"
                    else ("Create3rdAngleViews2",)
                )
                native_created = False
                method_name = None
                for candidate in method_candidates:
                    if bool(_safe_member(drawing_model, candidate, str(part_path), default=False)):
                        native_created = True
                        method_name = candidate
                        break
                if native_created:
                    _safe_member(drawing_model, "ForceRebuild3", False)
                    _safe_member(drawing_model, "GraphicsRedraw2")
                    native_views = _collect_drawing_views(drawing_model)
                    by_orientation, diagnostics, mapping_method = _map_native_standard_views(native_views)
                    expected = {"front": "*Front", "top": "*Top", "right": "*Right"}
                    if set(by_orientation) >= set(expected):
                        layout_by_name = {entry["name"]: entry for entry in layout.get("views", [])}
                        try:
                            for orientation in ("front", "top", "right"):
                                view_objects[orientation] = by_orientation[orientation]
                                created.append(
                                    _apply_view_layout(
                                        by_orientation[orientation],
                                        layout_by_name[expected[orientation]],
                                        numerator,
                                        denominator,
                                    )
                                )
                            if "*Isometric" in layout_by_name:
                                isometric_item = layout_by_name["*Isometric"]
                                isometric_center = isometric_item["center"]
                                native_isometric_name = _resolve_model_view_name(
                                    drawing_model,
                                    str(part_path),
                                    "*Isometric",
                                    sw_app=sw_app,
                                )
                                isometric_view = drawing_model.CreateDrawViewFromModelView3(
                                    str(part_path),
                                    native_isometric_name,
                                    isometric_center[0],
                                    isometric_center[1],
                                    0,
                                )
                                if isometric_view is None:
                                    raise RuntimeError("原生三视图已建立，但等轴测视图创建失败")
                                view_objects["isometric"] = isometric_view
                                created.append(
                                    _apply_view_layout(
                                        isometric_view,
                                        isometric_item,
                                        numerator,
                                        denominator,
                                    )
                                )
                        except Exception as exc:
                            return {
                                "status": "failed",
                                "stage": "layout",
                                "backend": f"native_{projection}",
                                "views": created,
                                "native_view_diagnostics": diagnostics,
                                "retryable": True,
                                "error_code": "DRAWING_VIEW_POSITION_FAILED",
                                "error": str(exc),
                            }
                        refinement = _refine_standard_view_spacing(
                            view_objects,
                            created,
                            projection,
                            layout.get("gap_m", 0.018),
                        )
                        backend = (
                            "native_3rd_angle"
                            if projection == "third_angle"
                            else "native_first_angle"
                            if method_name == "CreateFirstAngleViews2"
                            else "native_first_angle_via_3rd_angle"
                        )
                        return {
                            "status": "pass",
                            "stage": "create",
                            "backend": backend,
                            "creation_method": method_name,
                            "mapping_method": mapping_method,
                            "native_view_diagnostics": diagnostics,
                            "layout_refinement": refinement,
                            "views": created,
                            "view_count": len(created),
                            "retryable": False,
                            "error_code": None,
                            "manual_review_required": True,
                        }
                    return {
                        "status": "failed",
                        "stage": "map",
                        "backend": f"native_{projection}",
                        "views": [],
                        "orientations_found": sorted(by_orientation),
                        "mapping_method": mapping_method,
                        "native_view_diagnostics": diagnostics,
                        "retryable": True,
                        "error_code": "DRAWING_VIEW_ORIENTATION_MAP_FAILED",
                    }
            return {
                "status": "failed",
                "stage": "create",
                "views": created,
                "retryable": True,
                "error_code": "DRAWING_VIEW_CREATE_FAILED",
            }
        try:
            orientation = _normalise_orientation(item["name"])
            if orientation:
                view_objects[orientation] = view
            created.append(_apply_view_layout(view, item, numerator, denominator))
        except Exception as exc:
            return {
                "status": "failed",
                "stage": "layout",
                "backend": "individual_model_views",
                "views": created,
                "retryable": True,
                "error_code": "DRAWING_VIEW_POSITION_FAILED",
                "error": str(exc),
            }
    refinement = _refine_standard_view_spacing(
        view_objects,
        created,
        str(layout.get("projection", "third_angle")).lower(),
        layout.get("gap_m", 0.018),
    )
    return {
        "status": "pass",
        "stage": "create",
        "backend": "individual_model_views",
        "views": created,
        "layout_refinement": refinement,
        "view_count": len(created),
        "retryable": False,
        "error_code": None,
        "manual_review_required": True,
    }


def create_standard_views(drawing_model, part_path):
    """
    创建标准三视图（第三角投影法）

    参数:
        drawing_model: IDrawingDoc
        part_path: 零件文件路径
    """
    return drawing_model.Create3rdAngleViews2(part_path)


def create_standard_views_with_projection(drawing_model, part_path, projection="first_angle"):
    """@brief 按指定投影法创建原生三视图并返回明确失败状态。"""
    projection = str(projection).lower()
    if projection not in {"first_angle", "third_angle"}:
        raise ValueError("projection 必须是 first_angle 或 third_angle")
    method_name = "CreateFirstAngleViews2" if projection == "first_angle" else "Create3rdAngleViews2"
    method = getattr(drawing_model, method_name, None)
    if method is None:
        return {
            "status": "blocked",
            "projection": projection,
            "method": method_name,
            "error_code": "DRAWING_PROJECTION_API_UNAVAILABLE",
            "manual_review_required": True,
        }
    created = bool(method(part_path))
    return {
        "status": "pass" if created else "failed",
        "projection": projection,
        "method": method_name,
        "created": created,
        "error_code": None if created else "DRAWING_STANDARD_VIEWS_CREATE_FAILED",
        "manual_review_required": True,
    }


def add_view(drawing_model, part_path, view_name, x, y, scale=None):
    """
    添加单个视图

    参数:
        view_name: 视图方向名称
            "*Front", "*Back", "*Top", "*Bottom",
            "*Left", "*Right", "*Isometric",
            "*Trimetric", "*Dimetric"
        x, y: 视图放置位置（米）
        scale: 视图比例（如 0.5 表示 1:2），None 使用图纸默认
    """
    view = None
    for native_view_name in _model_view_name_candidates(
        drawing_model,
        part_path,
        view_name,
    ):
        view = drawing_model.CreateDrawViewFromModelView3(
            part_path, native_view_name, x, y, 0
        )
        if view is not None:
            break
    if view and scale:
        view.ScaleRatio = (1.0, 1.0 / scale)
    return view


def add_section_view(drawing_model, x, y):
    """在当前选择的剖切线位置创建剖视图"""
    return drawing_model.CreateSectionViewAt5(
        x,
        y,
        0,
        "",
        0,
        create_empty_dispatch_variant(),
        0,
    )


def add_detail_view(drawing_model, x, y, scale=2.0):
    """@brief 从当前选择的局部圆创建局部放大视图。

    SW2025 IDrawingDoc::CreateDetailViewAt4 要求 12 个参数。Scale1/Scale2
    是比例的分子/分母；本函数把公开的 ``scale`` 因子转换为 ``scale:1``。
    """
    return drawing_model.CreateDetailViewAt4(
        x,
        y,
        0,
        4,
        float(scale),
        1.0,
        "",
        1,
        True,
        False,
        False,
        1,
    )


def insert_dimensions(drawing_model, view=None):
    """
    自动标注尺寸（模型项目）

    参数:
        view: 目标视图对象，None 则标注所有视图
    """
    # SolidWorks 2024 新增 InsertModelAnnotations4，返回实际插入的 IAnnotation
    # 数组；旧版/动态代理仍可能只有 InsertModelAnnotations3。优先使用 4，
    # 再回退到 3，避免把“方法返回 True”误当成已经插入尺寸。
    # SW2024 swInsertAnnotation_e：32768=标记为工程图的模型尺寸。
    # 8 是通用尺寸类型、524288 是未标记尺寸；本机 SW2024 对二者组合静默
    # 返回 None，而 32768 会返回真实 IAnnotation 数组。
    args4 = (
        0,          # swImportModelItemsFromEntireModel
        32768,      # swInsertDimensionsMarkedForDrawing
        True, False, False, False,
        False, False,
    )
    args3 = args4[:6]
    # 官方 API 示例要求先激活一个工程图视图；未激活时 SW2024 会静默返回空结果。
    try:
        sheet = _safe_member(drawing_model, "GetCurrentSheet")
        views = _as_sequence(_safe_member(sheet, "GetViews", default=[]))
        if views:
            # 三视图第一个通常是前视图；通过对象 Name 读取失败时使用已知顺序，
            # 但仍要求 SelectByID2/ActivateView 真正返回成功。
            first_view = views[0]
            name = _safe_member(first_view, "Name", default="")
            if name:
                extension = getattr(drawing_model, "Extension", None)
                if extension is not None:
                    get_com_member(
                        extension, "SelectByID2",
                        name, "DRAWINGVIEW", 0, 0, 0, False, 0,
                        create_empty_dispatch_variant(), 0,
                    )
                get_com_member(drawing_model, "ActivateView", name)
    except Exception:
        # 激活失败仍继续尝试，让结构复核决定是否有真实尺寸证据。
        pass
    owners = (drawing_model, getattr(drawing_model, "Extension", None))
    for owner in owners:
        if owner is None:
            continue
        try:
            method4 = getattr(owner, "InsertModelAnnotations4", None)
            if method4 is not None:
                inserted = get_com_member(owner, "InsertModelAnnotations4", *args4)
                if inserted is not None:
                    return inserted
            method3 = getattr(owner, "InsertModelAnnotations3", None)
            if method3 is not None:
                return get_com_member(owner, "InsertModelAnnotations3", *args3)
        except (AttributeError, TypeError, pythoncom.com_error):
            continue
    # 新建三视图后 SW2024 有时尚未建立可导入的视图缓存；强制重建后仅重试
    # 一次。使用“标记为工程图”与消重语义，不会靠重复调用制造重复尺寸。
    try:
        get_com_member(drawing_model, "ForceRebuild3", False)
        get_com_member(drawing_model, "GraphicsRedraw2")
        for owner in owners:
            if owner is not None and getattr(owner, "InsertModelAnnotations4", None) is not None:
                inserted = get_com_member(owner, "InsertModelAnnotations4", *args4)
                if inserted is not None:
                    return inserted
    except (AttributeError, TypeError, pythoncom.com_error):
        pass
    # 调用方可以继续做结构复核，但必须把缺少真实尺寸证据显示为 warning。
    return False


def _note_text(note):
    """@brief 读取 INote 的实际文字，兼容动态 COM 未公开成员名称的情况。"""
    text = _safe_member(note, "GetText")
    if isinstance(text, str):
        return text
    ole_object = getattr(note, "_oleobj_", None)
    if ole_object is None:
        return ""
    try:
        # SW2026 sldworks.tlb: INote.GetText 的 DISPID 为 2，返回 BSTR。
        return str(ole_object.InvokeTypes(2, 0, 1, (8, 0), ()) or "")
    except Exception:
        return ""


def _note_annotation(note):
    """@brief 获取 INote 对应的 IAnnotation；动态 COM 不公开该成员时按类型库调用。"""
    annotation = _safe_member(note, "GetAnnotation")
    if annotation is not None:
        return annotation
    ole_object = getattr(note, "_oleobj_", None)
    if ole_object is None:
        return None
    try:
        # SW2026 sldworks.tlb: INote.GetAnnotation 的 DISPID 为 85。
        from win32com.client.dynamic import Dispatch

        return Dispatch(ole_object.InvokeTypes(85, 0, 1, (9, 0), ()))
    except Exception:
        return None


def _set_annotation_position(annotation, x, y, z=0.0):
    """@brief 设置 IAnnotation 的图纸坐标，返回 SolidWorks 的布尔结果。"""
    try:
        result = get_com_member(annotation, "SetPosition2", x, y, z)
        if isinstance(result, bool):
            return result
    except Exception:
        pass
    ole_object = getattr(annotation, "_oleobj_", None)
    if ole_object is None:
        return False
    try:
        # SW2026 sldworks.tlb: IAnnotation.SetPosition2 的 DISPID 为 91。
        return bool(ole_object.InvokeTypes(91, 0, 1, (11, 0), ((5, 1), (5, 1), (5, 1)), x, y, z))
    except Exception:
        return False


def _annotation_position(annotation):
    """@brief 回读 IAnnotation 图纸坐标，坐标不可用时返回 None。"""
    position = _safe_member(annotation, "GetPosition")
    values = _as_sequence(position)
    try:
        x, y = float(values[0]), float(values[1])
    except (IndexError, TypeError, ValueError):
        return None
    if not math.isfinite(x) or not math.isfinite(y):
        return None
    return [x, y, float(values[2]) if len(values) > 2 else 0.0]


def _note_box(note, annotation):
    """@brief 优先读取 INote 的图纸空间范围；没有时退回通用注释边界。"""
    extent = _safe_member(note, "GetExtent")
    if extent is None:
        ole_object = getattr(note, "_oleobj_", None)
        if ole_object is not None:
            try:
                # SW2026 sldworks.tlb: INote.GetExtent 的 DISPID 为 22。
                extent = ole_object.InvokeTypes(22, 0, 1, (12, 0), ())
            except Exception:
                extent = None
    return _normalise_box(extent) or _annotation_box(annotation)


def _note_evidence(note):
    """@brief 收集注释的文字、位置和边界，作为工程图结构证据。"""
    annotation = _note_annotation(note)
    return {
        "text": _note_text(note),
        "property_linked_text": str(_safe_member(note, "PropertyLinkedText", default="") or ""),
        "persistent_name": str(_safe_member(annotation, "GetName", default="") or ""),
        "position_m": _annotation_position(annotation),
        "box": _note_box(note, annotation),
    }


def _normalise_property_expression(value):
    """Normalise quoted and brace forms of ``$PRP`` expressions."""
    text = str(value or "")

    def replace(match):
        token = re.sub(r"\s+", " ", match.group(2)).strip()
        return f"{match.group(1).upper()}:{token.casefold()}"

    return re.sub(
        r"(\$PRP(?:SHEET)?)\s*:\s*[\{\"]\s*([^\}\"]+?)\s*[\}\"]",
        replace,
        text,
        flags=re.IGNORECASE,
    )


def _normalised_title_token(value):
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]", "", str(value or "").casefold())


def _title_field_from_expression(expression, persistent_name=""):
    """Map a native property-linked note to one semantic title-block field."""
    name = str(persistent_name or "")
    if name.startswith("CAD_TITLE__"):
        field = name.removeprefix("CAD_TITLE__")
        return field if field in TITLE_BLOCK_FIELDS else None
    match = re.search(
        r"\$PRP(?:SHEET)?\s*:\s*[\{\"]?\s*([^\}\"]+?)\s*(?:[\}\"]|$)",
        str(expression or ""),
        re.IGNORECASE,
    )
    if not match:
        return None
    token = _normalised_title_token(match.group(1))
    for field, aliases in TITLE_FIELD_PROPERTY_ALIASES.items():
        if any(token == _normalised_title_token(alias) for alias in aliases):
            return field
    return None


def _iter_drawing_notes(drawing_model):
    """Yield all drawing notes through the native view chain."""
    view = _safe_member(drawing_model, "GetFirstView", default=None)
    visited = 0
    while view is not None and visited < 4096:
        owner_view = str(_safe_member(view, "Name", default="") or "")
        owner_type = _safe_member(view, "Type", default=None)
        for note in _as_sequence(_safe_member(view, "GetNotes", default=[])):
            yield note, owner_view, owner_type
        view = _safe_member(view, "GetNextView", default=None)
        visited += 1


def collect_existing_title_block_fields(drawing_model, *, title_block_box=None):
    """Return semantic title-block fields already supplied by the sheet format."""
    title_box = _normalise_box(title_block_box) if title_block_box is not None else None
    fields = {field: [] for field in TITLE_BLOCK_FIELDS}
    for note, owner_view, owner_type in _iter_drawing_notes(drawing_model):
        evidence = _note_evidence(note)
        field = _title_field_from_expression(
            evidence.get("property_linked_text"),
            evidence.get("persistent_name", ""),
        )
        if field:
            note_box = _normalise_box(evidence.get("box"))
            if title_box is not None and (
                note_box is None
                or min(note_box["right"], title_box["right"]) <= max(note_box["left"], title_box["left"])
                or min(note_box["top"], title_box["top"]) <= max(note_box["bottom"], title_box["bottom"])
            ):
                continue
            fields[field].append({
                **evidence,
                "owner_view": owner_view,
                "owner_view_type": owner_type,
                "field": field,
            })
    return {field: records for field, records in fields.items() if records}


def _bom_balloon_evidence(note):
    """@brief 只从 SolidWorks INote 的 BOM Balloon 原生状态提取气泡证据。"""
    if not bool(_safe_member(note, "IsBomBalloon", default=False)):
        return None
    upper_text = str(_safe_member(note, "GetBomBalloonText", True, default="") or "")
    evidence = _note_evidence(note)
    return {
        **evidence,
        "item_number": upper_text or str(evidence.get("text") or ""),
        "is_bom_balloon": True,
        "has_balloon": bool(_safe_member(note, "HasBalloon", default=False)),
        "balloon_style": _safe_member(note, "GetBalloonStyle", default=None),
        "balloon_size": _safe_member(note, "GetBalloonSize", default=None),
    }


def add_note(drawing_model, x, y, text, *, persistent_name=None, accepted_texts=None):
    """@brief 创建并验证工程图文字注释。

    @param drawing_model SolidWorks IModelDoc2 工程图对象。
    @param x 注释锚点 X 坐标（米）。
    @param y 注释锚点 Y 坐标（米）。
    @param text 需要写入图纸的非空文字。
    @return 包含 COM 回读文字、坐标和边界的可审计结果。
    """
    expected_text = str(text)
    if not expected_text.strip() or not all(math.isfinite(float(value)) for value in (x, y)):
        return {
            "text": expected_text,
            "created": False,
            "status": "failed",
            "error_code": "DRAWING_NOTE_INPUT_INVALID",
        }
    note = _safe_member(drawing_model, "InsertNote", expected_text)
    if note is None:
        return {
            "text": expected_text,
            "created": False,
            "status": "failed",
            "error_code": "DRAWING_NOTE_INSERT_FAILED",
        }
    annotation = _note_annotation(note)
    positioned = _set_annotation_position(annotation, float(x), float(y)) if annotation is not None else False
    assigned_name = None
    if positioned and annotation is not None and persistent_name:
        expected_name = str(persistent_name)
        named = bool(_safe_member(annotation, "SetName", expected_name, default=False))
        actual_name = str(_safe_member(annotation, "GetName", default="") or "")
        if named and actual_name == expected_name:
            assigned_name = actual_name
    if positioned:
        # 刷新文字与坐标；边界仍必须在视图重枚举后的结构审查阶段读取。
        _safe_member(drawing_model, "ForceRebuild3", False)
    evidence = _note_evidence(note)
    position = evidence.get("position_m") or []
    normalise_newlines = lambda value: str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    expected_texts = tuple(
        normalise_newlines(item)
        for item in (accepted_texts or (expected_text,))
    )
    actual_text = normalise_newlines(evidence.get("text"))
    linked_text = normalise_newlines(evidence.get("property_linked_text"))
    text_matches = actual_text in expected_texts or any(
        _normalise_property_expression(actual_text) == _normalise_property_expression(expected)
        or _normalise_property_expression(linked_text) == _normalise_property_expression(expected)
        for expected in expected_texts
    )
    position_matches = (
        len(position) >= 2
        and math.isclose(position[0], float(x), abs_tol=1e-6)
        and math.isclose(position[1], float(y), abs_tol=1e-6)
    )
    verified = bool(
        positioned
        and text_matches
        and position_matches
        and (not persistent_name or assigned_name == persistent_name)
    )
    return {
        "text": expected_text,
        "created": True,
        "position_requested_m": [float(x), float(y), 0.0],
        "positioned": positioned,
        "text_evidence": evidence.get("text"),
        "property_linked_text": evidence.get("property_linked_text"),
        "position_evidence_m": position,
        "persistent_id": assigned_name,
        "box": None,
        "box_source": "deferred_to_structure_inspection",
        "verified": verified,
        "status": "pass" if verified else "failed",
        "error_code": None if verified else "DRAWING_NOTE_COM_EVIDENCE_MISSING",
    }


def _title_property_aliases(title_block, field):
    """@brief Resolve the property alias list for one title-block field."""
    mapping = (title_block or {}).get("propertyMap") or {}
    requested = mapping.get(field)
    if isinstance(requested, str) and requested.strip():
        return (requested.strip(),)
    if isinstance(requested, (list, tuple)):
        aliases = tuple(str(item).strip() for item in requested if str(item).strip())
        if aliases:
            return aliases
    return TITLE_FIELD_PROPERTY_ALIASES[field]


def resolve_title_block_fields(source_model, title_block) -> tuple[dict, dict]:
    """Resolve title-block values from explicit fields or source custom properties.

    Property resolution prefers the requested configuration and then file-level
    properties. Missing engineering data is reported, never replaced with a
    fabricated placeholder.
    """
    from scripts.sw_document_data import read_custom_property

    normalized = dict(title_block or {})
    requested_configuration = str(normalized.get("configurationName") or "").strip()
    if not requested_configuration:
        try:
            requested_configuration = str(get_com_member(
                get_com_member(get_com_member(source_model, "ConfigurationManager"), "ActiveConfiguration"),
                "Name",
                default="",
            ) or "")
        except Exception:
            requested_configuration = ""
    scopes = tuple(dict.fromkeys(item for item in (requested_configuration, "") if item is not None))
    evidence = {"configuration": requested_configuration, "fields": {}}
    for field in TITLE_BLOCK_FIELDS:
        explicit = normalized.get(field)
        if explicit is not None and str(explicit).strip():
            normalized[field] = str(explicit).strip()
            evidence["fields"][field] = {
                "value": normalized[field],
                "source": "explicit",
                "property": None,
                "scope": None,
            }
            continue
        resolved = None
        for scope in scopes:
            for alias in _title_property_aliases(normalized, field):
                try:
                    record = read_custom_property(source_model, alias, configuration_name=scope)
                except Exception:
                    continue
                if record.get("exists"):
                    value = str(record.get("resolved") or record.get("raw") or "").strip()
                    if value:
                        resolved = {
                            "value": value,
                            "source": "custom_property",
                            "property": alias,
                            "scope": scope,
                        }
                        break
            if resolved:
                break
        if resolved:
            normalized[field] = resolved["value"]
        evidence["fields"][field] = resolved or {
            "value": None,
            "source": "missing",
            "property": None,
            "scope": None,
        }
    return normalized, evidence


def _title_field_cells(title_block, paper_size):
    configured = (title_block or {}).get("fieldPositionsMm") or {}
    defaults = DEFAULT_A3_GB_TITLE_FIELD_CELLS_MM if str(paper_size).upper() == "A3" else {}
    cells = {}
    for field in TITLE_BLOCK_FIELDS:
        value = configured.get(field) or defaults.get(field)
        if isinstance(value, (list, tuple)) and len(value) == 2:
            cells[field] = {
                "positionMm": [float(value[0]), float(value[1])],
                "maxWidthMm": 38.0,
                "maxLines": 1,
            }
        elif isinstance(value, dict):
            position = value.get("positionMm")
            if isinstance(position, (list, tuple)) and len(position) == 2:
                cells[field] = {
                    "positionMm": [float(position[0]), float(position[1])],
                    "maxWidthMm": float(value.get("maxWidthMm", 38.0)),
                    "maxLines": int(value.get("maxLines", 1)),
                }
    return cells


def _wrap_title_text(value, *, width_mm, height_mm, max_lines=None):
    """Wrap by a conservative character width while preserving explicit lines."""
    max_units = max(1, int(float(width_mm) / 2.0))
    visible_lines = max(1, int(float(height_mm) / 4.0))
    if max_lines is not None:
        visible_lines = min(visible_lines, max(1, int(max_lines)))
    result = []
    for source_line in str(value).splitlines() or [str(value)]:
        def units(text):
            return sum(2 if ord(character) > 0xFF else 1 for character in text)

        if " " in source_line.strip():
            line = ""
            for word in source_line.split():
                candidate = f"{line} {word}".strip()
                if line and units(candidate) > max_units:
                    result.append(line)
                    line = word
                else:
                    line = candidate
            if line:
                result.append(line)
        else:
            line = ""
            for character in source_line:
                candidate = line + character
                if line and units(candidate) > max_units:
                    result.append(line)
                    line = character
                else:
                    line = candidate
            if line:
                result.append(line)
    clipped = any(len(line.encode("gb18030")) / 2 > max_units for line in result) or len(result) > visible_lines
    return "\n".join(result[:visible_lines]), clipped


def add_title_block_fields(drawing_model, title_block, title_block_box, *, paper_size="A3") -> dict:
    """Verify or selectively write title-block values without duplicating template links."""
    request = dict(title_block or {})
    box = _normalise_box(title_block_box)
    if not request.get("required"):
        return {
            "status": "pass",
            "required": False,
            "fields": {},
            "existing_fields": {},
            "inserted_fields": [],
            "error_code": None,
        }
    existing_fields = collect_existing_title_block_fields(
        drawing_model,
        title_block_box=box,
    )
    manual_override = bool(
        request.get("overwriteExistingFields")
        or request.get("manualOverride")
    )
    requested_fields = [
        field for field in TITLE_BLOCK_FIELDS
        if field in request and str(request.get(field) or "").strip()
    ]
    if not requested_fields:
        return {
            "status": "pass" if existing_fields else "review_required",
            "required": True,
            "fields": {},
            "existing_fields": existing_fields,
            "inserted_fields": [],
            "error_code": None if existing_fields else "DRAWING_TITLE_BLOCK_FIELDS_MISSING",
            "manual_review_required": not bool(existing_fields),
        }

    fields = {}
    skipped_existing = []
    override_existing = []
    insertion_fields = []
    for field in requested_fields:
        existing = existing_fields.get(field) or []
        program_field_exists = any(
            str(item.get("persistent_name") or "").startswith("CAD_TITLE__")
            for item in existing
        )
        if existing and (not manual_override or program_field_exists):
            fields[field] = {
                "value": str(request.get(field) or "").strip(),
                "source": "existing_template_property" if not program_field_exists else "existing_program_note",
                "linked_to_model_property": any(
                    bool(item.get("property_linked_text")) for item in existing
                ),
                "existing": existing,
                "clipped": False,
            }
            skipped_existing.append(field)
            continue
        if existing and manual_override:
            override_existing.append(field)
        insertion_fields.append(field)

    if box is None and insertion_fields:
        return {
            "status": "blocked",
            "required": True,
            "fields": fields,
            "existing_fields": existing_fields,
            "inserted_fields": [],
            "error_code": "DRAWING_TITLE_BLOCK_BOX_MISSING",
        }
    cells = _title_field_cells(request, paper_size)
    missing_positions = [field for field in insertion_fields if field not in cells]
    if missing_positions:
        return {
            "status": "blocked",
            "required": True,
            "fields": fields,
            "existing_fields": existing_fields,
            "inserted_fields": [],
            "missingPositions": missing_positions,
            "error_code": "DRAWING_TITLE_BLOCK_POSITION_REQUIRED",
        }
    failures = []
    occupied = []
    planned = []
    for field in insertion_fields:
        value = str(request.get(field) or "").strip()
        cell = cells[field]
        position = cell["positionMm"]
        x, y = position[0] / 1000.0, position[1] / 1000.0
        if not (box["left"] <= x <= box["right"] and box["bottom"] <= y <= box["top"]):
            failures.append({"field": field, "reason": "position_outside_title_block"})
            continue
        cell_height_mm = 5.0 * max(1, int(cell["maxLines"]))
        wrapped, clipped = _wrap_title_text(
            value,
            width_mm=cell["maxWidthMm"],
            height_mm=cell_height_mm,
            max_lines=cell["maxLines"],
        )
        if clipped:
            failures.append({"field": field, "reason": "text_truncated"})
            continue
        estimated_margin = 0.003
        field_box = {
            "left": x - estimated_margin,
            "right": x + cell["maxWidthMm"] / 1000.0,
            "bottom": y - cell_height_mm / 1000.0,
            "top": y,
        }
        if (
            field_box["left"] < box["left"] - 1e-9
            or field_box["right"] > box["right"] + 1e-9
            or field_box["bottom"] < box["bottom"] - 1e-9
            or field_box["top"] > box["top"] + 1e-9
        ):
            failures.append({"field": field, "reason": "estimated_text_outside_title_block"})
            continue
        overlap = next((
            previous_field for previous_field, previous_box in occupied
            if (
                min(field_box["right"], previous_box["right"]) > max(field_box["left"], previous_box["left"])
                and min(field_box["top"], previous_box["top"]) > max(field_box["bottom"], previous_box["bottom"])
            )
        ), None)
        if overlap:
            failures.append({"field": field, "reason": f"overlaps_{overlap}"})
            continue
        occupied.append((field, field_box))
        planned.append({
            "field": field,
            "value": value,
            "wrapped_text": wrapped,
            "clipped": clipped,
            "cell": cell,
            "box": field_box,
            "x": x,
            "y": y,
        })
    if failures:
        clip_only = all(item["reason"] == "text_truncated" for item in failures)
        return {
            "status": "review_required" if clip_only else "failed",
            "required": True,
            "fields": fields,
            "existing_fields": existing_fields,
            "inserted_fields": [],
            "failures": failures,
            "error_code": (
                "DRAWING_TITLE_BLOCK_TEXT_CLIPPED"
                if clip_only else "DRAWING_TITLE_BLOCK_WRITE_FAILED"
            ),
            "manual_review_required": True,
        }

    link_model_properties = bool(request.get("linkToModelProperties", True))
    inserted_fields = []
    for item in planned:
        field = item["field"]
        aliases = _title_property_aliases(request, field)
        link_expression = f'$PRPSHEET:"{aliases[0]}"' if link_model_properties and aliases else None
        note_text = link_expression or item["wrapped_text"]
        brace_expression = (
            f"$PRPSHEET:{{{aliases[0]}}}"
            if link_expression and aliases
            else None
        )
        note_result = add_note(
            drawing_model,
            item["x"],
            item["y"],
            note_text,
            persistent_name=f"CAD_TITLE__{field}",
            accepted_texts=tuple(
                value for value in (note_text, brace_expression, item["wrapped_text"], item["value"])
                if value
            ),
        )
        fields[field] = {
            "value": item["value"],
            "wrapped_text": item["wrapped_text"],
            "linked_to_model_property": bool(link_expression),
            "link_expression": link_expression,
            "clipped": False,
            "cell": item["cell"],
            "box": item["box"],
            "note": note_result,
        }
        inserted_fields.append(field)
        if note_result.get("status") != "pass":
            failures.append({"field": field, "reason": "note_create_or_position_failed"})
    if failures:
        return {
            "status": "failed",
            "required": True,
            "fields": fields,
            "existing_fields": existing_fields,
            "inserted_fields": inserted_fields,
            "failures": failures,
            "error_code": "DRAWING_TITLE_BLOCK_WRITE_FAILED",
            "manual_review_required": True,
        }
    status = "review_required" if manual_override and (override_existing or skipped_existing) else "pass"
    return {
        "status": status,
        "required": True,
        "fields": fields,
        "existing_fields": existing_fields,
        "inserted_fields": inserted_fields,
        "skipped_existing_fields": skipped_existing,
        "overridden_existing_fields": override_existing,
        "manual_override": manual_override,
        "failures": [],
        "error_code": None if status == "pass" else "DRAWING_TITLE_BLOCK_MANUAL_OVERRIDE",
        "manual_review_required": status != "pass",
    }


def _bom_source_view(drawing_model):
    """Return the base drawing view that owns the assembly BOM."""
    sheet = get_com_member(drawing_model, "GetCurrentSheet")
    views = tuple(get_com_member(sheet, "GetViews") or ())
    if not views:
        raise RuntimeError("当前图纸没有可用于插入 BOM 的工程视图")
    for view in views:
        try:
            if get_com_member(view, "GetBaseView", default=None) is None:
                return view
        except Exception:
            continue
    return views[0]


def insert_bom_table(
    drawing_model,
    template_path,
    x,
    y,
    bom_type=1,
    config_name="",
    anchor_type=1,
    include_thickness=False,
    include_surface_treatment=False,
):
    """
    插入 BOM 表

    参数:
        template_path: BOM 模板路径（.sldbomtbt）
        x, y: 表格放置位置（米）
        bom_type: 1=顶层, 2=仅零件, 3=缩进
        config_name: 配置名称
        anchor_type: swBOMConfigurationAnchorType_e；默认左上角
    """
    view = _bom_source_view(drawing_model)
    # SolidWorks 2025 exposes native BOM insertion on IView. The historical
    # DrawingDoc.InsertBomTable4 call is not available through pywin32.
    try:
        table = get_com_member(
            view,
            "InsertBomTable6",
            False,
            float(x),
            float(y),
            int(anchor_type),
            int(bom_type),
            str(config_name),
            str(template_path),
            False,
            0,
            False,
            False,
            False,
        )
    except Exception:
        table = None
    if table is None:
        table = get_com_member(
            view,
            "InsertBomTable2",
            False,
            float(x),
            float(y),
            int(anchor_type),
            int(bom_type),
            str(config_name),
            str(template_path),
        )
    if table is None:
        raise RuntimeError("SolidWorks 未返回 BOM 表注解")

    column_count = int(get_com_member(table, "ColumnCount") or 0)
    if column_count < 5:
        raise RuntimeError(f"BOM 表仅包含 {column_count} 列，无法建立要求的 5 列")
    thickness_index = None
    surface_treatment_index = None
    if include_thickness:
        inserted = bool(get_com_member(table, "InsertColumn2", 4, 0, "板厚", 0))
        if not inserted:
            inserted = bool(get_com_member(table, "InsertColumn", 4, 0, "板厚"))
        if not inserted:
            raise RuntimeError("BOM 表无法插入厚度列")
        thickness_index = int(get_com_member(table, "ColumnCount") or 0) - 1
    if include_surface_treatment:
        inserted = bool(get_com_member(table, "InsertColumn2", 4, 0, "表面处理", 0))
        if not inserted:
            inserted = bool(get_com_member(table, "InsertColumn", 4, 0, "表面处理"))
        if not inserted:
            raise RuntimeError("BOM 表无法插入表面处理列")
        surface_treatment_index = int(get_com_member(table, "ColumnCount") or 0) - 1

    # Rebind item metadata columns to the component properties that carry the
    # manufacturing identifiers. swBomTableColumnType_CustomProperty = 204.
    for index, property_name in (
        (1, "PartNumber"),
        (2, "Description"),
        (4, "Material"),
    ):
        status = get_com_member(
            table,
            "SetColumnType3",
            index,
            204,
            False,
            property_name,
        )
        if int(status) != 0:
            raise RuntimeError(
                f"BOM 第 {index + 1} 列无法绑定属性 {property_name!r}: status={status}"
            )
    if thickness_index is not None:
        status = get_com_member(table, "SetColumnType3", thickness_index, 204, False, "Thickness")
        if int(status) != 0:
            raise RuntimeError(f"BOM 厚度列无法绑定 Thickness 属性: status={status}")
    if surface_treatment_index is not None:
        status = get_com_member(
            table,
            "SetColumnType3",
            surface_treatment_index,
            204,
            False,
            "SurfaceTreatment",
        )
        if int(status) != 0:
            raise RuntimeError(
                f"BOM 表面处理列无法绑定 SurfaceTreatment 属性: status={status}"
            )
    for index, title in (
        (0, "序号"),
        (1, "图号"),
        (2, "名称"),
        (3, "数量"),
        (4, "材料"),
    ):
        get_com_member(table, "SetColumnTitle2", index, title, False)
    if thickness_index is not None:
        get_com_member(table, "SetColumnTitle2", thickness_index, "板厚", False)
    if surface_treatment_index is not None:
        get_com_member(
            table,
            "SetColumnTitle2",
            surface_treatment_index,
            "表面处理",
            False,
        )

    # Put material before quantity while retaining native Item/Part/QTY columns.
    try:
        get_com_member(table, "MoveColumn", 4, 2, 3)
    except Exception:
        pass
    if thickness_index is not None:
        try:
            get_com_member(table, "MoveColumn", thickness_index, 2, 4)
        except Exception:
            pass
        if surface_treatment_index is not None:
            try:
                get_com_member(table, "MoveColumn", surface_treatment_index, 2, 5)
            except Exception:
                pass
    widths = [0.010, 0.027, 0.034, 0.016, 0.015]
    if thickness_index is not None:
        widths = [0.010, 0.027, 0.034, 0.015, 0.012, 0.016]
    if surface_treatment_index is not None:
        widths = [0.010, 0.027, 0.034, 0.015, 0.012, 0.018, 0.016]
    for index, width_m in enumerate(widths):
        get_com_member(table, "SetColumnWidth", index, float(width_m), 0)
    return table


def _native_bom_item_numbers(drawing_model):
    """Read configured item-number cells from a native drawing BOM table."""
    sheet = _safe_member(drawing_model, "GetCurrentSheet")
    sheet_name = str(_safe_member(sheet, "GetName", default="") or "")
    native_view = _safe_member(drawing_model, "GetFirstView")
    visited = 0
    while native_view is not None and visited < 4096:
        for table in _as_sequence(_safe_member(native_view, "GetTableAnnotations", default=[])):
            evidence = _table_evidence(table, sheet_name)
            if evidence.get("type") == 2 and evidence.get("row_count", 0) > 1:
                cells = evidence.get("cells") or []
                numbers = [
                    str(row[0]).strip()
                    for row in cells[1:]
                    if isinstance(row, (list, tuple)) and row and str(row[0]).strip()
                ]
                if numbers:
                    return numbers, None
        native_view = _safe_member(native_view, "GetNextView")
        visited += 1
    return [], None


def add_bom_balloons(drawing_model, *, view_name=None, insert_magnetic_line=False):
    """Insert native BOM balloons linked to the existing table item numbers."""
    item_numbers, bom_view = _native_bom_item_numbers(drawing_model)
    if not item_numbers:
        return {
            "status": "blocked",
            "error_code": "DRAWING_NATIVE_BOM_MISSING",
            "message": "未找到可读取项目号的原生 BOM 表。",
        }
    views = tuple(_as_sequence(_safe_member(_safe_member(drawing_model, "GetCurrentSheet"), "GetViews", default=[])))
    view = next(
        (item for item in views if str(_safe_member(item, "Name", default="")) == str(view_name or "")),
        bom_view or _bom_source_view(drawing_model),
    )
    actual_view_name = str(_safe_member(view, "Name", default="") or "")
    extension = _safe_member(drawing_model, "Extension")
    _safe_member(drawing_model, "ClearSelection2", True)
    if not bool(_safe_member(drawing_model, "ActivateView", actual_view_name, default=False)):
        return {"status": "failed", "error_code": "DRAWING_BALLOON_VIEW_ACTIVATE_FAILED", "view": actual_view_name}
    selected = bool(get_com_member(
        extension,
        "SelectByID2",
        actual_view_name,
        "DRAWINGVIEW",
        0.0,
        0.0,
        0.0,
        False,
        0,
        create_empty_dispatch_variant(),
        0,
    ))
    manager = _safe_member(drawing_model, "SelectionManager")
    selected_count = int(_safe_member(manager, "GetSelectedObjectCount2", -1, default=0) or 0)
    if not selected or selected_count != 1:
        return {
            "status": "failed",
            "error_code": "DRAWING_BALLOON_VIEW_SELECT_FAILED",
            "view": actual_view_name,
            "selected": selected,
            "selected_count": selected_count,
        }
    options = _safe_member(drawing_model, "CreateAutoBalloonOptions")
    if options is None:
        return {"status": "blocked", "error_code": "DRAWING_AUTO_BALLOON_OPTIONS_UNAVAILABLE"}
    settings = {
        "Layout": 1,
        "ReverseDirection": False,
        "IgnoreMultiple": True,
        "InsertMagneticLine": bool(insert_magnetic_line),
        "LeaderAttachmentToFaces": True,
        "UpperTextContent": 1,
        "ItemNumberStart": 1,
        "ItemNumberIncrement": 1,
        "ItemOrder": 1,
    }
    for name, value in settings.items():
        try:
            setattr(options, name, value)
        except Exception as exc:
            return {
                "status": "failed",
                "error_code": "DRAWING_AUTO_BALLOON_OPTIONS_FAILED",
                "option": name,
                "error": str(exc),
            }
    notes = tuple(_as_sequence(get_com_member(drawing_model, "AutoBalloon5", options, default=[])))
    _safe_member(drawing_model, "ClearSelection2", True)
    records = []
    for note in notes:
        evidence = _note_evidence(note)
        upper_text = str(_safe_member(note, "GetBomBalloonText", True, default="") or "")
        records.append({
            **evidence,
            "item_number": upper_text or str(evidence.get("text") or ""),
            "is_bom_balloon": bool(_safe_member(note, "IsBomBalloon", default=False)),
            "has_balloon": bool(_safe_member(note, "HasBalloon", default=False)),
        })
    actual_numbers = [str(item["item_number"]).strip() for item in records]
    expected = sorted(str(item) for item in item_numbers)
    actual = sorted(actual_numbers)
    linked = bool(records) and actual == expected and all(item["is_bom_balloon"] for item in records)
    return {
        "status": "pass" if linked else "failed",
        "method": "IDrawingDoc.AutoBalloon5",
        "view": actual_view_name,
        "expected_item_numbers": expected,
        "actual_item_numbers": actual,
        "balloon_count": len(records),
        "balloons": records,
        "error_code": None if linked else "DRAWING_BOM_BALLOON_MAPPING_FAILED",
        "manual_review_required": not linked,
    }


def set_sheet_format(drawing_model, format_path):
    """
    设置图纸格式（图框）

    参数:
        format_path: 图纸格式文件路径（.slddrt）
    """
    sheet = drawing_model.GetCurrentSheet()
    return sheet.SetTemplateName(format_path)


def add_sheet(drawing_model, paper_size=PAPER_SIZES["A4"]["code"], template_path="", first_angle=True):
    """
    添加新图纸

    参数:
        paper_size: 纸张大小
            SolidWorks swDwgPaperSizes_e，例如 6=A4、7=A4P、
            8=A3、9=A2、10=A1、11=A0
        template_path: 图纸格式模板路径
    """
    return drawing_model.NewSheet4(
        "", paper_size, SW_DWG_TEMPLATE_CUSTOM, 1.0, 1.0, bool(first_angle),
        template_path, 0, 0, "", 0, 0, 0, 0, 0, 0
    )


def add_a3_sheet(drawing_model, template_candidates, *, require_gbt=True, projection="first_angle") -> dict:
    """@brief 选择本机 A3 图框并创建横向 A3 工程图页。"""
    selection = select_drawing_template(template_candidates, paper_size="A3", require_gbt=require_gbt)
    if selection["selected"] is None:
        return {
            **selection,
            "stage": "preflight",
            "retryable": True,
            "created": False,
        }
    created = bool(add_sheet(
        drawing_model,
        paper_size=PAPER_SIZES["A3"]["code"],
        template_path=selection["selected"],
        first_angle=str(projection).lower() == "first_angle",
    ))
    return {
        **selection,
        "status": "pass" if created else "failed",
        "stage": "create",
        "retryable": not created,
        "created": created,
        "projection": str(projection).lower(),
        "error_code": None if created else "DRAWING_A3_SHEET_CREATE_FAILED",
    }


def setup_current_sheet_as_a3(drawing_model, template_candidates, *, require_gbt=True, projection="first_angle") -> dict:
    """@brief 使用统一的受控逻辑将当前页设置为横向 A3。"""
    return setup_current_sheet(
        drawing_model,
        template_candidates,
        paper_size="A3",
        projection=projection,
        require_gbt=require_gbt,
    )


def get_all_views(drawing_model):
    """获取当前图纸上的所有视图"""
    sheet = get_com_member(drawing_model, "GetCurrentSheet")
    views = get_com_member(sheet, "GetViews")
    result = []
    if views:
        for view in views:
            result.append({
                "name": view.Name,
                "type": view.Type,
                "scale": view.ScaleRatio,
            })
    return result


def _paper_size_from_template(template_path):
    """@brief 从模板文件名推断标准图幅；无法判断时返回 None。"""
    name = Path(str(template_path or "")).stem.upper()
    for paper_size in PAPER_SIZES:
        if re.search(rf"(?:^|[^A-Z0-9]){paper_size}(?:[^A-Z0-9]|$)", name):
            return paper_size
    return None


TABLE_ANNOTATION_KINDS = {
    0: "general",
    1: "hole_chart",
    2: "bom",
    3: "revision",
    4: "weldment_cut_list",
    5: "title_block",
    6: "general_tolerance",
}


def _table_cell_text(table, row, column):
    """@brief 按新版优先、旧版回退的顺序读取表格显示文字。"""
    for member, args in (
        ("DisplayedText2", (row, column, False)),
        ("DisplayedText", (row, column)),
        ("Text2", (row, column, False)),
        ("Text", (row, column)),
    ):
        value = _safe_member(table, member, *args, default=None)
        if value is not None:
            return str(value)
    return ""


def _table_evidence(table, sheet_name):
    """@brief 回读表格类型、数据行、单元格及 BOM 配置证据。"""
    table_type = _safe_member(table, "Type", default=None)
    try:
        normalized_type = int(table_type)
    except (TypeError, ValueError):
        normalized_type = table_type
    try:
        row_count = int(_safe_member(table, "RowCount", default=0) or 0)
        column_count = int(_safe_member(table, "ColumnCount", default=0) or 0)
    except (TypeError, ValueError):
        row_count, column_count = 0, 0
    cells = []
    if 0 < row_count <= 500 and 0 < column_count <= 100 and row_count * column_count <= 5000:
        cells = [
            [_table_cell_text(table, row, column) for column in range(column_count)]
            for row in range(row_count)
        ]
    configuration = ""
    if normalized_type == 2:
        bom_feature = _safe_member(table, "BomFeature", default=None)
        configuration = str(_safe_member(bom_feature, "Configuration", default="") or "")
    return {
        "sheet": str(sheet_name),
        "type": normalized_type,
        "kind": TABLE_ANNOTATION_KINDS.get(normalized_type, "unknown"),
        "title": str(_safe_member(table, "Title", default="") or ""),
        "row_count": row_count,
        "column_count": column_count,
        "configuration": configuration,
        "cells": cells,
        "box": _annotation_box(table),
    }


def bom_table_evidence(table, sheet_name=""):
    """Return structured evidence for a native BOM table annotation."""
    return _table_evidence(table, sheet_name)


def _annotation_text_parts(annotation_owner):
    """@brief 回读专业标注的可见文字片段，保留原始顺序。"""
    try:
        count = int(_safe_member(annotation_owner, "GetTextCount", default=0) or 0)
    except (TypeError, ValueError):
        count = 0
    if not 0 <= count <= 1000:
        count = 0
    parts = []
    for index in range(count):
        text = str(_safe_member(annotation_owner, "GetTextAtIndex", index, default="") or "")
        if text:
            parts.append(text)
    return parts


def _professional_annotation_record(owner, kind, view_record):
    """@brief 构造带所属视图、文字和边界的专业标注证据。"""
    annotation = _safe_member(owner, "GetAnnotation")
    annotation_name = str(_safe_member(annotation, "GetName", default="") or "")
    from scripts.sw_drawing_native import describe_target
    return {
        "kind": kind,
        "sheet": view_record["sheet"],
        "view": view_record["name"],
        "semantic_view": view_record.get("semantic_view") or "",
        "text_parts": _annotation_text_parts(owner),
        "box": _annotation_box(owner),
        "id": annotation_name.removeprefix("CAD_ANN__") if annotation_name.startswith("CAD_ANN__") else None,
        "position_m": _safe_member(annotation, "GetPosition"),
        "target": describe_target(owner),
    }


def first_center_mark(view):
    """@brief 仅对缺失成员回退旧接口，真实调用错误继续向上传递。"""
    for name in ("GetFirstCenterMark2", "GetFirstCenterMark"):
        value = get_com_member(view, name, default=None)
        if value is not None:
            return value
    return None


def _view_center_marks(view):
    """@brief 遍历视图中心标记，并兼容 SW2025 SP1 之前的回读接口。"""
    current = first_center_mark(view)
    marks = []
    seen = set()
    while current is not None and len(marks) < 10000:
        identity = id(current)
        if identity in seen:
            break
        seen.add(identity)
        marks.append(current)
        current = _safe_member(current, "GetNext")
    if marks:
        return marks
    # GetCenterMarks 不能返回注解型中心标记，仅作为旧版本兼容回退。
    return _as_sequence(_safe_member(view, "GetCenterMarks", default=[]))


def _gtol_frame_records(owner, frame_count):
    """回读 2022+ XML 或旧格式框；框序号从 1 开始。"""
    records = []
    format_type = _safe_member(owner, "GetFormat", default=None)
    for index in range(1, frame_count + 1):
        if format_type == 2:
            frame = _safe_member(owner, "GetFrame", index, default=None)
            xml = _safe_member(frame, "GetSymbolXml", default="") if frame else ""
            item = {"index": index, "symbols": [], "values": []}
            if isinstance(xml, str) and xml and len(xml) <= 65536 and "<!" not in xml:
                try:
                    root = ET.fromstring(xml)
                    if root.tag == "GtolFrame":
                        item["xml"] = xml
                        item["symbols"] = [node.text for node in root.findall("./ToleranceSymbol") if node.text]
                        item["values"] = [node.text for node in root.findall("./ToleranceRangeInfo/PrimaryToleranceValue") if node.text]
                        item["values"] += [node.text for node in root.findall(".//DatumLetter") if node.text]
                    else:
                        item["xml_error"] = "invalid_xml"
                except ET.ParseError:
                    item["xml_error"] = "invalid_xml"
            elif xml:
                item["xml_error"] = "invalid_xml"
            records.append(item)
        elif format_type == 1:
            records.append({"index": index,
                            "symbols": _as_sequence(_safe_member(owner, "GetFrameSymbols3", index, default=[])),
                            "values": _as_sequence(_safe_member(owner, "GetFrameValues", index, default=[]))})
        else:
            records.append({"index": index, "symbols": [], "values": [], "error": "unknown_gtol_format"})
    return records


def _collect_view_professional_annotations(view, view_record):
    """@brief 使用 SW2026 Interop 已反射确认的 IView 回读接口收集专业标注。"""
    result = {
        "center_marks": [],
        "center_lines": [],
        "datum_tags": [],
        "geometric_tolerances": [],
        "surface_finish_symbols": [],
        "weld_symbols": [],
    }
    for owner in _view_center_marks(view):
        record = _professional_annotation_record(owner, "center_mark", view_record)
        record.update({
            "size_m": _safe_member(owner, "Size", default=None),
            "show_lines": _safe_member(owner, "ShowLines", default=None),
            "style": _safe_member(owner, "Style", default=None),
        })
        result["center_marks"].append(record)
    for owner in _as_sequence(_safe_member(view, "GetCenterLines", default=[])):
        result["center_lines"].append(_professional_annotation_record(owner, "center_line", view_record))
    for owner in _as_sequence(_safe_member(view, "GetDatumTags", default=[])):
        record = _professional_annotation_record(owner, "datum", view_record)
        record["label"] = str(_safe_member(owner, "GetLabel", default="") or "")
        record["display_style"] = _safe_member(owner, "GetDisplayStyle")
        result["datum_tags"].append(record)
    for owner in _as_sequence(_safe_member(view, "GetGTols", default=[])):
        record = _professional_annotation_record(owner, "geometric_tolerance", view_record)
        try:
            frame_count = int(_safe_member(owner, "GetFrameCount", default=0) or 0)
        except (TypeError, ValueError):
            frame_count = 0
        frame_count = frame_count if 0 <= frame_count <= 100 else 0
        record["datum_identifier"] = str(_safe_member(owner, "GetDatumIdentifier", default="") or "")
        record["frames"] = _gtol_frame_records(owner, frame_count)
        result["geometric_tolerances"].append(record)
    for owner in _as_sequence(_safe_member(view, "GetSFSymbols", default=[])):
        record = _professional_annotation_record(owner, "surface_finish", view_record)
        record.update({
            "symbol_type": _safe_member(owner, "GetSymbolType", default=None),
            "symbol": _safe_member(owner, "GetSymbol", default=None),
            "direction_of_lay": _safe_member(owner, "GetDirectionOfLay", default=None),
        })
        result["surface_finish_symbols"].append(record)
    for owner in _as_sequence(_safe_member(view, "GetWeldSymbols", default=[])):
        result["weld_symbols"].append(_professional_annotation_record(owner, "weld_symbol", view_record))
    return result


def inspect_drawing_structure(drawing_model, *, paper_size_hint=None, title_block_box=None) -> dict:
    """@brief 读取工程图结构并返回可审计报告，不修改文档。"""
    sheets = _as_sequence(_safe_member(drawing_model, "GetSheetNames", default=[]))
    if not sheets:
        current_sheet = _safe_member(drawing_model, "GetCurrentSheet")
        current_name = _safe_member(current_sheet, "GetName", default="")
        if current_name:
            sheets = [current_name]
    views = []
    dimensions = []
    notes = []
    balloons = []
    tables = []
    professional_annotations = {
        "center_marks": [],
        "center_lines": [],
        "hole_callouts": [],
        "datum_tags": [],
        "geometric_tolerances": [],
        "surface_finish_symbols": [],
        "weld_symbols": [],
    }
    for sheet_name in sheets or [""]:
        sheet = _safe_member(drawing_model, "GetSheet", sheet_name) or _safe_member(drawing_model, "GetCurrentSheet")
        sheet_views = _as_sequence(_safe_member(sheet, "GetViews", default=[]))
        mapped_views, _, _ = _map_standard_views_from_sheet_views(sheet_views)
        semantic_by_object = {id(view): name for name, view in mapped_views.items()}
        for view in sheet_views:
            view_record = {
                "sheet": str(sheet_name),
                "name": _safe_member(view, "Name", default=""),
                "type": _safe_member(view, "Type", default=None),
                "orientation": _safe_member(view, "GetOrientationName", default=""),
                "semantic_view": semantic_by_object.get(id(view), ""),
                "scale": _safe_member(view, "ScaleRatio", default=None),
                "box": _normalise_box(_safe_member(view, "GetOutline")),
            }
            views.append(view_record)
            view_annotations = _collect_view_professional_annotations(view, view_record)
            for key, records in view_annotations.items():
                professional_annotations[key].extend(records)
            view_dimensions = _view_display_dimensions(view)
            for dimension in view_dimensions:
                native_box = _annotation_box(dimension)
                estimated_box_evidence = estimate_dimension_text_box(dimension) if native_box is None else None
                native_dimension = (
                    _safe_member(dimension, "GetDimension2", 0)
                    or _safe_member(dimension, "GetDimension")
                )
                native_annotation = _safe_member(dimension, "GetAnnotation")
                native_dimension_name = str(_safe_member(native_dimension, "FullName", default="") or "")
                annotation_name = str(_safe_member(native_annotation, "GetName", default="") or "")
                dimension_record = {
                    "sheet": str(sheet_name),
                    "view": _safe_member(view, "Name", default=""),
                    "semantic_view": view_record["semantic_view"],
                    "name": (
                        _safe_member(dimension, "Name", default="")
                        or _safe_member(dimension, "GetNameForSelection", default="")
                        or _safe_member(_safe_member(dimension, "GetDimension"), "FullName", default="")
                    ),
                    "type": _safe_member(dimension, "Type2", default=None),
                    "text": _safe_member(dimension, "GetText", 0, default=""),
                    "native_dimension_name": native_dimension_name,
                    "annotation_name": annotation_name,
                    "box": native_box or estimated_box_evidence.get("box"),
                    "box_source": "native" if native_box else estimated_box_evidence.get("source"),
                    "box_confidence": "high" if native_box else estimated_box_evidence.get("confidence"),
                    "box_evidence": {
                        "box": native_box,
                        "source": "native",
                        "confidence": "high",
                        "method": "annotation_get_box",
                    } if native_box else estimated_box_evidence,
                    "is_hole_callout": bool(_safe_member(dimension, "IsHoleCallout", default=False)),
                    "hole_callout_variables": _as_sequence(_safe_member(dimension, "GetHoleCalloutVariables", default=[])),
                }
                from scripts.sw_drawing_native import dimension_binding
                dimension_record.update(dimension_binding(_safe_member(native_annotation, "GetName", default=""), dimension_record["type"]))
                system_value = _safe_member(native_dimension, "SystemValue")
                dimension_record["value_mm"] = float(system_value) * 1000 if isinstance(system_value, (int, float)) and dimension_record["type"] != 3 else None
                dimension_record["value_degrees"] = math.degrees(system_value) if isinstance(system_value, (int, float)) and dimension_record["type"] == 3 else None
                dimension_record["basic"] = _safe_member(_safe_member(native_dimension, "Tolerance"), "Type") == 1
                dimension_record["prefix"] = _safe_member(dimension, "GetText", 1, default="")
                dimension_record["dedupe_identity"] = (
                    native_dimension_name
                    or (f"CAD_DIM__{dimension_record.get('kind')}__{dimension_record.get('id')}"
                        if dimension_record.get("id")
                        else "")
                )
                dimensions.append(dimension_record)
                if dimension_record["is_hole_callout"]:
                    professional_annotations["hole_callouts"].append({
                        "kind": "hole_callout",
                        "sheet": dimension_record["sheet"],
                        "view": dimension_record["view"],
                        "semantic_view": dimension_record["semantic_view"],
                        "name": dimension_record["name"],
                        "text_parts": [dimension_record["text"]] if dimension_record["text"] else [],
                        "variables": dimension_record["hole_callout_variables"],
                        "box": dimension_record["box"],
                    })
            for note in _as_sequence(_safe_member(view, "GetNotes", default=[])):
                note_evidence = _note_evidence(note)
                note_text = str(note_evidence.get("text") or "").strip()
                owner_view_type = view_record["type"]
                balloon_evidence = _bom_balloon_evidence(note)
                notes.append({
                    "sheet": str(sheet_name),
                    "owner_view": view_record["name"],
                    "owner_view_type": owner_view_type,
                    "note_kind": (
                        "bom_balloon"
                        if balloon_evidence is not None
                        else
                        "title_block_field"
                        if str(note_evidence.get("persistent_name") or "").startswith("CAD_TITLE__")
                        else "view_label"
                        if owner_view_type in {2, 3} and not note_text
                        else "note"
                    ),
                    **note_evidence,
                })
                if balloon_evidence is not None:
                    balloons.append({
                        "sheet": str(sheet_name),
                        "view": view_record["name"],
                        "semantic_view": view_record["semantic_view"],
                        **balloon_evidence,
                    })
            for table in _as_sequence(_safe_member(view, "GetTableAnnotations", default=[])):
                tables.append(_table_evidence(table, sheet_name))

    # IDrawingDoc.GetFirstView starts with the sheet view itself. BOM tables are
    # commonly owned by that sheet view and are not returned by ISheet.GetViews.
    native_view = _safe_member(drawing_model, "GetFirstView", default=None)
    visited = 0
    while native_view is not None and visited < 4096:
        native_sheet_name = str(
            _safe_member(_safe_member(native_view, "GetSheet"), "GetName", default="")
            or (sheets[0] if sheets else "")
        )
        for table in _as_sequence(_safe_member(native_view, "GetTableAnnotations", default=[])):
            evidence = _table_evidence(table, native_sheet_name)
            signature = (
                evidence.get("type"),
                evidence.get("title"),
                evidence.get("row_count"),
                evidence.get("column_count"),
                tuple((evidence.get("box") or {}).get(key) for key in ("left", "bottom", "right", "top")),
            )
            existing = {
                (
                    item.get("type"),
                    item.get("title"),
                    item.get("row_count"),
                    item.get("column_count"),
                    tuple((item.get("box") or {}).get(key) for key in ("left", "bottom", "right", "top")),
                )
                for item in tables
            }
            if signature not in existing:
                tables.append(evidence)
        for note in _as_sequence(_safe_member(native_view, "GetNotes", default=[])):
            evidence = _note_evidence(note)
            balloon_evidence = _bom_balloon_evidence(note)
            signature = (
                str(evidence.get("text") or ""),
                str(evidence.get("persistent_name") or ""),
                tuple((evidence.get("box") or {}).get(key) for key in ("left", "bottom", "right", "top")),
            )
            existing_notes = {
                (
                    str(item.get("text") or ""),
                    str(item.get("persistent_name") or ""),
                    tuple((item.get("box") or {}).get(key) for key in ("left", "bottom", "right", "top")),
                )
                for item in notes
            }
            if signature not in existing_notes:
                notes.append({
                    "sheet": native_sheet_name,
                    "owner_view": str(_safe_member(native_view, "Name", default="") or ""),
                    "owner_view_type": _safe_member(native_view, "Type", default=None),
                    "note_kind": (
                        "bom_balloon"
                        if balloon_evidence is not None
                        else
                        "title_block_field"
                        if str(evidence.get("persistent_name") or "").startswith("CAD_TITLE__")
                        else "sheet_format_note"
                    ),
                    **evidence,
                })
            if balloon_evidence is not None:
                balloons.append({
                    "sheet": native_sheet_name,
                    "view": str(_safe_member(native_view, "Name", default="") or ""),
                    "semantic_view": "",
                    **balloon_evidence,
                })
        native_view = _safe_member(native_view, "GetNextView", default=None)
        visited += 1
    current_sheet = _safe_member(drawing_model, "GetCurrentSheet")
    template = _safe_member(current_sheet, "GetTemplateName", default="")
    paper_size = str(paper_size_hint or _paper_size_from_template(template) or "").upper() or None
    spec = PAPER_SIZES.get(paper_size)
    sheet_size_source = "inferred" if spec else "unavailable"
    projection = None
    try:
        properties = _current_sheet_properties(current_sheet)
        spec = {"width_m": properties[5], "height_m": properties[6]}
        sheet_size_source = "GetProperties2"
        projection = "first_angle" if properties[4] else "third_angle"
        paper_size = _paper_size_from_dimensions(properties[5], properties[6]) or "custom"
    except Exception:
        pass  # Legacy inspection fallback is explicitly labelled as inferred.
    inferred_title_box = title_block_box
    if inferred_title_box is None and spec is not None:
        inferred_title_box = {
            "left": spec["width_m"] - 0.012 - 0.180,
            "bottom": 0.012,
            "right": spec["width_m"] - 0.012,
            "top": 0.067,
        }
    compact_template_name = re.sub(r"[^a-z0-9\u4e00-\u9fff]", "", Path(str(template or "")).stem.casefold())
    template_name = Path(str(template or "")).stem.casefold()
    gbt_candidate = (
        "gbt" in compact_template_name
        or "国标" in compact_template_name
        or bool(re.search(r"(?:^|[^a-z0-9])gb(?:t)?(?:[^a-z0-9]|$)", template_name, re.IGNORECASE))
    )
    outline_count = sum(item.get("box") is not None for item in views)
    dimension_box_count = sum(item.get("box") is not None for item in dimensions)
    native_dimension_box_count = sum(item.get("box_source") == "native" for item in dimensions)
    estimated_dimension_box_count = sum(item.get("box_source") == "estimated" and item.get("box") is not None for item in dimensions)
    low_confidence_dimension_box_count = sum(item.get("box_confidence") in {"low", "unavailable"} for item in dimensions)
    duplicate_groups = {}
    for dimension in dimensions:
        identity = str(dimension.get("dedupe_identity") or "")
        if not identity:
            continue
        key = (
            identity.casefold(),
            dimension.get("type"),
            round(float(dimension.get("value_mm") or 0.0), 9),
        )
        duplicate_groups.setdefault(key, []).append({
            "view": dimension.get("view"),
            "semantic_view": dimension.get("semantic_view"),
            "name": dimension.get("name"),
        })
    dimension_duplicates = [
        {"identity": key[0], "type": key[1], "value": key[2], "views": value}
        for key, value in duplicate_groups.items()
        if len(value) > 1
    ]
    title_fields = {}
    template_title_fields = {}
    semantic_title_links = {field: [] for field in TITLE_BLOCK_FIELDS}
    for note in notes:
        persistent_name = str(note.get("persistent_name") or "")
        field = _title_field_from_expression(
            note.get("property_linked_text"),
            persistent_name,
        )
        if field:
            semantic_title_links[field].append(note)
        if persistent_name.startswith("CAD_TITLE__"):
            title_fields[persistent_name.removeprefix("CAD_TITLE__")] = note
        elif field:
            template_title_fields.setdefault(field, []).append(note)
    semantic_duplicates = []
    template_semantic_multiplicity = {}
    for field, linked_notes in semantic_title_links.items():
        manual_notes = [
            note for note in linked_notes
            if str(note.get("persistent_name") or "").startswith("CAD_TITLE__")
        ]
        template_notes_for_field = [
            note for note in linked_notes
            if not str(note.get("persistent_name") or "").startswith("CAD_TITLE__")
        ]
        if len(template_notes_for_field) > 1:
            template_semantic_multiplicity[field] = len(template_notes_for_field)
        if len(manual_notes) > 1 or (manual_notes and template_notes_for_field):
            semantic_duplicates.append({
                "kind": "manual_field_duplicate",
                "field": field,
                "manual_note_count": len(manual_notes),
                "template_link_count": len(template_notes_for_field),
                "manual_notes": manual_notes,
                "template_links": template_notes_for_field,
            })
    if len(template_semantic_multiplicity) >= 3:
        semantic_duplicates.append({
            "kind": "multiple_template_title_blocks",
            "fields": sorted(template_semantic_multiplicity),
            "field_counts": template_semantic_multiplicity,
        })
    title_box = _normalise_box(title_block_box) if title_block_box is not None else inferred_title_box
    title_outside = []
    title_overlaps = []
    title_template_collisions = []
    if title_box is not None:
        for field, note in title_fields.items():
            note_box = _normalise_box(note.get("box"))
            if note_box is None:
                title_outside.append({"field": field, "reason": "box_unavailable"})
            elif (
                note_box["left"] < title_box["left"] - 1e-9
                or note_box["right"] > title_box["right"] + 1e-9
                or note_box["bottom"] < title_box["bottom"] - 1e-9
                or note_box["top"] > title_box["top"] + 1e-9
            ):
                title_outside.append({"field": field, "reason": "outside_title_block", "box": note_box})
        field_items = list(title_fields.items())
        for index, (first_field, first_note) in enumerate(field_items):
            first_box = _normalise_box(first_note.get("box"))
            if first_box is None:
                continue
            for second_field, second_note in field_items[index + 1:]:
                second_box = _normalise_box(second_note.get("box"))
                if second_box is None:
                    continue
                if (
                    min(first_box["right"], second_box["right"]) > max(first_box["left"], second_box["left"])
                    and min(first_box["top"], second_box["top"]) > max(first_box["bottom"], second_box["bottom"])
                ):
                    title_overlaps.append([first_field, second_field])
        template_notes = [
            note for note in notes
            if not str(note.get("persistent_name") or "").startswith("CAD_TITLE__")
            and _normalise_box(note.get("box")) is not None
            and _normalise_box(note.get("box"))["left"] >= title_box["left"]
            and _normalise_box(note.get("box"))["right"] <= title_box["right"]
            and _normalise_box(note.get("box"))["bottom"] >= title_box["bottom"]
            and _normalise_box(note.get("box"))["top"] <= title_box["top"]
        ]
        for field, field_note in field_items:
            field_box = _normalise_box(field_note.get("box"))
            if field_box is None:
                continue
            for template_note in template_notes:
                template_box = _normalise_box(template_note.get("box"))
                if (
                    min(field_box["right"], template_box["right"]) > max(field_box["left"], template_box["left"])
                    and min(field_box["top"], template_box["top"]) > max(field_box["bottom"], template_box["bottom"])
                ):
                    title_template_collisions.append({
                        "field": field,
                        "template_text": str(template_note.get("text") or ""),
                        "field_box": field_box,
                        "template_box": template_box,
                    })
    structural_quality_pass = (
        bool(views)
        and not dimension_duplicates
        and not title_outside
        and not title_overlaps
        and not title_template_collisions
        and not semantic_duplicates
    )
    template_title_values = {
        field: next(
            (str(note.get("text") or "") for note in records if str(note.get("text") or "").strip()),
            "",
        )
        for field, records in template_title_fields.items()
    }
    title_block_values = dict(template_title_values)
    title_block_values.update({
        field: str(note.get("text") or "")
        for field, note in title_fields.items()
    })
    result = {
        "status": "pass" if structural_quality_pass else "blocked" if not views else "review_required",
        "stage": "review",
        "sheets": [str(item) for item in sheets],
        "views": views,
        "dimensions": dimensions,
        "dimension_duplicates": dimension_duplicates,
        "notes": notes,
        "balloons": balloons,
        "tables": tables,
        "professional_annotations": professional_annotations,
        "template_path": str(template or ""),
        "paper_size": paper_size,
        "sheet_size": {"width_m": spec["width_m"], "height_m": spec["height_m"]} if spec else None,
        "sheet_size_source": sheet_size_source,
        "projection": projection,
        "title_block": {
            "candidate": bool(template),
            "gbt_candidate": gbt_candidate,
            "content_verified": bool(template_title_fields or title_fields),
            "fields": title_block_values,
            "field_evidence": title_fields,
            "template_field_evidence": template_title_fields,
            "template_semantic_multiplicity": template_semantic_multiplicity,
            "semantic_duplicates": semantic_duplicates,
            "outside_fields": title_outside,
            "overlapping_fields": title_overlaps,
            "template_collisions": title_template_collisions,
            "box": title_box,
        },
        "view_count": len(views),
        "dimension_count": len(dimensions),
        "table_count": len(tables),
        "view_outline_count": outline_count,
        "dimension_box_count": dimension_box_count,
        "native_dimension_box_count": native_dimension_box_count,
        "estimated_dimension_box_count": estimated_dimension_box_count,
        "low_confidence_dimension_box_count": low_confidence_dimension_box_count,
        "manual_review_required": not structural_quality_pass,
        "retryable": not bool(views),
        "error_code": (
            "DRAWING_VIEWS_MISSING"
            if not views
            else "DRAWING_DIMENSION_DUPLICATES_PRESENT"
            if dimension_duplicates
            else "DRAWING_TITLE_BLOCK_LAYOUT_RISK"
            if title_outside or title_overlaps or title_template_collisions
            else "DRAWING_TITLE_BLOCK_SEMANTIC_DUPLICATE"
            if semantic_duplicates
            else None
        ),
        "checks": [
            {"id": "drawing-views", "status": "pass" if views else "fail", "message": "工程图包含视图" if views else "未读取到工程图视图"},
            {"id": "drawing-template", "status": "pass" if template else "warning", "message": "已读取图框模板" if template else "图框模板需要人工确认"},
            {"id": "drawing-a3-sheet", "status": "pass" if paper_size == "A3" else "warning", "message": "当前图幅识别为 A3" if paper_size == "A3" else "当前图幅不是 A3 或无法识别"},
            {"id": "drawing-gbt-template", "status": "pass" if gbt_candidate else "warning", "message": "模板名称是 GB/T 候选，内容仍需目视复核" if gbt_candidate else "未发现 GB/T 图框候选证据"},
            {"id": "drawing-dimensions", "status": "pass" if dimensions else "warning", "message": "已读取真实尺寸实体" if dimensions else "未读取到尺寸实体"},
            {"id": "drawing-view-outlines", "status": "pass" if views and outline_count == len(views) else "warning", "message": "已读取全部视图边界" if views and outline_count == len(views) else "部分视图缺少边界，无法完整检查碰撞"},
            {
                "id": "drawing-dimension-boxes",
                "status": "pass" if dimensions and native_dimension_box_count == len(dimensions) else "warning",
                "message": (
                    "已读取全部尺寸文字原生边界"
                    if dimensions and native_dimension_box_count == len(dimensions)
                    else f"原生边界 {native_dimension_box_count}/{len(dimensions)}，保守估算 {estimated_dimension_box_count}/{len(dimensions)}；估算不等于原生证据"
                ),
            },
            {
                "id": "drawing-dimension-duplicates",
                "status": "pass" if not dimension_duplicates else "fail",
                "message": (
                    "未发现同一原生尺寸的重复显示"
                    if not dimension_duplicates
                    else f"发现 {len(dimension_duplicates)} 组重复原生尺寸"
                ),
                "duplicates": dimension_duplicates,
            },
            {
                "id": "drawing-title-block-bounds",
                "status": "pass" if not title_outside and not title_overlaps and not title_template_collisions and not semantic_duplicates else "fail",
                "message": (
                    "标题栏字段均在边界内、互不重叠且没有程序重复字段"
                    if not title_outside and not title_overlaps and not title_template_collisions and not semantic_duplicates
                    else "标题栏字段存在越界、文字框重叠或语义重复风险"
                ),
                "outside_fields": title_outside,
                "overlapping_fields": title_overlaps,
                "template_collisions": title_template_collisions,
                "semantic_duplicates": semantic_duplicates,
            },
        ],
    }
    return result


def auto_insert_center_marks(drawing_model, requirements) -> dict:
    """@brief 按视图自动插入中心标记，并以实体数量回读作为成功依据。"""
    requested = list(requirements or [])
    if not requested:
        return {
            "status": "not_requested",
            "requested": False,
            "requirements": [],
            "manual_review_required": False,
            "error_code": None,
        }

    sheet = _safe_member(drawing_model, "GetCurrentSheet")
    sheet_views = _as_sequence(_safe_member(sheet, "GetViews", default=[]))
    mapped_views, diagnostics, mapping_method = _map_standard_views_from_sheet_views(sheet_views)
    drawing_path = str(_safe_member(drawing_model, "GetPathName", default="") or "")
    results = []
    for requirement in requested:
        requirement_id = str(requirement.get("id") or "")
        orientation = _normalise_orientation(requirement.get("view"))
        expected_count = int(requirement.get("count") or 0)
        targets = list(requirement.get("targets") or [])
        insert_type = 0
        for target in targets:
            insert_type |= AUTO_CENTER_MARK_TARGETS.get(str(target), 0)
        view = mapped_views.get(orientation)
        if view is None or not orientation or insert_type == 0 or expected_count <= 0:
            results.append({
                "id": requirement_id,
                "status": "failed",
                "view": orientation or str(requirement.get("view") or ""),
                "targets": targets,
                "expected_count": expected_count,
                "before_count": 0,
                "after_count": 0,
                "created_count": 0,
                "api_returned": None,
                "error_code": "DRAWING_CENTER_MARK_REQUIREMENT_UNRESOLVED",
            })
            continue

        before_count = len(_view_center_marks(view))
        api_returned = None
        error = None
        if before_count < expected_count:
            view_name = str(_safe_member(view, "Name", default="") or "")
            if view_name:
                _safe_member(drawing_model, "ActivateView", view_name)
            try:
                api_returned = bool(get_com_member(
                    view,
                    "AutoInsertCenterMarks2",
                    insert_type,
                    0,      # swCenterMarkConnectionLine_None
                    True,   # 线性槽使用槽中心
                    True,   # 圆弧槽使用槽中心
                    True,   # 使用文档默认尺寸与间隙
                    0.0,
                    0.0,
                    False,
                    True,
                    0.0,
                ))
            except Exception as exc:
                error = str(exc)
            _safe_member(drawing_model, "ForceRebuild3", False)
            _safe_member(drawing_model, "GraphicsRedraw2")
        after_count = len(_view_center_marks(view))
        passed = after_count >= expected_count
        failure_code = None
        if not passed:
            failure_code = (
                "DRAWING_CENTER_MARK_DRAWING_SAVE_REQUIRED"
                if api_returned is True and not drawing_path
                else "DRAWING_CENTER_MARK_INSERT_OR_READBACK_FAILED"
            )
        results.append({
            "id": requirement_id,
            "status": "pass" if passed else "failed",
            "view": orientation,
            "actual_view": str(_safe_member(view, "Name", default="") or ""),
            "targets": targets,
            "insert_type": insert_type,
            "expected_count": expected_count,
            "before_count": before_count,
            "after_count": after_count,
            "created_count": max(0, after_count - before_count),
            "api_returned": api_returned,
            "error": error,
            "error_code": failure_code,
        })

    failed = [item for item in results if item["status"] != "pass"]
    aggregate_error = None
    if failed:
        aggregate_error = (
            "DRAWING_CENTER_MARK_DRAWING_SAVE_REQUIRED"
            if all(item.get("error_code") == "DRAWING_CENTER_MARK_DRAWING_SAVE_REQUIRED" for item in failed)
            else "DRAWING_CENTER_MARK_INSERT_OR_READBACK_FAILED"
        )
    return {
        "status": "failed" if failed else "pass",
        "requested": True,
        "requirements": results,
        "mapping_method": mapping_method,
        "mapping_diagnostics": diagnostics,
        "drawing_path": drawing_path,
        "manual_review_required": True,
        "retryable": aggregate_error == "DRAWING_CENTER_MARK_DRAWING_SAVE_REQUIRED",
        "error_code": aggregate_error,
    }


def export_sheet_to_pdf(model, output_path, sheet_names=None, sw_app=None):
    """
    将工程图导出为 PDF

    参数:
        model: IModelDoc2（工程图文档）
        output_path: 输出 PDF 路径
        sheet_names: 图纸名称列表，None=所有图纸
        sw_app: 可选的 SldWorks.Application 对象；传入会话对象可避免 SW2024
            动态 IModelDoc2 未暴露 GetSldWorksObject 的兼容性问题。
    """
    sw = sw_app
    if sw is None:
        for prog_id in ("SldWorks.Application.32", "SldWorks.Application"):
            try:
                sw = _win32com.GetActiveObject(prog_id)
                break
            except Exception:
                continue
    if sw is None:
        return False
    try:
        pdf_data = get_com_member(sw, "GetExportFileData", 1)  # 1 = swExportPDFData
    except Exception:
        return False

    if sheet_names is None:
        drawing = model
        sheet_names = get_com_member(drawing, "GetSheetNames")

    try:
        pdf_data.SetSheets(0, sheet_names)  # 0 = swExportData_ExportSpecifiedSheets
    except Exception:
        return False

    errors = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    warnings = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    success = model.Extension.SaveAs(output_path, 0, 1, pdf_data, errors, warnings)

    if success:
        print(f"PDF 导出成功: {output_path}")
    else:
        print(f"PDF 导出失败, 错误码: {errors.value}")
    return success


def _current_sheet_properties(sheet):
    """Read the actual sheet, including portrait/custom sizes; never infer its geometry."""
    values = get_com_member(sheet, "GetProperties2")
    if not isinstance(values, (tuple, list)) or len(values) != 8:
        raise ValueError("GetProperties2 did not return eight sheet properties")
    values = tuple(float(value) for value in values)
    if not all(math.isfinite(value) for value in values) or any(values[i] <= 0 for i in (2, 3, 5, 6)):
        raise ValueError("Invalid sheet scale or dimensions")
    return values


def _preserve_default_sheet(drawing_model, projection, paper_size=None):
    """Keep the sheet format embedded in NewDocument's default drawing template."""
    result = {"mode": "default_template", "configured": False, "projection": projection,
              "manual_review_required": True, "stage": "sheet", "status": "blocked"}
    sheet = _safe_member(drawing_model, "GetCurrentSheet")
    name = str(_safe_member(sheet, "GetName", default="") or "")
    if not name:
        return {**result, "error_code": "DRAWING_CURRENT_SHEET_MISSING"}
    try:
        before = _current_sheet_properties(sheet)
        template = str(_safe_member(sheet, "GetTemplateName", default="") or "")
        actual_paper_size = _paper_size_from_dimensions(before[5], before[6])
        requested_paper_size = _normalise_paper_size(paper_size)
        if actual_paper_size is None:
            return {
                **result,
                "status": "blocked",
                "error_code": "DRAWING_TEMPLATE_CUSTOM_SIZE_UNSUPPORTED",
                "template_path": template,
                "sheet_size_m": [before[5], before[6]],
            }
        if requested_paper_size is not None and actual_paper_size != requested_paper_size:
            return {
                **result,
                "status": "blocked",
                "error_code": "DRAWING_TEMPLATE_SIZE_MISMATCH",
                "requested_paper_size": requested_paper_size,
                "actual_paper_size": actual_paper_size,
                "template_path": template,
                "sheet_size_m": [before[5], before[6]],
            }
        first_angle = projection == "first_angle"
        if bool(before[4]) != first_angle:
            # SetProperties2 returns void. Preserve every property except projection,
            # and verify the result instead of treating its return value as success.
            get_com_member(sheet, "SetProperties2", int(before[0]), int(before[1]),
                           before[2], before[3], first_angle, before[5], before[6], bool(before[7]))
        after = _current_sheet_properties(sheet)
        if (bool(after[4]) != first_angle
                or any(not math.isclose(before[i], after[i], rel_tol=0, abs_tol=1e-9) for i in (0, 1, 2, 3, 5, 6, 7))
                or str(_safe_member(sheet, "GetTemplateName", default="") or "") != template):
            raise ValueError("Sheet properties or format did not match the requested preservation")
        return {**result, "status": "pass", "configured": True, "sheet_name": name,
                "template_path": template, "sheet_size_m": [after[5], after[6]],
                "paper_size": actual_paper_size, "requested_paper_size": requested_paper_size,
                "properties_before": list(before), "properties_after": list(after),
                "error_code": None}
    except Exception as exc:
        return {**result, "status": "failed", "error_code": "DRAWING_DEFAULT_SHEET_SETUP_FAILED", "error": str(exc)}


def _title_note_fingerprints(drawing_model):
    """Capture stable title-field note identities before a sheet format switch."""
    records = []
    for note, owner_view, owner_type in _iter_drawing_notes(drawing_model):
        evidence = _note_evidence(note)
        field = _title_field_from_expression(
            evidence.get("property_linked_text"),
            evidence.get("persistent_name", ""),
        )
        if not field:
            continue
        position = tuple(
            round(float(value), 9)
            for value in (evidence.get("position_m") or [])
        )
        records.append({
            "field": field,
            "persistent_name": str(evidence.get("persistent_name") or ""),
            "text": str(evidence.get("text") or ""),
            "property_linked_text": str(evidence.get("property_linked_text") or ""),
            "position_m": list(position),
            "owner_view": owner_view,
            "owner_view_type": owner_type,
            "program_owned": str(evidence.get("persistent_name") or "").startswith("CAD_TITLE__"),
        })
    return records


def _fingerprint_key(record):
    return (
        record.get("field"),
        record.get("persistent_name"),
        record.get("text"),
        record.get("property_linked_text"),
        tuple(record.get("position_m") or ()),
    )


def _program_note_identity(record):
    return (
        record.get("field"),
        record.get("persistent_name"),
        _normalise_property_expression(record.get("property_linked_text")),
    )


def _is_template_definition_note_name(name):
    """Return whether a native note name belongs to the installed sheet format."""
    value = str(name or "").strip()
    if not value or value.startswith("CAD_"):
        return False
    compact = re.sub(r"\s+", "", value).casefold()
    return bool(re.fullmatch(
        r"(?:detail|detailitem|detailcn|细节项目)\d+",
        compact,
    ))


def _protected_note_fingerprints(drawing_model):
    """Capture program and user notes that must survive a sheet-format switch."""
    records = []
    for note, owner_view, owner_type in _iter_drawing_notes(drawing_model):
        evidence = _note_evidence(note)
        name = str(evidence.get("persistent_name") or "")
        if _is_template_definition_note_name(name):
            continue
        records.append({
            **evidence,
            "owner_view": owner_view,
            "owner_view_type": owner_type,
            "program_owned": name.startswith("CAD_TITLE__"),
        })
    return records


def _protected_note_identity(record):
    position = tuple(
        round(float(value), 9)
        for value in (record.get("position_m") or [])
    )
    return (
        str(record.get("persistent_name") or ""),
        str(record.get("text") or "").replace("\r\n", "\n").replace("\r", "\n"),
        _normalise_property_expression(record.get("property_linked_text")),
        position,
    )


def setup_current_sheet(drawing_model, template_candidates, *, paper_size=None, projection="first_angle", require_gbt=True) -> dict:
    """@brief 按 DrawingSpec 配置当前图纸页并回读基本配置证据。"""
    paper_size = _normalise_paper_size(paper_size)
    projection = str(projection).lower()
    if projection not in {"first_angle", "third_angle"}:
        raise ValueError("projection 必须是 first_angle 或 third_angle")
    if not template_candidates or paper_size is None:
        return _preserve_default_sheet(drawing_model, projection, paper_size)
    selection = select_drawing_template(template_candidates, paper_size=paper_size, require_gbt=require_gbt)
    if not selection["selected"]:
        return {**selection, "status": "blocked", "stage": "preflight", "configured": False, "retryable": True}
    sheet = _safe_member(drawing_model, "GetCurrentSheet")
    sheet_name = str(_safe_member(sheet, "GetName", default="") or "")
    if not sheet_name:
        return {**selection, "status": "blocked", "stage": "preflight", "configured": False, "error_code": "DRAWING_CURRENT_SHEET_MISSING"}
    notes_before = _title_note_fingerprints(drawing_model)
    protected_notes_before = _protected_note_fingerprints(drawing_model)
    program_notes_before = {
        _program_note_identity(record)
        for record in notes_before
        if record.get("program_owned")
    }
    template_notes_before = {
        _fingerprint_key(record)
        for record in notes_before
        if not record.get("program_owned")
    }
    try:
        configured = bool(get_com_member(
            drawing_model,
            "SetupSheet6",
            sheet_name,
            PAPER_SIZES[paper_size]["code"],
            SW_DWG_TEMPLATE_CUSTOM,
            1.0,
            1.0,
            projection == "first_angle",
            selection["selected"],
            0.0,
            0.0,
            "",
            True,
            0.0,
            0.0,
            0.0,
            0.0,
            0,
            0,
        ))
    except Exception as exc:
        return {**selection, "status": "failed", "stage": "create", "configured": False, "projection": projection, "error_code": "DRAWING_SHEET_SETUP_FAILED", "error": str(exc)}
    try:
        _safe_member(drawing_model, "ForceRebuild3", False)
        actual_properties = _current_sheet_properties(sheet)
    except Exception as exc:
        return {
            **selection,
            "status": "failed",
            "stage": "verify",
            "configured": False,
            "projection": projection,
            "error_code": "DRAWING_SHEET_SETUP_READBACK_FAILED",
            "error": str(exc),
        }
    actual_paper_size = _paper_size_from_dimensions(actual_properties[5], actual_properties[6])
    actual_template_name = str(_safe_member(sheet, "GetTemplateName", default="") or "")
    expected_template_name = str(selection["selected"])
    template_matches = (
        os.path.normcase(os.path.abspath(actual_template_name))
        == os.path.normcase(os.path.abspath(expected_template_name))
    )
    expected_first_angle = projection == "first_angle"
    if (
        not configured
        or actual_paper_size != paper_size
        or bool(actual_properties[4]) != expected_first_angle
        or not template_matches
    ):
        return {
            **selection,
            "status": "failed",
            "stage": "verify",
            "configured": bool(configured),
            "paper_size": paper_size,
            "actual_paper_size": actual_paper_size,
            "actual_template_path": actual_template_name,
            "expected_template_path": expected_template_name,
            "actual_projection": "first_angle" if bool(actual_properties[4]) else "third_angle",
            "projection": projection,
            "sheet_name": sheet_name,
            "sheet_size_m": [actual_properties[5], actual_properties[6]],
            "remove_modified_notes": True,
            "error_code": "DRAWING_SHEET_SIZE_MISMATCH",
        }
    notes_after = _title_note_fingerprints(drawing_model)
    protected_notes_after = _protected_note_fingerprints(drawing_model)
    program_notes_after = {
        _program_note_identity(record)
        for record in notes_after
        if record.get("program_owned")
    }
    template_notes_after = {
        _fingerprint_key(record)
        for record in notes_after
        if not record.get("program_owned")
    }
    lost_program_notes = program_notes_before - program_notes_after
    protected_notes_before_identities = {
        _protected_note_identity(record)
        for record in protected_notes_before
    }
    protected_notes_after_identities = {
        _protected_note_identity(record)
        for record in protected_notes_after
    }
    lost_protected_notes = (
        protected_notes_before_identities
        - protected_notes_after_identities
    )
    lost_user_notes = {
        item
        for item in lost_protected_notes
        if not str(item[0] or "").startswith("CAD_TITLE__")
    }
    residual_template_notes = template_notes_before & template_notes_after
    if lost_program_notes:
        return {
            **selection,
            "status": "failed",
            "stage": "verify",
            "configured": True,
            "paper_size": paper_size,
            "actual_paper_size": actual_paper_size,
            "actual_template_path": actual_template_name,
            "expected_template_path": expected_template_name,
            "projection": projection,
            "sheet_name": sheet_name,
            "sheet_size_m": [actual_properties[5], actual_properties[6]],
            "remove_modified_notes": True,
            "lost_program_notes": [list(item) for item in lost_program_notes],
            "error_code": "DRAWING_SHEET_USER_NOTES_LOST",
            "manual_review_required": True,
        }
    if lost_user_notes:
        return {
            **selection,
            "status": "failed",
            "stage": "verify",
            "configured": True,
            "paper_size": paper_size,
            "actual_paper_size": actual_paper_size,
            "actual_template_path": actual_template_name,
            "expected_template_path": expected_template_name,
            "projection": projection,
            "sheet_name": sheet_name,
            "sheet_size_m": [actual_properties[5], actual_properties[6]],
            "remove_modified_notes": True,
            "lost_user_notes": [list(item) for item in lost_user_notes],
            "error_code": "DRAWING_SHEET_USER_NOTES_LOST",
            "manual_review_required": True,
        }
    if residual_template_notes:
        return {
            **selection,
            "status": "review_required",
            "stage": "verify",
            "configured": True,
            "paper_size": paper_size,
            "actual_paper_size": actual_paper_size,
            "actual_template_path": actual_template_name,
            "expected_template_path": expected_template_name,
            "projection": projection,
            "sheet_name": sheet_name,
            "sheet_size_m": [actual_properties[5], actual_properties[6]],
            "remove_modified_notes": True,
            "residual_template_notes": [list(item) for item in residual_template_notes],
            "error_code": "DRAWING_SHEET_OLD_TITLE_BLOCK_REMAINS",
            "manual_review_required": True,
        }
    return {
        **selection,
        "status": "pass",
        "stage": "create",
        "configured": True,
        "paper_size": paper_size,
        "actual_paper_size": actual_paper_size,
        "actual_template_path": actual_template_name,
        "expected_template_path": expected_template_name,
        "projection": projection,
        "sheet_name": sheet_name,
        "sheet_size_m": [actual_properties[5], actual_properties[6]],
        "remove_modified_notes": True,
        "program_notes_preserved": len(program_notes_before),
        "user_notes_preserved": sum(
            1
            for record in protected_notes_before
            if not record.get("program_owned")
        ),
        "residual_template_note_count": 0,
        "error_code": None,
        "manual_review_required": True,
    }


def validate_generic_drawing_generation(spec) -> dict:
    """@brief 在修改文档前声明通用生成器无法可靠执行的 DrawingSpec 字段。"""
    issues = []
    views = dict(spec.get("views") or {})
    standard_views = {name for name in ("front", "top", "right") if name in views}
    if standard_views != {"front", "top", "right"}:
        issues.append({
            "code": "DRAWING_STANDARD_VIEW_SET_UNSUPPORTED",
            "path": "views",
            "message": "通用生成器必须同时生成 front/top/right 三视图，可选追加 isometric 轴测视图。",
        })
    unsupported_views = [name for name in ("bottom", "left") if name in views]
    unsupported_views.extend(name for name in ("sections", "details") if views.get(name))
    if unsupported_views:
        issues.append({
            "code": "DRAWING_REQUESTED_VIEWS_UNSUPPORTED",
            "path": "views",
            "views": unsupported_views,
            "message": "通用生成器尚不能创建请求的仰视、左视、剖视或局部视图。",
        })
    from scripts.sw_drawing_native import validate_native_requests, _position
    configured_views = [name for name in ("front", "top", "right", "isometric") if views.get(name)
                        and (set(views[name]) != {"positionMm"} or not _position(views[name]["positionMm"]))]
    if configured_views:
        issues.append({
            "code": "DRAWING_VIEW_OPTIONS_UNSUPPORTED",
            "path": "views",
            "views": configured_views,
            "message": "标准视图对象仅支持显式 positionMm，尚不支持自定义名称或方向。",
        })
    issues.extend(validate_native_requests(spec))
    professional_annotations = dict(spec.get("professionalAnnotations") or {})
    unsupported_professional_fields = sorted(
        name for name, values in professional_annotations.items()
        if name not in {"centerMarks", "datums", "geometricTolerances"} and values
    )
    if unsupported_professional_fields:
        issues.append({
            "code": "DRAWING_PROFESSIONAL_ANNOTATIONS_UNSUPPORTED",
            "path": "professionalAnnotations",
            "fields": unsupported_professional_fields,
            "message": "通用生成器支持中心标记、原生基准和 GD&T；请求的其他专业标注仍须使用专项脚本。",
        })
    title_block = dict(spec.get("titleBlock") or {})
    title_fields = sorted(set(title_block) - TITLE_BLOCK_CONTROL_FIELDS - set(TITLE_BLOCK_FIELDS))
    if title_fields:
        issues.append({
            "code": "DRAWING_TITLE_BLOCK_FIELDS_UNSUPPORTED",
            "path": "titleBlock",
            "fields": title_fields,
            "message": "标题栏仅支持 drawingNumber、name、material、scale、date 及 propertyMap/fieldPositionsMm。",
        })
    if title_block.get("required"):
        if str(title_block.get("format") or "GB_T").upper() not in {"GB_T", "ISO"}:
            issues.append({
                "code": "DRAWING_TITLE_BLOCK_FORMAT_UNSUPPORTED",
                "path": "titleBlock.format",
                "message": "标题栏格式必须是 GB_T 或 ISO。",
            })
        property_map = title_block.get("propertyMap") or {}
        if not isinstance(property_map, dict) or any(
            field not in TITLE_BLOCK_FIELDS or not isinstance(value, (str, list, tuple))
            for field, value in property_map.items()
        ):
            issues.append({
                "code": "DRAWING_TITLE_BLOCK_PROPERTY_MAP_INVALID",
                "path": "titleBlock.propertyMap",
                "message": "propertyMap 只能把受支持字段映射到一个或多个自定义属性名。",
            })
        positions = title_block.get("fieldPositionsMm") or {}
        if not isinstance(positions, dict) or any(field not in TITLE_BLOCK_FIELDS for field in positions):
            issues.append({
                "code": "DRAWING_TITLE_BLOCK_POSITION_INVALID",
                "path": "titleBlock.fieldPositionsMm",
                "message": "fieldPositionsMm 只能包含受支持标题栏字段。",
            })
        for name in ("linkToModelProperties", "overwriteExistingFields", "manualOverride"):
            if name in title_block and not isinstance(title_block[name], bool):
                issues.append({
                    "code": "DRAWING_TITLE_BLOCK_CONTROL_INVALID",
                    "path": f"titleBlock.{name}",
                    "message": f"{name} 必须是布尔值。",
                })
    if spec.get("sheetMetal"):
        issues.append({
            "code": "DRAWING_SHEET_METAL_OPTIONS_UNSUPPORTED",
            "path": "sheetMetal",
            "message": "通用生成器尚不能执行展开图、折弯表或钣金专用选项。",
        })
    return {
        "status": "blocked" if issues else "pass",
        "stage": "capability_preflight",
        "issues": issues,
        "error_code": "DRAWING_SPEC_CAPABILITY_UNSUPPORTED" if issues else None,
        "manual_review_required": bool(issues),
    }


def generate_drawing_from_spec(
    drawing_model,
    spec,
    source_model_path,
    template_candidates=None,
    *,
    sw_app=None,
    source_model=None,
    initial_save_path=None,
    evidence_context=None,
) -> dict:
    """@brief 按已校验 DrawingSpec 创建标准工程图结构和制造标注入口。"""
    capability = validate_generic_drawing_generation(spec)
    if capability["status"] != "pass":
        return capability
    professional_annotations_requested = dict(spec.get("professionalAnnotations") or {})
    gdt_requested = any(professional_annotations_requested.get(key) for key in ("datums", "geometricTolerances"))
    native_requested = gdt_requested or bool(spec.get("requiredDimensions"))
    if native_requested:
        from scripts.drawing_spec import validate_drawing_spec
        validation = validate_drawing_spec(spec)
        if validation["status"] == "blocked":
            return validation
        revision = str(_safe_member(sw_app, "RevisionNumber", default="") or "")
        if initial_save_path is None or evidence_context is None or (gdt_requested and revision.split(".")[0] != "34"):
            return {"status": "blocked", "stage": "capability_preflight", "error_code": "DRAWING_NATIVE_CONTEXT_REQUIRED",
                    "message": "原生尺寸/GD&T 必须通过受控出图包入口执行并完成初次保存与持久关联核验；原生 GD&T 当前限 SW2026。", "manual_review_required": True}
    requested_paper_size = _normalise_paper_size(spec.get("paperSize"))
    projection = str(spec.get("projection", "first_angle")).lower()
    model_size_mm = spec.get("modelSizeMm")
    if not isinstance(model_size_mm, (list, tuple)) or len(model_size_mm) != 3:
        return {
            "status": "blocked",
            "stage": "planning",
            "error_code": "DRAWING_MODEL_SIZE_MISSING",
            "message": "DrawingSpec 必须提供 modelSizeMm，避免凭空推断工程图比例和视图布局。",
            "manual_review_required": True,
        }
    candidates = list(template_candidates or spec.get("templateCandidates") or [])
    sheet_setup = setup_current_sheet(
        drawing_model,
        candidates,
        paper_size=requested_paper_size,
        projection=projection,
        require_gbt=spec.get("standard") == "GB_T",
    )
    if sheet_setup.get("status") != "pass":
        return {"status": sheet_setup.get("status", "blocked"), "stage": "sheet", "sheetSetup": sheet_setup, "error_code": sheet_setup.get("error_code"), "manual_review_required": True}
    paper_size = sheet_setup.get("paper_size")
    if paper_size not in PAPER_SIZES:
        return {
            "status": "blocked",
            "stage": "sheet",
            "sheetSetup": sheet_setup,
            "error_code": "DRAWING_TEMPLATE_SIZE_UNAVAILABLE",
            "manual_review_required": True,
        }
    model_size_m = tuple(float(value) / 1000.0 for value in model_size_mm)
    layout = plan_standard_view_layout(
        model_size_m,
        paper_size=paper_size,
        projection=projection,
        requested_scale=spec.get("scale"),
        gap_m=0.055 if spec.get("requiredDimensions") else 0.018,
        sheet_size_m=sheet_setup.get("sheet_size_m"),
        include_isometric="isometric" in (spec.get("views") or {}),
    )
    if layout.get("status") != "pass":
        return {"status": "blocked", "stage": "layout", "sheetSetup": sheet_setup, "layout": layout, "error_code": layout.get("error_code"), "manual_review_required": True}
    views = create_adaptive_standard_views(
        drawing_model,
        str(source_model_path),
        layout,
        sw_app=sw_app,
    )
    if views.get("status") != "pass":
        return {"status": "failed", "stage": "views", "sheetSetup": sheet_setup, "layout": layout, "views": views, "error_code": views.get("error_code"), "manual_review_required": True}
    from scripts.sw_drawing_native import map_views, create_dimensions, create_professional_annotations
    requested_view_names = set(spec.get("views") or {})
    view_objects = map_views(drawing_model, views) if native_requested or requested_view_names else {}
    for key, view in view_objects.items():
        if (spec.get("views", {}).get(key) or {}).get("positionMm"):
            position = [value / 1000 for value in spec["views"][key]["positionMm"]]
            view.Position = VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, position)
            if any(abs(actual - intended) > 1e-7 for actual, intended in zip(get_com_member(view, "Position")[:2], position)):
                raise RuntimeError("标准视图位置设置未生效")
            for records in (layout["views"], views["views"]):
                for record in records:
                    if _normalise_orientation(record["name"]) == key:
                        record.update(center=position, actual_center=position, explicit_position=True)
    title_block_request = dict(spec.get("titleBlock") or {})
    title_block_result = add_title_block_fields(
        drawing_model,
        title_block_request,
        layout.get("title_block_box"),
        paper_size=paper_size,
    )
    if title_block_result.get("status") == "failed":
        return {
            "status": "failed",
            "stage": "title_block",
            "titleBlock": title_block_result,
            "sheetSetup": sheet_setup,
            "layout": layout,
            "views": views,
            "error_code": title_block_result.get("error_code"),
            "manual_review_required": True,
        }
    if native_requested:
        sheet = get_com_member(drawing_model, "GetCurrentSheet")
        numerator, denominator = layout["scale_ratio"]
        if not get_com_member(sheet, "SetScale", float(numerator), float(denominator), False, False):
            raise RuntimeError("图纸比例设置失败")
        properties = get_com_member(sheet, "GetProperties2")
        if len(properties) != 8 or abs(properties[2] / properties[3] - layout["scale"]) > 1e-8:
            raise RuntimeError("图纸比例回读与计划不一致")
    if initial_save_path is not None:
        try:
            from scripts.sw_connect import save_document
            if not save_document(drawing_model, str(initial_save_path)):
                raise RuntimeError("工程图初次保存失败")
        except Exception as error:
            return {"status": "failed", "stage": "initial_save", "error_code": "DRAWING_INITIAL_SAVE_FAILED", "message": str(error), "manual_review_required": True}
    professional_annotations = dict(spec.get("professionalAnnotations") or {})
    center_marks = auto_insert_center_marks(drawing_model, professional_annotations.get("centerMarks"))
    if center_marks.get("status") == "failed":
        save_required = center_marks.get("error_code") == "DRAWING_CENTER_MARK_DRAWING_SAVE_REQUIRED"
        return {
            "status": "blocked" if save_required else "failed",
            "stage": "professional_annotations",
            "professionalAnnotations": {"centerMarks": center_marks},
            "sheetSetup": sheet_setup,
            "layout": layout,
            "views": views,
            "error_code": center_marks.get("error_code"),
            "retryable": bool(center_marks.get("retryable")),
            "manual_review_required": True,
        }
    dimensions = create_dimensions(
        drawing_model,
        spec["requiredDimensions"],
        view_objects,
        source_model=source_model,
    ) if spec.get("requiredDimensions") else {}
    dimension_result = bool(dimensions) or (insert_dimensions(drawing_model) if spec.get("insertModelDimensions", True) else False)
    deduplication = deduplicate_drawing_dimensions(drawing_model) if dimension_result else {
        "status": "not_requested",
        "removed_count": 0,
        "error_code": None,
        "manual_review_required": False,
    }
    arrangement = {"status": "pass", "method": "explicit_positions"} if dimensions else auto_arrange_drawing_dimensions(drawing_model) if dimension_result else {"status": "review_required", "error_code": "DRAWING_DIMENSIONS_NOT_REQUESTED"}
    native_records = []
    if any(professional_annotations.get(key) for key in ("datums", "geometricTolerances")):
        paper = layout["sheet"]
        native_records = create_professional_annotations(drawing_model, professional_annotations, views, sw_app, dimensions, (paper["width_m"], paper["height_m"]))
    if evidence_context is not None:
        evidence_context.update(dimensions=dimensions, native_records=native_records)
    bom_spec = spec.get("bom") or {}
    bom_requested = bool(bom_spec.get("required")) or spec.get("documentType") == "assembly"
    bom_result = {"requested": bom_requested, "created": False, "status": "not_requested"}
    balloon_result = {"requested": False, "status": "not_requested"}
    if bom_requested:
        template_path = str(bom_spec.get("templatePath") or "")
        if not template_path or not Path(template_path).expanduser().is_file():
            return {"status": "blocked", "stage": "bom", "error_code": "DRAWING_BOM_TEMPLATE_MISSING", "message": "BOM 已要求但模板不存在，不能伪造表格交付。", "sheetSetup": sheet_setup, "layout": layout, "views": views, "manual_review_required": True}
        position = bom_spec.get("positionMm") or [250.0, 45.0]
        bom_table = insert_bom_table(
            drawing_model,
            template_path,
            float(position[0]) / 1000.0,
            float(position[1]) / 1000.0,
            int(bom_spec.get("bomType", 1)),
            str(bom_spec.get("configuration", "")),
            include_thickness=bool(bom_spec.get("includeThickness", False)),
            include_surface_treatment=bool(
                bom_spec.get("includeSurfaceTreatment", False)
            ),
        )
        bom_result = {"requested": True, "created": bom_table is not None, "status": "pass" if bom_table is not None else "failed", "template_path": template_path, "position_mm": position, "error_code": None if bom_table is not None else "DRAWING_BOM_INSERT_FAILED"}
        if bom_table is None:
            return {"status": "failed", "stage": "bom", "bom": bom_result, "sheetSetup": sheet_setup, "layout": layout, "views": views, "manual_review_required": True}
        balloon_spec = bom_spec.get("balloons") or {}
        if balloon_spec.get("required"):
            balloon_result = add_bom_balloons(
                drawing_model,
                view_name=balloon_spec.get("view"),
                insert_magnetic_line=bool(balloon_spec.get("insertMagneticLine", False)),
            )
            balloon_result["requested"] = True
            if balloon_result.get("status") != "pass":
                return {
                    "status": "failed",
                    "stage": "bom_balloons",
                    "bom": bom_result,
                    "balloons": balloon_result,
                    "sheetSetup": sheet_setup,
                    "layout": layout,
                    "views": views,
                    "error_code": balloon_result.get("error_code"),
                    "manual_review_required": True,
                }
    notes = []
    for index, note_text in enumerate(spec.get("notes") or []):
        note_result = add_note(drawing_model, 0.02, 0.02 + index * 0.006, str(note_text))
        notes.append(note_result)
        if note_result.get("status") != "pass":
            return {
                "status": "failed",
                "stage": "notes",
                "error_code": note_result.get("error_code") or "DRAWING_NOTE_COM_EVIDENCE_MISSING",
                "notes": notes,
                "sheetSetup": sheet_setup,
                "layout": layout,
                "views": views,
                "manual_review_required": True,
            }
    structure = inspect_drawing_structure(
        drawing_model,
        paper_size_hint=paper_size,
        title_block_box=layout.get("title_block_box"),
    )
    status = "pass" if (
        structure.get("status") == "pass"
        and dimension_result
        and title_block_result.get("status") != "review_required"
        and not deduplication.get("unresolved")
    ) else "review_required"
    return {
        "status": status,
        "stage": "review",
        "source_model": str(source_model_path),
        "standard": spec.get("standard"),
        "projection": projection,
        "sheetSetup": sheet_setup,
        "layout": layout,
        "views": views,
        "titleBlock": title_block_result,
        "professionalAnnotations": {"centerMarks": center_marks},
        "dimensions": {
            "inserted": bool(dimension_result),
            "arrangement": arrangement,
            "deduplication": deduplication,
        },
        "bom": bom_result,
        "balloons": balloon_result,
        "notes": notes,
        "structure": structure,
        "manual_review_required": True,
        "error_code": None if status == "pass" else "DRAWING_GENERATION_REVIEW_REQUIRED",
    }


def generate_drawing_package(
    spec_source,
    output_dir,
    drawing_filename="drawing.slddrw",
    *,
    overwrite=False,
    drawing_template_path=None,
):
    """完整受控入口；CLI、Skill 和现有 MCP 出图工具共用。"""
    from scripts.sw_drawing_package import generate_package
    return generate_package(
        spec_source,
        output_dir,
        drawing_filename,
        overwrite=overwrite,
        drawing_template_path=drawing_template_path,
    )
