"""Tests del middleware X-Request-ID (fix P0-01)."""

import re

from fastapi.testclient import TestClient

from app.main import app
from tests.audio_utils import tone_wav

client = TestClient(app)

_UUID_HEX = re.compile(r"^[a-f0-9]{32}$")
_FILES = {"audio": ("alumno.wav", tone_wav(duration=1.0), "audio/wav")}
_DATA = {"attempt_id": "rid-att-1", "routine_id": "rid-routine", "mode": "absolute"}


def test_generates_request_id_when_missing() -> None:
    response = client.post("/api/v1/analyze", files=_FILES, data=_DATA)
    assert response.status_code == 202
    request_id = response.headers.get("x-request-id")
    assert request_id is not None
    assert _UUID_HEX.match(request_id)


def test_echoes_valid_request_id() -> None:
    response = client.post(
        "/api/v1/analyze",
        files=_FILES,
        data={**_DATA, "attempt_id": "rid-echo"},
        headers={"X-Request-ID": "abc-123"},
    )
    assert response.status_code == 202
    assert response.headers["x-request-id"] == "abc-123"


def test_invalid_request_id_is_replaced() -> None:
    response = client.post(
        "/api/v1/analyze",
        files=_FILES,
        data={**_DATA, "attempt_id": "rid-invalid"},
        headers={"X-Request-ID": "<script>alert(1)</script>"},
    )
    assert response.status_code == 202
    request_id = response.headers.get("x-request-id")
    assert request_id is not None
    assert request_id != "<script>alert(1)</script>"
    assert _UUID_HEX.match(request_id)


def test_error_400_has_header_and_body_request_id() -> None:
    response = client.post(
        "/api/v1/analyze",
        files={"audio": ("roto.wav", b"esto no es audio", "audio/wav")},
        data={**_DATA, "attempt_id": "rid-400"},
        headers={"X-Request-ID": "rid-400"},
    )
    assert response.status_code == 400
    assert response.headers["x-request-id"] == "rid-400"
    body = response.json()
    assert body["detail"]["code"] == "INVALID_AUDIO"
    assert body["detail"]["request_id"] == "rid-400"


def test_validation_422_has_header_and_body_request_id() -> None:
    response = client.post(
        "/api/v1/analyze",
        data={"attempt_id": "rid-422", "routine_id": "rid-routine", "mode": "absolute"},
        headers={"X-Request-ID": "rid-422"},
    )
    assert response.status_code == 422
    assert response.headers["x-request-id"] == "rid-422"
    assert response.json()["request_id"] == "rid-422"
