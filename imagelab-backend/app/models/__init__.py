# Import all table modules here so Alembic can detect them via SQLModel.metadata.
# alembic/env.py does: from app import models  — this file is the entry-point.
from app.models import batch, macro  # noqa: F401
