from __future__ import annotations

from sqlalchemy import text

# Import model modules so SQLAlchemy metadata is complete before create_all.
import app.db.models  # noqa: F401
from app.db.session import Base, engine


def ensure_database_schema() -> None:
    """Create missing application tables and indexes without dropping data.

    Timescale-specific telemetry setup remains owned by ops/postgres/init.sql.
    SQLAlchemy create_all is deliberately used only as an idempotent bootstrap
    for ordinary application tables (for example schedules) on existing volumes.
    """
    Base.metadata.create_all(bind=engine)

    # Keep the scheduler lookup efficient even when this table is created on an
    # existing database rather than by the initial Postgres bootstrap script.
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_schedules_device_key "
                "ON schedules (device_key)"
            )
        )
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_schedules_enabled "
                "ON schedules (enabled)"
            )
        )
