"""Bundle schemas for session prep artifacts.

Formalizes "prep vs play" concept as structured data.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Literal
from aidm.schemas.citation import Citation
from aidm.schemas.doctrine import MonsterDoctrine
from aidm.schemas.policy_config import PolicyVarietyConfig
from aidm.schemas.time import GameClock
from aidm.schemas.timers import Deadline
from aidm.schemas.durations import EffectDuration
from aidm.schemas.visibility import AmbientLightSchedule
from aidm.schemas.hazards import EnvironmentalHazard
from aidm.schemas.exposure import EnvironmentalCondition
from aidm.schemas.campaign_memory import SessionLedgerEntry, EvidenceLedger, ThreadRegistry


@dataclass
class SceneCard:
    """Description of a scene/location for session prep."""

    scene_id: str
    title: str
    description: str
    key_npcs: List[str] = field(default_factory=list)
    exits: List[str] = field(default_factory=list)
    secrets: List[str] = field(default_factory=list)
    ambient_light_level: str = "bright"
    """Ambient light level (bright/dim/dark)"""

    ambient_light_schedule: Optional[AmbientLightSchedule] = None
    """Optional lighting schedule for time-based light changes"""

    environmental_hazards: List[EnvironmentalHazard] = field(default_factory=list)
    """Environmental hazards present in this scene"""

    environmental_conditions: List[EnvironmentalCondition] = field(default_factory=list)
    """Active environmental conditions affecting this scene"""


@dataclass
class NpcCard:
    """NPC stat block and roleplay notes."""

    npc_id: str
    name: str
    role: str
    stats: Dict[str, Any] = field(default_factory=dict)
    personality: str = ""
    goals: List[str] = field(default_factory=list)


@dataclass
class EncounterSpec:
    """Combat encounter specification."""

    encounter_id: str
    name: str
    creatures: List[Dict[str, Any]] = field(default_factory=list)
    terrain: str = ""
    trigger_condition: str = ""
    monster_doctrines_by_id: Dict[str, MonsterDoctrine] = field(default_factory=dict)
    """Tactical envelopes for monsters, keyed by monster_id (deterministic binding)"""

    terrain_overrides: List[Dict[str, Any]] = field(default_factory=list)
    """Tiles/zones with special terrain tags"""

    light_sources: List[Dict[str, Any]] = field(default_factory=list)
    """Light sources (position + radius + light_level)"""


@dataclass
class CampaignBundle:
    """Campaign-level prep bundle."""

    id: str
    title: str
    created_at: str  # ISO timestamp
    sources_used: List[str] = field(default_factory=list)
    """List of sourceIds referenced during prep"""

    world_facts: List[str] = field(default_factory=list)
    """Campaign-wide facts and lore"""

    factions: List[Dict[str, Any]] = field(default_factory=list)
    """Factions and their relationships"""

    npc_index: List[str] = field(default_factory=list)
    """Index of all NPCs across campaign"""

    policy_variety_config: Optional[PolicyVarietyConfig] = None
    """Campaign-wide policy variety configuration"""

    session_ledger: List[SessionLedgerEntry] = field(default_factory=list)
    """Session ledger entries (high-level session summaries)"""

    evidence_ledger: Optional[EvidenceLedger] = None
    """Character behavioral evidence ledger"""

    thread_registry: Optional[ThreadRegistry] = None
    """Campaign mystery and clue thread registry"""


@dataclass
class SessionBundle:
    """Session-level prep bundle with all required assets and data."""

    id: str
    campaign_id: str
    session_number: int
    created_at: str  # ISO timestamp

    scene_cards: List[SceneCard] = field(default_factory=list)
    npc_cards: List[NpcCard] = field(default_factory=list)
    encounter_specs: List[EncounterSpec] = field(default_factory=list)

    assets: Dict[str, Any] = field(default_factory=dict)
    """Paths to token images, portraits, handouts (string values)"""

    citations: List[Dict[str, Any]] = field(default_factory=list)
    """Pre-loaded citations likely to be referenced"""

    doctrine_required: bool = True
    """Whether doctrine enforcement is enabled (default True)"""

    initial_clock: Optional[GameClock] = None
    """Initial game clock state for this session"""

    deadlines: List[Deadline] = field(default_factory=list)
    """Time-sensitive deadlines and timers for this session"""

    active_effects: List[EffectDuration] = field(default_factory=list)
    """Active spell/buff/debuff durations at session start"""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "id": self.id,
            "campaign_id": self.campaign_id,
            "session_number": self.session_number,
            "created_at": self.created_at,
            "scene_cards": [
                {
                    "scene_id": sc.scene_id,
                    "title": sc.title,
                    "description": sc.description,
                    "key_npcs": sc.key_npcs,
                    "exits": sc.exits,
                    "secrets": sc.secrets,
                    "ambient_light_level": sc.ambient_light_level,
                    **({"ambient_light_schedule": sc.ambient_light_schedule.to_dict()}
                       if sc.ambient_light_schedule else {}),
                    "environmental_hazards": [h.to_dict() for h in sc.environmental_hazards],
                    "environmental_conditions": [c.to_dict() for c in sc.environmental_conditions]
                }
                for sc in self.scene_cards
            ],
            "npc_cards": [
                {
                    "npc_id": nc.npc_id,
                    "name": nc.name,
                    "role": nc.role,
                    "stats": nc.stats,
                    "personality": nc.personality,
                    "goals": nc.goals
                }
                for nc in self.npc_cards
            ],
            "encounter_specs": [
                {
                    "encounter_id": es.encounter_id,
                    "name": es.name,
                    "creatures": es.creatures,
                    "terrain": es.terrain,
                    "trigger_condition": es.trigger_condition,
                    "monster_doctrines_by_id": {
                        monster_id: md.to_dict()
                        for monster_id, md in es.monster_doctrines_by_id.items()
                    },
                    "terrain_overrides": es.terrain_overrides,
                    "light_sources": es.light_sources
                }
                for es in self.encounter_specs
            ],
            "assets": self.assets,
            "citations": self.citations,
            "doctrine_required": self.doctrine_required
        }

        # Add optional temporal fields if present
        if self.initial_clock is not None:
            result["initial_clock"] = self.initial_clock.to_dict()

        if self.deadlines:
            result["deadlines"] = [d.to_dict() for d in self.deadlines]

        if self.active_effects:
            result["active_effects"] = [e.to_dict() for e in self.active_effects]

        return result


@dataclass
class ReadinessCertificate:
    """Validation result for session bundle readiness.

    Indicates whether bundle is ready for play or has blockers.
    """

    bundle_id: str
    status: Literal["ready", "blocked"]

    missing_assets: List[str] = field(default_factory=list)
    """Asset paths that were referenced but don't exist"""

    missing_citations: List[str] = field(default_factory=list)
    """Citations with invalid structure (empty source_id/page)"""

    notes: List[str] = field(default_factory=list)
    """Additional warnings or informational messages"""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "bundle_id": self.bundle_id,
            "status": self.status,
            "missing_assets": self.missing_assets,
            "missing_citations": self.missing_citations,
            "notes": self.notes
        }
