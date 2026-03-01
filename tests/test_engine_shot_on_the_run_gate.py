"""Gate tests: ENGINE-AH-WO3 — Shot on the Run (PHB p.99)

Full-round action. Move up to speed, make one ranged attack at any point
during movement, continue moving. Target does not get AoO. Range increment
penalties still apply. Cannot use in heavy armor.

Authority: RAW — PHB p.99 ('works like Spring Attack, but with a ranged weapon.')
Shared AoO suppression via filter_aoo_from_target (aoo.py) — SAME mechanism as Spring Attack.
Tests: SOTR-001 through SOTR-008
"""

import unittest.mock as mock
import pytest
from aidm.core.attack_resolver import resolve_shot_on_the_run
from aidm.core.aoo import AooTrigger, filter_aoo_from_target
from aidm.core.action_economy import get_action_type
from aidm.core.state import WorldState
from aidm.schemas.intents import ShotOnTheRunIntent
from aidm.schemas.position import Position
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


def _attacker(eid="archer", bab=6, feats=None, armor_type="none", dex_mod=2) -> dict:
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: 50,
        EF.HP_MAX: 50,
        EF.AC: 14,
        EF.ATTACK_BONUS: bab,
        EF.BAB: bab,
        EF.STR_MOD: 1,
        EF.DEX_MOD: dex_mod,
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
        EF.ARMOR_TYPE: armor_type,
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
        rolls = [15, 4, 4, 4, 4, 4, 4, 4, 4, 4]
    stream.randint.side_effect = rolls
    rng = mock.MagicMock()
    rng.stream.return_value = stream
    return rng


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestEngineShotOnTheRunGate:

    def test_SOTR001_feat_present_resolves_ranged_attack(self):
        """SOTR-001: Entity with Shot on the Run feat → intent resolves single ranged attack."""
        a = _attacker(feats=["shot_on_the_run"])
        t = _target(ac=5)
        ws = _world(a, t)
        intent = ShotOnTheRunIntent(attacker_id="archer", target_id="goblin",
                                    weapon=_ranged_weapon_dict(), range_penalty=0)
        events = resolve_shot_on_the_run(intent, ws, _rng(), next_event_id=0, timestamp=0.0)
        roll_events = [e for e in events if e.event_type == "attack_roll"]
        invalid = [e for e in events if e.event_type == "shot_on_the_run_invalid"]
        assert len(roll_events) >= 1, "Expected at least one attack_roll with feat present"
        assert len(invalid) == 0, "No shot_on_the_run_invalid with feat present"

    def test_SOTR002_no_feat_blocked(self):
        """SOTR-002: No feat → intent blocked with shot_on_the_run_invalid event."""
        a = _attacker(feats=[])
        t = _target()
        ws = _world(a, t)
        intent = ShotOnTheRunIntent(attacker_id="archer", target_id="goblin",
                                    weapon=_ranged_weapon_dict())
        events = resolve_shot_on_the_run(intent, ws, _rng(), next_event_id=0, timestamp=0.0)
        types = [e.event_type for e in events]
        assert "shot_on_the_run_invalid" in types
        assert "attack_roll" not in types

    def test_SOTR003_heavy_armor_blocked(self):
        """SOTR-003: Heavy armor → intent blocked (PHB p.99 — same rule as Spring Attack).

        EF.ARMOR_TYPE == 'heavy' → shot_on_the_run_invalid with reason='heavy_armor'.
        """
        a = _attacker(feats=["shot_on_the_run"], armor_type="heavy")
        t = _target()
        ws = _world(a, t)
        intent = ShotOnTheRunIntent(attacker_id="archer", target_id="goblin",
                                    weapon=_ranged_weapon_dict())
        events = resolve_shot_on_the_run(intent, ws, _rng(), next_event_id=0, timestamp=0.0)
        types = [e.event_type for e in events]
        assert "shot_on_the_run_invalid" in types
        invalid = next(e for e in events if e.event_type == "shot_on_the_run_invalid")
        assert invalid.payload.get("reason") == "heavy_armor"

    def test_SOTR004_same_aoo_suppression_as_spring_attack(self):
        """SOTR-004: Target AoO suppressed. filter_aoo_from_target is the SAME mechanism as WO2.

        PHB p.99: 'works like Spring Attack, but with a ranged weapon.' Same AoO rule.
        Both Spring Attack (WO2) and Shot on the Run (WO3) call filter_aoo_from_target
        from aoo.py — one implementation, two call sites.

        For Shot on the Run (ranged): the ranged attack provokes AoO from all threatening
        enemies. filter_aoo_from_target removes ONLY the target's trigger, leaving others.
        """
        pos = Position(x=0, y=0)
        trigger_target = AooTrigger(
            reactor_id="goblin",
            provoker_id="archer",
            provoking_action="ranged_attack",
            reactor_position=pos,
            provoker_from_pos=pos,
        )
        trigger_side = AooTrigger(
            reactor_id="orc_guard",
            provoker_id="archer",
            provoking_action="ranged_attack",
            reactor_position=pos,
            provoker_from_pos=pos,
        )
        # Same function as Spring Attack calls — confirm shared mechanism
        filtered = filter_aoo_from_target([trigger_target, trigger_side], target_id="goblin")

        assert all(t.reactor_id != "goblin" for t in filtered), \
            "Target's AoO must be removed by filter_aoo_from_target (same as Spring Attack)"
        assert any(t.reactor_id == "orc_guard" for t in filtered), \
            "Side-enemy AoO must remain after filtering"

    def test_SOTR005_full_round_action_registered(self):
        """SOTR-005: Shot on the Run is a full-round action (PHB p.99).

        action_economy.get_action_type(ShotOnTheRunIntent) must return 'full_round'.
        """
        intent = ShotOnTheRunIntent(attacker_id="archer", target_id="goblin",
                                    weapon=_ranged_weapon_dict())
        slot = get_action_type(intent)
        assert slot == "full_round", \
            f"ShotOnTheRunIntent must be 'full_round' action, got '{slot}'"

    def test_SOTR006_ranged_path_not_melee(self):
        """SOTR-006: Only a ranged attack resolved — not melee, not full_attack.

        resolve_shot_on_the_run routes through resolve_attack (single ranged).
        Confirmed: one attack_roll event, no full_attack_start event.
        Resolver enforces ranged weapon_type internally (weapon_type='ranged').
        """
        a = _attacker(feats=["shot_on_the_run"])
        t = _target(ac=1)
        ws = _world(a, t)
        intent = ShotOnTheRunIntent(attacker_id="archer", target_id="goblin",
                                    weapon=_ranged_weapon_dict())
        events = resolve_shot_on_the_run(intent, ws,
                                         _rng(rolls=[15, 4, 4, 4, 4]),
                                         next_event_id=0, timestamp=0.0)
        roll_events = [e for e in events if e.event_type == "attack_roll"]
        full_atk = [e for e in events if e.event_type == "full_attack_start"]
        assert len(roll_events) == 1, \
            f"Single ranged attack (1 attack_roll), got {len(roll_events)}"
        assert len(full_atk) == 0, \
            "Shot on the Run must not produce full_attack_start event"

    def test_SOTR007_range_penalty_still_applies(self):
        """SOTR-007: Range increment penalty still applies (NOT suppressed by feat).

        PHB p.99: 'Range increment penalties still apply normally.'
        Shot on the Run only suppresses AoO from target — NOT range penalties.

        Proven: attack_roll total with range_penalty=-2 is 2 lower than with range_penalty=0,
        using the same fixed d20 roll.
        """
        a = _attacker(feats=["shot_on_the_run"], bab=6)
        t = _target(ac=1)

        fixed_roll = 10
        intent_no = ShotOnTheRunIntent(attacker_id="archer", target_id="goblin",
                                       weapon=_ranged_weapon_dict(), range_penalty=0)
        intent_pen = ShotOnTheRunIntent(attacker_id="archer", target_id="goblin",
                                        weapon=_ranged_weapon_dict(), range_penalty=-2)

        evts_no = resolve_shot_on_the_run(intent_no, _world(a, t),
                                          _rng(rolls=[fixed_roll] + [4] * 10),
                                          next_event_id=0, timestamp=0.0)
        evts_pen = resolve_shot_on_the_run(intent_pen, _world(a, t),
                                           _rng(rolls=[fixed_roll] + [4] * 10),
                                           next_event_id=0, timestamp=0.0)

        roll_no = next(e for e in evts_no if e.event_type == "attack_roll")
        roll_pen = next(e for e in evts_pen if e.event_type == "attack_roll")
        total_no = roll_no.payload["total"]
        total_pen = roll_pen.payload["total"]

        assert total_pen == total_no - 2, \
            (f"range_penalty=-2 should reduce total by 2. "
             f"no_penalty={total_no}, with_penalty={total_pen}")

    def test_SOTR008_hit_miss_resolve_normally(self):
        """SOTR-008: Hit/miss resolve normally — no special mechanic from Shot on the Run.

        Shot on the Run is a movement wrapper + AoO suppression only.
        Hit → hp_changed event with delta < 0.
        Miss → no hp_changed, one attack_roll.
        """
        a = _attacker(feats=["shot_on_the_run"])

        # Hit case
        t_hit = _target(eid="goblin_hit", ac=1)
        evts_hit = resolve_shot_on_the_run(
            ShotOnTheRunIntent(attacker_id="archer", target_id="goblin_hit",
                               weapon=_ranged_weapon_dict()),
            _world(a, t_hit),
            _rng(rolls=[15, 4, 4, 4]),
            next_event_id=0, timestamp=0.0,
        )
        hp_hit = [e for e in evts_hit if e.event_type == "hp_changed"]
        assert len(hp_hit) >= 1, "Hit case: hp_changed expected"

        # Miss case
        t_miss = _target(eid="goblin_miss", ac=99)
        evts_miss = resolve_shot_on_the_run(
            ShotOnTheRunIntent(attacker_id="archer", target_id="goblin_miss",
                               weapon=_ranged_weapon_dict()),
            _world(a, t_miss),
            _rng(rolls=[1, 4, 4, 4]),
            next_event_id=0, timestamp=0.0,
        )
        hp_miss = [e for e in evts_miss if e.event_type == "hp_changed"]
        roll_miss = [e for e in evts_miss if e.event_type == "attack_roll"]
        assert len(hp_miss) == 0, "Miss case: no hp_changed"
        assert len(roll_miss) == 1, "Miss case: one attack_roll event"
