"""Métricas Prometheus del servicio (HU-S1-05).

Se exponen en `GET /metrics` (sin auth; red interna). Los nombres siguen la
convención `_total` para counters y `_seconds` para histogramas de latencia.
"""

from prometheus_client import Counter, Gauge, Histogram

# Latencia total de un POST /analyze (desde que pasa validación hasta terminar).
_ANALYSIS_BUCKETS = (0.5, 1, 2, 5, 10, 30, 60, 120, 300)
_PITCH_BUCKETS = (0.1, 0.25, 0.5, 1, 2, 5, 10, 30, 60, 120, 300)
_ALIGN_BUCKETS = (0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5)
_RHYTHM_BUCKETS = (0.1, 0.5, 1, 2, 3, 5, 10, 30, 60)

analysis_requests_total = Counter(
    "analysis_requests_total",
    "Análisis finalizados por modo y resultado",
    ["mode", "status"],
)

analysis_duration_seconds = Histogram(
    "analysis_duration_seconds",
    "Duración total del análisis (segundos)",
    ["mode"],
    buckets=_ANALYSIS_BUCKETS,
)

pitch_duration_seconds = Histogram(
    "pitch_duration_seconds",
    "Duración de la extracción de pitch con pyin (segundos)",
    buckets=_PITCH_BUCKETS,
)

align_duration_seconds = Histogram(
    "align_duration_seconds",
    "Duración de la alineación (segundos)",
    ["method"],
    buckets=_ALIGN_BUCKETS,
)

rhythm_duration_seconds = Histogram(
    "rhythm_duration_seconds",
    "Duración del análisis de ritmo (segundos)",
    buckets=_RHYTHM_BUCKETS,
)

active_requests = Gauge(
    "active_requests",
    "Análisis en curso (incluye espera de semáforo)",
)

analysis_timeouts_total = Counter(
    "analysis_timeouts_total",
    "Timeouts internos por fase",
    ["phase"],
)
