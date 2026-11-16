"""Cache en memoria del análisis de ritmo (HU-S2-XX, optimización A).

Clave: `sha256(audio_bytes)[:16]` + sample rate + `tempo_bpm_hint`. Así el mismo
audio con el mismo hint evita repetir `librosa.load` + `beat_track` +
`onset_detect`. El cache vive en el proceso: no persiste entre reinicios (para
producción real, Redis en Sprint 3+).

TTL 1 h y máximo 128 entradas; el resultado cacheado es exacto (mismos hops y
mismo sample rate que el baseline).
"""

from __future__ import annotations

import hashlib
import threading
import time
from collections import OrderedDict
from pathlib import Path

import librosa

from app.services.rhythm_eval import RhythmResult, analyze_rhythm

_CACHE_TTL_SECONDS = 3600.0
_CACHE_MAX_ENTRIES = 128

_cache: OrderedDict[str, tuple[float, RhythmResult]] = OrderedDict()
_lock = threading.Lock()


def rhythm_cache_key(
    audio_bytes: bytes, sr: int, tempo_bpm_hint: float | None
) -> str:
    """Identifica un análisis de ritmo reproducible."""
    digest = hashlib.sha256(audio_bytes).hexdigest()[:16]
    hint = "none" if tempo_bpm_hint is None else f"{float(tempo_bpm_hint):.3f}"
    return f"{digest}:{sr}:{hint}"


def _get(key: str) -> RhythmResult | None:
    now = time.monotonic()
    with _lock:
        entry = _cache.get(key)
        if entry is None:
            return None
        stored_at, result = entry
        if now - stored_at > _CACHE_TTL_SECONDS:
            del _cache[key]
            return None
        _cache.move_to_end(key)
        return result


def _put(key: str, result: RhythmResult) -> None:
    with _lock:
        _cache[key] = (time.monotonic(), result)
        _cache.move_to_end(key)
        while len(_cache) > _CACHE_MAX_ENTRIES:
            _cache.popitem(last=False)


def clear_rhythm_cache() -> None:
    """Vacía el cache (tests y reinicios lógicos)."""
    with _lock:
        _cache.clear()


def analyze_rhythm_file(
    path: Path,
    *,
    key: str,
    sr: int,
    tempo_bpm_hint: float | None,
) -> RhythmResult:
    """Cache hit → resultado inmediato; miss → carga y analiza."""
    cached = _get(key)
    if cached is not None:
        return cached
    y, _ = librosa.load(str(path), sr=sr, mono=True)
    result = analyze_rhythm(y, sr, tempo_bpm_hint)
    _put(key, result)
    return result
