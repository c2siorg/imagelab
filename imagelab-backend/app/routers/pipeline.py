import logging

from fastapi import APIRouter, HTTPException

from app.models.pipeline import PipelineRequest, PipelineResponse
from app.services.pipeline_executor import execute_pipeline

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.post("/pipeline/execute", response_model=PipelineResponse)
def execute(request: PipelineRequest):
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
