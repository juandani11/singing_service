"""Health check extendido (Sprint 0 — gap O5)."""

from datetime import datetime

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200_with_checks() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "ok"
    assert data["service"] == "singing-service"
    assert data["version"] == "0.4.0"

    checks = data["checks"]
    assert checks["ffmpeg"]["ok"] is True
    assert checks["ffmpeg"]["version"]
    assert checks["librosa"]["ok"] is True
    assert checks["librosa"]["version"]
    assert checks["models_loaded"]["ok"] is True
    assert isinstance(checks["disk_space_mb"], int)
    assert checks["disk_space_mb"] > 0

    datetime.fromisoformat(data["timestamp"])  # ISO8601 válido


def test_health_degraded_without_ffmpeg(monkeypatch) -> None:
    monkeypatch.setattr("app.main.ffmpeg_version", lambda: None)

    response = client.get("/health")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "degraded"
    assert data["checks"]["ffmpeg"] == {"ok": False, "version": None}


def test_swagger_docs_available() -> None:
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_schema_generated() -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "/health" in schema["paths"]
    assert schema["info"]["title"].startswith("SyncDance AI")
    assert schema["info"]["version"] == "0.4.0"
