"""Gate ENGINE-ENERGY-DRAIN — WO-ENGINE-ENERGY-DRAIN-001: Negative Levels.

Tests (10/10):
ED-01: EnergyDrainAttackIntent resolves attack roll first (normal to-hit mechanics)
ED-02: Miss → no negative_levels_applied events emitted
ED-03: Hit → negative_levels_applied event emitted
ED-04: Each negative_levels_applied event: hp_max_reduced_by == N * 5
ED-05: Entity's subsequent attack rolls penalized by -1 per negative level
ED-06: Entity's subsequent saving throws penalized by -1 per negative level
ED-07: Spellcaster loses highest available spell slot on each negative level
ED-08: total_negative_levels >= target HD_COUNT → energy_drain_death emitted, entity defeated
ED-09: Two hits from same attacker accumulate negative levels (additive, not overwrite)
ED-10: Negative levels persist across rounds (no rest cure)
"""

import unittest.mock as mock
from copy import deepcopy
from typing import Any, Dict

import pytest

from aidm.core.action_economy import get_action_type
from aidm.core.attack_resolver import resolve_attack
from aidm.core.energy_drain_resolver import (
    apply_energy_drain_events,
    get_negative_level_attack_penalty,
    get_negative_level_save_penalty,
    resolve_energy_drain,
)
from aidm.core.rest_resolver import resolve_rest
from aidm.core.state import WorldState
from aidm.schemas.attack import AttackIntent, EnergyDrainAttackIntent, Weapon
from aidm.schemas.entity_fields import EF
from aidm.schemas.intents import RestIntent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _natural_weapon(damage_dice: str = "1d6") -> Weapon:
    return Weapon(
        damage_dice=damage_dice,
        damage_bonus=0,
        damage_type="negative",
        critical_range=20,
        critical_multiplier=2,
        grip="one-handed",
        is_two_handed=False,
        weapon_type="natural",
    )


def _attacker(eid: str = "wight1", neg_levels: int = 0) -> Dict[str, Any]:
    e = {
        EF.ENTITY_ID: eid,
        EF.TEAM: "monsters",
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 30,
        EF.AC: 14,
        EF.ATTACK_BONUS: 5,
        EF.BAB: 5,
        EF.STR_MOD: 2,
        EF.DEX_MOD: 1,
        EF.LEVEL: 5,
        EF.HD_COUNT: 5,
        EF.DEFEATED: False,
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.POSITION: {"x": 0, "y": 0},
        EF.SIZE_CATEGORY: "medium",
    }
    if neg_levels:
        e[EF.NEGATIVE_LEVELS] = neg_levels
    return e


def _target(
    eid: str = "hero1",
    hp: int = 20,
    hp_max: int = 20,
    ac: int = 10,
    hd: int = 4,
    spell_slots: Dict = None,
    neg_levels: int = 0,
) -> Dict[str, Any]:
    e = {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp_max,
        EF.AC: ac,
        EF.HD_COUNT: hd,
        EF.LEVEL: hd,
        EF.BAB: hd,
        EF.STR_MOD: 1,
        EF.DEX_MOD: 1,
        EF.CON_MOD: 1,
        EF.SAVE_FORT: 4,
        EF.SAVE_REF: 2,
        EF.SAVE_WILL: 3,
        EF.ATTACK_BONUS: hd,
        EF.DEFEATED: False,
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.POSITION: {"x": 1, "y": 0},
        EF.SIZE_CATEGORY: "medium",
    }
    if spell_slots is not None:
        e[EF.SPELL_SLOTS] = dict(spell_slots)
    if neg_levels:
        e[EF.NEGATIVE_LEVELS] = neg_levels
    return e


def _world(*entities) -> WorldState:
    return WorldState(
        ruleset_version="3.5e",
        entities={e[EF.ENTITY_ID]: e for e in entities},
        active_combat={"initiative_order": [e[EF.ENTITY_ID] for e in entities]},
    )


def _rng_hit(damage: int = 4):
    """RNG: attack roll = 15 (guaranteed hit vs AC 10), damage = given."""
    stream = mock.MagicMock()
    stream.randint.side_effect = [15, damage] + [3] * 20
    rng = mock.MagicMock()
    rng.stream.return_value = stream
    return rng


def _rng_miss():
    """RNG: attack roll = 1 (natural 1 = always miss)."""
    stream = mock.MagicMock()
    stream.randint.side_effect = [1] + [3] * 20
    rng = mock.MagicMock()
    rng.stream.return_value = stream
    return rng


# ---------------------------------------------------------------------------
# ED-01: EnergyDrainAttackIntent resolves attack roll first
# ---------------------------------------------------------------------------

def test_ed01_attack_roll_emitted():
    """EnergyDrainAttackIntent resolves attack_roll event as first event."""
    wight = _attacker()
    hero = _target(ac=10)
    ws = _world(wight, hero)
    intent = EnergyDrainAttackIntent(
        attacker_id="wight1",
        target_id="hero1",
        attack_bonus=5,
        weapon=_natural_weapon(),
        negative_levels_per_hit=1,
    )
    rng = _rng_hit(damage=3)
    events = resolve_energy_drain(intent, ws, rng, next_event_id=0, timestamp=0.0)

    assert events[0].event_type == "attack_roll"
    assert "hit" in events[0].payload


# ---------------------------------------------------------------------------
# ED-02: Miss → no negative_levels_applied
# ---------------------------------------------------------------------------

def test_ed02_miss_no_drain():
    """Attack miss → no negative_levels_applied event."""
    wight = _attacker()
    hero = _target(ac=10)
    ws = _world(wight, hero)
    intent = EnergyDrainAttackIntent(
        attacker_id="wight1", target_id="hero1",
        attack_bonus=5, weapon=_natural_weapon(), negative_levels_per_hit=1,
    )
    rng = _rng_miss()
    events = resolve_energy_drain(intent, ws, rng, next_event_id=0, timestamp=0.0)

    drain_evs = [e for e in events if e.event_type == "negative_levels_applied"]
    assert len(drain_evs) == 0

    atk_ev = events[0]
    assert atk_ev.event_type == "attack_roll"
    assert atk_ev.payload["hit"] is False


# ---------------------------------------------------------------------------
# ED-03: Hit → negative_levels_applied event
# ---------------------------------------------------------------------------

def test_ed03_hit_drain_event_emitted():
    """Attack hit → negative_levels_applied event emitted."""
    wight = _attacker()
    hero = _target(ac=5)  # Very low AC to guarantee hit
    ws = _world(wight, hero)
    intent = EnergyDrainAttackIntent(
        attacker_id="wight1", target_id="hero1",
        attack_bonus=5, weapon=_natural_weapon(), negative_levels_per_hit=1,
    )
    rng = _rng_hit(damage=2)
    events = resolve_energy_drain(intent, ws, rng, next_event_id=0, timestamp=0.0)

    drain_ev = next((e for e in events if e.event_type == "negative_levels_applied"), None)
    assert drain_ev is not None
    p = drain_ev.payload
    assert p["attacker_id"] == "wight1"
    assert p["target_id"] == "hero1"
    assert p["negative_levels_added"] == 1
    assert p["total_negative_levels"] == 1


# ---------------------------------------------------------------------------
# ED-04: hp_max_reduced_by == N * 5 per hit
# ---------------------------------------------------------------------------

def test_ed04_hp_max_reduced_by_5_per_level():
    """Wight (1 neg level per hit): hp_max_reduced_by == 5."""
    wight = _attacker()
    hero = _target(ac=5, hp=20, hp_max=20)
    ws = _world(wight, hero)
    intent = EnergyDrainAttackIntent(
        attacker_id="wight1", target_id="hero1",
        attack_bonus=5, weapon=_natural_weapon(), negative_levels_per_hit=1,
    )
    rng = _rng_hit(damage=2)
    events = resolve_energy_drain(intent, ws, rng, next_event_id=0, timestamp=0.0)

    drain_ev = next((e for e in events if e.event_type == "negative_levels_applied"), None)
    assert drain_ev is not None
    assert drain_ev.payload["hp_max_reduced_by"] == 5
    assert drain_ev.payload["hp_max_after"] == 15

    # Vampire bestows 2 negative levels per hit → 10 HP
    vampire = _attacker(eid="vampire1")
    hero2 = _target(eid="hero2", ac=5, hp=20, hp_max=20)
    ws2 = _world(vampire, hero2)
    intent2 = EnergyDrainAttackIntent(
        attacker_id="vampire1", target_id="hero2",
        attack_bonus=5, weapon=_natural_weapon(), negative_levels_per_hit=2,
    )
    rng2 = _rng_hit(damage=2)
    events2 = resolve_energy_drain(intent2, ws2, rng2, next_event_id=0, timestamp=0.0)

    drain_ev2 = next((e for e in events2 if e.event_type == "negative_levels_applied"), None)
    assert drain_ev2 is not None
    assert drain_ev2.payload["hp_max_reduced_by"] == 10
    assert drain_ev2.payload["hp_max_after"] == 10


# ---------------------------------------------------------------------------
# ED-05: Subsequent attack roll penalized by -1 per negative level
# ---------------------------------------------------------------------------

def test_ed05_attack_penalty_from_negative_levels():
    """Entity with NEGATIVE_LEVELS=2 has -2 on attack rolls."""
    # get_negative_level_attack_penalty returns -N
    hero = _target(neg_levels=2)
    penalty = get_negative_level_attack_penalty(hero)
    assert penalty == -2

    hero0 = _target(neg_levels=0)
    assert get_negative_level_attack_penalty(hero0) == 0

    hero_no_field = _target()
    # NEGATIVE_LEVELS not set → defaults to 0 → penalty 0
    assert EF.NEGATIVE_LEVELS not in hero_no_field
    assert get_negative_level_attack_penalty(hero_no_field) == 0


# ---------------------------------------------------------------------------
# ED-06: Subsequent saving throws penalized by -1 per negative level
# ---------------------------------------------------------------------------

def test_ed06_save_penalty_from_negative_levels():
    """Entity with NEGATIVE_LEVELS=3 has -3 on saving throws."""
    hero = _target(neg_levels=3)
    assert get_negative_level_save_penalty(hero) == -3

    hero0 = _target()
    assert get_negative_level_save_penalty(hero0) == 0


def test_ed06b_save_penalty_applied_in_target_stats():
    """Negative level save penalty is pre-subtracted from TargetStats in play_loop."""
    # Verify the play_loop _create_target_stats subtracts neg levels from saves
    from aidm.core.play_loop import _create_target_stats
    hero = _target(neg_levels=2)
    hero[EF.SAVE_FORT] = 5
    hero[EF.SAVE_WILL] = 3
    ws = _world(hero)
    stats = _create_target_stats("hero1", ws)
    assert stats.fort_save == 3   # 5 - 2
    assert stats.will_save == 1   # 3 - 2


# ---------------------------------------------------------------------------
# ED-07: Spellcaster loses highest available spell slot on negative level
# ---------------------------------------------------------------------------

def test_ed07_spell_slot_drained():
    """Spellcaster hit by energy drain loses highest available spell slot."""
    wight = _attacker()
    # Wizard with spell slots: level 3=1, level 2=2, level 1=3
    hero = _target(ac=5, spell_slots={3: 1, 2: 2, 1: 3})
    ws = _world(wight, hero)
    intent = EnergyDrainAttackIntent(
        attacker_id="wight1", target_id="hero1",
        attack_bonus=5, weapon=_natural_weapon(), negative_levels_per_hit=1,
    )
    rng = _rng_hit(damage=2)
    events = resolve_energy_drain(intent, ws, rng, next_event_id=0, timestamp=0.0)

    drain_ev = next((e for e in events if e.event_type == "negative_levels_applied"), None)
    assert drain_ev is not None
    # Highest slot is level 3
    assert drain_ev.payload["spell_slot_lost"] == 3


def test_ed07b_non_caster_spell_slot_lost_is_none():
    """Non-caster target: spell_slot_lost is None."""
    wight = _attacker()
    hero = _target(ac=5)  # no spell slots field
    ws = _world(wight, hero)
    intent = EnergyDrainAttackIntent(
        attacker_id="wight1", target_id="hero1",
        attack_bonus=5, weapon=_natural_weapon(), negative_levels_per_hit=1,
    )
    rng = _rng_hit(damage=2)
    events = resolve_energy_drain(intent, ws, rng, next_event_id=0, timestamp=0.0)

    drain_ev = next((e for e in events if e.event_type == "negative_levels_applied"), None)
    assert drain_ev is not None
    assert drain_ev.payload["spell_slot_lost"] is None


# ---------------------------------------------------------------------------
# ED-08: total_negative_levels >= HD_COUNT → energy_drain_death + entity defeated
# ---------------------------------------------------------------------------

def test_ed08_energy_drain_death():
    """total_negative_levels >= HD_COUNT (4) → energy_drain_death emitted, entity defeated."""
    wight = _attacker()
    # HD=4; already 3 negative levels; 1 more → total=4 >= 4
    hero = _target(ac=5, hd=4, neg_levels=3)
    ws = _world(wight, hero)
    intent = EnergyDrainAttackIntent(
        attacker_id="wight1", target_id="hero1",
        attack_bonus=5, weapon=_natural_weapon(), negative_levels_per_hit=1,
    )
    rng = _rng_hit(damage=2)
    events = resolve_energy_drain(intent, ws, rng, next_event_id=0, timestamp=0.0)

    death_ev = next((e for e in events if e.event_type == "energy_drain_death"), None)
    assert death_ev is not None
    assert death_ev.payload["target_id"] == "hero1"
    assert death_ev.payload["negative_levels"] == 4
    assert death_ev.payload["effective_hd"] == 4

    updated = apply_energy_drain_events(events, ws)
    assert updated.entities["hero1"][EF.DEFEATED] is True


# ---------------------------------------------------------------------------
# ED-09: Two hits accumulate negative levels (additive, not overwrite)
# ---------------------------------------------------------------------------

def test_ed09_two_hits_accumulate_negative_levels():
    """Two separate hits accumulate NEGATIVE_LEVELS correctly (1+1=2)."""
    wight = _attacker()
    hero = _target(ac=5, hp=20, hp_max=20, hd=10)
    ws = _world(wight, hero)
    weapon = _natural_weapon()

    # First hit
    intent1 = EnergyDrainAttackIntent(
        attacker_id="wight1", target_id="hero1",
        attack_bonus=5, weapon=weapon, negative_levels_per_hit=1,
    )
    rng1 = _rng_hit(damage=2)
    events1 = resolve_energy_drain(intent1, ws, rng1, next_event_id=0, timestamp=0.0)
    ws = apply_energy_drain_events(events1, ws)

    drain_ev1 = next((e for e in events1 if e.event_type == "negative_levels_applied"), None)
    assert drain_ev1.payload["total_negative_levels"] == 1

    # Second hit (state persisted)
    intent2 = EnergyDrainAttackIntent(
        attacker_id="wight1", target_id="hero1",
        attack_bonus=5, weapon=weapon, negative_levels_per_hit=1,
    )
    rng2 = _rng_hit(damage=2)
    events2 = resolve_energy_drain(intent2, ws, rng2, next_event_id=10, timestamp=1.0)
    ws = apply_energy_drain_events(events2, ws)

    drain_ev2 = next((e for e in events2 if e.event_type == "negative_levels_applied"), None)
    assert drain_ev2 is not None
    assert drain_ev2.payload["total_negative_levels"] == 2  # additive

    assert ws.entities["hero1"].get(EF.NEGATIVE_LEVELS) == 2


# ---------------------------------------------------------------------------
# ED-10: Negative levels persist across rounds (overnight rest does NOT cure)
# ---------------------------------------------------------------------------

def test_ed10_negative_levels_persist_after_rest():
    """Negative levels are NOT cleared by overnight rest (PHB p.215 — 24h save only)."""
    hero = _target(neg_levels=2)
    ws = WorldState(
        ruleset_version="3.5e",
        entities={"hero1": hero},
        active_combat=None,
    )
    rest_intent = RestIntent(rest_type="overnight")
    resolve_rest(rest_intent, ws, actor_id="hero1")

    assert ws.entities["hero1"].get(EF.NEGATIVE_LEVELS, 0) == 2  # unchanged
