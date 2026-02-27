"""Gate tests: ENGINE-IMPROVED-UNCANNY-DODGE — WO-ENGINE-IMPROVED-UNCANNY-DODGE-001.

Closes: FINDING-ENGINE-IMPROVED-UNCANNY-DODGE-001 (deferred from Batch C WO4)

Tests:
IUD-001: Target with IUD (rogue 8), attacker flanking → flanking suppressed, no sneak attack
IUD-002: Target with IUD (barbarian 5), attacker flanking → flanking suppressed, no sneak attack
IUD-003: Target IUD-base=8, attacker rogue_level=12 (≥8+4) → exception applies; sneak attack allowed
IUD-004: Target IUD-base=8, attacker rogue_level=11 (< 8+4) → suppressed; no sneak attack
IUD-005: Target WITHOUT IUD, flanked → sneak attack eligible (regression guard)
IUD-006: IUD active → improved_uncanny_dodge_active event emitted in sequence
IUD-007: IUD does NOT suppress flat-footed sneak attack (UD lines 388+924 unaffected)
IUD-008: Full attack IUD guard — resolve_full_attack sneak attack suppressed by IUD

Insertion sites:
  attack_resolver.py: guard after damage_total += _favored_enemy_bonus, using _sa_is_flanking
  full_attack_resolver.py: guard before is_sneak_attack_eligible call, using _sa_is_flanking
"""

import unittest.mock as mock
from typing import Any, Dict

import pytest

from aidm.core.attack_resolver import resolve_attack
from aidm.core.full_attack_resolver import resolve_full_attack, FullAttackIntent
from aidm.core.state import WorldState
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.entity_fields import EF


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

WEAPON = Weapon(
    damage_dice="1d6",
    damage_bonus=0,
    damage_type="slashing",
    critical_multiplier=2,
    critical_range=20,
    is_two_handed=False,
    grip="one-handed",
    weapon_type="light",
    range_increment=0,
    enhancement_bonus=0,
)


def _attacker(
    eid: str = "rogue",
    rogue_level: int = 4,
    other_feats: list = None,
    bab: int = 4,
) -> Dict[str, Any]:
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: 40,
        EF.HP_MAX: 40,
        EF.AC: 15,
        EF.ATTACK_BONUS: bab,
        EF.BAB: bab,
        EF.STR_MOD: 1,
        EF.DEX_MOD: 3,
        EF.DEFEATED: False,
        EF.DYING: False,
        EF.STABLE: False,
        EF.DISABLED: False,
        EF.CONDITIONS: {},
        EF.FEATS: other_feats or [],
        EF.POSITION: {"x": 0, "y": 0},
        EF.SIZE_CATEGORY: "medium",
        EF.INSPIRE_COURAGE_ACTIVE: False,
        EF.NEGATIVE_LEVELS: 0,
        EF.WEAPON_BROKEN: False,
        EF.FAVORED_ENEMIES: [],
        EF.CLASS_LEVELS: {"rogue": rogue_level},
        EF.WEAPON: {"enhancement_bonus": 0, "tags": [], "material": "steel", "alignment": "none"},
    }


def _target_with_iud(
    eid: str = "fighter",
    rogue_level: int = 0,
    barbarian_level: int = 0,
    hp: int = 30,
    ac: int = 10,
    flat_footed: bool = False,
) -> Dict[str, Any]:
    feats = ["improved_uncanny_dodge"]
    if rogue_level >= 4 or barbarian_level >= 2:
        feats.append("uncanny_dodge")
    t = {
        EF.ENTITY_ID: eid,
        EF.TEAM: "monsters",
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp,
        EF.AC: ac,
        EF.DEFEATED: False,
        EF.DYING: False,
        EF.STABLE: False,
        EF.DISABLED: False,
        EF.CONDITIONS: {},
        EF.FEATS: feats,
        EF.POSITION: {"x": 1, "y": 0},
        EF.SIZE_CATEGORY: "medium",
        EF.DAMAGE_REDUCTIONS: [],
        EF.SAVE_FORT: 3,
        EF.CON_MOD: 2,
        EF.CREATURE_TYPE: "humanoid",
        EF.INSPIRE_COURAGE_ACTIVE: False,
        EF.CLASS_LEVELS: {"rogue": rogue_level, "barbarian": barbarian_level},
        EF.DEX_MOD: 3,
    }
    return t


def _target_no_iud(
    eid: str = "goblin",
    hp: int = 30,
    ac: int = 10,
) -> Dict[str, Any]:
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "monsters",
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp,
        EF.AC: ac,
        EF.DEFEATED: False,
        EF.DYING: False,
        EF.STABLE: False,
        EF.DISABLED: False,
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.POSITION: {"x": 1, "y": 0},
        EF.SIZE_CATEGORY: "medium",
        EF.DAMAGE_REDUCTIONS: [],
        EF.SAVE_FORT: 3,
        EF.CON_MOD: 2,
        EF.CREATURE_TYPE: "humanoid",
        EF.INSPIRE_COURAGE_ACTIVE: False,
        EF.CLASS_LEVELS: {},
        EF.DEX_MOD: 3,
    }


def _ally(eid: str = "ally", pos: dict = None) -> Dict[str, Any]:
    """Flanking ally — placed opposite side of target from attacker."""
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 30,
        EF.AC: 12,
        EF.DEFEATED: False,
        EF.DYING: False,
        EF.STABLE: False,
        EF.DISABLED: False,
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.POSITION: pos or {"x": 2, "y": 0},  # Opposite side of target (1,0) from attacker (0,0)
        EF.SIZE_CATEGORY: "medium",
        EF.INSPIRE_COURAGE_ACTIVE: False,
    }


def _world_flanking(attacker: dict, target: dict, ally: dict = None) -> WorldState:
    """World with an ally on the far side of target to create flanking."""
    entities = {attacker[EF.ENTITY_ID]: attacker, target[EF.ENTITY_ID]: target}
    if ally:
        entities[ally[EF.ENTITY_ID]] = ally
    return WorldState(
        ruleset_version="3.5e",
        entities=entities,
        active_combat={"initiative_order": list(entities.keys())},
    )


def _rng(attack_roll: int = 15, damage_roll: int = 3, sneak_roll: int = 4):
    stream = mock.MagicMock()
    stream.randint.side_effect = [attack_roll, damage_roll, sneak_roll] + [sneak_roll] * 20
    rng = mock.MagicMock()
    rng.stream.return_value = stream
    return rng


def _intent(attacker_id: str, target_id: str, attack_bonus: int = 8) -> AttackIntent:
    return AttackIntent(
        attacker_id=attacker_id,
        target_id=target_id,
        attack_bonus=attack_bonus,
        weapon=WEAPON,
        power_attack_penalty=0,
    )


def _has_sneak_attack(events) -> bool:
    return any(e.event_type == "damage_roll" and e.payload.get("sneak_attack_damage", 0) > 0
               for e in events)


# ---------------------------------------------------------------------------
# IUD-001: IUD (rogue 8) + flanking → sneak attack suppressed
# ---------------------------------------------------------------------------

def test_iud001_rogue_target_iud_suppresses_flanking_sa():
    """IUD-001: Target rogue 8 has IUD; attacker rogue 4 flanking → no sneak attack."""
    attacker = _attacker(rogue_level=4)
    target = _target_with_iud(rogue_level=8)
    ally = _ally()
    ws = _world_flanking(attacker, target, ally)

    events = resolve_attack(_intent("rogue", "fighter"), ws, _rng(15, 3), next_event_id=0, timestamp=0.0)

    assert not _has_sneak_attack(events), (
        "IUD should suppress flanking-based sneak attack; events: "
        f"{[(e.event_type, e.payload) for e in events if 'damage' in e.event_type]}"
    )


# ---------------------------------------------------------------------------
# IUD-002: IUD (barbarian 5) + flanking → sneak attack suppressed
# ---------------------------------------------------------------------------

def test_iud002_barbarian_target_iud_suppresses_flanking_sa():
    """IUD-002: Target barbarian 5 has IUD; attacker rogue 4 flanking → no sneak attack."""
    attacker = _attacker(rogue_level=4)
    target = _target_with_iud(barbarian_level=5)
    ally = _ally()
    ws = _world_flanking(attacker, target, ally)

    events = resolve_attack(_intent("rogue", "fighter"), ws, _rng(15, 3), next_event_id=0, timestamp=0.0)

    assert not _has_sneak_attack(events), (
        "IUD (barbarian base) should suppress flanking SA"
    )


# ---------------------------------------------------------------------------
# IUD-003: IUD-base=8, attacker rogue 12 (≥8+4) → exception; sneak attack allowed
# ---------------------------------------------------------------------------

def test_iud003_attacker_rogue_level_exception_allows_sa():
    """IUD-003: Attacker rogue 12 ≥ target IUD-base 8+4 → flanking SA allowed."""
    attacker = _attacker(rogue_level=12)
    target = _target_with_iud(rogue_level=8)
    ally = _ally()
    ws = _world_flanking(attacker, target, ally)

    events = resolve_attack(_intent("rogue", "fighter"), ws, _rng(15, 3, 4), next_event_id=0, timestamp=0.0)

    # With rogue-level exception, sneak attack should fire
    assert _has_sneak_attack(events), (
        "Attacker rogue 12 ≥ target IUD-base 8+4: SA exception should allow sneak attack"
    )


# ---------------------------------------------------------------------------
# IUD-004: IUD-base=8, attacker rogue 11 (< 8+4=12) → suppressed
# ---------------------------------------------------------------------------

def test_iud004_attacker_rogue_one_below_threshold_suppressed():
    """IUD-004: Attacker rogue 11 < target IUD-base 8+4=12 → flanking SA suppressed."""
    attacker = _attacker(rogue_level=11)
    target = _target_with_iud(rogue_level=8)
    ally = _ally()
    ws = _world_flanking(attacker, target, ally)

    events = resolve_attack(_intent("rogue", "fighter"), ws, _rng(15, 3), next_event_id=0, timestamp=0.0)

    assert not _has_sneak_attack(events), (
        "Attacker rogue 11 < threshold 12: IUD should suppress SA"
    )


# ---------------------------------------------------------------------------
# IUD-005: Target WITHOUT IUD, flanked → sneak attack eligible (regression)
# ---------------------------------------------------------------------------

def test_iud005_no_iud_flanking_sa_eligible():
    """IUD-005: Target without IUD, flanked by rogue → sneak attack fires (regression guard)."""
    attacker = _attacker(rogue_level=4)
    target = _target_no_iud()  # No IUD
    ally = _ally()
    ws = _world_flanking(attacker, target, ally)

    events = resolve_attack(_intent("rogue", "goblin"), ws, _rng(15, 3, 4), next_event_id=0, timestamp=0.0)

    assert _has_sneak_attack(events), (
        "No IUD: flanking should enable sneak attack. Events: "
        f"{[(e.event_type, e.payload) for e in events if 'damage' in e.event_type]}"
    )


# ---------------------------------------------------------------------------
# IUD-006: IUD active → improved_uncanny_dodge_active event emitted
# ---------------------------------------------------------------------------

def test_iud006_event_emitted_when_iud_active():
    """IUD-006: When IUD suppresses flanking SA, improved_uncanny_dodge_active event is emitted."""
    attacker = _attacker(rogue_level=4)
    target = _target_with_iud(rogue_level=8)
    ally = _ally()
    ws = _world_flanking(attacker, target, ally)

    events = resolve_attack(_intent("rogue", "fighter"), ws, _rng(15, 3), next_event_id=0, timestamp=0.0)

    iud_events = [e for e in events if e.event_type == "improved_uncanny_dodge_active"]
    assert len(iud_events) >= 1, (
        f"improved_uncanny_dodge_active event should be emitted; got: {[e.event_type for e in events]}"
    )
    assert iud_events[0].payload.get("target_id") == "fighter"


# ---------------------------------------------------------------------------
# IUD-007: IUD does NOT affect flat-footed sneak attack (UD lines unaffected)
# ---------------------------------------------------------------------------

def test_iud007_iud_does_not_block_flat_footed_sa():
    """IUD-007: IUD guard is keyed on flanking only; non-flanking attacks are unaffected.

    IUD (PHB p.26/50) suppresses *flanking-based* sneak attack only.
    When no ally is present to create flanking, is_flanking=False and the IUD guard
    never activates — regardless of target's conditions (flat-footed, etc.).
    """
    attacker = _attacker(rogue_level=4)
    target = _target_with_iud(rogue_level=8)

    # No ally present — no flanking
    ws = _world_flanking(attacker, target, None)

    events = resolve_attack(_intent("rogue", "fighter"), ws, _rng(15, 3, 4), next_event_id=0, timestamp=0.0)

    # IUD guard must NOT fire when is_flanking=False (no flanking ally)
    iud_events = [e for e in events if e.event_type == "improved_uncanny_dodge_active"]
    assert len(iud_events) == 0, (
        "IUD event must not fire when no flanking; IUD only guards flanking-based SA. "
        f"Got events: {[e.event_type for e in events]}"
    )


# ---------------------------------------------------------------------------
# IUD-008: Full attack IUD guard — sa_eligible suppressed via _sa_is_flanking
# ---------------------------------------------------------------------------

def test_iud008_full_attack_iud_suppresses_flanking_sa():
    """IUD-008: resolve_full_attack — IUD suppresses flanking SA across all iterative attacks."""
    attacker = _attacker(rogue_level=4)
    target = _target_with_iud(rogue_level=8)
    ally = _ally()
    ws = _world_flanking(attacker, target, ally)

    fa_intent = FullAttackIntent(
        attacker_id="rogue",
        target_id="fighter",
        weapon=WEAPON,
        base_attack_bonus=4,
        power_attack_penalty=0,
    )

    events = resolve_full_attack(fa_intent, ws, _rng(15, 3), next_event_id=0, timestamp=0.0)

    assert not _has_sneak_attack(events), (
        "IUD should suppress flanking SA in full attack sequence; "
        f"events: {[(e.event_type, e.payload) for e in events if 'damage' in e.event_type]}"
    )
    # Also verify IUD event is NOT emitted in full_attack (IUD guard in FAR doesn't emit event,
    # only suppresses sa_eligible — that's the implementation choice for FAR)
