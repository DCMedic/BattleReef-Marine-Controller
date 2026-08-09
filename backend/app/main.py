from __future__ import annotations

import threading
import time

from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.authz import require_role
from app.api.routes import (
    alerts,
    audit,
    auth,
    commands,
    device_health,
    devices,
    device_states,
    health,
    nodes,
    schedules,
    stream,
    system,
    tanks,
    telemetry,
    thresholds,
)
from app.config import get_settings
from app.core.api_self_test import run_api_self_test
from app.db.schema import ensure_database_schema
from app.db.session import SessionLocal
from app.services.auth_service import AuthService
from app.services.command_dispatcher import start_command_dispatcher
from app.services.device_health_service import DeviceHealthService
from app.services.mqtt_listener import start_mqtt_listener
from app.services.safety_watchdog import SafetyWatchdogService
from app.services.schedule_engine import ScheduleEngine

settings = get_settings()


def start_schedule_loop() -> None:
    def loop() -> None:
        while True:
            db = SessionLocal()
            try:
                result = ScheduleEngine(db).evaluate()
                print("SCHEDULE ENGINE:", result)
            except Exception as exc:
                db.rollback()
                print(f"[SCHEDULE] Evaluation error: {exc}")
            finally:
                db.close()
            time.sleep(30)
    threading.Thread(target=loop, name="schedule-engine", daemon=True).start()


def start_safety_watchdog_loop() -> None:
    def loop() -> None:
        while True:
            db = SessionLocal()
            try:
                result = SafetyWatchdogService(db).evaluate()
                print("SAFETY WATCHDOG:", result)
            except Exception as exc:
                db.rollback()
                print(f"[WATCHDOG] Evaluation error: {exc}")
            finally:
                db.close()
            time.sleep(15)
    threading.Thread(target=loop, name="safety-watchdog", daemon=True).start()


def start_device_health_loop() -> None:
    def loop() -> None:
        while True:
            db = SessionLocal()
            try:
                records = DeviceHealthService(db).evaluate_all()
                print(f"DEVICE HEALTH: evaluated={len(records)}")
            except Exception as exc:
                db.rollback()
                print(f"[DEVICE HEALTH] Evaluation error: {exc}")
            finally:
                db.close()
            time.sleep(30)
    threading.Thread(target=loop, name="device-health", daemon=True).start()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.3.0",
        description="Backend API for BattleReef monitoring, automation, authenticated control, and device health.",
        debug=settings.app_debug,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", tags=["system"])
    def root() -> dict[str, str]:
        return {"name": settings.app_name, "status": "online"}

    public_v1 = APIRouter(prefix=settings.api_prefix)
    public_v1.include_router(health.router)
    public_v1.include_router(auth.router)
    app.include_router(public_v1)

    protected_v1 = APIRouter(prefix=settings.api_prefix, dependencies=[Depends(require_role("viewer"))])
    protected_v1.include_router(system.router)
    protected_v1.include_router(alerts.router)
    protected_v1.include_router(audit.router)
    protected_v1.include_router(commands.router)
    protected_v1.include_router(device_health.router)
    protected_v1.include_router(device_states.router)
    protected_v1.include_router(nodes.router)
    protected_v1.include_router(schedules.router)
    protected_v1.include_router(stream.router)
    protected_v1.include_router(tanks.router)
    protected_v1.include_router(telemetry.router)
    protected_v1.include_router(devices.router)
    protected_v1.include_router(thresholds.router)
    app.include_router(protected_v1)

    @app.on_event("startup")
    def run_startup_checks() -> None:
        AuthService.validate_security_config()
        ensure_database_schema()
        db = SessionLocal()
        try:
            AuthService(db).ensure_bootstrap_admin()
        finally:
            db.close()
        run_api_self_test(app)
        start_mqtt_listener()
        start_schedule_loop()
        start_command_dispatcher()
        start_safety_watchdog_loop()
        start_device_health_loop()

    return app


app = create_app()
