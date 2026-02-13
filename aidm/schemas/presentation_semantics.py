"""AD-007: Presentation Semantics frozen dataclasses.

Mirrors the canonical JSON schema at:
  docs/schemas/presentation_semantics_registry.schema.json

These structured tags define how abilities and events BEHAVE VISUALLY
in a given world. Frozen at world compile time. Content-independent —
the same mechanical template can have different presentation semantics
in different worlds.

Three-layer description model:
  Layer A: Behavior (Box / Mechanics) — deterministic
  Layer B: Presentation Semantics (World Model) — frozen at world compile
  Layer C: Narration (Spark) — ephemeral

This module implements Layer B dataclasses.

BOUNDARY LAW: No imports from aidm.core — this is a schemas-layer component.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ═══════════════════════════════════════════════════════════════════════
# Enums (match JSON schema enum values exactly)
# ═══════════════════════════════════════════════════════════════════════


class DeliveryMode(Enum):
    """How the effect reaches its target (AD-007 Layer B)."""

    PROJECTILE = "projectile"
    BEAM = "beam"
    BURST_FROM_POINT = "burst_from_point"
    AURA = "aura"
    CONE = "cone"
    LINE = "line"
    TOUCH = "touch"
    SELF = "self"
    SUMMON = "summon"
    TELEPORT = "teleport"
    EMANATION = "emanation"
    GAZE = "gaze"


class Staging(Enum):
    """Temporal sequence of the effect (AD-007 Layer B)."""

    TRAVEL_THEN_DETONATE = "travel_then_detonate"
    INSTANT = "instant"
    LINGER = "linger"
    PULSES = "pulses"
    CHANNELED = "channeled"
    DELAYED = "delayed"
    EXPANDING = "expanding"
    FADING = "fading"


class OriginRule(Enum):
    """Where the effect originates visually (AD-007 Layer B)."""

    FROM_CASTER = "from_caster"
    FROM_CHOSEN_POINT = "from_chosen_point"
    FROM_OBJECT = "from_object"
    FROM_TARGET = "from_target"
    FROM_GROUND = "from_ground"
    AMBIENT = "ambient"


class Scale(Enum):
    """Perceived size/impact of the effect (AD-007 Layer B)."""

    SUBTLE = "subtle"
    MODERATE = "moderate"
    DRAMATIC = "dramatic"
    CATASTROPHIC = "catastrophic"


class NarrationPriority(Enum):
    """How eagerly Spark should narrate this event type."""

    ALWAYS_NARRATE = "always_narrate"
    NARRATE_IF_SIGNIFICANT = "narrate_if_significant"
    NARRATE_ON_REQUEST = "narrate_on_request"
    NEVER_NARRATE = "never_narrate"


class EventCategory(Enum):
    """Event category for default presentation semantics."""

    MELEE_ATTACK = "melee_attack"
    RANGED_ATTACK = "ranged_attack"
    COMBAT_MANEUVER = "combat_maneuver"
    SAVING_THROW = "saving_throw"
    SKILL_CHECK = "skill_check"
    CONDITION_APPLIED = "condition_applied"
    CONDITION_REMOVED = "condition_removed"
    HP_CHANGE = "hp_change"
    ENTITY_DEFEATED = "entity_defeated"
    MOVEMENT = "movement"
    ENVIRONMENTAL_DAMAGE = "environmental_damage"
    ENVIRONMENTAL_EFFECT = "environmental_effect"
    SOCIAL_INTERACTION = "social_interaction"
    DISCOVERY = "discovery"
    REST = "rest"
    TRADE = "trade"
    TURN_BOUNDARY = "turn_boundary"
    ROUND_BOUNDARY = "round_boundary"


# ═══════════════════════════════════════════════════════════════════════
# Frozen Dataclasses
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class SemanticsProvenance:
    """Provenance record for a presentation semantics entry.

    Tracks how this entry was generated (world compiler version, seed,
    content pack, templates used, LLM hash if applicable).
    """

    source: str
    compiler_version: str
    seed_used: int
    content_pack_id: Optional[str] = None
    template_ids: tuple = ()
    llm_output_hash: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict matching JSON schema field names."""
        result: Dict[str, Any] = {
            "source": self.source,
            "compiler_version": self.compiler_version,
            "seed_used": self.seed_used,
        }
        if self.content_pack_id is not None:
            result["content_pack_id"] = self.content_pack_id
        if self.template_ids:
            result["template_ids"] = list(self.template_ids)
        else:
            result["template_ids"] = []
        if self.llm_output_hash is not None:
            result["llm_output_hash"] = self.llm_output_hash
        else:
            result["llm_output_hash"] = None
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SemanticsProvenance":
        """Deserialize from dict matching JSON schema field names."""
        return cls(
            source=data["source"],
            compiler_version=data["compiler_version"],
            seed_used=data["seed_used"],
            content_pack_id=data.get("content_pack_id"),
            template_ids=tuple(data.get("template_ids", [])),
            llm_output_hash=data.get("llm_output_hash"),
        )


@dataclass(frozen=True)
class AbilityPresentationEntry:
    """AD-007 Layer B presentation semantics for a single ability.

    These structured tags tell Spark how to narrate, the battle map how
    to animate, and the discovery log what to progressively reveal.
    Frozen at compile time.

    Required fields (per JSON schema):
      content_id, delivery_mode, staging, origin_rule, vfx_tags,
      sfx_tags, scale, provenance

    Optional fields (have defaults in JSON schema):
      residue, ui_description, token_style, handout_style,
      contraindications
    """

    # Required fields
    content_id: str
    delivery_mode: DeliveryMode
    staging: Staging
    origin_rule: OriginRule
    vfx_tags: tuple
    sfx_tags: tuple
    scale: Scale
    provenance: SemanticsProvenance

    # Optional fields (with JSON schema defaults)
    residue: tuple = ()
    ui_description: Optional[str] = None
    token_style: Optional[str] = None
    handout_style: Optional[str] = None
    contraindications: tuple = ()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict matching JSON schema field names."""
        result: Dict[str, Any] = {
            "content_id": self.content_id,
            "delivery_mode": self.delivery_mode.value,
            "staging": self.staging.value,
            "origin_rule": self.origin_rule.value,
            "vfx_tags": list(self.vfx_tags),
            "sfx_tags": list(self.sfx_tags),
            "scale": self.scale.value,
            "provenance": self.provenance.to_dict(),
            "residue": list(self.residue),
            "contraindications": list(self.contraindications),
        }
        if self.ui_description is not None:
            result["ui_description"] = self.ui_description
        if self.token_style is not None:
            result["token_style"] = self.token_style
        if self.handout_style is not None:
            result["handout_style"] = self.handout_style
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AbilityPresentationEntry":
        """Deserialize from dict matching JSON schema field names."""
        return cls(
            content_id=data["content_id"],
            delivery_mode=DeliveryMode(data["delivery_mode"]),
            staging=Staging(data["staging"]),
            origin_rule=OriginRule(data["origin_rule"]),
            vfx_tags=tuple(data["vfx_tags"]),
            sfx_tags=tuple(data.get("sfx_tags", [])),
            scale=Scale(data["scale"]),
            provenance=SemanticsProvenance.from_dict(data["provenance"]),
            residue=tuple(data.get("residue", [])),
            ui_description=data.get("ui_description"),
            token_style=data.get("token_style"),
            handout_style=data.get("handout_style"),
            contraindications=tuple(data.get("contraindications", [])),
        )


@dataclass(frozen=True)
class EventPresentationEntry:
    """Default presentation semantics for an event category.

    Applies to events that don't have ability-specific semantics
    (e.g., generic melee hit, environmental damage, social interaction).
    """

    # Required fields
    event_category: EventCategory
    default_scale: Scale
    default_vfx_tags: tuple
    default_sfx_tags: tuple

    # Optional fields (with JSON schema defaults)
    default_residue: tuple = ()
    narration_priority: NarrationPriority = NarrationPriority.NARRATE_IF_SIGNIFICANT

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict matching JSON schema field names."""
        return {
            "event_category": self.event_category.value,
            "default_scale": self.default_scale.value,
            "default_vfx_tags": list(self.default_vfx_tags),
            "default_sfx_tags": list(self.default_sfx_tags),
            "default_residue": list(self.default_residue),
            "narration_priority": self.narration_priority.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EventPresentationEntry":
        """Deserialize from dict matching JSON schema field names."""
        return cls(
            event_category=EventCategory(data["event_category"]),
            default_scale=Scale(data["default_scale"]),
            default_vfx_tags=tuple(data.get("default_vfx_tags", [])),
            default_sfx_tags=tuple(data.get("default_sfx_tags", [])),
            default_residue=tuple(data.get("default_residue", [])),
            narration_priority=NarrationPriority(
                data.get("narration_priority", "narrate_if_significant"),
            ),
        )


@dataclass(frozen=True)
class PresentationSemanticsRegistry:
    """Top-level registry of all AD-007 Layer B presentation semantics.

    Every ability and event category in the content pack has a
    corresponding entry. Sorted by content_id / event_category
    for deterministic serialization.
    """

    schema_version: str
    world_id: str
    ability_entries: tuple
    event_entries: tuple
    compiler_version: Optional[str] = None
    ability_entry_count: Optional[int] = None
    event_entry_count: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict matching JSON schema field names."""
        result: Dict[str, Any] = {
            "schema_version": self.schema_version,
            "world_id": self.world_id,
            "ability_entries": [e.to_dict() for e in self.ability_entries],
            "event_entries": [e.to_dict() for e in self.event_entries],
        }
        if self.compiler_version is not None:
            result["compiler_version"] = self.compiler_version
        if self.ability_entry_count is not None:
            result["ability_entry_count"] = self.ability_entry_count
        else:
            result["ability_entry_count"] = len(self.ability_entries)
        if self.event_entry_count is not None:
            result["event_entry_count"] = self.event_entry_count
        else:
            result["event_entry_count"] = len(self.event_entries)
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PresentationSemanticsRegistry":
        """Deserialize from dict matching JSON schema field names."""
        ability_entries = tuple(
            AbilityPresentationEntry.from_dict(e)
            for e in data.get("ability_entries", [])
        )
        event_entries = tuple(
            EventPresentationEntry.from_dict(e)
            for e in data.get("event_entries", [])
        )
        return cls(
            schema_version=data["schema_version"],
            world_id=data["world_id"],
            compiler_version=data.get("compiler_version"),
            ability_entry_count=data.get("ability_entry_count"),
            event_entry_count=data.get("event_entry_count"),
            ability_entries=ability_entries,
            event_entries=event_entries,
        )
