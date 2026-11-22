"""受控 DrawingSpec 出图包：创建、保存重开、原生核验及 PDF 制造交付审视。"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.drawing_spec import validate_drawing_spec
from scripts.sw_connect import activate_document, get_com_member, save_document
from scripts.sw_document_data import set_custom_properties
from scripts.sw_file_rename import _valid_filename
from scripts.sw_read_guard import SolidWorksReadGuard
from scripts.sw_rename_copy import _open_checked, _sha256
from scripts.sw_session import SolidWorksSession


DRAWING_STATE_MARKER = "__SOLIDWORKS_DRAWING_STATE__"


def _perform_drawing_state_action(action: str, drawing_path: str | Path) -> dict:
    """Run one document-state action in an otherwise fresh parent process."""
    path = Path(drawing_path).expanduser().resolve(strict=True)
    with SolidWorksReadGuard(), SolidWorksSession(
        version=None,
        visible=True,
        max_documents=9,
    ) as session:
        if action == "stabilize":
            drawing = session.open(
                str(path),
                read_only=False,
                silent=True,
            )
            before = bool(get_com_member(drawing, "GetSaveFlag"))
            saved = bool(save_document(drawing))
            after = bool(get_com_member(drawing, "GetSaveFlag"))
            return {
                "status": "pass" if saved and not after else "failed",
                "action": action,
                "path": str(path),
                "save_flag_before": before,
                "save3": saved,
                "save_flag_after": after,
            }
        if action == "verify":
            drawing = session.open(
                str(path),
                read_only=True,
                silent=True,
            )
            save_flag = bool(get_com_member(drawing, "GetSaveFlag"))
            read_only = bool(get_com_member(drawing, "IsOpenedReadOnly"))
            return {
                "status": "pass" if read_only and not save_flag else "failed",
                "action": action,
                "path": str(path),
                "read_only": read_only,
                "save_flag": save_flag,
                "sheet_count": len(
                    list(get_com_member(drawing, "GetSheetNames") or [])
                ),
            }
    raise ValueError(f"未知工程图状态动作: {action}")


def _run_drawing_state_action(action: str, drawing_path: Path) -> dict:
    completed = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--drawing-state-action",
            action,
            "--drawing-path",
            str(drawing_path),
        ],
        cwd=str(Path(__file__).resolve().parents[1]),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        timeout=120,
        check=False,
    )
    for line in reversed(completed.stdout.splitlines()):
        if line.startswith(DRAWING_STATE_MARKER):
            return json.loads(line[len(DRAWING_STATE_MARKER):])
    return {
        "status": "failed",
        "action": action,
        "exit_code": completed.returncode,
        "stdout": completed.stdout[-4000:],
        "stderr": completed.stderr[-4000:],
    }


def generate_package(
    spec_source,
    output_dir,
    drawing_filename="drawing.slddrw",
    *,
    overwrite=False,
    drawing_template_path=None,
):
    from scripts.sw_drawing import (
        validate_generic_drawing_generation,
        generate_drawing_from_spec,
        inspect_drawing_structure,
        export_sheet_to_pdf,
        resolve_title_block_fields,
        resolve_drawing_template,
    )
    from scripts.sw_drawing_review import review_drawing_artifacts
    from scripts.sw_review import save_review_previews, inspect_bmp_preview, collect_geometry_measurements
    from scripts.sw_gdt_copy import _capture_saved_positions, _verify_reopened
    from scripts.sw_drawing_native import verify_dimensions
    from scripts.sw_drawing_sheet_metal import (
        add_flat_pattern_sheet,
        add_forming_dimensions,
        add_forming_information,
        analyze_flat_pattern_dxf,
        sheet_metal_layout_decision,
        verify_sheet_metal_drawing,
        _set_scale as set_sheet_scale,
    )

    validation = validate_drawing_spec(spec_source)
    if not isinstance(overwrite, bool):
        raise ValueError("overwrite 必须是布尔值")
    if validation["status"] == "blocked":
        return validation
    spec = validation["spec"]
    sheet_metal = (
        dict(spec.get("sheetMetal") or {})
        if spec.get("documentType") == "sheet_metal"
        else None
    )
    sheet_metal_enabled = bool(sheet_metal and sheet_metal.get("enabled", True))
    sheet_metal_layout = None
    flat_analysis = None
    if sheet_metal_enabled:
        flat_evidence = Path(
            str(sheet_metal.get("flatPatternEvidencePath") or "")
        ).expanduser()
        if not flat_evidence.is_file():
            return {
                "status": "blocked",
                "stage": "sheet_metal",
                "error_code": "DRAWING_SHEET_METAL_FLAT_PATTERN_EVIDENCE_MISSING",
            }
        flat_analysis = analyze_flat_pattern_dxf(flat_evidence)
        sheet_metal_layout = sheet_metal_layout_decision(spec, flat_analysis)
        if sheet_metal_layout.get("status") != "pass":
            return sheet_metal_layout
        spec["paperSize"] = sheet_metal_layout["paper_size"]
        spec["scale"] = sheet_metal_layout["formed_scale"]
        spec["insertModelDimensions"] = False
    capability = validate_generic_drawing_generation(spec)
    if capability["status"] != "pass":
        return capability
    source = Path(spec["sourceModel"]).expanduser().resolve(strict=True)
    if source.suffix.casefold() != (".sldasm" if spec["documentType"] == "assembly" else ".sldprt"):
        raise ValueError("源文件类型与 DrawingSpec.documentType 不一致")
    if Path(drawing_filename).name != drawing_filename or not _valid_filename(drawing_filename) or Path(drawing_filename).suffix.casefold() != ".slddrw":
        raise ValueError("drawing_filename 必须是合法的 SLDDRW 文件名")
    output = Path(output_dir).expanduser().resolve()
    drawing_path = output / drawing_filename
    pdf_path = drawing_path.with_suffix(".pdf")
    report_path = output / (drawing_path.stem + "_review_report.json")
    for path in (drawing_path, pdf_path, report_path):
        if path.is_symlink() or (path.exists() and not overwrite):
            raise ValueError("输出已存在或为符号链接，拒绝覆盖")
    advanced_native = any(
        (spec.get("professionalAnnotations") or {}).get(key)
        for key in ("datums", "geometricTolerances")
    )
    native = bool(spec.get("requiredDimensions")) or advanced_native
    requested_source = source
    working_source = source
    if sheet_metal_enabled and sheet_metal.get("useIndependentCopy", True):
        output.mkdir(parents=True, exist_ok=True)
        source_copy_dir = output / "_source"
        source_copy = source_copy_dir / f"{source.stem}_drawing_source{source.suffix}"
        if source_copy.exists():
            raise ValueError(f"独立源副本已存在，拒绝覆盖: {source_copy}")
        source_copy_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, source_copy)
        if _sha256(source) != _sha256(source_copy):
            raise RuntimeError("独立源副本与实际源文件 SHA-256 不一致")
        working_source = source_copy
        spec["sourceModel"] = str(source_copy)
    hashes = {requested_source: _sha256(requested_source)}
    if working_source != requested_source:
        hashes[working_source] = _sha256(working_source)
    result = {"status": "blocked", "capability": "solidworks-engineering-drawing", "sourceModel": str(requested_source),
              "workingSourceModel": str(working_source),
              "outputs": {}, "manual_review_required": True}
    try:
        # The package needs one owned temporary drawing even when the user's
        # normal document budget is already full. The session closes that
        # drawing on exit, while pre-existing user documents remain untouched.
        with SolidWorksReadGuard(), SolidWorksSession(
            version=None,
            visible=True,
            max_documents=9,
        ) as session:
            # 排队等待锁期间可能有其他进程完成同名输出；不得覆盖其结果或报告。
            if any(path.is_symlink() or (path.exists() and not overwrite) for path in (drawing_path, pdf_path, report_path)):
                return {**result, "error_code": "DRAWING_OUTPUT_EXISTS", "message": "等待期间同名输出已出现，拒绝覆盖"}
            template_resolution = resolve_drawing_template(
                session.sw,
                paper_size=spec.get("paperSize"),
                explicit_template=drawing_template_path or spec.get("drawingTemplatePath"),
                template_candidates=(
                    spec.get("drawingTemplateCandidates")
                    or spec.get("templateCandidates")
                    or ()
                ),
                standard=spec.get("standard", "GB_T"),
            )
            if template_resolution.get("status") != "pass":
                result.update(
                    status="blocked",
                    stage="template",
                    templateResolution=template_resolution,
                    error_code=template_resolution.get("error_code"),
                )
                return result
            if spec.get("paperSize") is None:
                spec["paperSize"] = template_resolution["paper_size"]
            elif template_resolution.get("paper_size") != spec.get("paperSize"):
                result.update(
                    status="blocked",
                    stage="template",
                    templateResolution=template_resolution,
                    error_code="DRAWING_TEMPLATE_SIZE_MISMATCH",
                )
                return result
            result["templateResolution"] = template_resolution
            title_property_seeding = None
            title_request = dict(spec.get("titleBlock") or {})
            if sheet_metal_enabled:
                properties = {
                    "代号": str(title_request.get("drawingNumber") or source.stem),
                    "PartNumber": str(title_request.get("drawingNumber") or source.stem),
                    "名称": str(title_request.get("name") or source.stem),
                    "Description": str(title_request.get("name") or source.stem),
                }
                for aliases, field in (
                    (("材料", "Material"), "material"),
                ):
                    value = str(title_request.get(field) or "").strip()
                    if value:
                        properties.update({alias: value for alias in aliases})
                if properties:
                    writable_model = _open_checked(
                        session,
                        working_source,
                        read_only=False,
                    )
                    title_property_seeding = set_custom_properties(
                        writable_model,
                        properties,
                        save=True,
                    )
                    if not title_property_seeding.get("success"):
                        raise RuntimeError("钣金标题栏模型属性写入或回读失败")
                    session.close(model=writable_model)
                    hashes[working_source] = _sha256(working_source)
            model = _open_checked(session, working_source)
            if (
                get_com_member(model, "GetSaveFlag") not in (False, 0)
                and not bool(get_com_member(model, "IsOpenedReadOnly"))
            ):
                raise ValueError("源模型存在未保存修改")
            title_property_evidence = None
            if (spec.get("titleBlock") or {}).get("required"):
                spec["titleBlock"], title_property_evidence = resolve_title_block_fields(
                    model,
                    spec.get("titleBlock") or {},
                )
            expected_type = 2 if spec["documentType"] == "assembly" else 1
            if get_com_member(model, "GetType") != expected_type:
                raise ValueError("源模型实际类型与规格不一致")
            dependencies = get_com_member(model, "GetDependencies2", True, True, False)
            if not isinstance(dependencies, (list, tuple)) or len(dependencies) % 2:
                raise ValueError("不能确认模型依赖清单")
            for index in range(1, len(dependencies), 2):
                path = Path(str(dependencies[index])).resolve(strict=True)
                hashes[path] = _sha256(path)
            if native:
                from scripts.sw_measure import collect_bounding_box
                bounds = collect_bounding_box(model)
                if bounds.get("errors") or len(bounds.get("size_mm") or []) != 3 or any(not math.isclose(a, b, abs_tol=.01, rel_tol=0) for a, b in zip(bounds["size_mm"], spec["modelSizeMm"])):
                    raise ValueError("modelSizeMm 与真实模型包围盒不一致")
            for document in session._documents():
                path = str(get_com_member(document, "GetPathName") or "")
                title = str(get_com_member(document, "GetTitle") or "")
                if (Path(path).name.casefold() == drawing_path.name.casefold() or title.casefold() in {drawing_path.name.casefold(), drawing_path.stem.casefold()}):
                    raise ValueError("已打开同名输出文档，拒绝复用或关闭用户文档")
            output.mkdir(parents=True, exist_ok=True)
            drawing = session.new_drawing(template_path=template_resolution["selected"])
            context = {}
            format_candidates = (
                [template_resolution["sheet_format_path"]]
                if template_resolution.get("mode") == "sheet_format"
                else None
            )
            generation = generate_drawing_from_spec(drawing, spec, str(working_source), template_candidates=format_candidates,
                                                    sw_app=session.sw, source_model=model,
                                                    initial_save_path=drawing_path, evidence_context=context)
            if generation.get("status") in {"failed", "blocked"}:
                result.update(generation=generation, error_code=generation.get("error_code"), stage=generation.get("stage"))
            else:
                sheet_metal_generation = None
                sheet_metal_verification = None
                if sheet_metal_enabled:
                    drawing = activate_document(session.sw, drawing)
                    first_sheet = get_com_member(drawing, "GetCurrentSheet")
                    set_sheet_scale(
                        first_sheet,
                        1.0,
                        float(sheet_metal_layout["formed_scale"]) ** -1,
                    )
                    forming_dimensions = add_forming_dimensions(drawing)
                    forming_information = add_forming_information(
                        drawing, flat_analysis
                    )
                    flat_result = add_flat_pattern_sheet(
                        drawing,
                        sw_app=session.sw,
                        part=model,
                        part_path=working_source,
                        spec=spec,
                        paper_size=sheet_metal_layout["paper_size"],
                        source_sheet=first_sheet,
                        format_output_path=(
                            output
                            / "_format"
                            / (
                                f"{sheet_metal_layout['paper_size'].lower()}"
                                "_gb.slddrt"
                            )
                        ),
                        coordinate_table_layout=sheet_metal_layout,
                    )
                    if flat_result.get("status") != "pass":
                        result.update(
                            status="blocked",
                            stage="sheet_metal",
                            sheetMetal=flat_result,
                            error_code=flat_result.get("error_code"),
                        )
                        return result
                    sheet_metal_generation = {
                        "layout": sheet_metal_layout,
                        "formingDimensions": forming_dimensions,
                        "formingInformation": forming_information,
                        "flatPattern": flat_result,
                    }
                if not get_com_member(drawing, "ForceRebuild3", False) or not session.save(drawing, str(drawing_path)):
                    raise RuntimeError("最终工程图重建或保存失败")
                if get_com_member(drawing, "GetSaveFlag") not in (False, 0):
                    if not save_document(drawing):
                        raise RuntimeError("最终工程图稳定化保存失败")
                    if get_com_member(drawing, "GetSaveFlag") not in (False, 0):
                        raise RuntimeError("最终工程图稳定化保存后仍为未保存状态")
                records = context.get("native_records") or []
                _capture_saved_positions(records)
                dimensions = context.get("dimensions") or {}
                for record in dimensions.values():
                    record["saved_position"] = get_com_member(get_com_member(record["object"], "GetAnnotation"), "GetPosition")
                session.close(model=drawing)
                drawing = _open_checked(session, drawing_path, read_only=False)
                first_reopen_dirty = get_com_member(drawing, "GetSaveFlag") not in (False, 0)
                if not bool(get_com_member(model, "IsOpenedReadOnly")):
                    raise RuntimeError("工程图稳定化保存前无法证明源模型只读")
                # Saving by path uses SaveAs and can leave the in-memory document
                # dirty. Always perform one native Save3 on the normal reopen.
                if not save_document(drawing):
                    raise RuntimeError("工程图稳定化保存失败")
                if get_com_member(drawing, "GetSaveFlag") not in (False, 0):
                    raise RuntimeError("工程图稳定化 Save3 后仍为未保存状态")
                session.close(model=drawing)
                drawing = _open_checked(session, drawing_path, read_only=True)
                final_reopen_dirty = get_com_member(drawing, "GetSaveFlag") not in (False, 0)
                reopen_evidence = {
                    "status": "pass" if not final_reopen_dirty else "review_required",
                    "first_normal_reopen_dirty": first_reopen_dirty,
                    "stabilizing_save_method": "Save3",
                    "stabilizing_save_performed": True,
                    "final_read_only_save_flag": bool(final_reopen_dirty),
                    "final_read_only": bool(get_com_member(drawing, "IsOpenedReadOnly")),
                }
                if native and not sheet_metal_enabled:
                    from scripts.sw_drawing_native import map_views
                    sheet = get_com_member(drawing, "GetCurrentSheet")
                    properties = get_com_member(sheet, "GetProperties2")
                    if len(properties) != 8 or not math.isclose(properties[2] / properties[3], generation["layout"]["scale"], abs_tol=1e-8, rel_tol=0):
                        raise RuntimeError("重开后图纸比例不一致")
                    for view in map_views(drawing, generation["views"]).values():
                        ratio = get_com_member(view, "ScaleRatio")
                        if not math.isclose(ratio[0] / ratio[1], generation["layout"]["scale"], abs_tol=1e-8, rel_tol=0):
                            raise RuntimeError("重开后视图比例不一致")
                _verify_reopened(drawing, records)
                verify_dimensions(drawing, dimensions)
                if sheet_metal_enabled:
                    sheet_metal_verification = verify_sheet_metal_drawing(
                        drawing,
                        analysis=flat_analysis,
                        formed_paper_size=sheet_metal_layout["paper_size"],
                        flat_paper_size=sheet_metal_layout["paper_size"],
                        formed_scale=float(sheet_metal_layout["formed_scale"]),
                        flat_scale=float(sheet_metal_layout["flat_scale"]),
                    )
                structure = inspect_drawing_structure(drawing, paper_size_hint=spec["paperSize"], title_block_box=generation["layout"].get("title_block_box"))
                sheet_setup = generation.get("sheetSetup") or {}
                if sheet_setup.get("mode") == "default_template" and not sheet_metal_enabled:
                    size = structure.get("sheet_size") or {}
                    expected_size = sheet_setup["sheet_size_m"]
                    if (structure.get("sheet_size_source") != "GetProperties2"
                            or structure.get("projection") != spec["projection"]
                            or structure.get("template_path") != sheet_setup["template_path"]
                            or any(not math.isclose(size.get(key, 0), value, abs_tol=1e-9, rel_tol=0)
                                   for key, value in zip(("width_m", "height_m"), expected_size))):
                        raise RuntimeError("重开后默认模板的图纸格式、尺寸或投影方式不一致")
                generation["structure"] = structure
                pdf_ok = export_sheet_to_pdf(drawing, str(pdf_path), sw_app=session.sw)
                previews = save_review_previews(drawing, output / "previews", basename=drawing_path.stem, views=("front",))
                preview_evidence = [inspect_bmp_preview(path) for path in previews]
                # PDF export can dirty SolidWorks' in-memory view state even on a
                # read-only reopen. Stabilize the file after the final export,
                # then verify with a separate read-only reopen as the last
                # document operation.
                session.close(model=drawing)
                drawing = _open_checked(session, drawing_path, read_only=False)
                if not save_document(drawing):
                    raise RuntimeError("PDF 后工程图稳定化 Save3 失败")
                if get_com_member(drawing, "GetSaveFlag") not in (False, 0):
                    raise RuntimeError("PDF 后工程图稳定化 Save3 仍为未保存状态")
                session.close(model=drawing)
                drawing = _open_checked(session, drawing_path, read_only=True)
                post_export_save_flag = get_com_member(drawing, "GetSaveFlag") not in (False, 0)
                reopen_evidence.update(
                    {
                        "pdf_export_before_final_reopen": True,
                        "post_pdf_stabilizing_save_method": "Save3",
                        "post_pdf_save_flag": bool(post_export_save_flag),
                        "final_state": (
                            "clean"
                            if not post_export_save_flag
                            else "dirty"
                        ),
                    }
                )
                if post_export_save_flag:
                    raise RuntimeError("PDF 后最终只读重开仍为未保存状态")
                geometry = collect_geometry_measurements(model) if spec.get("holeRequirements") else None
                review = review_drawing_artifacts(spec, structure=structure, pdf_path=pdf_path if pdf_ok else None,
                                                 preview_evidence=preview_evidence, model_evidence=geometry)
                status = review.get("status", "review_required")
                if sheet_metal_verification and sheet_metal_verification.get("status") != "pass":
                    status = "review_required"
                if advanced_native and status == "pass":
                    status = "review_required"
                if (
                    get_com_member(model, "GetSaveFlag") not in (False, 0)
                    and not bool(get_com_member(model, "IsOpenedReadOnly"))
                ):
                    raise RuntimeError("出图期间源模型出现未保存修改")
                result.update(status=status, generation=generation, review=review, native_validation="pass",
                              manual_review_required=advanced_native or bool(review.get("manual_review_required", True)),
                              title_block_property_evidence=title_property_evidence,
                              titlePropertySeeding=title_property_seeding,
                              reopenValidation=reopen_evidence,
                              sheetMetalGeneration=sheet_metal_generation,
                              sheetMetalVerification=sheet_metal_verification,
                              outputs={"slddrw": {"path": str(drawing_path), "exists": drawing_path.is_file(), "size_bytes": drawing_path.stat().st_size if drawing_path.is_file() else 0},
                                       "pdf": {"path": str(pdf_path), "exists": pdf_path.is_file(), "size_bytes": pdf_path.stat().st_size if pdf_path.is_file() else 0}, "previews": preview_evidence})
                if status in {"blocked", "failed", "fail"}:
                    result["draftArtifacts"] = result.pop("outputs")
                    result["outputs"] = {}
    except Exception as error:
        result.update(status="blocked", error_code="DRAWING_PACKAGE_FAILED", message=f"{type(error).__name__}: {error}", outputs={})
    if (
        sheet_metal_enabled
        and drawing_path.is_file()
        and result.get("status") in {"pass", "review_required"}
    ):
        stabilization = _run_drawing_state_action("stabilize", drawing_path)
        # SolidWorks can keep the closing document reachable for a short time
        # after the stabilizing process exits. Let that teardown complete
        # before launching the independent read-only verifier.
        time.sleep(5.0)
        verification = _run_drawing_state_action("verify", drawing_path)
        external_evidence = {
            "stabilization": stabilization,
            "read_only_verification": verification,
        }
        existing = dict(result.get("reopenValidation") or {})
        existing["fresh_process"] = external_evidence
        if verification.get("status") != "pass":
            existing["status"] = "review_required"
            result["status"] = "review_required"
        result["reopenValidation"] = existing
        outputs = result.get("outputs") or {}
        for key, path in (("slddrw", drawing_path), ("pdf", pdf_path)):
            if key in outputs and path.is_file():
                outputs[key]["exists"] = True
                outputs[key]["size_bytes"] = path.stat().st_size
    if any(_sha256(path) != digest for path, digest in hashes.items()):
        result.update(status="blocked", error_code="DRAWING_SOURCE_CHANGED", outputs={})
    if output.is_dir() and not report_path.is_symlink() and (overwrite or not report_path.exists()):
        result["reportPath"] = str(report_path)
        report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main(argv=None):
    import argparse
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    if raw_argv and raw_argv[0] == "--drawing-state-action":
        action_parser = argparse.ArgumentParser()
        action_parser.add_argument("--drawing-state-action", required=True)
        action_parser.add_argument("--drawing-path", required=True)
        action_args = action_parser.parse_args(raw_argv)
        try:
            state = _perform_drawing_state_action(
                action_args.drawing_state_action,
                action_args.drawing_path,
            )
        except Exception as error:
            state = {
                "status": "failed",
                "action": action_args.drawing_state_action,
                "path": action_args.drawing_path,
                "error": f"{type(error).__name__}: {error}",
            }
        print(DRAWING_STATE_MARKER + json.dumps(state, ensure_ascii=True))
        return 0 if state.get("status") == "pass" else 1
    parser = argparse.ArgumentParser(description="从结构化 DrawingSpec 自动创建并重开核验原生工程图")
    parser.add_argument("--spec", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--filename", default="drawing.slddrw")
    parser.add_argument("--drawing-template", default=None, help="显式 .drwdot 模板路径")
    args = parser.parse_args(argv)
    result = generate_package(
        args.spec,
        args.output_dir,
        args.filename,
        drawing_template_path=args.drawing_template,
    )
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result["status"] == "pass" else 2 if result["status"] in {"pilot", "review_required"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
