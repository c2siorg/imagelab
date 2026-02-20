from app.models.pipeline import PipelineRequest, PipelineResponse
from app.operators.registry import get_operator
from app.utils.image import decode_base64_image, encode_image_base64

NOOP_TYPES = {"basic_readimage", "basic_writeimage", "border_for_all", "border_each_side"}


def execute_pipeline(request: PipelineRequest) -> PipelineResponse:
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
                error=f"Unknown operator: {step.type}",
                step=i,
            )

        try:
            operator = operator_cls(step.params)
            image = operator.compute(image)
        except Exception as e:
            return PipelineResponse(
                success=False,
                error=f"Error in step {i} ({step.type}): {e}",
                step=i,
            )

    try:
        encoded = encode_image_base64(image, request.image_format)
    except Exception as e:
        return PipelineResponse(success=False, error=f"Failed to encode result: {e}")

    return PipelineResponse(
        success=True,
        image=encoded,
        image_format=request.image_format,
    )
