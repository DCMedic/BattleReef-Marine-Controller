from __future__ import annotations

import logging
from typing import Iterable

from fastapi.testclient import TestClient

logger = logging.getLogger("battlereef.api.selftest")


def run_api_self_test(app) -> None:
    """
    Perform a lightweight self-test against critical API endpoints.
    Failures are logged but do not crash the service.
    """

    endpoints: Iterable[str] = [
        "/api/v1/health",
        "/api/v1/system/summary",
        "/api/v1/telemetry/history",
        "/api/v1/commands?limit=1",
        "/api/v1/schedules?limit=1",
    ]

    client = TestClient(app)

    logger.info("Running BattleReef API self-test...")

    for path in endpoints:
        try:
            response = client.get(path)

            if response.status_code != 200:
                logger.error(
                    "API SELFTEST FAILED: %s returned %s",
                    path,
                    response.status_code,
                )
            else:
                logger.info(
                    "API OK: %s",
                    path,
                )

        except Exception as exc:
            logger.exception(
                "API SELFTEST ERROR: %s raised exception %s",
                path,
                exc,
            )

    logger.info("BattleReef API self-test complete.")