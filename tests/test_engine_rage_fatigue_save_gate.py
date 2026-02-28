"""Gate tests — RFS-AE-001 through RFS-AE-008
WO-AE-WO2: Rage fatigue dual-track — Ref save penalty.
PHB p.308 (Fatigued condition: -2 Str, -2 Dex). DEX penalty → -2 Reflex save.
Fix: save_resolver.get_save_bonus() checks EF.FATIGUED → applies -2 Reflex (not Fort/Will).
Rage resolver sets EF.FATIGUED=True (boolean) on rage end. NOT a ConditionInstance.
"""

import pytest
from aidm.core.save_resolver import get_save_bonus
from aidm.schemas.saves import SaveType
from aidm.schemas.entity_fields import EF
from aidm.core.state import WorldState


def _ws(entity: dict) -> WorldState:
    return WorldState(ruleset_version="3.5", entities={entity[EF.ENTITY_ID]: entity}, active_combat=None)


def _barb_entity(fatigued: bool = False, ref_base: int = 4, fort_base: int = 6, will_base: int = 1) -> dict:
    return {
        EF.ENTITY_ID: "barb",
        EF.SAVE_FORT: fort_base,
        EF.SAVE_REF: ref_base,
        EF.SAVE_WILL: will_base,
        EF.FATIGUED: fatigued,
        EF.FEATS: [],
        EF.CLASS_LEVELS: {"barbarian": 4},
        EF.RACE: "human",
        EF.RACIAL_SAVE_BONUS: 0,
        EF.SAVE_BONUS_POISON: 0,
        EF.SAVE_BONUS_SPELLS: 0,
        EF.SAVE_BONUS_ENCHANTMENT: 0,
        EF.CONDITIONS: [],
        EF.TEAM: "players",
    }


def test_rfs_ae_001_fatigued_ref_penalty_applied():
    """RFS-AE-001: EF.FATIGUED=True → Reflex save bonus reduced by 2."""
    entity = _barb_entity(fatigued=True)
    ws = _ws(entity)

    ref_bonus = get_save_bonus(ws, "barb", SaveType.REF, save_descriptor="")

    assert ref_bonus == entity[EF.SAVE_REF] - 2, (
        f"Fatigued entity Ref save should be EF.SAVE_REF - 2 = {entity[EF.SAVE_REF] - 2}. Got {ref_bonus}"
    )


def test_rfs_ae_002_not_fatigued_no_ref_penalty():
    """RFS-AE-002: EF.FATIGUED=False → Reflex save bonus unchanged."""
    entity = _barb_entity(fatigued=False)
    ws = _ws(entity)

    ref_bonus = get_save_bonus(ws, "barb", SaveType.REF, save_descriptor="")

    assert ref_bonus == entity[EF.SAVE_REF], (
        f"Non-fatigued entity Ref save should equal EF.SAVE_REF = {entity[EF.SAVE_REF]}. Got {ref_bonus}"
    )


def test_rfs_ae_003_fatigued_fort_unaffected():
    """RFS-AE-003: EF.FATIGUED=True does NOT penalize Fortitude save (fatigue only affects DEX → Ref)."""
    entity = _barb_entity(fatigued=True)
    ws = _ws(entity)

    fort_bonus = get_save_bonus(ws, "barb", SaveType.FORT, save_descriptor="")

    assert fort_bonus == entity[EF.SAVE_FORT], (
        f"Fatigued entity Fort save should be unaffected. Expected {entity[EF.SAVE_FORT]}, got {fort_bonus}"
    )


def test_rfs_ae_004_fatigued_will_unaffected():
    """RFS-AE-004: EF.FATIGUED=True does NOT penalize Will save (fatigue only affects DEX → Ref)."""
    entity = _barb_entity(fatigued=True)
    ws = _ws(entity)

    will_bonus = get_save_bonus(ws, "barb", SaveType.WILL, save_descriptor="")

    assert will_bonus == entity[EF.SAVE_WILL], (
        f"Fatigued entity Will save should be unaffected. Expected {entity[EF.SAVE_WILL]}, got {will_bonus}"
    )


def test_rfs_ae_005_fatigued_magnitude_is_minus_two():
    """RFS-AE-005: Fatigue Ref penalty is exactly -2 (PHB p.308: -2 DEX × 1 = -2 Ref)."""
    entity = _barb_entity(fatigued=True, ref_base=8)
    ws = _ws(entity)

    not_fatigued = _barb_entity(fatigued=False, ref_base=8)
    ws2 = _ws(not_fatigued)

    ref_fatigued = get_save_bonus(ws, "barb", SaveType.REF)
    ref_normal = get_save_bonus(ws2, "barb", SaveType.REF)

    assert ref_fatigued == ref_normal - 2, (
        f"Fatigue penalty should be exactly -2. fatigued={ref_fatigued}, normal={ref_normal}"
    )


def test_rfs_ae_006_fatigued_false_missing_key_no_penalty():
    """RFS-AE-006: Entity without EF.FATIGUED key (defaults to False) — no Ref penalty."""
    entity = _barb_entity(fatigued=False)
    entity.pop(EF.FATIGUED, None)  # remove the key entirely
    ws = _ws(entity)

    ref_bonus = get_save_bonus(ws, "barb", SaveType.REF)

    assert ref_bonus == entity[EF.SAVE_REF], (
        f"Missing EF.FATIGUED key should default to no penalty. Expected {entity[EF.SAVE_REF]}, got {ref_bonus}"
    )


def test_rfs_ae_007_fatigued_stacks_with_other_ref_penalties():
    """RFS-AE-007: Fatigue Ref penalty stacks correctly with other modifiers (e.g., lightning reflexes feat adds +2)."""
    entity = _barb_entity(fatigued=True, ref_base=4)
    entity[EF.FEATS] = ["lightning_reflexes"]  # +2 Ref save
    ws = _ws(entity)

    # net = 4 (base) + 2 (LR feat) - 2 (fatigue) = 4
    ref_bonus = get_save_bonus(ws, "barb", SaveType.REF)

    assert ref_bonus == entity[EF.SAVE_REF] + 2 - 2, (
        f"Fatigued + Lightning Reflexes: expected {entity[EF.SAVE_REF]} (base {entity[EF.SAVE_REF]} +2 LR -2 fatigue). Got {ref_bonus}"
    )


def test_rfs_ae_008_fatigued_does_not_create_condition_instance():
    """RFS-AE-008: EF.FATIGUED is a boolean — no ConditionInstance created.
    The boolean is read directly from entity dict, not from EF.CONDITIONS list.
    """
    entity = _barb_entity(fatigued=True)
    ws = _ws(entity)

    # Verify EF.FATIGUED is a boolean, not a condition object
    assert entity[EF.FATIGUED] is True, "EF.FATIGUED should be boolean True"
    assert not isinstance(entity[EF.FATIGUED], dict), "EF.FATIGUED must NOT be a ConditionInstance dict"

    # get_save_bonus should not raise — confirm it reads the boolean correctly
    ref_bonus = get_save_bonus(ws, "barb", SaveType.REF)
    assert ref_bonus == entity[EF.SAVE_REF] - 2
