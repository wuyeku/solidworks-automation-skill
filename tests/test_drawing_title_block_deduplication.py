"""Title-block semantic de-duplication and COM expression normalisation."""
from pathlib import Path

from scripts.sw_drawing import (
    add_note,
    add_title_block_fields,
    collect_existing_title_block_fields,
    inspect_drawing_structure,
    setup_current_sheet,
)


class FakeAnnotation:
    def __init__(self, name, position=(0.2, 0.05, 0.0)):
        self.name = name
        self.position = tuple(position)

    def GetName(self):
        return self.name

    def SetName(self, value):
        self.name = value
        return True

    def GetPosition(self):
        return self.position

    def SetPosition2(self, x, y, z):
        self.position = (x, y, z)
        return True

    def GetBox(self):
        x, y, _ = self.position
        return (x - 0.01, y - 0.003, 0.0, x + 0.02, y + 0.004, 0.0)


class FakeNote:
    def __init__(self, text, *, linked_text="", name="", position=(0.2, 0.05, 0.0)):
        self.text = text
        self.linked_text = linked_text
        self.annotation = FakeAnnotation(name, position)

    def GetText(self):
        return self.text

    @property
    def PropertyLinkedText(self):
        return self.linked_text

    def GetAnnotation(self):
        return self.annotation

    def GetExtent(self):
        return self.annotation.GetBox()


class FakeView:
    Name = "图纸1"
    Type = 1

    def __init__(self, notes=None):
        self.notes = list(notes or [])

    def GetNotes(self):
        return list(self.notes)

    def GetNextView(self):
        return None

    def GetOutline(self):
        return (0.01, 0.01, 0.0, 0.41, 0.28, 0.0)

    def GetDisplayDimensions(self):
        return []

    def GetTableAnnotations(self):
        return []


class FakeDrawing:
    def __init__(self, notes=None, *, actual_expression=None):
        self.view = FakeView(notes)
        self.sheet = FakeSheet(self.view)
        self.actual_expression = actual_expression
        self.insert_calls = []

    def GetFirstView(self):
        return self.view

    def GetCurrentSheet(self):
        return self.sheet

    def GetSheetNames(self):
        return ["图纸1"]

    def GetSheet(self, _name):
        return self.sheet

    def InsertNote(self, text):
        self.insert_calls.append(text)
        actual = self.actual_expression or text
        note = FakeNote(actual, linked_text=text, name="新建注释")
        self.view.notes.append(note)
        return note

    def ForceRebuild3(self, _top_only):
        return True


class FakeSheet:
    def __init__(self, view=None):
        self.view = view

    def GetName(self):
        return "图纸1"

    def GetTemplateName(self):
        return "C:/templates/gb_a3.slddrt"

    def GetProperties2(self):
        return (8, 12, 1, 1, True, 0.420, 0.297, True)

    def GetViews(self):
        return [self.view] if self.view is not None else []

    SheetFormatVisible = True


def _template_notes():
    return [
        FakeNote("", linked_text='$PRPSHEET:"代号"', name="Detail-A", position=(0.38, 0.02, 0.0)),
        FakeNote("", linked_text='$PRPSHEET:"名称"', name="Detail-B", position=(0.38, 0.03, 0.0)),
        FakeNote("", linked_text='$PRPSHEET:"材料"', name="Detail-C", position=(0.33, 0.05, 0.0)),
        FakeNote("1:1", linked_text='$PRP:"SW-图纸比例(Sheet Scale)"', name="Detail-D", position=(0.34, 0.03, 0.0)),
        FakeNote("", linked_text='$PRPSHEET:"设计日期"', name="Detail-E", position=(0.25, 0.03, 0.0)),
    ]


def _title_request(**extra):
    return {
        "required": True,
        "drawingNumber": "DWG-001",
        "name": "SAMPLE",
        "material": "Q235-A",
        "scale": "1:1",
        "date": "2026-11-22",
        "linkToModelProperties": False,
        **extra,
    }


def test_existing_template_links_are_not_duplicated():
    drawing = FakeDrawing(_template_notes())
    result = add_title_block_fields(
        drawing,
        _title_request(),
        {"left": 0.228, "bottom": 0.012, "right": 0.408, "top": 0.067},
        paper_size="A3",
    )

    assert result["status"] == "pass"
    assert result["inserted_fields"] == []
    assert set(result["skipped_existing_fields"]) == {
        "drawingNumber", "name", "material", "scale", "date"
    }
    assert drawing.insert_calls == []
    assert set(result["existing_fields"]) == {
        "drawingNumber", "name", "material", "scale", "date"
    }


def test_unrelated_property_note_outside_title_block_does_not_block_insertion():
    drawing = FakeDrawing([
        FakeNote(
            "",
            linked_text='$PRPSHEET:"代号"',
            name="UnrelatedDrawingNote",
            position=(0.02, 0.24, 0.0),
        ),
    ])
    result = add_title_block_fields(
        drawing,
        {
            "required": True,
            "drawingNumber": "DWG-001",
            "linkToModelProperties": False,
        },
        {"left": 0.228, "bottom": 0.012, "right": 0.408, "top": 0.067},
        paper_size="A3",
    )

    assert "drawingNumber" not in result["existing_fields"]
    assert result["inserted_fields"] == ["drawingNumber"]
    assert len(drawing.insert_calls) == 1


def test_manual_override_is_required_to_add_a_second_field():
    drawing = FakeDrawing(_template_notes())
    result = add_title_block_fields(
        drawing,
        _title_request(overwriteExistingFields=True),
        {"left": 0.228, "bottom": 0.012, "right": 0.408, "top": 0.067},
        paper_size="A3",
    )

    assert result["status"] == "review_required"
    assert set(result["overridden_existing_fields"]) == {
        "drawingNumber", "name", "material", "scale", "date"
    }
    assert len(drawing.insert_calls) == 5


def test_repeated_title_block_call_is_idempotent():
    drawing = FakeDrawing()
    box = {"left": 0.228, "bottom": 0.012, "right": 0.408, "top": 0.067}
    first = add_title_block_fields(drawing, _title_request(), box, paper_size="A3")
    second = add_title_block_fields(drawing, _title_request(), box, paper_size="A3")

    assert first["status"] == "pass"
    assert len(first["inserted_fields"]) == 5
    assert second["status"] == "pass"
    assert second["inserted_fields"] == []
    assert set(second["skipped_existing_fields"]) == {
        "drawingNumber", "name", "material", "scale", "date"
    }
    assert len(drawing.insert_calls) == 5


def test_title_text_truncation_blocks_before_any_insertion():
    drawing = FakeDrawing()
    request = {
        "required": True,
        "drawingNumber": "DWG-TOO-LONG-FOR-CELL",
        "linkToModelProperties": False,
    }
    result = add_title_block_fields(
        drawing,
        request,
        {"left": 0.228, "bottom": 0.012, "right": 0.408, "top": 0.067},
        paper_size="A3",
    )

    assert result["status"] == "review_required"
    assert result["error_code"] == "DRAWING_TITLE_BLOCK_TEXT_CLIPPED"
    assert any(item["reason"] == "text_truncated" for item in result["failures"])
    assert drawing.insert_calls == []


def test_property_expression_readback_accepts_brace_form():
    drawing = FakeDrawing(actual_expression="$PRPSHEET:{PartNumber}")
    result = add_note(
        drawing,
        0.29,
        0.064,
        '$PRPSHEET:"PartNumber"',
        persistent_name="CAD_TITLE__drawingNumber",
    )

    assert result["status"] == "pass"
    assert result["property_linked_text"] == '$PRPSHEET:"PartNumber"'


def test_semantic_duplicate_is_reported_even_without_box_overlap():
    notes = [
        FakeNote("", linked_text='$PRPSHEET:"名称"', name="Detail-1", position=(0.38, 0.03, 0.0)),
        FakeNote("DUP", linked_text="$PRPSHEET:{Description}", name="CAD_TITLE__name", position=(0.25, 0.05, 0.0)),
    ]
    drawing = FakeDrawing(notes)

    result = inspect_drawing_structure(
        drawing,
        paper_size_hint="A3",
        title_block_box={"left": 0.228, "bottom": 0.012, "right": 0.408, "top": 0.067},
    )

    assert result["title_block"]["semantic_duplicates"]
    assert result["error_code"] == "DRAWING_TITLE_BLOCK_SEMANTIC_DUPLICATE"


def test_one_intentional_template_link_repeat_is_not_a_duplicate_layout():
    notes = [
        FakeNote("", linked_text='$PRPSHEET:"代号"', name="Code-A", position=(0.05, 0.28, 0.0)),
        FakeNote("", linked_text='$PRPSHEET:"代号"', name="Code-B", position=(0.38, 0.02, 0.0)),
        FakeNote("", linked_text='$PRPSHEET:"名称"', name="Name-A", position=(0.38, 0.03, 0.0)),
        FakeNote("", linked_text='$PRPSHEET:"材料"', name="Mat-A", position=(0.33, 0.05, 0.0)),
        FakeNote("1:1", linked_text='$PRP:"SW-图纸比例(Sheet Scale)"', name="Scale-A", position=(0.34, 0.03, 0.0)),
        FakeNote("", linked_text='$PRPSHEET:"设计日期"', name="Date-A", position=(0.25, 0.03, 0.0)),
    ]
    drawing = FakeDrawing(notes)

    result = inspect_drawing_structure(
        drawing,
        paper_size_hint="A3",
        title_block_box={"left": 0.228, "bottom": 0.012, "right": 0.408, "top": 0.067},
    )

    assert result["title_block"]["template_semantic_multiplicity"] == {"drawingNumber": 2}
    assert result["title_block"]["semantic_duplicates"] == []


def test_widespread_template_field_repetition_is_reported_as_duplicate_layout():
    first = _template_notes()
    second = [
        FakeNote(
            note.text,
            linked_text=note.linked_text,
            name=f"Second-{index}",
            position=(note.annotation.position[0] - 0.15, note.annotation.position[1], 0.0),
        )
        for index, note in enumerate(_template_notes())
    ]
    drawing = FakeDrawing(first + second)

    result = inspect_drawing_structure(
        drawing,
        paper_size_hint="A3",
        title_block_box={"left": 0.228, "bottom": 0.012, "right": 0.408, "top": 0.067},
    )

    duplicate = next(
        item for item in result["title_block"]["semantic_duplicates"]
        if item["kind"] == "multiple_template_title_blocks"
    )
    assert set(duplicate["fields"]) == {
        "drawingNumber", "name", "material", "scale", "date"
    }


def test_collect_existing_title_block_fields_reads_quoted_and_brace_links():
    drawing = FakeDrawing([
        FakeNote("", linked_text='$PRPSHEET:"代号"', name="A"),
        FakeNote("", linked_text="$PRPSHEET:{名称}", name="B"),
        FakeNote("", linked_text="$PRPSHEET:{材料}", name="C"),
    ])

    fields = collect_existing_title_block_fields(drawing)

    assert set(fields) == {"drawingNumber", "name", "material"}


def test_setup_sheet6_removes_old_template_notes_and_keeps_program_note(tmp_path):
    template = tmp_path / "a3 - gb.slddrt"
    template.write_bytes(b"sheet format")
    old_template_note = FakeNote(
        "OLD",
        linked_text='$PRPSHEET:"名称"',
        name="细节项目100",
        position=(0.10, 0.03, 0.0),
    )
    user_note = FakeNote(
        "USER",
        linked_text="$PRPSHEET:{Description}",
        name="CAD_TITLE__name",
        position=(0.35, 0.06, 0.0),
    )
    plain_user_note = FakeNote(
        "PLAIN USER",
        name="UserNoteProbe",
        position=(0.05, 0.20, 0.0),
    )
    new_template_note = FakeNote(
        "NEW",
        linked_text='$PRPSHEET:"名称"',
        name="细节项目101",
        position=(0.38, 0.03, 0.0),
    )

    class Sheet:
        def __init__(self):
            self.replaced = False

        def GetName(self):
            return "图纸1"

        def GetTemplateName(self):
            return str(template) if self.replaced else "old-a4.slddrt"

        def GetProperties2(self):
            return (8, 12, 1, 1, True, .420, .297, True) if self.replaced else (
                6, 12, 1, 1, True, .297, .210, True
            )

    class Drawing:
        def __init__(self):
            self.sheet = Sheet()
            self.view = FakeView([old_template_note, user_note, plain_user_note])
            self.args = None

        def GetCurrentSheet(self):
            return self.sheet

        def GetFirstView(self):
            return self.view

        def SetupSheet6(self, *args):
            self.args = args
            self.sheet.replaced = True
            self.view.notes = [new_template_note, user_note, plain_user_note]
            return True

        def ForceRebuild3(self, _top_only):
            return True

    drawing = Drawing()
    result = setup_current_sheet(
        drawing,
        [template],
        paper_size="A3",
        projection="first_angle",
        require_gbt=True,
    )

    assert result["status"] == "pass"
    assert result["remove_modified_notes"] is True
    assert result["program_notes_preserved"] == 1
    assert result["user_notes_preserved"] == 1
    assert result["residual_template_note_count"] == 0
    assert drawing.args[:7] == ("图纸1", 8, 12, 1.0, 1.0, True, str(template.resolve()))
    assert drawing.args[10] is True


def test_setup_sheet6_deleting_user_note_is_reported(tmp_path):
    template = tmp_path / "a3 - gb.slddrt"
    template.write_bytes(b"sheet format")
    plain_user_note = FakeNote(
        "MUST SURVIVE",
        name="UserNoteProbe",
        position=(0.05, 0.20, 0.0),
    )
    new_template_note = FakeNote(
        "NEW",
        linked_text='$PRPSHEET:"名称"',
        name="细节项目101",
        position=(0.38, 0.03, 0.0),
    )

    class Sheet:
        def GetName(self):
            return "图纸1"

        def GetTemplateName(self):
            return str(template)

        def GetProperties2(self):
            return (8, 12, 1, 1, True, .420, .297, True)

    class Drawing:
        def __init__(self):
            self.sheet = Sheet()
            self.view = FakeView([plain_user_note])

        def GetCurrentSheet(self):
            return self.sheet

        def GetFirstView(self):
            return self.view

        def SetupSheet6(self, *_args):
            self.view.notes = [new_template_note]
            return True

        def ForceRebuild3(self, _top_only):
            return True

    result = setup_current_sheet(
        Drawing(),
        [template],
        paper_size="A3",
        projection="first_angle",
        require_gbt=True,
    )

    assert result["status"] == "failed"
    assert result["error_code"] == "DRAWING_SHEET_USER_NOTES_LOST"
    assert result["lost_user_notes"][0][0] == "UserNoteProbe"
