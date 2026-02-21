"""WO-WAYPOINT-003: Weapon Name Plumbing — Gate Tests.

Proves that the attack resolver passes actual weapon names into feat context
so weapon-specific feats (Weapon Focus, Weapon Specialization) match correctly.
Also verifies NarrativeBrief weapon_name extraction from attack events.

GATE TESTS:
  WP3-0: Weapon Focus fires with correct weapon name
  WP3-1: Weapon Focus does NOT fire for wrong weapon
  WP3-2: Power Attack still works (regression check)
  WP3-3: Combined feats — Weapon Focus + Power Attack
  WP3-4: NarrativeBrief weapon_name populated
  WP3-5: Waypoint scenario regression — Weapon Focus now active

CANONICAL FIELD NOTE:
  The attack_roll event payload uses `d20_result` (not `d20_roll`) as the
  canonical field name for the d20 attack roll value. This was established
  in CP-10 and confirmed in WO-WAYPOINT-001.
"""

from copy import deepcopy
from pathlib import Path
from typing import Any, Dict

import pytest

# ---------------------------------------------------------------------------
# Project imports
# ---------------------------------------------------------------------------
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from aidm.core.event_log import EventLog
from aidm.core.play_loop import execute_turn, TurnContext
from aidm.core.rng_manager import RNGManager
from aidm.core.state import WorldState, FrozenWorldStateView
from aidm.lens.narrative_brief import assemble_narrative_brief
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.entity_fields import EF

# ---------------------------------------------------------------------------
# Re-use Waypoint 001 fixtures and scenario
# ---------------------------------------------------------------------------
from tests.test_waypoint_001 import (
    build_initial_state,
    run_scenario,
    normalize_events,
    WAYPOINT_SEED,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_fighter_entity(
    entity_id: str = "test_fighter",
    weapon: str = "longsword",
    feats: list = None,
) -> Dict[str, Any]:
    """Create a fighter entity with weapon and feats."""
    return {
        "entity_id": entity_id,
        "name": "Test Fighter",
        EF.HP_CURRENT: 45,
        EF.HP_MAX: 45,
        "ac": 18,
        EF.ATTACK_BONUS: 8,
        EF.BAB: 5,
        EF.STR_MOD: 3,
        EF.DEX_MOD: 1,
        EF.TEAM: "party",
        EF.POSITION: {"x": 0, "y": 0},
        EF.DEFEATED: False,
        EF.CONDITIONS: {},
        EF.WEAPON: weapon,
        EF.FEATS: feats or [],
        EF.SIZE_CATEGORY: "medium",
        EF.BASE_SPEED: 30,
    }


def make_target_entity(entity_id: str = "target_dummy") -> Dict[str, Any]:
    """Create a minimal target entity."""
    return {
        "entity_id": entity_id,
        "name": "Target Dummy",
        EF.HP_CURRENT: 50,
        EF.HP_MAX: 50,
        "ac": 10,
        EF.ATTACK_BONUS: 0,
        EF.TEAM: "monsters",
        EF.POSITION: {"x": 5, "y": 0},
        EF.DEFEATED: False,
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.SIZE_CATEGORY: "medium",
        EF.BASE_SPEED: 30,
    }


def build_two_entity_state(
    actor: Dict[str, Any],
    target: Dict[str, Any],
) -> WorldState:
    """Build a WorldState with two entities."""
    return WorldState(
        ruleset_version="3.5e",
        entities={
            actor["entity_id"]: actor,
            target["entity_id"]: target,
        },
        active_combat={
            "round_index": 1,
            "turn_counter": 0,
            "aoo_used_this_round": [],
            "duration_tracker": {"effects": []},
        },
    )


def make_longsword() -> Weapon:
    """Create a standard longsword Weapon."""
    return Weapon(
        damage_dice="1d8",
        damage_bonus=0,
        damage_type="slashing",
        critical_multiplier=2,
        critical_range=19,  # Longsword 19-20/x2
    )


def run_attack(
    actor: Dict[str, Any],
    target: Dict[str, Any],
    weapon: Weapon = None,
    power_attack_penalty: int = 0,
    seed: int = 42,
):
    """Execute a single attack turn and return the TurnResult."""
    ws = build_two_entity_state(actor, target)
    rng = RNGManager(master_seed=seed)

    intent = AttackIntent(
        attacker_id=actor["entity_id"],
        target_id=target["entity_id"],
        attack_bonus=actor.get(EF.ATTACK_BONUS, 5),
        weapon=weapon or make_longsword(),
        power_attack_penalty=power_attack_penalty,
    )
    ctx = TurnContext(
        turn_index=0,
        actor_id=actor["entity_id"],
        actor_team=actor.get(EF.TEAM, "party"),
    )

    return execute_turn(
        world_state=ws,
        turn_ctx=ctx,
        combat_intent=intent,
        rng=rng,
        next_event_id=0,
        timestamp=1.0,
    )


def get_attack_roll_payload(result):
    """Extract the first attack_roll event payload from a TurnResult."""
    for e in result.events:
        if e.event_type == "attack_roll":
            return e.payload
    return None


# ===========================================================================
# WP3-0: Weapon Focus Fires With Correct Weapon Name
# ===========================================================================


class TestWP3_0_WeaponFocusFires:
    """Entity with weapon_focus_longsword wielding a longsword gets +1 attack."""

    def test_feat_context_has_real_weapon_name(self):
        """The attack_roll event payload weapon_name is the actual weapon, not 'unknown'."""
        actor = make_fighter_entity(
            weapon="longsword",
            feats=["weapon_focus_longsword"],
        )
        target = make_target_entity()
        result = run_attack(actor, target)

        payload = get_attack_roll_payload(result)
        assert payload is not None, "No attack_roll event emitted"
        assert payload.get("weapon_name") == "longsword", (
            f"Expected weapon_name='longsword', got '{payload.get('weapon_name')}'"
        )

    def test_weapon_focus_adds_plus_one(self):
        """feat_modifier includes +1 from Weapon Focus (longsword)."""
        actor = make_fighter_entity(
            weapon="longsword",
            feats=["weapon_focus_longsword"],
        )
        target = make_target_entity()
        result = run_attack(actor, target)

        payload = get_attack_roll_payload(result)
        assert payload is not None, "No attack_roll event emitted"
        feat_mod = payload.get("feat_modifier")
        assert feat_mod == 1, (
            f"Expected feat_modifier == 1 (Weapon Focus +1), got {feat_mod}"
        )

    def test_attack_total_includes_weapon_focus(self):
        """Total attack roll includes the Weapon Focus +1."""
        actor = make_fighter_entity(
            weapon="longsword",
            feats=["weapon_focus_longsword"],
        )
        target = make_target_entity()
        result = run_attack(actor, target)

        p = get_attack_roll_payload(result)
        assert p is not None
        computed = (
            p["d20_result"]
            + p["attack_bonus"]
            + p.get("condition_modifier", 0)
            + p.get("mounted_bonus", 0)
            + p.get("terrain_higher_ground", 0)
            + p.get("feat_modifier", 0)
            + p.get("flanking_bonus", 0)
        )
        assert p["total"] == computed, (
            f"attack_roll total mismatch: payload={p['total']}, computed={computed}"
        )


# ===========================================================================
# WP3-1: Weapon Focus Does NOT Fire for Wrong Weapon
# ===========================================================================


class TestWP3_1_WeaponFocusWrongWeapon:
    """Entity with weapon_focus_longsword wielding a greataxe should NOT get +1."""

    def test_no_weapon_focus_bonus(self):
        """feat_modifier should be 0 when weapon doesn't match feat."""
        actor = make_fighter_entity(
            weapon="greataxe",
            feats=["weapon_focus_longsword"],
        )
        target = make_target_entity()
        result = run_attack(actor, target)

        payload = get_attack_roll_payload(result)
        assert payload is not None, "No attack_roll event emitted"
        feat_mod = payload.get("feat_modifier")
        assert feat_mod == 0, (
            f"Expected feat_modifier == 0 (wrong weapon), got {feat_mod}"
        )

    def test_weapon_name_is_greataxe(self):
        """weapon_name in payload should be 'greataxe', not 'longsword' or 'unknown'."""
        actor = make_fighter_entity(
            weapon="greataxe",
            feats=["weapon_focus_longsword"],
        )
        target = make_target_entity()
        result = run_attack(actor, target)

        payload = get_attack_roll_payload(result)
        assert payload is not None
        assert payload.get("weapon_name") == "greataxe"


# ===========================================================================
# WP3-2: Power Attack Still Works (Regression Check)
# ===========================================================================


class TestWP3_2_PowerAttackRegression:
    """Power Attack must still function correctly after weapon_name fix."""

    def test_power_attack_penalty_in_feat_modifier(self):
        """feat_modifier includes -2 from Power Attack."""
        actor = make_fighter_entity(
            weapon="longsword",
            feats=["power_attack"],
        )
        target = make_target_entity()
        result = run_attack(actor, target, power_attack_penalty=2)

        payload = get_attack_roll_payload(result)
        assert payload is not None
        feat_mod = payload.get("feat_modifier")
        assert feat_mod == -2, (
            f"Expected feat_modifier == -2 (Power Attack), got {feat_mod}"
        )

    def test_power_attack_damage_if_hit(self):
        """If hit, damage_roll feat_modifier includes Power Attack bonus."""
        actor = make_fighter_entity(
            weapon="longsword",
            feats=["power_attack"],
        )
        target = make_target_entity()
        result = run_attack(actor, target, power_attack_penalty=2)

        # Check if attack hit
        ar = get_attack_roll_payload(result)
        if not ar or not ar.get("hit"):
            pytest.skip("Attack missed — damage proof conditional on hit")

        damage_rolls = [e for e in result.events if e.event_type == "damage_roll"]
        assert len(damage_rolls) >= 1, "No damage_roll event despite hit"

        feat_dmg = damage_rolls[0].payload.get("feat_modifier")
        # Power Attack penalty=2 → +2 damage (one-handed, 1:1 ratio)
        assert feat_dmg == 2, f"Expected damage feat_modifier == 2, got {feat_dmg}"


# ===========================================================================
# WP3-3: Combined Feats — Weapon Focus + Power Attack
# ===========================================================================


class TestWP3_3_CombinedFeats:
    """Both Weapon Focus +1 and Power Attack -2 fire simultaneously."""

    def test_combined_attack_modifier(self):
        """feat_modifier includes both Weapon Focus +1 and Power Attack -2 → net -1."""
        actor = make_fighter_entity(
            weapon="longsword",
            feats=["weapon_focus_longsword", "power_attack"],
        )
        target = make_target_entity()
        result = run_attack(actor, target, power_attack_penalty=2)

        payload = get_attack_roll_payload(result)
        assert payload is not None
        feat_mod = payload.get("feat_modifier")
        # Weapon Focus +1, Power Attack -2 → net -1
        assert feat_mod == -1, (
            f"Expected feat_modifier == -1 (WF+1 + PA-2), got {feat_mod}"
        )

    def test_combined_total_math(self):
        """Attack total = d20 + attack_bonus + feat_modifier + other_modifiers."""
        actor = make_fighter_entity(
            weapon="longsword",
            feats=["weapon_focus_longsword", "power_attack"],
        )
        target = make_target_entity()
        result = run_attack(actor, target, power_attack_penalty=2)

        p = get_attack_roll_payload(result)
        assert p is not None
        computed = (
            p["d20_result"]
            + p["attack_bonus"]
            + p.get("condition_modifier", 0)
            + p.get("mounted_bonus", 0)
            + p.get("terrain_higher_ground", 0)
            + p.get("feat_modifier", 0)
            + p.get("flanking_bonus", 0)
        )
        assert p["total"] == computed, (
            f"Total mismatch: payload={p['total']}, computed={computed}"
        )

    def test_weapon_name_in_payload(self):
        """weapon_name is 'longsword' even with combined feats."""
        actor = make_fighter_entity(
            weapon="longsword",
            feats=["weapon_focus_longsword", "power_attack"],
        )
        target = make_target_entity()
        result = run_attack(actor, target, power_attack_penalty=2)

        payload = get_attack_roll_payload(result)
        assert payload is not None
        assert payload.get("weapon_name") == "longsword"


# ===========================================================================
# WP3-4: NarrativeBrief Weapon Name Populated
# ===========================================================================


class TestWP3_4_NarrativeBriefWeaponName:
    """NarrativeBrief.weapon_name is populated from attack_roll event payload."""

    def test_brief_weapon_name_not_none(self):
        """weapon_name in NarrativeBrief is not None after an attack."""
        actor = make_fighter_entity(
            weapon="longsword",
            feats=["weapon_focus_longsword"],
        )
        target = make_target_entity()
        result = run_attack(actor, target)

        # Build frozen view for brief assembly
        ws = build_two_entity_state(actor, target)
        frozen_view = FrozenWorldStateView(ws)

        event_dicts = []
        for event in result.events:
            event_dicts.append({
                "event_id": event.event_id,
                "type": event.event_type,
                "event_type": event.event_type,
                "timestamp": event.timestamp,
                "payload": event.payload,
                "citations": event.citations,
            })

        narration_token = result.narration or "attack_hit"
        brief = assemble_narrative_brief(
            events=event_dicts,
            narration_token=narration_token,
            frozen_view=frozen_view,
        )

        assert brief.weapon_name is not None, (
            "NarrativeBrief.weapon_name is None — weapon_name not extracted from events"
        )

    def test_brief_weapon_name_matches(self):
        """weapon_name in NarrativeBrief matches the weapon used."""
        actor = make_fighter_entity(
            weapon="longsword",
            feats=["weapon_focus_longsword"],
        )
        target = make_target_entity()
        result = run_attack(actor, target)

        ws = build_two_entity_state(actor, target)
        frozen_view = FrozenWorldStateView(ws)

        event_dicts = []
        for event in result.events:
            event_dicts.append({
                "event_id": event.event_id,
                "type": event.event_type,
                "event_type": event.event_type,
                "timestamp": event.timestamp,
                "payload": event.payload,
                "citations": event.citations,
            })

        narration_token = result.narration or "attack_hit"
        brief = assemble_narrative_brief(
            events=event_dicts,
            narration_token=narration_token,
            frozen_view=frozen_view,
        )

        assert brief.weapon_name == "longsword", (
            f"Expected weapon_name='longsword', got '{brief.weapon_name}'"
        )


# ===========================================================================
# WP3-5: Waypoint Scenario Regression — Weapon Focus Now Active
# ===========================================================================


class TestWP3_5_WaypointRegression:
    """Re-run WO-WAYPOINT-001 scenario. Kael's Weapon Focus now fires."""

    def test_kael_feat_modifier_includes_weapon_focus(self):
        """Kael's attack_roll feat_modifier now includes both WF+1 and PA-2 → net -1.

        FINDING-WAYPOINT-02 is resolved: weapon_name is no longer 'unknown'.
        """
        _ws, event_log, _briefs = run_scenario()

        attack_rolls = [
            e for e in event_log.events
            if e.event_type == "attack_roll"
            and e.payload.get("attacker_id") == "kael_ironfist"
        ]
        assert len(attack_rolls) >= 1, "No attack_roll event from Kael"

        ar = attack_rolls[0].payload
        feat_mod = ar.get("feat_modifier")
        # Weapon Focus +1, Power Attack penalty 2 → -2 from PA + 1 from WF = -1
        assert feat_mod == -1, (
            f"Expected feat_modifier == -1 (WF+1 + PA-2), got {feat_mod}. "
            f"FINDING-WAYPOINT-02 not resolved."
        )

    def test_kael_weapon_name_is_longsword(self):
        """Kael's attack_roll payload shows weapon_name='longsword'."""
        _ws, event_log, _briefs = run_scenario()

        attack_rolls = [
            e for e in event_log.events
            if e.event_type == "attack_roll"
            and e.payload.get("attacker_id") == "kael_ironfist"
        ]
        assert len(attack_rolls) >= 1

        weapon_name = attack_rolls[0].payload.get("weapon_name")
        assert weapon_name == "longsword", (
            f"Expected weapon_name='longsword', got '{weapon_name}'"
        )

    def test_attack_roll_math_still_correct(self):
        """Total attack roll math is correct with the new feat modifier."""
        _ws, event_log, _briefs = run_scenario()

        attack_rolls = [
            e for e in event_log.events
            if e.event_type == "attack_roll"
            and e.payload.get("attacker_id") == "kael_ironfist"
        ]
        assert len(attack_rolls) >= 1

        p = attack_rolls[0].payload
        computed = (
            p["d20_result"]
            + p["attack_bonus"]
            + p.get("condition_modifier", 0)
            + p.get("mounted_bonus", 0)
            + p.get("terrain_higher_ground", 0)
            + p.get("feat_modifier", 0)
            + p.get("flanking_bonus", 0)
        )
        assert p["total"] == computed, (
            f"Total mismatch: payload={p['total']}, computed={computed}"
        )

    def test_all_existing_waypoint_gates_pass(self):
        """All W-0 event types still present (regression canary)."""
        _ws, event_log, _briefs = run_scenario()
        event_types = {e.event_type for e in event_log.events}

        assert "spell_cast" in event_types
        assert "condition_applied" in event_types
        assert "attack_roll" in event_types
        assert "skill_check" in event_types
        assert "action_denied" in event_types  # WO-WAYPOINT-002

    def test_turn1_brief_has_weapon_name(self):
        """Turn 1 NarrativeBrief now has weapon_name populated."""
        _ws, _log, briefs = run_scenario()
        brief1 = briefs[1]  # Turn 1 is Kael's attack
        weapon = brief1.get("weapon_name")
        assert weapon == "longsword", (
            f"Turn 1 brief weapon_name should be 'longsword', got: {weapon}"
        )

    def test_transcript_determinism(self):
        """Same seed → same NarrativeBriefs (W-3 regression)."""
        _ws1, _log1, briefs1 = run_scenario(seed=WAYPOINT_SEED, timestamp=1.0)
        _ws2, _log2, briefs2 = run_scenario(seed=WAYPOINT_SEED, timestamp=1.0)

        assert len(briefs1) == len(briefs2)
        for i, (b1, b2) in enumerate(zip(briefs1, briefs2)):
            assert b1 == b2, f"Brief for turn {i} differs between runs"

    def test_time_isolation(self):
        """Timestamps must not affect rule outcomes (W-4 regression)."""
        _ws1, log1, _b1 = run_scenario(seed=WAYPOINT_SEED, timestamp=1000.0)
        _ws2, log2, _b2 = run_scenario(seed=WAYPOINT_SEED, timestamp=9999.0)

        norm1 = normalize_events(log1.events)
        norm2 = normalize_events(log2.events)

        assert norm1 == norm2
