# BattleReef Marine Controller

BattleReef Marine Controller is a secure, event-driven cyber-physical platform for marine aquarium monitoring, automation, and device control. The current stack combines a FastAPI/SQLAlchemy backend, TimescaleDB/PostgreSQL telemetry storage, mutually authenticated MQTT transport, an authenticated HTTP control plane, and a React/Vite operator interface.

## Control flow

The normal remote-control lifecycle is intentionally single-path:

1. An authenticated node publishes telemetry over MQTT/TLS.
2. Mosquitto authorizes the certificate identity against the topic ACL.
3. The backend verifies topic/payload identity, evaluates telemetry plausibility, and persists the reading.
4. Implausible readings are retained for forensics as `quality=suspect` but are excluded from trusted automation.
5. Rules, schedules, and the safety watchdog may create a queued command using only recent trusted telemetry where sensor evidence is involved.
6. The command dispatcher publishes the queued command to the target device and marks it `dispatched`.
7. The authenticated device executes the command and publishes an ACK containing its correlation ID and resulting state.
8. The backend verifies device identity, command correlation, and reported state before marking the command completed.
9. Independent physical evidence such as return flow or a dedicated heater power channel can then challenge the device's self-reported state.

Publishing a command is not treated as successful actuation. An ACK proves what a device reports; independent physical verification provides a separate evidence layer for what the system appears to be doing physically.

## HTTP authentication and RBAC

The operator API uses Argon2 password hashing and short-lived HS256 bearer tokens. Tokens are bound to username, role, principal type, issuer/audience, and a database token version. Password, role, or activation changes invalidate previously issued sessions. Browser tokens are stored only in `sessionStorage`.

Repeated bad credentials trigger a temporary database-backed lockout. The role hierarchy is `viewer`, `operator`, `engineer`, and `administrator`, with both human `user` and non-interactive `service` principals supported.

## MQTT identity and authorization

MQTT listens on TLS port `8883` and requires an X.509 client certificate. Mosquitto uses certificate CN as MQTT identity, anonymous access is disabled, and broker ACLs restrict nodes/devices to their own telemetry, ACK, and command namespaces.

## Audit trail

Security, command, operator, device-health, telemetry-quarantine, and independent physical-verification transitions are persisted in PostgreSQL as an append-only SHA-256 hash-chained journal. Historical audit events have read/integrity APIs but no update/delete API.

## Telemetry plausibility and quarantine

Before a new reading is trusted, BattleReef evaluates conservative physical bounds and selected rate-of-change/correlation rules. Current examples include temperature, pH, salinity, sump level, dissolved oxygen, ORP, flow, and power channels. Large salinity changes are additionally checked against recent sump-level movement from the same authenticated telemetry source.

A failed plausibility check does not delete data. The reading is persisted as `quality=suspect`, a runtime alert is raised, and a durable audit event records the quarantine reason. Automation reads use only `quality=good` telemetry. Temperature automation also rejects trusted readings older than 120 seconds, preventing fallback to stale-but-valid data after a sensor begins producing implausible samples.

The safety watchdog follows the same trust model. Critical temperature/sump actions and threshold evaluation require recent trusted data. Leak probes remain deliberately fail-safe: only a trusted `0.0` reading is accepted as dry.

## Independent physical-state verification

A background verifier runs every 15 seconds and compares fresh device-reported state against fresh independent telemetry. Current rules include:

- Return pump state vs. `flow_return_main`: a pump reporting ON with very low flow, or OFF while substantial return flow continues, is a critical contradiction.
- Heater relay state vs. `power_heater_main`: a dedicated heater circuit power sensor can prove whether the heater is physically drawing power. Aggregate `power_monitor_main` is intentionally not used for this critical assertion because other loads could create false positives.

Independent evidence older than 120 seconds is not used to verify state; the result becomes `unknown`. A critical contradiction raises a runtime alert, creates a tamper-evident audit event, and imposes a large device-health penalty. Recovery clears the physical-verification alert and is also audited.

Engineers can manually invoke the verifier at `POST /api/v1/physical-verification/evaluate` in addition to the periodic background evaluation.

## Device health monitoring

BattleReef evaluates device/node health every 30 seconds and persists the latest score in `device_health`. Health uses telemetry/state freshness, telemetry quality, command failures/timeouts, ACK state mismatches, average ACK latency, and active independent physical-verification failures.

Health states are `healthy`, `degraded`, `critical`, and `unknown`. Degraded/critical states create runtime alerts; transitions are written to the audit journal. Authenticated viewers can read `/api/v1/device-health`, while engineers can manually request evaluation at `/api/v1/device-health/evaluate`.

## Development fault injection

`tools/simulator/device_fault_injector.py` exercises the real mTLS command/ACK path with `normal`, `drop_ack`, `delayed_ack`, `wrong_state`, and `explicit_failure` behaviors.

`tools/simulator/physical_fault_injector.py` exercises the telemetry/plausibility/physical-verification path using development-only mTLS credentials. Scenarios include:

```bash
python tools/simulator/physical_fault_injector.py salinity_spike
python tools/simulator/physical_fault_injector.py return_flow_zero
python tools/simulator/physical_fault_injector.py heater_power_present
```

The fault injectors are external development tools. No production HTTP endpoint can enable them. Never deploy the aggregate development simulator certificates to production hardware.

## Telemetry contract

Telemetry values are numeric throughout the API/database (`value_double`) and timestamps are normalized to UTC. Leak probes use `0.0 = dry` and `1.0 = wet`. Unknown, suspect, or non-dry leak evidence is treated fail-safe.

`power_heater_main` is reserved for an independent heater circuit power measurement. `power_monitor_main` remains aggregate system power and is not considered strong enough evidence by itself to declare a stuck heater relay.

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

GitHub Actions validates pull requests to `main` with repository hygiene, backend regression tests, frontend build/security audit, Compose validation, and a live MQTT mTLS security integration gate. Plausibility boundaries, fail-safe leak semantics, and independent binary physical-signal verification are regression tested.

## Safety principles

BattleReef treats automation as a cyber-physical safety system. Safety-critical commands use explicit delivery policies, automation commands are deduplicated, safety/schedule/health/physical-verification loops recover from transient errors, remote commands require authenticated ACKs, independent evidence can contradict device self-reports, implausible telemetry is quarantined rather than trusted, and privileged HTTP actions require an authenticated principal with the appropriate role.
