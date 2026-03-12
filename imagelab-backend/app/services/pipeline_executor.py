import base64
import logging
import time

import cv2
import numpy as np

from app.models.pipeline import (
    ImageStats,
    PipelineRequest,
    PipelineResponse,
    PipelineTimings,
    StepResult,
    StepTiming,
)
from app.operators.registry import get_operator
from app.utils.image import compute_image_stats, decode_base64_image, encode_image_base64

logger = logging.getLogger(__name__)
NOOP_TYPES = {"basic_readimage", "basic_writeimage", "border_for_all", "border_each_side"}
_THUMB_MAX_WIDTH = 200


def _make_thumbnail(image: np.ndarray) -> str:
    """Encode *image* as a base64 JPEG thumbnail (max 200 px wide).

    Notes:
    - Float images in [0, 1] are scaled to [0, 255].
    - Other non-uint8 inputs are contrast-stretched for visibility.
    """
    h, w = image.shape[:2]
    if w > _THUMB_MAX_WIDTH:
        scale = _THUMB_MAX_WIDTH / w
        new_w, new_h = _THUMB_MAX_WIDTH, max(1, int(h * scale))
        thumb = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    else:
        thumb = image

    if thumb.dtype != np.uint8:
        thumb_f = thumb.astype(np.float64)
        mn = float(thumb_f.min())
        mx = float(thumb_f.max())
        if thumb.dtype.kind == "f" and mn >= 0.0 and mx <= 1.0:
            thumb = (thumb_f * 255.0).clip(0, 255).astype(np.uint8)
        elif mx > mn:
            thumb = ((thumb_f - mn) / (mx - mn) * 255).clip(0, 255).astype(np.uint8)
        else:
            thumb = np.zeros_like(thumb, dtype=np.uint8)

    # Drop alpha channel for JPEG (JPEG does not support transparency)
    if thumb.ndim == 3 and thumb.shape[2] == 4:
        thumb = thumb[:, :, :3]

    success, buf = cv2.imencode(".jpg", thumb, [cv2.IMWRITE_JPEG_QUALITY, 80])
    if not success:
        return ""
    return base64.b64encode(buf).decode("utf-8")


# Thread-safety: this function is safe to call concurrently from FastAPI's
# threadpool. All processing state (image array, operator instances, encoded
# output) is local to each invocation.
def execute_pipeline(request: PipelineRequest) -> PipelineResponse:
    """Execute the image-processing pipeline described by *request*.

    When ``request.include_intermediates`` is ``True`` the response includes a
    ``StepResult`` for every non-NOOP operator, containing a JPEG thumbnail and
    pixel statistics for that step's output image.
    """
    t_start_total = time.perf_counter()
    step_timings: list[StepTiming] = []
    intermediates: list[StepResult] = []
    collect = request.include_intermediates

    try:
        image = decode_base64_image(request.image)
    except Exception as e:
        t_fail = time.perf_counter()
        return PipelineResponse(
            success=False,
            error=f"Failed to decode image: {e}",
            step=0,
            timings=PipelineTimings(total_ms=(t_fail - t_start_total) * 1000, steps=step_timings),
        )

    for i, step in enumerate(request.pipeline):
        if step.type in NOOP_TYPES:
            continue

        operator_cls = get_operator(step.type)
        if operator_cls is None:
            t_fail = time.perf_counter()
            return PipelineResponse(
                success=False,
                error=f"Unknown operator '{step.type}' at step {i + 1}",
                step=i + 1,
                timings=PipelineTimings(total_ms=(t_fail - t_start_total) * 1000, steps=step_timings),
            )

        try:
            t_step_start = time.perf_counter()
            operator = operator_cls(step.params)
            image = operator.compute(image)
            t_step_end = time.perf_counter()
            step_timings.append(
                StepTiming(step=i + 1, operator_type=step.type, duration_ms=(t_step_end - t_step_start) * 1000)
            )
        except Exception as e:
            t_fail = time.perf_counter()
            return PipelineResponse(
                success=False,
                error=f"Error in step {i + 1} ({step.type}): {type(e).__name__}: {e}",
                step=i + 1,
                timings=PipelineTimings(total_ms=(t_fail - t_start_total) * 1000, steps=step_timings),
            )

        # Intermediate capture is isolated from operator execution: a stats/thumbnail
        # failure must never turn a successful pipeline step into an error response.
        if collect:
            try:
                raw_stats = compute_image_stats(image)
                intermediates.append(
                    StepResult(
                        step=i + 1,
                        operator_type=step.type,
                        thumbnail=_make_thumbnail(image),
                        stats=ImageStats(**raw_stats),
                    )
                )
            except Exception:
                logger.warning("Failed to capture intermediate for step %d (%s)", i + 1, step.type, exc_info=True)

    try:
        encoded = encode_image_base64(image, request.image_format)
    except Exception as e:
        t_fail = time.perf_counter()
        return PipelineResponse(
            success=False,
            error=f"Failed to encode result: {type(e).__name__}: {e}",
            step=len(request.pipeline),
            timings=PipelineTimings(total_ms=(t_fail - t_start_total) * 1000, steps=step_timings),
        )

    t_end_total = time.perf_counter()

    return PipelineResponse(
        success=True,
        image=encoded,
        image_format=request.image_format,
        timings=PipelineTimings(total_ms=(t_end_total - t_start_total) * 1000, steps=step_timings),
        intermediates=intermediates if collect else None,
    )
