"""Stage 6 cache: dossiers keyed by (edge, evidence version), in-process, with an
export so an uploaded map can be baked into its own offline artifact — the same way
the demo dataset was. API-mode only; never touches the demo artifact.
"""
from __future__ import annotations

import threading

from backend import config

_LOCK = threading.Lock()
_CACHE = {}  # (edge, version) -> result


def _key(edge):
    return (edge, config.AGENT_EVIDENCE_VERSION)


def get(edge):
    with _LOCK:
        return _CACHE.get(_key(edge))


def put(edge, result):
    with _LOCK:
        _CACHE[_key(edge)] = result


def export():
    """Dump the cache as an offline-able artifact (edge -> dossier)."""
    with _LOCK:
        return {"evidence_version": config.AGENT_EVIDENCE_VERSION,
                "dossiers": {edge: r for (edge, _v), r in _CACHE.items()}}


def clear():
    with _LOCK:
        _CACHE.clear()
