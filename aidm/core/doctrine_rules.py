"""Doctrine rules for deriving tactical envelopes.

Pure deterministic helpers for computing allowed/forbidden tactics
based on INT/WIS scores and doctrine tags.

This is GATING, not optimization. Low INT doesn't make monsters "dumb"
in the narrative sense - it constrains which tactical patterns they can execute.
"""

from typing import Optional, List
from aidm.schemas.doctrine import (
    MonsterDoctrine,
    IntelligenceBand,
    WisdomBand,
    TacticClass,
    DoctrineTag
)


def derive_int_band(int_score: Optional[int]) -> IntelligenceBand:
    """
    Derive intelligence band from INT score.

    Args:
        int_score: Intelligence score (None for mindless creatures)

    Returns:
        IntelligenceBand classification
    """
    if int_score is None:
        return "NO_INT"
    elif int_score == 1:
        return "INT_1"
    elif int_score == 2:
        return "INT_2"
    elif 3 <= int_score <= 4:
        return "INT_3_4"
    elif 5 <= int_score <= 7:
        return "INT_5_7"
    elif 8 <= int_score <= 10:
        return "INT_8_10"
    elif 11 <= int_score <= 13:
        return "INT_11_13"
    elif 14 <= int_score <= 16:
        return "INT_14_16"
    else:  # 17+
        return "INT_17_PLUS"


def derive_wis_band(wis_score: Optional[int]) -> Optional[WisdomBand]:
    """
    Derive wisdom band from WIS score.

    Args:
        wis_score: Wisdom score (None if not specified)

    Returns:
        WisdomBand classification or None
    """
    if wis_score is None:
        return None
    elif 1 <= wis_score <= 7:
        return "WIS_LOW"
    elif 8 <= wis_score <= 12:
        return "WIS_AVG"
    elif 13 <= wis_score <= 16:
        return "WIS_HIGH"
    else:  # 17+
        return "WIS_EXCELLENT"


def derive_tactical_envelope(doctrine: MonsterDoctrine) -> MonsterDoctrine:
    """
    Populate allowed/forbidden tactics based on INT/WIS bands and tags.

    This is capability gating based on creature stats and nature.
    NOT mercy, sympathy, or fairness balancing.

    Args:
        doctrine: MonsterDoctrine with INT/WIS scores and tags set

    Returns:
        MonsterDoctrine with int_band, wis_band, allowed_tactics, forbidden_tactics populated
    """
    # Derive bands
    doctrine.int_band = derive_int_band(doctrine.int_score)
    doctrine.wis_band = derive_wis_band(doctrine.wis_score)

    allowed: List[TacticClass] = []
    forbidden: List[TacticClass] = []

    # Baseline tactics by INT band
    if doctrine.int_band == "NO_INT" or doctrine.int_band == "INT_1":
        # Mindless or near-mindless: pure reflexive behavior
        allowed.extend(["attack_nearest"])
        forbidden.extend([
            "deny_actions_chain",
            "bait_and_switch",
            "target_support",
            "target_controller",
            "use_cover",
            "setup_flank",
            "retreat_regroup"
        ])

    elif doctrine.int_band == "INT_2":
        # Minimal cognition
        allowed.extend(["attack_nearest", "random_target"])
        forbidden.extend([
            "deny_actions_chain",
            "bait_and_switch",
            "target_support",
            "target_controller",
            "use_cover"
        ])

    elif doctrine.int_band == "INT_3_4":
        # Animal intelligence
        allowed.extend(["attack_nearest", "random_target", "focus_fire"])
        if "pack_hunter" in doctrine.tags:
            allowed.append("setup_flank")
        forbidden.extend([
            "deny_actions_chain",
            "bait_and_switch",
            "target_controller"
        ])

    elif doctrine.int_band == "INT_5_7":
        # Low but functional intelligence
        allowed.extend([
            "attack_nearest",
            "focus_fire",
            "setup_flank",
            "use_cover",
            "ignore_downs_keep_killing"
        ])
        if "pack_hunter" in doctrine.tags:
            allowed.append("target_support")

    elif doctrine.int_band == "INT_8_10":
        # Average intelligence
        allowed.extend([
            "attack_nearest",
            "focus_fire",
            "setup_flank",
            "use_cover",
            "retreat_regroup",
            "ignore_downs_keep_killing"
        ])
        if "tactician" in doctrine.tags or "disciplined" in doctrine.tags:
            allowed.extend(["target_support", "target_controller"])

    elif doctrine.int_band == "INT_11_13":
        # Above average intelligence
        allowed.extend([
            "attack_nearest",
            "focus_fire",
            "target_support",
            "setup_flank",
            "use_cover",
            "retreat_regroup",
            "ignore_downs_keep_killing"
        ])
        if "tactician" in doctrine.tags:
            allowed.extend(["deny_actions_chain", "target_controller"])

    else:  # INT_14_16 or INT_17_PLUS
        # High intelligence: all tactics available by default
        allowed.extend([
            "focus_fire",
            "target_support",
            "target_controller",
            "setup_flank",
            "use_cover",
            "bait_and_switch",
            "deny_actions_chain",
            "retreat_regroup",
            "ignore_downs_keep_killing",
            "attack_nearest"
        ])

    # Tag overrides (these can forbid or allow tactics regardless of INT)
    if "mindless_feeder" in doctrine.tags:
        # Override everything - pure feeding instinct
        allowed = ["attack_nearest", "random_target"]
        forbidden = [
            t for t in [
                "focus_fire", "target_support", "target_controller",
                "setup_flank", "use_cover", "bait_and_switch",
                "deny_actions_chain", "retreat_regroup"
            ]
        ]

    if "fanatical" in doctrine.tags:
        allowed.append("fight_to_the_death")
        if "retreat_regroup" in allowed:
            allowed.remove("retreat_regroup")
        forbidden.append("retreat_regroup")

    if "cowardly" in doctrine.tags:
        allowed.append("retreat_regroup")
        if "fight_to_the_death" in allowed:
            allowed.remove("fight_to_the_death")
        forbidden.append("fight_to_the_death")

    if "berserker" in doctrine.tags:
        allowed.append("fight_to_the_death")
        allowed.append("ignore_downs_keep_killing")
        if "retreat_regroup" in allowed:
            allowed.remove("retreat_regroup")

    if "ambusher" in doctrine.tags:
        allowed.extend(["bait_and_switch", "use_cover"])

    if "assassin" in doctrine.tags:
        allowed.extend(["target_support", "target_controller", "deny_actions_chain"])

    if "caster_controller" in doctrine.tags:
        allowed.extend(["target_controller", "deny_actions_chain", "use_cover"])

    # Deduplicate
    doctrine.allowed_tactics = list(dict.fromkeys(allowed))  # Preserve order, remove dupes
    doctrine.forbidden_tactics = list(dict.fromkeys(forbidden))

    return doctrine
