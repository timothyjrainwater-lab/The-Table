"""Gate ENGINE-REST — WO-ENGINE-REST-001: Rest Mechanics + Slot Recovery.

Tests:
R-01: Overnight rest with depleted slots → spell_slots_restored event, slots back to max
R-02: Overnight rest with damaged HP → hp_restored event, HP increases
R-03: Overnight rest at full HP → no hp_restored event
R-04: Rest during active combat → rest_denied with reason "combat_active"
R-05: Full day rest → double HP healing rate
R-06: Non-caster rests → rest_completed event, no spell_slots_restored
R-07: Overnight rest clears fatigued condition
R-08: Dual-caster rests → both SPELL_SLOTS and SPELL_SLOTS_2 restored
R-09: Prepared caster (wizard) rests → SPELLS_PREPARED reset to match SPELLS_KNOWN
R-10: rest_completed event always emitted last
R-11: SPELL_SLOTS_MAX set at chargen for wizard L5 → correct slot table
R-12: SPELL_SLOTS_MAX unchanged after two full rests (immutable baseline)
"""

from copy import deepcopy
from typing import Any, Dict

import pytest

from aidm.core.rest_resolver import resolve_rest, RestResult
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.schemas.intents import RestIntent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_world_state(entities: Dict[str, Any], in_combat: bool = False) -> WorldState:
    """Build a minimal WorldState for rest tests."""
    active_combat = {"initiative_order": []} if in_combat else None
    return WorldState(
        ruleset_version="RAW_3.5",
        entities=entities,
        active_combat=active_combat,
    )


def _wizard_entity(
    entity_id: str = "wizard_pc",
    level: int = 5,
    con_mod: int = 1,
    hp_current: int = 20,
    hp_max: int = 30,
    spell_slots: Dict[int, int] = None,
    spell_slots_max: Dict[int, int] = None,
    spells_known: Dict[int, list] = None,
    spells_prepared: Dict[int, list] = None,
    conditions: list = None,
) -> Dict[str, Any]:
    if spell_slots is None:
        spell_slots = {1: 2, 2: 1}
    if spell_slots_max is None:
        spell_slots_max = {1: 4, 2: 3}
    if spells_known is None:
        spells_known = {1: ["magic_missile", "shield"], 2: ["blur"]}
    if spells_prepared is None:
        spells_prepared = {}
    return {
        EF.ENTITY_ID: entity_id,
        EF.TEAM: "player",
        EF.LEVEL: level,
        EF.CON_MOD: con_mod,
        EF.HP_CURRENT: hp_current,
        EF.HP_MAX: hp_max,
        EF.SPELL_SLOTS: dict(spell_slots),
        EF.SPELL_SLOTS_MAX: dict(spell_slots_max),
        EF.SPELLS_KNOWN: dict(spells_known),
        EF.SPELLS_PREPARED: dict(spells_prepared),
        EF.CASTER_CLASS: "wizard",
        EF.CASTER_LEVEL: level,
        EF.CONDITIONS: list(conditions) if conditions else [],
    }


def _fighter_entity(
    entity_id: str = "fighter_pc",
    level: int = 5,
    con_mod: int = 2,
    hp_current: int = 25,
    hp_max: int = 40,
    conditions: list = None,
) -> Dict[str, Any]:
    return {
        EF.ENTITY_ID: entity_id,
        EF.TEAM: "player",
        EF.LEVEL: level,
        EF.CON_MOD: con_mod,
        EF.HP_CURRENT: hp_current,
        EF.HP_MAX: hp_max,
        EF.CONDITIONS: list(conditions) if conditions else [],
        # Non-casters: no SPELL_SLOTS_MAX
    }


# ---------------------------------------------------------------------------
# R-01: Overnight rest with depleted slots → spell_slots_restored event, slots back to max
# ---------------------------------------------------------------------------

def test_R01_overnight_rest_restores_spell_slots():
    max_slots = {1: 4, 2: 3}
    actor = _wizard_entity(
        spell_slots={1: 0, 2: 0},   # fully depleted
        spell_slots_max=max_slots,
        hp_current=30, hp_max=30,   # full HP so no hp_restored event
    )
    ws = _make_world_state({"wizard_pc": actor})
    intent = RestIntent(rest_type="overnight")

    result = resolve_rest(intent, ws, "wizard_pc")

    event_types = [e["event_type"] for e in result.events]
    assert "spell_slots_restored" in event_types, "Expected spell_slots_restored event"

    restore_evt = next(e for e in result.events if e["event_type"] == "spell_slots_restored")
    assert restore_evt["payload"]["slots"] == max_slots

    # Entity slots now match max
    assert result.world_state.entities["wizard_pc"][EF.SPELL_SLOTS] == max_slots


# ---------------------------------------------------------------------------
# R-02: Overnight rest with damaged HP → hp_restored event, HP increases
# ---------------------------------------------------------------------------

def test_R02_overnight_rest_recovers_hp():
    # Level 5, CON mod +2 → heal = 5 * max(1, 2) = 10
    actor = _wizard_entity(
        level=5, con_mod=2,
        hp_current=10, hp_max=30,
        spell_slots={1: 4, 2: 3},   # full slots so no slot events
        spell_slots_max={1: 4, 2: 3},
    )
    ws = _make_world_state({"wizard_pc": actor})
    intent = RestIntent(rest_type="overnight")

    result = resolve_rest(intent, ws, "wizard_pc")

    event_types = [e["event_type"] for e in result.events]
    assert "hp_restored" in event_types

    hp_evt = next(e for e in result.events if e["event_type"] == "hp_restored")
    assert hp_evt["payload"]["amount"] == 10
    assert hp_evt["payload"]["new_hp"] == 20
    assert result.world_state.entities["wizard_pc"][EF.HP_CURRENT] == 20


# ---------------------------------------------------------------------------
# R-03: Overnight rest at full HP → no hp_restored event
# ---------------------------------------------------------------------------

def test_R03_overnight_rest_full_hp_no_hp_event():
    actor = _wizard_entity(
        level=5, con_mod=2,
        hp_current=30, hp_max=30,   # already full
        spell_slots={1: 4}, spell_slots_max={1: 4},
    )
    ws = _make_world_state({"wizard_pc": actor})
    intent = RestIntent(rest_type="overnight")

    result = resolve_rest(intent, ws, "wizard_pc")

    event_types = [e["event_type"] for e in result.events]
    assert "hp_restored" not in event_types


# ---------------------------------------------------------------------------
# R-04: Rest during active combat → rest_denied with reason "combat_active"
# ---------------------------------------------------------------------------

def test_R04_rest_denied_during_combat():
    actor = _wizard_entity()
    ws = _make_world_state({"wizard_pc": actor}, in_combat=True)
    intent = RestIntent(rest_type="overnight")

    result = resolve_rest(intent, ws, "wizard_pc")

    assert len(result.events) == 1
    evt = result.events[0]
    assert evt["event_type"] == "rest_denied"
    assert evt["payload"]["reason"] == "combat_active"


# ---------------------------------------------------------------------------
# R-05: Full day rest → double HP healing rate
# ---------------------------------------------------------------------------

def test_R05_full_day_rest_double_healing():
    # Level 4, CON mod +2 → overnight = 4 * 2 = 8, full_day = 16
    actor = _wizard_entity(
        level=4, con_mod=2,
        hp_current=5, hp_max=100,
        spell_slots={1: 4}, spell_slots_max={1: 4},
    )
    ws = _make_world_state({"wizard_pc": actor})
    intent = RestIntent(rest_type="full_day")

    result = resolve_rest(intent, ws, "wizard_pc")

    hp_evt = next(e for e in result.events if e["event_type"] == "hp_restored")
    expected_heal = 4 * max(1, 2) * 2  # 16
    assert hp_evt["payload"]["amount"] == expected_heal


# ---------------------------------------------------------------------------
# R-06: Non-caster rests → rest_completed event, no spell_slots_restored
# ---------------------------------------------------------------------------

def test_R06_noncaster_no_slot_events():
    actor = _fighter_entity(
        level=5, con_mod=2,
        hp_current=40, hp_max=40,   # full HP
    )
    ws = _make_world_state({"fighter_pc": actor})
    intent = RestIntent(rest_type="overnight")

    result = resolve_rest(intent, ws, "fighter_pc")

    event_types = [e["event_type"] for e in result.events]
    assert "spell_slots_restored" not in event_types
    assert "rest_completed" in event_types


# ---------------------------------------------------------------------------
# R-07: Overnight rest clears fatigued condition
# ---------------------------------------------------------------------------

def test_R07_overnight_rest_clears_fatigued():
    actor = _wizard_entity(
        hp_current=30, hp_max=30,
        spell_slots={1: 4}, spell_slots_max={1: 4},
        conditions=["fatigued"],
    )
    ws = _make_world_state({"wizard_pc": actor})
    intent = RestIntent(rest_type="overnight")

    result = resolve_rest(intent, ws, "wizard_pc")

    post_conditions = result.world_state.entities["wizard_pc"][EF.CONDITIONS]
    assert "fatigued" not in post_conditions

    # rest_completed payload should note the cleared condition
    rc_evt = next(e for e in result.events if e["event_type"] == "rest_completed")
    assert "fatigued" in rc_evt["payload"]["conditions_cleared"]


# ---------------------------------------------------------------------------
# R-08: Dual-caster rests → both SPELL_SLOTS and SPELL_SLOTS_2 restored
# ---------------------------------------------------------------------------

def test_R08_dual_caster_both_slot_pools_restored():
    primary_max = {1: 3, 2: 2}
    secondary_max = {1: 2}
    actor = {
        EF.ENTITY_ID: "mc_pc",
        EF.TEAM: "player",
        EF.LEVEL: 5,
        EF.CON_MOD: 1,
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 30,
        EF.SPELL_SLOTS: {1: 0, 2: 0},        # depleted
        EF.SPELL_SLOTS_MAX: dict(primary_max),
        EF.SPELL_SLOTS_2: {1: 0},             # depleted
        EF.SPELL_SLOTS_MAX_2: dict(secondary_max),
        EF.CASTER_CLASS: "wizard",
        EF.CASTER_CLASS_2: "cleric",
        EF.SPELLS_KNOWN: {},
        EF.SPELLS_PREPARED: {},
        EF.CONDITIONS: [],
    }
    ws = _make_world_state({"mc_pc": actor})
    intent = RestIntent(rest_type="overnight")

    result = resolve_rest(intent, ws, "mc_pc")

    restored_entity = result.world_state.entities["mc_pc"]
    assert restored_entity[EF.SPELL_SLOTS] == primary_max
    assert restored_entity[EF.SPELL_SLOTS_2] == secondary_max

    # Two spell_slots_restored events
    slot_events = [e for e in result.events if e["event_type"] == "spell_slots_restored"]
    assert len(slot_events) == 2
    caster_classes = {e["payload"]["caster_class"] for e in slot_events}
    assert "wizard" in caster_classes
    assert "cleric" in caster_classes


# ---------------------------------------------------------------------------
# R-09: Prepared caster (wizard) rests → SPELLS_PREPARED reset to SPELLS_KNOWN
# ---------------------------------------------------------------------------

def test_R09_prepared_caster_spells_prepared_reset():
    spells_known = {1: ["magic_missile", "shield"], 2: ["blur", "invisibility"]}
    actor = _wizard_entity(
        hp_current=30, hp_max=30,
        spell_slots={1: 4, 2: 3},
        spell_slots_max={1: 4, 2: 3},
        spells_known=spells_known,
        spells_prepared={},  # empty before rest
    )
    ws = _make_world_state({"wizard_pc": actor})
    intent = RestIntent(rest_type="overnight")

    result = resolve_rest(intent, ws, "wizard_pc")

    post_prepared = result.world_state.entities["wizard_pc"][EF.SPELLS_PREPARED]
    assert set(post_prepared.get(1, [])) == set(spells_known[1])
    assert set(post_prepared.get(2, [])) == set(spells_known[2])


# ---------------------------------------------------------------------------
# R-10: rest_completed event always emitted last
# ---------------------------------------------------------------------------

def test_R10_rest_completed_always_last():
    actor = _wizard_entity(
        level=5, con_mod=2,
        hp_current=10, hp_max=30,
        spell_slots={1: 0}, spell_slots_max={1: 4},
        conditions=["fatigued"],
    )
    ws = _make_world_state({"wizard_pc": actor})
    intent = RestIntent(rest_type="overnight")

    result = resolve_rest(intent, ws, "wizard_pc")

    assert len(result.events) >= 1
    assert result.events[-1]["event_type"] == "rest_completed"


# ---------------------------------------------------------------------------
# R-11: SPELL_SLOTS_MAX set at chargen for wizard L5 → correct slot table
# ---------------------------------------------------------------------------

def test_R11_chargen_wizard_l5_spell_slots_max():
    from aidm.chargen.builder import build_character

    entity = build_character(
        race="human",
        class_name="wizard",
        level=5,
        ability_overrides={"str": 10, "dex": 10, "con": 10, "int": 16, "wis": 10, "cha": 10},
    )

    # Wizard L5 with INT 16 (mod +3) → {0:4, 1:4, 2:3, 3:2} per PHB table + bonus spells
    assert EF.SPELL_SLOTS_MAX in entity, "SPELL_SLOTS_MAX must be set at chargen"
    slots_max = entity[EF.SPELL_SLOTS_MAX]
    assert slots_max == entity[EF.SPELL_SLOTS], "SPELL_SLOTS_MAX must equal SPELL_SLOTS at chargen"
    # Verify PHB values for wizard L5 with INT 16 (bonus spells at 1st, 2nd, 3rd)
    assert slots_max.get(1, 0) >= 4  # 4 first-level slots (3 base + 1 bonus)
    assert slots_max.get(2, 0) >= 3  # 3 second-level slots (2 base + 1 bonus)
    assert slots_max.get(3, 0) >= 2  # 2 third-level slots (1 base + 1 bonus)


# ---------------------------------------------------------------------------
# R-12: SPELL_SLOTS_MAX unchanged after two full rests (immutable baseline)
# ---------------------------------------------------------------------------

def test_R12_spell_slots_max_immutable_across_rests():
    initial_max = {1: 4, 2: 3}
    actor = _wizard_entity(
        level=5, con_mod=1,
        hp_current=30, hp_max=30,
        spell_slots={1: 0, 2: 0},        # depleted before first rest
        spell_slots_max=dict(initial_max),
    )
    ws = _make_world_state({"wizard_pc": actor})
    intent = RestIntent(rest_type="overnight")

    # First rest
    result1 = resolve_rest(intent, ws, "wizard_pc")
    ws_after_1 = result1.world_state

    # Verify max unchanged after first rest
    max_after_1 = ws_after_1.entities["wizard_pc"][EF.SPELL_SLOTS_MAX]
    assert max_after_1 == initial_max, "SPELL_SLOTS_MAX must not change after first rest"

    # Simulate slot depletion again
    ws_after_1.entities["wizard_pc"][EF.SPELL_SLOTS] = {1: 0, 2: 0}

    # Second rest
    result2 = resolve_rest(intent, ws_after_1, "wizard_pc")
    max_after_2 = result2.world_state.entities["wizard_pc"][EF.SPELL_SLOTS_MAX]
    assert max_after_2 == initial_max, "SPELL_SLOTS_MAX must not change after second rest"

    # Slots fully restored again
    assert result2.world_state.entities["wizard_pc"][EF.SPELL_SLOTS] == initial_max
