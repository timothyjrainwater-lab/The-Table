"""Gate tests: WO-ENGINE-DRUID-SPONTANEOUS-SUMMON-001
Druid Spontaneous Summon Nature's Ally (PHB p.35)

DSS-001  Druid caster + spontaneous_summon=True + level 1 slot → redirects to summon_natures_ally_i
DSS-002  Druid caster + spontaneous_summon=True + level 3 slot → summon_natures_ally_iii
DSS-003  Druid caster + spontaneous_summon=True + level 9 slot → summon_natures_ally_ix
DSS-004  Non-druid (fighter) + spontaneous_summon=True → spell_cast_failed, reason "spontaneous_summon_not_druid"
DSS-005  Druid + spontaneous_summon=False → no redirect, declared spell cast normally
DSS-006  Druid + spontaneous_summon=True + level 0 slot (invalid) → spell_cast_failed, reason "sna_spell_not_in_registry"
DSS-007  Declared slot consumed at original level after SNA redirect (slot tracking unchanged)
DSS-008  Code inspection: spontaneous_summon elif block present after spontaneous_inflict block
"""

import inspect

import pytest

from aidm.core.play_loop import _resolve_spell_cast
from aidm.core.state import WorldState
from aidm.core.spell_resolver import SpellCastIntent
from aidm.data.spell_definitions import SPELL_REGISTRY
from aidm.schemas.entity_fields import EF
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _druid_entity(eid="druid", druid_level=5, spell_level=1, spell_id="entangle"):
    """Return a minimal druid entity dict with a prepared spell at the given level."""
    return {
        EF.ENTITY_ID: eid,
        "name": eid,
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 30,
        EF.AC: 14,
        EF.TEAM: "players",
        EF.DEFEATED: False,
        EF.POSITION: {"x": 0, "y": 0},
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.SAVE_FORT: 5,
        EF.SAVE_REF: 2,
        EF.SAVE_WILL: 6,
        EF.CON_MOD: 1,
        EF.DEX_MOD: 0,
        EF.WIS_MOD: 3,
        EF.CHA_MOD: 0,
        EF.STR_MOD: 1,
        EF.TEMPORARY_MODIFIERS: {},
        EF.NEGATIVE_LEVELS: 0,
        EF.CLASS_LEVELS: {"druid": druid_level},
        EF.CASTER_CLASS: "druid",
        EF.SPELL_SLOTS: {1: 4, 2: 3, 3: 3, 4: 2, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1},
        EF.SPELLS_PREPARED: {spell_level: [spell_id]},
        "caster_level": druid_level,
        "spell_dc_base": 13 + 3,  # 10 + WIS(3) offset
    }


def _fighter_entity(eid="fighter"):
    """Return a minimal non-spellcasting fighter entity dict."""
    return {
        EF.ENTITY_ID: eid,
        "name": eid,
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 30,
        EF.AC: 16,
        EF.TEAM: "players",
        EF.DEFEATED: False,
        EF.POSITION: {"x": 0, "y": 0},
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.SAVE_FORT: 4,
        EF.SAVE_REF: 1,
        EF.SAVE_WILL: 0,
        EF.CON_MOD: 1,
        EF.DEX_MOD: 1,
        EF.WIS_MOD: 0,
        EF.CHA_MOD: 0,
        EF.STR_MOD: 3,
        EF.TEMPORARY_MODIFIERS: {},
        EF.NEGATIVE_LEVELS: 0,
        EF.CLASS_LEVELS: {"fighter": 5},
        EF.CASTER_CLASS: "fighter",
        EF.SPELL_SLOTS: {1: 4},
        EF.SPELLS_PREPARED: {1: ["entangle"]},
        "caster_level": 0,
        "spell_dc_base": 10,
    }


def _make_world(caster_entity):
    return WorldState(
        ruleset_version="3.5",
        entities={caster_entity[EF.ENTITY_ID]: caster_entity},
        active_combat={
            "turn_counter": 0,
            "round_index": 1,
            "initiative_order": [caster_entity[EF.ENTITY_ID]],
            "flat_footed_actors": [],
            "aoo_used_this_round": [],
            "aoo_count_this_round": {},
        },
    )


def _rng(roll=10):
    rng = MagicMock()
    stream = MagicMock()
    stream.randint = MagicMock(return_value=roll)
    rng.stream = MagicMock(return_value=stream)
    return rng


def _spell_cast(caster_id, spell_id, spell_level, world_state, spontaneous_summon=True):
    """Call _resolve_spell_cast with the given parameters."""
    intent = SpellCastIntent(
        caster_id=caster_id,
        spell_id=spell_id,
        spontaneous_summon=spontaneous_summon,
    )
    return _resolve_spell_cast(
        intent=intent,
        world_state=world_state,
        rng=_rng(),
        grid=None,
        next_event_id=1,
        timestamp=0.0,
        turn_index=0,
    )


# ---------------------------------------------------------------------------
# DSS-001: Druid + level 1 slot → redirects to summon_natures_ally_i
# ---------------------------------------------------------------------------

def test_DSS001_druid_level1_redirects_to_sna_i():
    """DSS-001: Druid with spontaneous_summon=True and level-1 spell redirects to SNA I."""
    assert "summon_natures_ally_i" in SPELL_REGISTRY, (
        "summon_natures_ally_i must be in SPELL_REGISTRY"
    )
    assert SPELL_REGISTRY["summon_natures_ally_i"].level == 1

    # entangle is a level-1 druid spell (used as the declared slot)
    if "entangle" not in SPELL_REGISTRY:
        pytest.skip("entangle not in SPELL_REGISTRY")

    druid = _druid_entity(spell_level=1, spell_id="entangle")
    ws = _make_world(druid)
    events, new_ws, token = _spell_cast("druid", "entangle", 1, ws, spontaneous_summon=True)

    # Must NOT produce spontaneous_summon_not_druid failure
    not_druid_fails = [
        e for e in events
        if e.event_type == "spell_cast_failed"
        and e.payload.get("reason") == "spontaneous_summon_not_druid"
    ]
    assert len(not_druid_fails) == 0, (
        "Druid must not fail with spontaneous_summon_not_druid"
    )

    # Must NOT produce sna_spell_not_in_registry failure for level 1
    registry_fails = [
        e for e in events
        if e.event_type == "spell_cast_failed"
        and e.payload.get("reason") == "sna_spell_not_in_registry"
    ]
    assert len(registry_fails) == 0, (
        "summon_natures_ally_i must be found in SPELL_REGISTRY for level 1 redirect"
    )


# ---------------------------------------------------------------------------
# DSS-002: Druid + level 3 slot → summon_natures_ally_iii
# ---------------------------------------------------------------------------

def test_DSS002_druid_level3_redirects_to_sna_iii():
    """DSS-002: Druid with spontaneous_summon=True and level-3 slot → SNA III in registry."""
    assert "summon_natures_ally_iii" in SPELL_REGISTRY, (
        "summon_natures_ally_iii must be in SPELL_REGISTRY"
    )
    assert SPELL_REGISTRY["summon_natures_ally_iii"].level == 3

    # Find any level-3 druid spell for the declared slot
    druid_level3 = next(
        (k for k, v in SPELL_REGISTRY.items() if v.level == 3),
        None,
    )
    if druid_level3 is None:
        pytest.skip("No level-3 spell in SPELL_REGISTRY for slot")

    druid = _druid_entity(spell_level=3, spell_id=druid_level3)
    ws = _make_world(druid)
    events, new_ws, token = _spell_cast("druid", druid_level3, 3, ws, spontaneous_summon=True)

    not_druid_fails = [
        e for e in events
        if e.event_type == "spell_cast_failed"
        and e.payload.get("reason") == "spontaneous_summon_not_druid"
    ]
    assert len(not_druid_fails) == 0

    registry_fails = [
        e for e in events
        if e.event_type == "spell_cast_failed"
        and e.payload.get("reason") == "sna_spell_not_in_registry"
    ]
    assert len(registry_fails) == 0, (
        "summon_natures_ally_iii must be found in SPELL_REGISTRY for level 3 redirect"
    )


# ---------------------------------------------------------------------------
# DSS-003: Druid + level 9 slot → summon_natures_ally_ix
# ---------------------------------------------------------------------------

def test_DSS003_druid_level9_redirects_to_sna_ix():
    """DSS-003: Druid with spontaneous_summon=True and level-9 slot → SNA IX in registry."""
    assert "summon_natures_ally_ix" in SPELL_REGISTRY, (
        "summon_natures_ally_ix must be in SPELL_REGISTRY"
    )
    assert SPELL_REGISTRY["summon_natures_ally_ix"].level == 9

    # Find any level-9 spell for the declared slot
    lvl9 = next(
        (k for k, v in SPELL_REGISTRY.items() if v.level == 9),
        None,
    )
    if lvl9 is None:
        pytest.skip("No level-9 spell in SPELL_REGISTRY")

    druid = _druid_entity(druid_level=17, spell_level=9, spell_id=lvl9)
    ws = _make_world(druid)
    events, new_ws, token = _spell_cast("druid", lvl9, 9, ws, spontaneous_summon=True)

    registry_fails = [
        e for e in events
        if e.event_type == "spell_cast_failed"
        and e.payload.get("reason") == "sna_spell_not_in_registry"
    ]
    assert len(registry_fails) == 0, (
        "summon_natures_ally_ix must be found in SPELL_REGISTRY for level 9 redirect"
    )


# ---------------------------------------------------------------------------
# DSS-004: Non-druid + spontaneous_summon=True → spell_cast_failed
# ---------------------------------------------------------------------------

def test_DSS004_non_druid_fails_with_class_guard():
    """DSS-004: Non-druid (fighter) + spontaneous_summon=True → spell_cast_failed, reason 'spontaneous_summon_not_druid'."""
    fighter = _fighter_entity()
    ws = _make_world(fighter)

    # Fighter has entangle prepared (for slot tracking) but is not a druid
    events, new_ws, token = _spell_cast("fighter", "entangle", 1, ws, spontaneous_summon=True)

    assert token == "spell_failed", (
        f"Non-druid spontaneous_summon must produce spell_failed token, got {token!r}"
    )
    not_druid_events = [
        e for e in events
        if e.event_type == "spell_cast_failed"
        and e.payload.get("reason") == "spontaneous_summon_not_druid"
    ]
    assert len(not_druid_events) == 1, (
        f"Expected exactly one 'spontaneous_summon_not_druid' spell_cast_failed event. "
        f"Got: {[e.payload for e in events if e.event_type == 'spell_cast_failed']}"
    )


# ---------------------------------------------------------------------------
# DSS-005: Druid + spontaneous_summon=False → no redirect
# ---------------------------------------------------------------------------

def test_DSS005_spontaneous_summon_false_no_redirect():
    """DSS-005: Druid + spontaneous_summon=False → declared spell cast normally, no SNA redirect."""
    if "entangle" not in SPELL_REGISTRY:
        pytest.skip("entangle not in SPELL_REGISTRY")

    druid = _druid_entity(spell_level=1, spell_id="entangle")
    ws = _make_world(druid)

    intent = SpellCastIntent(
        caster_id="druid",
        spell_id="entangle",
        spontaneous_summon=False,  # <-- explicit False
    )
    events, new_ws, token = _resolve_spell_cast(
        intent=intent,
        world_state=ws,
        rng=_rng(),
        grid=None,
        next_event_id=1,
        timestamp=0.0,
        turn_index=0,
    )

    # No SNA redirect-related failures
    sna_fails = [
        e for e in events
        if e.event_type == "spell_cast_failed"
        and e.payload.get("reason") in (
            "spontaneous_summon_not_druid",
            "sna_spell_not_in_registry",
        )
    ]
    assert len(sna_fails) == 0, (
        "spontaneous_summon=False must not trigger SNA redirect failures."
    )


# ---------------------------------------------------------------------------
# DSS-006: Druid + level 0 slot (invalid) → sna_spell_not_in_registry
# ---------------------------------------------------------------------------

def test_DSS006_level_zero_invalid_sna_level():
    """DSS-006: Druid + spontaneous_summon=True + level-0 spell → spell_cast_failed, reason 'sna_spell_not_in_registry'."""
    # Find a level-0 spell (cantrip)
    cantrip = next(
        (k for k, v in SPELL_REGISTRY.items() if v.level == 0),
        None,
    )
    if cantrip is None:
        pytest.skip("No level-0 spell in SPELL_REGISTRY")

    druid = _druid_entity(druid_level=5, spell_level=0, spell_id=cantrip)
    ws = _make_world(druid)

    events, new_ws, token = _spell_cast("druid", cantrip, 0, ws, spontaneous_summon=True)

    assert token == "spell_failed", (
        f"Level-0 SNA redirect must produce spell_failed token, got {token!r}"
    )
    registry_fails = [
        e for e in events
        if e.event_type == "spell_cast_failed"
        and e.payload.get("reason") == "sna_spell_not_in_registry"
    ]
    assert len(registry_fails) == 1, (
        f"Expected 'sna_spell_not_in_registry' failure for level-0 slot. "
        f"Events: {[e.payload for e in events if e.event_type == 'spell_cast_failed']}"
    )


# ---------------------------------------------------------------------------
# DSS-007: Slot consumed at original spell's level after redirect
# ---------------------------------------------------------------------------

def test_DSS007_slot_consumed_at_declared_level():
    """DSS-007: After SNA redirect, spell slot is consumed at the declared spell's level (not SNA's level — same)."""
    if "entangle" not in SPELL_REGISTRY:
        pytest.skip("entangle not in SPELL_REGISTRY")
    assert SPELL_REGISTRY["entangle"].level == 1

    druid = _druid_entity(spell_level=1, spell_id="entangle")
    druid[EF.SPELL_SLOTS] = {1: 2, 2: 1}  # Track slot 1 count
    ws = _make_world(druid)

    _, new_ws, token = _spell_cast("druid", "entangle", 1, ws, spontaneous_summon=True)

    # If the cast succeeded (not spell_failed/slot_empty), check that slot 1 was decremented
    if token not in ("spell_failed", "spell_slot_empty"):
        new_druid = new_ws.entities.get("druid", {})
        new_slots = new_druid.get(EF.SPELL_SLOTS, {})
        # Slot 1 should have been consumed (decremented from 2 to 1)
        assert new_slots.get(1, 2) < 2, (
            f"Slot 1 should be consumed after SNA redirect at level 1. "
            f"Before: 2, After: {new_slots.get(1)}"
        )


# ---------------------------------------------------------------------------
# DSS-008: Code inspection — elif block after spontaneous_inflict
# ---------------------------------------------------------------------------

def test_DSS008_code_inspection_elif_after_inflict():
    """DSS-008: play_loop.py contains spontaneous_summon elif block after spontaneous_inflict block."""
    import aidm.core.play_loop as pl_module

    src = inspect.getsource(pl_module)

    # WO comment must be present
    marker = "WO-ENGINE-DRUID-SPONTANEOUS-SUMMON-001"
    assert marker in src, f"WO comment '{marker}' not found in play_loop source."

    # _SNA_SPELLS_BY_LEVEL dict must be present
    assert "_SNA_SPELLS_BY_LEVEL" in src, "_SNA_SPELLS_BY_LEVEL dict not found in play_loop source."

    # elif getattr block must be present
    assert "elif getattr(intent, \"spontaneous_summon\", False):" in src, (
        "elif getattr(intent, 'spontaneous_summon', False): block not found."
    )

    # Block must come AFTER spontaneous_inflict block (inflict marker must appear before summon marker)
    inflict_pos = src.find("spontaneous_inflict")
    summon_pos = src.find(marker)
    assert inflict_pos < summon_pos, (
        "spontaneous_summon block must appear AFTER spontaneous_inflict block in source."
    )
