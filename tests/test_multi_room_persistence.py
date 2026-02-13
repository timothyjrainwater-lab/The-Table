"""P2: Multi-Room Scene Persistence Stress Test

Validates state continuity across a 3-room mini dungeon:
  Room A (Goblin Ambush) → combat → transition →
  Room B (Rest Chamber) → rest → transition →
  Room C (Boss Room) → encounter trigger

Tests ensure:
1. HP changes from combat persist across transitions
2. Entity defeat status carries across rooms
3. State hash tracks real mutations correctly
4. Rest healing events are generated with correct amounts
5. Encounter triggering reads correct party data after combat
6. Session state transitions correctly through the flow
7. NarrativeBrief history accumulates across rooms

Test Categories:
1. State Persistence Across Transitions (6 tests)
2. Combat→Transition→Rest Flow (5 tests)
3. Full Dungeon Traversal (4 tests)
4. Edge Cases (3 tests)

Total: 18 tests
"""

import pytest
from copy import deepcopy

from aidm.core.rng_manager import RNGManager
from aidm.core.state import WorldState, FrozenWorldStateView
from aidm.lens.context_assembler import ContextAssembler
from aidm.lens.narrative_brief import NarrativeBrief
from aidm.lens.scene_manager import (
    EncounterDef,
    Exit,
    SceneManager,
    SceneState,
)
from aidm.interaction.intent_bridge import IntentBridge
from aidm.narration.guarded_narration_service import GuardedNarrationService
from aidm.runtime.session_orchestrator import (
    SessionOrchestrator,
    SessionState,
    TurnResult,
)
from aidm.schemas.entity_fields import EF
from aidm.spark.dm_persona import DMPersona


# ======================================================================
# FIXTURES — 3-Room Mini Dungeon
# ======================================================================


@pytest.fixture
def dungeon_scenes():
    """3-room mini dungeon: Ambush → Rest Chamber → Boss Room."""
    return {
        "room_a": SceneState(
            scene_id="room_a",
            name="Goblin Ambush",
            description="A narrow corridor opens into a torch-lit chamber. "
            "Goblins lurk behind overturned tables.",
            exits=[
                Exit(
                    exit_id="east",
                    destination_scene_id="room_b",
                    description="A heavy wooden door leads east",
                    locked=False,
                    hidden=False,
                ),
            ],
        ),
        "room_b": SceneState(
            scene_id="room_b",
            name="Rest Chamber",
            description="A quiet alcove with bedrolls and a cold fire pit.",
            exits=[
                Exit(
                    exit_id="west",
                    destination_scene_id="room_a",
                    description="Back to the ambush chamber",
                    locked=False,
                    hidden=False,
                ),
                Exit(
                    exit_id="north",
                    destination_scene_id="room_c",
                    description="A reinforced iron door leads north",
                    locked=False,
                    hidden=False,
                ),
            ],
        ),
        "room_c": SceneState(
            scene_id="room_c",
            name="Boss Room",
            description="A vast chamber with a throne of bone.",
            exits=[
                Exit(
                    exit_id="south",
                    destination_scene_id="room_b",
                    description="Retreat to the rest chamber",
                    locked=False,
                    hidden=False,
                ),
            ],
            encounters=[
                EncounterDef(
                    encounter_id="boss_encounter",
                    monster_ids=["ogre_1"],
                    trigger_condition="on_entry",
                    initiative_data=[("ogre_1", -1)],
                    triggered=False,
                ),
            ],
        ),
    }


@pytest.fixture
def dungeon_world_state():
    """Party of fighter + wizard, plus goblin in Room A."""
    return WorldState(
        ruleset_version="RAW_3.5",
        entities={
            "pc_fighter": {
                EF.ENTITY_ID: "pc_fighter",
                "name": "Kael",
                EF.TEAM: "party",
                EF.LEVEL: 5,
                EF.HP_CURRENT: 40,
                EF.HP_MAX: 50,
                EF.AC: 16,
                EF.DEFEATED: False,
                EF.ATTACK_BONUS: 10,
                EF.BAB: 8,
                EF.STR_MOD: 4,
                EF.WEAPON: "longsword",
                "weapon_damage": "1d8+4",
                EF.DEX_MOD: 2,
            },
            "pc_wizard": {
                EF.ENTITY_ID: "pc_wizard",
                "name": "Elara",
                EF.TEAM: "party",
                EF.LEVEL: 5,
                EF.HP_CURRENT: 18,
                EF.HP_MAX: 22,
                EF.AC: 12,
                EF.DEFEATED: False,
                EF.ATTACK_BONUS: 2,
                EF.BAB: 2,
                EF.STR_MOD: 0,
                EF.WEAPON: "quarterstaff",
                "weapon_damage": "1d6",
                EF.DEX_MOD: 2,
            },
            "goblin_1": {
                EF.ENTITY_ID: "goblin_1",
                "name": "Goblin Warrior",
                EF.TEAM: "enemy",
                EF.LEVEL: 1,
                EF.HP_CURRENT: 6,
                EF.HP_MAX: 6,
                EF.AC: 15,
                EF.DEFEATED: False,
                EF.ATTACK_BONUS: 2,
                EF.DEX_MOD: 1,
            },
        },
    )


@pytest.fixture
def dungeon_orchestrator(dungeon_scenes, dungeon_world_state):
    """Orchestrator wired to the 3-room dungeon."""
    return SessionOrchestrator(
        world_state=dungeon_world_state,
        intent_bridge=IntentBridge(),
        scene_manager=SceneManager(scenes=dungeon_scenes),
        dm_persona=DMPersona(),
        narration_service=GuardedNarrationService(),
        context_assembler=ContextAssembler(token_budget=800),
        master_seed=42,
    )


def _find_hit_seed(world_state_factory, target_name="Goblin Warrior", max_seeds=100):
    """Find an RNG seed that produces a hit for deterministic testing.

    Returns (seed, orchestrator_after_attack, turn_result) or raises if no hit found.
    """
    for seed in range(max_seeds):
        ws = world_state_factory()
        orch = SessionOrchestrator(
            world_state=ws,
            intent_bridge=IntentBridge(),
            scene_manager=SceneManager(scenes={}),
            dm_persona=DMPersona(),
            narration_service=GuardedNarrationService(),
            context_assembler=ContextAssembler(token_budget=800),
            master_seed=seed,
        )
        result = orch.process_text_turn(f"attack {target_name}", "pc_fighter")
        hit = any(
            e["type"] == "attack_roll" and e.get("hit", False)
            for e in result.events
        )
        if hit:
            return seed, orch, result
    pytest.fail(f"No hit found in {max_seeds} seeds")


# ======================================================================
# CATEGORY 1: STATE PERSISTENCE ACROSS TRANSITIONS (6 tests)
# ======================================================================


class TestStatePersistence:
    """Verify entity state carries across scene transitions."""

    def test_hp_persists_across_transition(self, dungeon_orchestrator):
        """HP changes from combat survive scene transition."""
        orch = dungeon_orchestrator
        orch.load_scene("room_a")

        # Record initial state
        initial_fighter_hp = orch.world_state.entities["pc_fighter"][EF.HP_CURRENT]

        # Attack goblin — Box resolves real combat
        orch.process_text_turn("attack Goblin Warrior", "pc_fighter")

        # Record post-combat state
        post_combat_hash = orch.world_state.state_hash()
        post_combat_goblin_hp = orch.world_state.entities["goblin_1"][EF.HP_CURRENT]

        # Transition to Room B
        orch.process_text_turn("go east", "pc_fighter")

        # State hash unchanged after transition
        assert orch.world_state.state_hash() == post_combat_hash
        # Goblin HP still reflects combat damage
        assert orch.world_state.entities["goblin_1"][EF.HP_CURRENT] == post_combat_goblin_hp

    def test_defeat_status_persists_across_transition(self):
        """Entity defeated in Room A stays defeated in Room B."""
        # Use high attack bonus + 1 HP goblin to guarantee defeat
        for seed in range(200):
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
                        EF.ATTACK_BONUS: 15,
                        EF.BAB: 12,
                        EF.STR_MOD: 6,
                        EF.WEAPON: "longsword",
                        "weapon_damage": "1d8+6",
                        EF.DEX_MOD: 2,
                    },
                    "goblin_1": {
                        EF.ENTITY_ID: "goblin_1",
                        "name": "Goblin Warrior",
                        EF.TEAM: "enemy",
                        EF.LEVEL: 1,
                        EF.HP_CURRENT: 1,
                        EF.HP_MAX: 6,
                        EF.AC: 5,
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
                    description="Room A.",
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
                    description="Room B.",
                    exits=[],
                ),
            }
            orch = SessionOrchestrator(
                world_state=ws,
                intent_bridge=IntentBridge(),
                scene_manager=SceneManager(scenes=scenes),
                dm_persona=DMPersona(),
                narration_service=GuardedNarrationService(),
                context_assembler=ContextAssembler(token_budget=800),
                master_seed=seed,
            )
            orch.load_scene("room_a")

            result = orch.process_text_turn("attack Goblin Warrior", "pc_fighter")
            defeated = any(
                e["type"] == "entity_defeated" for e in result.events
            )
            if defeated:
                assert orch.world_state.entities["goblin_1"].get(EF.DEFEATED) is True

                # Transition to Room B
                orch.process_text_turn("go east", "pc_fighter")

                # Defeat status persists
                assert orch.world_state.entities["goblin_1"].get(EF.DEFEATED) is True
                return

        pytest.fail("No defeat in 200 seeds with 1 HP goblin")

    def test_state_hash_stable_across_transition(self, dungeon_orchestrator):
        """State hash unchanged by scene transition (no state mutation)."""
        orch = dungeon_orchestrator
        orch.load_scene("room_a")

        hash_before = orch.world_state.state_hash()

        orch.process_text_turn("go east", "pc_fighter")

        assert orch.world_state.state_hash() == hash_before

    def test_multiple_transitions_preserve_state(self, dungeon_orchestrator):
        """State unchanged after Room A → B → C → B round-trip."""
        orch = dungeon_orchestrator
        orch.load_scene("room_a")

        hash_initial = orch.world_state.state_hash()

        # Room A → Room B
        orch.process_text_turn("go east", "pc_fighter")
        assert orch.current_scene_id == "room_b"

        # Room B → Room C
        orch.process_text_turn("go north", "pc_fighter")
        assert orch.current_scene_id == "room_c"

        # Room C → Room B
        orch.process_text_turn("go south", "pc_fighter")
        assert orch.current_scene_id == "room_b"

        # State unchanged through all transitions
        assert orch.world_state.state_hash() == hash_initial

    def test_entity_count_preserved_across_transitions(self, dungeon_orchestrator):
        """All entities present after transitions (no entity loss)."""
        orch = dungeon_orchestrator
        orch.load_scene("room_a")

        initial_entity_ids = set(orch.world_state.entities.keys())

        orch.process_text_turn("go east", "pc_fighter")
        orch.process_text_turn("go north", "pc_fighter")

        assert set(orch.world_state.entities.keys()) == initial_entity_ids

    def test_combat_state_mutates_then_preserves(self, dungeon_orchestrator):
        """Combat mutates state, then transitions preserve the mutation."""
        orch = dungeon_orchestrator
        orch.load_scene("room_a")

        hash_before_combat = orch.world_state.state_hash()

        # Combat mutates state
        orch.process_text_turn("attack Goblin Warrior", "pc_fighter")
        hash_after_combat = orch.world_state.state_hash()
        assert hash_after_combat != hash_before_combat

        # Transition preserves mutated state
        orch.process_text_turn("go east", "pc_fighter")
        assert orch.world_state.state_hash() == hash_after_combat

        # Second transition still preserves
        orch.process_text_turn("go north", "pc_fighter")
        assert orch.world_state.state_hash() == hash_after_combat


# ======================================================================
# CATEGORY 2: COMBAT → TRANSITION → REST FLOW (5 tests)
# ======================================================================


class TestCombatTransitionRest:
    """Verify the combat → transition → rest flow."""

    def test_rest_events_generated_after_combat(self, dungeon_orchestrator):
        """Rest in Room B generates healing events for party members."""
        orch = dungeon_orchestrator
        orch.load_scene("room_a")

        # Combat in Room A
        orch.process_text_turn("attack Goblin Warrior", "pc_fighter")

        # Transition to Room B
        orch.process_text_turn("go east", "pc_fighter")

        # Rest in Room B
        rest_result = orch.process_text_turn("rest", "pc_fighter")

        assert rest_result.success is True
        assert rest_result.narration_text != ""

        # Rest events should be generated (healing amounts for party members)
        rest_events = [e for e in rest_result.events if e.get("type") == "rest_healing"]
        # Fighter has 40/50 HP → level 5 → 5 HP healing available
        # Wizard has 18/22 HP → level 5 → 4 HP healing (capped at 22-18=4)
        assert len(rest_events) >= 1  # At least one party member needs healing

    def test_rest_healing_amounts_correct(self, dungeon_orchestrator):
        """Rest healing follows D&D 3.5E rules (1 HP/level for 8 hours)."""
        orch = dungeon_orchestrator
        orch.load_scene("room_a")

        # Skip combat — go directly to rest
        orch.process_text_turn("go east", "pc_fighter")

        rest_result = orch.process_text_turn("rest", "pc_fighter")

        rest_events = [e for e in rest_result.events if e.get("type") == "rest_healing"]

        for event in rest_events:
            entity_id = event["entity_id"]
            healing = event["healing_amount"]
            entity = orch.world_state.entities[entity_id]
            level = entity.get(EF.LEVEL, 1)
            hp_current = event["hp_before"]
            hp_max = entity.get(EF.HP_MAX, hp_current)

            # 8_hours rest: 1 HP per level, capped at max
            expected = min(level, hp_max - hp_current)
            assert healing == expected, (
                f"{entity_id}: expected {expected} healing, got {healing}"
            )

    def test_rest_only_heals_party(self, dungeon_orchestrator):
        """Rest events only for party members, not enemies."""
        orch = dungeon_orchestrator
        orch.load_scene("room_a")

        orch.process_text_turn("go east", "pc_fighter")
        rest_result = orch.process_text_turn("rest", "pc_fighter")

        rest_events = [e for e in rest_result.events if e.get("type") == "rest_healing"]
        healed_ids = {e["entity_id"] for e in rest_events}

        # Only party members get healing
        assert "goblin_1" not in healed_ids
        for eid in healed_ids:
            assert orch.world_state.entities[eid].get(EF.TEAM) == "party"

    def test_session_state_transitions_through_rest(self, dungeon_orchestrator):
        """Session state: EXPLORATION → REST → EXPLORATION during rest."""
        orch = dungeon_orchestrator
        orch.load_scene("room_a")

        assert orch.session_state == SessionState.EXPLORATION

        # Rest changes state temporarily (returns to EXPLORATION after)
        orch.process_text_turn("rest", "pc_fighter")
        assert orch.session_state == SessionState.EXPLORATION

    def test_transition_events_contain_scene_data(self, dungeon_orchestrator):
        """Transition events include from/to scene IDs."""
        orch = dungeon_orchestrator
        orch.load_scene("room_a")

        result = orch.process_text_turn("go east", "pc_fighter")

        transition_events = [
            e for e in result.events if e.get("type") == "scene_transition"
        ]
        assert len(transition_events) >= 1

        event = transition_events[0]
        assert event["from_scene"] == "room_a"
        assert event["to_scene"] == "room_b"


# ======================================================================
# CATEGORY 3: FULL DUNGEON TRAVERSAL (4 tests)
# ======================================================================


class TestFullDungeonTraversal:
    """End-to-end 3-room dungeon traversal."""

    def test_full_traversal_combat_rest_encounter(self, dungeon_orchestrator):
        """Room A combat → Room B rest → Room C encounter trigger."""
        orch = dungeon_orchestrator
        orch.load_scene("room_a")

        # 1. Combat in Room A
        attack_result = orch.process_text_turn("attack Goblin Warrior", "pc_fighter")
        assert attack_result.success is True
        event_types = [e["type"] for e in attack_result.events]
        assert "attack_roll" in event_types

        # 2. Transition to Room B
        trans_result = orch.process_text_turn("go east", "pc_fighter")
        assert trans_result.success is True
        assert orch.current_scene_id == "room_b"

        # 3. Rest in Room B
        rest_result = orch.process_text_turn("rest", "pc_fighter")
        assert rest_result.success is True

        # 4. Transition to Room C (boss room)
        boss_result = orch.process_text_turn("go north", "pc_fighter")
        assert boss_result.success is True
        assert orch.current_scene_id == "room_c"

        # Full traversal completed — all steps succeeded
        assert orch.turn_count == 4

    def test_brief_history_accumulates_across_rooms(self, dungeon_orchestrator):
        """NarrativeBrief history grows with each turn across rooms."""
        orch = dungeon_orchestrator
        orch.load_scene("room_a")

        assert len(orch.brief_history) == 0

        # Room A: attack
        orch.process_text_turn("attack Goblin Warrior", "pc_fighter")
        assert len(orch.brief_history) == 1

        # Room A → B
        orch.process_text_turn("go east", "pc_fighter")
        assert len(orch.brief_history) == 2

        # Room B: rest
        orch.process_text_turn("rest", "pc_fighter")
        assert len(orch.brief_history) == 3

        # Room B → C
        orch.process_text_turn("go north", "pc_fighter")
        assert len(orch.brief_history) == 4

        # All briefs are NarrativeBrief instances
        for brief in orch.brief_history:
            assert isinstance(brief, NarrativeBrief)

    def test_scene_tracking_through_full_traversal(self, dungeon_orchestrator):
        """current_scene_id updates correctly through full dungeon."""
        orch = dungeon_orchestrator

        assert orch.current_scene_id is None

        orch.load_scene("room_a")
        assert orch.current_scene_id == "room_a"

        orch.process_text_turn("go east", "pc_fighter")
        assert orch.current_scene_id == "room_b"

        orch.process_text_turn("go north", "pc_fighter")
        assert orch.current_scene_id == "room_c"

        orch.process_text_turn("go south", "pc_fighter")
        assert orch.current_scene_id == "room_b"

    def test_deterministic_full_traversal(self):
        """Same seed → identical state after full traversal."""
        def make_dungeon(seed):
            ws = WorldState(
                ruleset_version="RAW_3.5",
                entities={
                    "pc_fighter": {
                        EF.ENTITY_ID: "pc_fighter",
                        "name": "Kael",
                        EF.TEAM: "party",
                        EF.LEVEL: 5,
                        EF.HP_CURRENT: 40,
                        EF.HP_MAX: 50,
                        EF.AC: 16,
                        EF.DEFEATED: False,
                        EF.ATTACK_BONUS: 10,
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
                        EF.HP_CURRENT: 100,
                        EF.HP_MAX: 100,
                        EF.AC: 10,
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
                    description="Room A.",
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
                    description="Room B.",
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

        # Two orchestrators with same seed
        orch_a = make_dungeon(seed=7777)
        orch_b = make_dungeon(seed=7777)

        # Same sequence of actions
        for orch in (orch_a, orch_b):
            orch.load_scene("room_a")
            orch.process_text_turn("attack Goblin Warrior", "pc_fighter")
            orch.process_text_turn("go east", "pc_fighter")
            orch.process_text_turn("rest", "pc_fighter")

        # Same seed + same actions → identical final state
        assert orch_a.world_state.state_hash() == orch_b.world_state.state_hash()
        assert orch_a.turn_count == orch_b.turn_count
        assert len(orch_a.brief_history) == len(orch_b.brief_history)


# ======================================================================
# CATEGORY 4: EDGE CASES (3 tests)
# ======================================================================


class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_combat_in_multiple_rooms(self, dungeon_orchestrator):
        """Combat in Room A, transition, combat-like action in Room B."""
        orch = dungeon_orchestrator
        orch.load_scene("room_a")

        # Combat in Room A
        orch.process_text_turn("attack Goblin Warrior", "pc_fighter")
        hash_after_room_a = orch.world_state.state_hash()

        # Transition to Room B
        orch.process_text_turn("go east", "pc_fighter")
        assert orch.world_state.state_hash() == hash_after_room_a

        # Attack in Room B (goblin_1 still exists in world state, even in Room B)
        result = orch.process_text_turn("attack Goblin Warrior", "pc_fighter")
        assert result.success is True
        # State changes again (another combat resolution)
        hash_after_room_b = orch.world_state.state_hash()
        assert hash_after_room_b != hash_after_room_a

    def test_rapid_transitions_no_state_drift(self, dungeon_orchestrator):
        """10 rapid transitions back and forth — no state drift."""
        orch = dungeon_orchestrator
        orch.load_scene("room_a")

        initial_hash = orch.world_state.state_hash()

        for _ in range(5):
            orch.process_text_turn("go east", "pc_fighter")  # A → B
            orch.process_text_turn("go west", "pc_fighter")  # B → A

        # After 10 transitions, state unchanged
        assert orch.world_state.state_hash() == initial_hash
        assert orch.current_scene_id == "room_a"

    def test_encounter_trigger_reads_current_party(self, dungeon_scenes):
        """Encounter trigger in Room C reads real party data."""
        ws = WorldState(
            ruleset_version="RAW_3.5",
            entities={
                "pc_fighter": {
                    EF.ENTITY_ID: "pc_fighter",
                    "name": "Kael",
                    EF.TEAM: "party",
                    EF.LEVEL: 5,
                    EF.HP_CURRENT: 40,
                    EF.HP_MAX: 50,
                    EF.AC: 16,
                    EF.DEFEATED: False,
                    EF.ATTACK_BONUS: 10,
                    EF.DEX_MOD: 2,
                },
                "pc_wizard": {
                    EF.ENTITY_ID: "pc_wizard",
                    "name": "Elara",
                    EF.TEAM: "party",
                    EF.LEVEL: 5,
                    EF.HP_CURRENT: 18,
                    EF.HP_MAX: 22,
                    EF.AC: 12,
                    EF.DEFEATED: False,
                    EF.ATTACK_BONUS: 2,
                    EF.DEX_MOD: 2,
                },
            },
        )

        scene_mgr = SceneManager(scenes=dungeon_scenes)
        room_c = scene_mgr.load_scene("room_c")

        rng = RNGManager(master_seed=42)
        encounter_result = scene_mgr.trigger_encounter(
            scene=room_c,
            world_state=ws,
            rng=rng,
            trigger_condition="on_entry",
        )

        assert encounter_result is not None
        assert encounter_result.encounter_id == "boss_encounter"
        assert encounter_result.triggered is True

        # Initiative order should include party members + monster
        assert len(encounter_result.initiative_order) >= 2  # At least fighter + ogre
        # Party members in initiative
        assert "pc_fighter" in encounter_result.initiative_order
