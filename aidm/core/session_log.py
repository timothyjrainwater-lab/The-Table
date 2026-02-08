"""M1 Session Log — Unified intent + result logging with replay support.

Extends the core EventLog to provide:
- Intent-to-result correlation
- Deterministic replay verification
- 10× replay verification capability

Reference: docs/runtime/IPC_CONTRACT.md, docs/runtime/INTENT_LIFECYCLE.md
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import json
from pathlib import Path
from copy import deepcopy

from aidm.core.event_log import Event, EventLog
from aidm.core.state import WorldState
from aidm.core.rng_manager import RNGManager
from aidm.schemas.intent_lifecycle import IntentObject, IntentStatus
from aidm.schemas.engine_result import EngineResult, EngineResultStatus


@dataclass
class SessionLogEntry:
    """Single entry in the session log.

    Correlates an intent with its resolution result.
    """

    intent: IntentObject
    """The intent that was resolved."""

    result: Optional[EngineResult] = None
    """The resolution result (None if intent was retracted)."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = {"intent": self.intent.to_dict()}
        if self.result is not None:
            data["result"] = self.result.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionLogEntry":
        """Create from dictionary."""
        intent = IntentObject.from_dict(data["intent"])
        result = None
        if "result" in data and data["result"] is not None:
            result = EngineResult.from_dict(data["result"])
        return cls(intent=intent, result=result)


@dataclass
class SessionLog:
    """Session log with intent-result correlation.

    Provides:
    - Append-only logging of intent → result pairs
    - JSONL serialization for persistence
    - Replay verification support
    """

    entries: List[SessionLogEntry] = field(default_factory=list)
    """All logged intent-result pairs."""

    master_seed: int = 0
    """Master RNG seed for the session."""

    initial_state_hash: str = ""
    """Hash of initial world state for verification."""

    def append(self, intent: IntentObject, result: Optional[EngineResult] = None) -> None:
        """Append an intent-result pair to the log.

        Args:
            intent: The intent (should be CONFIRMED, RESOLVED, or RETRACTED)
            result: The resolution result (None for RETRACTED intents)
        """
        entry = SessionLogEntry(intent=intent, result=result)
        self.entries.append(entry)

    def get_by_intent_id(self, intent_id: str) -> Optional[SessionLogEntry]:
        """Find entry by intent ID."""
        for entry in self.entries:
            if entry.intent.intent_id == intent_id:
                return entry
        return None

    def to_jsonl(self, path: Path) -> None:
        """Serialize to JSONL file.

        Format:
        - Line 1: Session metadata (seed, initial_state_hash)
        - Lines 2+: Intent-result entries
        """
        with open(path, "w", encoding="utf-8") as f:
            # Write metadata
            metadata = {
                "_type": "session_metadata",
                "master_seed": self.master_seed,
                "initial_state_hash": self.initial_state_hash,
            }
            json.dump(metadata, f, sort_keys=True)
            f.write("\n")

            # Write entries
            for entry in self.entries:
                json.dump(entry.to_dict(), f, sort_keys=True)
                f.write("\n")

    @classmethod
    def from_jsonl(cls, path: Path) -> "SessionLog":
        """Deserialize from JSONL file."""
        log = cls()

        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if not lines:
            return log

        # First line is metadata
        metadata = json.loads(lines[0])
        if metadata.get("_type") == "session_metadata":
            log.master_seed = metadata.get("master_seed", 0)
            log.initial_state_hash = metadata.get("initial_state_hash", "")
            lines = lines[1:]

        # Remaining lines are entries
        for line in lines:
            line = line.strip()
            if not line:
                continue
            entry_data = json.loads(line)
            entry = SessionLogEntry.from_dict(entry_data)
            log.entries.append(entry)

        return log

    def __len__(self) -> int:
        """Number of entries in log."""
        return len(self.entries)


@dataclass
class ReplayVerificationResult:
    """Result of replay verification."""

    verified: bool
    """True if replay produced identical results."""

    entries_checked: int
    """Number of entries verified."""

    divergence_index: Optional[int] = None
    """Index of first divergence (None if verified)."""

    divergence_details: Optional[str] = None
    """Details about the divergence."""

    replay_time_ms: float = 0.0
    """Time taken for replay in milliseconds."""


def verify_result_match(
    original: EngineResult,
    replayed: EngineResult,
) -> Tuple[bool, str]:
    """Verify two EngineResults match for determinism.

    Returns:
        Tuple of (matches, details_if_mismatch)
    """
    if original.status != replayed.status:
        return False, f"Status mismatch: {original.status} vs {replayed.status}"

    if original.rng_final_offset != replayed.rng_final_offset:
        return False, (
            f"RNG offset mismatch: {original.rng_final_offset} vs "
            f"{replayed.rng_final_offset}"
        )

    if len(original.rolls) != len(replayed.rolls):
        return False, (
            f"Roll count mismatch: {len(original.rolls)} vs {len(replayed.rolls)}"
        )

    for i, (orig_roll, replay_roll) in enumerate(zip(original.rolls, replayed.rolls)):
        if orig_roll.natural_roll != replay_roll.natural_roll:
            return False, (
                f"Roll {i} natural mismatch: {orig_roll.natural_roll} vs "
                f"{replay_roll.natural_roll}"
            )
        if orig_roll.total != replay_roll.total:
            return False, (
                f"Roll {i} total mismatch: {orig_roll.total} vs {replay_roll.total}"
            )

    if len(original.state_changes) != len(replayed.state_changes):
        return False, (
            f"State change count mismatch: {len(original.state_changes)} vs "
            f"{len(replayed.state_changes)}"
        )

    for i, (orig_sc, replay_sc) in enumerate(
        zip(original.state_changes, replayed.state_changes)
    ):
        if orig_sc.entity_id != replay_sc.entity_id:
            return False, f"State change {i} entity mismatch"
        if orig_sc.field != replay_sc.field:
            return False, f"State change {i} field mismatch"
        if orig_sc.new_value != replay_sc.new_value:
            return False, (
                f"State change {i} value mismatch: {orig_sc.new_value} vs "
                f"{replay_sc.new_value}"
            )

    return True, ""


class ReplayHarness:
    """Replay harness for deterministic verification.

    Provides:
    - Single replay verification
    - 10× replay verification (per M1 requirements)
    - Intent-based resolution replay
    """

    def __init__(
        self,
        resolver_fn: callable,
        initial_state: WorldState,
        master_seed: int,
    ):
        """Initialize replay harness.

        Args:
            resolver_fn: Function that resolves IntentObject → EngineResult
                        Signature: (intent, world_state, rng) -> EngineResult
            initial_state: Starting world state
            master_seed: Master RNG seed
        """
        self.resolver_fn = resolver_fn
        self.initial_state = initial_state
        self.master_seed = master_seed

    def replay_session(
        self,
        session_log: SessionLog,
        apply_state_changes: bool = True,
    ) -> ReplayVerificationResult:
        """Replay a session log and verify all results.

        Args:
            session_log: The session log to replay
            apply_state_changes: If True, apply state changes between entries

        Returns:
            ReplayVerificationResult
        """
        import time

        start_time = time.perf_counter()

        rng = RNGManager(self.master_seed)
        current_state = deepcopy(self.initial_state)

        for i, entry in enumerate(session_log.entries):
            # Skip retracted intents (no result to verify)
            if entry.result is None:
                continue

            # Reset RNG to the entry's initial offset
            rng_offset = entry.result.rng_initial_offset

            # Replay resolution
            try:
                replayed_result = self.resolver_fn(
                    entry.intent, current_state, rng
                )
            except Exception as e:
                return ReplayVerificationResult(
                    verified=False,
                    entries_checked=i,
                    divergence_index=i,
                    divergence_details=f"Resolver exception: {e}",
                    replay_time_ms=(time.perf_counter() - start_time) * 1000,
                )

            # Verify match
            matches, details = verify_result_match(entry.result, replayed_result)

            if not matches:
                return ReplayVerificationResult(
                    verified=False,
                    entries_checked=i + 1,
                    divergence_index=i,
                    divergence_details=details,
                    replay_time_ms=(time.perf_counter() - start_time) * 1000,
                )

            # Apply state changes if requested
            if apply_state_changes:
                for sc in entry.result.state_changes:
                    if sc.entity_id in current_state.entities:
                        current_state.entities[sc.entity_id][sc.field] = sc.new_value

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return ReplayVerificationResult(
            verified=True,
            entries_checked=len(session_log.entries),
            replay_time_ms=elapsed_ms,
        )

    def verify_10x(
        self,
        session_log: SessionLog,
    ) -> Tuple[bool, List[ReplayVerificationResult]]:
        """Run 10× replay verification.

        Per M1 requirements, identical inputs must produce identical outputs
        across 10 replay runs.

        Returns:
            Tuple of (all_passed, list_of_results)
        """
        results = []

        for run in range(10):
            result = self.replay_session(session_log)
            results.append(result)

            if not result.verified:
                return False, results

        return True, results


def create_test_resolver():
    """Create a simple test resolver for demos.

    This is a stub resolver that just returns success for any intent.
    Real resolvers would implement actual game logic.
    """
    from aidm.schemas.engine_result import EngineResultBuilder

    def test_resolver(
        intent: IntentObject,
        world_state: WorldState,
        rng: RNGManager,
    ) -> EngineResult:
        # Get the combat stream and track RNG usage
        combat_rng = rng.stream("combat")
        initial_offset = combat_rng.call_count

        builder = EngineResultBuilder(
            intent_id=intent.intent_id,
            rng_offset=initial_offset,
        )

        # Simple attack resolution
        if intent.action_type.value == "attack":
            # Roll attack (1d20)
            attack_roll = combat_rng.randint(1, 20)
            builder.add_roll(
                roll_type="attack",
                dice="1d20",
                natural_roll=attack_roll,
                modifiers=5,  # Stub modifier
                total=attack_roll + 5,
            )

            # Determine hit (AC 15 stub)
            hit = (attack_roll + 5) >= 15

            if hit:
                # Roll damage (1d8)
                damage_roll = combat_rng.randint(1, 8)
                builder.add_roll(
                    roll_type="damage",
                    dice="1d8",
                    natural_roll=damage_roll,
                    modifiers=3,
                    total=damage_roll + 3,
                )

                if intent.target_id:
                    target = world_state.entities.get(intent.target_id, {})
                    old_hp = target.get("hp", 20)
                    builder.add_state_change(
                        entity_id=intent.target_id,
                        field="hp",
                        old_value=old_hp,
                        new_value=old_hp - (damage_roll + 3),
                    )

                builder.set_narration_token("attack_hit")
            else:
                builder.set_narration_token("attack_miss")

            builder.add_event({
                "type": "attack_roll",
                "hit": hit,
                "natural": attack_roll,
            })

        else:
            # Default: just mark as resolved
            builder.set_narration_token("action_complete")

        return builder.build()

    return test_resolver
