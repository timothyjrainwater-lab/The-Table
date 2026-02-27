"""Gate tests: WO-ENGINE-BARBARIAN-DR-001

ENGINE-BARBARIAN-DR: Barbarian gains DR/— starting at level 7, scaling by 1
every 3 levels. DR system reads EF.DAMAGE_REDUCTIONS list.

BDR-001 – BDR-008 (8 tests)
"""
import pytest
from aidm.chargen.builder import build_character
from aidm.schemas.entity_fields import EF
from aidm.core.state import WorldState
from aidm.core.damage_reduction import get_applicable_dr


def _get_dash_dr(entity):
    """Return the DR/— amount from entity, or 0 if absent."""
    for dr in entity.get(EF.DAMAGE_REDUCTIONS, []):
        if dr.get("bypass") == "-":
            return dr["amount"]
    return 0


# ---------------------------------------------------------------------------
# BDR-001 – BDR-005: Scaling thresholds
# ---------------------------------------------------------------------------

def test_bdr_001_level_7_dr_1():
    """BDR-001: Barbarian level 7 → DR 1/—"""
    entity = build_character("human", "barbarian", level=7)
    assert _get_dash_dr(entity) == 1


def test_bdr_002_level_10_dr_2():
    """BDR-002: Barbarian level 10 → DR 2/—"""
    entity = build_character("human", "barbarian", level=10)
    assert _get_dash_dr(entity) == 2


def test_bdr_003_level_13_dr_3():
    """BDR-003: Barbarian level 13 → DR 3/—"""
    entity = build_character("human", "barbarian", level=13)
    assert _get_dash_dr(entity) == 3


def test_bdr_004_level_16_dr_4():
    """BDR-004: Barbarian level 16 → DR 4/—"""
    entity = build_character("human", "barbarian", level=16)
    assert _get_dash_dr(entity) == 4


def test_bdr_005_level_19_dr_5():
    """BDR-005: Barbarian level 19 → DR 5/—"""
    entity = build_character("human", "barbarian", level=19)
    assert _get_dash_dr(entity) == 5


# ---------------------------------------------------------------------------
# BDR-006: Below threshold — no DR
# ---------------------------------------------------------------------------

def test_bdr_006_level_6_no_dr():
    """BDR-006: Barbarian level 6 → no DR/— set."""
    entity = build_character("human", "barbarian", level=6)
    assert _get_dash_dr(entity) == 0


# ---------------------------------------------------------------------------
# BDR-007: Non-barbarian — no barbarian DR
# ---------------------------------------------------------------------------

def test_bdr_007_fighter_no_barbarian_dr():
    """BDR-007: Fighter level 10 → no DR/— from barbarian progression."""
    entity = build_character("human", "fighter", level=10)
    assert _get_dash_dr(entity) == 0


# ---------------------------------------------------------------------------
# BDR-008: Integration smoke — DR system reduces physical damage
# ---------------------------------------------------------------------------

def test_bdr_008_dr_system_reduces_damage():
    """BDR-008: DR 1/— at level 7 — damage_reduction resolver reads entity correctly."""
    entity = build_character("human", "barbarian", level=7)
    assert _get_dash_dr(entity) == 1
    # Smoke: wire entity into WorldState and confirm resolver sees DR 1
    ws = WorldState(ruleset_version="RAW_3.5")
    ws.entities["barb"] = entity
    dr_amount = get_applicable_dr(
        ws,
        "barb",
        damage_type="slashing",
        is_magic_weapon=False,
        weapon_material="steel",
    )
    assert dr_amount == 1
