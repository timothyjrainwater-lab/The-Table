"""Dice rolling — thin wrapper over d20 (MIT licence).

Provides seeded, deterministic dice rolling backed by the d20 library.
This is the NEW external interface.  The legacy parse_damage_dice /
roll_dice pair in attack_resolver.py continues to work for existing call sites.

Seeding: when an rng is supplied, dice are parsed with a simple internal
parser (XdY[+/-Z] format) and rolled using rng.randint — fully deterministic.
When rng is None, d20.roll() is used (random result each call).

WO-INFRA-DICE-001
"""

import re
import random as _random
from typing import Optional

import d20 as _d20


# ---------------------------------------------------------------------------
# Simple parser for the seeded path — handles the formats in use by the engine:
#   "XdY"        e.g. "2d6"
#   "XdY+Z"      e.g. "2d6+3"
#   "XdY-Z"      e.g. "2d4-1"
#   "N"          bare integer e.g. "1"
# ---------------------------------------------------------------------------
_DICE_RE = re.compile(
    r'^(?P<num>\d+)d(?P<size>\d+)(?P<bonus>[+-]\d+)?$',
    re.IGNORECASE,
)
_FLAT_RE = re.compile(r'^\d+$')


def _roll_seeded(dice_str: str, rng: _random.Random) -> int:
    """Roll dice_str using the provided rng instance. Internal helper."""
    s = dice_str.strip().replace(' ', '')

    # Bare integer
    if _FLAT_RE.match(s):
        return int(s)

    m = _DICE_RE.match(s)
    if m is None:
        raise ValueError(f"roll_dice: unsupported dice expression for seeded roll: {dice_str!r}")

    num_dice = int(m.group('num'))
    die_size = int(m.group('size'))
    bonus_str = m.group('bonus')
    bonus = int(bonus_str) if bonus_str else 0

    total = sum(rng.randint(1, die_size) for _ in range(num_dice)) + bonus
    return total


def roll_dice(dice_str: str, rng: Optional[_random.Random] = None) -> int:
    """Roll a dice expression and return the total.

    Args:
        dice_str: Standard dice expression, e.g. ``"2d6+3"``, ``"1d20"``,
                  ``"1d4"``.  A bare integer (e.g. ``"1"``) is also accepted.
        rng: Optional :class:`random.Random` instance.  When supplied, rolls
             are fully deterministic for a given seed — useful in gate tests.
             Supports XdY, XdY+Z, XdY-Z, and bare-integer formats.
             When ``None``, uses ``d20.roll()`` (random result each call).

    Returns:
        Integer total of the rolled expression.
    """
    if rng is not None:
        return _roll_seeded(dice_str, rng)
    return _d20.roll(dice_str).total
