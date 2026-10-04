"""Pipeline Python Exporter generator.

Generates standalone, runnable Python OpenCV scripts from ImageLab pipelines
and graphs, supporting all registered operators and macro control flow.
"""

import re
from typing import Any

from sqlmodel import Session

from app.models.graph import PipelineGraph
from app.models.pipeline import PipelineStep
from app.services.graph_engine import _coerce_graph, compile_graph
from app.services.python_exporter.templates import (
    OPERATOR_TEMPLATES,
    safe_float,
)

NOOP_TYPES = {
    "basic_readimage",
    "basic_writeimage",
    "macro_input",
    "macro_output",
    "border_each_side",
}

OPERATOR_NAMES: dict[str, str] = {
    "imageconversions_grayimage": "Convert to Grayscale",
    "imageconversions_bgrtohsv": "Convert BGR to HSV",
    "imageconversions_hsvtobgr": "Convert HSV to BGR",
    "imageconversions_bgrtolab": "Convert BGR to Lab",
    "imageconversions_labtobgr": "Convert Lab to BGR",
    "imageconversions_bgrtoycrcb": "Convert BGR to YCrCb",
    "imageconversions_ycrcbtobgr": "Convert YCrCb to BGR",
    "imageconversions_invertimage": "Invert Image",
    "imageconversions_brightnessandcontrast": "Brightness and Contrast",
    "imageconversions_histogramequalization": "Histogram Equalization",
    "imageconversions_clahe": "CLAHE (Contrast Limited Adaptive Histogram Equalization)",
    "imageconversions_channelsplit": "Channel Split",
    "imageconversions_colormaps": "Apply Colormap",
    "imageconversions_colortobinary": "Color to Binary",
    "imageconversions_graytobinary": "Grayscale to Binary",
    "imageconvertions_grayimage": "Convert to Grayscale",
    "imageconvertions_bgrtohsv": "Convert BGR to HSV",
    "imageconvertions_hsvtobgr": "Convert HSV to BGR",
    "imageconvertions_bgrtolab": "Convert BGR to Lab",
    "imageconvertions_labtobgr": "Convert Lab to BGR",
    "imageconvertions_bgrtoycrcb": "Convert BGR to YCrCb",
    "imageconvertions_ycrcbtobgr": "Convert YCrCb to BGR",
    "imageconvertions_invertimage": "Invert Image",
    "imageconvertions_brightnessandcontrast": "Brightness and Contrast",
    "imageconvertions_histogramequalization": "Histogram Equalization",
    "imageconvertions_clahe": "CLAHE (Contrast Limited Adaptive Histogram Equalization)",
    "imageconvertions_channelsplit": "Channel Split",
    "imageconvertions_colormaps": "Apply Colormap",
    "imageconvertions_colortobinary": "Color to Binary",
    "imageconvertions_graytobinary": "Grayscale to Binary",
    "blurring_applyblur": "Averaging Blur",
    "blurring_applygaussianblur": "Gaussian Blur",
    "blurring_applymedianblur": "Median Blur",
    "filtering_boxfilter": "Box Filter",
    "filtering_bilateral": "Bilateral Filter",
    "filtering_cannyedge": "Canny Edge Detection",
    "filtering_houghlines": "Hough Line Transform",
    "filtering_sharpen": "Sharpen Filter",
    "filtering_pyramiddown": "Pyramid Down",
    "filtering_pyramidup": "Pyramid Up",
    "filtering_erosion": "Erosion",
    "filtering_dilation": "Dilation",
    "filtering_morphological": "Morphological Operations",
    "filtering_gaborfilter": "Gabor Filter",
    "filtering_contourdetection": "Contour Detection",
    "geometric_resizeimage": "Resize Image",
    "geometric_scaleimage": "Scale Image",
    "geometric_rotateimage": "Rotate Image",
    "geometric_reflectimage": "Flip / Reflect Image",
    "geometric_affineimage": "Affine Transformation",
    "geometric_cropimage": "Crop Image",
    "thresholding_applythreshold": "Simple Threshold",
    "thresholding_adaptivethreshold": "Adaptive Threshold",
    "thresholding_otsuthreshold": "Otsu Threshold",
    "thresholding_applyborders": "Apply Borders",
    "sobelderivatives_soblederivate": "Sobel Derivative",
    "sobelderivatives_scharrderivate": "Scharr Derivative",
    "sobelderivatives_prewittoperator": "Prewitt Operator",
    "sobelderivatives_robertsoperator": "Roberts Cross Operator",
    "transformation_distance": "Distance Transform",
    "transformation_laplacian": "Laplacian Filter",
    "laplacian": "Laplacian Filter",
    "segmentation_kmeans": "K-Means Color Segmentation",
    "segmentation_meanshift": "Mean Shift Segmentation",
    "segmentation_watershed": "Watershed Segmentation",
    "augmentation_gaussiannoise": "Gaussian Noise",
    "augmentation_saltpeppernoise": "Salt & Pepper Noise",
    "augmentation_sepiafilter": "Sepia Filter",
    "detection_eyedetection": "Eye Detection (Haar Cascade)",
    "detection_smiledetection": "Smile Detection (Haar Cascade)",
    "detection_facedetection": "Face Detection (Haar Cascade)",
    "arithmetic_addweighted": "Blend / Add Weighted",
    "macro_blend": "Blend Branches",
    "macro_if_else": "Conditional Branch",
}


def slugify_filename(pipeline_name: str) -> str:
    """Sanitize pipeline name into a safe, valid .py filename."""
    name_for_slug = (pipeline_name or "pipeline").strip()
    if name_for_slug.lower().endswith(".py"):
        name_for_slug = name_for_slug[:-3]
    script_slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", name_for_slug.lower()).strip("_")
    return f"{script_slug or 'pipeline'}.py"


def _sanitize_single_line(text: Any, max_len: int = 120) -> str:
    """Strip newlines and control characters from text so it can safely sit on a single comment line."""
    s = str(text or "")
    s = re.sub(r"[\r\n\x00-\x1f\x7f-\x9f]", " ", s)
    s = " ".join(s.split())
    if len(s) > max_len:
        s = s[:max_len] + "..."
    return s


def _sanitize_step_type(step_type: str) -> str:
    """Allow only safe identifier characters in operator types to prevent comment break-outs."""
    clean = re.sub(r"[^a-zA-Z0-9_.-]", "_", str(step_type or ""))
    return clean[:80] or "unknown_operator"


def _sanitize_docstring(text: str) -> str:
    """Sanitize text inside module docstrings against triple-quotes and control characters."""
    s = re.sub(r"[\r\n\x00-\x1f\x7f-\x9f]", " ", str(text or ""))
    s = s.replace('"""', r"\"\"\"").replace("'''", r"\'\'\'")
    return " ".join(s.split())


def _format_operator_name(step_type: str) -> str:
    safe_type = _sanitize_step_type(step_type)
    name = OPERATOR_NAMES.get(step_type)
    if name:
        return f"{name} ({safe_type})"
    clean = safe_type.replace("_", " ").title()
    return f"{clean} ({safe_type})"


def _coerce_step(raw: PipelineStep | dict[str, Any]) -> PipelineStep:
    if isinstance(raw, PipelineStep):
        return raw
    return PipelineStep(
        type=raw.get("type") or raw.get("op") or "",
        block_id=raw.get("block_id") or raw.get("id"),
        params=raw.get("params", {}),
        branches=raw.get("branches", {}),
        macro_stack=raw.get("macro_stack", []),
    )


def _emit_steps(
    steps: list[PipelineStep],
    var_name: str = "image",
    indent_level: int = 1,
    var_counter: int = 0,
) -> tuple[list[str], bool, list[str], int]:
    """Recursively emits python code lines for a list of steps.

    Returns:
        (lines, needs_numpy, unsupported_operators, updated_var_counter)
    """
    indent = "    " * indent_level
    lines: list[str] = []
    needs_numpy = False
    unsupported_ops: list[str] = []

    for idx, raw_step in enumerate(steps, 1):
        step = _coerce_step(raw_step)
        step_type = step.type

        if not step_type:
            continue

        if step_type in NOOP_TYPES:
            display_name = _format_operator_name(step_type)
            lines.append(f"{indent}# Step {idx}: {display_name} (handled by I/O)")
            continue

        # Control flow: macro_blend
        if step_type == "macro_blend":
            var_counter += 1
            blend_id = var_counter
            branches = dict(step.branches)
            if "op1_branch" in step.params and "left" not in branches:
                branches["left"] = step.params["op1_branch"]
            if "op2_branch" in step.params and "right" not in branches:
                branches["right"] = step.params["op2_branch"]

            alpha = safe_float(step.params.get("alpha", 0.5), 0.5)
            beta = safe_float(step.params.get("beta", 1.0 - alpha), 1.0 - alpha)
            gamma = safe_float(step.params.get("gamma", 0.0), 0.0)

            left_steps = [_coerce_step(s) for s in branches.get("left", [])]
            right_steps = [_coerce_step(s) for s in branches.get("right", [])]

            left_var = f"_branch_left_{blend_id}"
            right_var = f"_branch_right_{blend_id}"

            lines.append(f"{indent}# Step {idx}: Blend Branches (alpha={alpha}, beta={beta}, gamma={gamma})")
            lines.append(f"{indent}{left_var} = {var_name}.copy()")
            left_lines, left_np, left_unsupported, var_counter = _emit_steps(
                left_steps, var_name=left_var, indent_level=indent_level, var_counter=var_counter
            )
            lines.extend(left_lines)

            lines.append(f"{indent}{right_var} = {var_name}.copy()")
            right_lines, right_np, right_unsupported, var_counter = _emit_steps(
                right_steps, var_name=right_var, indent_level=indent_level, var_counter=var_counter
            )
            lines.extend(right_lines)

            needs_numpy = needs_numpy or left_np or right_np
            unsupported_ops.extend(left_unsupported)
            unsupported_ops.extend(right_unsupported)

            lines.extend(
                [
                    f"{indent}if {right_var}.shape[:2] != {left_var}.shape[:2]:",
                    f"{indent}    {right_var} = cv2.resize(",
                    f"{indent}        {right_var},",
                    f"{indent}        ({left_var}.shape[1], {left_var}.shape[0]),",
                    f"{indent}        interpolation=cv2.INTER_AREA,",
                    f"{indent}    )",
                    f"{indent}if {left_var}.ndim != {right_var}.ndim:",
                    f"{indent}    if {left_var}.ndim == 2 and {right_var}.ndim == 3:",
                    f"{indent}        {right_var} = cv2.cvtColor({right_var}, cv2.COLOR_BGR2GRAY)",
                    f"{indent}    elif {left_var}.ndim == 3 and {right_var}.ndim == 2:",
                    f"{indent}        {right_var} = cv2.cvtColor({right_var}, cv2.COLOR_GRAY2BGR)",
                    f"{indent}if {right_var}.dtype != {left_var}.dtype:",
                    f"{indent}    {right_var} = {right_var}.astype({left_var}.dtype)",
                    f"{indent}{var_name} = cv2.addWeighted({left_var}, {alpha}, {right_var}, {beta}, {gamma})",
                ]
            )
            continue

        # Control flow: macro_if_else
        if step_type == "macro_if_else":
            branches = dict(step.branches)
            if "if_branch" in step.params and "then" not in branches:
                branches["then"] = step.params["if_branch"]
            if "else_branch" in step.params and "else" not in branches:
                branches["else"] = step.params["else_branch"]

            metric_name = str(
                step.params.get("metric") or step.params.get("condition_metric") or "mean_brightness"
            ).lower()
            comparator_raw = str(step.params.get("comparator") or step.params.get("operator") or ">").strip()
            if comparator_raw == "=":
                comparator = "=="
            elif comparator_raw in {">", "<", ">=", "<=", "==", "!="}:
                comparator = comparator_raw
            else:
                comparator = ">"
            threshold = safe_float(step.params.get("threshold", 0.0), 0.0)

            if metric_name == "mean_brightness":
                val_expr = f"float(cv2.mean({var_name})[0])"
            elif metric_name == "width":
                val_expr = f"float({var_name}.shape[1])"
            elif metric_name == "height":
                val_expr = f"float({var_name}.shape[0])"
            else:
                val_expr = f"float(cv2.mean({var_name})[0])"

            cond_expr = f"{val_expr} {comparator} {threshold}"

            then_steps = [_coerce_step(s) for s in branches.get("then", [])]
            else_steps = [_coerce_step(s) for s in branches.get("else", [])]

            lines.append(f"{indent}# Step {idx}: Conditional Branch ({metric_name} {comparator} {threshold})")
            lines.append(f"{indent}if {cond_expr}:")

            then_lines, then_np, then_unsupported, var_counter = _emit_steps(
                then_steps, var_name=var_name, indent_level=indent_level + 1, var_counter=var_counter
            )
            if then_lines:
                lines.extend(then_lines)
            else:
                lines.append(f"{indent}    pass")

            lines.append(f"{indent}else:")
            else_lines, else_np, else_unsupported, var_counter = _emit_steps(
                else_steps, var_name=var_name, indent_level=indent_level + 1, var_counter=var_counter
            )
            if else_lines:
                lines.extend(else_lines)
            else:
                lines.append(f"{indent}    pass")

            needs_numpy = needs_numpy or then_np or else_np
            unsupported_ops.extend(then_unsupported)
            unsupported_ops.extend(else_unsupported)
            continue

        # Regular operator step
        template_fn = OPERATOR_TEMPLATES.get(step_type)
        if template_fn is None:
            safe_type = _sanitize_step_type(step_type)
            unsupported_ops.append(safe_type)
            lines.append(f"{indent}# Step {idx}: Unsupported operator '{safe_type}' (skipped)")
            lines.append(
                f"{indent}warnings.warn("
                f"\"Step {idx}: Operator '{safe_type}' is not supported in exported script and was skipped.\", "
                f"RuntimeWarning,"
                f")"
            )
            continue

        try:
            code_lines, req_np = template_fn(step.params, var_name)
            if req_np:
                needs_numpy = True
            display_title = _format_operator_name(step_type)
            lines.append(f"{indent}# Step {idx}: {display_title}")
            for cl in code_lines:
                lines.append(f"{indent}{cl}")
        except Exception as err:
            safe_type = _sanitize_step_type(step_type)
            safe_err = _sanitize_single_line(err, max_len=100)
            unsupported_ops.append(safe_type)
            lines.append(f"{indent}# Step {idx}: Error generating '{safe_type}': {safe_err}")
            lines.append(
                f"{indent}warnings.warn("
                f"\"Step {idx}: Failed generating code for '{safe_type}' and was skipped.\", "
                f"RuntimeWarning,"
                f")"
            )

    return lines, needs_numpy, unsupported_ops, var_counter


def get_unsupported_operators(steps: list[PipelineStep]) -> list[str]:
    """Return list of any operator types in steps or control flow branches not supported."""
    _, _, unsupported, _ = _emit_steps(steps)
    return sorted(list(set(unsupported)))


def export_pipeline_to_python(
    steps: list[PipelineStep],
    pipeline_name: str = "ImageLab Pipeline",
    input_default: str = "input.jpg",
    output_default: str = "output.jpg",
) -> tuple[str, list[str]]:
    """Export pipeline steps to a runnable Python OpenCV script.

    Returns:
        (python_code, unsupported_operators_list)
    """
    body_lines, needs_numpy, unsupported_ops, _ = _emit_steps(steps, var_name="image", indent_level=1)
    unique_unsupported = sorted(list(set(unsupported_ops)))

    script_filename = slugify_filename(pipeline_name)
    clean_pipeline_name = _sanitize_docstring(pipeline_name)
    doc_input = _sanitize_docstring(input_default)
    doc_output = _sanitize_docstring(output_default)

    header_doc = f'''"""Image processing pipeline generated by ImageLab.

Pipeline: {clean_pipeline_name}
Total Steps: {len(steps)}

Usage:
    python {script_filename} --input {doc_input} --output {doc_output}
"""'''

    imports = ["import argparse", "import os", "import sys", "import warnings", "", "import cv2"]
    if needs_numpy:
        imports.append("import numpy as np")
    imports_str = "\n".join(imports)

    run_pipeline_header = (
        "def run_pipeline(image: np.ndarray) -> np.ndarray:" if needs_numpy else "def run_pipeline(image):"
    )
    run_pipeline_doc = '    """Execute the image processing pipeline."""'

    if body_lines:
        pipeline_code_body = "\n".join(body_lines)
        pipeline_func = f"{run_pipeline_header}\n{run_pipeline_doc}\n{pipeline_code_body}\n    return image"
    else:
        pipeline_func = f"{run_pipeline_header}\n{run_pipeline_doc}\n    return image"

    process_func = '''def process_image(input_path: str, output_path: str) -> None:
    """Load image from disk, process it, and save the result."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input image not found: {input_path}")

    image = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError(f"Failed to read image from: {input_path}")

    result = run_pipeline(image)

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    success = cv2.imwrite(output_path, result)
    if not success:
        raise IOError(f"Failed to write output image to: {output_path}")
    print(f"Successfully processed image and saved to: {output_path}")'''

    main_func = f"""def main() -> None:
    parser = argparse.ArgumentParser(description={repr(f"{clean_pipeline_name} (ImageLab exported script)")})
    parser.add_argument(
        "-i", "--input", default={repr(input_default)}, help={repr(f"Path to input image (default: {doc_input})")}
    )
    parser.add_argument(
        "-o", "--output", default={repr(output_default)}, help={repr(f"Path to output image (default: {doc_output})")}
    )
    args = parser.parse_args()

    process_image(args.input, args.output)


if __name__ == "__main__":
    main()
"""

    full_code = f"{header_doc}\n{imports_str}\n\n\n{pipeline_func}\n\n\n{process_func}\n\n\n{main_func}"
    return full_code, unique_unsupported


def export_graph_to_python(
    graph: PipelineGraph | dict[str, Any],
    session: Session | None = None,
    input_channels: int = 3,
    pipeline_name: str = "ImageLab Pipeline",
    input_default: str = "input.jpg",
    output_default: str = "output.jpg",
) -> tuple[str, list[str]]:
    """Compile graph to steps, then export to runnable Python script."""
    if isinstance(graph, dict):
        graph = _coerce_graph(graph)
    steps = compile_graph(graph, session=session, input_channels=input_channels)
    return export_pipeline_to_python(
        steps=steps,
        pipeline_name=pipeline_name,
        input_default=input_default,
        output_default=output_default,
    )
