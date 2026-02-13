"""M1 Runtime Session Manager for Intent → Result → Log flow.

Implements the M1 execution model from IPC_CONTRACT.md Section 6:
1. Create intent from input
2. Clarify if needed (blocking)
3. Freeze intent on confirmation
4. Resolve via Engine (produces EngineResult)
5. Log intent + result (authoritative)
6. Apply state changes
7. Narrate (non-authoritative)
8. Update UI

This module provides:
- RuntimeSession: Manages single session lifecycle
- IntentEntry: Logged intent with resolution
- SessionLog: Append-only session record
- ReplayVerifier: 10× replay verification

Reference: docs/runtime/IPC_CONTRACT.md
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple
import json
from pathlib import Path

from aidm.schemas.intent_lifecycle import (
    IntentObject,
    IntentStatus,
    ActionType,
    create_intent_from_input,
    IntentTransitionError,
)
from aidm.schemas.engine_result import (
    EngineResult,
    EngineResultStatus,
    EngineResultBuilder,
)
from aidm.core.state import WorldState
from aidm.core.rng_manager import RNGManager


@dataclass
class IntentEntry:
    """A logged intent with its resolution result.

    Captures the full lifecycle of a single player action:
    - The confirmed intent (frozen)
    - The engine result (immutable)
    - Timestamps for auditing
    """

    intent: IntentObject
    result: Optional[EngineResult]
    logged_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for logging."""
        return {
            "intent": self.intent.to_dict(),
            "result": self.result.to_dict() if self.result else None,
            "logged_at": self.logged_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IntentEntry":
        """Deserialize from log."""
        logged_at = data["logged_at"]
        if isinstance(logged_at, str):
            logged_at = datetime.fromisoformat(logged_at)

        return cls(
            intent=IntentObject.from_dict(data["intent"]),
            result=(
                EngineResult.from_dict(data["result"])
                if data.get("result")
                else None
            ),
            logged_at=logged_at,
        )


@dataclass
class SessionLog:
    """Append-only log of intent entries for a session.

    Provides:
    - Append-only semantics
    - JSONL serialization
    - Replay support
    """

    entries: List[IntentEntry] = field(default_factory=list)
    session_id: str = ""
    started_at: Optional[datetime] = None
    master_seed: int = 0

    def append(self, entry: IntentEntry) -> None:
        """Append an entry to the log.

        Validates that intent is CONFIRMED or RESOLVED before logging.
        """
        if entry.intent.status not in (
            IntentStatus.CONFIRMED,
            IntentStatus.RESOLVED,
            IntentStatus.RETRACTED,
        ):
            raise ValueError(
                f"Cannot log intent with status {entry.intent.status}. "
                "Only CONFIRMED, RESOLVED, or RETRACTED intents can be logged."
            )
        self.entries.append(entry)

    def to_jsonl(self, path: Path) -> None:
        """Serialize to JSONL file."""
        with open(path, "w", encoding="utf-8") as f:
            # Write header with session metadata
            header = {
                "_type": "session_header",
                "session_id": self.session_id,
                "started_at": self.started_at.isoformat() if self.started_at else "",
                "master_seed": self.master_seed,
            }
            json.dump(header, f, sort_keys=True)
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
            for line in f:
                line = line.strip()
                if not line:
                    continue

                data = json.loads(line)

                # Check for header
                if data.get("_type") == "session_header":
                    log.session_id = data.get("session_id", "")
                    log.master_seed = data.get("master_seed", 0)
                    started_at = data.get("started_at")
                    if isinstance(started_at, str):
                        log.started_at = datetime.fromisoformat(started_at)
                else:
                    # Parse as intent entry
                    entry = IntentEntry.from_dict(data)
                    log.entries.append(entry)

        return log

    def __len__(self) -> int:
        """Number of entries in log."""
        return len(self.entries)


# Type alias for engine resolver function
EngineResolver = Callable[
    [IntentObject, WorldState, RNGManager],
    Tuple[EngineResult, WorldState],
]


@dataclass
class RuntimeSession:
    """M1 runtime session manager.

    Coordinates the intent → result → log flow per IPC_CONTRACT.md.
    """

    world_state: WorldState
    rng: RNGManager
    log: SessionLog
    engine_resolver: Optional[EngineResolver] = None

    # Tracking
    _current_intent: Optional[IntentObject] = None

    @classmethod
    def create(
        cls,
        initial_state: WorldState,
        master_seed: int,
        session_id: str = "",
        engine_resolver: Optional[EngineResolver] = None,
    ) -> "RuntimeSession":
        """Create a new runtime session.

        Args:
            initial_state: Starting world state
            master_seed: RNG seed for determinism
            session_id: Optional session identifier
            engine_resolver: Function that resolves intents to results
        """
        return cls(
            world_state=initial_state,
            rng=RNGManager(master_seed),
            log=SessionLog(
                session_id=session_id,
                master_seed=master_seed,
            ),
            engine_resolver=engine_resolver,
        )

    def create_intent(
        self,
        actor_id: str,
        source_text: str,
        action_type: ActionType,
        intent_id: str,
        timestamp: datetime,
        **kwargs: Any,
    ) -> IntentObject:
        """Create a new intent from player input.

        The intent starts in PENDING status.

        Args:
            actor_id: Entity performing the action
            source_text: Original player input text
            action_type: Category of action
            intent_id: Unique ID (BL-017: must be injected)
            timestamp: Creation timestamp (BL-018: must be injected)
        """
        intent = create_intent_from_input(
            actor_id=actor_id,
            source_text=source_text,
            action_type=action_type,
            intent_id=intent_id,
            created_at=timestamp,
            **kwargs,
        )
        self._current_intent = intent
        return intent

    def needs_clarification(self, intent: IntentObject) -> bool:
        """Check if intent needs clarification."""
        return not intent.has_required_fields()

    def update_intent(
        self,
        intent: IntentObject,
        updates: Dict[str, Any],
        timestamp: datetime,
    ) -> IntentObject:
        """Update intent with clarification responses.

        Args:
            intent: The intent to update
            updates: Field updates from player
            timestamp: Current timestamp (BL-018: must be injected)

        Returns:
            Updated intent (same object, mutated in place)
        """
        if intent.is_frozen:
            raise IntentTransitionError("Cannot update frozen intent")

        for key, value in updates.items():
            if hasattr(intent, key):
                setattr(intent, key, value)

        intent.updated_at = timestamp
        return intent

    def confirm_intent(self, intent: IntentObject, timestamp: datetime) -> IntentObject:
        """Confirm intent, freezing it for resolution.

        Args:
            intent: The intent to confirm
            timestamp: Current timestamp (BL-018: must be injected)

        Returns:
            Confirmed (frozen) intent
        """
        if not intent.has_required_fields():
            raise IntentTransitionError(
                f"Cannot confirm intent with missing fields: {intent.get_missing_fields()}"
            )

        intent.transition_to(IntentStatus.CONFIRMED, timestamp=timestamp)
        return intent

    def retract_intent(self, intent: IntentObject, timestamp: datetime) -> IntentObject:
        """Retract an intent (player cancellation).

        Args:
            intent: The intent to retract
            timestamp: Current timestamp (BL-018: must be injected)

        Returns:
            Retracted intent
        """
        if intent.is_frozen:
            raise IntentTransitionError("Cannot retract frozen intent")

        intent.transition_to(IntentStatus.RETRACTED, timestamp=timestamp)

        # Log retracted intents for debugging
        entry = IntentEntry(intent=intent, result=None, logged_at=timestamp)
        self.log.append(entry)

        return intent

    def resolve(self, intent: IntentObject, timestamp: datetime) -> Tuple[EngineResult, str]:
        """Resolve a confirmed intent through the engine.

        Args:
            intent: Confirmed intent to resolve
            timestamp: Current timestamp (BL-018: must be injected)

        Returns:
            Tuple of (EngineResult, narration_token)
        """
        if intent.status != IntentStatus.CONFIRMED:
            raise IntentTransitionError(
                f"Can only resolve CONFIRMED intents, got {intent.status}"
            )

        if self.engine_resolver is None:
            raise RuntimeError("No engine resolver configured")

        # Resolve through engine
        result, new_state = self.engine_resolver(intent, self.world_state, self.rng)

        # Update intent with result reference.
        # The intent is frozen (CONFIRMED), so normal attribute assignment goes
        # through IntentObject.__setattr__ which permits only the resolution
        # fields.  We use object.__setattr__() explicitly to make it obvious
        # that we are writing to a frozen object on purpose and to guarantee
        # we never accidentally trigger descriptor / property side-effects.
        object.__setattr__(intent, "result_id", result.result_id)
        object.__setattr__(intent, "resolved_at", timestamp)
        # Transition status via the lifecycle guard so the valid-transition
        # check still fires.
        intent.transition_to(IntentStatus.RESOLVED, timestamp=timestamp)

        # Update world state
        self.world_state = new_state

        # Log the entry
        entry = IntentEntry(intent=intent, result=result, logged_at=timestamp)
        self.log.append(entry)

        # Return result and narration token
        narration_token = result.narration_token or ""
        return result, narration_token

    def process_input(
        self,
        actor_id: str,
        source_text: str,
        action_type: ActionType,
        intent_id: str,
        timestamp: datetime,
        result_id: str,
        get_clarification: Optional[Callable[[List[str]], Dict[str, Any]]] = None,
        **initial_fields: Any,
    ) -> Tuple[EngineResult, str]:
        """Process complete player input through the full pipeline.

        This is the main entry point that implements the IPC contract flow:
        1. Create intent
        2. Clarify if needed
        3. Confirm
        4. Resolve
        5. Log
        6. Return result + narration

        Args:
            actor_id: Entity performing the action
            source_text: Original player input
            action_type: Type of action
            intent_id: Unique ID for this intent (BL-017: must be injected)
            timestamp: Current timestamp (BL-018: must be injected)
            result_id: Unique ID for fallback result (BL-017: must be injected)
            get_clarification: Callback to get clarification responses
            **initial_fields: Initial field values

        Returns:
            Tuple of (EngineResult, narration_token)
        """
        # 1. Create intent
        intent = self.create_intent(
            actor_id=actor_id,
            source_text=source_text,
            action_type=action_type,
            intent_id=intent_id,
            timestamp=timestamp,
            **initial_fields,
        )

        # 2. Clarify if needed
        while self.needs_clarification(intent):
            missing = intent.get_missing_fields()

            if get_clarification is None:
                raise IntentTransitionError(
                    f"Intent requires clarification for: {missing}"
                )

            # Transition to CLARIFYING
            if intent.status == IntentStatus.PENDING:
                intent.transition_to(IntentStatus.CLARIFYING, timestamp=timestamp)

            # Get clarification
            updates = get_clarification(missing)

            if updates is None:
                # Player retracted
                retracted_intent = self.retract_intent(intent, timestamp=timestamp)
                # Build a proper EngineResult so return type matches signature
                # Use injected result_id (BL-017 compliant)
                builder = EngineResultBuilder(intent_id=retracted_intent.intent_id)
                result = builder.build(
                    result_id=result_id,
                    resolved_at=timestamp,
                    status=EngineResultStatus.FAILURE,
                    failure_reason="action_retracted",
                )
                return result, "action_retracted"

            # Apply updates
            self.update_intent(intent, updates, timestamp=timestamp)

        # 3. Confirm
        self.confirm_intent(intent, timestamp=timestamp)

        # 4-6. Resolve (includes logging)
        return self.resolve(intent, timestamp=timestamp)


@dataclass
class ReplayResult:
    """Result of replay verification."""

    success: bool
    """True if all replays matched."""

    replays_run: int
    """Number of replay iterations run."""

    divergences: List[str]
    """List of divergence descriptions if any."""

    final_state: WorldState
    """Final world state after replay."""


def replay_session(
    session_log: SessionLog,
    initial_state: WorldState,
    engine_resolver: EngineResolver,
) -> ReplayResult:
    """Replay a session log and verify determinism.

    Args:
        session_log: The session log to replay
        initial_state: Initial world state
        engine_resolver: Engine resolver function

    Returns:
        ReplayResult with verification status
    """
    rng = RNGManager(session_log.master_seed)
    state = initial_state
    divergences = []

    for i, entry in enumerate(session_log.entries):
        # Skip retracted intents
        if entry.intent.status == IntentStatus.RETRACTED:
            continue

        # Re-resolve the intent
        logged_result = entry.result
        if logged_result is None:
            divergences.append(f"Entry {i}: No logged result to verify")
            continue

        # Create a fresh intent for replay (read from logged data)
        replay_intent = IntentObject.from_dict(entry.intent.to_dict())

        # Replay resolution
        replay_result, new_state = engine_resolver(replay_intent, state, rng)

        # Verify determinism
        if replay_result.status != logged_result.status:
            divergences.append(
                f"Entry {i}: Status mismatch - "
                f"logged={logged_result.status.value}, "
                f"replay={replay_result.status.value}"
            )

        if replay_result.rng_final_offset != logged_result.rng_final_offset:
            divergences.append(
                f"Entry {i}: RNG offset mismatch - "
                f"logged={logged_result.rng_final_offset}, "
                f"replay={replay_result.rng_final_offset}"
            )

        # Verify rolls match
        if len(replay_result.rolls) != len(logged_result.rolls):
            divergences.append(
                f"Entry {i}: Roll count mismatch - "
                f"logged={len(logged_result.rolls)}, "
                f"replay={len(replay_result.rolls)}"
            )
        else:
            for j, (logged_roll, replay_roll) in enumerate(
                zip(logged_result.rolls, replay_result.rolls)
            ):
                if logged_roll.natural_roll != replay_roll.natural_roll:
                    divergences.append(
                        f"Entry {i} Roll {j}: Natural roll mismatch - "
                        f"logged={logged_roll.natural_roll}, "
                        f"replay={replay_roll.natural_roll}"
                    )

        state = new_state

    return ReplayResult(
        success=len(divergences) == 0,
        replays_run=len(session_log.entries),
        divergences=divergences,
        final_state=state,
    )


def verify_10x_replay(
    session_log: SessionLog,
    initial_state: WorldState,
    engine_resolver: EngineResolver,
) -> ReplayResult:
    """Run 10× replay verification as required by design doctrine.

    Runs the same session 10 times and verifies all produce identical results.

    Args:
        session_log: The session log to verify
        initial_state: Initial world state
        engine_resolver: Engine resolver function

    Returns:
        ReplayResult with combined verification status
    """
    all_divergences = []
    final_states = []

    for run in range(10):
        result = replay_session(session_log, initial_state, engine_resolver)

        if not result.success:
            for div in result.divergences:
                all_divergences.append(f"Run {run + 1}: {div}")

        final_states.append(result.final_state)

    # Verify all final states have same hash
    if final_states:
        first_hash = final_states[0].state_hash()
        for i, state in enumerate(final_states[1:], start=2):
            if state.state_hash() != first_hash:
                all_divergences.append(
                    f"Run {i}: Final state hash mismatch with Run 1"
                )

    return ReplayResult(
        success=len(all_divergences) == 0,
        replays_run=10,
        divergences=all_divergences,
        final_state=final_states[-1] if final_states else initial_state,
    )
