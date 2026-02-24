"""Energy Drain resolution engine for D&D 3.5e.

PHB p.215-216: Creatures with the energy drain ability bestow negative levels
via a successful natural attack. Each negative level imposes:
  -1 penalty to attack rolls, saves, skill checks, ability checks
  -5 effective max HP (and current HP reduced by 5)
  Loss of 1 highest available spell slot

WO-ENGINE-ENERGY-DRAIN-001

MECHANICS IMPLEMENTED:
- Runs full attack resolution (resolve_attack) internally
- On hit: bestows negative_levels_per_hit negative levels
- Per level: hp_max and hp_current reduced by 5; highest spell slot drained
- `negative_levels_applied` event per hit (not per level — one event with N levels)
- Death if total NEGATIVE_LEVELS >= HD_COUNT → `energy_drain_death`
- Attack penalty: NEGATIVE_LEVELS subtracted from attack rolls (in attack_resolver)
- Save penalty: NEGATIVE_LEVELS subtracted from save rolls (in play_loop TargetStats)

DEFERRED:
- 24h Fort save (temporary vs permanent)
- Restoration spell recovery of negative levels
- Shadow STR drain (different mechanic)
- Incorporeal miss chance (handled by MISS_CHANCE field on entity)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from aidm.core.event_log import Event
from aidm.core.rng_protocol import RNGProvider
from aidm.core.state import WorldState
from aidm.schemas.attack import AttackIntent, EnergyDrainAttackIntent
from aidm.schemas.entity_fields import EF


# ===========================================================================
# Helpers
# ===========================================================================

def get_negative_level_attack_penalty(entity: Dict[str, Any]) -> int:
    """Return the attack penalty from negative levels (a negative int or 0).

    PHB p.215: Each negative level gives -1 to attack rolls.
    Returns: -N where N = NEGATIVE_LEVELS count (e.g., 2 levels → -2).
    """
    return -entity.get(EF.NEGATIVE_LEVELS, 0)


def get_negative_level_save_penalty(entity: Dict[str, Any]) -> int:
    """Return the save penalty from negative levels (a negative int or 0).

    PHB p.215: Each negative level gives -1 to saving throws.
    Returns: -N where N = NEGATIVE_LEVELS count.
    """
    return -entity.get(EF.NEGATIVE_LEVELS, 0)


def _check_energy_drain_death(target: Dict[str, Any]) -> bool:
    """True if total negative levels >= target's effective HD (PHB p.215)."""
    neg_levels = target.get(EF.NEGATIVE_LEVELS, 0)
    effective_hd = target.get(EF.HD_COUNT, 1)
    return neg_levels >= effective_hd


def _drain_spell_slot(target: Dict[str, Any]) -> Optional[int]:
    """Drain the highest available spell slot from target.

    Checks SPELL_SLOTS first (primary caster), then SPELL_SLOTS_2 (dual-caster).
    Returns the spell level drained, or None if target has no slots.
    Mutates target directly (caller's responsibility to track in event).
    """
    # Primary caster slots
    slots: Optional[Dict] = target.get(EF.SPELL_SLOTS)
    if slots:
        for level in sorted(slots.keys(), key=int, reverse=True):
            if slots[level] > 0:
                slots[level] -= 1
                return int(level)

    # Secondary caster slots (dual-caster)
    slots_2: Optional[Dict] = target.get(EF.SPELL_SLOTS_2)
    if slots_2:
        for level in sorted(slots_2.keys(), key=int, reverse=True):
            if slots_2[level] > 0:
                slots_2[level] -= 1
                return int(level)

    return None  # Non-caster or all slots empty


# ===========================================================================
# Resolution
# ===========================================================================

def resolve_energy_drain(
    intent: EnergyDrainAttackIntent,
    world_state: WorldState,
    rng: RNGProvider,
    next_event_id: int,
    timestamp: float,
) -> List[Event]:
    """Resolve an EnergyDrainAttackIntent.

    RNG consumption: follows resolve_attack() internal order (attack roll d20,
    optional crit confirm d20, optional miss-chance d100, damage XdY).

    Returns list of events (state NOT mutated — call apply_energy_drain_events).
    """
    from aidm.core.attack_resolver import resolve_attack, apply_attack_events

    events: List[Event] = []

    # ── Build underlying AttackIntent and resolve ────────────────────────────
    underlying = AttackIntent(
        attacker_id=intent.attacker_id,
        target_id=intent.target_id,
        attack_bonus=intent.attack_bonus,
        weapon=intent.weapon,
    )
    attack_events = resolve_attack(
        intent=underlying,
        world_state=world_state,
        rng=rng,
        next_event_id=next_event_id,
        timestamp=timestamp,
    )
    events.extend(attack_events)
    current_id = next_event_id + len(attack_events)

    # ── Check if attack hit ─────────────────────────────────────────────────
    attack_roll_event = next(
        (e for e in attack_events if e.event_type == "attack_roll"), None
    )
    hit = attack_roll_event is not None and attack_roll_event.payload.get("hit", False)

    if not hit:
        return events

    # ── Apply attack events to get updated state for drain calculations ──────
    updated_ws = apply_attack_events(world_state, attack_events)
    target = updated_ws.entities.get(intent.target_id)
    if target is None or target.get(EF.DEFEATED):
        return events

    # ── Bestow negative levels ───────────────────────────────────────────────
    n = intent.negative_levels_per_hit
    old_neg_levels = target.get(EF.NEGATIVE_LEVELS, 0)
    # Accumulate in target (for death check and spell drain)
    target[EF.NEGATIVE_LEVELS] = old_neg_levels + n

    # HP drain: 5 per negative level
    hp_max_before = target.get(EF.HP_MAX, 1)
    new_hp_max = max(1, hp_max_before - n * 5)
    target[EF.HP_MAX] = new_hp_max
    # Clamp current HP to new max
    hp_current = target.get(EF.HP_CURRENT, 0)
    if hp_current > new_hp_max:
        target[EF.HP_CURRENT] = new_hp_max

    # Drain spell slot(s) — one per negative level bestowed
    spell_slot_lost: Optional[int] = None
    for _ in range(n):
        drained = _drain_spell_slot(target)
        if drained is not None:
            spell_slot_lost = drained  # Report highest drained level

    events.append(Event(
        event_id=current_id,
        event_type="negative_levels_applied",
        timestamp=timestamp + 0.05,
        payload={
            "target_id": intent.target_id,
            "attacker_id": intent.attacker_id,
            "negative_levels_added": n,
            "total_negative_levels": target[EF.NEGATIVE_LEVELS],
            "hp_max_reduced_by": n * 5,
            "hp_max_before": hp_max_before,
            "hp_max_after": new_hp_max,
            "spell_slot_lost": spell_slot_lost,
            "source": "energy_drain",
        },
    ))
    current_id += 1

    # ── Death check ───────────────────────────────────────────────────────────
    if _check_energy_drain_death(target):
        events.append(Event(
            event_id=current_id,
            event_type="energy_drain_death",
            timestamp=timestamp + 0.06,
            payload={
                "target_id": intent.target_id,
                "negative_levels": target[EF.NEGATIVE_LEVELS],
                "effective_hd": target.get(EF.HD_COUNT, 1),
            },
        ))
        current_id += 1

    return events


# ===========================================================================
# State application
# ===========================================================================

def apply_energy_drain_events(events: List[Event], world_state: WorldState) -> WorldState:
    """Apply energy drain events to world state.

    Handles both the underlying attack events and the drain-specific events.
    Pattern: identical to apply_attack_events / apply_cdg_events.
    """
    from aidm.core.attack_resolver import apply_attack_events

    # Apply underlying attack events first (hp_changed, entity_defeated, etc.)
    attack_event_types = {"attack_roll", "damage_roll", "hp_changed",
                          "entity_defeated", "targeting_failed", "critical_hit"}
    attack_events = [e for e in events if e.event_type in attack_event_types]
    if attack_events:
        world_state = apply_attack_events(world_state, attack_events)

    # Apply drain-specific events
    for event in events:
        et = event.event_type
        p = event.payload

        if et == "negative_levels_applied":
            tid = p["target_id"]
            target = world_state.entities.get(tid)
            if target is None:
                continue
            target[EF.NEGATIVE_LEVELS] = p["total_negative_levels"]
            target[EF.HP_MAX] = p["hp_max_after"]
            # Clamp current HP if needed
            if target.get(EF.HP_CURRENT, 0) > p["hp_max_after"]:
                target[EF.HP_CURRENT] = p["hp_max_after"]
            # Spell slot was already drained in resolve_energy_drain on the
            # updated_ws copy; world_state needs the same decrement
            slot_level = p.get("spell_slot_lost")
            if slot_level is not None:
                slots = target.get(EF.SPELL_SLOTS, {})
                if isinstance(slots, dict):
                    level_key = slot_level  # may be int or str key
                    # Find and decrement the correct key
                    for k in sorted(slots.keys(), key=int, reverse=True):
                        if int(k) == slot_level and slots[k] > 0:
                            slots[k] -= 1
                            break

        elif et == "energy_drain_death":
            tid = p["target_id"]
            target = world_state.entities.get(tid)
            if target is not None:
                target[EF.DEFEATED] = True
                target[EF.HP_CURRENT] = 0

    return world_state
