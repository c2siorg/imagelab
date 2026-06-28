"""Persistence router – pipeline CRUD, versioning, and restore endpoints.

Transaction safety
------------------
Version creation uses explicit ``session.commit()`` after atomically computing
``MAX(version_number) + 1``.  Because SQLAlchemy 2 sessions auto-begin on the
first DB touch, we never call ``session.begin()`` manually inside a route that
has already issued a query (e.g. _get_pipeline_or_404).  Instead we rely on
the session's implicit transaction + ``session.commit()`` / ``session.rollback()``.

The DB-level UNIQUE(pipeline_id, version_number) constraint is the final guard
against concurrent duplicate version numbers; the router surfaces that as 409.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.database import get_db
from app.models.persistence import Pipeline, PipelineShare, PipelineVersion

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pipelines", tags=["pipelines"])
share_router = APIRouter(prefix="/share", tags=["sharing"])


# Request / Response schemas


class PipelineCreate(BaseModel):
    name: str
    owner_id: str | None = None
    workspace_json: dict[str, Any]
    pipeline_json: dict[str, Any]
    change_note: str | None = None


class VersionCreate(BaseModel):
    workspace_json: dict[str, Any]
    pipeline_json: dict[str, Any]
    change_note: str | None = None


class PipelineOut(BaseModel):
    id: uuid.UUID
    name: str
    owner_id: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VersionOut(BaseModel):
    id: uuid.UUID
    pipeline_id: uuid.UUID
    version_number: int
    workspace_json: dict[str, Any]
    pipeline_json: dict[str, Any]
    change_note: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class VersionSummary(BaseModel):
    id: uuid.UUID
    pipeline_id: uuid.UUID
    version_number: int
    change_note: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ShareCreate(BaseModel):
    version_number: int
    permission: str  # "view" | "clone" | "edit"
    expires_at: datetime | None = None
    created_by: str | None = None

    @field_validator("permission")
    @classmethod
    def validate_permission(cls, value: str) -> str:
        if value not in {"view", "clone", "edit"}:
            raise ValueError("permission must be view, clone, or edit")
        return value


class ShareTokenOut(BaseModel):
    token: str


class ShareLookupOut(BaseModel):
    pipeline_id: uuid.UUID
    pipeline_name: str
    version_number: int
    workspace_json: dict[str, Any]
    pipeline_json: dict[str, Any]
    permission: str


class CloneRequest(BaseModel):
    name: str | None = None
    owner_id: str | None = None


INVALID_SHARE_DETAIL = "Invalid or expired share link"


# Dependency alias

SessionDep = Annotated[Session, Depends(get_db)]

# Helpers


def _get_pipeline_or_404(session: Session, pipeline_id: uuid.UUID) -> Pipeline:
    pipeline = session.get(Pipeline, pipeline_id)
    if pipeline is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return pipeline


def _next_version_number(session: Session, pipeline_id: uuid.UUID) -> int:
    """Return MAX(version_number) + 1 for *pipeline_id* within the current tx."""
    max_version = session.exec(
        select(func.max(PipelineVersion.version_number)).where(PipelineVersion.pipeline_id == pipeline_id)
    ).one()
    return (max_version or 0) + 1


def _build_version(
    session: Session,
    pipeline_id: uuid.UUID,
    workspace_json: dict[str, Any],
    pipeline_json: dict[str, Any],
    change_note: str | None,
) -> PipelineVersion:
    """Add a new PipelineVersion to the session; caller must commit."""
    version = PipelineVersion(
        pipeline_id=pipeline_id,
        version_number=_next_version_number(session, pipeline_id),
        workspace_json=workspace_json,
        pipeline_json=pipeline_json,
        change_note=change_note,
    )
    session.add(version)
    return version


def _get_active_share(session: Session, token: str) -> PipelineShare:
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    share = session.exec(select(PipelineShare).where(PipelineShare.token_hash == token_hash)).first()
    if share is None or (share.expires_at is not None and share.expires_at < datetime.now(UTC)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=INVALID_SHARE_DETAIL)
    return share


# POST /api/pipelines  – create pipeline + version 1


@router.post(
    "/",
    response_model=VersionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a pipeline and its first immutable version (v1)",
)
def create_pipeline(body: PipelineCreate, session: SessionDep) -> VersionOut:
    try:
        pipeline = Pipeline(name=body.name, owner_id=body.owner_id)
        session.add(pipeline)
        session.flush()  # populate pipeline.id before FK reference

        version = _build_version(
            session,
            pipeline_id=pipeline.id,
            workspace_json=body.workspace_json,
            pipeline_json=body.pipeline_json,
            change_note=body.change_note,
        )
        session.commit()
        session.refresh(version)
        return VersionOut.model_validate(version)
    except IntegrityError as exc:
        session.rollback()
        logger.warning("Integrity error creating pipeline: %s", exc)
        raise HTTPException(status_code=409, detail="Version conflict – please retry") from exc
    except Exception as exc:
        session.rollback()
        logger.exception("Failed to create pipeline")
        raise HTTPException(status_code=500, detail="Failed to create pipeline") from exc


# GET /api/pipelines  – list all pipelines (metadata only)


@router.get(
    "/",
    response_model=list[PipelineOut],
    summary="List all pipelines",
)
def list_pipelines(session: SessionDep) -> list[PipelineOut]:
    pipelines = session.exec(select(Pipeline)).all()  # type: ignore[arg-type]
    return [PipelineOut.model_validate(p) for p in pipelines]


# GET /api/pipelines/{pipeline_id}  – latest version


@router.get(
    "/{pipeline_id}",
    response_model=VersionOut,
    summary="Retrieve the latest version of a pipeline",
)
def get_pipeline(pipeline_id: uuid.UUID, session: SessionDep) -> VersionOut:
    _get_pipeline_or_404(session, pipeline_id)

    version = session.exec(
        select(PipelineVersion)
        .where(PipelineVersion.pipeline_id == pipeline_id)
        .order_by(PipelineVersion.version_number.desc())  # type: ignore[attr-defined]
        .limit(1)
    ).first()

    if version is None:
        raise HTTPException(status_code=404, detail="No versions found for this pipeline")

    return VersionOut.model_validate(version)


# DELETE /api/pipelines/{pipeline_id}


@router.delete(
    "/{pipeline_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a pipeline and all its versions (cascade)",
)
def delete_pipeline(pipeline_id: uuid.UUID, session: SessionDep) -> None:
    pipeline = _get_pipeline_or_404(session, pipeline_id)
    session.delete(pipeline)
    session.commit()


# POST /api/pipelines/{pipeline_id}/versions  – save a new version


@router.post(
    "/{pipeline_id}/versions",
    response_model=VersionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Save a new immutable version for a pipeline",
)
def create_version(pipeline_id: uuid.UUID, body: VersionCreate, session: SessionDep) -> VersionOut:
    pipeline = _get_pipeline_or_404(session, pipeline_id)

    try:
        pipeline.updated_at = datetime.now(UTC)
        session.add(pipeline)

        version = _build_version(
            session,
            pipeline_id=pipeline_id,
            workspace_json=body.workspace_json,
            pipeline_json=body.pipeline_json,
            change_note=body.change_note,
        )
        session.commit()
        session.refresh(version)
        return VersionOut.model_validate(version)
    except IntegrityError as exc:
        session.rollback()
        logger.warning("Version conflict for pipeline %s: %s", pipeline_id, exc)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Version conflict – please retry",
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        session.rollback()
        logger.exception("Failed to create version for pipeline %s", pipeline_id)
        raise HTTPException(status_code=500, detail="Internal error") from exc


# GET /api/pipelines/{pipeline_id}/versions  – list all versions (summaries)


@router.get(
    "/{pipeline_id}/versions",
    response_model=list[VersionSummary],
    summary="List all versions of a pipeline (newest first)",
)
def list_versions(pipeline_id: uuid.UUID, session: SessionDep) -> list[VersionSummary]:
    _get_pipeline_or_404(session, pipeline_id)

    versions = session.exec(
        select(PipelineVersion)
        .where(PipelineVersion.pipeline_id == pipeline_id)
        .order_by(PipelineVersion.version_number.desc())  # type: ignore[attr-defined]
    ).all()

    return [VersionSummary.model_validate(v) for v in versions]


# GET /api/pipelines/{pipeline_id}/versions/{version_number}


@router.get(
    "/{pipeline_id}/versions/{version_number}",
    response_model=VersionOut,
    summary="Fetch a specific historical version by number",
)
def get_version(pipeline_id: uuid.UUID, version_number: int, session: SessionDep) -> VersionOut:
    _get_pipeline_or_404(session, pipeline_id)

    version = session.exec(
        select(PipelineVersion).where(
            PipelineVersion.pipeline_id == pipeline_id,
            PipelineVersion.version_number == version_number,
        )
    ).first()

    if version is None:
        raise HTTPException(
            status_code=404,
            detail=f"Version {version_number} not found for this pipeline",
        )

    return VersionOut.model_validate(version)


# POST /api/pipelines/{pipeline_id}/restore/{version_number}


@router.post(
    "/{pipeline_id}/restore/{version_number}",
    response_model=VersionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Restore a historical version by creating a new version from it",
)
def restore_version(pipeline_id: uuid.UUID, version_number: int, session: SessionDep) -> VersionOut:
    pipeline = _get_pipeline_or_404(session, pipeline_id)

    source = session.exec(
        select(PipelineVersion).where(
            PipelineVersion.pipeline_id == pipeline_id,
            PipelineVersion.version_number == version_number,
        )
    ).first()

    if source is None:
        raise HTTPException(
            status_code=404,
            detail=f"Version {version_number} not found for this pipeline",
        )

    try:
        pipeline.updated_at = datetime.now(UTC)
        session.add(pipeline)

        restored = _build_version(
            session,
            pipeline_id=pipeline_id,
            workspace_json=dict(source.workspace_json),
            pipeline_json=dict(source.pipeline_json),
            change_note=f"Restored from v{version_number}",
        )
        session.commit()
        session.refresh(restored)
        return VersionOut.model_validate(restored)
    except IntegrityError as exc:
        session.rollback()
        logger.warning(
            "Version conflict restoring v%s for pipeline %s: %s",
            version_number,
            pipeline_id,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Version conflict – please retry",
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        session.rollback()
        logger.exception("Failed to restore version %s for pipeline %s", version_number, pipeline_id)
        raise HTTPException(status_code=500, detail="Internal error") from exc


# POST /api/pipelines/{pipeline_id}/share
@router.post(
    "/{pipeline_id}/share",
    response_model=ShareTokenOut,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a secure share token for a specific pipeline version",
)
def share_pipeline(
    pipeline_id: uuid.UUID,
    body: ShareCreate,
    session: SessionDep,
) -> ShareTokenOut:
    _get_pipeline_or_404(session, pipeline_id)

    # Find the version
    version = session.exec(
        select(PipelineVersion).where(
            PipelineVersion.pipeline_id == pipeline_id,
            PipelineVersion.version_number == body.version_number,
        )
    ).first()

    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {body.version_number} not found for this pipeline",
        )

    try:
        raw_token = str(uuid.uuid4())
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

        share = PipelineShare(
            pipeline_id=pipeline_id,
            pipeline_version_id=version.id,
            token_hash=token_hash,
            permission=body.permission,
            expires_at=body.expires_at,
            created_by=body.created_by,
        )
        session.add(share)
        session.commit()
        return ShareTokenOut(token=raw_token)
    except Exception as exc:
        session.rollback()
        logger.exception("Failed to create share link")
        raise HTTPException(status_code=500, detail="Internal error") from exc


# GET /api/share/{token}
@share_router.get(
    "/{token}",
    response_model=ShareLookupOut,
    summary="Look up a shared pipeline/version configuration",
)
def get_shared_pipeline(token: str, session: SessionDep) -> ShareLookupOut:
    share = _get_active_share(session, token)

    pipeline = session.get(Pipeline, share.pipeline_id)
    version = session.get(PipelineVersion, share.pipeline_version_id)

    if pipeline is None or version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired share link",
        )

    return ShareLookupOut(
        pipeline_id=pipeline.id,
        pipeline_name=pipeline.name,
        version_number=version.version_number,
        workspace_json=version.workspace_json,
        pipeline_json=version.pipeline_json,
        permission=share.permission,
    )


# POST /api/share/{token}/clone
@share_router.post(
    "/{token}/clone",
    response_model=VersionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Clone a shared pipeline into a new local pipeline",
)
def clone_shared_pipeline(
    token: str,
    body: CloneRequest,
    session: SessionDep,
) -> VersionOut:
    share = _get_active_share(session, token)

    if share.permission != "clone":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cloning not permitted for this share link",
        )

    pipeline = session.get(Pipeline, share.pipeline_id)
    version = session.get(PipelineVersion, share.pipeline_version_id)

    if pipeline is None or version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired share link",
        )

    try:
        new_name = body.name or f"Clone of {pipeline.name}"
        new_pipeline = Pipeline(name=new_name, owner_id=body.owner_id)
        session.add(new_pipeline)
        session.flush()

        new_version = PipelineVersion(
            pipeline_id=new_pipeline.id,
            version_number=1,
            workspace_json=dict(version.workspace_json),
            pipeline_json=dict(version.pipeline_json),
            change_note=f"Cloned from {pipeline.name} (v{version.version_number})",
        )
        session.add(new_version)
        session.commit()
        session.refresh(new_version)
        return VersionOut.model_validate(new_version)
    except Exception as exc:
        session.rollback()
        logger.exception("Failed to clone shared pipeline")
        raise HTTPException(status_code=500, detail="Internal error") from exc


@share_router.post(
    "/{token}/versions",
    response_model=VersionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a version in a pipeline through an edit share token",
)
def create_shared_version(
    token: str,
    body: VersionCreate,
    session: SessionDep,
) -> VersionOut:
    share = _get_active_share(session, token)
    if share.permission != "edit":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Editing not permitted for this share link",
        )

    pipeline = session.get(Pipeline, share.pipeline_id)
    if pipeline is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=INVALID_SHARE_DETAIL)

    try:
        version = _build_version(
            session,
            pipeline_id=pipeline.id,
            workspace_json=body.workspace_json,
            pipeline_json=body.pipeline_json,
            change_note=body.change_note,
        )
        pipeline.updated_at = datetime.now(UTC)
        session.add(pipeline)
        session.commit()
        session.refresh(version)
        return VersionOut.model_validate(version)
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Version conflict – please retry",
        ) from exc
    except Exception as exc:
        session.rollback()
        logger.exception("Failed to create shared pipeline version")
        raise HTTPException(status_code=500, detail="Internal error") from exc
