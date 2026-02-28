"""Gate tests — BSS-AE-001 through BSS-AE-004
WO-AE-WO3: Bardic Inspire Courage save bonus scoped to fear/charm saves only.
PHB p.29: Inspire Courage grants +morale bonus vs charm and fear effects.
Fix: save_resolver.get_save_bonus() — inspire_courage_bonus now only fires when
     save_descriptor in ("fear", "charm"); previously applied to ALL saves.
"""

import pytest
from aidm.core.save_resolver import get_save_bonus
from aidm.schemas.saves import SaveType
from aidm.schemas.entity_fields import EF
from aidm.core.state import WorldState


def _ws(entity: dict) -> WorldState:
    return WorldState(ruleset_version="3.5", entities={entity[EF.ENTITY_ID]: entity}, active_combat=None)


def _bard_buffed_entity(entity_id: str = "hero") -> dict:
    """Entity with active Inspire Courage +2."""
    return {
        EF.ENTITY_ID: entity_id,
        EF.SAVE_FORT: 3,
        EF.SAVE_REF: 4,
        EF.SAVE_WILL: 5,
        EF.FEATS: [],
        EF.CLASS_LEVELS: {},
        EF.RACE: "human",
        EF.RACIAL_SAVE_BONUS: 0,
        EF.SAVE_BONUS_POISON: 0,
        EF.SAVE_BONUS_SPELLS: 0,
        EF.SAVE_BONUS_ENCHANTMENT: 0,
        EF.CONDITIONS: [],
        EF.TEAM: "players",
        EF.INSPIRE_COURAGE_ACTIVE: True,
        EF.INSPIRE_COURAGE_BONUS: 2,
    }


def test_bss_ae_001_inspire_courage_fires_on_fear_save():
    """BSS-AE-001: Inspire Courage +2 fires when save_descriptor='fear'."""
    entity = _bard_buffed_entity()
    ws = _ws(entity)

    bonus = get_save_bonus(ws, "hero", SaveType.WILL, save_descriptor="fear")
    base = entity[EF.SAVE_WILL]

    assert bonus >= base + 2, (
        f"Inspire Courage +2 should fire on fear save. "
        f"Got {bonus}, expected >= {base + 2}"
    )


def test_bss_ae_002_inspire_courage_fires_on_charm_save():
    """BSS-AE-002: Inspire Courage +2 fires when save_descriptor='charm'."""
    entity = _bard_buffed_entity()
    ws = _ws(entity)

    bonus = get_save_bonus(ws, "hero", SaveType.WILL, save_descriptor="charm")
    base = entity[EF.SAVE_WILL]

    assert bonus >= base + 2, (
        f"Inspire Courage +2 should fire on charm save. "
        f"Got {bonus}, expected >= {base + 2}"
    )


def test_bss_ae_003_inspire_courage_does_not_fire_on_empty_descriptor():
    """BSS-AE-003: Inspire Courage +2 does NOT fire when save_descriptor='' (generic Will save).
    Before fix: bonus applied to all saves regardless of descriptor.
    After fix: only fires for fear/charm.
    """
    entity = _bard_buffed_entity()
    ws = _ws(entity)

    bonus_generic = get_save_bonus(ws, "hero", SaveType.WILL, save_descriptor="")

    # Build same entity without inspire courage to get baseline
    entity_no_bard = dict(entity)
    entity_no_bard[EF.INSPIRE_COURAGE_ACTIVE] = False
    entity_no_bard[EF.INSPIRE_COURAGE_BONUS] = 0
    ws_no_bard = _ws(entity_no_bard)
    baseline = get_save_bonus(ws_no_bard, "hero", SaveType.WILL, save_descriptor="")

    assert bonus_generic == baseline, (
        f"Inspire Courage should NOT fire on generic Will save (no descriptor). "
        f"Got {bonus_generic}, expected {baseline} (same as without inspire courage)."
    )


def test_bss_ae_004_inspire_courage_does_not_fire_on_fort_save():
    """BSS-AE-004: Inspire Courage +2 does NOT fire on Fort save (non-fear/charm descriptor).
    Fort saves are not charm or fear saves — bonus should not apply.
    """
    entity = _bard_buffed_entity()
    ws = _ws(entity)

    bonus_fort = get_save_bonus(ws, "hero", SaveType.FORT, save_descriptor="")

    entity_no_bard = dict(entity)
    entity_no_bard[EF.INSPIRE_COURAGE_ACTIVE] = False
    entity_no_bard[EF.INSPIRE_COURAGE_BONUS] = 0
    ws_no_bard = _ws(entity_no_bard)
    baseline = get_save_bonus(ws_no_bard, "hero", SaveType.FORT, save_descriptor="")

    assert bonus_fort == baseline, (
        f"Inspire Courage should NOT fire on Fort save. "
        f"Got {bonus_fort}, expected {baseline}."
    )
