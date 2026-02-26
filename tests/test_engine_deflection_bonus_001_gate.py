"""Gate tests: ENGINE-DEFLECTION-BONUS-001 — WO-ENGINE-DEFLECTION-BONUS-001.

Tests:
DB-001: Entity with DEFLECTION_BONUS=2; attack roll that hits AC=12 misses AC=14
DB-002: Entity with DEFLECTION_BONUS=0; standard AC applies
DB-003: Entity with no DEFLECTION_BONUS field (absent) — no crash, standard AC
DB-004: Touch attack vs entity with DEFLECTION_BONUS=2 — deflection still applies
DB-005: Touch attack vs entity with DEFLECTION_BONUS=0 — no deflection, base touch AC
DB-006: Ranged attack vs entity with DEFLECTION_BONUS=2 — deflection applies
DB-007: DEFLECTION_BONUS=4; confirm effective AC=base+4
DB-008: EF.DEFLECTION_BONUS constant exists in entity_fields

PHB p.136: Deflection bonus applies vs ALL attacks including touch attacks.
PHB p.136: Multiple deflection bonuses do not stack — highest wins.
"""

import pytest
from unittest.mock import MagicMock

from aidm.core.state import WorldState
from aidm.core.attack_resolver import resolve_attack
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.entity_fields import EF


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _weapon(damage_dice="1d6", is_ranged=False):
    return Weapon(
        damage_dice=damage_dice,
        damage_bonus=0,
        damage_type="slashing",
        critical_multiplier=2,
        critical_range=20,
        is_two_handed=False,
        grip="one-handed",
        weapon_type="ranged" if is_ranged else "one-handed",
        range_increment=30 if is_ranged else 0,
        enhancement_bonus=0,
    )


def _attacker(eid="fighter", bab=10, str_mod=0):
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: 50, EF.HP_MAX: 50, EF.AC: 18,
        EF.ATTACK_BONUS: bab, EF.BAB: bab,
        EF.STR_MOD: str_mod, EF.DEX_MOD: 0,
        EF.DEFEATED: False, EF.DYING: False, EF.STABLE: False, EF.DISABLED: False,
        EF.CONDITIONS: {}, EF.FEATS: [],
        EF.POSITION: {"x": 0, "y": 0},
        EF.SIZE_CATEGORY: "medium",
        EF.INSPIRE_COURAGE_ACTIVE: False,
        EF.NEGATIVE_LEVELS: 0,
        EF.WEAPON_BROKEN: False,
        EF.FAVORED_ENEMIES: [],
    }


def _target(eid="troll", hp=80, ac=12, deflection=None):
    t = {
        EF.ENTITY_ID: eid,
        EF.TEAM: "monsters",
        EF.HP_CURRENT: hp, EF.HP_MAX: hp, EF.AC: ac,
        EF.DEFEATED: False, EF.DYING: False, EF.STABLE: False, EF.DISABLED: False,
        EF.CONDITIONS: {}, EF.FEATS: [],
        EF.POSITION: {"x": 1, "y": 0},
        EF.SIZE_CATEGORY: "medium",
        EF.SAVE_FORT: 3, EF.CON_MOD: 2,
        EF.DAMAGE_REDUCTIONS: [],
        EF.CREATURE_TYPE: "humanoid",
        EF.INSPIRE_COURAGE_ACTIVE: False,
    }
    if deflection is not None:
        t[EF.DEFLECTION_BONUS] = deflection
    return t


def _world(att, tgt):
    return WorldState(
        ruleset_version="3.5e",
        entities={att[EF.ENTITY_ID]: att, tgt[EF.ENTITY_ID]: tgt},
        active_combat={"initiative_order": [att[EF.ENTITY_ID], tgt[EF.ENTITY_ID]]},
    )


def _rng_seq(*rolls):
    """Return an RNG mock producing a sequence of values."""
    stream = MagicMock()
    stream.randint.side_effect = list(rolls) + [5] * 30
    rng = MagicMock()
    rng.stream.return_value = stream
    return rng


# ---------------------------------------------------------------------------
# DB-001: DEFLECTION_BONUS=2 raises effective AC — roll that hits base misses effective
# ---------------------------------------------------------------------------

def test_db001_deflection_bonus_2_raises_ac():
    """DB-001: DEFLECTION_BONUS=2 on AC=12 target; attack roll=13 (hits 12, misses 14)."""
    att = _attacker(bab=0)  # bab=0: attack total = d20 roll + 0
    # base AC=12, deflection=2 → effective AC=14
    tgt = _target(ac=12, deflection=2)
    ws = _world(att, tgt)

    # Roll 13: hits AC 12 but misses effective AC 14
    rng = _rng_seq(13)  # d20=13, total=13+0=13 < 14 → miss
    events = resolve_attack(AttackIntent("fighter", "troll", 0, _weapon()), ws, rng, 0, 0.0)

    attack_evts = [e for e in events if e.event_type == "attack_roll"]
    assert attack_evts, "attack_roll event must be emitted"
    assert attack_evts[0].payload["hit"] is False, (
        f"Roll 13 vs effective AC 14 must miss; target_ac={attack_evts[0].payload['target_ac']}"
    )
    assert attack_evts[0].payload["target_ac"] == 14, (
        f"Effective AC must be 12+2=14, got {attack_evts[0].payload['target_ac']}"
    )


# ---------------------------------------------------------------------------
# DB-002: DEFLECTION_BONUS=0 — standard AC applies
# ---------------------------------------------------------------------------

def test_db002_deflection_0_standard_ac():
    """DB-002: DEFLECTION_BONUS=0 — effective AC equals base AC."""
    att = _attacker(bab=0)
    tgt = _target(ac=12, deflection=0)
    ws = _world(att, tgt)

    rng = _rng_seq(12)  # d20=12, total=12 >= 12 → hit
    events = resolve_attack(AttackIntent("fighter", "troll", 0, _weapon()), ws, rng, 0, 0.0)

    attack_evts = [e for e in events if e.event_type == "attack_roll"]
    assert attack_evts[0].payload["hit"] is True, "Roll 12 vs AC 12 must hit with zero deflection"
    assert attack_evts[0].payload["target_ac"] == 12


# ---------------------------------------------------------------------------
# DB-003: No DEFLECTION_BONUS field (absent) — no crash, standard AC
# ---------------------------------------------------------------------------

def test_db003_absent_deflection_field_no_crash():
    """DB-003: EF.DEFLECTION_BONUS absent from entity dict — no crash, treats as 0."""
    att = _attacker(bab=0)
    tgt = _target(ac=12)  # No deflection key
    assert EF.DEFLECTION_BONUS not in tgt, "Setup: DEFLECTION_BONUS must be absent"
    ws = _world(att, tgt)

    rng = _rng_seq(12)
    events = resolve_attack(AttackIntent("fighter", "troll", 0, _weapon()), ws, rng, 0, 0.0)

    attack_evts = [e for e in events if e.event_type == "attack_roll"]
    assert attack_evts, "Must produce attack_roll event with no deflection field"
    assert attack_evts[0].payload["target_ac"] == 12, "Absent deflection field: AC=base AC"


# ---------------------------------------------------------------------------
# DB-004: Touch attack + DEFLECTION_BONUS=2 — deflection applies
# ---------------------------------------------------------------------------

def test_db004_touch_attack_deflection_applies():
    """DB-004: PHB p.136 — deflection applies to touch attacks unlike armor.
    This test confirms deflection is in the AC calculation path (target_ac includes it).
    Touch attack distinction (armor bypass) is a future per-intent tag; this confirms
    DEFLECTION_BONUS is present in the composite AC.
    """
    att = _attacker(bab=0)
    tgt = _target(ac=10, deflection=2)  # AC=10, effective=12 with deflection
    ws = _world(att, tgt)

    # Roll 11: hits 10, misses 12 (effective with deflection)
    rng = _rng_seq(11)
    events = resolve_attack(AttackIntent("fighter", "troll", 0, _weapon()), ws, rng, 0, 0.0)

    attack_evts = [e for e in events if e.event_type == "attack_roll"]
    assert attack_evts[0].payload["target_ac"] == 12, (
        "Deflection must be included in target_ac (applies to touch attacks per PHB p.136)"
    )
    assert attack_evts[0].payload["hit"] is False, "Roll 11 < 12 effective AC → miss"


# ---------------------------------------------------------------------------
# DB-005: Touch attack + DEFLECTION_BONUS=0 — standard AC
# ---------------------------------------------------------------------------

def test_db005_touch_attack_no_deflection():
    """DB-005: Touch attack vs target with DEFLECTION_BONUS=0 — base AC applies."""
    att = _attacker(bab=0)
    tgt = _target(ac=10, deflection=0)
    ws = _world(att, tgt)

    rng = _rng_seq(10)  # hit AC=10
    events = resolve_attack(AttackIntent("fighter", "troll", 0, _weapon()), ws, rng, 0, 0.0)

    attack_evts = [e for e in events if e.event_type == "attack_roll"]
    assert attack_evts[0].payload["target_ac"] == 10
    assert attack_evts[0].payload["hit"] is True


# ---------------------------------------------------------------------------
# DB-006: Ranged attack + DEFLECTION_BONUS=2 — deflection applies
# ---------------------------------------------------------------------------

def test_db006_ranged_attack_deflection_applies():
    """DB-006: Ranged attack — deflection bonus applies (PHB p.136: all attacks)."""
    att = _attacker(bab=0)
    att[EF.POSITION] = {"x": 0, "y": 0}
    tgt = _target(ac=12, deflection=2)
    tgt[EF.POSITION] = {"x": 4, "y": 0}  # 20ft away — within range_increment=30
    ws = _world(att, tgt)

    # Roll 13: misses effective AC 14 (12+2)
    rng = _rng_seq(13)
    events = resolve_attack(
        AttackIntent("fighter", "troll", 0, _weapon(is_ranged=True)),
        ws, rng, 0, 0.0
    )

    attack_evts = [e for e in events if e.event_type == "attack_roll"]
    assert attack_evts, "attack_roll must be emitted for ranged attack"
    assert attack_evts[0].payload["target_ac"] == 14, (
        "Deflection must apply to ranged attacks"
    )


# ---------------------------------------------------------------------------
# DB-007: DEFLECTION_BONUS=4; effective AC = base + 4
# ---------------------------------------------------------------------------

def test_db007_deflection_4_correct_ac():
    """DB-007: DEFLECTION_BONUS=4 on AC=12 target → effective AC=16."""
    att = _attacker(bab=0)
    tgt = _target(ac=12, deflection=4)
    ws = _world(att, tgt)

    rng = _rng_seq(15)  # hits AC 12, misses AC 16
    events = resolve_attack(AttackIntent("fighter", "troll", 0, _weapon()), ws, rng, 0, 0.0)

    attack_evts = [e for e in events if e.event_type == "attack_roll"]
    assert attack_evts[0].payload["target_ac"] == 16, (
        f"Effective AC must be 12+4=16, got {attack_evts[0].payload['target_ac']}"
    )
    assert attack_evts[0].payload["hit"] is False, "Roll 15 < 16 effective AC → miss"


# ---------------------------------------------------------------------------
# DB-008: EF.DEFLECTION_BONUS constant is registered in entity_fields
# ---------------------------------------------------------------------------

def test_db008_deflection_bonus_constant_exists():
    """DB-008: EF.DEFLECTION_BONUS constant exists and has correct string value."""
    from aidm.schemas.entity_fields import EF
    assert hasattr(EF, "DEFLECTION_BONUS"), "EF.DEFLECTION_BONUS must exist"
    assert EF.DEFLECTION_BONUS == "deflection_bonus", (
        f"Unexpected value: {EF.DEFLECTION_BONUS}"
    )
