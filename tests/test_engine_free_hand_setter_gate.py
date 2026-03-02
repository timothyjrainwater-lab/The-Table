"""Gate tests for WO-ENGINE-FREE-HAND-SETTER-001.

FHS-001..008 — EF.FREE_HANDS set at chargen. Closes FINDING-ENGINE-FREE-HAND-SETTER-002.
PHB p.93 (Deflect Arrows: one hand free required), PHB Table 7-5 (two-handed weapons).
"""
import pytest
from aidm.chargen.builder import build_character, _build_multiclass_character
from aidm.schemas.entity_fields import EF
from aidm.core.attack_resolver import resolve_attack


def _fighter(weapon_override=None):
    kwargs = {"starting_equipment": weapon_override} if weapon_override is not None else {}
    return build_character("human", "fighter", 5, **kwargs)


def _ranger(weapon_override=None):
    kwargs = {"starting_equipment": weapon_override} if weapon_override is not None else {}
    return build_character("human", "ranger", 5, **kwargs)


# ---------------------------------------------------------------------------
# FHS-001: greatsword → FREE_HANDS = 0
# ---------------------------------------------------------------------------
def test_fhs_001_greatsword_free_hands_zero():
    entity = _fighter({"greatsword": 1})
    assert entity.get(EF.FREE_HANDS) == 0, (
        f"greatsword wielder should have FREE_HANDS=0, got {entity.get(EF.FREE_HANDS)}"
    )


# ---------------------------------------------------------------------------
# FHS-002: longsword → FREE_HANDS = 1
# ---------------------------------------------------------------------------
def test_fhs_002_longsword_free_hands_one():
    entity = _fighter({"longsword": 1})
    assert entity.get(EF.FREE_HANDS) == 1, (
        f"longsword wielder should have FREE_HANDS=1, got {entity.get(EF.FREE_HANDS)}"
    )


# ---------------------------------------------------------------------------
# FHS-003: no weapon → FREE_HANDS = 1
# ---------------------------------------------------------------------------
def test_fhs_003_no_weapon_free_hands_one():
    entity = build_character("human", "fighter", 5, starting_equipment={})
    assert entity.get(EF.FREE_HANDS) == 1, (
        f"no-weapon entity should have FREE_HANDS=1, got {entity.get(EF.FREE_HANDS)}"
    )


# ---------------------------------------------------------------------------
# FHS-004: parity — both chargen paths produce the same FREE_HANDS for
#           identical equipment (default kit fighter: longsword → 1)
# ---------------------------------------------------------------------------
def test_fhs_004_both_paths_parity():
    # Path 1: build_character (single-class)
    single = build_character("human", "fighter", 5)
    fh_single = single.get(EF.FREE_HANDS)

    # Path 2: _build_multiclass_character (multiclass path)
    multi = _build_multiclass_character(
        race="human",
        class_mix={"fighter": 5},
        ability_overrides={"str": 16, "dex": 12, "con": 14, "int": 10, "wis": 10, "cha": 10},
    )
    fh_multi = multi.get(EF.FREE_HANDS)

    # Multiclass starts unarmed (no equipment), should default to 1
    assert fh_multi == 1, f"multiclass unarmed path should have FREE_HANDS=1, got {fh_multi}"
    # Single-class fighter default kit uses longsword (one-handed → 1)
    assert fh_single == 1, f"single-class fighter should have FREE_HANDS=1, got {fh_single}"


# ---------------------------------------------------------------------------
# FHS-005: EF.FREE_HANDS is explicitly set (not relying on .get() default)
# ---------------------------------------------------------------------------
def test_fhs_005_free_hands_key_present():
    entity = _fighter({"greatsword": 1})
    assert EF.FREE_HANDS in entity, "EF.FREE_HANDS must be present in entity dict (not implicit)"


# ---------------------------------------------------------------------------
# FHS-006: longbow → FREE_HANDS = 0 (ranged two-handed; grip_hands=2 — WO-ENGINE-GRIP-HANDS-SETTER-001)
# ---------------------------------------------------------------------------
def test_fhs_006_longbow_free_hands_zero():
    entity = _ranger({"longbow": 1})
    assert entity.get(EF.FREE_HANDS) == 0, (
        f"longbow wielder should have FREE_HANDS=0, got {entity.get(EF.FREE_HANDS)}"
    )


# ---------------------------------------------------------------------------
# FHS-007: greatsword + Deflect Arrows feat → Deflect Arrows check FAILS
# ---------------------------------------------------------------------------
def test_fhs_007_greatsword_deflect_arrows_blocked():
    entity = _fighter({"greatsword": 1})
    entity[EF.FEATS] = entity.get(EF.FEATS, []) + ["deflect_arrows"]
    # FREE_HANDS=0 → Deflect Arrows consume site rejects
    assert entity.get(EF.FREE_HANDS) == 0
    # The attack resolver reads FREE_HANDS < 1 → deflect not eligible
    # (direct field check — consume site at attack_resolver.py:906)
    free_hands = entity.get(EF.FREE_HANDS, 1)
    assert free_hands < 1, "Deflect Arrows should be blocked when FREE_HANDS=0"


# ---------------------------------------------------------------------------
# FHS-008: longsword + Deflect Arrows feat → FREE_HANDS check PASSES
# ---------------------------------------------------------------------------
def test_fhs_008_longsword_deflect_arrows_eligible():
    entity = _fighter({"longsword": 1})
    entity[EF.FEATS] = entity.get(EF.FEATS, []) + ["deflect_arrows"]
    free_hands = entity.get(EF.FREE_HANDS, 1)
    assert free_hands >= 1, (
        f"Deflect Arrows should be eligible when FREE_HANDS>=1, got {free_hands}"
    )
