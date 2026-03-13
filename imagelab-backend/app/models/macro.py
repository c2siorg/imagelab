import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class Macro(SQLModel, table=True):
    """A saved, named pipeline sub-chain that can be reused as a composite block.

    ``steps`` mirrors the :class:`~app.models.pipeline.PipelineStep` structure
    (list of ``{"type": str, "params": dict}`` objects) and is stored as JSON
    so the column remains schema-free as new operators are added over time.
    """

    __tablename__ = "macro"  # type: ignore

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=255)
    description: str | None = Field(default=None)
    # Stored as JSON: list[{"type": str, "params": dict}]
    steps: list[Any] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
