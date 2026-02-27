"""Gate tests for WO-CHARGEN-POOL-INIT-001 — Class feature pool initialization.

Tests: CPI-01 through CPI-10
Covers smite_uses_remaining, lay_on_hands_pool, lay_on_hands_used,
bardic_music_uses_remaining, and wild_shape_uses_remaining.
"""

import pytest

from aidm.chargen.builder import build_character
from aidm.schemas.entity_fields import EF


# ---------------------------------------------------------------------------
# CPI-01: Paladin L1 — smite_uses_remaining initialized (1 smite at L1)
# ---------------------------------------------------------------------------

def test_cpi_01_paladin_l1_smite_initialized():
    """CPI-01: Paladin L1 — SMITE_USES_REMAINING == 1."""
    entity = build_character(
        "human", "paladin", level=1,
        ability_overrides={"str": 14, "dex": 12, "con": 12, "int": 10, "wis": 12, "cha": 14},
    )
    assert EF.SMITE_USES_REMAINING in entity, "SMITE_USES_REMAINING must be set at L1 paladin"
    assert entity[EF.SMITE_USES_REMAINING] == 1


# ---------------------------------------------------------------------------
# CPI-02: Paladin L5 — smite_uses_remaining == 1 (second use unlocks at L6, not L5)
# ---------------------------------------------------------------------------

def test_cpi_02_paladin_l5_smite_one():
    """CPI-02: Paladin L5 — SMITE_USES_REMAINING == 1 (smite_evil_2_per_day now at L6 per PHB p.44)."""
    entity = build_character(
        "human", "paladin", level=5,
        ability_overrides={"str": 14, "dex": 12, "con": 12, "int": 10, "wis": 12, "cha": 14},
    )
    assert entity[EF.SMITE_USES_REMAINING] == 1


# ---------------------------------------------------------------------------
# CPI-03: Paladin L10 — smite_uses_remaining == 2
# ---------------------------------------------------------------------------

def test_cpi_03_paladin_l10_smite_two():
    """CPI-03: Paladin L10 — SMITE_USES_REMAINING == 2 (smite at L1, L6; L11 not yet reached)."""
    entity = build_character(
        "human", "paladin", level=10,
        ability_overrides={"str": 14, "dex": 12, "con": 12, "int": 10, "wis": 12, "cha": 14},
    )
    # Smite markers at levels 1, 6 only (L11=3rd not yet reached at L10)
    assert entity[EF.SMITE_USES_REMAINING] == 2


# ---------------------------------------------------------------------------
# CPI-04: Paladin L2 positive CHA — lay_on_hands_pool > 0
# ---------------------------------------------------------------------------

def test_cpi_04_paladin_l2_positive_cha_lay_on_hands():
    """CPI-04: Paladin L2, CHA 14 (mod +2) — LAY_ON_HANDS_POOL > 0."""
    entity = build_character(
        "human", "paladin", level=2,
        ability_overrides={"str": 14, "dex": 12, "con": 12, "int": 10, "wis": 12, "cha": 14},
    )
    assert EF.LAY_ON_HANDS_POOL in entity, "LAY_ON_HANDS_POOL must be set at L2 paladin"
    assert entity[EF.LAY_ON_HANDS_POOL] > 0
    assert entity[EF.LAY_ON_HANDS_USED] == 0


# ---------------------------------------------------------------------------
# CPI-05: Paladin L2 CHA_mod=0 — lay_on_hands_pool == 0
# ---------------------------------------------------------------------------

def test_cpi_05_paladin_l2_cha10_lay_on_hands_zero():
    """CPI-05: Paladin L2, CHA 10 (mod 0) — LAY_ON_HANDS_POOL == 0 (PHB: pool = pal_lvl × cha_mod, min 0)."""
    entity = build_character(
        "human", "paladin", level=2,
        ability_overrides={"str": 14, "dex": 12, "con": 12, "int": 10, "wis": 12, "cha": 10},
    )
    assert EF.LAY_ON_HANDS_POOL in entity
    assert entity[EF.LAY_ON_HANDS_POOL] == 0, (
        "Paladin with CHA mod 0 must have LAY_ON_HANDS_POOL == 0 (PHB p.44)"
    )


# ---------------------------------------------------------------------------
# CPI-06: Bard L5 — bardic_music_uses_remaining == bard_level + cha_mod
# ---------------------------------------------------------------------------

def test_cpi_06_bard_l5_bardic_music_formula():
    """CPI-06: Bard L5, CHA 14 (mod +2) — BARDIC_MUSIC_USES_REMAINING == 7."""
    entity = build_character(
        "human", "bard", level=5,
        ability_overrides={"str": 10, "dex": 12, "con": 10, "int": 12, "wis": 10, "cha": 14},
    )
    assert EF.BARDIC_MUSIC_USES_REMAINING in entity, (
        "BARDIC_MUSIC_USES_REMAINING must be set at L5 bard"
    )
    # bard_level=5, cha_mod=+2 → max(1, 5+2) = 7
    assert entity[EF.BARDIC_MUSIC_USES_REMAINING] == 7


# ---------------------------------------------------------------------------
# CPI-07: Bard L1 negative CHA — bardic_music_uses_remaining == 1 (min 1)
# ---------------------------------------------------------------------------

def test_cpi_07_bard_l1_negative_cha_bardic_music_min():
    """CPI-07: Bard L1, CHA 8 (mod -1) — BARDIC_MUSIC_USES_REMAINING == 1 (minimum enforced)."""
    entity = build_character(
        "human", "bard", level=1,
        ability_overrides={"str": 10, "dex": 12, "con": 10, "int": 12, "wis": 10, "cha": 8},
    )
    # bard_level=1, cha_mod=-1 → max(1, 1+(-1)) = max(1, 0) = 1
    assert entity[EF.BARDIC_MUSIC_USES_REMAINING] == 1


# ---------------------------------------------------------------------------
# CPI-08: Druid L5 — wild_shape_uses_remaining == 1
# ---------------------------------------------------------------------------

def test_cpi_08_druid_l5_wild_shape_one():
    """CPI-08: Druid L5 — WILD_SHAPE_USES_REMAINING == 1 (first use unlocks at L5)."""
    entity = build_character(
        "human", "druid", level=5,
        ability_overrides={"str": 10, "dex": 12, "con": 10, "int": 10, "wis": 16, "cha": 10},
    )
    assert EF.WILD_SHAPE_USES_REMAINING in entity, (
        "WILD_SHAPE_USES_REMAINING must be set at L5 druid"
    )
    assert entity[EF.WILD_SHAPE_USES_REMAINING] == 1


# ---------------------------------------------------------------------------
# CPI-09: Druid L7 — wild_shape_uses_remaining == 2
# ---------------------------------------------------------------------------

def test_cpi_09_druid_l7_wild_shape_two():
    """CPI-09: Druid L7 — WILD_SHAPE_USES_REMAINING == 2."""
    entity = build_character(
        "human", "druid", level=7,
        ability_overrides={"str": 10, "dex": 12, "con": 10, "int": 10, "wis": 16, "cha": 10},
    )
    # 1 + (7-4)//2 = 1 + 1 = 2
    assert entity[EF.WILD_SHAPE_USES_REMAINING] == 2


# ---------------------------------------------------------------------------
# CPI-10: Fighter — none of the pool fields present
# ---------------------------------------------------------------------------

def test_cpi_10_fighter_no_pool_fields():
    """CPI-10: Fighter L10 — pool fields must NOT be set (fighter has none of these features)."""
    entity = build_character(
        "human", "fighter", level=10,
        ability_overrides={"str": 16, "dex": 12, "con": 14, "int": 10, "wis": 10, "cha": 10},
    )
    assert EF.SMITE_USES_REMAINING not in entity
    assert EF.LAY_ON_HANDS_POOL not in entity
    assert EF.BARDIC_MUSIC_USES_REMAINING not in entity
    assert EF.WILD_SHAPE_USES_REMAINING not in entity
