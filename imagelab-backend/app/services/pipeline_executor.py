import time
import uuid
from threading import RLock

import cv2
import numpy as np

from app.exceptions import PipelineExecutionError
from app.models.pipeline import (
    ImageAnalysis,
    ImageHistogram,
    PipelineRequest,
    PipelineResponse,
    PipelineStep,
    PipelineTimings,
    StepResult,
    StepTiming,
)
from app.operators.registry import get_operator
from app.utils.image import decode_base64_image, encode_image_base64

NOOP_TYPES = {"basic_readimage", "basic_writeimage", "border_for_all", "border_each_side"}
THUMBNAIL_MAX_SIZE = 128
EXECUTION_CACHE_TTL_SECONDS = 30 * 60
MAX_EXECUTION_CACHE_ENTRIES = 25

_EXECUTION_CACHE: dict[str, dict[str, object]] = {}
_EXECUTION_CACHE_LOCK = RLock()


def _evaluate_condition(image: np.ndarray, params: dict) -> bool:
    metric_name = str(params.get("metric") or params.get("condition_metric") or "mean_brightness").lower()
    comparator = str(params.get("comparator") or params.get("operator") or ">")
    threshold = float(params.get("threshold", 0))

    if metric_name == "mean_brightness":
        val = float(cv2.mean(image)[0])
    elif metric_name == "width":
        val = float(image.shape[1])
    elif metric_name == "height":
        val = float(image.shape[0])
    else:
        val = float(cv2.mean(image)[0])

    if comparator == ">":
        return val > threshold
    elif comparator == "<":
        return val < threshold
    elif comparator == "==":
        return abs(val - threshold) < 1e-6
    elif comparator == ">=":
        return val >= threshold
    elif comparator == "<=":
        return val <= threshold
    elif comparator == "!=":
        return abs(val - threshold) >= 1e-6
    return val > threshold


def _run_sub_pipeline(steps: list, current_image: np.ndarray) -> np.ndarray:
    img = current_image.copy()
    for s in steps:
        if isinstance(s, dict):
            step_type = s.get("type", "")
            step_params = s.get("params", {})
            step_id = s.get("block_id", "")
        else:
            step_type = getattr(s, "type", "")
            step_params = getattr(s, "params", {})
            step_id = getattr(s, "block_id", "")

        if step_type in NOOP_TYPES or not step_type:
            continue

        try:
            if step_type == "macro_blend":
                img = _execute_macro_blend(step_params, img)
            elif step_type == "macro_if_else":
                img = _execute_macro_if_else(step_params, img)
            else:
                op_cls = get_operator(step_type)
                if op_cls is None:
                    raise ValueError(f"Unknown operator '{step_type}'")
                op = op_cls(step_params)
                img = op.compute(img)
        except ValueError as e:
            # Convert ValueError to PipelineExecutionError with step context
            raise PipelineExecutionError(
                step_id=step_id or step_type,
                step_type=step_type,
                user_friendly_message=str(e),
            ) from e
    return img


def _execute_macro_blend(params: dict, image: np.ndarray) -> np.ndarray:
    alpha = float(params.get("alpha", 0.5))
    beta = float(params.get("beta", 1.0 - alpha))

    op1_steps = params.get("op1_branch") or params.get("OP1") or []
    op2_steps = params.get("op2_branch") or params.get("OP2") or []

    img1 = _run_sub_pipeline(op1_steps, image)
    img2 = _run_sub_pipeline(op2_steps, image)

    if img2.shape[:2] != img1.shape[:2]:
        img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]), interpolation=cv2.INTER_AREA)

    if img1.ndim != img2.ndim:
        if img1.ndim == 2 and img2.ndim == 3:
            img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        elif img1.ndim == 3 and img2.ndim == 2:
            img2 = cv2.cvtColor(img2, cv2.COLOR_GRAY2BGR)

    try:
        return cv2.addWeighted(img1, alpha, img2, beta, 0.0)
    except Exception as err:
        raise ValueError(
            "Failed to blend branch outputs: mismatched image dimensions, channels, or data types."
        ) from err


def _execute_macro_if_else(params: dict, image: np.ndarray) -> np.ndarray:
    cond = _evaluate_condition(image, params)
    if_branch = params.get("if_branch") or params.get("IF_BRANCH") or []
    else_branch = params.get("else_branch") or params.get("ELSE_BRANCH") or []
    selected = if_branch if cond else else_branch
    return _run_sub_pipeline(selected, image)


def expand_macro_steps(steps: list[PipelineStep], session=None) -> list[PipelineStep]:
    """
    Recursively unrolls any macro steps in a flat list of PipelineSteps.
    Supports macro_blend, macro_if_else, and DB-persisted macro_ref steps.
    """
    expanded: list[PipelineStep] = []
    for step in steps:
        if step.type == "macro_blend":
            params = dict(step.params)
            op1_branch = params.get("op1_branch") or params.get("OP1") or []
            op2_branch = params.get("op2_branch") or params.get("OP2") or []

            def _to_steps(raw_list):
                res = []
                for item in raw_list:
                    if isinstance(item, PipelineStep):
                        res.append(item)
                    elif isinstance(item, dict):
                        res.append(PipelineStep(**item))
                return res

            exp_op1 = expand_macro_steps(_to_steps(op1_branch), session=session)
            exp_op2 = expand_macro_steps(_to_steps(op2_branch), session=session)
            alpha = float(params.get("alpha", 0.5))
            params["op1_branch"] = [s.model_dump() for s in exp_op1]
            params["op2_branch"] = [s.model_dump() for s in exp_op2]
            params["OP1"] = params["op1_branch"]
            params["OP2"] = params["op2_branch"]
            params["alpha"] = alpha
            params["beta"] = 1.0 - alpha
            expanded.append(PipelineStep(type=step.type, block_id=step.block_id, params=params))
        elif step.type == "macro_if_else":
            params = dict(step.params)
            if_branch = params.get("if_branch") or params.get("IF_BRANCH") or []
            else_branch = params.get("else_branch") or params.get("ELSE_BRANCH") or []

            def _to_steps(raw_list):
                res = []
                for item in raw_list:
                    if isinstance(item, PipelineStep):
                        res.append(item)
                    elif isinstance(item, dict):
                        res.append(PipelineStep(**item))
                return res

            exp_if = expand_macro_steps(_to_steps(if_branch), session=session)
            exp_else = expand_macro_steps(_to_steps(else_branch), session=session)
            params["if_branch"] = [s.model_dump() for s in exp_if]
            params["else_branch"] = [s.model_dump() for s in exp_else]
            params["IF_BRANCH"] = params["if_branch"]
            params["ELSE_BRANCH"] = params["else_branch"]
            expanded.append(PipelineStep(type=step.type, block_id=step.block_id, params=params))
        elif step.type == "macro_ref" or (step.params.get("macro_id") and step.type.startswith("macro")):
            if session is not None:
                import uuid

                from app.services.graph_engine import prepare_pipeline

                macro_id_str = step.params.get("macro_id")
                if not macro_id_str:
                    raise ValueError(f"Step {step.block_id} is a macro reference but missing 'macro_id' parameter.")
                macro_id = uuid.UUID(str(macro_id_str))
                sub_steps = prepare_pipeline(session, macro_id, input_channels=3)
                # Recursively expand nested macros inside the sub-steps
                expanded_sub_steps = expand_macro_steps(sub_steps, session=session)
                prefix = step.block_id or f"macro_{macro_id}"
                for sub_step in expanded_sub_steps:
                    new_block_id = f"{prefix}:{sub_step.block_id}" if sub_step.block_id else prefix
                    expanded.append(
                        PipelineStep(
                            type=sub_step.type,
                            block_id=new_block_id,
                            params=sub_step.params,
                        )
                    )
            else:
                expanded.append(step)
        else:
            expanded.append(step)
    return expanded


# Thread-safety: this function is safe to call concurrently from FastAPI's
# threadpool. All processing state (image array, operator instances, encoded
# output) is local to each invocation. The module-level NOOP_TYPES set and
# OPERATOR_REGISTRY dict are read-only after import and never mutated.
def execute_pipeline(request: PipelineRequest) -> PipelineResponse:
    """
    Execute the image-processing pipeline described by *request*.

    Returns a PipelineResponse that always includes a ``timings`` field
    populated with every step that completed before the function returned,
    even when the response indicates failure.  This allows callers to
    inspect partial execution progress on error.
    """
    t_start_total = time.perf_counter()
    execution_id = uuid.uuid4().hex
    step_timings: list[StepTiming] = []
    step_results: list[StepResult] = []
    full_images: dict[str, dict[str, object]] = {}

    try:
        image = decode_base64_image(request.image)
    except Exception as e:
        t_fail = time.perf_counter()
        return PipelineResponse(
            success=False,
            execution_id=execution_id,
            error=f"Failed to decode image: {e}",
            step=0,
            timings=PipelineTimings(total_ms=(t_fail - t_start_total) * 1000, steps=step_timings),
            step_results=step_results,
        )

    for i, step in enumerate(request.pipeline):
        if step.type in NOOP_TYPES:
            continue

        try:
            t_step_start = time.perf_counter()
            if step.type == "macro_blend":
                image = _execute_macro_blend(step.params, image)
            elif step.type == "macro_if_else":
                image = _execute_macro_if_else(step.params, image)
            else:
                operator_cls = get_operator(step.type)
                if operator_cls is None:
                    t_fail = time.perf_counter()
                    step_results.append(
                        StepResult(
                            index=i + 1,
                            block_id=step.block_id,
                            type=step.type,
                            success=False,
                            image_format=request.image_format,
                            error=f"Unknown operator '{step.type}'",
                        )
                    )
                    _store_execution(execution_id, full_images)
                    return PipelineResponse(
                        success=False,
                        execution_id=execution_id,
                        error=f"Unknown operator '{step.type}' at step {i + 1}",
                        step=i + 1,
                        error_block_id=step.block_id,
                        timings=PipelineTimings(total_ms=(t_fail - t_start_total) * 1000, steps=step_timings),
                        step_results=step_results,
                    )

                operator = operator_cls(step.params)
                image = operator.compute(image)

            t_step_end = time.perf_counter()
            timing_ms = (t_step_end - t_step_start) * 1000
            step_timings.append(StepTiming(step=i + 1, operator_type=step.type, duration_ms=timing_ms))
            thumbnail = encode_thumbnail_base64(image, request.image_format)
            cache_key = step.block_id or str(i + 1)
            full_images[cache_key] = {
                "index": i + 1,
                "block_id": cache_key,
                "type": step.type,
                "image_bytes": encode_image_bytes(image, request.image_format),
                "image_format": request.image_format,
                "timing_ms": timing_ms,
            }
            step_results.append(
                StepResult(
                    index=i + 1,
                    block_id=step.block_id,
                    type=step.type,
                    success=True,
                    thumbnail=thumbnail,
                    image_format=request.image_format,
                    timing_ms=timing_ms,
                    has_full_image=True,
                )
            )
        except ValueError as e:
            # Convert ValueError (from operators) to PipelineExecutionError
            t_fail = time.perf_counter()
            step_id = step.block_id or str(i + 1)
            error_msg = str(e)
            step_results.append(
                StepResult(
                    index=i + 1,
                    block_id=step.block_id,
                    type=step.type,
                    success=False,
                    image_format=request.image_format,
                    error=error_msg,
                )
            )
            _store_execution(execution_id, full_images)
            raise PipelineExecutionError(
                step_id=step_id,
                step_type=step.type,
                user_friendly_message=error_msg,
            ) from e
        except Exception as e:
            t_fail = time.perf_counter()
            step_results.append(
                StepResult(
                    index=i + 1,
                    block_id=step.block_id,
                    type=step.type,
                    success=False,
                    image_format=request.image_format,
                    error=f"{type(e).__name__}: {e}",
                )
            )
            _store_execution(execution_id, full_images)
            return PipelineResponse(
                success=False,
                execution_id=execution_id,
                error=f"Error in step {i + 1} ({step.type}): {type(e).__name__}: {e}",
                step=i + 1,
                error_block_id=step.block_id,
                timings=PipelineTimings(total_ms=(t_fail - t_start_total) * 1000, steps=step_timings),
                step_results=step_results,
            )

    try:
        encoded = encode_image_base64(image, request.image_format)
    except Exception as e:
        t_fail = time.perf_counter()
        error_msg = f"Failed to encode result: {type(e).__name__}: {e}"
        _store_execution(execution_id, full_images)
        return PipelineResponse(
            success=False,
            execution_id=execution_id,
            error=error_msg,
            step=len(request.pipeline),
            timings=PipelineTimings(total_ms=(t_fail - t_start_total) * 1000, steps=step_timings),
            step_results=step_results,
        )

    t_end_total = time.perf_counter()
    _store_execution(execution_id, full_images)

    return PipelineResponse(
        success=True,
        execution_id=execution_id,
        image=encoded,
        image_format=request.image_format,
        timings=PipelineTimings(total_ms=(t_end_total - t_start_total) * 1000, steps=step_timings),
        step_results=step_results,
    )


def encode_thumbnail_base64(image: np.ndarray, fmt: str = "png") -> str:
    height, width = image.shape[:2]
    largest_side = max(width, height)
    if largest_side <= THUMBNAIL_MAX_SIZE:
        thumbnail = image
    else:
        scale = THUMBNAIL_MAX_SIZE / largest_side
        thumbnail = cv2.resize(
            image,
            (max(1, int(width * scale)), max(1, int(height * scale))),
            interpolation=cv2.INTER_AREA,
        )
    return encode_image_base64(thumbnail, fmt)


def inspect_step(execution_id: str, block_id: str):
    _evict_expired_executions()
    with _EXECUTION_CACHE_LOCK:
        cached = _EXECUTION_CACHE.get(execution_id)
        if not cached:
            return None
        steps = cached["steps"]
        if not isinstance(steps, dict):
            return None
        step = steps.get(block_id)
        if step is None:
            # Fallback for parent macro block_id matching (e.g., 'm1' matching 'm1:gray')
            matching_keys = [k for k in steps if k.startswith(f"{block_id}:")]
            if matching_keys:
                last_key = max(
                    matching_keys,
                    key=lambda k: int(steps[k]["index"]) if isinstance(steps[k], dict) and "index" in steps[k] else 0,
                )
                step = steps[last_key]
        if not isinstance(step, dict):
            return None
        cached["last_accessed_at"] = time.time()
    image_format = str(step["image_format"])
    image_bytes = step.get("image_bytes")
    if not isinstance(image_bytes, bytes):
        return None
    image = decode_image_bytes(image_bytes)
    if image is None:
        return None
    return {
        "execution_id": execution_id,
        "block_id": block_id,
        "index": int(step["index"]),
        "type": str(step["type"]),
        "image": encode_image_base64(image, image_format),
        "image_format": image_format,
        "timing_ms": step["timing_ms"],
        "analysis": analyze_image(image),
        "histogram": calculate_histogram(image),
    }


def encode_image_bytes(image: np.ndarray, fmt: str = "png") -> bytes:
    fmt = fmt.lower()
    ext = "jpeg" if fmt == "jpg" else "tiff" if fmt == "tif" else fmt
    success, buf = cv2.imencode(f".{ext}", image)
    if not success:
        raise ValueError(f"Could not encode image as {ext}")
    return buf.tobytes()


def decode_image_bytes(image_bytes: bytes) -> np.ndarray | None:
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_UNCHANGED)


def analyze_image(image: np.ndarray) -> ImageAnalysis:
    height, width = image.shape[:2]
    channels = 1 if image.ndim == 2 else image.shape[2]
    mean, stddev = cv2.meanStdDev(image)
    mean_values = [float(v) for v in mean.flatten()]
    std_values = [float(v) for v in stddev.flatten()]
    return ImageAnalysis(
        width=width,
        height=height,
        channels=channels,
        dtype=str(image.dtype),
        min=float(np.min(image)),
        max=float(np.max(image)),
        mean=mean_values[0] if channels == 1 else mean_values[:channels],
        std=std_values[0] if channels == 1 else std_values[:channels],
    )


def _histogram_counts(channel: np.ndarray) -> list[int]:
    normalized = np.clip(channel, 0, 255).astype(np.uint8, copy=False)
    return np.bincount(normalized.ravel(), minlength=256).astype(int).tolist()


def calculate_histogram(image: np.ndarray) -> ImageHistogram:
    bins = list(range(256))

    # Downsample fallback for very large images (max dimension > 2048)
    height, width = image.shape[:2]
    largest_side = max(width, height)
    HISTOGRAM_MAX_SIZE = 2048
    if largest_side > HISTOGRAM_MAX_SIZE:
        scale = HISTOGRAM_MAX_SIZE / largest_side
        image = cv2.resize(
            image,
            (max(1, int(width * scale)), max(1, int(height * scale))),
            interpolation=cv2.INTER_AREA,
        )

    if image.ndim == 2:
        return ImageHistogram(bins=bins, luminance=_histogram_counts(image))

    channels = image.shape[2] if image.ndim == 3 else 1
    if channels < 3:
        luminance_source = image[:, :, 0]
        return ImageHistogram(bins=bins, luminance=_histogram_counts(luminance_source))

    bgr = image[:, :, :3]
    luminance = cv2.cvtColor(np.clip(bgr, 0, 255).astype(np.uint8, copy=False), cv2.COLOR_BGR2GRAY)
    return ImageHistogram(
        bins=bins,
        luminance=_histogram_counts(luminance),
        red=_histogram_counts(bgr[:, :, 2]),
        green=_histogram_counts(bgr[:, :, 1]),
        blue=_histogram_counts(bgr[:, :, 0]),
    )


def _store_execution(execution_id: str, steps: dict[str, dict[str, object]]) -> None:
    _evict_expired_executions()
    now = time.time()
    with _EXECUTION_CACHE_LOCK:
        _EXECUTION_CACHE[execution_id] = {
            "created_at": now,
            "last_accessed_at": now,
            "steps": steps,
        }
        if len(_EXECUTION_CACHE) > MAX_EXECUTION_CACHE_ENTRIES:
            least_recently_used_execution_id = min(
                _EXECUTION_CACHE,
                key=lambda key: float(_EXECUTION_CACHE[key].get("last_accessed_at", 0)),
            )
            _EXECUTION_CACHE.pop(least_recently_used_execution_id, None)


def _evict_expired_executions() -> None:
    now = time.time()
    with _EXECUTION_CACHE_LOCK:
        expired = [
            execution_id
            for execution_id, entry in _EXECUTION_CACHE.items()
            if now - float(entry.get("created_at", 0)) > EXECUTION_CACHE_TTL_SECONDS
        ]
        for execution_id in expired:
            _EXECUTION_CACHE.pop(execution_id, None)
