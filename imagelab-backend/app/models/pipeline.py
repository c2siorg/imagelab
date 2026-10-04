import re
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.graph import PipelineGraph


class PipelineStep(BaseModel):
    type: str
    block_id: str | None = None
    params: dict = Field(default_factory=dict)
    branches: dict[str, list["PipelineStep"]] = Field(default_factory=dict)
    macro_stack: list[dict[str, str]] = Field(default_factory=list)


class PipelineRequest(BaseModel):
    image: str
    image_format: str = "png"
    graph: PipelineGraph | None = None
    # Keep default None so Pydantic catches when the key is completely missing in raw JSON
    pipeline: list[PipelineStep] | None = None

    @model_validator(mode="after")
    def validate_payload_presence(self):
        # 1. If 'pipeline' key was completely missing and no 'graph' was given, raise ValueError (HTTP 422)
        if self.pipeline is None and self.graph is None:
            raise ValueError("Field 'pipeline' or 'graph' is required.")
        # 2. If 'pipeline' key was explicitly provided as missing/None, initialize to [] for execution
        if self.pipeline is None:
            self.pipeline = []
        return self


class StepTiming(BaseModel):
    step: int
    operator_type: str
    duration_ms: float


class PipelineTimings(BaseModel):
    total_ms: float
    steps: list[StepTiming]


class StepResult(BaseModel):
    index: int
    block_id: str | None = None
    type: str
    success: bool
    thumbnail: str | None = None
    image_format: str | None = None
    timing_ms: float | None = None
    has_full_image: bool = False
    error: str | None = None
    macro_stack: list[dict[str, str]] = Field(default_factory=list)


class ImageAnalysis(BaseModel):
    width: int
    height: int
    channels: int
    dtype: str
    min: float
    max: float
    mean: float | list[float]
    std: float | list[float]


class ImageHistogram(BaseModel):
    bins: list[int]
    luminance: list[int]
    red: list[int] | None = None
    green: list[int] | None = None
    blue: list[int] | None = None


class PipelineResponse(BaseModel):
    success: bool
    execution_id: str | None = None
    image: str | None = None
    image_format: str | None = None
    error: str | None = None
    step: int | None = None
    error_block_id: str | None = None
    timings: PipelineTimings | None = None
    step_results: list[StepResult] = []


class StepInspectResponse(BaseModel):
    success: bool
    execution_id: str
    block_id: str
    index: int
    type: str
    image: str
    image_format: str
    timing_ms: float | None = None
    analysis: ImageAnalysis
    histogram: ImageHistogram


class ExportPythonRequest(BaseModel):
    graph: PipelineGraph | None = None
    pipeline: list[PipelineStep] | None = None
    pipeline_name: str = "ImageLab Pipeline"
    input_filename: str = "input.jpg"
    output_filename: str = "output.jpg"

    @field_validator("input_filename", mode="before")
    @classmethod
    def sanitize_input_filename(cls, v: Any) -> str:
        if not isinstance(v, str):
            return "input.jpg"
        cleaned = re.sub(r"[\r\n\x00-\x1f\x7f-\x9f]", "", v).strip()
        return cleaned or "input.jpg"

    @field_validator("output_filename", mode="before")
    @classmethod
    def sanitize_output_filename(cls, v: Any) -> str:
        if not isinstance(v, str):
            return "output.jpg"
        cleaned = re.sub(r"[\r\n\x00-\x1f\x7f-\x9f]", "", v).strip()
        return cleaned or "output.jpg"

    @field_validator("pipeline_name", mode="before")
    @classmethod
    def sanitize_pipeline_name(cls, v: Any) -> str:
        if not isinstance(v, str):
            return "ImageLab Pipeline"
        cleaned = re.sub(r"[\r\n\x00-\x1f\x7f-\x9f]", " ", v).strip()
        return cleaned or "ImageLab Pipeline"

    @model_validator(mode="after")
    def validate_payload_presence(self):
        if self.pipeline is None and self.graph is None:
            raise ValueError("Field 'pipeline' or 'graph' is required.")
        if self.pipeline is None:
            self.pipeline = []
        return self


class ExportPythonResponse(BaseModel):
    success: bool
    code: str
    filename: str
    unsupported_operators: list[str] = Field(default_factory=list)
