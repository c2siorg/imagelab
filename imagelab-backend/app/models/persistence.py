import uuid
from datetime import UTC, datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy import Column, UniqueConstraint
from sqlmodel import Field, SQLModel


class Pipeline(SQLModel, table=True):
    __tablename__ = "pipeline"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    name: str
    owner_id: str | None = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=datetime.now(UTC))
    updated_at: datetime = Field(default_factory=datetime.now(UTC))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PipelineVersion(SQLModel, table=True):
    __tablename__ = "pipeline_version"
    __table_args__ = (UniqueConstraint("pipeline_id", "version_number", name="uq_pipeline_id_version_number"),)
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    pipeline_id: uuid.UUID = Field(foreign_key="pipeline.id", ondelete="CASCADE")
    version_number: int
    workspace_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(sa.JSON, nullable=False))
    pipeline_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(sa.JSON, nullable=False))
    change_note: str | None = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=datetime.now(UTC))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PipelineShare(SQLModel, table=True):
    __tablename__ = "pipeline_shares"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    pipeline_id: uuid.UUID = Field(foreign_key="pipeline.id", ondelete="CASCADE")
    pipeline_version_id: uuid.UUID = Field(foreign_key="pipeline_version.id", ondelete="CASCADE")
    token_hash: str = Field(index=True)
    permission: str  # "view" | "clone" | "edit"
    expires_at: datetime | None = Field(default=None, nullable=True)
    created_by: str | None = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=datetime.now(UTC))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
