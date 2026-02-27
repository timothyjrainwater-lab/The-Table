"""Gate tests: WO-ENGINE-MONK-UNARMED-PROGRESSION-001

ENGINE-MONK-UNARMED-PROGRESSION: Monk unarmed strike damage scales with level
(PHB Table 3-10, p.41). Stored in EF.MONK_UNARMED_DICE on the entity.

Level → Damage (Medium):
  1–3  → "1d6"
  4–7  → "1d8"
  8–11 → "1d10"
  12–15 → "2d6"
  16–19 → "2d8"
  20   → "2d10"

MUP-001 – MUP-008 (8 tests)
"""
from aidm.chargen.builder import build_character
from aidm.schemas.entity_fields import EF


# ---------------------------------------------------------------------------
# MUP-001 – MUP-006: Scaling table entries
# ---------------------------------------------------------------------------

def test_mup_001_level_1_1d6():
    """MUP-001: Monk level 1 → unarmed damage_dice = '1d6'."""
    entity = build_character("human", "monk", level=1)
    assert entity.get(EF.MONK_UNARMED_DICE) == "1d6"


def test_mup_002_level_4_1d8():
    """MUP-002: Monk level 4 → '1d8'."""
    entity = build_character("human", "monk", level=4)
    assert entity.get(EF.MONK_UNARMED_DICE) == "1d8"


def test_mup_003_level_8_1d10():
    """MUP-003: Monk level 8 → '1d10'."""
    entity = build_character("human", "monk", level=8)
    assert entity.get(EF.MONK_UNARMED_DICE) == "1d10"


def test_mup_004_level_12_2d6():
    """MUP-004: Monk level 12 → '2d6'."""
    entity = build_character("human", "monk", level=12)
    assert entity.get(EF.MONK_UNARMED_DICE) == "2d6"


def test_mup_005_level_16_2d8():
    """MUP-005: Monk level 16 → '2d8'."""
    entity = build_character("human", "monk", level=16)
    assert entity.get(EF.MONK_UNARMED_DICE) == "2d8"


def test_mup_006_level_20_2d10():
    """MUP-006: Monk level 20 → '2d10'."""
    entity = build_character("human", "monk", level=20)
    assert entity.get(EF.MONK_UNARMED_DICE) == "2d10"


# ---------------------------------------------------------------------------
# MUP-007: Non-monk — no unarmed dice field
# ---------------------------------------------------------------------------

def test_mup_007_non_monk_no_unarmed_dice():
    """MUP-007: Fighter level 12 → no monk unarmed progression applied."""
    entity = build_character("human", "fighter", level=12)
    assert EF.MONK_UNARMED_DICE not in entity


# ---------------------------------------------------------------------------
# MUP-008: Boundary — level 3 still "1d6", level 4 is "1d8"
# ---------------------------------------------------------------------------

def test_mup_008_level_3_still_1d6():
    """MUP-008: Monk level 3 → still '1d6' (level 4 triggers upgrade, not level 3)."""
    entity = build_character("human", "monk", level=3)
    assert entity.get(EF.MONK_UNARMED_DICE) == "1d6"
