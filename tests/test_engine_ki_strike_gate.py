"""Gate tests: WO-ENGINE-KI-STRIKE-001

Ki Strike (PHB p.42):
- L4: unarmed treated as magic for DR bypass
- L10: unarmed treated as lawful for DR bypass
- L16: unarmed treated as adamantine for DR bypass

KIS-001 – KIS-008 (8 tests)
"""
import pytest

from aidm.core.damage_reduction import extract_weapon_bypass_flags, _weapon_bypasses_dr
from aidm.schemas.attack import Weapon
from aidm.schemas.entity_fields import EF


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _unarmed_weapon():
    """Natural weapon representing monk unarmed strike."""
    return Weapon(
        damage_dice="1d8",
        damage_bonus=0,
        damage_type="bludgeoning",
        weapon_type="natural",
        grip="one-handed",
    )


def _monk_entity(level=4):
    """Minimal monk entity with MONK_UNARMED_DICE set (identifies as monk unarmed)."""
    return {
        EF.CLASS_LEVELS: {"monk": level},
        EF.MONK_UNARMED_DICE: "1d8",
        EF.WEAPON: {
            "weapon_type": "natural",
            "damage_dice": "1d8",
            "damage_bonus": 0,
            "damage_type": "bludgeoning",
        },
    }


def _nonmonk_entity():
    """Non-monk entity with natural attack (no MONK_UNARMED_DICE)."""
    return {
        EF.CLASS_LEVELS: {"fighter": 5},
        EF.WEAPON: {
            "weapon_type": "natural",
            "damage_dice": "1d6",
            "damage_bonus": 0,
            "damage_type": "slashing",
        },
    }


# ---------------------------------------------------------------------------
# KIS-001: Monk L4 unarmed bypasses DR/magic
# ---------------------------------------------------------------------------

def test_kis_001_monk_l4_bypasses_dr_magic():
    """KIS-001: Monk L4 unarmed → Ki Strike (magic) bypasses DR/magic."""
    weapon = _unarmed_weapon()
    attacker = _monk_entity(level=4)
    is_magic, material, alignment, enh = extract_weapon_bypass_flags(weapon, attacker)
    assert is_magic is True, "Ki Strike L4: unarmed should count as magic"
    # Verify it actually bypasses DR/magic
    assert _weapon_bypasses_dr("magic", is_magic, material, alignment, enh) is True, \
        "DR/magic should be bypassed by Ki Strike magic"


# ---------------------------------------------------------------------------
# KIS-002: Monk L3 unarmed does NOT bypass DR/magic
# ---------------------------------------------------------------------------

def test_kis_002_monk_l3_no_ki_strike():
    """KIS-002: Monk L3 — Ki Strike not yet available."""
    weapon = _unarmed_weapon()
    attacker = _monk_entity(level=3)
    is_magic, material, alignment, enh = extract_weapon_bypass_flags(weapon, attacker)
    assert is_magic is False, "Monk L3: no Ki Strike yet"
    # DR/magic should NOT be bypassed
    assert _weapon_bypasses_dr("magic", is_magic, material, alignment, enh) is False, \
        "DR/magic should NOT be bypassed at L3"


# ---------------------------------------------------------------------------
# KIS-003: Monk L10 unarmed bypasses DR/lawful
# ---------------------------------------------------------------------------

def test_kis_003_monk_l10_bypasses_dr_lawful():
    """KIS-003: Monk L10 unarmed → Ki Strike (lawful) bypasses DR/lawful."""
    weapon = _unarmed_weapon()
    attacker = _monk_entity(level=10)
    is_magic, material, alignment, enh = extract_weapon_bypass_flags(weapon, attacker)
    assert is_magic is True
    assert alignment == "lawful", "Ki Strike L10: alignment should be lawful"
    # Verify it bypasses DR/lawful
    assert _weapon_bypasses_dr("lawful", is_magic, material, alignment, enh) is True, \
        "DR/lawful should be bypassed by Ki Strike lawful"


# ---------------------------------------------------------------------------
# KIS-004: Monk L9 unarmed does NOT bypass DR/lawful
# ---------------------------------------------------------------------------

def test_kis_004_monk_l9_no_lawful():
    """KIS-004: Monk L9 — Ki Strike (lawful) not yet available."""
    weapon = _unarmed_weapon()
    attacker = _monk_entity(level=9)
    is_magic, material, alignment, enh = extract_weapon_bypass_flags(weapon, attacker)
    assert is_magic is True, "Monk L9 has Ki Strike magic (L4+)"
    assert alignment == "none", "Monk L9: no lawful alignment yet"
    # DR/lawful should NOT be bypassed
    assert _weapon_bypasses_dr("lawful", is_magic, material, alignment, enh) is False, \
        "DR/lawful should NOT be bypassed at L9"


# ---------------------------------------------------------------------------
# KIS-005: Monk L16 unarmed bypasses DR/adamantine
# ---------------------------------------------------------------------------

def test_kis_005_monk_l16_bypasses_dr_adamantine():
    """KIS-005: Monk L16 unarmed → Ki Strike (adamantine) bypasses DR/adamantine."""
    weapon = _unarmed_weapon()
    attacker = _monk_entity(level=16)
    is_magic, material, alignment, enh = extract_weapon_bypass_flags(weapon, attacker)
    assert is_magic is True
    assert alignment == "lawful"
    assert material == "adamantine", "Ki Strike L16: material should be adamantine"
    # Verify it bypasses DR/adamantine
    assert _weapon_bypasses_dr("adamantine", is_magic, material, alignment, enh) is True, \
        "DR/adamantine should be bypassed by Ki Strike adamantine"


# ---------------------------------------------------------------------------
# KIS-006: Monk L15 unarmed does NOT bypass DR/adamantine
# ---------------------------------------------------------------------------

def test_kis_006_monk_l15_no_adamantine():
    """KIS-006: Monk L15 — Ki Strike (adamantine) not yet available."""
    weapon = _unarmed_weapon()
    attacker = _monk_entity(level=15)
    is_magic, material, alignment, enh = extract_weapon_bypass_flags(weapon, attacker)
    assert is_magic is True, "Monk L15 has Ki Strike magic (L4+)"
    assert alignment == "lawful", "Monk L15 has Ki Strike lawful (L10+)"
    assert material == "steel", "Monk L15: no adamantine yet"
    # DR/adamantine should NOT be bypassed
    assert _weapon_bypasses_dr("adamantine", is_magic, material, alignment, enh) is False, \
        "DR/adamantine should NOT be bypassed at L15"


# ---------------------------------------------------------------------------
# KIS-007: Non-monk natural attack does NOT get Ki Strike
# ---------------------------------------------------------------------------

def test_kis_007_nonmonk_natural_no_ki_strike():
    """KIS-007: Non-monk natural attack — no Ki Strike bypass."""
    weapon = _unarmed_weapon()
    attacker = _nonmonk_entity()
    is_magic, material, alignment, enh = extract_weapon_bypass_flags(weapon, attacker)
    assert is_magic is False, "Non-monk: natural attack is not magic"
    assert material == "steel"
    assert alignment == "none"


# ---------------------------------------------------------------------------
# KIS-008: Monk L16 vs DR/- — Ki Strike does NOT bypass
# ---------------------------------------------------------------------------

def test_kis_008_ki_strike_does_not_bypass_dr_dash():
    """KIS-008: DR/- cannot be bypassed even by Ki Strike (PHB p.42)."""
    weapon = _unarmed_weapon()
    attacker = _monk_entity(level=16)
    is_magic, material, alignment, enh = extract_weapon_bypass_flags(weapon, attacker)
    # Monk L16 has magic + lawful + adamantine
    assert is_magic is True
    # But DR/- is bypass="-" which cannot be bypassed
    assert _weapon_bypasses_dr("-", is_magic, material, alignment, enh) is False, \
        "DR/- cannot be bypassed by any weapon property including Ki Strike"
