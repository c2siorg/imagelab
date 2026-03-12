from pydantic import BaseModel


class PipelineStep(BaseModel):
    type: str
    params: dict = {}


class PipelineRequest(BaseModel):
    image: str
    image_format: str = "png"
    pipeline: list[PipelineStep]
    include_intermediates: bool = False


class StepTiming(BaseModel):
    step: int
    operator_type: str
    duration_ms: float


class PipelineTimings(BaseModel):
    total_ms: float
    steps: list[StepTiming]


class ImageStats(BaseModel):
    width: int
    height: int
    channels: int
    dtype: str
    min_val: float
    max_val: float
    mean_val: float
    histograms: list[list[int]]  # one list for grayscale, three lists for B/G/R; alpha excluded


class StepResult(BaseModel):
    step: int
    operator_type: str
    thumbnail: str  # base64-encoded JPEG thumbnail, max 200px wide
    stats: ImageStats


class PipelineResponse(BaseModel):
    success: bool
    image: str | None = None
    image_format: str | None = None
    error: str | None = None
    step: int | None = None
    timings: PipelineTimings | None = None
    intermediates: list[StepResult] | None = None
