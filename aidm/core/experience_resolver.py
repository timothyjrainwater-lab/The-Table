"""Experience and leveling system for D&D 3.5e.

Handles XP calculation, level threshold checking, and level-up mechanics
per DMG Chapter 2-3 and PHB Chapter 3.

References:
- DMG Table 2-6 (XP Awards by CR): DMG p.38
- DMG Table 3-2 (Experience and Level-Dependent Benefits): DMG p.46
- PHB Chapter 3 (Classes): PHB p.22+
- PHB p.60 (Multiclass XP Penalty)
"""

from copy import deepcopy
from typing import Optional, Dict
from aidm.schemas.leveling import (
    LEVEL_THRESHOLDS,
    XP_TABLE,
    CR_FRACTIONS,
    CLASS_PROGRESSIONS,
    BAB_PROGRESSION,
    GOOD_SAVE_PROGRESSION,
    POOR_SAVE_PROGRESSION,
    LevelUpResult,
)
from aidm.schemas.entity_fields import EF
from aidm.core.rng_manager import RNGManager


def calculate_xp_award(
    party_level: int,
    party_size: int,
    defeated_cr: float,
) -> int:
    """Calculate XP per party member for defeating a creature.

    Uses DMG Table 2-6 (p.38). XP is split equally among party members.
    CR values include fractional CRs (1/2, 1/3, 1/4, 1/6, 1/8).

    Args:
        party_level: Average level of the party (1-20)
        party_size: Number of party members (typically 3-6)
        defeated_cr: Challenge Rating of defeated creature

    Returns:
        XP award per party member (integer)

    Citations:
        - DMG p.38, Table 2-6: Experience Point Awards
    """
    # Clamp party level to valid range
    if party_level < 1:
        party_level = 1
    elif party_level > 20:
        party_level = 20

    # Clamp party size to reasonable range
    if party_size < 1:
        party_size = 1

    # Calculate CR delta
    cr_delta = int(defeated_cr) - party_level

    # Look up base XP from table (assumes 4-person party)
    key = (party_level, cr_delta)
    base_xp = XP_TABLE.get(key, 0)

    # Adjust for party size
    # DMG p.38: "These values assume a party of four characters"
    adjusted_xp = int(base_xp * (4.0 / party_size))

    return adjusted_xp


def calculate_multiclass_penalty(
    class_levels: Dict[str, int],
    favored_class: Optional[str] = None,
) -> float:
    """Calculate XP penalty multiplier for multiclass imbalance.

    Per PHB p.60: "If your multiclass character has classes of different levels,
    and none of those classes is within 1 level of your highest-level class,
    you take a -20% XP penalty."

    More specifically: For each class that is more than 1 level below the
    highest class level (excluding the favored class), apply -20% penalty.

    Args:
        class_levels: Dict mapping class name to level
        favored_class: Favored class (if any). Defaults to highest-level class.

    Returns:
        XP multiplier (1.0 = no penalty, 0.8 = one offending class, etc.)

    Citations:
        - PHB p.60: Multiclass Characters
    """
    if not class_levels or len(class_levels) == 1:
        # Single-class or no classes: no penalty
        return 1.0

    # Default favored class to highest-level class
    if favored_class is None:
        favored_class = max(class_levels, key=class_levels.get)

    # Find highest class level (may or may not be the favored class)
    highest_level = max(class_levels.values())

    # Count offending classes:
    # Any class (except favored) more than 1 level below the highest class
    offending_count = 0
    for class_name, level in class_levels.items():
        if class_name != favored_class:
            if highest_level - level > 1:
                offending_count += 1

    # Apply penalty: -20% per offending class
    penalty_multiplier = 1.0 - (0.2 * offending_count)

    # Minimum 0.0 (can't have negative XP)
    return max(0.0, penalty_multiplier)


def check_level_up(entity: dict) -> Optional[LevelUpResult]:
    """Check if entity has enough XP to level up.

    Args:
        entity: Entity dict with EF.XP and EF.LEVEL

    Returns:
        LevelUpResult if level up is available, None otherwise

    Citations:
        - DMG p.46, Table 3-2: Experience and Level-Dependent Benefits
    """
    current_xp = entity.get(EF.XP, 0)
    current_level = entity.get(EF.LEVEL, 1)

    # Check if next level exists in table
    next_level = current_level + 1
    if next_level not in LEVEL_THRESHOLDS:
        # Max level reached
        return None

    # Check if XP threshold met
    required_xp = LEVEL_THRESHOLDS[next_level]
    if current_xp < required_xp:
        return None

    # Determine which class to advance
    # For Phase 2, advance highest-level class
    class_levels = entity.get(EF.CLASS_LEVELS, {})
    if not class_levels:
        # No class data — cannot level up
        return None

    class_name = max(class_levels, key=class_levels.get)

    # Level up available — return None for now
    # (actual level-up requires apply_level_up with RNG)
    return None  # Placeholder


def apply_level_up(
    entity: dict,
    class_name: str,
    rng: RNGManager,
) -> tuple[dict, LevelUpResult]:
    """Apply level-up changes to entity.

    Creates a new entity dict (deepcopy) with level-up applied.

    Changes applied:
    1. Increment EF.LEVEL
    2. Roll hit die (class-dependent) + CON mod, add to EF.HP_MAX and EF.HP_CURRENT
    3. Add skill points (class-dependent + INT mod)
    4. Grant feat slot every 3rd level (3, 6, 9, 12, 15, 18)
    5. Grant ability score increase every 4th level (4, 8, 12, 16, 20)
    6. Update BAB per class progression
    7. Update save bonuses per class progression

    Args:
        entity: Source entity dict
        class_name: Class to advance in
        rng: RNG manager for hit die rolls

    Returns:
        Tuple of (new_entity_dict, LevelUpResult)

    Citations:
        - PHB p.22+: Class progressions
        - DMG p.46, Table 3-2: Experience and Level-Dependent Benefits
    """
    # Deep copy entity for mutation
    new_entity = deepcopy(entity)

    # Get current state
    current_level = new_entity.get(EF.LEVEL, 1)
    class_levels = new_entity.get(EF.CLASS_LEVELS, {})
    con_mod = new_entity.get(EF.CON_MOD, 0)
    int_mod = new_entity.get(EF.INT_MOD, 0)

    # Validate class exists
    if class_name not in CLASS_PROGRESSIONS:
        raise ValueError(f"Unknown class: {class_name}")

    progression = CLASS_PROGRESSIONS[class_name]

    # Increment level
    new_level = current_level + 1
    new_entity[EF.LEVEL] = new_level

    # Increment class level
    class_level = class_levels.get(class_name, 0) + 1
    new_class_levels = deepcopy(class_levels)
    new_class_levels[class_name] = class_level
    new_entity[EF.CLASS_LEVELS] = new_class_levels

    # Roll hit die
    hp_roll = rng.stream("combat").randint(1, progression.hit_die)
    hp_gained = max(1, hp_roll + con_mod)  # Minimum 1 HP per level

    old_hp_max = new_entity.get(EF.HP_MAX, 0)
    new_entity[EF.HP_MAX] = old_hp_max + hp_gained
    new_entity[EF.HP_CURRENT] = new_entity.get(EF.HP_CURRENT, 0) + hp_gained

    # Calculate skill points
    skill_points = max(1, progression.skill_points_per_level + int_mod)

    # Check for feat slot (every 3rd level)
    feat_slot_gained = (new_level % 3 == 0)
    if feat_slot_gained:
        new_entity[EF.FEAT_SLOTS] = new_entity.get(EF.FEAT_SLOTS, 0) + 1

    # Check for ability score increase (every 4th level)
    ability_score_increase = (new_level % 4 == 0)

    # Calculate BAB increase
    bab_type = progression.bab_type
    old_bab = new_entity.get(EF.BAB, 0)
    new_bab = BAB_PROGRESSION[bab_type][class_level - 1]

    # For multiclass, use highest BAB among all classes
    # (This is simplified — real 3.5e stacks BABs, but for Phase 2 we use highest)
    new_entity[EF.BAB] = max(old_bab, new_bab)
    bab_increase = new_entity[EF.BAB] - old_bab

    # Calculate save increases
    save_increases = {}
    for save_type in ["fort", "ref", "will"]:
        ef_save = {
            "fort": EF.SAVE_FORT,
            "ref": EF.SAVE_REF,
            "will": EF.SAVE_WILL,
        }[save_type]

        old_save = new_entity.get(ef_save, 0)

        if save_type in progression.good_saves:
            new_save = GOOD_SAVE_PROGRESSION[class_level - 1]
        else:
            new_save = POOR_SAVE_PROGRESSION[class_level - 1]

        # For multiclass, use best save from any class
        new_entity[ef_save] = max(old_save, new_save)
        save_increases[save_type] = new_entity[ef_save] - old_save

    # Build result
    result = LevelUpResult(
        new_level=new_level,
        class_name=class_name,
        hp_roll=hp_roll,
        hp_gained=hp_gained,
        skill_points=skill_points,
        bab_increase=bab_increase,
        save_increases=save_increases,
        feat_slot_gained=feat_slot_gained,
        ability_score_increase=ability_score_increase,
    )

    return new_entity, result


def award_xp(
    entity: dict,
    xp_amount: int,
    apply_multiclass_penalty: bool = True,
) -> dict:
    """Award XP to an entity.

    Creates a new entity dict (deepcopy) with XP added.
    Optionally applies multiclass penalty.

    Args:
        entity: Source entity dict
        xp_amount: XP to award (before penalty)
        apply_multiclass_penalty: Whether to apply multiclass XP penalty

    Returns:
        New entity dict with XP updated

    Citations:
        - PHB p.60: Multiclass XP Penalty
    """
    new_entity = deepcopy(entity)

    # Apply multiclass penalty if enabled
    if apply_multiclass_penalty:
        class_levels = entity.get(EF.CLASS_LEVELS, {})
        penalty_multiplier = calculate_multiclass_penalty(class_levels)
        xp_amount = int(xp_amount * penalty_multiplier)

    # Add XP
    current_xp = new_entity.get(EF.XP, 0)
    new_entity[EF.XP] = current_xp + xp_amount

    return new_entity
