import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class JobStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class ItemStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    success = "success"
    failed = "failed"


class BatchJob(SQLModel, table=True):
    """Represents a single batch-processing run submitted by the client.

    One BatchJob contains N images that are all processed through the same
    pipeline concurrently.  Results are written to :class:`BatchItemResult`
    rows as each image finishes so the client can poll progress in real time.
    """

    __tablename__ = "batchjob"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    status: JobStatus = Field(default=JobStatus.pending)
    total_images: int
    completed_count: int = Field(default=0)
    failed_count: int = Field(default=0)
    image_format: str = Field(default="png")
    # Pipeline definition stored as JSON so it travels with the job record.
    pipeline_steps: list[Any] = Field(default_factory=list, sa_column=Column(JSON))
    error: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class BatchItemResult(SQLModel, table=True):
    """Per-image result row for a :class:`BatchJob`.

    One row is created (as *pending*) for every image before execution starts,
    then updated in-place as the background worker processes each image.
    ``result_image_b64`` is **not** returned through the status endpoint —
    it is only used when building the ZIP download to avoid bloating JSON
    polling responses.  For production workloads with large images, replace
    this column with an object-storage key.
    """

    __tablename__ = "batchitemresult"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    job_id: uuid.UUID = Field(foreign_key="batchjob.id", index=True)
    image_index: int
    status: ItemStatus = Field(default=ItemStatus.pending)
    result_image_b64: str | None = Field(default=None)
    error: str | None = Field(default=None)
    duration_ms: float | None = Field(default=None)
