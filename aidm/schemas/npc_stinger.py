"""NPC comedy stinger schema.

Defines the frozen Stinger dataclass for the comedy stinger content subsystem.
Each stinger is an immutable content entry: 3 credentials + 1 punchline,
delivered in staccato rhythm for NPC introductions and interjections.

WO-COMEDY-STINGERS-P1: Comedy Stinger Content Subsystem (Phase 1)

BOUNDARY LAW: No imports from aidm/core/, aidm/oracle/, aidm/director/,
or aidm/immersion/.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Dict, Mapping, Tuple


CANONICAL_ARCHETYPES = (
    "tavern_keeper",
    "town_guard",
    "merchant",
    "quest_giver",
    "petty_villain",
    "old_sage",
    "bard",
)

CANONICAL_DELIVERY_CONTEXTS = (
    "first_meeting",
    "post_combat_lull",
    "tavern_downtime",
    "quest_refusal",
    "callback",
)


@dataclass(frozen=True)
class Stinger:
    """A single NPC comedy stinger — immutable content entry.

    Fragments are exactly 4 strings: 3 credentials followed by 1 punchline.
    The staccato rhythm (credential-credential-credential-punchline) is
    enforced by the validator, not by this dataclass.
    """

    stinger_id: str                    # stable ID, format: "{archetype}_{nnn}"
    archetype: str                     # one of CANONICAL_ARCHETYPES
    delivery_contexts: Tuple[str, ...]  # subset of CANONICAL_DELIVERY_CONTEXTS
    fragments: Tuple[str, ...]        # exactly 4: [cred, cred, cred, punchline]
    tags: Mapping[str, Any]           # pace, pause_ms_before_punchline, emphasis_target, mood_hint

    def __post_init__(self) -> None:
        """Freeze mutable containers: List→tuple, Dict→MappingProxyType."""
        object.__setattr__(
            self, "delivery_contexts", tuple(self.delivery_contexts)
        )
        object.__setattr__(
            self, "fragments", tuple(self.fragments)
        )
        object.__setattr__(
            self, "tags", MappingProxyType(dict(self.tags))
        )

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> Stinger:
        """Construct a Stinger from a JSON-deserialized dict."""
        return cls(
            stinger_id=d["stinger_id"],
            archetype=d["archetype"],
            delivery_contexts=d["delivery_contexts"],
            fragments=d["fragments"],
            tags=d.get("tags", {}),
        )
