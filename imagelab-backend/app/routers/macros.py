"""Macros router — Feature 5: Custom Composite Operators.

A *macro* is a named, stored pipeline sub-chain (list of operator steps) that
can be loaded by the frontend and inserted into any pipeline as a reusable
composite block.

Endpoints
---------
POST   /api/macros              — create a new macro
GET    /api/macros              — list all macros (summary, no steps)
GET    /api/macros/{macro_id}   — retrieve a single macro with full steps
PUT    /api/macros/{macro_id}   — update name, description and/or steps
DELETE /api/macros/{macro_id}   — permanently delete a macro

All routes use plain ``def`` (not ``async def``) because they only perform
synchronous DB I/O, consistent with the existing pipeline router pattern.
"""

import logging
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, col, select

from app.database import get_db
from app.models.macro import Macro

logger = logging.getLogger(__name__)

router = APIRouter(tags=["macros"])


# ---------------------------------------------------------------------------
# Pydantic schemas  (kept separate from SQLModel table to avoid coupling)
# ---------------------------------------------------------------------------


class MacroStepSchema(BaseModel):
    type: str = Field(..., description="Operator type key (e.g. 'blurring_applygaussianblur').")
    params: dict = Field(default_factory=dict, description="Operator parameters.")


class MacroCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Unique human-readable name.")
    description: str | None = Field(None, description="Optional description of what this macro does.")
    steps: list[MacroStepSchema] = Field(..., description="Ordered list of pipeline steps.")


class MacroUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255, description="Updated name.")
    description: str | None = Field(None, description="Updated description.")
    steps: list[MacroStepSchema] | None = Field(None, description="Updated list of steps.")


class MacroSummary(BaseModel):
    id: uuid.UUID = Field(..., description="Unique ID of the macro.")
    name: str = Field(..., description="Human-readable name.")
    description: str | None = Field(None, description="Optional description.")
    step_count: int = Field(..., description="Number of operators in the macro.")
    created_at: datetime = Field(..., description="ISO creation timestamp.")
    updated_at: datetime = Field(..., description="ISO last-update timestamp.")


class MacroDetail(MacroSummary):
    steps: list[MacroStepSchema]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _to_summary(m: Macro) -> MacroSummary:
    return MacroSummary(
        id=m.id,
        name=m.name,
        description=m.description,
        step_count=len(m.steps) if m.steps else 0,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _to_detail(m: Macro) -> MacroDetail:
    return MacroDetail(
        id=m.id,
        name=m.name,
        description=m.description,
        step_count=len(m.steps) if m.steps else 0,
        steps=[MacroStepSchema(**s) for s in (m.steps or [])],
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _assert_name_available(name: str, db: Session, exclude_id: uuid.UUID | None = None) -> None:
    """Raise 409 if *name* is already taken by another macro row."""
    stmt = select(Macro).where(Macro.name == name)
    existing = db.exec(stmt).first()
    if existing and existing.id != exclude_id:
        raise HTTPException(status_code=409, detail=f"A macro named '{name}' already exists.")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/macros", response_model=MacroDetail, status_code=201)
def create_macro(body: MacroCreate, db: Session = Depends(get_db)) -> MacroDetail:  # noqa: B008
    """Persist a new macro and return it with its generated ``id``."""
    _assert_name_available(body.name, db)

    macro = Macro(
        name=body.name,
        description=body.description,
        steps=[s.model_dump() for s in body.steps],
    )
    db.add(macro)
    db.commit()
    db.refresh(macro)
    logger.info("Macro '%s' created (%s)", macro.name, macro.id)
    return _to_detail(macro)


@router.get("/macros", response_model=list[MacroSummary])
def list_macros(db: Session = Depends(get_db)) -> list[MacroSummary]:  # noqa: B008
    """Return all macros ordered by creation date (newest first).

    Steps are **not** included in the list response to keep payloads small;
    fetch a single macro via ``GET /api/macros/{id}`` to get the full definition.
    """
    macros = db.exec(select(Macro).order_by(col(Macro.created_at).desc())).all()
    return [_to_summary(m) for m in macros]


@router.get("/macros/{macro_id}", response_model=MacroDetail)
def get_macro(macro_id: uuid.UUID, db: Session = Depends(get_db)) -> MacroDetail:  # noqa: B008
    """Return a single macro including its full ``steps`` list."""
    macro = db.get(Macro, macro_id)
    if macro is None:
        raise HTTPException(status_code=404, detail="Macro not found")
    return _to_detail(macro)


@router.put("/macros/{macro_id}", response_model=MacroDetail)
def update_macro(macro_id: uuid.UUID, body: MacroUpdate, db: Session = Depends(get_db)) -> MacroDetail:  # noqa: B008
    """Partially update a macro.  Only supplied fields are changed."""
    macro = db.get(Macro, macro_id)
    if macro is None:
        raise HTTPException(status_code=404, detail="Macro not found")

    if body.name is not None and body.name != macro.name:
        _assert_name_available(body.name, db, exclude_id=macro_id)
        macro.name = body.name

    if body.description is not None:
        macro.description = body.description

    if body.steps is not None:
        macro.steps = [s.model_dump() for s in body.steps]

    macro.updated_at = datetime.now(UTC)
    db.add(macro)
    db.commit()
    db.refresh(macro)
    logger.info("Macro '%s' updated (%s)", macro.name, macro.id)
    return _to_detail(macro)


@router.delete("/macros/{macro_id}", status_code=204)
def delete_macro(macro_id: uuid.UUID, db: Session = Depends(get_db)) -> None:  # noqa: B008
    """Permanently delete a macro.  Returns 204 No Content on success."""
    macro = db.get(Macro, macro_id)
    if macro is None:
        raise HTTPException(status_code=404, detail="Macro not found")
    db.delete(macro)
    db.commit()
    logger.info("Macro deleted (%s)", macro_id)
