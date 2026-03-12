from collections.abc import Generator

from sqlalchemy import Engine
from sqlmodel import Session, create_engine

from app.config import get_settings

engine = create_engine(get_settings().database_url, pool_pre_ping=True)


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


def get_engine() -> Engine:
    """FastAPI dependency — returns the shared SQLAlchemy engine.

    Exposed as a dependency (rather than a direct import) so that tests can
    override it via ``app.dependency_overrides[get_engine]`` and inject an
    in-memory SQLite engine for the batch background task.
    """
    return engine

