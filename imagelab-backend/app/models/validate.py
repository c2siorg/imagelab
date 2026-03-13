from pydantic import BaseModel


class ValidationError(BaseModel):
    """Describes a validation error for a single pipeline step."""

    step: int
    operator: str
    message: str


class ValidationResponse(BaseModel):
    """Response from the pipeline validation endpoint."""

    valid: bool
    warnings: list[str]
    errors: list[ValidationError]
