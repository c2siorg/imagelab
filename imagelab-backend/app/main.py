import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.exceptions import register_exception_handlers
from app.routers import pipeline

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app):
    """Application startup/shutdown lifecycle."""
    from alembic import command
    from alembic.config import Config

    cfg = Config("alembic.ini")
    try:
        command.upgrade(cfg, "head")
    except Exception:
        logger.warning(
            "Failed to run database migrations — PostgreSQL may be unavailable. "
            "The app will start without database features.",
            exc_info=True,
        )
    yield


app = FastAPI(title="ImageLab API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(pipeline.router, prefix="/api")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=4100)
