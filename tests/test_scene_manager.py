"""WO-040: Scene Manager Tests

Comprehensive test suite for scene management, covering:
- Scene loading
- Scene transitions
- Encounter triggers
- Rest mechanics (D&D 3.5e)
- Loot management
- Environmental data

Test tiers:
- Tier 1: Scene loading and data structures (8 tests)
- Tier 2: Scene transitions (7 tests)
- Tier 3: Encounter triggers (5 tests)
- Tier 4: Rest mechanics (5 tests)
- Tier 5: Boundary law compliance (3 tests)

Total: 28 tests
"""

import pytest
from copy import deepcopy

from aidm.lens.scene_manager import (
    SceneManager,
    SceneState,
    Exit,
    EncounterDef,
    LootDef,
    TransitionResult,
    EncounterResult,
    RestResult,
)
from aidm.core.state import WorldState, FrozenWorldStateView
from aidm.core.rng_manager import RNGManager
from aidm.schemas.entity_fields import EF


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def simple_scene():
    """Create a simple scene with exits and loot."""
    return SceneState(
        scene_id="dungeon_entrance",
        name="Dungeon Entrance",
        description="A dark stone corridor descends into darkness.",
        exits=[
            Exit(
                exit_id="north",
                destination_scene_id="chamber_01",
                description="A passage leading north",
                locked=False,
                hidden=False,
            ),
            Exit(
                exit_id="locked_door",
                destination_scene_id="treasure_room",
                description="A locked iron door",
                locked=True,
                hidden=False,
            ),
        ],
        loot=[
            LootDef(
                item_id="torch_01",
                description="A lit torch",
                location="on the wall",
                hidden=False,
                collected=False,
            ),
        ],
        environmental={
            "lighting": "dim",
            "terrain": ["stone", "damp"],
        }
    )


@pytest.fixture
def encounter_scene():
    """Create a scene with an encounter."""
    return SceneState(
        scene_id="goblin_ambush",
        name="Goblin Ambush",
        description="The corridor widens into a small chamber. Goblins lurk in the shadows!",
        exits=[
            Exit(
                exit_id="retreat",
                destination_scene_id="dungeon_entrance",
                description="Back the way you came",
                locked=False,
                hidden=False,
            ),
        ],
        encounters=[
            EncounterDef(
                encounter_id="goblin_ambush_01",
                monster_ids=["goblin_01", "goblin_02"],
                trigger_condition="on_entry",
                initiative_data=[
                    ("goblin_01", 2),  # Dex mod +2
                    ("goblin_02", 2),  # Dex mod +2
                ],
                triggered=False,
            ),
        ],
        loot=[],
        environmental={"lighting": "dim"}
    )


@pytest.fixture
def scene_manager(simple_scene, encounter_scene):
    """Create a scene manager with test scenes."""
    scenes = {
        "dungeon_entrance": simple_scene,
        "chamber_01": SceneState(
            scene_id="chamber_01",
            name="Chamber 01",
            description="A small chamber with ancient murals.",
            exits=[
                Exit(
                    exit_id="south",
                    destination_scene_id="dungeon_entrance",
                    description="Back to the entrance",
                ),
            ],
        ),
        "treasure_room": SceneState(
            scene_id="treasure_room",
            name="Treasure Room",
            description="A room filled with gold and jewels!",
            exits=[],
            loot=[
                LootDef(
                    item_id="gold_pile",
                    description="500 gold pieces",
                    location="in a chest",
                ),
            ],
        ),
        "goblin_ambush": encounter_scene,
    }

    return SceneManager(scenes=scenes)


@pytest.fixture
def world_state():
    """Create a world state with party members."""
    return WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter_01": {
                EF.ENTITY_ID: "fighter_01",
                "name": "Ragnar",
                EF.TEAM: "party",
                EF.LEVEL: 5,
                EF.HP_CURRENT: 30,
                EF.HP_MAX: 50,
                EF.DEX_MOD: 2,
            },
            "wizard_01": {
                EF.ENTITY_ID: "wizard_01",
                "name": "Elara",
                EF.TEAM: "party",
                EF.LEVEL: 5,
                EF.HP_CURRENT: 20,
                EF.HP_MAX: 25,
                EF.DEX_MOD: 3,
            },
        },
    )


@pytest.fixture
def rng():
    """Create a deterministic RNG manager."""
    return RNGManager(master_seed=42)


# ==============================================================================
# TIER 1: SCENE LOADING AND DATA STRUCTURES (8 tests)
# ==============================================================================

def test_scene_state_immutable(simple_scene):
    """Tier 1: SceneState is immutable (frozen dataclass)."""
    with pytest.raises(AttributeError):
        simple_scene.name = "Modified Name"


def test_load_scene_success(scene_manager):
    """Tier 1: load_scene() returns correct scene."""
    scene = scene_manager.load_scene("dungeon_entrance")

    assert scene.scene_id == "dungeon_entrance"
    assert scene.name == "Dungeon Entrance"
    assert len(scene.exits) == 2
    assert len(scene.loot) == 1


def test_load_scene_not_found(scene_manager):
    """Tier 1: load_scene() raises KeyError for unknown scene."""
    with pytest.raises(KeyError, match="Scene not found: nonexistent"):
        scene_manager.load_scene("nonexistent")


def test_exit_structure(simple_scene):
    """Tier 1: Exit dataclass has required fields."""
    exit_obj = simple_scene.exits[0]

    assert exit_obj.exit_id == "north"
    assert exit_obj.destination_scene_id == "chamber_01"
    assert exit_obj.description == "A passage leading north"
    assert exit_obj.locked is False
    assert exit_obj.hidden is False


def test_encounter_def_structure(encounter_scene):
    """Tier 1: EncounterDef dataclass has required fields."""
    encounter = encounter_scene.encounters[0]

    assert encounter.encounter_id == "goblin_ambush_01"
    assert encounter.monster_ids == ["goblin_01", "goblin_02"]
    assert encounter.trigger_condition == "on_entry"
    assert len(encounter.initiative_data) == 2
    assert encounter.triggered is False


def test_loot_def_structure(simple_scene):
    """Tier 1: LootDef dataclass has required fields."""
    loot = simple_scene.loot[0]

    assert loot.item_id == "torch_01"
    assert loot.description == "A lit torch"
    assert loot.location == "on the wall"
    assert loot.hidden is False
    assert loot.collected is False


def test_environmental_data(simple_scene):
    """Tier 1: Scene can store environmental data."""
    assert simple_scene.environmental["lighting"] == "dim"
    assert "stone" in simple_scene.environmental["terrain"]
    assert "damp" in simple_scene.environmental["terrain"]


def test_scene_with_no_exits():
    """Tier 1: Scene can have no exits (dead end)."""
    scene = SceneState(
        scene_id="dead_end",
        name="Dead End",
        description="A corridor ends in a blank wall.",
        exits=[],
    )

    assert len(scene.exits) == 0


# ==============================================================================
# TIER 2: SCENE TRANSITIONS (7 tests)
# ==============================================================================

def test_transition_success(scene_manager, world_state):
    """Tier 2: transition_scene() succeeds with valid exit."""
    result = scene_manager.transition_scene(
        from_scene="dungeon_entrance",
        exit_id="north",
        world_state=world_state,
    )

    assert result.success is True
    assert result.new_scene is not None
    assert result.new_scene.scene_id == "chamber_01"
    assert result.new_scene.name == "Chamber 01"
    assert len(result.events) == 1
    assert result.events[0]["type"] == "scene_transition"
    assert result.narrative_hint != ""


def test_transition_preserves_world_state(scene_manager, world_state):
    """Tier 2: transition_scene() preserves entity state."""
    result = scene_manager.transition_scene(
        from_scene="dungeon_entrance",
        exit_id="north",
        world_state=world_state,
    )

    # World state should be unchanged (transitions don't modify entities)
    assert world_state.entities["fighter_01"][EF.HP_CURRENT] == 30
    assert world_state.entities["wizard_01"][EF.HP_CURRENT] == 20


def test_transition_locked_exit(scene_manager, world_state):
    """Tier 2: transition_scene() fails for locked exit."""
    result = scene_manager.transition_scene(
        from_scene="dungeon_entrance",
        exit_id="locked_door",
        world_state=world_state,
    )

    assert result.success is False
    assert result.new_scene is None
    assert "locked" in result.error_message.lower()


def test_transition_invalid_exit(scene_manager, world_state):
    """Tier 2: transition_scene() fails for nonexistent exit."""
    result = scene_manager.transition_scene(
        from_scene="dungeon_entrance",
        exit_id="nonexistent",
        world_state=world_state,
    )

    assert result.success is False
    assert result.new_scene is None
    assert "not found" in result.error_message.lower()


def test_transition_invalid_source_scene(scene_manager, world_state):
    """Tier 2: transition_scene() fails for nonexistent source scene."""
    result = scene_manager.transition_scene(
        from_scene="nonexistent",
        exit_id="north",
        world_state=world_state,
    )

    assert result.success is False
    assert result.new_scene is None
    assert "not found" in result.error_message.lower()


def test_transition_event_structure(scene_manager, world_state):
    """Tier 2: transition events have correct structure."""
    result = scene_manager.transition_scene(
        from_scene="dungeon_entrance",
        exit_id="north",
        world_state=world_state,
    )

    assert len(result.events) == 1
    event = result.events[0]

    assert event["type"] == "scene_transition"
    assert event["from_scene"] == "dungeon_entrance"
    assert event["to_scene"] == "chamber_01"
    assert event["exit_id"] == "north"
    assert "exit_description" in event


def test_transition_narrative_hint(scene_manager, world_state):
    """Tier 2: transition provides narrative hint."""
    result = scene_manager.transition_scene(
        from_scene="dungeon_entrance",
        exit_id="north",
        world_state=world_state,
    )

    assert "party" in result.narrative_hint.lower()
    assert "chamber 01" in result.narrative_hint.lower()


# ==============================================================================
# TIER 3: ENCOUNTER TRIGGERS (5 tests)
# ==============================================================================

def test_trigger_encounter_success(scene_manager, encounter_scene, world_state, rng):
    """Tier 3: trigger_encounter() successfully triggers encounter."""
    result = scene_manager.trigger_encounter(
        scene=encounter_scene,
        world_state=world_state,
        rng=rng,
        trigger_condition="on_entry",
    )

    assert result is not None
    assert result.triggered is True
    assert result.encounter_id == "goblin_ambush_01"
    assert len(result.initiative_rolls) == 4  # 2 goblins + 2 party members
    assert len(result.initiative_order) == 4


def test_trigger_encounter_initiative_order(scene_manager, encounter_scene, world_state, rng):
    """Tier 3: encounter trigger produces valid initiative order."""
    result = scene_manager.trigger_encounter(
        scene=encounter_scene,
        world_state=world_state,
        rng=rng,
        trigger_condition="on_entry",
    )

    # All combatants should be in initiative order
    assert "goblin_01" in result.initiative_order
    assert "goblin_02" in result.initiative_order
    assert "fighter_01" in result.initiative_order
    assert "wizard_01" in result.initiative_order


def test_trigger_encounter_no_match(scene_manager, encounter_scene, world_state, rng):
    """Tier 3: trigger_encounter() returns None when no encounter matches."""
    result = scene_manager.trigger_encounter(
        scene=encounter_scene,
        world_state=world_state,
        rng=rng,
        trigger_condition="nonexistent_trigger",
    )

    assert result is None


def test_trigger_encounter_events(scene_manager, encounter_scene, world_state, rng):
    """Tier 3: encounter trigger generates correct events."""
    result = scene_manager.trigger_encounter(
        scene=encounter_scene,
        world_state=world_state,
        rng=rng,
        trigger_condition="on_entry",
    )

    assert len(result.events) == 2

    # Event 1: encounter_triggered
    assert result.events[0]["type"] == "encounter_triggered"
    assert result.events[0]["encounter_id"] == "goblin_ambush_01"
    assert result.events[0]["scene_id"] == "goblin_ambush"

    # Event 2: initiative_rolled
    assert result.events[1]["type"] == "initiative_rolled"
    assert "initiative_order" in result.events[1]
    assert "initiative_rolls" in result.events[1]


def test_trigger_encounter_narrative_hint(scene_manager, encounter_scene, world_state, rng):
    """Tier 3: encounter trigger provides narrative hint."""
    result = scene_manager.trigger_encounter(
        scene=encounter_scene,
        world_state=world_state,
        rng=rng,
        trigger_condition="on_entry",
    )

    assert "combat" in result.narrative_hint.lower()
    assert "2" in result.narrative_hint  # Number of enemies


# ==============================================================================
# TIER 4: REST MECHANICS (D&D 3.5E) (5 tests)
# ==============================================================================

def test_rest_8_hours_healing(scene_manager, world_state, rng):
    """Tier 4: 8 hours rest heals 1 HP per level (PHB p.146)."""
    result = scene_manager.process_rest(
        rest_type="8_hours",
        world_state=world_state,
        rng=rng,
    )

    assert result.rest_type == "8_hours"

    # Fighter: level 5 → 5 HP healed
    assert result.healing_applied["fighter_01"] == 5

    # Wizard: level 5 → 5 HP healed
    assert result.healing_applied["wizard_01"] == 5


def test_rest_long_term_care_healing(scene_manager, world_state, rng):
    """Tier 4: Long-term care heals 2 HP per level (PHB p.146)."""
    result = scene_manager.process_rest(
        rest_type="long_term_care",
        world_state=world_state,
        rng=rng,
    )

    assert result.rest_type == "long_term_care"

    # Fighter: level 5 → 10 HP healed
    assert result.healing_applied["fighter_01"] == 10

    # Wizard: level 5 → 5 HP healed (capped at max HP)
    # Wizard is at 20/25, so can only heal 5 HP
    assert result.healing_applied["wizard_01"] == 5


def test_rest_bed_rest_healing(scene_manager, world_state, rng):
    """Tier 4: Bed rest heals 1.5 HP per level (PHB p.146)."""
    result = scene_manager.process_rest(
        rest_type="bed_rest",
        world_state=world_state,
        rng=rng,
    )

    assert result.rest_type == "bed_rest"

    # Fighter: level 5 → int(5 * 1.5) = 7 HP healed
    assert result.healing_applied["fighter_01"] == 7

    # Wizard: level 5 → 5 HP healed (capped at max HP)
    assert result.healing_applied["wizard_01"] == 5


def test_rest_no_overheal(scene_manager, rng):
    """Tier 4: Rest healing does not exceed max HP."""
    # Create world state with near-full HP
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter_01": {
                EF.ENTITY_ID: "fighter_01",
                EF.TEAM: "party",
                EF.LEVEL: 5,
                EF.HP_CURRENT: 48,  # 2 HP from max
                EF.HP_MAX: 50,
            },
        },
    )

    result = scene_manager.process_rest(
        rest_type="8_hours",
        world_state=world_state,
        rng=rng,
    )

    # Should only heal 2 HP (not 5)
    assert result.healing_applied["fighter_01"] == 2


def test_rest_events_structure(scene_manager, world_state, rng):
    """Tier 4: Rest events have correct structure."""
    result = scene_manager.process_rest(
        rest_type="8_hours",
        world_state=world_state,
        rng=rng,
    )

    assert len(result.events) == 2  # One per party member

    for event in result.events:
        assert event["type"] == "rest_healing"
        assert "entity_id" in event
        assert "rest_type" in event
        assert event["rest_type"] == "8_hours"
        assert "healing_amount" in event
        assert "hp_before" in event
        assert "hp_after" in event


# ==============================================================================
# TIER 5: BOUNDARY LAW COMPLIANCE (3 tests)
# ==============================================================================

def test_frozen_world_state_view_read_only(scene_manager, encounter_scene, world_state, rng):
    """Tier 5: SceneManager uses FrozenWorldStateView for read-only access."""
    # trigger_encounter internally uses FrozenWorldStateView
    result = scene_manager.trigger_encounter(
        scene=encounter_scene,
        world_state=world_state,
        rng=rng,
        trigger_condition="on_entry",
    )

    # World state should be unchanged
    assert world_state.entities["fighter_01"][EF.HP_CURRENT] == 30
    assert world_state.entities["wizard_01"][EF.HP_CURRENT] == 20


def test_rest_does_not_mutate_world_state(scene_manager, world_state, rng):
    """Tier 5: process_rest() does not mutate world_state directly."""
    original_hp = world_state.entities["fighter_01"][EF.HP_CURRENT]

    result = scene_manager.process_rest(
        rest_type="8_hours",
        world_state=world_state,
        rng=rng,
    )

    # World state should be unchanged (events should be applied externally)
    assert world_state.entities["fighter_01"][EF.HP_CURRENT] == original_hp


def test_scene_manager_only_returns_events(scene_manager, world_state):
    """Tier 5: SceneManager returns events for event sourcing, not modified state."""
    result = scene_manager.transition_scene(
        from_scene="dungeon_entrance",
        exit_id="north",
        world_state=world_state,
    )

    # Result contains events, not modified WorldState
    assert isinstance(result.events, list)
    assert len(result.events) > 0
    assert isinstance(result.events[0], dict)


# ==============================================================================
# TIER 6: EDGE CASES (3 tests)
# ==============================================================================

def test_rest_only_heals_party_members(scene_manager, rng):
    """Tier 6: Rest only heals party members, not monsters."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter_01": {
                EF.ENTITY_ID: "fighter_01",
                EF.TEAM: "party",
                EF.LEVEL: 5,
                EF.HP_CURRENT: 30,
                EF.HP_MAX: 50,
            },
            "goblin_01": {
                EF.ENTITY_ID: "goblin_01",
                EF.TEAM: "monster",
                EF.LEVEL: 1,
                EF.HP_CURRENT: 3,
                EF.HP_MAX: 5,
            },
        },
    )

    result = scene_manager.process_rest(
        rest_type="8_hours",
        world_state=world_state,
        rng=rng,
    )

    # Only fighter should be healed
    assert "fighter_01" in result.healing_applied
    assert "goblin_01" not in result.healing_applied


def test_encounter_with_no_party_members(scene_manager, encounter_scene, rng):
    """Tier 6: Encounter trigger handles world state with no party members."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={},  # No entities
    )

    result = scene_manager.trigger_encounter(
        scene=encounter_scene,
        world_state=world_state,
        rng=rng,
        trigger_condition="on_entry",
    )

    # Should still trigger, but only roll initiative for monsters
    assert result is not None
    assert len(result.initiative_rolls) == 2  # Only 2 goblins


def test_scene_with_multiple_encounters(scene_manager, rng):
    """Tier 6: Scene can have multiple encounters with different triggers."""
    scene = SceneState(
        scene_id="multi_encounter",
        name="Multi Encounter",
        description="A dangerous room.",
        exits=[],
        encounters=[
            EncounterDef(
                encounter_id="enc_01",
                monster_ids=["orc_01"],
                trigger_condition="on_entry",
                initiative_data=[("orc_01", 0)],
                triggered=False,
            ),
            EncounterDef(
                encounter_id="enc_02",
                monster_ids=["troll_01"],
                trigger_condition="manual",
                initiative_data=[("troll_01", -1)],
                triggered=False,
            ),
        ],
    )

    manager = SceneManager(scenes={"multi_encounter": scene})

    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter_01": {
                EF.ENTITY_ID: "fighter_01",
                EF.TEAM: "party",
                EF.DEX_MOD: 2,
            },
        },
    )

    # Trigger first encounter
    result1 = manager.trigger_encounter(
        scene=scene,
        world_state=world_state,
        rng=rng,
        trigger_condition="on_entry",
    )

    assert result1.encounter_id == "enc_01"

    # Trigger second encounter (different condition)
    result2 = manager.trigger_encounter(
        scene=scene,
        world_state=world_state,
        rng=rng,
        trigger_condition="manual",
    )

    assert result2.encounter_id == "enc_02"


# ==============================================================================
# TIER 7: STM CLEAR ON TRANSITION (1 test)
# ==============================================================================

def test_stm_cleared_on_scene_transition(world_state):
    """Tier 7: STMContext.clear() is called on scene transition.

    After a scene transition, previously-tracked entity names must NOT
    resolve — 'attack him' should not carry over from the previous room.
    """
    from aidm.immersion.voice_intent_parser import STMContext

    stm = STMContext()
    stm.update(action="attack", target="goblin_01", weapon="longsword")
    assert stm.last_target == "goblin_01"
    assert stm.last_weapon == "longsword"
    assert len(stm.history) == 1

    scenes = {
        "room_a": SceneState(
            scene_id="room_a",
            name="Room A",
            description="First room.",
            exits=[Exit(exit_id="door", destination_scene_id="room_b", description="a door")],
        ),
        "room_b": SceneState(
            scene_id="room_b",
            name="Room B",
            description="Second room.",
        ),
    }

    manager = SceneManager(scenes=scenes, stm=stm)
    result = manager.transition_scene(
        from_scene="room_a",
        exit_id="door",
        world_state=world_state,
    )

    assert result.success is True
    # STM should be cleared — no carryover from previous room
    assert stm.last_target is None
    assert stm.last_weapon is None
    assert stm.last_action is None
    assert stm.last_spell is None
    assert stm.last_location is None
    assert stm.history == []
