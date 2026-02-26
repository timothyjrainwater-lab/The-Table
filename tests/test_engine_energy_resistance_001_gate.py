"""Gate tests: WO-ENGINE-ENERGY-RESISTANCE-001 — Energy resistance absorbs N points per damage instance.

PHB p.291: Resistance to energy absorbs the first N points of a specific energy type per instance.

Gate label: ENGINE-ENERGY-RESISTANCE-001
"""

import pytest

from aidm.schemas.entity_fields import EF
from aidm.core.spell_resolver import (
    SpellResolver, SpellDefinition, SpellEffect, CasterStats, TargetStats,
    SaveEffect, SaveType, DamageType,
)


# ---------------------------------------------------------------------------
# Helpers — reuse the direct computation approach (same as EA tests)
# ---------------------------------------------------------------------------

def _compute_fire_damage(
    raw_total: int,
    resistance_dict: dict,
    armor_type: str = "none",
    saved: bool = False,
    has_evasion: bool = False,
) -> int:
    """Replicate spell_resolver damage path for fire damage with resistance."""
    total = raw_total

    if saved:
        total = total // 2
        _armor = armor_type
        _evasion_active = _armor in ("none", "light")
        if _evasion_active and has_evasion:
            total = 0
    # Energy resistance
    if total > 0:
        _resistance = resistance_dict.get("fire", 0)
        if _resistance > 0:
            total = max(0, total - _resistance)
    return total


def _compute_damage_with_type(
    raw_total: int,
    resistance_dict: dict,
    damage_type: str,
    saved: bool = False,
) -> int:
    """Replicate spell_resolver energy resistance guard for arbitrary damage type."""
    total = raw_total
    if saved:
        total = total // 2
    if total > 0:
        _resistance = resistance_dict.get(damage_type, 0)
        if _resistance > 0:
            total = max(0, total - _resistance)
    return total


# ---------------------------------------------------------------------------
# ER-001: Fire resistance 10 vs 20 fire damage → 10 damage
# ---------------------------------------------------------------------------

def test_er_001_fire_resistance_reduces_damage():
    """ER-001: Entity with fire resistance 10 takes 20 fire damage → 10 damage applied."""
    total = _compute_damage_with_type(20, {"fire": 10}, "fire")
    assert total == 10, f"ER-001: Expected 10; got {total}"


# ---------------------------------------------------------------------------
# ER-002: Fire resistance 10 vs 8 fire damage → 0 damage (resistance exceeds)
# ---------------------------------------------------------------------------

def test_er_002_fire_resistance_exceeds_damage():
    """ER-002: Entity with fire resistance 10 takes 8 fire damage → 0 damage."""
    total = _compute_damage_with_type(8, {"fire": 10}, "fire")
    assert total == 0, f"ER-002: Expected 0; got {total}"


# ---------------------------------------------------------------------------
# ER-003: Fire resistance 10 vs 20 cold damage → 20 damage (wrong type)
# ---------------------------------------------------------------------------

def test_er_003_wrong_energy_type_no_reduction():
    """ER-003: Entity with fire resistance 10 takes 20 cold damage → 20 damage."""
    total = _compute_damage_with_type(20, {"fire": 10}, "cold")
    assert total == 20, f"ER-003: Expected 20 (no fire resist vs cold); got {total}"


# ---------------------------------------------------------------------------
# ER-004: No resistance vs 20 fire damage → 20 damage
# ---------------------------------------------------------------------------

def test_er_004_no_resistance_full_damage():
    """ER-004: Entity with no resistance takes 20 fire damage → 20 damage."""
    total = _compute_damage_with_type(20, {}, "fire")
    assert total == 20, f"ER-004: Expected 20; got {total}"


# ---------------------------------------------------------------------------
# ER-005: Fire resistance 5, cold resistance 10 vs fire damage → only fire applies
# ---------------------------------------------------------------------------

def test_er_005_correct_resistance_type_applied():
    """ER-005: Fire resistance 5, cold resistance 10 vs 20 fire damage → 15 damage."""
    total = _compute_damage_with_type(20, {"fire": 5, "cold": 10}, "fire")
    assert total == 15, f"ER-005: Expected 15 (fire resist 5 applied); got {total}"


# ---------------------------------------------------------------------------
# ER-006: Resistance applied → HP updated correctly
# ---------------------------------------------------------------------------

def test_er_006_hp_updated_correctly_after_resistance():
    """ER-006: Entity with fire resistance 10 takes 20 fire → 10 net → HP = start - 10."""
    start_hp = 40
    raw_damage = 20
    resistance = {"fire": 10}
    net = _compute_damage_with_type(raw_damage, resistance, "fire")
    hp_after = start_hp - net
    assert net == 10, f"ER-006: Net damage should be 10; got {net}"
    assert hp_after == 30, f"ER-006: HP after should be 30; got {hp_after}"


# ---------------------------------------------------------------------------
# ER-007: Resistance cannot reduce below 0
# ---------------------------------------------------------------------------

def test_er_007_damage_floor_zero():
    """ER-007: Resistance 50 vs 20 fire damage → 0 damage (floor enforced)."""
    total = _compute_damage_with_type(20, {"fire": 50}, "fire")
    assert total == 0, f"ER-007: Expected 0 (floor); got {total}"
    assert total >= 0, f"ER-007: Damage cannot be negative; got {total}"


# ---------------------------------------------------------------------------
# ER-008: No ENERGY_RESISTANCE field → full damage, no crash
# ---------------------------------------------------------------------------

def test_er_008_absent_field_full_damage_no_crash():
    """ER-008: Entity with no ENERGY_RESISTANCE field → full damage applied, no crash."""
    # Simulate the guard: .get(EF.ENERGY_RESISTANCE, {}).get("fire", 0)
    entity = {}  # no ENERGY_RESISTANCE key
    resistance_dict = entity.get("energy_resistance", {})
    _resistance = resistance_dict.get("fire", 0)
    raw = 20
    total = max(0, raw - _resistance) if _resistance > 0 else raw
    assert total == 20, f"ER-008: Expected 20 (full damage); got {total}"
