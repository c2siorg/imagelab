from pydantic import BaseModel, Field


class ValidationError(BaseModel):
    """Describes a validation error for a single pipeline step."""

    step: int = Field(..., description="The 1-based index of the pipeline step.")
    operator: str = Field(..., description="The operator type key that failed validation.")
    message: str = Field(..., description="Detailed error message.")


class ValidationResponse(BaseModel):
    """Response from the pipeline validation endpoint."""

    valid: bool = Field(..., description="True if the pipeline has no errors.")
    warnings: list[str] = Field(default_factory=list, description="List of potential non-blocking issues.")
    errors: list[ValidationError] = Field(default_factory=list, description="List of blocking errors found.")
