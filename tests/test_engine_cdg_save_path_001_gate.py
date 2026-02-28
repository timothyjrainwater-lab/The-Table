"""Gate tests for WO2 — ENGINE-CDG-SAVE-PATH-001.

8 tests: CDG-001..CDG-008.
Fix: Route CdG Fort save through get_save_bonus() instead of raw EF.SAVE_FORT.
     Add nat1/nat20 auto-fail/pass (PHB p.136).
RAW: PHB p.153 — "If the defender survives the damage, he must make a
     Fortitude save (DC 10 + damage dealt) or die."
"""
import unittest.mock as mock
from typing import Any, Dict

import pytest

from aidm.core.play_loop import TurnContext, execute_turn
from aidm.core.action_economy import ActionBudget
from aidm.core.state import WorldState
from aidm.schemas.intents import CoupDeGraceIntent
from aidm.schemas.entity_fields import EF


# ---------------------------------------------------------------------------
# Helpers (adapted from test_engine_gate_cdg.py)
# ---------------------------------------------------------------------------

def _weapon(
    damage_dice: str = "1d4",
    damage_bonus: int = 0,
    crit_multiplier: int = 2,
    damage_type: str = "slashing",
    grip: str = "one-handed",
) -> dict:
    return {
        "damage_dice": damage_dice,
        "damage_bonus": damage_bonus,
        "crit_multiplier": crit_multiplier,
        "damage_type": damage_type,
        "grip": grip,
    }


def _entity(
    eid: str,
    team: str,
    hp: int,
    hp_max: int = 30,
    save_fort: int = 0,
    feats: list = None,
    conditions: dict = None,
    class_levels: dict = None,
    cha_mod: int = 0,
    racial_save_bonus: int = 0,
) -> Dict[str, Any]:
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: team,
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp_max,
        EF.AC: 5,
        EF.SAVE_FORT: save_fort,
        EF.STR_MOD: 0,
        EF.DEX_MOD: 0,
        EF.ATTACK_BONUS: 5,
        EF.BAB: 5,
        "bab": 5,
        EF.DEFEATED: False,
        EF.DYING: False,
        EF.STABLE: False,
        EF.DISABLED: False,
        EF.CONDITIONS: conditions if conditions is not None else {},
        EF.POSITION: {"x": 0, "y": 0},
        EF.SIZE_CATEGORY: "medium",
        EF.FEATS: feats if feats is not None else [],
        EF.CLASS_LEVELS: class_levels if class_levels is not None else {},
        EF.CHA_MOD: cha_mod,
        EF.RACIAL_SAVE_BONUS: racial_save_bonus,
    }


def _world(attacker: dict, target: dict) -> WorldState:
    return WorldState(
        ruleset_version="3.5e",
        entities={"attacker": attacker, "target": target},
        active_combat={"initiative_order": ["attacker", "target"]},
    )


def _ctx() -> TurnContext:
    return TurnContext(turn_index=0, actor_id="attacker", actor_team="party")


def _rng_fixed(damage_roll: int, fort_roll: int):
    """RNG: damage_roll first (for weapon die), then fort_roll (d20)."""
    stream = mock.MagicMock()
    stream.randint.side_effect = [damage_roll, fort_roll] + [fort_roll] * 10
    rng = mock.MagicMock()
    rng.stream.return_value = stream
    return rng


def _run_cdg(target, damage_roll=1, fort_roll=10, weapon=None):
    """Execute a CdG and return events dict keyed by event_type."""
    attacker = _entity("attacker", "party", hp=20)
    ws = _world(attacker, target)
    intent = CoupDeGraceIntent(
        attacker_id="attacker",
        target_id="target",
        weapon=weapon or _weapon(),
    )
    rng = _rng_fixed(damage_roll=damage_roll, fort_roll=fort_roll)
    result = execute_turn(ws, _ctx(), combat_intent=intent, rng=rng)
    return result


# ---------------------------------------------------------------------------
# CDG-001: Great Fortitude feat (+2) applies to CdG Fort save
# ---------------------------------------------------------------------------
class TestCDG001:
    """CdG Fort save includes Great Fortitude (+2 Fort, PHB p.94)."""

    def test_great_fortitude_makes_save_pass(self):
        # Weapon 1d4, roll=1, crit*2 -> damage=2. DC = 10+2 = 12.
        # save_fort=0, fort_roll=11. Without feat: 11+0=11 < 12 -> FAIL.
        # With Great Fortitude (+2): 11+0+2=13 >= 12 -> PASS.
        target = _entity(
            "target", "monsters", hp=5,
            conditions={"helpless": {}},
            save_fort=0,
            feats=["great_fortitude"],
        )
        result = _run_cdg(target, damage_roll=1, fort_roll=11)

        fort_ev = next(
            (e for e in result.events if e.event_type == "cdg_fort_save"),
            None,
        )
        assert fort_ev is not None
        assert fort_ev.payload["passed"] is True, (
            "Great Fortitude +2 should push 11+0+2=13 >= DC 12"
        )


# ---------------------------------------------------------------------------
# CDG-002: Condition modifiers preserved (shaken -2)
# ---------------------------------------------------------------------------
class TestCDG002:
    """CdG Fort save still includes condition modifiers (shaken -2)."""

    def test_shaken_condition_reduces_save(self):
        # Weapon 1d4, roll=1, crit*2 -> damage=2. DC = 12.
        # save_fort=10, shaken -> condition_mod=-2, effective=8.
        # fort_roll=4: 4+8=12 >= 12 -> PASS.
        target = _entity(
            "target", "monsters", hp=5,
            conditions={"helpless": {}, "shaken": {}},
            save_fort=10,
        )
        result = _run_cdg(target, damage_roll=1, fort_roll=4)

        fort_ev = next(
            (e for e in result.events if e.event_type == "cdg_fort_save"),
            None,
        )
        assert fort_ev is not None
        assert fort_ev.payload["passed"] is True


# ---------------------------------------------------------------------------
# CDG-003: DC = 10 + damage_total
# ---------------------------------------------------------------------------
class TestCDG003:
    """CdG Fort save DC = 10 + damage_total (PHB p.153)."""

    def test_dc_is_10_plus_damage(self):
        # Weapon 1d4, roll=3, crit*2 -> damage=6. DC = 10+6 = 16.
        target = _entity(
            "target", "monsters", hp=5,
            conditions={"helpless": {}},
            save_fort=0,
        )
        result = _run_cdg(target, damage_roll=3, fort_roll=10)

        fort_ev = next(
            (e for e in result.events if e.event_type == "cdg_fort_save"),
            None,
        )
        assert fort_ev is not None
        assert fort_ev.payload["dc"] == 16


# ---------------------------------------------------------------------------
# CDG-004: Fort save failure → death (HP=-10)
# ---------------------------------------------------------------------------
class TestCDG004:
    """CdG Fort save failure → entity set to -10 HP (dead)."""

    def test_failed_fort_save_causes_death(self):
        # Weapon 1d4, roll=1, crit*2 -> damage=2. DC=12.
        # save_fort=0, fort_roll=1: 1+0=1 < 12 -> FAIL -> death.
        target = _entity(
            "target", "monsters", hp=5,
            conditions={"helpless": {}},
            save_fort=0,
        )
        result = _run_cdg(target, damage_roll=1, fort_roll=1)

        defeated = [e for e in result.events if e.event_type == "entity_defeated"]
        assert len(defeated) > 0
        final = result.world_state.entities.get("target", {})
        assert final.get(EF.HP_CURRENT, 0) == -10


# ---------------------------------------------------------------------------
# CDG-005: Nat 20 auto-passes (PHB p.136)
# ---------------------------------------------------------------------------
class TestCDG005:
    """CdG Fort save nat 20 auto-passes regardless of DC."""

    def test_nat_20_auto_pass(self):
        # Massive damage -> very high DC. save_fort=0, fort_roll=20.
        # Normal: 20+0=20 < 110 -> FAIL. With nat20: auto-PASS.
        target = _entity(
            "target", "monsters", hp=200, hp_max=200,
            conditions={"helpless": {}},
            save_fort=0,
        )
        # 1d4 roll=4, crit*2 -> damage=8, but we need huge damage.
        # Use big weapon: 1d4 damage_bonus=45, crit*2 -> base=4+45=49, damage=98.
        # DC = 10+98 = 108. Nat 20: 20+0 = 20 < 108 normally.
        result = _run_cdg(
            target, damage_roll=4, fort_roll=20,
            weapon=_weapon("1d4", damage_bonus=45, crit_multiplier=2),
        )

        fort_ev = next(
            (e for e in result.events if e.event_type == "cdg_fort_save"),
            None,
        )
        assert fort_ev is not None
        assert fort_ev.payload["passed"] is True, (
            "Natural 20 should auto-pass Fort save (PHB p.136)"
        )


# ---------------------------------------------------------------------------
# CDG-006: Nat 1 auto-fails (PHB p.136)
# ---------------------------------------------------------------------------
class TestCDG006:
    """CdG Fort save nat 1 auto-fails regardless of bonus."""

    def test_nat_1_auto_fail(self):
        # Tiny damage -> low DC. High save_fort. fort_roll=1.
        # Normal: 1+20=21 >= 12 -> PASS. With nat1: auto-FAIL.
        target = _entity(
            "target", "monsters", hp=5,
            conditions={"helpless": {}},
            save_fort=20,
        )
        # 1d4 roll=1, crit*2 -> damage=2. DC=12. 1+20=21>=12 normally.
        result = _run_cdg(target, damage_roll=1, fort_roll=1)

        fort_ev = next(
            (e for e in result.events if e.event_type == "cdg_fort_save"),
            None,
        )
        assert fort_ev is not None
        assert fort_ev.payload["passed"] is False, (
            "Natural 1 should auto-fail Fort save (PHB p.136)"
        )

        # Target should be killed (HP=-10)
        defeated = [e for e in result.events if e.event_type == "entity_defeated"]
        assert len(defeated) > 0


# ---------------------------------------------------------------------------
# CDG-007: Divine Grace (paladin CHA mod to Fort)
# ---------------------------------------------------------------------------
class TestCDG007:
    """CdG Fort save includes Divine Grace (+CHA mod) for paladin 2+."""

    def test_divine_grace_cha_bonus(self):
        # Weapon 1d4, roll=1, crit*2 -> damage=2. DC=12.
        # save_fort=0, cha_mod=3, paladin 2. fort_roll=9.
        # Without Divine Grace: 9+0=9 < 12 -> FAIL.
        # With Divine Grace (+3): 9+0+3=12 >= 12 -> PASS.
        target = _entity(
            "target", "monsters", hp=5,
            conditions={"helpless": {}},
            save_fort=0,
            class_levels={"paladin": 2},
            cha_mod=3,
        )
        result = _run_cdg(target, damage_roll=1, fort_roll=9)

        fort_ev = next(
            (e for e in result.events if e.event_type == "cdg_fort_save"),
            None,
        )
        assert fort_ev is not None
        assert fort_ev.payload["passed"] is True, (
            "Divine Grace +3 CHA should push 9+0+3=12 >= DC 12"
        )


# ---------------------------------------------------------------------------
# CDG-008: Halfling +1 all saves
# ---------------------------------------------------------------------------
class TestCDG008:
    """CdG Fort save includes halfling +1 racial bonus (PHB p.20)."""

    def test_halfling_racial_bonus(self):
        # Weapon 1d4, roll=1, crit*2 -> damage=2. DC=12.
        # save_fort=0, racial_save_bonus=1. fort_roll=11.
        # Without racial: 11+0=11 < 12 -> FAIL.
        # With racial (+1): 11+0+1=12 >= 12 -> PASS.
        target = _entity(
            "target", "monsters", hp=5,
            conditions={"helpless": {}},
            save_fort=0,
            racial_save_bonus=1,
        )
        result = _run_cdg(target, damage_roll=1, fort_roll=11)

        fort_ev = next(
            (e for e in result.events if e.event_type == "cdg_fort_save"),
            None,
        )
        assert fort_ev is not None
        assert fort_ev.payload["passed"] is True, (
            "Halfling +1 racial bonus should push 11+0+1=12 >= DC 12"
        )
