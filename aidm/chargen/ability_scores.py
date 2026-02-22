"""Ability score generation for D&D 3.5e character creation.

WO-CHARGEN-FOUNDATION-001 (Part A, GAP-CG-001).

Methods:
    - "4d6": Roll 4d6, drop lowest for each of 6 scores (PHB p.8)
    - "point_buy": Start all at 8, spend 25 points per DMG variant (PHB p.169)
    - "standard": Fixed array [15, 14, 13, 12, 10, 8]

Source: PHB Chapter 1 (Abilities), PHB p.8 (modifier formula).
"""

import random
from typing import Dict

# Ability score names in standard PHB order
ABILITY_NAMES = ("str", "dex", "con", "int", "wis", "cha")

# Point-buy cost table (PHB p.169 / DMG variant).
# Score 8 = 0 points, up to 18 = 16 points.
POINT_BUY_COST: Dict[int, int] = {
    8: 0, 9: 1, 10: 2, 11: 3, 12: 4,
    13: 5, 14: 6, 15: 8, 16: 10, 17: 13, 18: 16,
}

# Standard point-buy budget
POINT_BUY_BUDGET = 25

# Standard array (PHB p.169)
STANDARD_ARRAY = (15, 14, 13, 12, 10, 8)


def roll_4d6_drop_lowest() -> int:
    """Roll 4d6, drop the lowest die. Returns sum of top 3.

    Per PHB p.8: Roll four six-sided dice, discard the lowest,
    and total the remaining three.

    Returns:
        int: Sum of top 3 dice (range 3-18).
    """
    dice = [random.randint(1, 6) for _ in range(4)]
    dice.sort()
    return sum(dice[1:])  # drop lowest


def ability_modifier(score: int) -> int:
    """Calculate ability modifier from ability score.

    Formula: (score - 10) // 2, per PHB p.8.

    Args:
        score: Ability score (typically 1-30+).

    Returns:
        int: Ability modifier.
    """
    return (score - 10) // 2


def generate_ability_array(method: str = "4d6") -> Dict[str, int]:
    """Generate 6 ability scores using the specified method.

    Args:
        method: Generation method.
            "4d6" — Roll 4d6 drop lowest for each score.
            "point_buy" — All scores start at 8, returns the default
                          balanced spread for 25 points.
            "standard" — Fixed array [15, 14, 13, 12, 10, 8].

    Returns:
        Dict with keys: str, dex, con, int, wis, cha.

    Raises:
        ValueError: If method is not recognized.
    """
    if method == "4d6":
        return {name: roll_4d6_drop_lowest() for name in ABILITY_NAMES}
    elif method == "standard":
        return dict(zip(ABILITY_NAMES, STANDARD_ARRAY))
    elif method == "point_buy":
        # Return a balanced default spread that totals 25 points:
        # 14(6) + 14(6) + 14(6) + 10(2) + 10(2) + 10(2) = 24 ... not quite
        # Better: 15(8) + 14(6) + 13(5) + 12(4) + 10(2) + 8(0) = 25
        return dict(zip(ABILITY_NAMES, STANDARD_ARRAY))
    else:
        raise ValueError(
            f"Unknown method '{method}'. Use '4d6', 'point_buy', or 'standard'."
        )


def validate_point_buy(scores: Dict[str, int], budget: int = POINT_BUY_BUDGET) -> bool:
    """Validate that a set of ability scores fits within point-buy budget.

    Args:
        scores: Dict mapping ability name to score (6 entries expected).
        budget: Maximum point-buy budget. Default 25.

    Returns:
        True if total cost <= budget and all scores are in valid range (8-18).

    Raises:
        ValueError: If a score is outside the 8-18 range or not in cost table.
    """
    if len(scores) != 6:
        raise ValueError(f"Expected 6 ability scores, got {len(scores)}")

    total_cost = 0
    for name, score in scores.items():
        if score not in POINT_BUY_COST:
            raise ValueError(
                f"Score {score} for {name} is outside point-buy range (8-18)."
            )
        total_cost += POINT_BUY_COST[score]

    return total_cost <= budget
