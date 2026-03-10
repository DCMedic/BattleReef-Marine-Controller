CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS telemetry_readings (
    id BIGSERIAL PRIMARY KEY,
    sensor_key TEXT NOT NULL,
    source_node TEXT NOT NULL,
    reading_time TIMESTAMPTZ NOT NULL,
    value_double DOUBLE PRECISION NOT NULL,
    unit TEXT NOT NULL,
    quality TEXT NOT NULL DEFAULT 'good',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_telemetry_sensor_time
    ON telemetry_readings (sensor_key, reading_time DESC);

CREATE TABLE IF NOT EXISTS commands (
    id BIGSERIAL PRIMARY KEY,
    requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    requested_by TEXT NOT NULL,
    target_device TEXT NOT NULL,
    command_type TEXT NOT NULL,
    command_payload JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued',
    acknowledged_at TIMESTAMPTZ NULL,
    completed_at TIMESTAMPTZ NULL,
    error_message TEXT NULL
);

CREATE INDEX IF NOT EXISTS idx_commands_requested_at
    ON commands (requested_at DESC);

CREATE INDEX IF NOT EXISTS idx_commands_target_device
    ON commands (target_device);

CREATE INDEX IF NOT EXISTS idx_commands_status
    ON commands (status);