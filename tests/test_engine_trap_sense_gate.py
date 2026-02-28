"""Gate tests — TSB-AE-001 through TSB-AE-008
WO-AE-WO4: Trap Sense — chargen write + save_resolver consume.
PHB p.26 (Barbarian): "A barbarian gains a +1 bonus on Reflex saves made to avoid traps
  and a +1 bonus to AC against attacks made by traps at 3rd level."
PHB p.51 (Rogue): "A rogue gains an intuitive sense that alerts her to danger from traps,
  giving her a +1 bonus on Reflex saves made to avoid traps and a +1 dodge bonus to AC
  against attacks made by traps at 3rd level."
New field: EF.TRAP_SENSE_BONUS = (barb_level // 3) + (rogue_level // 3).
Consume: save_resolver fires only when save_type=REF and save_descriptor="trap".
"""

import pytest
from aidm.chargen.builder import build_character, _build_multiclass_character
from aidm.core.save_resolver import get_save_bonus
from aidm.schemas.saves import SaveType
from aidm.schemas.entity_fields import EF
from aidm.core.state import WorldState


def _ws(entity: dict) -> WorldState:
    return WorldState(ruleset_version="3.5", entities={entity[EF.ENTITY_ID]: entity}, active_combat=None)


# ── Chargen write tests ─────────────────────────────────────────────────────

def test_tsb_ae_001_barbarian_l3_trap_sense_1():
    """TSB-AE-001: Barbarian L3 gets TRAP_SENSE_BONUS = 1 (3 // 3 = 1)."""
    entity = build_character("human", "barbarian", level=3,
                             ability_overrides={"str": 16, "dex": 12, "con": 14,
                                               "int": 8, "wis": 10, "cha": 8})
    assert entity.get(EF.TRAP_SENSE_BONUS, 0) == 1, (
        f"Barbarian L3 should have TRAP_SENSE_BONUS=1. Got {entity.get(EF.TRAP_SENSE_BONUS)}"
    )


def test_tsb_ae_002_barbarian_l2_trap_sense_0():
    """TSB-AE-002: Barbarian L2 gets TRAP_SENSE_BONUS = 0 (2 // 3 = 0)."""
    entity = build_character("human", "barbarian", level=2,
                             ability_overrides={"str": 16, "dex": 12, "con": 14,
                                               "int": 8, "wis": 10, "cha": 8})
    assert entity.get(EF.TRAP_SENSE_BONUS, 0) == 0, (
        f"Barbarian L2 should have TRAP_SENSE_BONUS=0. Got {entity.get(EF.TRAP_SENSE_BONUS)}"
    )


def test_tsb_ae_003_rogue_l3_trap_sense_1():
    """TSB-AE-003: Rogue L3 gets TRAP_SENSE_BONUS = 1 (3 // 3 = 1)."""
    entity = build_character("human", "rogue", level=3,
                             ability_overrides={"str": 10, "dex": 16, "con": 12,
                                               "int": 14, "wis": 10, "cha": 12})
    assert entity.get(EF.TRAP_SENSE_BONUS, 0) == 1, (
        f"Rogue L3 should have TRAP_SENSE_BONUS=1. Got {entity.get(EF.TRAP_SENSE_BONUS)}"
    )


def test_tsb_ae_004_fighter_trap_sense_0():
    """TSB-AE-004: Fighter (non-barb, non-rogue) gets TRAP_SENSE_BONUS = 0."""
    entity = build_character("human", "fighter", level=6,
                             ability_overrides={"str": 16, "dex": 12, "con": 14,
                                               "int": 8, "wis": 10, "cha": 8})
    assert entity.get(EF.TRAP_SENSE_BONUS, 0) == 0, (
        f"Fighter L6 should have TRAP_SENSE_BONUS=0. Got {entity.get(EF.TRAP_SENSE_BONUS)}"
    )


# ── Resolver consume tests ──────────────────────────────────────────────────

def _trap_sense_entity(trap_bonus: int, entity_id: str = "hero") -> dict:
    """Minimal entity with a pre-set TRAP_SENSE_BONUS (bypasses chargen for resolver tests)."""
    return {
        EF.ENTITY_ID: entity_id,
        EF.SAVE_FORT: 3,
        EF.SAVE_REF: 4,
        EF.SAVE_WILL: 2,
        EF.FEATS: [],
        EF.CLASS_LEVELS: {},
        EF.RACE: "human",
        EF.RACIAL_SAVE_BONUS: 0,
        EF.SAVE_BONUS_POISON: 0,
        EF.SAVE_BONUS_SPELLS: 0,
        EF.SAVE_BONUS_ENCHANTMENT: 0,
        EF.CONDITIONS: [],
        EF.TEAM: "players",
        EF.TRAP_SENSE_BONUS: trap_bonus,
        EF.FATIGUED: False,
    }


def test_tsb_ae_005_trap_sense_fires_on_ref_trap():
    """TSB-AE-005: TRAP_SENSE_BONUS fires when save_type=REF and save_descriptor='trap'."""
    entity = _trap_sense_entity(trap_bonus=2)
    ws = _ws(entity)

    bonus_trap = get_save_bonus(ws, "hero", SaveType.REF, save_descriptor="trap")
    base_ref = entity[EF.SAVE_REF]

    assert bonus_trap >= base_ref + 2, (
        f"Trap Sense +2 should fire on Ref/trap save. Got {bonus_trap}, expected >= {base_ref + 2}"
    )


def test_tsb_ae_006_trap_sense_does_not_fire_on_ref_empty():
    """TSB-AE-006: TRAP_SENSE_BONUS does NOT fire when save_descriptor='' (generic Ref save)."""
    entity = _trap_sense_entity(trap_bonus=2)
    ws = _ws(entity)

    bonus_generic = get_save_bonus(ws, "hero", SaveType.REF, save_descriptor="")

    entity_no_ts = dict(entity)
    entity_no_ts[EF.TRAP_SENSE_BONUS] = 0
    ws_no_ts = _ws(entity_no_ts)
    baseline = get_save_bonus(ws_no_ts, "hero", SaveType.REF, save_descriptor="")

    assert bonus_generic == baseline, (
        f"Trap Sense should NOT fire on generic Ref save. "
        f"Got {bonus_generic}, expected {baseline}."
    )


def test_tsb_ae_007_trap_sense_does_not_fire_on_fort():
    """TSB-AE-007: TRAP_SENSE_BONUS does NOT fire on Fort save even with 'trap' descriptor."""
    entity = _trap_sense_entity(trap_bonus=2)
    ws = _ws(entity)

    bonus_fort = get_save_bonus(ws, "hero", SaveType.FORT, save_descriptor="trap")

    entity_no_ts = dict(entity)
    entity_no_ts[EF.TRAP_SENSE_BONUS] = 0
    ws_no_ts = _ws(entity_no_ts)
    baseline = get_save_bonus(ws_no_ts, "hero", SaveType.FORT, save_descriptor="trap")

    assert bonus_fort == baseline, (
        f"Trap Sense should NOT fire on Fort save. Got {bonus_fort}, expected {baseline}."
    )


def test_tsb_ae_008_barbarian_l6_trap_sense_2():
    """TSB-AE-008: Barbarian L6 gets TRAP_SENSE_BONUS = 2 (6 // 3 = 2). End-to-end chargen→resolve."""
    entity = build_character("human", "barbarian", level=6,
                             ability_overrides={"str": 16, "dex": 12, "con": 14,
                                               "int": 8, "wis": 10, "cha": 8})
    assert entity.get(EF.TRAP_SENSE_BONUS, 0) == 2, (
        f"Barbarian L6 TRAP_SENSE_BONUS should be 2. Got {entity.get(EF.TRAP_SENSE_BONUS)}"
    )

    ws = _ws(entity)
    bonus_trap = get_save_bonus(ws, entity[EF.ENTITY_ID], SaveType.REF, save_descriptor="trap")
    base_ref = entity[EF.SAVE_REF]

    assert bonus_trap >= base_ref + 2, (
        f"Barbarian L6 Trap Sense end-to-end: Ref/trap bonus should be >= {base_ref + 2}. "
        f"Got {bonus_trap}"
    )
