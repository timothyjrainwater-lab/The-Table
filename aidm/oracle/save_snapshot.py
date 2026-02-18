"""SaveSnapshot — frozen record of Oracle state at a boundary.

A snapshot is NOT a copy of the stores — it is digests + pointers.
The snapshot records enough information to verify a cold boot rebuild
produces byte-identical state.

Authority: Session Lifecycle Spec v0 §2, Oracle Memo v5.2, GT v12.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Dict, Optional, Tuple

from aidm.oracle.canonical import canonical_json, canonical_short_hash


@dataclass(frozen=True)
class SaveSnapshot:
    """Frozen record of Oracle state at a save boundary.

    No wall-clock timestamps.  ``timestamp_event_id`` is the monotonic
    event boundary marker — "this snapshot reflects state after processing
    event N."
    """

    snapshot_id: str
    save_type: str  # SCENE | SESSION | CAMPAIGN
    timestamp_event_id: int
    facts_ledger_digest: str
    unlock_state_digest: str
    story_state_digest: str
    working_set_digest: str
    event_log_range: Tuple[int, int]  # (first_event_id, last_event_id)
    event_log_hash: str
    pending_state: None  # Phase 3: always None
    pins_snapshot: Dict[str, Any]
    compaction_ids: Tuple[str, ...]
    canonical_bytes: bytes
    bytes_hash: str

    def __post_init__(self) -> None:
        if self.save_type not in ("SCENE", "SESSION", "CAMPAIGN"):
            raise ValueError(f"Unknown save_type: {self.save_type!r}")
        # Freeze mutable containers (BL-010).
        object.__setattr__(
            self, "pins_snapshot", MappingProxyType(dict(self.pins_snapshot))
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serializable dict (excludes canonical_bytes — derived field)."""
        return {
            "snapshot_id": self.snapshot_id,
            "save_type": self.save_type,
            "timestamp_event_id": self.timestamp_event_id,
            "facts_ledger_digest": self.facts_ledger_digest,
            "unlock_state_digest": self.unlock_state_digest,
            "story_state_digest": self.story_state_digest,
            "working_set_digest": self.working_set_digest,
            "event_log_range": list(self.event_log_range),
            "event_log_hash": self.event_log_hash,
            "pending_state": self.pending_state,
            "pins_snapshot": dict(self.pins_snapshot),
            "compaction_ids": list(self.compaction_ids),
            "bytes_hash": self.bytes_hash,
        }


def create_snapshot(
    facts_ledger,
    unlock_state,
    story_state_log,
    working_set,
    event_log,
    event_range: Tuple[int, int],
    pins: Dict[str, Any],
    compaction_registry,
    save_type: str = "SESSION",
) -> SaveSnapshot:
    """Create a SaveSnapshot from Oracle stores at a boundary.

    Steps:
        1. Compute digest of each Oracle store
        2. Compute event_log_hash from events in range
        3. Collect active compaction IDs
        4. Assemble pre-hash dict
        5. Compute canonical_bytes, bytes_hash, snapshot_id
        6. Return frozen SaveSnapshot

    No entropy: no randomness, no wall-clock timestamps, no UUIDs.
    """
    # Step 1: Compute store digests.
    fl_digest = facts_ledger.digest()
    us_digest = unlock_state.digest()
    ss_digest = story_state_log.digest()
    ws_digest = working_set.bytes_hash

    # Step 2: Compute event_log_hash from events in range.
    event_log_hash = _compute_event_log_hash(event_log, event_range)

    # Step 3: Collect active compaction IDs.
    compaction_ids = compaction_registry.active_ids()

    # Step 4: Assemble pre-hash dict.
    pre_hash = {
        "save_type": save_type,
        "timestamp_event_id": event_range[1],
        "facts_ledger_digest": fl_digest,
        "unlock_state_digest": us_digest,
        "story_state_digest": ss_digest,
        "working_set_digest": ws_digest,
        "event_log_range": list(event_range),
        "event_log_hash": event_log_hash,
        "pending_state": None,
        "pins_snapshot": pins,
        "compaction_ids": list(compaction_ids),
    }

    # Step 5: Compute canonical bytes and IDs.
    canonical_bytes = canonical_json(pre_hash)
    bytes_hash = hashlib.sha256(canonical_bytes).hexdigest()
    snapshot_id = canonical_short_hash(pre_hash)

    return SaveSnapshot(
        snapshot_id=snapshot_id,
        save_type=save_type,
        timestamp_event_id=event_range[1],
        facts_ledger_digest=fl_digest,
        unlock_state_digest=us_digest,
        story_state_digest=ss_digest,
        working_set_digest=ws_digest,
        event_log_range=event_range,
        event_log_hash=event_log_hash,
        pending_state=None,
        pins_snapshot=pins,
        compaction_ids=compaction_ids,
        canonical_bytes=canonical_bytes,
        bytes_hash=bytes_hash,
    )


def _compute_event_log_hash(event_log, event_range: Tuple[int, int]) -> str:
    """Compute SHA-256 of JSONL bytes for events in [start, end] inclusive."""
    import json

    start_id, end_id = event_range
    lines = []
    for event in event_log.events:
        if start_id <= event.event_id <= end_id:
            lines.append(json.dumps(event.to_dict(), sort_keys=True))

    jsonl_bytes = ("\n".join(lines) + "\n").encode("utf-8") if lines else b""
    return hashlib.sha256(jsonl_bytes).hexdigest()
