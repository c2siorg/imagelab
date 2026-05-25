import time
import uuid
from threading import RLock

import cv2
import numpy as np

from app.models.pipeline import (
    ImageAnalysis,
    PipelineRequest,
    PipelineResponse,
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

        try:
            t_step_start = time.perf_counter()
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
                "image": image.copy(),
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
    if not isinstance(steps, dict) or block_id not in steps:
        return None
    step = steps[block_id]
    if not isinstance(step, dict):
        return None
    image = step["image"]
    if not isinstance(image, np.ndarray):
        return None
    image_format = str(step["image_format"])
    return {
        "execution_id": execution_id,
        "block_id": block_id,
        "index": int(step["index"]),
        "type": str(step["type"]),
        "image": encode_image_base64(image, image_format),
        "image_format": image_format,
        "timing_ms": step["timing_ms"],
        "analysis": analyze_image(image),
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


def _store_execution(execution_id: str, steps: dict[str, dict[str, object]]) -> None:
    _evict_expired_executions()
    with _EXECUTION_CACHE_LOCK:
        _EXECUTION_CACHE[execution_id] = {"created_at": time.time(), "steps": steps}
        if len(_EXECUTION_CACHE) > MAX_EXECUTION_CACHE_ENTRIES:
            oldest_execution_id = min(
                _EXECUTION_CACHE,
                key=lambda key: float(_EXECUTION_CACHE[key].get("created_at", 0)),
            )
            _EXECUTION_CACHE.pop(oldest_execution_id, None)


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
