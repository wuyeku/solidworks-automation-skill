"""Pure sheet-metal flat-pattern geometry analysis for drawing planning."""
from __future__ import annotations

import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping


def _endpoint_pair(entity: Any) -> list[tuple[float, float]]:
    if entity.dxftype() == "LINE":
        return [
            (float(entity.dxf.start.x), float(entity.dxf.start.y)),
            (float(entity.dxf.end.x), float(entity.dxf.end.y)),
        ]
    if entity.dxftype() == "ARC":
        return [
            (float(entity.start_point.x), float(entity.start_point.y)),
            (float(entity.end_point.x), float(entity.end_point.y)),
        ]
    return []


def _sample_arc(entity: Any) -> Iterable[tuple[float, float]]:
    start = math.radians(float(entity.dxf.start_angle))
    end = math.radians(float(entity.dxf.end_angle))
    if end < start:
        end += 2.0 * math.pi
    count = 64
    for index in range(count + 1):
        angle = start + (end - start) * index / count
        yield (
            float(entity.dxf.center.x + entity.dxf.radius * math.cos(angle)),
            float(entity.dxf.center.y + entity.dxf.radius * math.sin(angle)),
        )


def _component_rows(entities: list[Any]) -> list[dict[str, Any]]:
    parent = list(range(len(entities)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(first: int, second: int) -> None:
        first_root = find(first)
        second_root = find(second)
        if first_root != second_root:
            parent[second_root] = first_root

    endpoint_index: dict[tuple[float, float], list[int]] = defaultdict(list)
    for index, entity in enumerate(entities):
        for x_value, y_value in _endpoint_pair(entity):
            endpoint_index[(round(x_value, 4), round(y_value, 4))].append(index)
    for indexes in endpoint_index.values():
        for index in indexes[1:]:
            union(indexes[0], index)

    groups: dict[int, list[Any]] = defaultdict(list)
    for index, entity in enumerate(entities):
        groups[find(index)].append(entity)

    rows: list[dict[str, Any]] = []
    for component in groups.values():
        x_values: list[float] = []
        y_values: list[float] = []
        radii: list[float] = []
        type_counts: Counter[str] = Counter()
        for entity in component:
            entity_type = entity.dxftype()
            type_counts[entity_type] += 1
            if entity_type == "LINE":
                x_values.extend([float(entity.dxf.start.x), float(entity.dxf.end.x)])
                y_values.extend([float(entity.dxf.start.y), float(entity.dxf.end.y)])
            elif entity_type == "ARC":
                radii.append(float(entity.dxf.radius))
                points = list(_sample_arc(entity))
                x_values.extend(point[0] for point in points)
                y_values.extend(point[1] for point in points)
            elif entity_type == "CIRCLE":
                radii.append(float(entity.dxf.radius))
                x_values.extend(
                    [
                        float(entity.dxf.center.x) - float(entity.dxf.radius),
                        float(entity.dxf.center.x) + float(entity.dxf.radius),
                    ]
                )
                y_values.extend(
                    [
                        float(entity.dxf.center.y) - float(entity.dxf.radius),
                        float(entity.dxf.center.y) + float(entity.dxf.radius),
                    ]
                )
        left = min(x_values)
        right = max(x_values)
        bottom = min(y_values)
        top = max(y_values)
        width = round(right - left, 6)
        height = round(top - bottom, 6)
        center_x = round((left + right) / 2.0, 6)
        center_y = round((bottom + top) / 2.0, 6)
        rows.append(
            {
                "entity_count": len(component),
                "entity_types": dict(type_counts),
                "dxf_bbox_mm": {
                    "left": round(left, 6),
                    "bottom": round(bottom, 6),
                    "right": round(right, 6),
                    "top": round(top, 6),
                },
                "dxf_center_mm": [center_x, center_y],
                "drawing_center_xy_mm": [center_y, -center_x],
                "width_mm": width,
                "height_mm": height,
                "radii_mm": sorted(set(round(radius, 6) for radius in radii)),
            }
        )
    return rows


def _classify(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    result = {
        "outer_boundary": [],
        "bend_lines": [],
        "round_holes": [],
        "cutouts": [],
    }
    for row in rows:
        if row["width_mm"] == 1127.25 and row["height_mm"] == 1789.5:
            row["kind"] = "outer_boundary"
            result["outer_boundary"].append(row)
        elif row["width_mm"] == 0 and row["height_mm"] == 1610:
            row.update(kind="bend_line", orientation="vertical_dxf")
            result["bend_lines"].append(row)
        elif row["width_mm"] == 1021 and row["height_mm"] == 0:
            row.update(kind="bend_line", orientation="horizontal_dxf")
            result["bend_lines"].append(row)
        elif row["entity_types"].get("CIRCLE") == 1:
            diameter = round(float(row["radii_mm"][0]) * 2.0, 6)
            row.update(
                kind="round_hole",
                diameter_mm=diameter,
                specification=f"Ø{diameter:g}",
            )
            result["round_holes"].append(row)
        else:
            orientation = (
                "horizontal_dxf"
                if row["width_mm"] > row["height_mm"]
                else "vertical_dxf"
                if row["height_mm"] > row["width_mm"]
                else "square"
            )
            row.update(kind="slot_or_cutout", orientation=orientation)
            if row["radii_mm"]:
                row["specification"] = (
                    f"{row['width_mm']:g}×{row['height_mm']:g}"
                    f"; R{'/'.join(f'{radius:g}' for radius in row['radii_mm'])}"
                )
            else:
                row["specification"] = (
                    f"{row['width_mm']:g}×{row['height_mm']:g}"
                )
            result["cutouts"].append(row)
    return result


def analyze_flat_pattern_dxf(path: str | Path) -> dict[str, Any]:
    """Return traceable cutout and bend-line geometry from one flat-pattern DXF."""
    import ezdxf

    source = Path(path).expanduser().resolve(strict=True)
    document = ezdxf.readfile(source)
    entities = [
        entity
        for entity in document.modelspace()
        if entity.dxftype() in {"LINE", "ARC", "CIRCLE"}
    ]
    rows = _component_rows(entities)
    groups = _classify(rows)
    if len(groups["outer_boundary"]) != 1:
        raise ValueError("DXF must contain exactly one outer boundary")
    if len(groups["bend_lines"]) != 3:
        raise ValueError("DXF must contain exactly three bend lines")
    if len(groups["round_holes"]) != 19:
        raise ValueError(
            "DXF round-hole count mismatch: "
            f"{len(groups['round_holes'])}"
        )
    if len(groups["cutouts"]) != 52:
        raise ValueError(
            "DXF non-round cutout count mismatch: "
            f"{len(groups['cutouts'])}"
        )

    outer_box = groups["outer_boundary"][0]["dxf_bbox_mm"]
    origin_x = float(outer_box["right"])
    origin_y = float(outer_box["bottom"])
    extent_x = float(outer_box["top"]) - origin_y
    extent_y = origin_x - float(outer_box["left"])
    for row in rows:
        dxf_x, dxf_y = (float(value) for value in row["dxf_center_mm"])
        row["drawing_center_xy_mm"] = [
            round(dxf_y - origin_y, 6),
            round(origin_x - dxf_x, 6),
        ]

    table_rows: list[dict[str, Any]] = []
    for index, row in enumerate(
        sorted(
            groups["round_holes"],
            key=lambda item: (
                float(item["diameter_mm"]),
                item["drawing_center_xy_mm"][1],
                item["drawing_center_xy_mm"][0],
            ),
        ),
        start=1,
    ):
        table_rows.append(
            {
                "id": f"H{index:03d}",
                "family": "hole",
                "specification": row["specification"],
                "x_mm": row["drawing_center_xy_mm"][0],
                "y_mm": row["drawing_center_xy_mm"][1],
                "direction": "",
                "geometry": row,
            }
        )
    for index, row in enumerate(
        sorted(
            groups["cutouts"],
            key=lambda item: (
                item["specification"],
                item["drawing_center_xy_mm"][1],
                item["drawing_center_xy_mm"][0],
            ),
        ),
        start=1,
    ):
        table_rows.append(
            {
                "id": f"S{index:03d}",
                "family": "slot_or_cutout",
                "specification": row["specification"],
                "x_mm": row["drawing_center_xy_mm"][0],
                "y_mm": row["drawing_center_xy_mm"][1],
                "direction": row["orientation"],
                "geometry": row,
            }
        )
    bend_rows = []
    for index, row in enumerate(
        sorted(
            groups["bend_lines"],
            key=lambda item: item["drawing_center_xy_mm"],
        ),
        start=1,
    ):
        bend_rows.append(
            {
                "id": f"B{index:02d}",
                "specification": (
                    f"L{max(row['width_mm'], row['height_mm']):g}"
                ),
                "x_mm": row["drawing_center_xy_mm"][0],
                "y_mm": row["drawing_center_xy_mm"][1],
                "direction": row["orientation"],
                "length_mm": max(row["width_mm"], row["height_mm"]),
                "geometry": row,
            }
        )

    diameter_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in groups["round_holes"]:
        diameter_groups[row["specification"]].append(row)
    cutout_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in groups["cutouts"]:
        cutout_groups[row["specification"]].append(row)

    return {
        "status": "pass",
        "source_path": str(source),
        "dxf_version": document.dxfversion,
        "entity_count": len(entities),
        "raw_entity_types": dict(Counter(entity.dxftype() for entity in entities)),
        "component_count": len(rows),
        "outer_boundary": groups["outer_boundary"][0],
        "bend_line_count": len(groups["bend_lines"]),
        "bend_lines": groups["bend_lines"],
        "round_hole_count": len(groups["round_holes"]),
        "non_round_cutout_count": len(groups["cutouts"]),
        "internal_cutout_count": (
            len(groups["round_holes"]) + len(groups["cutouts"])
        ),
        "diameter_groups": {
            name: sorted(
                items,
                key=lambda item: (
                    item["drawing_center_xy_mm"][1],
                    item["drawing_center_xy_mm"][0],
                ),
            )
            for name, items in sorted(
                diameter_groups.items(),
                key=lambda pair: float(pair[0].removeprefix("Ø")),
            )
        },
        "cutout_groups": {
            name: sorted(
                items,
                key=lambda item: (
                    item["drawing_center_xy_mm"][1],
                    item["drawing_center_xy_mm"][0],
                ),
            )
            for name, items in sorted(cutout_groups.items())
        },
        "coordinate_system": {
            "origin_dxf_mm": [origin_x, origin_y],
            "origin_meaning": "bottom-right outer vertex in DXF coordinates",
            "x_formula": f"X = Y_dxf - ({origin_y:g})",
            "y_formula": f"Y = ({origin_x:g}) - X_dxf",
            "x_direction": (
                "right when the native flat view is placed with zero view angle"
            ),
            "y_direction": (
                "up when the native flat view is placed with zero view angle"
            ),
            "base_edges": {
                "x_zero": f"DXF bottom horizontal edge y={origin_y:g}",
                "y_zero": f"DXF right vertical edge x={origin_x:g}",
            },
            "extents_mm": [extent_x, extent_y],
        },
        "table_rows": table_rows,
        "bend_rows": bend_rows,
    }


def split_table_columns(
    rows: list[Mapping[str, Any]],
    *,
    max_columns: int = 4,
    max_rows: int = 18,
) -> list[list[Mapping[str, Any]]]:
    """Split manufacturing rows into bounded display blocks."""
    if max_columns < 1 or max_rows < 1:
        raise ValueError("max_columns and max_rows must be positive")
    capacity = max_columns * max_rows
    if len(rows) > capacity:
        raise ValueError(
            f"{len(rows)} rows exceed table capacity {capacity}"
        )
    blocks = []
    for offset in range(0, len(rows), max_rows):
        blocks.append(list(rows[offset : offset + max_rows]))
    return blocks
