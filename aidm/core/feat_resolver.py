"""Feat resolver for D&D 3.5e combat feat mechanics.

Provides feat prerequisite validation and combat modifier computation
for integration with existing attack/AoO/save resolvers.

WO-034: Core Feat System (15 Feats)

INTEGRATION PATTERN:
Feats modify combat resolution at specific hook points in existing resolvers:
- attack_resolver.py: get_attack_modifier(), get_damage_modifier()
- aoo.py: get_ac_modifier() for Mobility +4 vs movement AoO
- combat_controller.py: get_initiative_modifier() for Improved Initiative +4

All modifiers are computed from entity[EF.FEATS] list and context dict.
"""

from typing import Dict, List, Tuple, Any, Optional
from aidm.schemas.feats import (
    FeatDefinition,
    FeatID,
    FEAT_REGISTRY,
    get_feat_definition,
    extract_weapon_from_feat_id,
)
from aidm.schemas.entity_fields import EF


# ==============================================================================
# PREREQUISITE VALIDATION
# ==============================================================================

def check_prerequisites(entity: Dict[str, Any], feat_id: str) -> Tuple[bool, str]:
    """Check if entity meets prerequisites for a feat.

    Args:
        entity: Entity dict with stats and feats
        feat_id: Feat ID to check (may be weapon-specific like "weapon_focus_longsword")

    Returns:
        Tuple of (met: bool, reason: str)
        If met=True, reason is empty. If met=False, reason explains why.
    """
    feat_def = get_feat_definition(feat_id)
    if feat_def is None:
        return (False, f"Unknown feat: {feat_id}")

    prereqs = feat_def.prerequisites

    # Check ability score minimums
    if "min_str" in prereqs:
        base_stats = entity.get(EF.BASE_STATS, {})
        str_score = base_stats.get("str", 10)
        if str_score < prereqs["min_str"]:
            return (False, f"Requires STR {prereqs['min_str']}, entity has STR {str_score}")

    if "min_dex" in prereqs:
        base_stats = entity.get(EF.BASE_STATS, {})
        dex_score = base_stats.get("dex", 10)
        if dex_score < prereqs["min_dex"]:
            return (False, f"Requires DEX {prereqs['min_dex']}, entity has DEX {dex_score}")

    if "min_int" in prereqs:
        base_stats = entity.get(EF.BASE_STATS, {})
        int_score = base_stats.get("int", 10)
        if int_score < prereqs["min_int"]:
            return (False, f"Requires INT {prereqs['min_int']}, entity has INT {int_score}")

    # Check BAB minimum
    if "min_bab" in prereqs:
        bab = entity.get(EF.BAB, 0)
        if bab < prereqs["min_bab"]:
            return (False, f"Requires BAB +{prereqs['min_bab']}, entity has BAB +{bab}")

    # Check required feats
    if "required_feats" in prereqs:
        entity_feats = entity.get(EF.FEATS, [])
        for required_feat_id in prereqs["required_feats"]:
            # For weapon-specific feats, check if entity has the same weapon variant
            if required_feat_id == FeatID.WEAPON_FOCUS and feat_id.startswith("weapon_specialization_"):
                # Weapon Specialization requires Weapon Focus for the SAME weapon
                weapon = extract_weapon_from_feat_id(feat_id)
                required_feat_with_weapon = f"weapon_focus_{weapon}"
                if required_feat_with_weapon not in entity_feats:
                    return (False, f"Requires {required_feat_with_weapon}")
            else:
                if required_feat_id not in entity_feats:
                    feat_name = FEAT_REGISTRY.get(required_feat_id, FeatDefinition(
                        feat_id=required_feat_id,
                        name=required_feat_id,
                        prerequisites={},
                        modifier_type="",
                        phb_page=0,
                        description=""
                    )).name
                    return (False, f"Requires {feat_name}")

    # Check fighter level (for Weapon Specialization)
    if "fighter_level" in prereqs:
        class_levels = entity.get(EF.CLASS_LEVELS, {})
        fighter_level = class_levels.get("fighter", 0)
        if fighter_level < prereqs["fighter_level"]:
            return (False, f"Requires Fighter {prereqs['fighter_level']}, entity has Fighter {fighter_level}")

    # Check weapon proficiency (for Weapon Focus/Specialization)
    if "proficiency" in prereqs:
        # TODO: Implement weapon proficiency check when proficiency system exists
        # For now, assume proficiency is met
        pass

    return (True, "")


def has_feat(entity: Dict[str, Any], feat_id: str) -> bool:
    """Check if entity has a specific feat.

    Args:
        entity: Entity dict
        feat_id: Feat ID to check

    Returns:
        True if entity has the feat, False otherwise
    """
    feats = entity.get(EF.FEATS, [])
    return feat_id in feats


# ==============================================================================
# MODIFIER COMPUTATION
# ==============================================================================

def get_attack_modifier(
    attacker: Dict[str, Any],
    target: Dict[str, Any],
    context: Dict[str, Any]
) -> int:
    """Compute total feat-based attack modifier.

    Args:
        attacker: Attacker entity dict
        target: Target entity dict
        context: Context dict with keys:
            - weapon_name: str (e.g., "longsword")
            - range_ft: int (distance to target in feet)
            - is_ranged: bool (True for ranged attacks)
            - is_twf: bool (True for two-weapon fighting attacks)
            - power_attack_penalty: int (optional, user-chosen penalty)

    Returns:
        Total attack modifier from feats
    """
    feats = attacker.get(EF.FEATS, [])
    modifier = 0

    # Weapon Focus: +1 attack with chosen weapon
    weapon_name = context.get("weapon_name", "")
    weapon_focus_id = f"weapon_focus_{weapon_name}"
    if weapon_focus_id in feats:
        modifier += 1

    # Greater Weapon Focus: +1 attack (stacks with WF — total +2 with both)
    # WO-ENGINE-GWF-GWS-FEAT-RESOLVER-001: PHB p.94
    greater_weapon_focus_id = f"greater_weapon_focus_{weapon_name}"
    if greater_weapon_focus_id in feats:
        modifier += 1

    # Point Blank Shot: +1 attack within 30 ft
    if FeatID.POINT_BLANK_SHOT in feats:
        range_ft = context.get("range_ft", 999)
        is_ranged = context.get("is_ranged", False)
        if is_ranged and range_ft <= 30:
            modifier += 1

    # Rapid Shot: -2 to all attacks
    if FeatID.RAPID_SHOT in feats and context.get("is_ranged", False):
        modifier -= 2

    # Power Attack: user chooses penalty (stored in context)
    if FeatID.POWER_ATTACK in feats:
        power_attack_penalty = context.get("power_attack_penalty", 0)
        modifier -= power_attack_penalty

    return modifier


def get_damage_modifier(
    attacker: Dict[str, Any],
    target: Dict[str, Any],
    context: Dict[str, Any]
) -> int:
    """Compute total feat-based damage modifier.

    Args:
        attacker: Attacker entity dict
        target: Target entity dict
        context: Context dict with keys:
            - weapon_name: str
            - range_ft: int
            - is_ranged: bool
            - is_two_handed: bool (True if wielding weapon in two hands)
            - power_attack_penalty: int (optional, user-chosen penalty)

    Returns:
        Total damage modifier from feats
    """
    feats = attacker.get(EF.FEATS, [])
    modifier = 0

    # Weapon Specialization: +2 damage with chosen weapon
    weapon_name = context.get("weapon_name", "")
    weapon_spec_id = f"weapon_specialization_{weapon_name}"
    if weapon_spec_id in feats:
        modifier += 2

    # Greater Weapon Specialization: +2 damage (stacks with WS — total +4 with both)
    # WO-ENGINE-GWF-GWS-FEAT-RESOLVER-001: PHB p.94
    greater_weapon_spec_id = f"greater_weapon_specialization_{weapon_name}"
    if greater_weapon_spec_id in feats:
        modifier += 2

    # Point Blank Shot: +1 damage within 30 ft
    if FeatID.POINT_BLANK_SHOT in feats:
        range_ft = context.get("range_ft", 999)
        is_ranged = context.get("is_ranged", False)
        if is_ranged and range_ft <= 30:
            modifier += 1

    # Power Attack: damage bonus (1:1 one-hand, 1.5:1 two-hand, 0.5:1 off-hand)
    # PHB p.98 note: RAW says 2:1 for two-handed; dispatch WO-ENGINE-POWER-ATTACK-001 specifies
    # 1.5:1 to mirror STR-to-damage multipliers (house rule / errata variant).
    # Off-hand (TWF) receives 0.5:1 per dispatch spec.
    if FeatID.POWER_ATTACK in feats:
        power_attack_penalty = context.get("power_attack_penalty", 0)
        is_two_handed = context.get("is_two_handed", False)
        grip = context.get("grip", "one-handed")
        if is_two_handed:
            modifier += int(power_attack_penalty * 2)     # PHB p.98: 2:1 for two-handed
        elif grip == "off-hand":
            modifier += power_attack_penalty // 2  # 0.5:1 for off-hand (TWF)
        else:
            modifier += power_attack_penalty  # 1:1 for one-handed/natural

    return modifier


def get_ac_modifier(
    defender: Dict[str, Any],
    attacker: Dict[str, Any],
    context: Dict[str, Any]
) -> int:
    """Compute total feat-based AC modifier.

    Args:
        defender: Defender entity dict
        attacker: Attacker entity dict (None for generic AC checks)
        context: Context dict with keys:
            - is_aoo: bool (True if this is an AoO)
            - aoo_trigger: str (type of AoO trigger: "movement_out", etc.)
            - dodge_target: str (entity_id of designated Dodge target)

    Returns:
        Total AC modifier from feats
    """
    feats = defender.get(EF.FEATS, [])
    modifier = 0

    # Dodge: +1 dodge AC vs designated opponent
    # Context must specify dodge_target entity_id
    if FeatID.DODGE in feats and attacker is not None:
        dodge_target = context.get("dodge_target", "")
        attacker_id = attacker.get(EF.ENTITY_ID, "")
        if dodge_target == attacker_id:
            modifier += 1

    # Mobility: +4 dodge AC vs AoO from movement
    # PHB p.98: "+4 to AC against attacks of opportunity caused by moving out of a threatened square"
    if FeatID.MOBILITY in feats:
        is_aoo = context.get("is_aoo", False)
        aoo_trigger = context.get("aoo_trigger", "")
        if is_aoo and aoo_trigger in ("movement_out", "mounted_movement_out"):
            modifier += 4

    return modifier


def get_initiative_modifier(entity: Dict[str, Any]) -> int:
    """Compute feat-based initiative modifier.

    Args:
        entity: Entity dict

    Returns:
        Initiative modifier from feats
    """
    feats = entity.get(EF.FEATS, [])

    # Improved Initiative: +4 initiative
    if FeatID.IMPROVED_INITIATIVE in feats:
        return 4

    return 0


# ==============================================================================
# SPECIAL FEAT HANDLERS
# ==============================================================================

def can_use_cleave(entity: Dict[str, Any], killed_enemy_id: str, world_state: Any) -> bool:
    """Check if entity can use Cleave after dropping an enemy.

    PHB p.92: "If you deal a creature enough damage to make it drop (typically
    by dropping it to below 0 hit points or killing it), you get an immediate,
    extra melee attack against another creature within reach."

    Args:
        entity: Attacker entity dict
        killed_enemy_id: Entity ID of the enemy just dropped
        world_state: Current world state (to check for adjacent enemies)

    Returns:
        True if Cleave can be used, False otherwise
    """
    feats = entity.get(EF.FEATS, [])

    # Must have Cleave or Great Cleave
    if FeatID.CLEAVE not in feats and FeatID.GREAT_CLEAVE not in feats:
        return False

    # Check if there are adjacent enemies
    # (This would require checking world_state for adjacent hostile entities)
    # For now, return True if feat is present (actual target validation
    # happens in combat_controller when selecting Cleave target)
    return True


def get_cleave_limit(entity: Dict[str, Any]) -> Optional[int]:
    """Get Cleave usage limit per round.

    Args:
        entity: Entity dict

    Returns:
        Cleave limit (1 for Cleave, None for Great Cleave unlimited)
    """
    feats = entity.get(EF.FEATS, [])

    if FeatID.GREAT_CLEAVE in feats:
        return None  # Unlimited

    if FeatID.CLEAVE in feats:
        return 1  # Once per round

    return 0  # No Cleave


def suppresses_aoo_from_movement(entity: Dict[str, Any], context: Dict[str, Any]) -> bool:
    """Check if Spring Attack suppresses AoO from movement during attack.

    PHB p.100: "When using the attack action with a melee weapon, you can move
    both before and after the attack, provided that your total distance moved
    is not greater than your speed. Moving in this way does not provoke an
    attack of opportunity from the defender you attack."

    Args:
        entity: Entity dict
        context: Context with attack details

    Returns:
        True if Spring Attack is active and suppresses AoO, False otherwise
    """
    feats = entity.get(EF.FEATS, [])

    if FeatID.SPRING_ATTACK not in feats:
        return False

    # Spring Attack only suppresses AoO from the DEFENDER being attacked
    # Other enemies can still take AoO from movement
    # Context should specify if this is the attacked defender
    is_attacked_defender = context.get("is_attacked_defender", False)
    return is_attacked_defender


def get_twf_penalties(entity: Dict[str, Any], has_light_offhand: bool) -> Tuple[int, int]:
    """Get Two-Weapon Fighting attack penalties.

    PHB p.160 (Two-Weapon Fighting rules):
    - No TWF feat: -6 main/-10 off (or -4/-8 with light off-hand)
    - Two-Weapon Fighting: -4 main/-4 off (or -2/-2 with light off-hand)
    - Applied via feat: -2/-2 regardless of off-hand weight

    Args:
        entity: Entity dict
        has_light_offhand: True if off-hand weapon is light

    Returns:
        Tuple of (main_hand_penalty, off_hand_penalty)
    """
    feats = entity.get(EF.FEATS, [])

    if FeatID.TWO_WEAPON_FIGHTING in feats:
        # TWF feat: -2/-2 with light off-hand, -4/-4 with heavy (PHB p.105)
        if has_light_offhand:
            return (-2, -2)
        else:
            return (-4, -4)
    else:
        # No feat: -6/-10 or -4/-8 with light off-hand (PHB p.160)
        if has_light_offhand:
            return (-4, -8)
        else:
            return (-6, -10)


def get_twf_extra_attacks(entity: Dict[str, Any]) -> int:
    """Get number of extra off-hand attacks from TWF feat chain.

    Args:
        entity: Entity dict

    Returns:
        Number of extra off-hand attacks (0, 1, 2, or 3)
    """
    feats = entity.get(EF.FEATS, [])

    if FeatID.GREATER_TWF in feats:
        return 3  # Base + 2 extra = 3 total off-hand attacks

    if FeatID.IMPROVED_TWF in feats:
        return 2  # Base + 1 extra = 2 total off-hand attacks

    if FeatID.TWO_WEAPON_FIGHTING in feats:
        return 1  # Base off-hand attack only

    return 0  # No TWF, no off-hand attacks


def ignores_shooting_into_melee_penalty(entity: Dict[str, Any]) -> bool:
    """Check if entity ignores -4 penalty for shooting into melee.

    PHB p.140: "If you shoot or throw a ranged weapon at a target engaged in
    melee with a friendly character, you take a -4 penalty on your attack roll."

    PHB p.98: Precise Shot negates this penalty.

    Args:
        entity: Entity dict

    Returns:
        True if Precise Shot is present, False otherwise
    """
    feats = entity.get(EF.FEATS, [])
    return FeatID.PRECISE_SHOT in feats
