"""
rest_resolver.py — D&D 3.5e rest mechanics.

Implements PHB p.130 rest rules:
- Overnight rest (8h): full spell slot recovery + natural HP healing
- Full day rest: double natural healing rate, still full slots
- Short rest (< 8h): 3.5e has no mechanical benefit for spells/HP

Called from play_loop.execute_turn() on RestIntent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from aidm.schemas.entity_fields import EF
from aidm.schemas.intents import RestIntent
from aidm.core.state import WorldState


# PHB p.130 — natural healing per full night's rest
# HP gained = character level × max(1, CON modifier)
# Full day bed rest = double rate


@dataclass
class RestResult:
    """Result of a rest resolution."""
    events: List[Dict[str, Any]] = field(default_factory=list)
    world_state: Optional[WorldState] = None
    narration: Optional[str] = None


def resolve_rest(
    intent: RestIntent,
    world_state: WorldState,
    actor_id: str,
    next_event_id: int = 0,
    timestamp: float = 0.0,
) -> RestResult:
    """
    Resolve a RestIntent for the given actor.

    Fail-closed on:
    - Active combat (rest denied)
    - Actor not found in world_state
    """
    events: List[Dict[str, Any]] = []

    # ── Combat guard ──────────────────────────────────────────────────────────
    if world_state.active_combat is not None:
        events.append({
            "event_id": next_event_id,
            "event_type": "rest_denied",
            "payload": {
                "actor_id": actor_id,
                "reason": "combat_active",
            },
            "timestamp": timestamp,
        })
        return RestResult(events=events, world_state=world_state)

    # ── Actor lookup ──────────────────────────────────────────────────────────
    actor = world_state.entities.get(actor_id)
    if actor is None:
        events.append({
            "event_id": next_event_id,
            "event_type": "rest_denied",
            "payload": {
                "actor_id": actor_id,
                "reason": "actor_not_found",
            },
            "timestamp": timestamp,
        })
        return RestResult(events=events, world_state=world_state)

    # ── Determine rest quality ────────────────────────────────────────────────
    is_full_rest = intent.rest_type in ("overnight", "full_day")
    is_double_rate = intent.rest_type == "full_day"

    # ── HP recovery (natural healing) ────────────────────────────────────────
    hp_restored = 0
    if is_full_rest:
        hp_current = actor.get(EF.HP_CURRENT, 0)
        hp_max = actor.get(EF.HP_MAX, 0)
        level = actor.get(EF.LEVEL, 1)
        # Use pre-computed CON_MOD stored at chargen (= (CON - 10) // 2)
        con_mod = actor.get(EF.CON_MOD, 0)
        heal_per_night = level * max(1, con_mod)
        if is_double_rate:
            heal_per_night *= 2
        hp_restored = min(heal_per_night, hp_max - hp_current)
        if hp_restored > 0:
            actor[EF.HP_CURRENT] = hp_current + hp_restored
            events.append({
                "event_id": next_event_id,
                "event_type": "hp_restored",
                "payload": {
                    "actor_id": actor_id,
                    "amount": hp_restored,
                    "new_hp": actor[EF.HP_CURRENT],
                    "source": "natural_rest",
                },
                "timestamp": timestamp,
            })
            next_event_id += 1

    # ── Spell slot recovery ───────────────────────────────────────────────────
    if is_full_rest:
        slots_restored = _restore_spell_slots(actor, actor_id, next_event_id, timestamp)
        events.extend(slots_restored)
        if slots_restored:
            next_event_id += len(slots_restored)

    # ── Turn undead use recovery (WO-ENGINE-TURN-UNDEAD-001) ─────────────────
    # PHB p.159: Turn undead uses refresh after a full night's rest
    if is_full_rest:
        turn_max = actor.get(EF.TURN_UNDEAD_USES_MAX)
        if turn_max is not None and actor.get(EF.TURN_UNDEAD_USES, turn_max) < turn_max:
            actor[EF.TURN_UNDEAD_USES] = turn_max

    # ── Condition cleanup (overnight rest clears fatigue, exhaustion) ─────────
    # 3.5e: 8h rest removes fatigued; exhausted → fatigued after 1h rest (PHB p.300)
    conditions = actor.get(EF.CONDITIONS, [])
    removed_conditions = []
    for cond in list(conditions):
        if cond in ("fatigued", "exhausted"):
            if is_full_rest:
                conditions.remove(cond)
                removed_conditions.append(cond)
    if removed_conditions:
        actor[EF.CONDITIONS] = conditions

    # ── Nonlethal damage recovery (WO-ENGINE-NONLETHAL-001) ───────────────────
    # PHB p.146: Overnight rest clears all nonlethal damage (approximation for per-hour rule)
    if is_full_rest and actor.get(EF.NONLETHAL_DAMAGE, 0) > 0:
        actor[EF.NONLETHAL_DAMAGE] = 0
        # Clear staggered/unconscious conditions caused by nonlethal damage
        nl_conds = actor.get(EF.CONDITIONS, [])
        if isinstance(nl_conds, dict):
            actor[EF.CONDITIONS] = {k: v for k, v in nl_conds.items() if k not in ("staggered", "unconscious")}
        else:
            actor[EF.CONDITIONS] = [c for c in nl_conds if c not in ("staggered", "unconscious")]

    # ── Ability damage recovery (WO-ENGINE-ABILITY-DAMAGE-001) ────────────────
    # PHB p.215: 1 point of each ability damage heals per overnight rest
    if is_full_rest:
        from aidm.core.ability_damage_resolver import expire_ability_damage_regen
        actor, ability_heal_events = expire_ability_damage_regen(
            actor, actor_id, next_event_id, timestamp
        )
        events.extend(ability_heal_events)
        if ability_heal_events:
            next_event_id += len(ability_heal_events)

    # ── rest_completed event ──────────────────────────────────────────────────
    events.append({
        "event_id": next_event_id,
        "event_type": "rest_completed",
        "payload": {
            "actor_id": actor_id,
            "rest_type": intent.rest_type,
            "hp_restored": hp_restored,
            "conditions_cleared": removed_conditions,
        },
        "timestamp": timestamp,
    })

    return RestResult(
        events=events,
        world_state=world_state,
        narration=_rest_narration(intent.rest_type, hp_restored),
    )


def _restore_spell_slots(
    actor: Dict[str, Any],
    actor_id: str,
    next_event_id: int,
    timestamp: float,
) -> List[Dict[str, Any]]:
    """
    Restore all spell slots to max values (from SPELL_SLOTS_MAX).
    Also resets SPELLS_PREPARED for prepared casters.
    Returns list of spell_slots_restored events.
    """
    events = []

    # Primary slots
    slots_max: Optional[Dict[int, int]] = actor.get(EF.SPELL_SLOTS_MAX)
    if slots_max is not None:
        actor[EF.SPELL_SLOTS] = dict(slots_max)  # restore to max
        events.append({
            "event_id": next_event_id,
            "event_type": "spell_slots_restored",
            "payload": {
                "actor_id": actor_id,
                "caster_class": actor.get(EF.CASTER_CLASS, "unknown"),
                "slots": dict(slots_max),
            },
            "timestamp": timestamp,
        })
        next_event_id += 1

    # Secondary slots (dual-caster)
    slots_max_2: Optional[Dict[int, int]] = actor.get(EF.SPELL_SLOTS_MAX_2)
    if slots_max_2 is not None:
        actor[EF.SPELL_SLOTS_2] = dict(slots_max_2)
        events.append({
            "event_id": next_event_id,
            "event_type": "spell_slots_restored",
            "payload": {
                "actor_id": actor_id,
                "caster_class": actor.get(EF.CASTER_CLASS_2, "unknown"),
                "slots": dict(slots_max_2),
            },
            "timestamp": timestamp,
        })
        next_event_id += 1

    # Prepared caster spell re-preparation (wizard, cleric, druid, ranger, paladin)
    PREPARED_CASTERS = {"wizard", "cleric", "druid", "ranger", "paladin"}
    caster_class = actor.get(EF.CASTER_CLASS, "")
    if caster_class in PREPARED_CASTERS:
        # On long rest, prepared casters may re-prepare — reset to full known list
        spells_known = actor.get(EF.SPELLS_KNOWN, {})
        if spells_known:
            actor[EF.SPELLS_PREPARED] = {
                level: list(spells)
                for level, spells in spells_known.items()
            }

    return events


def _rest_narration(rest_type: str, hp_restored: int) -> str:
    """Return brief narration string for rest result."""
    if rest_type == "overnight":
        base = "You take a full night's rest."
    elif rest_type == "full_day":
        base = "You rest for a full day."
    else:
        base = "You take a brief rest."

    if hp_restored > 0:
        return f"{base} You recover {hp_restored} hit points and your spells return."
    return f"{base} Your spells return."
