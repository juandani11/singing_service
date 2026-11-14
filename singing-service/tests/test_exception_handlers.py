"""Tests de los exception handlers y de `request_id` (cobertura de app/main.py)."""

import builtins
import logging
import re
import shutil

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.main import _http_exception_handler, _validation_exception_handler, app
from app.middleware.request_id import RequestIDMiddleware
from tests.audio_utils import tone_wav

_UUID_HEX = re.compile(r"^[a-f0-9]{32}$")


def _teapot_app() -> FastAPI:
    """App aislada con los mismos handlers/middleware (no contamina el OpenAPI)."""
    test_app = FastAPI()
    test_app.add_middleware(RequestIDMiddleware)
    test_app.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    test_app.add_exception_handler(RequestValidationError, _validation_exception_handler)

    @test_app.get("/teapot")
    def teapot() -> None:
        raise HTTPException(
            status_code=418,
            detail={"code": "TEAPOT", "message": "short and stout"},
        )

    return test_app


def test_http_exception_418_has_request_id() -> None:
    client = TestClient(_teapot_app())
    response = client.get("/teapot", headers={"X-Request-ID": "teapot-418"})
    assert response.status_code == 418
    assert response.headers["x-request-id"] == "teapot-418"
    body = response.json()
    assert body["detail"]["code"] == "TEAPOT"
    assert body["detail"]["request_id"] == "teapot-418"


def test_validation_error_422_has_request_id() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/analyze",
        data={"attempt_id": "handlers-422", "routine_id": "r", "mode": "absolute"},
        headers={"X-Request-ID": "handlers-422"},
    )
    assert response.status_code == 422
    assert response.headers["x-request-id"] == "handlers-422"
    assert response.json()["request_id"] == "handlers-422"


def test_unhandled_error_500_has_request_id_and_logs_exc_info(
    monkeypatch, caplog
) -> None:
    client = TestClient(app)

    def boom(*_args, **_kwargs):
        raise RuntimeError("boom")

    # `librosa.pyin` está capturado por pitch.py (400 PITCH_EXTRACT_FAILED);
    # para el 500 se monkeypatchea la función ya importada en la ruta.
    monkeypatch.setattr("app.api.routes.analyze.extract_pitch", boom)

    with caplog.at_level(logging.ERROR, logger="singing"):
        response = client.post(
            "/api/v1/analyze",
            files={"audio": ("a.wav", tone_wav(duration=1.0), "audio/wav")},
            data={"attempt_id": "handlers-500", "routine_id": "r", "mode": "absolute"},
            headers={"X-Request-ID": "handlers-500"},
        )

    assert response.status_code == 500
    assert response.headers["x-request-id"] == "handlers-500"
    body = response.json()
    assert body["detail"]["code"] == "UNHANDLED_ERROR"
    assert body["detail"]["request_id"] == "handlers-500"
    assert "Traceback" not in response.text

    records = [r for r in caplog.records if "unhandled_exception" in r.getMessage()]
    assert records, "falta el log unhandled_exception"
    assert any(r.exc_info is not None for r in records)


def test_http_exception_non_dict_detail_has_request_id() -> None:
    client = TestClient(app)
    response = client.get("/ruta-inexistente", headers={"X-Request-ID": "not-found"})
    assert response.status_code == 404
    assert response.headers["x-request-id"] == "not-found"
    body = response.json()
    assert body["detail"] == "Not Found"
    assert body["request_id"] == "not-found"


def test_health_librosa_failure_is_degraded(monkeypatch) -> None:
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "librosa":
            raise ImportError("librosa roto")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    client = TestClient(app)
    response = client.get("/health", headers={"X-Request-ID": "health-librosa"})
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"]["librosa"]["ok"] is False
    assert body["request_id"] == "health-librosa"


def test_health_disk_error_uses_zero(monkeypatch) -> None:
    def boom(_path):
        raise OSError("disk error")

    monkeypatch.setattr(shutil, "disk_usage", boom)
    client = TestClient(app)
    response = client.get("/health", headers={"X-Request-ID": "health-disk"})
    assert response.status_code == 200
    assert response.json()["checks"]["disk_space_mb"] == 0


def test_health_has_request_id_header_and_body() -> None:
    client = TestClient(app)
    response = client.get("/health", headers={"X-Request-ID": "health-rid"})
    assert response.status_code == 200
    assert response.headers["x-request-id"] == "health-rid"
    assert response.json()["request_id"] == "health-rid"
    assert _UUID_HEX.match(response.json()["request_id"]) is None  # es el enviado
