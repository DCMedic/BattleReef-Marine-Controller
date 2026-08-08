from __future__ import annotations

import threading
import time

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    alerts,
    commands,
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
from app.services.command_dispatcher import start_command_dispatcher
from app.services.mqtt_listener import start_mqtt_listener
from app.services.safety_watchdog import SafetyWatchdogService
from app.services.schedule_engine import ScheduleEngine

settings = get_settings()


def start_schedule_loop() -> None:
    def loop() -> None:
        while True:
            db = SessionLocal()
            try:
                engine = ScheduleEngine(db)
                result = engine.evaluate()
                print("SCHEDULE ENGINE:", result)
            except Exception as exc:
                db.rollback()
                print(f"[SCHEDULE] Evaluation error: {exc}")
            finally:
                db.close()

            time.sleep(30)

    thread = threading.Thread(target=loop, name="schedule-engine", daemon=True)
    thread.start()


def start_safety_watchdog_loop() -> None:
    def loop() -> None:
        while True:
            db = SessionLocal()
            try:
                watchdog = SafetyWatchdogService(db)
                result = watchdog.evaluate()
                print("SAFETY WATCHDOG:", result)
            except Exception as exc:
                db.rollback()
                print(f"[WATCHDOG] Evaluation error: {exc}")
            finally:
                db.close()

            time.sleep(15)

    thread = threading.Thread(target=loop, name="safety-watchdog", daemon=True)
    thread.start()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Backend API for BattleReef aquarium monitoring, automation, and device control.",
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
        return {
            "name": settings.app_name,
            "status": "online",
        }

    api_v1 = APIRouter(prefix=settings.api_prefix)

    api_v1.include_router(health.router)
    api_v1.include_router(system.router)
    api_v1.include_router(alerts.router)
    api_v1.include_router(commands.router)
    api_v1.include_router(device_states.router)
    api_v1.include_router(nodes.router)
    api_v1.include_router(schedules.router)
    api_v1.include_router(stream.router)
    api_v1.include_router(tanks.router)
    api_v1.include_router(telemetry.router)
    api_v1.include_router(devices.router)
    api_v1.include_router(thresholds.router)

    app.include_router(api_v1)

    @app.on_event("startup")
    def run_startup_checks() -> None:
        ensure_database_schema()
        run_api_self_test(app)
        start_mqtt_listener()
        start_schedule_loop()
        start_command_dispatcher()
        start_safety_watchdog_loop()

    return app


app = create_app()
