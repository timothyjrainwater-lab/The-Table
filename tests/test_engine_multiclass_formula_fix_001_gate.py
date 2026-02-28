"""Gate tests for WO1 — ENGINE-MULTICLASS-FORMULA-FIX-001.

8 tests: MSF-001..MSF-008.
Fix: multiclass save/BAB max()→sum() at 4 sites in builder.py.
RAW: PHB p.22 — "add together the base save bonuses for each class"
     PHB p.22 — "add the base attack bonuses acquired for each class"

Progressions (0-indexed, level-1):
  GOOD_SAVE: [2, 3, 3, 4, 4, 5, ...]
  POOR_SAVE: [0, 0, 1, 1, 1, 2, ...]
  BAB full:          [1, 2, 3, 4, 5, 6, ...]
  BAB threequarters: [0, 1, 2, 3, 3, 4, ...]
  BAB half:          [0, 1, 1, 2, 2, 3, ...]

Class saves:
  Fighter: full BAB, good_saves=(fort,)
  Rogue: threequarters BAB, good_saves=(ref,)
  Wizard: half BAB, good_saves=(will,)
  Cleric: threequarters BAB, good_saves=(fort, will)
"""
import pytest

from aidm.chargen.builder import build_character, level_up
from aidm.schemas.entity_fields import EF


ALL_10 = {"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10}


def _build_multiclass(class_mix):
    """Build multiclass entity with all abilities at 10 (0 mods)."""
    total = sum(class_mix.values())
    primary = next(iter(class_mix))
    return build_character(
        race="human",
        class_name=primary,
        level=total,
        class_mix=class_mix,
        ability_overrides=ALL_10,
    )


# ── MSF-001: Fighter 3/Rogue 4 Fort save ──────────────────────────────────
class TestMSF001:
    """Fort = good(3)+poor(4)+CON = 3+1+0 = 4 (PHB p.22 sum rule)."""

    def test_fort_save_is_sum_not_max(self):
        entity = _build_multiclass({"fighter": 3, "rogue": 4})
        # sum: GOOD[2]=3 + POOR[3]=1 = 4
        # max (bug): max(3,1) = 3
        assert entity[EF.SAVE_FORT] == 4


# ── MSF-002: Fighter 3/Rogue 4 Ref save ───────────────────────────────────
class TestMSF002:
    """Ref = poor(3)+good(4)+DEX = 1+4+0 = 5 (PHB p.22 sum rule)."""

    def test_ref_save_is_sum_not_max(self):
        entity = _build_multiclass({"fighter": 3, "rogue": 4})
        # sum: POOR[2]=1 + GOOD[3]=4 = 5
        # max (bug): max(1,4) = 4
        assert entity[EF.SAVE_REF] == 5


# ── MSF-003: Fighter 3/Rogue 4 Will save ──────────────────────────────────
class TestMSF003:
    """Will = poor(3)+poor(4)+WIS = 1+1+0 = 2 (PHB p.22 sum rule)."""

    def test_will_save_is_sum_not_max(self):
        entity = _build_multiclass({"fighter": 3, "rogue": 4})
        # sum: POOR[2]=1 + POOR[3]=1 = 2
        # max (bug): max(1,1) = 1
        assert entity[EF.SAVE_WILL] == 2


# ── MSF-004: Single-class Rogue 4 unchanged ───────────────────────────────
class TestMSF004:
    """Single-class: sum([x]) == max([x]). Regression guard."""

    def test_rogue_4_saves_unaffected(self):
        entity = build_character(
            race="human",
            class_name="rogue",
            level=4,
            ability_overrides=ALL_10,
        )
        # Single-class uses _calculate_saves(), not _resolve_multiclass_stats()
        assert entity[EF.SAVE_FORT] == 1   # POOR[3] = 1
        assert entity[EF.SAVE_REF] == 4    # GOOD[3] = 4
        assert entity[EF.SAVE_WILL] == 1   # POOR[3] = 1
        assert entity[EF.BAB] == 3         # threequarters[3] = 3


# ── MSF-005: Fighter 3/Rogue 4 BAB ────────────────────────────────────────
class TestMSF005:
    """BAB = full(3)+threequarters(4) = 3+3 = 6 (PHB p.22 sum rule)."""

    def test_bab_is_sum_not_max(self):
        entity = _build_multiclass({"fighter": 3, "rogue": 4})
        # sum: full[2]=3 + threequarters[3]=3 = 6
        # max (bug): max(3,3) = 3
        assert entity[EF.BAB] == 6


# ── MSF-006: Wizard 5/Cleric 3 BAB ────────────────────────────────────────
class TestMSF006:
    """BAB = half(5)+threequarters(3) = 2+2 = 4 (PHB p.22 sum rule)."""

    def test_bab_is_sum_not_max(self):
        entity = _build_multiclass({"wizard": 5, "cleric": 3})
        # sum: half[4]=2 + threequarters[2]=2 = 4
        # max (bug): max(2,2) = 2
        assert entity[EF.BAB] == 4


# ── MSF-007: level_up path parity ─────────────────────────────────────────
class TestMSF007:
    """level_up(Fighter3→Rogue4) same BAB+saves as direct build."""

    def test_level_up_matches_build(self):
        # Path 1: direct multiclass build
        direct = _build_multiclass({"fighter": 3, "rogue": 4})

        # Path 2: build Fighter 3, simulate rogue 1-3 already applied,
        # then level_up to Rogue 4
        entity = build_character(
            race="human",
            class_name="fighter",
            level=3,
            ability_overrides=ALL_10,
        )
        entity[EF.CLASS_LEVELS] = {"fighter": 3, "rogue": 3}
        delta = level_up(entity, "rogue", 4)

        # Parity: both paths produce same values
        assert delta["bab"] == direct[EF.BAB]
        assert delta["saves"]["fort"] == direct[EF.SAVE_FORT]
        assert delta["saves"]["ref"] == direct[EF.SAVE_REF]
        assert delta["saves"]["will"] == direct[EF.SAVE_WILL]

        # Absolute values (proves sum, not max)
        assert delta["bab"] == 6           # full(3)+threequarters(4) = 3+3
        assert delta["saves"]["fort"] == 4  # GOOD(3)+POOR(4) = 3+1


# ── MSF-008: Fighter 6/Rogue 4 Fort (wider gap) ───────────────────────────
class TestMSF008:
    """Fort = good(6)+poor(4) = 5+1 = 6 (PHB p.22 sum rule)."""

    def test_fort_save_is_sum_not_max(self):
        entity = _build_multiclass({"fighter": 6, "rogue": 4})
        # sum: GOOD[5]=5 + POOR[3]=1 = 6
        # max (bug): max(5,1) = 5
        assert entity[EF.SAVE_FORT] == 6
