CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS telemetry_readings (
    reading_time TIMESTAMPTZ NOT NULL,
    id BIGSERIAL NOT NULL,
    sensor_key TEXT NOT NULL,
    source_node TEXT NOT NULL,
    value_double DOUBLE PRECISION NOT NULL,
    unit TEXT NOT NULL,
    quality TEXT NOT NULL DEFAULT 'good',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (reading_time, id)
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

CREATE TABLE IF NOT EXISTS device_states (
    id BIGSERIAL PRIMARY KEY,
    device_key TEXT NOT NULL UNIQUE,
    state_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    state_source TEXT NOT NULL DEFAULT 'system',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_device_states_updated_at
    ON device_states (updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_device_states_device_key
    ON device_states (device_key);

DO $$
BEGIN
    PERFORM create_hypertable(
        'telemetry_readings',
        'reading_time',
        if_not_exists => TRUE,
        migrate_data => TRUE
    );
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'create_hypertable skipped: %', SQLERRM;
END
$$;

DO $$
BEGIN
    ALTER TABLE telemetry_readings
        SET (
            timescaledb.compress,
            timescaledb.compress_segmentby = 'sensor_key',
            timescaledb.compress_orderby = 'reading_time DESC'
        );
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'compression settings skipped: %', SQLERRM;
END
$$;

DO $$
BEGIN
    PERFORM add_compression_policy('telemetry_readings', INTERVAL '7 days', if_not_exists => TRUE);
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'compression policy skipped: %', SQLERRM;
END
$$;

DO $$
BEGIN
    PERFORM add_retention_policy('telemetry_readings', INTERVAL '30 days', if_not_exists => TRUE);
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'retention policy skipped: %', SQLERRM;
END
$$;