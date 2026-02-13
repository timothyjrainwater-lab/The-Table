"""WO-CODE-LOOP-001: Replay determinism test.

Verifies that running the exact same fixture + input 25 times produces
identical event logs (byte-identical JSONL) and identical narration
template selection.

PHB: Determinism is the foundation of replay and auditability.
"""

import json
import pytest

from aidm.core.event_log import EventLog
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.runtime.play_controller import (
    PlayOneTurnController,
    ScenarioFixture,
    build_simple_combat_fixture,
)


REPLAY_COUNT = 25


class TestReplayDeterminism:
    """Same input + same fixture → identical output, every time."""

    def _run_once(self, fixture: ScenarioFixture, text: str):
        """Run one turn and return (events_json, narration, hash_after)."""
        ctrl = PlayOneTurnController(event_log=EventLog())
        result = ctrl.play_turn(fixture, text)

        events_json = json.dumps(
            list(result.events),
            sort_keys=True,
            separators=(",", ":"),
        )
        return events_json, result.narration_text, result.state_hash_after

    @staticmethod
    def _build_move_fixture(master_seed: int = 42) -> ScenarioFixture:
        """Build a fixture with enemy far away (no AoO on step-move)."""
        entities = {
            "pc_fighter": {
                EF.ENTITY_ID: "pc_fighter",
                "name": "Aldric",
                EF.HP_CURRENT: 28, EF.HP_MAX: 28,
                EF.AC: 18, EF.ATTACK_BONUS: 6,
                EF.BAB: 3, EF.STR_MOD: 3, EF.DEX_MOD: 1,
                EF.TEAM: "party", EF.WEAPON: "longsword",
                "weapon_damage": "1d8",
                EF.POSITION: {"x": 3, "y": 3},
                EF.DEFEATED: False, EF.SIZE_CATEGORY: "medium",
            },
            "goblin_1": {
                EF.ENTITY_ID: "goblin_1",
                "name": "Goblin Warrior",
                EF.HP_CURRENT: 5, EF.HP_MAX: 5,
                EF.AC: 15, EF.ATTACK_BONUS: 3,
                EF.BAB: 1, EF.STR_MOD: 0, EF.DEX_MOD: 1,
                EF.TEAM: "monsters", EF.WEAPON: "shortbow",
                "weapon_damage": "1d4",
                EF.POSITION: {"x": 10, "y": 3},
                EF.DEFEATED: False, EF.SIZE_CATEGORY: "small",
            },
        }
        ws = WorldState(
            ruleset_version="3.5e",
            entities=entities,
            active_combat={
                "turn_counter": 0, "round_index": 0,
                "initiative_order": ["pc_fighter", "goblin_1"],
                "flat_footed_actors": [], "aoo_used_this_round": [],
            },
        )
        return ScenarioFixture(
            world_state=ws, master_seed=master_seed,
            actor_id="pc_fighter", turn_index=0,
            next_event_id=0, timestamp=0.0,
        )

    def test_attack_determinism_25_runs(self):
        """Attack scenario produces identical results across 25 runs."""
        fixture = build_simple_combat_fixture(master_seed=42)
        baseline_events, baseline_narration, baseline_hash = self._run_once(
            fixture, "attack the goblin",
        )

        for i in range(1, REPLAY_COUNT):
            events, narration, state_hash = self._run_once(
                fixture, "attack the goblin",
            )
            assert events == baseline_events, (
                f"Run {i}: event log differs from baseline"
            )
            assert narration == baseline_narration, (
                f"Run {i}: narration differs from baseline"
            )
            assert state_hash == baseline_hash, (
                f"Run {i}: state hash differs from baseline"
            )

    def test_move_determinism_25_runs(self):
        """Move scenario produces identical results across 25 runs."""
        fixture = self._build_move_fixture(master_seed=42)
        baseline_events, baseline_narration, baseline_hash = self._run_once(
            fixture, "move 4 4",
        )

        for i in range(1, REPLAY_COUNT):
            events, narration, state_hash = self._run_once(
                self._build_move_fixture(master_seed=42), "move 4 4",
            )
            assert events == baseline_events, (
                f"Run {i}: event log differs from baseline"
            )
            assert narration == baseline_narration, (
                f"Run {i}: narration differs from baseline"
            )
            assert state_hash == baseline_hash, (
                f"Run {i}: state hash differs from baseline"
            )

    def test_end_turn_determinism_25_runs(self):
        """End-turn produces identical results across 25 runs."""
        fixture = build_simple_combat_fixture(master_seed=42)
        baseline_events, baseline_narration, baseline_hash = self._run_once(
            fixture, "end turn",
        )

        for i in range(1, REPLAY_COUNT):
            events, narration, state_hash = self._run_once(
                fixture, "end turn",
            )
            assert events == baseline_events, (
                f"Run {i}: event log differs from baseline"
            )
            assert narration == baseline_narration, (
                f"Run {i}: narration differs from baseline"
            )
            assert state_hash == baseline_hash, (
                f"Run {i}: state hash differs from baseline"
            )

    def test_different_seeds_produce_different_results(self):
        """Different seeds should produce different attack outcomes."""
        results = set()
        for seed in range(10):
            fixture = build_simple_combat_fixture(master_seed=seed)
            events, _, _ = self._run_once(fixture, "attack the goblin")
            results.add(events)

        # With 10 different seeds, we should get at least 2 distinct outcomes
        # (some hits, some misses)
        assert len(results) >= 2, (
            "10 different seeds all produced identical results — "
            "RNG is likely not being consumed"
        )

    def test_event_log_jsonl_byte_identical(self, tmp_path):
        """JSONL serialization is byte-identical across runs."""
        fixture = build_simple_combat_fixture(master_seed=42)

        ctrl_a = PlayOneTurnController(event_log=EventLog())
        ctrl_a.play_turn(fixture, "attack the goblin")
        path_a = tmp_path / "events_a.jsonl"
        ctrl_a.event_log.to_jsonl(path_a)

        ctrl_b = PlayOneTurnController(event_log=EventLog())
        ctrl_b.play_turn(fixture, "attack the goblin")
        path_b = tmp_path / "events_b.jsonl"
        ctrl_b.event_log.to_jsonl(path_b)

        assert path_a.read_bytes() == path_b.read_bytes(), (
            "JSONL files are not byte-identical"
        )
