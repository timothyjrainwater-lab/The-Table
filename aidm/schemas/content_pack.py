"""Content pack schemas for the mechanical extraction pipeline.

Defines skin-stripped mechanical templates for game content. These templates
contain only Bone (math/formulas) and Muscle (behavioral contracts). All
Skin (names, prose, flavor) is stripped during extraction and regenerated
by the World Compiler at compile time.

The content pack is the database that the World Compiler consumes.

WO-CONTENT-EXTRACT-001: Mechanical Extraction Pipeline — Spells
WO-CONTENT-PACK-SCHEMA-001: Content Pack Shared Dataclasses
Reference: docs/specs/RQ-PRODUCT-001_CONTENT_INDEPENDENCE_ARCHITECTURE.md

BOUNDARY LAW: No imports from aidm/core/.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, fields as dc_fields
from typing import Any, Dict, Mapping, Optional, Tuple


# ═══════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════

def _tuple_from_list(val: Any) -> tuple:
    """Convert a list (from JSON) to a tuple."""
    if val is None:
        return ()
    if isinstance(val, tuple):
        return val
    if isinstance(val, list):
        return tuple(val)
    return (val,)


def _to_json_value(val: Any) -> Any:
    """Convert a dataclass field value to a JSON-serializable form."""
    if isinstance(val, tuple):
        return [_to_json_value(v) for v in val]
    if isinstance(val, Mapping):
        return {k: _to_json_value(v) for k, v in val.items()}
    return val


@dataclass(frozen=True)
class MechanicalSpellTemplate:
    """A single spell's bone + muscle, with all skin stripped.

    This is the content pack entry format. The World Compiler
    consumes these to generate world-flavored spell entries.

    IP Firewall: No original names, no prose, no flavor text.
    Only formulas, enums, numbers, and flags.
    """

    # -- Identity (no name field) ------------------------------------------
    template_id: str
    """Sequential ID in SPELL_NNN format. No original name."""

    # -- Level / School ----------------------------------------------------
    tier: int
    """Minimum spell level across all classes (0-9)."""

    school_category: str
    """Spell school: abjuration, conjuration, divination, enchantment,
    evocation, illusion, necromancy, transmutation, universal."""

    subschool: Optional[str] = None
    """Optional subschool: creation, healing, charm, compulsion,
    figment, glamer, pattern, shadow, summoning, teleportation, etc."""

    descriptors: Tuple[str, ...] = ()
    """Spell descriptors: fire, cold, acid, mind-affecting, death, etc."""

    # -- Class / Level pairs -----------------------------------------------
    class_levels: Tuple[Tuple[str, int], ...] = ()
    """All class/level pairs, e.g. (('sor_wiz', 3), ('clr', 4)).
    Class abbreviations are lowercased and slash-joined."""

    # -- Targeting ---------------------------------------------------------
    target_type: str = "single"
    """How the spell selects targets: single, area, self, touch, ray."""

    range_formula: Optional[str] = None
    """Range formula: 'close', 'medium', 'long', 'touch', 'personal',
    'unlimited', or a fixed distance like '30'. None if variable."""

    aoe_shape: Optional[str] = None
    """AoE shape: burst, cone, line, emanation, spread, cylinder,
    sphere, or None for non-area spells."""

    aoe_radius_ft: Optional[int] = None
    """AoE radius/length in feet, or None."""

    # -- Effect ------------------------------------------------------------
    effect_type: str = "utility"
    """Primary effect: damage, healing, buff, debuff, utility."""

    damage_formula: Optional[str] = None
    """Damage dice expression: '8d6', '1d6_per_CL_max_10d6', etc."""

    damage_type: Optional[str] = None
    """Damage type: fire, cold, acid, electricity, sonic, force,
    positive, negative, untyped, or None."""

    healing_formula: Optional[str] = None
    """Healing dice expression: '1d8+CL_max_5', etc."""

    # -- Resolution --------------------------------------------------------
    save_type: Optional[str] = None
    """Save type: fortitude, reflex, will, or None."""

    save_effect: Optional[str] = None
    """Save effect: half, negates, partial, none, or None."""

    spell_resistance: bool = False
    """Whether spell resistance applies."""

    requires_attack_roll: bool = False
    """Whether the spell requires an attack roll (touch/ray)."""

    auto_hit: bool = False
    """Whether the spell automatically hits (e.g. magic missile)."""

    # -- Timing ------------------------------------------------------------
    casting_time: str = "standard"
    """Casting time: standard, full_round, 1_round, 10_min, 1_min,
    1_hour, 24_hour, see_text, free, swift, immediate."""

    duration_formula: Optional[str] = None
    """Duration formula: '1_round_per_CL', '10_min_per_CL',
    '1_hour_per_CL', 'instantaneous', 'permanent',
    'concentration', 'see_text', or None."""

    concentration: bool = False
    """Whether the spell requires concentration."""

    dismissible: bool = False
    """Whether the spell can be dismissed early."""

    # -- Components (boolean flags only) -----------------------------------
    verbal: bool = False
    """Requires verbal component."""

    somatic: bool = False
    """Requires somatic component."""

    material: bool = False
    """Requires material component (no description stored)."""

    focus: bool = False
    """Requires a focus item."""

    divine_focus: bool = False
    """Requires a divine focus."""

    xp_cost: bool = False
    """Requires an XP cost."""

    # -- Conditions --------------------------------------------------------
    conditions_applied: Tuple[str, ...] = ()
    """Conditions this spell applies: blinded, deafened, paralyzed,
    stunned, nauseated, frightened, etc."""

    conditions_duration: Optional[str] = None
    """How long conditions last: save_ends, 1_round, duration, etc."""

    # -- Classification ----------------------------------------------------
    combat_role_tags: Tuple[str, ...] = ()
    """Combat role: direct_damage, area_control, single_target_damage,
    healing, buff, debuff, battlefield_control, support, utility."""

    delivery_mode: str = "instantaneous"
    """Delivery mode: projectile, ray, burst_from_point, touch,
    self, emanation, cone, line, instantaneous, summon, teleport."""

    # -- Provenance (internal only) ----------------------------------------
    source_page: str = ""
    """Source page reference: 'PHB p.231'."""

    source_id: str = ""
    """Source document ID: '681f92bc94ff'."""

    # -- Inheritance -------------------------------------------------------
    inherits_from_template: Optional[str] = None
    """Template ID of parent spell for 'as X except' spells."""

    def __post_init__(self) -> None:
        if not self.template_id.startswith("SPELL_"):
            raise ValueError(
                f"template_id must start with 'SPELL_': {self.template_id}"
            )
        if not (0 <= self.tier <= 9):
            raise ValueError(f"tier must be 0-9: {self.tier}")
        if not self.school_category:
            raise ValueError("school_category must not be empty")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "template_id": self.template_id,
            "tier": self.tier,
            "school_category": self.school_category,
            "subschool": self.subschool,
            "descriptors": list(self.descriptors),
            "class_levels": [list(cl) for cl in self.class_levels],
            "target_type": self.target_type,
            "range_formula": self.range_formula,
            "aoe_shape": self.aoe_shape,
            "aoe_radius_ft": self.aoe_radius_ft,
            "effect_type": self.effect_type,
            "damage_formula": self.damage_formula,
            "damage_type": self.damage_type,
            "healing_formula": self.healing_formula,
            "save_type": self.save_type,
            "save_effect": self.save_effect,
            "spell_resistance": self.spell_resistance,
            "requires_attack_roll": self.requires_attack_roll,
            "auto_hit": self.auto_hit,
            "casting_time": self.casting_time,
            "duration_formula": self.duration_formula,
            "concentration": self.concentration,
            "dismissible": self.dismissible,
            "verbal": self.verbal,
            "somatic": self.somatic,
            "material": self.material,
            "focus": self.focus,
            "divine_focus": self.divine_focus,
            "xp_cost": self.xp_cost,
            "conditions_applied": list(self.conditions_applied),
            "conditions_duration": self.conditions_duration,
            "combat_role_tags": list(self.combat_role_tags),
            "delivery_mode": self.delivery_mode,
            "source_page": self.source_page,
            "source_id": self.source_id,
            "inherits_from_template": self.inherits_from_template,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "MechanicalSpellTemplate":
        """Deserialize from dict."""
        return cls(
            template_id=data["template_id"],
            tier=data["tier"],
            school_category=data["school_category"],
            subschool=data.get("subschool"),
            descriptors=tuple(data.get("descriptors", ())),
            class_levels=tuple(
                tuple(cl) for cl in data.get("class_levels", ())
            ),
            target_type=data.get("target_type", "single"),
            range_formula=data.get("range_formula"),
            aoe_shape=data.get("aoe_shape"),
            aoe_radius_ft=data.get("aoe_radius_ft"),
            effect_type=data.get("effect_type", "utility"),
            damage_formula=data.get("damage_formula"),
            damage_type=data.get("damage_type"),
            healing_formula=data.get("healing_formula"),
            save_type=data.get("save_type"),
            save_effect=data.get("save_effect"),
            spell_resistance=data.get("spell_resistance", False),
            requires_attack_roll=data.get("requires_attack_roll", False),
            auto_hit=data.get("auto_hit", False),
            casting_time=data.get("casting_time", "standard"),
            duration_formula=data.get("duration_formula"),
            concentration=data.get("concentration", False),
            dismissible=data.get("dismissible", False),
            verbal=data.get("verbal", False),
            somatic=data.get("somatic", False),
            material=data.get("material", False),
            focus=data.get("focus", False),
            divine_focus=data.get("divine_focus", False),
            xp_cost=data.get("xp_cost", False),
            conditions_applied=tuple(data.get("conditions_applied", ())),
            conditions_duration=data.get("conditions_duration"),
            combat_role_tags=tuple(data.get("combat_role_tags", ())),
            delivery_mode=data.get("delivery_mode", "instantaneous"),
            source_page=data.get("source_page", ""),
            source_id=data.get("source_id", ""),
            inherits_from_template=data.get("inherits_from_template"),
        )


# ═══════════════════════════════════════════════════════════════════════
# MechanicalCreatureTemplate
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class MechanicalCreatureTemplate:
    """A single creature's mechanical stat block (bone + muscle, zero skin).

    Field names match the actual JSON in aidm/data/content_pack/creatures.json.

    Deviations from WO-CONTENT-PACK-SCHEMA-001 spec:
    - Added advancement (str) — present in live creatures.json
    - Added level_adjustment (str) — present in live creatures.json
    - Added treasure (str) — present in live creatures.json
    """

    # -- Identity --------------------------------------------------------------
    template_id: str
    """Sequential ID in CREATURE_NNNN format. No original name."""

    # -- Classification --------------------------------------------------------
    size_category: str
    """fine, diminutive, tiny, small, medium, large, huge, gargantuan, colossal."""

    creature_type: str
    """aberration, animal, construct, dragon, elemental, fey, giant,
    humanoid, magical beast, monstrous humanoid, ooze, outsider,
    plant, undead, vermin."""

    subtypes: Tuple[str, ...] = ()
    """Subtypes in lowercase."""

    # -- Core stats ------------------------------------------------------------
    hit_dice: str = ""
    """Hit dice expression: '8d8+40'."""

    hp_typical: int = 0
    """Average HP from hit dice."""

    initiative_mod: int = 0
    """Initiative modifier."""

    speed_ft: int = 0
    """Base land speed in feet."""

    speed_modes: Dict[str, int] = None  # type: ignore[assignment]
    """Additional movement modes: {'fly': 60, 'swim': 30}."""

    # -- Defense ---------------------------------------------------------------
    ac_total: int = 10
    """Total Armor Class."""

    ac_touch: int = 10
    """Touch AC."""

    ac_flat_footed: int = 10
    """Flat-footed AC."""

    ac_components: Dict[str, int] = None  # type: ignore[assignment]
    """AC component breakdown: {'natural': 7, 'dex': 1}."""

    # -- Offense ---------------------------------------------------------------
    bab: int = 0
    """Base attack bonus."""

    grapple_mod: int = 0
    """Grapple modifier."""

    attacks: Tuple[Any, ...] = ()
    """Single attack entries (list of dicts with description, bonus, damage)."""

    full_attacks: Tuple[Any, ...] = ()
    """Full attack entries."""

    space_ft: int = 5
    """Space occupied in feet."""

    reach_ft: int = 5
    """Natural reach in feet."""

    # -- Saves -----------------------------------------------------------------
    fort_save: int = 0
    ref_save: int = 0
    will_save: int = 0

    # -- Ability scores --------------------------------------------------------
    str_score: Optional[int] = None
    dex_score: Optional[int] = None
    con_score: Optional[int] = None
    int_score: Optional[int] = None
    wis_score: Optional[int] = None
    cha_score: Optional[int] = None

    # -- Special abilities -----------------------------------------------------
    special_attacks: Tuple[str, ...] = ()
    special_qualities: Tuple[str, ...] = ()

    # -- Challenge Rating / Classification -------------------------------------
    cr: float = 0.0
    alignment_tendency: str = ""
    environment_tags: Tuple[str, ...] = ()

    # -- Tactical --------------------------------------------------------------
    intelligence_band: str = ""
    """mindless, animal, low, average, high, genius."""

    organization_patterns: Tuple[str, ...] = ()

    # -- Provenance ------------------------------------------------------------
    source_page: str = ""
    source_id: str = ""

    # -- Advancement (raw text from stat block) --------------------------------
    advancement: str = ""
    level_adjustment: str = ""
    treasure: str = ""

    def __post_init__(self) -> None:
        # Fix mutable default for speed_modes and ac_components
        # WO-AUDIT-003: Freeze dict fields to prevent post-construction mutation
        from types import MappingProxyType
        if self.speed_modes is None:
            object.__setattr__(self, "speed_modes", MappingProxyType({}))
        elif isinstance(self.speed_modes, dict):
            object.__setattr__(self, "speed_modes", MappingProxyType(self.speed_modes))
        if self.ac_components is None:
            object.__setattr__(self, "ac_components", MappingProxyType({}))
        elif isinstance(self.ac_components, dict):
            object.__setattr__(self, "ac_components", MappingProxyType(self.ac_components))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        d: Dict[str, Any] = {}
        for f in dc_fields(self):
            val = getattr(self, f.name)
            d[f.name] = _to_json_value(val)
        return d

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "MechanicalCreatureTemplate":
        """Deserialize from dict."""
        # attacks and full_attacks are lists of dicts in JSON
        attacks_raw = data.get("attacks", [])
        attacks = tuple(
            a if isinstance(a, dict) else {"description": str(a)}
            for a in attacks_raw
        )
        full_attacks_raw = data.get("full_attacks", [])
        full_attacks = tuple(
            a if isinstance(a, dict) else {"description": str(a)}
            for a in full_attacks_raw
        )

        return cls(
            template_id=data["template_id"],
            size_category=data["size_category"],
            creature_type=data["creature_type"],
            subtypes=_tuple_from_list(data.get("subtypes", ())),
            hit_dice=data.get("hit_dice", ""),
            hp_typical=data.get("hp_typical", 0),
            initiative_mod=data.get("initiative_mod", 0),
            speed_ft=data.get("speed_ft", 0),
            speed_modes=dict(data.get("speed_modes", {})),
            ac_total=data.get("ac_total", 10),
            ac_touch=data.get("ac_touch", 10),
            ac_flat_footed=data.get("ac_flat_footed", 10),
            ac_components=dict(data.get("ac_components", {})),
            bab=data.get("bab", 0),
            grapple_mod=data.get("grapple_mod", 0),
            attacks=attacks,
            full_attacks=full_attacks,
            space_ft=data.get("space_ft", 5),
            reach_ft=data.get("reach_ft", 5),
            fort_save=data.get("fort_save", 0),
            ref_save=data.get("ref_save", 0),
            will_save=data.get("will_save", 0),
            str_score=data.get("str_score"),
            dex_score=data.get("dex_score"),
            con_score=data.get("con_score"),
            int_score=data.get("int_score"),
            wis_score=data.get("wis_score"),
            cha_score=data.get("cha_score"),
            special_attacks=_tuple_from_list(data.get("special_attacks", ())),
            special_qualities=_tuple_from_list(data.get("special_qualities", ())),
            cr=float(data.get("cr", 0.0)),
            alignment_tendency=data.get("alignment_tendency", ""),
            environment_tags=_tuple_from_list(data.get("environment_tags", ())),
            intelligence_band=data.get("intelligence_band", ""),
            organization_patterns=_tuple_from_list(data.get("organization_patterns", ())),
            source_page=data.get("source_page", ""),
            source_id=data.get("source_id", ""),
            advancement=data.get("advancement", ""),
            level_adjustment=data.get("level_adjustment", ""),
            treasure=data.get("treasure", ""),
        )


# ═══════════════════════════════════════════════════════════════════════
# MechanicalFeatTemplate
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class MechanicalFeatTemplate:
    """A single feat's mechanical data (bone + muscle, zero skin).

    Field names match the actual JSON in aidm/data/content_pack/feats.json.
    """

    # -- Identity --------------------------------------------------------------
    template_id: str
    """Sequential ID in FEAT_NNN format. No original name."""

    feat_type: str
    """general, metamagic, item_creation."""

    # -- Prerequisites ---------------------------------------------------------
    prereq_ability_scores: Dict[str, int] = None  # type: ignore[assignment]
    """Ability score minimums: {'str': 13, 'dex': 15}."""

    prereq_bab: Optional[int] = None
    """Minimum BAB required."""

    prereq_feat_refs: Tuple[str, ...] = ()
    """Prerequisite feat template_ids: ('FEAT_003',)."""

    prereq_class_features: Tuple[str, ...] = ()
    """Required class features: ('turn_undead',)."""

    prereq_caster_level: Optional[int] = None
    """Minimum caster level."""

    prereq_other: Tuple[str, ...] = ()
    """Freeform mechanical prerequisites."""

    # -- Mechanical effect -----------------------------------------------------
    effect_type: str = "special_action"
    """attack_modifier, skill_modifier, save_modifier, ac_modifier,
    damage_modifier, action_economy, special_action, proficiency,
    passive_defense, metamagic_modifier, item_creation, etc."""

    bonus_value: Optional[int] = None
    bonus_type: Optional[str] = None
    bonus_applies_to: Optional[str] = None

    # -- Trigger / Action economy ----------------------------------------------
    trigger: Optional[str] = None
    replaces_normal: Optional[str] = None
    grants_action: Optional[str] = None
    removes_penalty: Optional[str] = None

    # -- Conditional -----------------------------------------------------------
    stacks_with: Tuple[str, ...] = ()
    limited_to: Optional[str] = None

    # -- Fighter bonus ---------------------------------------------------------
    fighter_bonus_eligible: bool = False

    # -- Repeatable ------------------------------------------------------------
    can_take_multiple: bool = False
    effects_stack: bool = False

    # -- Metamagic -------------------------------------------------------------
    metamagic_slot_increase: Optional[int] = None

    # -- Provenance ------------------------------------------------------------
    source_page: str = ""
    source_id: str = ""

    def __post_init__(self) -> None:
        # WO-AUDIT-003: Freeze dict fields to prevent post-construction mutation
        from types import MappingProxyType
        if self.prereq_ability_scores is None:
            object.__setattr__(self, "prereq_ability_scores", MappingProxyType({}))
        elif isinstance(self.prereq_ability_scores, dict):
            object.__setattr__(self, "prereq_ability_scores", MappingProxyType(self.prereq_ability_scores))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        d: Dict[str, Any] = {}
        for f in dc_fields(self):
            val = getattr(self, f.name)
            d[f.name] = _to_json_value(val)
        return d

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "MechanicalFeatTemplate":
        """Deserialize from dict."""
        return cls(
            template_id=data["template_id"],
            feat_type=data["feat_type"],
            prereq_ability_scores=dict(data.get("prereq_ability_scores", {})),
            prereq_bab=data.get("prereq_bab"),
            prereq_feat_refs=_tuple_from_list(data.get("prereq_feat_refs", ())),
            prereq_class_features=_tuple_from_list(data.get("prereq_class_features", ())),
            prereq_caster_level=data.get("prereq_caster_level"),
            prereq_other=_tuple_from_list(data.get("prereq_other", ())),
            effect_type=data.get("effect_type", "special_action"),
            bonus_value=data.get("bonus_value"),
            bonus_type=data.get("bonus_type"),
            bonus_applies_to=data.get("bonus_applies_to"),
            trigger=data.get("trigger"),
            replaces_normal=data.get("replaces_normal"),
            grants_action=data.get("grants_action"),
            removes_penalty=data.get("removes_penalty"),
            stacks_with=_tuple_from_list(data.get("stacks_with", ())),
            limited_to=data.get("limited_to"),
            fighter_bonus_eligible=data.get("fighter_bonus_eligible", False),
            can_take_multiple=data.get("can_take_multiple", False),
            effects_stack=data.get("effects_stack", False),
            metamagic_slot_increase=data.get("metamagic_slot_increase"),
            source_page=data.get("source_page", ""),
            source_id=data.get("source_id", ""),
        )


# ═══════════════════════════════════════════════════════════════════════
# ContentPack — top-level container
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ContentPack:
    """Top-level container for all content pack data.

    Aggregates spells, creatures, and feats into a single immutable bundle.
    The pack_id is a deterministic hash of the sorted file hashes.
    """

    schema_version: str
    pack_id: str
    spells: Tuple[MechanicalSpellTemplate, ...] = ()
    creatures: Tuple[MechanicalCreatureTemplate, ...] = ()
    feats: Tuple[MechanicalFeatTemplate, ...] = ()
    source_ids: Tuple[str, ...] = ()
    extraction_versions: Dict[str, str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        # WO-AUDIT-003: Freeze dict fields to prevent post-construction mutation
        from types import MappingProxyType
        if self.extraction_versions is None:
            object.__setattr__(self, "extraction_versions", MappingProxyType({}))
        elif isinstance(self.extraction_versions, dict):
            object.__setattr__(self, "extraction_versions", MappingProxyType(self.extraction_versions))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "schema_version": self.schema_version,
            "pack_id": self.pack_id,
            "spells": [s.to_dict() for s in self.spells],
            "creatures": [c.to_dict() for c in self.creatures],
            "feats": [f.to_dict() for f in self.feats],
            "source_ids": list(self.source_ids),
            "extraction_versions": dict(self.extraction_versions),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ContentPack":
        """Deserialize from dict."""
        spells = tuple(
            MechanicalSpellTemplate.from_dict(s)
            for s in data.get("spells", [])
        )
        creatures = tuple(
            MechanicalCreatureTemplate.from_dict(c)
            for c in data.get("creatures", [])
        )
        feats = tuple(
            MechanicalFeatTemplate.from_dict(f)
            for f in data.get("feats", [])
        )
        return cls(
            schema_version=data.get("schema_version", "1.0.0"),
            pack_id=data.get("pack_id", ""),
            spells=spells,
            creatures=creatures,
            feats=feats,
            source_ids=_tuple_from_list(data.get("source_ids", ())),
            extraction_versions=dict(data.get("extraction_versions", {})),
        )


def compute_pack_id(*file_paths: str) -> str:
    """Compute a deterministic pack_id from sorted file content hashes.

    Args:
        *file_paths: Paths to content pack JSON files.

    Returns:
        First 32 hex chars of sha256(sorted hashes).
    """
    hashes = []
    for path in sorted(file_paths):
        try:
            with open(path, "rb") as f:
                h = hashlib.sha256(f.read()).hexdigest()
                hashes.append(h)
        except FileNotFoundError:
            continue
    combined = "|".join(sorted(hashes))
    return hashlib.sha256(combined.encode()).hexdigest()[:32]
