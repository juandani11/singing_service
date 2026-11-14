"""Tests de extracción de pitch con pyin (Sprint 3, plan §4 — HU-43)."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.analyze import AcceptedResponse, AnalysisResult
from app.services.pitch import extract_pitch
from tests.audio_utils import tone_wav

client = TestClient(app)


def _post_absolute(
    data: bytes, filename: str, attempt_id: str
) -> AcceptedResponse:
    response = client.post(
        "/api/v1/analyze",
        files={"audio": (filename, data, "audio/wav")},
        data={"attempt_id": attempt_id, "routine_id": "routine-1", "mode": "absolute"},
    )
    assert response.status_code == 202, response.text
    return AcceptedResponse.model_validate(response.json())


def _median_f0(points: list, lo: float, hi: float) -> float | None:
    values = [p.f0 for p in points if lo <= p.t <= hi and p.voiced and p.f0 is not None]
    if not values:
        return None
    values.sort()
    return values[len(values) // 2]


def test_extract_pitch_finds_tone_and_silence(tmp_path: Path) -> None:
    wav = tmp_path / "tono.wav"
    wav.write_bytes(tone_wav(duration=3.0, freq=440.0, silence=0.5))

    result = extract_pitch(wav, hop_length=512)

    assert result.pitch_ms >= 0
    assert result.points  # frames presentes
    assert all(p.t <= 3.1 for p in result.points)
    # Silencio inicial: sin voz y sin F0
    assert all(not p.voiced and p.f0 is None for p in result.points if p.t < 0.4)
    # Tono 440 Hz: mediana de los frames voceados ≈ 440
    median = _median_f0(result.points, 1.0, 2.9)
    assert median is not None and abs(median - 440.0) < 10.0
    # silence_pct acorde a ~0.5 s de silencio en 3 s (~17%)
    assert 8 <= result.silence_pct <= 30


def test_absolute_mode_uses_pyin_pitch() -> None:
    accepted = _post_absolute(
        tone_wav(duration=3.0), "alumno.wav", attempt_id="pitch-route"
    )
    get = client.get(f"/api/v1/analyze/{accepted.analysis_id}")
    assert get.status_code == 200
    result = AnalysisResult.model_validate(get.json())

    assert result.algorithm_version == "0.5.0-hybrid-modes"
    assert result.pitch.hop_ms == 32  # hop_length 512 @ 16 kHz
    assert result.pitch.reference is None
    assert result.timings.pitch_ms >= 0
    assert result.timings.scoring_ms >= 0
    assert 0.9 <= result.duration_sec <= 3.2

    # Curva real del alumno detectada
    student_median = _median_f0(result.pitch.student, 1.0, 2.9)
    assert student_median is not None and abs(student_median - 440.0) < 15.0
    assert result.metrics.mean_pitch_hz is not None
    assert abs(result.metrics.mean_pitch_hz - 440.0) < 15.0

    # HU-43: silencio inicial detectado en la curva y reflejado en silence_pct
    assert all(not p.voiced for p in result.pitch.student if p.t < 0.4)
    assert 8 <= result.scores.silence_pct <= 30
    # Sin referencia no hay desafinación ni segmentos out_of_tune
    assert not any(s.type == "out_of_tune" for s in result.segments)


def test_pure_silence_reports_high_silence_pct() -> None:
    accepted = _post_absolute(
        tone_wav(duration=1.0, silence=1.0), "silencio.wav", attempt_id="pitch-silence"
    )
    get = client.get(f"/api/v1/analyze/{accepted.analysis_id}")
    result = AnalysisResult.model_validate(get.json())

    assert result.scores.silence_pct >= 90
    assert not any(p.voiced for p in result.pitch.student)
    # HU-46: silencio total → segmento no_voice + feedback NO_VOICE (no desafinación)
    assert [s.type for s in result.segments] == ["no_voice"]
    assert [f.code for f in result.feedback] == ["NO_VOICE"]
