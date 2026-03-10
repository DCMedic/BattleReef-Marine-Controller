from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.telemetry import router as telemetry_router
from app.config import get_settings
from app.db.models.telemetry import TelemetryReading  # noqa: F401
from app.services.mqtt_listener import start_mqtt_listener

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.app_debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(telemetry_router, prefix=settings.api_prefix)


@app.on_event("startup")
def startup_event() -> None:
    start_mqtt_listener()


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "environment": settings.app_env,
        "docs": "/docs",
        "api_prefix": settings.api_prefix,
    }