import secrets
from datetime import UTC, datetime

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


class SavedPipelineResponse(SQLModel):
    id: int
    name: str
    description: str
    share_token: str
    created_at: datetime
    updated_at: datetime
    pipeline_json: str
    workspace_state: str


class SavedPipelineSummary(SQLModel):
    id: int
    name: str
    description: str
    share_token: str
    created_at: datetime
    updated_at: datetime
