"""Gate tests: ENGINE-AH-WO2 — Spring Attack (PHB p.100)

Full-round action. Move up to speed, make one melee attack at any point
during movement, continue moving. Target does not get AoO from the attacker.
Cannot use in heavy armor.

Authority: RAW — PHB p.100
Shared AoO suppression via filter_aoo_from_target (aoo.py) — same mechanism as Shot on the Run.
Tests: SPRK-001 through SPRK-008
"""

import unittest.mock as mock
import pytest
from aidm.core.attack_resolver import resolve_spring_attack
from aidm.core.aoo import AooTrigger, filter_aoo_from_target
from aidm.core.action_economy import get_action_type
from aidm.core.state import WorldState
from aidm.schemas.intents import SpringAttackIntent
from aidm.schemas.position import Position
from aidm.schemas.entity_fields import EF


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _melee_weapon_dict():
    return {
        "damage_dice": "1d8",
        "damage_bonus": 0,
        "damage_type": "slashing",
        "critical_multiplier": 2,
        "critical_range": 20,
        "weapon_type": "one-handed",
        "range_increment": 0,
        "enhancement_bonus": 0,
    }


def _attacker(eid="fighter", bab=6, feats=None, armor_type="none", str_mod=2) -> dict:
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: 50,
        EF.HP_MAX: 50,
        EF.AC: 14,
        EF.ATTACK_BONUS: bab,
        EF.BAB: bab,
        EF.STR_MOD: str_mod,
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
        rolls = [15, 4, 4, 4, 4, 4, 4, 4, 4, 4]  # d20 hit + damage + extras
    stream.randint.side_effect = rolls
    rng = mock.MagicMock()
    rng.stream.return_value = stream
    return rng


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestEngineSpringAttackGate:

    def test_SPRK001_feat_present_resolves_attack(self):
        """SPRK-001: Entity with Spring Attack feat → intent resolves single attack event."""
        a = _attacker(feats=["spring_attack"])
        t = _target(ac=5)
        ws = _world(a, t)
        intent = SpringAttackIntent(attacker_id="fighter", target_id="goblin",
                                    weapon=_melee_weapon_dict())
        events = resolve_spring_attack(intent, ws, _rng(), next_event_id=0, timestamp=0.0)
        roll_events = [e for e in events if e.event_type == "attack_roll"]
        invalid_events = [e for e in events if e.event_type == "spring_attack_invalid"]
        assert len(roll_events) >= 1, "Expected at least one attack_roll with feat present"
        assert len(invalid_events) == 0, "No spring_attack_invalid expected with feat present"

    def test_SPRK002_no_feat_blocked(self):
        """SPRK-002: No Spring Attack feat → intent blocked with spring_attack_invalid event."""
        a = _attacker(feats=[])
        t = _target()
        ws = _world(a, t)
        intent = SpringAttackIntent(attacker_id="fighter", target_id="goblin",
                                    weapon=_melee_weapon_dict())
        events = resolve_spring_attack(intent, ws, _rng(), next_event_id=0, timestamp=0.0)
        types = [e.event_type for e in events]
        assert "spring_attack_invalid" in types, "Expected spring_attack_invalid when feat missing"
        assert "attack_roll" not in types, "No attack_roll should fire without feat"

    def test_SPRK003_heavy_armor_blocked(self):
        """SPRK-003: Heavy armor equipped → intent blocked (PHB p.100).

        EF.ARMOR_TYPE == 'heavy' → spring_attack_invalid with reason='heavy_armor'.
        """
        a = _attacker(feats=["spring_attack"], armor_type="heavy")
        t = _target()
        ws = _world(a, t)
        intent = SpringAttackIntent(attacker_id="fighter", target_id="goblin",
                                    weapon=_melee_weapon_dict())
        events = resolve_spring_attack(intent, ws, _rng(), next_event_id=0, timestamp=0.0)
        types = [e.event_type for e in events]
        assert "spring_attack_invalid" in types, "Expected spring_attack_invalid with heavy armor"
        invalid = next(e for e in events if e.event_type == "spring_attack_invalid")
        assert invalid.payload.get("reason") == "heavy_armor", \
            f"Expected reason='heavy_armor', got {invalid.payload.get('reason')}"

    def test_SPRK004_target_aoo_suppressed_by_shared_mechanism(self):
        """SPRK-004: filter_aoo_from_target removes target's AoO trigger (WO2+WO3 shared mechanism).

        PHB p.100: 'without provoking an attack of opportunity from the target of your attack.'
        Other threatening creatures can still AoO the movement normally.

        Proves filter_aoo_from_target (aoo.py) is the shared suppression for WO2 and WO3:
        - Target's trigger removed; side-enemy's trigger preserved.
        - Spring Attack: melee doesn't provoke AoO at all, so filter is a no-op in practice.
          Still called from play_loop to prove shared mechanism with Shot on the Run.
        """
        pos = Position(x=0, y=0)
        trigger_from_target = AooTrigger(
            reactor_id="goblin",        # Attack target — must be suppressed
            provoker_id="fighter",
            provoking_action="ranged_attack",
            reactor_position=pos,
            provoker_from_pos=pos,
        )
        trigger_from_side = AooTrigger(
            reactor_id="orc_guard",     # Side enemy — must be preserved
            provoker_id="fighter",
            provoking_action="ranged_attack",
            reactor_position=pos,
            provoker_from_pos=pos,
        )

        filtered = filter_aoo_from_target([trigger_from_target, trigger_from_side],
                                          target_id="goblin")

        target_remaining = [t for t in filtered if t.reactor_id == "goblin"]
        side_remaining = [t for t in filtered if t.reactor_id == "orc_guard"]

        assert len(target_remaining) == 0, \
            "Target AoO must be removed by filter_aoo_from_target"
        assert len(side_remaining) == 1, \
            "Side-enemy AoO must remain after filtering"

    def test_SPRK005_full_round_action_registered(self):
        """SPRK-005: Spring Attack is a full-round action (PHB p.100).

        action_economy.get_action_type(SpringAttackIntent) must return 'full_round'.
        Consuming full_round also marks standard+move used, blocking second attacks.
        """
        intent = SpringAttackIntent(attacker_id="fighter", target_id="goblin",
                                    weapon=_melee_weapon_dict())
        slot = get_action_type(intent)
        assert slot == "full_round", \
            f"SpringAttackIntent must be 'full_round' action, got '{slot}'"

    def test_SPRK006_single_attack_only(self):
        """SPRK-006: Only one attack resolved — iterative attack logic does NOT fire.

        BAB=11 would normally give 3 iterative attacks via full_attack_resolver.
        Spring Attack bypasses this: one attack_roll event only.
        resolve_spring_attack → resolve_attack (single), never full_attack_resolver.
        """
        a = _attacker(feats=["spring_attack"], bab=11)
        t = _target(ac=1)
        ws = _world(a, t)
        intent = SpringAttackIntent(attacker_id="fighter", target_id="goblin",
                                    weapon=_melee_weapon_dict())
        events = resolve_spring_attack(intent, ws,
                                       _rng(rolls=[15, 4, 4, 4, 4, 4, 4, 4]),
                                       next_event_id=0, timestamp=0.0)
        roll_events = [e for e in events if e.event_type == "attack_roll"]
        full_atk_events = [e for e in events if e.event_type == "full_attack_start"]
        assert len(roll_events) == 1, \
            f"Spring Attack must produce exactly 1 attack_roll (not iterative), got {len(roll_events)}"
        assert len(full_atk_events) == 0, \
            "Spring Attack must not produce full_attack_start event"

    def test_SPRK007_hit_resolves_normally(self):
        """SPRK-007: Hit resolves normally — standard damage, hp_changed event present.

        Spring Attack is a movement wrapper, NOT an attack modifier. The attack itself
        is a standard melee attack with no bonus or penalty from the feat.
        """
        a = _attacker(feats=["spring_attack"])
        t = _target(ac=1)  # Very low AC — always hits
        ws = _world(a, t)
        intent = SpringAttackIntent(attacker_id="fighter", target_id="goblin",
                                    weapon=_melee_weapon_dict())
        events = resolve_spring_attack(intent, ws,
                                       _rng(rolls=[15, 4, 4, 4, 4]),
                                       next_event_id=0, timestamp=0.0)
        hp_events = [e for e in events if e.event_type == "hp_changed"]
        assert len(hp_events) >= 1, "Hit case must produce hp_changed event"
        assert hp_events[0].payload.get("delta", 0) < 0, \
            "Damage must reduce HP (delta < 0)"

    def test_SPRK008_miss_resolves_normally(self):
        """SPRK-008: Miss resolves normally — no damage, no hp_changed. No special miss mechanic.

        PHB p.100: Spring Attack only changes movement + AoO suppression. Miss is standard.
        """
        a = _attacker(feats=["spring_attack"])
        t = _target(ac=99)  # Unreachable AC — always misses
        ws = _world(a, t)
        intent = SpringAttackIntent(attacker_id="fighter", target_id="goblin",
                                    weapon=_melee_weapon_dict())
        events = resolve_spring_attack(intent, ws,
                                       _rng(rolls=[1, 4, 4, 4]),
                                       next_event_id=0, timestamp=0.0)
        roll_events = [e for e in events if e.event_type == "attack_roll"]
        hp_events = [e for e in events if e.event_type == "hp_changed"]
        assert len(roll_events) == 1, "One attack_roll event even on miss"
        assert len(hp_events) == 0, "Miss: no hp_changed"
