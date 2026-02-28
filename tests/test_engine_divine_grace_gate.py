"""
ENGINE GATE -- WO-ENGINE-DIVINE-GRACE-001: Paladin Divine Grace
Tests DG-001 through DG-008.
PHB Paladin p.44.
"""
from aidm.core.save_resolver import get_save_bonus
from aidm.schemas.saves import SaveType
from aidm.schemas.entity_fields import EF
from aidm.core.state import WorldState


def _make_ws(entity_dict):
    return WorldState(
        ruleset_version="3.5",
        entities={"pal": entity_dict},
        active_combat=None,
    )


def _base_paladin(paladin_level=2, cha_score=14):
    """Minimal paladin entity dict with given level and CHA score.

    EF.SAVE_* fields are Type 2 (base + ability_mod baked at chargen).
    WO-ENGINE-SAVE-DOUBLE-COUNT-FIX-001.
    """
    cha_mod = (cha_score - 10) // 2
    con_mod = 1
    dex_mod = 0
    wis_mod = 0
    return {
        EF.CLASS_LEVELS: {"paladin": paladin_level},
        EF.CHA_MOD: cha_mod,
        EF.SAVE_FORT: 4 + con_mod,   # Type 2: base 4 + CON 1 baked
        EF.SAVE_REF: 2 + dex_mod,    # Type 2: base 2 + DEX 0 baked
        EF.SAVE_WILL: 2 + wis_mod,   # Type 2: base 2 + WIS 0 baked
        EF.CON_MOD: con_mod,
        EF.DEX_MOD: dex_mod,
        EF.WIS_MOD: wis_mod,
        EF.CONDITIONS: [],
        EF.FEATS: [],
        EF.INSPIRE_COURAGE_ACTIVE: False,
        EF.INSPIRE_COURAGE_BONUS: 0,
    }


def test_dg001_paladin2_cha14_fort():
    """DG-001: Paladin 2, CHA 14 (mod +2): Fort save includes +2 divine grace."""
    entity = _base_paladin(paladin_level=2, cha_score=14)
    ws = _make_ws(entity)
    bonus = get_save_bonus(ws, "pal", SaveType.FORT)
    # base_fort=4, con_mod=1, divine_grace=2 -> 7
    assert bonus == 7, f"Expected 7, got {bonus}"


def test_dg002_paladin2_cha14_ref():
    """DG-002: Paladin 2, CHA 14 (mod +2): Ref save includes +2."""
    entity = _base_paladin(paladin_level=2, cha_score=14)
    ws = _make_ws(entity)
    bonus = get_save_bonus(ws, "pal", SaveType.REF)
    # base_ref=2, dex_mod=0, divine_grace=2 -> 4
    assert bonus == 4, f"Expected 4, got {bonus}"


def test_dg003_paladin2_cha14_will():
    """DG-003: Paladin 2, CHA 14 (mod +2): Will save includes +2."""
    entity = _base_paladin(paladin_level=2, cha_score=14)
    ws = _make_ws(entity)
    bonus = get_save_bonus(ws, "pal", SaveType.WILL)
    # base_will=2, wis_mod=0, divine_grace=2 -> 4
    assert bonus == 4, f"Expected 4, got {bonus}"


def test_dg004_paladin2_cha10_no_bonus():
    """DG-004: Paladin 2, CHA 10 (mod 0): no Divine Grace bonus."""
    entity = _base_paladin(paladin_level=2, cha_score=10)
    ws = _make_ws(entity)
    bonus = get_save_bonus(ws, "pal", SaveType.FORT)
    # base_fort=4, con_mod=1, divine_grace=0 -> 5
    assert bonus == 5, f"Expected 5 (no grace), got {bonus}"


def test_dg005_paladin2_cha8_no_bonus():
    """DG-005: Paladin 2, CHA 8 (mod -1): no Divine Grace bonus (not positive)."""
    entity = _base_paladin(paladin_level=2, cha_score=8)
    ws = _make_ws(entity)
    bonus = get_save_bonus(ws, "pal", SaveType.FORT)
    # base_fort=4, con_mod=1, divine_grace=0 -> 5
    assert bonus == 5, f"Expected 5 (no grace for negative cha_mod), got {bonus}"


def test_dg006_paladin1_no_divine_grace():
    """DG-006: Paladin 1: Divine Grace not yet gained (unlocks at level 2)."""
    entity = _base_paladin(paladin_level=1, cha_score=14)
    ws = _make_ws(entity)
    bonus = get_save_bonus(ws, "pal", SaveType.FORT)
    # base_fort=4, con_mod=1, divine_grace=0 -> 5
    assert bonus == 5, f"Expected 5 (paladin 1, no grace yet), got {bonus}"


def test_dg007_non_paladin_no_bonus():
    """DG-007: Non-paladin with CHA 18: no Divine Grace bonus."""
    fighter = {
        EF.CLASS_LEVELS: {"fighter": 5},
        EF.CHA_MOD: 4,
        EF.SAVE_FORT: 4 + 2,    # Type 2: base 4 + CON 2 baked
        EF.SAVE_REF: 2 + 0,     # Type 2: base 2 + DEX 0 baked
        EF.SAVE_WILL: 2 + 0,    # Type 2: base 2 + WIS 0 baked
        EF.CON_MOD: 2,
        EF.DEX_MOD: 0,
        EF.WIS_MOD: 0,
        EF.CONDITIONS: [],
        EF.FEATS: [],
        EF.INSPIRE_COURAGE_ACTIVE: False,
        EF.INSPIRE_COURAGE_BONUS: 0,
    }
    ws = _make_ws(fighter)
    bonus = get_save_bonus(ws, "pal", SaveType.FORT)
    # base=4, con=2, no grace -> 6
    assert bonus == 6, f"Expected 6 (fighter, no grace), got {bonus}"


def test_dg008_divine_grace_stacks_great_fortitude():
    """DG-008: Paladin 2, CHA 14 + Great Fortitude: +2 feat + +2 grace = +4 on Fort."""
    entity = _base_paladin(paladin_level=2, cha_score=14)
    entity[EF.FEATS] = ["great_fortitude"]
    ws = _make_ws(entity)
    bonus = get_save_bonus(ws, "pal", SaveType.FORT)
    # base=4, con=1, great_fortitude=2, divine_grace=2 -> 9
    assert bonus == 9, f"Expected 9 (base+con+gf+grace), got {bonus}"
