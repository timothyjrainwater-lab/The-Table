"""Damage Reduction resolver for WO-048.

Implements D&D 3.5e Damage Reduction (PHB p.291, DMG p.292-293):
- DR X/type reduces physical damage by X unless bypassed
- Multiple DR sources: best applicable DR wins (no stacking)
- DR does not reduce energy damage (fire, cold, acid, electricity, sonic)
- DR does not reduce force damage
- DR reduces damage to a minimum of 0

BYPASS TYPES (PHB p.291):
- "magic"       — Bypassed by magic weapons (+1 or better)
- "adamantine"  — Bypassed by adamantine weapons
- "cold_iron"   — Bypassed by cold iron weapons
- "silver"      — Bypassed by silver/alchemical silver weapons
- "good"        — Bypassed by good-aligned weapons
- "evil"        — Bypassed by evil-aligned weapons
- "lawful"      — Bypassed by lawful-aligned weapons
- "chaotic"     — Bypassed by chaotic-aligned weapons
- "epic"        — Bypassed by +6 or better weapons
- "-"           — Cannot be bypassed (e.g., barbarian DR/-)

ENTITY FORMAT:
  entity[EF.DAMAGE_REDUCTIONS] = [
      {"amount": 10, "bypass": "magic"},
      {"amount": 5, "bypass": "-"},
  ]

WEAPON FORMAT (optional enhancement fields):
  weapon.is_magic: bool (default False)
  weapon.material: str (default "steel")
  weapon.alignment: str (default "none")
  weapon.enhancement_bonus: int (default 0)

Since weapon schemas don't yet carry these fields, the resolver accepts
them as optional parameters and defaults to non-magic steel weapons.
"""

from typing import Any, Dict, List, Optional
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF


# Damage types that DR does NOT apply to (PHB p.291: DR only reduces
# "physical" damage — slashing, piercing, bludgeoning)
_ENERGY_DAMAGE_TYPES = frozenset({
    "fire", "cold", "acid", "electricity", "sonic",
    "force", "positive", "negative", "untyped",
})

# Physical damage types that DR applies to
_PHYSICAL_DAMAGE_TYPES = frozenset({
    "slashing", "piercing", "bludgeoning",
})


def get_applicable_dr(
    world_state: WorldState,
    defender_id: str,
    damage_type: str,
    is_magic_weapon: bool = False,
    weapon_material: str = "steel",
    weapon_alignment: str = "none",
    weapon_enhancement: int = 0,
) -> int:
    """Calculate the applicable Damage Reduction for an attack.

    Per PHB p.291: When multiple DR sources exist, use the best applicable
    DR (highest amount whose bypass is NOT satisfied by the weapon).

    Args:
        world_state: Current world state
        defender_id: Entity ID of the defender
        damage_type: Type of damage being dealt (e.g., "slashing", "fire")
        is_magic_weapon: Whether the weapon is magical (+1 or better)
        weapon_material: Material of the weapon ("steel", "adamantine", "cold_iron", "silver")
        weapon_alignment: Alignment of the weapon ("none", "good", "evil", "lawful", "chaotic")
        weapon_enhancement: Enhancement bonus of the weapon (0-5+)

    Returns:
        int: Amount of damage to reduce (0 if no applicable DR)
    """
    # DR does not apply to energy/force/untyped damage
    if damage_type in _ENERGY_DAMAGE_TYPES:
        return 0

    # DR only applies to physical damage
    if damage_type not in _PHYSICAL_DAMAGE_TYPES:
        return 0

    entity = world_state.entities.get(defender_id)
    if entity is None:
        return 0

    dr_list = entity.get(EF.DAMAGE_REDUCTIONS, [])
    if not dr_list:
        return 0

    # Magic weapons: +1 or better, or explicitly flagged
    effective_magic = is_magic_weapon or weapon_enhancement >= 1

    best_dr = 0

    for dr_entry in dr_list:
        amount = dr_entry.get("amount", 0)
        bypass = dr_entry.get("bypass", "-")

        if amount <= 0:
            continue

        # Check if weapon bypasses this DR
        if _weapon_bypasses_dr(bypass, effective_magic, weapon_material, weapon_alignment, weapon_enhancement):
            continue  # This DR is bypassed

        # This DR applies — track best
        if amount > best_dr:
            best_dr = amount

    return best_dr


def _weapon_bypasses_dr(
    bypass_type: str,
    is_magic: bool,
    material: str,
    alignment: str,
    enhancement: int,
) -> bool:
    """Check whether a weapon bypasses a specific DR type.

    Args:
        bypass_type: The DR bypass requirement (e.g., "magic", "adamantine")
        is_magic: Whether the weapon counts as magical
        material: Weapon material (e.g., "steel", "adamantine")
        alignment: Weapon alignment (e.g., "none", "good")
        enhancement: Weapon enhancement bonus

    Returns:
        True if the weapon bypasses this DR type
    """
    if bypass_type == "-":
        # DR/- cannot be bypassed by any weapon property
        return False

    if bypass_type == "magic":
        return is_magic

    if bypass_type == "adamantine":
        return material == "adamantine"

    if bypass_type == "cold_iron":
        return material == "cold_iron"

    if bypass_type == "silver":
        return material in ("silver", "alchemical_silver")

    if bypass_type == "epic":
        return enhancement >= 6

    # Alignment-based DR
    if bypass_type in ("good", "evil", "lawful", "chaotic"):
        return alignment == bypass_type

    # Unknown bypass type — fail-closed (DR applies)
    return False


def apply_dr_to_damage(
    damage_total: int,
    dr_amount: int,
) -> tuple:
    """Apply Damage Reduction to damage.

    PHB p.291: DR reduces damage to a minimum of 0.

    Args:
        damage_total: Total damage before DR
        dr_amount: Amount of DR to apply

    Returns:
        Tuple of (final_damage, damage_reduced)
    """
    if dr_amount <= 0 or damage_total <= 0:
        return damage_total, 0

    damage_reduced = min(dr_amount, damage_total)
    final_damage = damage_total - damage_reduced
    return final_damage, damage_reduced


def extract_weapon_bypass_flags(
    weapon: Any,
    attacker: dict,
) -> tuple:
    """Extract magic/material/alignment bypass flags from a Weapon or entity dict.

    Priority order:
    1. weapon.weapon_type == "natural" -> never magic
    2. attacker[EF.WEAPON] dict "tags" list: ["magic", "silver", ...]
    3. attacker[EF.WEAPON] dict "material" key: "adamantine", "cold_iron", etc.
    4. Default: non-magic steel, no alignment

    WO-ENGINE-DR-001

    Returns:
        (is_magic: bool, material: str, alignment: str, enhancement: int)
    """
    # Natural attacks: never magic
    weapon_type = getattr(weapon, "weapon_type", "one-handed")
    if weapon_type == "natural":
        return (False, "steel", "none", 0)

    entity_weapon = attacker.get(EF.WEAPON, {}) if attacker else {}
    if not isinstance(entity_weapon, dict):
        entity_weapon = {}
    tags = entity_weapon.get("tags", [])
    material = entity_weapon.get("material", "steel")
    alignment = entity_weapon.get("alignment", "none")
    enhancement = entity_weapon.get("enhancement_bonus", 0)

    # "magic" in tags or enhancement >= 1 -> magic weapon
    is_magic = ("magic" in tags) or (enhancement >= 1)

    return (is_magic, material, alignment, enhancement)


def _get_bypass_type(dr_list: list, applied_dr_amount: int) -> str:
    """Return the bypass type of the DR entry that was applied.

    Used to populate damage_reduced event payload.
    Returns the bypass of the highest-amount DR entry matching applied_dr_amount,
    or "-" if not found.

    WO-ENGINE-DR-001
    """
    for entry in dr_list:
        if entry.get("amount", 0) == applied_dr_amount:
            return entry.get("bypass", "-")
    return "-"
