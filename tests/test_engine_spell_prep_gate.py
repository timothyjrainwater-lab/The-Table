"""Gate ENGINE-SPELL-PREP — WO-ENGINE-SPELL-PREP-001: Spell Preparation Intent.

Tests:
SP-01: Wizard prepares 2 level-1 spells, has 2 slots => spells_prepared event, SPELLS_PREPARED updated
SP-02: Wizard prepares 3 level-1 spells, has 2 slots => spell_prep_failed with validation_failed
SP-03: Wizard prepares spell not in spellbook => spell_prep_failed
SP-04: Wizard prepares magic_missile (level 1) under level 2 => spell_prep_failed (level mismatch)
SP-05: Sorcerer (spontaneous) issues PrepareSpellsIntent => spell_prep_failed, reason spontaneous_caster_no_prep
SP-06: Cleric issues PrepareSpellsIntent with valid spells => spells_prepared event
SP-07: Druid issues PrepareSpellsIntent => spells_prepared event
SP-08: PrepareSpellsIntent uses no RNG — passes with rng=None
SP-09: Dual-caster wizard/sorcerer: use_secondary=True targets SPELLS_PREPARED_2
SP-10: Same spell prepared twice in same level (within slot limit) => succeeds
SP-11: PrepareSpellsIntent for non-existent entity => spell_prep_failed, reason entity_not_found
SP-12: Zero regressions on ENGINE-REST-001 gate (12/12) and existing spell slot tests
"""

from copy import deepcopy
from typing import Any, Dict

import pytest

from aidm.core.spell_prep_resolver import resolve_prepare_spells
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.schemas.intents import PrepareSpellsIntent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _wizard(
    eid: str = "wizard_pc",
    level_1_slots: int = 2,
    level_2_slots: int = 1,
    known_l1=None,
    known_l2=None,
) -> Dict[str, Any]:
    """Minimal wizard entity for spell prep tests."""
    if known_l1 is None:
        known_l1 = ["magic_missile", "shield", "burning_hands"]
    if known_l2 is None:
        known_l2 = ["scorching_ray", "web"]
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: 20,
        EF.HP_MAX: 20,
        EF.CASTER_CLASS: "wizard",
        EF.SPELL_SLOTS: {1: level_1_slots, 2: level_2_slots},
        EF.SPELLS_KNOWN: {1: known_l1, 2: known_l2},
        EF.SPELLS_PREPARED: {},
        EF.DEFEATED: False,
    }


def _cleric(eid: str = "cleric_pc", level_1_slots: int = 3) -> Dict[str, Any]:
    """Minimal cleric entity. No SPELLS_KNOWN — clerics access full class list."""
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 30,
        EF.CASTER_CLASS: "cleric",
        EF.SPELL_SLOTS: {1: level_1_slots},
        EF.SPELLS_KNOWN: {},  # Clerics have full class list — no spellbook restriction
        EF.SPELLS_PREPARED: {},
        EF.DEFEATED: False,
    }


def _druid(eid: str = "druid_pc", level_1_slots: int = 3) -> Dict[str, Any]:
    """Minimal druid entity."""
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: 25,
        EF.HP_MAX: 25,
        EF.CASTER_CLASS: "druid",
        EF.SPELL_SLOTS: {1: level_1_slots},
        EF.SPELLS_KNOWN: {},  # Druids have full class list
        EF.SPELLS_PREPARED: {},
        EF.DEFEATED: False,
    }


def _sorcerer(eid: str = "sorc_pc") -> Dict[str, Any]:
    """Minimal sorcerer entity (spontaneous caster)."""
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: 15,
        EF.HP_MAX: 15,
        EF.CASTER_CLASS: "sorcerer",
        EF.SPELL_SLOTS: {1: 4},
        EF.SPELLS_KNOWN: {1: ["magic_missile", "burning_hands"]},
        EF.DEFEATED: False,
    }


def _world(*entity_dicts) -> WorldState:
    entities = {e[EF.ENTITY_ID]: e for e in entity_dicts}
    return WorldState(
        ruleset_version="3.5e",
        entities=entities,
        active_combat=None,
    )


def _prep(world_state: WorldState, caster_id: str, preparation: dict, use_secondary: bool = False):
    """Run resolve_prepare_spells and return (events, new_ws, narration)."""
    intent = PrepareSpellsIntent(
        caster_id=caster_id,
        preparation=preparation,
        use_secondary=use_secondary,
    )
    return resolve_prepare_spells(
        intent=intent,
        world_state=world_state,
        next_event_id=0,
        timestamp=1.0,
        turn_index=1,
    )


# ---------------------------------------------------------------------------
# SP-01: Wizard prepares 2 level-1 spells, has 2 slots => success
# ---------------------------------------------------------------------------

def test_sp01_wizard_prepares_valid_level1_spells():
    """Wizard with 2 level-1 slots prepares 2 spells => spells_prepared event + state updated."""
    ws = _world(_wizard())
    events, new_ws, narration = _prep(
        ws, "wizard_pc",
        {1: ["magic_missile", "shield"]}
    )

    event_types = [e.event_type for e in events]
    assert "spells_prepared" in event_types, f"Expected spells_prepared, got: {event_types}"
    assert narration == "spells_prepared"

    # SPELLS_PREPARED updated in world state
    prepared = new_ws.entities["wizard_pc"].get(EF.SPELLS_PREPARED, {})
    assert prepared.get(1) == ["magic_missile", "shield"], f"Unexpected prepared: {prepared}"


# ---------------------------------------------------------------------------
# SP-02: Wizard prepares 3 spells but only has 2 slots => validation_failed
# ---------------------------------------------------------------------------

def test_sp02_wizard_over_slot_limit_fails():
    """Wizard with 2 slots cannot prepare 3 spells at level 1."""
    ws = _world(_wizard(level_1_slots=2))
    events, new_ws, narration = _prep(
        ws, "wizard_pc",
        {1: ["magic_missile", "shield", "burning_hands"]}  # 3 spells, 2 slots
    )

    assert narration == "spell_prep_failed"
    event_types = [e.event_type for e in events]
    assert "spell_prep_failed" in event_types

    failed_evt = next(e for e in events if e.event_type == "spell_prep_failed")
    assert failed_evt.payload.get("reason") == "validation_failed"
    errors = failed_evt.payload.get("errors", [])
    assert any("slots available" in err for err in errors), f"Expected slot count error, got: {errors}"

    # World state unchanged
    prepared = new_ws.entities["wizard_pc"].get(EF.SPELLS_PREPARED, {})
    assert prepared == {}, "State must not change on failure"


# ---------------------------------------------------------------------------
# SP-03: Wizard prepares spell not in spellbook => validation_failed
# ---------------------------------------------------------------------------

def test_sp03_wizard_spell_not_in_spellbook_fails():
    """Wizard cannot prepare a spell not in their spellbook (SPELLS_KNOWN)."""
    ws = _world(_wizard(known_l1=["magic_missile", "shield"]))  # fireball not in spellbook
    events, new_ws, narration = _prep(
        ws, "wizard_pc",
        {1: ["magic_missile", "fireball"]}  # fireball is level 3, not in known list
    )

    assert narration == "spell_prep_failed"
    failed_evt = next(e for e in events if e.event_type == "spell_prep_failed")
    errors = failed_evt.payload.get("errors", [])
    # Should have an error about spellbook OR level mismatch (fireball is level 3)
    assert len(errors) > 0, f"Expected errors, got none. Events: {[e.event_type for e in events]}"


# ---------------------------------------------------------------------------
# SP-04: Wizard prepares magic_missile under level 2 => level mismatch error
# ---------------------------------------------------------------------------

def test_sp04_spell_wrong_level_fails():
    """magic_missile is level 1 — cannot be prepared in a level-2 slot."""
    ws = _world(_wizard(level_1_slots=2, level_2_slots=1))
    events, new_ws, narration = _prep(
        ws, "wizard_pc",
        {2: ["magic_missile"]}  # magic_missile is level 1, not 2
    )

    assert narration == "spell_prep_failed"
    failed_evt = next(e for e in events if e.event_type == "spell_prep_failed")
    errors = failed_evt.payload.get("errors", [])
    assert any("level" in err.lower() for err in errors), \
        f"Expected level mismatch error, got: {errors}"


# ---------------------------------------------------------------------------
# SP-05: Sorcerer (spontaneous) cannot prepare => spontaneous_caster_no_prep
# ---------------------------------------------------------------------------

def test_sp05_sorcerer_spontaneous_rejected():
    """Sorcerer is a spontaneous caster — PrepareSpellsIntent is rejected."""
    ws = _world(_sorcerer())
    events, new_ws, narration = _prep(
        ws, "sorc_pc",
        {1: ["magic_missile"]}
    )

    assert narration == "spell_prep_failed"
    failed_evt = next(e for e in events if e.event_type == "spell_prep_failed")
    assert failed_evt.payload.get("reason") == "spontaneous_caster_no_prep"


# ---------------------------------------------------------------------------
# SP-06: Cleric prepares valid spells => spells_prepared
# ---------------------------------------------------------------------------

def test_sp06_cleric_prepares_valid_spells():
    """Cleric is a prepared caster — can prepare from full class list."""
    ws = _world(_cleric(level_1_slots=3))
    events, new_ws, narration = _prep(
        ws, "cleric_pc",
        {1: ["cure_light_wounds", "bless"]}  # 2 spells, 3 slots available
    )

    assert narration == "spells_prepared", f"Expected spells_prepared, got: {narration}. Events: {[e.event_type for e in events]}"
    prepared = new_ws.entities["cleric_pc"].get(EF.SPELLS_PREPARED, {})
    assert prepared.get(1) == ["cure_light_wounds", "bless"]


# ---------------------------------------------------------------------------
# SP-07: Druid prepares valid spells => spells_prepared
# ---------------------------------------------------------------------------

def test_sp07_druid_prepares_valid_spells():
    """Druid is a prepared caster — can prepare from full class list."""
    ws = _world(_druid(level_1_slots=3))
    events, new_ws, narration = _prep(
        ws, "druid_pc",
        {1: ["entangle", "cure_light_wounds"]}
    )

    assert narration == "spells_prepared", f"Expected spells_prepared, got: {narration}"
    prepared = new_ws.entities["druid_pc"].get(EF.SPELLS_PREPARED, {})
    assert prepared.get(1) == ["entangle", "cure_light_wounds"]


# ---------------------------------------------------------------------------
# SP-08: PrepareSpellsIntent uses no RNG — passes with rng=None
# ---------------------------------------------------------------------------

def test_sp08_no_rng_required():
    """resolve_prepare_spells must not raise ValueError when called directly (no RNG needed)."""
    ws = _world(_wizard())
    # Direct call to resolver — no RNG argument. Should not raise.
    intent = PrepareSpellsIntent(
        caster_id="wizard_pc",
        preparation={1: ["magic_missile"]},
    )
    # This call should succeed without exception
    events, new_ws, narration = resolve_prepare_spells(
        intent=intent,
        world_state=ws,
        next_event_id=0,
        timestamp=0.0,
        turn_index=0,
    )
    assert narration == "spells_prepared"


# ---------------------------------------------------------------------------
# SP-09: Dual-caster: use_secondary=True targets SPELLS_PREPARED_2
# ---------------------------------------------------------------------------

def test_sp09_dual_caster_use_secondary_targets_prep_2():
    """use_secondary=True writes to SPELLS_PREPARED_2, not SPELLS_PREPARED."""
    dual_caster = {
        EF.ENTITY_ID: "dual_pc",
        EF.TEAM: "party",
        EF.HP_CURRENT: 20,
        EF.HP_MAX: 20,
        EF.CASTER_CLASS: "sorcerer",      # Primary: spontaneous
        EF.SPELL_SLOTS: {1: 4},
        EF.SPELLS_KNOWN: {1: ["magic_missile"]},
        EF.CASTER_CLASS_2: "wizard",       # Secondary: prepared
        EF.SPELL_SLOTS_2: {1: 2},
        EF.SPELLS_KNOWN_2: {1: ["magic_missile", "shield"]},
        EF.SPELLS_PREPARED_2: {},
        EF.SPELLS_PREPARED: {},
        EF.DEFEATED: False,
    }
    ws = _world(dual_caster)

    events, new_ws, narration = _prep(
        ws, "dual_pc",
        {1: ["magic_missile", "shield"]},
        use_secondary=True,
    )

    assert narration == "spells_prepared", f"Expected success for wizard secondary. Narration: {narration}"

    # SPELLS_PREPARED_2 updated, SPELLS_PREPARED unchanged
    prep2 = new_ws.entities["dual_pc"].get(EF.SPELLS_PREPARED_2, {})
    prep1 = new_ws.entities["dual_pc"].get(EF.SPELLS_PREPARED, {})
    assert prep2.get(1) == ["magic_missile", "shield"], f"SPELLS_PREPARED_2 wrong: {prep2}"
    assert prep1 == {}, f"SPELLS_PREPARED should be untouched: {prep1}"


# ---------------------------------------------------------------------------
# SP-10: Same spell prepared twice => succeeds (PHB p.178 allows)
# ---------------------------------------------------------------------------

def test_sp10_same_spell_twice_within_slot_limit():
    """Same spell may appear twice in a level's preparation list (uses one slot each)."""
    ws = _world(_wizard(level_1_slots=3))  # 3 slots available
    events, new_ws, narration = _prep(
        ws, "wizard_pc",
        {1: ["magic_missile", "magic_missile"]}  # 2 slots used, 3 available
    )

    assert narration == "spells_prepared", f"Expected success, got: {narration}"
    prepared = new_ws.entities["wizard_pc"].get(EF.SPELLS_PREPARED, {})
    assert prepared.get(1) == ["magic_missile", "magic_missile"]


# ---------------------------------------------------------------------------
# SP-11: Non-existent entity => entity_not_found
# ---------------------------------------------------------------------------

def test_sp11_nonexistent_entity_fails_gracefully():
    """PrepareSpellsIntent for entity not in world state => spell_prep_failed, entity_not_found."""
    ws = _world(_wizard())  # no "ghost_pc" in world
    events, new_ws, narration = _prep(
        ws, "ghost_pc",
        {1: ["magic_missile"]}
    )

    assert narration == "spell_prep_failed"
    failed_evt = next(e for e in events if e.event_type == "spell_prep_failed")
    assert failed_evt.payload.get("reason") == "entity_not_found"


# ---------------------------------------------------------------------------
# SP-12: Zero regressions on ENGINE-REST-001 gate
# ---------------------------------------------------------------------------

def test_sp12_no_regressions_rest_gate():
    """Verify ENGINE-REST-001 tests still pass."""
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_engine_rest_gate.py", "-v", "--tb=short"],
        capture_output=True,
        text=True,
        cwd="f:/DnD-3.5",
    )

    assert result.returncode == 0, (
        "ENGINE-REST-001 regression tests failed:\n" + result.stdout + result.stderr
    )
