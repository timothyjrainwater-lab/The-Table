"""Gate tests — WO-ENGINE-SAVECONTEXT-DESCRIPTOR-001.

SCS-001 through SCS-008: SaveContext descriptor + school threading through
resolve_save() → get_save_bonus(). 8 tests.

Pre-existing failures: 149. Any new failures beyond 149 are regressions.
"""
import pytest
from copy import deepcopy

from aidm.core.save_resolver import get_save_bonus, resolve_save
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.schemas.saves import SaveContext, SaveType, EffectSpec
from aidm.core.rng_protocol import RNGProvider


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _ws(entities: dict) -> WorldState:
    return WorldState(ruleset_version="3.5", entities=deepcopy(entities), active_combat=None)


def _monk_l3():
    return {
        EF.CLASS_LEVELS: {"monk": 3},
        EF.SAVE_FORT: 3, EF.SAVE_REF: 3, EF.SAVE_WILL: 5,
        EF.CONDITIONS: {}, EF.FEATS: [], EF.TEMPORARY_MODIFIERS: {},
    }


def _barbarian_l14():
    return {
        EF.CLASS_LEVELS: {"barbarian": 14},
        EF.SAVE_FORT: 9, EF.SAVE_REF: 4, EF.SAVE_WILL: 4,
        EF.CONDITIONS: {}, EF.FEATS: [], EF.TEMPORARY_MODIFIERS: {"indomitable_will_active": True},
    }


def _paladin_l2():
    """Self — fear immune."""
    return {
        EF.CLASS_LEVELS: {"paladin": 2},
        EF.SAVE_FORT: 5, EF.SAVE_REF: 2, EF.SAVE_WILL: 2,
        EF.CONDITIONS: {}, EF.FEATS: [], EF.TEMPORARY_MODIFIERS: {},
        EF.FEAR_IMMUNE: True,
        EF.POSITION: {"x": 0, "y": 0}, EF.TEAM: "heroes",
    }


def _fighter_ally():
    """Non-paladin ally near a paladin."""
    return {
        EF.CLASS_LEVELS: {"fighter": 4},
        EF.SAVE_FORT: 4, EF.SAVE_REF: 1, EF.SAVE_WILL: 1,
        EF.CONDITIONS: {}, EF.FEATS: [], EF.TEMPORARY_MODIFIERS: {},
        EF.POSITION: {"x": 1, "y": 0}, EF.TEAM: "heroes",
    }


def _gnome():
    """Gnome with +2 vs illusions stored in SPELL_RESISTANCE_ILLUSION."""
    return {
        EF.CLASS_LEVELS: {"fighter": 2},
        EF.SAVE_FORT: 4, EF.SAVE_REF: 1, EF.SAVE_WILL: 1,
        EF.CONDITIONS: {}, EF.FEATS: [], EF.TEMPORARY_MODIFIERS: {},
        EF.SPELL_RESISTANCE_ILLUSION: 2,
    }


class _FixedRNG:
    def stream(self, name: str):
        return self

    def randint(self, lo: int, hi: int) -> int:
        return lo  # always rolls minimum


# ---------------------------------------------------------------------------
# SCS-001: Still Mind via resolve_save()
# ---------------------------------------------------------------------------

def test_scs_001_still_mind_via_resolve_save():
    """Monk L3: resolve_save() with SaveContext(school='enchantment') → Still Mind +2."""
    entity = _monk_l3()
    ws = _ws({"monk1": entity})

    # Baseline without school — get_save_bonus should not include +2
    bonus_without = get_save_bonus(ws, "monk1", SaveType.WILL, school="")
    # With school="enchantment" — should include +2
    bonus_with = get_save_bonus(ws, "monk1", SaveType.WILL, school="enchantment")

    assert bonus_with - bonus_without == 2, (
        f"Still Mind should add +2 vs enchantment. "
        f"Without: {bonus_without}, With: {bonus_with}"
    )

    # Now prove via the full resolve_save() path (the fix — not just get_save_bonus directly)
    ctx = SaveContext(
        save_type=SaveType.WILL,
        dc=99,  # impossible DC so outcome is FAILURE regardless
        source_id="src",
        target_id="monk1",
        school="enchantment",
    )
    rng = _FixedRNG()
    _, events = resolve_save(ctx, ws, rng, next_event_id=1, timestamp=0.0)
    assert events, "Expected at least one event (save_rolled)"
    rolled_event = next(e for e in events if e.event_type == "save_rolled")
    reported_bonus = rolled_event.payload["save_bonus"]
    assert reported_bonus == bonus_with, (
        f"resolve_save() reported bonus {reported_bonus} != get_save_bonus with school {bonus_with}. "
        f"Threading gap — descriptor not passed from SaveContext to get_save_bonus."
    )


# ---------------------------------------------------------------------------
# SCS-002: Indomitable Will via resolve_save()
# ---------------------------------------------------------------------------

def test_scs_002_indomitable_will_via_resolve_save():
    """Barbarian L14 in rage (indomitable_will_active=True): +4 Will vs enchantment."""
    entity = _barbarian_l14()
    ws = _ws({"barb1": entity})

    bonus_without = get_save_bonus(ws, "barb1", SaveType.WILL, school="")
    bonus_with = get_save_bonus(ws, "barb1", SaveType.WILL, school="enchantment")

    assert bonus_with - bonus_without == 4, (
        f"Indomitable Will should add +4 vs enchantment while raging. "
        f"Without: {bonus_without}, With: {bonus_with}"
    )

    ctx = SaveContext(
        save_type=SaveType.WILL,
        dc=99,
        source_id="src",
        target_id="barb1",
        school="enchantment",
    )
    _, events = resolve_save(ctx, ws, _FixedRNG(), next_event_id=1, timestamp=0.0)
    rolled_event = next(e for e in events if e.event_type == "save_rolled")
    assert rolled_event.payload["save_bonus"] == bonus_with


# ---------------------------------------------------------------------------
# SCS-003: Aura of Courage via resolve_save() — ally gets +4 fear bonus
# ---------------------------------------------------------------------------

def test_scs_003_aura_of_courage_via_resolve_save():
    """Paladin L3 ally within 10 ft: resolve_save() with save_descriptor='fear' → +4.
    WO-AE-WO3: AoC granted at L3+ (PHB p.49), not L2. Updated from L2 to L3.
    """
    paladin = {
        EF.CLASS_LEVELS: {"paladin": 3},
        EF.SAVE_FORT: 5, EF.SAVE_REF: 2, EF.SAVE_WILL: 2,
        EF.CONDITIONS: {}, EF.FEATS: [], EF.TEMPORARY_MODIFIERS: {},
        EF.POSITION: {"x": 0, "y": 0}, EF.TEAM: "heroes",
        EF.FEAR_IMMUNE: True,
    }
    fighter = _fighter_ally()
    ws = _ws({"pal1": paladin, "fig1": fighter})

    bonus_without_fear = get_save_bonus(ws, "fig1", SaveType.WILL, save_descriptor="")
    bonus_with_fear = get_save_bonus(ws, "fig1", SaveType.WILL, save_descriptor="fear")

    assert bonus_with_fear - bonus_without_fear == 4, (
        f"AoC should add +4 vs fear for ally within 10 ft. "
        f"Without: {bonus_without_fear}, With: {bonus_with_fear}"
    )

    ctx = SaveContext(
        save_type=SaveType.WILL,
        dc=99,
        source_id="src",
        target_id="fig1",
        save_descriptor="fear",
    )
    _, events = resolve_save(ctx, ws, _FixedRNG(), next_event_id=1, timestamp=0.0)
    rolled_event = next(e for e in events if e.event_type == "save_rolled")
    assert rolled_event.payload["save_bonus"] == bonus_with_fear


# ---------------------------------------------------------------------------
# SCS-004: Paladin self — fear immunity fires
# ---------------------------------------------------------------------------

def test_scs_004_paladin_self_fear_immunity():
    """Paladin L2 self: save_descriptor='fear' → fear_bonus == 999 (immunity sentinel)."""
    paladin = _paladin_l2()
    ws = _ws({"pal1": paladin})

    bonus = get_save_bonus(ws, "pal1", SaveType.WILL, save_descriptor="fear")
    assert bonus >= 999, f"Fear immunity sentinel expected >= 999, got {bonus}"


# ---------------------------------------------------------------------------
# SCS-005: Empty descriptor/school → no change
# ---------------------------------------------------------------------------

def test_scs_005_empty_descriptor_no_change():
    """SaveContext() with no descriptor/school → no regression, empty string passthrough."""
    entity = _monk_l3()
    ws = _ws({"monk1": entity})

    bonus_direct = get_save_bonus(ws, "monk1", SaveType.WILL)
    ctx = SaveContext(
        save_type=SaveType.WILL,
        dc=1,
        source_id="src",
        target_id="monk1",
        # save_descriptor and school default to ""
    )
    _, events = resolve_save(ctx, ws, _FixedRNG(), next_event_id=1, timestamp=0.0)
    rolled_event = next(e for e in events if e.event_type == "save_rolled")
    assert rolled_event.payload["save_bonus"] == bonus_direct


# ---------------------------------------------------------------------------
# SCS-006: Gnome +2 vs illusions (school="illusion")
# ---------------------------------------------------------------------------

def test_scs_006_gnome_illusion_save_bonus():
    """Gnome: SaveContext(school='illusion') → +2 illusion save fires via resolve_save()."""
    gnome = _gnome()
    ws = _ws({"gnome1": gnome})

    bonus_without = get_save_bonus(ws, "gnome1", SaveType.WILL, school="")
    bonus_with = get_save_bonus(ws, "gnome1", SaveType.WILL, school="illusion")

    assert bonus_with - bonus_without == 2, (
        f"Gnome illusion save should add +2. Without: {bonus_without}, With: {bonus_with}"
    )

    ctx = SaveContext(
        save_type=SaveType.WILL,
        dc=99,
        source_id="src",
        target_id="gnome1",
        school="illusion",
    )
    _, events = resolve_save(ctx, ws, _FixedRNG(), next_event_id=1, timestamp=0.0)
    rolled_event = next(e for e in events if e.event_type == "save_rolled")
    assert rolled_event.payload["save_bonus"] == bonus_with


# ---------------------------------------------------------------------------
# SCS-007: School from spell definition paths through resolve_save()
# ---------------------------------------------------------------------------

def test_scs_007_school_threading_end_to_end():
    """SaveContext(school='enchantment') on monk L3 → Still Mind +2 fires end-to-end."""
    entity = _monk_l3()
    ws = _ws({"monk1": entity})

    ctx_no_school = SaveContext(
        save_type=SaveType.WILL, dc=99, source_id="src", target_id="monk1",
        school="",
    )
    ctx_with_school = SaveContext(
        save_type=SaveType.WILL, dc=99, source_id="src", target_id="monk1",
        school="enchantment",
    )

    _, events_no = resolve_save(ctx_no_school, ws, _FixedRNG(), next_event_id=1, timestamp=0.0)
    _, events_with = resolve_save(ctx_with_school, ws, _FixedRNG(), next_event_id=1, timestamp=0.0)

    bonus_no = next(e for e in events_no if e.event_type == "save_rolled").payload["save_bonus"]
    bonus_with = next(e for e in events_with if e.event_type == "save_rolled").payload["save_bonus"]

    assert bonus_with - bonus_no == 2, (
        f"Still Mind +2 must fire via resolve_save() school threading. "
        f"No school: {bonus_no}, With enchantment: {bonus_with}"
    )


# ---------------------------------------------------------------------------
# SCS-008: Non-descriptor save (standard Fort) — no change
# ---------------------------------------------------------------------------

def test_scs_008_non_descriptor_save_no_change():
    """Standard Fort save (no descriptor): no bonus delta, result unchanged."""
    entity = _monk_l3()
    ws = _ws({"monk1": entity})

    bonus_direct = get_save_bonus(ws, "monk1", SaveType.FORT)
    ctx = SaveContext(
        save_type=SaveType.FORT,
        dc=5,
        source_id="src",
        target_id="monk1",
    )
    _, events = resolve_save(ctx, ws, _FixedRNG(), next_event_id=1, timestamp=0.0)
    rolled_event = next(e for e in events if e.event_type == "save_rolled")
    assert rolled_event.payload["save_bonus"] == bonus_direct
