# BattleReef Marine Controller

BattleReef Marine Controller is a secure, event-driven cyber-physical platform for marine aquarium monitoring, automation, and device control. The current stack combines a FastAPI/SQLAlchemy backend, TimescaleDB/PostgreSQL telemetry storage, mutually authenticated MQTT transport, an authenticated HTTP control plane, and a React/Vite operator interface.

## Control flow

The normal remote-control lifecycle is intentionally single-path:

1. An authenticated node publishes telemetry over MQTT/TLS.
2. Mosquitto authorizes the certificate identity against the topic ACL.
3. The backend verifies that topic identity and payload identity agree, then persists the reading.
4. Rules, schedules, and the safety watchdog may create a queued command.
5. The command dispatcher publishes the queued command to the target device and marks it `dispatched`.
6. The authenticated device executes the command and publishes an ACK containing its correlation ID and resulting state.
7. The backend verifies device identity, command correlation, and resulting physical state before marking the command `completed`.

Publishing a command is not treated as successful actuation. Completion requires an authenticated, state-verifying device ACK.

## HTTP authentication and RBAC

The operator API uses Argon2 password hashing and short-lived HS256 bearer tokens. Tokens are bound to username, role, principal type, issuer/audience, and a database token version. Changing a principal's password, role, or active state increments that version and invalidates previously issued tokens. Browser tokens are stored only in `sessionStorage`.

Repeated bad credentials trigger a temporary database-backed account lockout. Unknown usernames still execute an Argon2 verification against a dummy hash to reduce username-enumeration timing differences.

Health and login routes remain public. Operational API routes require authentication. The role hierarchy is:

- `viewer`: read telemetry, system state, alerts, audit history, schedules, thresholds, and device status.
- `operator`: viewer permissions plus routine queued commands, direct device commands, and alert clearing.
- `engineer`: operator permissions plus schedule/threshold configuration, device mode changes, and manual automation evaluation.
- `administrator`: engineer permissions plus principal/account management and infrastructure-level maintenance operations.

Accounts can be typed as `user` or `service`. The same RBAC, lockout, auditing, and token-revocation controls apply to both.

## MQTT identity and authorization

MQTT listens on TLS port `8883` and requires an X.509 client certificate. Mosquitto uses the client certificate common name (CN) as the MQTT username/identity. Anonymous MQTT access is disabled.

The backend certificate CN is `battlereef-backend`. Production device/node certificates should use the exact device or node key as their CN. Broker ACL patterns restrict them to their own command, ACK, and telemetry namespaces.

## Audit trail

Security, command, operator, and device-health state changes are persisted in PostgreSQL as an append-only, SHA-256 hash-chained audit journal. Historical audit events have read and integrity-verification APIs but no update/delete API.

## Device health monitoring

BattleReef evaluates device/node health every 30 seconds and persists the latest score in `device_health`. Health is derived from evidence already available to the controller rather than a self-reported online flag. The evaluator considers telemetry/state freshness, telemetry quality, command failures/timeouts, physical-state verification mismatches, and average ACK latency.

Health states are `healthy`, `degraded`, `critical`, and `unknown`. Degraded/critical devices create runtime alerts, while health-state transitions are written to the tamper-evident audit journal. Authenticated viewers can read `/api/v1/device-health`; engineers can manually request an evaluation at `/api/v1/device-health/evaluate`.

Repeated physical-state mismatches receive an additional penalty because they may indicate a stuck relay, failed actuator, wiring fault, or a device reporting state inconsistent with the requested physical condition.

## Development fault injection

`tools/simulator/device_fault_injector.py` exercises the real mTLS MQTT command/ACK path without adding any fault-injection API to the production backend. It uses the development-only aggregate `device-simulator` certificate and supports:

- `normal` — valid ACK and matching state
- `drop_ack` — simulates an offline/nonresponsive actuator
- `delayed_ack` — simulates excessive command latency
- `wrong_state` — simulates a stuck/incorrect physical state
- `explicit_failure` — simulates an actuator reporting failure

Example after generating the development PKI:

```bash
FAULT_DEVICE=heater_main FAULT_MODE=wrong_state python tools/simulator/device_fault_injector.py
```

Never deploy the fault injector or its aggregate development certificate to production hardware.

## Telemetry contract

Telemetry values are numeric throughout the API and database (`value_double`). Timestamps are normalized to UTC. Leak probes use `0.0 = dry` and `1.0 = wet`. Unknown/non-dry values are treated fail-safe.

## Local development

```bash
cp .env.example .env
bash ops/mosquitto/generate-dev-pki.sh
docker compose up --build
```

For backend tests:

```bash
cd backend
python -m venv .venv
# Activate .venv for your platform
python -m pip install --upgrade pip
pip install -e ".[dev]"
MQTT_TLS_ENABLED=false pytest
```

For the frontend:

```bash
cd frontend
cp .env.example .env
npm ci
npm run dev
```

## Production certificate provisioning

Production deployments should use a dedicated BattleReef device CA or enterprise PKI. Each hardware node should receive its own private key/certificate and independently revocable identity.

## Database bootstrap

`ops/postgres/init.sql` owns TimescaleDB-specific telemetry initialization. The backend also runs an idempotent SQLAlchemy schema bootstrap at startup so application schema evolution can occur without destructive database-volume resets.

## Continuous integration

GitHub Actions validates every pull request to `main` with repository hygiene, backend tests, frontend build/security audit, Compose validation, and an MQTT security integration gate. Device-health scoring boundaries are regression tested as part of the backend suite.

## Safety principles

BattleReef treats automation as a cyber-physical safety system. Safety-critical commands use explicit delivery policies, repetitive automation commands are deduplicated, background safety/schedule/health loops recover from transient errors, remote commands require authenticated ACKs, device-reported state must match the requested physical state before completion, and privileged HTTP actions require an authenticated principal with the appropriate role.
