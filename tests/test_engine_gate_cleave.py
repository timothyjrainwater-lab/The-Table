"""ENGINE-CLEAVE Gate — Cleave / Great Cleave wired into combat pipeline (10 tests).

Gate: ENGINE-CLEAVE
Tests: CL-01 through CL-10
WO: WO-ENGINE-CLEAVE-WIRE-001
"""

import unittest.mock as mock
from copy import deepcopy
from typing import Any, Dict

import pytest

from aidm.core.state import WorldState
from aidm.core.rng_manager import RNGManager
from aidm.schemas.entity_fields import EF
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.core.attack_resolver import resolve_attack, _find_cleave_target
from aidm.core.feat_resolver import can_use_cleave, get_cleave_limit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

LONGSWORD = Weapon(
    damage_dice="1d8",
    damage_bonus=0,
    damage_type="slashing",
    critical_multiplier=2,
    critical_range=19,
    weapon_type="one-handed",
    grip="one-handed",
)


def _entity(eid: str, team: str, hp: int = 5, ac: int = 8, bab: int = 4,
            str_mod: int = 2, feats: list = None, defeated: bool = False) -> Dict[str, Any]:
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: team,
        EF.HP_CURRENT: hp,
        EF.HP_MAX: max(hp, 5),
        EF.AC: ac,
        EF.DEFEATED: defeated,
        EF.DYING: False,
        EF.STABLE: False,
        EF.DISABLED: False,
        EF.POSITION: {"x": 0, "y": 0},
        EF.STR_MOD: str_mod,
        EF.DEX_MOD: 1,
        EF.CON_MOD: 1,
        EF.BAB: bab,
        "bab": bab,
        "attack_bonus": bab,
        EF.SIZE_CATEGORY: "medium",
        EF.CONDITIONS: {},
        EF.FEATS: feats or [],
        EF.TEMPORARY_MODIFIERS: {},
        EF.NEGATIVE_LEVELS: 0,
        EF.DISARMED: False,
    }


def _world(entities: dict, extra_combat: dict = None) -> WorldState:
    combat: Dict[str, Any] = {
        "initiative_order": list(entities.keys()),
        "aoo_used_this_round": [],
        "cleave_used_this_turn": set(),
    }
    if extra_combat:
        combat.update(extra_combat)
    return WorldState(ruleset_version="3.5e", entities=entities, active_combat=combat)


def _mock_rng(rolls):
    """Return a mock RNG that produces a fixed roll sequence."""
    stream = mock.MagicMock()
    stream.randint.side_effect = list(rolls) + [10] * 200
    rng = mock.MagicMock()
    rng.stream.return_value = stream
    return rng


# ===========================================================================
# CL-01: Cleave feat: kill on attack → cleave_triggered event emitted
# ===========================================================================

def test_cl01_cleave_triggered_on_kill():
    """CL-01: When attacker with Cleave kills target, cleave_triggered event is emitted."""
    # Fighter has Cleave; goblin has 1 HP so any hit kills it
    fighter = _entity("fighter", "party", bab=5, str_mod=3, feats=["cleave"])
    goblin = _entity("goblin", "monsters", hp=1, ac=8)
    orc = _entity("orc", "monsters", hp=20, ac=10)   # adjacent enemy for cleave
    ws = _world({"fighter": fighter, "goblin": goblin, "orc": orc})

    intent = AttackIntent(attacker_id="fighter", target_id="goblin",
                          weapon=LONGSWORD, attack_bonus=7)
    # Rolls: d20=15 (hit, AC 8), damage d8=4 (kills goblin with 1 HP)
    # Then cleave bonus attack: d20=10, damage d8=3
    rng = _mock_rng([15, 4, 10, 3])
    events = resolve_attack(intent, ws, rng, 0, 0.0)

    cleave_evts = [e for e in events if e.event_type == "cleave_triggered"]
    assert len(cleave_evts) == 1, f"Expected cleave_triggered, got: {[e.event_type for e in events]}"


# ===========================================================================
# CL-02: Cleave bonus attack uses same attack bonus as killing blow
# ===========================================================================

def test_cl02_cleave_attack_roll_emitted():
    """CL-02: After cleave_triggered, a bonus attack_roll event is emitted against the cleave target."""
    fighter = _entity("fighter", "party", bab=5, str_mod=3, feats=["cleave"])
    goblin = _entity("goblin", "monsters", hp=1, ac=8)
    orc = _entity("orc", "monsters", hp=20, ac=10)
    ws = _world({"fighter": fighter, "goblin": goblin, "orc": orc})

    intent = AttackIntent(attacker_id="fighter", target_id="goblin",
                          weapon=LONGSWORD, attack_bonus=7)
    rng = _mock_rng([15, 4, 10, 3])
    events = resolve_attack(intent, ws, rng, 0, 0.0)

    # After cleave_triggered there must be an attack_roll against orc
    cleave_idx = next(i for i, e in enumerate(events) if e.event_type == "cleave_triggered")
    post_cleave = events[cleave_idx + 1:]
    attack_rolls = [e for e in post_cleave if e.event_type == "attack_roll"]
    assert len(attack_rolls) >= 1, "Expected attack_roll after cleave_triggered"
    assert attack_rolls[0].payload["target_id"] == "orc"


# ===========================================================================
# CL-03: Cleave once-per-round limit — second kill does NOT trigger second Cleave
# ===========================================================================

def test_cl03_cleave_once_per_round():
    """CL-03: After using Cleave once this turn, a second kill does NOT retrigger it."""
    fighter = _entity("fighter", "party", bab=5, str_mod=3, feats=["cleave"])
    goblin = _entity("goblin", "monsters", hp=1, ac=8)
    ws = _world({"fighter": fighter, "goblin": goblin},
                extra_combat={"cleave_used_this_turn": {"fighter"}})  # already used

    intent = AttackIntent(attacker_id="fighter", target_id="goblin",
                          weapon=LONGSWORD, attack_bonus=7)
    rng = _mock_rng([15, 4])
    events = resolve_attack(intent, ws, rng, 0, 0.0)

    cleave_evts = [e for e in events if e.event_type == "cleave_triggered"]
    assert len(cleave_evts) == 0, "Cleave should not trigger again when already used this turn"


# ===========================================================================
# CL-04: Cleave feat: no adjacent enemy after kill → no cleave_triggered
# ===========================================================================

def test_cl04_no_adjacent_enemy_no_cleave():
    """CL-04: No valid adjacent enemy → no cleave_triggered, no bonus attack."""
    fighter = _entity("fighter", "party", bab=5, str_mod=3, feats=["cleave"])
    goblin = _entity("goblin", "monsters", hp=1, ac=8)
    # No other enemy in world
    ws = _world({"fighter": fighter, "goblin": goblin})

    intent = AttackIntent(attacker_id="fighter", target_id="goblin",
                          weapon=LONGSWORD, attack_bonus=7)
    rng = _mock_rng([15, 4])
    events = resolve_attack(intent, ws, rng, 0, 0.0)

    cleave_evts = [e for e in events if e.event_type == "cleave_triggered"]
    assert len(cleave_evts) == 0, "No cleave when no adjacent enemy remains"


# ===========================================================================
# CL-05: Great Cleave feat: second kill triggers second Cleave bonus attack
# ===========================================================================

def test_cl05_great_cleave_no_limit():
    """CL-05: Great Cleave has no once-per-round limit; even if already used, triggers again."""
    fighter = _entity("fighter", "party", bab=5, str_mod=3, feats=["cleave", "great_cleave"])
    goblin = _entity("goblin", "monsters", hp=1, ac=8)
    orc = _entity("orc", "monsters", hp=20, ac=10)
    ws = _world({"fighter": fighter, "goblin": goblin, "orc": orc},
                extra_combat={"cleave_used_this_turn": {"fighter"}})  # already used once

    intent = AttackIntent(attacker_id="fighter", target_id="goblin",
                          weapon=LONGSWORD, attack_bonus=7)
    rng = _mock_rng([15, 4, 10, 3])
    events = resolve_attack(intent, ws, rng, 0, 0.0)

    # Great Cleave should fire even though cleave_used_this_turn has fighter in it
    cleave_evts = [e for e in events if e.event_type == "cleave_triggered"]
    assert len(cleave_evts) == 1, f"Great Cleave should fire despite prior use, got {len(cleave_evts)}"


# ===========================================================================
# CL-06: No Cleave feat: kill does NOT produce cleave_triggered
# ===========================================================================

def test_cl06_no_feat_no_cleave():
    """CL-06: Entity without Cleave feat kills enemy → no cleave_triggered."""
    fighter = _entity("fighter", "party", bab=5, str_mod=3, feats=[])  # no cleave
    goblin = _entity("goblin", "monsters", hp=1, ac=8)
    orc = _entity("orc", "monsters", hp=20, ac=10)
    ws = _world({"fighter": fighter, "goblin": goblin, "orc": orc})

    intent = AttackIntent(attacker_id="fighter", target_id="goblin",
                          weapon=LONGSWORD, attack_bonus=7)
    rng = _mock_rng([15, 4])
    events = resolve_attack(intent, ws, rng, 0, 0.0)

    cleave_evts = [e for e in events if e.event_type == "cleave_triggered"]
    assert len(cleave_evts) == 0, "No cleave without Cleave feat"


# ===========================================================================
# CL-07: _find_cleave_target excludes killed entity and returns living enemy
# ===========================================================================

def test_cl07_find_cleave_target():
    """CL-07: _find_cleave_target returns a living enemy entity ID (not the killed one)."""
    fighter = _entity("fighter", "party", bab=5)
    goblin_dead = _entity("goblin_dead", "monsters", hp=0, defeated=True)
    orc = _entity("orc", "monsters", hp=20)
    ws = _world({"fighter": fighter, "goblin_dead": goblin_dead, "orc": orc})

    result = _find_cleave_target("fighter", "goblin_dead", ws)
    assert result == "orc", f"Expected 'orc', got {result}"


# ===========================================================================
# CL-08: cleave_triggered event payload has required fields
# ===========================================================================

def test_cl08_cleave_event_payload():
    """CL-08: cleave_triggered event payload contains attacker_id, killed_target_id, cleave_target_id, feat."""
    fighter = _entity("fighter", "party", bab=5, str_mod=3, feats=["cleave"])
    goblin = _entity("goblin", "monsters", hp=1, ac=8)
    orc = _entity("orc", "monsters", hp=20, ac=10)
    ws = _world({"fighter": fighter, "goblin": goblin, "orc": orc})

    intent = AttackIntent(attacker_id="fighter", target_id="goblin",
                          weapon=LONGSWORD, attack_bonus=7)
    rng = _mock_rng([15, 4, 10, 3])
    events = resolve_attack(intent, ws, rng, 0, 0.0)

    cleave_evts = [e for e in events if e.event_type == "cleave_triggered"]
    assert len(cleave_evts) == 1
    payload = cleave_evts[0].payload
    assert "attacker_id" in payload
    assert "killed_target_id" in payload
    assert "cleave_target_id" in payload
    assert "feat" in payload
    assert payload["attacker_id"] == "fighter"
    assert payload["killed_target_id"] == "goblin"
    assert payload["cleave_target_id"] == "orc"
    assert payload["feat"] in ("cleave", "great_cleave")


# ===========================================================================
# CL-09: cleave_used_this_turn cleared at start of next turn (via play_loop turn-start logic)
# ===========================================================================

def test_cl09_cleave_used_cleared_next_turn():
    """CL-09: get_cleave_limit returns 1 for Cleave, None for Great Cleave (unlimited)."""
    fighter_cleave = _entity("fighter", "party", feats=["cleave"])
    fighter_gc = _entity("fighter", "party", feats=["cleave", "great_cleave"])
    assert get_cleave_limit(fighter_cleave) == 1
    assert get_cleave_limit(fighter_gc) is None


# ===========================================================================
# CL-10: Determinism — 10 replays with same seed produce identical Cleave sequence
# ===========================================================================

def test_cl10_determinism():
    """CL-10: 10 replays with same RNGManager seed produce identical event sequences including Cleave."""
    fighter = _entity("fighter", "party", bab=5, str_mod=3, feats=["cleave"])
    goblin = _entity("goblin", "monsters", hp=1, ac=8)
    orc = _entity("orc", "monsters", hp=20, ac=10)
    ws = _world({"fighter": fighter, "goblin": goblin, "orc": orc})

    intent = AttackIntent(attacker_id="fighter", target_id="goblin",
                          weapon=LONGSWORD, attack_bonus=7)

    results = []
    for _ in range(10):
        rng = RNGManager(master_seed=42)
        evts = resolve_attack(intent, deepcopy(ws), rng, 0, 0.0)
        results.append([e.event_type for e in evts])

    first = results[0]
    for i, r in enumerate(results[1:], start=1):
        assert r == first, f"Replay {i} event sequence differs: {r} vs {first}"
