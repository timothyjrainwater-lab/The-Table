"""Stage 4: NPC Archetypes + Doctrine Profiles.

WO-WORLDCOMPILE-NPC-001 — Generates behavioral templates for non-combat
NPCs and tactical doctrine profiles for creature categories.

Stub mode produces 8 standard archetypes and 6 doctrine profiles
deterministically from the world seed. LLM mode flavors them with
world-theme data (not implemented in this WO).

BOUNDARY LAW: This is a core-layer component. Imports from aidm.schemas
are allowed. No imports from aidm.lens or aidm.narration.
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

from aidm.core.compile_stages._base import CompileContext, CompileStage, StageResult
from aidm.schemas.npc_archetype import (
    DoctrineProfile,
    NPCArchetype,
    NPCArchetypeRegistry,
)

COMPILER_VERSION = "0.1.0"
SCHEMA_VERSION = "1.0"


# ═══════════════════════════════════════════════════════════════════════
# Stub archetype definitions (8 standard archetypes)
# ═══════════════════════════════════════════════════════════════════════

_STUB_ARCHETYPES = (
    {
        "key": "shopkeeper",
        "world_name": "Shopkeeper",
        "personality_traits": ("mercantile", "cautious", "observant"),
        "speech_register": "colloquial",
        "knowledge_domains": ("commerce", "local_rumors", "item_valuation"),
        "behavioral_constraints": ("will_not_fight", "calls_guards_if_threatened"),
        "interaction_hooks": ("can_appraise_items", "sells_equipment", "knows_local_gossip"),
        "voice_description": "Warm, measured tone with a merchant's practiced friendliness",
    },
    {
        "key": "guard",
        "world_name": "Guard",
        "personality_traits": ("vigilant", "dutiful", "suspicious"),
        "speech_register": "formal",
        "knowledge_domains": ("local_law", "patrol_routes", "criminal_activity"),
        "behavioral_constraints": ("follows_orders", "will_not_accept_bribes"),
        "interaction_hooks": ("can_provide_directions", "enforces_curfew", "reports_crimes"),
        "voice_description": "Stern, authoritative voice with clipped military cadence",
    },
    {
        "key": "noble",
        "world_name": "Noble",
        "personality_traits": ("proud", "cultured", "politically_astute"),
        "speech_register": "formal",
        "knowledge_domains": ("politics", "heraldry", "high_society"),
        "behavioral_constraints": ("will_not_perform_manual_labor", "demands_respect"),
        "interaction_hooks": ("can_grant_audience", "offers_quests", "knows_court_intrigue"),
        "voice_description": "Refined, aristocratic diction with deliberate pacing",
    },
    {
        "key": "peasant",
        "world_name": "Peasant",
        "personality_traits": ("humble", "hardworking", "superstitious"),
        "speech_register": "colloquial",
        "knowledge_domains": ("farming", "local_folklore", "weather_signs"),
        "behavioral_constraints": ("defers_to_authority", "avoids_conflict"),
        "interaction_hooks": ("shares_local_rumors", "offers_simple_goods", "warns_of_dangers"),
        "voice_description": "Plain-spoken, rustic accent with a weary warmth",
    },
    {
        "key": "scholar",
        "world_name": "Scholar",
        "personality_traits": ("curious", "absent_minded", "knowledgeable"),
        "speech_register": "formal",
        "knowledge_domains": ("arcana", "history", "languages"),
        "behavioral_constraints": ("will_not_fight", "prefers_negotiation"),
        "interaction_hooks": ("can_identify_items", "translates_texts", "provides_lore"),
        "voice_description": "Thoughtful, precise speech with occasional excited tangents",
    },
    {
        "key": "criminal",
        "world_name": "Criminal",
        "personality_traits": ("cunning", "streetwise", "distrustful"),
        "speech_register": "colloquial",
        "knowledge_domains": ("underworld", "black_market", "lockpicking"),
        "behavioral_constraints": ("flees_if_outnumbered", "will_not_betray_guild"),
        "interaction_hooks": ("fences_stolen_goods", "offers_shady_quests", "knows_secret_passages"),
        "voice_description": "Low, guarded tone with street slang and quick delivery",
    },
    {
        "key": "priest",
        "world_name": "Priest",
        "personality_traits": ("pious", "compassionate", "resolute"),
        "speech_register": "formal",
        "knowledge_domains": ("religion", "healing", "undead_lore"),
        "behavioral_constraints": ("will_not_use_violence_unprovoked", "follows_religious_code"),
        "interaction_hooks": ("offers_healing", "blesses_party", "provides_sanctuary"),
        "voice_description": "Calm, resonant voice with a serene, measured cadence",
    },
    {
        "key": "innkeeper",
        "world_name": "Innkeeper",
        "personality_traits": ("hospitable", "shrewd", "gossipy"),
        "speech_register": "colloquial",
        "knowledge_domains": ("local_rumors", "travelers_news", "food_and_drink"),
        "behavioral_constraints": ("will_not_fight", "protects_establishment"),
        "interaction_hooks": ("offers_lodging", "serves_food_and_drink", "shares_traveler_tales"),
        "voice_description": "Hearty, boisterous voice that carries across a crowded room",
    },
)


# ═══════════════════════════════════════════════════════════════════════
# Stub doctrine definitions (6 doctrine profiles)
# ═══════════════════════════════════════════════════════════════════════

_STUB_DOCTRINES = (
    {
        "key": "pack_predator",
        "creature_types": ("beast", "animal", "magical_beast"),
        "aggression": "aggressive",
        "retreat_threshold": 0.25,
        "pack_behavior": "pack",
        "preferred_tactics": ("flank", "focus_fire"),
        "morale": "steady",
        "special_behaviors": ("protects_young", "calls_reinforcements"),
    },
    {
        "key": "ambusher",
        "creature_types": ("aberration", "magical_beast", "monstrous_humanoid"),
        "aggression": "cautious",
        "retreat_threshold": 0.4,
        "pack_behavior": "solo",
        "preferred_tactics": ("ambush", "retreat"),
        "morale": "cowardly",
        "special_behaviors": ("guards_lair", "uses_terrain"),
    },
    {
        "key": "territorial_defender",
        "creature_types": ("dragon", "magical_beast", "outsider"),
        "aggression": "aggressive",
        "retreat_threshold": 0.1,
        "pack_behavior": "solo",
        "preferred_tactics": ("charge", "focus_fire"),
        "morale": "fanatical",
        "special_behaviors": ("guards_lair", "fights_to_death_in_lair"),
    },
    {
        "key": "mindless_aggressor",
        "creature_types": ("undead", "construct", "ooze"),
        "aggression": "berserk",
        "retreat_threshold": 0.0,
        "pack_behavior": "swarm",
        "preferred_tactics": ("charge",),
        "morale": "fanatical",
        "special_behaviors": (),
    },
    {
        "key": "tactical_caster",
        "creature_types": ("outsider", "fey", "humanoid"),
        "aggression": "cautious",
        "retreat_threshold": 0.5,
        "pack_behavior": "pair",
        "preferred_tactics": ("cast", "ranged_kite", "retreat"),
        "morale": "cowardly",
        "special_behaviors": ("calls_reinforcements",),
    },
    {
        "key": "cowardly_scavenger",
        "creature_types": ("beast", "vermin", "humanoid"),
        "aggression": "timid",
        "retreat_threshold": 0.7,
        "pack_behavior": "pack",
        "preferred_tactics": ("ambush", "flank"),
        "morale": "cowardly",
        "special_behaviors": ("flees_if_leader_falls",),
    },
)


# ═══════════════════════════════════════════════════════════════════════
# Seed derivation
# ═══════════════════════════════════════════════════════════════════════

_MAX_SEED = (2**63) - 1


def _derive_npc_seed(world_seed: int) -> int:
    """Derive a deterministic seed for NPC archetype generation.

    Uses sha256('npc:{world_seed}') clamped to 63-bit.
    Matches the convention in world_compiler.py derive_seeds().
    """
    raw = f"npc:{world_seed}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return int(digest, 16) % (_MAX_SEED + 1)


# ═══════════════════════════════════════════════════════════════════════
# Stub generators
# ═══════════════════════════════════════════════════════════════════════


def _build_stub_archetypes(
    world_seed: int,
    content_pack_id: str,
) -> List[NPCArchetype]:
    """Build 8 standard NPC archetypes with deterministic data."""
    npc_seed = _derive_npc_seed(world_seed)
    provenance = {
        "source": "world_compiler",
        "compiler_version": COMPILER_VERSION,
        "seed_used": npc_seed,
        "content_pack_id": content_pack_id,
        "llm_output_hash": None,
    }

    archetypes: List[NPCArchetype] = []
    for defn in _STUB_ARCHETYPES:
        archetype = NPCArchetype(
            archetype_id=f"archetype_{defn['key']}",
            world_name=defn["world_name"],
            personality_traits=defn["personality_traits"],
            speech_register=defn["speech_register"],
            knowledge_domains=defn["knowledge_domains"],
            behavioral_constraints=defn["behavioral_constraints"],
            interaction_hooks=defn["interaction_hooks"],
            voice_description=defn["voice_description"],
            provenance=provenance,
        )
        archetypes.append(archetype)

    return archetypes


def _build_stub_doctrines(
    world_seed: int,
    content_pack_id: str,
) -> List[DoctrineProfile]:
    """Build 6 standard doctrine profiles with deterministic data."""
    npc_seed = _derive_npc_seed(world_seed)
    provenance = {
        "source": "world_compiler",
        "compiler_version": COMPILER_VERSION,
        "seed_used": npc_seed,
        "content_pack_id": content_pack_id,
        "llm_output_hash": None,
    }

    doctrines: List[DoctrineProfile] = []
    for defn in _STUB_DOCTRINES:
        doctrine = DoctrineProfile(
            doctrine_id=f"doctrine_{defn['key']}",
            creature_types=defn["creature_types"],
            aggression=defn["aggression"],
            retreat_threshold=defn["retreat_threshold"],
            pack_behavior=defn["pack_behavior"],
            preferred_tactics=defn["preferred_tactics"],
            morale=defn["morale"],
            special_behaviors=defn["special_behaviors"],
            provenance=provenance,
        )
        doctrines.append(doctrine)

    return doctrines


# ═══════════════════════════════════════════════════════════════════════
# NPCArchetypeStage
# ═══════════════════════════════════════════════════════════════════════


class NPCArchetypeStage(CompileStage):
    """Stage 4: Generate NPC archetypes and doctrine profiles."""

    @property
    def stage_id(self) -> str:
        return "npc_archetypes"

    @property
    def stage_number(self) -> int:
        return 4

    @property
    def depends_on(self) -> Tuple[str, ...]:
        return ("lexicon",)

    def execute(self, context: CompileContext) -> StageResult:
        """Generate NPC archetypes and doctrine profiles.

        1. Determine mode (stub vs LLM)
        2. Generate archetypes and doctrines
        3. Build registry
        4. Write npc_archetypes.json + doctrine_profiles.json
        """
        log = logging.getLogger(__name__)
        log.info("Stage 4 (npc_archetypes): starting")

        try:
            return self._execute_inner(context, log)
        except Exception as exc:
            log.error("Stage 4 (npc_archetypes) failed: %s", exc)
            return StageResult(
                stage_id=self.stage_id,
                status="failed",
                output_files=(),
                error=str(exc),
            )

    def _execute_inner(self, context: CompileContext, log: logging.Logger) -> StageResult:
        # Determine mode
        llm_model_id = context.toolchain_pins.get("llm_model_id", "stub")
        use_stub = llm_model_id == "stub"

        content_pack_id = context.content_pack_id

        # Generate archetypes and doctrines
        if use_stub:
            archetypes = _build_stub_archetypes(context.world_seed, content_pack_id)
            doctrines = _build_stub_doctrines(context.world_seed, content_pack_id)
        else:
            # LLM mode — not implemented in this WO.
            # Falls back to stub with world-theme naming not yet applied.
            archetypes = _build_stub_archetypes(context.world_seed, content_pack_id)
            doctrines = _build_stub_doctrines(context.world_seed, content_pack_id)

        # Sort by ID for deterministic output
        archetypes.sort(key=lambda a: a.archetype_id)
        doctrines.sort(key=lambda d: d.doctrine_id)

        # Compute world_id
        world_id = context.world_id
        if not world_id:
            world_id = hashlib.sha256(
                f"{context.world_seed}:{content_pack_id}".encode()
            ).hexdigest()[:32]

        # Build registry
        registry = NPCArchetypeRegistry(
            schema_version=SCHEMA_VERSION,
            world_id=world_id,
            archetypes=tuple(archetypes),
            doctrines=tuple(doctrines),
        )

        # Write output files
        context.workspace_dir.mkdir(parents=True, exist_ok=True)

        # Write npc_archetypes.json (archetypes portion)
        archetypes_data = {
            "schema_version": registry.schema_version,
            "world_id": registry.world_id,
            "archetypes": [a.to_dict() for a in registry.archetypes],
        }
        archetypes_path = context.workspace_dir / "npc_archetypes.json"
        with open(archetypes_path, "w", encoding="utf-8") as f:
            json.dump(archetypes_data, f, indent=2, sort_keys=False)

        # Write doctrine_profiles.json (doctrines portion)
        doctrines_data = {
            "schema_version": registry.schema_version,
            "world_id": registry.world_id,
            "doctrines": [d.to_dict() for d in registry.doctrines],
        }
        doctrines_path = context.workspace_dir / "doctrine_profiles.json"
        with open(doctrines_path, "w", encoding="utf-8") as f:
            json.dump(doctrines_data, f, indent=2, sort_keys=False)

        log.info(
            "Stage 4 (npc_archetypes): wrote %d archetypes + %d doctrines",
            len(archetypes),
            len(doctrines),
        )

        return StageResult(
            stage_id=self.stage_id,
            status="success",
            output_files=("npc_archetypes.json", "doctrine_profiles.json"),
        )
