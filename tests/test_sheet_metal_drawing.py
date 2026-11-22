"""Sheet-metal drawing planning checks that do not require SolidWorks."""
from __future__ import annotations

import pytest

from scripts.sheet_metal_geometry import split_table_columns
from scripts.sw_drawing_sheet_metal import (
    _title_scale_evidence,
    sheet_metal_layout_decision,
)
from scripts.sw_review import review_drawing_layout


def _analysis() -> dict:
    return {
        "coordinate_system": {"extents_mm": [1789.5, 1127.25]},
        "table_rows": [
            {"id": f"H{index:03d}"} for index in range(19)
        ] + [
            {"id": f"S{index:03d}"} for index in range(1, 53)
        ],
        "bend_rows": [{"id": f"B{index:02d}"} for index in range(1, 4)],
    }


def test_sheet_metal_a2_layout_uses_four_readable_table_columns():
    spec = {
        "paperSize": "A2",
        "sheetMetal": {
            "paperSize": "A2",
            "formedScale": 0.1,
            "flatScale": 0.2,
            "coordinateTable": {"rowsPerBlock": 15},
        },
    }

    result = sheet_metal_layout_decision(spec, _analysis())

    assert result["status"] == "pass"
    assert result["paper_size"] == "A2"
    assert result["table_columns"] == 4
    assert result["table_rows_per_block"] == 19
    assert result["table_row_count"] == 74
    assert result["minimum_font_height_mm"] == 3.5


def test_sheet_metal_table_split_preserves_all_feature_ids():
    rows = [{"id": f"F{index:03d}"} for index in range(74)]

    blocks = split_table_columns(rows, max_columns=5, max_rows=15)

    assert [len(block) for block in blocks] == [15, 15, 15, 15, 14]
    assert [row["id"] for block in blocks for row in block] == [
        row["id"] for row in rows
    ]


def test_sheet_metal_table_split_rejects_insufficient_capacity():
    rows = [{"id": f"F{index:03d}"} for index in range(74)]

    with pytest.raises(ValueError, match="exceed table capacity"):
        split_table_columns(rows, max_columns=4, max_rows=18)


def test_sheet_metal_title_scale_evidence_matches_each_field():
    class Note:
        PropertyLinkedText = '$PRP:"SW-图纸比例(Sheet Scale)"'

        def __init__(self, text):
            self.text = text

        def GetText(self):
            return self.text

    assert _title_scale_evidence([Note("1:5")], "1:5")["pass"] is True
    assert _title_scale_evidence([Note("1:1")], "1:5")["pass"] is False


def test_multi_sheet_layout_review_does_not_compare_boxes_across_sheets():
    box = {"left": 0.10, "bottom": 0.10, "right": 0.20, "top": 0.20}
    result = review_drawing_layout(
        {
            "views": [
                {"sheet": "formed", "name": "formed-front", "box": box},
                {"sheet": "flat", "name": "flat-view", "box": box},
            ],
            "dimensions": [],
            "notes": [],
            "title_block": {
                "sheet": "formed",
                "box": {"left": 0.40, "bottom": 0.01, "right": 0.59, "top": 0.08},
            },
        }
    )

    assert not any(
        finding["code"] == "DRAWING_VIEW_OVERLAP"
        for finding in result["findings"]
    )


def test_sheet_format_notes_are_not_reported_as_title_block_intrusions():
    box = {"left": 0.40, "bottom": 0.01, "right": 0.59, "top": 0.08}
    result = review_drawing_layout(
        {
            "views": [],
            "dimensions": [],
            "notes": [
                {
                    "sheet": "formed",
                    "note_kind": "sheet_format_note",
                    "text": "比例",
                    "box": box,
                }
            ],
            "title_block": {"sheet": "formed", "box": box},
        }
    )

    assert not any(
        finding["code"] == "DRAWING_NOTE_TITLE_BLOCK_INTRUSION"
        for finding in result["findings"]
    )
