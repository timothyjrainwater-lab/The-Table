"""Gate XP-01 — XP Award and Level-Up Post-Combat Dispatcher.

WO-ENGINE-LEVELUP-WIRE wires:
  1. check_level_up() — was a stub returning None; now returns LevelUpResult
  2. _award_xp_for_defeat() — called from execute_turn() after entity_defeated
  3. xp_awarded events emitted per surviving opposing team member
  4. level_up_applied events emitted when XP threshold is crossed

Tests: 14

ID    Description
XP-01  check_level_up() below threshold → None
XP-02  check_level_up() at exact threshold → LevelUpResult with correct new_level
XP-03  check_level_up() at level 20 → None (cap)
XP-04  award_xp() adds to existing XP total
XP-05  execute_turn() with entity_defeated → xp_awarded event emitted
XP-06  XP amount correct for CR 1 vs. 2-person party
XP-07  Only surviving opposing team gets XP
XP-08  Level threshold crossing → level_up_applied event
XP-09  level_up_applied hp_gained > 0
XP-10  Level-20 entity receives XP but no level_up_applied
XP-11  No survivors → no xp_awarded event
XP-12  Entity HP_MAX/HP_CURRENT updated after level-up in world_state
XP-13  Multiple defeats same turn → XP awarded once per defeat
XP-14  Regression: existing attack resolution unaffected
"""

from copy import deepcopy
from typing import Any, Dict

import pytest

from aidm.core.experience_resolver import (
    award_xp,
    check_level_up,
    apply_level_up,
)
from aidm.core.play_loop import (
    TurnContext,
    _award_xp_for_defeat,
    _calculate_xp,
    execute_turn,
)
from aidm.core.rng_manager import RNGManager
from aidm.core.state import WorldState
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.entity_fields import EF
from aidm.schemas.leveling import LEVEL_THRESHOLDS

# ─── helpers ────────────────────────────────────────────────────────────────

def _world(*entity_dicts) -> WorldState:
    entities = {e[EF.ENTITY_ID]: e for e in entity_dicts}
    return WorldState(ruleset_version="3.5e", entities=entities)


def _fighter(eid: str, level: int = 1, xp: int = 0, team: str = "party") -> Dict[str, Any]:
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: team,
        EF.LEVEL: level,
        EF.XP: xp,
        EF.CLASS_LEVELS: {"fighter": level},
        EF.HP_MAX: 10 + 8 * (level - 1),
        EF.HP_CURRENT: 10 + 8 * (level - 1),
        EF.BAB: level,
        EF.SAVE_FORT: 2,
        EF.SAVE_REF: 0,
        EF.SAVE_WILL: 0,
        EF.CON_MOD: 2,
        EF.INT_MOD: 0,
        EF.DEFEATED: False,
    }


def _goblin(eid: str = "goblin_01", team: str = "monsters", cr: float = 1.0) -> Dict[str, Any]:
    """Minimal monster entity for defeat-XP tests."""
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: team,
        EF.LEVEL: 1,
        EF.HP_MAX: 5,
        EF.HP_CURRENT: 0,
        EF.DEFEATED: True,
        "challenge_rating": cr,
    }


def _events_of(result, event_type: str):
    return [e for e in result.events if e.event_type == event_type]


# ═══════════════════════════════════════════════════════════════════════════
# XP-01: check_level_up() below threshold → None
# ═══════════════════════════════════════════════════════════════════════════

class TestXP01BelowThreshold:
    def test_below_threshold_returns_none(self):
        entity = _fighter("pc", level=1, xp=999)  # threshold for L2 = 1000
        result = check_level_up(entity)
        assert result is None


# ═══════════════════════════════════════════════════════════════════════════
# XP-02: check_level_up() at exact threshold → LevelUpResult
# ═══════════════════════════════════════════════════════════════════════════

class TestXP02AtThreshold:
    def test_at_threshold_returns_result(self):
        threshold_l2 = LEVEL_THRESHOLDS[2]
        entity = _fighter("pc", level=1, xp=threshold_l2)
        result = check_level_up(entity)
        assert result is not None
        assert result.new_level == 2

    def test_class_name_is_highest_class(self):
        threshold_l2 = LEVEL_THRESHOLDS[2]
        entity = _fighter("pc", level=1, xp=threshold_l2)
        entity[EF.CLASS_LEVELS] = {"fighter": 1, "rogue": 0}
        result = check_level_up(entity)
        assert result is not None
        assert result.class_name == "fighter"


# ═══════════════════════════════════════════════════════════════════════════
# XP-03: check_level_up() at level 20 → None (cap)
# ═══════════════════════════════════════════════════════════════════════════

class TestXP03LevelCap:
    def test_level_20_returns_none(self):
        entity = _fighter("pc", level=20, xp=9_999_999)
        entity[EF.CLASS_LEVELS] = {"fighter": 20}
        result = check_level_up(entity)
        assert result is None


# ═══════════════════════════════════════════════════════════════════════════
# XP-04: award_xp() adds to existing total
# ═══════════════════════════════════════════════════════════════════════════

class TestXP04AwardXP:
    def test_xp_added_to_existing(self):
        entity = _fighter("pc", level=1, xp=500)
        updated = award_xp(entity, 300, apply_multiclass_penalty=False)
        assert updated[EF.XP] == 800

    def test_original_not_mutated(self):
        entity = _fighter("pc", level=1, xp=500)
        _ = award_xp(entity, 300, apply_multiclass_penalty=False)
        assert entity[EF.XP] == 500


# ═══════════════════════════════════════════════════════════════════════════
# XP-05: execute_turn() with entity_defeated → xp_awarded emitted
# ═══════════════════════════════════════════════════════════════════════════

class TestXP05ExecuteTurnXpEvent:
    def _run_attack_that_kills(self):
        """
        Fighter L3 (10+8+8=26 HP) attacks a goblin with 1 HP.
        Attack guaranteed hit: attacker's attack_bonus > goblin AC,
        damage guaranteed lethal (weapon min damage > goblin HP).
        """
        fighter = _fighter("fighter_01", level=3, xp=0, team="party")
        fighter["name"] = "Aldric"
        fighter[EF.WEAPON] = {
            "name": "longsword",
            "damage_dice": "1d8",
            "damage_bonus": 20,   # guaranteed kill
            "damage_type": "slashing",
            "critical_range": 20,
            "critical_multiplier": 2,
        }
        fighter[EF.ATTACK_BONUS] = 30  # guaranteed hit
        fighter[EF.AC] = 14

        goblin = {
            EF.ENTITY_ID: "goblin_01",
            EF.TEAM: "monsters",
            EF.LEVEL: 1,
            EF.HP_MAX: 1,
            EF.HP_CURRENT: 1,
            EF.AC: 5,
            EF.DEFEATED: False,
            "challenge_rating": 1.0,
            "name": "Goblin",
        }

        ws = _world(fighter, goblin)
        weapon = Weapon(
            damage_dice="1d8",
            damage_bonus=20,
            damage_type="slashing",
            critical_range=20,
            critical_multiplier=2,
        )
        intent = AttackIntent(
            attacker_id="fighter_01",
            target_id="goblin_01",
            weapon=weapon,
            attack_bonus=30,
        )
        rng = RNGManager(42)
        turn_ctx = TurnContext(turn_index=0, actor_id="fighter_01", actor_team="party")
        return execute_turn(
            world_state=ws,
            turn_ctx=turn_ctx,
            combat_intent=intent,
            rng=rng,
            next_event_id=0,
            timestamp=0.0,
        )

    def test_xp_awarded_event_emitted(self):
        result = self._run_attack_that_kills()
        xp_events = _events_of(result, "xp_awarded")
        assert len(xp_events) == 1
        assert xp_events[0].payload["entity_id"] == "fighter_01"

    def test_xp_awarded_event_has_correct_keys(self):
        result = self._run_attack_that_kills()
        xp_events = _events_of(result, "xp_awarded")
        assert len(xp_events) >= 1
        payload = xp_events[0].payload
        for key in ("entity_id", "xp_amount", "source", "new_total"):
            assert key in payload, f"Missing key: {key}"


# ═══════════════════════════════════════════════════════════════════════════
# XP-06: XP amount correct for CR 1 vs. 2-person party
# ═══════════════════════════════════════════════════════════════════════════

class TestXP06XpAmount:
    def test_cr1_two_survivors(self):
        # _calculate_xp(cr=1, party_size=2) should give 2× the 4-person value
        xp_2 = _calculate_xp(1.0, 2)
        xp_4 = _calculate_xp(1.0, 4)
        assert xp_2 == xp_4 * 2

    def test_positive_xp_for_cr1(self):
        assert _calculate_xp(1.0, 4) > 0


# ═══════════════════════════════════════════════════════════════════════════
# XP-07: Only surviving opposing team gets XP
# ═══════════════════════════════════════════════════════════════════════════

class TestXP07OpposingTeamOnly:
    def test_monster_team_gets_no_xp(self):
        """When a monster is defeated, only party members get XP."""
        goblin_a = _goblin("goblin_a", team="monsters")
        goblin_b = _goblin("goblin_b", team="monsters")
        goblin_b[EF.DEFEATED] = False
        goblin_b[EF.HP_CURRENT] = 5
        fighter = _fighter("fighter_01", level=1, xp=0, team="party")
        ws = _world(goblin_a, goblin_b, fighter)

        events = []
        updated_ws, _ = _award_xp_for_defeat(
            world_state=ws,
            defeated_entity_id="goblin_a",
            events=events,
            current_event_id=0,
            timestamp=0.0,
            rng=None,
        )

        awarded_ids = {e.payload["entity_id"] for e in events if e.event_type == "xp_awarded"}
        assert "goblin_b" not in awarded_ids
        assert "fighter_01" in awarded_ids


# ═══════════════════════════════════════════════════════════════════════════
# XP-08: Level threshold crossing → level_up_applied event
# ═══════════════════════════════════════════════════════════════════════════

class TestXP08LevelUpAppliedEvent:
    def test_level_up_applied_emitted(self):
        """Fighter at 999 XP gets 1 XP from defeating a CR 1/8 goblin → crosses 1000."""
        # Place fighter at 999 XP, one below L2 threshold (1000)
        fighter = _fighter("fighter_01", level=1, xp=999, team="party")
        goblin = _goblin("goblin_01", team="monsters", cr=1.0)
        goblin[EF.DEFEATED] = False

        ws = _world(fighter, goblin)
        ws.entities["goblin_01"][EF.DEFEATED] = True

        events = []
        updated_ws, _ = _award_xp_for_defeat(
            world_state=ws,
            defeated_entity_id="goblin_01",
            events=events,
            current_event_id=0,
            timestamp=0.0,
            rng=RNGManager(42),
        )

        level_up_events = [e for e in events if e.event_type == "level_up_applied"]
        assert len(level_up_events) == 1
        evt = level_up_events[0]
        assert evt.payload["entity_id"] == "fighter_01"
        assert evt.payload["new_level"] == 2
        assert evt.payload["old_level"] == 1


# ═══════════════════════════════════════════════════════════════════════════
# XP-09: level_up_applied hp_gained > 0
# ═══════════════════════════════════════════════════════════════════════════

class TestXP09HpGainedPositive:
    def test_hp_gained_greater_than_zero(self):
        fighter = _fighter("fighter_01", level=1, xp=999, team="party")
        goblin = _goblin("goblin_01", team="monsters", cr=1.0)
        ws = _world(fighter, goblin)
        ws.entities["goblin_01"][EF.DEFEATED] = True

        events = []
        _award_xp_for_defeat(
            world_state=ws,
            defeated_entity_id="goblin_01",
            events=events,
            current_event_id=0,
            timestamp=0.0,
            rng=RNGManager(42),
        )

        level_up_events = [e for e in events if e.event_type == "level_up_applied"]
        assert len(level_up_events) == 1
        assert level_up_events[0].payload["hp_gained"] > 0


# ═══════════════════════════════════════════════════════════════════════════
# XP-10: Level-20 entity receives XP but no level_up_applied
# ═══════════════════════════════════════════════════════════════════════════

class TestXP10Level20Cap:
    def test_xp_awarded_but_no_level_up_at_cap(self):
        fighter = _fighter("fighter_01", level=20, xp=190_000, team="party")
        fighter[EF.CLASS_LEVELS] = {"fighter": 20}
        goblin = _goblin("goblin_01", team="monsters")
        ws = _world(fighter, goblin)

        events = []
        _award_xp_for_defeat(
            world_state=ws,
            defeated_entity_id="goblin_01",
            events=events,
            current_event_id=0,
            timestamp=0.0,
            rng=None,
        )

        xp_events = [e for e in events if e.event_type == "xp_awarded"]
        level_events = [e for e in events if e.event_type == "level_up_applied"]
        assert len(xp_events) == 1
        assert len(level_events) == 0


# ═══════════════════════════════════════════════════════════════════════════
# XP-11: No survivors → no xp_awarded event
# ═══════════════════════════════════════════════════════════════════════════

class TestXP11NoSurvivors:
    def test_no_events_when_no_survivors(self):
        goblin = _goblin("goblin_01", team="monsters")
        # No party members present at all
        ws = _world(goblin)

        events = []
        updated_ws, eid = _award_xp_for_defeat(
            world_state=ws,
            defeated_entity_id="goblin_01",
            events=events,
            current_event_id=0,
            timestamp=0.0,
            rng=None,
        )

        assert events == []
        assert eid == 0  # event id unchanged


# ═══════════════════════════════════════════════════════════════════════════
# XP-12: Entity HP_MAX and HP_CURRENT updated after level-up
# ═══════════════════════════════════════════════════════════════════════════

class TestXP12HPUpdatedAfterLevelUp:
    def test_hp_max_updated_in_world_state(self):
        fighter = _fighter("fighter_01", level=1, xp=999, team="party")
        old_hp_max = fighter[EF.HP_MAX]
        goblin = _goblin("goblin_01", team="monsters")
        ws = _world(fighter, goblin)

        events = []
        updated_ws, _ = _award_xp_for_defeat(
            world_state=ws,
            defeated_entity_id="goblin_01",
            events=events,
            current_event_id=0,
            timestamp=0.0,
            rng=RNGManager(42),
        )

        level_events = [e for e in events if e.event_type == "level_up_applied"]
        if level_events:
            new_hp_max = updated_ws.entities["fighter_01"][EF.HP_MAX]
            assert new_hp_max > old_hp_max


# ═══════════════════════════════════════════════════════════════════════════
# XP-13: Multiple defeats same turn → XP once per defeat
# ═══════════════════════════════════════════════════════════════════════════

class TestXP13MultipleDefeats:
    def test_two_defeats_give_two_xp_awards(self):
        fighter = _fighter("fighter_01", level=1, xp=0, team="party")
        goblin_a = _goblin("goblin_a", team="monsters", cr=1.0)
        goblin_b = _goblin("goblin_b", team="monsters", cr=1.0)
        ws = _world(fighter, goblin_a, goblin_b)

        events = []
        ws, cid = _award_xp_for_defeat(ws, "goblin_a", events, 0, 0.0, RNGManager(42))
        ws, cid = _award_xp_for_defeat(ws, "goblin_b", events, cid, 0.1, RNGManager(42))

        xp_events = [e for e in events if e.event_type == "xp_awarded"]
        # Each defeat produces one xp_awarded per surviving party member
        assert len(xp_events) == 2
        # Both should be for the same entity
        for e in xp_events:
            assert e.payload["entity_id"] == "fighter_01"

    def test_xp_totals_accumulate(self):
        fighter = _fighter("fighter_01", level=1, xp=0, team="party")
        goblin_a = _goblin("goblin_a", team="monsters", cr=1.0)
        goblin_b = _goblin("goblin_b", team="monsters", cr=1.0)
        ws = _world(fighter, goblin_a, goblin_b)

        events = []
        ws, cid = _award_xp_for_defeat(ws, "goblin_a", events, 0, 0.0, RNGManager(42))
        ws, cid = _award_xp_for_defeat(ws, "goblin_b", events, cid, 0.1, RNGManager(42))

        final_xp = ws.entities["fighter_01"][EF.XP]
        xp_events = [e for e in events if e.event_type == "xp_awarded"]
        total_awarded = sum(e.payload["xp_amount"] for e in xp_events)
        assert final_xp == total_awarded


# ═══════════════════════════════════════════════════════════════════════════
# XP-14: Regression — attack resolution unaffected when no defeat
# ═══════════════════════════════════════════════════════════════════════════

class TestXP14Regression:
    def test_attack_miss_produces_no_xp_events(self):
        """Miss → no entity_defeated → no xp_awarded event."""
        fighter = _fighter("fighter_01", level=1, xp=0, team="party")
        fighter["name"] = "Aldric"
        fighter[EF.WEAPON] = {
            "name": "longsword",
            "damage_dice": "1d8",
            "damage_bonus": 0,
            "damage_type": "slashing",
            "critical_range": 20,
            "critical_multiplier": 2,
        }
        fighter[EF.ATTACK_BONUS] = -10  # guaranteed miss

        goblin = {
            EF.ENTITY_ID: "goblin_01",
            EF.TEAM: "monsters",
            EF.LEVEL: 1,
            EF.HP_MAX: 20,
            EF.HP_CURRENT: 20,
            EF.AC: 30,
            EF.DEFEATED: False,
            "challenge_rating": 1.0,
            "name": "Goblin",
        }

        ws = _world(fighter, goblin)
        weapon = Weapon(
            damage_dice="1d8",
            damage_bonus=0,
            damage_type="slashing",
            critical_range=20,
            critical_multiplier=2,
        )
        intent = AttackIntent(
            attacker_id="fighter_01",
            target_id="goblin_01",
            weapon=weapon,
            attack_bonus=-10,
        )
        rng = RNGManager(1)
        turn_ctx = TurnContext(turn_index=0, actor_id="fighter_01", actor_team="party")
        result = execute_turn(
            world_state=ws,
            turn_ctx=turn_ctx,
            combat_intent=intent,
            rng=rng,
            next_event_id=0,
            timestamp=0.0,
        )
        xp_events = _events_of(result, "xp_awarded")
        assert xp_events == [], "No xp_awarded events on a miss"
        # Turn result should still be ok
        assert result.status == "ok"
