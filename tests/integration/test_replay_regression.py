"""Replay Regression Test Suite.

Tests for deterministic replay verification and Gold Master comparison.
Validates the 1000-turn determinism gate.

WO-018: Replay Regression Suite

Test Classes:
- TestGoldMasterRecording: Recording produces valid Gold Master
- TestReplayComparison: Replay matches Gold Master exactly
- TestThousandTurnGate: 1000-turn scenario replays deterministically
- TestDriftDetection: Drift detector finds first divergence
- TestCrossScenario: All 4 scenarios pass regression
- TestSerialization: Gold Master round-trips through JSONL
- TestRNGIsolation: Different streams don't cross-contaminate
- TestPersistedGoldMasters: Tests using pre-recorded Gold Masters
"""

import pytest
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import tempfile
import json

from aidm.schemas.testing import ScenarioConfig
from aidm.testing.replay_regression import (
    GoldMaster,
    DriftReport,
    ReplayResult,
    ReplayRegressionHarness,
    compute_event_log_hash,
    verify_gold_master_integrity,
    create_minimal_gold_master,
)
from aidm.testing.scenario_runner import ScenarioRunner


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def harness() -> ReplayRegressionHarness:
    """Create a fresh ReplayRegressionHarness instance."""
    return ReplayRegressionHarness()


@pytest.fixture
def temp_gold_master_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for Gold Master files."""
    gm_dir = tmp_path / "gold_masters"
    gm_dir.mkdir(parents=True, exist_ok=True)
    return gm_dir


@pytest.fixture
def gold_master_dir() -> Path:
    """Get the path to persisted Gold Master files."""
    return Path(__file__).parent.parent / "fixtures" / "gold_masters"


@pytest.fixture
def sample_events() -> List[Dict[str, Any]]:
    """Sample event list for testing."""
    return [
        {
            "event_id": 0,
            "event_type": "combat_started",
            "timestamp": 0.0,
            "payload": {"participants": ["fighter", "goblin"]},
            "rng_offset": 0,
            "citations": [],
        },
        {
            "event_id": 1,
            "event_type": "combat_round_started",
            "timestamp": 1.0,
            "payload": {"round_index": 1},
            "rng_offset": 0,
            "citations": [],
        },
        {
            "event_id": 2,
            "event_type": "attack_roll",
            "timestamp": 1.1,
            "payload": {"attacker": "fighter", "target": "goblin", "roll": 15},
            "rng_offset": 1,
            "citations": [],
        },
    ]


@pytest.fixture
def sample_gold_master(sample_events: List[Dict[str, Any]]) -> GoldMaster:
    """Sample Gold Master for testing."""
    return GoldMaster(
        scenario_name="test_scenario",
        seed=12345,
        turn_count=1,
        events=sample_events,
        final_state_hash="a" * 64,
        recorded_at=datetime.now(),
    )


# ==============================================================================
# TEST: GOLD MASTER RECORDING
# ==============================================================================

@pytest.mark.replay
class TestGoldMasterRecording:
    """Tests for recording Gold Master event logs."""

    def test_record_tavern_gold_master(
        self,
        tavern_scenario: ScenarioConfig,
        harness: ReplayRegressionHarness,
    ):
        """Recording tavern scenario produces valid Gold Master."""
        gold_master = harness.record_gold_master(
            tavern_scenario, turns=10, seed=42
        )

        assert gold_master.scenario_name == "Tavern Brawl"
        assert gold_master.seed == 42
        assert gold_master.turn_count >= 1
        assert len(gold_master.events) > 0
        assert len(gold_master.final_state_hash) == 64

    def test_record_dungeon_gold_master(
        self,
        dungeon_scenario: ScenarioConfig,
        harness: ReplayRegressionHarness,
    ):
        """Recording dungeon scenario produces valid Gold Master."""
        gold_master = harness.record_gold_master(
            dungeon_scenario, turns=10, seed=123
        )

        assert gold_master.scenario_name == "Dungeon Corridor"
        assert gold_master.seed == 123
        assert gold_master.turn_count >= 1
        assert len(gold_master.events) > 0

    def test_gold_master_has_initial_state(
        self,
        tavern_scenario: ScenarioConfig,
        harness: ReplayRegressionHarness,
    ):
        """Gold Master includes initial state for replay."""
        gold_master = harness.record_gold_master(
            tavern_scenario, turns=5, seed=42
        )

        assert gold_master.initial_state is not None
        assert "entities" in gold_master.initial_state

    def test_gold_master_has_scenario_config(
        self,
        tavern_scenario: ScenarioConfig,
        harness: ReplayRegressionHarness,
    ):
        """Gold Master includes scenario config for reference."""
        gold_master = harness.record_gold_master(
            tavern_scenario, turns=5, seed=42
        )

        assert gold_master.scenario_config is not None
        assert gold_master.scenario_config["name"] == "Tavern Brawl"

    def test_gold_master_event_count(
        self,
        tavern_scenario: ScenarioConfig,
        harness: ReplayRegressionHarness,
    ):
        """Gold Master event_count() matches events list length."""
        gold_master = harness.record_gold_master(
            tavern_scenario, turns=5, seed=42
        )

        assert gold_master.event_count() == len(gold_master.events)


# ==============================================================================
# TEST: REPLAY COMPARISON
# ==============================================================================

@pytest.mark.replay
class TestReplayComparison:
    """Tests for replaying and comparing against Gold Masters."""

    def test_replay_matches_gold_master(
        self,
        tavern_scenario: ScenarioConfig,
        harness: ReplayRegressionHarness,
    ):
        """Replay with same seed produces identical events."""
        gold_master = harness.record_gold_master(
            tavern_scenario, turns=10, seed=42
        )

        result = harness.replay_and_compare(gold_master)

        assert result.success, f"Replay failed: {result.drift_report}"
        assert result.final_state_hash == gold_master.final_state_hash

    def test_replay_detects_hash_mismatch(
        self,
        tavern_scenario: ScenarioConfig,
        harness: ReplayRegressionHarness,
    ):
        """Replay detects when final state hash doesn't match."""
        gold_master = harness.record_gold_master(
            tavern_scenario, turns=5, seed=42
        )

        # Corrupt the expected hash
        gold_master_corrupted = GoldMaster(
            scenario_name=gold_master.scenario_name,
            seed=gold_master.seed,
            turn_count=gold_master.turn_count,
            events=gold_master.events,
            final_state_hash="b" * 64,  # Wrong hash
            recorded_at=gold_master.recorded_at,
            initial_state=gold_master.initial_state,
            scenario_config=gold_master.scenario_config,
        )

        result = harness.replay_and_compare(gold_master_corrupted)

        assert not result.success
        assert result.drift_report is not None
        assert "hash mismatch" in result.drift_report.context.lower()

    def test_replay_processes_all_events(
        self,
        tavern_scenario: ScenarioConfig,
        harness: ReplayRegressionHarness,
    ):
        """Replay processes the expected number of events."""
        gold_master = harness.record_gold_master(
            tavern_scenario, turns=5, seed=42
        )

        result = harness.replay_and_compare(gold_master)

        assert result.events_processed == len(gold_master.events)

    def test_replay_handles_missing_initial_state(
        self,
        harness: ReplayRegressionHarness,
        sample_events: List[Dict[str, Any]],
    ):
        """Replay fails gracefully when initial_state is missing."""
        gold_master = GoldMaster(
            scenario_name="test",
            seed=42,
            turn_count=1,
            events=sample_events,
            final_state_hash="a" * 64,
            recorded_at=datetime.now(),
            initial_state=None,  # Missing
            scenario_config=None,
        )

        result = harness.replay_and_compare(gold_master)

        assert not result.success
        assert "initial_state" in result.drift_report.context


# ==============================================================================
# TEST: THOUSAND TURN GATE
# ==============================================================================

@pytest.mark.replay
class TestThousandTurnGate:
    """Tests for the 1000-turn determinism gate."""

    def test_tavern_thousand_turn_gate(
        self,
        tavern_scenario: ScenarioConfig,
        harness: ReplayRegressionHarness,
    ):
        """Tavern scenario passes 1000-turn determinism gate."""
        success, drift = harness.run_thousand_turn_gate(tavern_scenario, seed=42)

        assert success, f"1000-turn gate failed: {drift}"

    def test_dungeon_thousand_turn_gate(
        self,
        dungeon_scenario: ScenarioConfig,
        harness: ReplayRegressionHarness,
    ):
        """Dungeon scenario passes 1000-turn determinism gate."""
        success, drift = harness.run_thousand_turn_gate(dungeon_scenario, seed=123)

        assert success, f"1000-turn gate failed: {drift}"

    def test_field_thousand_turn_gate(
        self,
        field_battle_scenario: ScenarioConfig,
        harness: ReplayRegressionHarness,
    ):
        """Field battle scenario passes 1000-turn determinism gate."""
        success, drift = harness.run_thousand_turn_gate(field_battle_scenario, seed=456)

        assert success, f"1000-turn gate failed: {drift}"

    def test_boss_thousand_turn_gate(
        self,
        boss_fight_scenario: ScenarioConfig,
        harness: ReplayRegressionHarness,
    ):
        """Boss fight scenario passes 1000-turn determinism gate."""
        success, drift = harness.run_thousand_turn_gate(boss_fight_scenario, seed=789)

        assert success, f"1000-turn gate failed: {drift}"


# ==============================================================================
# TEST: DRIFT DETECTION
# ==============================================================================

@pytest.mark.replay
class TestDriftDetection:
    """Tests for drift detection between event logs."""

    def test_detect_no_drift_identical_logs(
        self,
        harness: ReplayRegressionHarness,
        sample_events: List[Dict[str, Any]],
    ):
        """No drift detected for identical event logs."""
        drift = harness.detect_drift(sample_events, sample_events.copy())

        assert not drift.has_drift

    def test_detect_drift_different_event_type(
        self,
        harness: ReplayRegressionHarness,
        sample_events: List[Dict[str, Any]],
    ):
        """Drift detected when event type differs."""
        modified = [e.copy() for e in sample_events]
        modified[1] = {**modified[1], "event_type": "different_type"}

        drift = harness.detect_drift(sample_events, modified)

        assert drift.has_drift
        assert drift.event_index == 1
        assert drift.field_that_differs == "event_type"
        assert drift.expected_value == "combat_round_started"
        assert drift.actual_value == "different_type"

    def test_detect_drift_different_payload(
        self,
        harness: ReplayRegressionHarness,
        sample_events: List[Dict[str, Any]],
    ):
        """Drift detected when payload differs."""
        modified = [e.copy() for e in sample_events]
        modified[2] = {
            **modified[2],
            "payload": {"attacker": "fighter", "target": "goblin", "roll": 20},
        }

        drift = harness.detect_drift(sample_events, modified)

        assert drift.has_drift
        assert drift.event_index == 2
        assert "payload" in drift.field_that_differs
        assert "roll" in drift.field_that_differs

    def test_detect_drift_length_mismatch(
        self,
        harness: ReplayRegressionHarness,
        sample_events: List[Dict[str, Any]],
    ):
        """Drift detected when event log lengths differ."""
        shorter = sample_events[:2]

        drift = harness.detect_drift(sample_events, shorter)

        assert drift.has_drift
        assert drift.field_that_differs == "event_count"
        assert drift.expected_value == 3
        assert drift.actual_value == 2

    def test_detect_drift_extra_events(
        self,
        harness: ReplayRegressionHarness,
        sample_events: List[Dict[str, Any]],
    ):
        """Drift detected when actual has extra events."""
        longer = sample_events + [{
            "event_id": 3,
            "event_type": "extra_event",
            "timestamp": 2.0,
            "payload": {},
            "rng_offset": 0,
            "citations": [],
        }]

        drift = harness.detect_drift(sample_events, longer)

        assert drift.has_drift
        assert drift.field_that_differs == "event_count"

    def test_drift_report_includes_turn_number(
        self,
        harness: ReplayRegressionHarness,
        sample_events: List[Dict[str, Any]],
    ):
        """Drift report includes turn number for context."""
        modified = [e.copy() for e in sample_events]
        modified[2] = {**modified[2], "event_type": "wrong_type"}

        drift = harness.detect_drift(sample_events, modified)

        assert drift.has_drift
        assert drift.turn_number == 1  # After combat_round_started

    def test_drift_report_str_representation(
        self,
        harness: ReplayRegressionHarness,
        sample_events: List[Dict[str, Any]],
    ):
        """Drift report has human-readable string representation."""
        modified = [e.copy() for e in sample_events]
        modified[1] = {**modified[1], "event_type": "wrong"}

        drift = harness.detect_drift(sample_events, modified)

        drift_str = str(drift)
        assert "DRIFT DETECTED" in drift_str
        assert "turn" in drift_str.lower()
        assert "event_type" in drift_str


# ==============================================================================
# TEST: CROSS-SCENARIO REGRESSION
# ==============================================================================

@pytest.mark.replay
class TestCrossScenario:
    """Tests that all scenarios pass regression."""

    def test_all_scenarios_record_valid_gold_masters(
        self,
        tavern_scenario: ScenarioConfig,
        dungeon_scenario: ScenarioConfig,
        field_battle_scenario: ScenarioConfig,
        boss_fight_scenario: ScenarioConfig,
        harness: ReplayRegressionHarness,
    ):
        """All 4 scenarios produce valid Gold Master recordings."""
        scenarios = [
            ("Tavern", tavern_scenario, 42),
            ("Dungeon", dungeon_scenario, 123),
            ("Field", field_battle_scenario, 456),
            ("Boss", boss_fight_scenario, 789),
        ]

        for name, scenario, seed in scenarios:
            gold_master = harness.record_gold_master(scenario, turns=10, seed=seed)

            assert gold_master.scenario_name, f"{name} missing scenario_name"
            assert gold_master.seed == seed, f"{name} seed mismatch"
            assert gold_master.turn_count >= 1, f"{name} no turns recorded"
            assert len(gold_master.events) > 0, f"{name} no events"
            assert len(gold_master.final_state_hash) == 64, f"{name} invalid hash"

    def test_all_scenarios_replay_deterministically(
        self,
        tavern_scenario: ScenarioConfig,
        dungeon_scenario: ScenarioConfig,
        field_battle_scenario: ScenarioConfig,
        boss_fight_scenario: ScenarioConfig,
        harness: ReplayRegressionHarness,
    ):
        """All 4 scenarios replay with identical results."""
        scenarios = [
            ("Tavern", tavern_scenario, 42),
            ("Dungeon", dungeon_scenario, 123),
            ("Field", field_battle_scenario, 456),
            ("Boss", boss_fight_scenario, 789),
        ]

        for name, scenario, seed in scenarios:
            gold_master = harness.record_gold_master(scenario, turns=10, seed=seed)
            result = harness.replay_and_compare(gold_master)

            assert result.success, f"{name} replay failed: {result.drift_report}"


# ==============================================================================
# TEST: SERIALIZATION
# ==============================================================================

@pytest.mark.replay
class TestSerialization:
    """Tests for Gold Master serialization."""

    def test_serialize_and_load_gold_master(
        self,
        tavern_scenario: ScenarioConfig,
        harness: ReplayRegressionHarness,
        temp_gold_master_dir: Path,
    ):
        """Gold Master round-trips through JSONL serialization."""
        original = harness.record_gold_master(
            tavern_scenario, turns=5, seed=42
        )

        path = temp_gold_master_dir / "test_tavern.jsonl"
        harness.serialize_gold_master(original, path)
        loaded = harness.load_gold_master(path)

        assert loaded.scenario_name == original.scenario_name
        assert loaded.seed == original.seed
        assert loaded.turn_count == original.turn_count
        assert loaded.final_state_hash == original.final_state_hash
        assert len(loaded.events) == len(original.events)

    def test_serialized_events_match_original(
        self,
        tavern_scenario: ScenarioConfig,
        harness: ReplayRegressionHarness,
        temp_gold_master_dir: Path,
    ):
        """Serialized events are identical to original."""
        original = harness.record_gold_master(
            tavern_scenario, turns=5, seed=42
        )

        path = temp_gold_master_dir / "test_events.jsonl"
        harness.serialize_gold_master(original, path)
        loaded = harness.load_gold_master(path)

        for i, (orig_event, loaded_event) in enumerate(zip(
            original.events, loaded.events
        )):
            orig_json = json.dumps(orig_event, sort_keys=True)
            loaded_json = json.dumps(loaded_event, sort_keys=True)
            assert orig_json == loaded_json, f"Event {i} differs"

    def test_serialized_gold_master_is_human_readable(
        self,
        tavern_scenario: ScenarioConfig,
        harness: ReplayRegressionHarness,
        temp_gold_master_dir: Path,
    ):
        """Serialized Gold Master file is human-readable JSONL."""
        gold_master = harness.record_gold_master(
            tavern_scenario, turns=3, seed=42
        )

        path = temp_gold_master_dir / "readable.jsonl"
        harness.serialize_gold_master(gold_master, path)

        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # First line is header
        header = json.loads(lines[0])
        assert header["type"] == "gold_master_header"
        assert header["scenario_name"] == "Tavern Brawl"

        # Remaining lines are events
        for line in lines[1:]:
            event = json.loads(line.strip())
            assert "event_id" in event
            assert "event_type" in event

    def test_load_from_file_and_replay(
        self,
        tavern_scenario: ScenarioConfig,
        harness: ReplayRegressionHarness,
        temp_gold_master_dir: Path,
    ):
        """Load Gold Master from file and replay successfully."""
        original = harness.record_gold_master(
            tavern_scenario, turns=5, seed=42
        )

        path = temp_gold_master_dir / "replay_from_file.jsonl"
        harness.serialize_gold_master(original, path)

        result = harness.replay_from_gold_master_file(path)

        assert result.success, f"Replay from file failed: {result.drift_report}"

    def test_load_invalid_file_raises_error(
        self,
        harness: ReplayRegressionHarness,
        temp_gold_master_dir: Path,
    ):
        """Loading invalid Gold Master file raises ValueError."""
        path = temp_gold_master_dir / "invalid.jsonl"
        with open(path, "w") as f:
            f.write('{"not": "a_header"}\n')

        with pytest.raises(ValueError):
            harness.load_gold_master(path)

    def test_load_empty_file_raises_error(
        self,
        harness: ReplayRegressionHarness,
        temp_gold_master_dir: Path,
    ):
        """Loading empty Gold Master file raises ValueError."""
        path = temp_gold_master_dir / "empty.jsonl"
        path.touch()

        with pytest.raises(ValueError):
            harness.load_gold_master(path)

    def test_serialize_creates_parent_dirs(
        self,
        tavern_scenario: ScenarioConfig,
        harness: ReplayRegressionHarness,
        temp_gold_master_dir: Path,
    ):
        """Serialization creates parent directories if needed."""
        gold_master = harness.record_gold_master(
            tavern_scenario, turns=2, seed=42
        )

        nested_path = temp_gold_master_dir / "nested" / "dirs" / "test.jsonl"
        harness.serialize_gold_master(gold_master, nested_path)

        assert nested_path.exists()


# ==============================================================================
# TEST: RNG ISOLATION
# ==============================================================================

@pytest.mark.replay
class TestRNGIsolation:
    """Tests for RNG stream isolation."""

    def test_different_seeds_produce_different_results(
        self,
        tavern_scenario: ScenarioConfig,
        harness: ReplayRegressionHarness,
    ):
        """Different seeds produce different event logs."""
        gold_master_1 = harness.record_gold_master(
            tavern_scenario, turns=5, seed=42
        )
        gold_master_2 = harness.record_gold_master(
            tavern_scenario, turns=5, seed=99
        )

        # Final state hashes should differ
        assert gold_master_1.final_state_hash != gold_master_2.final_state_hash

    def test_same_seed_produces_identical_results(
        self,
        tavern_scenario: ScenarioConfig,
        harness: ReplayRegressionHarness,
    ):
        """Same seed always produces identical event logs."""
        gold_master_1 = harness.record_gold_master(
            tavern_scenario, turns=5, seed=42
        )
        gold_master_2 = harness.record_gold_master(
            tavern_scenario, turns=5, seed=42
        )

        # Final state hashes should be identical
        assert gold_master_1.final_state_hash == gold_master_2.final_state_hash
        assert len(gold_master_1.events) == len(gold_master_2.events)

    def test_rng_streams_dont_contaminate(
        self,
        tavern_scenario: ScenarioConfig,
        harness: ReplayRegressionHarness,
    ):
        """Different scenario runs don't contaminate RNG state."""
        # Run multiple scenarios
        gm1 = harness.record_gold_master(tavern_scenario, turns=3, seed=42)
        gm2 = harness.record_gold_master(tavern_scenario, turns=3, seed=99)
        gm3 = harness.record_gold_master(tavern_scenario, turns=3, seed=42)

        # First and third should be identical
        assert gm1.final_state_hash == gm3.final_state_hash
        assert gm1.final_state_hash != gm2.final_state_hash


# ==============================================================================
# TEST: UTILITY FUNCTIONS
# ==============================================================================

@pytest.mark.replay
class TestUtilityFunctions:
    """Tests for standalone utility functions."""

    def test_compute_event_log_hash(
        self,
        sample_events: List[Dict[str, Any]],
    ):
        """Event log hash is computed correctly."""
        hash1 = compute_event_log_hash(sample_events)
        hash2 = compute_event_log_hash(sample_events)

        assert len(hash1) == 64
        assert hash1 == hash2

    def test_compute_event_log_hash_differs_for_different_events(
        self,
        sample_events: List[Dict[str, Any]],
    ):
        """Different events produce different hashes."""
        modified = [e.copy() for e in sample_events]
        modified[0] = {**modified[0], "payload": {"different": "data"}}

        hash1 = compute_event_log_hash(sample_events)
        hash2 = compute_event_log_hash(modified)

        assert hash1 != hash2

    def test_verify_gold_master_integrity_valid(
        self,
        sample_gold_master: GoldMaster,
    ):
        """Valid Gold Master passes integrity check."""
        assert verify_gold_master_integrity(sample_gold_master)

    def test_verify_gold_master_integrity_invalid_hash(
        self,
        sample_events: List[Dict[str, Any]],
    ):
        """Gold Master with invalid hash fails integrity check."""
        invalid = GoldMaster(
            scenario_name="test",
            seed=42,
            turn_count=1,
            events=sample_events,
            final_state_hash="short",  # Invalid length
            recorded_at=datetime.now(),
        )

        assert not verify_gold_master_integrity(invalid)

    def test_verify_gold_master_integrity_missing_name(
        self,
        sample_events: List[Dict[str, Any]],
    ):
        """Gold Master with missing name fails integrity check."""
        invalid = GoldMaster(
            scenario_name="",
            seed=42,
            turn_count=1,
            events=sample_events,
            final_state_hash="a" * 64,
            recorded_at=datetime.now(),
        )

        assert not verify_gold_master_integrity(invalid)

    def test_create_minimal_gold_master(
        self,
        sample_events: List[Dict[str, Any]],
    ):
        """Minimal Gold Master is created correctly."""
        gm = create_minimal_gold_master(
            scenario_name="test",
            seed=42,
            events=sample_events,
            final_state_hash="a" * 64,
        )

        assert gm.scenario_name == "test"
        assert gm.seed == 42
        assert gm.turn_count == 1  # One combat_round_started event
        assert len(gm.events) == 3


# ==============================================================================
# TEST: GOLD MASTER DATACLASS
# ==============================================================================

@pytest.mark.replay
class TestGoldMasterDataclass:
    """Tests for GoldMaster dataclass methods."""

    def test_gold_master_to_dict(
        self,
        sample_gold_master: GoldMaster,
    ):
        """Gold Master serializes to dict correctly."""
        data = sample_gold_master.to_dict()

        assert data["scenario_name"] == "test_scenario"
        assert data["seed"] == 12345
        assert data["turn_count"] == 1
        assert len(data["events"]) == 3
        assert data["final_state_hash"] == "a" * 64

    def test_gold_master_from_dict(
        self,
        sample_gold_master: GoldMaster,
    ):
        """Gold Master deserializes from dict correctly."""
        data = sample_gold_master.to_dict()
        restored = GoldMaster.from_dict(data)

        assert restored.scenario_name == sample_gold_master.scenario_name
        assert restored.seed == sample_gold_master.seed
        assert restored.turn_count == sample_gold_master.turn_count
        assert len(restored.events) == len(sample_gold_master.events)

    def test_gold_master_roundtrip_dict(
        self,
        sample_gold_master: GoldMaster,
    ):
        """Gold Master round-trips through dict serialization."""
        data = sample_gold_master.to_dict()
        restored = GoldMaster.from_dict(data)
        data2 = restored.to_dict()

        # Compare JSON for determinism
        json1 = json.dumps(data, sort_keys=True)
        json2 = json.dumps(data2, sort_keys=True)
        assert json1 == json2


# ==============================================================================
# TEST: DRIFT REPORT DATACLASS
# ==============================================================================

@pytest.mark.replay
class TestDriftReportDataclass:
    """Tests for DriftReport dataclass."""

    def test_no_drift_report_str(self):
        """No-drift report has appropriate string representation."""
        report = DriftReport(has_drift=False)
        assert str(report) == "No drift detected"

    def test_drift_report_str_includes_details(self):
        """Drift report includes all relevant details."""
        report = DriftReport(
            has_drift=True,
            turn_number=5,
            event_index=42,
            field_that_differs="payload.roll",
            expected_value=15,
            actual_value=20,
            context="test context",
        )

        report_str = str(report)
        assert "turn 5" in report_str
        assert "event index 42" in report_str
        assert "payload.roll" in report_str
        assert "15" in report_str
        assert "20" in report_str
        assert "test context" in report_str


# ==============================================================================
# TEST: PERSISTED GOLD MASTERS
# ==============================================================================

@pytest.mark.replay
class TestPersistedGoldMasters:
    """Tests using pre-recorded Gold Master files.

    These tests load Gold Masters from tests/fixtures/gold_masters/ and
    verify that replaying with the same seed produces identical results.
    """

    def test_load_tavern_gold_master(
        self,
        harness: ReplayRegressionHarness,
        gold_master_dir: Path,
    ):
        """Tavern Gold Master loads successfully."""
        path = gold_master_dir / "tavern_100turn.jsonl"
        if not path.exists():
            pytest.skip("Gold Master file not found")

        gold_master = harness.load_gold_master(path)

        assert gold_master.scenario_name == "Tavern Brawl"
        assert gold_master.seed == 42
        assert len(gold_master.events) > 0

    def test_load_dungeon_gold_master(
        self,
        harness: ReplayRegressionHarness,
        gold_master_dir: Path,
    ):
        """Dungeon Gold Master loads successfully."""
        path = gold_master_dir / "dungeon_100turn.jsonl"
        if not path.exists():
            pytest.skip("Gold Master file not found")

        gold_master = harness.load_gold_master(path)

        assert gold_master.scenario_name == "Dungeon Corridor"
        assert gold_master.seed == 123
        assert len(gold_master.events) > 0

    def test_load_field_gold_master(
        self,
        harness: ReplayRegressionHarness,
        gold_master_dir: Path,
    ):
        """Field battle Gold Master loads successfully."""
        path = gold_master_dir / "field_100turn.jsonl"
        if not path.exists():
            pytest.skip("Gold Master file not found")

        gold_master = harness.load_gold_master(path)

        assert gold_master.scenario_name == "Open Field Battle"
        assert gold_master.seed == 456
        assert len(gold_master.events) > 0

    def test_load_boss_gold_master(
        self,
        harness: ReplayRegressionHarness,
        gold_master_dir: Path,
    ):
        """Boss fight Gold Master loads successfully."""
        path = gold_master_dir / "boss_100turn.jsonl"
        if not path.exists():
            pytest.skip("Gold Master file not found")

        gold_master = harness.load_gold_master(path)

        assert gold_master.scenario_name == "Boss Fight"
        assert gold_master.seed == 789
        assert len(gold_master.events) > 0

    def test_replay_tavern_gold_master(
        self,
        harness: ReplayRegressionHarness,
        gold_master_dir: Path,
    ):
        """Tavern Gold Master replays deterministically."""
        path = gold_master_dir / "tavern_100turn.jsonl"
        if not path.exists():
            pytest.skip("Gold Master file not found")

        result = harness.replay_from_gold_master_file(path)

        assert result.success, f"Tavern replay failed: {result.drift_report}"

    def test_replay_dungeon_gold_master(
        self,
        harness: ReplayRegressionHarness,
        gold_master_dir: Path,
    ):
        """Dungeon Gold Master replays deterministically."""
        path = gold_master_dir / "dungeon_100turn.jsonl"
        if not path.exists():
            pytest.skip("Gold Master file not found")

        result = harness.replay_from_gold_master_file(path)

        assert result.success, f"Dungeon replay failed: {result.drift_report}"

    def test_replay_field_gold_master(
        self,
        harness: ReplayRegressionHarness,
        gold_master_dir: Path,
    ):
        """Field battle Gold Master replays deterministically."""
        path = gold_master_dir / "field_100turn.jsonl"
        if not path.exists():
            pytest.skip("Gold Master file not found")

        result = harness.replay_from_gold_master_file(path)

        assert result.success, f"Field replay failed: {result.drift_report}"

    def test_replay_boss_gold_master(
        self,
        harness: ReplayRegressionHarness,
        gold_master_dir: Path,
    ):
        """Boss fight Gold Master replays deterministically."""
        path = gold_master_dir / "boss_100turn.jsonl"
        if not path.exists():
            pytest.skip("Gold Master file not found")

        result = harness.replay_from_gold_master_file(path)

        assert result.success, f"Boss replay failed: {result.drift_report}"

    def test_all_gold_masters_have_valid_integrity(
        self,
        harness: ReplayRegressionHarness,
        gold_master_dir: Path,
    ):
        """All persisted Gold Masters pass integrity verification."""
        files = [
            "tavern_100turn.jsonl",
            "dungeon_100turn.jsonl",
            "field_100turn.jsonl",
            "boss_100turn.jsonl",
        ]

        for filename in files:
            path = gold_master_dir / filename
            if not path.exists():
                pytest.skip(f"Gold Master file not found: {filename}")

            gold_master = harness.load_gold_master(path)
            assert verify_gold_master_integrity(gold_master), \
                f"{filename} failed integrity check"
