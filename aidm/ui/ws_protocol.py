"""WebSocket protocol message types and registry for the Table UI.

RESULT types (Server → Client):
- RollResult: Authoritative dice roll outcome from the Box.

Message registry:
- MESSAGE_REGISTRY maps type strings to from_dict() constructors.
- parse_message() dispatches raw dicts to typed dataclass instances.

Non-negotiable:
- UI never generates randomness for outcomes. RollResult carries Box results.
- to_dict() output is deterministic for same inputs. No timestamps, no auto-IDs.
- No imports from aidm/core/. Direction is Box→UI, not UI→Box.

Authority: WO-UI-04, DOCTRINE_04_TABLE_UI_MEMO_V4.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Type


# ---------------------------------------------------------------------------
# RESULT types (Server → Client)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RollResult:
    """Authoritative dice roll outcome from the Box.

    Produced by the engine, received by the UI. The UI never generates
    these values — it only displays them.

    Attributes:
        d20_result: The face value of the d20 roll (1-20).
        total: The total after modifiers.
        success: Whether the roll met the target (hit/save/etc).
    """

    d20_result: int
    total: int
    success: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "roll_result",
            "d20_result": self.d20_result,
            "total": self.total,
            "success": self.success,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RollResult:
        return cls(
            d20_result=data["d20_result"],
            total=data["total"],
            success=data["success"],
        )


# ---------------------------------------------------------------------------
# Message registry — maps type strings to from_dict() constructors
# ---------------------------------------------------------------------------

MESSAGE_REGISTRY: Dict[str, Type] = {
    "roll_result": RollResult,
}


def parse_message(data: Dict[str, Any]) -> object:
    """Dispatch a raw message dict to a typed dataclass instance.

    Looks up the message type string in MESSAGE_REGISTRY and calls
    the corresponding from_dict() class method.

    Raises ValueError if the type string is not registered.
    """
    msg_type = data.get("type") or data.get("msg_type")
    if msg_type is None:
        raise ValueError("Message has no 'type' or 'msg_type' field")

    cls = MESSAGE_REGISTRY.get(msg_type)
    if cls is None:
        raise ValueError(
            f"Unknown message type: {msg_type!r}. "
            f"Registered types: {sorted(MESSAGE_REGISTRY.keys())}"
        )

    return cls.from_dict(data)
