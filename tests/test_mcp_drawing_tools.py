"""工程图 MCP 工具注册和输入契约测试。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MCP_SERVER = ROOT / "mcp-server"
if str(MCP_SERVER) not in sys.path:
    sys.path.insert(0, str(MCP_SERVER))

import server  # noqa: E402
from scripts.drawing_spec import validate_drawing_spec  # noqa: E402
from scripts.sw_drawing import generate_drawing_package  # noqa: E402
from scripts.validate_mcp import REQUIRED_TOOLS  # noqa: E402


def test_drawing_mcp_tools_are_registered():
    tools = server.mcp._tool_manager._tools

    assert {"solidworks_generate_drawing", "solidworks_review_drawing", "solidworks_inspect_drawing"} <= set(tools)


def test_release_mcp_gate_requires_drawing_tools():
    """@brief 发布验证清单必须覆盖三个工程图 MCP 工具。"""
    assert {"solidworks_generate_drawing", "solidworks_review_drawing", "solidworks_inspect_drawing"} <= REQUIRED_TOOLS


def test_generate_drawing_input_rejects_non_drawing_spec(tmp_path: Path):
    source = tmp_path / "spec.txt"
    source.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="DrawingSpec"):
        server.SolidWorksGenerateDrawingInput(spec_path=str(source), output_dir=str(tmp_path / "out"))


def test_drawing_spec_validation_can_be_used_without_loading_com(tmp_path: Path):
    source = tmp_path / "drawing.json"
    source.write_text(json.dumps({"schemaVersion": "1.0"}), encoding="utf-8")

    result = validate_drawing_spec(str(source))

    assert result["status"] == "blocked"


def test_generate_tool_routes_to_managed_package_without_new_tool_name(tmp_path, monkeypatch):
    source = tmp_path / "spec.json"
    source.write_text("{}", encoding="utf-8")
    calls = []
    monkeypatch.setattr(server, "_run_locked", lambda operation, response_format: operation())

    def backend(spec_path, output_dir, drawing_filename, *, overwrite, drawing_template_path=None):
        calls.append((spec_path, output_dir, drawing_filename, overwrite, drawing_template_path))
        return {"status": "review_required", "native_validation": "pass"}

    monkeypatch.setattr(server, "drawing_generate_package", backend, raising=False)
    result = server.solidworks_generate_drawing(server.SolidWorksGenerateDrawingInput(spec_path=str(source), output_dir=str(tmp_path / "out")))
    assert result["native_validation"] == "pass"
    assert len(calls) == 1


def test_generate_tool_forwards_explicit_drawing_template(tmp_path, monkeypatch):
    source = tmp_path / "spec.json"
    source.write_text("{}", encoding="utf-8")
    calls = []
    monkeypatch.setattr(server, "_run_locked", lambda operation, response_format: operation())

    def backend(spec_path, output_dir, drawing_filename, *, overwrite, drawing_template_path=None):
        calls.append(drawing_template_path)
        return {"status": "blocked"}

    monkeypatch.setattr(server, "drawing_generate_package", backend, raising=False)
    server.solidworks_generate_drawing(server.SolidWorksGenerateDrawingInput(
        spec_path=str(source),
        output_dir=str(tmp_path / "out"),
        drawing_template_path=r"C:\templates\gb_a3.drwdot",
    ))

    assert calls == [r"C:\templates\gb_a3.drwdot"]


def test_compat_package_entry_forwards_explicit_drawing_template(tmp_path, monkeypatch):
    """@brief MCP 使用的兼容入口也必须把显式模板传给底层出图包。"""
    import scripts.sw_drawing_package as package

    calls = []

    def backend(spec_path, output_dir, drawing_filename, *, overwrite, drawing_template_path=None):
        calls.append({
            "spec_path": spec_path,
            "output_dir": output_dir,
            "drawing_filename": drawing_filename,
            "overwrite": overwrite,
            "drawing_template_path": drawing_template_path,
        })
        return {"status": "blocked"}

    monkeypatch.setattr(package, "generate_package", backend)
    result = generate_drawing_package(
        str(tmp_path / "spec.json"),
        str(tmp_path / "out"),
        "user.drwdrw",
        drawing_template_path=r"C:\templates\gb_a3.drwdot",
    )

    assert result["status"] == "blocked"
    assert calls == [{
        "spec_path": str(tmp_path / "spec.json"),
        "output_dir": str(tmp_path / "out"),
        "drawing_filename": "user.drwdrw",
        "overwrite": False,
        "drawing_template_path": r"C:\templates\gb_a3.drwdot",
    }]
