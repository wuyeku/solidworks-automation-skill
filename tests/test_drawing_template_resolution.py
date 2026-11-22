"""Drawing template resolution and SolidWorks 2025 paper-size contracts."""
from pathlib import Path

from scripts.sw_connect import find_template
from scripts.sw_drawing import PAPER_SIZES, resolve_drawing_template


class FakeSolidWorks:
    def __init__(self, default_template, template_sizes):
        self.default_template = str(default_template)
        self.template_sizes = {
            str(Path(path).resolve()): values
            for path, values in template_sizes.items()
        }

    def GetUserPreferenceStringValue(self, preference):
        return self.default_template if preference == 10 else ""

    def GetTemplateSizes(self, path):
        return self.template_sizes.get(str(Path(path).resolve()))


def _template(path, width_m, height_m):
    path.write_bytes(b"fake drawing template")
    return Path(path).resolve(), [12.0, width_m, height_m]


def test_sw2025_paper_size_enum_values():
    assert {name: spec["code"] for name, spec in PAPER_SIZES.items()} == {
        "A4": 6,
        "A4P": 7,
        "A3": 8,
        "A2": 9,
        "A1": 10,
        "A0": 11,
    }


def test_resolver_uses_default_template_when_size_is_unspecified(tmp_path):
    a4, values = _template(tmp_path / "gb_a4.drwdot", .297, .210)
    sw = FakeSolidWorks(a4, {a4: values})

    result = resolve_drawing_template(sw)

    assert result["status"] == "pass"
    assert result["mode"] == "default"
    assert result["selected"] == str(a4)
    assert result["paper_size"] == "A4"


def test_resolver_selects_verified_size_matching_template(tmp_path):
    a4, a4_values = _template(tmp_path / "gb_a4.drwdot", .297, .210)
    a3, a3_values = _template(tmp_path / "gb_a3.drwdot", .420, .297)
    decoy, decoy_values = _template(tmp_path / "gb_a3_old.drwdot", .594, .420)
    sw = FakeSolidWorks(a4, {a4: a4_values, a3: a3_values, decoy: decoy_values})

    result = resolve_drawing_template(sw, paper_size="A3", standard="GB_T")

    assert result["status"] == "pass"
    assert result["mode"] == "paper_size"
    assert result["selected"] == str(a3)
    assert result["paper_size"] == "A3"


def test_drawing_template_candidates_are_size_verified(tmp_path):
    default_dir = tmp_path / "default"
    other_dir = tmp_path / "other"
    default_dir.mkdir()
    other_dir.mkdir()
    a4, a4_values = _template(default_dir / "gb_a4.drwdot", .297, .210)
    candidate, a3_values = _template(other_dir / "custom_gb_a3.drwdot", .420, .297)
    sw = FakeSolidWorks(a4, {a4: a4_values, candidate: a3_values})

    result = resolve_drawing_template(
        sw,
        paper_size="A3",
        template_candidates=[candidate],
        standard="GB_T",
    )

    assert result["status"] == "pass"
    assert result["mode"] == "paper_size"
    assert result["selected"] == str(candidate)


def test_explicit_template_wins_but_mismatch_blocks(tmp_path):
    default, a4_values = _template(tmp_path / "gb_a4.drwdot", .297, .210)
    explicit, a3_values = _template(tmp_path / "custom_drawing.drwdot", .420, .297)
    sw = FakeSolidWorks(default, {default: a4_values, explicit: a3_values})

    matching = resolve_drawing_template(
        sw,
        paper_size="A3",
        explicit_template=str(explicit),
    )
    mismatched = resolve_drawing_template(
        sw,
        paper_size="A4",
        explicit_template=str(explicit),
    )

    assert matching["status"] == "pass"
    assert matching["mode"] == "explicit"
    assert matching["selected"] == str(explicit)
    assert mismatched["status"] == "blocked"
    assert mismatched["error_code"] == "DRAWING_TEMPLATE_SIZE_MISMATCH"


def test_missing_default_template_blocks_without_requested_size(tmp_path):
    missing = tmp_path / "missing.drwdot"
    sw = FakeSolidWorks(missing, {})

    result = resolve_drawing_template(sw)

    assert result["status"] == "blocked"
    assert result["error_code"] == "DRAWING_DEFAULT_TEMPLATE_MISSING"


def test_explicit_sheet_format_is_not_accepted_as_drawing_template(tmp_path):
    default, values = _template(tmp_path / "gb_a4.drwdot", .297, .210)
    sheet_format = tmp_path / "a3 - gb.slddrt"
    sheet_format.write_bytes(b"sheet format")
    sw = FakeSolidWorks(default, {default: values})

    result = resolve_drawing_template(
        sw,
        paper_size="A3",
        explicit_template=str(sheet_format),
    )

    assert result["status"] == "blocked"
    assert result["error_code"] == "DRAWING_TEMPLATE_NOT_DRWDOT"


def test_explicit_sheet_format_fallback_is_used_only_after_drwdot_search(tmp_path):
    default, values = _template(tmp_path / "gb_a4.drwdot", .297, .210)
    sheet_format = tmp_path / "a3 - gb.slddrt"
    sheet_format.write_bytes(b"sheet format")
    sw = FakeSolidWorks(default, {default: values})

    result = resolve_drawing_template(
        sw,
        paper_size="A3",
        template_candidates=[sheet_format],
        standard="GB_T",
    )

    assert result["status"] == "pass"
    assert result["mode"] == "sheet_format"
    assert result["selected"] == str(default)
    assert result["sheet_format_path"] == str(sheet_format.resolve())


def test_drawing_find_template_does_not_silently_use_fallback(tmp_path):
    missing = tmp_path / "missing.drwdot"
    sw = FakeSolidWorks(missing, {})

    try:
        find_template(sw, "drawing", allow_fallback=False)
    except FileNotFoundError as exc:
        assert "默认模板不存在或无效" in str(exc)
    else:
        raise AssertionError("drawing template lookup unexpectedly used a fallback")
