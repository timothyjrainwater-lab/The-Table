"""W3C PROV-DM provenance tracking for the Lens.

Implements provenance tracking for facts in the Spark-Box data membrane.
Every fact is tagged with its source, derivation chain, and attribution.
This enables trust/transparency features and audit trails.

W3C PROV-DM Core Concepts:
- Entity: A fact or data item
- Activity: An action that created/modified data
- Agent: The source that performed an activity

PROV Relations:
- wasGeneratedBy: Links entity to activity that created it
- wasAttributedTo: Links entity to agent responsible for it
- wasDerivedFrom: Links derived entity to source entity

WO-009: Provenance Tracking (W3C PROV-DM)
Reference: RQ-LENS-001 Finding 6
"""

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ==============================================================================
# HASH COMPUTATION
# ==============================================================================

def compute_value_hash(value: Any) -> str:
    """Compute deterministic SHA-256 hash of a value.

    Args:
        value: Any JSON-serializable value

    Returns:
        First 16 characters of SHA-256 hex digest
    """
    serialized = json.dumps(value, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()[:16]


# ==============================================================================
# PROV-DM CORE TYPES
# ==============================================================================

@dataclass(frozen=True)
class ProvenanceEntity:
    """A fact or data item in the provenance graph.

    Corresponds to prov:Entity in W3C PROV-DM.
    Represents a snapshot of data at a point in time.
    """

    entity_id: str
    """Unique identifier (typically entity_id:attribute)."""

    value_hash: str
    """SHA-256 hash of the value (first 16 chars)."""

    created_at: int
    """Turn number when this entity was created."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "entity_id": self.entity_id,
            "value_hash": self.value_hash,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProvenanceEntity':
        """Deserialize from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            ProvenanceEntity instance
        """
        return cls(
            entity_id=data["entity_id"],
            value_hash=data["value_hash"],
            created_at=data["created_at"],
        )


@dataclass(frozen=True)
class ProvenanceActivity:
    """An action that created or modified data.

    Corresponds to prov:Activity in W3C PROV-DM.
    Has a start and end time (turn numbers).
    """

    activity_id: str
    """Unique activity identifier."""

    activity_type: str
    """Type of activity (e.g., 'spark_generation', 'box_calculation', 'player_input')."""

    started_at: int
    """Turn number when activity started."""

    ended_at: Optional[int] = None
    """Turn number when activity ended (None if still running)."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "activity_id": self.activity_id,
            "activity_type": self.activity_type,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProvenanceActivity':
        """Deserialize from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            ProvenanceActivity instance
        """
        return cls(
            activity_id=data["activity_id"],
            activity_type=data["activity_type"],
            started_at=data["started_at"],
            ended_at=data.get("ended_at"),
        )


@dataclass(frozen=True)
class ProvenanceAgent:
    """The source that performed an activity.

    Corresponds to prov:Agent in W3C PROV-DM.
    Can be a system component, player, or other source.
    """

    agent_id: str
    """Unique agent identifier."""

    agent_type: str
    """Type of agent ('spark', 'box', 'player', 'system')."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProvenanceAgent':
        """Deserialize from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            ProvenanceAgent instance
        """
        return cls(
            agent_id=data["agent_id"],
            agent_type=data["agent_type"],
        )


# ==============================================================================
# PROV-DM RELATIONS
# ==============================================================================

@dataclass(frozen=True)
class WasGeneratedBy:
    """Relation linking an entity to the activity that created it.

    Corresponds to prov:wasGeneratedBy in W3C PROV-DM.
    """

    entity_id: str
    """ID of the generated entity."""

    activity_id: str
    """ID of the generating activity."""

    timestamp: int
    """Turn when generation occurred."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "entity_id": self.entity_id,
            "activity_id": self.activity_id,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WasGeneratedBy':
        """Deserialize from dictionary."""
        return cls(
            entity_id=data["entity_id"],
            activity_id=data["activity_id"],
            timestamp=data["timestamp"],
        )


@dataclass(frozen=True)
class WasAttributedTo:
    """Relation linking an entity to the agent responsible for it.

    Corresponds to prov:wasAttributedTo in W3C PROV-DM.
    """

    entity_id: str
    """ID of the attributed entity."""

    agent_id: str
    """ID of the responsible agent."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "entity_id": self.entity_id,
            "agent_id": self.agent_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WasAttributedTo':
        """Deserialize from dictionary."""
        return cls(
            entity_id=data["entity_id"],
            agent_id=data["agent_id"],
        )


@dataclass(frozen=True)
class WasDerivedFrom:
    """Relation linking a derived entity to its source entity.

    Corresponds to prov:wasDerivedFrom in W3C PROV-DM.
    """

    derived_entity_id: str
    """ID of the derived entity."""

    source_entity_id: str
    """ID of the source entity."""

    activity_id: Optional[str] = None
    """Optional activity that performed the derivation."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "derived_entity_id": self.derived_entity_id,
            "source_entity_id": self.source_entity_id,
            "activity_id": self.activity_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WasDerivedFrom':
        """Deserialize from dictionary."""
        return cls(
            derived_entity_id=data["derived_entity_id"],
            source_entity_id=data["source_entity_id"],
            activity_id=data.get("activity_id"),
        )


# ==============================================================================
# PROVENANCE EXPLANATION
# ==============================================================================

@dataclass(frozen=True)
class ProvenanceExplanation:
    """Human-readable provenance summary for an entity.

    Provides a complete explanation of where a fact came from,
    who created it, and what it was derived from.
    """

    entity_id: str
    """ID of the entity being explained."""

    current_value_hash: str
    """Hash of the current value."""

    attributed_to: List[str]
    """List of agent IDs responsible for this entity."""

    derived_from: List[str]
    """List of source entity IDs this was derived from."""

    generation_activity: Optional[str]
    """Activity type that generated this entity (if any)."""

    generation_turn: Optional[int]
    """Turn when entity was generated (if known)."""

    chain_depth: int
    """Depth of the derivation chain (0 = original, 1 = derived once, etc.)."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "entity_id": self.entity_id,
            "current_value_hash": self.current_value_hash,
            "attributed_to": list(self.attributed_to),
            "derived_from": list(self.derived_from),
            "generation_activity": self.generation_activity,
            "generation_turn": self.generation_turn,
            "chain_depth": self.chain_depth,
        }


# ==============================================================================
# PROVENANCE STORE
# ==============================================================================

class ProvenanceStore:
    """Central store for provenance data.

    Tracks entities, activities, agents, and their relationships
    according to W3C PROV-DM model.
    """

    def __init__(self):
        """Initialize empty provenance store."""
        # Core registries
        self._entities: Dict[str, ProvenanceEntity] = {}
        self._activities: Dict[str, ProvenanceActivity] = {}
        self._agents: Dict[str, ProvenanceAgent] = {}

        # Relation storage
        self._generations: Dict[str, WasGeneratedBy] = {}  # entity_id -> relation
        self._attributions: Dict[str, List[WasAttributedTo]] = {}  # entity_id -> relations
        self._derivations: Dict[str, List[WasDerivedFrom]] = {}  # derived_entity_id -> relations

        # Reverse index for derivation chains
        self._derived_entities: Dict[str, List[str]] = {}  # source_entity_id -> derived_entity_ids

    # ==========================================================================
    # ENTITY REGISTRATION
    # ==========================================================================

    def register_entity(self, entity_id: str, value: Any, turn: int) -> ProvenanceEntity:
        """Register a new provenance entity.

        Args:
            entity_id: Unique identifier for the entity
            value: The value to compute hash from
            turn: Turn number when entity was created

        Returns:
            Created ProvenanceEntity
        """
        value_hash = compute_value_hash(value)
        entity = ProvenanceEntity(
            entity_id=entity_id,
            value_hash=value_hash,
            created_at=turn,
        )
        self._entities[entity_id] = entity
        return entity

    def get_entity(self, entity_id: str) -> Optional[ProvenanceEntity]:
        """Get a provenance entity by ID.

        Args:
            entity_id: Entity to retrieve

        Returns:
            ProvenanceEntity or None if not found
        """
        return self._entities.get(entity_id)

    # ==========================================================================
    # ACTIVITY REGISTRATION
    # ==========================================================================

    def register_activity(self, activity_type: str, turn: int) -> ProvenanceActivity:
        """Register a new activity.

        Args:
            activity_type: Type of activity (e.g., 'spark_generation')
            turn: Turn number when activity started

        Returns:
            Created ProvenanceActivity with unique ID
        """
        activity_id = f"activity_{uuid.uuid4().hex[:8]}"
        activity = ProvenanceActivity(
            activity_id=activity_id,
            activity_type=activity_type,
            started_at=turn,
            ended_at=None,
        )
        self._activities[activity_id] = activity
        return activity

    def complete_activity(self, activity_id: str, turn: int) -> None:
        """Mark an activity as completed.

        Args:
            activity_id: Activity to complete
            turn: Turn number when activity ended
        """
        activity = self._activities.get(activity_id)
        if activity is None:
            return

        # Create new immutable activity with ended_at set
        completed = ProvenanceActivity(
            activity_id=activity.activity_id,
            activity_type=activity.activity_type,
            started_at=activity.started_at,
            ended_at=turn,
        )
        self._activities[activity_id] = completed

    def get_activity(self, activity_id: str) -> Optional[ProvenanceActivity]:
        """Get an activity by ID.

        Args:
            activity_id: Activity to retrieve

        Returns:
            ProvenanceActivity or None if not found
        """
        return self._activities.get(activity_id)

    # ==========================================================================
    # AGENT REGISTRATION
    # ==========================================================================

    def register_agent(self, agent_id: str, agent_type: str) -> ProvenanceAgent:
        """Register a new agent.

        Args:
            agent_id: Unique identifier for the agent
            agent_type: Type of agent ('spark', 'box', 'player', 'system')

        Returns:
            Created ProvenanceAgent
        """
        agent = ProvenanceAgent(
            agent_id=agent_id,
            agent_type=agent_type,
        )
        self._agents[agent_id] = agent
        return agent

    def get_agent(self, agent_id: str) -> Optional[ProvenanceAgent]:
        """Get an agent by ID.

        Args:
            agent_id: Agent to retrieve

        Returns:
            ProvenanceAgent or None if not found
        """
        return self._agents.get(agent_id)

    # ==========================================================================
    # RELATION CREATION
    # ==========================================================================

    def record_generation(self, entity_id: str, activity_id: str, turn: int) -> None:
        """Record that an entity was generated by an activity.

        Args:
            entity_id: ID of the generated entity
            activity_id: ID of the generating activity
            turn: Turn when generation occurred
        """
        relation = WasGeneratedBy(
            entity_id=entity_id,
            activity_id=activity_id,
            timestamp=turn,
        )
        self._generations[entity_id] = relation

    def record_attribution(self, entity_id: str, agent_id: str) -> None:
        """Record that an entity was attributed to an agent.

        Args:
            entity_id: ID of the entity
            agent_id: ID of the responsible agent
        """
        relation = WasAttributedTo(
            entity_id=entity_id,
            agent_id=agent_id,
        )
        if entity_id not in self._attributions:
            self._attributions[entity_id] = []
        self._attributions[entity_id].append(relation)

    def record_derivation(
        self,
        derived_id: str,
        source_id: str,
        activity_id: Optional[str] = None,
    ) -> None:
        """Record that an entity was derived from another entity.

        Args:
            derived_id: ID of the derived entity
            source_id: ID of the source entity
            activity_id: Optional activity that performed derivation
        """
        relation = WasDerivedFrom(
            derived_entity_id=derived_id,
            source_entity_id=source_id,
            activity_id=activity_id,
        )
        if derived_id not in self._derivations:
            self._derivations[derived_id] = []
        self._derivations[derived_id].append(relation)

        # Update reverse index
        if source_id not in self._derived_entities:
            self._derived_entities[source_id] = []
        self._derived_entities[source_id].append(derived_id)

    # ==========================================================================
    # QUERY METHODS
    # ==========================================================================

    def get_provenance_chain(self, entity_id: str) -> List[ProvenanceEntity]:
        """Get the full derivation chain for an entity.

        Traces back through all wasDerivedFrom relations to find
        the complete ancestry of an entity.

        Args:
            entity_id: Entity to trace

        Returns:
            List of ProvenanceEntity from root to current (current is last)
        """
        chain = []
        visited = set()
        current_id = entity_id

        # Build chain from current back to root
        while current_id is not None:
            if current_id in visited:
                # Circular reference detected, stop
                break
            visited.add(current_id)

            entity = self._entities.get(current_id)
            if entity is not None:
                chain.append(entity)

            # Find source
            derivations = self._derivations.get(current_id, [])
            if derivations:
                # Take first source (could be multiple)
                current_id = derivations[0].source_entity_id
            else:
                current_id = None

        # Reverse so root is first, current is last
        chain.reverse()
        return chain

    def get_entity_sources(self, entity_id: str) -> List[ProvenanceAgent]:
        """Get all agents responsible for an entity.

        Args:
            entity_id: Entity to query

        Returns:
            List of ProvenanceAgent attributed to this entity
        """
        attributions = self._attributions.get(entity_id, [])
        agents = []
        for attr in attributions:
            agent = self._agents.get(attr.agent_id)
            if agent is not None:
                agents.append(agent)
        return agents

    def explain(self, entity_id: str) -> ProvenanceExplanation:
        """Generate a human-readable explanation of an entity's provenance.

        Args:
            entity_id: Entity to explain

        Returns:
            ProvenanceExplanation with full provenance details
        """
        entity = self._entities.get(entity_id)
        current_hash = entity.value_hash if entity else ""

        # Get attributed agents
        attributions = self._attributions.get(entity_id, [])
        attributed_to = [attr.agent_id for attr in attributions]

        # Get direct sources
        derivations = self._derivations.get(entity_id, [])
        derived_from = [deriv.source_entity_id for deriv in derivations]

        # Get generation info
        generation = self._generations.get(entity_id)
        generation_activity = None
        generation_turn = None
        if generation:
            activity = self._activities.get(generation.activity_id)
            if activity:
                generation_activity = activity.activity_type
            generation_turn = generation.timestamp

        # Calculate chain depth
        chain = self.get_provenance_chain(entity_id)
        chain_depth = len(chain) - 1 if chain else 0

        return ProvenanceExplanation(
            entity_id=entity_id,
            current_value_hash=current_hash,
            attributed_to=attributed_to,
            derived_from=derived_from,
            generation_activity=generation_activity,
            generation_turn=generation_turn,
            chain_depth=chain_depth,
        )

    # ==========================================================================
    # SERIALIZATION
    # ==========================================================================

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary.

        Returns:
            Dictionary representation of entire store
        """
        return {
            "entities": {
                eid: entity.to_dict()
                for eid, entity in self._entities.items()
            },
            "activities": {
                aid: activity.to_dict()
                for aid, activity in self._activities.items()
            },
            "agents": {
                aid: agent.to_dict()
                for aid, agent in self._agents.items()
            },
            "generations": {
                eid: gen.to_dict()
                for eid, gen in self._generations.items()
            },
            "attributions": {
                eid: [attr.to_dict() for attr in attrs]
                for eid, attrs in self._attributions.items()
            },
            "derivations": {
                eid: [deriv.to_dict() for deriv in derivs]
                for eid, derivs in self._derivations.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProvenanceStore':
        """Deserialize from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            ProvenanceStore instance
        """
        store = cls()

        # Restore entities
        for eid, entity_data in data.get("entities", {}).items():
            store._entities[eid] = ProvenanceEntity.from_dict(entity_data)

        # Restore activities
        for aid, activity_data in data.get("activities", {}).items():
            store._activities[aid] = ProvenanceActivity.from_dict(activity_data)

        # Restore agents
        for aid, agent_data in data.get("agents", {}).items():
            store._agents[aid] = ProvenanceAgent.from_dict(agent_data)

        # Restore generations
        for eid, gen_data in data.get("generations", {}).items():
            store._generations[eid] = WasGeneratedBy.from_dict(gen_data)

        # Restore attributions
        for eid, attr_list in data.get("attributions", {}).items():
            store._attributions[eid] = [
                WasAttributedTo.from_dict(attr_data) for attr_data in attr_list
            ]

        # Restore derivations and rebuild reverse index
        for eid, deriv_list in data.get("derivations", {}).items():
            store._derivations[eid] = []
            for deriv_data in deriv_list:
                deriv = WasDerivedFrom.from_dict(deriv_data)
                store._derivations[eid].append(deriv)
                # Rebuild reverse index
                source_id = deriv.source_entity_id
                if source_id not in store._derived_entities:
                    store._derived_entities[source_id] = []
                store._derived_entities[source_id].append(eid)

        return store
