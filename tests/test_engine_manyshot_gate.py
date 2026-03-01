"""Gate tests: ENGINE-AH-WO4 — Manyshot (PHB p.97)

Standard action. Fire two arrows at single target within 30 feet.
Single attack roll at -4 penalty. Each arrow deals damage independently on hit.
BAB scaling (3+ arrows at BAB +11/+16) explicitly OUT OF SCOPE.

Authority: RAW — PHB p.97. Attack penalty: -4 (NOT Rapid Shot's -2).
Tests: MS-001 through MS-008
"""

import unittest.mock as mock
import pytest
from aidm.core.attack_resolver import resolve_manyshot
from aidm.core.action_economy import get_action_type
from aidm.core.state import WorldState
from aidm.schemas.intents import ManyShotIntent
from aidm.schemas.entity_fields import EF


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _ranged_weapon_dict():
    return {
        "damage_dice": "1d8",
        "damage_bonus": 0,
        "damage_type": "piercing",
        "critical_multiplier": 3,
        "critical_range": 20,
        "weapon_type": "ranged",
        "range_increment": 60,
        "enhancement_bonus": 0,
    }


def _attacker(eid="archer", bab=6, feats=None) -> dict:
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: 50,
        EF.HP_MAX: 50,
        EF.AC: 14,
        EF.ATTACK_BONUS: bab,
        EF.BAB: bab,
        EF.STR_MOD: 1,
        EF.DEX_MOD: 2,
        EF.DEFEATED: False,
        EF.DYING: False,
        EF.STABLE: False,
        EF.DISABLED: False,
        EF.CONDITIONS: {},
        EF.FEATS: feats if feats is not None else [],
        EF.POSITION: {"x": 0, "y": 0},
        EF.SIZE_CATEGORY: "medium",
        EF.FAVORED_ENEMIES: [],
        EF.DAMAGE_REDUCTIONS: [],
        EF.WEAPON: {"enhancement_bonus": 0, "tags": [], "material": "steel", "alignment": "none"},
        EF.ARMOR_TYPE: "none",
    }


def _target(eid="goblin", hp=100, ac=5) -> dict:
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
        EF.SAVE_FORT: 3,
        EF.CON_MOD: 2,
        EF.CREATURE_TYPE: "humanoid",
        EF.DAMAGE_REDUCTIONS: [],
    }


def _world(attacker, target) -> WorldState:
    return WorldState(
        ruleset_version="3.5e",
        entities={attacker[EF.ENTITY_ID]: attacker, target[EF.ENTITY_ID]: target},
        active_combat={
            "initiative_order": [attacker[EF.ENTITY_ID], target[EF.ENTITY_ID]],
            "cleave_used_this_turn": set(),
            "aoo_used_this_round": [],
        },
    )


def _rng(rolls=None) -> mock.MagicMock:
    stream = mock.MagicMock()
    if rolls is None:
        # Default: d20 hit (15) + two arrow damage (4, 4) + extras
        rolls = [15, 4, 4, 4, 4, 4, 4, 4, 4, 4]
    stream.randint.side_effect = rolls
    rng = mock.MagicMock()
    rng.stream.return_value = stream
    return rng


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestEngineManyShotGate:

    def test_MS001_feat_present_attack_roll_has_minus4_penalty(self):
        """MS-001: Entity with Manyshot feat → attack_roll event has manyshot_penalty: -4.

        PHB p.97: 'both arrows use the same attack roll (with a -4 penalty).'
        Penalty is -4 — NOT Rapid Shot's -2. Proven via attack_roll payload.
        """
        a = _attacker(feats=["manyshot"], bab=6)
        t = _target(ac=1)
        ws = _world(a, t)
        intent = ManyShotIntent(attacker_id="archer", target_id="goblin",
                                weapon=_ranged_weapon_dict(), within_30_feet=True)
        events = resolve_manyshot(intent, ws, _rng(), next_event_id=0, timestamp=0.0)
        roll_events = [e for e in events if e.event_type == "attack_roll"]
        assert len(roll_events) >= 1, "Expected attack_roll event with feat present"
        payload = roll_events[0].payload
        assert payload.get("manyshot_penalty") == -4, \
            f"Expected manyshot_penalty=-4 (PHB p.97), got {payload.get('manyshot_penalty')}"
        invalid = [e for e in events if e.event_type == "manyshot_invalid"]
        assert len(invalid) == 0, "No manyshot_invalid with feat present"

    def test_MS002_no_feat_blocked(self):
        """MS-002: No Manyshot feat → manyshot_invalid event, no attack_roll."""
        a = _attacker(feats=[])
        t = _target()
        ws = _world(a, t)
        intent = ManyShotIntent(attacker_id="archer", target_id="goblin",
                                weapon=_ranged_weapon_dict(), within_30_feet=True)
        events = resolve_manyshot(intent, ws, _rng(), next_event_id=0, timestamp=0.0)
        types = [e.event_type for e in events]
        assert "manyshot_invalid" in types, "Expected manyshot_invalid without feat"
        assert "attack_roll" not in types, "No attack_roll without feat"

    def test_MS003_target_beyond_30_feet_blocked(self):
        """MS-003: within_30_feet=False → manyshot_invalid (PHB p.97: 30-ft range cap).

        PHB p.97: 'you may fire two arrows at a single opponent within 30 feet.'
        The DM/AI asserts within_30_feet. False → blocked.
        """
        a = _attacker(feats=["manyshot"])
        t = _target()
        ws = _world(a, t)
        intent = ManyShotIntent(attacker_id="archer", target_id="goblin",
                                weapon=_ranged_weapon_dict(), within_30_feet=False)
        events = resolve_manyshot(intent, ws, _rng(), next_event_id=0, timestamp=0.0)
        types = [e.event_type for e in events]
        assert "manyshot_invalid" in types
        invalid = next(e for e in events if e.event_type == "manyshot_invalid")
        assert invalid.payload.get("reason") == "target_out_of_30ft_range", \
            f"Expected reason='target_out_of_30ft_range', got {invalid.payload.get('reason')}"

    def test_MS004_hit_produces_two_damage_events(self):
        """MS-004: Hit → exactly two damage_roll events (two arrows).

        PHB p.97: 'deal damage normally (one per arrow).'
        Single attack roll, two independent damage dice on hit.
        Proven by: len(damage_roll events) == 2, arrow_index 0 and 1.
        """
        a = _attacker(feats=["manyshot"], bab=6)
        t = _target(ac=1)  # Very low AC — always hits
        ws = _world(a, t)
        intent = ManyShotIntent(attacker_id="archer", target_id="goblin",
                                weapon=_ranged_weapon_dict(), within_30_feet=True)
        events = resolve_manyshot(intent, ws,
                                  _rng(rolls=[15, 4, 4, 4, 4, 4, 4]),
                                  next_event_id=0, timestamp=0.0)
        damage_events = [e for e in events if e.event_type == "damage_roll"]
        assert len(damage_events) == 2, \
            f"Hit must produce exactly 2 damage_roll events (two arrows), got {len(damage_events)}"
        indices = [e.payload.get("arrow_index") for e in damage_events]
        assert 0 in indices and 1 in indices, \
            f"Arrow indices must be 0 and 1 (both arrows), got {indices}"

    def test_MS005_miss_produces_zero_damage_events(self):
        """MS-005: Miss → zero damage events emitted.

        PHB p.97: Both arrows share the one attack roll — on miss, neither deals damage.
        """
        a = _attacker(feats=["manyshot"], bab=6)
        t = _target(ac=99)  # Unreachable AC — always misses
        ws = _world(a, t)
        intent = ManyShotIntent(attacker_id="archer", target_id="goblin",
                                weapon=_ranged_weapon_dict(), within_30_feet=True)
        events = resolve_manyshot(intent, ws,
                                  _rng(rolls=[1, 4, 4, 4, 4]),
                                  next_event_id=0, timestamp=0.0)
        damage_events = [e for e in events if e.event_type == "damage_roll"]
        hp_events = [e for e in events if e.event_type == "hp_changed"]
        assert len(damage_events) == 0, "Miss: no damage_roll events"
        assert len(hp_events) == 0, "Miss: no hp_changed events"

    def test_MS006_standard_action_not_full_round(self):
        """MS-006: Manyshot is a STANDARD action (NOT full-round). Move action still available.

        PHB p.97: 'As a standard action, you may fire two arrows.'
        Distinct from Rapid Shot (full attack) and Spring Attack (full-round).
        Confirmed: get_action_type(ManyShotIntent) == 'standard'.
        """
        intent = ManyShotIntent(attacker_id="archer", target_id="goblin",
                                weapon=_ranged_weapon_dict(), within_30_feet=True)
        slot = get_action_type(intent)
        assert slot == "standard", \
            f"ManyShotIntent must be 'standard' action (not full_round), got '{slot}'"

    def test_MS007_single_attack_roll_event(self):
        """MS-007: Only ONE attack_roll event — single d20 roll for both arrows.

        PHB p.97: 'both arrows use the same attack roll.'
        Manyshot fires one d20, then branches to two damage rolls on hit.
        Not two separate attack rolls (that would be iterative attacks).
        """
        a = _attacker(feats=["manyshot"], bab=6)
        t = _target(ac=1)
        ws = _world(a, t)
        intent = ManyShotIntent(attacker_id="archer", target_id="goblin",
                                weapon=_ranged_weapon_dict(), within_30_feet=True)
        events = resolve_manyshot(intent, ws,
                                  _rng(rolls=[15, 4, 4, 4, 4, 4]),
                                  next_event_id=0, timestamp=0.0)
        roll_events = [e for e in events if e.event_type == "attack_roll"]
        assert len(roll_events) == 1, \
            f"Manyshot fires exactly one d20 (one attack_roll event), got {len(roll_events)}"

    def test_MS008_penalty_is_minus4_not_rapid_shot_minus2(self):
        """MS-008: Manyshot penalty is -4, NOT Rapid Shot's -2 (PHB p.97 vs p.99).

        PHB p.97 explicit: '-4 penalty' for 2-arrow Manyshot volley.
        PHB p.99: Rapid Shot is '-2 to all attacks' during full attack (different mechanic).
        Both feats may coexist on entity; each fires on its own action type.
        Proven: attack_roll.attack_bonus == bab - 4 (not bab - 2).
        """
        a = _attacker(feats=["manyshot", "rapid_shot"], bab=6)  # Both feats present
        t = _target(ac=1)
        ws = _world(a, t)
        intent = ManyShotIntent(attacker_id="archer", target_id="goblin",
                                weapon=_ranged_weapon_dict(), within_30_feet=True)
        events = resolve_manyshot(intent, ws, _rng(), next_event_id=0, timestamp=0.0)
        roll_events = [e for e in events if e.event_type == "attack_roll"]
        assert len(roll_events) >= 1
        payload = roll_events[0].payload

        # PHB p.97: Manyshot penalty = -4
        assert payload.get("manyshot_penalty") == -4, \
            f"Manyshot penalty must be -4 (PHB p.97), got {payload.get('manyshot_penalty')}"

        # Effective attack_bonus = bab - 4 (not bab - 2 from Rapid Shot)
        base_bab = a[EF.ATTACK_BONUS]
        effective = payload.get("attack_bonus", 0)
        assert effective == base_bab - 4, \
            (f"attack_bonus = bab({base_bab}) + manyshot_penalty(-4) = {base_bab - 4}, "
             f"got {effective}. Must NOT be bab-2 (Rapid Shot penalty).")
