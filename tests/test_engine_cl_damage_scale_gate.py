"""Gate tests for WO-ENGINE-CL-DAMAGE-SCALE-001.

CDS-001..008 — SpellDefinition.effective_damage_dice() + fireball/lightning_bolt CL scaling.
PHB p.231 (fireball), PHB p.243 (lightning bolt).
"""
import pytest
from aidm.core.spell_resolver import SpellDefinition, SpellTarget, SpellEffect
from aidm.data.spell_definitions import SPELL_REGISTRY


def _make_cl_spell(damage_dice_per_cl: str, max_damage_cl: int = 0) -> SpellDefinition:
    return SpellDefinition(
        spell_id="test_cl_spell",
        name="Test CL Spell",
        level=3,
        school="evocation",
        target_type=SpellTarget.AREA,
        range_ft=400,
        damage_dice_per_cl=damage_dice_per_cl,
        max_damage_cl=max_damage_cl,
    )


def _make_static_spell(damage_dice: str) -> SpellDefinition:
    return SpellDefinition(
        spell_id="test_static",
        name="Test Static",
        level=2,
        school="evocation",
        target_type=SpellTarget.SINGLE,
        range_ft=0,
        damage_dice=damage_dice,
    )


# ---------------------------------------------------------------------------
# CDS-001: effective_damage_dice() at CL5 with d6/CL max 10 → "5d6"
# ---------------------------------------------------------------------------
def test_cds_001_effective_damage_dice_cl5():
    spell = _make_cl_spell("d6", max_damage_cl=10)
    result = spell.effective_damage_dice(5)
    assert result == "5d6", f"expected '5d6' got {result!r}"


# ---------------------------------------------------------------------------
# CDS-002: effective_damage_dice() at CL10 → "10d6" (cap)
# ---------------------------------------------------------------------------
def test_cds_002_effective_damage_dice_cl10_cap():
    spell = _make_cl_spell("d6", max_damage_cl=10)
    result = spell.effective_damage_dice(10)
    assert result == "10d6", f"expected '10d6' got {result!r}"


# ---------------------------------------------------------------------------
# CDS-003: effective_damage_dice() at CL15 → "10d6" (still capped at 10)
# ---------------------------------------------------------------------------
def test_cds_003_effective_damage_dice_cl15_still_capped():
    spell = _make_cl_spell("d6", max_damage_cl=10)
    result = spell.effective_damage_dice(15)
    assert result == "10d6", f"expected '10d6' got {result!r}"


# ---------------------------------------------------------------------------
# CDS-004: static damage_dice — effective_damage_dice() ignores CL
# ---------------------------------------------------------------------------
def test_cds_004_static_damage_dice_ignores_cl():
    spell = _make_static_spell("3d6")
    assert spell.effective_damage_dice(1) == "3d6"
    assert spell.effective_damage_dice(10) == "3d6"
    assert spell.effective_damage_dice(20) == "3d6"


# ---------------------------------------------------------------------------
# CDS-005: SPELL_REGISTRY fireball at CL5 → effective_damage_dice = "5d6"
# ---------------------------------------------------------------------------
def test_cds_005_fireball_registry_cl5():
    fireball = SPELL_REGISTRY["fireball"]
    result = fireball.effective_damage_dice(5)
    assert result == "5d6", f"expected '5d6' got {result!r}"
    # confirm static damage_dice is cleared
    assert fireball.damage_dice is None, "fireball.damage_dice should be None (CL-scaled)"


# ---------------------------------------------------------------------------
# CDS-006: SPELL_REGISTRY lightning_bolt at CL3 → "3d6"
# ---------------------------------------------------------------------------
def test_cds_006_lightning_bolt_registry_cl3():
    lb = SPELL_REGISTRY["lightning_bolt"]
    result = lb.effective_damage_dice(3)
    assert result == "3d6", f"expected '3d6' got {result!r}"


# ---------------------------------------------------------------------------
# CDS-007: fireball at CL10 → "10d6"
# ---------------------------------------------------------------------------
def test_cds_007_fireball_cl10():
    fireball = SPELL_REGISTRY["fireball"]
    result = fireball.effective_damage_dice(10)
    assert result == "10d6", f"expected '10d6' got {result!r}"


# ---------------------------------------------------------------------------
# CDS-008: fireball at CL12 → "10d6" (cap enforced)
# ---------------------------------------------------------------------------
def test_cds_008_fireball_cl12_cap():
    fireball = SPELL_REGISTRY["fireball"]
    result = fireball.effective_damage_dice(12)
    assert result == "10d6", f"expected '10d6' (cap) got {result!r}"
    assert fireball.max_damage_cl == 10, "fireball.max_damage_cl should be 10"
    assert fireball.damage_dice_per_cl == "d6"
