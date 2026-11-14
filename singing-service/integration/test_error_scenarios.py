"""Matriz de errores ejecutable contra el singing-service real.

Uso:
    python integration/test_error_scenarios.py

Requiere el servicio levantado (por defecto http://localhost:5000).
Exit code 0 si todos los escenarios pasan.

Nota: el servicio real clasifica un .txt renombrado a .wav como INVALID_AUDIO
(400), no como UNSUPPORTED_FORMAT. Se verifica el comportamiento real y se
marca la desviacion; UNSUPPORTED_FORMAT se comprueba con la extension .txt.
"""

from __future__ import annotations

import http.server
import os
import sys
import tempfile
import threading
import wave
from pathlib import Path

import numpy as np
import requests

DEFAULT_URL = "http://localhost:5000/api/v1/analyze"
ANALYZE_PATH = "/api/v1/analyze"
TIMEOUT = (5, 300)
MB = 1024 * 1024


def normalize_analyze_url(value: str) -> str:
    url = (value or DEFAULT_URL).strip().rstrip("/")
    if url.endswith(ANALYZE_PATH):
        return url
    if url.endswith("/api/v1"):
        return f"{url}/analyze"
    return f"{url}{ANALYZE_PATH}"


def health_url(analyze_url: str) -> str:
    return analyze_url[: -len(ANALYZE_PATH)] + "/health"


def extract_code(payload: object) -> str | None:
    if not isinstance(payload, dict):
        return None
    detail = payload.get("detail")
    if isinstance(detail, dict):
        return detail.get("code")
    if isinstance(detail, list) and detail:
        first = detail[0]
        if isinstance(first, dict):
            loc = ".".join(str(x) for x in first.get("loc", []))
            return f"VALIDATION_ERROR ({loc}: {first.get('msg', '')})"
    return None


def write_sine_wav(path: Path, duration: float = 1.0, freq: float = 440.0) -> None:
    rate = 44100
    t = np.arange(int(duration * rate)) / rate
    samples = (0.3 * 32767 * np.sin(2 * np.pi * freq * t)).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(samples.tobytes())


def write_large_wav(path: Path, total_mb: int = 51) -> None:
    """WAV de relleno > 50 MB (el servicio corta por tamano antes de decodificar)."""
    with open(path, "wb") as f:
        f.write(b"RIFF")
        f.write((total_mb * MB - 8).to_bytes(4, "little"))
        f.write(b"WAVEfmt ")
        f.write(b"\x00" * 16)
        remaining = total_mb * MB - 28
        chunk = b"\x00" * MB
        while remaining > 0:
            f.write(chunk[: min(MB, remaining)])
            remaining -= MB


def write_long_wav(path: Path, duration_sec: int = 660, rate: int = 8000) -> None:
    """WAV de 11 min a 8 kHz (10.6 MB) para disparar AUDIO_TOO_LONG."""
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        second = b"\x00\x00" * rate
        for _ in range(duration_sec):
            w.writeframes(second)


def post(
    url: str,
    *,
    audio: Path | None,
    mode: str,
    field: str = "audio",
    attempt_id: str,
) -> requests.Response:
    data = {"attempt_id": attempt_id, "routine_id": "err-routine", "mode": mode}
    if audio is None:
        return requests.post(url, data=data, timeout=TIMEOUT)
    with open(audio, "rb") as handle:
        return requests.post(
            url,
            data=data,
            files={field: (audio.name, handle, "application/octet-stream")},
            timeout=TIMEOUT,
        )


class Results:
    def __init__(self) -> None:
        self.total = 0
        self.passed = 0

    def check(
        self,
        name: str,
        *,
        expected_status: int,
        expected_code: str | None,
        response: requests.Response | None,
        note: str = "",
    ) -> None:
        self.total += 1
        if response is None:
            print(f"[FAIL] {name}: sin respuesta (se esperaba {expected_status})")
            return
        try:
            body = response.json()
        except ValueError:
            body = response.text
        code = extract_code(body)
        ok = response.status_code == expected_status and (
            expected_code is None or code == expected_code
        )
        if ok:
            self.passed += 1
            suffix = f"  NOTE: {note}" if note else ""
            print(
                f"[PASS] {name}: HTTP {response.status_code} code={code}"
                f" (esperado {expected_status}/{expected_code}){suffix}"
            )
        else:
            print(
                f"[FAIL] {name}: HTTP {response.status_code} code={code}"
                f" (esperado {expected_status}/{expected_code})"
            )
            print(f"       body: {body}")


class _FiveHundredHandler(http.server.BaseHTTPRequestHandler):
    """Responde 500 con body no-JSON (simula crash/proxy/truncado)."""

    def do_POST(self) -> None:  # noqa: N802 (API de http.server)
        self.send_response(500)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"upstream error, not json")

    def log_message(self, *_args: object) -> None:
        pass


def _check_5xx_without_json() -> tuple[str, str | None]:
    """Clasifica un 5xx sin JSON con el guard del worker (sin KeyError)."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from simulate_celery_worker import classify_response

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _FiveHundredHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_port}/analyze"
        response = requests.post(url, data={"mode": "absolute"}, timeout=(5, 10))
        return classify_response(response)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def main() -> int:
    analyze_url = normalize_analyze_url(
        os.environ.get("SINGING_SERVICE_URL", DEFAULT_URL)
    )

    try:
        health = requests.get(health_url(analyze_url), timeout=(5, 10))
    except requests.RequestException as exc:
        print(f"ERROR: servicio no disponible en {health_url(analyze_url)}: {exc}")
        return 1
    if health.status_code != 200:
        print(f"ERROR: /health devolvio {health.status_code}: {health.text[:300]}")
        return 1
    print(f"Servicio OK: {health_url(analyze_url)} -> 200\n")

    results = Results()
    with tempfile.TemporaryDirectory(prefix="syncdance-errors-") as tmp:
        tmp_dir = Path(tmp)
        sine = tmp_dir / "sine.wav"
        write_sine_wav(sine)

        results.check(
            "mode_invalido",
            expected_status=422,
            expected_code="INVALID_MODE",
            response=post(analyze_url, audio=sine, mode="turbo", attempt_id="err-mode"),
        )

        results.check(
            "comparative_sin_referencia",
            expected_status=400,
            expected_code="MISSING_REFERENCE",
            response=post(
                analyze_url, audio=sine, mode="comparative", attempt_id="err-ref"
            ),
        )

        large = tmp_dir / "large.wav"
        write_large_wav(large, total_mb=51)
        results.check(
            "audio_mayor_50mb",
            expected_status=413,
            expected_code="AUDIO_TOO_LARGE",
            response=post(analyze_url, audio=large, mode="absolute", attempt_id="err-large"),
        )

        long = tmp_dir / "long_11min.wav"
        write_long_wav(long)
        results.check(
            "audio_mayor_600s",
            expected_status=413,
            expected_code="AUDIO_TOO_LONG",
            response=post(analyze_url, audio=long, mode="absolute", attempt_id="err-long"),
        )

        fake_wav = tmp_dir / "texto_renombrado.wav"
        fake_wav.write_text("esto no es audio, es texto plano", encoding="utf-8")
        results.check(
            "txt_renombrado_a_wav",
            expected_status=400,
            expected_code="INVALID_AUDIO",
            response=post(
                analyze_url, audio=fake_wav, mode="absolute", attempt_id="err-fakewav"
            ),
            note="el servicio clasifica datos corruptos como INVALID_AUDIO (no UNSUPPORTED_FORMAT)",
        )

        fake_txt = tmp_dir / "texto.txt"
        fake_txt.write_text("esto no es audio", encoding="utf-8")
        results.check(
            "extension_txt_no_soportada",
            expected_status=400,
            expected_code="UNSUPPORTED_FORMAT",
            response=post(
                analyze_url, audio=fake_txt, mode="absolute", attempt_id="err-faketxt"
            ),
        )

        results.check(
            "sin_campo_audio",
            expected_status=422,
            expected_code=None,
            response=post(analyze_url, audio=None, mode="absolute", attempt_id="err-nofile"),
        )

    # Servicio caido: puerto cerrado -> ConnectionError, nunca un 5xx.
    dead_url = "http://127.0.0.1:1/api/v1/analyze"
    results.total += 1
    try:
        post(dead_url, audio=None, mode="absolute", attempt_id="err-down")
    except requests.ConnectionError:
        results.passed += 1
        print("[PASS] servicio_caido: ConnectionError (sin respuesta 5xx)")
    except requests.RequestException as exc:
        print(f"[FAIL] servicio_caido: excepcion inesperada: {type(exc).__name__}: {exc}")
    else:
        print("[FAIL] servicio_caido: se esperaba ConnectionError")

    # 5xx sin JSON parseable -> recuperable (guard del worker Celery, sin KeyError)
    results.total += 1
    try:
        action, reason = _check_5xx_without_json()
    except Exception as exc:  # noqa: BLE001 (se reporta como FAIL, no se propaga)
        print(f"[FAIL] 5xx_sin_json: {type(exc).__name__}: {exc}")
    else:
        if action == "retry" and reason and "Non-JSON" in reason:
            results.passed += 1
            print(f"[PASS] 5xx_sin_json: action={action} reason={reason}")
        else:
            print(f"[FAIL] 5xx_sin_json: action={action} reason={reason}")

    print(f"\nRESUMEN: {results.passed}/{results.total} checks OK")
    return 0 if results.passed == results.total else 1


def test_5xx_without_json_is_recoverable() -> None:
    """El guard del worker trata un 5xx sin JSON como recuperable (sin KeyError)."""
    action, reason = _check_5xx_without_json()
    assert action == "retry"
    assert reason is not None and "Non-JSON" in reason


if __name__ == "__main__":
    sys.exit(main())
