"""Tests HU-S1-02: `/ready` (readiness) y `/version` (metadatos de build)."""

import pytest
from fastapi.testclient import TestClient

from app.main import _pkg_version, app, app_state

client = TestClient(app)


@pytest.fixture(autouse=True)
def _reset_app_state(monkeypatch):
    monkeypatch.setattr(app_state, "ready", False)
    monkeypatch.setattr(app_state, "shutting_down", False)


def test_ready_200_when_ready(monkeypatch) -> None:
    monkeypatch.setattr(app_state, "ready", True)
    monkeypatch.setattr(
        "app.main._check_ffmpeg", lambda: {"ok": True, "version": "7.1.5"}
    )

    response = client.get("/ready", headers={"X-Request-ID": "ready-200"})

    assert response.status_code == 200
    assert response.json() == {
        "ready": True,
        "reason": None,
        "request_id": "ready-200",
    }
    assert response.headers["x-request-id"] == "ready-200"


def test_ready_503_warmup() -> None:
    response = client.get("/ready", headers={"X-Request-ID": "ready-warmup"})

    assert response.status_code == 503
    body = response.json()
    assert body["ready"] is False
    assert body["reason"] == "warmup"
    assert body["request_id"] == "ready-warmup"
    assert response.headers["x-request-id"] == "ready-warmup"


def test_ready_503_shutting_down(monkeypatch) -> None:
    monkeypatch.setattr(app_state, "ready", True)
    monkeypatch.setattr(app_state, "shutting_down", True)

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["reason"] == "shutting_down"


def test_ready_503_ffmpeg_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(app_state, "ready", True)
    monkeypatch.setattr(
        "app.main._check_ffmpeg", lambda: {"ok": False, "version": None}
    )

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["reason"] == "ffmpeg_unavailable"


def test_version_from_env(monkeypatch) -> None:
    monkeypatch.setenv("GIT_SHA", "abc1234")
    monkeypatch.setenv("BUILD_TIME", "2026-11-15T12:00:00Z")

    response = client.get("/version")

    assert response.status_code == 200
    body = response.json()
    assert body["version"] == "0.3.0"
    assert body["git_sha"] == "abc1234"
    assert body["build_time"] == "2026-11-15T12:00:00Z"
    for key in ("python", "ffmpeg", "fastapi", "librosa", "request_id"):
        assert body[key]
    assert body["fastapi"] != "unknown"
    assert body["librosa"] != "unknown"


def test_version_unknown_env(monkeypatch) -> None:
    monkeypatch.delenv("GIT_SHA", raising=False)
    monkeypatch.delenv("BUILD_TIME", raising=False)

    body = client.get("/version").json()

    assert body["git_sha"] == "unknown"
    assert body["build_time"] == "unknown"


def test_version_has_request_id_header(monkeypatch) -> None:
    response = client.get("/version", headers={"X-Request-ID": "ver-123"})

    assert response.headers["x-request-id"] == "ver-123"
    assert response.json()["request_id"] == "ver-123"


def test_pkg_version_unknown() -> None:
    assert _pkg_version("definitely-not-a-package") == "unknown"


def test_lifespan_sets_ready_and_shutting_down(monkeypatch) -> None:
    monkeypatch.setenv("SKIP_WARMUP", "true")
    with TestClient(app) as lifespan_client:
        assert app_state.ready is True
        response = lifespan_client.get("/ready")
        assert response.status_code == 200
        assert response.json()["ready"] is True

    assert app_state.shutting_down is True
    assert app_state.ready is False
