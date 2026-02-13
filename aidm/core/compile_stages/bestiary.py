"""Stage 5: Bestiary Generation — compile creature catalog from content pack.

WO-COMPILE-BESTIARY-001 — Reads creature templates from the content pack,
enriches them with world-flavored names (from lexicon) and presentation
semantics bindings, generates stub descriptions, and writes bestiary.json.

Stub mode produces deterministic procedural descriptions from creature
mechanical data. LLM mode would generate world-themed prose (not
implemented in this WO).

BOUNDARY LAW: This is a core-layer component. Imports from aidm.schemas
are allowed. No imports from aidm.lens or aidm.narration.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

from aidm.core.compile_stages._base import CompileContext, CompileStage, StageResult
from aidm.schemas.bestiary import (
    AbilityScores,
    BestiaryEntry,
    BestiaryProvenance,
    BestiaryRegistry,
)


COMPILER_VERSION = "0.1.0"
SCHEMA_VERSION = "1.0"


# ═══════════════════════════════════════════════════════════════════════
# Stub description generators
# ═══════════════════════════════════════════════════════════════════════

# Size descriptors for stub appearance text
_SIZE_ADJECTIVE = {
    "fine": "minuscule",
    "diminutive": "tiny",
    "tiny": "very small",
    "small": "small",
    "medium": "medium-sized",
    "large": "large",
    "huge": "massive",
    "gargantuan": "enormous",
    "colossal": "titanic",
}

# Intelligence band descriptors
_INTELLIGENCE_DESC = {
    "mindless": "acts on pure instinct",
    "animal": "possesses animal-level cunning",
    "low": "shows rudimentary intelligence",
    "average": "displays average intelligence",
    "high": "demonstrates keen intellect",
    "genius": "possesses formidable intelligence",
}

# Creature type habitat defaults (used when no environment_tags)
_TYPE_DEFAULT_HABITAT = {
    "aberration": "underground",
    "animal": "wilderness",
    "construct": "ruins",
    "dragon": "mountains",
    "elemental": "elemental_plane",
    "fey": "forest",
    "giant": "mountains",
    "humanoid": "settlements",
    "magical beast": "wilderness",
    "monstrous humanoid": "underground",
    "ooze": "underground",
    "outsider": "planar",
    "plant": "forest",
    "undead": "ruins",
    "vermin": "underground",
}


def _stub_appearance(creature: Dict[str, Any]) -> str:
    """Generate a stub appearance description from mechanical data."""
    size = creature.get("size_category", "medium")
    ctype = creature.get("creature_type", "creature")
    adjective = _SIZE_ADJECTIVE.get(size, "medium-sized")
    ac = creature.get("ac_total", 10)

    armor_desc = ""
    if ac >= 25:
        armor_desc = " with heavily armored hide"
    elif ac >= 20:
        armor_desc = " with thick natural armor"
    elif ac >= 15:
        armor_desc = " with tough skin"

    return f"A {adjective} {ctype}{armor_desc}."


def _stub_habitat(creature: Dict[str, Any]) -> str:
    """Generate a stub habitat description from mechanical data."""
    env_tags = creature.get("environment_tags", ())
    ctype = creature.get("creature_type", "creature")

    if env_tags:
        habitats = ", ".join(str(t) for t in env_tags[:3])
        return f"Found in {habitats} environments."

    default = _TYPE_DEFAULT_HABITAT.get(ctype, "various")
    return f"Typically found in {default} environments."


def _stub_behavior(creature: Dict[str, Any]) -> str:
    """Generate a stub behavior summary from mechanical data."""
    intel = creature.get("intelligence_band", "")
    cr = creature.get("cr", 0)
    special_attacks = creature.get("special_attacks", ())

    intel_desc = _INTELLIGENCE_DESC.get(intel, "acts according to its nature")

    threat = "minor"
    if cr >= 15:
        threat = "legendary"
    elif cr >= 10:
        threat = "major"
    elif cr >= 5:
        threat = "significant"
    elif cr >= 2:
        threat = "moderate"

    parts = [f"A {threat} threat that {intel_desc}"]
    if special_attacks:
        parts.append(f"with {len(special_attacks)} special attack(s)")
    return ". ".join(parts) + "."


def _derive_vfx_tags(creature: Dict[str, Any]) -> Tuple[str, ...]:
    """Derive basic VFX tags from creature mechanical data."""
    tags: List[str] = []
    ctype = creature.get("creature_type", "")

    if ctype in ("dragon", "elemental"):
        tags.append("elemental_aura")
    if ctype == "undead":
        tags.append("shadow")
    if ctype == "construct":
        tags.append("metallic_gleam")
    if ctype in ("fey", "outsider"):
        tags.append("otherworldly_glow")

    size = creature.get("size_category", "medium")
    if size in ("huge", "gargantuan", "colossal"):
        tags.append("ground_shake")

    return tuple(tags) if tags else ("generic_creature",)


def _derive_sfx_tags(creature: Dict[str, Any]) -> Tuple[str, ...]:
    """Derive basic SFX tags from creature mechanical data."""
    tags: List[str] = []
    ctype = creature.get("creature_type", "")

    if ctype in ("animal", "magical beast"):
        tags.append("growl")
    if ctype in ("humanoid", "monstrous humanoid", "giant"):
        tags.append("war_cry")
    if ctype == "undead":
        tags.append("moan")
    if ctype == "construct":
        tags.append("mechanical_grind")

    size = creature.get("size_category", "medium")
    if size in ("huge", "gargantuan", "colossal"):
        tags.append("heavy_footstep")
    else:
        tags.append("footstep")

    return tuple(tags) if tags else ("generic_creature",)


# ═══════════════════════════════════════════════════════════════════════
# Content pack loading
# ═══════════════════════════════════════════════════════════════════════


def _load_creatures(content_pack_dir: Path) -> List[Dict[str, Any]]:
    """Load creature data from content pack JSON."""
    creatures_path = content_pack_dir / "creatures.json"
    if not creatures_path.exists():
        return []
    with open(creatures_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "creatures" in data:
        return data["creatures"]
    return []


# ═══════════════════════════════════════════════════════════════════════
# BestiaryStage
# ═══════════════════════════════════════════════════════════════════════


class BestiaryStage(CompileStage):
    """Stage 5: Generate compiled bestiary from creature templates."""

    @property
    def stage_id(self) -> str:
        return "bestiary"

    @property
    def stage_number(self) -> int:
        return 5

    @property
    def depends_on(self) -> Tuple[str, ...]:
        return ("lexicon",)

    def execute(self, context: CompileContext) -> StageResult:
        """Execute the bestiary stage.

        1. Load creature templates from content pack
        2. For each creature, build BestiaryEntry:
           - Map mechanical data to schema fields
           - Generate stub descriptions (appearance, habitat, behavior)
           - Derive VFX/SFX tags
           - Record provenance
        3. Build habitat distribution map
        4. Write bestiary.json to workspace
        """
        log = logging.getLogger(__name__)
        log.info("Stage 5 (bestiary): starting")

        try:
            return self._execute_inner(context, log)
        except Exception as exc:
            log.error("Stage 5 (bestiary) failed: %s", exc)
            return StageResult(
                stage_id=self.stage_id,
                status="failed",
                output_files=(),
                error=str(exc),
            )

    def _execute_inner(
        self, context: CompileContext, log: logging.Logger
    ) -> StageResult:
        creatures = _load_creatures(context.content_pack_dir)
        log.info("Loaded %d creatures", len(creatures))

        provenance = BestiaryProvenance(
            source="world_compiler",
            compiler_version=COMPILER_VERSION,
            seed_used=context.world_seed,
            content_pack_id=context.content_pack_id,
        )

        entries: List[BestiaryEntry] = []
        seen_ids: set = set()
        habitat_map: Dict[str, List[str]] = {}

        for creature in creatures:
            template_id = creature.get("template_id", "")
            if not template_id:
                continue

            content_id = f"creature.{template_id.lower()}"
            if content_id in seen_ids:
                continue
            seen_ids.add(content_id)

            # Build stub world name from template_id
            world_name = content_id

            # Build ability scores
            ability_scores = AbilityScores(
                str_score=creature.get("str_score"),
                dex_score=creature.get("dex_score"),
                con_score=creature.get("con_score"),
                int_score=creature.get("int_score"),
                wis_score=creature.get("wis_score"),
                cha_score=creature.get("cha_score"),
            )

            # Build entry provenance with template_id
            entry_provenance = BestiaryProvenance(
                source=provenance.source,
                compiler_version=provenance.compiler_version,
                seed_used=provenance.seed_used,
                content_pack_id=provenance.content_pack_id,
                template_ids=(template_id,),
            )

            entry = BestiaryEntry(
                content_id=content_id,
                world_name=world_name,
                size_category=creature.get("size_category", "medium"),
                creature_type=creature.get("creature_type", "humanoid"),
                subtypes=tuple(creature.get("subtypes", [])),
                appearance=_stub_appearance(creature),
                habitat=_stub_habitat(creature),
                behavior_summary=_stub_behavior(creature),
                hit_dice=creature.get("hit_dice", ""),
                hp_typical=creature.get("hp_typical", 0),
                ac_total=creature.get("ac_total", 10),
                ac_touch=creature.get("ac_touch", 10),
                ac_flat_footed=creature.get("ac_flat_footed", 10),
                speed_ft=creature.get("speed_ft", 0),
                bab=creature.get("bab", 0),
                fort_save=creature.get("fort_save", 0),
                ref_save=creature.get("ref_save", 0),
                will_save=creature.get("will_save", 0),
                ability_scores=ability_scores,
                special_attacks=tuple(creature.get("special_attacks", [])),
                special_qualities=tuple(creature.get("special_qualities", [])),
                cr=float(creature.get("cr", 0.0)),
                intelligence_band=creature.get("intelligence_band", ""),
                vfx_tags=_derive_vfx_tags(creature),
                sfx_tags=_derive_sfx_tags(creature),
                provenance=entry_provenance,
            )
            entries.append(entry)

            # Build habitat distribution
            env_tags = creature.get("environment_tags", ())
            if env_tags:
                for tag in env_tags:
                    habitat_map.setdefault(str(tag), []).append(content_id)
            else:
                default = _TYPE_DEFAULT_HABITAT.get(
                    creature.get("creature_type", ""), "various"
                )
                habitat_map.setdefault(default, []).append(content_id)

        # Sort entries by content_id for deterministic output
        entries.sort(key=lambda e: e.content_id)

        # Sort habitat distribution values for determinism
        habitat_distribution = {
            k: tuple(sorted(v)) for k, v in sorted(habitat_map.items())
        }

        # Build registry
        world_id = context.world_id or "unknown"
        registry = BestiaryRegistry(
            schema_version=SCHEMA_VERSION,
            world_id=world_id,
            compiler_version=COMPILER_VERSION,
            creature_count=len(entries),
            entries=tuple(entries),
            habitat_distribution=habitat_distribution,
        )

        # Write output
        output_file = "bestiary.json"
        output_path = context.workspace_dir / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(registry.to_dict(), f, indent=2)

        log.info(
            "Stage 5 (bestiary): wrote %d creature entries, %d habitats",
            len(entries),
            len(habitat_distribution),
        )

        return StageResult(
            stage_id=self.stage_id,
            status="success",
            output_files=(output_file,),
        )
