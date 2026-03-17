from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter


router = APIRouter(prefix="/api/v1/nodes", tags=["nodes"])


@router.get("", summary="List controller nodes")
def list_nodes() -> dict[str, object]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "items": [
            {
                "node_key": "primary_controller",
                "name": "Primary Controller",
                "status": "online",
                "role": "core",
            }
        ],
        "count": 1,
    }


@router.get("/health", summary="Get node subsystem health")
def nodes_health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "nodes",
    }