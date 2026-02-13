"""Discovery Log service — bestiary knowledge mask state management.

Manages per-player, per-entity knowledge tiers and produces masked views
of entity data. All tier transitions happen via explicit events only.

Deterministic: same event stream → same knowledge state. No time-based
logic, no inference-based upgrades.

WO-CODE-DISCOVERY-001: Bestiary Knowledge Mask + Asset Binding Pools

.. deprecated::
    This module is deprecated. Use aidm.lens.discovery_log instead.
"""

from __future__ import annotations

import warnings

warnings.warn(
    "aidm.services.discovery_log is deprecated. Use aidm.lens.discovery_log instead. "
    "This module will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

from typing import Any, Dict, List, Mapping, Optional, Tuple

from aidm.schemas.knowledge_mask import (
    DiscoveryEvent,
    DiscoveryEventType,
    KnowledgeEntry,
    KnowledgeTier,
    MaskedEntityView,
    REVEAL_SPEC,
    TIER_TRANSITIONS,
)


class DiscoveryLog:
    """Manages progressive knowledge revelation for the bestiary.

    Each player has independent knowledge about each entity type.
    Knowledge advances only through explicit DiscoveryEvents.

    Usage:
        log = DiscoveryLog()
        log.apply_event(event)
        view = log.get_entry_view("player_1", "goblin_warrior", entity_data)
    """

    def __init__(self) -> None:
        # Key: (player_id, entity_id) → KnowledgeEntry
        self._entries: Dict[Tuple[str, str], KnowledgeEntry] = {}
        # Append-only event log for replay
        self._event_log: List[DiscoveryEvent] = []

    def apply_event(self, event: DiscoveryEvent) -> KnowledgeTier:
        """Apply a discovery event and return the new tier.

        If the event would advance the tier, it advances.
        If the player is already at or above the event's tier, no change.
        Tier never decreases.

        Args:
            event: The discovery event to apply.

        Returns:
            The player's tier for this entity after the event.
        """
        self._event_log.append(event)

        key = (event.player_id, event.entity_id)
        entry = self._entries.get(key)

        if entry is None:
            entry = KnowledgeEntry(
                player_id=event.player_id,
                entity_id=event.entity_id,
            )
            self._entries[key] = entry

        # Determine the tier this event can grant
        new_tier = TIER_TRANSITIONS[event.event_type]

        # Tier only advances, never decreases
        if new_tier > entry.tier:
            entry.tier = new_tier

        # Record observed facts (additive)
        for fact in event.observed_facts:
            if "=" in fact:
                field_name, value = fact.split("=", 1)
                entry.observed_facts[field_name.strip()] = value.strip()

        entry.event_log.append(event.to_dict())

        return entry.tier

    def get_tier(self, player_id: str, entity_id: str) -> KnowledgeTier:
        """Get the current knowledge tier for a player/entity pair."""
        key = (player_id, entity_id)
        entry = self._entries.get(key)
        if entry is None:
            return KnowledgeTier.UNKNOWN
        return entry.tier

    def get_entry(self, player_id: str, entity_id: str) -> Optional[KnowledgeEntry]:
        """Get the raw knowledge entry (for serialization/debugging)."""
        return self._entries.get((player_id, entity_id))

    def get_entry_view(
        self,
        player_id: str,
        entity_id: str,
        entity_data: Mapping[str, Any],
    ) -> MaskedEntityView:
        """Produce a masked view of an entity filtered by the player's knowledge tier.

        Only fields in REVEAL_SPEC[tier] are included. All other fields are
        absent from the view.

        Args:
            player_id: The player requesting the view.
            entity_id: The entity to view.
            entity_data: The full (unmasked) entity data dict.

        Returns:
            A MaskedEntityView containing only the revealed fields.
        """
        tier = self.get_tier(player_id, entity_id)
        allowed_fields = REVEAL_SPEC[tier]

        # Only include fields that are both allowed AND present in entity_data
        visible_fields: List[Tuple[str, Any]] = []
        for field_name in sorted(allowed_fields):
            if field_name in entity_data:
                visible_fields.append((field_name, entity_data[field_name]))

        return MaskedEntityView(
            entity_id=entity_id,
            player_id=player_id,
            tier=tier,
            fields=tuple(visible_fields),
        )

    def get_all_entries(self, player_id: str) -> List[KnowledgeEntry]:
        """Get all knowledge entries for a player (sorted by entity_id)."""
        entries = [
            entry for (pid, _), entry in self._entries.items()
            if pid == player_id
        ]
        return sorted(entries, key=lambda e: e.entity_id)

    @property
    def event_count(self) -> int:
        """Total number of events processed."""
        return len(self._event_log)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the entire discovery log for persistence."""
        return {
            "entries": {
                f"{k[0]}:{k[1]}": v.to_dict()
                for k, v in sorted(self._entries.items())
            },
            "event_count": len(self._event_log),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DiscoveryLog":
        """Restore from serialized state."""
        log = cls()
        for key_str, entry_data in data.get("entries", {}).items():
            entry = KnowledgeEntry.from_dict(entry_data)
            log._entries[(entry.player_id, entry.entity_id)] = entry
        return log
