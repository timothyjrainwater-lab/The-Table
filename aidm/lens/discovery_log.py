"""Discovery Log — Lens-tier bestiary knowledge state machine.

Manages per-player, per-entity knowledge tiers and provides field-gated
queries for the notebook bestiary section.  All tier transitions happen
via explicit KnowledgeEvents only — no inference, no time-based logic.

Deterministic: same event stream → same knowledge state.

Architecture:
    KnowledgeEvent → DiscoveryLog.process_event() → internal state update
    DiscoveryLog.get_visible_fields() → field whitelist for notebook rendering

BOUNDARY LAW (BL-003): Lens must NOT import from core (BOX) directly.
May import from aidm/schemas/ for data types.

WO-DISCOVERY-BACKEND-001: Discovery Log Backend
Reference: docs/contracts/DISCOVERY_LOG.md (RQ-DISCOVERY-001)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Dict, FrozenSet, List, Mapping, Tuple

from aidm.schemas.knowledge_mask import (
    KnowledgeTier,
    REVEAL_SPEC,
)


# ---------------------------------------------------------------------------
# Knowledge Source Taxonomy
# ---------------------------------------------------------------------------

class KnowledgeSource(IntEnum):
    """Sources that can produce knowledge events.

    Maps to the six source types in the Discovery Log contract (§3.1).
    """
    ENCOUNTER = 1           # encounter_observation — visual contact
    SKILL_CHECK = 2         # study_action — deliberate study + skill check
    NPC_CONVERSATION = 3    # npc_report — NPC provides information
    SPECIAL_ABILITY = 4     # special — class feature, spell, etc.
    DOCUMENT = 5            # document_source — tome, inscription
    PARTY_SHARE = 6         # party_share — PC-to-PC knowledge sharing


# ---------------------------------------------------------------------------
# Knowledge Event
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class KnowledgeEvent:
    """An event that reveals creature information to a player.

    Frozen: events are immutable facts in the event stream.
    Timestamp is injected by the caller (BL-018), not generated internally.
    """
    player_id: str
    creature_type: str
    source: KnowledgeSource
    resulting_level: KnowledgeTier
    timestamp: str

    def __post_init__(self) -> None:
        if not self.player_id:
            raise ValueError("player_id must be non-empty")
        if not self.creature_type:
            raise ValueError("creature_type must be non-empty")
        if not self.timestamp:
            raise ValueError("timestamp must be non-empty")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "player_id": self.player_id,
            "creature_type": self.creature_type,
            "source": self.source.name,
            "resulting_level": self.resulting_level.name,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "KnowledgeEvent":
        return cls(
            player_id=data["player_id"],
            creature_type=data["creature_type"],
            source=KnowledgeSource[data["source"]],
            resulting_level=KnowledgeTier[data["resulting_level"]],
            timestamp=data["timestamp"],
        )


# ---------------------------------------------------------------------------
# Discovery Log State Machine
# ---------------------------------------------------------------------------

class DiscoveryLog:
    """Manages per-player creature knowledge progression.

    State is keyed by (player_id, creature_type). Each key maps to
    a KnowledgeTier that can only advance (never regress).

    Usage:
        log = DiscoveryLog()
        log.record_encounter("player_1", "goblin", KnowledgeTier.SEEN)
        tier = log.get_knowledge("player_1", "goblin")
        fields = log.get_visible_fields("player_1", "goblin")
    """

    def __init__(self) -> None:
        # (player_id, creature_type) → KnowledgeTier
        self._state: Dict[Tuple[str, str], KnowledgeTier] = {}
        # Append-only event ledger
        self._events: List[KnowledgeEvent] = []

    # -- Mutation ----------------------------------------------------------

    def record_encounter(
        self,
        player_id: str,
        creature_type: str,
        knowledge_level: KnowledgeTier,
    ) -> None:
        """Record that a player gained knowledge about a creature type.

        Knowledge only advances — if the player already has equal or higher
        knowledge, the call is a no-op for state (but idempotent, not an error).
        """
        key = (player_id, creature_type)
        current = self._state.get(key, KnowledgeTier.UNKNOWN)
        if knowledge_level > current:
            self._state[key] = knowledge_level

    def process_event(self, event: KnowledgeEvent) -> KnowledgeTier:
        """Process a KnowledgeEvent and return the resulting tier.

        The event is appended to the ledger and the state is updated.
        """
        self._events.append(event)
        self.record_encounter(
            event.player_id, event.creature_type, event.resulting_level,
        )
        return self.get_knowledge(event.player_id, event.creature_type)

    # -- Queries -----------------------------------------------------------

    def get_knowledge(
        self, player_id: str, creature_type: str,
    ) -> KnowledgeTier:
        """Query current knowledge level for a player/creature pair."""
        return self._state.get(
            (player_id, creature_type), KnowledgeTier.UNKNOWN,
        )

    def get_all_known(self, player_id: str) -> Dict[str, KnowledgeTier]:
        """Return all creatures this player has any knowledge of.

        Returns a dict mapping creature_type → KnowledgeTier for every
        creature the player has at least HEARD_OF.
        """
        return {
            creature_type: tier
            for (pid, creature_type), tier in sorted(self._state.items())
            if pid == player_id and tier > KnowledgeTier.UNKNOWN
        }

    def get_visible_fields(
        self, player_id: str, creature_type: str,
    ) -> FrozenSet[str]:
        """Return the set of field names visible at current knowledge level.

        Uses REVEAL_SPEC from aidm.schemas.knowledge_mask as the single
        source of truth for field gating.
        """
        tier = self.get_knowledge(player_id, creature_type)
        return REVEAL_SPEC[tier]

    @property
    def event_count(self) -> int:
        """Total number of events processed."""
        return len(self._events)

    # -- Serialization -----------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the discovery log for persistence.

        Format: state entries + event ledger (append-only JSONL compatible).
        """
        return {
            "state": {
                f"{pid}:{ctype}": tier.name
                for (pid, ctype), tier in sorted(self._state.items())
            },
            "events": [e.to_dict() for e in self._events],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DiscoveryLog":
        """Restore from serialized state."""
        log = cls()
        for key_str, tier_name in data.get("state", {}).items():
            pid, ctype = key_str.split(":", 1)
            log._state[(pid, ctype)] = KnowledgeTier[tier_name]
        for event_data in data.get("events", []):
            log._events.append(KnowledgeEvent.from_dict(event_data))
        return log
