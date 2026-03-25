from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from app.db.session import SessionLocal, get_db
from app.services.command_service import CommandService
from app.services.device_state_service import DeviceStateService
from app.services.system_service import SystemService


router = APIRouter(prefix="/stream", tags=["stream"])


def build_stream_snapshot(db: Session) -> dict[str, object]:
    system_service = SystemService(db)
    command_service = CommandService(db)
    device_state_service = DeviceStateService(db)

    summary = system_service.get_summary()
    commands = command_service.list_recent(limit=10)
    device_states = device_state_service.list_recent(limit=20)

    return {
        "timestamp": datetime.now(timezone.utc),
        "summary": jsonable_encoder(summary),
        "commands": jsonable_encoder(commands),
        "device_states": jsonable_encoder(device_states),
    }


@router.get("", summary="Get stream service status")
def stream_status() -> dict[str, object]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "service": "telemetry_stream",
        "status": "online",
        "description": "Real-time event streaming service",
    }


@router.get("/health", summary="Stream subsystem health check")
def stream_health() -> dict[str, str]:
    return {
        "service": "stream",
        "status": "ok",
    }


@router.get("/latest", summary="Get latest stream snapshot")
def latest_stream_data(db: Session = Depends(get_db)) -> dict[str, object]:
    return jsonable_encoder(build_stream_snapshot(db))


@router.get("/events", summary="Server-Sent Events stream")
async def stream_events() -> StreamingResponse:
    async def event_generator():
        while True:
            db = SessionLocal()

            try:
                payload = build_stream_snapshot(db)
                yield f"event: battlereef_update\ndata: {json.dumps(jsonable_encoder(payload))}\n\n"
            except Exception as exc:
                error_payload = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "error": str(exc),
                }
                yield f"event: battlereef_error\ndata: {json.dumps(error_payload)}\n\n"
            finally:
                db.close()

            await asyncio.sleep(3)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )