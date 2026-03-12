import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_db
from app.models.saved_pipeline import (
    SavedPipeline,
    SavedPipelineResponse,
    SavedPipelineSummary,
    SavePipelineRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pipelines", tags=["pipelines"])


def _to_response(p: SavedPipeline) -> SavedPipelineResponse:
    return SavedPipelineResponse.model_validate(p)


@router.post("", response_model=SavedPipelineResponse, status_code=201)
def save_pipeline(request: SavePipelineRequest, db: Session = Depends(get_db)) -> SavedPipelineResponse:  # noqa: B008
    """Persist a pipeline and return its record (including share token)."""
    pipeline = SavedPipeline(
        name=request.name,
        description=request.description,
        pipeline_json=request.pipeline_json,
        workspace_state=request.workspace_state,
    )
    db.add(pipeline)
    db.commit()
    db.refresh(pipeline)
    return _to_response(pipeline)


@router.get("", response_model=list[SavedPipelineSummary])
def list_pipelines(db: Session = Depends(get_db)) -> list[SavedPipelineSummary]:  # noqa: B008
    """Return all saved pipelines (summary only; no pipeline_json payload)."""
    rows = db.exec(select(SavedPipeline).order_by(SavedPipeline.updated_at.desc())).all()  # type: ignore[arg-type]
    return [SavedPipelineSummary.model_validate(p) for p in rows]


@router.get("/share/{token}", response_model=SavedPipelineResponse)
def get_pipeline_by_token(token: str, db: Session = Depends(get_db)) -> SavedPipelineResponse:  # noqa: B008
    """Load a pipeline by its share token (for URL-based sharing)."""
    pipeline = db.exec(select(SavedPipeline).where(SavedPipeline.share_token == token)).first()
    if pipeline is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return _to_response(pipeline)


@router.get("/{pipeline_id}", response_model=SavedPipelineResponse)
def get_pipeline(pipeline_id: int, db: Session = Depends(get_db)) -> SavedPipelineResponse:  # noqa: B008
    """Load a pipeline by ID."""
    pipeline = db.get(SavedPipeline, pipeline_id)
    if pipeline is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return _to_response(pipeline)


@router.put("/{pipeline_id}", response_model=SavedPipelineResponse)
def update_pipeline(
    pipeline_id: int,
    request: SavePipelineRequest,
    db: Session = Depends(get_db),  # noqa: B008
) -> SavedPipelineResponse:
    """Update a saved pipeline's name, description, or steps."""
    pipeline = db.get(SavedPipeline, pipeline_id)
    if pipeline is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    pipeline.name = request.name
    pipeline.description = request.description
    pipeline.pipeline_json = request.pipeline_json
    pipeline.workspace_state = request.workspace_state
    pipeline.updated_at = datetime.now(UTC)
    db.add(pipeline)
    db.commit()
    db.refresh(pipeline)
    return _to_response(pipeline)


@router.delete("/{pipeline_id}", status_code=204)
def delete_pipeline(pipeline_id: int, db: Session = Depends(get_db)) -> None:  # noqa: B008
    """Delete a saved pipeline."""
    pipeline = db.get(SavedPipeline, pipeline_id)
    if pipeline is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    db.delete(pipeline)
    db.commit()
