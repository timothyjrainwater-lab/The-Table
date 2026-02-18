"""UnlockState — enforcement state for precision tokens and content visibility.

Tracks which content handles are unlocked at which scope level.
Scope ordering: SCENE < SESSION < CAMPAIGN.  A broader unlock satisfies
narrower checks.  Re-unlocking with broader scope upgrades; narrower is
ignored.

Authority: Oracle Memo v5.2 section 5, GT v12 A-ORACLE-SPINE.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, FrozenSet, List

from aidm.oracle.canonical import canonical_hash, canonical_json

# Scope ordering — higher index = broader.
SCOPE_ORDER: Dict[str, int] = {
    "SCENE": 0,
    "SESSION": 1,
    "CAMPAIGN": 2,
}

VALID_SCOPES = frozenset(SCOPE_ORDER.keys())

VALID_SOURCES = frozenset({
    "NOTEBOOK",
    "RULEBOOK",
    "RECALL_ROLL",
    "SYSTEM",
})


@dataclass(frozen=True)
class UnlockEntry:
    """A single unlock record.  Immutable."""

    handle: str
    scope: str = "SCENE"
    source: str = "SYSTEM"
    provenance_event_id: int = 0
    created_at: str = ""

    def __post_init__(self) -> None:
        if self.scope not in VALID_SCOPES:
            raise ValueError(f"Unknown scope: {self.scope!r}")
        if self.source not in VALID_SOURCES:
            raise ValueError(f"Unknown source: {self.source!r}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "handle": self.handle,
            "scope": self.scope,
            "source": self.source,
            "provenance_event_id": self.provenance_event_id,
            "created_at": self.created_at,
        }


class UnlockState:
    """Tracks unlocked content handles with scope-based access control."""

    def __init__(self) -> None:
        # handle -> UnlockEntry (keeps the broadest-scope entry).
        self._unlocks: Dict[str, UnlockEntry] = {}

    def unlock(self, entry: UnlockEntry) -> None:
        """Record an unlock.

        Idempotent: re-unlocking with broader scope upgrades the stored
        entry.  Re-unlocking with same or narrower scope is a no-op.
        """
        existing = self._unlocks.get(entry.handle)
        if existing is None:
            self._unlocks[entry.handle] = entry
            return

        existing_rank = SCOPE_ORDER[existing.scope]
        new_rank = SCOPE_ORDER[entry.scope]
        if new_rank > existing_rank:
            # Broader scope — upgrade.
            self._unlocks[entry.handle] = entry

    def is_unlocked(self, handle: str, current_scope: str) -> bool:
        """Check if *handle* is unlocked at *current_scope* or broader.

        A CAMPAIGN unlock satisfies SESSION and SCENE checks.
        """
        entry = self._unlocks.get(handle)
        if entry is None:
            return False
        entry_rank = SCOPE_ORDER[entry.scope]
        check_rank = SCOPE_ORDER[current_scope]
        return entry_rank >= check_rank

    def unlocked_handles(self, current_scope: str) -> FrozenSet[str]:
        """All handles unlocked at or above *current_scope*."""
        check_rank = SCOPE_ORDER[current_scope]
        return frozenset(
            handle
            for handle, entry in self._unlocks.items()
            if SCOPE_ORDER[entry.scope] >= check_rank
        )

    def to_jsonl(self, path: Path) -> None:
        """Persist using canonical_json()."""
        with open(path, "wb") as fh:
            for entry in self._sorted_entries():
                fh.write(canonical_json(entry.to_dict()))
                fh.write(b"\n")

    @classmethod
    def from_jsonl(cls, path: Path) -> "UnlockState":
        """Load from JSONL."""
        state = cls()
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                entry = UnlockEntry(**data)
                # Direct insert — persisted data is already deduplicated.
                state._unlocks[entry.handle] = entry
        return state

    def digest(self) -> str:
        """Determinism receipt: canonical_hash of sorted unlock entries.

        Same unlocks in any insertion order produce the same digest.
        """
        sorted_dicts = [e.to_dict() for e in self._sorted_entries()]
        return canonical_hash(sorted_dicts)

    def _sorted_entries(self) -> List[UnlockEntry]:
        """Entries sorted by handle for deterministic ordering."""
        return sorted(self._unlocks.values(), key=lambda e: e.handle)

    def __len__(self) -> int:
        return len(self._unlocks)
