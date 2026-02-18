"""PENDING handshake + REQUEST intent types for the Table UI protocol.

PENDING types (Server → Client):
- PendingRoll: Dice roll needed (spec + handle)
- PendingPoint: Targeting mode (target_type + valid_targets)

REQUEST types (Client → Server):
- DeclareActionIntent: Player declares an action (voice or click)
- DiceTowerDropIntent: Player drops dice to resolve a PendingRoll

State machine rules (UI doctrine §7):
- Only one PENDING active at a time
- New PENDING cancels existing PENDING
- PENDING clears when corresponding REQUEST is received or runtime cancels

Hard bans (UI doctrine §8):
- No REQUEST types named ROLL, CAST, ATTACK, END_TURN, or any other
  "do the action" verb. These bypass declare→point→confirm.

Authority: WO-UI-01, DOCTRINE_04_TABLE_UI_MEMO_V4 §7, §8, §16.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple


# ---------------------------------------------------------------------------
# PENDING types (Server → Client)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PendingRoll:
    """Server requests the player roll dice.

    Attributes:
        spec: Dice formula, e.g. "1d20", "2d6+3".
        pending_handle: Unique handle for this PENDING instance.
    """

    spec: str
    pending_handle: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "PENDING_ROLL",
            "spec": self.spec,
            "pending_handle": self.pending_handle,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PendingRoll:
        return cls(
            spec=data["spec"],
            pending_handle=data["pending_handle"],
        )


@dataclass(frozen=True)
class PendingPoint:
    """Server requests the player select a target.

    Attributes:
        target_type: Kind of target expected, e.g. "creature", "square", "object".
        valid_targets: Tuple of valid target identifiers.
    """

    target_type: str
    valid_targets: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "PENDING_POINT",
            "target_type": self.target_type,
            "valid_targets": list(self.valid_targets),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PendingPoint:
        return cls(
            target_type=data["target_type"],
            valid_targets=tuple(data.get("valid_targets", ())),
        )


# ---------------------------------------------------------------------------
# REQUEST types (Client → Server)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DeclareActionIntent:
    """Player declares an action (voice or click).

    This is a declaration, not an execution. The runtime decides legality.

    Attributes:
        action_kind: Category of action, e.g. "melee_strike", "cast", "move".
        source_ref: Reference to the source of the declaration (e.g. BeatIntent handle).
    """

    action_kind: str
    source_ref: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "DECLARE_ACTION_INTENT",
            "action_kind": self.action_kind,
            "source_ref": self.source_ref,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DeclareActionIntent:
        return cls(
            action_kind=data["action_kind"],
            source_ref=data["source_ref"],
        )


@dataclass(frozen=True)
class DiceTowerDropIntent:
    """Player drops dice into the tower to resolve a PendingRoll.

    Attributes:
        dice_ids: Tuple of dice identifiers being dropped (e.g. ("d20",)).
        pending_roll_handle: The pending_handle from the PendingRoll being resolved.
    """

    dice_ids: Tuple[str, ...]
    pending_roll_handle: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "DICE_TOWER_DROP_INTENT",
            "dice_ids": list(self.dice_ids),
            "pending_roll_handle": self.pending_roll_handle,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DiceTowerDropIntent:
        return cls(
            dice_ids=tuple(data.get("dice_ids", ())),
            pending_roll_handle=data["pending_roll_handle"],
        )


# ---------------------------------------------------------------------------
# All REQUEST type classes — used by gate tests to scan for hard bans
# ---------------------------------------------------------------------------

ALL_REQUEST_TYPES = (DeclareActionIntent, DiceTowerDropIntent)

# Banned action-verb names (doctrine §8).  No REQUEST type may use these.
BANNED_REQUEST_VERBS = frozenset({"ROLL", "CAST", "ATTACK", "END_TURN"})


# ---------------------------------------------------------------------------
# PENDING state machine
# ---------------------------------------------------------------------------

class PendingStateMachine:
    """Enforces the one-PENDING-at-a-time rule.

    Rules:
    - At most one PENDING is active.
    - Emitting a new PENDING cancels the old one.
    - Receiving the matching REQUEST clears the active PENDING.
    - Runtime can cancel explicitly.
    """

    def __init__(self) -> None:
        self._active: Optional[object] = None  # PendingRoll | PendingPoint | None

    @property
    def active(self) -> Optional[object]:
        return self._active

    def emit(self, pending: object) -> Optional[object]:
        """Emit a new PENDING, cancelling any existing one.

        Returns the cancelled PENDING (if any), or None.
        """
        cancelled = self._active
        self._active = pending
        return cancelled

    def resolve(self, request: object) -> bool:
        """Attempt to resolve the active PENDING with a REQUEST.

        Returns True if resolved (cleared), False if no match.
        For PendingRoll, expects a DiceTowerDropIntent whose pending_roll_handle
        matches the PendingRoll's pending_handle.
        """
        if self._active is None:
            return False

        if isinstance(self._active, PendingRoll) and isinstance(request, DiceTowerDropIntent):
            if request.pending_roll_handle == self._active.pending_handle:
                self._active = None
                return True

        # Generic clear: any REQUEST clears the active PENDING
        # (for PendingPoint + DeclareActionIntent, etc.)
        if isinstance(self._active, PendingPoint) and isinstance(request, DeclareActionIntent):
            self._active = None
            return True

        return False

    def cancel(self) -> Optional[object]:
        """Runtime cancels the active PENDING.

        Returns the cancelled PENDING, or None.
        """
        cancelled = self._active
        self._active = None
        return cancelled
