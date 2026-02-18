"""Canonical JSON profile for Oracle artifacts.

Defines the single authoritative serialization profile used by all Oracle
stores.  Every persisted Oracle artifact uses this profile.

Profile:
    - object keys: sorted lexicographically (sort_keys=True)
    - separators: (',', ':') -- no insignificant whitespace
    - encoding: UTF-8, ensure_ascii=True
    - no trailing newline in canonical form
    - floats: FORBIDDEN (raise TypeError if encountered)
    - hash algorithm: SHA-256, full hex digest (64 chars)
    - short hash: first 16 chars of full hex digest

Authority: Oracle Memo v5.2 section 6, GT v12 A-ORACLE-SPINE.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any


class _FloatBlockEncoder(json.JSONEncoder):
    """JSON encoder that rejects float values anywhere in the object graph."""

    def default(self, o: Any) -> Any:  # pragma: no cover — fallback path
        raise TypeError(f"canonical_json forbids type {type(o).__name__}: {o!r}")

    def encode(self, o: Any) -> str:
        self._reject_floats(o)
        return super().encode(o)

    def _reject_floats(self, o: Any) -> None:
        if isinstance(o, float):
            raise TypeError(
                f"Floats are forbidden in canonical Oracle artifacts (got {o!r}). "
                "Convert to int or str before serialization."
            )
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(k, float):
                    raise TypeError(
                        f"Float dict key forbidden in canonical artifacts (got {k!r})."
                    )
                self._reject_floats(v)
        elif isinstance(o, (list, tuple)):
            for item in o:
                self._reject_floats(item)


# Module-level encoder instance — reusable, thread-safe for encode().
_ENCODER = _FloatBlockEncoder(
    sort_keys=True,
    separators=(",", ":"),
    ensure_ascii=True,
)


def canonical_json(obj: Any) -> bytes:
    """Serialize *obj* to canonical JSON bytes.

    Returns UTF-8 bytes with no trailing newline.  Raises ``TypeError`` if
    any float value is encountered anywhere in the object graph.
    """
    return _ENCODER.encode(obj).encode("utf-8")


def canonical_hash(obj: Any) -> str:
    """Return the SHA-256 hex digest (64 chars) of ``canonical_json(obj)``."""
    return hashlib.sha256(canonical_json(obj)).hexdigest()


def canonical_short_hash(obj: Any) -> str:
    """Return the first 16 chars of ``canonical_hash(obj)``."""
    return canonical_hash(obj)[:16]
