"""Generative spell fuzzer for smoke testing.

WO-SMOKE-FUZZER: Picks random spells from SPELL_REGISTRY and exercises the
full narration pipeline with randomized entities. Discovers integration gaps
that hand-authored scenarios miss.

Usage (standalone):
    python -m smoke_scenarios.fuzzer --fuzz-count 20 --fuzz-seed 42

Usage (from smoke_test.py):
    from smoke_scenarios.fuzzer import run_fuzz
    results = run_fuzz(fuzz_count=20, seed=42)
"""
from __future__ import annotations

import random
import traceback
from typing import Any, Dict, List

from smoke_scenarios.common import (
    EF,
    SPELL_REGISTRY,
    WorldState,
    RNGManager,
    SpellTarget,
    Position,
    FrozenWorldStateView,
    SpellCastIntent,
    TurnContext,
    execute_turn,
    assemble_narrative_brief,
    get_spell,
    FUZZ_RESULTS,
    NEW_FINDINGS,
    banner,
    record_finding,
    make_caster,
    make_target,
    make_world_state,
)


# Name pools for generated entities
CASTER_NAMES = [
    "Aldric the Wise", "Selene Duskmantle", "Theron Ironquill",
    "Mira Starweave", "Gideon the Grey", "Lyra Flameheart",
    "Orin Shadowcast", "Nessa Brightstaff",
]

TARGET_NAMES = [
    "Goblin Scout", "Orc Warrior", "Bandit Thug", "Kobold Trapper",
    "Skeleton Archer", "Dire Wolf", "Zombie Hulk", "Giant Spider",
    "Gnoll Hunter", "Hobgoblin Captain", "Bugbear Lurker", "Ogre Brute",
]


def _make_fuzz_caster(
    entity_id: str,
    name: str,
    spell_id: str,
    position: Dict[str, int],
    rng: random.Random,
) -> Dict[str, Any]:
    """Create a caster entity with randomized but valid stats."""
    return make_caster(
        entity_id=entity_id,
        name=name,
        hp=rng.randint(20, 50),
        position=position,
        caster_level=rng.randint(3, 10),
        spell_dc_base=rng.randint(12, 18),
        spells_prepared=[spell_id],
    )


def _make_fuzz_target(
    entity_id: str,
    name: str,
    position: Dict[str, int],
    rng: random.Random,
) -> Dict[str, Any]:
    """Create a target entity with randomized but valid stats."""
    hp = rng.randint(1, 100)
    target = make_target(
        entity_id=entity_id,
        name=name,
        hp=hp,
        position=position,
        size=rng.choice(["small", "medium", "large"]),
    )
    # Randomize saves beyond what make_target provides
    target[EF.SAVE_FORT] = rng.randint(0, 8)
    target[EF.SAVE_REF] = rng.randint(0, 8)
    target[EF.SAVE_WILL] = rng.randint(0, 8)
    return target


def _fuzz_one_spell(
    spell_id: str,
    iteration: int,
    rng: random.Random,
) -> Dict[str, Any]:
    """Run a single fuzz iteration for one spell. Returns structured result."""
    result: Dict[str, Any] = {
        "iteration": iteration,
        "spell_id": spell_id,
        "status": "PASS",
        "findings": [],
    }

    try:
        spell = get_spell(spell_id)
        result["spell_name"] = spell.name
        result["target_type"] = spell.target_type.value if spell.target_type else "none"

        # Determine target count based on spell type
        if spell.aoe_shape is not None:
            target_count = rng.randint(1, 4)
        elif spell.target_type in (SpellTarget.SELF,):
            target_count = 0
        else:
            target_count = 1

        result["target_count"] = target_count

        # Generate entities
        caster_name = rng.choice(CASTER_NAMES)
        caster_pos = {"x": 5, "y": 5}
        caster = _make_fuzz_caster(
            f"fuzz_caster_{iteration}",
            caster_name,
            spell_id,
            caster_pos,
            rng,
        )

        targets = []
        for t_idx in range(target_count):
            t_name = rng.choice(TARGET_NAMES)
            if spell.aoe_shape is not None:
                t_pos = {"x": 20 + t_idx, "y": 20}
            else:
                t_pos = {"x": 6 + t_idx, "y": 5}
            targets.append(_make_fuzz_target(
                f"fuzz_target_{iteration}_{t_idx}",
                t_name,
                t_pos,
                rng,
            ))

        # For SELF spells, still need a second entity for valid combat state
        if target_count == 0:
            targets.append(_make_fuzz_target(
                f"fuzz_dummy_{iteration}",
                "Dummy Bystander",
                {"x": 15, "y": 15},
                rng,
            ))

        # Build world state
        entities = {caster[EF.ENTITY_ID]: caster}
        for t in targets:
            entities[t[EF.ENTITY_ID]] = t

        world_state = make_world_state(entities)
        engine_rng = RNGManager(master_seed=rng.randint(1, 99999))

        # Build intent based on spell type
        intent_kwargs: Dict[str, Any] = {
            "caster_id": caster[EF.ENTITY_ID],
            "spell_id": spell_id,
        }

        if spell.aoe_shape is not None:
            if target_count > 0:
                pos = targets[0][EF.POSITION]
                intent_kwargs["target_position"] = Position(x=pos["x"], y=pos["y"])
            else:
                intent_kwargs["target_position"] = Position(x=10, y=10)
        elif spell.target_type == SpellTarget.SELF:
            intent_kwargs["target_entity_id"] = caster[EF.ENTITY_ID]
        elif target_count > 0:
            intent_kwargs["target_entity_id"] = targets[0][EF.ENTITY_ID]

        intent = SpellCastIntent(**intent_kwargs)

        turn_ctx = TurnContext(
            turn_index=0,
            actor_id=caster[EF.ENTITY_ID],
            actor_team="party",
        )

        # Execute
        turn_result = execute_turn(
            world_state=world_state,
            turn_ctx=turn_ctx,
            combat_intent=intent,
            rng=engine_rng,
            next_event_id=0,
            timestamp=1.0,
        )

        result["engine_status"] = turn_result.status
        result["narration_token"] = turn_result.narration
        result["event_count"] = len(turn_result.events)

        if turn_result.status != "ok":
            result["status"] = "FINDING"
            result["findings"].append(
                f"Engine returned status={turn_result.status}: "
                f"{turn_result.failure_reason}"
            )
            return result

        # Assemble NarrativeBrief
        updated_state = turn_result.world_state
        frozen = FrozenWorldStateView(updated_state)
        event_dicts = [
            {"event_id": e.event_id, "type": e.event_type,
             "event_type": e.event_type,
             "payload": e.payload, "timestamp": e.timestamp,
             "citations": getattr(e, "citations", [])}
            for e in turn_result.events
        ]
        brief = assemble_narrative_brief(
            events=event_dicts,
            narration_token=turn_result.narration,
            frozen_view=frozen,
        )
        result["brief_populated"] = True

        # Validate NarrativeBrief fields
        if brief.spell_name is None:
            result["findings"].append("brief.spell_name is None")
        if brief.actor_name is None:
            result["findings"].append("brief.actor_name is None")

        if spell.damage_dice and not brief.damage_type:
            result["findings"].append(
                f"spell has damage_dice={spell.damage_dice} but "
                f"brief.damage_type is None"
            )

        conditions = spell.conditions_on_fail or spell.conditions_on_success
        if conditions and not brief.condition_applied:
            has_cond_event = any(
                e.event_type == "condition_applied" for e in turn_result.events
            )
            if has_cond_event:
                result["findings"].append(
                    f"condition_applied event exists but "
                    f"brief.condition_applied is None"
                )

        # Generate template narration
        try:
            from aidm.narration.narrator import NarrationTemplates
            template = NarrationTemplates.get_template(
                turn_result.narration, brief.severity
            )
            narration_text = template.format(
                actor=brief.actor_name or "the caster",
                target=brief.target_name or "the target",
                weapon=brief.spell_name or spell_id,
                damage=0,
            )
            result["narration_text"] = narration_text

            if not narration_text or not narration_text.strip():
                result["findings"].append("narration text is empty")
        except KeyError:
            result["narration_text"] = f"[no template for token: {turn_result.narration}]"
        except Exception as exc:
            result["findings"].append(f"narration generation failed: {exc}")

        # Run NarrationValidator if available
        try:
            from aidm.narration.narration_validator import NarrationValidator
            validator = NarrationValidator()
            narr_text = result.get("narration_text", "")
            if narr_text:
                validation = validator.validate(narr_text, brief)
                result["validator_verdict"] = validation.verdict
                if validation.verdict == "FAIL":
                    result["findings"].append(
                        f"NarrationValidator FAIL: "
                        f"{[v.detail for v in validation.violations]}"
                    )
        except ImportError:
            pass
        except Exception as exc:
            result["findings"].append(f"validator error: {exc}")

        if result["findings"]:
            result["status"] = "FINDING"

    except Exception as exc:
        result["status"] = "CRASH"
        result["error"] = str(exc)
        result["traceback"] = traceback.format_exc()

    return result


def run_fuzz(fuzz_count: int = 20, seed: int = 42) -> List[Dict[str, Any]]:
    """Run the generative fuzzer. Returns list of per-scenario results."""
    banner(f"GENERATIVE FUZZER — {fuzz_count} random spells (seed={seed})")

    rng = random.Random(seed)
    spell_ids = list(SPELL_REGISTRY.keys())

    results: List[Dict[str, Any]] = []

    for i in range(fuzz_count):
        spell_id = rng.choice(spell_ids)
        result = _fuzz_one_spell(spell_id, i, rng)
        results.append(result)
        FUZZ_RESULTS.append(result)

        # Print per-scenario summary
        status_tag = result["status"]
        spell_name = result.get("spell_name", spell_id)
        target_type = result.get("target_type", "?")
        target_count = result.get("target_count", 0)
        event_count = result.get("event_count", 0)

        detail = f"[{status_tag}] #{i:02d} {spell_name:<25} " \
                 f"({target_type}, {target_count}T, {event_count}ev)"

        if result["status"] == "PASS":
            print(f"  {detail}")
        elif result["status"] == "FINDING":
            print(f"  {detail}")
            for finding in result.get("findings", []):
                finding_msg = f"Fuzz #{i} {spell_name}: {finding}"
                print(f"    -> {finding_msg}")
                record_finding(finding_msg)
        elif result["status"] == "CRASH":
            print(f"  {detail}")
            error = result.get("error", "unknown")
            finding_msg = f"Fuzz #{i} {spell_name}: CRASH — {error}"
            print(f"    -> {finding_msg}")
            record_finding(finding_msg)

    # Summary
    passed = sum(1 for r in results if r["status"] == "PASS")
    findings = sum(1 for r in results if r["status"] == "FINDING")
    crashes = sum(1 for r in results if r["status"] == "CRASH")

    print()
    print(f"  Fuzzer summary: {passed} PASS, {findings} FINDING, "
          f"{crashes} CRASH out of {fuzz_count}")

    return results
