"""@brief SolidWorks 复杂孔、复合孔和半圆端槽的稳定草图切除封装。"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Iterable, Sequence

try:
    from .sw_connect import get_com_member
    from .sw_part import (
        _select_com_object,
        end_sketch,
        extrude_cut,
        sketch,
        sketch_circle,
        sketch_slot,
    )
except ImportError:
    from sw_connect import get_com_member
    from sw_part import (
        _select_com_object,
        end_sketch,
        extrude_cut,
        sketch,
        sketch_circle,
        sketch_slot,
    )


@dataclass(frozen=True)
class HoleFeatureEvidence:
    """@brief 创建侧参数证据；长度统一使用米。"""

    feature_kind: str
    center_m: tuple[float, float]
    diameter_m: float
    depth_m: float | None
    through: bool
    plane_name: str
    feature_names: tuple[str, ...]
    counterbore_diameter_m: float | None = None
    counterbore_depth_m: float | None = None
    countersink_diameter_m: float | None = None
    countersink_angle_deg: float | None = None
    reverse_direction: bool | None = None
    both_directions: bool | None = None
    face_point_m: tuple[float, float, float] | None = None

    def to_dict(self) -> dict:
        """@brief 返回可序列化证据，并附加毫米值。"""
        value = asdict(self)
        value["center_mm"] = [round(item * 1000.0, 6) for item in self.center_m]
        for key in (
            "diameter_m",
            "depth_m",
            "counterbore_diameter_m",
            "counterbore_depth_m",
            "countersink_diameter_m",
        ):
            if value.get(key) is not None:
                value[key.replace("_m", "_mm")] = round(value[key] * 1000.0, 6)
        if value.get("face_point_m") is not None:
            value["face_point_mm"] = [
                round(float(item) * 1000.0, 6) for item in value["face_point_m"]
            ]
        return value


def _positive(name: str, value: float) -> float:
    """@brief 校验正有限长度。"""
    number = float(value)
    if not math.isfinite(number) or number <= 0.0:
        raise ValueError(f"{name} 必须是正有限值，单位为米")
    return number


def _center(center: Sequence[float]) -> tuple[float, float]:
    """@brief 校验二维孔中心坐标。"""
    if len(center) != 2:
        raise ValueError("center 必须包含两个草图平面坐标，单位为米")
    values = (float(center[0]), float(center[1]))
    if not all(math.isfinite(value) for value in values):
        raise ValueError("center 必须是有限值")
    return values


def _feature_name(feature, fallback: str) -> str:
    """@brief 设置并回读特征名称；COM 不允许改名时返回当前名称或兜底名。"""
    if feature is None:
        raise RuntimeError(f"SolidWorks 未创建特征: {fallback}")
    try:
        feature.Name = fallback
    except Exception:
        pass
    try:
        return str(feature.Name or fallback)
    except Exception:
        return fallback


def find_planar_face_at_point(
    model,
    point: Sequence[float],
    tolerance: float,
):
    """Find the planar solid face coincident with a model-space point."""
    if len(point) != 3:
        raise ValueError("face_point must contain three model-space coordinates in metres")
    values = tuple(float(item) for item in point)
    if not all(math.isfinite(item) for item in values):
        raise ValueError("face_point must contain finite coordinates")

    candidates = []
    for body_index, body in enumerate(get_com_member(model, "GetBodies2", 0, False) or []):
        for face_index, face in enumerate(get_com_member(body, "GetFaces") or []):
            try:
                surface = get_com_member(face, "GetSurface")
                if surface is None or not bool(get_com_member(surface, "IsPlane")):
                    continue
                closest = list(get_com_member(face, "GetClosestPointOn", *values) or [])
                if len(closest) < 3:
                    continue
                distance = math.dist(values, closest[:3])
                candidates.append((distance, body_index, face_index, face, closest))
            except Exception:
                continue

    if not candidates:
        raise RuntimeError("未找到可用于草图的可选平面实体面")
    candidates.sort(key=lambda item: item[0])
    distance, body_index, face_index, face, closest = candidates[0]
    if distance > float(tolerance):
        raise RuntimeError(
            "指定点不在实体面上，最近平面面距离 "
            f"{distance * 1000.0:.6f} mm，超过容差 {float(tolerance) * 1000.0:.6f} mm"
        )
    return {
        "face": face,
        "body_index": body_index,
        "face_index": face_index,
        "point_m": tuple(values),
        "closest_point_m": tuple(float(item) for item in closest[:3]),
        "distance_m": distance,
    }


def _circle_cut(
    model,
    plane_name: str,
    center: tuple[float, float],
    diameter: float,
    depth: float,
    feature_name: str,
    *,
    reverse_direction: bool = True,
    both_directions: bool = False,
    face_point: Sequence[float] | None = None,
    face_tolerance: float = 1e-5,
):
    """@brief 创建单个圆形草图并执行定深或贯穿切除。"""
    if face_point is None:
        with sketch(model, plane_name) as sketch_name:
            segment = sketch_circle(model, center[0], center[1], diameter / 2.0)
            if segment is None:
                raise RuntimeError(f"创建圆草图失败: {feature_name}")
    else:
        selected = find_planar_face_at_point(model, face_point, face_tolerance)
        model.ClearSelection2(True)
        if not _select_com_object(selected["face"], append=False, mark=0):
            raise RuntimeError(f"选择实体面失败: {feature_name}")
        model.SketchManager.InsertSketch(True)
        try:
            segment = sketch_circle(model, center[0], center[1], diameter / 2.0)
        finally:
            sketch_name = end_sketch(model)
        if segment is None:
            raise RuntimeError(f"创建圆草图失败: {feature_name}")

    feature = extrude_cut(
        model,
        sketch_name,
        depth,
        direction=bool(reverse_direction),
        both_directions=bool(both_directions),
    )
    return _feature_name(feature, feature_name)


def _entry_point_3d(plane_name: str, center: tuple[float, float]) -> tuple[float, float, float]:
    """@brief 把标准基准面的二维坐标映射到入口平面三维点。"""
    normalized = str(plane_name).strip().lower()
    if "top" in normalized or "上视" in normalized:
        return center[0], 0.0, center[1]
    if "right" in normalized or "右视" in normalized:
        return 0.0, center[0], center[1]
    return center[0], center[1], 0.0


def _find_hole_entry_edge(
    model,
    plane_name: str,
    center: tuple[float, float],
    radius: float,
    tolerance=1e-6,
    entry_point=None,
):
    """@brief 按圆心和半径寻找通孔在草图基准面一侧的圆边。"""
    target = tuple(entry_point) if entry_point is not None else _entry_point_3d(plane_name, center)
    candidates = []
    for body in get_com_member(model, "GetBodies2", 0, False) or []:
        for face in get_com_member(body, "GetFaces") or []:
            for edge in get_com_member(face, "GetEdges") or []:
                try:
                    curve = get_com_member(edge, "GetCurve")
                    if curve is None or not bool(get_com_member(curve, "IsCircle")):
                        continue
                    params = list(get_com_member(curve, "CircleParams") or [])
                    if len(params) < 7 or abs(float(params[6]) - radius) > tolerance:
                        continue
                    distance = math.dist([float(value) for value in params[:3]], target)
                    candidates.append((distance, edge))
                except Exception:
                    continue
    if not candidates:
        raise RuntimeError("无法按圆心和半径找到沉头孔入口圆边")
    candidates.sort(key=lambda item: item[0])
    if candidates[0][0] > max(tolerance * 10.0, 1e-5):
        raise RuntimeError(f"找到的圆边偏离沉头入口位置: {candidates[0][0] * 1000.0:.3f} mm")
    return candidates[0][1]


def _chamfer_hole_entry(
    model,
    plane_name,
    center,
    hole_diameter,
    countersink_diameter,
    half_angle_rad,
    feature_name,
    entry_point=None,
):
    """@brief 选择通孔入口圆边并创建角度/距离倒角。"""
    edge = _find_hole_entry_edge(
        model,
        plane_name,
        center,
        hole_diameter / 2.0,
        entry_point=entry_point,
    )
    model.ClearSelection2(True)
    if not _select_com_object(edge, append=False, mark=0):
        raise RuntimeError(f"选择沉头孔入口圆边失败: {feature_name}")
    radial_distance = (countersink_diameter - hole_diameter) / 2.0
    feature = model.FeatureManager.InsertFeatureChamfer(
        4, 1, radial_distance, half_angle_rad, 0.0, 0.0, 0.0, 0.0
    )
    model.ClearSelection2(True)
    return _feature_name(feature, feature_name)


def create_blind_hole(
    model,
    center,
    diameter,
    depth,
    plane_name="Front Plane",
    name="盲孔",
    reverse_direction=True,
    both_directions=False,
    face_point=None,
    face_tolerance=1e-5,
) -> dict:
    """@brief 创建定深盲孔，并返回创建参数证据。"""
    center = _center(center)
    diameter = _positive("diameter", diameter)
    depth = _positive("depth", depth)
    feature_name = _circle_cut(
        model,
        plane_name,
        center,
        diameter,
        depth,
        name,
        reverse_direction=reverse_direction,
        both_directions=both_directions,
        face_point=face_point,
        face_tolerance=face_tolerance,
    )
    return HoleFeatureEvidence(
        "blind",
        center,
        diameter,
        depth,
        False,
        plane_name,
        (feature_name,),
        reverse_direction=bool(reverse_direction),
        both_directions=bool(both_directions),
        face_point_m=tuple(face_point) if face_point is not None else None,
    ).to_dict()


def create_through_hole(
    model,
    center,
    diameter,
    plane_name="Front Plane",
    name="通孔",
    reverse_direction=False,
    both_directions=True,
    face_point=None,
    face_tolerance=1e-5,
) -> dict:
    """@brief 创建完全贯穿圆孔，并返回创建参数证据。"""
    center = _center(center)
    diameter = _positive("diameter", diameter)
    feature_name = _circle_cut(
        model,
        plane_name,
        center,
        diameter,
        0.0,
        name,
        reverse_direction=reverse_direction,
        both_directions=both_directions,
        face_point=face_point,
        face_tolerance=face_tolerance,
    )
    return HoleFeatureEvidence(
        "through",
        center,
        diameter,
        None,
        True,
        plane_name,
        (feature_name,),
        reverse_direction=bool(reverse_direction),
        both_directions=bool(both_directions),
        face_point_m=tuple(face_point) if face_point is not None else None,
    ).to_dict()


def create_counterbore_hole(
    model,
    center,
    hole_diameter,
    counterbore_diameter,
    counterbore_depth,
    plane_name="Front Plane",
    name="沉孔",
    reverse_direction=True,
    through_both_directions=True,
    face_point=None,
    face_tolerance=1e-5,
) -> dict:
    """@brief 创建通孔加同轴圆柱沉孔的两级复合孔。"""
    center = _center(center)
    hole_diameter = _positive("hole_diameter", hole_diameter)
    counterbore_diameter = _positive("counterbore_diameter", counterbore_diameter)
    counterbore_depth = _positive("counterbore_depth", counterbore_depth)
    if counterbore_diameter <= hole_diameter:
        raise ValueError("counterbore_diameter 必须大于 hole_diameter")
    through_name = _circle_cut(
        model,
        plane_name,
        center,
        hole_diameter,
        0.0,
        f"{name}_通孔",
        reverse_direction=reverse_direction,
        both_directions=through_both_directions,
        face_point=face_point,
        face_tolerance=face_tolerance,
    )
    recess_name = _circle_cut(
        model,
        plane_name,
        center,
        counterbore_diameter,
        counterbore_depth,
        f"{name}_沉孔",
        reverse_direction=reverse_direction,
        both_directions=False,
        face_point=face_point,
        face_tolerance=face_tolerance,
    )
    return HoleFeatureEvidence(
        "counterbore", center, hole_diameter, None, True, plane_name, (through_name, recess_name),
        counterbore_diameter_m=counterbore_diameter,
        counterbore_depth_m=counterbore_depth,
        reverse_direction=bool(reverse_direction),
        both_directions=bool(through_both_directions),
        face_point_m=tuple(face_point) if face_point is not None else None,
    ).to_dict()


def create_countersink_hole(
    model,
    center,
    hole_diameter,
    countersink_diameter,
    included_angle_deg=90.0,
    plane_name="Front Plane",
    name="沉头孔",
    reverse_direction=True,
    through_both_directions=True,
    face_point=None,
    face_tolerance=1e-5,
) -> dict:
    """@brief 创建通孔加锥形沉头；角度为沉头包含角。"""
    center = _center(center)
    hole_diameter = _positive("hole_diameter", hole_diameter)
    countersink_diameter = _positive("countersink_diameter", countersink_diameter)
    angle = float(included_angle_deg)
    if countersink_diameter <= hole_diameter:
        raise ValueError("countersink_diameter 必须大于 hole_diameter")
    if not math.isfinite(angle) or not 10.0 <= angle < 170.0:
        raise ValueError("included_angle_deg 必须在 [10, 170) 范围内")
    half_angle = math.radians(angle / 2.0)
    through_name = _circle_cut(
        model,
        plane_name,
        center,
        hole_diameter,
        0.0,
        f"{name}_通孔",
        reverse_direction=reverse_direction,
        both_directions=through_both_directions,
        face_point=face_point,
        face_tolerance=face_tolerance,
    )
    sink_name = _chamfer_hole_entry(
        model,
        plane_name,
        center,
        hole_diameter,
        countersink_diameter,
        half_angle,
        f"{name}_锥面",
        entry_point=tuple(face_point) if face_point is not None else None,
    )
    return HoleFeatureEvidence(
        "countersink", center, hole_diameter, None, True, plane_name, (through_name, sink_name),
        countersink_diameter_m=countersink_diameter,
        countersink_angle_deg=angle,
        reverse_direction=bool(reverse_direction),
        both_directions=bool(through_both_directions),
        face_point_m=tuple(face_point) if face_point is not None else None,
    ).to_dict()


def create_semicircular_slot(
    model,
    start,
    end,
    width,
    depth=0.0,
    plane_name="Front Plane",
    name="半圆端槽",
    reverse_direction=True,
    both_directions=None,
    face_point=None,
    face_tolerance=1e-5,
) -> dict:
    """@brief 创建两端为半圆的直槽；depth=0 表示贯穿。"""
    start = _center(start)
    end = _center(end)
    width = _positive("width", width)
    depth = 0.0 if float(depth) == 0.0 else _positive("depth", depth)
    if math.dist(start, end) <= 1e-12:
        raise ValueError("槽起点和终点不能重合")
    if both_directions is None:
        both_directions = depth == 0.0
    if face_point is None:
        with sketch(model, plane_name) as sketch_name:
            segments = sketch_slot(model, start[0], start[1], end[0], end[1], width / 2.0)
            if segments is None:
                raise RuntimeError(f"创建半圆端槽草图失败: {name}")
    else:
        selected = find_planar_face_at_point(model, face_point, face_tolerance)
        model.ClearSelection2(True)
        if not _select_com_object(selected["face"], append=False, mark=0):
            raise RuntimeError(f"选择实体面失败: {name}")
        model.SketchManager.InsertSketch(True)
        try:
            segments = sketch_slot(model, start[0], start[1], end[0], end[1], width / 2.0)
        finally:
            sketch_name = end_sketch(model)
        if segments is None:
            raise RuntimeError(f"创建半圆端槽草图失败: {name}")
    feature_name = _feature_name(
        extrude_cut(
            model,
            sketch_name,
            depth,
            direction=bool(reverse_direction),
            both_directions=bool(both_directions),
        ),
        name,
    )
    return {
        "feature_kind": "semicircular_slot",
        "start_m": list(start),
        "end_m": list(end),
        "start_mm": [round(value * 1000.0, 6) for value in start],
        "end_mm": [round(value * 1000.0, 6) for value in end],
        "width_m": width,
        "width_mm": round(width * 1000.0, 6),
        "depth_m": None if depth == 0.0 else depth,
        "depth_mm": None if depth == 0.0 else round(depth * 1000.0, 6),
        "through": depth == 0.0,
        "plane_name": plane_name,
        "feature_names": [feature_name],
        "reverse_direction": bool(reverse_direction),
        "both_directions": bool(both_directions),
        "face_point_mm": [round(float(item) * 1000.0, 6) for item in face_point]
        if face_point is not None
        else None,
    }


def create_hole_pattern(model, positions: Iterable[Sequence[float]], creator, **kwargs) -> list[dict]:
    """@brief 按显式孔位逐个创建孔；creator 为本模块任一孔创建函数。"""
    evidence = []
    for index, position in enumerate(positions, start=1):
        item_kwargs = dict(kwargs)
        base_name = str(item_kwargs.pop("name", "孔"))
        evidence.append(creator(model, position, name=f"{base_name}_{index}", **item_kwargs))
    if not evidence:
        raise ValueError("positions 至少包含一个孔位")
    return evidence
