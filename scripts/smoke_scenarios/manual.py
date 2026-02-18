"""Manual smoke test scenarios B through H.

WO-SMOKE-FUZZER: Extracted from scripts/smoke_test.py to support modular structure.
Original scenarios preserved exactly — imports happen inside each function body.
"""
from __future__ import annotations

import traceback
from typing import Any, Dict, List, Optional

from smoke_scenarios.common import (
    STAGE_RESULTS,
    SCENARIO_RESULTS,
    NEW_FINDINGS,
    banner,
    record_pass,
    record_fail,
    record_finding,
)


def scenario_b_melee_attack() -> Optional[Dict[str, Any]]:
    """Scenario B: Fighter attacks goblin with longsword. Exercises melee event path."""
    banner("SCENARIO B: Melee Attack — Fighter vs Goblin")
    result: Dict[str, Any] = {}

    try:
        from aidm.schemas.entity_fields import EF
        from aidm.schemas.attack import Weapon, AttackIntent
        from aidm.core.play_loop import execute_turn, TurnContext
        from aidm.core.state import WorldState, FrozenWorldStateView
        from aidm.core.rng_manager import RNGManager
        from aidm.lens.narrative_brief import NarrativeBrief, assemble_narrative_brief
        from aidm.narration.narrator import Narrator, NarrationTemplates
        from aidm.schemas.engine_result import EngineResult, EngineResultStatus
        from datetime import datetime, timezone

        # B1: Create fighter entity (STR 16 → +3 mod, longsword equipped)
        fighter = {
            EF.ENTITY_ID: "fighter_1",
            "name": "Gareth the Bold",
            EF.HP_CURRENT: 45,
            EF.HP_MAX: 45,
            EF.AC: 18,
            EF.ATTACK_BONUS: 7,  # BAB 4 + STR 3
            EF.BAB: 4,
            EF.STR_MOD: 3,
            EF.DEX_MOD: 1,
            EF.INT_MOD: 0,
            EF.CON_MOD: 2,
            EF.WIS_MOD: 1,
            EF.CHA_MOD: 0,
            EF.SAVE_FORT: 6,
            EF.SAVE_REF: 2,
            EF.SAVE_WILL: 2,
            EF.TEAM: "party",
            EF.WEAPON: "longsword",
            EF.POSITION: {"x": 5, "y": 5},
            EF.DEFEATED: False,
            EF.SIZE_CATEGORY: "medium",
            EF.BASE_SPEED: 30,
            EF.CONDITIONS: {},
        }
        print(f"  Fighter: {fighter['name']} (STR mod +{fighter[EF.STR_MOD]}, BAB +{fighter[EF.BAB]})")
        record_pass("B1: Create fighter entity")

        # B2: Create goblin target (HP 5/5, AC 15)
        goblin = {
            EF.ENTITY_ID: "goblin_b",
            "name": "Goblin Skirmisher",
            EF.HP_CURRENT: 5,
            EF.HP_MAX: 5,
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
            EF.TEAM: "monsters",
            EF.WEAPON: "shortbow",
            EF.POSITION: {"x": 6, "y": 5},  # Adjacent to fighter
            EF.DEFEATED: False,
            EF.SIZE_CATEGORY: "small",
            EF.BASE_SPEED: 30,
            EF.CONDITIONS: {},
        }
        print(f"  Goblin: {goblin['name']} (HP {goblin[EF.HP_CURRENT]}/{goblin[EF.HP_MAX]}, AC {goblin[EF.AC]})")
        record_pass("B2: Create goblin target")

        # B3: Build WorldState and execute melee attack
        entities = {
            fighter[EF.ENTITY_ID]: fighter,
            goblin[EF.ENTITY_ID]: goblin,
        }
        world_state = WorldState(
            ruleset_version="3.5e",
            entities=entities,
            active_combat={
                "round_index": 1,
                "turn_counter": 0,
                "initiative_order": ["fighter_1", "goblin_b"],
                "flat_footed_actors": [],
                "aoo_used_this_round": [],
                "duration_tracker": {"effects": []},
            },
        )

        rng = RNGManager(master_seed=99)

        longsword = Weapon(
            damage_dice="1d8",
            damage_bonus=0,
            damage_type="slashing",
            critical_multiplier=2,
            critical_range=19,  # Longsword threatens on 19-20
            grip="one-handed",
            weapon_type="one-handed",
        )

        intent = AttackIntent(
            attacker_id="fighter_1",
            target_id="goblin_b",
            attack_bonus=fighter[EF.ATTACK_BONUS],
            weapon=longsword,
        )

        turn_ctx = TurnContext(
            turn_index=0,
            actor_id="fighter_1",
            actor_team="party",
        )

        print(f"  Intent: Melee attack with longsword (bonus +{intent.attack_bonus})")

        turn_result = execute_turn(
            world_state=world_state,
            turn_ctx=turn_ctx,
            combat_intent=intent,
            rng=rng,
            next_event_id=0,
            timestamp=1.0,
        )

        result["turn_result"] = turn_result

        # B4: Print events emitted
        print(f"  Status: {turn_result.status}")
        print(f"  Narration token: {turn_result.narration}")
        print(f"  Events emitted: {len(turn_result.events)}")
        for event in turn_result.events:
            print(f"    Event #{event.event_id}: {event.event_type} — {list(event.payload.keys())}")

        # Check for expected event types
        event_types = [e.event_type for e in turn_result.events]
        has_attack_roll = "attack_roll" in event_types
        has_hp_changed = "hp_changed" in event_types
        has_defeat = "entity_defeated" in event_types

        if turn_result.status == "ok":
            record_pass("B3: Execute melee attack",
                        f"events={event_types}, narration={turn_result.narration}")
        else:
            record_fail("B3: Execute melee attack",
                        f"status={turn_result.status}: {turn_result.failure_reason}")

        # B5-B6: Assemble NarrativeBrief from events
        frozen_view = FrozenWorldStateView(turn_result.world_state)
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

        narration_token = turn_result.narration or "attack_hit"
        brief = assemble_narrative_brief(
            events=event_dicts,
            narration_token=narration_token,
            frozen_view=frozen_view,
        )
        result["brief"] = brief

        print(f"  NarrativeBrief:")
        print(f"    actor_name: {brief.actor_name}")
        print(f"    target_name: {brief.target_name}")
        print(f"    damage_type: {brief.damage_type}")
        print(f"    severity: {brief.severity}")
        print(f"    target_defeated: {brief.target_defeated}")
        print(f"    weapon_name: {brief.weapon_name}")

        record_pass("B5: Assemble NarrativeBrief (melee)",
                     f"actor={brief.actor_name}, damage_type={brief.damage_type}")

        # B7-B8: Generate template narration
        try:
            template = NarrationTemplates.get_template(narration_token, brief.severity)
            actor_name = brief.actor_name
            target_name = brief.target_name or "the target"
            weapon_name = brief.weapon_name or "longsword"
            damage = 0
            for event in turn_result.events:
                if event.event_type == "hp_changed" and event.payload.get("delta", 0) < 0:
                    damage = abs(event.payload.get("delta", 0))
                    break

            try:
                narration_text = template.format(
                    actor=actor_name, target=target_name,
                    weapon=weapon_name, damage=damage,
                )
            except KeyError:
                narration_text = template

            print(f"  Narration (template): {narration_text!r}")
            result["narration_text"] = narration_text

            # Check entity names and damage type in narration
            has_entity_names = "Gareth" in narration_text or "Goblin" in narration_text
            print(f"  Entity names in narration: {has_entity_names}")

            record_pass("B7: Template narration (melee)", f"text={narration_text!r}")
        except Exception as exc:
            record_fail("B7: Template narration (melee)", str(exc), error=str(exc))

        # Also try Narrator class
        try:
            event_dicts_narrator = [
                {"type": e.event_type, "timestamp": e.timestamp, **e.payload}
                for e in turn_result.events
            ]
            engine_result = EngineResult(
                result_id="smoke_test_b_001",
                intent_id="smoke_test_b_intent",
                status=EngineResultStatus.SUCCESS,
                resolved_at=datetime.now(timezone.utc),
                narration_token=turn_result.narration or "attack_hit",
                events=event_dicts_narrator,
            )
            narrator = Narrator(use_templates=True)
            narrator.register_entity_name("fighter_1", "Gareth the Bold")
            narrator.register_entity_name("goblin_b", "Goblin Skirmisher")
            narrator_output = narrator.narrate(engine_result)
            result["narrator_output"] = narrator_output
            print(f"  Narration (Narrator class): {narrator_output!r}")
            record_pass("B8: Narrator class (melee)")
        except Exception as exc:
            record_fail("B8: Narrator class (melee)", str(exc), error=str(exc))
            record_finding(f"Narrator class failed on melee path: {exc}")

        SCENARIO_RESULTS["B"] = "PASS"
        return result

    except Exception as exc:
        record_fail("B: Melee attack scenario", str(exc),
                     module=traceback.format_exc().splitlines()[-2] if traceback.format_exc() else "",
                     error=str(exc))
        traceback.print_exc()
        SCENARIO_RESULTS["B"] = "FAIL"
        record_finding(f"Scenario B crashed: {exc}")
        return None


# ══════════════════════════════════════════════════════════════════════════
# SCENARIO C: Multi-Target Spell — Fireball hitting 2+ Goblins
# ══════════════════════════════════════════════════════════════════════════

def scenario_c_multi_target() -> Optional[Dict[str, Any]]:
    """Scenario C: Fireball at 2-3 goblins. Exercises multi-target NarrativeBrief."""
    banner("SCENARIO C: Multi-Target Spell — Fireball vs 3 Goblins")
    result: Dict[str, Any] = {}

    try:
        from aidm.schemas.entity_fields import EF
        from aidm.core.play_loop import execute_turn, TurnContext
        from aidm.core.spell_resolver import SpellCastIntent
        from aidm.schemas.position import Position
        from aidm.core.state import WorldState, FrozenWorldStateView
        from aidm.core.rng_manager import RNGManager
        from aidm.lens.narrative_brief import NarrativeBrief, assemble_narrative_brief

        # C1: Create caster (reuse Elara stats)
        caster = {
            EF.ENTITY_ID: "wizard_c",
            "name": "Elara the Evoker",
            EF.HP_CURRENT: 32,
            EF.HP_MAX: 32,
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
            EF.POSITION: {"x": 5, "y": 5},
            EF.DEFEATED: False,
            EF.SIZE_CATEGORY: "medium",
            EF.BASE_SPEED: 30,
            EF.CONDITIONS: {},
            "caster_level": 5,
            "spell_dc_base": 13,
            "spells_prepared": ["fireball"],
        }

        # C2: Create 3 goblins clustered within fireball radius
        # Fireball is 20ft radius burst — place all goblins at (20, 20) area
        goblins = []
        for i in range(1, 4):
            g = {
                EF.ENTITY_ID: f"goblin_c{i}",
                "name": f"Goblin Grunt {i}",
                EF.HP_CURRENT: 6,
                EF.HP_MAX: 6,
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
                EF.TEAM: "monsters",
                EF.WEAPON: "shortbow",
                EF.POSITION: {"x": 20 + i, "y": 20},  # Clustered
                EF.DEFEATED: False,
                EF.SIZE_CATEGORY: "small",
                EF.BASE_SPEED: 30,
                EF.CONDITIONS: {},
            }
            goblins.append(g)

        print(f"  Caster: {caster['name']} at ({caster[EF.POSITION]['x']}, {caster[EF.POSITION]['y']})")
        for g in goblins:
            print(f"  Target: {g['name']} at ({g[EF.POSITION]['x']}, {g[EF.POSITION]['y']})")
        record_pass("C1: Create entities (1 caster + 3 goblins)")

        # C3: Build WorldState and cast fireball
        entities = {caster[EF.ENTITY_ID]: caster}
        for g in goblins:
            entities[g[EF.ENTITY_ID]] = g

        world_state = WorldState(
            ruleset_version="3.5e",
            entities=entities,
            active_combat={
                "round_index": 1,
                "turn_counter": 0,
                "initiative_order": ["wizard_c", "goblin_c1", "goblin_c2", "goblin_c3"],
                "flat_footed_actors": [],
                "aoo_used_this_round": [],
                "duration_tracker": {"effects": []},
            },
        )

        rng = RNGManager(master_seed=77)

        # Target center of goblin cluster
        intent = SpellCastIntent(
            caster_id="wizard_c",
            spell_id="fireball",
            target_position=Position(x=21, y=20),
        )

        turn_ctx = TurnContext(
            turn_index=0,
            actor_id="wizard_c",
            actor_team="party",
        )

        print(f"  Intent: Fireball at ({intent.target_position.x}, {intent.target_position.y})")

        turn_result = execute_turn(
            world_state=world_state,
            turn_ctx=turn_ctx,
            combat_intent=intent,
            rng=rng,
            next_event_id=0,
            timestamp=1.0,
        )
        result["turn_result"] = turn_result

        # C4: Print events emitted
        print(f"  Status: {turn_result.status}")
        print(f"  Events emitted: {len(turn_result.events)}")

        hp_events = [e for e in turn_result.events if e.event_type == "hp_changed"]
        defeat_events = [e for e in turn_result.events if e.event_type == "entity_defeated"]
        spell_events = [e for e in turn_result.events if e.event_type == "spell_cast"]

        print(f"  hp_changed events: {len(hp_events)}")
        print(f"  entity_defeated events: {len(defeat_events)}")

        for event in turn_result.events:
            if event.event_type in ("spell_cast", "hp_changed", "entity_defeated"):
                print(f"    {event.event_type}: {event.payload}")

        # Check affected entities in spell_cast
        affected = []
        if spell_events:
            affected = spell_events[0].payload.get("affected_entities", [])
            print(f"  Affected entities: {affected}")

        if turn_result.status == "ok":
            record_pass("C3: Cast fireball at cluster",
                        f"{len(hp_events)} hp_changed, {len(defeat_events)} defeated, "
                        f"{len(affected)} affected")
        else:
            record_fail("C3: Cast fireball at cluster",
                        f"status={turn_result.status}: {turn_result.failure_reason}")

        # C5-C6: Assemble NarrativeBrief
        frozen_view = FrozenWorldStateView(turn_result.world_state)
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

        narration_token = turn_result.narration or "spell_damage_dealt"
        brief = assemble_narrative_brief(
            events=event_dicts,
            narration_token=narration_token,
            frozen_view=frozen_view,
        )
        result["brief"] = brief

        print(f"  NarrativeBrief:")
        print(f"    actor_name: {brief.actor_name}")
        print(f"    target_name: {brief.target_name}")
        print(f"    additional_targets: {brief.additional_targets}")
        print(f"    damage_type: {brief.damage_type}")
        print(f"    severity: {brief.severity}")

        multi_target_captured = len(brief.additional_targets) > 0
        print(f"  Multi-target captured: {multi_target_captured} "
              f"(primary + {len(brief.additional_targets)} additional)")

        if multi_target_captured:
            record_pass("C5: Multi-target NarrativeBrief",
                        f"{1 + len(brief.additional_targets)} targets captured")
        else:
            if len(hp_events) > 1:
                record_fail("C5: Multi-target NarrativeBrief",
                            "Multiple hp_changed events but additional_targets is empty")
                record_finding("NarrativeBrief assembler did not capture multi-target "
                               "despite multiple hp_changed events")
            elif len(hp_events) <= 1:
                record_pass("C5: Multi-target NarrativeBrief",
                            f"Only {len(hp_events)} target(s) hit — multi-target not applicable")
                if len(affected) > 1 and len(hp_events) <= 1:
                    record_finding(f"spell_cast affected {len(affected)} entities but "
                                   f"only {len(hp_events)} hp_changed events emitted")

        # C7-C8: Generate narration
        try:
            from aidm.narration.narrator import NarrationTemplates
            template = NarrationTemplates.get_template(narration_token, brief.severity)
            actor_name = brief.actor_name
            target_name = brief.target_name or "the targets"
            damage = 0
            for event in turn_result.events:
                if event.event_type == "hp_changed" and event.payload.get("delta", 0) < 0:
                    damage = abs(event.payload.get("delta", 0))
                    break

            try:
                narration_text = template.format(
                    actor=actor_name, target=target_name,
                    weapon="fireball", damage=damage,
                )
            except KeyError:
                narration_text = template

            print(f"  Narration: {narration_text!r}")
            result["narration_text"] = narration_text

            # Does it reference multiple targets?
            refs_multi = any(g["name"] in narration_text for g in goblins)
            print(f"  References multiple targets by name: {refs_multi}")
            if not refs_multi and len(brief.additional_targets) > 0:
                record_finding("Template narration only references primary target; "
                               "multi-target narration requires LLM or custom template")

            record_pass("C7: Template narration (multi-target)")
        except Exception as exc:
            record_fail("C7: Template narration (multi-target)", str(exc), error=str(exc))

        SCENARIO_RESULTS["C"] = "PASS"
        return result

    except Exception as exc:
        record_fail("C: Multi-target spell scenario", str(exc),
                     module=traceback.format_exc().splitlines()[-2] if traceback.format_exc() else "",
                     error=str(exc))
        traceback.print_exc()
        SCENARIO_RESULTS["C"] = "FAIL"
        record_finding(f"Scenario C crashed: {exc}")
        return None


# ══════════════════════════════════════════════════════════════════════════
# SCENARIO D: Condition Spell + NarrationValidator
# ══════════════════════════════════════════════════════════════════════════

def scenario_d_condition_validator() -> Optional[Dict[str, Any]]:
    """Scenario D: Hold Person on humanoid. Exercises condition path + NarrationValidator."""
    banner("SCENARIO D: Condition Spell + NarrationValidator")
    result: Dict[str, Any] = {}

    try:
        from aidm.data.spell_definitions import SPELL_REGISTRY, get_spell
        from aidm.schemas.entity_fields import EF
        from aidm.core.play_loop import execute_turn, TurnContext
        from aidm.core.spell_resolver import SpellCastIntent
        from aidm.core.state import WorldState, FrozenWorldStateView
        from aidm.core.rng_manager import RNGManager
        from aidm.lens.narrative_brief import NarrativeBrief, assemble_narrative_brief

        # D1: Check if hold_person exists in SPELL_REGISTRY
        if "hold_person" not in SPELL_REGISTRY:
            print("  hold_person not in SPELL_REGISTRY — skipping Scenario D")
            record_pass("D1: Check SPELL_REGISTRY", "hold_person not found")
            SCENARIO_RESULTS["D"] = "SKIPPED"
            record_finding("No condition-applying spell available for Scenario D")
            return None

        hold_person = get_spell("hold_person")
        print(f"  Spell: {hold_person.name} (level {hold_person.level}, "
              f"save={hold_person.save_type.value}, "
              f"conditions={hold_person.conditions_on_fail})")
        print(f"  content_id: {hold_person.content_id!r}")
        record_pass("D1: Load Hold Person",
                     f"conditions_on_fail={hold_person.conditions_on_fail}")

        # D2: Create caster and humanoid target
        caster = {
            EF.ENTITY_ID: "wizard_d",
            "name": "Morwen the Enchantress",
            EF.HP_CURRENT: 28,
            EF.HP_MAX: 28,
            EF.AC: 13,
            EF.ATTACK_BONUS: 2,
            EF.BAB: 2,
            EF.STR_MOD: 0,
            EF.DEX_MOD: 1,
            EF.INT_MOD: 3,
            EF.CON_MOD: 1,
            EF.WIS_MOD: 2,
            EF.CHA_MOD: 1,
            EF.SAVE_FORT: 2,
            EF.SAVE_REF: 2,
            EF.SAVE_WILL: 6,
            EF.TEAM: "party",
            EF.WEAPON: "quarterstaff",
            EF.POSITION: {"x": 5, "y": 5},
            EF.DEFEATED: False,
            EF.SIZE_CATEGORY: "medium",
            EF.BASE_SPEED: 30,
            EF.CONDITIONS: {},
            "caster_level": 5,
            "spell_dc_base": 15,  # 10 + INT(3) + spell level(3) – note: DC set here
            "spells_prepared": ["hold_person"],
        }

        bandit = {
            EF.ENTITY_ID: "bandit_1",
            "name": "Bandit Lieutenant",
            EF.HP_CURRENT: 18,
            EF.HP_MAX: 18,
            EF.AC: 16,
            EF.ATTACK_BONUS: 5,
            EF.BAB: 3,
            EF.STR_MOD: 2,
            EF.DEX_MOD: 1,
            EF.INT_MOD: 0,
            EF.CON_MOD: 1,
            EF.WIS_MOD: 0,
            EF.CHA_MOD: 0,
            EF.SAVE_FORT: 4,
            EF.SAVE_REF: 2,
            EF.SAVE_WILL: 1,  # Low Will save — likely to fail
            EF.TEAM: "monsters",
            EF.WEAPON: "longsword",
            EF.POSITION: {"x": 10, "y": 5},
            EF.DEFEATED: False,
            EF.SIZE_CATEGORY: "medium",
            EF.BASE_SPEED: 30,
            EF.CONDITIONS: {},
        }
        print(f"  Caster: {caster['name']} (DC base {caster['spell_dc_base']})")
        print(f"  Target: {bandit['name']} (Will save +{bandit[EF.SAVE_WILL]})")
        record_pass("D2: Create entities")

        # D3: Cast Hold Person
        entities = {
            caster[EF.ENTITY_ID]: caster,
            bandit[EF.ENTITY_ID]: bandit,
        }
        world_state = WorldState(
            ruleset_version="3.5e",
            entities=entities,
            active_combat={
                "round_index": 1,
                "turn_counter": 0,
                "initiative_order": ["wizard_d", "bandit_1"],
                "flat_footed_actors": [],
                "aoo_used_this_round": [],
                "duration_tracker": {"effects": []},
            },
        )

        rng = RNGManager(master_seed=55)

        intent = SpellCastIntent(
            caster_id="wizard_d",
            spell_id="hold_person",
            target_entity_id="bandit_1",
        )

        turn_ctx = TurnContext(
            turn_index=0,
            actor_id="wizard_d",
            actor_team="party",
        )

        print(f"  Intent: Cast Hold Person on {bandit['name']}")

        turn_result = execute_turn(
            world_state=world_state,
            turn_ctx=turn_ctx,
            combat_intent=intent,
            rng=rng,
            next_event_id=0,
            timestamp=1.0,
        )
        result["turn_result"] = turn_result

        # D4: Print events
        print(f"  Status: {turn_result.status}")
        print(f"  Narration token: {turn_result.narration}")
        print(f"  Events emitted: {len(turn_result.events)}")
        for event in turn_result.events:
            print(f"    {event.event_type}: {event.payload}")

        event_types = [e.event_type for e in turn_result.events]
        has_condition = "condition_applied" in event_types
        has_spell_cast = "spell_cast" in event_types

        # D5: Check content_id in condition_applied event
        condition_event_content_id = None
        for event in turn_result.events:
            if event.event_type == "condition_applied":
                condition_event_content_id = event.payload.get("content_id")
                print(f"  condition_applied content_id: {condition_event_content_id!r}")
        if not has_condition:
            print("  No condition_applied event — target may have saved")

        if turn_result.status == "ok":
            if has_condition:
                record_pass("D3: Cast Hold Person",
                            f"condition_applied, narration={turn_result.narration}")
            else:
                record_pass("D3: Cast Hold Person",
                            f"target resisted (saved), narration={turn_result.narration}")
                record_finding("Hold Person: target saved — condition path not fully exercised. "
                               "Re-run with different seed for full coverage.")
        else:
            record_fail("D3: Cast Hold Person",
                        f"status={turn_result.status}: {turn_result.failure_reason}")

        # D6: Assemble NarrativeBrief
        frozen_view = FrozenWorldStateView(turn_result.world_state)
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

        narration_token = turn_result.narration or "spell_debuff_applied"
        brief = assemble_narrative_brief(
            events=event_dicts,
            narration_token=narration_token,
            frozen_view=frozen_view,
        )
        result["brief"] = brief

        print(f"  NarrativeBrief:")
        print(f"    actor_name: {brief.actor_name}")
        print(f"    target_name: {brief.target_name}")
        print(f"    condition_applied: {brief.condition_applied}")
        print(f"    spell_name: {brief.spell_name}")
        print(f"    active_conditions on target: {brief.active_conditions}")

        if has_condition:
            if brief.condition_applied:
                record_pass("D6: NarrativeBrief captures condition",
                            f"condition={brief.condition_applied}")
            else:
                record_fail("D6: NarrativeBrief captures condition",
                            "condition_applied event exists but brief.condition_applied is None")
                record_finding("NarrativeBrief assembler did not extract condition from event")
        else:
            record_pass("D6: NarrativeBrief (no condition — target saved)")

        # D7: Attempt NarrationValidator
        try:
            from aidm.narration.narration_validator import NarrationValidator

            # Generate narration text for validation
            from aidm.narration.narrator import NarrationTemplates
            template = NarrationTemplates.get_template(narration_token, brief.severity)
            actor_name = brief.actor_name
            target_name = brief.target_name or "the target"
            try:
                narration_text = template.format(
                    actor=actor_name, target=target_name,
                    weapon="spell", damage=0,
                )
            except KeyError:
                narration_text = template

            print(f"  Narration text for validation: {narration_text!r}")

            validator = NarrationValidator()
            validation_result = validator.validate(narration_text, brief)

            print(f"  NarrationValidator verdict: {validation_result.verdict}")
            print(f"  Violations: {len(validation_result.violations)}")
            for v in validation_result.violations:
                print(f"    {v.rule_id} [{v.severity}]: {v.detail}")

            result["validation_result"] = validation_result

            record_pass("D7: NarrationValidator invocation",
                        f"verdict={validation_result.verdict}, "
                        f"violations={len(validation_result.violations)}")

        except ImportError as exc:
            record_fail("D7: NarrationValidator invocation",
                        f"import failed: {exc}", error=str(exc))
            record_finding(f"NarrationValidator not importable: {exc}")
        except Exception as exc:
            record_fail("D7: NarrationValidator invocation",
                        str(exc), error=str(exc))
            record_finding(f"NarrationValidator invocation failed: {exc}")
            traceback.print_exc()

        SCENARIO_RESULTS["D"] = "PASS"
        return result

    except Exception as exc:
        record_fail("D: Condition spell scenario", str(exc),
                     module=traceback.format_exc().splitlines()[-2] if traceback.format_exc() else "",
                     error=str(exc))
        traceback.print_exc()
        SCENARIO_RESULTS["D"] = "FAIL"
        record_finding(f"Scenario D crashed: {exc}")
        return None


# ══════════════════════════════════════════════════════════════════════════
# SCENARIO E: Self-Buff Spell — Shield on self
# ══════════════════════════════════════════════════════════════════════════

def scenario_e_self_buff() -> Optional[Dict[str, Any]]:
    """Scenario E: Cast Shield on self. Exercises non-damage, SELF-targeted spell path."""
    banner("SCENARIO E: Self-Buff — Shield on Self")
    result: Dict[str, Any] = {}

    try:
        from aidm.data.spell_definitions import SPELL_REGISTRY, get_spell
        from aidm.schemas.entity_fields import EF
        from aidm.core.play_loop import execute_turn, TurnContext
        from aidm.core.spell_resolver import SpellCastIntent
        from aidm.core.state import WorldState, FrozenWorldStateView
        from aidm.core.rng_manager import RNGManager
        from aidm.lens.narrative_brief import assemble_narrative_brief

        # E1: Check if shield exists
        if "shield" not in SPELL_REGISTRY:
            print("  'shield' not in SPELL_REGISTRY — skipping Scenario E")
            SCENARIO_RESULTS["E"] = "SKIPPED"
            record_finding("Shield spell not in SPELL_REGISTRY for self-buff test")
            return None

        shield = get_spell("shield")
        print(f"  Spell: {shield.name} (level {shield.level}, target={shield.target_type.value}, "
              f"effect={shield.effect_type.value})")
        print(f"  conditions_on_success: {shield.conditions_on_success}")
        record_pass("E1: Load Shield spell")

        # E2: Create wizard (needs a buff, in a fight)
        wizard = {
            EF.ENTITY_ID: "wizard_e",
            "name": "Thalric the Wary",
            EF.HP_CURRENT: 20,
            EF.HP_MAX: 20,
            EF.AC: 12,
            EF.ATTACK_BONUS: 2,
            EF.BAB: 2,
            EF.STR_MOD: -1,
            EF.DEX_MOD: 2,
            EF.INT_MOD: 4,
            EF.CON_MOD: 0,
            EF.WIS_MOD: 1,
            EF.CHA_MOD: 0,
            EF.SAVE_FORT: 1,
            EF.SAVE_REF: 3,
            EF.SAVE_WILL: 5,
            EF.TEAM: "party",
            EF.WEAPON: "dagger",
            EF.POSITION: {"x": 5, "y": 5},
            EF.DEFEATED: False,
            EF.SIZE_CATEGORY: "medium",
            EF.BASE_SPEED: 30,
            EF.CONDITIONS: {},
            "caster_level": 5,
            "spell_dc_base": 14,
            "spells_prepared": ["shield"],
        }
        # Need a second entity for valid combat state
        dummy = {
            EF.ENTITY_ID: "orc_e",
            "name": "Orc Berserker",
            EF.HP_CURRENT: 12,
            EF.HP_MAX: 12,
            EF.AC: 13,
            EF.ATTACK_BONUS: 5,
            EF.BAB: 2,
            EF.STR_MOD: 3,
            EF.DEX_MOD: 0,
            EF.INT_MOD: -1,
            EF.CON_MOD: 2,
            EF.WIS_MOD: 0,
            EF.CHA_MOD: -1,
            EF.SAVE_FORT: 4,
            EF.SAVE_REF: 0,
            EF.SAVE_WILL: 0,
            EF.TEAM: "monsters",
            EF.WEAPON: "greataxe",
            EF.POSITION: {"x": 10, "y": 5},
            EF.DEFEATED: False,
            EF.SIZE_CATEGORY: "medium",
            EF.BASE_SPEED: 30,
            EF.CONDITIONS: {},
        }
        print(f"  Caster: {wizard['name']} (AC {wizard[EF.AC]})")
        record_pass("E2: Create entities")

        # E3: Cast Shield on self
        entities = {
            wizard[EF.ENTITY_ID]: wizard,
            dummy[EF.ENTITY_ID]: dummy,
        }
        world_state = WorldState(
            ruleset_version="3.5e",
            entities=entities,
            active_combat={
                "round_index": 1,
                "turn_counter": 0,
                "initiative_order": ["wizard_e", "orc_e"],
                "flat_footed_actors": [],
                "aoo_used_this_round": [],
                "duration_tracker": {"effects": []},
            },
        )

        rng = RNGManager(master_seed=33)

        intent = SpellCastIntent(
            caster_id="wizard_e",
            spell_id="shield",
        )

        turn_ctx = TurnContext(
            turn_index=0,
            actor_id="wizard_e",
            actor_team="party",
        )

        print(f"  Intent: Cast Shield (self-targeted)")

        turn_result = execute_turn(
            world_state=world_state,
            turn_ctx=turn_ctx,
            combat_intent=intent,
            rng=rng,
            next_event_id=0,
            timestamp=1.0,
        )
        result["turn_result"] = turn_result

        print(f"  Status: {turn_result.status}")
        print(f"  Narration token: {turn_result.narration}")
        print(f"  Events emitted: {len(turn_result.events)}")
        for event in turn_result.events:
            print(f"    {event.event_type}: {event.payload}")

        event_types = [e.event_type for e in turn_result.events]
        has_spell_cast = "spell_cast" in event_types
        has_condition = "condition_applied" in event_types

        # Check if shield condition was applied to caster
        shield_on_caster = False
        for event in turn_result.events:
            if event.event_type == "condition_applied":
                if event.payload.get("entity_id") == "wizard_e":
                    shield_on_caster = True
                    print(f"  Shield condition applied to caster: YES")

        if turn_result.status == "ok":
            if has_condition and shield_on_caster:
                record_pass("E3: Cast Shield on self",
                            f"narration={turn_result.narration}, condition applied to caster")
            elif has_spell_cast and not has_condition:
                record_pass("E3: Cast Shield on self",
                            f"spell_cast emitted but no condition_applied (possible resolver gap)")
                record_finding("Self-buff spell cast succeeded but no condition_applied event "
                               "— buff conditions may not be applied by spell resolver")
            else:
                record_pass("E3: Cast Shield on self", f"narration={turn_result.narration}")
        else:
            record_fail("E3: Cast Shield on self",
                        f"status={turn_result.status}: {turn_result.failure_reason}")

        # E4: Assemble NarrativeBrief
        frozen_view = FrozenWorldStateView(turn_result.world_state)
        event_dicts = [{
            "event_id": e.event_id, "type": e.event_type,
            "event_type": e.event_type, "timestamp": e.timestamp,
            "payload": e.payload, "citations": e.citations,
        } for e in turn_result.events]

        narration_token = turn_result.narration or "spell_buff_applied"
        brief = assemble_narrative_brief(
            events=event_dicts, narration_token=narration_token, frozen_view=frozen_view,
        )
        result["brief"] = brief

        print(f"  NarrativeBrief:")
        print(f"    actor_name: {brief.actor_name}")
        print(f"    target_name: {brief.target_name}")
        print(f"    spell_name: {brief.spell_name}")
        print(f"    condition_applied: {brief.condition_applied}")
        print(f"    outcome_summary: {brief.outcome_summary}")

        # For self-buff, actor and target should be the same entity
        if brief.actor_name and brief.target_name:
            same_entity = brief.actor_name == brief.target_name
            print(f"  Actor == Target (self-buff): {same_entity}")
            if not same_entity:
                record_finding(f"Self-buff: actor_name={brief.actor_name!r} != "
                               f"target_name={brief.target_name!r} — expected same entity")

        record_pass("E4: NarrativeBrief (self-buff)",
                     f"actor={brief.actor_name}, spell={brief.spell_name}")

        SCENARIO_RESULTS["E"] = "PASS"
        return result

    except Exception as exc:
        record_fail("E: Self-buff scenario", str(exc),
                     module=traceback.format_exc().splitlines()[-2] if traceback.format_exc() else "",
                     error=str(exc))
        traceback.print_exc()
        SCENARIO_RESULTS["E"] = "FAIL"
        record_finding(f"Scenario E crashed: {exc}")
        return None


# ══════════════════════════════════════════════════════════════════════════
# SCENARIO F: Healing Spell — Cure Light Wounds on injured ally
# ══════════════════════════════════════════════════════════════════════════

def scenario_f_healing() -> Optional[Dict[str, Any]]:
    """Scenario F: Heal injured ally. Exercises healing event path + narration."""
    banner("SCENARIO F: Healing — Cure Light Wounds on Injured Ally")
    result: Dict[str, Any] = {}

    try:
        from aidm.data.spell_definitions import SPELL_REGISTRY, get_spell
        from aidm.schemas.entity_fields import EF
        from aidm.core.play_loop import execute_turn, TurnContext
        from aidm.core.spell_resolver import SpellCastIntent
        from aidm.core.state import WorldState, FrozenWorldStateView
        from aidm.core.rng_manager import RNGManager
        from aidm.lens.narrative_brief import assemble_narrative_brief

        if "cure_light_wounds" not in SPELL_REGISTRY:
            print("  'cure_light_wounds' not in SPELL_REGISTRY — skipping Scenario F")
            SCENARIO_RESULTS["F"] = "SKIPPED"
            record_finding("Cure Light Wounds not in SPELL_REGISTRY")
            return None

        clw = get_spell("cure_light_wounds")
        print(f"  Spell: {clw.name} (level {clw.level}, healing_dice={clw.healing_dice})")
        record_pass("F1: Load Cure Light Wounds")

        # F2: Create cleric and injured fighter
        cleric = {
            EF.ENTITY_ID: "cleric_f",
            "name": "Brother Aldric",
            EF.HP_CURRENT: 30,
            EF.HP_MAX: 30,
            EF.AC: 18,
            EF.ATTACK_BONUS: 4,
            EF.BAB: 3,
            EF.STR_MOD: 1,
            EF.DEX_MOD: 0,
            EF.INT_MOD: 0,
            EF.CON_MOD: 2,
            EF.WIS_MOD: 3,
            EF.CHA_MOD: 1,
            EF.SAVE_FORT: 5,
            EF.SAVE_REF: 1,
            EF.SAVE_WILL: 6,
            EF.TEAM: "party",
            EF.WEAPON: "mace",
            EF.POSITION: {"x": 5, "y": 5},
            EF.DEFEATED: False,
            EF.SIZE_CATEGORY: "medium",
            EF.BASE_SPEED: 30,
            EF.CONDITIONS: {},
            "caster_level": 5,
            "spell_dc_base": 13,
            "spells_prepared": ["cure_light_wounds"],
        }

        injured_fighter = {
            EF.ENTITY_ID: "fighter_f",
            "name": "Wounded Kael",
            EF.HP_CURRENT: 8,   # Injured! (out of 40 max)
            EF.HP_MAX: 40,
            EF.AC: 17,
            EF.ATTACK_BONUS: 7,
            EF.BAB: 4,
            EF.STR_MOD: 3,
            EF.DEX_MOD: 1,
            EF.INT_MOD: 0,
            EF.CON_MOD: 2,
            EF.WIS_MOD: 1,
            EF.CHA_MOD: 0,
            EF.SAVE_FORT: 6,
            EF.SAVE_REF: 2,
            EF.SAVE_WILL: 2,
            EF.TEAM: "party",
            EF.WEAPON: "longsword",
            EF.POSITION: {"x": 6, "y": 5},
            EF.DEFEATED: False,
            EF.SIZE_CATEGORY: "medium",
            EF.BASE_SPEED: 30,
            EF.CONDITIONS: {},
        }

        print(f"  Cleric: {cleric['name']} (CL {cleric['caster_level']})")
        print(f"  Patient: {injured_fighter['name']} (HP {injured_fighter[EF.HP_CURRENT]}/{injured_fighter[EF.HP_MAX]})")
        record_pass("F2: Create entities")

        # F3: Cast CLW on injured fighter
        entities = {
            cleric[EF.ENTITY_ID]: cleric,
            injured_fighter[EF.ENTITY_ID]: injured_fighter,
        }
        world_state = WorldState(
            ruleset_version="3.5e",
            entities=entities,
            active_combat={
                "round_index": 1,
                "turn_counter": 0,
                "initiative_order": ["cleric_f", "fighter_f"],
                "flat_footed_actors": [],
                "aoo_used_this_round": [],
                "duration_tracker": {"effects": []},
            },
        )

        rng = RNGManager(master_seed=44)

        intent = SpellCastIntent(
            caster_id="cleric_f",
            spell_id="cure_light_wounds",
            target_entity_id="fighter_f",
        )

        turn_ctx = TurnContext(
            turn_index=0,
            actor_id="cleric_f",
            actor_team="party",
        )

        print(f"  Intent: Cast Cure Light Wounds on {injured_fighter['name']}")

        turn_result = execute_turn(
            world_state=world_state,
            turn_ctx=turn_ctx,
            combat_intent=intent,
            rng=rng,
            next_event_id=0,
            timestamp=1.0,
        )
        result["turn_result"] = turn_result

        print(f"  Status: {turn_result.status}")
        print(f"  Narration token: {turn_result.narration}")
        print(f"  Events emitted: {len(turn_result.events)}")
        for event in turn_result.events:
            print(f"    {event.event_type}: {event.payload}")

        # Check for positive hp_changed (healing)
        hp_events = [e for e in turn_result.events if e.event_type == "hp_changed"]
        healed = False
        for hp_e in hp_events:
            delta = hp_e.payload.get("delta", 0)
            if delta > 0:
                healed = True
                print(f"  Healing: {hp_e.payload.get('entity_id')} "
                      f"{hp_e.payload.get('old_hp')} → {hp_e.payload.get('new_hp')} "
                      f"(+{delta})")

        if turn_result.status == "ok":
            if healed:
                record_pass("F3: Cast Cure Light Wounds",
                            f"healed! narration={turn_result.narration}")
            else:
                record_pass("F3: Cast Cure Light Wounds",
                            f"no hp_changed with positive delta — narration={turn_result.narration}")
                if not hp_events:
                    record_finding("Healing spell cast OK but no hp_changed event emitted")
        else:
            record_fail("F3: Cast Cure Light Wounds",
                        f"status={turn_result.status}: {turn_result.failure_reason}")

        # F4: NarrativeBrief
        frozen_view = FrozenWorldStateView(turn_result.world_state)
        event_dicts = [{
            "event_id": e.event_id, "type": e.event_type,
            "event_type": e.event_type, "timestamp": e.timestamp,
            "payload": e.payload, "citations": e.citations,
        } for e in turn_result.events]

        narration_token = turn_result.narration or "spell_healed"
        brief = assemble_narrative_brief(
            events=event_dicts, narration_token=narration_token, frozen_view=frozen_view,
        )
        result["brief"] = brief

        print(f"  NarrativeBrief:")
        print(f"    actor_name: {brief.actor_name}")
        print(f"    target_name: {brief.target_name}")
        print(f"    spell_name: {brief.spell_name}")
        print(f"    outcome_summary: {brief.outcome_summary}")
        print(f"    severity: {brief.severity}")

        record_pass("F4: NarrativeBrief (healing)")

        SCENARIO_RESULTS["F"] = "PASS"
        return result

    except Exception as exc:
        record_fail("F: Healing scenario", str(exc),
                     module=traceback.format_exc().splitlines()[-2] if traceback.format_exc() else "",
                     error=str(exc))
        traceback.print_exc()
        SCENARIO_RESULTS["F"] = "FAIL"
        record_finding(f"Scenario F crashed: {exc}")
        return None


# ══════════════════════════════════════════════════════════════════════════
# SCENARIO G: Edge Case — Spell at already-defeated entity
# ══════════════════════════════════════════════════════════════════════════

def scenario_g_spell_on_dead() -> Optional[Dict[str, Any]]:
    """Scenario G: Cast spell at defeated target. Verifies AoE skips defeated entities."""
    banner("SCENARIO G: Edge Case — AoE Skips Defeated Entity")
    result: Dict[str, Any] = {}

    try:
        from aidm.schemas.entity_fields import EF
        from aidm.core.play_loop import execute_turn, TurnContext
        from aidm.core.spell_resolver import SpellCastIntent
        from aidm.schemas.position import Position
        from aidm.core.state import WorldState
        from aidm.core.rng_manager import RNGManager

        # G1: Create caster and already-defeated goblin
        caster = {
            EF.ENTITY_ID: "wizard_g",
            "name": "Overkill Ollie",
            EF.HP_CURRENT: 30,
            EF.HP_MAX: 30,
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
            EF.POSITION: {"x": 5, "y": 5},
            EF.DEFEATED: False,
            EF.SIZE_CATEGORY: "medium",
            EF.BASE_SPEED: 30,
            EF.CONDITIONS: {},
            "caster_level": 5,
            "spell_dc_base": 13,
            "spells_prepared": ["fireball"],
        }

        dead_goblin = {
            EF.ENTITY_ID: "dead_goblin_g",
            "name": "Very Dead Goblin",
            EF.HP_CURRENT: -5,
            EF.HP_MAX: 5,
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
            EF.TEAM: "monsters",
            EF.WEAPON: "shortbow",
            EF.POSITION: {"x": 10, "y": 10},
            EF.DEFEATED: True,  # Already defeated!
            EF.SIZE_CATEGORY: "small",
            EF.BASE_SPEED: 30,
            EF.CONDITIONS: {},
        }

        print(f"  Caster: {caster['name']}")
        print(f"  Target: {dead_goblin['name']} (HP {dead_goblin[EF.HP_CURRENT]}, DEFEATED={dead_goblin[EF.DEFEATED]})")
        record_pass("G1: Create entities (one defeated)")

        # G2: Cast fireball at dead goblin's position (AoE — should still fire)
        entities = {
            caster[EF.ENTITY_ID]: caster,
            dead_goblin[EF.ENTITY_ID]: dead_goblin,
        }
        world_state = WorldState(
            ruleset_version="3.5e",
            entities=entities,
            active_combat={
                "round_index": 1,
                "turn_counter": 0,
                "initiative_order": ["wizard_g", "dead_goblin_g"],
                "flat_footed_actors": [],
                "aoo_used_this_round": [],
                "duration_tracker": {"effects": []},
            },
        )

        rng = RNGManager(master_seed=66)

        # AoE spell at the dead goblin's position — interesting: AoE doesn't validate individual targets
        intent = SpellCastIntent(
            caster_id="wizard_g",
            spell_id="fireball",
            target_position=Position(x=10, y=10),
        )

        turn_ctx = TurnContext(
            turn_index=0,
            actor_id="wizard_g",
            actor_team="party",
        )

        print(f"  Intent: Fireball at ({intent.target_position.x}, {intent.target_position.y}) "
              f"— targeting defeated goblin's position")

        turn_result = execute_turn(
            world_state=world_state,
            turn_ctx=turn_ctx,
            combat_intent=intent,
            rng=rng,
            next_event_id=0,
            timestamp=1.0,
        )
        result["turn_result"] = turn_result

        print(f"  Status: {turn_result.status}")
        print(f"  Narration token: {turn_result.narration}")
        print(f"  Events: {len(turn_result.events)}")
        for event in turn_result.events:
            print(f"    {event.event_type}: {event.payload}")

        # Verify defeated entity was NOT re-damaged (WO-AOE-DEFEATED-FILTER)
        hp_events = [e for e in turn_result.events if e.event_type == "hp_changed"]
        re_damaged = any(e.payload.get("entity_id") == "dead_goblin_g" for e in hp_events)
        double_defeat = any(
            e.event_type == "entity_defeated" and e.payload.get("entity_id") == "dead_goblin_g"
            for e in turn_result.events
        )

        print(f"  Defeated entity re-damaged: {re_damaged}")
        print(f"  Double entity_defeated event: {double_defeat}")

        if turn_result.status == "ok" and not re_damaged:
            record_pass("G2: Fireball at dead goblin position",
                        f"status=ok, dead goblin correctly skipped")
        elif turn_result.status == "ok" and re_damaged:
            record_fail("G2: Fireball at dead goblin position",
                        "AoE still damaged defeated entity",
                        error="Defeated entity filter not working")
        else:
            record_pass("G2: Fireball at dead goblin position",
                        f"rejected: {turn_result.failure_reason}")

        SCENARIO_RESULTS["G"] = "PASS" if not re_damaged else "FAIL"
        return result

    except Exception as exc:
        record_fail("G: Spell-on-dead scenario", str(exc),
                     module=traceback.format_exc().splitlines()[-2] if traceback.format_exc() else "",
                     error=str(exc))
        traceback.print_exc()
        SCENARIO_RESULTS["G"] = "FAIL"
        record_finding(f"Scenario G crashed: {exc}")
        return None


# ══════════════════════════════════════════════════════════════════════════
# SCENARIO H: Sequential Actions — melee then spell in same session
# ══════════════════════════════════════════════════════════════════════════

def scenario_h_sequential() -> Optional[Dict[str, Any]]:
    """Scenario H: Two combat turns in sequence. Tests event accumulation + state mutation."""
    banner("SCENARIO H: Sequential Actions — Melee then Spell")
    result: Dict[str, Any] = {}

    try:
        from aidm.schemas.entity_fields import EF
        from aidm.schemas.attack import Weapon, AttackIntent
        from aidm.core.play_loop import execute_turn, TurnContext
        from aidm.core.spell_resolver import SpellCastIntent
        from aidm.schemas.position import Position
        from aidm.core.state import WorldState, FrozenWorldStateView
        from aidm.core.rng_manager import RNGManager
        from aidm.lens.narrative_brief import assemble_narrative_brief
        from aidm.narration.narration_validator import NarrationValidator
        from aidm.narration.narrator import NarrationTemplates

        # H1: Create 3 entities — fighter, wizard, and a tough ogre
        fighter = {
            EF.ENTITY_ID: "fighter_h",
            "name": "Sir Brennan",
            EF.HP_CURRENT: 45,
            EF.HP_MAX: 45,
            EF.AC: 18,
            EF.ATTACK_BONUS: 8,
            EF.BAB: 5,
            EF.STR_MOD: 3,
            EF.DEX_MOD: 1,
            EF.INT_MOD: 0,
            EF.CON_MOD: 2,
            EF.WIS_MOD: 1,
            EF.CHA_MOD: 1,
            EF.SAVE_FORT: 6,
            EF.SAVE_REF: 2,
            EF.SAVE_WILL: 2,
            EF.TEAM: "party",
            EF.WEAPON: "greatsword",
            EF.POSITION: {"x": 5, "y": 5},
            EF.DEFEATED: False,
            EF.SIZE_CATEGORY: "medium",
            EF.BASE_SPEED: 30,
            EF.CONDITIONS: {},
        }
        wizard = {
            EF.ENTITY_ID: "wizard_h",
            "name": "Elara the Evoker",
            EF.HP_CURRENT: 28,
            EF.HP_MAX: 28,
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
            EF.POSITION: {"x": 3, "y": 5},
            EF.DEFEATED: False,
            EF.SIZE_CATEGORY: "medium",
            EF.BASE_SPEED: 30,
            EF.CONDITIONS: {},
            "caster_level": 5,
            "spell_dc_base": 13,
            "spells_prepared": ["fireball"],
        }
        ogre = {
            EF.ENTITY_ID: "ogre_h",
            "name": "Groknak the Immovable",
            EF.HP_CURRENT: 50,
            EF.HP_MAX: 50,
            EF.AC: 16,
            EF.ATTACK_BONUS: 8,
            EF.BAB: 4,
            EF.STR_MOD: 5,
            EF.DEX_MOD: -1,
            EF.INT_MOD: -2,
            EF.CON_MOD: 3,
            EF.WIS_MOD: 0,
            EF.CHA_MOD: -1,
            EF.SAVE_FORT: 7,
            EF.SAVE_REF: 0,
            EF.SAVE_WILL: 1,
            EF.TEAM: "monsters",
            EF.WEAPON: "greatclub",
            EF.POSITION: {"x": 6, "y": 5},  # Adjacent to fighter
            EF.DEFEATED: False,
            EF.SIZE_CATEGORY: "large",
            EF.BASE_SPEED: 30,
            EF.CONDITIONS: {},
        }

        print(f"  Fighter: {fighter['name']} at ({fighter[EF.POSITION]['x']},{fighter[EF.POSITION]['y']})")
        print(f"  Wizard:  {wizard['name']} at ({wizard[EF.POSITION]['x']},{wizard[EF.POSITION]['y']})")
        print(f"  Ogre:    {ogre['name']} HP {ogre[EF.HP_CURRENT]}/{ogre[EF.HP_MAX]} "
              f"at ({ogre[EF.POSITION]['x']},{ogre[EF.POSITION]['y']})")
        record_pass("H1: Create 3-entity combat")

        entities = {
            fighter[EF.ENTITY_ID]: fighter,
            wizard[EF.ENTITY_ID]: wizard,
            ogre[EF.ENTITY_ID]: ogre,
        }
        world_state = WorldState(
            ruleset_version="3.5e",
            entities=entities,
            active_combat={
                "round_index": 1,
                "turn_counter": 0,
                "initiative_order": ["fighter_h", "wizard_h", "ogre_h"],
                "flat_footed_actors": [],
                "aoo_used_this_round": [],
                "duration_tracker": {"effects": []},
            },
        )
        rng = RNGManager(master_seed=88)

        # H2: Turn 1 — Fighter attacks ogre with greatsword
        greatsword = Weapon(
            damage_dice="2d6",
            damage_bonus=0,
            damage_type="slashing",
            critical_multiplier=2,
            critical_range=19,
            grip="two-handed",
            weapon_type="two-handed",
            is_two_handed=True,
        )
        attack_intent = AttackIntent(
            attacker_id="fighter_h",
            target_id="ogre_h",
            attack_bonus=fighter[EF.ATTACK_BONUS],
            weapon=greatsword,
        )
        turn_ctx_1 = TurnContext(turn_index=0, actor_id="fighter_h", actor_team="party")

        print(f"\n  === TURN 1: Fighter attacks Ogre ===")
        turn_result_1 = execute_turn(
            world_state=world_state, turn_ctx=turn_ctx_1,
            combat_intent=attack_intent, rng=rng,
            next_event_id=0, timestamp=1.0,
        )
        result["turn_result_1"] = turn_result_1

        print(f"  Status: {turn_result_1.status}, narration: {turn_result_1.narration}")
        ogre_hp_after_melee = None
        for event in turn_result_1.events:
            if event.event_type == "hp_changed":
                ogre_hp_after_melee = event.payload.get("new_hp")
                print(f"  Ogre HP: {event.payload.get('old_hp')} → {ogre_hp_after_melee}")

        if turn_result_1.status == "ok":
            record_pass("H2: Turn 1 — Fighter attacks ogre",
                        f"narration={turn_result_1.narration}")
        else:
            record_fail("H2: Turn 1 — Fighter attacks ogre",
                        f"status={turn_result_1.status}")

        # H3: Turn 2 — Wizard casts fireball at ogre (using updated state!)
        updated_state = turn_result_1.world_state

        spell_intent = SpellCastIntent(
            caster_id="wizard_h",
            spell_id="fireball",
            target_position=Position(x=6, y=5),  # Ogre position
        )
        turn_ctx_2 = TurnContext(turn_index=1, actor_id="wizard_h", actor_team="party")

        print(f"\n  === TURN 2: Wizard casts Fireball at Ogre ===")
        turn_result_2 = execute_turn(
            world_state=updated_state, turn_ctx=turn_ctx_2,
            combat_intent=spell_intent, rng=rng,
            next_event_id=len(turn_result_1.events), timestamp=2.0,
        )
        result["turn_result_2"] = turn_result_2

        print(f"  Status: {turn_result_2.status}, narration: {turn_result_2.narration}")
        ogre_hp_after_spell = None
        for event in turn_result_2.events:
            if event.event_type == "hp_changed" and event.payload.get("entity_id") == "ogre_h":
                ogre_hp_after_spell = event.payload.get("new_hp")
                print(f"  Ogre HP: {event.payload.get('old_hp')} → {ogre_hp_after_spell}")
            if event.event_type == "entity_defeated":
                print(f"  DEFEATED: {event.payload.get('entity_id')}")

        if turn_result_2.status == "ok":
            record_pass("H3: Turn 2 — Wizard fireballs ogre",
                        f"narration={turn_result_2.narration}")
        else:
            record_fail("H3: Turn 2 — Wizard fireballs ogre",
                        f"status={turn_result_2.status}")

        # H4: Verify state continuity — ogre HP should reflect both hits
        ogre_state = turn_result_2.world_state.entities.get("ogre_h", {})
        final_hp = ogre_state.get(EF.HP_CURRENT, "???")
        defeated = ogre_state.get(EF.DEFEATED, False)
        print(f"\n  State continuity check:")
        print(f"    Ogre started: {ogre[EF.HP_CURRENT]}/{ogre[EF.HP_MAX]}")
        print(f"    After melee:  {ogre_hp_after_melee}")
        print(f"    After spell:  {ogre_hp_after_spell}")
        print(f"    Final state:  HP={final_hp}, defeated={defeated}")

        # Verify damage accumulated correctly
        if ogre_hp_after_spell is not None and final_hp != "???":
            if final_hp == ogre_hp_after_spell:
                record_pass("H4: State continuity verified",
                            f"sequential damage accumulated correctly, final HP={final_hp}")
            else:
                record_fail("H4: State continuity",
                            f"final HP mismatch: state says {final_hp}, event says {ogre_hp_after_spell}")
                record_finding("State continuity mismatch between world_state.entities and hp_changed event")
        else:
            record_pass("H4: State continuity", f"final HP={final_hp}, defeated={defeated}")

        # H5: Run NarrationValidator on the spell narration
        try:
            frozen_view = FrozenWorldStateView(turn_result_2.world_state)
            event_dicts = [{
                "event_id": e.event_id, "type": e.event_type,
                "event_type": e.event_type, "timestamp": e.timestamp,
                "payload": e.payload, "citations": e.citations,
            } for e in turn_result_2.events]

            narration_token = turn_result_2.narration or "spell_damage_dealt"
            brief = assemble_narrative_brief(
                events=event_dicts, narration_token=narration_token, frozen_view=frozen_view,
            )

            template = NarrationTemplates.get_template(narration_token, brief.severity)
            try:
                narration_text = template.format(
                    actor=brief.actor_name, target=brief.target_name or "the target",
                    weapon="fireball", damage=0,
                )
            except KeyError:
                narration_text = template

            validator = NarrationValidator()
            val_result = validator.validate(narration_text, brief)
            print(f"  NarrationValidator: {val_result.verdict} ({len(val_result.violations)} violations)")
            for v in val_result.violations:
                print(f"    {v.rule_id} [{v.severity}]: {v.detail}")

            record_pass("H5: NarrationValidator on sequential combat",
                        f"verdict={val_result.verdict}")
        except Exception as exc:
            record_fail("H5: NarrationValidator on sequential combat", str(exc), error=str(exc))

        SCENARIO_RESULTS["H"] = "PASS"
        return result

    except Exception as exc:
        record_fail("H: Sequential actions scenario", str(exc),
                     module=traceback.format_exc().splitlines()[-2] if traceback.format_exc() else "",
                     error=str(exc))
        traceback.print_exc()
        SCENARIO_RESULTS["H"] = "FAIL"
        record_finding(f"Scenario H crashed: {exc}")
        return None


# ══════════════════════════════════════════════════════════════════════════

