"""Metamagic feat resolution for WO-ENGINE-METAMAGIC-001.

Implements runtime metamagic effects for:
  - Empower Spell (PHB p.93): variable numeric effects × 1.5, slot +2
  - Maximize Spell (PHB p.97): max value, no RNG consumed, slot +3
  - Extend Spell (PHB p.94): duration × 2, slot +1
  - Heighten Spell (PHB p.95): raises save DC to target level, slot = target level
  - Quicken Spell (PHB p.98): swift action, no AoO, slot +4

This module provides pure functions with no side effects.
All wiring into play_loop.py and spell_resolver.py is done externally.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any


METAMAGIC_SLOT_COST: Dict[str, int] = {
    "empower": 2,
    "maximize": 3,
    "extend": 1,
    "heighten": 0,  # variable — cost = heighten_to_level - base_level
    "quicken": 4,
}

# Feat name in EF.FEATS corresponding to each metamagic keyword
_FEAT_NAMES: Dict[str, str] = {
    "empower": "Empower Spell",
    "maximize": "Maximize Spell",
    "extend": "Extend Spell",
    "heighten": "Heighten Spell",
    "quicken": "Quicken Spell",
}

_VALID_METAMAGIC = frozenset(METAMAGIC_SLOT_COST.keys())


def validate_metamagic(metamagic: List[str], caster: Dict[str, Any],
                        heighten_to_level: Optional[int] = None,
                        base_spell_level: int = 0) -> Optional[str]:
    """Validate metamagic prerequisites.

    Returns error reason string or None (success).

    Checks:
      - All metamagic keywords are valid
      - Caster has the required feat in EF.FEATS
      - Empower and Maximize are not combined (incompatible)
      - Heighten requires heighten_to_level > base_spell_level
    """
    from aidm.schemas.entity_fields import EF

    if not metamagic:
        return None

    feats = caster.get(EF.FEATS, [])

    # Validate each metamagic keyword
    for mm in metamagic:
        if mm not in _VALID_METAMAGIC:
            return "missing_metamagic_feat"
        feat_name = _FEAT_NAMES[mm]
        if feat_name not in feats:
            return "missing_metamagic_feat"

    # Empower + Maximize on same cast is incompatible
    if "empower" in metamagic and "maximize" in metamagic:
        return "incompatible_metamagic"

    # Heighten requires a target level higher than base
    if "heighten" in metamagic:
        if heighten_to_level is None or heighten_to_level <= base_spell_level:
            return "missing_metamagic_feat"

    return None


def compute_effective_slot_level(spell_base_level: int, metamagic: List[str],
                                  heighten_to_level: Optional[int] = None) -> int:
    """Compute slot level after metamagic surcharges.

    For Heighten: slot cost = heighten_to_level (not additive).
    For all other feats: additive surcharge on top of base level.
    Slot level is floored at spell_base_level.
    """
    if not metamagic:
        return spell_base_level

    if "heighten" in metamagic and heighten_to_level is not None:
        # Heighten: slot = target level; other metamagics stack on top
        base = heighten_to_level
        other = [mm for mm in metamagic if mm != "heighten"]
        surcharge = sum(METAMAGIC_SLOT_COST[mm] for mm in other)
        return base + surcharge

    surcharge = sum(METAMAGIC_SLOT_COST[mm] for mm in metamagic)
    return spell_base_level + surcharge


def apply_empower(damage_total: int) -> int:
    """Return floor(damage_total * 1.5).

    PHB p.93: All variable numeric effects × 1.5.
    Applied to the final dice-based total (not flat bonuses).
    """
    return int(damage_total * 1.5)


def apply_maximize_dice(dice_expr: str) -> int:
    """Return maximum possible value for dice string without consuming RNG.

    PHB p.97: All variable numeric effects use maximum value.
    Supports formats like '8d6', '2d8+5', '1d12'.
    Does NOT consume RNG — determinism preserved.
    """
    expr = dice_expr.lower().strip()

    bonus = 0
    if "+" in expr:
        parts = expr.split("+", 1)
        expr = parts[0]
        bonus = int(parts[1])
    elif "-" in expr:
        parts = expr.split("-", 1)
        expr = parts[0]
        bonus = -int(parts[1])

    if "d" not in expr:
        return bonus

    parts = expr.split("d")
    num_dice = int(parts[0]) if parts[0] else 1
    die_size = int(parts[1])

    return num_dice * die_size + bonus


def apply_extend(effect: Any) -> Any:
    """Return effect with rounds_remaining doubled.

    PHB p.94: Duration × 2.
    Works on ActiveSpellEffect (has rounds_remaining attribute).
    If already permanent (-1), returns unchanged.
    """
    from dataclasses import replace as _replace
    if hasattr(effect, "rounds_remaining"):
        if effect.rounds_remaining == -1:
            return effect  # Permanent effects unchanged
        return _replace(effect, rounds_remaining=effect.rounds_remaining * 2)
    return effect


def apply_heighten_dc(base_dc: int, base_spell_level: int, heighten_to_level: int) -> int:
    """Return DC adjusted for heightened spell level.

    PHB p.95: Spell treated as higher level for DC calculation.
    DC formula: 10 + spell_level + ability_mod.
    Raising spell_level by (heighten_to_level - base_spell_level) raises DC by same amount.
    """
    return base_dc + (heighten_to_level - base_spell_level)
