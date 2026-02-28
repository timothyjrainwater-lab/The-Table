"""Gate tests: Paladin Remove Disease — WO-ENGINE-AF-WO3.

RD-001 through RD-008.

PHB p.44: Paladin can remove disease once per week (modeled as per full rest)
per 3 paladin levels. Formula: paladin_level // 3 uses per rest.

HOUSE_POLICY: 'per week' modeled as 'per full rest'.
"""

import pytest

from aidm.core.remove_disease_resolver import resolve_remove_disease
from aidm.core.rest_resolver import resolve_rest
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.schemas.intents import RemoveDiseaseIntent, RestIntent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _paladin(eid="paladin", paladin_level=6, *, rd_uses=None, rd_used=0):
    uses = rd_uses if rd_uses is not None else (paladin_level // 3 if paladin_level >= 3 else 0)
    entity = {
        EF.ENTITY_ID: eid,
        EF.CLASS_LEVELS: {"paladin": paladin_level},
        EF.LEVEL: paladin_level,
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 40,
        EF.SAVE_FORT: 5,
        EF.CON_MOD: 1,
        EF.CONDITIONS: [],
        EF.NONLETHAL_DAMAGE: 0,
    }
    if paladin_level >= 3:
        entity[EF.REMOVE_DISEASE_USES] = uses
        entity[EF.REMOVE_DISEASE_USED] = rd_used
    return entity


def _target(eid="target", *, diseased=False):
    entity = {
        EF.ENTITY_ID: eid,
        EF.CLASS_LEVELS: {},
        EF.HP_CURRENT: 20,
        EF.HP_MAX: 20,
    }
    if diseased:
        entity[EF.ACTIVE_DISEASES] = [
            {"disease_id": "filth_fever", "save_dc": 12, "incubation_days": 2}
        ]
    else:
        entity[EF.ACTIVE_DISEASES] = []
    return entity


def _ws(*entities):
    return WorldState(
        ruleset_version="3.5",
        entities={e[EF.ENTITY_ID]: e for e in entities},
        active_combat=None,
    )


def _intent(actor_id="paladin", target_id="target"):
    return RemoveDiseaseIntent(actor_id=actor_id, target_id=target_id)


# ---------------------------------------------------------------------------
# RD-001: Paladin L3 has 1 use per rest
# ---------------------------------------------------------------------------

def test_rd_001_paladin_l3_has_1_use():
    """RD-001: Paladin L3 has 1 use (3 // 3 = 1)."""
    paladin = _paladin(paladin_level=3)
    target = _target(diseased=True)
    ws = _ws(paladin, target)

    events, ws2 = resolve_remove_disease(_intent(), ws, 1, 0.0)

    cured = next((e for e in events if e.event_type == "remove_disease_cured"), None)
    assert cured is not None, "RD-001: Expected remove_disease_cured event at L3"
    assert cured.payload["uses_remaining"] == 0  # 1 - 1 = 0
    assert ws2.entities["paladin"][EF.REMOVE_DISEASE_USED] == 1


# ---------------------------------------------------------------------------
# RD-002: Paladin L6 has 2 uses per rest
# ---------------------------------------------------------------------------

def test_rd_002_paladin_l6_has_2_uses():
    """RD-002: Paladin L6 has 2 uses (6 // 3 = 2); after first use, 1 remains."""
    paladin = _paladin(paladin_level=6)  # 2 uses
    target = _target(diseased=True)
    ws = _ws(paladin, target)

    events, ws2 = resolve_remove_disease(_intent(), ws, 1, 0.0)

    cured = next((e for e in events if e.event_type == "remove_disease_cured"), None)
    assert cured is not None, "RD-002: Expected remove_disease_cured"
    assert cured.payload["uses_remaining"] == 1  # 2 - 1 = 1


# ---------------------------------------------------------------------------
# RD-003: Paladin L9 has 3 uses per rest
# ---------------------------------------------------------------------------

def test_rd_003_paladin_l9_has_3_uses():
    """RD-003: Paladin L9 has 3 uses (9 // 3 = 3); after first use, 2 remain."""
    paladin = _paladin(paladin_level=9)
    target = _target(diseased=True)
    ws = _ws(paladin, target)

    events, ws2 = resolve_remove_disease(_intent(), ws, 1, 0.0)

    cured = next((e for e in events if e.event_type == "remove_disease_cured"), None)
    assert cured is not None, "RD-003: Expected remove_disease_cured"
    assert cured.payload["uses_remaining"] == 2  # 3 - 1 = 2


# ---------------------------------------------------------------------------
# RD-004: Non-paladin (or L1 paladin) → remove_disease_invalid
# ---------------------------------------------------------------------------

def test_rd_004_non_paladin_invalid():
    """RD-004: Fighter using RemoveDiseaseIntent → remove_disease_invalid."""
    fighter = {
        EF.ENTITY_ID: "fighter",
        EF.CLASS_LEVELS: {"fighter": 10},
        EF.LEVEL: 10,
        EF.HP_CURRENT: 40,
        EF.HP_MAX: 40,
        EF.SAVE_FORT: 6,
        EF.CON_MOD: 2,
        EF.CONDITIONS: [],
        EF.NONLETHAL_DAMAGE: 0,
        # No REMOVE_DISEASE_USES — not a paladin
    }
    target = _target(diseased=True)
    ws = _ws(fighter, target)

    intent = RemoveDiseaseIntent(actor_id="fighter", target_id="target")
    events, ws2 = resolve_remove_disease(intent, ws, 1, 0.0)

    assert any(e.event_type == "remove_disease_invalid" for e in events), (
        "RD-004: Expected remove_disease_invalid for non-paladin"
    )
    assert not any(e.event_type == "remove_disease_cured" for e in events)
    # Disease not cleared
    assert ws2.entities["target"][EF.ACTIVE_DISEASES] != []


def test_rd_004b_paladin_l2_invalid():
    """RD-004b: Paladin L2 (below L3 threshold) → remove_disease_invalid."""
    paladin = {
        EF.ENTITY_ID: "paladin",
        EF.CLASS_LEVELS: {"paladin": 2},
        EF.LEVEL: 2,
        EF.HP_CURRENT: 15,
        EF.HP_MAX: 20,
        # No REMOVE_DISEASE_USES at L2
    }
    target = _target(diseased=True)
    ws = _ws(paladin, target)

    events, ws2 = resolve_remove_disease(_intent(), ws, 1, 0.0)

    assert any(e.event_type == "remove_disease_invalid" for e in events)


# ---------------------------------------------------------------------------
# RD-005: Target with DISEASED condition → condition cleared after use
# ---------------------------------------------------------------------------

def test_rd_005_disease_cleared():
    """RD-005: Target with active disease → ACTIVE_DISEASES cleared after use."""
    paladin = _paladin(paladin_level=6)
    target = _target(diseased=True)
    assert len(target[EF.ACTIVE_DISEASES]) == 1

    ws = _ws(paladin, target)

    events, ws2 = resolve_remove_disease(_intent(), ws, 1, 0.0)

    assert any(e.event_type == "remove_disease_cured" for e in events)
    assert ws2.entities["target"][EF.ACTIVE_DISEASES] == [], (
        "RD-005: ACTIVE_DISEASES should be empty after remove_disease_cured"
    )


# ---------------------------------------------------------------------------
# RD-006: No uses remaining → remove_disease_exhausted
# ---------------------------------------------------------------------------

def test_rd_006_no_uses_exhausted():
    """RD-006: Paladin with 0 uses remaining → remove_disease_exhausted."""
    paladin = _paladin(paladin_level=3, rd_uses=1, rd_used=1)  # 1 used, 0 remaining
    target = _target(diseased=True)
    ws = _ws(paladin, target)

    events, ws2 = resolve_remove_disease(_intent(), ws, 1, 0.0)

    assert any(e.event_type == "remove_disease_exhausted" for e in events), (
        "RD-006: Expected remove_disease_exhausted when no uses remain"
    )
    assert not any(e.event_type == "remove_disease_cured" for e in events)
    # Disease NOT cleared
    assert ws2.entities["target"][EF.ACTIVE_DISEASES] != []


# ---------------------------------------------------------------------------
# RD-007: Uses reset to 0 on RestIntent
# ---------------------------------------------------------------------------

def test_rd_007_uses_reset_on_rest():
    """RD-007: RestIntent (overnight) resets REMOVE_DISEASE_USED to 0, restores uses."""
    paladin = _paladin(paladin_level=6, rd_uses=2, rd_used=2)  # fully used
    paladin[EF.HP_CURRENT] = paladin[EF.HP_MAX]  # full HP
    ws = _ws(paladin)

    intent = RestIntent(rest_type="overnight")
    result = resolve_rest(intent, ws, actor_id="paladin")
    actor_after = result.world_state.entities["paladin"]

    assert actor_after[EF.REMOVE_DISEASE_USED] == 0, (
        "RD-007: REMOVE_DISEASE_USED must reset to 0 on full rest"
    )
    assert actor_after[EF.REMOVE_DISEASE_USES] == 2, (
        "RD-007: REMOVE_DISEASE_USES must be recalculated (paladin_level // 3 = 2)"
    )


# ---------------------------------------------------------------------------
# RD-008: Target with no disease → remove_disease_no_effect (graceful no-op)
# ---------------------------------------------------------------------------

def test_rd_008_no_disease_no_effect():
    """RD-008: Target has no active disease → remove_disease_no_effect event, use still consumed."""
    paladin = _paladin(paladin_level=6)
    target = _target(diseased=False)  # No disease
    ws = _ws(paladin, target)

    events, ws2 = resolve_remove_disease(_intent(), ws, 1, 0.0)

    assert any(e.event_type == "remove_disease_no_effect" for e in events), (
        "RD-008: Expected remove_disease_no_effect when target has no disease"
    )
    assert not any(e.event_type == "remove_disease_cured" for e in events)
    # Use IS consumed (paladin acted, even if no disease was present)
    assert ws2.entities["paladin"][EF.REMOVE_DISEASE_USED] == 1
