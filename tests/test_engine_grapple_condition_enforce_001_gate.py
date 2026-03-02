"""Gate tests: WO-ENGINE-GRAPPLE-CONDITION-ENFORCE-001 (Batch AU).

GCE-001..008 — Grapple condition enforcement:
  GCE-001: Grappled entity does NOT make AoO when enemy movement provokes
  GCE-002: Grappling entity does NOT make AoO (initiator also restricted)
  GCE-003: Grappled caster must roll Concentration check (DC 20 + spell level)
  GCE-004: Grappled caster failing Concentration → concentration_failed event
  GCE-005: Grappled caster passing Concentration → spell resolves normally
  GCE-006: Non-grappled entity with Combat Reflexes CAN make AoOs (regression)
  GCE-007: Pinned somatic block still fires unchanged (regression)
  GCE-008: get_condition_modifiers() reports aoo_blocked=True for grappled/grappling

PHB p.156: "While grappling, you cannot make attacks of opportunity."
PHB p.156: "If you try to cast a spell while you are grappled or pinned, you must make a
            Concentration check (DC 20 + spell level) or lose the spell."
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from aidm.core.aoo import check_aoo_triggers
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF


# ---------------------------------------------------------------------------
# Helpers — AoO path (mirrors test_engine_flatfooted_aoo_001_gate.py)
# ---------------------------------------------------------------------------

def _make_entity(entity_id: str, team: str, position: dict,
                 conditions: dict = None, feats: list = None,
                 defeated: bool = False) -> dict:
    return {
        EF.ENTITY_ID: entity_id,
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 30,
        EF.TEAM: team,
        EF.DEFEATED: defeated,
        EF.CONDITIONS: conditions or {},
        EF.FEATS: feats or [],
        EF.DEX_MOD: 2,
        EF.ATTACK_BONUS: 5,
        EF.BAB: 5,
        EF.STR_MOD: 2,
        EF.WEAPON: {
            "name": "longsword", "damage_dice": "1d8",
            "crit_range": 19, "crit_multiplier": 2,
            "damage_type": "slashing", "attack_bonus": 0,
            "enhancement_bonus": 0,
        },
        EF.POSITION: position,
    }


def _make_world(entities: dict, initiative: list = None) -> WorldState:
    return WorldState(
        ruleset_version="3.5e",
        entities=entities,
        active_combat={
            "initiative_order": initiative or list(entities.keys()),
            "aoo_used_this_round": [],
            "aoo_count_this_round": {},
            "flat_footed_actors": [],
            "feint_flat_footed": [],
        },
    )


def _count_aoo_from_reactor(provoker_id: str, reactor_id: str,
                              reactor_conditions: dict = None,
                              reactor_feats: list = None) -> int:
    """Run check_aoo_triggers(); return number of triggers from reactor_id."""
    from aidm.schemas.attack import StepMoveIntent
    from aidm.schemas.position import Position

    provoker = _make_entity(provoker_id, "monsters", {"x": 1, "y": 0})
    reactor = _make_entity(reactor_id, "players", {"x": 0, "y": 0},
                           conditions=reactor_conditions or {},
                           feats=reactor_feats or [])
    ws = _make_world({provoker_id: provoker, reactor_id: reactor},
                     initiative=[reactor_id, provoker_id])
    intent = StepMoveIntent(
        actor_id=provoker_id,
        from_pos=Position(x=1, y=0),
        to_pos=Position(x=2, y=0),
    )
    triggers = check_aoo_triggers(ws, provoker_id, intent)
    return sum(1 for t in triggers if t.reactor_id == reactor_id)


# ---------------------------------------------------------------------------
# Helpers — Spell path (mirrors test_engine_concentration_grapple_001_gate.py)
# ---------------------------------------------------------------------------

def _make_caster(caster_id: str = "caster_01", conditions: dict = None,
                 conc_bonus: int = 0) -> dict:
    return {
        EF.ENTITY_ID: caster_id,
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 30,
        EF.TEAM: "players",
        EF.DEFEATED: False,
        EF.CONDITIONS: conditions or {},
        EF.CLASS_LEVELS: {"wizard": 5},
        EF.SPELL_SLOTS: {3: 3, 1: 4, 2: 3},
        EF.SPELLS_PREPARED: {3: ["fireball"], 1: ["magic_missile"], 2: ["scorching_ray"]},
        EF.CASTER_CLASS: "wizard",
        EF.INT_MOD: 3,
        EF.WIS_MOD: 0,
        EF.FEATS: [],
        EF.CONCENTRATION_BONUS: conc_bonus,
        EF.POSITION: {"x": 0, "y": 0},
    }


def _make_spell_world(caster_id: str = "caster_01", conditions: dict = None,
                      conc_bonus: int = 0) -> WorldState:
    return WorldState(
        ruleset_version="3.5e",
        entities={caster_id: _make_caster(caster_id, conditions=conditions,
                                          conc_bonus=conc_bonus)},
        active_combat={
            "initiative_order": [caster_id],
            "aoo_used_this_round": [],
            "flat_footed_actors": [],
            "feint_flat_footed": [],
        },
    )


def _make_rng(d20_roll: int = 15):
    rng = MagicMock()
    stream = MagicMock()
    stream.randint.return_value = d20_roll
    rng.stream.return_value = stream
    return rng


def _run_spell(spell_id: str, conditions: dict, conc_bonus: int = 0, d20_roll: int = 15):
    from aidm.core.spell_resolver import SpellCastIntent
    from aidm.core.play_loop import _resolve_spell_cast
    caster_id = "caster_01"
    ws = _make_spell_world(caster_id, conditions=conditions, conc_bonus=conc_bonus)
    intent = SpellCastIntent(caster_id=caster_id, spell_id=spell_id)
    rng = _make_rng(d20_roll)
    events, ws_after, narration = _resolve_spell_cast(
        intent=intent, world_state=ws, rng=rng,
        grid=None, next_event_id=0, timestamp=0.0, turn_index=0,
    )
    return events, narration


# ---------------------------------------------------------------------------
# GCE-001: Grappled reactor → no AoO
# ---------------------------------------------------------------------------

def test_GCE001_grappled_reactor_no_aoo():
    """GCE-001: Grappled entity in threatened square; enemy provokes → no AoO.
    PHB p.156: 'While grappling, you cannot make attacks of opportunity.'"""
    count = _count_aoo_from_reactor(
        provoker_id="orc_01", reactor_id="fighter_01",
        reactor_conditions={"grappled": {}}
    )
    assert count == 0, (
        f"GCE-001: Grappled entity must not make AoO (PHB p.156). Got count={count}. "
        "Pre-fix: aoo.py had no grappled check; grappled entities could make AoOs."
    )


# ---------------------------------------------------------------------------
# GCE-002: Grappling reactor → no AoO
# ---------------------------------------------------------------------------

def test_GCE002_grappling_reactor_no_aoo():
    """GCE-002: Grappling entity (attacker in pair); enemy provokes → no AoO.
    PHB p.156: Both participants in a grapple cannot make AoOs."""
    count = _count_aoo_from_reactor(
        provoker_id="orc_01", reactor_id="fighter_01",
        reactor_conditions={"grappling": {}}
    )
    assert count == 0, (
        f"GCE-002: Grappling entity must not make AoO (PHB p.156). Got count={count}. "
        "Pre-fix: grappling condition had no AoO block."
    )


# ---------------------------------------------------------------------------
# GCE-003: Grappled caster → Concentration check fires (DC 20 + spell_level)
# ---------------------------------------------------------------------------

def test_GCE003_grappled_caster_concentration_check_fires():
    """GCE-003: Grappled caster casting 2nd level spell → Concentration check fires (DC 22)."""
    from aidm.data.spell_definitions import SPELL_REGISTRY
    if SPELL_REGISTRY.get("scorching_ray") is None:
        pytest.skip("scorching_ray not in registry")
    # d20=1, conc_bonus=0 → total=1 < DC 22 → fails — concentration_failed proves check fired
    events, _ = _run_spell("scorching_ray", conditions={"grappled": {}},
                            conc_bonus=0, d20_roll=1)
    event_types = [e.event_type for e in events]
    assert "concentration_failed" in event_types, (
        f"GCE-003: Grappled caster must trigger Concentration check (PHB p.156). "
        f"Got event_types={event_types}"
    )


# ---------------------------------------------------------------------------
# GCE-004: Grappled caster failing Concentration → spell lost
# ---------------------------------------------------------------------------

def test_GCE004_grappled_caster_fails_concentration_spell_lost():
    """GCE-004: Grappled caster; Concentration fails → concentration_failed with reason=grappled, DC=22."""
    from aidm.data.spell_definitions import SPELL_REGISTRY
    if SPELL_REGISTRY.get("scorching_ray") is None:
        pytest.skip("scorching_ray not in registry")
    events, _ = _run_spell("scorching_ray", conditions={"grappled": {}},
                            conc_bonus=0, d20_roll=1)
    failed = next((e for e in events if e.event_type == "concentration_failed"), None)
    assert failed is not None, "GCE-004: concentration_failed event must be emitted on check failure"
    assert failed.payload.get("reason") == "grappled", (
        f"GCE-004: reason must be 'grappled'; got {failed.payload.get('reason')!r}"
    )
    assert failed.payload.get("dc") == 22, (
        f"GCE-004: DC must be 22 (20 + spell_level=2); got {failed.payload.get('dc')}"
    )


# ---------------------------------------------------------------------------
# GCE-005: Grappled caster passing Concentration → spell resolves
# ---------------------------------------------------------------------------

def test_GCE005_grappled_caster_passes_concentration_spell_resolves():
    """GCE-005: Grappled caster; Concentration succeeds → no concentration_failed, concentration_success fires."""
    from aidm.data.spell_definitions import SPELL_REGISTRY
    if SPELL_REGISTRY.get("scorching_ray") is None:
        pytest.skip("scorching_ray not in registry")
    # DC=22, conc_bonus=10, d20=15 → total=25 ≥ 22 → passes
    events, _ = _run_spell("scorching_ray", conditions={"grappled": {}},
                            conc_bonus=10, d20_roll=15)
    event_types = [e.event_type for e in events]
    assert "concentration_failed" not in event_types, (
        f"GCE-005: concentration_failed must NOT fire when check passes. Got {event_types}"
    )
    assert "concentration_success" in event_types, (
        f"GCE-005: concentration_success must fire when check passes. Got {event_types}"
    )


# ---------------------------------------------------------------------------
# GCE-006: Non-grappled entity with Combat Reflexes CAN make AoOs (regression)
# ---------------------------------------------------------------------------

def test_GCE006_non_grappled_combat_reflexes_aoo_fires():
    """GCE-006: Non-grappled entity with Combat Reflexes; enemy provokes → AoO triggers normally."""
    count = _count_aoo_from_reactor(
        provoker_id="orc_01", reactor_id="fighter_01",
        reactor_conditions={},  # no grapple conditions
        reactor_feats=["combat_reflexes"]
    )
    assert count == 1, (
        f"GCE-006: Non-grappled entity with Combat Reflexes must still make AoOs. Got count={count}. "
        "GCE fix must not block non-grappled AoOs."
    )


# ---------------------------------------------------------------------------
# GCE-007: Pinned somatic block still fires unchanged (regression)
# ---------------------------------------------------------------------------

def test_GCE007_pinned_somatic_block_unchanged():
    """GCE-007: Pinned caster → spell_blocked (somatic) fires. Pinned path must not be broken.
    Pinned blocks somatic outright (PHB p.174); distinct from grappled concentration check."""
    from aidm.data.spell_definitions import SPELL_REGISTRY
    if SPELL_REGISTRY.get("fireball") is None:
        pytest.skip("fireball not in registry")
    events, _ = _run_spell("fireball", conditions={"pinned": {}},
                            conc_bonus=0, d20_roll=20)
    event_types = [e.event_type for e in events]
    assert "spell_blocked" in event_types, (
        f"GCE-007: Pinned caster must get spell_blocked (somatic). Got {event_types}. "
        "GCE fix must not alter the pinned somatic block."
    )
    blocked = next((e for e in events if e.event_type == "spell_blocked"), None)
    assert blocked is not None
    assert blocked.payload.get("reason") == "somatic_component_blocked", (
        f"GCE-007: spell_blocked reason must be 'somatic_component_blocked'; "
        f"got {blocked.payload.get('reason')!r}"
    )


# ---------------------------------------------------------------------------
# GCE-008: get_condition_modifiers() returns aoo_blocked=True for grappled/grappling
# ---------------------------------------------------------------------------

def test_GCE008_condition_modifiers_aoo_blocked_field():
    """GCE-008: get_condition_modifiers() returns aoo_blocked=True when grappled or grappling.
    Verifies the schema update (ConditionModifiers.aoo_blocked) propagates through the
    condition aggregation pipeline."""
    from aidm.core.conditions import get_condition_modifiers
    from aidm.schemas.conditions import create_grappled_condition, create_grappling_condition

    # Test grappled
    ws_grappled = WorldState(
        ruleset_version="3.5e",
        entities={
            "e1": {
                EF.ENTITY_ID: "e1",
                EF.TEAM: "players",
                EF.CONDITIONS: {"grappled": create_grappled_condition("test", 0).to_dict()},
            }
        },
        active_combat=None,
    )
    mods_grappled = get_condition_modifiers(ws_grappled, "e1")
    assert mods_grappled.aoo_blocked is True, (
        f"GCE-008: grappled → aoo_blocked must be True; got {mods_grappled.aoo_blocked}"
    )

    # Test grappling
    ws_grappling = WorldState(
        ruleset_version="3.5e",
        entities={
            "e2": {
                EF.ENTITY_ID: "e2",
                EF.TEAM: "players",
                EF.CONDITIONS: {"grappling": create_grappling_condition("test", 0).to_dict()},
            }
        },
        active_combat=None,
    )
    mods_grappling = get_condition_modifiers(ws_grappling, "e2")
    assert mods_grappling.aoo_blocked is True, (
        f"GCE-008: grappling → aoo_blocked must be True; got {mods_grappling.aoo_blocked}"
    )

    # Test clean entity — aoo_blocked must be False (regression guard)
    ws_clean = WorldState(
        ruleset_version="3.5e",
        entities={
            "e3": {
                EF.ENTITY_ID: "e3",
                EF.TEAM: "players",
                EF.CONDITIONS: {},
            }
        },
        active_combat=None,
    )
    mods_clean = get_condition_modifiers(ws_clean, "e3")
    assert mods_clean.aoo_blocked is False, (
        f"GCE-008: clean entity → aoo_blocked must be False; got {mods_clean.aoo_blocked}"
    )
