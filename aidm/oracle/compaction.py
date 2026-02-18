"""Compaction — non-canon accelerator with reproducibility guarantees.

Compactions are derived views that speed up queries but can always be
rebuilt from source data.  They never authorize canon writes.

Rules (Session Lifecycle Spec v0 §4.2):
    - RULE-C1: Compactions never authorize canon writes.
    - RULE-C2: Delete all + rebuild = identical output_bytes.
    - RULE-C3: Same input_handles + policy = identical output_bytes.
    - RULE-C4: allowmention_handles constrains Lens output from compaction.
    - RULE-C5: Provenance is explicit (input_handles + policy_id).

Authority: Session Lifecycle Spec v0 §4, Oracle Memo v5.2 §4.3, GT v12.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from aidm.oracle.canonical import canonical_json, canonical_short_hash


# Valid compaction purposes.
COMPACTION_PURPOSES = frozenset({
    "RECAP",
    "SYNOPSIS",
    "SEGMENT_SUMMARY",
    "CONTEXT_CACHE",
})


@dataclass(frozen=True)
class Compaction:
    """A single non-canon compaction artifact.  Immutable."""

    compaction_id: str
    purpose: str
    compaction_policy_id: str
    input_handles: Tuple[str, ...]
    output_bytes: bytes
    output_hash: str
    allowmention_handles: Tuple[str, ...]

    def __post_init__(self) -> None:
        if self.purpose not in COMPACTION_PURPOSES:
            raise ValueError(f"Unknown compaction purpose: {self.purpose!r}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "compaction_id": self.compaction_id,
            "purpose": self.purpose,
            "compaction_policy_id": self.compaction_policy_id,
            "input_handles": list(self.input_handles),
            "output_hash": self.output_hash,
            "allowmention_handles": list(self.allowmention_handles),
        }


def make_compaction(
    purpose: str,
    compaction_policy_id: str,
    input_handles: Tuple[str, ...],
    source_facts: list,
    allowmention_handles: Optional[Tuple[str, ...]] = None,
) -> Compaction:
    """Build a Compaction from source facts using a deterministic policy.

    Phase 3 compaction policy: concatenate fact payloads sorted by
    stable_key, serialize to canonical JSON.  This is a deterministic
    template, not an LLM.
    """
    # Sort facts by stable_key for determinism.
    sorted_facts = sorted(source_facts, key=lambda f: f.stable_key)

    # Build deterministic output: canonical JSON of ordered payloads.
    payloads = [f.payload for f in sorted_facts]
    output_bytes = canonical_json({
        "compaction_policy_id": compaction_policy_id,
        "purpose": purpose,
        "payloads": payloads,
    })
    output_hash = hashlib.sha256(output_bytes).hexdigest()

    # Compute compaction_id from input handles + policy.
    id_input = canonical_json({
        "input_handles": sorted(input_handles),
        "compaction_policy_id": compaction_policy_id,
    })
    compaction_id = canonical_short_hash({
        "input_handles": sorted(input_handles),
        "compaction_policy_id": compaction_policy_id,
    })

    if allowmention_handles is None:
        allowmention_handles = input_handles

    return Compaction(
        compaction_id=compaction_id,
        purpose=purpose,
        compaction_policy_id=compaction_policy_id,
        input_handles=input_handles,
        output_bytes=output_bytes,
        output_hash=output_hash,
        allowmention_handles=allowmention_handles,
    )


class CompactionRegistry:
    """Registry managing compaction lifecycle.

    Tracks active and stale compactions.  Provides invalidation,
    rebuild, and verification operations.
    """

    def __init__(self) -> None:
        self._compactions: Dict[str, Compaction] = {}
        self._stale: set = set()

    def register(self, compaction: Compaction) -> None:
        """Add a compaction.  Raise ValueError on duplicate ID."""
        if compaction.compaction_id in self._compactions:
            raise ValueError(
                f"Duplicate compaction_id: {compaction.compaction_id!r}"
            )
        self._compactions[compaction.compaction_id] = compaction

    def get(self, compaction_id: str) -> Optional[Compaction]:
        """Get a compaction by ID, or None."""
        return self._compactions.get(compaction_id)

    def all_compactions(self) -> List[Compaction]:
        """All registered compactions, sorted by compaction_id."""
        return sorted(
            self._compactions.values(),
            key=lambda c: c.compaction_id,
        )

    def active_ids(self) -> Tuple[str, ...]:
        """IDs of non-stale compactions, sorted."""
        return tuple(sorted(
            cid for cid in self._compactions
            if cid not in self._stale
        ))

    def invalidate(self, fact_ids) -> List[str]:
        """Mark compactions stale whose input_handles overlap fact_ids.

        Returns list of invalidated compaction IDs.
        """
        fact_set = set(fact_ids)
        invalidated = []
        for cid, compaction in self._compactions.items():
            if fact_set & set(compaction.input_handles):
                self._stale.add(cid)
                invalidated.append(cid)
        return invalidated

    def rebuild(
        self,
        compaction_id: str,
        source_facts: list,
        compaction_policy_id: str,
    ) -> Compaction:
        """Regenerate a compaction from source facts + policy.

        The old compaction is replaced with the new one.
        If the inputs are unchanged, output_bytes will be identical (G4).
        """
        old = self._compactions.get(compaction_id)
        if old is None:
            raise KeyError(f"No compaction with id {compaction_id!r}")

        new = make_compaction(
            purpose=old.purpose,
            compaction_policy_id=compaction_policy_id,
            input_handles=old.input_handles,
            source_facts=source_facts,
            allowmention_handles=old.allowmention_handles,
        )

        # Replace in registry, clear stale flag.
        self._compactions.pop(compaction_id)
        self._stale.discard(compaction_id)
        self._compactions[new.compaction_id] = new
        return new

    def verify_all(self) -> List[Tuple[str, bool]]:
        """Verify output_hash matches for all compactions.

        Returns list of (compaction_id, is_valid) tuples.
        """
        results = []
        for cid in sorted(self._compactions):
            compaction = self._compactions[cid]
            actual_hash = hashlib.sha256(compaction.output_bytes).hexdigest()
            results.append((cid, actual_hash == compaction.output_hash))
        return results

    def __len__(self) -> int:
        return len(self._compactions)
