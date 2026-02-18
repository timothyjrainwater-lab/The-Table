"""Camera posture definitions for the Table UI.

Three postures (UI doctrine §5):
- STANDARD: Seated table view (default on load)
- DOWN: Reading/writing view (looking down at player-edge)
- LEAN_FORWARD: Map engagement view (angled toward center, no god cam)

All posture→posture transitions are valid.

Authority: WO-UI-01, DOCTRINE_04_TABLE_UI_MEMO_V4 §5.
"""
from __future__ import annotations

from enum import Enum
from typing import FrozenSet


class CameraPosture(Enum):
    """Camera posture enum — defines the 3 seated-at-table viewpoints."""

    STANDARD = "STANDARD"
    DOWN = "DOWN"
    LEAN_FORWARD = "LEAN_FORWARD"


# All postures as a frozenset for membership checks.
ALL_POSTURES: FrozenSet[CameraPosture] = frozenset(CameraPosture)

# All transitions are valid: any posture can transition to any other posture.
VALID_TRANSITIONS: FrozenSet[tuple] = frozenset(
    (src, dst)
    for src in CameraPosture
    for dst in CameraPosture
)
