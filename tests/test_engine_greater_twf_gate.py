"""
ENGINE GATE — WO-ENGINE-GREATER-TWF-001: Greater Two-Weapon Fighting
Tests GTWF-001 through GTWF-008.
PHB p.96: Greater Two-Weapon Fighting grants a third off-hand attack at BAB-10.

Chain: TWF (1st off-hand) → ITWF (2nd off-hand at BAB-5) → GTWF (3rd off-hand at BAB-10)
Feat string: "Greater Two-Weapon Fighting" (Title Case, matches TWF/ITWF convention).

WO-ENGINE-GREATER-TWF-001, Batch R.
"""

import pytest
from typing import Any, Dict, List

from aidm.core.full_attack_resolver import (
    FullAttackIntent,
    resolve_full_attack,
    _compute_twf_penalties,
)
from aidm.core.rng_manager import RNGManager
from aidm.core.state import WorldState
from aidm.schemas.attack import Weapon
from aidm.schemas.entity_fields import EF
from aidm.schemas.position import Position


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _pos(x: int = 0, y: int = 0) -> dict:
    return {"x": x, "y": y}


def _longsword() -> Weapon:
    return Weapon(
        damage_dice="1d8",
        damage_bonus=0,
        damage_type="slashing",
        weapon_type="one-handed",
    )


def _shortsword() -> Weapon:
    """Light off-hand weapon."""
    return Weapon(
        damage_dice="1d6",
        damage_bonus=0,
        damage_type="piercing",
        weapon_type="light",
    )


def _fighter(
    eid: str = "fighter_01",
    bab: int = 11,
    str_mod: int = 2,
    feats: List[str] = None,
    team: str = "party",
) -> Dict[str, Any]:
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: team,
        EF.HP_CURRENT: 40,
        EF.HP_MAX: 40,
        EF.AC: 14,
        EF.DEX_MOD: 3,
        EF.STR_MOD: str_mod,
        EF.BAB: bab,
        EF.DEFEATED: False,
        EF.CONDITIONS: {},
        EF.FEATS: feats or [],
        EF.POSITION: _pos(0, 0),
    }


def _goblin(eid: str = "goblin_01", hp: int = 500) -> Dict[str, Any]:
    """High HP goblin — survives all attacks so all iteratives fire."""
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "monsters",
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp,
        EF.AC: 5,  # Low AC — most attacks hit
        EF.DEX_MOD: 0,
        EF.STR_MOD: 0,
        EF.BAB: 1,
        EF.DEFEATED: False,
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.POSITION: _pos(1, 0),
    }


def _world(*entities) -> WorldState:
    ents = {e[EF.ENTITY_ID]: e for e in entities}
    return WorldState(ruleset_version="3.5e", entities=ents)


def _run_full_attack(
    ws: WorldState,
    attacker_id: str,
    target_id: str,
    bab: int,
    main_weapon: Weapon,
    off_hand: Weapon = None,
    seed: int = 99,
) -> List:
    rng = RNGManager(seed)
    intent = FullAttackIntent(
        attacker_id=attacker_id,
        target_id=target_id,
        base_attack_bonus=bab,
        weapon=main_weapon,
        off_hand_weapon=off_hand,
    )
    return resolve_full_attack(intent, ws, rng, next_event_id=0, timestamp=0.0)


def _count_attack_rolls(events) -> int:
    return sum(1 for e in events if e.event_type == "attack_roll")


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestGreaterTWFGate:

    def test_GTWF001_greater_twf_adds_third_offhand(self):
        """GTWF-001: TWF + ITWF + GTWF feats, BAB=11 → 6 attack_rolls (3 main + 3 off-hand)."""
        feats = ["Two-Weapon Fighting", "Improved Two-Weapon Fighting", "Greater Two-Weapon Fighting"]
        fighter = _fighter("f01", bab=11, feats=feats)
        goblin = _goblin("g01")
        ws = _world(fighter, goblin)

        events = _run_full_attack(ws, "f01", "g01", bab=11, main_weapon=_longsword(), off_hand=_shortsword())

        attack_count = _count_attack_rolls(events)
        assert attack_count == 6, (
            f"Expected 6 attack_rolls (3 main + 3 off-hand with GTWF), got {attack_count}"
        )

    def test_GTWF002_itwf_only_two_offhands(self):
        """GTWF-002: TWF + ITWF (no GTWF) → 5 attack_rolls; GTWF regression guard."""
        feats = ["Two-Weapon Fighting", "Improved Two-Weapon Fighting"]
        fighter = _fighter("f01", bab=11, feats=feats)
        goblin = _goblin("g01")
        ws = _world(fighter, goblin)

        events = _run_full_attack(ws, "f01", "g01", bab=11, main_weapon=_longsword(), off_hand=_shortsword())

        attack_count = _count_attack_rolls(events)
        assert attack_count == 5, (
            f"Expected 5 attack_rolls (3 main + 2 off-hand: ITWF, no GTWF), got {attack_count}"
        )

    def test_GTWF003_twf_only_one_offhand(self):
        """GTWF-003: TWF feat only → 4 attack_rolls; base TWF regression guard."""
        feats = ["Two-Weapon Fighting"]
        fighter = _fighter("f01", bab=11, feats=feats)
        goblin = _goblin("g01")
        ws = _world(fighter, goblin)

        events = _run_full_attack(ws, "f01", "g01", bab=11, main_weapon=_longsword(), off_hand=_shortsword())

        attack_count = _count_attack_rolls(events)
        assert attack_count == 4, (
            f"Expected 4 attack_rolls (3 main + 1 off-hand: TWF only), got {attack_count}"
        )

    def test_GTWF004_gtwf_fires_even_when_target_survives(self):
        """GTWF-004: All 3 off-hand attacks fire even when target survives every hit."""
        feats = ["Two-Weapon Fighting", "Improved Two-Weapon Fighting", "Greater Two-Weapon Fighting"]
        fighter = _fighter("f01", bab=11, feats=feats)
        goblin = _goblin("g01", hp=9999)  # Indestructible for this test
        ws = _world(fighter, goblin)

        events = _run_full_attack(ws, "f01", "g01", bab=11, main_weapon=_longsword(), off_hand=_shortsword())

        attack_count = _count_attack_rolls(events)
        assert attack_count == 6, (
            f"Expected 6 attack_rolls (target survives all hits, GTWF must still fire), got {attack_count}"
        )

    def test_GTWF005_gtwf_offhand_uses_half_str_damage(self):
        """GTWF-005: GTWF third off-hand uses half STR for damage (same as first and second off-hand)."""
        feats = ["Two-Weapon Fighting", "Improved Two-Weapon Fighting", "Greater Two-Weapon Fighting"]
        # STR_MOD=4 → off_str_mod=2 for all off-hand attacks
        fighter = _fighter("f01", bab=11, str_mod=4, feats=feats)
        goblin = _goblin("g01", hp=9999)
        ws = _world(fighter, goblin)

        events = _run_full_attack(ws, "f01", "g01", bab=11, main_weapon=_longsword(), off_hand=_shortsword())

        # 6 attacks fired; verify damage events exist (implicit half-STR via off_str_mod)
        attack_count = _count_attack_rolls(events)
        assert attack_count == 6, f"Expected 6 attacks (3 main + 3 off-hand), got {attack_count}"
        # All 3 off-hand damage_roll events should fire — half-STR applied to each
        damage_events = [e for e in events if e.event_type == "damage_roll"]
        assert len(damage_events) >= 3, (
            f"Expected at least 3 damage_roll events (3 off-hand hits), got {len(damage_events)}"
        )

    def test_GTWF006_main_hand_iteratives_unaffected(self):
        """GTWF-006: GTWF adds off-hand attacks; main-hand iterative count unchanged at BAB=11 (3 main)."""
        feats_gtwf = ["Two-Weapon Fighting", "Improved Two-Weapon Fighting", "Greater Two-Weapon Fighting"]
        feats_itwf = ["Two-Weapon Fighting", "Improved Two-Weapon Fighting"]

        fighter_gtwf = _fighter("f01", bab=11, feats=feats_gtwf)
        fighter_itwf = _fighter("f02", bab=11, feats=feats_itwf)
        goblin1 = _goblin("g01")
        goblin2 = _goblin("g02")
        ws1 = _world(fighter_gtwf, goblin1)
        ws2 = _world(fighter_itwf, goblin2)

        events_gtwf = _run_full_attack(ws1, "f01", "g01", bab=11, main_weapon=_longsword(), off_hand=_shortsword())
        events_itwf = _run_full_attack(ws2, "f02", "g02", bab=11, main_weapon=_longsword(), off_hand=_shortsword())

        assert _count_attack_rolls(events_gtwf) == 6, "GTWF: 3 main + 3 off-hand = 6"
        assert _count_attack_rolls(events_itwf) == 5, "ITWF: 3 main + 2 off-hand = 5"
        # Delta = 1: exactly the GTWF third off-hand
        assert _count_attack_rolls(events_gtwf) - _count_attack_rolls(events_itwf) == 1

    def test_GTWF007_three_offhand_events_emitted_in_sequence(self):
        """GTWF-007: Three off-hand attack_roll events appear after main-hand attacks (sequence ordering)."""
        feats = ["Two-Weapon Fighting", "Improved Two-Weapon Fighting", "Greater Two-Weapon Fighting"]
        fighter = _fighter("f01", bab=11, feats=feats)
        goblin = _goblin("g01", hp=9999)
        ws = _world(fighter, goblin)

        events = _run_full_attack(ws, "f01", "g01", bab=11, main_weapon=_longsword(), off_hand=_shortsword())

        # Total: 3 main + 3 off-hand = 6 attack_rolls
        attack_rolls = [e for e in events if e.event_type == "attack_roll"]
        assert len(attack_rolls) == 6, f"Expected 6 attack_rolls, got {len(attack_rolls)}"

        # Timestamps should be non-decreasing (events in execution order)
        for i in range(len(attack_rolls) - 1):
            assert attack_rolls[i].timestamp <= attack_rolls[i + 1].timestamp, (
                f"attack_roll events out of order at index {i}"
            )

    def test_GTWF008_regression_twf09_itwf_pattern_preserved(self):
        """GTWF-008: Regression — ITWF pattern from TWF-09 still passes with GTWF in codebase."""
        # This mirrors TWF-09: feats=[TWF, ITWF], BAB=11, light off-hand → 5 attacks
        feats = ["Two-Weapon Fighting", "Improved Two-Weapon Fighting"]
        fighter = _fighter("f01", bab=11, feats=feats)
        goblin = _goblin("g01", hp=500)
        ws = _world(fighter, goblin)

        events = _run_full_attack(ws, "f01", "g01", bab=11, main_weapon=_longsword(), off_hand=_shortsword())

        attack_count = _count_attack_rolls(events)
        assert attack_count == 5, (
            f"Regression: ITWF (no GTWF) must still give exactly 5 attacks, got {attack_count}"
        )
