"""Regressions for default drawing templates, without a SOLIDWORKS connection."""
import pytest

from scripts.sw_drawing import (
    setup_current_sheet, plan_standard_view_layout, inspect_drawing_structure,
)


class Sheet:
    def __init__(self, first_angle=False, paper_code=6, width=.297, height=.210):
        self.properties = [paper_code, 12, 1, 2, first_angle, width, height, True]
        self.calls = []

    def GetName(self):
        return "Sheet1"

    def GetTemplateName(self):
        # An embedded format does not require a separately available file.
        return "C:/unavailable/a4 - gb.slddrt"

    def GetProperties2(self):
        return tuple(self.properties)

    def SetProperties2(self, *args):
        self.calls.append(args)
        self.properties = list(args)

    def GetViews(self):
        return []


class Drawing:
    def __init__(self, sheet):
        self.sheet = sheet

    def GetCurrentSheet(self):
        return self.sheet

    def SetupSheet6(self, *args):
        raise AssertionError("Default sheet format must not be replaced")


@pytest.mark.parametrize("candidates", [None, []])
def test_default_template_keeps_embedded_format_size_scale_and_only_changes_projection(candidates):
    sheet = Sheet()
    before = list(sheet.properties)
    result = setup_current_sheet(Drawing(sheet), candidates, paper_size="A4")
    assert result["status"] == "pass"
    assert result["mode"] == "default_template"
    assert result["sheet_size_m"] == [.297, .210]
    assert result["paper_size"] == "A4"
    expected = before.copy()
    expected[4] = True
    assert sheet.properties == expected
    assert len(sheet.calls) == 1


def test_already_first_angle_does_not_write_sheet_properties():
    sheet = Sheet(first_angle=True)
    assert setup_current_sheet(Drawing(sheet), [])["status"] == "pass"
    assert sheet.calls == []


def test_failed_projection_readback_is_not_reported_as_success():
    sheet = Sheet()
    sheet.SetProperties2 = lambda *args: None
    result = setup_current_sheet(Drawing(sheet), [])
    assert result["status"] == "failed"
    assert result["error_code"] == "DRAWING_DEFAULT_SHEET_SETUP_FAILED"


@pytest.mark.parametrize("properties", [[], [7, 12, 1, 0, 0, .21, .297, 1],
                                        [7, 12, 1, 1, 0, float('nan'), .297, 1]])
def test_invalid_sheet_properties_block_before_mutation(properties):
    sheet = Sheet()
    sheet.properties = properties
    assert setup_current_sheet(Drawing(sheet), [])["status"] == "failed"
    assert sheet.calls == []


def test_explicit_missing_template_still_blocks(tmp_path):
    result = setup_current_sheet(Drawing(Sheet()), [tmp_path / "a4 - gb.slddrt"], paper_size="A4")
    assert result["status"] == "blocked"
    assert result["error_code"] == "DRAWING_GBT_TEMPLATE_MISSING"


def test_portrait_layout_and_inspection_use_actual_sheet_dimensions():
    layout = plan_standard_view_layout((.114, .054, .020), paper_size="A4",
                                      projection="first_angle", sheet_size_m=(.210, .297))
    assert layout["status"] == "pass"
    assert layout["sheet"] == {"width_m": .210, "height_m": .297}
    structure = inspect_drawing_structure(
        Drawing(Sheet(True, paper_code=7, width=.210, height=.297)),
        paper_size_hint="A4P",
    )
    assert structure["sheet_size"] == layout["sheet"]
    assert structure["paper_size"] == "A4P"
    assert structure["projection"] == "first_angle"
    assert structure["sheet_size_source"] == "GetProperties2"


@pytest.mark.parametrize("size", [(0, .21), (.297, float('inf')), (.21,)])
def test_layout_rejects_invalid_actual_size(size):
    with pytest.raises(ValueError):
        plan_standard_view_layout((.1, .05, .02), sheet_size_m=size)


def test_generator_passes_actual_default_sheet_size_to_view_creation(monkeypatch):
    from scripts.sw_drawing import generate_drawing_from_spec
    captured = {}

    def capture_views(drawing, source, layout, **kwargs):
        captured.update(layout)
        return {"status": "failed", "error_code": "STOP_TEST_BEFORE_CAD_CREATION"}

    monkeypatch.setitem(generate_drawing_from_spec.__globals__, "create_adaptive_standard_views", capture_views)
    spec = {"paperSize": "A4", "projection": "first_angle", "standard": "GB_T",
            "modelSizeMm": [114, 54, 20], "views": {"front": {}, "top": {}, "right": {}}}
    result = generate_drawing_from_spec(Drawing(Sheet()), spec, "part.sldprt")
    assert result["stage"] == "views"
    assert captured["sheet"] == {"width_m": .297, "height_m": .210}


def test_generator_derives_missing_paper_size_from_default_template(monkeypatch):
    from scripts.sw_drawing import generate_drawing_from_spec
    captured = {}

    def capture_views(drawing, source, layout, **kwargs):
        captured.update(layout)
        return {"status": "failed", "error_code": "STOP_TEST_BEFORE_CAD_CREATION"}

    monkeypatch.setitem(generate_drawing_from_spec.__globals__, "create_adaptive_standard_views", capture_views)
    spec = {
        "projection": "first_angle",
        "standard": "GB_T",
        "modelSizeMm": [114, 54, 20],
        "views": {"front": {}, "top": {}, "right": {}},
    }
    result = generate_drawing_from_spec(Drawing(Sheet()), spec, "part.sldprt")

    assert result["stage"] == "views"
    assert captured["sheet"] == {"width_m": .297, "height_m": .210}


def test_default_template_blocks_requested_size_mismatch_before_mutation():
    sheet = Sheet()
    before = list(sheet.properties)
    result = setup_current_sheet(Drawing(sheet), [], paper_size="A3")
    assert result["status"] == "blocked"
    assert result["error_code"] == "DRAWING_TEMPLATE_SIZE_MISMATCH"
    assert result["requested_paper_size"] == "A3"
    assert result["actual_paper_size"] == "A4"
    assert sheet.properties == before
    assert sheet.calls == []
