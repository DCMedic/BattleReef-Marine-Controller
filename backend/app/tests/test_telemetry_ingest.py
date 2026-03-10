from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ingest_telemetry():
    payload = {
        "sensor_key": "tank_temp_main",
        "timestamp": "2026-03-09T20:00:00Z",
        "value": 78.4,
        "unit": "F",
        "quality": "good",
        "source_node": "sump_node",
    }

    response = client.post("/api/v1/telemetry", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["sensor_key"] == "tank_temp_main"
    assert data["value"] == 78.4
    assert data["unit"] == "F"