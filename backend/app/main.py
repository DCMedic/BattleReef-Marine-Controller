from __future__ import annotations

from fastapi import FastAPI
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

    app.include_router(health.router)
    app.include_router(system.router)
    app.include_router(alerts.router)
    app.include_router(commands.router)
    app.include_router(device_states.router)
    app.include_router(nodes.router)
    app.include_router(schedules.router)
    app.include_router(stream.router)
    app.include_router(tanks.router)
    app.include_router(telemetry.router)

    # Existing repo already has a devices route file here.
    # This is the correct place to expose the new direct device-control endpoints.
    app.include_router(devices.router)

    return app


app = create_app()