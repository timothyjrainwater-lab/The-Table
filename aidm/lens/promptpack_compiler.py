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
from typing import Any, Dict, Tuple

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


def compile_promptpack(
    working_set: WorkingSet,
) -> tuple:
    """Compile a WorkingSet into (PromptPack, AllowedToSayEnvelope).

    Steps:
        1. Extract facts_slice → TruthChannel (mask-safe subset via
           allowmention_handles — already filtered by Oracle compiler)
        2. Extract compactions_slice → MemoryChannel (if present)
        3. Extract directives → TaskChannel + OutputContract
        4. Apply default StyleChannel (no Director input in Phase 2)
        5. Assemble PromptPack
        6. Compute promptpack_hash
        7. Build AllowedToSayEnvelope
        8. Return (PromptPack, AllowedToSayEnvelope)

    No truncation: WorkingSet slices are already budget-constrained.
    """
    # Step 1: Build TruthChannel from facts_slice.
    # Facts are Oracle-curated content.  Map to TruthChannel fields.
    # In Phase 2 the TruthChannel carries Oracle facts as outcome_summary.
    truth_parts = []
    for fact_payload in working_set.facts_slice:
        # Each fact payload is a dict — render as deterministic string.
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
    task = TaskChannel()
    contract = OutputContract()

    # Step 4: Default StyleChannel (no Director input).
    style = StyleChannel()

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
