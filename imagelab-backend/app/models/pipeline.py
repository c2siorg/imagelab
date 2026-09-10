from pydantic import BaseModel, Field, model_validator

from app.models.graph import PipelineGraph


class PipelineStep(BaseModel):
    type: str
    block_id: str | None = None
    params: dict = Field(default_factory=dict)
    branches: dict[str, list["PipelineStep"]] = Field(default_factory=dict)


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
