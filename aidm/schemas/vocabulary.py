"""Vocabulary object model — frozen dataclasses mirroring vocabulary_registry.schema.json.

These dataclasses define the runtime representation of the world's vocabulary
registry (lexicon). The World Compiler maps stable content_ids to world-flavored
names; these classes load and serve that data at runtime.

All dataclasses are frozen (immutable). The World Compiler writes them;
everything else reads them.

Reference: docs/schemas/vocabulary_registry.schema.json

BOUNDARY LAW: No imports from aidm/core/.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ═══════════════════════════════════════════════════════════════════════
# Domain enum values (match JSON schema exactly)
# ═══════════════════════════════════════════════════════════════════════

VALID_DOMAINS = frozenset({
    "spell",
    "feat",
    "skill",
    "class",
    "class_feature",
    "creature",
    "item",
    "condition",
    "action",
    "damage_type",
    "school",
    "terrain",
    "faction",
    "location",
    "cosmology",
})

VALID_TONE_REGISTERS = frozenset({
    "formal",
    "colloquial",
    "archaic",
    "technical",
    "mythic",
})

VALID_GENDER_CLASSES = frozenset({
    "masculine",
    "feminine",
    "neuter",
    "animate",
    "inanimate",
    None,
})

VALID_ARTICLES = frozenset({"a", "an", "the", None})


# ═══════════════════════════════════════════════════════════════════════
# Supporting types
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class LocalizationHooks:
    """Semantic anchors for future localization.

    Not translated text — structured data a translator can use.
    Matches LocalizationHooks in vocabulary_registry.schema.json.
    """

    semantic_root: str = ""
    """Language-independent semantic concept (e.g., 'fire_burst_projectile')."""

    tone_register: str = ""
    """Register/tone: formal, colloquial, archaic, technical, mythic."""

    gender_class: Optional[str] = None
    """Grammatical gender class (for languages that require it)."""

    syllable_count: Optional[int] = None
    """Syllable count of world_name (for rhythm-matching in localization)."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-compatible dictionary."""
        d: Dict[str, Any] = {}
        if self.semantic_root:
            d["semantic_root"] = self.semantic_root
        if self.tone_register:
            d["tone_register"] = self.tone_register
        if self.gender_class is not None:
            d["gender_class"] = self.gender_class
        if self.syllable_count is not None:
            d["syllable_count"] = self.syllable_count
        return d

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "LocalizationHooks":
        """Deserialize from dictionary."""
        if data is None:
            return cls()
        return cls(
            semantic_root=data.get("semantic_root", ""),
            tone_register=data.get("tone_register", ""),
            gender_class=data.get("gender_class"),
            syllable_count=data.get("syllable_count"),
        )


@dataclass(frozen=True)
class VocabularyProvenance:
    """Provenance record for a vocabulary entry.

    Tracks how this entry was generated (world compiler version, seed,
    content pack, templates used, LLM hash if applicable).

    Matches VocabularyProvenance in vocabulary_registry.schema.json.
    """

    source: str
    """Always 'world_compiler' for compiled entries."""

    compiler_version: str
    """Version of the compiler that generated this entry."""

    seed_used: int
    """Derived seed used for this entry's generation."""

    content_pack_id: str = ""
    """Content pack that provided the mechanical ID."""

    template_ids: tuple = ()
    """IDs of naming templates used."""

    llm_output_hash: Optional[str] = None
    """SHA-256 hash of LLM output used. None if no LLM was used."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-compatible dictionary."""
        result: Dict[str, Any] = {
            "source": self.source,
            "compiler_version": self.compiler_version,
            "seed_used": self.seed_used,
        }
        if self.content_pack_id:
            result["content_pack_id"] = self.content_pack_id
        result["template_ids"] = list(self.template_ids)
        result["llm_output_hash"] = self.llm_output_hash
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VocabularyProvenance":
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
class TaxonomySubcategory:
    """A subcategory within a taxonomy category.

    Matches the inline subcategory object in vocabulary_registry.schema.json.
    """

    subcategory_id: str
    """Stable subcategory identifier (e.g., 'fire_domain')."""

    display_name: str
    """World-flavored display name for this subcategory."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-compatible dictionary."""
        return {
            "subcategory_id": self.subcategory_id,
            "display_name": self.display_name,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaxonomySubcategory":
        """Deserialize from dictionary."""
        return cls(
            subcategory_id=data["subcategory_id"],
            display_name=data["display_name"],
        )


@dataclass(frozen=True)
class TaxonomyCategory:
    """A single taxonomy category with optional subcategories.

    Matches TaxonomyCategory in vocabulary_registry.schema.json.
    """

    category_id: str
    """Stable category identifier (e.g., 'destruction_magic')."""

    display_name: str
    """World-flavored display name for this category."""

    domain: str
    """Which vocabulary domain this category applies to (e.g., 'spell')."""

    subcategories: tuple = ()
    """Subcategories within this category. Tuple of TaxonomySubcategory."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-compatible dictionary."""
        d: Dict[str, Any] = {
            "category_id": self.category_id,
            "display_name": self.display_name,
            "domain": self.domain,
        }
        if self.subcategories:
            d["subcategories"] = [s.to_dict() for s in self.subcategories]
        else:
            d["subcategories"] = []
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaxonomyCategory":
        """Deserialize from dictionary."""
        subcategories = tuple(
            TaxonomySubcategory.from_dict(s)
            for s in data.get("subcategories", [])
        )
        return cls(
            category_id=data["category_id"],
            display_name=data["display_name"],
            domain=data["domain"],
            subcategories=subcategories,
        )


@dataclass(frozen=True)
class WorldTaxonomy:
    """World-specific classification tree.

    Defines how abilities, creatures, and entities are categorized
    in this world's vocabulary.

    Matches WorldTaxonomy in vocabulary_registry.schema.json.
    """

    categories: tuple
    """Top-level taxonomy categories, sorted by category_id.
    Tuple of TaxonomyCategory."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-compatible dictionary."""
        return {
            "categories": [c.to_dict() for c in self.categories],
        }

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "WorldTaxonomy":
        """Deserialize from dictionary."""
        if data is None:
            return cls(categories=())
        categories = tuple(
            TaxonomyCategory.from_dict(c)
            for c in data.get("categories", [])
        )
        return cls(categories=categories)


# ═══════════════════════════════════════════════════════════════════════
# Core types
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class VocabularyEntry:
    """A single vocabulary mapping: content_id -> world-flavored name.

    Maps a stable mechanical ID from the content pack to a world-flavored
    display name, with aliases, localization hooks, and taxonomy classification.

    Matches VocabularyEntry in vocabulary_registry.schema.json.
    """

    # Required fields
    content_id: str
    """Content pack identifier (e.g., 'spell.fireball', 'creature.goblin')."""

    lexicon_id: str
    """Deterministic stable ID: sha256(world_seed + content_id)[:16]."""

    domain: str
    """Vocabulary domain (e.g., 'spell', 'creature', 'feat')."""

    world_name: str
    """Canonical world-flavored display name."""

    category: str
    """World taxonomy category (e.g., 'destruction_magic')."""

    # Optional fields
    aliases: tuple = ()
    """Alternative names. Sorted alphabetically."""

    subcategory: Optional[str] = None
    """World taxonomy subcategory (e.g., 'fire_domain')."""

    short_description: str = ""
    """One-line world-flavored description (max 120 chars)."""

    article: Optional[str] = None
    """Grammatical article: 'a', 'an', 'the', or None."""

    plural_form: Optional[str] = None
    """Plural form of world_name. None if same as singular."""

    localization_hooks: LocalizationHooks = field(default_factory=LocalizationHooks)
    """Structured data for future localization."""

    ip_clean: bool = True
    """Compiler assertion that this name passes the Recognition Test."""

    provenance: Optional[VocabularyProvenance] = None
    """Provenance record for this entry."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-compatible dictionary."""
        d: Dict[str, Any] = {
            "content_id": self.content_id,
            "lexicon_id": self.lexicon_id,
            "domain": self.domain,
            "world_name": self.world_name,
            "category": self.category,
        }
        d["aliases"] = list(self.aliases)
        if self.subcategory is not None:
            d["subcategory"] = self.subcategory
        if self.short_description:
            d["short_description"] = self.short_description
        if self.article is not None:
            d["article"] = self.article
        if self.plural_form is not None:
            d["plural_form"] = self.plural_form
        hooks_dict = self.localization_hooks.to_dict()
        if hooks_dict:
            d["localization_hooks"] = hooks_dict
        d["ip_clean"] = self.ip_clean
        if self.provenance is not None:
            d["provenance"] = self.provenance.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VocabularyEntry":
        """Deserialize from dictionary."""
        return cls(
            content_id=data["content_id"],
            lexicon_id=data["lexicon_id"],
            domain=data["domain"],
            world_name=data["world_name"],
            category=data["category"],
            aliases=tuple(data.get("aliases", [])),
            subcategory=data.get("subcategory"),
            short_description=data.get("short_description", ""),
            article=data.get("article"),
            plural_form=data.get("plural_form"),
            localization_hooks=LocalizationHooks.from_dict(
                data.get("localization_hooks")
            ),
            ip_clean=data.get("ip_clean", True),
            provenance=(
                VocabularyProvenance.from_dict(data["provenance"])
                if "provenance" in data
                else None
            ),
        )


@dataclass(frozen=True)
class VocabularyRegistry:
    """Top-level vocabulary registry.

    Every mechanical ID in the content pack has exactly one canonical name
    in this world. Entries sorted by content_id for deterministic serialization.

    Matches VocabularyRegistry in vocabulary_registry.schema.json.
    """

    schema_version: str
    """Schema version of this registry file (major.minor)."""

    world_id: str
    """World identity hash — must match world_manifest.json world_id."""

    locale: str
    """BCP-47 locale tag (e.g., 'en', 'en-US')."""

    entries: tuple
    """All vocabulary entries, sorted by content_id. Tuple of VocabularyEntry."""

    naming_style: str = ""
    """Naming style from the world theme brief."""

    entry_count: Optional[int] = None
    """Total number of entries (for quick integrity check)."""

    taxonomy: Optional[WorldTaxonomy] = None
    """World-specific taxonomy tree."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-compatible dictionary."""
        d: Dict[str, Any] = {
            "schema_version": self.schema_version,
            "world_id": self.world_id,
            "locale": self.locale,
            "entries": [e.to_dict() for e in self.entries],
        }
        if self.naming_style:
            d["naming_style"] = self.naming_style
        if self.entry_count is not None:
            d["entry_count"] = self.entry_count
        else:
            d["entry_count"] = len(self.entries)
        if self.taxonomy is not None:
            d["taxonomy"] = self.taxonomy.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VocabularyRegistry":
        """Deserialize from dictionary."""
        entries = tuple(
            VocabularyEntry.from_dict(e)
            for e in data.get("entries", [])
        )
        taxonomy = None
        if "taxonomy" in data:
            taxonomy = WorldTaxonomy.from_dict(data["taxonomy"])
        return cls(
            schema_version=data.get("schema_version", "1.0"),
            world_id=data.get("world_id", ""),
            locale=data.get("locale", "en"),
            entries=entries,
            naming_style=data.get("naming_style", ""),
            entry_count=data.get("entry_count"),
            taxonomy=taxonomy,
        )
