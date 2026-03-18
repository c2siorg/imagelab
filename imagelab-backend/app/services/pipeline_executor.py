import time

from app.models.pipeline import PipelineRequest, PipelineResponse, PipelineTimings, StepTiming
from app.operators.registry import get_operator
from app.utils.image import decode_base64_image, encode_image_base64

NOOP_TYPES = {"basic_readimage", "basic_writeimage", "border_for_all", "border_each_side"}


def execute_pipeline(request: PipelineRequest) -> PipelineResponse:
    total_start = time.perf_counter()
    step_timings: list[StepTiming] = []

    try:
        image = decode_base64_image(request.image)
    except Exception as e:
        return PipelineResponse(success=False, error=f"Failed to decode image: {e}", step=0)

    for i, step in enumerate(request.pipeline):
        if step.type in NOOP_TYPES:
            continue

        operator_cls = get_operator(step.type)
        if operator_cls is None:
            return PipelineResponse(
                success=False,
                error=f"Unknown operator '{step.type}' at step {i}",
                step=i,
            )

        try:
            t0 = time.perf_counter()
            operator = operator_cls(step.params)
            image = operator.compute(image)
            t1 = time.perf_counter()
            step_timings.append(StepTiming(step=i, type=step.type, duration_ms=(t1 - t0) * 1000))
        except Exception as e:
            return PipelineResponse(
                success=False,
                error=f"Error in step {i} ({step.type}): {type(e).__name__}: {e}",
                step=i,
            )

    try:
        encoded = encode_image_base64(image, request.image_format)
    except Exception as e:
        error_msg = f"Failed to encode result: {type(e).__name__}: {e}"
        return PipelineResponse(success=False, error=error_msg, step=len(request.pipeline))

    total_ms = (time.perf_counter() - total_start) * 1000

    return PipelineResponse(
        success=True,
        image=encoded,
        image_format=request.image_format,
        timings=PipelineTimings(total_ms=total_ms, steps=step_timings),
    )
