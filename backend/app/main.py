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
)
from app.core.api_self_test import run_api_self_test
from app.db.session import SessionLocal
from app.mqtt.mqtt_listener import start_mqtt_listener
from app.services.command_dispatcher import start_command_dispatcher
from app.services.safety_watchdog import SafetyWatchdogService
from app.services.schedule_engine import ScheduleEngine


def start_schedule_loop() -> None:
    def loop() -> None:
        while True:
            db = SessionLocal()
            try:
                engine = ScheduleEngine(db)
                result = engine.evaluate()
                print("SCHEDULE ENGINE:", result)
            finally:
                db.close()

            time.sleep(30)

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()


def start_safety_watchdog_loop() -> None:
    def loop() -> None:
        while True:
            db = SessionLocal()
            try:
                watchdog = SafetyWatchdogService(db)
                result = watchdog.evaluate()
                print("SAFETY WATCHDOG:", result)
            finally:
                db.close()

            time.sleep(15)

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()


def create_app() -> FastAPI:
    app = FastAPI(
        title="BattleReef Marine Controller API",
        version="0.1.0",
        description="Backend API for BattleReef aquarium monitoring, automation, and device control.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", tags=["system"])
    def root() -> dict[str, str]:
        return {
            "name": "BattleReef Marine Controller API",
            "status": "online",
        }

    api_v1 = APIRouter(prefix="/api/v1")

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

    app.include_router(api_v1)

    @app.on_event("startup")
    def run_startup_checks() -> None:
        run_api_self_test(app)
        start_mqtt_listener()
        start_schedule_loop()
        start_command_dispatcher()
        start_safety_watchdog_loop()

    return app


app = create_app()