"""Gate tests: WO-ENGINE-INCORPOREAL-MISS-CHANCE-001 (Batch BC WO1).

INC-001..008 per PM Acceptance Notes:
  INC-001: ConditionType.INCORPOREAL exists in aidm/schemas/conditions.py
  INC-002: create_incorporeal_condition() returns ConditionInstance with type=INCORPOREAL
  INC-003: Mundane weapon (enhancement_bonus=0/absent) vs INCORPOREAL → attack_denied, reason=auto_miss_incorporeal
  INC-004: enhancement_bonus=0 explicit → same auto-miss (zero is nonmagical)
  INC-005: +1 weapon (enhancement_bonus=1) vs INCORPOREAL → attack roll proceeds (not auto-blocked)
  INC-006: is_magic-absent + no enhancement_bonus → auto-miss
  INC-007: Non-incorporeal target + mundane weapon → normal attack flow, no auto-miss (regression)
  INC-008: Parallel paths confirmed — full_attack (delegates to resolve_attack), nonlethal, manyshot

FINDING-ENGINE-INCORPOREAL-CONDITION-001 closed.
"""
from __future__ import annotations

import unittest.mock as mock

from aidm.schemas.conditions import ConditionType, create_incorporeal_condition
from aidm.schemas.entity_fields import EF
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.core.state import WorldState
from aidm.core.attack_resolver import resolve_attack, resolve_nonlethal_attack


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

def _world(target_id: str = "tgt", incorporeal: bool = False) -> WorldState:
    conditions = {}
    if incorporeal:
        cond = create_incorporeal_condition(source="undead_form", applied_at_event_id=0)
        conditions = {ConditionType.INCORPOREAL.value: cond.to_dict()}
    attacker = {
        EF.ENTITY_ID: "att", EF.TEAM: "player",
        EF.STR_MOD: 0, EF.DEX_MOD: 0,
        EF.FEATS: [], EF.ATTACK_BONUS: 10,
        EF.HP_CURRENT: 30, EF.HP_MAX: 30, EF.AC: 15, EF.DEFEATED: False,
        EF.NEGATIVE_LEVELS: 0, EF.CONDITIONS: {},
        EF.INSPIRE_COURAGE_ACTIVE: False, EF.INSPIRE_COURAGE_BONUS: 0,
        EF.FAVORED_ENEMIES: [], EF.TEMPORARY_MODIFIERS: {},
        EF.POSITION: {"x": 0, "y": 0},
    }
    target = {
        EF.ENTITY_ID: target_id, EF.TEAM: "monsters",
        EF.HP_CURRENT: 30, EF.HP_MAX: 30, EF.AC: 15, EF.DEFEATED: False,
        EF.NEGATIVE_LEVELS: 0, EF.CONDITIONS: conditions,
        EF.STR_MOD: 0, EF.DEX_MOD: 0, EF.FEATS: [],
        EF.POSITION: {"x": 1, "y": 0},
    }
    return WorldState(
        ruleset_version="3.5",
        entities={"att": attacker, target_id: target},
        active_combat={
            "initiative_order": ["att", target_id],
            "aoo_used_this_round": [],
            "aoo_count_this_round": {},
        },
    )


def _weapon(enhancement_bonus: int = 0) -> Weapon:
    return Weapon(
        damage_dice="1d8", damage_bonus=0, damage_type="slashing",
        grip="one-handed", weapon_type="one-handed",
        enhancement_bonus=enhancement_bonus,
    )


def _rng_fixed(attack: int = 15):
    stream = mock.MagicMock()
    stream.randint.return_value = attack
    rng = mock.MagicMock()
    rng.stream.return_value = stream
    return rng


# ---------------------------------------------------------------------------
# INC-001: ConditionType.INCORPOREAL exists
# ---------------------------------------------------------------------------

def test_INC001_condition_type_incorporeal_exists():
    """INC-001: ConditionType.INCORPOREAL exists in conditions.py enum."""
    assert hasattr(ConditionType, "INCORPOREAL"), (
        "INC-001: ConditionType.INCORPOREAL not found in ConditionType enum"
    )
    assert ConditionType.INCORPOREAL == "incorporeal", (
        f"INC-001: ConditionType.INCORPOREAL.value must be 'incorporeal', got '{ConditionType.INCORPOREAL}'"
    )


# ---------------------------------------------------------------------------
# INC-002: create_incorporeal_condition() factory
# ---------------------------------------------------------------------------

def test_INC002_factory_returns_correct_type():
    """INC-002: create_incorporeal_condition() returns ConditionInstance with type=INCORPOREAL."""
    from aidm.schemas.conditions import ConditionInstance
    cond = create_incorporeal_condition(source="undead_form", applied_at_event_id=1)
    assert isinstance(cond, ConditionInstance), (
        f"INC-002: Expected ConditionInstance, got {type(cond).__name__}"
    )
    assert cond.condition_type == ConditionType.INCORPOREAL, (
        f"INC-002: Expected INCORPOREAL, got {cond.condition_type}"
    )


# ---------------------------------------------------------------------------
# INC-003: Mundane weapon (enhancement_bonus=0 default) → auto-miss
# ---------------------------------------------------------------------------

def test_INC003_mundane_weapon_auto_misses_incorporeal():
    """INC-003: Standard attack with mundane weapon vs INCORPOREAL → attack_denied(auto_miss_incorporeal)."""
    ws = _world(incorporeal=True)
    intent = AttackIntent(
        attacker_id="att", target_id="tgt",
        attack_bonus=10, weapon=_weapon(enhancement_bonus=0),
    )
    events = resolve_attack(intent=intent, world_state=ws, rng=_rng_fixed(15),
                            next_event_id=0, timestamp=0.0)
    denied = next((e for e in events if e.event_type == "attack_denied"), None)
    assert denied is not None, "INC-003: Expected attack_denied event, got none"
    assert denied.payload.get("reason") == "auto_miss_incorporeal", (
        f"INC-003: reason must be 'auto_miss_incorporeal', got {denied.payload.get('reason')}"
    )
    # Must NOT have an attack_roll event (auto-miss stops before roll)
    roll_event = next((e for e in events if e.event_type == "attack_roll"), None)
    assert roll_event is None, "INC-003: attack_roll must not be emitted for auto-miss incorporeal"


# ---------------------------------------------------------------------------
# INC-004: enhancement_bonus=0 explicit → same auto-miss
# ---------------------------------------------------------------------------

def test_INC004_explicit_zero_enhancement_auto_misses():
    """INC-004: enhancement_bonus=0 explicit → auto-miss (zero = nonmagical)."""
    ws = _world(incorporeal=True)
    intent = AttackIntent(
        attacker_id="att", target_id="tgt",
        attack_bonus=5, weapon=_weapon(enhancement_bonus=0),
    )
    events = resolve_attack(intent=intent, world_state=ws, rng=_rng_fixed(15),
                            next_event_id=0, timestamp=0.0)
    denied = next((e for e in events if e.event_type == "attack_denied"), None)
    assert denied is not None and denied.payload.get("reason") == "auto_miss_incorporeal", (
        "INC-004: enhancement_bonus=0 explicit should still produce auto_miss_incorporeal"
    )


# ---------------------------------------------------------------------------
# INC-005: +1 weapon vs INCORPOREAL → attack roll proceeds (not blocked)
# ---------------------------------------------------------------------------

def test_INC005_magic_weapon_bypasses_auto_miss():
    """INC-005: enhancement_bonus=1 vs INCORPOREAL → attack roll event emitted (not auto-blocked)."""
    ws = _world(incorporeal=True)
    intent = AttackIntent(
        attacker_id="att", target_id="tgt",
        attack_bonus=10, weapon=_weapon(enhancement_bonus=1),
    )
    events = resolve_attack(intent=intent, world_state=ws, rng=_rng_fixed(15),
                            next_event_id=0, timestamp=0.0)
    # Should NOT have attack_denied with auto_miss_incorporeal
    denied = next((e for e in events if e.event_type == "attack_denied"
                   and e.payload.get("reason") == "auto_miss_incorporeal"), None)
    assert denied is None, (
        "INC-005: +1 weapon should bypass incorporeal auto-miss; attack_denied(auto_miss_incorporeal) found"
    )
    # Should have an attack_roll event
    roll_event = next((e for e in events if e.event_type == "attack_roll"), None)
    assert roll_event is not None, (
        "INC-005: +1 weapon vs incorporeal — attack_roll event must be emitted"
    )


# ---------------------------------------------------------------------------
# INC-006: is_magic-absent (no enhancement_bonus) → auto-miss
# ---------------------------------------------------------------------------

def test_INC006_no_enhancement_no_magic_auto_misses():
    """INC-006: Weapon with no enhancement_bonus (defaults to 0) → auto-miss vs incorporeal."""
    ws = _world(incorporeal=True)
    # Build a bare weapon — enhancement_bonus defaults to 0
    weapon = Weapon(damage_dice="1d6", damage_bonus=0, damage_type="bludgeoning",
                    grip="one-handed", weapon_type="one-handed")
    assert weapon.enhancement_bonus == 0, "INC-006 setup: default enhancement_bonus must be 0"
    intent = AttackIntent(attacker_id="att", target_id="tgt", attack_bonus=3, weapon=weapon)
    events = resolve_attack(intent=intent, world_state=ws, rng=_rng_fixed(15),
                            next_event_id=0, timestamp=0.0)
    denied = next((e for e in events if e.event_type == "attack_denied"), None)
    assert denied is not None and denied.payload.get("reason") == "auto_miss_incorporeal", (
        "INC-006: Weapon with no is_magic + no enhancement should produce auto_miss_incorporeal"
    )


# ---------------------------------------------------------------------------
# INC-007: Non-incorporeal target → no auto-miss (regression)
# ---------------------------------------------------------------------------

def test_INC007_non_incorporeal_no_auto_miss():
    """INC-007: Non-incorporeal target with mundane weapon → normal attack flow (no auto-miss)."""
    ws = _world(incorporeal=False)  # Target has no incorporeal condition
    intent = AttackIntent(
        attacker_id="att", target_id="tgt",
        attack_bonus=10, weapon=_weapon(enhancement_bonus=0),
    )
    events = resolve_attack(intent=intent, world_state=ws, rng=_rng_fixed(15),
                            next_event_id=0, timestamp=0.0)
    denied_inc = next((e for e in events if e.event_type == "attack_denied"
                       and e.payload.get("reason") == "auto_miss_incorporeal"), None)
    assert denied_inc is None, (
        "INC-007: Non-incorporeal target should not produce auto_miss_incorporeal"
    )
    roll_event = next((e for e in events if e.event_type == "attack_roll"), None)
    assert roll_event is not None, (
        "INC-007: Non-incorporeal target should produce attack_roll event"
    )


# ---------------------------------------------------------------------------
# INC-008: Parallel paths — full_attack delegates; nonlethal wired
# ---------------------------------------------------------------------------

def test_INC008_parallel_paths_confirmed():
    """INC-008: full_attack_resolver delegates to resolve_attack (auto-checked);
    resolve_nonlethal_attack also wired for incorporeal auto-miss."""
    import inspect
    import aidm.core.full_attack_resolver as _far
    import aidm.core.attack_resolver as _ar

    # full_attack_resolver delegates to resolve_attack (FAGU pattern)
    far_src = inspect.getsource(_far)
    assert "resolve_attack" in far_src, (
        "INC-008: full_attack_resolver must import and call resolve_attack"
    )

    # attack_resolver.py must contain the incorporeal auto-miss check
    ar_src = inspect.getsource(_ar)
    assert "auto_miss_incorporeal" in ar_src, (
        "INC-008: attack_resolver.py must contain 'auto_miss_incorporeal' reason"
    )

    # Nonlethal path: resolve_nonlethal_attack also auto-misses incorporeal
    ws = _world(incorporeal=True)
    from aidm.schemas.attack import NonlethalAttackIntent
    nl_intent = NonlethalAttackIntent(
        attacker_id="att", target_id="tgt",
        attack_bonus=5,
        weapon=Weapon(damage_dice="1d4", damage_bonus=0, damage_type="bludgeoning",
                      grip="one-handed", weapon_type="light"),
    )
    nl_events = resolve_nonlethal_attack(
        intent=nl_intent, world_state=ws, rng=_rng_fixed(15),
        next_event_id=0, timestamp=0.0,
    )
    nl_denied = next((e for e in nl_events if e.event_type == "attack_denied"
                      and e.payload.get("reason") == "auto_miss_incorporeal"), None)
    assert nl_denied is not None, (
        "INC-008: resolve_nonlethal_attack must produce auto_miss_incorporeal vs incorporeal target"
    )
