"""Gate tests — WO-ENGINE-EVIL-CLERIC-INFLICT-001.

ECI-001 through ECI-008: Evil cleric spontaneous inflict casting.
8 tests total.

Pre-existing failures: 149. Any new failures beyond 149 are regressions.
"""
import pytest
from copy import deepcopy

from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.core.play_loop import _resolve_spell_cast
from aidm.core.spell_resolver import SpellCastIntent
from aidm.data.spell_definitions import SPELL_REGISTRY


def _ws(entities):
    return WorldState(ruleset_version="3.5", entities=deepcopy(entities), active_combat=None)


class _SeededRNG:
    """Always rolls max (high hit, max damage for testing)."""
    def stream(self, name):
        return self
    def randint(self, lo, hi):
        return hi


def _evil_cleric(level: int, alignment: str = "lawful_evil"):
    """Minimal evil cleric entity with prepared spell slots (int keys per chargen convention)."""
    entity = {
        EF.ENTITY_ID: f"cleric_{level}",
        EF.CLASS_LEVELS: {"cleric": level},
        EF.ALIGNMENT: alignment,
        EF.CASTER_CLASS: "cleric",
        EF.CASTER_LEVEL: level,
        EF.SAVE_FORT: 3 + level // 3, EF.SAVE_REF: 1, EF.SAVE_WILL: 4 + level // 3,
        EF.CONDITIONS: {}, EF.FEATS: [], EF.TEMPORARY_MODIFIERS: {},
        EF.SPELLS_PREPARED: {1: ["magic_missile", "magic_missile"]},
        EF.SPELL_SLOTS: {1: 4, 2: 3, 3: 2, 4: 1, 5: 1},
        EF.HP_MAX: 10 * level, EF.HP_CURRENT: 10 * level,
        EF.POSITION: {"x": 0, "y": 0}, EF.TEAM: "enemies",
        EF.DEFEATED: False, EF.DYING: False,
        EF.STR_MOD: 1, EF.DEX_MOD: 0, EF.CON_MOD: 1,
        EF.INT_MOD: 0, EF.WIS_MOD: 2, EF.CHA_MOD: 1,
        EF.NEGATIVE_LEVELS: 0,
    }
    return entity


def _target():
    return {
        EF.ENTITY_ID: "target1",
        EF.CLASS_LEVELS: {"fighter": 3},
        EF.HP_MAX: 30, EF.HP_CURRENT: 30,
        EF.AC: 14,
        EF.CONDITIONS: {}, EF.FEATS: [], EF.TEMPORARY_MODIFIERS: {},
        EF.SAVE_FORT: 6, EF.SAVE_REF: 2, EF.SAVE_WILL: 1,
        EF.POSITION: {"x": 0, "y": 0}, EF.TEAM: "heroes",
        EF.DEFEATED: False, EF.DYING: False,
        EF.STR_MOD: 1, EF.DEX_MOD: 1, EF.CON_MOD: 1,
        EF.INT_MOD: 0, EF.WIS_MOD: 0, EF.CHA_MOD: 0,
        EF.NEGATIVE_LEVELS: 0,
    }


def _cast(intent, entities):
    """Helper to call _resolve_spell_cast and return (events, ws_after, token)."""
    ws = _ws(entities)
    return _resolve_spell_cast(
        intent=intent,
        world_state=ws,
        rng=_SeededRNG(),
        grid=None,
        next_event_id=1,
        timestamp=0.0,
        turn_index=0,
    )


# ---------------------------------------------------------------------------
# Verify inflict spells are in the registry (prerequisite for all ECI tests)
# ---------------------------------------------------------------------------

def test_inflict_spells_in_registry():
    """All 5 inflict spells must be in SPELL_REGISTRY before any ECI tests run."""
    for spell_id, level in [
        ("inflict_light_wounds", 1),
        ("inflict_moderate_wounds", 2),
        ("inflict_serious_wounds", 3),
        ("inflict_critical_wounds", 4),
        ("mass_inflict_light_wounds", 5),
    ]:
        assert spell_id in SPELL_REGISTRY, f"Missing inflict spell: {spell_id}"
        assert SPELL_REGISTRY[spell_id].school == "necromancy", f"{spell_id} should be necromancy"
        assert SPELL_REGISTRY[spell_id].level == level, f"{spell_id} should be level {level}"


# ---------------------------------------------------------------------------
# ECI-001: Evil cleric converts slot to inflict — slot consumed + inflict fires
# ---------------------------------------------------------------------------

def test_eci_001_evil_cleric_converts_slot_to_inflict():
    """Evil cleric L3: declared magic_missile (L1 slot) → spontaneous inflict light wounds."""
    cleric = _evil_cleric(level=3)
    cleric[EF.SPELLS_PREPARED] = {1: ["magic_missile", "magic_missile"]}
    tgt = _target()

    intent = SpellCastIntent(
        caster_id=cleric[EF.ENTITY_ID],
        spell_id="magic_missile",
        target_entity_id=tgt[EF.ENTITY_ID],
        spontaneous_inflict=True,
    )
    events, ws_after, narration_key = _cast(intent, {cleric[EF.ENTITY_ID]: cleric, tgt[EF.ENTITY_ID]: tgt})

    assert narration_key != "spell_failed", (
        f"Spell should not fail. narration_key={narration_key}, events={[e.event_type for e in events]}"
    )

    # The inflict spell must have fired (hp_changed, save_triggered, or save_rolled)
    event_types = [e.event_type for e in events]
    assert any(et in event_types for et in ("hp_changed", "save_triggered", "save_rolled", "spell_cast")), (
        f"Expect inflict spell to fire. Got: {event_types}"
    )

    # L1 slot consumed — slot governor decrements EF.SPELL_SLOTS count
    slots_after = ws_after.entities[cleric[EF.ENTITY_ID]].get(EF.SPELL_SLOTS, {})
    slots_l1_count = slots_after.get(1, slots_after.get("1", 4))
    assert slots_l1_count < 4, f"One L1 SPELL_SLOTS count should have been consumed. Count: {slots_l1_count}"


# ---------------------------------------------------------------------------
# ECI-002: Evil cleric L1 — inflict light wounds
# ---------------------------------------------------------------------------

def test_eci_002_evil_cleric_l1_inflict_light():
    """Evil cleric L1: spontaneous_inflict → inflict_light_wounds fires."""
    cleric = _evil_cleric(level=1)
    cleric[EF.SPELLS_PREPARED] = {1: ["bless"]}
    tgt = _target()

    intent = SpellCastIntent(
        caster_id=cleric[EF.ENTITY_ID],
        spell_id="bless",
        target_entity_id=tgt[EF.ENTITY_ID],
        spontaneous_inflict=True,
    )
    events, _, narration_key = _cast(intent, {cleric[EF.ENTITY_ID]: cleric, tgt[EF.ENTITY_ID]: tgt})
    assert narration_key != "spell_failed", (
        f"Evil cleric L1 should use inflict swap. narration_key={narration_key}"
    )


# ---------------------------------------------------------------------------
# ECI-003: Neutral evil cleric — inflict swap permitted
# ---------------------------------------------------------------------------

def test_eci_003_neutral_evil_alignment_permitted():
    """Neutral evil cleric: inflict swap allowed."""
    cleric = _evil_cleric(level=3, alignment="neutral_evil")
    cleric[EF.SPELLS_PREPARED] = {1: ["bless"]}
    tgt = _target()

    intent = SpellCastIntent(
        caster_id=cleric[EF.ENTITY_ID], spell_id="bless",
        target_entity_id=tgt[EF.ENTITY_ID], spontaneous_inflict=True,
    )
    events, _, narration_key = _cast(intent, {cleric[EF.ENTITY_ID]: cleric, tgt[EF.ENTITY_ID]: tgt})
    assert narration_key != "spell_failed"


# ---------------------------------------------------------------------------
# ECI-004: Good cleric — inflict swap blocked
# ---------------------------------------------------------------------------

def test_eci_004_good_cleric_inflict_blocked():
    """Good cleric attempting spontaneous_inflict → blocked (alignment_blocked)."""
    cleric = _evil_cleric(level=3, alignment="neutral_good")
    cleric[EF.SPELLS_PREPARED] = {1: ["bless"]}
    tgt = _target()

    intent = SpellCastIntent(
        caster_id=cleric[EF.ENTITY_ID], spell_id="bless",
        target_entity_id=tgt[EF.ENTITY_ID], spontaneous_inflict=True,
    )
    events, _, narration_key = _cast(intent, {cleric[EF.ENTITY_ID]: cleric, tgt[EF.ENTITY_ID]: tgt})
    assert narration_key == "spell_failed"
    reasons = [e.payload.get("reason", "") for e in events]
    assert any("alignment_blocked" in r for r in reasons), f"Expected alignment_blocked. Got: {reasons}"


# ---------------------------------------------------------------------------
# ECI-005: True neutral cleric — inflict swap blocked
# ---------------------------------------------------------------------------

def test_eci_005_true_neutral_cleric_blocked():
    """True neutral cleric (no deity): spontaneous_inflict blocked."""
    cleric = _evil_cleric(level=3, alignment="true_neutral")
    cleric[EF.SPELLS_PREPARED] = {1: ["bless"]}
    tgt = _target()

    intent = SpellCastIntent(
        caster_id=cleric[EF.ENTITY_ID], spell_id="bless",
        target_entity_id=tgt[EF.ENTITY_ID], spontaneous_inflict=True,
    )
    events, _, narration_key = _cast(intent, {cleric[EF.ENTITY_ID]: cleric, tgt[EF.ENTITY_ID]: tgt})
    assert narration_key == "spell_failed"


# ---------------------------------------------------------------------------
# ECI-006: Evil cleric — no prepared slots
# ---------------------------------------------------------------------------

def test_eci_006_no_prepared_slot():
    """Evil cleric with no prepared spell of that name → spell_failed."""
    cleric = _evil_cleric(level=3, alignment="lawful_evil")
    cleric[EF.SPELLS_PREPARED] = {}  # Empty
    tgt = _target()

    intent = SpellCastIntent(
        caster_id=cleric[EF.ENTITY_ID], spell_id="magic_missile",
        target_entity_id=tgt[EF.ENTITY_ID], spontaneous_inflict=True,
    )
    events, _, narration_key = _cast(intent, {cleric[EF.ENTITY_ID]: cleric, tgt[EF.ENTITY_ID]: tgt})
    # No slot found (empty SPELLS_PREPARED) → slot governor fires "spell_slot_empty"
    assert narration_key == "spell_slot_empty", f"Expected slot failure. Got: {narration_key}"


# ---------------------------------------------------------------------------
# ECI-007: Evil cleric L5 — inflict_critical_wounds (L4 slot)
# ---------------------------------------------------------------------------

def test_eci_007_evil_cleric_l5_inflict_critical():
    """Evil cleric L5 with L4 slot: spontaneous → inflict_critical_wounds."""
    cleric = _evil_cleric(level=5, alignment="chaotic_evil")
    cleric[EF.SPELLS_PREPARED] = {4: ["animate_dead"]}  # animate_dead is L4, in registry
    cleric[EF.CASTER_LEVEL] = 5
    tgt = _target()

    intent = SpellCastIntent(
        caster_id=cleric[EF.ENTITY_ID], spell_id="animate_dead",
        target_entity_id=tgt[EF.ENTITY_ID], spontaneous_inflict=True,
    )
    events, ws_after, narration_key = _cast(intent, {cleric[EF.ENTITY_ID]: cleric, tgt[EF.ENTITY_ID]: tgt})

    # inflict_critical_wounds (L4) is in registry — should fire
    assert narration_key != "spell_failed", (
        f"Evil cleric L5 should cast inflict_critical_wounds (L4 slot). "
        f"narration_key={narration_key}, events={[e.event_type for e in events]}"
    )


# ---------------------------------------------------------------------------
# ECI-008: Multiclass Evil Cleric 3/Fighter 2 — inflict swap available
# ---------------------------------------------------------------------------

def test_eci_008_multiclass_evil_cleric_fighter():
    """Multiclass Evil Cleric 3/Fighter 2: inflict swap available (cleric levels gate it)."""
    cleric_fighter = {
        EF.ENTITY_ID: "cf1",
        EF.CLASS_LEVELS: {"cleric": 3, "fighter": 2},
        EF.ALIGNMENT: "lawful_evil",
        EF.SPELLS_PREPARED: {1: ["bless"]},
        EF.CASTER_CLASS: "cleric",
        EF.CASTER_LEVEL: 3,
        EF.HP_MAX: 40, EF.HP_CURRENT: 40,
        EF.AC: 15,
        EF.CONDITIONS: {}, EF.FEATS: [], EF.TEMPORARY_MODIFIERS: {},
        EF.SAVE_FORT: 5, EF.SAVE_REF: 2, EF.SAVE_WILL: 4,
        EF.POSITION: {"x": 0, "y": 0}, EF.TEAM: "enemies",
        EF.DEFEATED: False, EF.DYING: False,
        EF.STR_MOD: 1, EF.DEX_MOD: 0, EF.CON_MOD: 1,
        EF.INT_MOD: 0, EF.WIS_MOD: 2, EF.CHA_MOD: 1,
        EF.NEGATIVE_LEVELS: 0,
    }
    tgt = _target()

    intent = SpellCastIntent(
        caster_id="cf1", spell_id="bless",
        target_entity_id=tgt[EF.ENTITY_ID], spontaneous_inflict=True,
    )
    events, _, narration_key = _cast(intent, {"cf1": cleric_fighter, tgt[EF.ENTITY_ID]: tgt})
    assert narration_key != "spell_failed", (
        f"Multiclass evil cleric should be able to use inflict swap. "
        f"narration_key={narration_key}, events={[e.event_type for e in events]}"
    )
