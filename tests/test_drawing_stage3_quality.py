"""Targeted drawing-quality regressions for stage 3."""
import importlib.util
from pathlib import Path

from scripts.sw_drawing import (
    plan_standard_view_layout,
    validate_generic_drawing_generation,
)

_REVIEW_IMPL = Path(__file__).resolve().parents[1] / "subskills" / "solidworks-engineering-drawing" / "scripts" / "drawing_review.py"
_REVIEW_SPEC = importlib.util.spec_from_file_location("stage3_drawing_review", _REVIEW_IMPL)
_REVIEW_MODULE = importlib.util.module_from_spec(_REVIEW_SPEC)
assert _REVIEW_SPEC.loader is not None
_REVIEW_SPEC.loader.exec_module(_REVIEW_MODULE)
_dimension_duplicate_report = _REVIEW_MODULE._dimension_duplicate_report
_balloon_report = _REVIEW_MODULE._balloon_report


def _drawing_spec():
    return {
        "schemaVersion": "1.0",
        "sourceModel": "part.sldprt",
        "documentType": "part",
        "standard": "GB_T",
        "projection": "first_angle",
        "paperSize": "A3",
        "modelSizeMm": [80, 50, 20],
        "insertModelDimensions": True,
        "views": {
            "front": {},
            "top": {},
            "right": {},
            "isometric": {"positionMm": [330, 180]},
        },
        "titleBlock": {
            "required": True,
            "format": "GB_T",
            "drawingNumber": "QA-001",
            "name": "Quality Test Part",
            "material": "Q235-A",
        },
        "outputs": {"slddrw": True, "pdf": True, "report": True},
    }


def test_layout_places_isometric_without_collision():
    layout = plan_standard_view_layout(
        (0.200, 0.100, 0.020),
        paper_size="A3",
        projection="first_angle",
        include_isometric=True,
    )
    assert layout["status"] == "pass"
    assert layout["view_collision_free"] is True
    assert [item["name"] for item in layout["views"]] == [
        "*Front", "*Top", "*Right", "*Isometric"
    ]
    isometric = next(item for item in layout["views"] if item["name"] == "*Isometric")
    assert isometric["kind"] == "isometric"
    assert isometric["box"]["right"] <= layout["sheet"]["width_m"]
    assert isometric["box"]["bottom"] >= layout["title_block_box"]["top"]


def test_generic_preflight_accepts_isometric_and_supported_title_fields():
    result = validate_generic_drawing_generation(_drawing_spec())
    assert result["status"] == "pass"
    assert not result["issues"]


def test_duplicate_review_uses_native_identity_not_value_only():
    structure = {
        "dimensions": [
            {
                "name": "D1@Sketch1",
                "native_dimension_name": "D1@Sketch1",
                "dedupe_identity": "D1@Sketch1",
                "type": 2,
                "value_mm": 10,
                "view": "Front",
            },
            {
                "name": "D1@Sketch1",
                "native_dimension_name": "D1@Sketch1",
                "dedupe_identity": "D1@Sketch1",
                "type": 2,
                "value_mm": 10,
                "view": "Top",
            },
            {
                "name": "D2@Sketch1",
                "native_dimension_name": "D2@Sketch1",
                "dedupe_identity": "D2@Sketch1",
                "type": 2,
                "value_mm": 10,
                "view": "Right",
            },
        ]
    }
    report = _dimension_duplicate_report(structure)
    assert report["status"] == "fail"
    assert len(report["duplicates"]) == 1
    assert {item["view"] for item in report["duplicates"][0]["views"]} == {"Front", "Top"}


def test_balloons_must_match_native_bom_item_numbers():
    spec = _drawing_spec()
    spec["bom"] = {"required": True, "balloons": {"required": True}}
    structure = {
        "tables": [{
            "type": 2,
            "cells": [["序号", "图号"], ["1", "A"], ["2", "B"]],
        }],
        "balloons": [
            {"item_number": "1", "is_bom_balloon": True, "position_m": [0.1, 0.2, 0]},
            {"item_number": "2", "is_bom_balloon": True, "position_m": [0.2, 0.2, 0]},
        ],
    }
    result = _balloon_report(spec, structure)
    assert result["status"] == "pass"
    assert result["expected"] == ["1", "2"]
