import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from app.models.pipeline import PipelineExportRequest, PipelineRequest, PipelineResponse
from app.services.pipeline_executor import execute_pipeline
from app.services.pipeline_python_exporter import export_pipeline_to_python

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


@router.post("/pipeline/export/python", response_class=PlainTextResponse)
def export_python(request: PipelineExportRequest):
    """Export a pipeline as a runnable Python script."""
    try:
        return export_pipeline_to_python(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        logger.exception("Unexpected error during pipeline export")
        raise HTTPException(status_code=500, detail="Internal pipeline export error") from None
