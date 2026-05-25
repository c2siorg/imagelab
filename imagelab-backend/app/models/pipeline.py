from pydantic import BaseModel


class PipelineStep(BaseModel):
    type: str
    block_id: str | None = None
    params: dict = {}


class PipelineRequest(BaseModel):
    image: str
    image_format: str = "png"
    pipeline: list[PipelineStep]


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
