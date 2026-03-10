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