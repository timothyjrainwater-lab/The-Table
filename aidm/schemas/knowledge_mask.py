"""Knowledge mask schemas for bestiary progressive revelation.

Defines per-player, per-entity knowledge tiers and field-level reveal specs.
Players progress through tiers via explicit events only — no inference-based
upgrades, no time-based reveals.

Knowledge Tiers:
    UNKNOWN  → Player has never encountered this entity type
    HEARD_OF → Rumor / NPC mention (name + type only)
    SEEN     → Visual encounter (appearance, size, speed)
    FOUGHT   → Combat observation (combat-relevant stats: AC range, attack pattern)
    STUDIED  → Deliberate study (full stat block, special abilities, vulnerabilities)

Each tier exposes a strict whitelist of fields. Fields not in the whitelist
are ABSENT from the masked view — not redacted, not zeroed, not ranged.
Absent means the key does not exist in the returned dict.

WO-CODE-DISCOVERY-001: Bestiary Knowledge Mask + Asset Binding Pools
Reference: docs/planning/RQ-TABLE-FOUNDATIONS-001.md (Topic B)
Reference: docs/specs/UX_VISION_PHYSICAL_TABLE.md (lines 84-98)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Dict, FrozenSet, List, Mapping, Optional, Tuple


# ---------------------------------------------------------------------------
# Knowledge Tiers
# ---------------------------------------------------------------------------

class KnowledgeTier(IntEnum):
    """Progressive knowledge levels for entity discovery.

    IntEnum so tiers are naturally ordered and comparable:
    UNKNOWN < HEARD_OF < SEEN < FOUGHT < STUDIED
    """
    UNKNOWN = 0
    HEARD_OF = 1
    SEEN = 2
    FOUGHT = 3
    STUDIED = 4


# ---------------------------------------------------------------------------
# Reveal Specification (whitelist per tier)
# ---------------------------------------------------------------------------

# Fields revealed at each tier. Each tier ADDS to the previous tier's fields.
# This is the SINGLE SOURCE OF TRUTH for what a player can see.

_HEARD_OF_FIELDS: FrozenSet[str] = frozenset({
    "entity_type",       # "beast", "undead", "humanoid", etc.
    "display_name",      # World-flavored creature name
    "size_category",     # "small", "medium", "large", etc.
    "rumor_text",        # Flavor text from NPC/lore source
})

_SEEN_FIELDS: FrozenSet[str] = _HEARD_OF_FIELDS | frozenset({
    "appearance",        # Physical description
    "speed",             # Movement speeds (walk, fly, swim, etc.)
    "senses",            # Darkvision, scent, etc.
    "natural_armor",     # Whether visibly armored
    "observed_weapons",  # Visible weapons/natural attacks
    "habitat",           # Where the creature was seen
})

_FOUGHT_FIELDS: FrozenSet[str] = _SEEN_FIELDS | frozenset({
    "ac_estimate",       # Qualitative: "lightly armored", "heavily armored"
    "hp_estimate",       # Qualitative: "fragile", "sturdy", "very tough"
    "attack_pattern",    # Observed attack types and approximate damage
    "save_estimates",    # Qualitative: "good reflexes", "poor willpower"
    "observed_abilities",  # Abilities seen in combat (not full list)
    "resistances_observed",  # Resistances/immunities observed in combat
    "morale_behavior",   # Did it flee? Fight to death? Call for help?
})

_STUDIED_FIELDS: FrozenSet[str] = _FOUGHT_FIELDS | frozenset({
    "ac",                # Exact AC value
    "hp_max",            # Exact max HP
    "hit_dice",          # Hit dice formula
    "base_attack_bonus", # BAB
    "attack_details",    # Full attack routine with bonuses and damage
    "saves_exact",       # Exact Fort/Ref/Will saves
    "special_abilities", # Complete list of special abilities
    "special_qualities", # Complete list of special qualities
    "damage_reduction",  # Exact DR (e.g., "DR 5/magic")
    "spell_resistance",  # Exact SR value
    "vulnerabilities",   # Full vulnerability list
    "skill_ranks",       # Skill ranks
    "feats",             # Feat list
    "challenge_rating",  # CR
    "lore_text",         # Full bestiary lore
})

# Canonical tier → field mapping
REVEAL_SPEC: Dict[KnowledgeTier, FrozenSet[str]] = {
    KnowledgeTier.UNKNOWN: frozenset(),
    KnowledgeTier.HEARD_OF: _HEARD_OF_FIELDS,
    KnowledgeTier.SEEN: _SEEN_FIELDS,
    KnowledgeTier.FOUGHT: _FOUGHT_FIELDS,
    KnowledgeTier.STUDIED: _STUDIED_FIELDS,
}


# ---------------------------------------------------------------------------
# Discovery Events
# ---------------------------------------------------------------------------

class DiscoveryEventType(IntEnum):
    """Types of events that can advance knowledge tiers."""
    ENCOUNTER_SEEN = 1
    COMBAT_OBSERVED = 2
    STUDY_SUCCESS = 3
    NPC_TOLD_YOU = 4


@dataclass(frozen=True)
class DiscoveryEvent:
    """A single discovery event that may advance a knowledge tier.

    Frozen: events are immutable facts in the event stream.
    """
    event_type: DiscoveryEventType
    player_id: str
    entity_id: str
    observed_facts: Tuple[str, ...] = ()
    metadata: Tuple[Tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not self.player_id:
            raise ValueError("player_id must be non-empty")
        if not self.entity_id:
            raise ValueError("entity_id must be non-empty")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type.name,
            "player_id": self.player_id,
            "entity_id": self.entity_id,
            "observed_facts": list(self.observed_facts),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DiscoveryEvent":
        return cls(
            event_type=DiscoveryEventType[data["event_type"]],
            player_id=data["player_id"],
            entity_id=data["entity_id"],
            observed_facts=tuple(data.get("observed_facts", ())),
            metadata=tuple(
                (k, v) for k, v in data.get("metadata", {}).items()
            ),
        )


# ---------------------------------------------------------------------------
# Tier Transition Rules (deterministic)
# ---------------------------------------------------------------------------

# Each event type advances the tier to AT LEAST this level.
# If the player is already at or above this level, no change.
TIER_TRANSITIONS: Dict[DiscoveryEventType, KnowledgeTier] = {
    DiscoveryEventType.NPC_TOLD_YOU: KnowledgeTier.HEARD_OF,
    DiscoveryEventType.ENCOUNTER_SEEN: KnowledgeTier.SEEN,
    DiscoveryEventType.COMBAT_OBSERVED: KnowledgeTier.FOUGHT,
    DiscoveryEventType.STUDY_SUCCESS: KnowledgeTier.STUDIED,
}


# ---------------------------------------------------------------------------
# Knowledge Entry (per player, per entity)
# ---------------------------------------------------------------------------

@dataclass
class KnowledgeEntry:
    """A player's knowledge about a specific entity type.

    Mutable: tier advances as events arrive. But only via apply_event().
    """
    player_id: str
    entity_id: str
    tier: KnowledgeTier = KnowledgeTier.UNKNOWN
    observed_facts: Dict[str, str] = field(default_factory=dict)
    event_log: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "player_id": self.player_id,
            "entity_id": self.entity_id,
            "tier": self.tier.name,
            "observed_facts": dict(self.observed_facts),
            "event_log": list(self.event_log),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "KnowledgeEntry":
        return cls(
            player_id=data["player_id"],
            entity_id=data["entity_id"],
            tier=KnowledgeTier[data["tier"]],
            observed_facts=dict(data.get("observed_facts", {})),
            event_log=list(data.get("event_log", [])),
        )


# ---------------------------------------------------------------------------
# Masked View
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MaskedEntityView:
    """A player-visible view of an entity, filtered by knowledge tier.

    Only fields in REVEAL_SPEC[tier] are present in `fields`.
    All other entity data is absent (not redacted, not zeroed — absent).
    """
    entity_id: str
    player_id: str
    tier: KnowledgeTier
    fields: Tuple[Tuple[str, Any], ...]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "player_id": self.player_id,
            "tier": self.tier.name,
            "fields": dict(self.fields),
        }

    def get_field(self, field_name: str) -> Optional[Any]:
        """Get a field value, or None if not revealed at this tier."""
        for k, v in self.fields:
            if k == field_name:
                return v
        return None

    @property
    def field_names(self) -> FrozenSet[str]:
        """Set of field names present in this view."""
        return frozenset(k for k, _ in self.fields)
