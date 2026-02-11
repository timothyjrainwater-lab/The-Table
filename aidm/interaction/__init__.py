"""Interaction layer: Intent translation between voice and engine.

Bridges player-facing declared intents (string names) to engine-facing
resolved intents (entity IDs, Weapon objects, spell IDs).

WO-038: Intent Bridge
"""

from aidm.interaction.intent_bridge import (
    IntentBridge,
    ClarificationRequest,
    AmbiguityType,
)

__all__ = [
    "IntentBridge",
    "ClarificationRequest",
    "AmbiguityType",
]
