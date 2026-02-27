"""ENGINE-SMITE-USES Gate -- WO-ENGINE-SMITE-USES-001: Smite Evil uses progression fix (8 tests).

Gate: ENGINE-SMITE-USES
Tests: SMITE-001 through SMITE-008
WO: WO-ENGINE-SMITE-USES-001 (Batch U WO3)
Source finding: FINDING-AUDIT-SMITE-USES-001 (AUDIT-WO-004, HIGH)

PHB p.44 (Table 3-4): "once per day for every five paladin levels she attains"
  — interpreted as: 1/day at L1, +1 at L6, L11, L16 (max 4/day at L20 per PHB parenthetical).
  — "to a maximum of four times per day at 20th level" (PHB p.44, explicit cap).

Prior bug: unlock at L1/5/8/10/12 (1–9 levels early per tier).
Fix: unlock at L1/6/11/16. L20 cap = 4/day per PHB text.
"""

from aidm.chargen.builder import build_character
from aidm.schemas.entity_fields import EF


_ABILITY_BASE = {"str": 14, "dex": 12, "con": 12, "int": 10, "wis": 12, "cha": 14}


def _paladin(level):
    return build_character("human", "paladin", level=level, ability_overrides=_ABILITY_BASE)


# ---------------------------------------------------------------------------
# SMITE-001: L1 → 1/day (unchanged from prior behavior — baseline correct)
# ---------------------------------------------------------------------------

def test_smite001_l1_one_use():
    """SMITE-001: Paladin L1 → 1 smite use/day."""
    entity = _paladin(1)
    assert entity[EF.SMITE_USES_REMAINING] == 1, (
        f"L1 paladin should have 1 smite use, got {entity[EF.SMITE_USES_REMAINING]}"
    )


# ---------------------------------------------------------------------------
# SMITE-002: L5 → 1/day (old code gave 2 — regression guard for fix)
# ---------------------------------------------------------------------------

def test_smite002_l5_still_one_use():
    """SMITE-002: Paladin L5 → 1 smite use/day (old buggy code gave 2 at L5)."""
    entity = _paladin(5)
    assert entity[EF.SMITE_USES_REMAINING] == 1, (
        f"L5 paladin should have 1 smite use (2nd unlocks at L6), got {entity[EF.SMITE_USES_REMAINING]}"
    )


# ---------------------------------------------------------------------------
# SMITE-003: L6 → 2/day (first new unlock at correct level)
# ---------------------------------------------------------------------------

def test_smite003_l6_two_uses():
    """SMITE-003: Paladin L6 → 2 smite uses/day (first additional use per PHB Table 3-4)."""
    entity = _paladin(6)
    assert entity[EF.SMITE_USES_REMAINING] == 2, (
        f"L6 paladin should have 2 smite uses, got {entity[EF.SMITE_USES_REMAINING]}"
    )


# ---------------------------------------------------------------------------
# SMITE-004: L10 → 2/day (old buggy code gave 4)
# ---------------------------------------------------------------------------

def test_smite004_l10_still_two_uses():
    """SMITE-004: Paladin L10 → 2 smite uses/day (3rd use unlocks at L11, not L10)."""
    entity = _paladin(10)
    assert entity[EF.SMITE_USES_REMAINING] == 2, (
        f"L10 paladin should have 2 smite uses, got {entity[EF.SMITE_USES_REMAINING]}"
    )


# ---------------------------------------------------------------------------
# SMITE-005: L11 → 3/day
# ---------------------------------------------------------------------------

def test_smite005_l11_three_uses():
    """SMITE-005: Paladin L11 → 3 smite uses/day."""
    entity = _paladin(11)
    assert entity[EF.SMITE_USES_REMAINING] == 3, (
        f"L11 paladin should have 3 smite uses, got {entity[EF.SMITE_USES_REMAINING]}"
    )


# ---------------------------------------------------------------------------
# SMITE-006: L15 → 3/day (regression guard — 4th use not yet)
# ---------------------------------------------------------------------------

def test_smite006_l15_still_three_uses():
    """SMITE-006: Paladin L15 → 3 smite uses/day (4th use unlocks at L16)."""
    entity = _paladin(15)
    assert entity[EF.SMITE_USES_REMAINING] == 3, (
        f"L15 paladin should have 3 smite uses, got {entity[EF.SMITE_USES_REMAINING]}"
    )


# ---------------------------------------------------------------------------
# SMITE-007: L16 → 4/day
# ---------------------------------------------------------------------------

def test_smite007_l16_four_uses():
    """SMITE-007: Paladin L16 → 4 smite uses/day."""
    entity = _paladin(16)
    assert entity[EF.SMITE_USES_REMAINING] == 4, (
        f"L16 paladin should have 4 smite uses, got {entity[EF.SMITE_USES_REMAINING]}"
    )


# ---------------------------------------------------------------------------
# SMITE-008: L20 → 4/day (cap per PHB p.44: "maximum of four times per day at 20th level")
# ---------------------------------------------------------------------------

def test_smite008_l20_four_uses_cap():
    """SMITE-008: Paladin L20 → 4 smite uses/day.

    PHB p.44 explicit cap: "to a maximum of four times per day at 20th level".
    The 5th use would require L21 which is beyond the class table.
    Implementation: 4 smite markers at L1/L6/L11/L16 — no 5th marker in table.
    """
    entity = _paladin(20)
    assert entity[EF.SMITE_USES_REMAINING] == 4, (
        f"L20 paladin should have 4 smite uses (PHB cap), got {entity[EF.SMITE_USES_REMAINING]}"
    )
