"""Generative spell fuzzer for smoke testing.

WO-SMOKE-FUZZER: Picks random spells from SPELL_REGISTRY and exercises the
full narration pipeline with randomized entities. Discovers integration gaps
that hand-authored scenarios miss.

WO-FUZZER-DETERMINISM-GATES: Adds provable reproducibility — ScenarioID
hashes, event log digests, FUZZ RECEIPT, stop-on-first-failure, and replay.

Usage (standalone):
    python -m smoke_scenarios.fuzzer --fuzz-count 20 --fuzz-seed 42
    python -m smoke_scenarios.fuzzer --fuzz-seed 42 --collect-all
    python -m smoke_scenarios.fuzzer --fuzz-seed 42 --replay abc12345

Usage (from smoke_test.py):
    from smoke_scenarios.fuzzer import run_fuzz
    results = run_fuzz(fuzz_count=20, seed=42)
"""
from __future__ import annotations

import hashlib
import json
import random
import traceback
from typing import Any, Dict, List, Optional

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


def _compute_hash(data: Any) -> str:
    """Compute sha256 hex digest of canonical JSON."""
    return hashlib.sha256(
        json.dumps(data, sort_keys=True).encode()
    ).hexdigest()


def _build_scenario_spec(
    spell_id: str,
    iteration: int,
    caster_name: str,
    caster_hp: int,
    caster_level: int,
    spell_dc_base: int,
    caster_pos: Dict[str, int],
    target_specs: List[Dict[str, Any]],
    engine_seed: int,
) -> Dict[str, Any]:
    """Build the canonical scenario spec dict for hashing.

    Includes all randomized input parameters. Does NOT include runtime
    results (events, damage rolls).
    """
    return {
        "spell_id": spell_id,
        "iteration": iteration,
        "caster": {
            "name": caster_name,
            "hp": caster_hp,
            "caster_level": caster_level,
            "spell_dc_base": spell_dc_base,
            "position": caster_pos,
        },
        "targets": target_specs,
        "engine_seed": engine_seed,
    }


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

        # Generate caster — capture randomized values for spec
        caster_name = rng.choice(CASTER_NAMES)
        caster_pos = {"x": 5, "y": 5}
        caster_hp = rng.randint(20, 50)
        caster_level = rng.randint(3, 10)
        spell_dc_base = rng.randint(12, 18)
        caster = make_caster(
            entity_id=f"fuzz_caster_{iteration}",
            name=caster_name,
            hp=caster_hp,
            position=caster_pos,
            caster_level=caster_level,
            spell_dc_base=spell_dc_base,
            spells_prepared=[spell_id],
        )

        # Generate targets — capture randomized values for spec
        targets = []
        target_specs = []
        for t_idx in range(target_count):
            t_name = rng.choice(TARGET_NAMES)
            if spell.aoe_shape is not None:
                t_pos = {"x": 20 + t_idx, "y": 20}
            else:
                t_pos = {"x": 6 + t_idx, "y": 5}
            t_hp = rng.randint(1, 100)
            t_size = rng.choice(["small", "medium", "large"])
            t_fort = rng.randint(0, 8)
            t_ref = rng.randint(0, 8)
            t_will = rng.randint(0, 8)
            target = make_target(
                entity_id=f"fuzz_target_{iteration}_{t_idx}",
                name=t_name,
                hp=t_hp,
                position=t_pos,
                size=t_size,
            )
            target[EF.SAVE_FORT] = t_fort
            target[EF.SAVE_REF] = t_ref
            target[EF.SAVE_WILL] = t_will
            targets.append(target)
            target_specs.append({
                "name": t_name,
                "hp": t_hp,
                "position": t_pos,
                "size": t_size,
                "save_fort": t_fort,
                "save_ref": t_ref,
                "save_will": t_will,
            })

        # For SELF spells, still need a second entity for valid combat state
        if target_count == 0:
            d_hp = rng.randint(1, 100)
            d_size = rng.choice(["small", "medium", "large"])
            d_fort = rng.randint(0, 8)
            d_ref = rng.randint(0, 8)
            d_will = rng.randint(0, 8)
            dummy = make_target(
                entity_id=f"fuzz_dummy_{iteration}",
                name="Dummy Bystander",
                hp=d_hp,
                position={"x": 15, "y": 15},
                size=d_size,
            )
            dummy[EF.SAVE_FORT] = d_fort
            dummy[EF.SAVE_REF] = d_ref
            dummy[EF.SAVE_WILL] = d_will
            targets.append(dummy)
            target_specs.append({
                "name": "Dummy Bystander",
                "hp": d_hp,
                "position": {"x": 15, "y": 15},
                "size": d_size,
                "save_fort": d_fort,
                "save_ref": d_ref,
                "save_will": d_will,
            })

        # Build world state
        entities = {caster[EF.ENTITY_ID]: caster}
        for t in targets:
            entities[t[EF.ENTITY_ID]] = t

        world_state = make_world_state(entities)
        engine_seed = rng.randint(1, 99999)
        engine_rng = RNGManager(master_seed=engine_seed)

        # ── ScenarioID (Change 1) ──────────────────────────────────────
        spec = _build_scenario_spec(
            spell_id=spell_id,
            iteration=iteration,
            caster_name=caster_name,
            caster_hp=caster_hp,
            caster_level=caster_level,
            spell_dc_base=spell_dc_base,
            caster_pos=caster_pos,
            target_specs=target_specs,
            engine_seed=engine_seed,
        )
        scenario_id = _compute_hash(spec)
        result["scenario_id"] = scenario_id

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

        # ── Event log digest (Change 2) ────────────────────────────────
        event_dicts = [
            {"event_id": e.event_id, "type": e.event_type,
             "event_type": e.event_type,
             "payload": e.payload, "timestamp": e.timestamp,
             "citations": getattr(e, "citations", [])}
            for e in turn_result.events
        ]
        # FINDING: payload.cast_id is uuid4() — not seeded by RNGManager.
        # Strip it for deterministic digest; raw digest stored separately.
        cleaned_events = []
        for ed in event_dicts:
            cleaned = dict(ed)
            if isinstance(cleaned.get("payload"), dict):
                cleaned["payload"] = {
                    k: v for k, v in cleaned["payload"].items()
                    if k != "cast_id"
                }
            cleaned_events.append(cleaned)
        event_digest = _compute_hash(cleaned_events)
        result["event_digest"] = event_digest
        result["event_digest_raw"] = _compute_hash(event_dicts)

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


def run_fuzz(
    fuzz_count: int = 20,
    seed: int = 42,
    collect_all: bool = False,
    replay_scenario_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Run the generative fuzzer. Returns list of per-scenario results.

    Args:
        fuzz_count: Number of random scenarios to generate.
        seed: RNG seed for reproducibility.
        collect_all: If False (default), stop on first failure. If True,
            continue past failures to collect all findings.
        replay_scenario_id: If provided, regenerate all scenarios but only
            execute the one matching this ScenarioID prefix or full hash.
    """
    if replay_scenario_id:
        banner(f"FUZZER REPLAY — seed={seed}, target={replay_scenario_id}")
    else:
        banner(f"GENERATIVE FUZZER — {fuzz_count} random spells (seed={seed})")

    rng = random.Random(seed)
    spell_ids = list(SPELL_REGISTRY.keys())

    results: List[Dict[str, Any]] = []
    all_scenario_ids: List[str] = []
    stopped_early = False

    for i in range(fuzz_count):
        spell_id = rng.choice(spell_ids)

        # ── Replay mode (Change 5) ─────────────────────────────────────
        # In replay mode, we must advance the RNG identically for every
        # scenario (so later ScenarioIDs are stable), but only execute the
        # matching one.
        if replay_scenario_id:
            # We need to generate the scenario to get its ScenarioID, but
            # _fuzz_one_spell consumes RNG. Save state, peek, decide.
            rng_state = rng.getstate()
            result = _fuzz_one_spell(spell_id, i, rng)
            sid = result.get("scenario_id", "")
            all_scenario_ids.append(sid)

            if sid.startswith(replay_scenario_id) or sid == replay_scenario_id:
                # This is the match — keep this result
                results.append(result)
                FUZZ_RESULTS.append(result)
                _print_scenario(i, result)
                print(f"  Replay matched ScenarioID {sid[:12]} at iteration {i}")
                break
            # Not a match — discard result, continue
            continue

        result = _fuzz_one_spell(spell_id, i, rng)
        results.append(result)
        FUZZ_RESULTS.append(result)

        scenario_id = result.get("scenario_id", "")
        all_scenario_ids.append(scenario_id)

        _print_scenario(i, result)

        # ── Stop-on-first-failure (Change 4) ───────────────────────────
        if result["status"] != "PASS" and not collect_all:
            print(f"\n  STOP: failure at iteration {i}, "
                  f"seed={seed}, ScenarioID={scenario_id[:12]}")
            for finding in result.get("findings", []):
                print(f"    -> {finding}")
            if result.get("error"):
                print(f"    -> CRASH: {result['error']}")
            stopped_early = True
            break

    # ── Replay miss ────────────────────────────────────────────────────
    if replay_scenario_id and not results:
        print(f"\n  ERROR: ScenarioID {replay_scenario_id} not found "
              f"for seed {seed} (searched {fuzz_count} scenarios)")
        return []

    # Summary
    passed = sum(1 for r in results if r["status"] == "PASS")
    findings = sum(1 for r in results if r["status"] == "FINDING")
    crashes = sum(1 for r in results if r["status"] == "CRASH")

    print()
    if replay_scenario_id:
        print(f"  Replay result: {results[0]['status']}")
    else:
        print(f"  Fuzzer summary: {passed} PASS, {findings} FINDING, "
              f"{crashes} CRASH out of {len(results)}"
              f"{' (stopped early)' if stopped_early else ''}")

    # ── FUZZ RECEIPT (Change 3) ────────────────────────────────────────
    if all_scenario_ids and not replay_scenario_id:
        run_digest = hashlib.sha256(
            "".join(all_scenario_ids).encode()
        ).hexdigest()
        first_id = all_scenario_ids[0][:8]
        last_id = all_scenario_ids[-1][:8]
        receipt = (
            f"FUZZ RECEIPT: seed={seed} count={len(results)} "
            f"first={first_id} last={last_id} "
            f"digest={run_digest[:12]}"
        )
        print(f"  {receipt}")

    return results


def _print_scenario(i: int, result: Dict[str, Any]) -> None:
    """Print per-scenario summary line."""
    status_tag = result["status"]
    spell_name = result.get("spell_name", result.get("spell_id", "?"))
    target_type = result.get("target_type", "?")
    target_count = result.get("target_count", 0)
    event_count = result.get("event_count", 0)
    sid = result.get("scenario_id", "????????")[:8]

    detail = (f"[{status_tag}] #{i:02d} {sid} {spell_name:<25} "
              f"({target_type}, {target_count}T, {event_count}ev)")

    print(f"  {detail}")
    if result["status"] in ("FINDING", "CRASH"):
        for finding in result.get("findings", []):
            finding_msg = f"Fuzz #{i} {spell_name}: {finding}"
            print(f"    -> {finding_msg}")
            record_finding(finding_msg)
        if result.get("error"):
            finding_msg = f"Fuzz #{i} {spell_name}: CRASH — {result['error']}"
            print(f"    -> {finding_msg}")
            record_finding(finding_msg)
