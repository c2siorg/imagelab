import os
import time
import uuid
from contextlib import suppress
from threading import RLock
from urllib.parse import unquote

import cv2
import numpy as np
from sqlmodel import Session

from app.exceptions import MemoryLimitExceededException, PipelineExecutionError
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

DEFAULT_EXECUTION_CACHE_TOTAL_BYTES = 150 * 1024 * 1024  # 150 MB default global ceiling
DEFAULT_EXECUTION_CACHE_PER_RUN_BYTES = 25 * 1024 * 1024  # 25 MB per-execution ceiling
DEFAULT_EXECUTION_CACHE_RAW_PER_RUN_BYTES = 15 * 1024 * 1024  # 15 MB raw array ceiling per run


def _parse_cache_byte_limit(env_var: str, default: int) -> int:
    raw = os.getenv(env_var)
    if not raw:
        return default
    try:
        val = int(raw.strip())
        return val if val > 0 else default
    except (ValueError, TypeError):
        return default


MAX_EXECUTION_CACHE_TOTAL_BYTES = _parse_cache_byte_limit(
    "EXECUTION_CACHE_MAX_BYTES", DEFAULT_EXECUTION_CACHE_TOTAL_BYTES
)
MAX_EXECUTION_CACHE_PER_RUN_BYTES = _parse_cache_byte_limit(
    "EXECUTION_CACHE_MAX_PER_RUN_BYTES", DEFAULT_EXECUTION_CACHE_PER_RUN_BYTES
)
MAX_EXECUTION_CACHE_RAW_PER_RUN_BYTES = _parse_cache_byte_limit(
    "EXECUTION_CACHE_MAX_RAW_PER_RUN_BYTES", DEFAULT_EXECUTION_CACHE_RAW_PER_RUN_BYTES
)
MAX_IMAGE_MEMORY_BYTES = 50 * 1024 * 1024  # 50 MB default threshold


def check_memory_limit(image: np.ndarray, max_bytes: int = MAX_IMAGE_MEMORY_BYTES) -> None:
    if image is not None and image.nbytes > max_bytes:
        raise MemoryLimitExceededException(
            f"Image memory footprint ({image.nbytes} bytes) exceeds memory limit threshold of {max_bytes} bytes."
        )


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


# In _run_sub_pipeline inside app/services/pipeline_executor.py:
def _run_sub_pipeline(steps: list[PipelineStep | dict], current_image: np.ndarray) -> np.ndarray:
    img = current_image.copy()
    for raw_s in steps:
        if isinstance(raw_s, PipelineStep):
            s = raw_s
        elif isinstance(raw_s, dict):
            s = PipelineStep(
                type=raw_s.get("type", ""),
                block_id=raw_s.get("block_id") or raw_s.get("id"),
                params=raw_s.get("params", {}),
                branches=raw_s.get("branches", {}),
            )
        else:
            continue

        step_type = s.type
        step_params = s.params
        step_id = s.block_id

        if step_type in NOOP_TYPES or not step_type:
            continue

        try:
            if step_type == "macro_blend":
                img = _execute_macro_blend(s, img)
            elif step_type == "macro_if_else":
                img = _execute_macro_if_else(s, img)
            else:
                op_cls = get_operator(step_type)
                if op_cls is None:
                    raise ValueError(f"Unknown operator '{step_type}'")
                op = op_cls(step_params)
                img = op.compute(img)
        except ValueError as e:
            raise PipelineExecutionError(
                step_id=step_id or step_type,
                step_type=step_type,
                user_friendly_message=str(e),
            ) from e
    return img


def harmonize_image_channels(src: np.ndarray, target_channels: int) -> np.ndarray:
    """Align image channels with target_channels (1, 3, or 4)."""
    src_channels = 1 if src.ndim == 2 else src.shape[2]
    if src_channels == target_channels:
        return src

    if src_channels == 1:
        if target_channels == 3:
            return cv2.cvtColor(src, cv2.COLOR_GRAY2BGR)
        if target_channels == 4:
            return cv2.cvtColor(src, cv2.COLOR_GRAY2BGRA)
    elif src_channels == 3:
        if target_channels == 1:
            return cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
        if target_channels == 4:
            return cv2.cvtColor(src, cv2.COLOR_BGR2BGRA)
    elif src_channels == 4:
        if target_channels == 1:
            return cv2.cvtColor(src, cv2.COLOR_BGRA2GRAY)
        if target_channels == 3:
            return cv2.cvtColor(src, cv2.COLOR_BGRA2BGR)
    return src


def _execute_macro_blend(step: PipelineStep, image: np.ndarray) -> np.ndarray:
    branches = dict(step.branches)
    if "op1_branch" in step.params:
        branches["left"] = step.params["op1_branch"]
    if "op2_branch" in step.params:
        branches["right"] = step.params["op2_branch"]

    params = dict(step.params)
    alpha = float(params.get("alpha", 0.5))
    beta = float(params.get("beta", 1.0 - alpha))
    params["alpha"] = alpha
    params["beta"] = beta

    step_with_branches = step.model_copy(update={"branches": branches, "params": params})

    img1 = _run_sub_pipeline(step_with_branches.branches.get("left", []), image)
    img2 = _run_sub_pipeline(step_with_branches.branches.get("right", []), image)

    if img2.shape[:2] != img1.shape[:2]:
        img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]), interpolation=cv2.INTER_AREA)

    ch1 = 1 if img1.ndim == 2 else img1.shape[2]
    ch2 = 1 if img2.ndim == 2 else img2.shape[2]
    if ch1 != ch2:
        img2 = harmonize_image_channels(img2, ch1)

    if img2.dtype != img1.dtype:
        img2 = img2.astype(img1.dtype)
    img1 = np.ascontiguousarray(img1)
    img2 = np.ascontiguousarray(img2)

    try:
        return cv2.addWeighted(img1, alpha, img2, beta, 0.0)
    except Exception as err:
        raise ValueError(
            "Failed to blend branch outputs: mismatched image dimensions, channels, or data types."
        ) from err


def _execute_macro_if_else(step: PipelineStep, image: np.ndarray) -> np.ndarray:
    branches = dict(step.branches)
    if "if_branch" in step.params:
        branches["then"] = step.params["if_branch"]
    if "else_branch" in step.params:
        branches["else"] = step.params["else_branch"]

    step_with_branches = step.model_copy(update={"branches": branches})
    cond = _evaluate_condition(image, step_with_branches.params)
    selected = step_with_branches.branches.get("then", []) if cond else step_with_branches.branches.get("else", [])
    return _run_sub_pipeline(selected, image)


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


def _get_entry_bytes(entry: dict[str, object] | None) -> tuple[int, int]:
    """Return (total_bytes, raw_bytes) for a cached step dictionary."""
    if not isinstance(entry, dict):
        return 0, 0
    arr = entry.get("image_array")
    if isinstance(arr, np.ndarray):
        return arr.nbytes, arr.nbytes
    b = entry.get("image_bytes")
    if isinstance(b, bytes):
        return len(b), 0
    return 0, 0


def execute_pipeline(request: PipelineRequest, cache_steps: bool = True) -> PipelineResponse:
    t_start_total = time.perf_counter()
    execution_id = uuid.uuid4().hex
    step_timings: list[StepTiming] = []
    step_results: list[StepResult] = []
    full_images: dict[str, dict[str, object]] = {}

    try:
        image = decode_base64_image(request.image)
        check_memory_limit(image)
    except Exception as e:
        if isinstance(e, MemoryLimitExceededException):
            raise
        t_fail = time.perf_counter()
        return PipelineResponse(
            success=False,
            execution_id=execution_id,
            error=f"Failed to decode image: {e}",
            step=0,
            timings=PipelineTimings(total_ms=(t_fail - t_start_total) * 1000, steps=step_timings),
            step_results=step_results,
        )

    cached_bytes_current_run = 0
    cached_raw_bytes_current_run = 0

    for i, step in enumerate(request.pipeline):
        if step.type in NOOP_TYPES:
            continue

        try:
            t_step_start = time.perf_counter()
            if step.type == "macro_blend":
                image = _execute_macro_blend(step, image)
            elif step.type == "macro_if_else":
                image = _execute_macro_if_else(step, image)
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
                            macro_stack=getattr(step, "macro_stack", []),
                        )
                    )
                    if cache_steps:
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

            check_memory_limit(image)

            t_step_end = time.perf_counter()
            timing_ms = (t_step_end - t_step_start) * 1000
            step_timings.append(StepTiming(step=i + 1, operator_type=step.type, duration_ms=timing_ms))
            thumbnail = encode_thumbnail_base64(image, request.image_format)
            cache_key = step.block_id or str(i + 1)
            prev_entry = full_images.get(cache_key)
            prev_bytes, prev_raw_bytes = _get_entry_bytes(prev_entry)

            can_cache = False
            cached_entry = None

            if cache_steps:
                step_raw_bytes = image.nbytes
                # Tier 1 (Fast path): Store uncompressed NumPy array if within per-run raw budget
                # and per-run total budget
                if (
                    cached_raw_bytes_current_run - prev_raw_bytes + step_raw_bytes
                    <= MAX_EXECUTION_CACHE_RAW_PER_RUN_BYTES
                    and cached_bytes_current_run - prev_bytes + step_raw_bytes <= MAX_EXECUTION_CACHE_PER_RUN_BYTES
                ):
                    cached_raw_bytes_current_run += step_raw_bytes - prev_raw_bytes
                    cached_bytes_current_run += step_raw_bytes - prev_bytes
                    cached_entry = {
                        "index": i + 1,
                        "block_id": cache_key,
                        "type": step.type,
                        "image_array": image.copy(),
                        "image_format": request.image_format,
                        "timing_ms": timing_ms,
                    }
                    can_cache = True
                else:
                    # Tier 2 (High-resolution fallback): Compress to bytes to preserve inspectability
                    # without exceeding memory limits for large or multi-step pipelines
                    try:
                        compressed_b = encode_image_bytes(image, request.image_format)
                        step_compressed_bytes = len(compressed_b)
                        if (
                            cached_bytes_current_run - prev_bytes + step_compressed_bytes
                            <= MAX_EXECUTION_CACHE_PER_RUN_BYTES
                        ):
                            cached_raw_bytes_current_run -= prev_raw_bytes
                            cached_bytes_current_run += step_compressed_bytes - prev_bytes
                            cached_entry = {
                                "index": i + 1,
                                "block_id": cache_key,
                                "type": step.type,
                                "image_bytes": compressed_b,
                                "image_format": request.image_format,
                                "timing_ms": timing_ms,
                            }
                            can_cache = True
                    except (ValueError, cv2.error):
                        can_cache = False

            if can_cache and cached_entry is not None:
                full_images[cache_key] = cached_entry
            else:
                # If duplicate block_id replacement cannot be cached, pop earlier entry to avoid stale inspection
                if cache_key in full_images:
                    full_images.pop(cache_key, None)
                    cached_bytes_current_run -= prev_bytes
                    cached_raw_bytes_current_run -= prev_raw_bytes

            step_results.append(
                StepResult(
                    index=i + 1,
                    block_id=step.block_id,
                    type=step.type,
                    success=True,
                    thumbnail=thumbnail,
                    image_format=request.image_format,
                    timing_ms=timing_ms,
                    has_full_image=can_cache,
                    macro_stack=getattr(step, "macro_stack", []),
                )
            )
        except ValueError as e:
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
                    macro_stack=getattr(step, "macro_stack", []),
                )
            )
            if cache_steps:
                _store_execution(execution_id, full_images)
            raise PipelineExecutionError(
                step_id=step_id,
                step_type=step.type,
                user_friendly_message=error_msg,
                step=i + 1,
                execution_id=execution_id,
                step_results=step_results,
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
                    macro_stack=getattr(step, "macro_stack", []),
                )
            )
            if cache_steps:
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
        if cache_steps:
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
    if cache_steps:
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
    # Decode URL-encoded block_id
    decoded_block_id = unquote(block_id)

    with _EXECUTION_CACHE_LOCK:
        cached = _EXECUTION_CACHE.get(execution_id)
        if not cached:
            return None
        steps = cached["steps"]
        if not isinstance(steps, dict):
            return None

        # Tier 1: Exact match with decoded ID
        step = steps.get(decoded_block_id)

        # Tier 2: Exact match with original ID (if different)
        if step is None and decoded_block_id != block_id:
            step = steps.get(block_id)

        # Tier 3: Fallback to leaf ID (last segment after colon)
        if step is None and ":" in decoded_block_id:
            leaf_id = decoded_block_id.split(":")[-1]
            step = steps.get(leaf_id)

        # Tier 4: Suffix match for namespaced IDs
        if step is None:
            matching_keys = [k for k in steps if k.endswith(f":{decoded_block_id}")]
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
    image_array = step.get("image_array")
    if isinstance(image_array, np.ndarray):
        image = image_array
    else:
        image_bytes = step.get("image_bytes")
        if not isinstance(image_bytes, bytes):
            return None
        image = decode_image_bytes(image_bytes)
        if image is None:
            return None

    image_b64 = encode_image_base64(image, image_format)
    # When inspecting lossy formats (JPEG), compression introduces quantization
    # artifacts. We decode the compressed buffer so that reported metrics (analysis & histogram)
    # match the exact pixel buffer delivered to the client.
    if image_format.lower() in ("jpeg", "jpg"):
        with suppress(ValueError, cv2.error):
            image = decode_base64_image(image_b64)

    return {
        "execution_id": execution_id,
        "block_id": block_id,
        "index": int(step["index"]),
        "type": str(step["type"]),
        "image": image_b64,
        "image_format": image_format,
        "timing_ms": step["timing_ms"],
        "analysis": analyze_image(image),
        "histogram": calculate_histogram(image),
    }


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


def _calculate_steps_byte_size(steps: dict[str, dict[str, object]]) -> int:
    total = 0
    for step in steps.values():
        if not isinstance(step, dict):
            continue
        arr = step.get("image_array")
        if isinstance(arr, np.ndarray):
            total += arr.nbytes
        else:
            b = step.get("image_bytes")
            if isinstance(b, bytes):
                total += len(b)
    return total


def _store_execution(execution_id: str, steps: dict[str, dict[str, object]]) -> None:
    if not steps:
        return
    execution_size = _calculate_steps_byte_size(steps)
    if execution_size > MAX_EXECUTION_CACHE_TOTAL_BYTES:
        return
    _evict_expired_executions()
    now = time.time()
    with _EXECUTION_CACHE_LOCK:
        _EXECUTION_CACHE[execution_id] = {
            "created_at": now,
            "last_accessed_at": now,
            "steps": steps,
            "byte_size": execution_size,
        }

        # 1. Enforce max entries limit
        while len(_EXECUTION_CACHE) > MAX_EXECUTION_CACHE_ENTRIES:
            least_recently_used_execution_id = min(
                _EXECUTION_CACHE,
                key=lambda key: float(_EXECUTION_CACHE[key].get("last_accessed_at", 0)),
            )
            _EXECUTION_CACHE.pop(least_recently_used_execution_id, None)

        # 2. Enforce total memory byte ceiling
        current_bytes = sum(int(entry.get("byte_size", 0)) for entry in _EXECUTION_CACHE.values())
        while current_bytes > MAX_EXECUTION_CACHE_TOTAL_BYTES and _EXECUTION_CACHE:
            least_recently_used_execution_id = min(
                _EXECUTION_CACHE,
                key=lambda key: float(_EXECUTION_CACHE[key].get("last_accessed_at", 0)),
            )
            removed = _EXECUTION_CACHE.pop(least_recently_used_execution_id, None)
            if removed:
                current_bytes -= int(removed.get("byte_size", 0))


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


def expand_macro_steps(steps: list[PipelineStep], session: Session | None = None) -> list[PipelineStep]:
    """Legacy helper wrapper for expanded step resolution."""
    from app.services.graph_engine import _coerce_graph, compile_graph

    raw_nodes = []
    for idx, step in enumerate(steps):
        s = step if isinstance(step, PipelineStep) else PipelineStep(**step)
        params = dict(s.params)

        # Populate legacy default beta parameter for macro_blend if omitted
        if s.type == "macro_blend" and "beta" not in params:
            alpha = float(params.get("alpha", 0.5))
            params["beta"] = 1.0 - alpha

        branches = {}
        for b_name, b_steps in s.branches.items():
            branches[b_name] = [b.model_dump() if hasattr(b, "model_dump") else b for b in b_steps]
        raw_nodes.append(
            {
                "id": s.block_id or str(idx),
                "type": s.type,
                "params": params,
                "branches": branches,
            }
        )

    graph = _coerce_graph({"nodes": raw_nodes, "edges": []})
    return compile_graph(graph, session=session, input_channels=3)
