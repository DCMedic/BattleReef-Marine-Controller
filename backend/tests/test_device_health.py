from app.services.device_health_service import DeviceHealthService


def test_device_health_classification_thresholds() -> None:
    assert DeviceHealthService.classify(100) == "healthy"
    assert DeviceHealthService.classify(85) == "healthy"
    assert DeviceHealthService.classify(84.9) == "degraded"
    assert DeviceHealthService.classify(60) == "degraded"
    assert DeviceHealthService.classify(59.9) == "critical"
    assert DeviceHealthService.classify(100, has_evidence=False) == "unknown"


def test_freshness_penalties_escalate_with_staleness() -> None:
    assert DeviceHealthService.freshness_penalty(30) == (0.0, None)
    assert DeviceHealthService.freshness_penalty(90)[0] == 15.0
    assert DeviceHealthService.freshness_penalty(180)[0] == 40.0
    assert DeviceHealthService.freshness_penalty(600)[0] == 70.0
    assert DeviceHealthService.freshness_penalty(None)[0] == 80.0
