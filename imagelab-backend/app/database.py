from collections.abc import Generator

from sqlmodel import Session, create_engine

from app.config import get_settings

_db_url = get_settings().database_url

# SQLite needs check_same_thread=False when used with FastAPI's threadpool.
_connect_args = {"check_same_thread": False} if _db_url.startswith("sqlite") else {}

engine = create_engine(_db_url, pool_pre_ping=True, connect_args=_connect_args)


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
