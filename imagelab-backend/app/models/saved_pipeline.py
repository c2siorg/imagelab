import json
import secrets
from datetime import UTC, datetime

from pydantic import ConfigDict, field_validator
from sqlmodel import Field, SQLModel


class SavedPipeline(SQLModel, table=True):
    """Persisted pipeline stored in the database."""

    __tablename__ = "saved_pipelines"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=200, index=True)
    description: str = Field(default="", max_length=1000)
    pipeline_json: str  # JSON-serialised list[PipelineStep]
    workspace_state: str = Field(default="")  # JSON-serialised Blockly workspace state
    share_token: str = Field(
        default_factory=lambda: secrets.token_urlsafe(12),
        unique=True,
        index=True,
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ---------------------------------------------------------------------------
# Pydantic schemas (separate from the SQLModel table to keep API surface clean)
# ---------------------------------------------------------------------------


class SavePipelineRequest(SQLModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)
    pipeline_json: str  # client serialises the pipeline steps as JSON
    workspace_state: str = Field(default="")  # Blockly workspace JSON for reload

    @field_validator("pipeline_json")
    @classmethod
    def validate_pipeline_json(cls, value: str) -> str:
        try:
            json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError(f"pipeline_json is not valid JSON: {exc}") from exc
        return value

    @field_validator("pipeline_json", "workspace_state")
    @classmethod
    def validate_payload_size(cls, value: str) -> str:
        # Keep payloads bounded to prevent accidental or malicious oversized requests.
        if len(value) > 1_000_000:
            raise ValueError("Payload too large (max 1,000,000 characters)")
        return value


class SavedPipelineResponse(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    share_token: str
    created_at: datetime
    updated_at: datetime
    pipeline_json: str
    workspace_state: str


class SavedPipelineSummary(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
