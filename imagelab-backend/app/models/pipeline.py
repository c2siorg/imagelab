from pydantic import BaseModel


class PipelineStep(BaseModel):
    type: str
    params: dict = {}


class PipelineRequest(BaseModel):
    image: str
    image_format: str = "png"
    pipeline: list[PipelineStep]


class StepTiming(BaseModel):
    step: int
    type: str
    duration_ms: float


class PipelineTimings(BaseModel):
    total_ms: float
    steps: list[StepTiming]


class PipelineResponse(BaseModel):
    success: bool
    image: str | None = None
    image_format: str | None = None
    error: str | None = None
    step: int | None = None
    timings: PipelineTimings | None = None
