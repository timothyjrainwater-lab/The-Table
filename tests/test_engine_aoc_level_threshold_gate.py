"""Gate tests — ALT-AE-001 through ALT-AE-004
WO-AE-WO3: Aura of Courage level threshold fix.
PHB p.49: "Beginning at 3rd level, a paladin is immune to fear (magical or otherwise)."
Fix: builder.py — paladin level threshold changed from >= 2 to >= 3 at both single-class and multiclass paths.
"""

import pytest
from aidm.chargen.builder import build_character
from aidm.schemas.entity_fields import EF


def _paladin_entity(level: int) -> dict:
    return build_character(
        "human", "paladin",
        level=level,
        ability_overrides={"str": 14, "dex": 12, "con": 12, "int": 10, "wis": 14, "cha": 16},
    )


def test_alt_ae_001_paladin_l2_no_fear_immunity():
    """ALT-AE-001: Paladin level 2 does NOT have fear immunity (AoC not yet granted at L2)."""
    entity = _paladin_entity(level=2)
    assert not entity.get(EF.FEAR_IMMUNE, False), (
        f"Paladin L2 should NOT have fear immunity (AoC granted at L3, not L2). "
        f"EF.FEAR_IMMUNE={entity.get(EF.FEAR_IMMUNE)}"
    )


def test_alt_ae_002_paladin_l3_has_fear_immunity():
    """ALT-AE-002: Paladin level 3 DOES have fear immunity (AoC granted at L3)."""
    entity = _paladin_entity(level=3)
    assert entity.get(EF.FEAR_IMMUNE, False) is True, (
        f"Paladin L3 should have fear immunity (PHB p.49). "
        f"EF.FEAR_IMMUNE={entity.get(EF.FEAR_IMMUNE)}"
    )


def test_alt_ae_003_paladin_l1_no_fear_immunity():
    """ALT-AE-003: Paladin level 1 does NOT have fear immunity."""
    entity = _paladin_entity(level=1)
    assert not entity.get(EF.FEAR_IMMUNE, False), (
        f"Paladin L1 should not have fear immunity. EF.FEAR_IMMUNE={entity.get(EF.FEAR_IMMUNE)}"
    )


def test_alt_ae_004_paladin_l5_has_fear_immunity():
    """ALT-AE-004: Paladin level 5 DOES have fear immunity (L3+ threshold maintained)."""
    entity = _paladin_entity(level=5)
    assert entity.get(EF.FEAR_IMMUNE, False) is True, (
        f"Paladin L5 should have fear immunity. EF.FEAR_IMMUNE={entity.get(EF.FEAR_IMMUNE)}"
    )
