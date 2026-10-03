from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.graph import PipelineGraph

# 1x1 PNG so the example actually decodes
TINY_PNG = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="


class PipelineStep(BaseModel):
    type: str = Field(
        description="Registered operator key in the form '<category>_<operatorname>', "
        "e.g. 'blurring_applyblur'.",
    )
    block_id: str | None = Field(
        default=None,
        description="Client-side block ID. Echoed back in step results and errors.",
    )
    params: dict = Field(
        default_factory=dict,
        description="Operator-specific parameters (camelCase), e.g. {'widthSize': 3}. "
        "Omitted params fall back to the operator's defaults.",
    )
    branches: dict[str, list["PipelineStep"]] = Field(
        default_factory=dict,
        description=(
            "Named sub-pipelines for branching operators. "
            "Maps a branch name to an ordered list of steps (same shape as this step)."
        ),
    )
    macro_stack: list[dict[str, str]] = Field(default_factory=list)


class PipelineRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "image": TINY_PNG,
                    "image_format": "png",
                    "pipeline": [
                        {
                            "type": "blurring_applyblur",
                            "block_id": "blur1",
                            "params": {"widthSize": 3, "heightSize": 3},
                        },
                        {
                            "type": "thresholding_applythreshold",
                            "block_id": "threshold1",
                            "params": {"thresholdValue": 127, "maxValue": 255},
                        },
                    ],
                }
            ]
        }
    )

    image: str = Field(
        min_length=1,
        description="Base64-encoded input image (no data-URI prefix).",
    )
    image_format: Literal["png", "jpeg"] = Field(
        default="png",
        description="Format used to encode output images.",
    )
    graph: PipelineGraph | None = Field(
        default=None,
        description="Node/edge graph. Compiled into a pipeline before execution.",
    )
    # Keep default None so Pydantic catches when the key is completely missing in raw JSON
    pipeline: list[PipelineStep] | None = Field(
        default=None,
        description="Flat ordered list of steps. Overwritten if 'graph' is provided.",
    )

    @model_validator(mode="after")
    def validate_payload_presence(self):
        if self.pipeline is None and self.graph is None:
            raise ValueError("Field 'pipeline' or 'graph' is required.")
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
