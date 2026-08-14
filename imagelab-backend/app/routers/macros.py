"""Macro REST CRUD endpoints.

Includes graph validation and dependency safety checks blocking deletion
if a macro is actively referenced by any existing pipeline or macro.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.database import get_db
from app.models.graph import GraphCycleError, PipelineGraph
from app.models.persistence import Pipeline, PipelineVersion
from app.services.graph_engine import GraphTypeError, validate_macro_graph

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/macros", tags=["macros"])

SessionDep = Annotated[Session, Depends(get_db)]


# Request / Response Schemas


class MacroCreate(BaseModel):
    name: str
    owner_id: str | None = None
    workspace_json: dict[str, Any] = {}
    pipeline_json: dict[str, Any] = {}
    description: str | None = None


class MacroUpdate(BaseModel):
    name: str | None = None
    owner_id: str | None = None
    workspace_json: dict[str, Any] | None = None
    pipeline_json: dict[str, Any] | None = None
    description: str | None = None


class MacroOut(BaseModel):
    id: uuid.UUID
    name: str
    owner_id: str | None
    is_macro: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MacroVersionOut(BaseModel):
    id: uuid.UUID
    macro_id: uuid.UUID
    version_number: int
    name: str
    owner_id: str | None
    workspace_json: dict[str, Any]
    pipeline_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime


# Helpers


def _get_macro_or_404(session: Session, macro_id: uuid.UUID) -> Pipeline:
    macro = session.get(Pipeline, macro_id)
    if macro is None or not macro.is_macro:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Macro not found")
    return macro


def _extract_macro_ids_from_nodes(nodes: list[dict[str, Any]]) -> set[str]:
    """Recursively extract all macro_id references from a list of graph nodes."""
    macro_ids: set[str] = set()
    for node in nodes:
        node_type = node.get("type") or node.get("op")
        params = node.get("params", {})

        if node_type == "macro_ref":
            macro_id = params.get("macro_id")
            if macro_id:
                macro_ids.add(macro_id)
        elif node_type in ("macro_blend", "macro_if_else"):
            # Recursively scan control-flow branches
            op1_branch = params.get("op1_branch") or params.get("OP1") or []
            op2_branch = params.get("op2_branch") or params.get("OP2") or []
            if_branch = params.get("if_branch") or params.get("IF_BRANCH") or []
            else_branch = params.get("else_branch") or params.get("ELSE_BRANCH") or []

            for branch in (op1_branch, op2_branch, if_branch, else_branch):
                if branch:
                    macro_ids.update(_extract_macro_ids_from_nodes(branch))

    return macro_ids


def _check_macro_in_use(session: Session, macro_id: uuid.UUID) -> bool:
    """Return True if macro_id is referenced in any existing pipeline or macro's latest PipelineVersion."""
    macro_id_str = str(macro_id)

    # Subquery to get the latest version for each pipeline
    latest_versions_subquery = (
        select(PipelineVersion.pipeline_id, func.max(PipelineVersion.version_number).label("max_version"))
        .group_by(PipelineVersion.pipeline_id)
        .subquery()
    )

    # Query only the latest versions
    latest_versions = session.exec(
        select(PipelineVersion).join(
            latest_versions_subquery,
            (PipelineVersion.pipeline_id == latest_versions_subquery.c.pipeline_id)
            & (PipelineVersion.version_number == latest_versions_subquery.c.max_version),
        )
    ).all()

    for ver in latest_versions:
        if ver.pipeline_id == macro_id:
            continue
        pipeline = session.get(Pipeline, ver.pipeline_id)
        if pipeline is None:
            continue
        p_json = ver.pipeline_json or {}
        nodes = p_json.get("nodes", [])
        referenced_macro_ids = _extract_macro_ids_from_nodes(nodes)
        if macro_id_str in referenced_macro_ids:
            return True
    return False


def _validate_macro_payload(session: Session, pipeline_json: dict[str, Any], macro_id: uuid.UUID | None = None) -> None:
    """Run graph structure, cycle, and nested macro validation on pipeline_json."""
    if not pipeline_json:
        return
    try:
        graph = PipelineGraph.model_validate(pipeline_json)
        validate_macro_graph(graph, session, macro_id=macro_id)
    except GraphCycleError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Graph cycle detected: {e}") from e
    except GraphTypeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Graph type mismatch: {e}") from e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid macro graph: {e}") from e


# Endpoints


@router.get("", response_model=list[MacroVersionOut], summary="List all macros")
@router.get("/", response_model=list[MacroVersionOut], summary="List all macros", include_in_schema=False)
def list_macros(session: SessionDep) -> list[MacroVersionOut]:
    macros = session.exec(select(Pipeline).where(Pipeline.is_macro == True)).all()  # noqa: E712
    result = []
    for macro in macros:
        version = session.exec(
            select(PipelineVersion)
            .where(PipelineVersion.pipeline_id == macro.id)
            .order_by(PipelineVersion.version_number.desc())
            .limit(1)
        ).first()
        if version:
            result.append(
                MacroVersionOut(
                    id=version.id,
                    macro_id=macro.id,
                    version_number=version.version_number,
                    name=macro.name,
                    owner_id=macro.owner_id,
                    workspace_json=version.workspace_json,
                    pipeline_json=version.pipeline_json,
                    created_at=version.created_at,
                    updated_at=macro.updated_at,
                )
            )
    return result


@router.post("", response_model=MacroVersionOut, status_code=status.HTTP_201_CREATED, summary="Create a new macro")
@router.post(
    "/",
    response_model=MacroVersionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new macro",
    include_in_schema=False,
)
def create_macro(body: MacroCreate, session: SessionDep) -> MacroVersionOut:
    _validate_macro_payload(session, body.pipeline_json)

    try:
        pipeline = Pipeline(name=body.name, owner_id=body.owner_id, is_macro=True)
        session.add(pipeline)
        session.flush()

        version = PipelineVersion(
            pipeline_id=pipeline.id,
            version_number=1,
            workspace_json=body.workspace_json,
            pipeline_json=body.pipeline_json,
            change_note=body.description,
        )
        session.add(version)
        session.commit()
        session.refresh(version)

        return MacroVersionOut(
            id=version.id,
            macro_id=pipeline.id,
            version_number=version.version_number,
            name=pipeline.name,
            owner_id=pipeline.owner_id,
            workspace_json=version.workspace_json,
            pipeline_json=version.pipeline_json,
            created_at=version.created_at,
            updated_at=pipeline.updated_at,
        )
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Macro version conflict") from exc
    except Exception as exc:
        session.rollback()
        logger.exception("Failed to create macro")
        raise HTTPException(status_code=500, detail="Failed to create macro. Please try again.") from exc


@router.get("/{macro_id}", response_model=MacroVersionOut, summary="Retrieve a macro by ID")
def get_macro(macro_id: uuid.UUID, session: SessionDep) -> MacroVersionOut:
    macro = _get_macro_or_404(session, macro_id)

    version = session.exec(
        select(PipelineVersion)
        .where(PipelineVersion.pipeline_id == macro_id)
        .order_by(PipelineVersion.version_number.desc())
        .limit(1)
    ).first()

    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Macro version not found")

    return MacroVersionOut(
        id=version.id,
        macro_id=macro.id,
        version_number=version.version_number,
        name=macro.name,
        owner_id=macro.owner_id,
        workspace_json=version.workspace_json,
        pipeline_json=version.pipeline_json,
        created_at=version.created_at,
        updated_at=macro.updated_at,
    )


@router.put("/{macro_id}", response_model=MacroVersionOut, summary="Update a macro")
def update_macro(macro_id: uuid.UUID, body: MacroUpdate, session: SessionDep) -> MacroVersionOut:
    macro = _get_macro_or_404(session, macro_id)

    latest_version = session.exec(
        select(PipelineVersion)
        .where(PipelineVersion.pipeline_id == macro_id)
        .order_by(PipelineVersion.version_number.desc())
        .limit(1)
    ).first()

    fallback_p_json = latest_version.pipeline_json if latest_version else {}
    fallback_w_json = latest_version.workspace_json if latest_version else {}
    new_pipeline_json = body.pipeline_json if body.pipeline_json is not None else fallback_p_json
    new_workspace_json = body.workspace_json if body.workspace_json is not None else fallback_w_json

    _validate_macro_payload(session, new_pipeline_json, macro_id=macro_id)

    try:
        if body.name:
            macro.name = body.name
        if body.owner_id is not None:
            macro.owner_id = body.owner_id
        macro.updated_at = datetime.now(UTC)
        session.add(macro)

        new_version_num = (latest_version.version_number + 1) if latest_version else 1
        new_version = PipelineVersion(
            pipeline_id=macro_id,
            version_number=new_version_num,
            workspace_json=new_workspace_json,
            pipeline_json=new_pipeline_json,
            change_note=body.description,
        )
        session.add(new_version)
        session.commit()
        session.refresh(new_version)

        return MacroVersionOut(
            id=new_version.id,
            macro_id=macro.id,
            version_number=new_version.version_number,
            name=macro.name,
            owner_id=macro.owner_id,
            workspace_json=new_version.workspace_json,
            pipeline_json=new_version.pipeline_json,
            created_at=new_version.created_at,
            updated_at=macro.updated_at,
        )
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Macro version conflict") from exc
    except Exception as exc:
        session.rollback()
        logger.exception("Failed to update macro")
        raise HTTPException(status_code=500, detail="Failed to update macro. Please try again.") from exc


@router.delete("/{macro_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a macro")
def delete_macro(macro_id: uuid.UUID, session: SessionDep) -> None:
    macro = _get_macro_or_404(session, macro_id)

    # Dependency safety check: block deletion if actively referenced
    if _check_macro_in_use(session, macro_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete macro: referenced by active pipelines/macros",
        )

    session.delete(macro)
    session.commit()
