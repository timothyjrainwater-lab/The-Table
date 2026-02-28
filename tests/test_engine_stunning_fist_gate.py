"""Gate tests for WO-ENGINE-AG-WO1: Stunning Fist (PHB p.101).

SF-001: Monk L4 has 4 uses per day (EF.STUNNING_FIST_USES = 4)
SF-002: Non-monk L8 with feat has 2 uses (char_level // 4 = 2)
SF-003: Hit + failed Fort save → STUNNED condition applied to target
SF-004: Hit + successful Fort save → no condition, use still consumed
SF-005: Miss → no condition, use still consumed (declared before roll)
SF-006: Uses exhausted → stunning_fist_exhausted event, attempt blocked
SF-007: Uses reset to 0 on RestIntent
SF-008: No HAS_STUNNING_FIST → attempt blocked (stunning_fist_invalid)
"""

import pytest
from copy import deepcopy

from aidm.core.state import WorldState
from aidm.core.attack_resolver import resolve_attack, apply_attack_events
from aidm.core.rest_resolver import resolve_rest
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.entity_fields import EF
from aidm.schemas.intents import RestIntent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FixedRNG:
    """Deterministic RNG for testing: streams return predefined rolls."""

    def __init__(self, combat_rolls, saves_rolls=None):
        self._combat = list(combat_rolls)
        self._saves = list(saves_rolls or [])
        self._combat_idx = 0
        self._saves_idx = 0

    def stream(self, name):
        return self

    def randint(self, lo, hi):
        # Use saves pool if available (for save rolls), else combat
        if self._saves and self._saves_idx < len(self._saves):
            val = self._saves[self._saves_idx]
            self._saves_idx += 1
            return val
        if self._combat_idx < len(self._combat):
            val = self._combat[self._combat_idx]
            self._combat_idx += 1
            return val
        return 10  # fallback


class _SeparateStreamRNG:
    """RNG with separate pools per stream name."""

    def __init__(self, combat_rolls, saves_rolls=None):
        self._pools = {
            "combat": list(combat_rolls),
            "saves": list(saves_rolls or []),
        }
        self._idxs = {"combat": 0, "saves": 0}

    def stream(self, name):
        return _StreamProxy(self._pools.get(name, [10] * 20), self._idxs, name)


class _StreamProxy:
    def __init__(self, pool, idxs, name):
        self._pool = pool
        self._idxs = idxs
        self._name = name

    def randint(self, lo, hi):
        idx = self._idxs[self._name]
        if idx < len(self._pool):
            val = self._pool[idx]
            self._idxs[self._name] = idx + 1
            return val
        return 10


def _make_weapon(damage_dice="1d6", weapon_type="natural"):
    return Weapon(
        damage_dice=damage_dice,
        damage_bonus=0,
        critical_range=20,
        critical_multiplier=2,
        damage_type="bludgeoning",
        weapon_type=weapon_type,
        is_two_handed=False,
        grip="one-handed",
        enhancement_bonus=0,
    )


def _make_monk(level, monk_level=None):
    """Build a minimal monk entity."""
    ml = monk_level if monk_level is not None else level
    return {
        EF.ENTITY_ID: "monk_1",
        EF.TEAM: "player",
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 30,
        EF.AC: 15,
        EF.DEFEATED: False,
        EF.BASE_STATS: {"strength": 14, "dexterity": 14, "constitution": 14,
                        "intelligence": 10, "wisdom": 16, "charisma": 10},
        EF.STR_MOD: 2,
        EF.DEX_MOD: 2,
        EF.CON_MOD: 2,
        EF.WIS_MOD: 3,
        EF.CHA_MOD: 0,
        EF.SAVE_FORT: 4,
        EF.SAVE_REF: 4,
        EF.SAVE_WILL: 4,
        EF.BAB: level,
        EF.ATTACK_BONUS: level + 2,
        EF.LEVEL: level,
        EF.CLASS_LEVELS: {"monk": ml},
        EF.FEATS: [],
        EF.CONDITIONS: {},
        EF.POSITION: {"x": 0, "y": 0},
        EF.HAS_STUNNING_FIST: True,
        EF.STUNNING_FIST_USES: ml,
        EF.STUNNING_FIST_USED: 0,
        EF.ARMOR_AC_BONUS: 0,
        EF.ARMOR_TYPE: "none",
        EF.MONK_WIS_AC_BONUS: 3,
    }


def _make_fighter(level, feats=None):
    """Build a minimal fighter entity (non-monk)."""
    return {
        EF.ENTITY_ID: "fighter_1",
        EF.TEAM: "player",
        EF.HP_CURRENT: 40,
        EF.HP_MAX: 40,
        EF.AC: 16,
        EF.DEFEATED: False,
        EF.BASE_STATS: {"strength": 16, "dexterity": 12, "constitution": 14,
                        "intelligence": 10, "wisdom": 14, "charisma": 10},
        EF.STR_MOD: 3,
        EF.DEX_MOD: 1,
        EF.CON_MOD: 2,
        EF.WIS_MOD: 2,
        EF.CHA_MOD: 0,
        EF.SAVE_FORT: 6,
        EF.SAVE_REF: 3,
        EF.SAVE_WILL: 2,
        EF.BAB: level,
        EF.ATTACK_BONUS: level + 3,
        EF.LEVEL: level,
        EF.CLASS_LEVELS: {"fighter": level},
        EF.FEATS: feats or [],
        EF.CONDITIONS: {},
        EF.POSITION: {"x": 0, "y": 0},
        EF.ARMOR_AC_BONUS: 4,
        EF.ARMOR_TYPE: "medium",
    }


def _make_target(fort_save=2, hp=30):
    return {
        EF.ENTITY_ID: "target_1",
        EF.TEAM: "enemy",
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp,
        EF.AC: 10,
        EF.DEFEATED: False,
        EF.BASE_STATS: {"strength": 12, "dexterity": 10, "constitution": 12,
                        "intelligence": 10, "wisdom": 10, "charisma": 10},
        EF.STR_MOD: 1,
        EF.DEX_MOD: 0,
        EF.CON_MOD: 1,
        EF.WIS_MOD: 0,
        EF.CHA_MOD: 0,
        EF.SAVE_FORT: fort_save,
        EF.SAVE_REF: 2,
        EF.SAVE_WILL: 0,
        EF.CONDITIONS: {},
        EF.POSITION: {"x": 1, "y": 0},
        EF.ARMOR_AC_BONUS: 0,
    }


def _make_world(attacker, target):
    return WorldState(
        ruleset_version="3.5",
        entities={attacker[EF.ENTITY_ID]: attacker, target[EF.ENTITY_ID]: target},
        active_combat=None,
    )


def _event_types(events):
    return [e.event_type for e in events]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_sf_001_monk_l4_has_4_uses():
    """SF-001: Monk L4 has 4 uses per day (EF.STUNNING_FIST_USES = 4)."""
    from aidm.chargen.builder import build_character
    entity = build_character(race="human", class_name="monk", level=4,
                             ability_overrides={"str": 14, "dex": 14, "con": 14,
                                                "int": 10, "wis": 14, "cha": 10})
    assert entity[EF.HAS_STUNNING_FIST] is True
    assert entity[EF.STUNNING_FIST_USES] == 4
    assert entity[EF.STUNNING_FIST_USED] == 0


def test_sf_002_non_monk_l8_with_feat_has_2_uses():
    """SF-002: Non-monk L8 with feat has 2 uses (char_level // 4 = 2)."""
    from aidm.chargen.builder import build_character
    entity = build_character(race="human", class_name="fighter", level=8,
                             ability_overrides={"str": 16, "dex": 14, "con": 14,
                                                "int": 10, "wis": 14, "cha": 10},
                             feat_choices=["power_attack", "improved_grapple", "stunning_fist"])
    assert entity[EF.HAS_STUNNING_FIST] is True
    assert entity[EF.STUNNING_FIST_USES] == 2  # 8 // 4 = 2
    assert entity[EF.STUNNING_FIST_USED] == 0


def test_sf_003_hit_failed_fort_save_stunned():
    """SF-003: Hit + failed Fort save → STUNNED condition applied to target."""
    monk = _make_monk(level=4)
    target = _make_target(fort_save=2)  # Fort +2; DC = 10 + 2 + 3(WIS) = 15; needs 13+ on d20
    ws = _make_world(monk, target)

    # combat: d20=18 (hit); saves: d20=1 (nat 1 = auto-fail Fort save)
    rng = _SeparateStreamRNG(combat_rolls=[18], saves_rolls=[1])
    intent = AttackIntent(
        attacker_id="monk_1",
        target_id="target_1",
        attack_bonus=6,
        weapon=_make_weapon(),
        stunning_fist=True,
    )
    events = resolve_attack(intent, ws, rng, next_event_id=1, timestamp=0.0)
    types = _event_types(events)
    assert "stunning_fist_used" in types, f"Expected stunning_fist_used, got {types}"
    assert "stunning_fist_hit" in types, f"Expected stunning_fist_hit (save failed), got {types}"
    assert "condition_applied" in types, "Expected condition_applied (STUNNED)"
    # Verify STUNNED specifically
    cond_events = [e for e in events if e.event_type == "condition_applied"]
    assert any(e.payload["condition"] == "stunned" for e in cond_events)


def test_sf_004_hit_successful_fort_save_no_condition():
    """SF-004: Hit + successful Fort save → no condition, use still consumed."""
    monk = _make_monk(level=4)
    target = _make_target(fort_save=20)  # Fort +20; will succeed on any non-nat-1
    ws = _make_world(monk, target)

    # combat: d20=18 (hit); saves: d20=10 (success with Fort +20)
    rng = _SeparateStreamRNG(combat_rolls=[18], saves_rolls=[10])
    intent = AttackIntent(
        attacker_id="monk_1",
        target_id="target_1",
        attack_bonus=6,
        weapon=_make_weapon(),
        stunning_fist=True,
    )
    events = resolve_attack(intent, ws, rng, next_event_id=1, timestamp=0.0)
    types = _event_types(events)
    assert "stunning_fist_used" in types, "Use must be consumed even on successful Fort save"
    assert "stunning_fist_saved" in types, "Expected stunning_fist_saved"
    # No STUNNED condition
    cond_events = [e for e in events if e.event_type == "condition_applied"]
    assert not any(e.payload.get("condition") == "stunned" for e in cond_events)


def test_sf_005_miss_use_still_consumed():
    """SF-005: Miss → no condition, use still consumed (declared before roll)."""
    monk = _make_monk(level=4)
    target = _make_target()
    target[EF.AC] = 30  # Very high AC → miss
    ws = _make_world(monk, target)

    # combat: d20=1 (natural miss); no save rolled
    rng = _SeparateStreamRNG(combat_rolls=[1], saves_rolls=[])
    intent = AttackIntent(
        attacker_id="monk_1",
        target_id="target_1",
        attack_bonus=6,
        weapon=_make_weapon(),
        stunning_fist=True,
    )
    events = resolve_attack(intent, ws, rng, next_event_id=1, timestamp=0.0)
    types = _event_types(events)
    assert "stunning_fist_used" in types, "SF-005: use consumed even on miss"
    # No condition applied (miss means no effect)
    cond_events = [e for e in events if e.event_type == "condition_applied"]
    assert not any(e.payload.get("condition") == "stunned" for e in cond_events)


def test_sf_006_uses_exhausted_blocks_attempt():
    """SF-006: Uses exhausted → stunning_fist_exhausted event, attempt blocked."""
    monk = _make_monk(level=4)
    monk[EF.STUNNING_FIST_USED] = 4  # Already used all 4 today
    target = _make_target()
    ws = _make_world(monk, target)

    rng = _SeparateStreamRNG(combat_rolls=[15], saves_rolls=[])
    intent = AttackIntent(
        attacker_id="monk_1",
        target_id="target_1",
        attack_bonus=6,
        weapon=_make_weapon(),
        stunning_fist=True,
    )
    events = resolve_attack(intent, ws, rng, next_event_id=1, timestamp=0.0)
    types = _event_types(events)
    assert "stunning_fist_exhausted" in types, f"Expected exhausted event, got {types}"
    # No attack_roll event — attempt was blocked before the roll
    assert "attack_roll" not in types, "Blocked attempt should not reach attack_roll"


def test_sf_007_uses_reset_on_rest():
    """SF-007: Uses reset to 0 on RestIntent."""
    monk = _make_monk(level=4)
    monk[EF.STUNNING_FIST_USED] = 3  # Partially used
    monk[EF.CLASS_LEVELS] = {"monk": 4}
    target = _make_target()
    ws = _make_world(monk, target)

    # Apply rest
    intent = RestIntent(rest_type="overnight")
    result = resolve_rest(intent, ws, actor_id="monk_1", next_event_id=1, timestamp=0.0)
    monk_after = result.world_state.entities["monk_1"]
    assert monk_after[EF.STUNNING_FIST_USED] == 0, (
        f"SF-007: STUNNING_FIST_USED should be 0 after rest, got {monk_after[EF.STUNNING_FIST_USED]}"
    )


def test_sf_008_no_has_stunning_fist_invalid():
    """SF-008: No HAS_STUNNING_FIST → attempt blocked (stunning_fist_invalid)."""
    fighter = _make_fighter(level=4)
    # No HAS_STUNNING_FIST set (fighter without the feat)
    target = _make_target()
    ws = _make_world(fighter, target)

    rng = _SeparateStreamRNG(combat_rolls=[15], saves_rolls=[])
    intent = AttackIntent(
        attacker_id="fighter_1",
        target_id="target_1",
        attack_bonus=7,
        weapon=_make_weapon(),
        stunning_fist=True,  # Attempting without the feat
    )
    events = resolve_attack(intent, ws, rng, next_event_id=1, timestamp=0.0)
    types = _event_types(events)
    assert "stunning_fist_invalid" in types, f"Expected stunning_fist_invalid, got {types}"
    assert "attack_roll" not in types, "Invalid attempt should not reach attack_roll"
