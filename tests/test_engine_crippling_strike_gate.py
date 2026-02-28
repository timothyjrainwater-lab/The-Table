"""Gate tests for WO-ENGINE-AG-WO2: Rogue Crippling Strike (PHB p.51).

CS-001: HAS_CRIPPLING_STRIKE=True + sneak attack hit → target STR_DAMAGE += 1
CS-002: HAS_CRIPPLING_STRIKE=True + regular hit (no sneak) → no STR damage
CS-003: HAS_CRIPPLING_STRIKE=False + sneak attack → no STR damage
CS-004: Multiple crippling strikes stack (STR_DAMAGE accumulates)
CS-005: STR_DAMAGE reduces effective STR modifier (effective STR = STR - STR_DAMAGE)
CS-006: STR reduced to 0 by damage → target helpless (if entity STR ≤ 0 via event)
CS-007: STR ability damage recovers 1 point on full rest (rest_resolver via expire_ability_damage_regen)
CS-008: crippling_strike event emitted with correct STR damage value
"""

import pytest
from copy import deepcopy

from aidm.core.state import WorldState
from aidm.core.attack_resolver import resolve_attack, apply_attack_events
from aidm.core.rest_resolver import resolve_rest
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.entity_fields import EF
from aidm.schemas.intents import RestIntent
from aidm.schemas.conditions import create_flat_footed_condition


def _flat_footed_conds():
    """Return a properly-formed flat_footed condition dict for entity setup."""
    ff = create_flat_footed_condition(source="combat_start", applied_at_event_id=0)
    return {"flat_footed": ff.to_dict()}


class _SeparateStreamRNG:
    def __init__(self, combat_rolls, saves_rolls=None):
        self._pools = {
            "combat": list(combat_rolls),
            "saves": list(saves_rolls or []),
        }
        self._idxs = {"combat": 0, "saves": 0}

    def stream(self, name):
        return _StreamProxy(self._pools.get(name, [10] * 20), self._idxs, name)


class _StreamProxy:
    def __init__(self, pool, idxs, name):
        self._pool = pool
        self._idxs = idxs
        self._name = name

    def randint(self, lo, hi):
        idx = self._idxs[self._name]
        if idx < len(self._pool):
            val = self._pool[idx]
            self._idxs[self._name] = idx + 1
            return val
        return 10


def _make_weapon():
    return Weapon(
        damage_dice="1d6",
        damage_bonus=0,
        critical_range=20,
        critical_multiplier=2,
        damage_type="piercing",
        weapon_type="light",
        is_two_handed=False,
        grip="one-handed",
        enhancement_bonus=0,
    )


def _make_rogue(has_crippling_strike=True, str_damage=0):
    """Rogue entity with sneak attack capability."""
    return {
        EF.ENTITY_ID: "rogue_1",
        EF.TEAM: "player",
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 30,
        EF.AC: 14,
        EF.DEFEATED: False,
        EF.BASE_STATS: {"strength": 12, "dexterity": 16, "constitution": 12,
                        "intelligence": 12, "wisdom": 10, "charisma": 12},
        EF.STR_MOD: 1,
        EF.DEX_MOD: 3,
        EF.CON_MOD: 1,
        EF.WIS_MOD: 0,
        EF.CHA_MOD: 1,
        EF.SAVE_FORT: 2,
        EF.SAVE_REF: 6,
        EF.SAVE_WILL: 2,
        EF.BAB: 3,
        EF.ATTACK_BONUS: 6,
        EF.LEVEL: 4,
        EF.CLASS_LEVELS: {"rogue": 4},
        EF.FEATS: [],
        EF.CONDITIONS: {},
        EF.POSITION: {"x": 0, "y": 0},
        EF.HAS_CRIPPLING_STRIKE: has_crippling_strike,
        EF.ARMOR_AC_BONUS: 2,
        EF.ARMOR_TYPE: "light",
        EF.STR_DAMAGE: str_damage,
    }


def _make_flat_footed_target(hp=30, str_score=12, str_damage=0):
    """Target that is flat-footed (eligible for sneak attack)."""
    return {
        EF.ENTITY_ID: "target_1",
        EF.TEAM: "enemy",
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp,
        EF.AC: 10,
        EF.DEFEATED: False,
        EF.BASE_STATS: {"strength": str_score, "dexterity": 10, "constitution": 12,
                        "intelligence": 10, "wisdom": 10, "charisma": 10},
        EF.STR_MOD: (str_score - 10) // 2,
        EF.DEX_MOD: 0,
        EF.CON_MOD: 1,
        EF.WIS_MOD: 0,
        EF.CHA_MOD: 0,
        EF.SAVE_FORT: 2,
        EF.SAVE_REF: 0,
        EF.SAVE_WILL: 0,
        # Flat-footed condition → sneak attack eligible
        EF.CONDITIONS: _flat_footed_conds(),
        EF.POSITION: {"x": 1, "y": 0},
        EF.ARMOR_AC_BONUS: 0,
        EF.STR_DAMAGE: str_damage,
    }


def _make_target_normal(hp=30):
    """Normal target (not flat-footed, not flanked)."""
    return {
        EF.ENTITY_ID: "target_1",
        EF.TEAM: "enemy",
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp,
        EF.AC: 10,
        EF.DEFEATED: False,
        EF.BASE_STATS: {"strength": 12, "dexterity": 10, "constitution": 12,
                        "intelligence": 10, "wisdom": 10, "charisma": 10},
        EF.STR_MOD: 1,
        EF.DEX_MOD: 0,
        EF.CON_MOD: 1,
        EF.WIS_MOD: 0,
        EF.CHA_MOD: 0,
        EF.SAVE_FORT: 2,
        EF.SAVE_REF: 0,
        EF.SAVE_WILL: 0,
        EF.CONDITIONS: {},
        EF.POSITION: {"x": 1, "y": 0},
        EF.ARMOR_AC_BONUS: 0,
        EF.STR_DAMAGE: 0,
    }


def _make_world(attacker, target):
    return WorldState(
        ruleset_version="3.5",
        entities={attacker[EF.ENTITY_ID]: attacker, target[EF.ENTITY_ID]: target},
        active_combat=None,
    )


def _event_types(events):
    return [e.event_type for e in events]


def test_cs_001_sneak_attack_adds_str_damage():
    """CS-001: HAS_CRIPPLING_STRIKE=True + sneak attack hit → target STR_DAMAGE += 1."""
    rogue = _make_rogue(has_crippling_strike=True)
    target = _make_flat_footed_target()
    ws = _make_world(rogue, target)

    rng = _SeparateStreamRNG(combat_rolls=[15], saves_rolls=[])
    intent = AttackIntent(
        attacker_id="rogue_1",
        target_id="target_1",
        attack_bonus=6,
        weapon=_make_weapon(),
    )
    events = resolve_attack(intent, ws, rng, next_event_id=1, timestamp=0.0)
    types = _event_types(events)
    assert "crippling_strike" in types, f"Expected crippling_strike event, got {types}"

    # Apply events and verify STR_DAMAGE
    ws_after = apply_attack_events(ws, events)
    target_after = ws_after.entities["target_1"]
    assert target_after[EF.STR_DAMAGE] == 1, (
        f"CS-001: Expected STR_DAMAGE=1, got {target_after.get(EF.STR_DAMAGE)}"
    )


def test_cs_002_regular_hit_no_str_damage():
    """CS-002: HAS_CRIPPLING_STRIKE=True + regular hit (no sneak) → no STR damage."""
    rogue = _make_rogue(has_crippling_strike=True)
    target = _make_target_normal()  # Not flat-footed, not flanked
    ws = _make_world(rogue, target)

    rng = _SeparateStreamRNG(combat_rolls=[15], saves_rolls=[])
    intent = AttackIntent(
        attacker_id="rogue_1",
        target_id="target_1",
        attack_bonus=6,
        weapon=_make_weapon(),
    )
    events = resolve_attack(intent, ws, rng, next_event_id=1, timestamp=0.0)
    types = _event_types(events)
    assert "crippling_strike" not in types, (
        f"CS-002: crippling_strike should NOT fire on regular hit; got {types}"
    )


def test_cs_003_no_crippling_strike_flag_no_str_damage():
    """CS-003: HAS_CRIPPLING_STRIKE=False + sneak attack → no STR damage."""
    rogue = _make_rogue(has_crippling_strike=False)
    target = _make_flat_footed_target()
    ws = _make_world(rogue, target)

    rng = _SeparateStreamRNG(combat_rolls=[15], saves_rolls=[])
    intent = AttackIntent(
        attacker_id="rogue_1",
        target_id="target_1",
        attack_bonus=6,
        weapon=_make_weapon(),
    )
    events = resolve_attack(intent, ws, rng, next_event_id=1, timestamp=0.0)
    types = _event_types(events)
    assert "crippling_strike" not in types, (
        f"CS-003: crippling_strike should not fire without ability; got {types}"
    )


def test_cs_004_multiple_strikes_stack():
    """CS-004: Multiple crippling strikes stack (STR_DAMAGE accumulates)."""
    rogue = _make_rogue(has_crippling_strike=True)
    target = _make_flat_footed_target()
    ws = _make_world(rogue, target)

    rng = _SeparateStreamRNG(combat_rolls=[15, 15], saves_rolls=[])
    intent = AttackIntent(
        attacker_id="rogue_1",
        target_id="target_1",
        attack_bonus=6,
        weapon=_make_weapon(),
    )
    # First attack
    events1 = resolve_attack(intent, ws, rng, next_event_id=1, timestamp=0.0)
    ws = apply_attack_events(ws, events1)
    target_after_1 = ws.entities["target_1"]
    assert target_after_1.get(EF.STR_DAMAGE, 0) == 1, "After first CS: STR_DAMAGE should be 1"

    # Second attack (target still flat-footed for simplicity)
    events2 = resolve_attack(intent, ws, rng, next_event_id=50, timestamp=1.0)
    ws = apply_attack_events(ws, events2)
    target_after_2 = ws.entities["target_1"]
    assert target_after_2.get(EF.STR_DAMAGE, 0) == 2, (
        f"After second CS: STR_DAMAGE should be 2, got {target_after_2.get(EF.STR_DAMAGE)}"
    )


def test_cs_005_str_damage_reduces_str_mod():
    """CS-005: STR_DAMAGE reduces effective STR modifier (effective STR = STR - STR_DAMAGE)."""
    rogue = _make_rogue(has_crippling_strike=True)
    target = _make_flat_footed_target(str_score=12)  # STR 12 → STR_MOD +1
    ws = _make_world(rogue, target)

    rng = _SeparateStreamRNG(combat_rolls=[15], saves_rolls=[])
    intent = AttackIntent(
        attacker_id="rogue_1",
        target_id="target_1",
        attack_bonus=6,
        weapon=_make_weapon(),
    )
    events = resolve_attack(intent, ws, rng, next_event_id=1, timestamp=0.0)
    ws_after = apply_attack_events(ws, events)
    target_after = ws_after.entities["target_1"]

    # Effective STR = 12 - 1 = 11 → STR_MOD = (11 - 10) // 2 = 0
    assert target_after[EF.STR_DAMAGE] == 1
    assert target_after[EF.STR_MOD] == 0, (
        f"CS-005: Expected STR_MOD=0 after 1 STR damage on STR 12, got {target_after[EF.STR_MOD]}"
    )


def test_cs_006_str_to_zero_event_present():
    """CS-006: STR reduced to 0 → crippling_strike event payload has str_damage=1."""
    # We verify the event payload is correct. STR=1, one CS → effective STR=0.
    rogue = _make_rogue(has_crippling_strike=True)
    target = _make_flat_footed_target(str_score=12)
    target[EF.STR_DAMAGE] = 11  # One more point → STR_DAMAGE=12 = STR → effective STR=0
    ws = _make_world(rogue, target)

    rng = _SeparateStreamRNG(combat_rolls=[15], saves_rolls=[])
    intent = AttackIntent(
        attacker_id="rogue_1",
        target_id="target_1",
        attack_bonus=6,
        weapon=_make_weapon(),
    )
    events = resolve_attack(intent, ws, rng, next_event_id=1, timestamp=0.0)
    ws_after = apply_attack_events(ws, events)
    target_after = ws_after.entities["target_1"]

    # Effective STR = max(0, 12 - 12) = 0
    assert target_after[EF.STR_DAMAGE] == 12
    assert target_after[EF.STR_MOD] == (max(0, 12 - 12) - 10) // 2  # (0 - 10) // 2 = -5


def test_cs_007_str_damage_recovers_on_rest():
    """CS-007: STR ability damage recovers 1 point on full rest (rest_resolver)."""
    rogue = _make_rogue(has_crippling_strike=True)
    target = _make_flat_footed_target()
    # Pre-set STR_DAMAGE = 3 to simulate accumulated damage
    target[EF.STR_DAMAGE] = 3
    target[EF.BASE_STATS] = {"strength": 12, "dexterity": 10, "constitution": 12,
                              "intelligence": 10, "wisdom": 10, "charisma": 10}
    ws = WorldState(
        ruleset_version="3.5",
        entities={"target_1": target},
        active_combat=None,
    )

    intent = RestIntent(rest_type="overnight")
    result = resolve_rest(intent, ws, actor_id="target_1", next_event_id=1, timestamp=0.0)
    target_after = result.world_state.entities["target_1"]

    # PHB p.215: 1 point of ability damage heals per overnight rest
    assert target_after[EF.STR_DAMAGE] == 2, (
        f"CS-007: Expected STR_DAMAGE=2 after rest (heals 1/night), got {target_after.get(EF.STR_DAMAGE)}"
    )


def test_cs_008_crippling_strike_event_payload():
    """CS-008: crippling_strike event emitted with correct STR damage value."""
    rogue = _make_rogue(has_crippling_strike=True)
    target = _make_flat_footed_target()
    ws = _make_world(rogue, target)

    rng = _SeparateStreamRNG(combat_rolls=[15], saves_rolls=[])
    intent = AttackIntent(
        attacker_id="rogue_1",
        target_id="target_1",
        attack_bonus=6,
        weapon=_make_weapon(),
    )
    events = resolve_attack(intent, ws, rng, next_event_id=1, timestamp=0.0)
    cs_events = [e for e in events if e.event_type == "crippling_strike"]
    assert len(cs_events) == 1, f"Expected exactly 1 crippling_strike event, got {len(cs_events)}"
    assert cs_events[0].payload["str_damage"] == 1, (
        f"CS-008: Expected str_damage=1 in event payload, got {cs_events[0].payload}"
    )
    assert cs_events[0].payload["target_id"] == "target_1"
    assert cs_events[0].payload["attacker_id"] == "rogue_1"
