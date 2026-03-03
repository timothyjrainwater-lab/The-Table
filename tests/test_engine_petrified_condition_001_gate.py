"""Gate tests: WO-ENGINE-PETRIFIED-CONDITION-001 (Batch BB WO3).

PTC-001..008 per PM Acceptance Notes:
  PTC-001: ConditionType.PETRIFIED exists in conditions.py enum
  PTC-002: create_petrified_condition() returns ConditionInstance with correct type
  PTC-003: Petrified entity gets -5 DEX modifier applied to AC (DEX score treated as 0)
  PTC-004: Petrified entity gets -5 DEX modifier applied to attack roll
  PTC-005: condition_instance.blocks_actions == True (actions_prohibited=True)
  PTC-006: "poison" in condition_instance.immune_to
  PTC-007: "disease" in condition_instance.immune_to
  PTC-008: Non-petrified entity — no AC/attack penalty (regression)

FINDING-ENGINE-PETRIFIED-CONDITION-001 closed.
"""
from __future__ import annotations

from aidm.schemas.conditions import ConditionType, create_petrified_condition
from aidm.schemas.entity_fields import EF
from aidm.core.conditions import get_condition_modifiers, apply_condition
from aidm.core.state import WorldState


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

def _build_world(entity_id: str, dex_mod: int = 0,
                 conditions: dict = None) -> WorldState:
    """Minimal WorldState for condition modifier queries."""
    entity = {
        EF.ENTITY_ID: entity_id,
        EF.TEAM: "player",
        EF.DEX_MOD: dex_mod,
        EF.HP_CURRENT: 30, EF.HP_MAX: 30, EF.AC: 10 + dex_mod,
        EF.CONDITIONS: conditions or {},
        EF.DEFEATED: False,
        EF.POSITION: {"x": 0, "y": 0},
    }
    return WorldState(
        ruleset_version="3.5",
        entities={entity_id: entity},
        active_combat={
            "initiative_order": [entity_id],
            "aoo_used_this_round": [],
            "aoo_count_this_round": {},
        },
    )


# ---------------------------------------------------------------------------
# PTC-001: ConditionType.PETRIFIED exists in enum
# ---------------------------------------------------------------------------

def test_PTC001_condition_type_petrified_exists():
    """PTC-001: ConditionType.PETRIFIED exists in conditions.py enum."""
    assert hasattr(ConditionType, "PETRIFIED"), (
        "PTC-001: ConditionType.PETRIFIED not found in ConditionType enum"
    )
    assert ConditionType.PETRIFIED == "petrified", (
        f"PTC-001: ConditionType.PETRIFIED.value must be 'petrified', got '{ConditionType.PETRIFIED}'"
    )


# ---------------------------------------------------------------------------
# PTC-002: create_petrified_condition() returns ConditionInstance with PETRIFIED type
# ---------------------------------------------------------------------------

def test_PTC002_factory_returns_correct_type():
    """PTC-002: create_petrified_condition() returns ConditionInstance with condition_type=PETRIFIED."""
    from aidm.schemas.conditions import ConditionInstance
    cond = create_petrified_condition(source="basilisk_gaze", applied_at_event_id=1)
    assert isinstance(cond, ConditionInstance), (
        f"PTC-002: Expected ConditionInstance, got {type(cond).__name__}"
    )
    assert cond.condition_type == ConditionType.PETRIFIED, (
        f"PTC-002: Expected PETRIFIED, got {cond.condition_type}"
    )


# ---------------------------------------------------------------------------
# PTC-003: Petrified entity — -5 DEX modifier applied to AC
# ---------------------------------------------------------------------------

def test_PTC003_petrified_dex_penalty_to_ac():
    """PTC-003: Petrified entity gets -5 DEX modifier applied to AC.
    Entity with DEX_MOD=+2: AC penalty = -5 - 2 = -7 (to override baked-in +2 with -5)."""
    dex_mod = 2
    cond = create_petrified_condition(source="test", applied_at_event_id=0)
    world = _build_world("ent", dex_mod=dex_mod,
                         conditions={ConditionType.PETRIFIED.value: cond.to_dict()})
    mods = get_condition_modifiers(world, "ent")

    # Expected: -5 - dex_mod = -7 penalty to AC
    expected_ac_penalty = -5 - dex_mod
    assert mods.ac_modifier == expected_ac_penalty, (
        f"PTC-003: Petrified AC penalty should be {expected_ac_penalty} for DEX_MOD={dex_mod}, "
        f"got {mods.ac_modifier}"
    )


# ---------------------------------------------------------------------------
# PTC-004: Petrified entity — -5 DEX modifier applied to attack roll
# ---------------------------------------------------------------------------

def test_PTC004_petrified_dex_penalty_to_attack():
    """PTC-004: Petrified entity gets -5 DEX modifier applied to attack roll.
    Same entity-specific penalty as AC: -5 - dex_mod."""
    dex_mod = 1
    cond = create_petrified_condition(source="test", applied_at_event_id=0)
    world = _build_world("ent", dex_mod=dex_mod,
                         conditions={ConditionType.PETRIFIED.value: cond.to_dict()})
    mods = get_condition_modifiers(world, "ent")

    expected_attack_penalty = -5 - dex_mod
    assert mods.attack_modifier == expected_attack_penalty, (
        f"PTC-004: Petrified attack penalty should be {expected_attack_penalty} for DEX_MOD={dex_mod}, "
        f"got {mods.attack_modifier}"
    )


# ---------------------------------------------------------------------------
# PTC-005: condition_instance.blocks_actions == True
# ---------------------------------------------------------------------------

def test_PTC005_blocks_actions_true():
    """PTC-005: Petrified condition has actions_prohibited=True (blocks all actions)."""
    cond = create_petrified_condition(source="medusa_gaze", applied_at_event_id=5)
    assert cond.modifiers.actions_prohibited is True, (
        f"PTC-005: Petrified condition must have actions_prohibited=True, "
        f"got {cond.modifiers.actions_prohibited}"
    )


# ---------------------------------------------------------------------------
# PTC-006: "poison" in condition_instance.immune_to
# ---------------------------------------------------------------------------

def test_PTC006_immune_to_poison():
    """PTC-006: 'poison' in condition_instance.immune_to (stone doesn't metabolize)."""
    cond = create_petrified_condition(source="test", applied_at_event_id=0)
    assert "poison" in cond.immune_to, (
        f"PTC-006: 'poison' must be in immune_to for PETRIFIED, got {cond.immune_to}"
    )


# ---------------------------------------------------------------------------
# PTC-007: "disease" in condition_instance.immune_to
# ---------------------------------------------------------------------------

def test_PTC007_immune_to_disease():
    """PTC-007: 'disease' in condition_instance.immune_to (stone doesn't metabolize)."""
    cond = create_petrified_condition(source="test", applied_at_event_id=0)
    assert "disease" in cond.immune_to, (
        f"PTC-007: 'disease' must be in immune_to for PETRIFIED, got {cond.immune_to}"
    )


# ---------------------------------------------------------------------------
# PTC-008: Non-petrified entity — no AC/attack penalty (regression)
# ---------------------------------------------------------------------------

def test_PTC008_non_petrified_no_penalty():
    """PTC-008: Non-petrified entity has no AC or attack penalty (regression).
    get_condition_modifiers() with empty conditions returns zero modifiers."""
    world = _build_world("ent", dex_mod=3, conditions={})
    mods = get_condition_modifiers(world, "ent")

    assert mods.ac_modifier == 0, (
        f"PTC-008: Non-petrified entity should have ac_modifier=0, got {mods.ac_modifier}"
    )
    assert mods.attack_modifier == 0, (
        f"PTC-008: Non-petrified entity should have attack_modifier=0, got {mods.attack_modifier}"
    )
    assert not mods.actions_prohibited, (
        f"PTC-008: Non-petrified entity should have actions_prohibited=False"
    )
