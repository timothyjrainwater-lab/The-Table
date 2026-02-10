"""M1.5 Runtime Text-Only Presentation Layer.

Per SONNET-C_WO-M1.5-UX-01 Section 6.2:
- Format WorldState into human-readable text
- Display campaign header, current scene, entity status
- Format EngineResult output (rolls, modifiers, outcome)
- NO graphics, NO UI state management, NO optimization

This is a presentation adapter - it does NOT:
- Modify WorldState
- Make mechanical decisions
- Bypass intent lifecycle
- Cache state outside event log
"""

from typing import Dict, Any, List, Optional
from aidm.core.state import WorldState
from aidm.schemas.engine_result import EngineResult
from aidm.schemas.campaign import CampaignManifest


def format_campaign_header(manifest: CampaignManifest, turn_count: int) -> str:
    """Format campaign header with basic metadata.

    Args:
        manifest: Campaign manifest
        turn_count: Number of turns executed so far

    Returns:
        Formatted header string
    """
    lines = [
        "=" * 80,
        "AIDM — AI Dungeon Master for D&D 3.5e",
        "=" * 80,
        "",
        f"Campaign: {manifest.title}",
        f"Session: {turn_count} turns played",
        f"Seed: {manifest.master_seed}",
        "",
    ]
    return "\n".join(lines)


def format_world_summary(world_state: WorldState) -> str:
    """Format current world state summary.

    Shows entities with HP, position, team, and conditions.

    Args:
        world_state: Current world state

    Returns:
        Formatted world summary string
    """
    lines = ["Current World State:", ""]

    if not world_state.entities:
        lines.append("  (No entities)")
        return "\n".join(lines)

    # Sort entities by ID for stable output
    for entity_id in sorted(world_state.entities.keys()):
        entity = world_state.entities[entity_id]

        # Format entity line
        hp_current = entity.get("hp_current", "?")
        hp_max = entity.get("hp_max", "?")
        team = entity.get("team", "unknown")
        position = entity.get("position", {})
        conditions = entity.get("conditions", [])
        defeated = entity.get("defeated", False)

        entity_line = f"  {entity_id}"
        entity_line += f" [{team}]"
        entity_line += f" HP: {hp_current}/{hp_max}"

        if position:
            x = position.get("x", 0)
            y = position.get("y", 0)
            entity_line += f" | Pos: ({x}, {y})"

        if conditions:
            entity_line += f" | Conditions: {', '.join(conditions)}"

        if defeated:
            entity_line += " | DEFEATED"

        lines.append(entity_line)

    lines.append("")

    # Show active combat if present
    if world_state.active_combat:
        lines.append("Active Combat:")
        turn_counter = world_state.active_combat.get("turn_counter", 0)
        lines.append(f"  Turn counter: {turn_counter}")
        lines.append("")

    return "\n".join(lines)


def format_available_actions() -> str:
    """Format minimal available actions list.

    M1.5 supports basic actions only.

    Returns:
        Formatted actions string
    """
    lines = [
        "Available Actions:",
        "  attack <target> - Attack a target entity",
        "  move <x> <y> - Move to grid position",
        "  /exit - Save and exit",
        "",
    ]
    return "\n".join(lines)


def format_engine_result(result: EngineResult) -> str:
    """Format EngineResult as human-readable text.

    Shows status, rolls, modifiers, and outcome.

    Args:
        result: Engine resolution result

    Returns:
        Formatted result string
    """
    lines = ["[RESOLVE] Processing action..."]

    # Show rolls
    if result.rolls:
        for roll in result.rolls:
            natural = roll.natural_roll
            modifier = roll.modifier
            total = roll.total
            roll_type = roll.roll_type or "d20"

            lines.append(f"[RESOLVE] Rolling {roll_type}: [{natural}]+{modifier} = {total}")

            # Show comparison if present
            if hasattr(roll, "target_number") and roll.target_number is not None:
                if total >= roll.target_number:
                    lines.append(f"[RESOLVE]   vs DC {roll.target_number} → SUCCESS")
                else:
                    lines.append(f"[RESOLVE]   vs DC {roll.target_number} → FAILURE")

    # Show status
    lines.append(f"[RESOLVE] Result: {result.status.value}")

    # Show failure reason if present
    if result.failure_reason:
        lines.append(f"[RESOLVE]   Reason: {result.failure_reason}")

    lines.append("")
    return "\n".join(lines)


def format_bootstrap_progress(stage: str, details: str = "") -> str:
    """Format bootstrap stage progress message.

    Args:
        stage: Bootstrap stage name
        details: Optional details about the stage

    Returns:
        Formatted progress message
    """
    line = f"[AIDM] {stage}"
    if details:
        line += f": {details}"
    return line


def format_error(error_type: str, message: str, recovery_hint: Optional[str] = None) -> str:
    """Format error message with optional recovery hint.

    Args:
        error_type: Type of error (e.g., "Campaign Load Error")
        message: Error message
        recovery_hint: Optional hint for recovery

    Returns:
        Formatted error string
    """
    lines = [
        "",
        f"[AIDM] ERROR: {error_type}",
        f"[AIDM] {message}",
    ]

    if recovery_hint:
        lines.append(f"[AIDM] {recovery_hint}")

    lines.append("")
    return "\n".join(lines)
