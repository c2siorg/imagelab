import logging

from fastapi import APIRouter, HTTPException

from app.models.pipeline import PipelineRequest, PipelineResponse, StepInspectResponse
from app.services.pipeline_executor import execute_pipeline, inspect_step

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.post("/v1/pipeline/executions", response_model=PipelineResponse)
def create_execution(request: PipelineRequest):
    """Execute an image processing pipeline.

    This endpoint performs CPU-bound OpenCV processing (image decoding,
    operator execution, and re-encoding). It intentionally uses ``def``
    instead of ``async def`` so that FastAPI runs it in a threadpool,
    preventing the asyncio event loop from being blocked.

    See: https://fastapi.tiangolo.com/async/
    """
    # Intentionally `def`, not `async def`: execute_pipeline() is synchronous
    # and CPU-bound. FastAPI dispatches plain `def` handlers to a threadpool
    # via anyio.to_thread.run_sync(), keeping the event loop responsive.
    # Do NOT convert to `async def` unless execute_pipeline() becomes fully
    # asynchronous.
    try:
        return execute_pipeline(request)
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
