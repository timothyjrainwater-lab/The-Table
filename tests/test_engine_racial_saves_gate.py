"""Gate tests: WO-ENGINE-RACIAL-SAVES-001

ENGINE-RACIAL-SAVES: Racial saving throw bonuses (PHB Table 2-1).
- Halfling: +1 all saves (EF.RACIAL_SAVE_BONUS)
- Dwarf: +2 vs poison (save_descriptor="poison"), +2 vs spells/SLAs (save_descriptor="spell")
- Gnome +2 vs illusions: BLOCKED — spell school not available in save context.
  FINDING-ENGINE-GNOME-ILLUSION-SAVE-001 filed.

RSV-001 – RSV-008 (8 tests)
"""
from aidm.core.save_resolver import get_save_bonus
from aidm.schemas.saves import SaveType
from aidm.schemas.entity_fields import EF
from aidm.core.state import WorldState
from aidm.chargen.builder import build_character


def _make_ws(entity_dict, actor_id="actor"):
    return WorldState(
        ruleset_version="3.5",
        entities={actor_id: entity_dict},
        active_combat=None,
    )


def _base_entity(race_save_bonus=0, save_bonus_poison=0, save_bonus_spells=0,
                 fort=2, ref=2, will=2):
    """Minimal entity for save testing."""
    e = {
        EF.CLASS_LEVELS: {},
        EF.SAVE_FORT: fort,
        EF.SAVE_REF: ref,
        EF.SAVE_WILL: will,
        EF.CON_MOD: 0,
        EF.DEX_MOD: 0,
        EF.WIS_MOD: 0,
        EF.CHA_MOD: 0,
        EF.CONDITIONS: [],
        EF.FEATS: [],
        EF.INSPIRE_COURAGE_ACTIVE: False,
        EF.INSPIRE_COURAGE_BONUS: 0,
    }
    if race_save_bonus:
        e[EF.RACIAL_SAVE_BONUS] = race_save_bonus
    if save_bonus_poison:
        e[EF.SAVE_BONUS_POISON] = save_bonus_poison
    if save_bonus_spells:
        e[EF.SAVE_BONUS_SPELLS] = save_bonus_spells
    return e


# ---------------------------------------------------------------------------
# RSV-001 – RSV-003: Halfling +1 all saves
# ---------------------------------------------------------------------------

def test_rsv_001_halfling_fort():
    """RSV-001: Halfling → +1 Fort save (racial_save_bonus applies to Fort)."""
    entity = _base_entity(race_save_bonus=1, fort=3)
    ws = _make_ws(entity)
    bonus = get_save_bonus(ws, "actor", SaveType.FORT)
    # base_fort=3, con=0, racial=1 → 4
    assert bonus == 4


def test_rsv_002_halfling_ref():
    """RSV-002: Halfling → +1 Ref save (same field covers all three)."""
    entity = _base_entity(race_save_bonus=1, ref=2)
    ws = _make_ws(entity)
    bonus = get_save_bonus(ws, "actor", SaveType.REF)
    # base_ref=2, dex=0, racial=1 → 3
    assert bonus == 3


def test_rsv_003_halfling_will():
    """RSV-003: Halfling → +1 Will save."""
    entity = _base_entity(race_save_bonus=1, will=1)
    ws = _make_ws(entity)
    bonus = get_save_bonus(ws, "actor", SaveType.WILL)
    # base_will=1, wis=0, racial=1 → 2
    assert bonus == 2


# ---------------------------------------------------------------------------
# RSV-004 – RSV-005: Dwarf conditional bonuses
# ---------------------------------------------------------------------------

def test_rsv_004_dwarf_fort_vs_poison():
    """RSV-004: Dwarf → +2 Fort vs poison (save_descriptor='poison')."""
    entity = _base_entity(save_bonus_poison=2, fort=2)
    ws = _make_ws(entity)
    bonus = get_save_bonus(ws, "actor", SaveType.FORT, save_descriptor="poison")
    # base=2, con=0, poison=2 → 4
    assert bonus == 4


def test_rsv_004b_dwarf_fort_without_descriptor():
    """RSV-004b: Dwarf poison bonus absent without save_descriptor='poison'."""
    entity = _base_entity(save_bonus_poison=2, fort=2)
    ws = _make_ws(entity)
    bonus = get_save_bonus(ws, "actor", SaveType.FORT)
    # base=2, no poison → 2
    assert bonus == 2


def test_rsv_005_dwarf_vs_spell():
    """RSV-005: Dwarf → +2 save vs spell (save_descriptor='spell')."""
    entity = _base_entity(save_bonus_spells=2, will=3)
    ws = _make_ws(entity)
    bonus = get_save_bonus(ws, "actor", SaveType.WILL, save_descriptor="spell")
    # base=3, wis=0, spell=2 → 5
    assert bonus == 5


# ---------------------------------------------------------------------------
# RSV-006: Gnome vs illusion — BLOCKED
# ---------------------------------------------------------------------------

def test_rsv_006_gnome_illusion_blocked():
    """RSV-006: Gnome +2 vs illusion save — BLOCKED.

    FINDING-ENGINE-GNOME-ILLUSION-SAVE-001 (OPEN/LOW):
    SaveContext carries no spell school field. get_save_bonus() has no
    save_descriptor for 'illusion'. Gnome EF.RACIAL_SAVE_BONUS not set
    (no all-save bonus; only +2 vs illusion). Deferred until spell school
    context is added to SaveContext.

    Test confirms gnome entity has no general racial save bonus.
    """
    entity = build_character("gnome", "wizard", level=1)
    # Gnome has no EF.RACIAL_SAVE_BONUS (all-saves) — illusion-only bonus deferred
    assert entity.get(EF.RACIAL_SAVE_BONUS, 0) == 0


# ---------------------------------------------------------------------------
# RSV-007: Human — no racial save bonus
# ---------------------------------------------------------------------------

def test_rsv_007_human_no_racial_bonus():
    """RSV-007: Human → no racial save bonus (regression guard)."""
    entity = build_character("human", "fighter", level=1)
    assert entity.get(EF.RACIAL_SAVE_BONUS, 0) == 0
    assert entity.get(EF.SAVE_BONUS_POISON, 0) == 0
    assert entity.get(EF.SAVE_BONUS_SPELLS, 0) == 0


# ---------------------------------------------------------------------------
# RSV-008: Halfling + Great Fortitude — stacking
# ---------------------------------------------------------------------------

def test_rsv_008_halfling_stacks_with_great_fortitude():
    """RSV-008: Halfling racial +1 stacks with Great Fortitude feat +2 → total +3 Fort."""
    entity = _base_entity(race_save_bonus=1, fort=2)
    entity[EF.FEATS] = ["great_fortitude"]
    ws = _make_ws(entity)
    bonus = get_save_bonus(ws, "actor", SaveType.FORT)
    # base=2, racial=1, great_fortitude=2 → 5
    assert bonus == 5
