from __future__ import annotations

from fastapi import FastAPI, APIRouter
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

    # Centralized API version router
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

    return app


app = create_app()