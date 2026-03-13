"""Pipeline validation router — Issue #197.

POST /api/pipeline/validate performs static analysis on a pipeline definition
without executing it. It checks that every operator type is registered in the
OPERATOR_REGISTRY and returns structured errors for any unknown operators.
"""

from fastapi import APIRouter

from app.models.pipeline import PipelineRequest
from app.models.validate import ValidationError, ValidationResponse
from app.operators.registry import OPERATOR_REGISTRY

router = APIRouter()

# Operators that require no params — used for warning generation
_NOOP_OPERATOR = "basic_readimage"


@router.post("/pipeline/validate", response_model=ValidationResponse)
def validate_pipeline(request: PipelineRequest) -> ValidationResponse:
    """Validate a pipeline definition without executing it.

    Checks that every step's operator type is present in the OPERATOR_REGISTRY.
    Returns a structured list of errors for unknown operators and warnings for
    empty pipelines or other potential issues.

    This endpoint is intentionally ``def`` (not ``async def``) to keep it
    consistent with the execute endpoint and avoid asyncio overhead.

    Returns:
        ValidationResponse with ``valid``, ``warnings``, and ``errors`` fields.
    """
    errors: list[ValidationError] = []
    warnings: list[str] = []

    if not request.pipeline:
        warnings.append("Pipeline is empty — no operators will be applied.")

    for i, step in enumerate(request.pipeline, start=1):
        op_type = step.type

        if not op_type or not op_type.strip():
            errors.append(
                ValidationError(
                    step=i,
                    operator=op_type or "",
                    message="Operator type must not be empty.",
                )
            )
            continue

        if op_type not in OPERATOR_REGISTRY:
            errors.append(
                ValidationError(
                    step=i,
                    operator=op_type,
                    message=f"Unknown operator '{op_type}'. It is not registered in the operator registry.",
                )
            )

    return ValidationResponse(
        valid=len(errors) == 0,
        warnings=warnings,
        errors=errors,
    )
