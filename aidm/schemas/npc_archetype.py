"""NPC archetype and doctrine profile schemas for World Compiler Stage 4.

Defines behavioral templates for non-combat NPCs (shopkeeper, guard, noble)
and tactical doctrine profiles for creatures (aggression, retreat, pack behavior).

All dataclasses are frozen (immutable). The World Compiler writes them;
everything else reads them.

Reference: docs/contracts/WORLD_COMPILER.md section 2.4
Reference: pm_inbox/DISPATCH_WO-WORLDCOMPILE-NPC-001.md

BOUNDARY LAW: No imports from aidm/core/.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ═══════════════════════════════════════════════════════════════════════
# NPC Archetype
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class NPCArchetype:
    """Behavioral template for a non-combat NPC role.

    Defines personality, speech, knowledge, and interaction patterns
    for an NPC archetype (e.g., shopkeeper, guard, noble).
    """

    archetype_id: str
    """Stable identifier: 'archetype_shopkeeper', 'archetype_guard', etc."""

    world_name: str
    """World-flavored display name: 'Merchant of the Ashen Roads'."""

    personality_traits: tuple
    """Personality descriptors: ('cautious', 'mercantile', 'observant')."""

    speech_register: str
    """Speech style: 'formal', 'colloquial', 'archaic'."""

    knowledge_domains: tuple
    """What this NPC knows about: ('commerce', 'local_rumors', 'item_valuation')."""

    behavioral_constraints: tuple
    """Hard behavioral limits: ('will_not_fight', 'calls_guards_if_threatened')."""

    interaction_hooks: tuple
    """Player interaction capabilities: ('can_appraise_items', 'sells_equipment')."""

    voice_description: str
    """Brief voice description for TTS persona mapping."""

    provenance: dict
    """Standard provenance record (source, compiler_version, seed_used)."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-compatible dictionary."""
        return {
            "archetype_id": self.archetype_id,
            "world_name": self.world_name,
            "personality_traits": list(self.personality_traits),
            "speech_register": self.speech_register,
            "knowledge_domains": list(self.knowledge_domains),
            "behavioral_constraints": list(self.behavioral_constraints),
            "interaction_hooks": list(self.interaction_hooks),
            "voice_description": self.voice_description,
            "provenance": dict(self.provenance),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NPCArchetype":
        """Deserialize from dictionary."""
        return cls(
            archetype_id=data["archetype_id"],
            world_name=data["world_name"],
            personality_traits=tuple(data.get("personality_traits", [])),
            speech_register=data["speech_register"],
            knowledge_domains=tuple(data.get("knowledge_domains", [])),
            behavioral_constraints=tuple(data.get("behavioral_constraints", [])),
            interaction_hooks=tuple(data.get("interaction_hooks", [])),
            voice_description=data.get("voice_description", ""),
            provenance=data.get("provenance", {}),
        )


# ═══════════════════════════════════════════════════════════════════════
# Doctrine Profile
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class DoctrineProfile:
    """Tactical behavior template for a creature category.

    Defines how a class of creatures fights: aggression, retreat threshold,
    pack behavior, preferred tactics, morale, and special behaviors.

    Convertible to the existing MonsterDoctrine format via to_monster_doctrine().
    """

    doctrine_id: str
    """Stable identifier: 'doctrine_pack_predator', 'doctrine_ambusher', etc."""

    creature_types: tuple
    """Which creature types this doctrine applies to: ('beast', 'animal')."""

    aggression: str
    """Aggression level: 'timid', 'cautious', 'aggressive', 'berserk'."""

    retreat_threshold: float
    """HP fraction (0.0-1.0) at which the creature attempts to retreat."""

    pack_behavior: str
    """Group behavior: 'solo', 'pair', 'pack', 'swarm'."""

    preferred_tactics: tuple
    """Preferred combat tactics: ('ambush', 'flank', 'charge', 'ranged_kite')."""

    morale: str
    """Morale descriptor: 'cowardly', 'steady', 'fanatical'."""

    special_behaviors: tuple
    """Special behavioral triggers: ('guards_lair', 'protects_young')."""

    provenance: dict
    """Standard provenance record."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-compatible dictionary."""
        return {
            "doctrine_id": self.doctrine_id,
            "creature_types": list(self.creature_types),
            "aggression": self.aggression,
            "retreat_threshold": self.retreat_threshold,
            "pack_behavior": self.pack_behavior,
            "preferred_tactics": list(self.preferred_tactics),
            "morale": self.morale,
            "special_behaviors": list(self.special_behaviors),
            "provenance": dict(self.provenance),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DoctrineProfile":
        """Deserialize from dictionary."""
        return cls(
            doctrine_id=data["doctrine_id"],
            creature_types=tuple(data.get("creature_types", [])),
            aggression=data["aggression"],
            retreat_threshold=float(data["retreat_threshold"]),
            pack_behavior=data["pack_behavior"],
            preferred_tactics=tuple(data.get("preferred_tactics", [])),
            morale=data["morale"],
            special_behaviors=tuple(data.get("special_behaviors", [])),
            provenance=data.get("provenance", {}),
        )

    def to_monster_doctrine(self, monster_id: str, source: str = "world_compiler") -> Dict[str, Any]:
        """Convert to MonsterDoctrine-compatible dictionary.

        Field mapping:
            doctrine_id          -> monster_id (overridden by argument)
            creature_types[0]    -> creature_type
            aggression           -> tags (mapped to DoctrineTag)
            retreat_threshold    -> (no direct field; encoded in tags/notes)
            pack_behavior        -> tags (mapped to DoctrineTag)
            preferred_tactics    -> allowed_tactics (mapped to TacticClass)
            morale               -> tags (mapped to DoctrineTag)
            special_behaviors    -> notes

        The caller must supply int_score/wis_score from creature data.
        """
        # Map aggression to doctrine tags
        _AGGRESSION_TAG_MAP = {
            "timid": "cowardly",
            "cautious": "animal_predator",
            "aggressive": "pack_hunter",
            "berserk": "berserker",
        }

        # Map pack_behavior to doctrine tags
        _PACK_TAG_MAP = {
            "solo": None,
            "pair": "pack_hunter",
            "pack": "pack_hunter",
            "swarm": "swarm_instinct",
        }

        # Map morale to doctrine tags
        _MORALE_TAG_MAP = {
            "cowardly": "cowardly",
            "steady": "disciplined",
            "fanatical": "fanatical",
        }

        # Map preferred_tactics to TacticClass values
        _TACTIC_MAP = {
            "ambush": "bait_and_switch",
            "flank": "setup_flank",
            "charge": "attack_nearest",
            "ranged_kite": "use_cover",
            "focus_fire": "focus_fire",
            "target_support": "target_support",
            "retreat": "retreat_regroup",
            "cast": "target_controller",
        }

        tags: List[str] = []
        agg_tag = _AGGRESSION_TAG_MAP.get(self.aggression)
        if agg_tag:
            tags.append(agg_tag)
        pack_tag = _PACK_TAG_MAP.get(self.pack_behavior)
        if pack_tag and pack_tag not in tags:
            tags.append(pack_tag)
        morale_tag = _MORALE_TAG_MAP.get(self.morale)
        if morale_tag and morale_tag not in tags:
            tags.append(morale_tag)

        allowed_tactics: List[str] = []
        for tactic in self.preferred_tactics:
            mapped = _TACTIC_MAP.get(tactic)
            if mapped and mapped not in allowed_tactics:
                allowed_tactics.append(mapped)

        notes_parts: List[str] = []
        if self.retreat_threshold > 0:
            notes_parts.append(f"retreats at {self.retreat_threshold:.0%} HP")
        if self.special_behaviors:
            notes_parts.append("; ".join(self.special_behaviors))
        notes = ". ".join(notes_parts) if notes_parts else None

        creature_type = self.creature_types[0] if self.creature_types else "unknown"

        return {
            "monster_id": monster_id,
            "source": source,
            "int_score": None,
            "wis_score": None,
            "creature_type": creature_type,
            "tags": tags,
            "notes": notes,
            "citations": [],
            "allowed_tactics": allowed_tactics,
        }


# ═══════════════════════════════════════════════════════════════════════
# NPC Archetype Registry
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class NPCArchetypeRegistry:
    """Top-level container for NPC archetypes and doctrine profiles.

    Serialized to npc_archetypes.json + doctrine_profiles.json
    in the world bundle.
    """

    schema_version: str
    """Schema version of this registry."""

    world_id: str
    """World identity hash — must match world_manifest.json world_id."""

    archetypes: tuple
    """All NPC archetypes, sorted by archetype_id. Tuple of NPCArchetype."""

    doctrines: tuple
    """All doctrine profiles, sorted by doctrine_id. Tuple of DoctrineProfile."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-compatible dictionary."""
        return {
            "schema_version": self.schema_version,
            "world_id": self.world_id,
            "archetypes": [a.to_dict() for a in self.archetypes],
            "doctrines": [d.to_dict() for d in self.doctrines],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NPCArchetypeRegistry":
        """Deserialize from dictionary."""
        return cls(
            schema_version=data.get("schema_version", "1.0"),
            world_id=data.get("world_id", ""),
            archetypes=tuple(
                NPCArchetype.from_dict(a) for a in data.get("archetypes", [])
            ),
            doctrines=tuple(
                DoctrineProfile.from_dict(d) for d in data.get("doctrines", [])
            ),
        )
