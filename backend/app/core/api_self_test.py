from __future__ import annotations

import logging
from typing import Iterable

from fastapi import FastAPI


logger = logging.getLogger("battlereef.api.selftest")


def run_api_self_test(app: FastAPI) -> None:
    """
    Lightweight startup self-test that validates critical routes are registered.

    This avoids using FastAPI/Starlette TestClient in runtime code, which would
    incorrectly require test-only dependencies such as httpx inside production
    containers.
    """

    expected_paths: Iterable[str] = [
        "/",
        "/api/v1/health",
        "/api/v1/health/ready",
        "/api/v1/system/summary",
        "/api/v1/system/health",
        "/api/v1/telemetry/history",
        "/api/v1/commands",
        "/api/v1/schedules",
        "/api/v1/alerts",
        "/api/v1/device-states/{device_key}",
        "/api/v1/devices",
    ]

    registered_paths = {route.path for route in app.routes}

    logger.info("Running BattleReef API self-test...")

    missing_paths: list[str] = []

    for path in expected_paths:
        if path in registered_paths:
            logger.info("API ROUTE OK: %s", path)
        else:
            logger.error("API ROUTE MISSING: %s", path)
            missing_paths.append(path)

    if missing_paths:
        logger.error(
            "BattleReef API self-test completed with missing routes: %s",
            ", ".join(missing_paths),
        )
    else:
        logger.info("BattleReef API self-test complete. All critical routes are registered.")