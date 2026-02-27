"""Turn Undead resolution engine for D&D 3.5e.

PHB p.159–161: Clerics (and paladins) can turn undead as a standard action.
Uses CHA modifier and effective cleric level to determine turning check and
HP budget.

WO-ENGINE-TURN-UNDEAD-001

MECHANICS IMPLEMENTED:
- Turning check: 1d20 + CHA_mod only (PHB p.159) — cleric_level is NOT part of the check
- HP budget: (2d6) × 10 → total HP of undead that can be affected
- Targets sorted by HD ascending (lowest first); budget consumed by HP_MAX
- Undead HD > cleric_level + 4 → immune (no effect)
- Undead HD ≤ cleric_level − 4 → destroyed (good) / commanded (evil, deferred)
- Undead HD ≤ turning check → turned (good) / rebuked (evil)
- Paladin: effective cleric level = paladin_level // 2 (PHB p.33)
- Evil cleric: channels_negative_energy flag → rebukes instead of turning
- TURN_UNDEAD_USES decremented per use; restored to MAX on overnight rest

DEFERRED:
- Command undead (evil cleric persistent control)
- Line of sight / 60ft range enforcement
- Domain bonuses (+2 effective level for Sun domain)
- 10-round expiry of TURNED condition
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple

from aidm.core.event_log import Event
from aidm.core.rng_protocol import RNGProvider
from aidm.core.state import WorldState
from aidm.schemas.conditions import ConditionType, create_turned_condition
from aidm.schemas.entity_fields import EF
from aidm.schemas.intents import TurnUndeadIntent


# ===========================================================================
# Helpers
# ===========================================================================

def _get_cleric_level(entity: Dict[str, Any]) -> int:
    """Return effective turning level for a cleric or paladin.

    PHB p.33: Paladin turns as cleric of level = paladin_level − 2,
    which resolves to paladin_level // 2 when level ≥ 1.
    """
    class_levels: Dict[str, int] = entity.get(EF.CLASS_LEVELS, {})
    cleric_level = class_levels.get("cleric", 0)
    paladin_effective = class_levels.get("paladin", 0) // 2
    return max(cleric_level, paladin_effective)


def _is_evil_cleric(entity: Dict[str, Any]) -> bool:
    """True if entity channels negative energy (rebuke) rather than positive (turn)."""
    class_features = entity.get("class_features", {})
    return bool(class_features.get("channels_negative_energy", False))


def _roll_turning_check(cha_mod: int, rng: RNGProvider) -> Tuple[int, int]:
    """Roll 1d20 + CHA_mod (PHB p.159). Turn check only — no cleric_level."""
    d20 = rng.stream("combat").randint(1, 20)
    return d20 + cha_mod, d20


def _roll_hp_budget(rng: RNGProvider) -> Tuple[int, int, int]:
    """Roll (2d6) × 10 HP budget (PHB p.160)."""
    combat_rng = rng.stream("combat")
    d1 = combat_rng.randint(1, 6)
    d2 = combat_rng.randint(1, 6)
    return (d1 + d2) * 10, d1, d2


def _classify_target(
    undead_hd: int,
    cleric_level: int,
    turning_check: int,
    is_evil: bool,
) -> str:
    """Classify a single undead target outcome (PHB p.160).

    Returns one of: 'immune', 'destroyed', 'commanded', 'turned', 'rebuked', 'unaffected'
    """
    if undead_hd > cleric_level + 4:
        return "immune"
    if not is_evil:
        if undead_hd <= cleric_level - 4:
            return "destroyed"
        if undead_hd <= turning_check:
            return "turned"
        return "unaffected"
    else:
        if undead_hd <= cleric_level - 4:
            return "commanded"  # Deferred; emitted as rebuked for now
        if undead_hd <= turning_check:
            return "rebuked"
        return "unaffected"


# ===========================================================================
# Resolution
# ===========================================================================

def resolve_turn_undead(
    intent: TurnUndeadIntent,
    world_state: WorldState,
    rng: RNGProvider,
    next_event_id: int,
    timestamp: float,
) -> List[Event]:
    """Resolve a TurnUndeadIntent.

    RNG consumption order (deterministic):
    1. Turning check: 1d20 (combat stream)
    2. HP budget: 2d6 (combat stream)

    Returns list of events (state NOT mutated — call apply_turn_undead_events).
    """
    events: List[Event] = []
    current_id = next_event_id

    cleric = world_state.entities.get(intent.cleric_id)
    if cleric is None:
        events.append(Event(
            event_id=current_id,
            event_type="intent_validation_failed",
            timestamp=timestamp,
            payload={
                "cleric_id": intent.cleric_id,
                "reason": "cleric_not_found",
            },
        ))
        return events

    # ── Effective level check ────────────────────────────────────────────────
    cleric_level = _get_cleric_level(cleric)

    # Improved Turning feat: +1 to effective turning level (PHB p.96)
    if "improved_turning" in cleric.get(EF.FEATS, []):
        cleric_level += 1
        events.append(Event(
            event_id=current_id,
            event_type="improved_turning_active",
            timestamp=timestamp,
            payload={
                "cleric_id": intent.cleric_id,
                "effective_level": cleric_level,
            },
        ))
        current_id += 1

    if cleric_level <= 0:
        events.append(Event(
            event_id=current_id,
            event_type="intent_validation_failed",
            timestamp=timestamp,
            payload={
                "cleric_id": intent.cleric_id,
                "reason": "not_a_turning_class",
            },
        ))
        return events

    # ── Uses check ───────────────────────────────────────────────────────────
    turn_uses = cleric.get(EF.TURN_UNDEAD_USES, 0)
    if turn_uses <= 0:
        events.append(Event(
            event_id=current_id,
            event_type="turn_undead_uses_exhausted",
            timestamp=timestamp,
            payload={
                "cleric_id": intent.cleric_id,
                "uses_remaining": 0,
            },
        ))
        return events

    # ── Turning check ────────────────────────────────────────────────────────
    cha_mod = cleric.get(EF.CHA_MOD, 0)
    is_evil = _is_evil_cleric(cleric)
    turning_check, tc_d20 = _roll_turning_check(cha_mod, rng)

    # ── HP budget ────────────────────────────────────────────────────────────
    hp_budget, hb_d1, hb_d2 = _roll_hp_budget(rng)

    events.append(Event(
        event_id=current_id,
        event_type="turning_check_rolled",
        timestamp=timestamp,
        payload={
            "cleric_id": intent.cleric_id,
            "roll_result": turning_check,
            "cleric_level": cleric_level,
            "cha_mod": cha_mod,
            "is_evil": is_evil,
            "hp_budget": hp_budget,
            "turning_dice": [tc_d20],
            "budget_dice": [hb_d1, hb_d2],
        },
    ))
    current_id += 1

    # ── Collect valid undead targets ─────────────────────────────────────────
    valid_targets: List[Tuple[int, str, Dict]] = []
    for tid in intent.target_ids:
        target = world_state.entities.get(tid)
        if target is None:
            continue
        if not target.get(EF.IS_UNDEAD, False):
            continue  # Silently skip non-undead per dispatch §4.4
        if target.get(EF.DEFEATED):
            continue
        hd = target.get(EF.HD_COUNT, 1)
        valid_targets.append((hd, tid, target))

    # Sort lowest HD first (PHB p.160)
    valid_targets.sort(key=lambda x: x[0])

    remaining_budget = hp_budget
    for hd, tid, target in valid_targets:
        outcome = _classify_target(hd, cleric_level, turning_check, is_evil)

        if outcome == "immune":
            events.append(Event(
                event_id=current_id,
                event_type="undead_immune_to_turning",
                timestamp=timestamp + 0.01,
                payload={
                    "cleric_id": intent.cleric_id,
                    "target_id": tid,
                    "target_hd": hd,
                    "cleric_level": cleric_level,
                },
            ))
            current_id += 1
            continue  # Immune targets don't consume budget

        if outcome == "unaffected":
            continue

        # Budget check: consume target's HP_MAX
        target_hp_max = target.get(EF.HP_MAX, hd * 5)
        if target_hp_max > remaining_budget:
            continue  # PHB p.160: skip if budget exhausted for this target
        remaining_budget -= target_hp_max

        if outcome == "destroyed":
            events.append(Event(
                event_id=current_id,
                event_type="undead_destroyed",
                timestamp=timestamp + 0.01,
                payload={
                    "cleric_id": intent.cleric_id,
                    "target_id": tid,
                    "target_hd": hd,
                    "source": "turn_undead",
                },
            ))
        elif outcome == "turned":
            events.append(Event(
                event_id=current_id,
                event_type="undead_turned",
                timestamp=timestamp + 0.01,
                payload={
                    "cleric_id": intent.cleric_id,
                    "target_id": tid,
                    "target_hd": hd,
                    "duration_rounds": 10,
                    "source": "turn_undead",
                },
            ))
        elif outcome in ("rebuked", "commanded"):
            # commanded is deferred; emit as rebuked for now
            events.append(Event(
                event_id=current_id,
                event_type="undead_rebuked",
                timestamp=timestamp + 0.01,
                payload={
                    "cleric_id": intent.cleric_id,
                    "target_id": tid,
                    "target_hd": hd,
                    "duration_rounds": 10,
                    "source": "turn_undead",
                },
            ))
        current_id += 1

    # ── Spend one use ────────────────────────────────────────────────────────
    events.append(Event(
        event_id=current_id,
        event_type="turn_undead_use_spent",
        timestamp=timestamp + 0.02,
        payload={
            "cleric_id": intent.cleric_id,
            "uses_remaining": turn_uses - 1,
        },
    ))
    current_id += 1

    return events


# ===========================================================================
# State application
# ===========================================================================

def apply_turn_undead_events(events: List[Event], world_state: WorldState) -> WorldState:
    """Apply turn undead events to world state.

    Returns updated WorldState (mutates entities in-place, consistent with
    apply_attack_events / apply_cdg_events patterns in this codebase).
    """
    for event in events:
        et = event.event_type
        p = event.payload

        if et == "turn_undead_use_spent":
            cleric_id = p["cleric_id"]
            cleric = world_state.entities.get(cleric_id)
            if cleric is not None:
                cleric[EF.TURN_UNDEAD_USES] = p["uses_remaining"]

        elif et == "undead_turned":
            tid = p["target_id"]
            target = world_state.entities.get(tid)
            if target is not None:
                conditions = target.get(EF.CONDITIONS, {})
                if isinstance(conditions, list):
                    conditions = {}
                turned_cond = create_turned_condition(
                    source=f"turn_undead:{p['cleric_id']}",
                    applied_at_event_id=event.event_id,
                )
                conditions[ConditionType.TURNED.value] = turned_cond.to_dict()
                target[EF.CONDITIONS] = conditions

        elif et == "undead_rebuked":
            # Rebuked undead also flee (same behavioral effect as turned)
            tid = p["target_id"]
            target = world_state.entities.get(tid)
            if target is not None:
                conditions = target.get(EF.CONDITIONS, {})
                if isinstance(conditions, list):
                    conditions = {}
                turned_cond = create_turned_condition(
                    source=f"turn_undead_rebuke:{p['cleric_id']}",
                    applied_at_event_id=event.event_id,
                )
                conditions[ConditionType.TURNED.value] = turned_cond.to_dict()
                target[EF.CONDITIONS] = conditions

        elif et == "undead_destroyed":
            tid = p["target_id"]
            target = world_state.entities.get(tid)
            if target is not None:
                target[EF.DEFEATED] = True
                target[EF.HP_CURRENT] = -10

    return world_state
