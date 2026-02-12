"""Stage 3: Presentation Semantics Binding.

WO-WORLDCOMPILE-SEMANTICS-001 — Assigns AD-007 presentation semantics
(Layer B) to every ability and event category in the content pack.

Uses rule-based mapping from mechanical data to presentation semantics.
Optional LLM enrichment for world-themed variants (not implemented in
stub mode).

BOUNDARY LAW: This is a core-layer component. Imports from aidm.schemas
are allowed. No imports from aidm.lens or aidm.narration.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from aidm.core.compile_stages._base import CompileContext, CompileStage, StageResult
from aidm.schemas.presentation_semantics import (
    AbilityPresentationEntry,
    DeliveryMode,
    EventCategory,
    EventPresentationEntry,
    NarrationPriority,
    OriginRule,
    PresentationSemanticsRegistry,
    Scale,
    SemanticsProvenance,
    Staging,
)


# ═══════════════════════════════════════════════════════════════════════
# Rule-based mapping tables
# ═══════════════════════════════════════════════════════════════════════

# VFX tags by damage type
VFX_BY_DAMAGE_TYPE: Dict[str, Tuple[str, ...]] = {
    "fire": ("fire", "glow", "heat_distortion"),
    "cold": ("frost", "ice_crystals", "mist"),
    "electricity": ("lightning", "spark", "arc"),
    "acid": ("acid", "dissolve", "hiss"),
    "sonic": ("shockwave", "ripple"),
    "force": ("shimmer", "pulse"),
    "positive energy": ("radiance", "warmth"),
    "negative energy": ("shadow", "drain"),
}

# VFX tags by school category
VFX_BY_SCHOOL: Dict[str, Tuple[str, ...]] = {
    "necromancy": ("shadow", "decay"),
    "illusion": ("shimmer", "distortion"),
    "enchantment": ("glow", "mesmerize"),
    "divination": ("glow", "reveal"),
    "abjuration": ("shield", "ward"),
    "transmutation": ("morph", "shift"),
    "conjuration": ("materialize", "portal"),
    "evocation": ("energy", "blast"),
}

# VFX tags by effect type
VFX_BY_EFFECT_TYPE: Dict[str, Tuple[str, ...]] = {
    "healing": ("radiance", "warmth"),
    "summoning": ("portal", "materialize"),
    "buff": ("glow", "aura"),
    "debuff": ("dim", "weaken"),
}

# SFX tags by damage type
SFX_BY_DAMAGE_TYPE: Dict[str, Tuple[str, ...]] = {
    "fire": ("whoosh", "crackle"),
    "cold": ("crystallize", "shatter"),
    "electricity": ("zap", "thunder"),
    "acid": ("sizzle", "bubble"),
    "sonic": ("boom", "rumble"),
    "force": ("hum", "pulse"),
}

# SFX tags by effect type
SFX_BY_EFFECT_TYPE: Dict[str, Tuple[str, ...]] = {
    "healing": ("chime", "swell"),
    "summoning": ("whoosh", "materialize"),
    "buff": ("chime", "hum"),
    "debuff": ("drone", "fade"),
}

# Default event category semantics
EVENT_DEFAULTS: Dict[EventCategory, Dict[str, Any]] = {
    EventCategory.MELEE_ATTACK: {
        "default_scale": Scale.MODERATE,
        "default_vfx_tags": ("impact", "sparks"),
        "default_sfx_tags": ("clang", "thud"),
        "narration_priority": NarrationPriority.ALWAYS_NARRATE,
    },
    EventCategory.RANGED_ATTACK: {
        "default_scale": Scale.MODERATE,
        "default_vfx_tags": ("projectile", "trail"),
        "default_sfx_tags": ("whoosh", "thunk"),
        "narration_priority": NarrationPriority.ALWAYS_NARRATE,
    },
    EventCategory.COMBAT_MANEUVER: {
        "default_scale": Scale.MODERATE,
        "default_vfx_tags": ("motion_blur",),
        "default_sfx_tags": ("grunt", "impact"),
        "narration_priority": NarrationPriority.ALWAYS_NARRATE,
    },
    EventCategory.SAVING_THROW: {
        "default_scale": Scale.SUBTLE,
        "default_vfx_tags": ("shield_flash",),
        "default_sfx_tags": ("hum",),
        "narration_priority": NarrationPriority.NARRATE_IF_SIGNIFICANT,
    },
    EventCategory.SKILL_CHECK: {
        "default_scale": Scale.SUBTLE,
        "default_vfx_tags": (),
        "default_sfx_tags": (),
        "narration_priority": NarrationPriority.NARRATE_IF_SIGNIFICANT,
    },
    EventCategory.CONDITION_APPLIED: {
        "default_scale": Scale.MODERATE,
        "default_vfx_tags": ("status_icon",),
        "default_sfx_tags": ("chime",),
        "narration_priority": NarrationPriority.ALWAYS_NARRATE,
    },
    EventCategory.CONDITION_REMOVED: {
        "default_scale": Scale.SUBTLE,
        "default_vfx_tags": ("fade_out",),
        "default_sfx_tags": ("release",),
        "narration_priority": NarrationPriority.NARRATE_IF_SIGNIFICANT,
    },
    EventCategory.HP_CHANGE: {
        "default_scale": Scale.MODERATE,
        "default_vfx_tags": ("number_pop",),
        "default_sfx_tags": ("hit",),
        "narration_priority": NarrationPriority.ALWAYS_NARRATE,
    },
    EventCategory.ENTITY_DEFEATED: {
        "default_scale": Scale.DRAMATIC,
        "default_vfx_tags": ("collapse", "fade"),
        "default_sfx_tags": ("thud", "silence"),
        "narration_priority": NarrationPriority.ALWAYS_NARRATE,
    },
    EventCategory.MOVEMENT: {
        "default_scale": Scale.SUBTLE,
        "default_vfx_tags": ("footstep_dust",),
        "default_sfx_tags": ("footstep",),
        "narration_priority": NarrationPriority.NARRATE_ON_REQUEST,
    },
    EventCategory.ENVIRONMENTAL_DAMAGE: {
        "default_scale": Scale.MODERATE,
        "default_vfx_tags": ("hazard_glow",),
        "default_sfx_tags": ("crackle",),
        "narration_priority": NarrationPriority.ALWAYS_NARRATE,
    },
    EventCategory.ENVIRONMENTAL_EFFECT: {
        "default_scale": Scale.MODERATE,
        "default_vfx_tags": ("ambient_shift",),
        "default_sfx_tags": ("rumble",),
        "narration_priority": NarrationPriority.NARRATE_IF_SIGNIFICANT,
    },
    EventCategory.SOCIAL_INTERACTION: {
        "default_scale": Scale.SUBTLE,
        "default_vfx_tags": (),
        "default_sfx_tags": ("speech",),
        "narration_priority": NarrationPriority.ALWAYS_NARRATE,
    },
    EventCategory.DISCOVERY: {
        "default_scale": Scale.MODERATE,
        "default_vfx_tags": ("reveal_glow",),
        "default_sfx_tags": ("chime",),
        "narration_priority": NarrationPriority.ALWAYS_NARRATE,
    },
    EventCategory.REST: {
        "default_scale": Scale.SUBTLE,
        "default_vfx_tags": ("fade_to_calm",),
        "default_sfx_tags": ("ambient",),
        "narration_priority": NarrationPriority.NARRATE_IF_SIGNIFICANT,
    },
    EventCategory.TRADE: {
        "default_scale": Scale.SUBTLE,
        "default_vfx_tags": ("coin_glint",),
        "default_sfx_tags": ("coin_clink",),
        "narration_priority": NarrationPriority.NARRATE_ON_REQUEST,
    },
    EventCategory.TURN_BOUNDARY: {
        "default_scale": Scale.SUBTLE,
        "default_vfx_tags": (),
        "default_sfx_tags": (),
        "narration_priority": NarrationPriority.NEVER_NARRATE,
    },
    EventCategory.ROUND_BOUNDARY: {
        "default_scale": Scale.SUBTLE,
        "default_vfx_tags": (),
        "default_sfx_tags": (),
        "narration_priority": NarrationPriority.NEVER_NARRATE,
    },
}


# ═══════════════════════════════════════════════════════════════════════
# Mechanical-to-Semantics Mapper
# ═══════════════════════════════════════════════════════════════════════


def map_delivery_mode(spell: Dict[str, Any]) -> DeliveryMode:
    """Map a spell's mechanical data to a DeliveryMode enum value."""
    target_type = spell.get("target_type", "")
    aoe_shape = spell.get("aoe_shape")
    effect_type = spell.get("effect_type", "")
    range_formula = spell.get("range_formula", "")

    if target_type == "ray":
        return DeliveryMode.BEAM
    if target_type == "touch":
        return DeliveryMode.TOUCH
    if target_type == "self":
        return DeliveryMode.SELF

    if aoe_shape == "burst":
        return DeliveryMode.BURST_FROM_POINT
    if aoe_shape == "cone":
        return DeliveryMode.CONE
    if aoe_shape == "line":
        return DeliveryMode.LINE
    if aoe_shape == "emanation":
        return DeliveryMode.EMANATION
    if aoe_shape == "spread":
        return DeliveryMode.BURST_FROM_POINT

    if effect_type == "summoning":
        return DeliveryMode.SUMMON

    if target_type == "area":
        return DeliveryMode.BURST_FROM_POINT

    if target_type == "single" and range_formula not in ("touch", "personal", ""):
        return DeliveryMode.PROJECTILE

    return DeliveryMode.PROJECTILE


def map_staging(spell: Dict[str, Any]) -> Staging:
    """Map a spell's mechanical data to a Staging enum value."""
    duration = spell.get("duration_formula", "")
    concentration = spell.get("concentration", False)
    aoe_shape = spell.get("aoe_shape")

    # burst + instantaneous is more specific, check first
    if aoe_shape == "burst" and duration == "instantaneous":
        return Staging.TRAVEL_THEN_DETONATE

    if duration == "instantaneous":
        return Staging.INSTANT

    if concentration:
        return Staging.CHANNELED

    if duration and "round" in str(duration).lower():
        return Staging.LINGER

    return Staging.INSTANT


def map_scale(spell: Dict[str, Any]) -> Scale:
    """Map a spell's mechanical data to a Scale enum value."""
    aoe_radius = spell.get("aoe_radius_ft") or 0
    tier = spell.get("tier", 0)

    if aoe_radius >= 40 or tier >= 7:
        return Scale.CATASTROPHIC
    if aoe_radius >= 20 or tier >= 5:
        return Scale.DRAMATIC
    if aoe_radius >= 10 or tier >= 3:
        return Scale.MODERATE
    return Scale.SUBTLE


def map_origin_rule(spell: Dict[str, Any]) -> OriginRule:
    """Map a spell's mechanical data to an OriginRule enum value."""
    target_type = spell.get("target_type", "")
    aoe_shape = spell.get("aoe_shape")
    effect_type = spell.get("effect_type", "")

    if target_type in ("self", "touch", "ray"):
        return OriginRule.FROM_CASTER
    if aoe_shape in ("burst", "spread"):
        return OriginRule.FROM_CHOSEN_POINT
    if aoe_shape in ("emanation", "cone"):
        return OriginRule.FROM_CASTER
    if effect_type == "summoning":
        return OriginRule.FROM_CHOSEN_POINT
    return OriginRule.FROM_CASTER


def map_vfx_tags(spell: Dict[str, Any]) -> Tuple[str, ...]:
    """Derive VFX tags from mechanical data."""
    tags: List[str] = []
    damage_type = spell.get("damage_type", "")
    school = spell.get("school_category", "")
    effect_type = spell.get("effect_type", "")

    if damage_type and damage_type in VFX_BY_DAMAGE_TYPE:
        tags.extend(VFX_BY_DAMAGE_TYPE[damage_type])
    if effect_type and effect_type in VFX_BY_EFFECT_TYPE:
        tags.extend(VFX_BY_EFFECT_TYPE[effect_type])
    if school and school in VFX_BY_SCHOOL:
        tags.extend(VFX_BY_SCHOOL[school])

    # Deduplicate while preserving order
    seen: set = set()
    deduped: List[str] = []
    for tag in tags:
        if tag not in seen:
            seen.add(tag)
            deduped.append(tag)
    return tuple(deduped) if deduped else ("generic_magic",)


def map_sfx_tags(spell: Dict[str, Any]) -> Tuple[str, ...]:
    """Derive SFX tags from mechanical data."""
    tags: List[str] = []
    damage_type = spell.get("damage_type", "")
    effect_type = spell.get("effect_type", "")

    if damage_type and damage_type in SFX_BY_DAMAGE_TYPE:
        tags.extend(SFX_BY_DAMAGE_TYPE[damage_type])
    if effect_type and effect_type in SFX_BY_EFFECT_TYPE:
        tags.extend(SFX_BY_EFFECT_TYPE[effect_type])

    # Deduplicate while preserving order
    seen: set = set()
    deduped: List[str] = []
    for tag in tags:
        if tag not in seen:
            seen.add(tag)
            deduped.append(tag)
    return tuple(deduped) if deduped else ("generic_cast",)


def map_spell_to_entry(
    spell: Dict[str, Any],
    provenance: SemanticsProvenance,
) -> AbilityPresentationEntry:
    """Map a single spell's mechanical data to an AbilityPresentationEntry."""
    return AbilityPresentationEntry(
        content_id=f"spell.{spell['template_id'].lower()}",
        delivery_mode=map_delivery_mode(spell),
        staging=map_staging(spell),
        origin_rule=map_origin_rule(spell),
        vfx_tags=map_vfx_tags(spell),
        sfx_tags=map_sfx_tags(spell),
        scale=map_scale(spell),
        provenance=provenance,
    )


def is_active_feat(feat: Dict[str, Any]) -> bool:
    """Return True if the feat has active presentation semantics.

    Only feats with a trigger or grants_action get ability entries.
    Passive feats (proficiency, skill modifiers) are excluded.
    """
    trigger = feat.get("trigger")
    grants_action = feat.get("grants_action")
    return bool(trigger) or bool(grants_action)


def map_feat_to_entry(
    feat: Dict[str, Any],
    provenance: SemanticsProvenance,
) -> AbilityPresentationEntry:
    """Map an active feat to an AbilityPresentationEntry."""
    delivery_mode = DeliveryMode.SELF
    staging = Staging.INSTANT
    origin_rule = OriginRule.FROM_CASTER
    scale = Scale.SUBTLE

    grants_action = feat.get("grants_action", "") or ""
    if "attack" in grants_action or "hit" in grants_action:
        delivery_mode = DeliveryMode.TOUCH
        scale = Scale.MODERATE
    if "ranged" in grants_action:
        delivery_mode = DeliveryMode.PROJECTILE

    vfx = map_vfx_tags(feat)
    sfx = map_sfx_tags(feat)

    return AbilityPresentationEntry(
        content_id=f"feat.{feat['template_id'].lower()}",
        delivery_mode=delivery_mode,
        staging=staging,
        origin_rule=origin_rule,
        vfx_tags=vfx,
        sfx_tags=sfx,
        scale=scale,
        provenance=provenance,
    )


def build_event_defaults() -> Tuple[EventPresentationEntry, ...]:
    """Build default EventPresentationEntry for all 18 EventCategory values."""
    entries = []
    for cat in EventCategory:
        defaults = EVENT_DEFAULTS[cat]
        entries.append(EventPresentationEntry(
            event_category=cat,
            default_scale=defaults["default_scale"],
            default_vfx_tags=defaults["default_vfx_tags"],
            default_sfx_tags=defaults["default_sfx_tags"],
            narration_priority=defaults["narration_priority"],
        ))
    return tuple(entries)


# ═══════════════════════════════════════════════════════════════════════
# SemanticsStage
# ═══════════════════════════════════════════════════════════════════════


class SemanticsStage(CompileStage):
    """Stage 3: Generate AD-007 presentation semantics bindings."""

    COMPILER_VERSION = "0.1.0"
    SCHEMA_VERSION = "1.0"

    @property
    def stage_id(self) -> str:
        return "semantics"

    @property
    def stage_number(self) -> int:
        return 3

    @property
    def depends_on(self) -> Tuple[str, ...]:
        return ()

    def execute(self, context: CompileContext) -> StageResult:
        """Execute the semantics stage.

        1. Enumerate all abilities from content pack
        2. Map each ability's mechanics to presentation semantics
        3. Generate event category defaults
        4. Build PresentationSemanticsRegistry
        5. Write presentation_semantics.json to workspace
        """
        log = logging.getLogger(__name__)
        log.info("Stage 3 (semantics): starting")

        try:
            provenance = SemanticsProvenance(
                source="world_compiler",
                compiler_version=self.COMPILER_VERSION,
                seed_used=context.world_seed,
                content_pack_id=context.content_pack_id,
            )

            spells = self._load_spells(context.content_pack_dir)
            log.info("Loaded %d spells", len(spells))

            feats = self._load_feats(context.content_pack_dir)
            active_feats = [f for f in feats if is_active_feat(f)]
            log.info(
                "Loaded %d feats (%d active)",
                len(feats),
                len(active_feats),
            )

            # Map spells to ability entries
            ability_entries: List[AbilityPresentationEntry] = []
            seen_ids: set = set()
            for spell in spells:
                entry = map_spell_to_entry(spell, provenance)
                if entry.content_id not in seen_ids:
                    ability_entries.append(entry)
                    seen_ids.add(entry.content_id)

            # Map active feats to ability entries
            for feat in active_feats:
                entry = map_feat_to_entry(feat, provenance)
                if entry.content_id not in seen_ids:
                    ability_entries.append(entry)
                    seen_ids.add(entry.content_id)

            # Sort by content_id for deterministic output
            ability_entries.sort(key=lambda e: e.content_id)

            # Build event defaults
            event_entries = build_event_defaults()

            # Build registry
            world_id = context.world_id or "unknown"
            registry = PresentationSemanticsRegistry(
                schema_version=self.SCHEMA_VERSION,
                world_id=world_id,
                compiler_version=self.COMPILER_VERSION,
                ability_entry_count=len(ability_entries),
                event_entry_count=len(event_entries),
                ability_entries=tuple(ability_entries),
                event_entries=event_entries,
            )

            # Write output
            output_file = "presentation_semantics.json"
            output_path = context.workspace_dir / output_file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(registry.to_dict(), f, indent=2)

            log.info(
                "Stage 3 (semantics): wrote %d ability + %d event entries",
                len(ability_entries),
                len(event_entries),
            )

            return StageResult(
                stage_id=self.stage_id,
                success=True,
                artifacts=(output_file,),
                metadata={
                    "ability_entry_count": len(ability_entries),
                    "event_entry_count": len(event_entries),
                },
            )

        except Exception as exc:
            log.error("Stage 3 (semantics) failed: %s", exc)
            return StageResult(
                stage_id=self.stage_id,
                success=False,
                error=str(exc),
            )

    @staticmethod
    def _load_spells(content_pack_dir: Path) -> List[Dict[str, Any]]:
        """Load spell data from content pack JSON."""
        spells_path = content_pack_dir / "spells.json"
        if not spells_path.exists():
            return []
        with open(spells_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "spells" in data:
            return data["spells"]
        return []

    @staticmethod
    def _load_feats(content_pack_dir: Path) -> List[Dict[str, Any]]:
        """Load feat data from content pack JSON."""
        feats_path = content_pack_dir / "feats.json"
        if not feats_path.exists():
            return []
        with open(feats_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "feats" in data:
            return data["feats"]
        if isinstance(data, list):
            return data
        return []
