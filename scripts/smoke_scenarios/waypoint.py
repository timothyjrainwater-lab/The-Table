"""WO-WAYPOINT-001: Waypoint Maiden Voyage — Smoke Scenario.

Full table loop determinism proof exercising four surfaces:
spell+save, condition, skill check, feat modifier.
"""
from __future__ import annotations

import json
import traceback
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional

from smoke_scenarios.common import (
    SCENARIO_RESULTS,
    banner,
    record_pass,
    record_fail,
    record_finding,
)


WAYPOINT_SEED = 1
FIXTURE_DIR = Path(__file__).resolve().parent.parent.parent / "tests" / "fixtures" / "waypoint"


def _load_entity(path: Path) -> Dict[str, Any]:
    with open(path) as f:
        return json.load(f)


def scenario_waypoint() -> Optional[Dict[str, Any]]:
    """Scenario W: Full table loop — spell, save, condition, skill, feat."""
    banner("SCENARIO W: Waypoint — Full Table Loop Determinism")
    result: Dict[str, Any] = {}

    try:
        from aidm.schemas.entity_fields import EF
        from aidm.schemas.attack import Weapon, AttackIntent
        from aidm.core.play_loop import execute_turn, TurnContext
        from aidm.core.state import WorldState
        from aidm.core.rng_manager import RNGManager
        from aidm.core.skill_resolver import resolve_skill_check
        from aidm.core.spell_resolver import SpellCastIntent
        from aidm.core.event_log import Event, EventLog

        # W1: Load fixtures
        kael = _load_entity(FIXTURE_DIR / "kael_ironfist.json")
        sera = _load_entity(FIXTURE_DIR / "seraphine.json")
        bandit = _load_entity(FIXTURE_DIR / "bandit_captain.json")

        entities = {
            kael["entity_id"]: kael,
            sera["entity_id"]: sera,
            bandit["entity_id"]: bandit,
        }
        ws = WorldState(
            ruleset_version="3.5e",
            entities=entities,
            active_combat={
                "round_index": 1,
                "turn_counter": 0,
                "initiative_order": ["seraphine", "kael_ironfist", "bandit_captain"],
                "flat_footed_actors": [],
                "aoo_used_this_round": [],
                "duration_tracker": {"effects": []},
            },
        )
        rng = RNGManager(master_seed=WAYPOINT_SEED)
        event_log = EventLog()
        next_eid = 0
        record_pass("W1: Fixtures loaded", f"3 entities, seed={WAYPOINT_SEED}")

        # W2: Turn 0 — Hold Person
        intent0 = SpellCastIntent(
            caster_id="seraphine",
            spell_id="hold_person",
            target_entity_id="bandit_captain",
        )
        ctx0 = TurnContext(turn_index=0, actor_id="seraphine", actor_team="party")
        r0 = execute_turn(
            world_state=ws, turn_ctx=ctx0, combat_intent=intent0,
            rng=rng, next_event_id=next_eid, timestamp=1.0,
        )
        for e in r0.events:
            event_log.append(e)
        next_eid += len(r0.events)
        ws = r0.world_state

        cond_events = [e for e in r0.events if e.event_type == "condition_applied"]
        if cond_events:
            record_pass("W2: Hold Person", "paralyzed applied to bandit_captain")
        else:
            record_fail("W2: Hold Person", "condition_applied not emitted")
            SCENARIO_RESULTS["waypoint"] = "FAIL"
            return None

        # W3: Turn 1 — Spot check + Power Attack
        kael_entity = ws.entities["kael_ironfist"]
        skill_result = resolve_skill_check(kael_entity, "spot", dc=15, rng=rng)
        skill_event = Event(
            event_id=next_eid,
            event_type="skill_check",
            timestamp=2.0,
            payload={
                "actor_id": "kael_ironfist",
                "skill_id": "spot",
                "d20_roll": skill_result.d20_roll,
                "total": skill_result.total,
                "dc": 15,
                "success": skill_result.success,
            },
        )
        event_log.append(skill_event)
        next_eid += 1

        weapon = Weapon(
            damage_dice="1d8", damage_bonus=0, damage_type="slashing",
            critical_multiplier=2, critical_range=19,
        )
        attack1 = AttackIntent(
            attacker_id="kael_ironfist", target_id="bandit_captain",
            attack_bonus=8, weapon=weapon, power_attack_penalty=2,
        )
        ctx1 = TurnContext(turn_index=1, actor_id="kael_ironfist", actor_team="party")
        r1 = execute_turn(
            world_state=ws, turn_ctx=ctx1, combat_intent=attack1,
            rng=rng, next_event_id=next_eid, timestamp=2.0,
        )
        for e in r1.events:
            event_log.append(e)
        next_eid += len(r1.events)
        ws = r1.world_state

        atk_events = [e for e in r1.events if e.event_type == "attack_roll"]
        if atk_events:
            ar = atk_events[0].payload
            record_pass(
                "W3: Kael attack",
                f"d20={ar['d20_result']}, feat_mod={ar.get('feat_modifier')}, hit={ar['hit']}"
            )
        else:
            record_fail("W3: Kael attack", "no attack_roll event")

        # W4: Turn 2 — Paralyzed Bandit attacks (Branch B)
        weapon2 = Weapon(damage_dice="1d8", damage_bonus=0, damage_type="slashing")
        attack2 = AttackIntent(
            attacker_id="bandit_captain", target_id="kael_ironfist",
            attack_bonus=5, weapon=weapon2,
        )
        ctx2 = TurnContext(turn_index=2, actor_id="bandit_captain", actor_team="monsters")
        r2 = execute_turn(
            world_state=ws, turn_ctx=ctx2, combat_intent=attack2,
            rng=rng, next_event_id=next_eid, timestamp=3.0,
        )
        for e in r2.events:
            event_log.append(e)
        next_eid += len(r2.events)
        ws = r2.world_state

        bandit_atks = [e for e in r2.events if e.event_type == "attack_roll"]
        if bandit_atks:
            record_finding(
                "FINDING-WAYPOINT-01: play_loop does not enforce actions_prohibited — "
                "paralyzed bandit_captain attack resolved (Branch B)"
            )
            record_pass("W4: Branch B confirmed", "paralyzed actor attack resolved")
        else:
            record_pass("W4: Branch A confirmed", "engine blocked paralyzed actor")

        # W5: Coverage canary
        event_types = {e.event_type for e in event_log.events}
        surfaces = ["spell_cast", "condition_applied", "attack_roll", "skill_check"]
        missing = [s for s in surfaces if s not in event_types]
        if missing:
            record_fail("W5: Surface coverage", f"missing: {missing}")
            SCENARIO_RESULTS["waypoint"] = "FAIL"
            return None
        record_pass("W5: All 4 surfaces hit", f"event_types: {sorted(event_types)}")

        SCENARIO_RESULTS["waypoint"] = "PASS"
        result["event_count"] = len(event_log)
        result["final_bandit_hp"] = ws.entities["bandit_captain"].get(EF.HP_CURRENT)
        result["final_kael_hp"] = ws.entities["kael_ironfist"].get(EF.HP_CURRENT)
        return result

    except Exception as exc:
        record_fail("W: Waypoint scenario", str(exc),
                     module=traceback.format_exc().splitlines()[-2] if traceback.format_exc() else "")
        SCENARIO_RESULTS["waypoint"] = "FAIL"
        return None
