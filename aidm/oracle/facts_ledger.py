"""FactsLedger — append-only store of canon facts with provenance.

Each fact is content-addressed by ``canonical_short_hash(payload)``.
Duplicate payloads are rejected.  The ledger produces a deterministic
``digest()`` regardless of insertion order (facts sorted by stable_key).

Authority: Oracle Memo v5.2 section 4, GT v12 A-ORACLE-SPINE.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from aidm.oracle.canonical import (
    canonical_hash,
    canonical_json,
    canonical_short_hash,
)

# Valid fact kinds.
FACT_KINDS = frozenset({
    "WORLD_RULE",
    "NPC_IDENTITY",
    "LOCATION",
    "FACTION_LAW",
    "CLUE",
    "ITEM_LORE",
    "QUEST_STATE",
    "ENTITY_STATE",
    "COMBAT_OUTCOME",
})

# Valid visibility masks.
VISIBILITY_MASKS = frozenset({
    "PUBLIC",
    "DM_ONLY",
    "PLAYER_SPECIFIC",
    "SYSTEM",
})

# Valid precision tags.
PRECISION_TAGS = frozenset({"LOCKED", "UNLOCKED"})


@dataclass(frozen=True)
class Fact:
    """A single canon fact with provenance.  Immutable."""

    fact_id: str
    kind: str
    payload: Dict[str, Any]
    provenance: Dict[str, Any]
    visibility_mask: str = "DM_ONLY"
    precision_tag: str = "LOCKED"
    stable_key: str = ""
    created_event_id: int = 0

    def __post_init__(self) -> None:
        if self.kind not in FACT_KINDS:
            raise ValueError(f"Unknown fact kind: {self.kind!r}")
        if self.visibility_mask not in VISIBILITY_MASKS:
            raise ValueError(f"Unknown visibility_mask: {self.visibility_mask!r}")
        if self.precision_tag not in PRECISION_TAGS:
            raise ValueError(f"Unknown precision_tag: {self.precision_tag!r}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fact_id": self.fact_id,
            "kind": self.kind,
            "payload": self.payload,
            "provenance": self.provenance,
            "visibility_mask": self.visibility_mask,
            "precision_tag": self.precision_tag,
            "stable_key": self.stable_key,
            "created_event_id": self.created_event_id,
        }


def make_fact(
    kind: str,
    payload: Dict[str, Any],
    provenance: Dict[str, Any],
    created_event_id: int,
    visibility_mask: str = "DM_ONLY",
    precision_tag: str = "LOCKED",
) -> Fact:
    """Factory: build a Fact with auto-computed fact_id and stable_key.

    Validates that payload and provenance can pass ``canonical_json()``
    (i.e., no floats).
    """
    # Validate canonical-safe before computing ID.
    canonical_json(payload)
    canonical_json(provenance)

    fact_id = canonical_short_hash(payload)
    stable_key = f"{kind}:{fact_id[:8]}"

    return Fact(
        fact_id=fact_id,
        kind=kind,
        payload=payload,
        provenance=provenance,
        visibility_mask=visibility_mask,
        precision_tag=precision_tag,
        stable_key=stable_key,
        created_event_id=created_event_id,
    )


class FactsLedger:
    """Append-only ledger of canon facts."""

    def __init__(self) -> None:
        self._facts: Dict[str, Fact] = {}

    def append(self, fact: Fact) -> None:
        """Append a fact.  Raise ``ValueError`` on duplicate fact_id."""
        if fact.fact_id in self._facts:
            raise ValueError(
                f"Duplicate fact_id {fact.fact_id!r} — content-addressed "
                f"dedup rejected this append."
            )
        self._facts[fact.fact_id] = fact

    def get(self, fact_id: str) -> Optional[Fact]:
        return self._facts.get(fact_id)

    def query(
        self,
        kind: Optional[str] = None,
        visibility_mask: Optional[str] = None,
    ) -> List[Fact]:
        """Filter facts.  Return sorted by stable_key."""
        results = list(self._facts.values())
        if kind is not None:
            results = [f for f in results if f.kind == kind]
        if visibility_mask is not None:
            results = [f for f in results if f.visibility_mask == visibility_mask]
        results.sort(key=lambda f: f.stable_key)
        return results

    def all_facts(self) -> List[Fact]:
        """All facts sorted by stable_key."""
        result = list(self._facts.values())
        result.sort(key=lambda f: f.stable_key)
        return result

    def to_jsonl(self, path: Path) -> None:
        """Persist to JSONL using canonical_json()."""
        with open(path, "wb") as fh:
            for fact in self.all_facts():
                fh.write(canonical_json(fact.to_dict()))
                fh.write(b"\n")

    @classmethod
    def from_jsonl(cls, path: Path) -> "FactsLedger":
        """Load from JSONL."""
        ledger = cls()
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                fact = Fact(**data)
                ledger._facts[fact.fact_id] = fact
        return ledger

    def digest(self) -> str:
        """Determinism receipt: canonical_hash of sorted fact list.

        Same facts in any insertion order produce the same digest.
        """
        sorted_dicts = [f.to_dict() for f in self.all_facts()]
        return canonical_hash(sorted_dicts)

    def __len__(self) -> int:
        return len(self._facts)
