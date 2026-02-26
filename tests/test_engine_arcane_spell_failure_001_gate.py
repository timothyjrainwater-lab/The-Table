"""Gate tests: ENGINE-ARCANE-SPELL-FAILURE-001 — WO-ENGINE-ARCANE-SPELL-FAILURE-001.

Tests:
AF-001: Arcane caster ASF 25%; somatic spell; roll<=25 — spell fails, slot consumed
AF-002: Arcane caster ASF 25%; somatic spell; roll>25 — spell resolves normally
AF-003: Arcane caster ASF 25%; non-somatic spell (V only) — no ASF check
AF-004: Arcane caster ASF 0% (unarmored) — no ASF check regardless
AF-005: Divine caster (cleric); somatic spell — no ASF check
AF-006: ASF 100%: somatic spell always fails (roll=100)
AF-007: ASF roll exactly at boundary (roll==ASF%) — spell fails
AF-008: Entity with no EF.ARCANE_SPELL_FAILURE field — no crash, spell resolves

PHB p.123 / p.175: ASF% roll <= threshold means spell fails, slot consumed.
"""

import pytest
from copy import deepcopy
from unittest.mock import patch

from aidm.core.state import WorldState
from aidm.core.play_loop import execute_turn, TurnContext
from aidm.core.rng_manager import RNGManager
from aidm.schemas.entity_fields import EF
from aidm.schemas.position import Position
from aidm.data.spell_definitions import SPELL_REGISTRY
from aidm.core.spell_resolver import SpellCastIntent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _wizard(asf=0, feats=None, slots=None):
    if slots is None:
        slots = {1: 4, 2: 3, 3: 3, 4: 2, 5: 1}
    return {
        EF.ENTITY_ID: "wizard",
        EF.TEAM: "party",
        EF.HP_CURRENT: 20, EF.HP_MAX: 20, EF.AC: 12, EF.DEFEATED: False,
        EF.POSITION: {"x": 0, "y": 0},
        EF.SAVE_FORT: 1, EF.SAVE_REF: 2, EF.SAVE_WILL: 5,
        EF.CON_MOD: 1, EF.DEX_MOD: 1, EF.WIS_MOD: 1,
        EF.CONDITIONS: {},
        EF.FEATS: feats if feats is not None else [],
        EF.TEMPORARY_MODIFIERS: {},
        EF.CLASS_LEVELS: {"wizard": 5},
        EF.SPELL_SLOTS: slots,
        EF.SPELLS_PREPARED: {0: ["message"], 1: ["magic_missile"], 3: ["fireball"]},
        EF.CASTER_CLASS: "wizard",
        EF.ARCANE_SPELL_FAILURE: asf,
        "caster_level": 5,
        "spell_dc_base": 14,
    }


def _cleric(asf=0, slots=None):
    if slots is None:
        slots = {1: 4, 2: 3, 3: 3}
    return {
        EF.ENTITY_ID: "cleric",
        EF.TEAM: "party",
        EF.HP_CURRENT: 25, EF.HP_MAX: 25, EF.AC: 16, EF.DEFEATED: False,
        EF.POSITION: {"x": 0, "y": 0},
        EF.SAVE_FORT: 5, EF.SAVE_REF: 2, EF.SAVE_WILL: 7,
        EF.CON_MOD: 2, EF.DEX_MOD: 1, EF.WIS_MOD: 3,
        EF.CONDITIONS: {}, EF.FEATS: [], EF.TEMPORARY_MODIFIERS: {},
        EF.CLASS_LEVELS: {"cleric": 5},
        EF.SPELL_SLOTS: slots,
        EF.SPELLS_PREPARED: {1: ["cure_light_wounds"], 3: ["cure_serious_wounds"]},
        EF.CASTER_CLASS: "cleric",
        EF.ARCANE_SPELL_FAILURE: asf,
        "caster_level": 5,
        "spell_dc_base": 15,
    }


def _goblin():
    return {
        EF.ENTITY_ID: "goblin", EF.TEAM: "monsters",
        EF.HP_CURRENT: 10, EF.HP_MAX: 10, EF.AC: 13, EF.DEFEATED: False,
        EF.POSITION: {"x": 5, "y": 5},
        EF.SAVE_FORT: 1, EF.SAVE_REF: 2, EF.SAVE_WILL: -1,
        EF.CON_MOD: 1, EF.DEX_MOD: 2, EF.WIS_MOD: 0,
        EF.CONDITIONS: {}, EF.FEATS: [],
    }


def _world_wiz(asf=0, feats=None, slots=None):
    return WorldState(
        ruleset_version="3.5e",
        entities={"wizard": _wizard(asf=asf, feats=feats, slots=slots), "goblin": _goblin()},
        active_combat={"initiative_order": ["wizard", "goblin"], "aoo_used_this_round": []},
    )


def _world_cleric(asf=0):
    return WorldState(
        ruleset_version="3.5e",
        entities={"cleric": _cleric(asf=asf), "goblin": _goblin()},
        active_combat={"initiative_order": ["cleric", "goblin"], "aoo_used_this_round": []},
    )


def _do_cast(ws, caster_id, spell_id, target_id=None, target_pos=None, seed=42):
    tc = TurnContext(turn_index=0, actor_id=caster_id, actor_team="party")
    intent = SpellCastIntent(
        caster_id=caster_id, spell_id=spell_id,
        target_entity_id=target_id, target_position=target_pos,
    )
    return execute_turn(ws, turn_ctx=tc, combat_intent=intent,
                        rng=RNGManager(master_seed=seed), next_event_id=0, timestamp=1.0)


# ---------------------------------------------------------------------------
# AF-001: ASF 25%, somatic spell, roll<=25 — spell fails, slot consumed
# ---------------------------------------------------------------------------

def test_af001_asf_fails_slot_consumed():
    """AF-001: ASF=25, somatic spell, roll=10 → spell fails, spell_failed_asf, slot consumed."""
    initial_slots = {1: 4, 2: 3, 3: 2, 4: 2, 5: 1}
    ws = _world_wiz(asf=25, slots=deepcopy(initial_slots))
    with patch("aidm.core.play_loop.random.randint", return_value=10):
        result = _do_cast(ws, "wizard", "fireball", target_pos=Position(x=5, y=5))
    assert result.narration == "spell_failed_asf"
    evs = [e for e in result.events if e.event_type == "spell_failed_asf"]
    assert len(evs) == 1
    assert evs[0].payload["asf_pct"] == 25
    assert evs[0].payload["roll"] == 10
    assert evs[0].payload["slot_consumed"] is True
    # Confirm slot decremented
    new_slots = result.world_state.entities["wizard"][EF.SPELL_SLOTS]
    assert new_slots[3] == initial_slots[3] - 1


# ---------------------------------------------------------------------------
# AF-002: ASF 25%, somatic spell, roll>25 — spell resolves normally
# ---------------------------------------------------------------------------

def test_af002_asf_high_roll_spell_succeeds():
    """AF-002: ASF=25, somatic spell, roll=50 → spell resolves normally."""
    ws = _world_wiz(asf=25)
    with patch("aidm.core.play_loop.random.randint", return_value=50):
        result = _do_cast(ws, "wizard", "fireball", target_pos=Position(x=5, y=5))
    assert result.narration != "spell_failed_asf"
    assert not [e for e in result.events if e.event_type == "spell_failed_asf"]


# ---------------------------------------------------------------------------
# AF-003: Arcane caster, non-somatic spell (V only) — no ASF check
# ---------------------------------------------------------------------------

def test_af003_v_only_spell_no_asf():
    """AF-003: message (has_somatic=False), ASF=100 — no ASF check fires."""
    ws = _world_wiz(asf=100)
    with patch("aidm.core.play_loop.random.randint", return_value=1):
        result = _do_cast(ws, "wizard", "message", target_id="goblin")
    assert not [e for e in result.events if e.event_type == "spell_failed_asf"]


# ---------------------------------------------------------------------------
# AF-004: Arcane caster ASF=0 (unarmored) — no ASF check regardless
# ---------------------------------------------------------------------------

def test_af004_asf_zero_no_check():
    """AF-004: ASF=0 — no ASF check regardless of spell components."""
    ws = _world_wiz(asf=0)
    with patch("aidm.core.play_loop.random.randint", return_value=1):
        result = _do_cast(ws, "wizard", "fireball", target_pos=Position(x=5, y=5))
    assert not [e for e in result.events if e.event_type == "spell_failed_asf"]


# ---------------------------------------------------------------------------
# AF-005: Divine caster (cleric) — no ASF even if field is set
# ---------------------------------------------------------------------------

def test_af005_divine_caster_immune_to_asf():
    """AF-005: Cleric has ASF=30 but is divine — no spell_failed_asf fires."""
    ws = _world_cleric(asf=30)
    with patch("aidm.core.play_loop.random.randint", return_value=5):
        result = _do_cast(ws, "cleric", "cure_light_wounds", target_id="cleric")
    assert not [e for e in result.events if e.event_type == "spell_failed_asf"]


# ---------------------------------------------------------------------------
# AF-006: ASF=100%; somatic spell always fails
# ---------------------------------------------------------------------------

def test_af006_asf_100_always_fails():
    """AF-006: ASF=100, roll=100 (at boundary) — spell always fails."""
    ws = _world_wiz(asf=100)
    with patch("aidm.core.play_loop.random.randint", return_value=100):
        result = _do_cast(ws, "wizard", "fireball", target_pos=Position(x=5, y=5))
    assert result.narration == "spell_failed_asf"


# ---------------------------------------------------------------------------
# AF-007: Roll exactly at ASF% boundary — spell fails (<=threshold is failure)
# ---------------------------------------------------------------------------

def test_af007_asf_boundary_roll_equals_threshold_fails():
    """AF-007: ASF=20, roll=20 (exactly at boundary) — spell fails."""
    ws = _world_wiz(asf=20)
    with patch("aidm.core.play_loop.random.randint", return_value=20):
        result = _do_cast(ws, "wizard", "fireball", target_pos=Position(x=5, y=5))
    assert result.narration == "spell_failed_asf"


# ---------------------------------------------------------------------------
# AF-008: Entity with no EF.ARCANE_SPELL_FAILURE field — no crash
# ---------------------------------------------------------------------------

def test_af008_no_asf_field_no_crash():
    """AF-008: EF.ARCANE_SPELL_FAILURE absent from entity dict — no crash, spell resolves."""
    wiz = _wizard(asf=0)
    del wiz[EF.ARCANE_SPELL_FAILURE]  # Remove field entirely
    ws = WorldState(
        ruleset_version="3.5e",
        entities={"wizard": wiz, "goblin": _goblin()},
        active_combat={"initiative_order": ["wizard", "goblin"], "aoo_used_this_round": []},
    )
    with patch("aidm.core.play_loop.random.randint", return_value=50):
        result = _do_cast(ws, "wizard", "fireball", target_pos=Position(x=5, y=5))
    assert not [e for e in result.events if e.event_type == "spell_failed_asf"]
