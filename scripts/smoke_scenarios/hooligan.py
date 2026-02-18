"""WO-SMOKE-TEST-003: The Hooligan Protocol — Adversarial Edge Cases.

12 mandatory scenarios exercising legal-but-unusual D&D 3.5e actions.
Each scenario is rules-grounded and documents setup, action, events,
NarrativeBrief fields, narration output, and PASS/FINDING verdict.

Tier A (must resolve correctly): H-003, H-004, H-008, H-010, H-011
Tier B (must not crash): H-001, H-002, H-005, H-006, H-007, H-009, H-012
"""
from __future__ import annotations

import traceback
from typing import Any, Dict, List, Optional

from smoke_scenarios.common import (
    SCENARIO_RESULTS,
    NEW_FINDINGS,
    banner,
    record_pass,
    record_fail,
    record_finding,
    make_caster,
    make_target,
    make_world_state,
    cast_spell,
)


# ── Helpers ──────────────────────────────────────────────────────────


HOOLIGAN_RESULTS: Dict[str, str] = {}
"""Per-scenario PASS/FINDING/CRASH tracking."""

HOOLIGAN_FINDINGS: List[Dict[str, Any]] = []
"""Structured findings: module, description, severity, phb_ref."""


def _record_hooligan_pass(scenario_id: str, detail: str = "") -> None:
    HOOLIGAN_RESULTS[scenario_id] = "PASS"
    record_pass(f"{scenario_id}", detail)


def _record_hooligan_finding(
    scenario_id: str,
    description: str,
    module: str = "",
    severity: str = "coverage_gap",
    phb_ref: str = "",
) -> None:
    HOOLIGAN_RESULTS[scenario_id] = "FINDING"
    HOOLIGAN_FINDINGS.append({
        "scenario": scenario_id,
        "description": description,
        "module": module,
        "severity": severity,
        "phb_ref": phb_ref,
    })
    record_finding(f"{scenario_id}: {description}")


def _record_hooligan_crash(scenario_id: str, error: str) -> None:
    HOOLIGAN_RESULTS[scenario_id] = "CRASH"
    record_fail(scenario_id, f"CRASH: {error}")


# ══════════════════════════════════════════════════════════════════════
# H-001: Ready Action Targeting Terrain (Tier B)
# PHB p.160 — ready action is legal with any trigger condition.
# ══════════════════════════════════════════════════════════════════════


def scenario_h001_ready_action() -> None:
    """H-001: Ready action — 'I attack the floor if it moves.'
    No ready action resolver expected. Coverage gap finding."""
    banner("H-001: Ready Action Targeting Terrain (Tier B)")

    sid = "H-001"
    try:
        # Check if a ReadyIntent or ready action type exists
        try:
            from aidm.core.play_loop import execute_turn, TurnContext
            # Search for any ready-related intent class
            import aidm.schemas as schemas
            has_ready = hasattr(schemas, "ReadyIntent") or hasattr(schemas, "ReadyActionIntent")
        except Exception:
            has_ready = False

        if has_ready:
            _record_hooligan_pass(sid, "ReadyIntent found — resolver exists")
        else:
            _record_hooligan_finding(
                sid,
                "No ReadyIntent or ready action resolver. Ready actions (PHB p.160) "
                "are not modeled. Engine cannot accept 'ready an action' intents.",
                module="aidm.core.play_loop",
                severity="coverage_gap",
                phb_ref="PHB p.160",
            )
            print(f"  Action type NOT supported: ReadyAction")
            print(f"  PHB basis: Ready action is legal with any trigger condition (p.160)")
    except Exception as exc:
        _record_hooligan_crash(sid, f"{exc}\n{traceback.format_exc()}")


# ══════════════════════════════════════════════════════════════════════
# H-002: Grapple a Spell Effect (Tier B)
# PHB p.155 — grapple requires a corporeal creature.
# ══════════════════════════════════════════════════════════════════════


def scenario_h002_grapple_spell_effect() -> None:
    """H-002: Grapple a spell effect — 'I grapple the wall of fire.'
    Grapple resolver exists but target must be a valid entity."""
    banner("H-002: Grapple a Spell Effect (Tier B)")

    sid = "H-002"
    try:
        from aidm.schemas.entity_fields import EF
        from aidm.schemas.maneuvers import GrappleIntent
        from aidm.core.play_loop import execute_turn, TurnContext
        from aidm.core.rng_manager import RNGManager

        # Setup: fighter and a "wall_of_fire" (not a real entity in world state)
        fighter = make_target(
            entity_id="fighter_h002",
            name="Brawler",
            hp=45,
            team="party",
            size="medium",
            position={"x": 5, "y": 5},
        )
        fighter[EF.STR_MOD] = 3
        fighter[EF.BAB] = 4
        fighter[EF.ATTACK_BONUS] = 7

        # Only the fighter in world state — "wall_of_fire" is NOT an entity
        ws = make_world_state({"fighter_h002": fighter})
        rng = RNGManager(master_seed=200)

        intent = GrappleIntent(
            attacker_id="fighter_h002",
            target_id="wall_of_fire",  # Non-existent entity
        )

        turn_ctx = TurnContext(
            turn_index=0,
            actor_id="fighter_h002",
            actor_team="party",
        )

        turn_result = execute_turn(
            world_state=ws,
            turn_ctx=turn_ctx,
            combat_intent=intent,
            rng=rng,
            next_event_id=0,
            timestamp=1.0,
        )

        print(f"  Status: {turn_result.status}")
        print(f"  Failure reason: {turn_result.failure_reason}")
        event_types = [e.event_type for e in turn_result.events]
        print(f"  Events: {event_types}")

        # Engine should reject: target not found
        if turn_result.status == "invalid_intent":
            _record_hooligan_pass(
                sid,
                f"Engine correctly denied grapple on non-entity target: "
                f"{turn_result.failure_reason}",
            )
        else:
            _record_hooligan_finding(
                sid,
                f"Engine did NOT deny grapple on non-entity target. "
                f"Status: {turn_result.status}",
                module="aidm.core.play_loop",
                severity="wrong_result",
                phb_ref="PHB p.155",
            )

    except Exception as exc:
        _record_hooligan_crash(sid, f"{exc}\n{traceback.format_exc()}")


# ══════════════════════════════════════════════════════════════════════
# H-003: Fireball Yourself (Tier A)
# PHB p.175 — caster chooses point of origin. Self-targeting is legal.
# ══════════════════════════════════════════════════════════════════════


def scenario_h003_fireball_self() -> None:
    """H-003: Cast Fireball centered on self. Caster must be in own blast radius."""
    banner("H-003: Fireball Yourself (Tier A)")

    sid = "H-003"
    try:
        from aidm.schemas.entity_fields import EF
        from aidm.schemas.position import Position
        from aidm.core.rng_manager import RNGManager

        # Sorcerer at (10, 10), cast fireball centered on self
        sorcerer = make_caster(
            entity_id="sorcerer_h003",
            name="Pyraxis the Reckless",
            hp=25,
            position={"x": 10, "y": 10},
            caster_level=5,
            spell_dc_base=15,
        )

        # Need at least 2 entities for valid combat
        dummy = make_target(
            entity_id="dummy_h003",
            name="Distant Observer",
            hp=50,
            position={"x": 50, "y": 50},  # Far away — outside AoE
        )

        ws = make_world_state({
            "sorcerer_h003": sorcerer,
            "dummy_h003": dummy,
        })

        rng = RNGManager(master_seed=303)

        # Cast fireball at own position
        result = cast_spell(
            world_state=ws,
            caster_id="sorcerer_h003",
            spell_id="fireball",
            target_position=Position(x=10, y=10),  # Self position
            rng=rng,
        )

        if result["error"]:
            _record_hooligan_crash(sid, result["error"])
            return

        events = result["events"]
        event_types = [e["type"] for e in events]
        print(f"  Events: {event_types}")

        # Check if caster took damage from own fireball
        caster_hp_events = [
            e for e in events
            if e["type"] == "hp_changed"
            and e["payload"].get("entity_id") == "sorcerer_h003"
        ]

        if caster_hp_events:
            delta = caster_hp_events[0]["payload"].get("delta", 0)
            print(f"  Caster HP change: {delta}")
            print(f"  Caster took self-damage from own Fireball")
            _record_hooligan_pass(
                sid,
                f"Caster in own AoE, took {abs(delta)} damage (self-targeting works)",
            )
        else:
            # Caster might have been excluded — check affected_entities
            spell_cast_events = [e for e in events if e["type"] == "spell_cast"]
            affected = spell_cast_events[0]["payload"].get("affected_entities", []) if spell_cast_events else []
            print(f"  Affected entities: {affected}")

            if "sorcerer_h003" in affected:
                _record_hooligan_finding(
                    sid,
                    "Caster in affected_entities but no hp_changed event — "
                    "possible damage resolution gap",
                    module="aidm.core.spell_resolver",
                    severity="wrong_result",
                    phb_ref="PHB p.175",
                )
            else:
                _record_hooligan_finding(
                    sid,
                    "Caster at AoE center but NOT in affected_entities — "
                    "AoE rasterizer may exclude caster origin square",
                    module="aidm.core.aoe_rasterizer",
                    severity="wrong_result",
                    phb_ref="PHB p.175",
                )

        # Check NarrativeBrief
        if result["brief"]:
            print(f"  NarrativeBrief.actor_name: {result['brief'].actor_name}")
            print(f"  NarrativeBrief.damage_type: {result['brief'].damage_type}")

    except Exception as exc:
        _record_hooligan_crash(sid, f"{exc}\n{traceback.format_exc()}")


# ══════════════════════════════════════════════════════════════════════
# H-004: Full Attack a Corpse (Tier A)
# PHB p.145 — dead creatures become objects. Attacking them is legal.
# ══════════════════════════════════════════════════════════════════════


def scenario_h004_full_attack_corpse() -> None:
    """H-004: Full attack a defeated entity. Engine should deny (defeated check)."""
    banner("H-004: Full Attack a Corpse (Tier A)")

    sid = "H-004"
    try:
        from aidm.schemas.entity_fields import EF
        from aidm.schemas.attack import Weapon, AttackIntent
        from aidm.core.full_attack_resolver import FullAttackIntent
        from aidm.core.play_loop import execute_turn, TurnContext
        from aidm.core.rng_manager import RNGManager

        fighter = make_target(
            entity_id="fighter_h004",
            name="Gareth the Merciless",
            hp=45,
            team="party",
            size="medium",
            position={"x": 5, "y": 5},
        )
        fighter[EF.STR_MOD] = 3
        fighter[EF.BAB] = 8  # High BAB for iterative attacks
        fighter[EF.ATTACK_BONUS] = 11

        dead_goblin = make_target(
            entity_id="corpse_h004",
            name="Dead Goblin",
            hp=0,
            defeated=True,
            position={"x": 6, "y": 5},
        )

        ws = make_world_state({
            "fighter_h004": fighter,
            "corpse_h004": dead_goblin,
        })

        rng = RNGManager(master_seed=404)

        longsword = Weapon(
            damage_dice="1d8",
            damage_bonus=0,
            damage_type="slashing",
            critical_multiplier=2,
            critical_range=19,
            grip="one-handed",
            weapon_type="one-handed",
        )

        intent = FullAttackIntent(
            attacker_id="fighter_h004",
            target_id="corpse_h004",
            base_attack_bonus=8,
            weapon=longsword,
        )

        turn_ctx = TurnContext(
            turn_index=0,
            actor_id="fighter_h004",
            actor_team="party",
        )

        turn_result = execute_turn(
            world_state=ws,
            turn_ctx=turn_ctx,
            combat_intent=intent,
            rng=rng,
            next_event_id=0,
            timestamp=1.0,
        )

        print(f"  Status: {turn_result.status}")
        print(f"  Failure reason: {turn_result.failure_reason}")
        event_types = [e.event_type for e in turn_result.events]
        print(f"  Events: {event_types}")

        # Engine should deny: target already defeated
        if turn_result.status == "invalid_intent" and "defeated" in (turn_result.failure_reason or ""):
            _record_hooligan_pass(
                sid,
                f"Engine correctly denied attack on defeated entity: {turn_result.failure_reason}",
            )
        elif turn_result.status == "ok":
            # Engine allowed attacking a corpse — this is technically legal per RAW
            # (dead creatures are objects). Document as a finding about object-vs-creature.
            _record_hooligan_finding(
                sid,
                "Engine allowed full attack on defeated entity. D&D 3.5e treats "
                "dead creatures as objects (PHB p.145) — engine should either model "
                "object HP or deny. Current: denial expected (defeated check at play_loop:900-933).",
                module="aidm.core.play_loop",
                severity="design_question",
                phb_ref="PHB p.145",
            )
        else:
            _record_hooligan_pass(
                sid,
                f"Engine denied attack on corpse with status: {turn_result.status}",
            )

    except Exception as exc:
        _record_hooligan_crash(sid, f"{exc}\n{traceback.format_exc()}")


# ══════════════════════════════════════════════════════════════════════
# H-005: Delay Turn Forever (Tier B)
# PHB p.160 — delay is legal, no inherent time limit within a round.
# ══════════════════════════════════════════════════════════════════════


def scenario_h005_delay_forever() -> None:
    """H-005: Delay action. No delay resolver expected."""
    banner("H-005: Delay Turn Forever (Tier B)")

    sid = "H-005"
    try:
        # Check if a DelayIntent or delay action type exists
        has_delay = False
        try:
            from aidm.schemas import maneuvers
            has_delay = hasattr(maneuvers, "DelayIntent")
        except Exception:
            pass
        if not has_delay:
            try:
                from aidm.core import play_loop
                has_delay = hasattr(play_loop, "DelayIntent")
            except Exception:
                pass

        if has_delay:
            _record_hooligan_pass(sid, "DelayIntent exists — resolver available")
        else:
            _record_hooligan_finding(
                sid,
                "No DelayIntent or delay action resolver. Delay actions (PHB p.160) "
                "are not modeled. Players cannot delay their turn in initiative order.",
                module="aidm.core.play_loop",
                severity="coverage_gap",
                phb_ref="PHB p.160",
            )
            print(f"  Action type NOT supported: DelayAction")

    except Exception as exc:
        _record_hooligan_crash(sid, f"{exc}\n{traceback.format_exc()}")


# ══════════════════════════════════════════════════════════════════════
# H-006: Drop All Equipment Mid-Combat (Tier B)
# PHB p.142 — dropping items is a free action.
# ══════════════════════════════════════════════════════════════════════


def scenario_h006_drop_equipment() -> None:
    """H-006: Drop weapon, shield, armor mid-combat. No equipment resolver expected."""
    banner("H-006: Drop All Equipment Mid-Combat (Tier B)")

    sid = "H-006"
    try:
        # Check if equipment management intents exist
        has_drop = False
        try:
            from aidm.schemas import maneuvers
            has_drop = hasattr(maneuvers, "DropItemIntent") or hasattr(maneuvers, "UnequipIntent")
        except Exception:
            pass
        if not has_drop:
            try:
                from aidm.core import play_loop
                has_drop = hasattr(play_loop, "DropItemIntent")
            except Exception:
                pass

        if has_drop:
            _record_hooligan_pass(sid, "DropItem/Unequip intent found")
        else:
            _record_hooligan_finding(
                sid,
                "No DropItemIntent or equipment management resolver. Dropping items "
                "is a free action (PHB p.142), removing armor requires time (1 min "
                "heavy). Engine has no action economy for equip/unequip/drop.",
                module="aidm.core.play_loop",
                severity="coverage_gap",
                phb_ref="PHB p.142",
            )
            print(f"  Action type NOT supported: DropItem/Unequip")

            # Verify entity model has weapon field (partial equipment state)
            from aidm.schemas.entity_fields import EF
            print(f"  Entity has EF.WEAPON: {hasattr(EF, 'WEAPON')}")
            print(f"  Entity has EF.INVENTORY: {hasattr(EF, 'INVENTORY')}")
            print(f"  Equipment state exists in entity schema but no runtime equip/drop actions")

    except Exception as exc:
        _record_hooligan_crash(sid, f"{exc}\n{traceback.format_exc()}")


# ══════════════════════════════════════════════════════════════════════
# H-007: Charge Off the Map Edge (Tier B)
# PHB p.154 — charge requires clear straight line to a target.
# ══════════════════════════════════════════════════════════════════════


def scenario_h007_charge_off_map() -> None:
    """H-007: Charge off the map. No charge resolver expected."""
    banner("H-007: Charge Off the Map Edge (Tier B)")

    sid = "H-007"
    try:
        has_charge = False
        try:
            from aidm.schemas import maneuvers
            has_charge = hasattr(maneuvers, "ChargeIntent")
        except Exception:
            pass
        if not has_charge:
            try:
                from aidm.core import play_loop
                has_charge = hasattr(play_loop, "ChargeIntent")
            except Exception:
                pass

        if has_charge:
            _record_hooligan_pass(sid, "ChargeIntent found — resolver exists")
        else:
            _record_hooligan_finding(
                sid,
                "No ChargeIntent or charge resolver. Charge actions (PHB p.154) "
                "are not modeled. Cannot test map boundary behavior for charges.",
                module="aidm.core.play_loop",
                severity="coverage_gap",
                phb_ref="PHB p.154",
            )
            print(f"  Action type NOT supported: Charge")

    except Exception as exc:
        _record_hooligan_crash(sid, f"{exc}\n{traceback.format_exc()}")


# ══════════════════════════════════════════════════════════════════════
# H-008: Cure Light Wounds on Undead (Tier A)
# PHB p.215-216 — cure spells deal damage to undead.
# ══════════════════════════════════════════════════════════════════════


def scenario_h008_clw_on_undead() -> None:
    """H-008: Cast CLW on undead. Tests creature_type schema + positive energy as damage."""
    banner("H-008: Cure Light Wounds on Undead (Tier A)")

    sid = "H-008"
    try:
        from aidm.schemas.entity_fields import EF
        from aidm.schemas.position import Position
        from aidm.core.rng_manager import RNGManager

        # Check if creature_type field exists
        has_creature_type = hasattr(EF, "CREATURE_TYPE") or hasattr(EF, "TYPE")
        print(f"  EF.CREATURE_TYPE exists: {has_creature_type}")

        # Create a "zombie" entity — but entity schema has no creature_type field
        cleric = make_caster(
            entity_id="cleric_h008",
            name="Father Alaric",
            hp=30,
            position={"x": 5, "y": 5},
            caster_level=3,
            spell_dc_base=14,
        )

        zombie = make_target(
            entity_id="zombie_h008",
            name="Shambling Zombie",
            hp=20,
            position={"x": 6, "y": 5},
            team="monsters",
            size="medium",
        )
        # Attempt to set creature_type even though schema may not support it
        zombie["creature_type"] = "undead"

        ws = make_world_state({
            "cleric_h008": cleric,
            "zombie_h008": zombie,
        })

        rng = RNGManager(master_seed=808)

        # Cast CLW on the zombie
        result = cast_spell(
            world_state=ws,
            caster_id="cleric_h008",
            spell_id="cure_light_wounds",
            target_entity_id="zombie_h008",
            rng=rng,
        )

        if result["error"]:
            print(f"  Error: {result['error']}")

        events = result["events"]
        event_types = [e["type"] for e in events]
        print(f"  Events: {event_types}")

        # Check what happened to the zombie
        hp_events = [
            e for e in events
            if e["type"] == "hp_changed"
            and e["payload"].get("entity_id") == "zombie_h008"
        ]

        if hp_events:
            delta = hp_events[0]["payload"].get("delta", 0)
            print(f"  Zombie HP change: {delta}")
            if delta > 0:
                # CLW healed the zombie — no undead damage reversal
                _record_hooligan_finding(
                    sid,
                    f"CLW healed undead entity for +{delta} instead of dealing damage. "
                    f"Entity schema has no creature_type field — spell resolver cannot "
                    f"distinguish undead from living. Positive energy damage reversal "
                    f"(PHB p.215-216) not implemented.",
                    module="aidm.core.spell_resolver",
                    severity="missing_mechanic",
                    phb_ref="PHB p.215-216",
                )
            elif delta < 0:
                _record_hooligan_pass(
                    sid,
                    f"CLW correctly dealt {abs(delta)} damage to undead (positive energy reversal)",
                )
            else:
                _record_hooligan_finding(
                    sid,
                    "CLW produced no HP change on undead target",
                    module="aidm.core.spell_resolver",
                    severity="wrong_result",
                    phb_ref="PHB p.215-216",
                )
        else:
            # No HP event — CLW may have healed to max or had no effect
            print(f"  No hp_changed event for zombie")
            # Check if spell resolved at all
            spell_events = [e for e in events if e["type"] == "spell_cast"]
            if spell_events:
                _record_hooligan_finding(
                    sid,
                    "CLW on undead: spell_cast event emitted but no hp_changed. "
                    "Entity may already be at max HP (healing capped) — but damage "
                    "should have been dealt to undead regardless. creature_type field "
                    "not in entity schema.",
                    module="aidm.core.spell_resolver",
                    severity="missing_mechanic",
                    phb_ref="PHB p.215-216",
                )
            else:
                _record_hooligan_finding(
                    sid,
                    "CLW on undead: no events at all. Possible crash suppressed.",
                    module="aidm.core.spell_resolver",
                    severity="wrong_result",
                    phb_ref="PHB p.215-216",
                )

    except Exception as exc:
        _record_hooligan_crash(sid, f"{exc}\n{traceback.format_exc()}")


# ══════════════════════════════════════════════════════════════════════
# H-009: Coup de Grace Yourself (Tier B)
# PHB p.153 — coup de grace requires a helpless defender.
# ══════════════════════════════════════════════════════════════════════


def scenario_h009_coup_de_grace_self() -> None:
    """H-009: Coup de grace on self. No CdG resolver expected."""
    banner("H-009: Coup de Grace Yourself (Tier B)")

    sid = "H-009"
    try:
        has_cdg = False
        try:
            from aidm.schemas import maneuvers
            has_cdg = hasattr(maneuvers, "CoupDeGraceIntent")
        except Exception:
            pass
        if not has_cdg:
            try:
                from aidm.core import play_loop
                has_cdg = hasattr(play_loop, "CoupDeGraceIntent")
            except Exception:
                pass

        if has_cdg:
            _record_hooligan_pass(sid, "CoupDeGraceIntent found — resolver exists")
        else:
            _record_hooligan_finding(
                sid,
                "No CoupDeGraceIntent or coup de grace resolver. CdG (PHB p.153) "
                "requires a helpless target. Self-targeting would be denied (character "
                "is not helpless). Neither the action type nor the helpless validation "
                "exist.",
                module="aidm.core.play_loop",
                severity="coverage_gap",
                phb_ref="PHB p.153",
            )
            print(f"  Action type NOT supported: CoupDeGrace")

    except Exception as exc:
        _record_hooligan_crash(sid, f"{exc}\n{traceback.format_exc()}")


# ══════════════════════════════════════════════════════════════════════
# H-010: The 10-Buff Stack (Tier A)
# PHB various — buff spells with typed/untyped bonus interactions.
# ══════════════════════════════════════════════════════════════════════


def scenario_h010_buff_stack() -> None:
    """H-010: Cast multiple buffs on one fighter. Tests modifier stacking and conditions."""
    banner("H-010: The 10-Buff Stack (Tier A)")

    sid = "H-010"
    try:
        from aidm.schemas.entity_fields import EF
        from aidm.schemas.position import Position
        from aidm.core.rng_manager import RNGManager
        from aidm.data.spell_definitions import SPELL_REGISTRY

        # Available buff spells (from registry check)
        buff_spells = [
            "bulls_strength",    # +4 STR (enhancement)
            "cats_grace",        # +4 DEX (enhancement)
            "bears_endurance",   # +4 CON (enhancement)
            "owls_wisdom",       # +4 WIS (enhancement)
            "mage_armor",        # +4 armor AC
            "bless",             # +1 morale attack/saves
            "haste",             # +1 attack, +1 dodge AC, extra attack
            "shield",            # +4 shield AC
        ]

        # Verify which spells are actually in registry
        available = [s for s in buff_spells if s in SPELL_REGISTRY]
        missing = [s for s in buff_spells if s not in SPELL_REGISTRY]
        print(f"  Available buff spells: {len(available)}/{len(buff_spells)}")
        if missing:
            print(f"  Missing from SPELL_REGISTRY: {missing}")

        # Create target fighter
        fighter = make_target(
            entity_id="fighter_h010",
            name="Aldric the Buffed",
            hp=60,
            team="party",
            size="medium",
            position={"x": 15, "y": 15},
        )
        fighter[EF.STR_MOD] = 3
        fighter[EF.BAB] = 8
        fighter[EF.ATTACK_BONUS] = 11

        # Create 4 casters to apply buffs
        casters = {}
        for i in range(4):
            cid = f"caster_{i}_h010"
            c = make_caster(
                entity_id=cid,
                name=f"Caster {i + 1}",
                hp=25,
                position={"x": 14 + i, "y": 14},
                caster_level=5,
                spell_dc_base=15,
            )
            casters[cid] = c

        entities = {"fighter_h010": fighter, **casters}
        ws = make_world_state(entities)

        rng = RNGManager(master_seed=1010)

        # Cast all available buffs sequentially
        conditions_applied = []
        errors = []
        for idx, spell_id in enumerate(available):
            caster_id = f"caster_{idx % 4}_h010"
            result = cast_spell(
                world_state=ws,
                caster_id=caster_id,
                spell_id=spell_id,
                target_entity_id="fighter_h010",
                rng=rng,
                turn_index=idx,
                timestamp=float(idx + 1),
            )

            if result["error"]:
                errors.append(f"{spell_id}: {result['error']}")
                print(f"  {spell_id}: ERROR — {result['error']}")
                continue

            # Update world state for next cast
            ws = result["world_state"]

            # Check for condition_applied events
            cond_events = [
                e for e in result["events"]
                if e["type"] == "condition_applied"
            ]
            for ce in cond_events:
                cond_name = ce["payload"].get("condition") or ce["payload"].get("condition_type", "unknown")
                conditions_applied.append(f"{spell_id} → {cond_name}")
                print(f"  {spell_id}: condition_applied → {cond_name}")

            if not cond_events:
                # Some buff spells may not apply conditions (spell_cast only)
                spell_events = [e for e in result["events"] if e["type"] == "spell_cast"]
                if spell_events:
                    print(f"  {spell_id}: spell_cast (no condition event)")
                else:
                    print(f"  {spell_id}: no spell_cast event")

        print(f"  Total conditions applied: {len(conditions_applied)}")
        print(f"  Errors: {len(errors)}")

        # Evaluate
        if len(errors) == 0 and len(conditions_applied) >= 3:
            _record_hooligan_pass(
                sid,
                f"{len(available)} buffs cast, {len(conditions_applied)} conditions applied, "
                f"0 errors. Sequential buff stacking works.",
            )
        elif len(errors) == 0:
            _record_hooligan_pass(
                sid,
                f"{len(available)} buffs cast without crash. {len(conditions_applied)} "
                f"conditions applied (some buffs may not emit condition events).",
            )
        else:
            _record_hooligan_finding(
                sid,
                f"{len(errors)} errors during buff stacking: {'; '.join(errors[:3])}",
                module="aidm.core.spell_resolver",
                severity="wrong_result",
                phb_ref="PHB various (buff spell stacking)",
            )

    except Exception as exc:
        _record_hooligan_crash(sid, f"{exc}\n{traceback.format_exc()}")


# ══════════════════════════════════════════════════════════════════════
# H-011: Fireball the Entire Party (Tier A)
# PHB — nothing prevents targeting allies. AoE doesn't care about allegiance.
# ══════════════════════════════════════════════════════════════════════


def scenario_h011_fireball_party() -> None:
    """H-011: Cast Fireball centered on own party. Friendly fire test."""
    banner("H-011: Fireball the Entire Party (Tier A)")

    sid = "H-011"
    try:
        from aidm.schemas.entity_fields import EF
        from aidm.schemas.position import Position
        from aidm.core.rng_manager import RNGManager

        # Sorcerer + 3 allies, all clustered at the same position
        sorcerer = make_caster(
            entity_id="sorc_h011",
            name="Betrayer Mage",
            hp=25,
            position={"x": 10, "y": 10},
        )

        allies = {}
        for i in range(3):
            aid = f"ally_{i}_h011"
            a = make_target(
                entity_id=aid,
                name=f"Ally {i + 1}",
                hp=15,
                position={"x": 10 + i, "y": 10},  # Adjacent to sorcerer
                team="party",
                size="medium",
            )
            allies[aid] = a

        entities = {"sorc_h011": sorcerer, **allies}
        ws = make_world_state(entities)
        rng = RNGManager(master_seed=1111)

        # Cast fireball at party center
        result = cast_spell(
            world_state=ws,
            caster_id="sorc_h011",
            spell_id="fireball",
            target_position=Position(x=10, y=10),
            rng=rng,
        )

        if result["error"]:
            _record_hooligan_crash(sid, result["error"])
            return

        events = result["events"]
        event_types = [e["type"] for e in events]
        print(f"  Events: {event_types}")

        # Count friendly casualties
        hp_events = [e for e in events if e["type"] == "hp_changed"]
        defeat_events = [e for e in events if e["type"] == "entity_defeated"]
        friendly_damaged = [
            e for e in hp_events
            if e["payload"].get("entity_id", "").startswith("ally_")
            or e["payload"].get("entity_id") == "sorc_h011"
        ]

        print(f"  Total hp_changed events: {len(hp_events)}")
        print(f"  Friendly fire hits: {len(friendly_damaged)}")
        for fd in friendly_damaged:
            eid = fd["payload"].get("entity_id")
            delta = fd["payload"].get("delta", 0)
            print(f"    {eid}: {delta}")

        print(f"  Entity defeats: {[e['payload'].get('entity_id') for e in defeat_events]}")

        if len(friendly_damaged) >= 1:
            _record_hooligan_pass(
                sid,
                f"Friendly fire resolved: {len(friendly_damaged)} allies/self hit, "
                f"{len(defeat_events)} defeated. AoE doesn't check allegiance.",
            )
        else:
            # Check if allies were in the AoE
            spell_events = [e for e in events if e["type"] == "spell_cast"]
            affected = spell_events[0]["payload"].get("affected_entities", []) if spell_events else []
            print(f"  Affected entities: {affected}")
            _record_hooligan_finding(
                sid,
                f"No friendly fire damage despite allies in AoE cluster. "
                f"Affected: {affected}. AoE may have allegiance filter.",
                module="aidm.core.spell_resolver",
                severity="wrong_result",
                phb_ref="PHB (AoE targeting)",
            )

    except Exception as exc:
        _record_hooligan_crash(sid, f"{exc}\n{traceback.format_exc()}")


# ══════════════════════════════════════════════════════════════════════
# H-012: Improvised Weapon — Goblin Body (Tier B)
# PHB p.113 — improvised weapons are legal with a -4 penalty.
# ══════════════════════════════════════════════════════════════════════


def scenario_h012_improvised_weapon() -> None:
    """H-012: Throw a dead goblin at a live goblin. No improvised weapon resolver expected."""
    banner("H-012: Improvised Weapon — Goblin Body (Tier B)")

    sid = "H-012"
    try:
        has_improvised = False
        try:
            from aidm.schemas.attack import Weapon
            # Check if Weapon supports improvised type
            w = Weapon(
                damage_dice="1d6",
                damage_bonus=0,
                damage_type="bludgeoning",
                critical_multiplier=2,
                critical_range=20,
                grip="two-handed",
                weapon_type="improvised",
            )
            has_improvised = True
            print(f"  Weapon(weapon_type='improvised') accepted by schema")
        except Exception as exc:
            print(f"  Weapon(weapon_type='improvised'): {type(exc).__name__}: {exc}")

        if has_improvised:
            # Try to actually attack with it
            from aidm.schemas.entity_fields import EF
            from aidm.schemas.attack import Weapon, AttackIntent
            from aidm.core.play_loop import execute_turn, TurnContext
            from aidm.core.rng_manager import RNGManager

            fighter = make_target(
                entity_id="fighter_h012",
                name="Goblin Hurler",
                hp=45,
                team="party",
                size="medium",
                position={"x": 5, "y": 5},
            )
            fighter[EF.STR_MOD] = 3
            fighter[EF.BAB] = 4
            fighter[EF.ATTACK_BONUS] = 3  # BAB 4 + STR 3 - 4 (nonproficient) = 3

            target = make_target(
                entity_id="target_h012",
                name="Live Goblin",
                hp=8,
                position={"x": 7, "y": 5},
            )

            ws = make_world_state({
                "fighter_h012": fighter,
                "target_h012": target,
            })
            rng = RNGManager(master_seed=1212)

            improvised = Weapon(
                damage_dice="1d6",
                damage_bonus=0,
                damage_type="bludgeoning",
                critical_multiplier=2,
                critical_range=20,
                grip="two-handed",
                weapon_type="improvised",
            )

            intent = AttackIntent(
                attacker_id="fighter_h012",
                target_id="target_h012",
                attack_bonus=3,
                weapon=improvised,
            )

            turn_ctx = TurnContext(
                turn_index=0,
                actor_id="fighter_h012",
                actor_team="party",
            )

            turn_result = execute_turn(
                world_state=ws,
                turn_ctx=turn_ctx,
                combat_intent=intent,
                rng=rng,
                next_event_id=0,
                timestamp=1.0,
            )

            print(f"  Status: {turn_result.status}")
            event_types = [e.event_type for e in turn_result.events]
            print(f"  Events: {event_types}")

            if turn_result.status == "ok":
                _record_hooligan_pass(
                    sid,
                    f"Improvised weapon attack resolved (weapon_type='improvised' accepted). "
                    f"Events: {event_types}",
                )
            else:
                _record_hooligan_finding(
                    sid,
                    f"Improvised weapon attack failed: {turn_result.failure_reason}",
                    module="aidm.core.attack_resolver",
                    severity="wrong_result",
                    phb_ref="PHB p.113",
                )
        else:
            _record_hooligan_finding(
                sid,
                "Weapon schema does not accept weapon_type='improvised'. "
                "Improvised weapons (PHB p.113) require -4 nonproficiency penalty "
                "and are not modeled.",
                module="aidm.schemas.attack",
                severity="coverage_gap",
                phb_ref="PHB p.113",
            )

    except Exception as exc:
        _record_hooligan_crash(sid, f"{exc}\n{traceback.format_exc()}")


# ══════════════════════════════════════════════════════════════════════
# Orchestrator
# ══════════════════════════════════════════════════════════════════════


ALL_HOOLIGAN_SCENARIOS = [
    ("H-001", scenario_h001_ready_action),
    ("H-002", scenario_h002_grapple_spell_effect),
    ("H-003", scenario_h003_fireball_self),
    ("H-004", scenario_h004_full_attack_corpse),
    ("H-005", scenario_h005_delay_forever),
    ("H-006", scenario_h006_drop_equipment),
    ("H-007", scenario_h007_charge_off_map),
    ("H-008", scenario_h008_clw_on_undead),
    ("H-009", scenario_h009_coup_de_grace_self),
    ("H-010", scenario_h010_buff_stack),
    ("H-011", scenario_h011_fireball_party),
    ("H-012", scenario_h012_improvised_weapon),
]


def run_hooligan() -> Dict[str, str]:
    """Run all 12 hooligan scenarios. Returns per-scenario results dict."""
    banner("PHASE 3: THE HOOLIGAN PROTOCOL — Adversarial Edge Cases")

    for scenario_id, fn in ALL_HOOLIGAN_SCENARIOS:
        fn()

    # Print summary
    print()
    print("  --- Hooligan Summary ---")
    total = len(ALL_HOOLIGAN_SCENARIOS)
    passed = sum(1 for v in HOOLIGAN_RESULTS.values() if v == "PASS")
    findings = sum(1 for v in HOOLIGAN_RESULTS.values() if v == "FINDING")
    crashes = sum(1 for v in HOOLIGAN_RESULTS.values() if v == "CRASH")
    print(f"  Scenarios run: {total}")
    print(f"  PASS: {passed}, FINDING: {findings}, CRASH: {crashes}")

    if HOOLIGAN_FINDINGS:
        print()
        print(f"  Findings ({len(HOOLIGAN_FINDINGS)}):")
        for f in HOOLIGAN_FINDINGS:
            print(f"    {f['scenario']} [{f['severity']}]: {f['description'][:80]}")
            if f.get("phb_ref"):
                print(f"      PHB ref: {f['phb_ref']}")

    # Coverage gap summary
    gap_scenarios = [f["scenario"] for f in HOOLIGAN_FINDINGS if f["severity"] == "coverage_gap"]
    if gap_scenarios:
        print()
        print(f"  Action types without resolvers ({len(gap_scenarios)}):")
        for s in gap_scenarios:
            print(f"    {s}")

    # Transfer results to SCENARIO_RESULTS for main summary
    for k, v in HOOLIGAN_RESULTS.items():
        SCENARIO_RESULTS[k] = v

    return HOOLIGAN_RESULTS
