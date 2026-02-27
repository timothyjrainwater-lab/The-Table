"""Attacks of Opportunity (AoO) kernel for CP-15.

Implements RAW D&D 3.5e AoO mechanics (PHB p. 137-138):
- Threatened squares (5-ft reach only)
- Provoking actions (movement out of threatened square, ranged attacks, spellcasting)
- AoO eligibility (one AoO per reactor per round)
- Deterministic resolution ordering (initiative order → lexicographic actor_id)

SCOPE (CP-15):
- 5-ft reach only (no reach weapons)
- One AoO per actor per round (no Combat Reflexes feat)
- Single-step movement only (StepMoveIntent)
- No 5-foot step immunity, withdraw action, readied actions (deferred to CP-16+)

CP-18A EXTENSION:
- Mounted movement AoO support (mount provokes, not rider)
- MountedMoveIntent triggers AoOs against mount

CP-18 EXTENSION:
- Combat maneuver AoO support
- BullRushIntent: provokes from ALL threatening enemies (including target)
- TripIntent, DisarmIntent, GrappleIntent: provokes from TARGET only
- OverrunIntent: provokes from target when entering their space
- SunderIntent: provokes from target only

CP-19 EXTENSION:
- Cover can block AoO execution (PHB p.151)
- Standard/improved cover blocks AoO
- Soft cover does NOT block AoO
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from aidm.core.event_log import Event
from aidm.core.state import WorldState
from aidm.schemas.attack import AttackIntent, StepMoveIntent
from aidm.schemas.position import Position  # CP-001: Canonical position type
from aidm.core.attack_resolver import resolve_attack, apply_attack_events
from aidm.core.rng_protocol import RNGProvider
from aidm.schemas.entity_fields import EF


@dataclass
class AooTrigger:
    """Single AoO opportunity identified during trigger check."""

    reactor_id: str
    """Entity making the AoO"""

    provoker_id: str
    """Entity provoking the AoO"""

    provoking_action: str
    """Type of provoking action: movement_out, ranged_attack, spellcasting"""

    reactor_position: Position
    """Position of reactor (for threatened square calculation)"""

    provoker_from_pos: Position
    """Starting position of provoker (threatened square)"""

    provoker_to_pos: Optional[Position] = None
    """Destination position (for movement provocation)"""


@dataclass
class AooSequenceResult:
    """Result of resolving AoO sequence."""

    provoker_defeated: bool
    """Whether provoker was defeated by AoOs (action should abort)"""

    events: List[Event]
    """All events emitted during AoO sequence"""

    aoo_reactors: List[str]
    """Actor IDs that used their AoO this round"""


def get_threatened_squares(
    reactor_id: str,
    world_state: WorldState
) -> List[Position]:
    """
    Get all squares threatened by an actor (5-ft reach only).

    Args:
        reactor_id: Entity ID
        world_state: Current world state

    Returns:
        List of threatened Position objects (all adjacent squares)
    """
    entity = world_state.entities.get(reactor_id)
    if entity is None:
        return []

    # Get reactor position
    pos_dict = entity.get(EF.POSITION)
    if pos_dict is None:
        return []

    reactor_pos = Position(x=pos_dict["x"], y=pos_dict["y"])

    # All adjacent squares (8 directions for 5-ft reach)
    threatened = []
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue  # Skip own square
            threatened.append(Position(x=reactor_pos.x + dx, y=reactor_pos.y + dy))

    return threatened


def _is_standard_spell_intent(intent) -> bool:
    """Return True if intent is a non-quickened standard-action spell cast.

    CP-23: Supports both SpellCastIntent (from spell_resolver) and
    CastSpellIntent (from schemas/intents). Quickened spells (free action)
    do not provoke AoO.

    WO-ENGINE-METAMAGIC-001: Canonical quicken check — 'quicken' in metamagic list
    takes precedence over legacy quickened bool field.
    """
    try:
        from aidm.core.spell_resolver import SpellCastIntent
        if isinstance(intent, SpellCastIntent):
            # Canonical: 'quicken' in metamagic list (WO-ENGINE-METAMAGIC-001)
            if "quicken" in getattr(intent, "metamagic", ()):
                return False
            # Legacy: quickened bool field (backward compat)
            if getattr(intent, "quickened", False):
                return False
            return True
    except ImportError:
        pass
    try:
        from aidm.schemas.intents import CastSpellIntent
        if isinstance(intent, CastSpellIntent):
            # Canonical: 'quicken' in metamagic list
            if "quicken" in getattr(intent, "metamagic", []):
                return False
            if getattr(intent, "quickened", False):
                return False
            return True
    except ImportError:
        pass
    return False


def _get_spell_caster_id(intent) -> str:
    """Return the caster entity ID from a spell intent."""
    # SpellCastIntent uses caster_id; CastSpellIntent may use actor_id
    return getattr(intent, 'caster_id', None) or getattr(intent, 'actor_id', '')


def _extract_maneuver_params(action_name, intent, world_state):
    """Extract common parameters for target-only maneuver AoO provocation.

    All target-only maneuvers (trip, disarm, grapple, overrun, sunder) share
    the same extraction pattern: attacker provokes, target gets the AoO,
    and we need the attacker's position for threat calculation.

    Returns:
        Tuple of (provoking_action, provoker_id, target_only, target_id, from_pos)
    """
    from aidm.schemas.entity_fields import EF
    provoker_id = intent.attacker_id
    target_id = intent.target_id
    from_pos = None
    provoker = world_state.entities.get(provoker_id)
    if provoker:
        pos_dict = provoker.get(EF.POSITION)
        if pos_dict:
            from_pos = Position(x=pos_dict["x"], y=pos_dict["y"])
    return action_name, provoker_id, True, target_id, from_pos


def check_aoo_triggers(
    world_state: WorldState,
    actor_id: str,
    intent: Any  # Union[StepMoveIntent, AttackIntent, ...] but allow Any for extensibility
) -> List[AooTrigger]:
    """
    Check if an intent triggers any AoOs.

    Evaluates provoking actions (movement out, ranged attack, spellcasting, maneuvers) and
    identifies eligible reactors who threaten the provoker.

    CP-18A: For MountedMoveIntent, the MOUNT is the provoker (not rider).
    PHB p.157/137: Movement AoOs are triggered by the entity moving through
    threatened squares. When mounted, the mount is moving, rider is carried.

    CP-18: Combat maneuvers have specific AoO rules:
    - BullRushIntent: Provokes from ALL threatening enemies (PHB p.154)
    - TripIntent: Provokes from TARGET only (unarmed, PHB p.158)
    - OverrunIntent: Provokes from TARGET only (entering space, PHB p.157)
    - SunderIntent: Provokes from TARGET only (PHB p.158)
    - DisarmIntent: Provokes from TARGET only (PHB p.155)
    - GrappleIntent: Provokes from TARGET only (PHB p.155)

    Args:
        world_state: Current world state
        actor_id: Provoking actor ID (for StepMoveIntent) or rider ID (for MountedMoveIntent)
        intent: Combat intent being declared

    Returns:
        List of AooTrigger objects in deterministic order (initiative → lexicographic)
    """
    # CP-18A: Import here to avoid circular dependency
    from aidm.schemas.mounted_combat import MountedMoveIntent
    # CP-18: Import maneuver intents
    from aidm.schemas.maneuvers import (
        BullRushIntent, TripIntent, OverrunIntent,
        SunderIntent, DisarmIntent, GrappleIntent,
    )

    triggers = []

    # Determine provoking action type and actual provoker
    provoking_action = None
    from_pos = None
    to_pos = None
    provoker_id = actor_id  # Default: actor is provoker
    target_only = False  # If True, only target can get AoO
    target_id = None  # For target-only maneuvers
    provokes_from_all = False  # If True, all threatening enemies get AoO

    if isinstance(intent, StepMoveIntent):
        # Movement provocation: leaving a threatened square
        provoking_action = "movement_out"
        from_pos = intent.from_pos
        to_pos = intent.to_pos
        provoker_id = intent.actor_id

    # CP-18A: Mounted movement - mount provokes, not rider
    elif isinstance(intent, MountedMoveIntent):
        provoking_action = "mounted_movement_out"
        from_pos = intent.from_pos
        to_pos = intent.to_pos
        provoker_id = intent.mount_id  # MOUNT is the provoker

    # CP-18: Combat maneuvers
    elif isinstance(intent, BullRushIntent):
        # Bull Rush provokes from ALL threatening enemies
        provoking_action = "bull_rush"
        provoker_id = intent.attacker_id
        provokes_from_all = True
        # Get provoker position for threat calculation
        provoker = world_state.entities.get(provoker_id)
        if provoker:
            pos_dict = provoker.get(EF.POSITION)
            if pos_dict:
                from_pos = Position(x=pos_dict["x"], y=pos_dict["y"])

    elif isinstance(intent, TripIntent):
        # Trip provokes from TARGET only (unarmed attack)
        provoking_action, provoker_id, target_only, target_id, from_pos = (
            _extract_maneuver_params("trip", intent, world_state)
        )

    elif isinstance(intent, OverrunIntent):
        # Overrun provokes from TARGET only (entering their space)
        provoking_action, provoker_id, target_only, target_id, from_pos = (
            _extract_maneuver_params("overrun", intent, world_state)
        )

    elif isinstance(intent, SunderIntent):
        # Sunder provokes from TARGET only
        provoking_action, provoker_id, target_only, target_id, from_pos = (
            _extract_maneuver_params("sunder", intent, world_state)
        )

    elif isinstance(intent, DisarmIntent):
        # Disarm provokes from TARGET only
        provoking_action, provoker_id, target_only, target_id, from_pos = (
            _extract_maneuver_params("disarm", intent, world_state)
        )

    elif isinstance(intent, GrappleIntent):
        # Grapple provokes from TARGET only
        provoking_action, provoker_id, target_only, target_id, from_pos = (
            _extract_maneuver_params("grapple", intent, world_state)
        )

    # CP-23: Ranged attack in threatened square → AoO from all threatening enemies
    # PHB p.137: Using a ranged weapon while threatened provokes AoO.
    # is_ranged checks weapon_type == "ranged"; also accept range_increment > 0.
    elif isinstance(intent, AttackIntent) and (intent.weapon.is_ranged or intent.weapon.range_increment > 0):
        provoking_action = "ranged_attack"
        provoker_id = intent.attacker_id
        provokes_from_all = True
        provoker_entity = world_state.entities.get(provoker_id)
        if provoker_entity:
            pos_dict = provoker_entity.get(EF.POSITION)
            if pos_dict:
                from_pos = Position(x=pos_dict["x"], y=pos_dict["y"])

    # CP-23: Spell cast (standard action, non-quickened) in threatened square → AoO
    # PHB p.137: Casting a spell with a 1-standard-action casting time while threatened provokes.
    elif _is_standard_spell_intent(intent):
        provoking_action = "spellcasting"
        provoker_id = _get_spell_caster_id(intent)
        provokes_from_all = True
        provoker_entity = world_state.entities.get(provoker_id)
        if provoker_entity:
            pos_dict = provoker_entity.get(EF.POSITION)
            if pos_dict:
                from_pos = Position(x=pos_dict["x"], y=pos_dict["y"])

    # No AoO if not a provoking action
    if provoking_action is None:
        return []

    # WO-ENGINE-WITHDRAW-DELAY-001: Withdraw suppresses first-square AoO (PHB p.144)
    if provoking_action in ("movement_out", "mounted_movement_out"):
        from aidm.core.withdraw_delay_resolver import is_withdrawn
        if is_withdrawn(world_state, provoker_id):
            return []

    # Get provoker entity
    provoker = world_state.entities.get(provoker_id)
    if provoker is None:
        return []

    provoker_team = provoker.get(EF.TEAM, "unknown")

    # Get initiative order and AoO usage tracking
    active_combat = world_state.active_combat
    if active_combat is None:
        return []  # Not in combat

    initiative_order = active_combat.get("initiative_order", [])
    aoo_used_this_round = set(active_combat.get("aoo_used_this_round", []))
    # WO-ENGINE-COMBAT-REFLEXES-001: per-entity AoO count tracker for Combat Reflexes
    aoo_count_this_round = active_combat.get("aoo_count_this_round", {})

    # Find all eligible reactors
    potential_reactors = []

    # For target-only maneuvers, only check the target
    if target_only and target_id is not None:
        # WO-ENGINE-COMBAT-REFLEXES-001: check Combat Reflexes limit for target-only path
        _to_target = world_state.entities.get(target_id)
        if _to_target is not None:
            _to_feats = _to_target.get(EF.FEATS, [])
            _to_dex = _to_target.get(EF.DEX_MOD, 0)
            _to_limit = 1 + max(0, _to_dex) if "combat_reflexes" in _to_feats else 1
            _to_used = aoo_count_this_round.get(target_id, 0)
            if _to_used >= _to_limit:
                return []  # Target exhausted AoO limit
        else:
            if target_id in aoo_used_this_round:
                return []  # Target already used AoO (fallback)

        target = world_state.entities.get(target_id)
        if target is None:
            return []

        if target.get(EF.DEFEATED, False):
            return []

        target_team = target.get(EF.TEAM, "unknown")
        if target_team == provoker_team or target_team == "unknown":
            return []

        target_pos_dict = target.get(EF.POSITION)
        if target_pos_dict is None:
            return []

        target_pos = Position(x=target_pos_dict["x"], y=target_pos_dict["y"])

        # Check if target is adjacent (threatens provoker)
        if from_pos is not None and target_pos.is_adjacent_to(from_pos):
            potential_reactors.append((target_id, target_pos))

    else:
        # Standard case: check all threatening enemies
        for entity_id in initiative_order:
            # Skip if reactor is provoker
            if entity_id == provoker_id:
                continue

            # WO-ENGINE-COMBAT-REFLEXES-001: check Combat Reflexes limit (PHB p.92)
            # Must get reactor entity first to check feats
            reactor = world_state.entities.get(entity_id)
            if reactor is None:
                continue

            # Skip if defeated
            if reactor.get(EF.DEFEATED, False):
                continue

            _reactor_feats = reactor.get(EF.FEATS, [])
            _reactor_dex = reactor.get(EF.DEX_MOD, 0)
            _aoo_limit = 1 + max(0, _reactor_dex) if "combat_reflexes" in _reactor_feats else 1
            _aoo_used = aoo_count_this_round.get(entity_id, 0)
            if _aoo_used >= _aoo_limit:
                continue  # Reactor has exhausted AoO limit for this round

            # WO-ENGINE-CONDITIONS-BLIND-DEAF-001: Confused entity cannot make AoOs
            # except against its current target (which we can't track here — suppress all)
            from aidm.core.condition_combat_resolver import is_confused
            if is_confused(reactor):
                continue

            # WO-ENGINE-FLATFOOTED-AOO-001: Flat-footed entity cannot make AoOs (PHB p.136)
            _reactor_conditions = reactor.get(EF.CONDITIONS, {})
            if "flat_footed" in _reactor_conditions:
                continue  # Flat-footed: no AoO regardless of Combat Reflexes

            # Skip if same team
            reactor_team = reactor.get(EF.TEAM, "unknown")
            if reactor_team == provoker_team or reactor_team == "unknown":
                continue

            # Get reactor position
            reactor_pos_dict = reactor.get(EF.POSITION)
            if reactor_pos_dict is None:
                continue

            reactor_pos = Position(x=reactor_pos_dict["x"], y=reactor_pos_dict["y"])

            # Check if provoker's from_pos is threatened by reactor
            if provoking_action in ("movement_out", "mounted_movement_out"):
                # Provokes if moving OUT of a threatened square
                if from_pos is not None and reactor_pos.is_adjacent_to(from_pos):
                    potential_reactors.append((entity_id, reactor_pos))

            elif provokes_from_all:
                # Bull Rush: provokes from ALL threatening enemies
                if from_pos is not None and reactor_pos.is_adjacent_to(from_pos):
                    potential_reactors.append((entity_id, reactor_pos))

    # Sort reactors by initiative order, then lexicographic
    def sort_key(reactor_tuple):
        reactor_id, _ = reactor_tuple
        # Initiative order index (lower = earlier in init order)
        init_index = initiative_order.index(reactor_id) if reactor_id in initiative_order else 9999
        return (init_index, reactor_id)

    sorted_reactors = sorted(potential_reactors, key=sort_key)

    # Build AooTrigger objects
    for reactor_id, reactor_pos in sorted_reactors:
        triggers.append(AooTrigger(
            reactor_id=reactor_id,
            provoker_id=provoker_id,  # Mount for mounted movement
            provoking_action=provoking_action,
            reactor_position=reactor_pos,
            provoker_from_pos=from_pos,
            provoker_to_pos=to_pos
        ))

    return triggers


def resolve_aoo_sequence(
    triggers: List[AooTrigger],
    world_state: WorldState,
    rng: RNGProvider,
    next_event_id: int,
    timestamp: float,
    causal_chain_id: Optional[str] = None,
) -> AooSequenceResult:
    """
    Resolve a sequence of AoOs in deterministic order.

    Args:
        triggers: List of AooTrigger objects (already sorted)
        world_state: Current world state
        rng: RNG manager
        next_event_id: Starting event ID
        timestamp: Starting timestamp
        causal_chain_id: WO-BRIEF-WIDTH-001: Optional chain ID for causal linking

    Returns:
        AooSequenceResult with defeat status, events, and reactor IDs
    """
    events = []
    current_event_id = next_event_id
    current_timestamp = timestamp
    aoo_reactors = []

    provoker_defeated = False

    for trigger in triggers:
        # CP-19: Check if cover blocks this AoO
        from aidm.core.terrain_resolver import check_cover
        cover_result = check_cover(
            world_state,
            trigger.reactor_id,  # Reactor is attacking
            trigger.provoker_id,  # Provoker is the target
            is_melee=True
        )

        if cover_result.blocks_aoo:
            # Cover blocks this AoO - emit blocked event and skip
            events.append(Event(
                event_id=current_event_id,
                event_type="aoo_blocked_by_cover",
                timestamp=current_timestamp,
                payload={
                    "reactor_id": trigger.reactor_id,
                    "provoker_id": trigger.provoker_id,
                    "cover_type": cover_result.cover_type,
                },
                citations=[{"source_id": "681f92bc94ff", "page": 151}]  # PHB cover blocks AoO
            ))
            current_event_id += 1
            current_timestamp += 0.01
            continue  # Skip this AoO

        # WO-035: Check for Tumble skill to avoid movement AoO
        provoker = world_state.entities.get(trigger.provoker_id)
        if provoker and trigger.provoking_action in ("movement_out", "mounted_movement_out"):
            from aidm.core.skill_resolver import resolve_skill_check
            from aidm.schemas.skills import SkillID

            # Check if provoker has Tumble ranks
            skill_ranks = provoker.get(EF.SKILL_RANKS, {})
            if skill_ranks.get(SkillID.TUMBLE, 0) > 0:
                # Attempt Tumble check (DC 15) to avoid AoO
                try:
                    tumble_result = resolve_skill_check(
                        entity=provoker,
                        skill_id=SkillID.TUMBLE,
                        dc=15,
                        rng=rng,
                        circumstance_modifier=0
                    )

                    # Emit tumble check event
                    events.append(Event(
                        event_id=current_event_id,
                        event_type="tumble_check",
                        timestamp=current_timestamp,
                        payload={
                            "entity_id": trigger.provoker_id,
                            "success": tumble_result.success,
                            "total": tumble_result.total,
                            "dc": tumble_result.dc,
                            "d20_roll": tumble_result.d20_roll,
                        },
                        citations=[{"source_id": "681f92bc94ff", "page": 84}]  # PHB Tumble
                    ))
                    current_event_id += 1
                    current_timestamp += 0.01

                    if tumble_result.success:
                        # Tumble success - AoO avoided
                        events.append(Event(
                            event_id=current_event_id,
                            event_type="aoo_avoided_by_tumble",
                            timestamp=current_timestamp,
                            payload={
                                "reactor_id": trigger.reactor_id,
                                "provoker_id": trigger.provoker_id,
                            },
                            citations=[{"source_id": "681f92bc94ff", "page": 84}]  # PHB Tumble
                        ))
                        current_event_id += 1
                        current_timestamp += 0.01
                        continue  # Skip this AoO

                except ValueError:
                    # Tumble is trained-only, but we checked ranks > 0, so this shouldn't happen
                    pass

        # Emit aoo_triggered event
        aoo_payload = {
            "reactor_id": trigger.reactor_id,
            "provoker_id": trigger.provoker_id,
            "provoking_action": trigger.provoking_action
        }
        # WO-BRIEF-WIDTH-001: Propagate causal chain
        if causal_chain_id is not None:
            aoo_payload["causal_chain_id"] = causal_chain_id
            aoo_payload["chain_position"] = 2  # AoO is always a continuation
        events.append(Event(
            event_id=current_event_id,
            event_type="aoo_triggered",
            timestamp=current_timestamp,
            payload=aoo_payload,
            citations=[{"source_id": "681f92bc94ff", "page": 137}]  # PHB AoO
        ))
        current_event_id += 1
        current_timestamp += 0.01

        # Get reactor's attack parameters from entity data
        reactor = world_state.entities.get(trigger.reactor_id)
        if reactor is None:
            continue  # Reactor disappeared (edge case)

        # WO-034: Check for Mobility feat (+4 AC vs movement AoO)
        from aidm.core.feat_resolver import get_ac_modifier
        provoker = world_state.entities.get(trigger.provoker_id)
        if provoker is None:
            continue  # Provoker disappeared (edge case)

        # Build context for feat AC modifier
        feat_context = {
            "is_aoo": True,
            "aoo_trigger": trigger.provoking_action,
        }
        feat_ac_modifier = get_ac_modifier(provoker, reactor, feat_context)

        # WO-ENGINE-MOBILITY-001: Modify provoker's AC in world_state copy for this AoO only
        if feat_ac_modifier != 0:
            # Create a modified world state with updated AC for this AoO only
            from copy import deepcopy
            temp_entities = deepcopy(world_state.entities)
            temp_entities[trigger.provoker_id][EF.AC] = temp_entities[trigger.provoker_id].get(EF.AC, 10) + feat_ac_modifier
            world_state = WorldState(
                ruleset_version=world_state.ruleset_version,
                entities=temp_entities,
                active_combat=world_state.active_combat
            )

        # Extract attack bonus and weapon from entity
        # TODO CP-15: This is a temporary hack - proper attack params should come from doctrine/equipment
        attack_bonus = reactor.get(EF.ATTACK_BONUS, 0)
        weapon_data = reactor.get(EF.WEAPON)

        if weapon_data is None or not isinstance(weapon_data, dict):
            # No weapon data or non-dict (e.g. string name), skip AoO
            continue

        from aidm.schemas.attack import Weapon
        weapon = Weapon(
            damage_dice=weapon_data.get("damage_dice", "1d4"),
            damage_bonus=weapon_data.get("damage_bonus", 0),
            damage_type=weapon_data.get("damage_type", "bludgeoning"),
            critical_multiplier=weapon_data.get("critical_multiplier", 2),
            critical_range=weapon_data.get("critical_range", 20),
            is_two_handed=weapon_data.get("is_two_handed", False),
            grip=weapon_data.get("grip", "one-handed"),
            weapon_type=weapon_data.get("weapon_type", "one-handed"),
            range_increment=weapon_data.get("range_increment", 0),
        )

        # Create AoO attack intent
        aoo_attack = AttackIntent(
            attacker_id=trigger.reactor_id,
            target_id=trigger.provoker_id,
            attack_bonus=attack_bonus,
            weapon=weapon
        )

        # Resolve AoO attack via existing attack pipeline
        attack_events = resolve_attack(
            intent=aoo_attack,
            world_state=world_state,
            rng=rng,
            next_event_id=current_event_id,
            timestamp=current_timestamp
        )
        events.extend(attack_events)
        current_event_id += len(attack_events)
        current_timestamp += 0.1

        # Apply attack events to world state
        world_state = apply_attack_events(world_state, attack_events)

        # Mark reactor as having used AoO
        aoo_reactors.append(trigger.reactor_id)

        # Check if provoker was defeated
        provoker = world_state.entities.get(trigger.provoker_id)
        if provoker and provoker.get(EF.DEFEATED, False):
            provoker_defeated = True
            break  # Stop processing further AoOs

    return AooSequenceResult(
        provoker_defeated=provoker_defeated,
        events=events,
        aoo_reactors=aoo_reactors
    )


def aoo_dealt_damage(events: List[Event]) -> bool:
    """Check if any AoO in the event list dealt damage.

    Used by Disarm and Grapple to determine auto-failure.
    PHB p.155: "If you are hit by the target's attack of opportunity,
    you automatically fail to grapple/disarm."

    Args:
        events: List of events from AoO resolution

    Returns:
        True if any damage was dealt, False otherwise
    """
    for event in events:
        if event.event_type == "hp_changed":
            # Damage dealt if HP decreased
            delta = event.payload.get("delta", 0)
            if delta < 0:
                return True
    return False


def check_stand_from_prone_aoo(
    world_state: WorldState,
    actor_id: str,
) -> List[AooTrigger]:
    """Check if standing from prone triggers AoOs (PHB p.137).

    Standing from prone is a move action that provokes attacks of opportunity
    from ALL enemies threatening the actor's square. The actor must currently
    have the PRONE condition for this to trigger.

    AoO fires BEFORE the prone condition is cleared — entity is still prone
    when AoOs resolve (KERNEL-06 Termination Doctrine).

    WO-ENGINE-AOO-STAND-FROM-PRONE-001.

    Args:
        world_state: Current world state
        actor_id: Entity standing from prone

    Returns:
        List of AooTrigger objects (sorted by initiative → lexicographic)
    """
    actor = world_state.entities.get(actor_id)
    if actor is None:
        return []

    # Only triggers if actor is currently prone
    actor_conditions = actor.get(EF.CONDITIONS, {})
    if "prone" not in actor_conditions:
        return []

    actor_pos_dict = actor.get(EF.POSITION)
    if actor_pos_dict is None:
        return []
    actor_pos = Position(x=actor_pos_dict["x"], y=actor_pos_dict["y"])
    actor_team = actor.get(EF.TEAM, "unknown")

    active_combat = world_state.active_combat
    if active_combat is None:
        return []

    initiative_order = active_combat.get("initiative_order", [])
    aoo_count_this_round = active_combat.get("aoo_count_this_round", {})

    potential_reactors = []

    for entity_id in initiative_order:
        if entity_id == actor_id:
            continue

        reactor = world_state.entities.get(entity_id)
        if reactor is None:
            continue

        if reactor.get(EF.DEFEATED, False):
            continue

        # AoO limit check (Combat Reflexes aware)
        _reactor_feats = reactor.get(EF.FEATS, [])
        _reactor_dex = reactor.get(EF.DEX_MOD, 0)
        _aoo_limit = 1 + max(0, _reactor_dex) if "combat_reflexes" in _reactor_feats else 1
        _aoo_used = aoo_count_this_round.get(entity_id, 0)
        if _aoo_used >= _aoo_limit:
            continue

        # WO-ENGINE-CONDITIONS-BLIND-DEAF-001: Confused entity cannot make AoOs
        from aidm.core.condition_combat_resolver import is_confused
        if is_confused(reactor):
            continue

        # WO-ENGINE-FLATFOOTED-AOO-001: Flat-footed entity cannot make AoOs (PHB p.136)
        _reactor_conditions = reactor.get(EF.CONDITIONS, {})
        if "flat_footed" in _reactor_conditions:
            continue

        # Skip same-team reactors
        reactor_team = reactor.get(EF.TEAM, "unknown")
        if reactor_team == actor_team or reactor_team == "unknown":
            continue

        # Check if reactor is adjacent (threatens actor's square)
        reactor_pos_dict = reactor.get(EF.POSITION)
        if reactor_pos_dict is None:
            continue
        reactor_pos = Position(x=reactor_pos_dict["x"], y=reactor_pos_dict["y"])

        if reactor_pos.is_adjacent_to(actor_pos):
            potential_reactors.append((entity_id, reactor_pos))

    # Sort by initiative order, then lexicographic
    def sort_key(reactor_tuple):
        reactor_id, _ = reactor_tuple
        init_index = initiative_order.index(reactor_id) if reactor_id in initiative_order else 9999
        return (init_index, reactor_id)

    sorted_reactors = sorted(potential_reactors, key=sort_key)

    triggers = []
    for reactor_id, reactor_pos in sorted_reactors:
        triggers.append(AooTrigger(
            reactor_id=reactor_id,
            provoker_id=actor_id,
            provoking_action="stand_from_prone",
            reactor_position=reactor_pos,
            provoker_from_pos=actor_pos,
            provoker_to_pos=actor_pos,  # Standing in place — same square
        ))

    return triggers
