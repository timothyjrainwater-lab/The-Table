"""PromptPack compiler — WorkingSet to PromptPack deterministic compilation.

Compiles an Oracle WorkingSet into a PromptPack + AllowedToSayEnvelope.
This is the Oracle Phase 2 Lens entry point: a parallel path to the existing
PromptPackBuilder (which takes NarrativeBrief).  The existing builder remains
valid for non-Oracle compilation paths.

Lens rules:
    - Read-only to all Oracle stores (no writes).
    - No truncation (Oracle is sole truncator; Lens routes, never clips).
    - No entropy (no randomness, timestamps, UUIDs).
    - Deterministic: same WorkingSet → byte-identical PromptPack.

Authority: Lens Spec v0 §3, Oracle Memo v5.2, GT v12 A-ORACLE-TRUNC.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from aidm.oracle.canonical import canonical_json
from aidm.oracle.working_set import WorkingSet
from aidm.schemas.prompt_pack import (
    MemoryChannel,
    OutputContract,
    PromptPack,
    StyleChannel,
    TaskChannel,
    TruthChannel,
)


@dataclass(frozen=True)
class AllowedToSayEnvelope:
    """Audit artifact emitted alongside every PromptPack compilation.

    Provides traceability from PromptPack content back to Oracle stores.
    """

    allowed_handles: Tuple[str, ...]
    locked_handles: Tuple[str, ...]
    mask_matrix_id: str
    promptpack_hash: str
    working_set_id: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed_handles": list(self.allowed_handles),
            "locked_handles": list(self.locked_handles),
            "mask_matrix_id": self.mask_matrix_id,
            "promptpack_hash": self.promptpack_hash,
            "working_set_id": self.working_set_id,
        }


# Pacing mode → StyleChannel pacing hint mapping (Director Spec v0 §3.1).
_PACING_MAP = {
    "NORMAL": None,       # default — no hint
    "SLOW_BURN": "SLOW_BURN",
    "ACCELERATE": "ACCELERATE",
    "CLIMAX": "CLIMAX",
}


def compile_promptpack(
    working_set: WorkingSet,
    beat_intent=None,
    nudge_directive=None,
) -> tuple:
    """Compile a WorkingSet into (PromptPack, AllowedToSayEnvelope).

    Steps:
        1. Extract facts_slice → TruthChannel (mask-safe subset via
           allowmention_handles — already filtered by Oracle compiler)
        2. Extract compactions_slice → MemoryChannel (if present)
        3. Extract directives → TaskChannel + OutputContract
        4. Apply StyleChannel with Director pacing hint (if BeatIntent provided)
        5. Apply NudgeDirective metadata to TaskChannel (if provided)
        6. If BeatIntent has target_handles, foreground those in TruthChannel
        7. Assemble PromptPack
        8. Compute promptpack_hash
        9. Build AllowedToSayEnvelope
       10. Return (PromptPack, AllowedToSayEnvelope)

    When beat_intent is None: existing Phase 1 behavior (no Director input).
    When nudge_directive is None or type=NONE: no nudge metadata added.

    No truncation: WorkingSet slices are already budget-constrained.
    """
    # Step 1: Build TruthChannel from facts_slice.
    # Facts are Oracle-curated content.  Map to TruthChannel fields.
    # If BeatIntent has target_handles, foreground those facts first.
    facts_list = list(working_set.facts_slice)

    if beat_intent is not None and beat_intent.target_handles:
        target_set = set(beat_intent.target_handles)
        # Partition: foregrounded facts first, then remaining (stable order).
        foregrounded = []
        remaining = []
        for i, fact_payload in enumerate(facts_list):
            # Check if any key in the fact matches a target handle.
            fact_id = fact_payload.get("fact_id", "")
            stable_key = fact_payload.get("stable_key", "")
            if fact_id in target_set or stable_key in target_set:
                foregrounded.append(fact_payload)
            else:
                remaining.append(fact_payload)
        facts_list = foregrounded + remaining

    truth_parts = []
    for fact_payload in facts_list:
        parts = []
        for key in sorted(fact_payload.keys()):
            parts.append(f"{key}: {fact_payload[key]}")
        truth_parts.append("; ".join(parts))

    outcome_summary = " | ".join(truth_parts) if truth_parts else ""

    truth = TruthChannel(
        action_type="oracle_compiled",
        actor_name=working_set.campaign_id,
        outcome_summary=outcome_summary,
        severity="minor",
    )

    # Step 2: Build MemoryChannel from compactions_slice.
    session_facts = tuple(
        str(canonical_json(c), "utf-8")
        for c in working_set.compactions_slice
    )
    memory = MemoryChannel(
        session_facts=session_facts,
    )

    # Step 3: Build TaskChannel + OutputContract from directives.
    # Include nudge metadata if NudgeDirective has type != NONE.
    nudge_type = None
    nudge_target_handle = None
    nudge_reason_code = None
    permission_prompt = False

    if nudge_directive is not None and nudge_directive.type != "NONE":
        nudge_type = nudge_directive.type
        nudge_target_handle = nudge_directive.target_handle
        nudge_reason_code = nudge_directive.reason_code

    if beat_intent is not None:
        permission_prompt = beat_intent.permission_prompt

    task = TaskChannel(
        nudge_type=nudge_type,
        nudge_target_handle=nudge_target_handle,
        nudge_reason_code=nudge_reason_code,
        permission_prompt=permission_prompt,
    )
    contract = OutputContract()

    # Step 4: StyleChannel with Director pacing hint.
    pacing_hint = None
    if beat_intent is not None:
        pacing_hint = _PACING_MAP.get(beat_intent.pacing_mode)

    style = StyleChannel(pacing_hint=pacing_hint)

    # Step 5: Assemble PromptPack.
    pack = PromptPack(
        truth=truth,
        memory=memory,
        task=task,
        style=style,
        contract=contract,
    )

    # Step 6: Compute promptpack_hash from canonical bytes.
    pack_dict = pack.to_dict()
    pack_canonical_bytes = canonical_json(pack_dict)
    promptpack_hash = hashlib.sha256(pack_canonical_bytes).hexdigest()

    # Step 7: Build AllowedToSayEnvelope.
    envelope = AllowedToSayEnvelope(
        allowed_handles=working_set.allowmention_handles,
        locked_handles=working_set.locked_precision_handles,
        mask_matrix_id=working_set.policy_ids.get("mask_matrix_id", "default"),
        promptpack_hash=promptpack_hash,
        working_set_id=working_set.working_set_id,
    )

    return (pack, envelope)
