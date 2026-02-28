"""ENGINE-SAVE-FEATS Gate — Great Fortitude / Iron Will / Lightning Reflexes (10 tests).

Gate: ENGINE-SAVE-FEATS
Tests: SF-01 through SF-10
WO: WO-ENGINE-SAVE-FEATS-001
PHB p.93-96: Saving throw feats each grant +2 to the corresponding save.
"""

import pytest
from copy import deepcopy

from aidm.core.state import WorldState
from aidm.core.save_resolver import get_save_bonus
from aidm.schemas.entity_fields import EF
from aidm.schemas.saves import SaveType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entity(
    eid="pc",
    save_fort=2,
    save_ref=1,
    save_will=0,
    con_mod=1,
    dex_mod=2,
    wis_mod=0,
    feats=None,
):
    """Create synthetic entity.

    save_fort/ref/will are base progression values. This helper auto-bakes
    the ability mod into EF.SAVE_* per Type 2 field contract
    (WO-ENGINE-SAVE-DOUBLE-COUNT-FIX-001).
    """
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: 20,
        EF.HP_MAX: 20,
        EF.AC: 12,
        EF.DEFEATED: False,
        EF.SAVE_FORT: save_fort + con_mod,   # Type 2: base + ability_mod baked
        EF.SAVE_REF: save_ref + dex_mod,     # Type 2: base + ability_mod baked
        EF.SAVE_WILL: save_will + wis_mod,   # Type 2: base + ability_mod baked
        EF.CON_MOD: con_mod,
        EF.DEX_MOD: dex_mod,
        EF.WIS_MOD: wis_mod,
        EF.CONDITIONS: {},
        EF.FEATS: feats if feats is not None else [],
        EF.INSPIRE_COURAGE_ACTIVE: False,
        EF.INSPIRE_COURAGE_BONUS: 0,
    }


def _world(entities):
    return WorldState(
        ruleset_version="3.5e",
        entities=entities,
        active_combat={"initiative_order": list(entities.keys()), "aoo_used_this_round": []},
    )


# ===========================================================================
# SF-01: No feat — Fort save equals base + CON_MOD only
# ===========================================================================
def test_sf01_no_feat_fort_baseline():
    """SF-01: Entity with no feat has Fort = base + CON_MOD (no feat bonus)."""
    ent = _entity(save_fort=2, con_mod=1, feats=[])
    ws = _world({"pc": ent})
    bonus = get_save_bonus(ws, "pc", SaveType.FORT)
    assert bonus == 3, f"Expected 3 (2+1), got {bonus}"


# ===========================================================================
# SF-02: Great Fortitude adds +2 to Fort save
# ===========================================================================
def test_sf02_great_fortitude_adds_two_to_fort():
    """SF-02: Great Fortitude grants +2 to Fortitude saves."""
    ent = _entity(save_fort=2, con_mod=1, feats=["great_fortitude"])
    ws = _world({"pc": ent})
    bonus = get_save_bonus(ws, "pc", SaveType.FORT)
    assert bonus == 5, f"Expected 5 (2+1+2), got {bonus}"


# ===========================================================================
# SF-03: Great Fortitude does NOT affect Reflex
# ===========================================================================
def test_sf03_great_fortitude_no_effect_on_reflex():
    """SF-03: Great Fortitude only applies to Fort — not Reflex."""
    ent = _entity(save_ref=1, dex_mod=2, feats=["great_fortitude"])
    ws = _world({"pc": ent})
    bonus = get_save_bonus(ws, "pc", SaveType.REF)
    assert bonus == 3, f"Expected 3 (1+2, no feat), got {bonus}"


# ===========================================================================
# SF-04: Great Fortitude does NOT affect Will
# ===========================================================================
def test_sf04_great_fortitude_no_effect_on_will():
    """SF-04: Great Fortitude only applies to Fort — not Will."""
    ent = _entity(save_will=1, wis_mod=1, feats=["great_fortitude"])
    ws = _world({"pc": ent})
    bonus = get_save_bonus(ws, "pc", SaveType.WILL)
    assert bonus == 2, f"Expected 2 (1+1, no feat), got {bonus}"


# ===========================================================================
# SF-05: Iron Will adds +2 to Will save
# ===========================================================================
def test_sf05_iron_will_adds_two_to_will():
    """SF-05: Iron Will grants +2 to Will saves."""
    ent = _entity(save_will=0, wis_mod=1, feats=["iron_will"])
    ws = _world({"pc": ent})
    bonus = get_save_bonus(ws, "pc", SaveType.WILL)
    assert bonus == 3, f"Expected 3 (0+1+2), got {bonus}"


# ===========================================================================
# SF-06: Lightning Reflexes adds +2 to Reflex save
# ===========================================================================
def test_sf06_lightning_reflexes_adds_two_to_reflex():
    """SF-06: Lightning Reflexes grants +2 to Reflex saves."""
    ent = _entity(save_ref=1, dex_mod=2, feats=["lightning_reflexes"])
    ws = _world({"pc": ent})
    bonus = get_save_bonus(ws, "pc", SaveType.REF)
    assert bonus == 5, f"Expected 5 (1+2+2), got {bonus}"


# ===========================================================================
# SF-07: Multiple save feats on same entity — each applies to correct save
# ===========================================================================
def test_sf07_multiple_save_feats_stack_correctly():
    """SF-07: All three save feats stack — each applies to its own save type."""
    feats = ["great_fortitude", "iron_will", "lightning_reflexes"]
    ent = _entity(save_fort=2, save_ref=1, save_will=0, con_mod=1, dex_mod=2, wis_mod=1, feats=feats)
    ws = _world({"pc": ent})
    fort = get_save_bonus(ws, "pc", SaveType.FORT)
    ref = get_save_bonus(ws, "pc", SaveType.REF)
    will = get_save_bonus(ws, "pc", SaveType.WILL)
    assert fort == 5, f"Fort: expected 5 (2+1+2), got {fort}"
    assert ref == 5, f"Ref: expected 5 (1+2+2), got {ref}"
    assert will == 3, f"Will: expected 3 (0+1+2), got {will}"


# ===========================================================================
# SF-08: Lightning Reflexes does NOT affect Fort
# ===========================================================================
def test_sf08_lightning_reflexes_no_effect_on_fort():
    """SF-08: Lightning Reflexes only applies to Reflex — not Fort."""
    ent = _entity(save_fort=3, con_mod=2, feats=["lightning_reflexes"])
    ws = _world({"pc": ent})
    bonus = get_save_bonus(ws, "pc", SaveType.FORT)
    assert bonus == 5, f"Expected 5 (3+2, no feat), got {bonus}"


# ===========================================================================
# SF-09: Iron Will does NOT affect Reflex
# ===========================================================================
def test_sf09_iron_will_no_effect_on_reflex():
    """SF-09: Iron Will only applies to Will — not Reflex."""
    ent = _entity(save_ref=2, dex_mod=3, feats=["iron_will"])
    ws = _world({"pc": ent})
    bonus = get_save_bonus(ws, "pc", SaveType.REF)
    assert bonus == 5, f"Expected 5 (2+3, no feat), got {bonus}"


# ===========================================================================
# SF-10: Great Fortitude stacks with Inspire Courage (both add to Fort)
# ===========================================================================
def test_sf10_great_fortitude_stacks_with_inspire_courage():
    """SF-10: Great Fortitude bonus stacks with inspire courage morale bonus on fear Fort save.
    WO-AE-WO3: IC only fires for fear/charm descriptors (PHB p.29). Test uses save_descriptor='fear'.
    """
    ent = _entity(save_fort=2, con_mod=1, feats=["great_fortitude"])
    ent[EF.INSPIRE_COURAGE_ACTIVE] = True
    ent[EF.INSPIRE_COURAGE_BONUS] = 1
    ws = _world({"pc": ent})
    bonus = get_save_bonus(ws, "pc", SaveType.FORT, save_descriptor="fear")
    # base=2, con=1, inspire=1, feat=2 → 6
    assert bonus == 6, f"Expected 6 (2+1+1+2), got {bonus}"
