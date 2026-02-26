import time
from app.models.pipeline import PipelineRequest, PipelineResponse, StepTiming
from app.operators.registry import get_operator
from app.utils.image import decode_base64_image, encode_image_base64

NOOP_TYPES = {"basic_readimage", "basic_writeimage", "border_for_all", "border_each_side"}


def execute_pipeline(request: PipelineRequest) -> PipelineResponse:
    t_start_total = time.perf_counter()
    step_timings = []

    try:
        image = decode_base64_image(request.image)
    except Exception as e:
        t_fail = time.perf_counter()
        return PipelineResponse(
            success=False, 
            error=f"Failed to decode image: {e}", 
            step=0,
            total_duration_ms=(t_fail - t_start_total) * 1000,
            step_timings=step_timings
        )

    for i, step in enumerate(request.pipeline):
        if step.type in NOOP_TYPES:
            continue

        operator_cls = get_operator(step.type)
        if operator_cls is None:
            t_fail = time.perf_counter()
            return PipelineResponse(
                success=False,
                error=f"Unknown operator '{step.type}' at step {i}",
                step=i,
                total_duration_ms=(t_fail - t_start_total) * 1000,
                step_timings=step_timings
            )

        try:
            operator = operator_cls(step.params)
            t_step_start = time.perf_counter()
            image = operator.compute(image)
            t_step_end = time.perf_counter()
            step_timings.append(
                StepTiming(step=i, type=step.type, duration_ms=(t_step_end - t_step_start) * 1000)
            )
        except Exception as e:
            t_fail = time.perf_counter()
            return PipelineResponse(
                success=False,
                error=f"Error in step {i} ({step.type}): {type(e).__name__}: {e}",
                step=i,
                total_duration_ms=(t_fail - t_start_total) * 1000,
                step_timings=step_timings
            )

    try:
        encoded = encode_image_base64(image, request.image_format)
    except Exception as e:
        t_fail = time.perf_counter()
        error_msg = f"Failed to encode result: {type(e).__name__}: {e}"
        return PipelineResponse(
            success=False, 
            error=error_msg, 
            step=len(request.pipeline),
            total_duration_ms=(t_fail - t_start_total) * 1000,
            step_timings=step_timings
        )

    t_end_total = time.perf_counter()

    return PipelineResponse(
        success=True,
        image=encoded,
        image_format=request.image_format,
        total_duration_ms=(t_end_total - t_start_total) * 1000,
        step_timings=step_timings
    )
