# BattleReef Marine Controller

BattleReef Marine Controller is a secure, event-driven cyber-physical platform for marine aquarium monitoring, automation, and device control. The current stack combines a FastAPI/SQLAlchemy backend, TimescaleDB/PostgreSQL telemetry storage, MQTT command and telemetry transport, and a React/Vite operator interface.

## Control flow

The normal remote-control lifecycle is intentionally single-path:

1. Telemetry is published to MQTT.
2. The backend MQTT listener validates and persists the reading.
3. Rules, schedules, and the safety watchdog may create a queued command.
4. The command dispatcher publishes the queued command to the target device over MQTT and marks it `dispatched`.
5. The device executes the command and publishes an ACK containing its resulting state.
6. The backend ACK listener marks the command `completed` and updates the authoritative device state.

Publishing a command is not treated as successful actuation. Completion requires the device ACK.

## Telemetry contract

Telemetry values are currently numeric throughout the API and database (`value_double`). Timestamps are normalized to UTC. Leak probes use the same numeric telemetry contract:

- `0.0` = dry
- `1.0` = wet

Unknown/non-dry leak values are treated fail-safe by the watchdog as an alert condition.

## Local development

Copy the example environment file and start the Compose stack:

```bash
cp .env.example .env
docker compose up --build
```

The backend is available on port 8000 and the PostgreSQL and MQTT services use their standard development ports defined in `docker-compose.yml`.

For backend-only development:

```bash
cd backend
python -m venv .venv
# Activate .venv for your platform
python -m pip install --upgrade pip
pip install -e ".[dev]"
pytest
```

For the frontend:

```bash
cd frontend
cp .env.example .env
npm ci
npm run dev
```

## Database bootstrap

`ops/postgres/init.sql` owns TimescaleDB-specific telemetry initialization. The backend also runs an idempotent SQLAlchemy schema bootstrap at startup so ordinary application tables, such as `schedules`, are created on existing database volumes without destructive resets.

## Continuous integration

GitHub Actions validates every pull request to `main` with four gates:

- repository hygiene (no tracked `.env`, `node_modules`, `__pycache__`, or `.pyc` files)
- backend compilation and pytest regression tests
- frontend production build
- Docker Compose configuration validation

## Safety principles

BattleReef treats automation as a cyber-physical safety system. Safety-critical commands use explicit command types and payloads, repetitive automation commands are deduplicated, background safety/schedule loops recover from transient evaluation errors, and device-reported ACK state is authoritative for remote command completion.
