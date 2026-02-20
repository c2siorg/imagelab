from fastapi import APIRouter

from app.models.pipeline import PipelineRequest, PipelineResponse
from app.services.pipeline_executor import execute_pipeline

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.post("/pipeline/execute", response_model=PipelineResponse)
async def execute(request: PipelineRequest):
    return execute_pipeline(request)
