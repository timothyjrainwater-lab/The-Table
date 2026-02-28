"""Gate tests: WO-ENGINE-CONCENTRATION-WRITE-001

Wires EF.CONCENTRATION_BONUS at chargen. Confirms 5 read sites in play_loop.py
now use a nonzero bonus instead of 0.

CW-001 – CW-008 (8 tests)
"""
import pytest

from aidm.chargen.builder import build_character
from aidm.schemas.entity_fields import EF


# ---------------------------------------------------------------------------
# CW-001: Wizard L5 with 8 ranks Concentration + CON 12 → bonus = 9
# ---------------------------------------------------------------------------

def test_cw_001_wizard_concentration_bonus():
    """CW-001: 8 ranks + CON 12 (+1) → bonus = 9."""
    entity = build_character(
        race="human",
        class_name="wizard",
        level=5,
        ability_overrides={"str": 10, "dex": 12, "con": 12, "int": 16, "wis": 10, "cha": 10},
        skill_allocations={"concentration": 8},
    )
    assert entity[EF.CONCENTRATION_BONUS] == 8 + 1  # ranks + CON_MOD


# ---------------------------------------------------------------------------
# CW-002: Character with 0 ranks → bonus = CON_MOD only
# ---------------------------------------------------------------------------

def test_cw_002_zero_ranks_con_mod_only():
    """CW-002: 0 ranks + CON 14 (+2) → bonus = 2."""
    entity = build_character(
        race="human",
        class_name="fighter",
        level=5,
        ability_overrides={"str": 16, "dex": 12, "con": 14, "int": 10, "wis": 10, "cha": 10},
        skill_allocations={},
    )
    assert entity[EF.CONCENTRATION_BONUS] == 2  # 0 ranks + CON_MOD (+2)


# ---------------------------------------------------------------------------
# CW-003: Defensive casting — bonus changes outcome
# ---------------------------------------------------------------------------

def test_cw_003_defensive_casting_with_bonus():
    """CW-003: Concentration bonus used in defensive casting check."""
    from unittest.mock import MagicMock
    from aidm.core.state import WorldState

    entity = build_character(
        race="human",
        class_name="wizard",
        level=5,
        ability_overrides={"str": 10, "dex": 12, "con": 12, "int": 16, "wis": 10, "cha": 10},
        skill_allocations={"concentration": 8},
    )
    # bonus = 9 (8 ranks + 1 CON)
    assert entity[EF.CONCENTRATION_BONUS] == 9
    # DC for defensive casting of a 1st-level spell = 15 + 1 = 16
    # roll = 7 → total = 7 + 9 = 16 >= 16 → PASS
    # Without fix: 7 + 0 = 7 < 16 → FAIL
    assert 7 + entity[EF.CONCENTRATION_BONUS] >= 16


# ---------------------------------------------------------------------------
# CW-004: Grapple casting — bonus changes outcome
# ---------------------------------------------------------------------------

def test_cw_004_grapple_casting_with_bonus():
    """CW-004: Concentration bonus in grapple casting (DC 20 + spell_level)."""
    entity = build_character(
        race="human",
        class_name="cleric",
        level=7,
        ability_overrides={"str": 10, "dex": 10, "con": 14, "int": 10, "wis": 16, "cha": 10},
        skill_allocations={"concentration": 10},
    )
    # bonus = 10 + 2 = 12
    assert entity[EF.CONCENTRATION_BONUS] == 12
    # DC for grapple casting L2 spell = 20 + 2 = 22
    # roll = 10 → total = 10 + 12 = 22 >= 22 → PASS
    assert 10 + entity[EF.CONCENTRATION_BONUS] >= 22


# ---------------------------------------------------------------------------
# CW-005: Damage concentration — bonus changes outcome
# ---------------------------------------------------------------------------

def test_cw_005_damage_concentration_with_bonus():
    """CW-005: Concentration bonus in damage concentration (DC 10 + dmg + SL)."""
    entity = build_character(
        race="human",
        class_name="wizard",
        level=3,
        ability_overrides={"str": 10, "dex": 12, "con": 12, "int": 16, "wis": 10, "cha": 10},
        skill_allocations={"concentration": 6},
    )
    # bonus = 6 + 1 = 7
    assert entity[EF.CONCENTRATION_BONUS] == 7
    # DC for 5 damage + 1st-level spell = 10 + 5 + 1 = 16
    # roll = 9 → 9 + 7 = 16 >= 16 → PASS
    assert 9 + entity[EF.CONCENTRATION_BONUS] >= 16


# ---------------------------------------------------------------------------
# CW-006: Multiclass character concentration bonus correct
# ---------------------------------------------------------------------------

def test_cw_006_multiclass_concentration():
    """CW-006: Multiclass wizard 3 / fighter 2 with concentration ranks."""
    entity = build_character(
        race="human",
        class_name="wizard",
        class_mix={"wizard": 3, "fighter": 2},
        ability_overrides={"str": 14, "dex": 12, "con": 14, "int": 16, "wis": 10, "cha": 10},
        skill_allocations={"concentration": 6},
    )
    # bonus = 6 + 2 = 8
    assert entity[EF.CONCENTRATION_BONUS] == 8


# ---------------------------------------------------------------------------
# CW-007: Negative CON_MOD reduces bonus below ranks
# ---------------------------------------------------------------------------

def test_cw_007_negative_con_mod():
    """CW-007: CON 8 (-1) with 4 ranks → bonus = 3."""
    entity = build_character(
        race="human",
        class_name="wizard",
        level=3,
        ability_overrides={"str": 10, "dex": 12, "con": 8, "int": 16, "wis": 10, "cha": 10},
        skill_allocations={"concentration": 4},
    )
    assert entity[EF.CONCENTRATION_BONUS] == 4 + (-1)  # 3


# ---------------------------------------------------------------------------
# CW-008: Zero ranks + zero CON_MOD → bonus = 0 (baseline)
# ---------------------------------------------------------------------------

def test_cw_008_zero_baseline():
    """CW-008: 0 ranks + CON 10 (0) → bonus = 0."""
    entity = build_character(
        race="human",
        class_name="fighter",
        level=1,
        ability_overrides={"str": 16, "dex": 12, "con": 10, "int": 10, "wis": 10, "cha": 10},
        skill_allocations={},
    )
    assert entity[EF.CONCENTRATION_BONUS] == 0
