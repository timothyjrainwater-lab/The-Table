"""WorkingSet — deterministic compiler from Oracle stores to WorkingSet bytes.

Oracle Phase 2: reads FactsLedger, UnlockState, StoryState and produces a
frozen WorkingSet dataclass with canonical JSON bytes.  The WorkingSet is
Oracle's output artifact consumed by the Lens PromptPack compiler.

Authority: Oracle Memo v5.2 §4.5, Lens Spec v0, GT v12.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Dict, Optional, Tuple

from aidm.oracle.canonical import canonical_json, canonical_hash, canonical_short_hash
from aidm.oracle.facts_ledger import Fact, FactsLedger
from aidm.oracle.unlock_state import UnlockState
from aidm.oracle.story_state import StoryState, StoryStateLog


@dataclass(frozen=True)
class WorkingSet:
    """Deterministic snapshot compiled from Oracle stores.

    All mutable containers replaced with frozen equivalents.
    ``canonical_bytes`` is computed at construction time.
    """

    working_set_id: str
    world_id: Optional[str]
    campaign_id: str
    scene_id: Optional[str]
    mode: str
    policy_ids: Dict[str, str]
    pins_snapshot: Dict[str, Any]
    allowmention_handles: Tuple[str, ...]
    locked_precision_handles: Tuple[str, ...]
    facts_slice: Tuple[Dict[str, Any], ...]
    state_slice: Dict[str, Any]
    compactions_slice: Tuple[Dict[str, Any], ...]
    directives: Dict[str, Any]
    canonical_bytes: bytes
    bytes_hash: str

    def __post_init__(self) -> None:
        # Freeze mutable containers per immutability gate (BL-010).
        object.__setattr__(self, "policy_ids", MappingProxyType(dict(self.policy_ids)))
        object.__setattr__(self, "pins_snapshot", MappingProxyType(dict(self.pins_snapshot)))
        object.__setattr__(self, "state_slice", MappingProxyType(dict(self.state_slice)))
        object.__setattr__(self, "directives", MappingProxyType(dict(self.directives)))
        # Freeze inner dicts in tuple fields.
        object.__setattr__(
            self, "facts_slice",
            tuple(MappingProxyType(dict(f)) for f in self.facts_slice),
        )
        object.__setattr__(
            self, "compactions_slice",
            tuple(MappingProxyType(dict(c)) for c in self.compactions_slice),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serializable dict (excludes canonical_bytes — derived field)."""
        return {
            "working_set_id": self.working_set_id,
            "world_id": self.world_id,
            "campaign_id": self.campaign_id,
            "scene_id": self.scene_id,
            "mode": self.mode,
            "policy_ids": dict(self.policy_ids),
            "pins_snapshot": dict(self.pins_snapshot),
            "allowmention_handles": list(self.allowmention_handles),
            "locked_precision_handles": list(self.locked_precision_handles),
            "facts_slice": [dict(f) for f in self.facts_slice],
            "state_slice": dict(self.state_slice),
            "compactions_slice": [dict(c) for c in self.compactions_slice],
            "directives": dict(self.directives),
            "bytes_hash": self.bytes_hash,
        }


@dataclass(frozen=True)
class ScopeCursor:
    """Identifies the current scope for filtering facts and unlocks."""

    campaign_id: str
    scene_id: Optional[str] = None
    world_id: Optional[str] = None


@dataclass(frozen=True)
class CompilationPolicy:
    """Policy knobs for WorkingSet compilation.

    Phase 2: minimal policy — ordering by stable_key, no token budget
    enforcement (that's Phase 3).
    """

    mask_matrix_id: str = "default"
    ordering_policy_id: str = "stable_key"
    truncation_policy_id: str = "none"
    budget_policy_id: str = "unlimited"
    max_facts: int = 0  # 0 = no limit


def compile_working_set(
    facts_ledger: FactsLedger,
    unlock_state: UnlockState,
    story_state_log: StoryStateLog,
    policy: CompilationPolicy,
    scope_cursor: ScopeCursor,
) -> WorkingSet:
    """Compile Oracle stores into a deterministic WorkingSet.

    Steps:
        1. Read facts from FactsLedger (all facts, sorted by stable_key)
        2. Separate allowmention_handles vs locked_precision_handles
        3. Filter facts_slice to only allowmention (unlocked) facts
        4. Snapshot StoryState pointers
        5. Assemble pre-hash dict
        6. Compute canonical_bytes, bytes_hash, working_set_id
        7. Return frozen WorkingSet

    No entropy introduced: no randomness, timestamps, or UUIDs.
    """
    story = story_state_log.current()

    # Step 1: All facts sorted by stable_key.
    all_facts = facts_ledger.all_facts()

    # Step 2: Determine scope for unlock check.
    scope = "SCENE" if scope_cursor.scene_id else "SESSION"

    # Separate handles into allowed (unlocked) vs locked.
    unlocked = unlock_state.unlocked_handles(scope)

    allowmention = []
    locked_precision = []
    for fact in all_facts:
        if fact.fact_id in unlocked and fact.precision_tag == "UNLOCKED":
            allowmention.append(fact.fact_id)
        else:
            locked_precision.append(fact.fact_id)

    # Step 3: Build facts_slice — only allowmention facts, payload only.
    facts_slice = []
    for fact in all_facts:
        if fact.fact_id in allowmention:
            facts_slice.append(fact.payload)

    # Step 4: Apply truncation policy (max_facts).
    if policy.max_facts > 0 and len(facts_slice) > policy.max_facts:
        facts_slice = facts_slice[:policy.max_facts]

    # Step 5: Snapshot StoryState pointers.
    state_slice = {
        "campaign_id": story.campaign_id,
        "world_id": story.world_id,
        "scene_id": story.scene_id,
        "mode": story.mode,
        "version": story.version,
    }

    # Step 6: Policy IDs.
    policy_ids = {
        "mask_matrix_id": policy.mask_matrix_id,
        "ordering_policy_id": policy.ordering_policy_id,
        "truncation_policy_id": policy.truncation_policy_id,
        "budget_policy_id": policy.budget_policy_id,
    }

    pins_snapshot = {
        "hash_algorithm": "sha256",
        "short_hash_length": 16,
        "canonical_profile": "oracle_v0",
    }

    directives = {
        "output_class": "narration",
        "channel_rules": "five_channel_v1",
    }

    # Step 7: Assemble pre-hash dict for canonical serialization.
    pre_hash = {
        "world_id": story.world_id,
        "campaign_id": story.campaign_id,
        "scene_id": story.scene_id,
        "mode": story.mode,
        "policy_ids": policy_ids,
        "pins_snapshot": pins_snapshot,
        "allowmention_handles": sorted(allowmention),
        "locked_precision_handles": sorted(locked_precision),
        "facts_slice": facts_slice,
        "state_slice": state_slice,
        "compactions_slice": [],
        "directives": directives,
    }

    canonical_bytes = canonical_json(pre_hash)
    bytes_hash = hashlib.sha256(canonical_bytes).hexdigest()
    working_set_id = canonical_short_hash(pre_hash)

    return WorkingSet(
        working_set_id=working_set_id,
        world_id=story.world_id,
        campaign_id=story.campaign_id,
        scene_id=story.scene_id,
        mode=story.mode,
        policy_ids=policy_ids,
        pins_snapshot=pins_snapshot,
        allowmention_handles=tuple(sorted(allowmention)),
        locked_precision_handles=tuple(sorted(locked_precision)),
        facts_slice=tuple(dict(f) for f in facts_slice),
        state_slice=state_slice,
        compactions_slice=(),
        directives=directives,
        canonical_bytes=canonical_bytes,
        bytes_hash=bytes_hash,
    )
