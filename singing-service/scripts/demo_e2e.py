"""Demo E2E + métricas §15.1 para el singing-service.

Con el servicio levantado (local o Docker):

    python scripts/demo_e2e.py --base-url http://localhost:5000

Genera los audios §12.1 (casi afinado, desviación conocida de 80 cents, pausa
larga), ejecuta la tanda y reporta % de éxito, tiempo medio por intento
(wall y `timings`) y una sonda de rendimiento con audio de 40 s (objetivo
RNF "< 2 s" informativo). Código de salida != 0 si la tanda no está al 100 %.
"""

from __future__ import annotations

import argparse
import io
import math
import struct
import sys
import time
import uuid
import wave

import httpx

_RATE = 16000
_CENTS_80_HZ = 460.8  # 440 * 2^(80/1200)


def tone_wav(duration: float, freq: float, silence: float = 0.0) -> bytes:
    """WAV mono 16 kHz: `silence` s iniciales + tono puro."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(_RATE)
        silent = int(silence * _RATE)
        frames = bytearray()
        for i in range(int(duration * _RATE)):
            sample = 0 if i < silent else int(10000 * math.sin(2 * math.pi * freq * i / _RATE))
            frames += struct.pack("<h", sample)
        w.writeframes(bytes(frames))
    return buf.getvalue()


def analyze(client: httpx.Client, student: bytes, ref: bytes) -> dict:
    """POST + GET completo; devuelve el AnalysisResult o lanza RuntimeError."""
    attempt = f"demo-{uuid.uuid4().hex[:12]}"
    post = client.post(
        "/api/v1/analyze",
        files={
            "audio": ("alumno.wav", student, "audio/wav"),
            "reference_audio": ("ref.wav", ref, "audio/wav"),
        },
        data={"attempt_id": attempt, "routine_id": "demo", "mode": "comparative"},
    )
    if post.status_code != 202:
        raise RuntimeError(f"POST {post.status_code}: {post.text[:200]}")
    analysis_id = post.json()["analysis_id"]
    get = client.get(f"/api/v1/analyze/{analysis_id}")
    if get.status_code != 200:
        raise RuntimeError(f"GET {get.status_code}: {get.text[:200]}")
    result = get.json()
    if result["status"] != "completed":
        raise RuntimeError(f"status={result['status']}")
    return result


def check(scenario: str, r: dict) -> str | None:
    """Valida la expectativa de cada escenario; devuelve un error o None."""
    codes = [f["code"] for f in r["feedback"]]
    types = [s["type"] for s in r["segments"]]
    if scenario == "casi_afinado":
        if r["scores"]["afinacion"] < 80:
            return f"afinacion={r['scores']['afinacion']} < 80"
        if "OUT_OF_TUNE" in codes:
            return "feedback inesperado OUT_OF_TUNE"
    elif scenario == "desviacion_80c":
        tune = [s for s in r["segments"] if s["type"] == "out_of_tune"]
        if not tune or not 75 <= tune[0]["delta_cents"] <= 85:
            return f"segmento out_of_tune con delta fuera de 75-85: {tune[:1]}"
        if "OUT_OF_TUNE" not in codes:
            return "falta feedback OUT_OF_TUNE"
    elif scenario == "pausa_larga":
        if "NO_VOICE" not in codes:
            return "falta feedback NO_VOICE"
        if types != ["no_voice"]:
            return f"segments={types}"
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:5000")
    parser.add_argument("--repeat", type=int, default=1, help="repeticiones por escenario")
    args = parser.parse_args()

    ref_tone = tone_wav(3.0, 440.0)
    scenarios = [
        ("casi_afinado", tone_wav(3.0, 440.0), ref_tone),
        ("desviacion_80c", tone_wav(3.0, _CENTS_80_HZ), ref_tone),
        ("pausa_larga", tone_wav(2.0, 440.0, silence=0.9), tone_wav(2.0, 440.0)),
    ]

    rows: list[tuple[str, int, int, list[float], list[float], list[dict]]] = []
    failures: list[str] = []
    total = ok = 0

    with httpx.Client(base_url=args.base_url, timeout=180.0) as client:
        health = client.get("/health")
        if health.status_code != 200:
            print(f"Servicio no disponible en {args.base_url} (/health {health.status_code})")
            return 2

        print(f"=== singing-service — tanda de prueba ({args.base_url}) ===")
        for name, student, ref in scenarios:
            walls: list[float] = []
            totals: list[float] = []
            results: list[dict] = []
            for _ in range(args.repeat):
                total += 1
                start = time.perf_counter()
                try:
                    r = analyze(client, student, ref)
                    err = check(name, r)
                except (httpx.HTTPError, RuntimeError) as exc:
                    err = str(exc)
                    r = {}
                walls.append((time.perf_counter() - start) * 1000)
                if err is None:
                    ok += 1
                    results.append(r)
                    t = r["timings"]
                    totals.append(
                        t["preprocess_ms"] + t["pitch_ms"] + t["dtw_ms"] + t["scoring_ms"]
                    )
                else:
                    failures.append(f"{name}: {err}")
            rows.append((name, len(results), args.repeat, walls, totals, results))

        for name, hits, reps, walls, _totals, results in rows:
            vocal = ",".join(str(r["scores"]["vocal"]) for r in results) or "-"
            wall = f"{sum(walls) / len(walls):.0f}" if walls else "-"
            print(f"{name:<18} {hits}/{reps}  wall {wall} ms  vocal {vocal}")

        # Sonda de rendimiento (RNF: < 2 s por audio de 40 s) — informativa
        start = time.perf_counter()
        perf = analyze(client, tone_wav(40.0, 440.0), tone_wav(40.0, 440.0))
        perf_wall = (time.perf_counter() - start) * 1000
        t = perf["timings"]
        phases = (t["preprocess_ms"], t["pitch_ms"], t["dtw_ms"], t["scoring_ms"])
        target = "OK" if sum(phases) < 2000 else "NO CUMPLE (informativo)"
        print(
            f"\nSonda rendimiento (audio 40 s): wall {perf_wall:.0f} ms | "
            f"timings {sum(phases)} ms (preprocess {phases[0]} + pitch {phases[1]} "
            f"+ dtw {phases[2]} + scoring {phases[3]}) — objetivo < 2000 ms: {target}"
        )

        # Métricas §15.1
        all_walls = [w for _, _, _, ws, _, _ in rows for w in ws]
        all_totals = [x for _, _, _, _, ts, _ in rows for x in ts]
        print("\n--- Métricas §15.1 ---")
        print(f"éxito: {ok}/{total} = {100.0 * ok / max(total, 1):.1f} %")
        if all_walls:
            print(f"tiempo medio wall por intento: {sum(all_walls) / len(all_walls):.0f} ms")
        if all_totals:
            print(
                f"tiempo medio `timings` por intento: "
                f"{sum(all_totals) / len(all_totals):.0f} ms"
            )
        for f in failures:
            print(f"FALLO: {f}")

    return 0 if ok == total else 1


if __name__ == "__main__":
    sys.exit(main())
