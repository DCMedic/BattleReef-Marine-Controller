from __future__ import annotations

from sqlalchemy import text

# Import model modules so SQLAlchemy metadata is complete before create_all.
import app.db.models  # noqa: F401
from app.db.session import Base, engine


def ensure_database_schema() -> None:
    """Create and evolve application schema without destructive resets.

    Timescale-specific telemetry setup remains owned by ops/postgres/init.sql.
    The explicit ALTER statements below are idempotent migrations for columns
    that SQLAlchemy create_all cannot add to existing tables.
    """
    Base.metadata.create_all(bind=engine)

    with engine.begin() as connection:
        # Command Lifecycle v2 migration for existing BattleReef volumes.
        connection.execute(text("ALTER TABLE commands ADD COLUMN IF NOT EXISTS correlation_id VARCHAR(36)"))
        connection.execute(
            text(
                "UPDATE commands SET correlation_id = 'cmd-' || md5(id::text || requested_at::text) "
                "WHERE correlation_id IS NULL"
            )
        )
        connection.execute(text("ALTER TABLE commands ALTER COLUMN correlation_id SET NOT NULL"))
        connection.execute(
            text("ALTER TABLE commands ADD COLUMN IF NOT EXISTS delivery_policy VARCHAR(50) NOT NULL DEFAULT 'best_effort'")
        )
        connection.execute(
            text("ALTER TABLE commands ADD COLUMN IF NOT EXISTS dispatch_attempts INTEGER NOT NULL DEFAULT 0")
        )
        connection.execute(
            text("ALTER TABLE commands ADD COLUMN IF NOT EXISTS max_attempts INTEGER NOT NULL DEFAULT 2")
        )
        connection.execute(text("ALTER TABLE commands ADD COLUMN IF NOT EXISTS last_dispatched_at TIMESTAMPTZ"))
        connection.execute(text("ALTER TABLE commands ADD COLUMN IF NOT EXISTS ack_deadline TIMESTAMPTZ"))
        connection.execute(text("ALTER TABLE commands ADD COLUMN IF NOT EXISTS verified_at TIMESTAMPTZ"))
        connection.execute(
            text("CREATE UNIQUE INDEX IF NOT EXISTS idx_commands_correlation_id ON commands (correlation_id)")
        )
        connection.execute(
            text("CREATE INDEX IF NOT EXISTS idx_commands_ack_deadline ON commands (ack_deadline)")
        )
        connection.execute(
            text("CREATE INDEX IF NOT EXISTS idx_commands_delivery_policy ON commands (delivery_policy)")
        )

        # Scheduler indexes for existing volumes.
        connection.execute(
            text("CREATE INDEX IF NOT EXISTS idx_schedules_device_key ON schedules (device_key)")
        )
        connection.execute(
            text("CREATE INDEX IF NOT EXISTS idx_schedules_enabled ON schedules (enabled)")
        )
