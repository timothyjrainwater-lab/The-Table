"""WO-032: NarrativeBrief — One-Way Valve (STP → Spark-Safe Context)

NarrativeBrief is the Lens layer's containment boundary. It controls exactly
what mechanical data Spark can see, preventing Box state contamination.

WHAT NARRATIVEBRIEF CONTAINS:
- What happened (action type, outcome summary, severity)
- Who was involved (display names, NOT entity IDs)
- Where it happened (location descriptions, NOT grid coordinates)
- Weapon/spell/condition names (NOT dataclass internals)

WHAT NARRATIVEBRIEF MUST NOT CONTAIN:
- Entity IDs (internal identifiers)
- Raw HP values (current or max)
- AC values
- Attack bonuses or roll results
- Damage numbers (unless explicitly allowed per transparency mode)
- Entity dictionaries
- Grid coordinates
- RNG state or seeds

SEVERITY MAPPING (from FrozenWorldStateView HP data):
- "minor": damage < 20% of target max HP
- "moderate": 20-40% of target max HP
- "severe": 40-60% of target max HP
- "devastating": 60-80% of target max HP
- "lethal": target defeated or > 80% of max HP

BOUNDARY LAW (BL-003): No imports from aidm.core.
BOUNDARY LAW (BL-020): FrozenWorldStateView for read-only state access.
AXIOM 3: Lens adapts stance, not authority — we describe outcomes, not compute them.

Reference: docs/planning/EXECUTION_PLAN_V2_POST_AUDIT.md (WO-032)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from aidm.core.state import FrozenWorldStateView


@dataclass(frozen=True)
class NarrativeBrief:
    """One-way valve: STP → Spark-safe context.

    Implements Lens layer's containment boundary per WO-032.
    Contains ONLY Spark-safe data derived from Box outcomes.

    Attributes:
        action_type: Narration token (e.g., "attack_hit", "spell_damage")
        actor_name: Display name of actor (NOT entity ID)
        target_name: Display name of target (NOT entity ID)
        outcome_summary: Natural language outcome summary
        severity: Wound severity category ("minor", "moderate", "severe", "devastating", "lethal")
        weapon_name: Weapon name (NOT Weapon dataclass)
        damage_type: Damage type string (e.g., "slashing", "fire")
        condition_applied: Condition name if applied (e.g., "prone", "stunned")
        target_defeated: Whether target was defeated
        previous_narrations: Last N narration texts for continuity
        scene_description: Brief location context
        source_event_ids: STP event IDs this was built from
        provenance_tag: Always [DERIVED] from [BOX] STPs
    """

    # What happened (mechanical outcome)
    action_type: str
    actor_name: str
    target_name: Optional[str] = None

    # Outcome description (safe to show)
    outcome_summary: str = ""
    severity: str = "minor"  # "minor", "moderate", "severe", "devastating", "lethal"

    # Context for narration quality
    weapon_name: Optional[str] = None
    damage_type: Optional[str] = None
    condition_applied: Optional[str] = None
    target_defeated: bool = False

    # Scene context (for continuity)
    previous_narrations: List[str] = field(default_factory=list)
    scene_description: Optional[str] = None

    # Provenance tracking
    source_event_ids: List[int] = field(default_factory=list)
    provenance_tag: str = "[DERIVED]"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation
        """
        return {
            "action_type": self.action_type,
            "actor_name": self.actor_name,
            "target_name": self.target_name,
            "outcome_summary": self.outcome_summary,
            "severity": self.severity,
            "weapon_name": self.weapon_name,
            "damage_type": self.damage_type,
            "condition_applied": self.condition_applied,
            "target_defeated": self.target_defeated,
            "previous_narrations": self.previous_narrations,
            "scene_description": self.scene_description,
            "source_event_ids": self.source_event_ids,
            "provenance_tag": self.provenance_tag,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NarrativeBrief":
        """Create from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            NarrativeBrief instance
        """
        return cls(
            action_type=data["action_type"],
            actor_name=data["actor_name"],
            target_name=data.get("target_name"),
            outcome_summary=data.get("outcome_summary", ""),
            severity=data.get("severity", "minor"),
            weapon_name=data.get("weapon_name"),
            damage_type=data.get("damage_type"),
            condition_applied=data.get("condition_applied"),
            target_defeated=data.get("target_defeated", False),
            previous_narrations=data.get("previous_narrations", []),
            scene_description=data.get("scene_description"),
            source_event_ids=data.get("source_event_ids", []),
            provenance_tag=data.get("provenance_tag", "[DERIVED]"),
        )


# ══════════════════════════════════════════════════════════════════════════
# Severity Mapping (HP Percentage → Severity Category)
# ══════════════════════════════════════════════════════════════════════════


def compute_severity(
    damage: int,
    target_hp_before: int,
    target_hp_max: int,
    target_defeated: bool = False,
) -> str:
    """Compute severity category from HP damage percentage.

    Severity categories:
    - "lethal": target defeated or > 80% of max HP
    - "devastating": 60-80% of max HP
    - "severe": 40-60% of max HP
    - "moderate": 20-40% of max HP
    - "minor": < 20% of max HP

    Args:
        damage: Damage dealt
        target_hp_before: Target HP before damage
        target_hp_max: Target max HP
        target_defeated: Whether target was defeated

    Returns:
        Severity category string
    """
    if target_defeated:
        return "lethal"

    if target_hp_max <= 0:
        return "minor"  # Can't compute severity

    # Compute damage as percentage of max HP
    damage_percent = (damage / target_hp_max) * 100

    if damage_percent >= 80:
        return "lethal"
    elif damage_percent >= 60:
        return "devastating"
    elif damage_percent >= 40:
        return "severe"
    elif damage_percent >= 20:
        return "moderate"
    else:
        return "minor"


# ══════════════════════════════════════════════════════════════════════════
# Entity Name Resolution (Entity Dict → Display Name)
# ══════════════════════════════════════════════════════════════════════════


def resolve_entity_name(entity_id: str, frozen_view: FrozenWorldStateView) -> str:
    """Resolve entity ID to display name from FrozenWorldStateView.

    Looks up entity_id in frozen view's entities dict and extracts the "name"
    field. Falls back to entity_id if name not found.

    Args:
        entity_id: Entity ID to resolve
        frozen_view: FrozenWorldStateView for read-only state access

    Returns:
        Display name string
    """
    entities = frozen_view.entities

    if entity_id not in entities:
        return entity_id  # Fallback to ID

    entity_data = entities[entity_id]
    return entity_data.get("name", entity_id)


def get_entity_hp_data(
    entity_id: str,
    frozen_view: FrozenWorldStateView,
) -> tuple[int, int]:
    """Get entity HP (current, max) from FrozenWorldStateView.

    Args:
        entity_id: Entity ID to query
        frozen_view: FrozenWorldStateView for read-only state access

    Returns:
        Tuple of (current_hp, max_hp)
    """
    entities = frozen_view.entities

    if entity_id not in entities:
        return (0, 0)

    entity_data = entities[entity_id]
    current_hp = entity_data.get("hp", 0)
    max_hp = entity_data.get("hp_max", 0)

    return (current_hp, max_hp)


# ══════════════════════════════════════════════════════════════════════════
# NarrativeBrief Assembler (STP Events → NarrativeBrief)
# ══════════════════════════════════════════════════════════════════════════


def assemble_narrative_brief(
    events: List[Dict[str, Any]],
    narration_token: str,
    frozen_view: FrozenWorldStateView,
    previous_narrations: Optional[List[str]] = None,
    scene_description: Optional[str] = None,
) -> NarrativeBrief:
    """Assemble NarrativeBrief from STP events and FrozenWorldStateView.

    This is the one-way valve from Box (STP events) to Spark-safe context.
    All mechanical data is filtered through this function to ensure only
    safe-to-show information reaches Spark.

    Args:
        events: List of STP event dicts from Box resolution
        narration_token: Narration token (e.g., "attack_hit", "spell_damage")
        frozen_view: FrozenWorldStateView for read-only state access
        previous_narrations: Last N narration texts for continuity
        scene_description: Brief location context

    Returns:
        NarrativeBrief with Spark-safe context
    """
    # Extract actor and target IDs from events
    actor_id = ""
    target_id = ""
    weapon_name = None
    damage_type = None
    condition_applied = None
    damage_dealt = 0
    target_defeated = False
    event_ids = []

    for event in events:
        # Track event IDs for provenance
        if "event_id" in event:
            event_ids.append(event["event_id"])

        # Extract actor/target from various event types
        event_type = event.get("type") or event.get("event_type")

        if event_type == "attack_roll":
            actor_id = event.get("attacker", actor_id)
            target_id = event.get("target", target_id)

        elif event_type == "damage_dealt":
            actor_id = event.get("attacker", actor_id)
            target_id = event.get("target", target_id)
            damage_dealt = event.get("damage", 0)
            damage_type = event.get("damage_type")

        elif event_type == "hp_changed":
            payload = event.get("payload", event)
            target_id = payload.get("entity_id", target_id)
            delta = payload.get("delta", 0)
            if delta < 0:
                damage_dealt = abs(delta)

        elif event_type == "entity_defeated":
            target_id = event.get("target", target_id)
            target_defeated = True

        elif event_type == "condition_applied":
            target_id = event.get("target", target_id)
            condition_applied = event.get("condition")

        # Extract weapon name
        if "weapon" in event:
            weapon_name = event["weapon"]

    # Resolve entity names from FrozenWorldStateView
    actor_name = resolve_entity_name(actor_id, frozen_view) if actor_id else "someone"
    target_name = resolve_entity_name(target_id, frozen_view) if target_id else None

    # Compute severity if damage was dealt
    severity = "minor"
    if damage_dealt > 0 and target_id:
        target_hp_before, target_hp_max = get_entity_hp_data(target_id, frozen_view)
        severity = compute_severity(
            damage=damage_dealt,
            target_hp_before=target_hp_before,
            target_hp_max=target_hp_max,
            target_defeated=target_defeated,
        )
    elif target_defeated:
        severity = "lethal"

    # Build outcome summary
    outcome_summary = _build_outcome_summary(
        action_type=narration_token,
        actor_name=actor_name,
        target_name=target_name,
        weapon_name=weapon_name,
        target_defeated=target_defeated,
    )

    # Assemble NarrativeBrief
    return NarrativeBrief(
        action_type=narration_token,
        actor_name=actor_name,
        target_name=target_name,
        outcome_summary=outcome_summary,
        severity=severity,
        weapon_name=weapon_name,
        damage_type=damage_type,
        condition_applied=condition_applied,
        target_defeated=target_defeated,
        previous_narrations=previous_narrations or [],
        scene_description=scene_description,
        source_event_ids=event_ids,
        provenance_tag="[DERIVED]",
    )


def _build_outcome_summary(
    action_type: str,
    actor_name: str,
    target_name: Optional[str],
    weapon_name: Optional[str],
    target_defeated: bool,
) -> str:
    """Build natural language outcome summary.

    Args:
        action_type: Narration token
        actor_name: Actor display name
        target_name: Target display name
        weapon_name: Weapon name
        target_defeated: Whether target defeated

    Returns:
        Outcome summary string
    """
    # Handle different action types
    if "attack_hit" in action_type:
        weapon = weapon_name or "weapon"
        target = target_name or "the target"
        if target_defeated:
            return f"{actor_name} defeats {target} with {weapon}"
        return f"{actor_name} hits {target} with {weapon}"

    elif "attack_miss" in action_type:
        weapon = weapon_name or "weapon"
        target = target_name or "the target"
        return f"{actor_name} misses {target} with {weapon}"

    elif "critical" in action_type:
        weapon = weapon_name or "weapon"
        target = target_name or "the target"
        return f"{actor_name} scores a critical hit on {target} with {weapon}"

    elif "spell" in action_type:
        target = target_name or "the target"
        return f"{actor_name} casts a spell on {target}"

    elif "defeat" in action_type:
        target = target_name or "the target"
        return f"{actor_name} defeats {target}"

    # Generic fallback
    if target_name:
        return f"{actor_name} acts against {target_name}"
    return f"{actor_name} acts"
