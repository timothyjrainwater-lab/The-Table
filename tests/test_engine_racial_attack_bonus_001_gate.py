"""
Gate tests: ENGINE-RACIAL-ATTACK-BONUS-001
WO-ENGINE-RACIAL-ATTACK-BONUS-001

PHB p.15 (Dwarf): +1 racial bonus on attack rolls against orcs and goblinoids.
PHB p.17 (Gnome): +1 racial bonus on attack rolls against kobolds and goblinoids.
PHB p.21 (Halfling): +1 racial bonus on attack rolls with thrown weapons or slings.

Tests RAAB-001 through RAAB-008.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from copy import deepcopy

from aidm.schemas.entity_fields import EF
from aidm.core.state import WorldState
from aidm.core.attack_resolver import resolve_attack
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.core.rng_manager import RNGManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_world_state(entities):
    return WorldState(ruleset_version="3.5", entities=entities)


def _base_entity(entity_id, team="party", hp=30, ac=10, creature_type="humanoid",
                 creature_subtypes=None, conditions=None):
    e = {
        EF.ENTITY_ID: entity_id,
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp,
        EF.AC: ac,
        EF.TEAM: team,
        EF.SAVE_FORT: 2,
        EF.SAVE_REF: 2,
        EF.SAVE_WILL: 2,
        EF.POSITION: {"x": 0, "y": 0},
        EF.CONDITIONS: conditions or {},
        EF.CREATURE_TYPE: creature_type,
        EF.CREATURE_SUBTYPES: creature_subtypes or [],
        EF.STR_MOD: 2,
        EF.DEX_MOD: 0,
    }
    return e


def _dwarf_attacker(entity_id="dwarf", bab=4):
    e = _base_entity(entity_id, team="party", creature_type="humanoid")
    e[EF.ATTACK_BONUS_VS_ORCS] = 1
    e[EF.BAB] = bab
    e[EF.FEATS] = []
    return e


def _gnome_attacker(entity_id="gnome", bab=4):
    e = _base_entity(entity_id, team="party", creature_type="humanoid")
    e[EF.ATTACK_BONUS_VS_KOBOLDS] = 1
    e[EF.BAB] = bab
    e[EF.FEATS] = []
    return e


def _halfling_attacker(entity_id="halfling", bab=4):
    e = _base_entity(entity_id, team="party", creature_type="humanoid")
    e[EF.ATTACK_BONUS_THROWN] = 1
    e[EF.BAB] = bab
    e[EF.FEATS] = []
    return e


def _human_attacker(entity_id="human", bab=4):
    e = _base_entity(entity_id, team="party", creature_type="humanoid")
    e[EF.BAB] = bab
    e[EF.FEATS] = []
    return e


_MELEE_WEAPON = Weapon(
    damage_dice="1d8",
    damage_bonus=0,
    damage_type="slashing",
    weapon_type="one-handed",
    is_thrown=False,
)

_THROWN_WEAPON = Weapon(
    damage_dice="1d4",
    damage_bonus=0,
    damage_type="piercing",
    weapon_type="ranged",
    range_increment=20,
    is_thrown=True,
)


def _make_intent(attacker_id, target_id, weapon=None, attack_bonus=4):
    return AttackIntent(
        attacker_id=attacker_id,
        target_id=target_id,
        weapon=weapon or _MELEE_WEAPON,
        attack_bonus=attack_bonus,
    )


def _run_attacks(attacker, target, weapon=None, n=40, base_ab=4):
    """Run n attacks and return set of d20 rolls + AB combinations observed."""
    ws = _make_world_state({attacker[EF.ENTITY_ID]: deepcopy(attacker),
                            target[EF.ENTITY_ID]: deepcopy(target)})
    total_attack_bonus_seen = []
    for seed in range(n):
        rng = RNGManager(master_seed=seed)
        intent = _make_intent(attacker[EF.ENTITY_ID], target[EF.ENTITY_ID],
                              weapon=weapon, attack_bonus=base_ab)
        events, _, _ = resolve_attack(intent, ws, rng, next_event_id=1, timestamp=0.0)
        for ev in events:
            if ev.event_type == "attack_rolled":
                total_attack_bonus_seen.append(ev.payload.get("attack_bonus", 0))
    return total_attack_bonus_seen


# ---------------------------------------------------------------------------
# RAAB-001: Dwarf vs. orc entity: attack bonus +1 vs. dwarf vs. human
# ---------------------------------------------------------------------------

def test_raab_001_dwarf_vs_orc():
    """RAAB-001: Dwarf attack bonus vs. orc is +1 higher than vs. human target."""
    dwarf = _dwarf_attacker()
    orc_target = _base_entity("orc_target", team="enemy", creature_subtypes=["orc"])
    human_target = _base_entity("human_target", team="enemy", creature_subtypes=[])

    ws_orc = _make_world_state({"dwarf": deepcopy(dwarf), "orc_target": orc_target})
    ws_human = _make_world_state({"dwarf": deepcopy(dwarf), "human_target": human_target})

    rng = RNGManager(master_seed=5)
    intent_orc = _make_intent("dwarf", "orc_target")
    intent_human = _make_intent("dwarf", "human_target")

    events_orc = resolve_attack(intent_orc, ws_orc, RNGManager(master_seed=5),
                                next_event_id=1, timestamp=0.0)
    events_human = resolve_attack(intent_human, ws_human, RNGManager(master_seed=5),
                                   next_event_id=1, timestamp=0.0)

    ab_orc = next(e.payload["total"] for e in events_orc if e.event_type == "attack_roll")
    ab_human = next(e.payload["total"] for e in events_human if e.event_type == "attack_roll")

    assert ab_orc == ab_human + 1, (
        f"Dwarf vs orc should be +1 vs human: orc={ab_orc}, human={ab_human}"
    )


# ---------------------------------------------------------------------------
# RAAB-002: Dwarf vs. goblinoid entity: attack bonus +1
# ---------------------------------------------------------------------------

def test_raab_002_dwarf_vs_goblinoid():
    """RAAB-002: Dwarf attack bonus vs. goblinoid is +1 higher than vs. human."""
    dwarf = _dwarf_attacker()
    goblinoid_target = _base_entity("goblinoid_target", team="enemy", creature_subtypes=["goblinoid"])
    human_target = _base_entity("human_target", team="enemy", creature_subtypes=[])

    ws_gob = _make_world_state({"dwarf": deepcopy(dwarf), "goblinoid_target": goblinoid_target})
    ws_human = _make_world_state({"dwarf": deepcopy(dwarf), "human_target": human_target})

    events_gob = resolve_attack(
        _make_intent("dwarf", "goblinoid_target"), ws_gob, RNGManager(master_seed=5),
        next_event_id=1, timestamp=0.0)
    events_human = resolve_attack(
        _make_intent("dwarf", "human_target"), ws_human, RNGManager(master_seed=5),
        next_event_id=1, timestamp=0.0)

    ab_gob = next(e.payload["total"] for e in events_gob if e.event_type == "attack_roll")
    ab_human = next(e.payload["total"] for e in events_human if e.event_type == "attack_roll")

    assert ab_gob == ab_human + 1, (
        f"Dwarf vs goblinoid should be +1 vs human: gob={ab_gob}, human={ab_human}"
    )


# ---------------------------------------------------------------------------
# RAAB-003: Gnome vs. kobold entity: attack bonus +1
# ---------------------------------------------------------------------------

def test_raab_003_gnome_vs_kobold():
    """RAAB-003: Gnome attack bonus vs. kobold is +1 higher than vs. human."""
    gnome = _gnome_attacker()
    kobold_target = _base_entity("kobold_target", team="enemy", creature_subtypes=["kobold"])
    human_target = _base_entity("human_target", team="enemy", creature_subtypes=[])

    ws_kob = _make_world_state({"gnome": deepcopy(gnome), "kobold_target": kobold_target})
    ws_human = _make_world_state({"gnome": deepcopy(gnome), "human_target": human_target})

    events_kob = resolve_attack(
        _make_intent("gnome", "kobold_target"), ws_kob, RNGManager(master_seed=5),
        next_event_id=1, timestamp=0.0)
    events_human = resolve_attack(
        _make_intent("gnome", "human_target"), ws_human, RNGManager(master_seed=5),
        next_event_id=1, timestamp=0.0)

    ab_kob = next(e.payload["total"] for e in events_kob if e.event_type == "attack_roll")
    ab_human = next(e.payload["total"] for e in events_human if e.event_type == "attack_roll")

    assert ab_kob == ab_human + 1, (
        f"Gnome vs kobold should be +1 vs human: kob={ab_kob}, human={ab_human}"
    )


# ---------------------------------------------------------------------------
# RAAB-004: Gnome vs. goblinoid entity: attack bonus +1
# ---------------------------------------------------------------------------

def test_raab_004_gnome_vs_goblinoid():
    """RAAB-004: Gnome attack bonus vs. goblinoid is +1 higher than vs. human."""
    gnome = _gnome_attacker()
    goblinoid_target = _base_entity("goblinoid_target", team="enemy", creature_subtypes=["goblinoid"])
    human_target = _base_entity("human_target", team="enemy", creature_subtypes=[])

    ws_gob = _make_world_state({"gnome": deepcopy(gnome), "goblinoid_target": goblinoid_target})
    ws_human = _make_world_state({"gnome": deepcopy(gnome), "human_target": human_target})

    events_gob = resolve_attack(
        _make_intent("gnome", "goblinoid_target"), ws_gob, RNGManager(master_seed=5),
        next_event_id=1, timestamp=0.0)
    events_human = resolve_attack(
        _make_intent("gnome", "human_target"), ws_human, RNGManager(master_seed=5),
        next_event_id=1, timestamp=0.0)

    ab_gob = next(e.payload["total"] for e in events_gob if e.event_type == "attack_roll")
    ab_human = next(e.payload["total"] for e in events_human if e.event_type == "attack_roll")

    assert ab_gob == ab_human + 1, (
        f"Gnome vs goblinoid should be +1 vs human: gob={ab_gob}, human={ab_human}"
    )


# ---------------------------------------------------------------------------
# RAAB-005: Halfling with thrown weapon: attack bonus +1 vs. halfling with melee
# ---------------------------------------------------------------------------

def test_raab_005_halfling_thrown_vs_melee():
    """RAAB-005: Halfling thrown weapon attack is +1 vs halfling melee attack vs same target."""
    halfling = _halfling_attacker()
    target = _base_entity("target", team="enemy")

    ws = _make_world_state({"halfling": deepcopy(halfling), "target": target})

    intent_thrown = _make_intent("halfling", "target", weapon=_THROWN_WEAPON)
    intent_melee = _make_intent("halfling", "target", weapon=_MELEE_WEAPON)

    events_thrown = resolve_attack(intent_thrown, ws, RNGManager(master_seed=5),
                                   next_event_id=1, timestamp=0.0)
    events_melee = resolve_attack(intent_melee, ws, RNGManager(master_seed=5),
                                  next_event_id=1, timestamp=0.0)

    ab_thrown = next(e.payload["total"] for e in events_thrown if e.event_type == "attack_roll")
    ab_melee = next(e.payload["total"] for e in events_melee if e.event_type == "attack_roll")

    assert ab_thrown == ab_melee + 1, (
        f"Halfling thrown should be +1 vs melee: thrown={ab_thrown}, melee={ab_melee}"
    )


# ---------------------------------------------------------------------------
# RAAB-006: Dwarf vs. giant (not orc): NO racial attack bonus
# ---------------------------------------------------------------------------

def test_raab_006_dwarf_vs_giant_no_bonus():
    """RAAB-006: Dwarf gets NO racial attack bonus vs. giant (only vs. orcs/goblinoids)."""
    dwarf = _dwarf_attacker()
    giant_target = _base_entity("giant_target", team="enemy",
                                 creature_type="giant", creature_subtypes=[])
    human_target = _base_entity("human_target", team="enemy", creature_subtypes=[])

    ws_giant = _make_world_state({"dwarf": deepcopy(dwarf), "giant_target": giant_target})
    ws_human = _make_world_state({"dwarf": deepcopy(dwarf), "human_target": human_target})

    events_giant = resolve_attack(
        _make_intent("dwarf", "giant_target"), ws_giant, RNGManager(master_seed=5),
        next_event_id=1, timestamp=0.0)
    events_human = resolve_attack(
        _make_intent("dwarf", "human_target"), ws_human, RNGManager(master_seed=5),
        next_event_id=1, timestamp=0.0)

    ab_giant = next(e.payload["total"] for e in events_giant if e.event_type == "attack_roll")
    ab_human = next(e.payload["total"] for e in events_human if e.event_type == "attack_roll")

    assert ab_giant == ab_human, (
        f"Dwarf vs giant should equal dwarf vs human (no bonus): giant={ab_giant}, human={ab_human}"
    )


# ---------------------------------------------------------------------------
# RAAB-007: Human vs. orc: NO racial attack bonus
# ---------------------------------------------------------------------------

def test_raab_007_human_vs_orc_no_bonus():
    """RAAB-007: Human attacker gets NO racial attack bonus vs. orc."""
    human_attacker = _human_attacker("human_atk")
    orc_target = _base_entity("orc_target", team="enemy", creature_subtypes=["orc"])
    human_target = _base_entity("human_target", team="enemy", creature_subtypes=[])

    ws_orc = _make_world_state({"human_atk": deepcopy(human_attacker), "orc_target": orc_target})
    ws_human = _make_world_state({"human_atk": deepcopy(human_attacker), "human_target": human_target})

    events_orc = resolve_attack(
        _make_intent("human_atk", "orc_target"), ws_orc, RNGManager(master_seed=5),
        next_event_id=1, timestamp=0.0)
    events_human = resolve_attack(
        _make_intent("human_atk", "human_target"), ws_human, RNGManager(master_seed=5),
        next_event_id=1, timestamp=0.0)

    ab_orc = next(e.payload["total"] for e in events_orc if e.event_type == "attack_roll")
    ab_human = next(e.payload["total"] for e in events_human if e.event_type == "attack_roll")

    assert ab_orc == ab_human, (
        f"Human vs orc should equal human vs human (no racial bonus): orc={ab_orc}, human={ab_human}"
    )


# ---------------------------------------------------------------------------
# RAAB-008: Dwarf bonus applies once even if target has both orc AND goblinoid subtypes
# ---------------------------------------------------------------------------

def test_raab_008_dwarf_bonus_applied_once():
    """RAAB-008: Dwarf +1 bonus applied once even if target has both orc+goblinoid subtypes."""
    dwarf = _dwarf_attacker()
    dual_target = _base_entity("dual_target", team="enemy", creature_subtypes=["orc", "goblinoid"])
    human_target = _base_entity("human_target", team="enemy", creature_subtypes=[])

    ws_dual = _make_world_state({"dwarf": deepcopy(dwarf), "dual_target": dual_target})
    ws_human = _make_world_state({"dwarf": deepcopy(dwarf), "human_target": human_target})

    events_dual = resolve_attack(
        _make_intent("dwarf", "dual_target"), ws_dual, RNGManager(master_seed=5),
        next_event_id=1, timestamp=0.0)
    events_human = resolve_attack(
        _make_intent("dwarf", "human_target"), ws_human, RNGManager(master_seed=5),
        next_event_id=1, timestamp=0.0)

    ab_dual = next(e.payload["total"] for e in events_dual if e.event_type == "attack_roll")
    ab_human = next(e.payload["total"] for e in events_human if e.event_type == "attack_roll")

    assert ab_dual == ab_human + 1, (
        f"Dwarf vs dual orc/goblinoid should be exactly +1 (not +2): dual={ab_dual}, human={ab_human}"
    )
