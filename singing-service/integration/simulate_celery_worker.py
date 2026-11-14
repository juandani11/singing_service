"""Simula el worker Celery del Core contra el singing-service.

Uso:
    python integration/simulate_celery_worker.py --audio fixtures/sine_440hz_5s.wav --mode absolute
    python integration/simulate_celery_worker.py --audio fixtures/sine_442hz_5s.wav \
        --mode comparative --reference fixtures/sine_440hz_5s.wav

URL: variable SINGING_SERVICE_URL (acepta base http://host:5000 o la URL completa
.../api/v1/analyze). Default: http://localhost:5000/api/v1/analyze.

El campo multipart del audio es `audio` (simetrico con `reference_audio`). Se envia
tambien `attempt_id` y `routine_id`, obligatorios para el contrato v1.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from pathlib import Path

import requests

DEFAULT_URL = "http://localhost:5000/api/v1/analyze"
ANALYZE_PATH = "/api/v1/analyze"


def normalize_analyze_url(value: str) -> str:
    """Acepta base o URL completa y devuelve siempre .../api/v1/analyze."""
    url = (value or DEFAULT_URL).strip().rstrip("/")
    if url.endswith(ANALYZE_PATH):
        return url
    if url.endswith("/api/v1"):
        return f"{url}/analyze"
    return f"{url}{ANALYZE_PATH}"


def detail_code(payload: object) -> str | None:
    """Extrae detail.code (dict) o el primer error de validacion (list)."""
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


def classify_response(response: requests.Response) -> tuple[str, str | None]:
    """Clasifica la respuesta como el worker Celery: ok | fail | retry.

    Misma logica que el ejemplo de `docs/celery-contract.md` §6:
    - 5xx sin JSON -> ("retry", "Non-JSON response ...") sin KeyError.
    - 5xx con JSON -> ("retry", detail.code).
    - 4xx (excepto 429) -> ("fail", detail.code).
    - 429 -> ("retry", "SERVICE_BUSY").
    - 2xx -> ("ok", None).
    """
    if response.status_code == 429:
        return "retry", "SERVICE_BUSY"
    if response.status_code >= 500:
        try:
            payload = response.json()
        except ValueError:
            return "retry", f"Non-JSON response {response.status_code}"
        return "retry", detail_code(payload)
    if 400 <= response.status_code < 500:
        try:
            payload = response.json()
        except ValueError:
            payload = {}
        return "fail", detail_code(payload)
    return "ok", None


def dump(payload: object) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audio", required=True, help="ruta del audio del intento")
    parser.add_argument("--mode", choices=("absolute", "comparative"), default="absolute")
    parser.add_argument("--reference", help="audio de referencia (requerido en comparative)")
    parser.add_argument(
        "--include-contour",
        action="store_true",
        help="flag futuro: el servicio v1 lo ignora (pitch_contour no implementado)",
    )
    parser.add_argument("--attempt-id", default=f"sim-{uuid.uuid4().hex[:12]}")
    parser.add_argument("--routine-id", default="sim-routine")
    parser.add_argument("--url", default=os.environ.get("SINGING_SERVICE_URL", DEFAULT_URL))
    parser.add_argument("--no-get", action="store_true", help="no hace el GET del resultado")
    args = parser.parse_args()

    audio = Path(args.audio)
    if not audio.is_file():
        print(f"ERROR: no existe el audio: {audio}")
        return 2
    if args.mode == "comparative" and not args.reference:
        print("AVISO: comparative sin --reference; el servicio respondera 400 MISSING_REFERENCE")

    analyze_url = normalize_analyze_url(args.url)
    data = {
        "attempt_id": args.attempt_id,
        "routine_id": args.routine_id,
        "mode": args.mode,
    }
    if args.include_contour:
        data["include_contour"] = "true"  # ignorado por v1 (documentado)

    files = {"audio": (audio.name, open(audio, "rb"), "application/octet-stream")}
    reference_handle = None
    if args.reference:
        reference = Path(args.reference)
        if not reference.is_file():
            print(f"ERROR: no existe la referencia: {reference}")
            return 2
        reference_handle = open(reference, "rb")
        files["reference_audio"] = (
            reference.name,
            reference_handle,
            "application/octet-stream",
        )

    print(f"POST {analyze_url}")
    print(f"  attempt_id={args.attempt_id} routine_id={args.routine_id} mode={args.mode}")

    started = time.perf_counter()
    try:
        response = requests.post(
            analyze_url, data=data, files=files, timeout=(5, 300)
        )
    except requests.ConnectionError as exc:
        elapsed = (time.perf_counter() - started) * 1000
        print(f"NETWORK ERROR: conexion rechazada ({elapsed:.0f} ms): {exc}")
        return 2
    except requests.Timeout as exc:
        elapsed = (time.perf_counter() - started) * 1000
        print(f"NETWORK ERROR: timeout ({elapsed:.0f} ms): {exc}")
        return 2
    except requests.RequestException as exc:
        print(f"NETWORK ERROR: {exc}")
        return 2
    finally:
        files["audio"][1].close()
        if reference_handle is not None:
            reference_handle.close()

    elapsed = (time.perf_counter() - started) * 1000
    print(f"STATUS: {response.status_code}")
    print(f"ELAPSED_MS: {elapsed:.0f}")
    try:
        body = response.json()
    except ValueError:
        body = response.text
    print("BODY:")
    dump(body)

    action, worker_code = classify_response(response)
    if action == "fail":
        if worker_code:
            print(f"DETAIL_CODE: {worker_code}")
        return 1
    if action == "retry":
        print(f"RETRY: {worker_code or 'recoverable'}")
        return 2

    if response.status_code in (200, 202) and not args.no_get:
        analysis_id = body.get("analysis_id") if isinstance(body, dict) else None
        if not analysis_id:
            print("ERROR: la respuesta no trae analysis_id")
            return 2
        get_url = f"{analyze_url}/{analysis_id}"
        print(f"\nGET {get_url}")
        started_get = time.perf_counter()
        try:
            result = requests.get(get_url, timeout=(5, 10))
        except requests.RequestException as exc:
            print(f"NETWORK ERROR en GET: {exc}")
            return 2
        get_elapsed = (time.perf_counter() - started_get) * 1000
        print(f"STATUS: {result.status_code}")
        print(f"ELAPSED_MS: {get_elapsed:.0f}")
        try:
            result_body = result.json()
        except ValueError:
            result_body = result.text
        print("RESULT:")
        dump(result_body)
        if result.status_code >= 500:
            return 2
        if result.status_code >= 400:
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
