"""Tests del pipeline de preprocesamiento y formatos (Sprint 0 — gap O2)."""

import subprocess
import wave
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from httpx2 import Response

from app.core.config import settings
from app.main import app
from app.schemas.analyze import AcceptedResponse, AnalysisResult
from app.services.preprocess import (
    PreprocessError,
    preprocess_bytes,
    resolve_ffmpeg,
    wav_duration_sec,
)
from tests.audio_utils import ffmpeg_available, tone_wav, transcode

client = TestClient(app)

_RATE = 44100  # tasa distinta de 16000 para probar la conversión


def _wav_44k(duration: float = 1.0, freq: float = 440.0) -> bytes:
    return tone_wav(duration=duration, freq=freq, silence=0.0, rate=_RATE)


def _post_absolute(
    data: bytes, filename: str, *, attempt_id: str
) -> Response:
    return client.post(
        "/api/v1/analyze",
        files={"audio": (filename, data, "application/octet-stream")},
        data={"attempt_id": attempt_id, "routine_id": "routine-1", "mode": "absolute"},
    )


def test_upload_limits_defaults() -> None:
    assert settings.max_file_mb == 50
    assert settings.max_duration_sec == 600


def test_absolute_mode_preprocesses_and_reports_duration() -> None:
    post = _post_absolute(_wav_44k(duration=1.0), "alumno.wav", attempt_id="prep-real")
    assert post.status_code == 202, post.text
    accepted = AcceptedResponse.model_validate(post.json())

    get = client.get(f"/api/v1/analyze/{accepted.analysis_id}")
    assert get.status_code == 200
    result = AnalysisResult.model_validate(get.json())

    assert result.algorithm_version == "0.5.0-hybrid-modes"
    assert 0.9 <= result.duration_sec <= 1.5  # duración REAL extraída del wav
    assert result.timings.preprocess_ms >= 0
    # Recorte coherente: un audio de 1 s no puede tener eventos en 12 s
    assert result.segments == []
    assert all(p.t <= result.duration_sec + 0.1 for p in result.pitch.student)


def test_absolute_mode_is_idempotent() -> None:
    first = _post_absolute(_wav_44k(), "alumno.wav", attempt_id="prep-idem")
    second = _post_absolute(_wav_44k(), "alumno.wav", attempt_id="prep-idem")
    assert first.json()["analysis_id"] == second.json()["analysis_id"]


def test_unsupported_extension_returns_400() -> None:
    response = _post_absolute(b"contenido de texto", "notas.txt", attempt_id="prep-400-ext")
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "UNSUPPORTED_FORMAT"


def test_corrupt_audio_returns_400() -> None:
    response = _post_absolute(
        b"esto no es audio de verdad", "roto.wav", attempt_id="prep-400-corrupt"
    )
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_AUDIO"


def test_corrupt_reference_returns_400() -> None:
    response = client.post(
        "/api/v1/analyze",
        files={
            "audio": ("alumno.wav", tone_wav(), "audio/wav"),
            "reference_audio": ("ref-rota.wav", b"referencia corrupta", "audio/wav"),
        },
        data={"attempt_id": "prep-400-ref", "routine_id": "routine-1", "mode": "comparative"},
    )
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_AUDIO"


def test_invalid_ffmpeg_binary_returns_500(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FFMPEG_BINARY", str(Path("no_existe") / "ffmpeg-fantasma"))
    response = _post_absolute(_wav_44k(), "alumno.wav", attempt_id="prep-500-ffmpeg")
    assert response.status_code == 500
    assert response.json()["detail"]["code"] == "FFMPEG_NOT_FOUND"


def test_empty_file_returns_400() -> None:
    response = _post_absolute(b"", "vacio.wav", attempt_id="prep-400-empty")
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "EMPTY_FILE"


def test_audio_too_large_returns_413(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "max_file_mb", 0)
    response = _post_absolute(_wav_44k(), "alumno.wav", attempt_id="prep-413-size")
    assert response.status_code == 413
    assert response.json()["detail"]["code"] == "AUDIO_TOO_LARGE"


def test_audio_too_long_returns_413(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "max_duration_sec", 0)
    response = _post_absolute(_wav_44k(duration=1.0), "alumno.wav", attempt_id="prep-413-dur")
    assert response.status_code == 413
    assert response.json()["detail"]["code"] == "AUDIO_TOO_LONG"


@pytest.mark.skipif(not ffmpeg_available(), reason="FFmpeg no disponible")
def test_video_without_audio_track_returns_400(tmp_path: Path) -> None:
    video = tmp_path / "sin_audio.mp4"
    subprocess.run(
        [
            resolve_ffmpeg(),
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc=duration=1:size=64x64:rate=10",
            "-c:v",
            "mpeg4",
            "-pix_fmt",
            "yuv420p",
            str(video),
        ],
        check=True,
        capture_output=True,
    )
    response = _post_absolute(
        video.read_bytes(), "sin_audio.mp4", attempt_id="prep-400-noaudio"
    )
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "NO_AUDIO_TRACK"


@pytest.mark.skipif(not ffmpeg_available(), reason="FFmpeg no disponible")
def test_convert_produces_16k_mono_wav(tmp_path: Path) -> None:
    processed = preprocess_bytes(
        _wav_44k(duration=1.0), "entrada.wav", tmp_dir=tmp_path, name="student"
    )
    with wave.open(str(processed.path), "rb") as w:
        assert w.getframerate() == 16000
        assert w.getnchannels() == 1
        assert abs(processed.duration_sec - 1.0) <= 0.3


@pytest.mark.skipif(not ffmpeg_available(), reason="FFmpeg no disponible")
def test_m4a_is_decoded_and_analyzed() -> None:
    """Mobile graba M4A/AAC por defecto: el servicio debe decodificarlo."""
    m4a = transcode(tone_wav(duration=2.0, freq=440.0, silence=0.0), "a.wav", "a.m4a")
    post = _post_absolute(m4a, "intento.m4a", attempt_id="prep-m4a")
    assert post.status_code == 202, post.text
    result = AnalysisResult.model_validate(
        client.get(f"/api/v1/analyze/{post.json()['analysis_id']}").json()
    )
    assert result.status == "completed"
    assert result.metrics.mean_pitch_hz is not None
    assert abs(result.metrics.mean_pitch_hz - 440.0) < 30.0


@pytest.mark.skipif(not ffmpeg_available(), reason="FFmpeg no disponible")
def test_mp3_is_decoded_and_analyzed() -> None:
    mp3 = transcode(tone_wav(duration=2.0, freq=440.0, silence=0.0), "a.wav", "a.mp3")
    post = _post_absolute(mp3, "intento.mp3", attempt_id="prep-mp3")
    assert post.status_code == 202, post.text


def test_wav_duration_on_non_wav_raises_typed_error(tmp_path: Path) -> None:
    # Salida ilegible → 400 tipado, nunca 500 sin código
    fake = tmp_path / "salida.wav"
    fake.write_bytes(b"esto no es un wav")

    with pytest.raises(PreprocessError) as exc_info:
        wav_duration_sec(fake)
    assert exc_info.value.code == "INVALID_AUDIO"
    assert exc_info.value.status_code == 400


def test_convert_keeps_files_inside_tmp_dir(tmp_path: Path) -> None:
    if not ffmpeg_available():
        pytest.skip("FFmpeg no disponible")
    preprocess_bytes(_wav_44k(duration=1.0), "entrada.wav", tmp_dir=tmp_path, name="a")
    names = {p.name for p in tmp_path.iterdir()}
    assert names == {"a_in.wav", "a.wav"}
