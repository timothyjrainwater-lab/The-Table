"""cold_boot — rebuild byte-identical Oracle state from snapshot + event log.

Given a SaveSnapshot and the stored EventLog, cold_boot() replays events
through an Oracle-specific reducer to reconstruct FactsLedger, UnlockState,
and StoryState, then verifies all digests match the snapshot.

Authority: Session Lifecycle Spec v0 §3, Oracle Memo v5.2, GT v12.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Tuple

from aidm.core.event_log import Event, EventLog
from aidm.oracle.facts_ledger import Fact, FactsLedger, make_fact
from aidm.oracle.unlock_state import UnlockEntry, UnlockState
from aidm.oracle.story_state import StoryState, StoryStateLog
from aidm.oracle.table_mood import MoodObservation, TableMoodStore
from aidm.oracle.working_set import (
    CompilationPolicy,
    ScopeCursor,
    WorkingSet,
    compile_working_set,
)
from aidm.oracle.save_snapshot import SaveSnapshot


class ColdBootDigestMismatchError(Exception):
    """Raised when cold boot digest verification fails.

    Attributes:
        store_name: Which store's digest failed (e.g., "facts_ledger").
        expected: The digest stored in the snapshot.
        actual: The digest computed from the rebuilt store.
    """

    def __init__(self, store_name: str, expected: str, actual: str) -> None:
        self.store_name = store_name
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"Cold boot digest mismatch for {store_name}: "
            f"expected {expected[:16]}..., got {actual[:16]}..."
        )


class ColdBootPinMismatchError(Exception):
    """Raised when cold boot pin assertion fails.

    Attributes:
        mismatched_pin: The pin key that doesn't match.
        expected_value: The value stored in the snapshot.
        actual_value: The current environment value.
    """

    def __init__(
        self, mismatched_pin: str, expected_value: Any, actual_value: Any
    ) -> None:
        self.mismatched_pin = mismatched_pin
        self.expected_value = expected_value
        self.actual_value = actual_value
        super().__init__(
            f"Cold boot pin mismatch: pin '{mismatched_pin}' "
            f"expected {expected_value!r}, got {actual_value!r}"
        )


class ColdBootEventLogCorruptionError(Exception):
    """Raised when event log hash doesn't match snapshot."""

    def __init__(self, expected: str, actual: str) -> None:
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"Event log corruption: expected hash {expected[:16]}..., "
            f"got {actual[:16]}..."
        )


def cold_boot(
    snapshot: SaveSnapshot,
    event_log: EventLog,
    current_pins: Dict[str, Any] | None = None,
) -> Tuple[FactsLedger, UnlockState, StoryStateLog, WorkingSet]:
    """Rebuild byte-identical Oracle state from snapshot + event log.

    Steps:
        1. Assert event_log_hash matches — HARD FAIL on mismatch
        2. Assert pins_snapshot matches current_pins — HARD FAIL on mismatch
        3. Initialize empty Oracle stores
        4. Replay events through Oracle-specific reducer
        5. Assert all store digests match — HARD FAIL on mismatch
        6. Rebuild WorkingSet via compile_working_set()
        7. Assert working_set_digest matches — HARD FAIL on mismatch
        8. Return reconstructed stores

    No entropy: deterministic replay, no randomness or timestamps.
    """
    if current_pins is None:
        current_pins = dict(snapshot.pins_snapshot)

    # Step 1: Assert event_log_hash matches.
    actual_event_hash = _compute_event_log_hash(
        event_log, snapshot.event_log_range
    )
    if actual_event_hash != snapshot.event_log_hash:
        raise ColdBootEventLogCorruptionError(
            expected=snapshot.event_log_hash,
            actual=actual_event_hash,
        )

    # Step 2: Assert pins match.
    snapshot_pins = dict(snapshot.pins_snapshot)
    for key in sorted(set(snapshot_pins) | set(current_pins)):
        expected = snapshot_pins.get(key)
        actual = current_pins.get(key)
        if expected != actual:
            raise ColdBootPinMismatchError(
                mismatched_pin=key,
                expected_value=expected,
                actual_value=actual,
            )

    # Step 3: Initialize empty Oracle stores.
    # StoryStateLog requires an initial state — extract campaign_id
    # from the first oracle_story event, or use a default from the snapshot.
    facts_ledger = FactsLedger()
    unlock_state = UnlockState()
    # We'll initialize with a default campaign_id from the snapshot working_set_digest context.
    # The actual campaign_id comes from oracle_story_init events during replay.
    story_state_log: StoryStateLog | None = None

    # Step 4: Replay events through Oracle-specific reducer.
    start_id, end_id = snapshot.event_log_range
    for event in event_log.events:
        if event.event_id < start_id or event.event_id > end_id:
            continue
        story_state_log = _reduce_oracle_event(
            facts_ledger, unlock_state, story_state_log, event
        )

    # If no story events were processed, create a minimal StoryStateLog.
    if story_state_log is None:
        story_state_log = StoryStateLog(StoryState(campaign_id="default"))

    # Step 5: Assert store digests match.
    _assert_digest(
        "facts_ledger",
        snapshot.facts_ledger_digest,
        facts_ledger.digest(),
    )
    _assert_digest(
        "unlock_state",
        snapshot.unlock_state_digest,
        unlock_state.digest(),
    )
    _assert_digest(
        "story_state",
        snapshot.story_state_digest,
        story_state_log.digest(),
    )

    # Step 6: Rebuild WorkingSet.
    story = story_state_log.current()
    working_set = compile_working_set(
        facts_ledger=facts_ledger,
        unlock_state=unlock_state,
        story_state_log=story_state_log,
        policy=CompilationPolicy(),
        scope_cursor=ScopeCursor(
            campaign_id=story.campaign_id,
            scene_id=story.scene_id,
            world_id=story.world_id,
        ),
    )

    # Step 7: Assert working_set_digest matches.
    _assert_digest(
        "working_set",
        snapshot.working_set_digest,
        working_set.bytes_hash,
    )

    return (facts_ledger, unlock_state, story_state_log, working_set)


def _reduce_oracle_event(
    facts_ledger: FactsLedger,
    unlock_state: UnlockState,
    story_state_log: StoryStateLog | None,
    event: Event,
    table_mood_store: TableMoodStore | None = None,
) -> StoryStateLog | None:
    """Map a single event to Oracle store mutations.

    Oracle event types (parallel to replay_runner.reduce_event, which
    operates on WorldState):
        - oracle_fact_created: append fact to FactsLedger
        - oracle_unlock: record unlock in UnlockState
        - oracle_story_init: initialize StoryStateLog
        - scene_start, scene_end, mode_changed, world_id_set:
          apply to StoryStateLog
        - mood_observation: append to TableMoodStore (if provided)

    Unknown event types are silently ignored.
    """
    event_type = event.event_type
    payload = event.payload

    if event_type == "oracle_fact_created":
        fact = Fact(
            fact_id=payload["fact_id"],
            kind=payload["kind"],
            payload=payload["payload"],
            provenance=payload.get("provenance", {}),
            visibility_mask=payload.get("visibility_mask", "DM_ONLY"),
            precision_tag=payload.get("precision_tag", "LOCKED"),
            stable_key=payload.get("stable_key", ""),
            created_event_id=event.event_id,
        )
        facts_ledger.append(fact)

    elif event_type == "oracle_unlock":
        entry = UnlockEntry(
            handle=payload["handle"],
            scope=payload.get("scope", "SCENE"),
            source=payload.get("source", "SYSTEM"),
            provenance_event_id=event.event_id,
        )
        unlock_state.unlock(entry)

    elif event_type == "oracle_story_init":
        if story_state_log is None:
            initial = StoryState(
                campaign_id=payload["campaign_id"],
                world_id=payload.get("world_id"),
                scene_id=payload.get("scene_id"),
                mode=payload.get("mode", "EXPLORATION"),
            )
            story_state_log = StoryStateLog(initial)

    elif event_type in ("scene_start", "scene_end", "mode_changed", "world_id_set"):
        if story_state_log is not None:
            story_state_log.apply(event_type, payload)

    elif event_type == "mood_observation":
        if table_mood_store is not None:
            obs = MoodObservation(
                observation_id=payload["observation_id"],
                source=payload["source"],
                scope=payload["scope"],
                tags=tuple(payload["tags"]),
                scene_id=payload["scene_id"],
                provenance_event_id=payload["provenance_event_id"],
                confidence=payload.get("confidence"),
                evidence=payload.get("evidence"),
            )
            table_mood_store.append(obs)

    return story_state_log


def _assert_digest(store_name: str, expected: str, actual: str) -> None:
    """Assert digest match, raise ColdBootDigestMismatchError on failure."""
    if expected != actual:
        raise ColdBootDigestMismatchError(
            store_name=store_name,
            expected=expected,
            actual=actual,
        )


def _compute_event_log_hash(
    event_log: EventLog, event_range: Tuple[int, int]
) -> str:
    """Compute SHA-256 of JSONL bytes for events in [start, end] inclusive.

    Must match the same computation in save_snapshot.py.
    """
    start_id, end_id = event_range
    lines = []
    for event in event_log.events:
        if start_id <= event.event_id <= end_id:
            lines.append(json.dumps(event.to_dict(), sort_keys=True))

    jsonl_bytes = ("\n".join(lines) + "\n").encode("utf-8") if lines else b""
    return hashlib.sha256(jsonl_bytes).hexdigest()
