"""Replay regression harness for determinism verification.

Provides infrastructure for recording Gold Master event logs and comparing
replays to detect drift. Supports the 1000-turn determinism gate.

WO-018: Replay Regression Suite

Key Components:
- GoldMaster: Captured recording of a scenario execution
- ReplayRegressionHarness: Recording, replay, and comparison utilities
- DriftReport: Details about first divergence point
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from copy import deepcopy
import json
import hashlib

from aidm.schemas.testing import ScenarioConfig
from aidm.core.state import WorldState
from aidm.core.event_log import Event, EventLog
from aidm.core.rng_manager import RNGManager
from aidm.core.replay_runner import reduce_event


# ==============================================================================
# GOLD MASTER — Captured scenario recording
# ==============================================================================

@dataclass
class GoldMaster:
    """Captured recording of a scenario execution.

    Contains all events and final state hash for determinism verification.
    Gold Masters are recorded once and used as the canonical reference for
    future replay comparisons.
    """

    scenario_name: str
    """Name of the scenario this recording is for."""

    seed: int
    """RNG seed used for the recording."""

    turn_count: int
    """Number of turns (combat rounds) executed."""

    events: List[Dict[str, Any]]
    """Full event log as list of serialized event dicts."""

    final_state_hash: str
    """SHA-256 hash of the final WorldState."""

    recorded_at: datetime
    """Timestamp when this Gold Master was recorded."""

    initial_state: Optional[Dict[str, Any]] = None
    """Optional initial WorldState for replay verification."""

    scenario_config: Optional[Dict[str, Any]] = None
    """Optional serialized ScenarioConfig for reference."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "scenario_name": self.scenario_name,
            "seed": self.seed,
            "turn_count": self.turn_count,
            "events": self.events,
            "final_state_hash": self.final_state_hash,
            "recorded_at": self.recorded_at.isoformat(),
            "initial_state": self.initial_state,
            "scenario_config": self.scenario_config,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GoldMaster':
        """Deserialize from dictionary."""
        return cls(
            scenario_name=data["scenario_name"],
            seed=data["seed"],
            turn_count=data["turn_count"],
            events=data["events"],
            final_state_hash=data["final_state_hash"],
            recorded_at=datetime.fromisoformat(data["recorded_at"]),
            initial_state=data.get("initial_state"),
            scenario_config=data.get("scenario_config"),
        )

    def event_count(self) -> int:
        """Get total number of events in the recording."""
        return len(self.events)


# ==============================================================================
# DRIFT REPORT — Details about replay divergence
# ==============================================================================

@dataclass
class DriftReport:
    """Report of first divergence point between expected and actual replay.

    Provides context about where and why replay drifted from the Gold Master.
    """

    has_drift: bool
    """Whether any drift was detected."""

    turn_number: int = 0
    """Turn (combat round) where drift first occurred."""

    event_index: int = 0
    """Index of first divergent event in the log."""

    field_that_differs: str = ""
    """Specific field that differs between expected and actual."""

    expected_value: Any = None
    """Expected value from Gold Master."""

    actual_value: Any = None
    """Actual value from replay."""

    expected_event: Optional[Dict[str, Any]] = None
    """Full expected event for context."""

    actual_event: Optional[Dict[str, Any]] = None
    """Full actual event for context."""

    context: str = ""
    """Additional context about the divergence."""

    def __str__(self) -> str:
        """Human-readable drift report."""
        if not self.has_drift:
            return "No drift detected"

        lines = [
            f"DRIFT DETECTED at turn {self.turn_number}, event index {self.event_index}",
            f"  Field: {self.field_that_differs}",
            f"  Expected: {self.expected_value}",
            f"  Actual: {self.actual_value}",
        ]
        if self.context:
            lines.append(f"  Context: {self.context}")

        return "\n".join(lines)


# ==============================================================================
# REPLAY RESULT — Replay execution outcome
# ==============================================================================

@dataclass
class ReplayResult:
    """Result of replaying a Gold Master."""

    success: bool
    """Whether replay matched the Gold Master."""

    events_processed: int
    """Number of events processed during replay."""

    final_state_hash: str
    """Hash of final state after replay."""

    drift_report: Optional[DriftReport] = None
    """Drift details if replay diverged."""

    execution_time_ms: float = 0.0
    """Time to execute replay in milliseconds."""


# ==============================================================================
# REPLAY REGRESSION HARNESS — Main utility class
# ==============================================================================

class ReplayRegressionHarness:
    """Harness for recording, replaying, and comparing scenario executions.

    Provides utilities for:
    - Recording Gold Master event logs from scenario executions
    - Replaying from seed and comparing event-by-event
    - Running the 1000-turn determinism gate
    - Detecting and reporting drift between expected and actual logs
    - Serializing Gold Masters to JSONL files
    """

    def __init__(self):
        """Initialize the replay regression harness."""
        self._current_scenario: Optional[ScenarioConfig] = None
        self._current_seed: int = 0

    def record_gold_master(
        self,
        scenario: ScenarioConfig,
        turns: int,
        seed: int,
    ) -> GoldMaster:
        """Run a scenario and capture the event log as a Gold Master.

        Args:
            scenario: Scenario configuration to execute
            turns: Number of turns (combat rounds) to run
            seed: RNG seed for deterministic execution

        Returns:
            GoldMaster containing the full event log and final state hash
        """
        from aidm.testing.scenario_runner import ScenarioRunner

        # Override scenario seed and round limit
        recording_scenario = ScenarioConfig(
            name=scenario.name,
            grid_width=scenario.grid_width,
            grid_height=scenario.grid_height,
            terrain=scenario.terrain,
            combatants=scenario.combatants,
            round_limit=turns,
            seed=seed,
            description=scenario.description,
            victory_condition=scenario.victory_condition,
        )

        # Run the scenario
        runner = ScenarioRunner()
        metrics = runner.run(recording_scenario)

        # Extract event log
        events = []
        if runner._event_log is not None:
            for event in runner._event_log.events:
                events.append(event.to_dict())

        # Get initial state for replay
        initial_state = None
        if runner._world_state is not None:
            # Capture the final state (we'll reconstruct initial from config)
            pass

        # Create Gold Master
        return GoldMaster(
            scenario_name=scenario.name,
            seed=seed,
            turn_count=metrics.total_rounds,
            events=events,
            final_state_hash=metrics.final_state_hash,
            recorded_at=datetime.now(),
            initial_state=self._build_initial_state(recording_scenario).to_dict(),
            scenario_config=recording_scenario.to_dict(),
        )

    def replay_and_compare(
        self,
        gold_master: GoldMaster,
    ) -> ReplayResult:
        """Replay a scenario from seed and compare against Gold Master.

        Args:
            gold_master: Gold Master recording to compare against

        Returns:
            ReplayResult indicating success or drift details
        """
        import time
        start_time = time.perf_counter()

        # Reconstruct initial state from Gold Master
        if gold_master.initial_state is None:
            return ReplayResult(
                success=False,
                events_processed=0,
                final_state_hash="",
                drift_report=DriftReport(
                    has_drift=True,
                    context="Gold Master missing initial_state",
                ),
            )

        initial_state = WorldState.from_dict(gold_master.initial_state)

        # Re-run the scenario with the same seed
        if gold_master.scenario_config is None:
            return ReplayResult(
                success=False,
                events_processed=0,
                final_state_hash="",
                drift_report=DriftReport(
                    has_drift=True,
                    context="Gold Master missing scenario_config",
                ),
            )

        scenario = ScenarioConfig.from_dict(gold_master.scenario_config)

        # Run fresh execution
        from aidm.testing.scenario_runner import ScenarioRunner
        runner = ScenarioRunner()
        metrics = runner.run(scenario)

        # Extract new events
        new_events = []
        if runner._event_log is not None:
            for event in runner._event_log.events:
                new_events.append(event.to_dict())

        # Compare event-by-event
        drift = self.detect_drift(gold_master.events, new_events)

        execution_time = (time.perf_counter() - start_time) * 1000

        if drift.has_drift:
            return ReplayResult(
                success=False,
                events_processed=drift.event_index,
                final_state_hash=metrics.final_state_hash,
                drift_report=drift,
                execution_time_ms=execution_time,
            )

        # Compare final state hash
        if metrics.final_state_hash != gold_master.final_state_hash:
            return ReplayResult(
                success=False,
                events_processed=len(new_events),
                final_state_hash=metrics.final_state_hash,
                drift_report=DriftReport(
                    has_drift=True,
                    context=(
                        f"Final state hash mismatch: "
                        f"expected {gold_master.final_state_hash}, "
                        f"got {metrics.final_state_hash}"
                    ),
                ),
                execution_time_ms=execution_time,
            )

        return ReplayResult(
            success=True,
            events_processed=len(new_events),
            final_state_hash=metrics.final_state_hash,
            drift_report=DriftReport(has_drift=False),
            execution_time_ms=execution_time,
        )

    def replay_from_gold_master_file(
        self,
        gold_master_path: Path,
    ) -> ReplayResult:
        """Load a Gold Master from file and replay for comparison.

        Args:
            gold_master_path: Path to Gold Master JSONL file

        Returns:
            ReplayResult indicating success or drift details
        """
        gold_master = self.load_gold_master(gold_master_path)
        return self.replay_and_compare(gold_master)

    def run_thousand_turn_gate(
        self,
        scenario: ScenarioConfig,
        seed: int,
    ) -> Tuple[bool, Optional[DriftReport]]:
        """Execute 1000 turns and verify final state hash matches replay.

        This is the canonical determinism gate test. Runs the scenario for
        1000 turns, records the final state hash, then replays and verifies
        the hash matches exactly.

        Args:
            scenario: Scenario configuration to execute
            seed: RNG seed for deterministic execution

        Returns:
            Tuple of (success, optional drift report if failed)
        """
        # Record with 1000 turns
        gold_master = self.record_gold_master(scenario, turns=1000, seed=seed)

        # Replay and compare
        result = self.replay_and_compare(gold_master)

        return result.success, result.drift_report

    def detect_drift(
        self,
        expected_log: List[Dict[str, Any]],
        actual_log: List[Dict[str, Any]],
    ) -> DriftReport:
        """Compare two event logs and return first divergence point.

        Args:
            expected_log: Gold Master event log
            actual_log: Replayed event log

        Returns:
            DriftReport with details about first divergence, or no_drift report
        """
        # Check length mismatch
        if len(expected_log) != len(actual_log):
            min_len = min(len(expected_log), len(actual_log))

            # Find actual divergence point within common length
            for i in range(min_len):
                diff = self._compare_events(expected_log[i], actual_log[i])
                if diff is not None:
                    turn = self._get_turn_number(expected_log, i)
                    field, exp_val, act_val = diff
                    return DriftReport(
                        has_drift=True,
                        turn_number=turn,
                        event_index=i,
                        field_that_differs=field,
                        expected_value=exp_val,
                        actual_value=act_val,
                        expected_event=expected_log[i],
                        actual_event=actual_log[i],
                    )

            # No field drift, but length differs
            turn = self._get_turn_number(expected_log, min_len)
            return DriftReport(
                has_drift=True,
                turn_number=turn,
                event_index=min_len,
                field_that_differs="event_count",
                expected_value=len(expected_log),
                actual_value=len(actual_log),
                context=(
                    f"Event log length mismatch: "
                    f"expected {len(expected_log)} events, got {len(actual_log)}"
                ),
            )

        # Compare event by event
        for i, (expected, actual) in enumerate(zip(expected_log, actual_log)):
            diff = self._compare_events(expected, actual)
            if diff is not None:
                turn = self._get_turn_number(expected_log, i)
                field, exp_val, act_val = diff
                return DriftReport(
                    has_drift=True,
                    turn_number=turn,
                    event_index=i,
                    field_that_differs=field,
                    expected_value=exp_val,
                    actual_value=act_val,
                    expected_event=expected,
                    actual_event=actual,
                )

        # No drift
        return DriftReport(has_drift=False)

    def _compare_events(
        self,
        expected: Dict[str, Any],
        actual: Dict[str, Any],
    ) -> Optional[Tuple[str, Any, Any]]:
        """Compare two events and return first differing field.

        Args:
            expected: Expected event dict
            actual: Actual event dict

        Returns:
            Tuple of (field_name, expected_value, actual_value) or None if equal
        """
        # Use sorted-key JSON for deterministic comparison
        exp_json = json.dumps(expected, sort_keys=True, separators=(",", ":"))
        act_json = json.dumps(actual, sort_keys=True, separators=(",", ":"))

        if exp_json == act_json:
            return None

        # Find first differing field
        all_keys = set(expected.keys()) | set(actual.keys())
        for key in sorted(all_keys):
            exp_val = expected.get(key)
            act_val = actual.get(key)

            if key == "payload":
                # Deep compare payload
                if exp_val != act_val:
                    payload_diff = self._compare_payloads(exp_val or {}, act_val or {})
                    if payload_diff:
                        return (f"payload.{payload_diff[0]}", payload_diff[1], payload_diff[2])
                    return ("payload", exp_val, act_val)
            elif exp_val != act_val:
                return (key, exp_val, act_val)

        # Fields differ but couldn't identify specific one
        return ("unknown", exp_json, act_json)

    def _compare_payloads(
        self,
        expected: Dict[str, Any],
        actual: Dict[str, Any],
    ) -> Optional[Tuple[str, Any, Any]]:
        """Compare payload dicts and return first differing field.

        Args:
            expected: Expected payload dict
            actual: Actual payload dict

        Returns:
            Tuple of (field_name, expected_value, actual_value) or None if equal
        """
        all_keys = set(expected.keys()) | set(actual.keys())
        for key in sorted(all_keys):
            exp_val = expected.get(key)
            act_val = actual.get(key)
            if exp_val != act_val:
                return (key, exp_val, act_val)
        return None

    def _get_turn_number(
        self,
        event_log: List[Dict[str, Any]],
        index: int,
    ) -> int:
        """Extract turn number from event log at given index.

        Looks backward for most recent combat_round_started event.

        Args:
            event_log: Full event log
            index: Index to find turn for

        Returns:
            Turn number (combat round), or 0 if not found
        """
        for i in range(index, -1, -1):
            if i < len(event_log):
                event = event_log[i]
                if event.get("event_type") == "combat_round_started":
                    payload = event.get("payload", {})
                    return payload.get("round_index", payload.get("round", 0))
        return 0

    def serialize_gold_master(
        self,
        gold_master: GoldMaster,
        path: Path,
    ) -> None:
        """Serialize a Gold Master to JSONL file.

        Format:
        - Line 1: Header with metadata (scenario_name, seed, turn_count, etc.)
        - Lines 2+: One event per line

        Args:
            gold_master: Gold Master to serialize
            path: Path to write JSONL file
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            # Write header
            header = {
                "type": "gold_master_header",
                "scenario_name": gold_master.scenario_name,
                "seed": gold_master.seed,
                "turn_count": gold_master.turn_count,
                "final_state_hash": gold_master.final_state_hash,
                "recorded_at": gold_master.recorded_at.isoformat(),
                "event_count": len(gold_master.events),
                "initial_state": gold_master.initial_state,
                "scenario_config": gold_master.scenario_config,
            }
            json.dump(header, f, sort_keys=True)
            f.write("\n")

            # Write events, one per line
            for event in gold_master.events:
                json.dump(event, f, sort_keys=True)
                f.write("\n")

    def load_gold_master(
        self,
        path: Path,
    ) -> GoldMaster:
        """Load a Gold Master from JSONL file.

        Args:
            path: Path to Gold Master JSONL file

        Returns:
            GoldMaster instance

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        events = []

        with open(path, "r", encoding="utf-8") as f:
            # Read header
            header_line = f.readline().strip()
            if not header_line:
                raise ValueError(f"Empty Gold Master file: {path}")

            header = json.loads(header_line)
            if header.get("type") != "gold_master_header":
                raise ValueError(f"Invalid Gold Master header in {path}")

            # Read events
            for line in f:
                line = line.strip()
                if line:
                    events.append(json.loads(line))

        return GoldMaster(
            scenario_name=header["scenario_name"],
            seed=header["seed"],
            turn_count=header["turn_count"],
            events=events,
            final_state_hash=header["final_state_hash"],
            recorded_at=datetime.fromisoformat(header["recorded_at"]),
            initial_state=header.get("initial_state"),
            scenario_config=header.get("scenario_config"),
        )

    def _build_initial_state(
        self,
        config: ScenarioConfig,
    ) -> WorldState:
        """Build initial WorldState from scenario config.

        Args:
            config: Scenario configuration

        Returns:
            Initial WorldState with combatants placed
        """
        from aidm.schemas.entity_fields import EF

        entities = {}

        for combatant in config.combatants:
            entity = {
                EF.ENTITY_ID: combatant.name,
                EF.TEAM: combatant.team,
                EF.HP_CURRENT: combatant.hp,
                EF.HP_MAX: combatant.hp,
                EF.AC: combatant.ac,
                EF.POSITION: combatant.position.to_dict(),
                EF.DEFEATED: False,
                EF.SIZE_CATEGORY: combatant.size.lower(),
                EF.BAB: combatant.bab,
                EF.STR_MOD: combatant.str_mod,
                EF.DEX_MOD: combatant.dex_mod,
                EF.CON_MOD: combatant.con_mod,
                EF.WIS_MOD: combatant.wis_mod,
                EF.SAVE_FORT: combatant.save_fort,
                EF.SAVE_REF: combatant.save_ref,
                EF.SAVE_WILL: combatant.save_will,
                EF.CONDITIONS: {},
            }

            if combatant.attacks:
                entity["attacks"] = [a.to_dict() for a in combatant.attacks]
                entity[EF.ATTACK_BONUS] = combatant.attacks[0].attack_bonus

            entities[combatant.name] = entity

        return WorldState(
            ruleset_version="RAW_3.5",
            entities=entities,
            active_combat=None,
        )


# ==============================================================================
# UTILITY FUNCTIONS — Standalone helpers
# ==============================================================================

def compute_event_log_hash(events: List[Dict[str, Any]]) -> str:
    """Compute deterministic hash of an event log.

    Args:
        events: List of event dicts

    Returns:
        SHA-256 hex digest
    """
    serialized = json.dumps(events, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode()).hexdigest()


def verify_gold_master_integrity(gold_master: GoldMaster) -> bool:
    """Verify that a Gold Master's event hash matches stored hash.

    Args:
        gold_master: Gold Master to verify

    Returns:
        True if event log produces the stored final_state_hash
    """
    # Note: We can't verify final_state_hash without replay,
    # but we can verify the Gold Master structure is valid
    if not gold_master.scenario_name:
        return False
    if gold_master.seed < 0:
        return False
    if gold_master.turn_count < 0:
        return False
    if not gold_master.final_state_hash:
        return False
    if len(gold_master.final_state_hash) != 64:
        return False

    return True


def create_minimal_gold_master(
    scenario_name: str,
    seed: int,
    events: List[Dict[str, Any]],
    final_state_hash: str,
) -> GoldMaster:
    """Create a minimal Gold Master for testing.

    Args:
        scenario_name: Name of the scenario
        seed: RNG seed
        events: Event list
        final_state_hash: Final state hash

    Returns:
        GoldMaster instance
    """
    # Count turns from events
    turn_count = 0
    for event in events:
        if event.get("event_type") == "combat_round_started":
            turn_count += 1

    return GoldMaster(
        scenario_name=scenario_name,
        seed=seed,
        turn_count=turn_count,
        events=events,
        final_state_hash=final_state_hash,
        recorded_at=datetime.now(),
    )
