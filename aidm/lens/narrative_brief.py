"""WO-032/WO-046B: NarrativeBrief — One-Way Valve (STP → Spark-Safe Context)

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

EVENT TYPES HANDLED (WO-046B):
- Attack events: attack_roll, damage_dealt/damage_roll, concealment_miss
- Full attack events: full_attack_start, full_attack_end
- HP events: hp_changed, entity_defeated
- Condition events: condition_applied, condition_removed
- Spell events: spell_cast, spell_cast_failed, concentration_broken
- Maneuver events: bull_rush_*, trip_*, overrun_*, sunder_*, disarm_*, grapple_*
- AoO events: aoo_triggered, aoo_blocked_by_cover, aoo_avoided_by_tumble
- Movement events: movement_declared, mounted_move_declared
- Targeting events: targeting_failed

BOUNDARY LAW (BL-003): No imports from aidm.core.
BOUNDARY LAW (BL-020): FrozenWorldStateView for read-only state access.
AXIOM 3: Lens adapts stance, not authority — we describe outcomes, not compute them.

Reference: docs/planning/EXECUTION_PLAN_V2_POST_AUDIT.md (WO-032, WO-046B)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from aidm.core.state import FrozenWorldStateView
from aidm.schemas.presentation_semantics import AbilityPresentationEntry

# TYPE_CHECKING import to avoid circular dependency at runtime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aidm.lens.presentation_registry import PresentationRegistryLoader


@dataclass(frozen=True)
class NarrativeBrief:
    """One-way valve: STP → Spark-safe context.

    Implements Lens layer's containment boundary per WO-032/WO-046B.
    Contains ONLY Spark-safe data derived from Box outcomes.

    Attributes:
        action_type: Narration token (e.g., "attack_hit", "spell_damage_dealt")
        actor_name: Display name of actor (NOT entity ID)
        target_name: Display name of target (NOT entity ID)
        outcome_summary: Natural language outcome summary
        severity: Wound severity category ("minor", "moderate", "severe", "devastating", "lethal")
        weapon_name: Weapon name (NOT Weapon dataclass)
        spell_name: Spell name string (WO-046B)
        damage_type: Damage type string (e.g., "slashing", "fire")
        condition_applied: Condition name if applied (e.g., "prone", "stunned")
        condition_removed: Condition name if removed (WO-046B)
        maneuver_type: Combat maneuver type (e.g., "bull_rush", "trip") (WO-046B)
        target_defeated: Whether target was defeated
        visible_gear: Externally visible gear names for actor (WO-056, AD-005 Layer 3)
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
    spell_name: Optional[str] = None
    damage_type: Optional[str] = None
    condition_applied: Optional[str] = None
    condition_removed: Optional[str] = None
    maneuver_type: Optional[str] = None
    target_defeated: bool = False

    # Multi-target (WO-BRIEF-WIDTH-001)
    additional_targets: tuple = ()  # ((name: str, severity: str, defeated: bool), ...)

    # Causal chain (WO-BRIEF-WIDTH-001)
    causal_chain_id: Optional[str] = None
    chain_position: int = 0  # 0=standalone, 1=first, 2+=continuation

    # Condition stack (WO-BRIEF-WIDTH-001)
    active_conditions: tuple = ()   # All conditions currently on target
    actor_conditions: tuple = ()    # Conditions on actor affecting this action

    # Gear affordance (WO-056, AD-005 Layer 3)
    visible_gear: Optional[tuple] = None  # Display names, NOT item_ids

    # Presentation semantics (AD-007 Layer B)
    presentation_semantics: Optional[AbilityPresentationEntry] = None

    # Scene context (for continuity)
    previous_narrations: tuple = ()
    scene_description: Optional[str] = None

    # Provenance tracking
    source_event_ids: tuple = ()
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
            "spell_name": self.spell_name,
            "damage_type": self.damage_type,
            "condition_applied": self.condition_applied,
            "condition_removed": self.condition_removed,
            "maneuver_type": self.maneuver_type,
            "target_defeated": self.target_defeated,
            "additional_targets": [
                {"name": t[0], "severity": t[1], "defeated": t[2]}
                for t in self.additional_targets
            ],
            "causal_chain_id": self.causal_chain_id,
            "chain_position": self.chain_position,
            "active_conditions": list(self.active_conditions),
            "actor_conditions": list(self.actor_conditions),
            "visible_gear": list(self.visible_gear) if self.visible_gear else self.visible_gear,
            "presentation_semantics": (
                self.presentation_semantics.to_dict()
                if self.presentation_semantics is not None
                else None
            ),
            "previous_narrations": list(self.previous_narrations),
            "scene_description": self.scene_description,
            "source_event_ids": list(self.source_event_ids),
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
            spell_name=data.get("spell_name"),
            damage_type=data.get("damage_type"),
            condition_applied=data.get("condition_applied"),
            condition_removed=data.get("condition_removed"),
            maneuver_type=data.get("maneuver_type"),
            target_defeated=data.get("target_defeated", False),
            additional_targets=tuple(
                (t["name"], t["severity"], t["defeated"])
                for t in data.get("additional_targets", [])
            ),
            causal_chain_id=data.get("causal_chain_id"),
            chain_position=data.get("chain_position", 0),
            active_conditions=tuple(data.get("active_conditions", ())),
            actor_conditions=tuple(data.get("actor_conditions", ())),
            visible_gear=tuple(data.get("visible_gear")) if data.get("visible_gear") is not None else None,
            presentation_semantics=(
                AbilityPresentationEntry.from_dict(data["presentation_semantics"])
                if data.get("presentation_semantics") is not None
                else None
            ),
            previous_narrations=tuple(data.get("previous_narrations", ())),
            scene_description=data.get("scene_description"),
            source_event_ids=tuple(data.get("source_event_ids", ())),
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


def get_entity_conditions(
    entity_id: str,
    frozen_view: FrozenWorldStateView,
) -> tuple:
    """Get active condition names for an entity from FrozenWorldStateView.

    Returns condition type names only (Spark-safe). No modifier data.

    Args:
        entity_id: Entity ID to query
        frozen_view: FrozenWorldStateView for read-only state access

    Returns:
        Tuple of condition name strings (e.g., ("prone", "grappled"))
    """
    entities = frozen_view.entities

    if entity_id not in entities:
        return ()

    entity_data = entities[entity_id]
    conditions_data = entity_data.get("conditions", {})

    if not conditions_data:
        return ()

    # Return condition type keys (these are display-safe names like "prone", "grappled")
    # Note: FrozenWorldStateView wraps dicts in MappingProxyType, so we use
    # hasattr(.keys) rather than isinstance(dict) to support both.
    if not hasattr(conditions_data, "keys"):
        return ()

    return tuple(sorted(conditions_data.keys()))


# ══════════════════════════════════════════════════════════════════════════
# Gear Affordance Resolution (WO-056, AD-005 Layer 3)
# ══════════════════════════════════════════════════════════════════════════


def resolve_visible_gear_names(
    item_ids: List[str],
    catalog,
) -> List[str]:
    """Convert item_ids from container resolver into display names.

    Bridges Box layer (item_ids from get_visible_gear()) to Lens layer
    (display names safe for Spark narration). Item IDs that don't resolve
    in the catalog are humanized (underscores → spaces, title case).

    Args:
        item_ids: List of item_id strings from ContainerResolver.get_visible_gear().
        catalog: EquipmentCatalog instance for name lookups.

    Returns:
        List of display name strings (never item_ids).
    """
    names = []
    for item_id in item_ids:
        if catalog is not None:
            item = catalog.get(item_id)
            if item is not None:
                names.append(item.name)
                continue
        # Fallback: humanize item_id
        names.append(item_id.replace("_", " ").title())
    return names


# ══════════════════════════════════════════════════════════════════════════
# NarrativeBrief Assembler (STP Events → NarrativeBrief)
# ══════════════════════════════════════════════════════════════════════════


def assemble_narrative_brief(
    events: List[Dict[str, Any]],
    narration_token: str,
    frozen_view: FrozenWorldStateView,
    previous_narrations: Optional[List[str]] = None,
    scene_description: Optional[str] = None,
    visible_gear: Optional[List[str]] = None,
    presentation_semantics: Optional[AbilityPresentationEntry] = None,
    presentation_registry: Optional["PresentationRegistryLoader"] = None,
) -> NarrativeBrief:
    """Assemble NarrativeBrief from STP events and FrozenWorldStateView.

    This is the one-way valve from Box (STP events) to Spark-safe context.
    All mechanical data is filtered through this function to ensure only
    safe-to-show information reaches Spark.

    WO-046B: Handles all event types emitted by Box layer:
    - Attack events (attack_roll, damage_dealt/damage_roll, concealment_miss)
    - Full attack events (full_attack_start, full_attack_end)
    - HP events (hp_changed, entity_defeated)
    - Condition events (condition_applied, condition_removed)
    - Spell events (spell_cast, spell_cast_failed, concentration_broken)
    - Maneuver events (bull_rush_*, trip_*, overrun_*, sunder_*, disarm_*, grapple_*)
    - AoO events (aoo_triggered, aoo_blocked_by_cover, aoo_avoided_by_tumble)
    - Movement events (movement_declared, mounted_move_declared)
    - Targeting events (targeting_failed)

    Args:
        events: List of STP event dicts from Box resolution
        narration_token: Narration token (e.g., "attack_hit", "spell_damage_dealt")
        frozen_view: FrozenWorldStateView for read-only state access
        previous_narrations: Last N narration texts for continuity
        scene_description: Brief location context
        visible_gear: Display names of externally visible gear (WO-056, AD-005 Layer 3)
        presentation_semantics: AD-007 Layer B semantics for the ability (if applicable)
        presentation_registry: AD-007 registry for content_id → Layer B lookup (WO-GAP-B-001)

    Returns:
        NarrativeBrief with Spark-safe context
    """
    # Extract actor and target IDs from events
    actor_id = ""
    target_id = ""
    weapon_name = None
    spell_name = None
    damage_type = None
    condition_applied = None
    condition_removed = None
    maneuver_type = None
    damage_dealt = 0
    target_defeated = False
    event_ids = []
    content_id = None
    # WO-BRIEF-WIDTH-001: Multi-target tracking
    damage_by_target: Dict[str, Dict[str, Any]] = {}  # {target_id: {damage, defeated}}
    # WO-BRIEF-WIDTH-001: Causal chain tracking
    causal_chain_id = None
    chain_position = 0

    for event in events:
        # Track event IDs for provenance
        if "event_id" in event:
            event_ids.append(event["event_id"])

        # Extract actor/target from various event types
        event_type = event.get("type") or event.get("event_type")
        payload = event.get("payload", event)

        # === ATTACK EVENTS ===
        if event_type == "attack_roll":
            actor_id = (
                event.get("attacker")
                or payload.get("attacker_id")
                or actor_id
            )
            target_id = (
                event.get("target")
                or payload.get("target_id")
                or target_id
            )

        elif event_type in ("damage_dealt", "damage_roll"):
            actor_id = (
                event.get("attacker")
                or payload.get("attacker_id")
                or actor_id
            )
            dmg_target = (
                event.get("target")
                or payload.get("target_id")
                or target_id
            )
            target_id = dmg_target
            dmg_amount = (
                event.get("damage")
                or payload.get("final_damage")
                or payload.get("damage_total")
                or 0
            )
            damage_dealt = dmg_amount
            damage_type = (
                event.get("damage_type")
                or payload.get("damage_type")
                or damage_type
            )
            # WO-BRIEF-WIDTH-001: Track damage per target for multi-target assembly
            if dmg_target:
                entry = damage_by_target.setdefault(dmg_target, {"damage": 0, "defeated": False})
                entry["damage"] += dmg_amount

        elif event_type == "concealment_miss":
            actor_id = payload.get("attacker_id", actor_id)
            target_id = payload.get("target_id", target_id)

        # === FULL ATTACK EVENTS ===
        elif event_type == "full_attack_start":
            actor_id = payload.get("attacker_id", actor_id)
            target_id = payload.get("target_id", target_id)

        elif event_type == "full_attack_end":
            actor_id = payload.get("attacker_id", actor_id)
            target_id = payload.get("target_id", target_id)

        # === HP EVENTS ===
        elif event_type == "hp_changed":
            target_id = payload.get("entity_id", target_id)
            delta = payload.get("delta", 0)
            if delta < 0:
                damage_dealt = abs(delta)
            # WO-SPELL-NARRATION-POLISH: Extract damage_type from hp_changed
            # (spell damage path adds damage_type to payload)
            if payload.get("damage_type"):
                damage_type = payload["damage_type"]

        elif event_type == "entity_defeated":
            defeated_target = (
                event.get("target")
                or payload.get("entity_id")
                or target_id
            )
            target_id = defeated_target
            target_defeated = True
            # WO-BRIEF-WIDTH-001: Track defeated per target
            if defeated_target:
                entry = damage_by_target.setdefault(defeated_target, {"damage": 0, "defeated": False})
                entry["defeated"] = True

        # === CONDITION EVENTS ===
        elif event_type == "condition_applied":
            target_id = (
                event.get("target")
                or payload.get("target_id")
                or target_id
            )
            condition_applied = (
                event.get("condition")
                or payload.get("condition_type")
                or condition_applied
            )

        elif event_type == "condition_removed":
            target_id = payload.get("entity_id", target_id)
            condition_removed = payload.get("condition_type", condition_removed)

        # === SPELL EVENTS ===
        elif event_type == "spell_cast":
            actor_id = payload.get("caster_id", actor_id)
            spell_name = payload.get("spell_id", spell_name)
            targets = payload.get("targets", [])
            if targets and not target_id:
                target_id = targets[0] if isinstance(targets[0], str) else ""

        elif event_type == "spell_cast_failed":
            actor_id = payload.get("caster_id", actor_id)
            spell_name = payload.get("spell_id", spell_name)

        elif event_type == "concentration_broken":
            actor_id = payload.get("caster_id", actor_id)
            spell_name = payload.get("spell_id", spell_name)

        # === MANEUVER EVENTS ===
        elif event_type in (
            "bull_rush_declared", "bull_rush_success", "bull_rush_failure",
        ):
            actor_id = payload.get("attacker_id", actor_id)
            target_id = payload.get("target_id", target_id)
            maneuver_type = "bull_rush"

        elif event_type in (
            "trip_declared", "trip_success", "trip_failure",
        ):
            actor_id = payload.get("attacker_id", actor_id)
            target_id = payload.get("target_id", target_id)
            maneuver_type = "trip"
            if event_type == "trip_success":
                condition_applied = payload.get("condition_applied", condition_applied)

        elif event_type in ("counter_trip_success", "counter_trip_failure"):
            actor_id = payload.get("counter_attacker", actor_id)
            target_id = payload.get("target_id", target_id)
            maneuver_type = "trip"
            if event_type == "counter_trip_success":
                condition_applied = payload.get("condition_applied", condition_applied)

        elif event_type in (
            "overrun_declared", "overrun_success", "overrun_failure",
        ):
            actor_id = payload.get("attacker_id", actor_id)
            target_id = (
                payload.get("target_id")
                or payload.get("defender_id")
                or target_id
            )
            maneuver_type = "overrun"
            if event_type == "overrun_success":
                condition_applied = payload.get("condition_applied", condition_applied)

        elif event_type == "overrun_avoided":
            actor_id = payload.get("attacker_id", actor_id)
            target_id = payload.get("defender_id", target_id)
            maneuver_type = "overrun"

        elif event_type in (
            "sunder_declared", "sunder_success", "sunder_failure",
        ):
            actor_id = payload.get("attacker_id", actor_id)
            target_id = payload.get("target_id", target_id)
            maneuver_type = "sunder"

        elif event_type in (
            "disarm_declared", "disarm_success", "disarm_failure",
        ):
            actor_id = payload.get("attacker_id", actor_id)
            target_id = payload.get("target_id", target_id)
            maneuver_type = "disarm"

        elif event_type in ("counter_disarm_success", "counter_disarm_failure"):
            actor_id = payload.get("counter_attacker", actor_id)
            target_id = payload.get("target_id", target_id)
            maneuver_type = "disarm"

        elif event_type in (
            "grapple_declared", "grapple_success", "grapple_failure",
        ):
            actor_id = payload.get("attacker_id", actor_id)
            target_id = payload.get("target_id", target_id)
            maneuver_type = "grapple"
            if event_type == "grapple_success":
                condition_applied = payload.get("condition_applied", condition_applied)

        # === AOO EVENTS ===
        elif event_type == "aoo_triggered":
            actor_id = payload.get("reactor_id", actor_id)
            target_id = payload.get("provoker_id", target_id)

        elif event_type == "aoo_blocked_by_cover":
            actor_id = payload.get("reactor_id", actor_id)
            target_id = payload.get("provoker_id", target_id)

        elif event_type == "aoo_avoided_by_tumble":
            actor_id = payload.get("reactor_id", actor_id)
            target_id = payload.get("provoker_id", target_id)

        # === MOVEMENT EVENTS ===
        elif event_type == "movement_declared":
            actor_id = payload.get("actor_id", actor_id)

        elif event_type == "mounted_move_declared":
            actor_id = payload.get("rider_id", actor_id)

        # === TARGETING EVENTS ===
        elif event_type == "targeting_failed":
            actor_id = payload.get("actor_id", actor_id)
            target_id = payload.get("target_id", target_id)

        # Extract weapon name from any event
        if "weapon" in event:
            weapon_name = event["weapon"]
        elif "weapon_name" in payload and payload is not event:
            weapon_name = payload["weapon_name"]

        # Extract content_id from any event (WO-GAP-B-001)
        if content_id is None:
            content_id = event.get("content_id")
            if content_id is None and payload is not event:
                content_id = payload.get("content_id")

        # WO-BRIEF-WIDTH-001: Extract causal_chain_id from any event
        if causal_chain_id is None:
            causal_chain_id = event.get("causal_chain_id")
            if causal_chain_id is None and payload is not event:
                causal_chain_id = payload.get("causal_chain_id")
            if causal_chain_id is not None:
                chain_position = (
                    event.get("chain_position")
                    or (payload.get("chain_position") if payload is not event else None)
                    or 1
                )

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

    # WO-BRIEF-WIDTH-001: Assemble additional_targets from multi-target damage tracking
    additional_targets = ()
    if len(damage_by_target) > 1:
        # Primary target is the one already set as target_id
        # Additional targets are all others
        additional = []
        for tid, tdata in damage_by_target.items():
            if tid == target_id:
                continue
            t_name = resolve_entity_name(tid, frozen_view)
            t_hp_before, t_hp_max = get_entity_hp_data(tid, frozen_view)
            t_severity = compute_severity(
                damage=tdata["damage"],
                target_hp_before=t_hp_before,
                target_hp_max=t_hp_max,
                target_defeated=tdata["defeated"],
            )
            additional.append((t_name, t_severity, tdata["defeated"]))
        additional_targets = tuple(additional)

    # WO-BRIEF-WIDTH-001: Query active conditions from FrozenWorldStateView
    active_conditions = get_entity_conditions(target_id, frozen_view) if target_id else ()
    actor_conditions = get_entity_conditions(actor_id, frozen_view) if actor_id else ()

    # WO-GAP-B-001: Look up presentation semantics from registry by content_id
    if presentation_registry is not None and content_id is not None:
        registry_entry = presentation_registry.get_ability_semantics(content_id)
        if registry_entry is not None:
            presentation_semantics = registry_entry

    # Build outcome summary
    outcome_summary = _build_outcome_summary(
        action_type=narration_token,
        actor_name=actor_name,
        target_name=target_name,
        weapon_name=weapon_name,
        spell_name=spell_name,
        condition_applied=condition_applied,
        condition_removed=condition_removed,
        maneuver_type=maneuver_type,
        target_defeated=target_defeated,
        additional_targets=additional_targets,
        causal_chain_id=causal_chain_id,
        chain_position=chain_position,
    )

    # Assemble NarrativeBrief
    return NarrativeBrief(
        action_type=narration_token,
        actor_name=actor_name,
        target_name=target_name,
        outcome_summary=outcome_summary,
        severity=severity,
        weapon_name=weapon_name,
        spell_name=spell_name,
        damage_type=damage_type,
        condition_applied=condition_applied,
        condition_removed=condition_removed,
        maneuver_type=maneuver_type,
        target_defeated=target_defeated,
        additional_targets=additional_targets,
        causal_chain_id=causal_chain_id,
        chain_position=chain_position,
        active_conditions=active_conditions,
        actor_conditions=actor_conditions,
        visible_gear=tuple(visible_gear) if visible_gear else None,
        presentation_semantics=presentation_semantics,
        previous_narrations=tuple(previous_narrations) if previous_narrations else (),
        scene_description=scene_description,
        source_event_ids=tuple(event_ids),
        provenance_tag="[DERIVED]",
    )


def _build_outcome_summary(
    action_type: str,
    actor_name: str,
    target_name: Optional[str],
    weapon_name: Optional[str],
    spell_name: Optional[str],
    condition_applied: Optional[str],
    condition_removed: Optional[str],
    maneuver_type: Optional[str],
    target_defeated: bool,
    additional_targets: tuple = (),
    causal_chain_id: Optional[str] = None,
    chain_position: int = 0,
) -> str:
    """Build natural language outcome summary (WO-046B + WO-BRIEF-WIDTH-001).

    Handles all narration tokens emitted by play_loop.py.
    WO-BRIEF-WIDTH-001: Appends multi-target and causal chain context.
    """
    base = _build_base_outcome_summary(
        action_type=action_type,
        actor_name=actor_name,
        target_name=target_name,
        weapon_name=weapon_name,
        spell_name=spell_name,
        condition_applied=condition_applied,
        condition_removed=condition_removed,
        maneuver_type=maneuver_type,
        target_defeated=target_defeated,
    )
    return _append_context_suffixes(base, additional_targets, causal_chain_id, chain_position)


def _append_context_suffixes(
    base: str,
    additional_targets: tuple = (),
    causal_chain_id: Optional[str] = None,
    chain_position: int = 0,
) -> str:
    """Append multi-target and causal chain context to outcome summary.

    WO-BRIEF-WIDTH-001: If additional_targets is non-empty, appends target count.
    If causal_chain_id is set and chain_position > 1, notes triggered action.
    """
    suffixes = []
    if additional_targets:
        total = 1 + len(additional_targets)  # primary + additional
        suffixes.append(f"affecting {total} targets")
    if causal_chain_id and chain_position > 1:
        suffixes.append("triggered by a prior action")
    if suffixes:
        return f"{base}, {', '.join(suffixes)}"
    return base


def _build_base_outcome_summary(
    action_type: str,
    actor_name: str,
    target_name: Optional[str],
    weapon_name: Optional[str],
    spell_name: Optional[str],
    condition_applied: Optional[str],
    condition_removed: Optional[str],
    maneuver_type: Optional[str],
    target_defeated: bool,
) -> str:
    """Build base natural language outcome summary (WO-046B).

    Handles all narration tokens emitted by play_loop.py:
    - Attack: attack_hit, attack_miss, critical, full_attack_complete
    - Spell: spell_damage_dealt, spell_no_effect, spell_healed,
             spell_buff_applied, spell_debuff_applied, spell_resisted,
             spell_cast_success
    - Maneuver: {maneuver}_success, {maneuver}_failure
    - Movement: movement_stub, mounted_movement, mounted, dismounted
    - AoO: action_aborted_by_aoo
    - Defeat: defeat (standalone)
    - Condition: condition_applied, condition_removed

    Args:
        action_type: Narration token
        actor_name: Actor display name
        target_name: Target display name
        weapon_name: Weapon name
        spell_name: Spell name
        condition_applied: Condition name if applied
        condition_removed: Condition name if removed
        maneuver_type: Combat maneuver type
        target_defeated: Whether target defeated

    Returns:
        Outcome summary string
    """
    target = target_name or "the target"

    # === ATTACK NARRATION TOKENS ===

    if "attack_hit" in action_type:
        weapon = weapon_name or "weapon"
        if target_defeated:
            return f"{actor_name} defeats {target} with {weapon}"
        return f"{actor_name} hits {target} with {weapon}"

    if "attack_miss" in action_type:
        weapon = weapon_name or "weapon"
        return f"{actor_name} misses {target} with {weapon}"

    if "critical" in action_type:
        weapon = weapon_name or "weapon"
        return f"{actor_name} scores a critical hit on {target} with {weapon}"

    if action_type == "full_attack_complete":
        weapon = weapon_name or "weapons"
        if target_defeated:
            return f"{actor_name} strikes down {target} with a flurry of blows"
        return f"{actor_name} unleashes a flurry of attacks on {target}"

    if action_type == "concealment_miss":
        return f"{actor_name}'s attack passes through {target}'s concealment"

    # === SPELL NARRATION TOKENS ===

    if action_type == "spell_damage_dealt":
        spell = spell_name or "a spell"
        if target_defeated:
            return f"{actor_name} destroys {target} with {spell}"
        return f"{actor_name}'s {spell} strikes {target}"

    if action_type == "spell_no_effect":
        spell = spell_name or "spell"
        return f"{actor_name}'s {spell} has no effect on {target}"

    if action_type == "spell_healed":
        spell = spell_name or "a healing spell"
        return f"{actor_name} heals {target} with {spell}"

    if action_type == "spell_buff_applied":
        spell = spell_name or "a spell"
        return f"{actor_name} enhances {target} with {spell}"

    if action_type == "spell_debuff_applied":
        spell = spell_name or "a spell"
        condition = condition_applied or "an affliction"
        return f"{actor_name}'s {spell} inflicts {condition} on {target}"

    if action_type == "spell_resisted":
        spell = spell_name or "spell"
        return f"{target} resists {actor_name}'s {spell}"

    if action_type == "spell_cast_success":
        spell = spell_name or "a spell"
        if target_name:
            return f"{actor_name} casts {spell} on {target}"
        return f"{actor_name} casts {spell}"

    # Generic spell fallback (matches any action_type containing "spell")
    if "spell" in action_type and action_type not in (
        "spell_damage_dealt", "spell_no_effect", "spell_healed",
        "spell_buff_applied", "spell_debuff_applied", "spell_resisted",
        "spell_cast_success",
    ):
        spell = spell_name or "a spell"
        return f"{actor_name} casts {spell} on {target}"

    # === MANEUVER NARRATION TOKENS ===

    if action_type == "bull_rush_success":
        return f"{actor_name} bull rushes {target} backward"

    if action_type == "bull_rush_failure":
        return f"{actor_name} fails to bull rush {target}"

    if action_type == "trip_success":
        return f"{actor_name} trips {target} to the ground"

    if action_type == "trip_failure":
        return f"{actor_name} fails to trip {target}"

    if action_type == "overrun_success":
        return f"{actor_name} overruns {target}, knocking them prone"

    if action_type == "overrun_failure":
        return f"{actor_name} fails to overrun {target}"

    if action_type == "sunder_success":
        return f"{actor_name} sunders {target}'s equipment"

    if action_type == "sunder_failure":
        return f"{actor_name} fails to sunder {target}'s equipment"

    if action_type == "disarm_success":
        return f"{actor_name} disarms {target}"

    if action_type == "disarm_failure":
        return f"{actor_name} fails to disarm {target}"

    if action_type == "grapple_success":
        return f"{actor_name} grapples {target}"

    if action_type == "grapple_failure":
        return f"{actor_name} fails to grapple {target}"

    # Dynamic maneuver tokens (e.g., "overrun_avoided")
    if maneuver_type and "success" in action_type:
        return f"{actor_name}'s {maneuver_type} succeeds against {target}"
    if maneuver_type and "failure" in action_type:
        return f"{actor_name}'s {maneuver_type} fails against {target}"
    if maneuver_type and "avoided" in action_type:
        return f"{target} avoids {actor_name}'s {maneuver_type}"

    # === MOVEMENT NARRATION TOKENS ===

    if action_type == "movement_stub":
        return f"{actor_name} moves"

    if action_type == "mounted_movement":
        return f"{actor_name} rides forward"

    if action_type == "mounted":
        return f"{actor_name} mounts up"

    if action_type == "dismounted":
        return f"{actor_name} dismounts"

    # === AOO NARRATION TOKENS ===

    if action_type == "action_aborted_by_aoo":
        return f"{actor_name}'s action is interrupted by an attack of opportunity"

    # === CONDITION NARRATION TOKENS ===

    if action_type == "condition_applied" and condition_applied:
        return f"{target} is now {condition_applied}"

    if action_type == "condition_removed" and condition_removed:
        return f"{target} is no longer {condition_removed}"

    # === DEFEAT NARRATION TOKEN ===

    if "defeat" in action_type:
        return f"{actor_name} defeats {target}"

    # === GENERIC FALLBACK ===

    if target_name:
        return f"{actor_name} acts against {target_name}"
    return f"{actor_name} acts"
