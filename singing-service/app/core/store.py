"""Almacén stateless con TTL (plan §2.1): caché operativa, no fuente de verdad.

- `analysis_id -> AnalysisResult` con expiración (TTL por env).
- `attempt_id -> analysis_id` para idempotencia de reintentos (RNF-07).
- La persistencia real la hace el Core (PostgreSQL) con el JSON recibido.
"""

from __future__ import annotations

import threading
import time

from app.core.config import settings
from app.schemas.analyze import AnalysisResult

_MAX_ENTRIES = 1000


class TtlStore[T]:
    def __init__(self, ttl_seconds: int, max_entries: int = _MAX_ENTRIES) -> None:
        self._ttl = ttl_seconds
        self._max = max_entries
        self._data: dict[str, tuple[float, T]] = {}
        self._index: dict[str, str] = {}
        self._lock = threading.Lock()

    def save(self, key: str, value: T, *, index_key: str | None = None) -> None:
        expires = time.monotonic() + self._ttl
        with self._lock:
            self._purge_locked()
            if len(self._data) >= self._max:
                oldest = min(self._data, key=lambda k: self._data[k][0])
                self._remove_locked(oldest)
            self._data[key] = (expires, value)
            if index_key is not None:
                self._index[index_key] = key

    def get(self, key: str) -> T | None:
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            expires, value = entry
            if time.monotonic() > expires:
                self._remove_locked(key)
                return None
            return value

    def get_by_index(self, index_key: str) -> str | None:
        """Resuelve idempotencia; devuelve None si el análisis asociado expiró."""
        with self._lock:
            key = self._index.get(index_key)
            if key is None:
                return None
            entry = self._data.get(key)
            if entry is None:
                self._index.pop(index_key, None)
                return None
            if time.monotonic() > entry[0]:
                self._remove_locked(key)
                return None
            return key

    def _remove_locked(self, key: str) -> None:
        """Elimina un dato y cualquier índice que apunte a él."""
        del self._data[key]
        stale = [k for k, v in self._index.items() if v == key]
        for k in stale:
            del self._index[k]

    def _purge_locked(self) -> None:
        now = time.monotonic()
        expired = [k for k, (exp, _) in self._data.items() if now > exp]
        for k in expired:
            self._remove_locked(k)


analysis_store: TtlStore[AnalysisResult] = TtlStore(
    ttl_seconds=settings.analysis_ttl_seconds
)
