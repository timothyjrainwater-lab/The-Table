"""Gate tests: Monk Flurry of Blows — WO-ENGINE-FLURRY-OF-BLOWS-001.

FOB-001: Monk L3 unarmored light load — 2 attacks at BAB-2
FOB-002: Monk L6 — 2 attacks at BAB-1
FOB-003: Monk L12 — 3 attacks at no penalty
FOB-004: Monk in armor — blocked (wearing_armor)
FOB-005: Monk with longsword — blocked (invalid_weapon)
FOB-006: Monk L5 with kama — allowed (-1 penalty)
FOB-007: Non-monk — blocked (not_a_monk)
FOB-008: Monk 6 / Fighter 4 multiclass — flurry based on monk 6 levels
"""

import pytest
from copy import deepcopy
from aidm.core.flurry_of_blows_resolver import (
    FlurryOfBlowsIntent, resolve_flurry_of_blows, _flurry_attack_bonuses,
)
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF


class _FixedRNG:
    """RNG that always returns a fixed value on randint calls."""
    def __init__(self, value: int = 10):
        self._value = value

    def stream(self, name):
        return self

    def randint(self, lo, hi):
        return min(max(self._value, lo), hi)

    def random(self):
        return 0.5


def _make_ws(entities: dict) -> WorldState:
    return WorldState(
        ruleset_version="3.5",
        entities=entities,
        active_combat=None,
    )


def _target(ac: int = 10) -> dict:
    return {
        EF.HP_CURRENT: 50,
        EF.HP_MAX: 50,
        EF.AC: ac,
        EF.DEFEATED: False,
        EF.TEAM: "monsters",
        EF.POSITION: {"x": 1, "y": 0},
        EF.CONDITIONS: [],
    }


def _monk(
    level: int,
    *,
    armor: str = "none",
    enc: str = "light",
    bab: int | None = None,
    attack_bonus: int | None = None,
    class_mix: dict | None = None,
    weapon_data: dict | None = None,
) -> dict:
    """Build a minimal monk entity dict for flurry tests."""
    # Monk BAB ≈ 3/4 level (PHB Table 3-10)
    _monk_bab_table = [
        (20, 15), (16, 12), (12, 9), (8, 6), (6, 4), (4, 3), (3, 2), (2, 1), (1, 0),
    ]
    if bab is None:
        bab = next(b for t, b in _monk_bab_table if level >= t)
    if attack_bonus is None:
        attack_bonus = bab  # STR mod = 0 for clean entities

    entity = {
        EF.CLASS_LEVELS: class_mix or {"monk": level},
        EF.BAB: bab,
        EF.ATTACK_BONUS: attack_bonus,
        EF.ARMOR_TYPE: armor,
        EF.ENCUMBRANCE_LOAD: enc,
        EF.MONK_UNARMED_DICE: "1d6",
        EF.HP_CURRENT: 50,
        EF.HP_MAX: 50,
        EF.AC: 12,
        EF.DEFEATED: False,
        EF.TEAM: "party",
        EF.POSITION: {"x": 0, "y": 0},
        EF.CONDITIONS: [],
        EF.FEATS: [],
        EF.STR_MOD: 0,
        EF.NEGATIVE_LEVELS: 0,
    }
    if weapon_data is not None:
        entity[EF.WEAPON] = weapon_data
    return entity


def _resolve(actor: dict, target: dict, actor_id: str = "monk", target_id: str = "target"):
    ws = _make_ws({actor_id: actor, target_id: target})
    intent = FlurryOfBlowsIntent(actor_id=actor_id, target_id=target_id)
    events, _ = resolve_flurry_of_blows(intent, ws, _FixedRNG(15), 1, 0.0)
    return events


# ── FOB-001: Monk L3 unarmored light load — 2 attacks at BAB-2 ───────────────

def test_fob001_monk_l3_two_attacks_at_minus2():
    """L3 monk: 2 flurry attacks; BAB=2, penalty=-2 → both at bonus 0."""
    actor = _monk(3)  # BAB=2, attack_bonus=2
    events = _resolve(actor, _target())
    attack_events = [e for e in events if e.event_type == "attack_roll"]
    assert len(attack_events) == 2, f"Expected 2 attacks, got {len(attack_events)}"
    for ev in attack_events:
        assert ev.payload["attack_bonus"] == 0, (
            f"Expected bonus 0 (BAB 2 - 2), got {ev.payload['attack_bonus']}"
        )


# ── FOB-002: Monk L6 — 2 attacks at BAB-1 ────────────────────────────────────

def test_fob002_monk_l6_two_attacks_at_minus1():
    """L6 monk: 2 flurry attacks; BAB=4, penalty=-1 → both at bonus 3."""
    actor = _monk(6)  # BAB=4, attack_bonus=4
    events = _resolve(actor, _target())
    attack_events = [e for e in events if e.event_type == "attack_roll"]
    assert len(attack_events) == 2
    for ev in attack_events:
        assert ev.payload["attack_bonus"] == 3, (
            f"Expected bonus 3 (BAB 4 - 1), got {ev.payload['attack_bonus']}"
        )


# ── FOB-003: Monk L12 — 3 attacks at no penalty ──────────────────────────────

def test_fob003_monk_l12_three_attacks_no_penalty():
    """L12 monk: 3 flurry attacks; BAB=9, penalty=0 → [9, 9, 4]."""
    actor = _monk(12)  # BAB=9, attack_bonus=9
    events = _resolve(actor, _target(ac=5))  # AC 5 ensures hits for clean measurement
    attack_events = [e for e in events if e.event_type == "attack_roll"]
    assert len(attack_events) == 3
    bonuses = [ev.payload["attack_bonus"] for ev in attack_events]
    assert bonuses == [9, 9, 4], f"Expected [9, 9, 4], got {bonuses}"


# ── FOB-004: Monk in light armor — blocked ────────────────────────────────────

def test_fob004_monk_in_armor_blocked():
    """Monk wearing light armor: flurry blocked (any armor blocks)."""
    actor = _monk(3, armor="light")
    events = _resolve(actor, _target())
    blocked = [e for e in events if e.event_type == "flurry_blocked"]
    assert len(blocked) == 1
    assert blocked[0].payload["reason"] == "wearing_armor"
    assert not any(e.event_type == "attack_roll" for e in events)


# ── FOB-005: Monk with longsword — blocked ────────────────────────────────────

def test_fob005_monk_with_longsword_blocked():
    """Monk wielding a longsword (non-monk weapon): flurry blocked."""
    longsword = {
        "weapon_id": "longsword",
        "damage_dice": "1d8",
        "damage_bonus": 0,
        "damage_type": "slashing",
        "weapon_type": "one-handed",
    }
    actor = _monk(5, weapon_data=longsword)
    events = _resolve(actor, _target())
    blocked = [e for e in events if e.event_type == "flurry_blocked"]
    assert len(blocked) == 1
    assert blocked[0].payload["reason"] == "invalid_weapon"


# ── FOB-006: Monk L5 with kama (monk weapon) — allowed ───────────────────────

def test_fob006_monk_l5_kama_flurry_permitted():
    """L5 monk with kama (monk weapon): flurry permitted; penalty -1."""
    kama = {
        "weapon_id": "kama",
        "damage_dice": "1d6",
        "damage_bonus": 0,
        "damage_type": "slashing",
        "weapon_type": "light",
    }
    actor = _monk(5, weapon_data=kama)  # BAB=3, attack_bonus=3, penalty=-1 → bonus=2
    events = _resolve(actor, _target())
    assert not any(e.event_type == "flurry_blocked" for e in events)
    attack_events = [e for e in events if e.event_type == "attack_roll"]
    assert len(attack_events) == 2
    for ev in attack_events:
        assert ev.payload["attack_bonus"] == 2, (
            f"Expected kama bonus 2 (BAB 3 - 1), got {ev.payload['attack_bonus']}"
        )


# ── FOB-007: Non-monk character — blocked ─────────────────────────────────────

def test_fob007_non_monk_blocked():
    """Non-monk (fighter) cannot use flurry."""
    actor = _monk(5)
    actor[EF.CLASS_LEVELS] = {"fighter": 5}  # Override to non-monk
    events = _resolve(actor, _target())
    blocked = [e for e in events if e.event_type == "flurry_blocked"]
    assert len(blocked) == 1
    assert blocked[0].payload["reason"] == "not_a_monk"


# ── FOB-008: Monk 6 / Fighter 4 multiclass — monk 6 penalty applies ──────────

def test_fob008_multiclass_monk6_fighter4():
    """Monk6/Fighter4: flurry allowed; penalty based on monk 6 (-1).
    Combined BAB = 4 (monk) + 4 (fighter) = 8. Penalty = -1.
    Attacks: [7, 7, 2] (extra + BAB-8 + iterative at BAB-3).
    """
    actor = _monk(
        6,
        class_mix={"monk": 6, "fighter": 4},
        bab=8,         # Sum: monk BAB 4 + fighter BAB 4
        attack_bonus=8,
    )
    events = _resolve(actor, _target(ac=5))
    assert not any(e.event_type == "flurry_blocked" for e in events)
    attack_events = [e for e in events if e.event_type == "attack_roll"]
    assert len(attack_events) == 3, f"Expected 3 attacks (BAB 8 + extra), got {len(attack_events)}"
    bonuses = [ev.payload["attack_bonus"] for ev in attack_events]
    assert bonuses == [7, 7, 2], f"Expected [7, 7, 2] (BAB 8 - 1 = 7, iterative 8-5-1=2), got {bonuses}"
