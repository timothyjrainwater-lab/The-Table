"""P1: Integration-Layer Replay Stability Tests

Proves that the orchestrator integration layer produces stable, deterministic
outputs at contract boundaries. This is NOT full replay_runner integration —
it validates that the orchestrator's extraction logic introduces no
nondeterminism.

Tests ensure:
1. Same seed + same commands → identical event payloads (not just state hash)
2. NarrativeBrief round-trip serialization preserves all fields
3. Event ordering invariants hold (turn_start first, turn_end last, causal order)
4. Multi-turn sequences produce identical event sequences across runs
5. Event extraction logic doesn't introduce nondeterminism

Test Categories:
1. Event Payload Equality (4 tests)
2. NarrativeBrief Serialization Round-Trip (4 tests)
3. Event Ordering Invariants (5 tests)

Total: 13 tests
"""

import json
import pytest

from aidm.core.rng_manager import RNGManager
from aidm.core.state import WorldState
from aidm.interaction.intent_bridge import IntentBridge
from aidm.lens.context_assembler import ContextAssembler
from aidm.lens.narrative_brief import NarrativeBrief, compute_severity
from aidm.lens.scene_manager import Exit, SceneManager, SceneState
from aidm.narration.guarded_narration_service import GuardedNarrationService
from aidm.runtime.session_orchestrator import SessionOrchestrator, TurnResult
from aidm.schemas.entity_fields import EF
from aidm.spark.dm_persona import DMPersona


# ======================================================================
# FIXTURES
# ======================================================================


def _make_orchestrator(seed, goblin_hp=100, goblin_ac=10, attack_bonus=10):
    """Factory for deterministic orchestrator instances."""
    ws = WorldState(
        ruleset_version="RAW_3.5",
        entities={
            "pc_fighter": {
                EF.ENTITY_ID: "pc_fighter",
                "name": "Kael",
                EF.TEAM: "party",
                EF.LEVEL: 5,
                EF.HP_CURRENT: 50,
                EF.HP_MAX: 50,
                EF.AC: 16,
                EF.DEFEATED: False,
                EF.ATTACK_BONUS: attack_bonus,
                EF.BAB: 8,
                EF.STR_MOD: 4,
                EF.WEAPON: "longsword",
                "weapon_damage": "1d8+4",
                EF.DEX_MOD: 2,
            },
            "goblin_1": {
                EF.ENTITY_ID: "goblin_1",
                "name": "Goblin Warrior",
                EF.TEAM: "enemy",
                EF.LEVEL: 1,
                EF.HP_CURRENT: goblin_hp,
                EF.HP_MAX: goblin_hp,
                EF.AC: goblin_ac,
                EF.DEFEATED: False,
                EF.ATTACK_BONUS: 2,
                EF.DEX_MOD: 1,
            },
        },
    )
    scenes = {
        "room_a": SceneState(
            scene_id="room_a",
            name="Room A",
            description="A room.",
            exits=[
                Exit(
                    exit_id="east",
                    destination_scene_id="room_b",
                    description="East",
                    locked=False,
                    hidden=False,
                ),
            ],
        ),
        "room_b": SceneState(
            scene_id="room_b",
            name="Room B",
            description="Another room.",
            exits=[],
        ),
    }
    return SessionOrchestrator(
        world_state=ws,
        intent_bridge=IntentBridge(),
        scene_manager=SceneManager(scenes=scenes),
        dm_persona=DMPersona(),
        narration_service=GuardedNarrationService(),
        context_assembler=ContextAssembler(token_budget=800),
        master_seed=seed,
    )


# ======================================================================
# CATEGORY 1: EVENT PAYLOAD EQUALITY (4 tests)
# ======================================================================


class TestEventPayloadEquality:
    """Same seed + same commands → identical event payloads."""

    def test_single_attack_payload_equality(self):
        """Same seed → identical event payloads (full dict comparison)."""
        orch_a = _make_orchestrator(seed=42)
        orch_b = _make_orchestrator(seed=42)

        result_a = orch_a.process_text_turn("attack Goblin Warrior", "pc_fighter")
        result_b = orch_b.process_text_turn("attack Goblin Warrior", "pc_fighter")

        assert len(result_a.events) == len(result_b.events)

        for i, (ea, eb) in enumerate(zip(result_a.events, result_b.events)):
            # Full payload equality — not just type matching
            assert ea == eb, (
                f"Event {i} payloads differ:\n"
                f"  A: {json.dumps(ea, sort_keys=True)}\n"
                f"  B: {json.dumps(eb, sort_keys=True)}"
            )

    def test_multi_turn_sequence_payload_equality(self):
        """Same seed + 3-turn sequence → identical event payloads across all turns."""
        commands = [
            ("attack Goblin Warrior", "pc_fighter"),
            ("attack Goblin Warrior", "pc_fighter"),
            ("move to 5,5", "pc_fighter"),
        ]

        orch_a = _make_orchestrator(seed=999)
        orch_b = _make_orchestrator(seed=999)

        for text, actor in commands:
            result_a = orch_a.process_text_turn(text, actor)
            result_b = orch_b.process_text_turn(text, actor)

            assert len(result_a.events) == len(result_b.events), (
                f"Event count differs for '{text}': "
                f"{len(result_a.events)} vs {len(result_b.events)}"
            )

            for i, (ea, eb) in enumerate(zip(result_a.events, result_b.events)):
                assert ea == eb, (
                    f"Event {i} in turn '{text}' differs:\n"
                    f"  A: {json.dumps(ea, sort_keys=True)}\n"
                    f"  B: {json.dumps(eb, sort_keys=True)}"
                )

        # Final state must match
        assert orch_a.world_state.state_hash() == orch_b.world_state.state_hash()

    def test_spell_turn_payload_equality(self):
        """Same seed → identical spell event payloads (excluding cast_id UUID).

        cast_id uses uuid.uuid4() in spell_resolver.py — non-deterministic by
        design (correlation ID, not gameplay value). All other fields must match.
        """
        # Known non-deterministic fields that are correlation IDs, not gameplay values
        NON_DETERMINISTIC_FIELDS = {"cast_id"}

        orch_a = _make_orchestrator(seed=77)
        orch_b = _make_orchestrator(seed=77)

        result_a = orch_a.process_text_turn("cast fireball at 10,5", "pc_fighter")
        result_b = orch_b.process_text_turn("cast fireball at 10,5", "pc_fighter")

        assert len(result_a.events) == len(result_b.events)

        for i, (ea, eb) in enumerate(zip(result_a.events, result_b.events)):
            # Strip non-deterministic correlation IDs before comparison
            ea_clean = {k: v for k, v in ea.items() if k not in NON_DETERMINISTIC_FIELDS}
            eb_clean = {k: v for k, v in eb.items() if k not in NON_DETERMINISTIC_FIELDS}
            assert ea_clean == eb_clean, (
                f"Spell event {i} differs (excluding {NON_DETERMINISTIC_FIELDS}):\n"
                f"  A: {json.dumps(ea_clean, sort_keys=True)}\n"
                f"  B: {json.dumps(eb_clean, sort_keys=True)}"
            )

    def test_mixed_combat_and_navigation_payload_equality(self):
        """Same seed → identical payloads through combat + scene transition."""
        commands = [
            ("attack Goblin Warrior", "pc_fighter"),
            ("go east", "pc_fighter"),
            ("rest", "pc_fighter"),
        ]

        orch_a = _make_orchestrator(seed=1234)
        orch_b = _make_orchestrator(seed=1234)

        for orch in (orch_a, orch_b):
            orch.load_scene("room_a")

        all_events_a = []
        all_events_b = []

        for text, actor in commands:
            result_a = orch_a.process_text_turn(text, actor)
            result_b = orch_b.process_text_turn(text, actor)
            all_events_a.extend(result_a.events)
            all_events_b.extend(result_b.events)

        assert len(all_events_a) == len(all_events_b)

        for i, (ea, eb) in enumerate(zip(all_events_a, all_events_b)):
            assert ea == eb, (
                f"Event {i} in mixed sequence differs:\n"
                f"  A: {json.dumps(ea, sort_keys=True)}\n"
                f"  B: {json.dumps(eb, sort_keys=True)}"
            )


# ======================================================================
# CATEGORY 2: NARRATIVEBRIEF SERIALIZATION ROUND-TRIP (4 tests)
# ======================================================================


class TestNarrativeBriefRoundTrip:
    """NarrativeBrief to_dict/from_dict preserves all fields."""

    def test_attack_hit_brief_round_trip(self):
        """NarrativeBrief from attack_hit round-trips through to_dict/from_dict."""
        brief = NarrativeBrief(
            action_type="attack_hit",
            actor_name="Kael",
            target_name="Goblin Warrior",
            outcome_summary="Kael hits Goblin Warrior for 8 damage",
            severity="moderate",
            weapon_name="longsword",
            damage_type="slashing",
            target_defeated=False,
            source_event_ids=[100, 101, 102],
        )

        serialized = brief.to_dict()
        restored = NarrativeBrief.from_dict(serialized)

        assert restored.action_type == brief.action_type
        assert restored.actor_name == brief.actor_name
        assert restored.target_name == brief.target_name
        assert restored.outcome_summary == brief.outcome_summary
        assert restored.severity == brief.severity
        assert restored.weapon_name == brief.weapon_name
        assert restored.damage_type == brief.damage_type
        assert restored.target_defeated == brief.target_defeated
        assert restored.source_event_ids == brief.source_event_ids
        assert restored.provenance_tag == brief.provenance_tag

    def test_full_brief_json_round_trip(self):
        """NarrativeBrief survives JSON serialization (the real boundary)."""
        brief = NarrativeBrief(
            action_type="attack_hit",
            actor_name="Kael",
            target_name="Goblin Warrior",
            outcome_summary="Kael strikes Goblin Warrior for 12 damage, defeating them",
            severity="lethal",
            weapon_name="longsword",
            damage_type="slashing",
            condition_applied="prone",
            target_defeated=True,
            previous_narrations=["The goblin snarls.", "Steel meets flesh."],
            scene_description="A torch-lit chamber.",
            source_event_ids=[200, 201, 202, 203],
            provenance_tag="[DERIVED]",
        )

        # Full round-trip: brief → dict → JSON → dict → brief
        serialized = brief.to_dict()
        json_str = json.dumps(serialized, sort_keys=True)
        deserialized = json.loads(json_str)
        restored = NarrativeBrief.from_dict(deserialized)

        # Compare all 13 fields
        assert restored.to_dict() == brief.to_dict()

    def test_minimal_brief_round_trip(self):
        """Minimal NarrativeBrief (only required fields) round-trips."""
        brief = NarrativeBrief(
            action_type="movement",
            actor_name="Kael",
        )

        serialized = brief.to_dict()
        restored = NarrativeBrief.from_dict(serialized)

        assert restored.action_type == "movement"
        assert restored.actor_name == "Kael"
        assert restored.target_name is None
        assert restored.outcome_summary == ""
        assert restored.severity == "minor"
        assert restored.target_defeated is False
        assert restored.source_event_ids == []
        assert restored.provenance_tag == "[DERIVED]"

    def test_real_orchestrator_brief_round_trip(self):
        """NarrativeBrief produced by real orchestrator turn round-trips."""
        orch = _make_orchestrator(seed=42)
        orch.process_text_turn("attack Goblin Warrior", "pc_fighter")

        brief = orch.brief_history[0]
        assert isinstance(brief, NarrativeBrief)

        # Round-trip through JSON
        serialized = brief.to_dict()
        json_str = json.dumps(serialized, sort_keys=True)
        deserialized = json.loads(json_str)
        restored = NarrativeBrief.from_dict(deserialized)

        assert restored.to_dict() == brief.to_dict()


# ======================================================================
# CATEGORY 3: EVENT ORDERING INVARIANTS (5 tests)
# ======================================================================


class TestEventOrderingInvariants:
    """Structural event ordering from Box resolution."""

    def test_turn_start_always_first(self):
        """turn_start is always the first event in attack turns."""
        for seed in range(10):
            orch = _make_orchestrator(seed=seed)
            result = orch.process_text_turn("attack Goblin Warrior", "pc_fighter")

            event_types = [e["type"] for e in result.events]
            assert event_types[0] == "turn_start", (
                f"seed={seed}: first event is '{event_types[0]}', expected 'turn_start'"
            )

    def test_turn_end_always_last(self):
        """turn_end is always the last event in attack turns."""
        for seed in range(10):
            orch = _make_orchestrator(seed=seed)
            result = orch.process_text_turn("attack Goblin Warrior", "pc_fighter")

            event_types = [e["type"] for e in result.events]
            assert event_types[-1] == "turn_end", (
                f"seed={seed}: last event is '{event_types[-1]}', expected 'turn_end'"
            )

    def test_attack_roll_before_damage(self):
        """attack_roll always precedes damage_roll in the event sequence."""
        for seed in range(20):
            orch = _make_orchestrator(seed=seed)
            result = orch.process_text_turn("attack Goblin Warrior", "pc_fighter")

            event_types = [e["type"] for e in result.events]

            if "damage_roll" in event_types:
                attack_idx = event_types.index("attack_roll")
                damage_idx = event_types.index("damage_roll")
                assert attack_idx < damage_idx, (
                    f"seed={seed}: attack_roll at {attack_idx}, damage_roll at {damage_idx}"
                )

    def test_damage_before_hp_changed(self):
        """damage_roll always precedes hp_changed in attack turns."""
        for seed in range(20):
            orch = _make_orchestrator(seed=seed)
            result = orch.process_text_turn("attack Goblin Warrior", "pc_fighter")

            event_types = [e["type"] for e in result.events]

            if "hp_changed" in event_types and "damage_roll" in event_types:
                damage_idx = event_types.index("damage_roll")
                hp_idx = event_types.index("hp_changed")
                assert damage_idx < hp_idx, (
                    f"seed={seed}: damage_roll at {damage_idx}, hp_changed at {hp_idx}"
                )

    def test_hp_changed_before_entity_defeated(self):
        """hp_changed always precedes entity_defeated."""
        for seed in range(200):
            orch = _make_orchestrator(
                seed=seed, goblin_hp=1, goblin_ac=5, attack_bonus=15
            )
            result = orch.process_text_turn("attack Goblin Warrior", "pc_fighter")

            event_types = [e["type"] for e in result.events]

            if "entity_defeated" in event_types:
                hp_idx = event_types.index("hp_changed")
                defeat_idx = event_types.index("entity_defeated")
                assert hp_idx < defeat_idx, (
                    f"seed={seed}: hp_changed at {hp_idx}, entity_defeated at {defeat_idx}"
                )
                return

        pytest.fail("No defeat in 200 seeds — cannot verify ordering")
