"""Shared utilities for smoke test scenarios.

Extracted from smoke_test.py to support both manual scenarios and the
generative fuzzer.
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from aidm.schemas.entity_fields import EF
from aidm.core.state import WorldState, FrozenWorldStateView
from aidm.core.rng_manager import RNGManager
from aidm.core.play_loop import execute_turn, TurnContext
from aidm.core.spell_resolver import SpellCastIntent, SpellTarget, SpellEffect
from aidm.data.spell_definitions import SPELL_REGISTRY, get_spell
from aidm.schemas.position import Position
from aidm.lens.narrative_brief import assemble_narrative_brief


# ── Shared State ─────────────────────────────────────────────────────

STAGE_RESULTS: List[Dict[str, Any]] = []
FIXES_APPLIED: List[str] = []
BREAK_POINTS: List[Dict[str, str]] = []
GAP_RESULTS: List[Dict[str, Any]] = []
SCENARIO_RESULTS: Dict[str, str] = {}
NEW_FINDINGS: List[str] = []
FUZZ_RESULTS: List[Dict[str, Any]] = []


def reset_state() -> None:
    """Clear all shared state. Useful for test isolation."""
    STAGE_RESULTS.clear()
    FIXES_APPLIED.clear()
    BREAK_POINTS.clear()
    GAP_RESULTS.clear()
    SCENARIO_RESULTS.clear()
    NEW_FINDINGS.clear()
    FUZZ_RESULTS.clear()


# ── Recording Helpers ────────────────────────────────────────────────


def banner(title: str) -> None:
    width = 70
    print()
    print("=" * width)
    print(f"  {title}")
    print("=" * width)


def record_pass(stage: str, detail: str = "") -> None:
    STAGE_RESULTS.append({"stage": stage, "status": "PASS", "detail": detail})
    print(f"  [PASS] {stage}" + (f" — {detail}" if detail else ""))


def record_fail(stage: str, detail: str, module: str = "", line: str = "", error: str = "") -> None:
    STAGE_RESULTS.append({"stage": stage, "status": "FAIL", "detail": detail})
    bp = {"stage": stage, "module": module, "line": line, "error": error or detail}
    BREAK_POINTS.append(bp)
    print(f"  [FAIL] {stage} — {detail}")
    if module:
        print(f"         module: {module}")
    if line:
        print(f"         line:   {line}")


def record_fix(description: str) -> None:
    FIXES_APPLIED.append(description)
    print(f"  [FIX]  {description}")


def record_gap(gap_name: str, confirmed: bool, detail: str = "") -> None:
    GAP_RESULTS.append({"gap": gap_name, "confirmed": confirmed, "detail": detail})
    tag = "CONFIRMED" if confirmed else "NOT CONFIRMED"
    print(f"  [{tag}] {gap_name}" + (f" — {detail}" if detail else ""))


def record_finding(description: str) -> None:
    NEW_FINDINGS.append(description)
    print(f"  [FINDING] {description}")


# ── Entity Factories ──────────────────────────────────────────────────


def make_caster(
    entity_id: str = "wizard_1",
    name: str = "Elara the Evoker",
    hp: int = 32,
    position: Dict[str, int] | None = None,
    caster_level: int = 5,
    spell_dc_base: int = 13,
    spells_prepared: List[str] | None = None,
) -> Dict[str, Any]:
    """Create a standard caster entity dict."""
    pos = position or {"x": 5, "y": 5}
    return {
        EF.ENTITY_ID: entity_id,
        "name": name,
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp,
        EF.AC: 14,
        EF.ATTACK_BONUS: 3,
        EF.BAB: 2,
        EF.STR_MOD: 0,
        EF.DEX_MOD: 2,
        EF.INT_MOD: 3,
        EF.CON_MOD: 1,
        EF.WIS_MOD: 1,
        EF.CHA_MOD: 0,
        EF.SAVE_FORT: 2,
        EF.SAVE_REF: 3,
        EF.SAVE_WILL: 5,
        EF.TEAM: "party",
        EF.WEAPON: "quarterstaff",
        EF.POSITION: pos,
        EF.DEFEATED: False,
        EF.SIZE_CATEGORY: "medium",
        EF.BASE_SPEED: 30,
        EF.CONDITIONS: {},
        "caster_level": caster_level,
        "spell_dc_base": spell_dc_base,
        "spells_prepared": spells_prepared or ["fireball"],
    }


def make_target(
    entity_id: str = "goblin_1",
    name: str = "Goblin Raider",
    hp: int = 5,
    position: Dict[str, int] | None = None,
    team: str = "monsters",
    size: str = "small",
    defeated: bool = False,
) -> Dict[str, Any]:
    """Create a standard target entity dict."""
    pos = position or {"x": 10, "y": 10}
    return {
        EF.ENTITY_ID: entity_id,
        "name": name,
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp,
        EF.AC: 15,
        EF.ATTACK_BONUS: 3,
        EF.BAB: 1,
        EF.STR_MOD: 0,
        EF.DEX_MOD: 1,
        EF.INT_MOD: -1,
        EF.CON_MOD: 0,
        EF.WIS_MOD: 0,
        EF.CHA_MOD: -1,
        EF.SAVE_FORT: 1,
        EF.SAVE_REF: 3,
        EF.SAVE_WILL: 0,
        EF.TEAM: team,
        EF.WEAPON: "shortbow",
        EF.POSITION: pos,
        EF.DEFEATED: defeated,
        EF.SIZE_CATEGORY: size,
        EF.BASE_SPEED: 30,
        EF.CONDITIONS: {},
    }


# ── World State Setup ─────────────────────────────────────────────────


def make_world_state(
    entities: Dict[str, Dict[str, Any]],
    initiative_order: List[str] | None = None,
) -> WorldState:
    """Create a WorldState with the given entities in round 1 combat."""
    if initiative_order is None:
        initiative_order = list(entities.keys())
    return WorldState(
        ruleset_version="3.5e",
        entities=entities,
        active_combat={
            "round_index": 1,
            "turn_counter": 0,
            "initiative_order": initiative_order,
            "flat_footed_actors": [],
            "aoo_used_this_round": [],
            "duration_tracker": {"effects": []},
        },
    )


# ── Spell Execution Pipeline ─────────────────────────────────────────


def cast_spell(
    world_state: WorldState,
    caster_id: str,
    spell_id: str,
    target_position: Position | None = None,
    target_entity_id: str | None = None,
    rng: RNGManager | None = None,
    turn_index: int = 0,
    timestamp: float = 1.0,
) -> Dict[str, Any]:
    """Execute a spell through the full play loop pipeline.

    Returns a dict with:
        turn_result: The raw TurnResult
        events: List of event dicts
        world_state: Updated WorldState
        brief: NarrativeBrief (or None if assembly fails)
        narration_text: str (or None if generation fails)
        error: str or None
    """
    if rng is None:
        rng = RNGManager(master_seed=42)

    intent = SpellCastIntent(
        caster_id=caster_id,
        spell_id=spell_id,
        target_position=target_position,
        target_entity_id=target_entity_id,
    )

    caster_entity = world_state.entities.get(caster_id, {})
    turn_ctx = TurnContext(
        turn_index=turn_index,
        actor_id=caster_id,
        actor_team=caster_entity.get(EF.TEAM, "party"),
    )

    result = {
        "turn_result": None,
        "events": [],
        "world_state": world_state,
        "brief": None,
        "narration_text": None,
        "error": None,
    }

    try:
        turn_result = execute_turn(
            world_state=world_state,
            turn_ctx=turn_ctx,
            combat_intent=intent,
            rng=rng,
            next_event_id=0,
            timestamp=timestamp,
        )
        result["turn_result"] = turn_result
        result["world_state"] = turn_result.world_state
    except Exception as exc:
        result["error"] = f"execute_turn crashed: {exc}"
        return result

    # Capture events
    try:
        event_dicts = []
        for event in turn_result.events:
            event_dicts.append({
                "event_id": event.event_id,
                "type": event.event_type,
                "event_type": event.event_type,
                "timestamp": event.timestamp,
                "payload": event.payload,
                "citations": event.citations,
            })
        result["events"] = event_dicts
    except Exception as exc:
        result["error"] = f"event capture failed: {exc}"
        return result

    # Assemble NarrativeBrief
    try:
        frozen_view = FrozenWorldStateView(turn_result.world_state)
        narration_token = turn_result.narration or "spell_damage_dealt"
        brief = assemble_narrative_brief(
            events=event_dicts,
            narration_token=narration_token,
            frozen_view=frozen_view,
        )
        result["brief"] = brief
    except Exception as exc:
        result["error"] = f"NarrativeBrief assembly failed: {exc}"
        return result

    # Generate narration text via template fallback
    try:
        from aidm.narration.narrator import NarrationTemplates
        template = NarrationTemplates.get_template(
            turn_result.narration or "spell_damage_dealt",
            brief.severity if brief else "minor",
        )
        narration_text = template.format(
            actor=brief.actor_name if brief else "Unknown",
            target=brief.target_name if brief else "Unknown",
            weapon=brief.weapon_name or brief.spell_name or "spell",
            damage=brief.damage_type or "magical",
        )
        result["narration_text"] = narration_text
    except Exception as exc:
        # Template narration failure is non-fatal for fuzzing
        result["narration_text"] = f"[template error: {exc}]"

    return result
