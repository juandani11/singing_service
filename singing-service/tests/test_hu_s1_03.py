"""Tests HU-S1-03: warm-up de librosa/numba en el lifespan."""

import asyncio
import logging
import time

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import _warmup, app, app_state, lifespan

client = TestClient(app)


@pytest.fixture(autouse=True)
def _reset_app_state(monkeypatch):
    monkeypatch.setattr(app_state, "ready", False)
    monkeypatch.setattr(app_state, "shutting_down", False)
    monkeypatch.setattr(app_state, "warmup_completed", False)
    monkeypatch.setattr(app_state, "warmup_duration_ms", None)
    monkeypatch.setattr(app_state, "warmup_beat_track_completed", False)
    monkeypatch.setattr(app_state, "warmup_beat_track_duration_ms", None)


def _fake_pyin_440(y, **kwargs):
    hop = kwargs.get("hop_length", 512)
    n = max(1, len(y) // hop + 1)
    return np.full(n, 440.0), np.ones(n, dtype=bool), np.ones(n, dtype=float)


def test_warmup_success(monkeypatch, caplog) -> None:
    monkeypatch.delenv("SKIP_WARMUP", raising=False)
    monkeypatch.setenv("SKIP_WARMUP_BEAT", "true")
    monkeypatch.setattr("librosa.pyin", _fake_pyin_440)

    with caplog.at_level(logging.INFO, logger="singing"):
        with TestClient(app) as lifespan_client:
            assert app_state.ready is True
            assert app_state.warmup_completed is True
            assert app_state.warmup_duration_ms is not None
            assert lifespan_client.get("/ready").status_code == 200

    assert "warmup_completed" in caplog.text


def test_warmup_failure_does_not_crash(monkeypatch, caplog) -> None:
    monkeypatch.delenv("SKIP_WARMUP", raising=False)
    monkeypatch.setenv("SKIP_WARMUP_BEAT", "true")

    def boom(*_args, **_kwargs):
        raise RuntimeError("pyin boom")

    monkeypatch.setattr("librosa.pyin", boom)

    with caplog.at_level(logging.WARNING, logger="singing"):
        with TestClient(app) as lifespan_client:
            assert app_state.ready is True
            assert app_state.warmup_completed is False
            assert lifespan_client.get("/ready").status_code == 200

    assert "warmup_failed" in caplog.text


def test_skip_warmup(monkeypatch, caplog) -> None:
    monkeypatch.setenv("SKIP_WARMUP", "true")
    called = {"pyin": False}

    def fail_if_called(*_args, **_kwargs):
        called["pyin"] = True
        raise AssertionError("pyin no debe llamarse con SKIP_WARMUP=true")

    monkeypatch.setattr("librosa.pyin", fail_if_called)

    with caplog.at_level(logging.INFO, logger="singing"):
        with TestClient(app) as lifespan_client:
            assert app_state.ready is True
            assert app_state.warmup_completed is False
            assert app_state.warmup_duration_ms is None
            assert lifespan_client.get("/ready").status_code == 200

    assert called["pyin"] is False
    assert "warmup_skipped" in caplog.text


def test_ready_503_during_warmup() -> None:
    response = client.get("/ready", headers={"X-Request-ID": "warmup-ready"})

    assert response.status_code == 503
    assert response.json()["reason"] == "warmup"
    assert response.headers["x-request-id"] == "warmup-ready"


def test_warmup_duration_under_5s() -> None:
    started = time.perf_counter()
    _warmup()
    elapsed_ms = (time.perf_counter() - started) * 1000

    assert app_state.warmup_completed is True
    assert app_state.warmup_duration_ms is not None
    assert app_state.warmup_duration_ms < 5000
    assert elapsed_ms < 5000


def test_health_includes_warmup(monkeypatch) -> None:
    monkeypatch.setattr(app_state, "warmup_completed", True)
    monkeypatch.setattr(app_state, "warmup_duration_ms", 1234.5)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["checks"]["warmup"] == {
        "ok": True,
        "duration_ms": 1234.5,
    }

def test_warmup_unexpected_hz(monkeypatch, caplog) -> None:
    def fake_300(y, **kwargs):
        hop = kwargs.get("hop_length", 512)
        n = max(1, len(y) // hop + 1)
        return np.full(n, 300.0), np.ones(n, dtype=bool), np.ones(n, dtype=float)

    monkeypatch.setattr("librosa.pyin", fake_300)

    with caplog.at_level(logging.WARNING, logger="singing"):
        _warmup()

    assert app_state.warmup_completed is False
    assert "warmup_failed" in caplog.text


def test_lifespan_exits_if_self_test_fails(monkeypatch) -> None:
    monkeypatch.setattr("app.main._self_test", lambda: False)

    async def run_lifespan() -> None:
        async with lifespan(app):
            pass

    with pytest.raises(SystemExit):
        asyncio.run(run_lifespan())
