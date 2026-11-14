"""Tests unitarios del almacén TTL (revisiones S1: expiración del índice)."""

import time

from app.core.store import TtlStore


def test_get_by_index_returns_none_after_expiry() -> None:
    store: TtlStore[int] = TtlStore(ttl_seconds=0)
    store.save("analysis-1", 1, index_key="attempt-1")
    time.sleep(0.01)
    # Regresión revisión S1: el índice no debe devolver un id ya expirado
    assert store.get_by_index("attempt-1") is None
    assert store.get("analysis-1") is None


def test_index_follows_value_expiry() -> None:
    store: TtlStore[str] = TtlStore(ttl_seconds=60)
    store.save("a", "valor", index_key="att")
    assert store.get_by_index("att") == "a"
    assert store.get("a") == "valor"


def test_purge_removes_stale_index_entries() -> None:
    store: TtlStore[int] = TtlStore(ttl_seconds=0, max_entries=2)
    store.save("k1", 1, index_key="i1")
    time.sleep(0.01)
    store.save("k2", 2, index_key="i2")  # purga k1 (expirado) y su índice i1
    assert store.get_by_index("i1") is None
    assert store.get("k1") is None


def test_max_entries_evicts_oldest() -> None:
    store: TtlStore[int] = TtlStore(ttl_seconds=60, max_entries=2)
    store.save("old", 1, index_key="i-old")
    store.save("new", 2)
    store.save("newest", 3)  # supera el máximo → expulsa "old"
    assert store.get("old") is None
    assert store.get("newest") == 3
    assert store.get_by_index("i-old") is None
