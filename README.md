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

The operator API uses Argon2 password hashing and short-lived HS256 bearer tokens. Tokens are bound to username, role, principal type, issuer/audience, and a database token version. Changing a principal's password, role, or active state increments that version and invalidates previously issued tokens. Browser tokens are stored only in `sessionStorage`, so closing the browser session removes them rather than leaving long-lived credentials in persistent local storage.

Repeated bad credentials trigger a temporary database-backed account lockout. Unknown usernames still execute an Argon2 verification against a dummy hash to reduce username-enumeration timing differences.

Health and login routes remain public. Operational API routes require authentication. The role hierarchy is:

- `viewer`: read telemetry, system state, alerts, audit history, schedules, thresholds, and device status.
- `operator`: viewer permissions plus routine queued commands, direct device commands, and alert clearing.
- `engineer`: operator permissions plus schedule/threshold configuration, device mode changes, and manual automation evaluation.
- `administrator`: engineer permissions plus principal/account management and infrastructure-level maintenance operations.

Accounts can be typed as `user` or `service`. The same RBAC, lockout, auditing, and token-revocation controls apply to both. Administrator account management is available through `/api/v1/auth/users` and through the administrator-only Security panel in the operator console.

The development `.env.example` contains bootstrap credentials solely to make a local stack usable. Replace both the bootstrap password and JWT secret before any non-local deployment. Outside development/test, BattleReef refuses to start with the known development JWT secret. Bootstrap administrator credentials are required only until an active administrator exists in the database; after first provisioning, the bootstrap password can and should be removed from the deployment environment.

## MQTT identity and authorization

MQTT listens on TLS port `8883` and requires an X.509 client certificate. Mosquitto uses the client certificate common name (CN) as the MQTT username/identity. Anonymous MQTT access is disabled.

The backend certificate CN is `battlereef-backend` and is authorized to read telemetry/ACKs and publish commands. Production device/node certificates should use the exact device or node key as their CN. Broker ACL patterns then restrict them to:

- `battlereef/cmd/<identity>/set` for device command subscriptions
- `battlereef/ack/<identity>` for device ACK publishing
- `battlereef/telemetry/<identity>/#` for sensor-node telemetry publishing

The development `device-simulator` certificate is intentionally broader because one simulator emulates multiple virtual devices. Never deploy that aggregate identity to production hardware.

## Audit trail

Security, command, and operator events are persisted in PostgreSQL as an append-only, SHA-256 hash-chained audit journal. Historical audit events have read and integrity-verification APIs but no update/delete API. Authenticated human/service identities are used as audit actors for privileged HTTP actions.

## Telemetry contract

Telemetry values are numeric throughout the API and database (`value_double`). Timestamps are normalized to UTC. Leak probes use the same numeric telemetry contract:

- `0.0` = dry
- `1.0` = wet

Unknown/non-dry leak values are treated fail-safe by the watchdog as an alert condition.

## Local development

Generate a development-only MQTT PKI before starting Compose:

```bash
cp .env.example .env
bash ops/mosquitto/generate-dev-pki.sh
docker compose up --build
```

The PKI generator creates a local CA, broker certificate, and separate backend/simulator client certificates under `ops/mosquitto/certs/`. That directory is ignored by Git. Never commit private keys and never reuse the development CA for production deployments.

The backend is available on port 8000. MQTT is exposed only on authenticated TLS port 8883. The operator console presents a login screen, sends bearer credentials on API requests and the live event stream, and automatically returns to login when a session expires or is revoked.

For backend-only development without starting MQTT, explicitly disable MQTT TLS in the test environment or provide the expected certificate files:

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

Production deployments should use a dedicated BattleReef device CA or an enterprise PKI, not the development generator. Each hardware node should receive its own private key and certificate with a CN equal to its BattleReef node/device key. Private keys should be generated on-device when practical, stored with OS/hardware-backed protections, and independently revocable. Broker and client certificates should be rotated before expiry.

## Database bootstrap

`ops/postgres/init.sql` owns TimescaleDB-specific telemetry initialization. The backend also runs an idempotent SQLAlchemy schema bootstrap at startup so application schema evolution can occur without destructive database-volume resets.

## Continuous integration

GitHub Actions validates every pull request to `main` with repository hygiene, backend tests, frontend build/security audit, Compose validation, and an MQTT security integration gate. Backend regression tests also validate password hashing, JWT identity claims, token-version binding, RBAC role ordering, brute-force lockout behavior, and authorization denial semantics.

## Safety principles

BattleReef treats automation as a cyber-physical safety system. Safety-critical commands use explicit delivery policies, repetitive automation commands are deduplicated, background safety/schedule loops recover from transient errors, remote commands require authenticated ACKs, device-reported state must match the requested physical state before completion, and privileged HTTP actions require an authenticated principal with the appropriate role.
