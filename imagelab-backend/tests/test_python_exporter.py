"""Tests for Python Pipeline Exporter service and API endpoint."""

import ast
import os
import subprocess
import sys
import tempfile

import cv2
import numpy as np

from app.models.graph import GraphEdge, GraphNode, PipelineGraph
from app.models.pipeline import PipelineStep
from app.operators.registry import OPERATOR_REGISTRY
from app.services.python_exporter import (
    export_graph_to_python,
    export_pipeline_to_python,
    get_unsupported_operators,
)

EXPORT_ENDPOINT = "/api/v1/pipeline/export-python"


def test_all_registered_operators_emit_valid_python_syntax():
    """Verify that every single operator in OPERATOR_REGISTRY generates valid Python AST."""
    for op_name in OPERATOR_REGISTRY:
        step = PipelineStep(type=op_name, params={})
        code, unsupported = export_pipeline_to_python([step], f"Test {op_name}")
        assert unsupported == [], f"Operator {op_name} reported as unsupported"
        try:
            tree = ast.parse(code)
            assert isinstance(tree, ast.Module)
        except SyntaxError as e:
            raise AssertionError(f"Operator {op_name} produced invalid Python code:\n{code}") from e


def test_unsupported_operator_reported_and_commented():
    """Verify unsupported operator is recorded and gracefully commented out."""
    step = PipelineStep(type="non_existent_future_operator", params={"val": 42})
    unsupported_list = get_unsupported_operators([step])
    assert unsupported_list == ["non_existent_future_operator"]

    code, unsupported = export_pipeline_to_python([step], "Unknown Operator Pipeline")
    assert unsupported == ["non_existent_future_operator"]
    assert "Unsupported operator 'non_existent_future_operator'" in code

    # The rest of the script is still syntactically valid
    ast.parse(code)


def test_macro_blend_code_generation():
    """Verify macro_blend generates branch logic, dimension checks, and cv2.addWeighted."""
    step = PipelineStep(
        type="macro_blend",
        params={"alpha": 0.6, "beta": 0.4, "gamma": 1.0},
        branches={
            "left": [PipelineStep(type="blurring_applygaussianblur", params={"widthSize": 5, "heightSize": 5})],
            "right": [PipelineStep(type="imageconvertions_grayimage", params={})],
        },
    )
    code, unsupported = export_pipeline_to_python([step], "Blend Pipeline")
    assert unsupported == []
    assert "cv2.addWeighted" in code
    assert "cv2.resize" in code
    assert "0.6" in code
    assert "0.4" in code
    ast.parse(code)


def test_macro_if_else_code_generation():
    """Verify macro_if_else generates conditional branching."""
    step = PipelineStep(
        type="macro_if_else",
        params={"metric": "mean_brightness", "comparator": ">", "threshold": 128},
        branches={
            "then": [PipelineStep(type="imageconvertions_invertimage", params={})],
            "else": [PipelineStep(type="blurring_applymedianblur", params={"kernelSize": 5})],
        },
    )
    code, unsupported = export_pipeline_to_python([step], "If Else Pipeline")
    assert unsupported == []
    assert "if float(cv2.mean(image)[0]) > 128.0:" in code
    assert "cv2.bitwise_not(image)" in code
    assert "cv2.medianBlur" in code
    ast.parse(code)


def test_numpy_import_deduplication():
    """Only import numpy if operators require numpy features."""
    # Pipeline without numpy requirements
    pure_cv_steps = [
        PipelineStep(type="blurring_applygaussianblur", params={"widthSize": 3, "heightSize": 3}),
        PipelineStep(type="imageconvertions_grayimage", params={}),
    ]
    code_pure, _ = export_pipeline_to_python(pure_cv_steps)
    assert "import cv2" in code_pure
    assert "import numpy as np" not in code_pure

    # Pipeline with numpy requirement (sharpen filter)
    sharpen_steps = [
        PipelineStep(type="filtering_sharpen", params={"strength": 2.0}),
    ]
    code_np, _ = export_pipeline_to_python(sharpen_steps)
    assert "import cv2" in code_np
    assert "import numpy as np" in code_np


def test_export_graph_to_python():
    """Verify PipelineGraph can be compiled and exported directly."""
    graph = PipelineGraph(
        nodes=[
            GraphNode(id="n1", type="blurring_applyblur", params={"widthSize": 3, "heightSize": 3}),
            GraphNode(id="n2", type="imageconvertions_grayimage", params={}),
        ],
        edges=[
            GraphEdge(from_node="n1", to_node="n2"),
        ],
    )
    code, unsupported = export_graph_to_python(graph, pipeline_name="Graph Export Pipeline")
    assert unsupported == []
    assert "cv2.blur" in code
    assert "Convert to Grayscale" in code
    ast.parse(code)


def test_end_to_end_script_execution():
    """Execute the exported Python script in a subprocess and verify output image generation."""
    steps = [
        PipelineStep(
            type="macro_blend",
            params={"alpha": 0.5, "beta": 0.5},
            branches={
                "left": [PipelineStep(type="blurring_applygaussianblur", params={"widthSize": 5, "heightSize": 5})],
                "right": [PipelineStep(type="imageconvertions_grayimage", params={})],
            },
        ),
        PipelineStep(
            type="macro_if_else",
            params={"metric": "mean_brightness", "comparator": ">", "threshold": 50},
            branches={
                "then": [PipelineStep(type="imageconvertions_invertimage", params={})],
                "else": [PipelineStep(type="filtering_sharpen", params={"strength": 1.0})],
            },
        ),
    ]

    code, _ = export_pipeline_to_python(steps, "Execution Test Pipeline")

    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = os.path.join(tmpdir, "run_script.py")
        input_path = os.path.join(tmpdir, "test_input.png")
        output_path = os.path.join(tmpdir, "test_output.png")

        # Create synthetic 80x80 BGR image
        test_img = np.full((80, 80, 3), 150, dtype=np.uint8)
        cv2.imwrite(input_path, test_img)

        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code)

        result = subprocess.run(
            [sys.executable, script_path, "--input", input_path, "--output", output_path],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Script failed: {result.stderr}"
        assert os.path.exists(output_path), "Output image was not generated"

        saved_img = cv2.imread(output_path)
        assert saved_img is not None
        assert saved_img.shape[:2] == (80, 80)


def test_exported_sepia_matches_the_operator():
    """The exported script must give the same image as the app for Sepia, with and without alpha."""
    bgr = np.zeros((16, 16, 3), dtype=np.uint8)
    bgr[:, :, 0] = np.arange(0, 256, 16, dtype=np.uint8)
    bgr[:, :, 1] = 100
    bgr[:, :, 2] = 30
    bgra = np.dstack([bgr, np.full((16, 16), 128, dtype=np.uint8)])

    for params in ({"intensity": 1.0}, {"intensity": 0.5}):
        code, _ = export_pipeline_to_python([PipelineStep(type="augmentation_sepiafilter", params=params)], "Sepia")
        for test_img in (bgr, bgra):
            with tempfile.TemporaryDirectory() as tmpdir:
                script_path = os.path.join(tmpdir, "run_script.py")
                input_path = os.path.join(tmpdir, "input.png")
                output_path = os.path.join(tmpdir, "output.png")
                cv2.imwrite(input_path, test_img)
                with open(script_path, "w", encoding="utf-8") as f:
                    f.write(code)

                result = subprocess.run(
                    [sys.executable, script_path, "--input", input_path, "--output", output_path],
                    capture_output=True,
                    text=True,
                )
                assert result.returncode == 0, f"Script failed: {result.stderr}"

                expected = OPERATOR_REGISTRY["augmentation_sepiafilter"](params).compute(test_img)
                np.testing.assert_array_equal(cv2.imread(output_path, cv2.IMREAD_UNCHANGED), expected)


def test_api_export_python_pipeline_request(client):
    """Test POST /api/v1/pipeline/export-python with pipeline steps."""
    payload = {
        "pipeline_name": "My Custom Pipeline",
        "input_filename": "source.png",
        "output_filename": "dest.png",
        "pipeline": [
            {"type": "blurring_applygaussianblur", "params": {"widthSize": 5, "heightSize": 5}},
            {"type": "imageconvertions_grayimage", "params": {}},
        ],
    }
    res = client.post(EXPORT_ENDPOINT, json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["filename"] == "my_custom_pipeline.py"
    assert data["unsupported_operators"] == []
    assert "cv2.GaussianBlur" in data["code"]
    ast.parse(data["code"])


def test_api_export_python_graph_request(client):
    """Test POST /api/v1/pipeline/export-python with graph."""
    payload = {
        "pipeline_name": "Graph Workflow",
        "graph": {
            "nodes": [
                {"id": "node-1", "type": "blurring_applyblur", "params": {"widthSize": 3, "heightSize": 3}},
                {"id": "node-2", "type": "imageconvertions_grayimage", "params": {}},
            ],
            "edges": [{"from_node": "node-1", "to_node": "node-2"}],
        },
    }
    res = client.post(EXPORT_ENDPOINT, json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["filename"] == "graph_workflow.py"
    assert "cv2.blur" in data["code"]


def test_api_export_python_missing_payload(client):
    """Test POST /api/v1/pipeline/export-python with neither pipeline nor graph fails validation."""
    payload = {"pipeline_name": "Empty"}
    res = client.post(EXPORT_ENDPOINT, json=payload)
    assert res.status_code == 422


def test_special_characters_and_quotes_in_pipeline_name(client):
    """Verify quotes, parentheses, and existing .py suffix in pipeline name are handled cleanly."""
    payload = {
        "pipeline_name": 'My "Super" Filter (v2.1).py',
        "pipeline": [{"type": "blurring_applyblur", "params": {"widthSize": 3, "heightSize": 3}}],
    }
    res = client.post(EXPORT_ENDPOINT, json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["filename"] == "my_super_filter_v2_1.py"
    # Verify no syntax error is caused by quotes inside argparse description
    ast.parse(data["code"])


def test_comparator_normalization_in_macro_if_else():
    """Verify '=' is normalized to '==' and invalid comparators fall back safely."""
    step_equal = PipelineStep(
        type="macro_if_else",
        params={"metric": "mean_brightness", "comparator": "=", "threshold": 100},
        branches={"then": [], "else": []},
    )
    code_eq, _ = export_pipeline_to_python([step_equal])
    assert "== 100.0:" in code_eq
    ast.parse(code_eq)

    step_fallback = PipelineStep(
        type="macro_if_else",
        params={"metric": "width", "comparator": "INVALID", "threshold": 640},
        branches={"then": [], "else": []},
    )
    code_fb, _ = export_pipeline_to_python([step_fallback])
    assert "> 640.0:" in code_fb
    ast.parse(code_fb)


def test_resilient_hex_color_handling():
    """Verify invalid or None hex color values fall back to default color without crashing."""
    step_none = PipelineStep(
        type="drawingoperations_drawrectangle",
        params={"rgbcolors_input": None},
    )
    code_none, _ = export_pipeline_to_python([step_none])
    ast.parse(code_none)

    step_invalid = PipelineStep(
        type="drawingoperations_drawcircle",
        params={"rgbcolors_input": "not_a_hex"},
    )
    code_invalid, _ = export_pipeline_to_python([step_invalid])
    ast.parse(code_invalid)


def test_exported_drawing_matches_the_app():
    """Exported drawing and contour steps must give the same image as the app, including on images with alpha."""
    color = {"rgbcolors_input": "#2828cc", "thickness": 2}
    cases = [
        ("drawingoperations_drawline", {**color, "starting_point_x1": 2, "starting_point_y1": 3, "ending_point_x": 40}),
        (
            "drawingoperations_drawarrowline",
            {**color, "starting_point_x": 5, "ending_point_x": 40, "ending_point_y": 30},
        ),
        ("drawingoperations_drawcircle", {**color, "radius": 10, "center_point_x": 24, "center_point_y": 20}),
        ("drawingoperations_drawellipse", {**color, "width": 15, "height": 8, "angle": 30, "center_point_x": 24}),
        (
            "drawingoperations_drawrectangle",
            {**color, "starting_point_x": 4, "ending_point_x": 30, "ending_point_y": 25},
        ),
        ("drawingoperations_drawtext", {**color, "draw_text": "Lab", "scale": 1, "starting_point_y": 30}),
        ("filtering_contourdetection", {"rgbcolors_input": "#00ff00", "thickness": 2, "mode": "TREE"}),
    ]
    bgr = np.zeros((40, 48, 3), dtype=np.uint8)
    cv2.rectangle(bgr, (10, 10), (30, 30), (200, 150, 100), -1)
    images = [bgr, np.dstack([bgr, np.full((40, 48), 90, dtype=np.uint8)]), cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)]

    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = os.path.join(tmpdir, "run_script.py")
        input_path = os.path.join(tmpdir, "input.png")
        output_path = os.path.join(tmpdir, "output.png")
        for op_type, params in cases:
            code, _ = export_pipeline_to_python([PipelineStep(type=op_type, params=params)], op_type)
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(code)
            for test_img in images:
                cv2.imwrite(input_path, test_img)
                result = subprocess.run(
                    [sys.executable, script_path, "--input", input_path, "--output", output_path],
                    capture_output=True,
                    text=True,
                )
                assert result.returncode == 0, f"{op_type} script failed: {result.stderr}"

                expected = OPERATOR_REGISTRY[op_type](dict(params)).compute(test_img.copy())
                np.testing.assert_array_equal(
                    cv2.imread(output_path, cv2.IMREAD_UNCHANGED), expected, err_msg=f"{op_type} {test_img.shape}"
                )


def test_all_62_operator_templates_individually_exercised():
    """Verify each registered operator template in OPERATOR_TEMPLATES individually generates valid Python AST."""
    from app.services.python_exporter.templates import OPERATOR_TEMPLATES

    assert len(OPERATOR_TEMPLATES) >= 60
    for op_name in OPERATOR_TEMPLATES:
        step = PipelineStep(type=op_name, params={})
        code, unsupported = export_pipeline_to_python([step], f"Test {op_name}")
        assert unsupported == [], f"Operator {op_name} should be supported"
        assert "def run_pipeline" in code
        try:
            tree = ast.parse(code)
            assert isinstance(tree, ast.Module)
        except SyntaxError as e:
            raise AssertionError(f"Operator {op_name} produced invalid Python code:\n{code}") from e


def test_exported_operators_match_the_app():
    """Exported scripts for these operators must give the same image as the app, for BGR, BGRA and gray input."""
    cases = [
        ("imageconversions_clahe", {"clipLimit": 3.0, "tileGridSizeX": 4, "tileGridSizeY": 6}),
        ("filtering_gaborfilter", {"kernelSize": 21, "sigma": 5.0, "theta": 45, "lambda_": 10.0, "gamma": 0.5}),
        ("sobelderivatives_soblederivate", {"type": "HORIZONTAL"}),
        ("sobelderivatives_soblederivate", {"type": "VERTICAL"}),
        ("sobelderivatives_soblederivate", {"type": "BOTH"}),
        ("sobelderivatives_scharrderivate", {"type": "HORIZONTAL"}),
        ("sobelderivatives_scharrderivate", {"type": "VERTICAL"}),
        ("sobelderivatives_prewittoperator", {}),
    ]
    bgr = np.random.default_rng(1).integers(0, 256, (40, 48, 3), dtype=np.uint8)
    cv2.circle(bgr, (24, 20), 10, (255, 255, 255), -1)
    images = [bgr, np.dstack([bgr, np.full((40, 48), 90, dtype=np.uint8)]), cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)]

    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = os.path.join(tmpdir, "run_script.py")
        input_path = os.path.join(tmpdir, "input.png")
        output_path = os.path.join(tmpdir, "output.png")
        for op_type, params in cases:
            code, _ = export_pipeline_to_python([PipelineStep(type=op_type, params=params)], op_type)
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(code)
            for test_img in images:
                cv2.imwrite(input_path, test_img)
                result = subprocess.run(
                    [sys.executable, script_path, "--input", input_path, "--output", output_path],
                    capture_output=True,
                    text=True,
                )
                assert result.returncode == 0, f"{op_type} {params} script failed: {result.stderr}"

                expected = OPERATOR_REGISTRY[op_type](dict(params)).compute(test_img.copy())
                output = cv2.imread(output_path, cv2.IMREAD_UNCHANGED)
                assert output.shape == expected.shape, f"{op_type} {params}: {output.shape} != {expected.shape}"
                np.testing.assert_array_equal(output, expected, err_msg=f"{op_type} {params}")


def test_hostile_filenames_prevent_code_injection():
    """Verify filenames with quotes, newlines, and Python statements do not inject code."""
    hostile_input = 'input.jpg"; import os; os.system("echo PWNED"); x="'
    hostile_output = "output.jpg'\nimport sys; sys.exit(42)\n#"
    hostile_pipeline = 'Hostile"""\nimport os\nos.system("rm -rf /")\n"""Pipeline'

    code, _ = export_pipeline_to_python(
        steps=[PipelineStep(type="blurring_applyblur", params={})],
        pipeline_name=hostile_pipeline,
        input_default=hostile_input,
        output_default=hostile_output,
    )

    # 1. Generated code must be valid Python syntax
    tree = ast.parse(code)
    assert isinstance(tree, ast.Module)

    # 2. Injected calls must not exist in AST
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "system":
                raise AssertionError("os.system call was injected into AST!")
            if node.func.attr == "exit":
                raise AssertionError("sys.exit call was injected into AST!")


def test_hostile_step_type_sanitized():
    """Verify malicious step types cannot break out of comments or inject statements."""
    hostile_type = 'blur\nimport os\nos.system("PWNED")\n# '
    step = PipelineStep(type=hostile_type, params={})

    code, unsupported = export_pipeline_to_python([step])
    assert len(unsupported) == 1
    assert "\n" not in unsupported[0]

    tree = ast.parse(code)
    assert isinstance(tree, ast.Module)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "system":
            raise AssertionError("os.system call was injected via step_type!")


def test_nan_inf_numeric_parameters_resilience():
    """Verify NaN, Inf, and non-numeric strings in template parameters fall back safely."""
    steps = [
        PipelineStep(
            type="macro_blend",
            params={"alpha": float("nan"), "beta": float("inf"), "gamma": float("-inf")},
            branches={
                "left": [PipelineStep(type="blurring_applyblur", params={"widthSize": "nan", "heightSize": "inf"})],
                "right": [
                    PipelineStep(
                        type="imageconvertions_brightnessandcontrast",
                        params={"alpha": float("nan"), "beta": float("inf")},
                    )
                ],
            },
        ),
        PipelineStep(
            type="macro_if_else",
            params={"threshold": float("nan")},
            branches={"then": [], "else": []},
        ),
        PipelineStep(
            type="filtering_sharpen",
            params={"strength": float("nan")},
        ),
        PipelineStep(
            type="filtering_cannyedge",
            params={"threshold1": float("nan"), "threshold2": float("inf")},
        ),
        PipelineStep(
            type="geometric_rotateimage",
            params={"angle": float("nan"), "scale": float("inf")},
        ),
        PipelineStep(
            type="thresholding_applythreshold",
            params={"thresholdValue": float("nan"), "maxValue": float("inf")},
        ),
        PipelineStep(
            type="detection_facedetection",
            params={"scaleFactor": float("nan"), "minNeighbors": "invalid"},
        ),
    ]

    code, unsupported = export_pipeline_to_python(steps)
    assert unsupported == []
    for line in code.splitlines():
        tokens = line.strip().split()
        assert "nan" not in tokens, f"Bare 'nan' found in line: {line}"
        assert "inf" not in tokens, f"Bare 'inf' found in line: {line}"

    tree = ast.parse(code)
    assert isinstance(tree, ast.Module)


def test_unsupported_operator_emits_runtime_warning():
    """Verify running a script with unsupported operators issues RuntimeWarning."""
    step = PipelineStep(type="futuristic_quantum_filter", params={})
    code, unsupported = export_pipeline_to_python([step], "Warning Pipeline")
    assert unsupported == ["futuristic_quantum_filter"]
    assert "warnings.warn" in code
    assert "RuntimeWarning" in code

    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = os.path.join(tmpdir, "warning_script.py")
        input_path = os.path.join(tmpdir, "in.png")
        output_path = os.path.join(tmpdir, "out.png")

        test_img = np.full((50, 50, 3), 120, dtype=np.uint8)
        cv2.imwrite(input_path, test_img)

        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code)

        result = subprocess.run(
            [sys.executable, script_path, "--input", input_path, "--output", output_path],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "RuntimeWarning" in result.stderr
        assert "futuristic_quantum_filter" in result.stderr
        assert os.path.exists(output_path)


def test_api_hostile_payload_sanitization(client):
    """Verify API endpoint cleanly handles hostile input names and docstrings."""
    payload = {
        "pipeline_name": 'Test\x00\r\n"""Injected"""\x1fPipeline',
        "input_filename": "evil\r\ninput.png",
        "output_filename": "evil\x00output.png",
        "pipeline": [{"type": "blurring_applyblur", "params": {"widthSize": 3, "heightSize": 3}}],
    }
    res = client.post(EXPORT_ENDPOINT, json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "\r" not in data["filename"]
    assert "\n" not in data["filename"]
    assert "\x00" not in data["filename"]
    tree = ast.parse(data["code"])
    assert isinstance(tree, ast.Module)


def test_exported_brightness_and_contrast_matches_the_operator():
    """The exported script must give the same image as the app for Brightness and Contrast."""
    params = {"brightnessValue": 20, "contrastValue": 1.5}
    code, _ = export_pipeline_to_python(
        [PipelineStep(type="imageconversions_brightnessandcontrast", params=params)], "Brightness Contrast"
    )
    test_img = np.tile(np.arange(0, 256, 4, dtype=np.uint8), (8, 1))
    test_img = cv2.merge([test_img, test_img, test_img])

    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = os.path.join(tmpdir, "run_script.py")
        input_path = os.path.join(tmpdir, "input.png")
        output_path = os.path.join(tmpdir, "output.png")
        cv2.imwrite(input_path, test_img)
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code)

        result = subprocess.run(
            [sys.executable, script_path, "--input", input_path, "--output", output_path],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Script failed: {result.stderr}"

        expected = OPERATOR_REGISTRY["imageconversions_brightnessandcontrast"](params).compute(test_img)
        np.testing.assert_array_equal(cv2.imread(output_path), expected)
