"""Semáforo de concurrencia del análisis real (Sprint 5 — hardening)."""

import threading

from fastapi.testclient import TestClient

from app.api.routes import analyze as analyze_route
from app.core.config import settings
from app.main import app
from tests.audio_utils import tone_wav

client = TestClient(app)


def _files(name: str = "intent.wav") -> dict:
    return {"audio": (name, tone_wav(1.0, 440.0, silence=0.0), "audio/wav")}


def _post(attempt_id: str, *, name: str = "intent.wav", mode: str = "absolute") -> dict:
    return client.post(
        "/api/v1/analyze",
        files=_files(name),
        data={"attempt_id": attempt_id, "routine_id": "r-busy", "mode": mode},
    )


def test_busy_returns_429_when_queue_full(monkeypatch) -> None:
    monkeypatch.setattr(analyze_route, "_analysis_semaphore", threading.Semaphore(0))
    monkeypatch.setattr(settings, "busy_timeout_sec", 0.0)

    resp = _post("busy-429")

    assert resp.status_code == 429
    assert resp.json()["detail"]["code"] == "SERVICE_BUSY"


def test_semaphore_released_after_error(monkeypatch) -> None:
    # Un solo permiso: si el 400 no libera, el siguiente request debe dar 429
    monkeypatch.setattr(analyze_route, "_analysis_semaphore", threading.Semaphore(1))
    monkeypatch.setattr(settings, "busy_timeout_sec", 0.0)

    bad = _post("busy-rel-bad", name="bad.txt")
    assert bad.status_code == 400

    good = _post("busy-rel-ok")
    assert good.status_code == 202


def test_invalid_mode_rejected_before_semaphore(monkeypatch) -> None:
    monkeypatch.setattr(analyze_route, "_analysis_semaphore", threading.Semaphore(0))
    monkeypatch.setattr(settings, "busy_timeout_sec", 0.0)

    resp = _post("busy-invalid-mode", mode="turbo")

    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "INVALID_MODE"
