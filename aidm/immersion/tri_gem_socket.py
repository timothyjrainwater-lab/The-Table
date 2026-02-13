"""Tri-Gem Socket transparency system for filtering combat events.

WO-023: Transparency Tri-Gem Socket
Provides three visibility modes for players to understand DM decisions:
- RUBY: Minimal — final results only
- SAPPHIRE: Standard — key rolls and modifiers (default)
- DIAMOND: Full — complete mechanical breakdown with rule references

Operates on event dictionaries (event_id, event_type, payload, citations).
All functions are pure (no state mutation) and work as a read-only view layer.

IMMERSION BOUNDARY: This module reads event data but does not import from
aidm.core.event_log directly to maintain the immersion authority boundary.
Events should be converted to EventData dicts before being passed here.

Example usage:
    socket = TriGemSocket()

    # Convert Event objects to EventData dicts (done by caller)
    event_data = [event.to_dict() for event in events]

    # Filter for SAPPHIRE mode
    filtered = socket.filter_events(event_data, TransparencyMode.SAPPHIRE)

    # Format for display
    for stp in filtered:
        print(format_for_display(stp))
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, TypedDict


# Import only from allowed immersion surfaces
from aidm.schemas.transparency import (
    TransparencyMode,
    TransparencyConfig,
    FilteredSTP,
    RollBreakdown,
    DamageBreakdown,
    ModifierBreakdown,
)


# ==============================================================================
# EVENT DATA TYPE DEFINITION
# ==============================================================================

class EventData(TypedDict, total=False):
    """Event data dictionary format.

    This matches the serialized form of Event from event_log but without
    importing from that module (maintains immersion boundary).

    Required fields:
        event_id: Monotonic event identifier
        event_type: Event type string (e.g., 'attack_roll', 'damage_roll')
        timestamp: Event timestamp
        payload: Event-specific data dictionary

    Optional fields:
        citations: List of rule citation dicts
        rng_offset: RNG offset for replay
    """
    event_id: int
    event_type: str
    timestamp: float
    payload: Dict[str, Any]
    citations: List[Dict[str, Any]]
    rng_offset: int


# ==============================================================================
# ENTITY NAME RESOLUTION
# ==============================================================================

def get_entity_display_name(
    entity_id: str,
    name_map: Optional[Dict[str, str]] = None
) -> str:
    """Get human-readable display name for an entity.

    Args:
        entity_id: Entity identifier
        name_map: Optional mapping of entity_id -> display name

    Returns:
        Display name (falls back to entity_id if no mapping)
    """
    if name_map is not None and entity_id in name_map:
        return name_map[entity_id]
    # Capitalize and clean up the ID as fallback
    return entity_id.replace("_", " ").title()


# ==============================================================================
# ATTACK ROLL FILTERING
# ==============================================================================

def _filter_attack_roll_ruby(
    event: EventData,
    name_map: Optional[Dict[str, str]] = None
) -> FilteredSTP:
    """Filter attack_roll event for RUBY mode (minimal).

    Shows only: "X hits/misses Y" or "X hits Y for N damage"
    """
    payload = event.get("payload", {})
    attacker = get_entity_display_name(payload.get("attacker_id", "Unknown"), name_map)
    target = get_entity_display_name(payload.get("target_id", "Unknown"), name_map)
    hit = payload.get("hit", False)

    if hit:
        final_result = f"{attacker} hits {target}."
    else:
        final_result = f"{attacker} misses {target}."

    return FilteredSTP(
        event_id=event.get("event_id", 0),
        event_type=event.get("event_type", "unknown"),
        mode=TransparencyMode.RUBY,
        final_result=final_result,
    )


def _filter_attack_roll_sapphire(
    event: EventData,
    name_map: Optional[Dict[str, str]] = None
) -> FilteredSTP:
    """Filter attack_roll event for SAPPHIRE mode (standard).

    Shows: "Attack roll: 18 + 5 = 23 vs AC 15. Hit!"
    """
    payload = event.get("payload", {})
    attacker = get_entity_display_name(payload.get("attacker_id", "Unknown"), name_map)
    target = get_entity_display_name(payload.get("target_id", "Unknown"), name_map)

    d20_result = payload.get("d20_result", 0)
    attack_bonus = payload.get("attack_bonus", 0)
    total = payload.get("total", 0)
    target_ac = payload.get("target_ac", 10)
    hit = payload.get("hit", False)
    is_natural_20 = payload.get("is_natural_20", False)
    is_natural_1 = payload.get("is_natural_1", False)

    # Build summary text
    if attack_bonus >= 0:
        summary_text = f"{d20_result} + {attack_bonus} = {total} vs AC {target_ac}"
    else:
        summary_text = f"{d20_result} - {abs(attack_bonus)} = {total} vs AC {target_ac}"

    # Build final result with natural roll notation
    if is_natural_20:
        final_result = f"{attacker} attacks {target}: Natural 20! Hit!"
    elif is_natural_1:
        final_result = f"{attacker} attacks {target}: Natural 1! Miss!"
    elif hit:
        final_result = f"{attacker} attacks {target}: {summary_text}. Hit!"
    else:
        final_result = f"{attacker} attacks {target}: {summary_text}. Miss."

    # Roll summary tuple: (roll_type, natural, total, success)
    roll_summaries = (("attack", d20_result, total, hit),)

    return FilteredSTP(
        event_id=event.get("event_id", 0),
        event_type=event.get("event_type", "unknown"),
        mode=TransparencyMode.SAPPHIRE,
        final_result=final_result,
        summary_text=summary_text,
        actor_name=attacker,
        target_name=target,
        roll_summaries=roll_summaries,
    )


def _filter_attack_roll_diamond(
    event: EventData,
    name_map: Optional[Dict[str, str]] = None
) -> FilteredSTP:
    """Filter attack_roll event for DIAMOND mode (full).

    Shows complete breakdown with all modifiers and rule citations.
    """
    payload = event.get("payload", {})
    attacker = get_entity_display_name(payload.get("attacker_id", "Unknown"), name_map)
    target = get_entity_display_name(payload.get("target_id", "Unknown"), name_map)

    d20_result = payload.get("d20_result", 0)
    attack_bonus = payload.get("attack_bonus", 0)
    condition_modifier = payload.get("condition_modifier", 0)
    mounted_bonus = payload.get("mounted_bonus", 0)
    terrain_higher_ground = payload.get("terrain_higher_ground", 0)
    cover_ac_bonus = payload.get("cover_ac_bonus", 0)
    total = payload.get("total", 0)
    target_ac = payload.get("target_ac", 10)
    target_base_ac = payload.get("target_base_ac", 10)
    target_ac_modifier = payload.get("target_ac_modifier", 0)
    hit = payload.get("hit", False)
    is_natural_20 = payload.get("is_natural_20", False)
    is_natural_1 = payload.get("is_natural_1", False)

    # Build modifier breakdowns for attack roll
    attack_modifiers = []
    if attack_bonus != 0:
        attack_modifiers.append(ModifierBreakdown(
            source="Base Attack Bonus",
            value=attack_bonus,
            rule_citation="PHB p.134"
        ))
    if condition_modifier != 0:
        attack_modifiers.append(ModifierBreakdown(
            source="Condition Modifier",
            value=condition_modifier,
            rule_citation="PHB p.308"
        ))
    if mounted_bonus != 0:
        attack_modifiers.append(ModifierBreakdown(
            source="Mounted Higher Ground",
            value=mounted_bonus,
            rule_citation="PHB p.157"
        ))
    if terrain_higher_ground != 0:
        attack_modifiers.append(ModifierBreakdown(
            source="Terrain Higher Ground",
            value=terrain_higher_ground,
            rule_citation="PHB p.151"
        ))

    attack_roll = RollBreakdown(
        roll_type="attack",
        natural_roll=d20_result,
        die_size=20,
        modifiers=tuple(attack_modifiers),
        total=total,
        target_value=target_ac,
        target_name="AC",
        success=hit,
        is_critical=is_natural_20,
        is_fumble=is_natural_1,
    )

    # Build AC breakdown string for summary
    ac_breakdown_parts = [f"base {target_base_ac}"]
    if target_ac_modifier != 0:
        ac_breakdown_parts.append(f"condition {target_ac_modifier:+d}")
    if cover_ac_bonus != 0:
        ac_breakdown_parts.append(f"cover {cover_ac_bonus:+d}")
    ac_breakdown = ", ".join(ac_breakdown_parts)

    # Summary text with modifier breakdown
    mod_total = attack_bonus + condition_modifier + mounted_bonus + terrain_higher_ground
    if mod_total >= 0:
        summary_text = f"d20={d20_result}, modifiers {mod_total:+d} = {total} vs AC {target_ac} ({ac_breakdown})"
    else:
        summary_text = f"d20={d20_result}, modifiers {mod_total:+d} = {total} vs AC {target_ac} ({ac_breakdown})"

    # Final result
    if is_natural_20:
        final_result = f"{attacker} attacks {target}: Natural 20! Automatic Hit!"
    elif is_natural_1:
        final_result = f"{attacker} attacks {target}: Natural 1! Automatic Miss!"
    elif hit:
        final_result = f"{attacker} attacks {target}: {summary_text}. Hit!"
    else:
        final_result = f"{attacker} attacks {target}: {summary_text}. Miss."

    # Extract citations
    citations = event.get("citations", [])
    rule_citations = tuple(
        (c.get("source_id", "unknown"), c.get("page", 0))
        for c in citations
    )

    return FilteredSTP(
        event_id=event.get("event_id", 0),
        event_type=event.get("event_type", "unknown"),
        mode=TransparencyMode.DIAMOND,
        final_result=final_result,
        summary_text=summary_text,
        actor_name=attacker,
        target_name=target,
        roll_summaries=(("attack", d20_result, total, hit),),
        roll_breakdowns=(attack_roll,),
        rule_citations=rule_citations,
        raw_payload=payload,
    )


# ==============================================================================
# DAMAGE ROLL FILTERING
# ==============================================================================

def _filter_damage_roll_ruby(
    event: EventData,
    name_map: Optional[Dict[str, str]] = None
) -> FilteredSTP:
    """Filter damage_roll event for RUBY mode (minimal)."""
    payload = event.get("payload", {})
    target = get_entity_display_name(payload.get("target_id", "Unknown"), name_map)
    damage_total = payload.get("damage_total", 0)
    damage_type = payload.get("damage_type", "")

    if damage_type:
        final_result = f"{target} takes {damage_total} {damage_type} damage."
    else:
        final_result = f"{target} takes {damage_total} damage."

    return FilteredSTP(
        event_id=event.get("event_id", 0),
        event_type=event.get("event_type", "unknown"),
        mode=TransparencyMode.RUBY,
        final_result=final_result,
    )


def _filter_damage_roll_sapphire(
    event: EventData,
    name_map: Optional[Dict[str, str]] = None
) -> FilteredSTP:
    """Filter damage_roll event for SAPPHIRE mode (standard)."""
    payload = event.get("payload", {})
    attacker = get_entity_display_name(payload.get("attacker_id", "Unknown"), name_map)
    target = get_entity_display_name(payload.get("target_id", "Unknown"), name_map)

    damage_dice = payload.get("damage_dice", "1d4")
    damage_rolls = payload.get("damage_rolls", [])
    damage_bonus = payload.get("damage_bonus", 0)
    str_modifier = payload.get("str_modifier", 0)
    damage_total = payload.get("damage_total", 0)
    damage_type = payload.get("damage_type", "")

    # Build dice result string
    if len(damage_rolls) == 1:
        dice_str = str(damage_rolls[0])
    else:
        dice_str = f"({'+'.join(str(r) for r in damage_rolls)})"

    # Build bonus string
    total_bonus = damage_bonus + str_modifier
    if total_bonus > 0:
        summary_text = f"{damage_dice}: {dice_str} + {total_bonus} = {damage_total}"
    elif total_bonus < 0:
        summary_text = f"{damage_dice}: {dice_str} - {abs(total_bonus)} = {damage_total}"
    else:
        summary_text = f"{damage_dice}: {dice_str} = {damage_total}"

    if damage_type:
        final_result = f"{target} takes {damage_total} {damage_type} damage. ({summary_text})"
    else:
        final_result = f"{target} takes {damage_total} damage. ({summary_text})"

    return FilteredSTP(
        event_id=event.get("event_id", 0),
        event_type=event.get("event_type", "unknown"),
        mode=TransparencyMode.SAPPHIRE,
        final_result=final_result,
        summary_text=summary_text,
        actor_name=attacker,
        target_name=target,
    )


def _filter_damage_roll_diamond(
    event: EventData,
    name_map: Optional[Dict[str, str]] = None
) -> FilteredSTP:
    """Filter damage_roll event for DIAMOND mode (full)."""
    payload = event.get("payload", {})
    attacker = get_entity_display_name(payload.get("attacker_id", "Unknown"), name_map)
    target = get_entity_display_name(payload.get("target_id", "Unknown"), name_map)

    damage_dice = payload.get("damage_dice", "1d4")
    damage_rolls = payload.get("damage_rolls", [])
    damage_bonus = payload.get("damage_bonus", 0)
    str_modifier = payload.get("str_modifier", 0)
    condition_modifier = payload.get("condition_modifier", 0)
    damage_total = payload.get("damage_total", 0)
    damage_type = payload.get("damage_type", "")

    # Build modifier breakdowns
    damage_modifiers = []
    if damage_bonus != 0:
        damage_modifiers.append(ModifierBreakdown(
            source="Weapon Damage Bonus",
            value=damage_bonus,
            rule_citation="PHB p.113"
        ))
    if str_modifier != 0:
        damage_modifiers.append(ModifierBreakdown(
            source="STR Modifier",
            value=str_modifier,
            rule_citation="PHB p.113"
        ))
    if condition_modifier != 0:
        damage_modifiers.append(ModifierBreakdown(
            source="Condition Modifier",
            value=condition_modifier,
            rule_citation="PHB p.308"
        ))

    damage_breakdown = DamageBreakdown(
        dice_expression=damage_dice,
        dice_results=tuple(damage_rolls),
        modifiers=tuple(damage_modifiers),
        total=damage_total,
        damage_type=damage_type or "untyped",
    )

    # Build detailed summary
    dice_str = "+".join(str(r) for r in damage_rolls) if damage_rolls else "0"
    mod_parts = []
    if damage_bonus != 0:
        mod_parts.append(f"weapon {damage_bonus:+d}")
    if str_modifier != 0:
        mod_parts.append(f"STR {str_modifier:+d}")
    if condition_modifier != 0:
        mod_parts.append(f"condition {condition_modifier:+d}")

    if mod_parts:
        summary_text = f"{damage_dice}=[{dice_str}], {', '.join(mod_parts)} = {damage_total} {damage_type}"
    else:
        summary_text = f"{damage_dice}=[{dice_str}] = {damage_total} {damage_type}"

    final_result = f"{target} takes {damage_total} {damage_type or 'untyped'} damage. ({summary_text})"

    # Extract citations
    citations = event.get("citations", [])
    rule_citations = tuple(
        (c.get("source_id", "unknown"), c.get("page", 0))
        for c in citations
    )

    return FilteredSTP(
        event_id=event.get("event_id", 0),
        event_type=event.get("event_type", "unknown"),
        mode=TransparencyMode.DIAMOND,
        final_result=final_result,
        summary_text=summary_text,
        actor_name=attacker,
        target_name=target,
        damage_breakdown=damage_breakdown,
        rule_citations=rule_citations,
        raw_payload=payload,
    )


# ==============================================================================
# SAVE ROLL FILTERING
# ==============================================================================

def _filter_save_rolled_ruby(
    event: EventData,
    name_map: Optional[Dict[str, str]] = None
) -> FilteredSTP:
    """Filter save_rolled event for RUBY mode (minimal)."""
    payload = event.get("payload", {})
    target = get_entity_display_name(payload.get("target_id", "Unknown"), name_map)
    save_type = payload.get("save_type", "save").upper()
    outcome = payload.get("outcome", "unknown")

    if outcome == "success":
        final_result = f"{target} makes the {save_type} save!"
    elif outcome == "partial":
        final_result = f"{target} partially resists! (Half effect)"
    else:
        final_result = f"{target} fails the {save_type} save!"

    return FilteredSTP(
        event_id=event.get("event_id", 0),
        event_type=event.get("event_type", "unknown"),
        mode=TransparencyMode.RUBY,
        final_result=final_result,
    )


def _filter_save_rolled_sapphire(
    event: EventData,
    name_map: Optional[Dict[str, str]] = None
) -> FilteredSTP:
    """Filter save_rolled event for SAPPHIRE mode (standard)."""
    payload = event.get("payload", {})
    target = get_entity_display_name(payload.get("target_id", "Unknown"), name_map)
    save_type = payload.get("save_type", "save").upper()

    d20_result = payload.get("d20_result", 0)
    save_bonus = payload.get("save_bonus", 0)
    total = payload.get("total", 0)
    dc = payload.get("dc", 10)
    outcome = payload.get("outcome", "unknown")
    is_natural_20 = payload.get("is_natural_20", False)
    is_natural_1 = payload.get("is_natural_1", False)

    # Build summary text
    if save_bonus >= 0:
        summary_text = f"{d20_result} + {save_bonus} = {total} vs DC {dc}"
    else:
        summary_text = f"{d20_result} - {abs(save_bonus)} = {total} vs DC {dc}"

    # Build final result
    if is_natural_20:
        final_result = f"{target} {save_type} save: Natural 20! Success!"
    elif is_natural_1:
        final_result = f"{target} {save_type} save: Natural 1! Failure!"
    elif outcome == "success":
        final_result = f"{target} {save_type} save: {summary_text}. Success!"
    elif outcome == "partial":
        final_result = f"{target} {save_type} save: {summary_text}. Partial success (half effect)!"
    else:
        final_result = f"{target} {save_type} save: {summary_text}. Failure!"

    # Roll summary
    success = outcome in ("success", "partial")
    roll_summaries = ((f"{save_type}_save", d20_result, total, success),)

    return FilteredSTP(
        event_id=event.get("event_id", 0),
        event_type=event.get("event_type", "unknown"),
        mode=TransparencyMode.SAPPHIRE,
        final_result=final_result,
        summary_text=summary_text,
        target_name=target,
        roll_summaries=roll_summaries,
    )


def _filter_save_rolled_diamond(
    event: EventData,
    name_map: Optional[Dict[str, str]] = None
) -> FilteredSTP:
    """Filter save_rolled event for DIAMOND mode (full)."""
    payload = event.get("payload", {})
    target = get_entity_display_name(payload.get("target_id", "Unknown"), name_map)
    save_type = payload.get("save_type", "save").upper()

    d20_result = payload.get("d20_result", 0)
    save_bonus = payload.get("save_bonus", 0)
    total = payload.get("total", 0)
    dc = payload.get("dc", 10)
    outcome = payload.get("outcome", "unknown")
    is_natural_20 = payload.get("is_natural_20", False)
    is_natural_1 = payload.get("is_natural_1", False)

    # Build modifier breakdowns
    save_modifiers = []
    if save_bonus != 0:
        save_modifiers.append(ModifierBreakdown(
            source=f"Base {save_type} Save",
            value=save_bonus,
            rule_citation="PHB p.177"
        ))

    save_roll = RollBreakdown(
        roll_type=f"{save_type.lower()}_save",
        natural_roll=d20_result,
        die_size=20,
        modifiers=tuple(save_modifiers),
        total=total,
        target_value=dc,
        target_name="DC",
        success=(outcome in ("success", "partial")),
        is_critical=is_natural_20,
        is_fumble=is_natural_1,
    )

    # Summary text
    summary_text = f"d20={d20_result}, save bonus {save_bonus:+d} = {total} vs DC {dc}"

    # Build final result
    if is_natural_20:
        final_result = f"{target} {save_type} save: Natural 20! Automatic Success!"
    elif is_natural_1:
        final_result = f"{target} {save_type} save: Natural 1! Automatic Failure!"
    elif outcome == "success":
        final_result = f"{target} {save_type} save: {summary_text}. Success!"
    elif outcome == "partial":
        final_result = f"{target} {save_type} save: {summary_text}. Partial (half effect)!"
    else:
        final_result = f"{target} {save_type} save: {summary_text}. Failure!"

    # Extract citations
    citations = event.get("citations", [])
    rule_citations = tuple(
        (c.get("source_id", "unknown"), c.get("page", 0))
        for c in citations
    )

    return FilteredSTP(
        event_id=event.get("event_id", 0),
        event_type=event.get("event_type", "unknown"),
        mode=TransparencyMode.DIAMOND,
        final_result=final_result,
        summary_text=summary_text,
        target_name=target,
        roll_summaries=((f"{save_type}_save", d20_result, total, outcome in ("success", "partial")),),
        roll_breakdowns=(save_roll,),
        rule_citations=rule_citations,
        raw_payload=payload,
    )


# ==============================================================================
# HP CHANGE FILTERING
# ==============================================================================

def _filter_hp_changed_ruby(
    event: EventData,
    name_map: Optional[Dict[str, str]] = None
) -> FilteredSTP:
    """Filter hp_changed event for RUBY mode (minimal)."""
    payload = event.get("payload", {})
    entity = get_entity_display_name(payload.get("entity_id", "Unknown"), name_map)
    delta = payload.get("delta", 0)

    if delta < 0:
        final_result = f"{entity} is wounded!"
    elif delta > 0:
        final_result = f"{entity} is healed!"
    else:
        final_result = f"{entity}'s health is unchanged."

    return FilteredSTP(
        event_id=event.get("event_id", 0),
        event_type=event.get("event_type", "unknown"),
        mode=TransparencyMode.RUBY,
        final_result=final_result,
    )


def _filter_hp_changed_sapphire(
    event: EventData,
    name_map: Optional[Dict[str, str]] = None
) -> FilteredSTP:
    """Filter hp_changed event for SAPPHIRE mode (standard)."""
    payload = event.get("payload", {})
    entity = get_entity_display_name(payload.get("entity_id", "Unknown"), name_map)
    hp_before = payload.get("hp_before", 0)
    hp_after = payload.get("hp_after", 0)
    delta = payload.get("delta", 0)

    summary_text = f"HP: {hp_before} → {hp_after}"

    if delta < 0:
        final_result = f"{entity} takes {abs(delta)} damage. ({summary_text})"
    elif delta > 0:
        final_result = f"{entity} heals {delta} HP. ({summary_text})"
    else:
        final_result = f"{entity}'s HP unchanged. ({summary_text})"

    return FilteredSTP(
        event_id=event.get("event_id", 0),
        event_type=event.get("event_type", "unknown"),
        mode=TransparencyMode.SAPPHIRE,
        final_result=final_result,
        summary_text=summary_text,
        target_name=entity,
    )


def _filter_hp_changed_diamond(
    event: EventData,
    name_map: Optional[Dict[str, str]] = None
) -> FilteredSTP:
    """Filter hp_changed event for DIAMOND mode (full)."""
    payload = event.get("payload", {})
    entity = get_entity_display_name(payload.get("entity_id", "Unknown"), name_map)
    hp_before = payload.get("hp_before", 0)
    hp_after = payload.get("hp_after", 0)
    delta = payload.get("delta", 0)
    source = payload.get("source", "unknown")

    summary_text = f"HP: {hp_before} → {hp_after} (source: {source})"

    if delta < 0:
        final_result = f"{entity} takes {abs(delta)} damage from {source}. ({summary_text})"
    elif delta > 0:
        final_result = f"{entity} heals {delta} HP from {source}. ({summary_text})"
    else:
        final_result = f"{entity}'s HP unchanged. ({summary_text})"

    return FilteredSTP(
        event_id=event.get("event_id", 0),
        event_type=event.get("event_type", "unknown"),
        mode=TransparencyMode.DIAMOND,
        final_result=final_result,
        summary_text=summary_text,
        target_name=entity,
        raw_payload=payload,
    )


# ==============================================================================
# ENTITY DEFEATED FILTERING
# ==============================================================================

def _filter_entity_defeated_ruby(
    event: EventData,
    name_map: Optional[Dict[str, str]] = None
) -> FilteredSTP:
    """Filter entity_defeated event for RUBY mode (minimal)."""
    payload = event.get("payload", {})
    entity = get_entity_display_name(payload.get("entity_id", "Unknown"), name_map)

    final_result = f"{entity} is defeated!"

    return FilteredSTP(
        event_id=event.get("event_id", 0),
        event_type=event.get("event_type", "unknown"),
        mode=TransparencyMode.RUBY,
        final_result=final_result,
    )


def _filter_entity_defeated_sapphire(
    event: EventData,
    name_map: Optional[Dict[str, str]] = None
) -> FilteredSTP:
    """Filter entity_defeated event for SAPPHIRE mode (standard)."""
    payload = event.get("payload", {})
    entity = get_entity_display_name(payload.get("entity_id", "Unknown"), name_map)
    defeated_by = get_entity_display_name(payload.get("defeated_by", "Unknown"), name_map)
    hp_final = payload.get("hp_final", 0)

    summary_text = f"Final HP: {hp_final}"
    final_result = f"{entity} is defeated by {defeated_by}! ({summary_text})"

    return FilteredSTP(
        event_id=event.get("event_id", 0),
        event_type=event.get("event_type", "unknown"),
        mode=TransparencyMode.SAPPHIRE,
        final_result=final_result,
        summary_text=summary_text,
        target_name=entity,
        actor_name=defeated_by,
    )


def _filter_entity_defeated_diamond(
    event: EventData,
    name_map: Optional[Dict[str, str]] = None
) -> FilteredSTP:
    """Filter entity_defeated event for DIAMOND mode (full)."""
    payload = event.get("payload", {})
    entity = get_entity_display_name(payload.get("entity_id", "Unknown"), name_map)
    defeated_by = get_entity_display_name(payload.get("defeated_by", "Unknown"), name_map)
    hp_final = payload.get("hp_final", 0)

    summary_text = f"Final HP: {hp_final}, defeated by: {defeated_by}"
    final_result = f"{entity} is defeated by {defeated_by}! ({summary_text})"

    # Extract citations
    citations = event.get("citations", [])
    rule_citations = tuple(
        (c.get("source_id", "unknown"), c.get("page", 0))
        for c in citations
    )

    return FilteredSTP(
        event_id=event.get("event_id", 0),
        event_type=event.get("event_type", "unknown"),
        mode=TransparencyMode.DIAMOND,
        final_result=final_result,
        summary_text=summary_text,
        target_name=entity,
        actor_name=defeated_by,
        rule_citations=rule_citations,
        raw_payload=payload,
    )


# ==============================================================================
# AOO TRIGGERED FILTERING
# ==============================================================================

def _filter_aoo_triggered_ruby(
    event: EventData,
    name_map: Optional[Dict[str, str]] = None
) -> FilteredSTP:
    """Filter aoo_triggered event for RUBY mode (minimal)."""
    payload = event.get("payload", {})
    reactor = get_entity_display_name(payload.get("reactor_id", "Unknown"), name_map)
    provoker = get_entity_display_name(payload.get("provoker_id", "Unknown"), name_map)

    final_result = f"{reactor} strikes at {provoker}!"

    return FilteredSTP(
        event_id=event.get("event_id", 0),
        event_type=event.get("event_type", "unknown"),
        mode=TransparencyMode.RUBY,
        final_result=final_result,
    )


def _filter_aoo_triggered_sapphire(
    event: EventData,
    name_map: Optional[Dict[str, str]] = None
) -> FilteredSTP:
    """Filter aoo_triggered event for SAPPHIRE mode (standard)."""
    payload = event.get("payload", {})
    reactor = get_entity_display_name(payload.get("reactor_id", "Unknown"), name_map)
    provoker = get_entity_display_name(payload.get("provoker_id", "Unknown"), name_map)
    provoking_action = payload.get("provoking_action", "movement")

    summary_text = f"Triggered by: {provoking_action}"
    final_result = f"{reactor} takes an Attack of Opportunity against {provoker}! ({summary_text})"

    return FilteredSTP(
        event_id=event.get("event_id", 0),
        event_type=event.get("event_type", "unknown"),
        mode=TransparencyMode.SAPPHIRE,
        final_result=final_result,
        summary_text=summary_text,
        actor_name=reactor,
        target_name=provoker,
    )


def _filter_aoo_triggered_diamond(
    event: EventData,
    name_map: Optional[Dict[str, str]] = None
) -> FilteredSTP:
    """Filter aoo_triggered event for DIAMOND mode (full)."""
    payload = event.get("payload", {})
    reactor = get_entity_display_name(payload.get("reactor_id", "Unknown"), name_map)
    provoker = get_entity_display_name(payload.get("provoker_id", "Unknown"), name_map)
    provoking_action = payload.get("provoking_action", "movement")

    summary_text = f"Trigger: {provoking_action}, reactor: {reactor}, provoker: {provoker}"
    final_result = f"{reactor} takes an Attack of Opportunity against {provoker}! ({summary_text})"

    # Extract citations
    citations = event.get("citations", [])
    rule_citations = tuple(
        (c.get("source_id", "unknown"), c.get("page", 0))
        for c in citations
    )

    return FilteredSTP(
        event_id=event.get("event_id", 0),
        event_type=event.get("event_type", "unknown"),
        mode=TransparencyMode.DIAMOND,
        final_result=final_result,
        summary_text=summary_text,
        actor_name=reactor,
        target_name=provoker,
        rule_citations=rule_citations,
        raw_payload=payload,
    )


# ==============================================================================
# GENERIC/FALLBACK FILTERING
# ==============================================================================

def _filter_generic_event(
    event: EventData,
    mode: TransparencyMode,
    name_map: Optional[Dict[str, str]] = None
) -> FilteredSTP:
    """Filter unknown event types with generic formatting."""
    payload = event.get("payload", {})

    # Try to extract common fields
    actor_id = payload.get("actor_id") or payload.get("attacker_id") or payload.get("entity_id", "")
    target_id = payload.get("target_id", "")

    actor_name = get_entity_display_name(actor_id, name_map) if actor_id else ""
    target_name = get_entity_display_name(target_id, name_map) if target_id else ""

    # Build generic final result
    event_type = event.get("event_type", "unknown")
    event_desc = event_type.replace("_", " ").title()
    if actor_name and target_name:
        final_result = f"{event_desc}: {actor_name} → {target_name}"
    elif actor_name:
        final_result = f"{event_desc}: {actor_name}"
    elif target_name:
        final_result = f"{event_desc}: {target_name}"
    else:
        final_result = f"{event_desc}"

    # For DIAMOND mode, include raw payload
    raw_payload = payload if mode == TransparencyMode.DIAMOND else None

    # Extract citations for DIAMOND
    rule_citations = ()
    if mode == TransparencyMode.DIAMOND:
        citations = event.get("citations", [])
        rule_citations = tuple(
            (c.get("source_id", "unknown"), c.get("page", 0))
            for c in citations
        )

    return FilteredSTP(
        event_id=event.get("event_id", 0),
        event_type=event_type,
        mode=mode,
        final_result=final_result,
        actor_name=actor_name,
        target_name=target_name,
        rule_citations=rule_citations,
        raw_payload=raw_payload,
    )


# ==============================================================================
# MAIN FILTER FUNCTION
# ==============================================================================

# Filter dispatch table: event_type -> {mode -> filter_function}
_FILTER_DISPATCH = {
    "attack_roll": {
        TransparencyMode.RUBY: _filter_attack_roll_ruby,
        TransparencyMode.SAPPHIRE: _filter_attack_roll_sapphire,
        TransparencyMode.DIAMOND: _filter_attack_roll_diamond,
    },
    "damage_roll": {
        TransparencyMode.RUBY: _filter_damage_roll_ruby,
        TransparencyMode.SAPPHIRE: _filter_damage_roll_sapphire,
        TransparencyMode.DIAMOND: _filter_damage_roll_diamond,
    },
    "save_rolled": {
        TransparencyMode.RUBY: _filter_save_rolled_ruby,
        TransparencyMode.SAPPHIRE: _filter_save_rolled_sapphire,
        TransparencyMode.DIAMOND: _filter_save_rolled_diamond,
    },
    "hp_changed": {
        TransparencyMode.RUBY: _filter_hp_changed_ruby,
        TransparencyMode.SAPPHIRE: _filter_hp_changed_sapphire,
        TransparencyMode.DIAMOND: _filter_hp_changed_diamond,
    },
    "entity_defeated": {
        TransparencyMode.RUBY: _filter_entity_defeated_ruby,
        TransparencyMode.SAPPHIRE: _filter_entity_defeated_sapphire,
        TransparencyMode.DIAMOND: _filter_entity_defeated_diamond,
    },
    "aoo_triggered": {
        TransparencyMode.RUBY: _filter_aoo_triggered_ruby,
        TransparencyMode.SAPPHIRE: _filter_aoo_triggered_sapphire,
        TransparencyMode.DIAMOND: _filter_aoo_triggered_diamond,
    },
}


def filter_stp(
    event: EventData,
    mode: TransparencyMode,
    name_map: Optional[Dict[str, str]] = None
) -> FilteredSTP:
    """Filter a single event dict into a FilteredSTP based on transparency mode.

    Pure function: no state mutation.

    Args:
        event: Event data dictionary (event_id, event_type, payload, citations)
        mode: Transparency mode (RUBY/SAPPHIRE/DIAMOND)
        name_map: Optional mapping of entity_id -> display name

    Returns:
        FilteredSTP containing mode-appropriate information
    """
    # Look up the filter function for this event type and mode
    event_type = event.get("event_type", "unknown")
    event_filters = _FILTER_DISPATCH.get(event_type)

    if event_filters is not None and mode in event_filters:
        return event_filters[mode](event, name_map)
    else:
        # Use generic fallback for unknown event types
        return _filter_generic_event(event, mode, name_map)


def filter_events(
    events: List[EventData],
    mode: TransparencyMode,
    name_map: Optional[Dict[str, str]] = None
) -> List[FilteredSTP]:
    """Filter a list of event dicts into FilteredSTPs.

    Pure function: no state mutation.

    Args:
        events: List of event data dictionaries
        mode: Transparency mode for all events
        name_map: Optional mapping of entity_id -> display name

    Returns:
        List of FilteredSTP objects in same order as input
    """
    return [filter_stp(event, mode, name_map) for event in events]


# ==============================================================================
# DISPLAY FORMATTING
# ==============================================================================

def format_for_display(filtered: FilteredSTP) -> str:
    """Format a FilteredSTP for human-readable text display.

    Pure function: no state mutation.

    Args:
        filtered: FilteredSTP to format

    Returns:
        Human-readable string representation
    """
    mode = filtered.mode

    if mode == TransparencyMode.RUBY:
        # RUBY: Just the final result
        return filtered.final_result

    elif mode == TransparencyMode.SAPPHIRE:
        # SAPPHIRE: Final result (already includes summary)
        return filtered.final_result

    else:  # DIAMOND
        # DIAMOND: Full breakdown with citations
        lines = [filtered.final_result]

        # Add roll breakdowns if present
        if filtered.roll_breakdowns:
            lines.append("  Roll Details:")
            for rb in filtered.roll_breakdowns:
                mod_str = ""
                if rb.modifiers:
                    mod_parts = [f"{m.source}: {m.value:+d}" for m in rb.modifiers]
                    mod_str = f" ({', '.join(mod_parts)})"
                lines.append(f"    {rb.roll_type}: d{rb.die_size}={rb.natural_roll}{mod_str} = {rb.total}")

        # Add damage breakdown if present
        if filtered.damage_breakdown is not None:
            db = filtered.damage_breakdown
            lines.append("  Damage Details:")
            dice_str = "+".join(str(r) for r in db.dice_results)
            lines.append(f"    {db.dice_expression}: [{dice_str}]")
            if db.modifiers:
                mod_parts = [f"{m.source}: {m.value:+d}" for m in db.modifiers]
                lines.append(f"    Modifiers: {', '.join(mod_parts)}")
            lines.append(f"    Total: {db.total} {db.damage_type}")

        # Add rule citations if present
        if filtered.rule_citations:
            citations = [f"PHB p.{page}" for source_id, page in filtered.rule_citations if page > 0]
            if citations:
                lines.append(f"  Rules: {', '.join(citations)}")

        return "\n".join(lines)


def format_events_for_display(
    filtered_events: List[FilteredSTP],
    separator: str = "\n"
) -> str:
    """Format multiple FilteredSTPs for display.

    Args:
        filtered_events: List of FilteredSTP objects
        separator: String to join individual formatted events

    Returns:
        Combined human-readable string
    """
    return separator.join(format_for_display(f) for f in filtered_events)


# ==============================================================================
# TRI-GEM SOCKET CLASS
# ==============================================================================

class TriGemSocket:
    """Tri-Gem Socket for filtering combat events by transparency mode.

    Provides a stateless interface for filtering event data streams based on
    transparency preferences. Supports per-player configuration via
    TransparencyConfig objects.

    IMMERSION BOUNDARY: This class works with event data dictionaries, not
    Event objects directly. Callers should convert events using event.to_dict().

    Usage:
        socket = TriGemSocket()

        # Convert Event objects to dicts (done by caller)
        event_data = [event.to_dict() for event in events]

        # Filter with default mode (SAPPHIRE)
        filtered = socket.filter_events(event_data)

        # Filter with specific mode
        filtered = socket.filter_events(event_data, TransparencyMode.DIAMOND)

        # Filter with player config
        config = TransparencyConfig(player_id="alice", mode=TransparencyMode.RUBY)
        filtered = socket.filter_events(event_data, config=config)

        # Format for display
        for stp in filtered:
            print(socket.format(stp))
    """

    def __init__(
        self,
        default_mode: TransparencyMode = TransparencyMode.SAPPHIRE,
        name_map: Optional[Dict[str, str]] = None
    ):
        """Initialize Tri-Gem Socket.

        Args:
            default_mode: Default transparency mode (SAPPHIRE if not specified)
            name_map: Optional mapping of entity_id -> display name
        """
        self._default_mode = default_mode
        self._name_map = name_map or {}

    @property
    def default_mode(self) -> TransparencyMode:
        """Get the default transparency mode."""
        return self._default_mode

    def set_name_map(self, name_map: Dict[str, str]) -> None:
        """Update the entity name mapping.

        Args:
            name_map: New mapping of entity_id -> display name
        """
        self._name_map = name_map.copy()

    def add_name(self, entity_id: str, display_name: str) -> None:
        """Add a single entity name mapping.

        Args:
            entity_id: Entity identifier
            display_name: Human-readable display name
        """
        self._name_map[entity_id] = display_name

    def filter_event(
        self,
        event: EventData,
        mode: Optional[TransparencyMode] = None,
        config: Optional[TransparencyConfig] = None
    ) -> FilteredSTP:
        """Filter a single event.

        Args:
            event: Event data dictionary to filter
            mode: Transparency mode (overrides config if both provided)
            config: Player configuration (uses config.mode if mode not provided)

        Returns:
            FilteredSTP for the event
        """
        # Determine mode: explicit mode > config mode > default mode
        effective_mode = mode
        if effective_mode is None and config is not None:
            effective_mode = config.mode
        if effective_mode is None:
            effective_mode = self._default_mode

        return filter_stp(event, effective_mode, self._name_map)

    def filter_events(
        self,
        events: List[EventData],
        mode: Optional[TransparencyMode] = None,
        config: Optional[TransparencyConfig] = None
    ) -> List[FilteredSTP]:
        """Filter multiple events.

        Args:
            events: List of event data dicts to filter
            mode: Transparency mode (overrides config if both provided)
            config: Player configuration (uses config.mode if mode not provided)

        Returns:
            List of FilteredSTP objects
        """
        return [self.filter_event(e, mode, config) for e in events]

    def format(self, filtered: FilteredSTP) -> str:
        """Format a FilteredSTP for display.

        Args:
            filtered: FilteredSTP to format

        Returns:
            Human-readable string
        """
        return format_for_display(filtered)

    def format_all(
        self,
        filtered_events: List[FilteredSTP],
        separator: str = "\n"
    ) -> str:
        """Format multiple FilteredSTPs for display.

        Args:
            filtered_events: List of FilteredSTP objects
            separator: String to join formatted events

        Returns:
            Combined human-readable string
        """
        return format_events_for_display(filtered_events, separator)
