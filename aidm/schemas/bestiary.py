"""Bestiary schemas — frozen dataclasses for compiled creature catalog.

The World Compiler Stage 5 produces bestiary.json containing every creature
in the content pack, enriched with world-flavored names, descriptions,
habitat info, and presentation semantics bindings.

All dataclasses are frozen (immutable). The compiler writes them;
everything downstream reads them.

Reference: docs/contracts/WORLD_COMPILER.md §2.5
BOUNDARY LAW: No imports from aidm/core/ or aidm/lens/.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class BestiaryProvenance:
    """Provenance record tracing a bestiary entry to compile inputs."""

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
        return {
            "source": self.source,
            "compiler_version": self.compiler_version,
            "seed_used": self.seed_used,
            "content_pack_id": self.content_pack_id,
            "template_ids": list(self.template_ids),
            "llm_output_hash": self.llm_output_hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BestiaryProvenance":
        return cls(
            source=data["source"],
            compiler_version=data["compiler_version"],
            seed_used=data["seed_used"],
            content_pack_id=data.get("content_pack_id", ""),
            template_ids=tuple(data.get("template_ids", [])),
            llm_output_hash=data.get("llm_output_hash"),
        )


@dataclass(frozen=True)
class AbilityScores:
    """Creature ability scores (some may be None for mindless creatures)."""

    str_score: Optional[int] = None
    dex_score: Optional[int] = None
    con_score: Optional[int] = None
    int_score: Optional[int] = None
    wis_score: Optional[int] = None
    cha_score: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {}
        if self.str_score is not None:
            d["str"] = self.str_score
        if self.dex_score is not None:
            d["dex"] = self.dex_score
        if self.con_score is not None:
            d["con"] = self.con_score
        if self.int_score is not None:
            d["int"] = self.int_score
        if self.wis_score is not None:
            d["wis"] = self.wis_score
        if self.cha_score is not None:
            d["cha"] = self.cha_score
        return d

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "AbilityScores":
        if data is None:
            return cls()
        return cls(
            str_score=data.get("str"),
            dex_score=data.get("dex"),
            con_score=data.get("con"),
            int_score=data.get("int"),
            wis_score=data.get("wis"),
            cha_score=data.get("cha"),
        )


@dataclass(frozen=True)
class BestiaryEntry:
    """A single creature in the compiled bestiary.

    Combines Layer A (mechanical stat block from content pack),
    Layer B (presentation semantics from Stage 3), and
    Layer C (world-flavored names from Stage 1).
    """

    # -- Identity --------------------------------------------------------------
    content_id: str
    """Content pack identifier: 'creature.CREATURE_0001'."""

    world_name: str
    """World-flavored display name (from lexicon or stub)."""

    # -- Classification --------------------------------------------------------
    size_category: str
    """fine, diminutive, tiny, small, medium, large, huge, gargantuan, colossal."""

    creature_type: str
    """Primary creature type: aberration, animal, construct, etc."""

    subtypes: Tuple[str, ...] = ()
    """Subtypes in lowercase."""

    # -- Generated descriptions (stub or LLM) ----------------------------------
    appearance: str = ""
    """Visual description of the creature."""

    habitat: str = ""
    """Where this creature typically lives."""

    behavior_summary: str = ""
    """Behavioral traits and combat tendencies."""

    # -- Layer A: Mechanical stat block ----------------------------------------
    hit_dice: str = ""
    hp_typical: int = 0
    ac_total: int = 10
    ac_touch: int = 10
    ac_flat_footed: int = 10
    speed_ft: int = 0
    bab: int = 0
    fort_save: int = 0
    ref_save: int = 0
    will_save: int = 0
    ability_scores: AbilityScores = field(default_factory=AbilityScores)
    special_attacks: Tuple[str, ...] = ()
    special_qualities: Tuple[str, ...] = ()
    cr: float = 0.0
    intelligence_band: str = ""

    # -- Layer B: Presentation semantics ---------------------------------------
    vfx_tags: Tuple[str, ...] = ()
    sfx_tags: Tuple[str, ...] = ()

    # -- Provenance ------------------------------------------------------------
    provenance: BestiaryProvenance = field(
        default_factory=lambda: BestiaryProvenance(
            source="world_compiler", compiler_version="0.1.0", seed_used=0
        )
    )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-compatible dictionary."""
        d: Dict[str, Any] = {
            "content_id": self.content_id,
            "world_name": self.world_name,
            "size_category": self.size_category,
            "creature_type": self.creature_type,
        }
        if self.subtypes:
            d["subtypes"] = list(self.subtypes)
        d["appearance"] = self.appearance
        d["habitat"] = self.habitat
        d["behavior_summary"] = self.behavior_summary
        d["hit_dice"] = self.hit_dice
        d["hp_typical"] = self.hp_typical
        d["ac_total"] = self.ac_total
        d["ac_touch"] = self.ac_touch
        d["ac_flat_footed"] = self.ac_flat_footed
        d["speed_ft"] = self.speed_ft
        d["bab"] = self.bab
        d["fort_save"] = self.fort_save
        d["ref_save"] = self.ref_save
        d["will_save"] = self.will_save
        d["ability_scores"] = self.ability_scores.to_dict()
        if self.special_attacks:
            d["special_attacks"] = list(self.special_attacks)
        if self.special_qualities:
            d["special_qualities"] = list(self.special_qualities)
        d["cr"] = self.cr
        d["intelligence_band"] = self.intelligence_band
        if self.vfx_tags:
            d["vfx_tags"] = list(self.vfx_tags)
        if self.sfx_tags:
            d["sfx_tags"] = list(self.sfx_tags)
        d["provenance"] = self.provenance.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BestiaryEntry":
        """Deserialize from dictionary."""
        return cls(
            content_id=data["content_id"],
            world_name=data["world_name"],
            size_category=data["size_category"],
            creature_type=data["creature_type"],
            subtypes=tuple(data.get("subtypes", [])),
            appearance=data.get("appearance", ""),
            habitat=data.get("habitat", ""),
            behavior_summary=data.get("behavior_summary", ""),
            hit_dice=data.get("hit_dice", ""),
            hp_typical=data.get("hp_typical", 0),
            ac_total=data.get("ac_total", 10),
            ac_touch=data.get("ac_touch", 10),
            ac_flat_footed=data.get("ac_flat_footed", 10),
            speed_ft=data.get("speed_ft", 0),
            bab=data.get("bab", 0),
            fort_save=data.get("fort_save", 0),
            ref_save=data.get("ref_save", 0),
            will_save=data.get("will_save", 0),
            ability_scores=AbilityScores.from_dict(data.get("ability_scores")),
            special_attacks=tuple(data.get("special_attacks", [])),
            special_qualities=tuple(data.get("special_qualities", [])),
            cr=float(data.get("cr", 0.0)),
            intelligence_band=data.get("intelligence_band", ""),
            vfx_tags=tuple(data.get("vfx_tags", [])),
            sfx_tags=tuple(data.get("sfx_tags", [])),
            provenance=BestiaryProvenance.from_dict(data["provenance"]),
        )


@dataclass(frozen=True)
class BestiaryRegistry:
    """Compiled bestiary catalog — all creatures in a world.

    Frozen after compilation. Contains BestiaryEntry for every creature
    in the content pack, plus habitat distribution data.
    """

    schema_version: str
    """Schema version of the bestiary format."""

    world_id: str
    """World identity hash."""

    compiler_version: str = "0.1.0"
    """Compiler version that produced this registry."""

    creature_count: int = 0
    """Total number of creature entries."""

    entries: Tuple[BestiaryEntry, ...] = ()
    """All creature entries, sorted by content_id."""

    habitat_distribution: Dict[str, Tuple[str, ...]] = field(default_factory=dict)
    """Mapping of habitat tag to list of content_ids found there."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-compatible dictionary."""
        return {
            "schema_version": self.schema_version,
            "world_id": self.world_id,
            "compiler_version": self.compiler_version,
            "creature_count": self.creature_count,
            "entries": [e.to_dict() for e in self.entries],
            "habitat_distribution": {
                k: list(v) for k, v in self.habitat_distribution.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BestiaryRegistry":
        """Deserialize from dictionary."""
        entries = tuple(
            BestiaryEntry.from_dict(e) for e in data.get("entries", [])
        )
        habitat_raw = data.get("habitat_distribution", {})
        habitat = {k: tuple(v) for k, v in habitat_raw.items()}
        return cls(
            schema_version=data["schema_version"],
            world_id=data["world_id"],
            compiler_version=data.get("compiler_version", "0.1.0"),
            creature_count=data.get("creature_count", len(entries)),
            entries=entries,
            habitat_distribution=habitat,
        )
