import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlmodel import Session

from app.database import get_db
from app.exceptions import PipelineExecutionError
from app.models.pipeline import PipelineRequest, PipelineResponse, StepInspectResponse
from app.services.graph_engine import compile_graph
from app.services.pipeline_executor import execute_pipeline, inspect_step
from app.utils.image import decode_base64_image

logger = logging.getLogger(__name__)

router = APIRouter()
SessionDep = Annotated[Session, Depends(get_db)]


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.post("/v1/pipeline/executions", response_model=PipelineResponse)
def create_execution(request: PipelineRequest, session: SessionDep):
    """Execute an image processing pipeline.

    This endpoint performs CPU-bound OpenCV processing (image decoding,
    operator execution, and re-encoding). It intentionally uses ``def``
    instead of ``async def`` so that FastAPI runs it in a threadpool,
    preventing the asyncio event loop from being blocked.

    See: https://fastapi.tiangolo.com/async/
    """
    try:
        if request.graph is not None:
            image = decode_base64_image(request.image)
            input_channels = 1 if image.ndim == 2 else image.shape[2]
            request.pipeline = compile_graph(request.graph, session, input_channels)
        response = execute_pipeline(request)
        if not response.success:
            return JSONResponse(
                status_code=200,
                content=response.model_dump(),
            )
        return response
    except PipelineExecutionError as e:
        logger.error(f"Pipeline execution error: {e}")
        return JSONResponse(
            status_code=200,
            content={
                "success": False,
                "execution_id": "",
                "error": e.user_friendly_message,
                "step": 0,
                "error_block_id": e.step_id,
                "timings": {"total_ms": 0, "steps": []},
                "step_results": [],
            },
        )
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "execution_id": "",
                "error": str(e),
                "step": 0,
                "timings": {"total_ms": 0, "steps": []},
                "step_results": [],
            },
        )
    except Exception:
        logger.exception("Unexpected error during pipeline execution")
        raise HTTPException(status_code=500, detail="Internal pipeline error") from None


@router.get("/v1/pipeline/executions/{execution_id}/steps/inspect", response_model=StepInspectResponse)
def inspect_execution_step(execution_id: str, block_id: str):
    """Return the full-resolution image and analysis for a cached step."""
    result = inspect_step(execution_id, block_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Step result not found or expired")
    return StepInspectResponse(success=True, **result)
