"""
ENGINE GATE — WO-ENGINE-MOBILITY-001: Mobility feat (+4 AC vs movement AoO)
Tests MB-001 through MB-008.
PHB p.97: "+4 to AC against attacks of opportunity provoked by moving out of a threatened square."

Wiring: feat_resolver.get_ac_modifier() computes +4 for "mobility" feat in movement AoO context.
aoo.py resolve_aoo_sequence() applies the modifier via deepcopy of world_state entities.

WO-ENGINE-MOBILITY-001, Batch R.
"""

import pytest
from unittest.mock import MagicMock
from copy import deepcopy

from aidm.core.aoo import AooTrigger, resolve_aoo_sequence
from aidm.core.feat_resolver import get_ac_modifier
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.schemas.position import Position


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _pos(x, y):
    return Position(x, y)


def _provoker(eid="mover", feats=None, ac=10):
    """Entity that moves and provokes AoO."""
    return {
        EF.ENTITY_ID: eid,
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 30,
        EF.AC: ac,
        EF.TEAM: "party",
        EF.POSITION: {"x": 3, "y": 3},
        EF.CONDITIONS: {},
        EF.FEATS: feats if feats is not None else [],
        EF.DEX_MOD: 0,
        EF.STR_MOD: 0,
    }


def _reactor(eid="goblin", attack_bonus=8, hp=20):
    """Enemy entity that makes the AoO."""
    return {
        EF.ENTITY_ID: eid,
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp,
        EF.AC: 12,
        EF.ATTACK_BONUS: attack_bonus,
        EF.TEAM: "monsters",
        EF.POSITION: {"x": 4, "y": 3},
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.DEX_MOD: 0,
        EF.STR_MOD: 0,
        EF.WEAPON: {"damage_dice": "1d6", "damage_bonus": 0, "damage_type": "slashing"},
    }


def _movement_trigger(provoker_id="mover", reactor_id="goblin"):
    """AoO trigger for movement_out (standard movement leaving threatened square)."""
    return AooTrigger(
        reactor_id=reactor_id,
        provoker_id=provoker_id,
        provoking_action="movement_out",
        reactor_position=_pos(4, 3),
        provoker_from_pos=_pos(3, 3),
        provoker_to_pos=_pos(3, 4),
    )


def _stand_trigger(provoker_id="mover", reactor_id="goblin"):
    """AoO trigger for stand_from_prone."""
    return AooTrigger(
        reactor_id=reactor_id,
        provoker_id=provoker_id,
        provoking_action="stand_from_prone",
        reactor_position=_pos(4, 3),
        provoker_from_pos=_pos(3, 3),
    )


def _world(mover, goblin):
    ents = {mover[EF.ENTITY_ID]: mover, goblin[EF.ENTITY_ID]: goblin}
    active_combat = {
        "initiative_order": [mover[EF.ENTITY_ID], goblin[EF.ENTITY_ID]],
        "aoo_used_this_round": [],
        "aoo_count_this_round": {},
        "action_budget_actor": None,
        "action_budget": None,
    }
    return WorldState(ruleset_version="3.5", entities=ents, active_combat=active_combat)


def _make_rng(roll=10):
    rng = MagicMock()
    stream = MagicMock()
    stream.randint.return_value = roll
    rng.stream.return_value = stream
    return rng


def _get_attack_rolls(result):
    return [e for e in result.events if e.event_type == "attack_roll"]


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestMobilityGate:

    def test_MB001_mobility_movement_aoo_returns_plus4(self):
        """MB-001: Mobility feat + movement_out AoO context → get_ac_modifier returns +4."""
        mover = _provoker(feats=["mobility"])
        context = {"is_aoo": True, "aoo_trigger": "movement_out"}
        modifier = get_ac_modifier(mover, {}, context)
        assert modifier == 4, f"Expected +4 AC for Mobility movement AoO, got {modifier}"

    def test_MB002_no_mobility_movement_aoo_returns_zero(self):
        """MB-002: No Mobility feat + movement_out AoO context → get_ac_modifier returns 0."""
        mover = _provoker(feats=[])
        context = {"is_aoo": True, "aoo_trigger": "movement_out"}
        modifier = get_ac_modifier(mover, {}, context)
        assert modifier == 0, f"Expected 0 AC for no-Mobility movement AoO, got {modifier}"

    def test_MB003_mobility_non_movement_aoo_returns_zero(self):
        """MB-003: Mobility feat + spellcasting AoO (not movement) → get_ac_modifier returns 0."""
        mover = _provoker(feats=["mobility"])
        context = {"is_aoo": True, "aoo_trigger": "spellcasting"}
        modifier = get_ac_modifier(mover, {}, context)
        assert modifier == 0, f"Expected 0 (non-movement trigger), got {modifier}"

    def test_MB004_mobility_aoo_misses_due_to_plus4(self):
        """MB-004: Mobility causes AoO to miss when attack_bonus + roll barely hits base AC but misses AC+4."""
        # Provoker AC=10, reactor attack_bonus=8, roll=3 → 8+3=11 >= 10 (hits without Mobility)
        # With Mobility: effective AC=14 → 8+3=11 < 14 (misses)
        mover = _provoker(feats=["mobility"], ac=10)
        goblin = _reactor(attack_bonus=8)
        ws = _world(mover, goblin)
        trigger = _movement_trigger()
        rng = _make_rng(roll=3)

        result = resolve_aoo_sequence([trigger], ws, rng, next_event_id=0, timestamp=0.0)
        attack_rolls = _get_attack_rolls(result)
        assert len(attack_rolls) == 1, "AoO should have resolved one attack"
        assert not attack_rolls[0].payload["hit"], "AoO should MISS with Mobility (+4 AC)"

    def test_MB005_no_mobility_same_setup_hits(self):
        """MB-005: No Mobility, same attack_bonus=8 + roll=3 → hits base AC=10 (control case for MB-004)."""
        mover = _provoker(feats=[], ac=10)  # No Mobility
        goblin = _reactor(attack_bonus=8)
        ws = _world(mover, goblin)
        trigger = _movement_trigger()
        rng = _make_rng(roll=3)

        result = resolve_aoo_sequence([trigger], ws, rng, next_event_id=0, timestamp=0.0)
        attack_rolls = _get_attack_rolls(result)
        assert len(attack_rolls) == 1, "AoO should have resolved one attack"
        assert attack_rolls[0].payload["hit"], "AoO should HIT without Mobility (AC=10, roll=3+8=11)"

    def test_MB006_stand_from_prone_trigger_no_mobility_bonus(self):
        """MB-006: Mobility feat + stand_from_prone trigger → no +4 (trigger not in allowed set)."""
        mover = _provoker(feats=["mobility"])
        context = {"is_aoo": True, "aoo_trigger": "stand_from_prone"}
        modifier = get_ac_modifier(mover, {}, context)
        assert modifier == 0, f"Expected 0 (stand_from_prone not in movement trigger set), got {modifier}"

    def test_MB007_multiple_movement_aoos_mobility_applies_each(self):
        """MB-007: Two movement AoOs in same sequence → Mobility applies to each (deepcopy per-AoO)."""
        # Two reactors, provoker has Mobility (AC=10 effective AC=14)
        mover = _provoker(feats=["mobility"], ac=10)
        goblin1 = _reactor(eid="goblin1", attack_bonus=8)
        goblin2_data = {
            EF.ENTITY_ID: "goblin2",
            EF.HP_CURRENT: 20,
            EF.HP_MAX: 20,
            EF.AC: 12,
            EF.ATTACK_BONUS: 8,
            EF.TEAM: "monsters",
            EF.POSITION: {"x": 3, "y": 4},  # Adjacent, different position
            EF.CONDITIONS: {},
            EF.FEATS: [],
            EF.DEX_MOD: 0,
            EF.STR_MOD: 0,
            EF.WEAPON: {"damage_dice": "1d6", "damage_bonus": 0, "damage_type": "slashing"},
        }
        ents = {
            "mover": mover,
            "goblin1": goblin1,
            "goblin2": goblin2_data,
        }
        active_combat = {
            "initiative_order": ["mover", "goblin1", "goblin2"],
            "aoo_used_this_round": [],
            "aoo_count_this_round": {},
            "action_budget_actor": None,
            "action_budget": None,
        }
        ws = WorldState(ruleset_version="3.5", entities=ents, active_combat=active_combat)

        trigger1 = AooTrigger(
            reactor_id="goblin1", provoker_id="mover",
            provoking_action="movement_out",
            reactor_position=_pos(4, 3), provoker_from_pos=_pos(3, 3), provoker_to_pos=_pos(3, 4),
        )
        trigger2 = AooTrigger(
            reactor_id="goblin2", provoker_id="mover",
            provoking_action="movement_out",
            reactor_position=_pos(3, 4), provoker_from_pos=_pos(3, 3), provoker_to_pos=_pos(3, 4),
        )
        rng = _make_rng(roll=3)  # 8+3=11 < 14 → both miss with Mobility

        result = resolve_aoo_sequence([trigger1, trigger2], ws, rng, next_event_id=0, timestamp=0.0)
        attack_rolls = _get_attack_rolls(result)
        assert len(attack_rolls) == 2, "Both AoOs should resolve"
        assert not attack_rolls[0].payload["hit"], "First AoO should miss (Mobility active)"
        assert not attack_rolls[1].payload["hit"], "Second AoO should miss (Mobility active for each)"

    def test_MB008_mounted_movement_trigger_returns_plus4(self):
        """MB-008: Mobility feat + mounted_movement_out trigger → get_ac_modifier returns +4."""
        mover = _provoker(feats=["mobility"])
        context = {"is_aoo": True, "aoo_trigger": "mounted_movement_out"}
        modifier = get_ac_modifier(mover, {}, context)
        assert modifier == 4, f"Expected +4 AC for Mobility mounted movement AoO, got {modifier}"
