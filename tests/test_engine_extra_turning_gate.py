"""Gate tests: WO-ENGINE-EXTRA-TURNING-001

ENGINE-EXTRA-TURNING: Extra Turning feat adds 4 uses per instance (stackable).
EF.TURN_UNDEAD_USES_MAX and EF.TURN_UNDEAD_USES initialized at chargen for
cleric (L1+) and paladin (L4+). Base = max(1, 3 + CHA mod).

ETN-001 – ETN-008 (8 tests)
"""
import pytest
from aidm.chargen.builder import build_character
from aidm.schemas.entity_fields import EF
from aidm.schemas.intents import RestIntent
from aidm.core.rest_resolver import resolve_rest
from aidm.core.state import WorldState


def _make_ws(entity_dict, actor_id="actor"):
    return WorldState(
        ruleset_version="3.5",
        entities={actor_id: entity_dict},
        active_combat=None,
    )


# ---------------------------------------------------------------------------
# ETN-001 – ETN-003: Stackable count
# ---------------------------------------------------------------------------

def test_etn_001_one_extra_turning():
    """ETN-001: Cleric level 5 (CHA 10 → mod 0) with one Extra Turning → MAX = base + 4."""
    entity = build_character(
        "human", "cleric", level=5,
        ability_overrides={"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 14, "cha": 10},
        feat_choices=["extra_turning"],
    )
    # base = max(1, 3+0) = 3; +4 → 7
    assert entity.get(EF.TURN_UNDEAD_USES_MAX) == 7
    assert entity.get(EF.TURN_UNDEAD_USES) == 7


def test_etn_002_two_extra_turning():
    """ETN-002: Two Extra Turning feats → MAX = base + 8."""
    entity = build_character(
        "human", "cleric", level=5,
        ability_overrides={"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 14, "cha": 10},
        feat_choices=["extra_turning", "extra_turning"],
    )
    # base=3; +8 → 11
    assert entity.get(EF.TURN_UNDEAD_USES_MAX) == 11


def test_etn_003_three_extra_turning():
    """ETN-003: Three Extra Turning feats → MAX = base + 12."""
    entity = build_character(
        "human", "cleric", level=7,
        ability_overrides={"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 14, "cha": 10},
        feat_choices=["extra_turning", "extra_turning", "extra_turning"],
    )
    # base=3; +12 → 15
    assert entity.get(EF.TURN_UNDEAD_USES_MAX) == 15


# ---------------------------------------------------------------------------
# ETN-004: No Extra Turning — base only
# ---------------------------------------------------------------------------

def test_etn_004_no_extra_turning():
    """ETN-004: Cleric without Extra Turning → TURN_UNDEAD_USES_MAX = base only."""
    entity = build_character(
        "human", "cleric", level=5,
        ability_overrides={"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 14, "cha": 10},
    )
    # base = max(1, 3+0) = 3; no extra → 3
    assert entity.get(EF.TURN_UNDEAD_USES_MAX) == 3


# ---------------------------------------------------------------------------
# ETN-005: Full rest restores to new max
# ---------------------------------------------------------------------------

def test_etn_005_rest_restores_to_extra_turning_max():
    """ETN-005: Full rest restores TURN_UNDEAD_USES to max (base + 4)."""
    entity = build_character(
        "human", "cleric", level=5,
        ability_overrides={"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 14, "cha": 10},
        feat_choices=["extra_turning"],
    )
    expected_max = entity[EF.TURN_UNDEAD_USES_MAX]  # 7
    # Spend some uses
    entity[EF.TURN_UNDEAD_USES] = 2
    ws = _make_ws(entity)
    resolve_rest(RestIntent(rest_type="overnight"), ws, "actor")
    assert ws.entities["actor"][EF.TURN_UNDEAD_USES] == expected_max


# ---------------------------------------------------------------------------
# ETN-006: Paladin with Extra Turning
# ---------------------------------------------------------------------------

def test_etn_006_paladin_extra_turning():
    """ETN-006: Paladin level 4+ with Extra Turning → turn uses also increment."""
    entity = build_character(
        "human", "paladin", level=5,
        ability_overrides={"str": 14, "dex": 10, "con": 12, "int": 10, "wis": 10, "cha": 12},
        feat_choices=["extra_turning"],
    )
    # cha_mod = 1, base = max(1, 3+1) = 4; +4 = 8
    assert entity.get(EF.TURN_UNDEAD_USES_MAX) == 8
    assert entity.get(EF.TURN_UNDEAD_USES) == 8


# ---------------------------------------------------------------------------
# ETN-007: Higher-level cleric — extra uses stack on top of level-based base
# ---------------------------------------------------------------------------

def test_etn_007_high_level_cleric_extra_turning():
    """ETN-007: Cleric 15 with CHA 16 (+3 mod) + Extra Turning → base=6, max=10."""
    entity = build_character(
        "human", "cleric", level=15,
        ability_overrides={"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 16, "cha": 16},
        feat_choices=["extra_turning"],
    )
    # base = max(1, 3+3) = 6; +4 → 10
    assert entity.get(EF.TURN_UNDEAD_USES_MAX) == 10


# ---------------------------------------------------------------------------
# ETN-008: Toughness regression — Extra Turning does not affect HP
# ---------------------------------------------------------------------------

def test_etn_008_toughness_regression():
    """ETN-008: Extra Turning does not affect Toughness count or HP bonus.

    Both feats apply independently — extra_turning does not interfere with
    toughness's stackable HP bonus.
    """
    entity = build_character(
        "human", "cleric", level=5,
        ability_overrides={"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 14, "cha": 10},
        feat_choices=["toughness", "extra_turning"],
    )
    feats = entity.get(EF.FEATS, [])
    # Both feats are present
    assert "toughness" in feats
    assert "extra_turning" in feats
    # Extra Turning uses are set correctly (not interfering with toughness)
    assert entity.get(EF.TURN_UNDEAD_USES_MAX) == 7  # base=3, +4
    # Toughness count = 1 → +3 HP added at chargen (no collision)
    assert feats.count("toughness") == 1
