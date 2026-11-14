"""Observabilidad RNF-03 y límites de env (revisión de Sprint 5)."""

import logging

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.main import app
from tests.audio_utils import tone_wav

client = TestClient(app)


def test_idempotent_hit_is_logged(caplog) -> None:
    payload = {
        "attempt_id": "log-idem-1",
        "routine_id": "r-log",
        "mode": "absolute",
    }
    files = {"audio": ("a.wav", tone_wav(1.0), "audio/wav")}

    with caplog.at_level(logging.INFO, logger="singing"):
        first = client.post("/api/v1/analyze", files=files, data=payload)
        second = client.post("/api/v1/analyze", files=files, data=payload)

    assert first.status_code == 202 and second.status_code == 202
    assert second.json()["analysis_id"] == first.json()["analysis_id"]
    assert "analysis_idempotent_hit" in caplog.text
    assert "log-idem-1" in caplog.text


def test_not_found_is_logged(caplog) -> None:
    with caplog.at_level(logging.INFO, logger="singing"):
        resp = client.get("/api/v1/analyze/id-que-no-existe")

    assert resp.status_code == 404
    assert "analysis_not_found" in caplog.text


def test_busy_env_bounds_fail_fast() -> None:
    # BUSY_TIMEOUT_SEC negativo → ValueError dentro de acquire() por request (500);
    # con Field(ge=...) la configuración inválida truena al arrancar en su lugar.
    with pytest.raises(ValidationError):
        Settings(busy_timeout_sec=-1.0)
    with pytest.raises(ValidationError):
        Settings(max_concurrent_analyses=0)
