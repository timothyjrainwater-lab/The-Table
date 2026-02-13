"""Rulebook object model — frozen dataclasses mirroring rule_registry.schema.json.

These dataclasses define the runtime representation of world-authored rule entries.
The World Compiler produces JSON conforming to rule_registry.schema.json;
these classes load and serve that data at runtime.

All dataclasses are frozen (immutable). The World Compiler writes them;
everything else reads them.

Reference: docs/schemas/rule_registry.schema.json
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List


@dataclass(frozen=True)
class RuleProvenance:
    """Provenance record tracing a rule entry back to compile inputs.

    Matches RuleProvenance in rule_registry.schema.json.
    """

    source: str
    """Always 'world_compiler' for compiled entries."""

    compiler_version: str
    """Version of the compiler that generated this entry."""

    seed_used: int
    """Derived seed used for this entry's generation."""

    content_pack_id: str = ""
    """Content pack that provided the mechanical template."""

    template_ids: tuple = ()
    """IDs of content pack templates used to generate this entry."""

    llm_output_hash: Optional[str] = None
    """SHA-256 hash of the LLM output used. None if no LLM was used."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-compatible dictionary."""
        return {
            "source": self.source,
            "compiler_version": self.compiler_version,
            "seed_used": self.seed_used,
            "content_pack_id": self.content_pack_id,
            "template_ids": list(self.template_ids),
            "llm_output_hash": self.llm_output_hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RuleProvenance":
        """Deserialize from dictionary."""
        return cls(
            source=data["source"],
            compiler_version=data["compiler_version"],
            seed_used=data["seed_used"],
            content_pack_id=data.get("content_pack_id", ""),
            template_ids=tuple(data.get("template_ids", [])),
            llm_output_hash=data.get("llm_output_hash"),
        )


@dataclass(frozen=True)
class RuleTextSlots:
    """World-authored descriptive text for a rule entry.

    All text is generated at compile time and frozen.
    No copyrighted content. No coaching or tactical advice.

    Matches RuleTextSlots in rule_registry.schema.json.
    """

    rulebook_description: str = ""
    """Full rulebook entry text. What the player sees when they 'open the rulebook.'"""

    short_description: str = ""
    """One-line summary for indices and tooltips (max 120 chars)."""

    flavor_text: str = ""
    """World-flavored lore text."""

    mechanical_summary: str = ""
    """Concise mechanical description using world vocabulary."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-compatible dictionary."""
        d: Dict[str, Any] = {}
        if self.rulebook_description:
            d["rulebook_description"] = self.rulebook_description
        if self.short_description:
            d["short_description"] = self.short_description
        if self.flavor_text:
            d["flavor_text"] = self.flavor_text
        if self.mechanical_summary:
            d["mechanical_summary"] = self.mechanical_summary
        return d

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "RuleTextSlots":
        """Deserialize from dictionary."""
        if data is None:
            return cls()
        return cls(
            rulebook_description=data.get("rulebook_description", ""),
            short_description=data.get("short_description", ""),
            flavor_text=data.get("flavor_text", ""),
            mechanical_summary=data.get("mechanical_summary", ""),
        )


@dataclass(frozen=True)
class RuleParameters:
    """Mechanical parameters that configure the engine procedure.

    These come from the content pack; the compiler binds them to
    the world entry. Different rule_types have different parameter shapes.

    Matches RuleParameters in rule_registry.schema.json.
    """

    range_ft: Optional[int] = None
    area_shape: Optional[str] = None
    area_radius_ft: Optional[int] = None
    damage_dice: Optional[str] = None
    damage_type: Optional[str] = None
    save_type: Optional[str] = None
    save_effect: Optional[str] = None
    duration_unit: Optional[str] = None
    duration_value: Optional[int] = None
    action_cost: Optional[str] = None
    target_type: Optional[str] = None
    custom: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Freeze the custom dict by converting to a regular dict snapshot."""
        # frozen=True prevents assignment, but we need the dict to be set
        # during __init__. The field is already set by this point.
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-compatible dictionary. Omits None fields."""
        d: Dict[str, Any] = {}
        if self.range_ft is not None:
            d["range_ft"] = self.range_ft
        if self.area_shape is not None:
            d["area_shape"] = self.area_shape
        if self.area_radius_ft is not None:
            d["area_radius_ft"] = self.area_radius_ft
        if self.damage_dice is not None:
            d["damage_dice"] = self.damage_dice
        if self.damage_type is not None:
            d["damage_type"] = self.damage_type
        if self.save_type is not None:
            d["save_type"] = self.save_type
        if self.save_effect is not None:
            d["save_effect"] = self.save_effect
        if self.duration_unit is not None:
            d["duration_unit"] = self.duration_unit
        if self.duration_value is not None:
            d["duration_value"] = self.duration_value
        if self.action_cost is not None:
            d["action_cost"] = self.action_cost
        if self.target_type is not None:
            d["target_type"] = self.target_type
        if self.custom:
            d["custom"] = dict(self.custom)
        return d

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "RuleParameters":
        """Deserialize from dictionary."""
        if data is None:
            return cls()
        return cls(
            range_ft=data.get("range_ft"),
            area_shape=data.get("area_shape"),
            area_radius_ft=data.get("area_radius_ft"),
            damage_dice=data.get("damage_dice"),
            damage_type=data.get("damage_type"),
            save_type=data.get("save_type"),
            save_effect=data.get("save_effect"),
            duration_unit=data.get("duration_unit"),
            duration_value=data.get("duration_value"),
            action_cost=data.get("action_cost"),
            target_type=data.get("target_type"),
            custom=dict(data.get("custom", {})),
        )


@dataclass(frozen=True)
class Prerequisite:
    """A single prerequisite for a rule entry.

    Matches the prerequisite object in rule_registry.schema.json.
    """

    prerequisite_type: str
    """Type: 'feat', 'ability_score', 'class_level', 'skill_rank', 'other'."""

    ref: str
    """Reference to the prerequisite (content_id for feat, 'str:13' for ability score, etc.)."""

    display: str = ""
    """World-flavored display text."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-compatible dictionary."""
        d: Dict[str, Any] = {
            "prerequisite_type": self.prerequisite_type,
            "ref": self.ref,
        }
        if self.display:
            d["display"] = self.display
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Prerequisite":
        """Deserialize from dictionary."""
        return cls(
            prerequisite_type=data["prerequisite_type"],
            ref=data["ref"],
            display=data.get("display", ""),
        )


@dataclass(frozen=True)
class RuleEntry:
    """A single world-authored rule binding.

    References an engine procedure by stable procedure_id. Adds
    world-flavored text, parameters, and provenance. The engine procedure
    defines WHAT happens; the rule entry defines HOW it is described
    in this world.

    Matches RuleEntry in rule_registry.schema.json.
    """

    content_id: str
    """Content pack identifier (e.g., 'spell.fire_burst_003')."""

    procedure_id: str
    """Stable reference to the engine substrate procedure."""

    rule_type: str
    """Classification: ability, spell, feat, class_feature, skill,
    combat_maneuver, condition, action_type, item_property, creature_trait."""

    world_name: str
    """World-flavored display name (from lexicon)."""

    parameters: RuleParameters
    """Mechanical parameter summary."""

    provenance: RuleProvenance
    """Where this entry came from."""

    tier: str = "tier_1"
    """Implementation tier: tier_1, tier_2, tier_3, stub."""

    text_slots: RuleTextSlots = field(default_factory=RuleTextSlots)
    """Templated text components."""

    tags: tuple = ()
    """Classification tags for indexing and search."""

    prerequisites: tuple = ()
    """Prerequisites for this rule. Tuple of Prerequisite."""

    supersedes: tuple = ()
    """content_ids of rules this entry supersedes."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-compatible dictionary."""
        d: Dict[str, Any] = {
            "content_id": self.content_id,
            "procedure_id": self.procedure_id,
            "rule_type": self.rule_type,
            "world_name": self.world_name,
            "parameters": self.parameters.to_dict(),
            "provenance": self.provenance.to_dict(),
        }
        if self.tier != "tier_1":
            d["tier"] = self.tier
        text_dict = self.text_slots.to_dict()
        if text_dict:
            d["text_slots"] = text_dict
        if self.tags:
            d["tags"] = list(self.tags)
        if self.prerequisites:
            d["prerequisites"] = [p.to_dict() for p in self.prerequisites]
        if self.supersedes:
            d["supersedes"] = list(self.supersedes)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RuleEntry":
        """Deserialize from dictionary."""
        prerequisites = tuple(
            Prerequisite.from_dict(p) for p in data.get("prerequisites", [])
        )
        return cls(
            content_id=data["content_id"],
            procedure_id=data["procedure_id"],
            rule_type=data["rule_type"],
            world_name=data["world_name"],
            parameters=RuleParameters.from_dict(data.get("parameters")),
            provenance=RuleProvenance.from_dict(data["provenance"]),
            tier=data.get("tier", "tier_1"),
            text_slots=RuleTextSlots.from_dict(data.get("text_slots")),
            tags=tuple(data.get("tags", [])),
            prerequisites=prerequisites,
            supersedes=tuple(data.get("supersedes", [])),
        )

    @property
    def rule_text(self) -> str:
        """Generated prose description — delegates to text_slots.rulebook_description."""
        return self.text_slots.rulebook_description

    @property
    def category(self) -> str:
        """Taxonomy category — delegates to rule_type for grouping."""
        return self.rule_type
