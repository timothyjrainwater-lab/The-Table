"""Gate ENGINE-SPELL-SLOTS — WO-ENGINE-SPELL-SLOTS-001: Spell Slot Governor.

Tests:
SS-01: Cast level-1 spell with 1 slot → succeeds, slot decrements to 0
SS-02: Cast level-1 spell with 0 slots → spell_slot_empty event, world unchanged
SS-03: Cast cantrip with depleted slots → succeeds (cantrips unlimited)
SS-04: Cast level-2 spell, level-1 depleted but level-2 available → succeeds
SS-05: Wizard casts unprepared spell → spell_slot_empty, reason spell_not_prepared
SS-06: Sorcerer casts unknown spell → spell_slot_empty, reason spell_not_known
SS-07: Non-caster (fighter) has no SPELL_SLOTS → spell_slot_empty, reason no_spell_slots
SS-08: Cleric casts from prepared list with slots available → succeeds, slot decrements
SS-09: Two sequential casts: first succeeds (slot 1→0), second fails (slot 0)
SS-10: Dual-caster: primary level exhausted, secondary has slots → succeeds via secondary
SS-11: Slot floor: decrement on already-0 slot stays at 0
SS-12: World state is unchanged on spell_slot_empty (no partial mutation)
"""

from copy import deepcopy
from typing import Any, Dict

import pytest

from aidm.core.play_loop import (
    TurnContext,
    execute_turn,
    _check_spell_slot,
    _check_spell_slot_for_dict,
    _validate_spell_known,
    _decrement_spell_slot,
)
from aidm.core.rng_manager import RNGManager
from aidm.core.state import WorldState
from aidm.core.spell_resolver import SpellCastIntent
from aidm.schemas.entity_fields import EF


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pos(x: int = 0, y: int = 0) -> dict:
    return {"x": x, "y": y}


def _caster_entity(
    eid: str,
    caster_class: str = "wizard",
    level_1_slots: int = 1,
    level_2_slots: int = 1,
    spells_prepared: Dict = None,
    spells_known: Dict = None,
    spell_slots_2: Dict = None,
    caster_class_2: str = None,
) -> Dict[str, Any]:
    """Build a minimal caster entity."""
    e: Dict[str, Any] = {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 30,
        EF.AC: 14,
        EF.DEX_MOD: 1,
        EF.STR_MOD: 0,
        EF.ATTACK_BONUS: 2,
        EF.BAB: 2,
        "bab": 2,
        EF.DEFEATED: False,
        EF.CONDITIONS: {},
        EF.POSITION: _pos(0, 0),
        EF.SIZE_CATEGORY: "medium",
        EF.SAVE_FORT: 2,
        EF.SAVE_REF: 2,
        EF.SAVE_WILL: 5,
        "caster_level": 3,
        "spell_dc_base": 13,
        EF.CASTER_CLASS: caster_class,
        EF.SPELL_SLOTS: {1: level_1_slots, 2: level_2_slots},
        EF.SPELLS_PREPARED: spells_prepared if spells_prepared is not None else {},
        EF.SPELLS_KNOWN: spells_known if spells_known is not None else {},
    }
    if spell_slots_2 is not None:
        e[EF.SPELL_SLOTS_2] = spell_slots_2
    if caster_class_2 is not None:
        e[EF.CASTER_CLASS_2] = caster_class_2
    return e


def _target_entity(eid: str = "enemy") -> Dict[str, Any]:
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "monsters",
        EF.HP_CURRENT: 20,
        EF.HP_MAX: 20,
        EF.AC: 12,
        EF.DEX_MOD: 0,
        EF.STR_MOD: 2,
        EF.ATTACK_BONUS: 3,
        EF.BAB: 3,
        "bab": 3,
        EF.DEFEATED: False,
        EF.CONDITIONS: {},
        EF.POSITION: _pos(0, 5),
        EF.SIZE_CATEGORY: "medium",
        EF.SAVE_FORT: 2,
        EF.SAVE_REF: 2,
        EF.SAVE_WILL: 1,
        "caster_level": 0,
        "spell_dc_base": 10,
    }


def _world(*entities) -> WorldState:
    ent_dict = {e[EF.ENTITY_ID]: e for e in entities}
    return WorldState(
        ruleset_version="3.5e",
        entities=ent_dict,
        active_combat={
            "initiative_order": [e[EF.ENTITY_ID] for e in entities],
            "aoo_used_this_round": [],
            "grapple_pairs": [],
        },
    )


def _cast(caster_id: str, spell_id: str, target_id: str) -> SpellCastIntent:
    return SpellCastIntent(
        caster_id=caster_id,
        spell_id=spell_id,
        target_entity_id=target_id,
        quickened=True,  # skip AoO to isolate slot logic
    )


def _run(ws: WorldState, caster_id: str, spell_id: str, target_id: str, seed: int = 0):
    """Execute a spell cast and return (result, final_world_state)."""
    rng = RNGManager(seed)
    ctx = TurnContext(actor_id=caster_id, actor_team="party", turn_index=0)
    intent = _cast(caster_id, spell_id, target_id)
    result = execute_turn(ws, ctx, combat_intent=intent, rng=rng)
    return result


# ---------------------------------------------------------------------------
# SS-01: Cast level-1 spell with 1 slot → succeeds, slot decrements to 0
# ---------------------------------------------------------------------------

def test_ss01_successful_cast_decrements_slot():
    wizard = _caster_entity(
        "wizard",
        caster_class="wizard",
        level_1_slots=1,
        spells_prepared={1: ["magic_missile"]},
    )
    target = _target_entity()
    ws = _world(wizard, target)

    result = _run(ws, "wizard", "magic_missile", "enemy")
    event_types = [e.event_type for e in result.events]

    # Spell resolved — spell_cast present, no spell_slot_empty
    assert "spell_cast" in event_types, f"Expected spell_cast, got: {event_types}"
    assert "spell_slot_empty" not in event_types

    # Slot decremented to 0
    final_slots = result.world_state.entities["wizard"][EF.SPELL_SLOTS]
    assert final_slots[1] == 0, f"Expected slot[1]==0, got {final_slots[1]}"


# ---------------------------------------------------------------------------
# SS-02: Cast level-1 spell with 0 slots → spell_slot_empty, world unchanged
# ---------------------------------------------------------------------------

def test_ss02_empty_slot_emits_event():
    wizard = _caster_entity(
        "wizard",
        caster_class="wizard",
        level_1_slots=0,
        spells_prepared={1: ["magic_missile"]},
    )
    target = _target_entity()
    ws = _world(wizard, target)
    ws_before = deepcopy(ws)

    result = _run(ws, "wizard", "magic_missile", "enemy")
    event_types = [e.event_type for e in result.events]

    assert "spell_slot_empty" in event_types, f"Expected spell_slot_empty, got: {event_types}"
    assert "spell_cast" not in event_types

    # Find the event
    ev = next(e for e in result.events if e.event_type == "spell_slot_empty")
    assert ev.payload["actor_id"] == "wizard"
    assert ev.payload["spell_level"] == 1


# ---------------------------------------------------------------------------
# SS-03: Cast cantrip with depleted slots → succeeds (cantrips unlimited)
# ---------------------------------------------------------------------------

def test_ss03_cantrip_bypasses_slot_check():
    wizard = _caster_entity(
        "wizard",
        caster_class="wizard",
        level_1_slots=0,
        level_2_slots=0,
        spells_prepared={0: ["detect_magic"]},
    )
    # detect_magic is self-targeting — target is the wizard itself
    ws = _world(wizard)

    result = _run(ws, "wizard", "detect_magic", "wizard")
    event_types = [e.event_type for e in result.events]

    assert "spell_slot_empty" not in event_types, f"Cantrip should not check slots; got: {event_types}"
    assert "spell_cast" in event_types, f"Expected spell_cast for cantrip; got: {event_types}"


# ---------------------------------------------------------------------------
# SS-04: Cast level-2 spell, level-1 depleted but level-2 available → succeeds
# ---------------------------------------------------------------------------

def test_ss04_correct_level_slot_targeted():
    wizard = _caster_entity(
        "wizard",
        caster_class="wizard",
        level_1_slots=0,
        level_2_slots=2,
        spells_prepared={2: ["scorching_ray"]},
    )
    target = _target_entity()
    ws = _world(wizard, target)

    result = _run(ws, "wizard", "scorching_ray", "enemy")
    event_types = [e.event_type for e in result.events]

    assert "spell_cast" in event_types, f"Expected spell_cast; got: {event_types}"
    assert "spell_slot_empty" not in event_types

    final_slots = result.world_state.entities["wizard"][EF.SPELL_SLOTS]
    assert final_slots[2] == 1, f"Expected slot[2] decremented to 1, got {final_slots[2]}"
    # Level-1 untouched (stays at 0)
    assert final_slots[1] == 0


# ---------------------------------------------------------------------------
# SS-05: Wizard casts unprepared spell → spell_slot_empty, reason spell_not_prepared
# ---------------------------------------------------------------------------

def test_ss05_wizard_unprepared_spell_fails():
    wizard = _caster_entity(
        "wizard",
        caster_class="wizard",
        level_1_slots=3,
        spells_prepared={1: ["shield"]},  # magic_missile NOT prepared
    )
    target = _target_entity()
    ws = _world(wizard, target)

    result = _run(ws, "wizard", "magic_missile", "enemy")
    event_types = [e.event_type for e in result.events]

    assert "spell_slot_empty" in event_types, f"Expected spell_slot_empty; got: {event_types}"
    ev = next(e for e in result.events if e.event_type == "spell_slot_empty")
    assert ev.payload["reason"] == "spell_not_prepared", f"Unexpected reason: {ev.payload['reason']}"

    # Slot must NOT have been decremented
    final_slots = result.world_state.entities["wizard"][EF.SPELL_SLOTS]
    assert final_slots[1] == 3, f"Slot should not have decremented; got {final_slots[1]}"


# ---------------------------------------------------------------------------
# SS-06: Sorcerer casts unknown spell → spell_slot_empty, reason spell_not_known
# ---------------------------------------------------------------------------

def test_ss06_sorcerer_unknown_spell_fails():
    sorc = _caster_entity(
        "sorc",
        caster_class="sorcerer",
        level_1_slots=4,
        spells_known={1: ["burning_hands"]},  # magic_missile NOT known
    )
    target = _target_entity()
    ws = _world(sorc, target)

    result = _run(ws, "sorc", "magic_missile", "enemy")
    event_types = [e.event_type for e in result.events]

    assert "spell_slot_empty" in event_types, f"Expected spell_slot_empty; got: {event_types}"
    ev = next(e for e in result.events if e.event_type == "spell_slot_empty")
    assert ev.payload["reason"] == "spell_not_known", f"Unexpected reason: {ev.payload['reason']}"


# ---------------------------------------------------------------------------
# SS-07: Non-caster (fighter) has no SPELL_SLOTS → spell_slot_empty, reason no_spell_slots
# ---------------------------------------------------------------------------

def test_ss07_non_caster_gets_no_spell_slots():
    fighter: Dict[str, Any] = {
        EF.ENTITY_ID: "fighter",
        EF.TEAM: "party",
        EF.HP_CURRENT: 40,
        EF.HP_MAX: 40,
        EF.AC: 16,
        EF.DEX_MOD: 1,
        EF.STR_MOD: 3,
        EF.ATTACK_BONUS: 5,
        EF.BAB: 5,
        "bab": 5,
        EF.DEFEATED: False,
        EF.CONDITIONS: {},
        EF.POSITION: _pos(0, 0),
        EF.SIZE_CATEGORY: "medium",
        EF.SAVE_FORT: 4,
        EF.SAVE_REF: 1,
        EF.SAVE_WILL: 1,
        "caster_level": 0,
        "spell_dc_base": 10,
        # No EF.SPELL_SLOTS key
    }
    target = _target_entity()
    ws = _world(fighter, target)

    result = _run(ws, "fighter", "magic_missile", "enemy")
    event_types = [e.event_type for e in result.events]

    assert "spell_slot_empty" in event_types, f"Expected spell_slot_empty for non-caster; got: {event_types}"
    ev = next(e for e in result.events if e.event_type == "spell_slot_empty")
    assert ev.payload["reason"] == "no_spell_slots", f"Unexpected reason: {ev.payload['reason']}"


# ---------------------------------------------------------------------------
# SS-08: Cleric casts from prepared list with slots available → succeeds, slot decrements
# ---------------------------------------------------------------------------

def test_ss08_cleric_prepared_spell_succeeds():
    cleric = _caster_entity(
        "cleric",
        caster_class="cleric",
        level_1_slots=3,
        spells_prepared={1: ["cure_light_wounds"]},
    )
    # cure_light_wounds is TOUCH/HEALING — target can be self
    ws = _world(cleric)

    result = _run(ws, "cleric", "cure_light_wounds", "cleric")
    event_types = [e.event_type for e in result.events]

    assert "spell_slot_empty" not in event_types, f"Unexpected slot failure; got: {event_types}"
    assert "spell_cast" in event_types, f"Expected spell_cast; got: {event_types}"

    final_slots = result.world_state.entities["cleric"][EF.SPELL_SLOTS]
    assert final_slots[1] == 2, f"Expected slot[1]==2 after cast, got {final_slots[1]}"


# ---------------------------------------------------------------------------
# SS-09: Two sequential casts: first succeeds (slot 1→0), second fails (slot 0)
# ---------------------------------------------------------------------------

def test_ss09_two_sequential_casts():
    wizard = _caster_entity(
        "wizard",
        caster_class="wizard",
        level_1_slots=1,
        spells_prepared={1: ["magic_missile"]},
    )
    target = _target_entity()
    ws = _world(wizard, target)

    # First cast — should succeed
    result1 = _run(ws, "wizard", "magic_missile", "enemy", seed=0)
    event_types1 = [e.event_type for e in result1.events]
    assert "spell_cast" in event_types1, f"First cast should succeed; got: {event_types1}"
    assert result1.world_state.entities["wizard"][EF.SPELL_SLOTS][1] == 0

    # Simulate start of new turn by resetting action budget in active_combat
    ws2 = result1.world_state
    if ws2.active_combat is not None:
        ac = deepcopy(ws2.active_combat)
        ac.pop("action_budget", None)
        ac.pop("action_budget_actor", None)
        ws2 = WorldState(
            ruleset_version=ws2.ruleset_version,
            entities=ws2.entities,
            active_combat=ac,
        )

    # Second cast from updated world state — should fail (slot=0)
    result2 = _run(ws2, "wizard", "magic_missile", "enemy", seed=0)
    event_types2 = [e.event_type for e in result2.events]
    assert "spell_slot_empty" in event_types2, f"Second cast should fail; got: {event_types2}"
    assert "spell_cast" not in event_types2


# ---------------------------------------------------------------------------
# SS-10: Dual-caster: primary level exhausted, secondary has slots → succeeds via secondary
# ---------------------------------------------------------------------------

def test_ss10_dual_caster_falls_back_to_secondary():
    # wizard/sorcerer dual: primary (wizard) level-1 empty, secondary (sorcerer) has level-1 slots
    dual = _caster_entity(
        "dual",
        caster_class="wizard",
        level_1_slots=0,      # primary exhausted
        level_2_slots=0,
        spells_prepared={},   # wizard has nothing prepared at level 1
        spell_slots_2={1: 2, 2: 1},
        caster_class_2="sorcerer",
    )
    # Also give SPELLS_KNOWN_2 so secondary known check is satisfied
    dual[EF.SPELLS_KNOWN_2] = {1: ["magic_missile"]}
    target = _target_entity()
    ws = _world(dual, target)

    result = _run(ws, "dual", "magic_missile", "enemy")
    event_types = [e.event_type for e in result.events]

    assert "spell_cast" in event_types, f"Dual-caster fallback should succeed; got: {event_types}"
    assert "spell_slot_empty" not in event_types

    # Secondary slot must be decremented
    final_slots_2 = result.world_state.entities["dual"][EF.SPELL_SLOTS_2]
    assert final_slots_2[1] == 1, f"Expected secondary slot[1]==1, got {final_slots_2[1]}"
    # Primary slot untouched (still 0)
    assert result.world_state.entities["dual"][EF.SPELL_SLOTS][1] == 0


# ---------------------------------------------------------------------------
# SS-11: Slot floor: decrement on already-0 slot stays at 0 (unit test helper)
# ---------------------------------------------------------------------------

def test_ss11_decrement_floor_at_zero():
    entity_state: Dict[str, Any] = {EF.SPELL_SLOTS: {1: 0, 2: 3}}

    _decrement_spell_slot(entity_state, 1)
    assert entity_state[EF.SPELL_SLOTS][1] == 0, "Slot must not go below 0"

    # Also verify normal decrement still works
    _decrement_spell_slot(entity_state, 2)
    assert entity_state[EF.SPELL_SLOTS][2] == 2


# ---------------------------------------------------------------------------
# SS-12: World state unchanged on spell_slot_empty (no partial mutation)
# ---------------------------------------------------------------------------

def test_ss12_world_state_unchanged_on_failure():
    wizard = _caster_entity(
        "wizard",
        caster_class="wizard",
        level_1_slots=0,
        spells_prepared={1: ["magic_missile"]},
    )
    target = _target_entity()
    ws = _world(wizard, target)
    ws_before = deepcopy(ws)

    result = _run(ws, "wizard", "magic_missile", "enemy")

    # Confirm failure path
    event_types = [e.event_type for e in result.events]
    assert "spell_slot_empty" in event_types

    # Entities in returned world state must be identical to original
    for eid, ent in result.world_state.entities.items():
        for key, val in ent.items():
            assert val == ws_before.entities[eid][key], (
                f"Entity {eid} field '{key}' mutated on failure: {val!r} != {ws_before.entities[eid][key]!r}"
            )
