"""Gate ENGINE-POISON-DISEASE — WO-ENGINE-POISON-DISEASE-001

Tests:
PP-01: is_immune_to_poison returns True for undead entity
PP-02: is_immune_to_poison returns True for paladin level 3+
PP-03: apply_poison emits poison_save_initial event
PP-04: apply_poison on failed save applies initial ability damage and queues secondary
PP-05: process_poison_secondaries fires at secondary_due_round
PP-06: process_poison_secondaries clears poison from ACTIVE_POISONS after resolving
PP-07: apply_disease_exposure on failed save adds disease to ACTIVE_DISEASES
PP-08: process_disease_ticks fires and applies damage on failed save
PP-09: process_disease_ticks tracks consecutive_successes and cures on 2 in a row
PP-10: disease_cured event emitted and disease removed from ACTIVE_DISEASES
"""

import unittest.mock as mock
from copy import deepcopy
from typing import Any, Dict

import pytest

from aidm.schemas.entity_fields import EF
from aidm.core.poison_disease_resolver import (
    is_immune_to_poison,
    apply_poison,
    process_poison_secondaries,
    apply_disease_exposure,
    process_disease_ticks,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entity(eid: str = "fighter") -> Dict[str, Any]:
    return {
        EF.ENTITY_ID: eid,
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 30,
        EF.SAVE_FORT: 4,
        EF.CON_MOD: 2,
        EF.IS_UNDEAD: False,
        EF.CLASS_LEVELS: {},
        EF.CONDITIONS: {},
    }


def _poison_stat(dc: int = 14) -> Dict[str, Any]:
    return {
        "poison_id": "giant_wasp_poison",
        "dc": dc,
        "initial_ability": "dex",
        "initial_amount": 1,
        "secondary_ability": "dex",
        "secondary_amount": 1,
    }


def _disease_stat(dc: int = 12) -> Dict[str, Any]:
    return {
        "disease_id": "filth_fever",
        "dc": dc,
        "incubation_rounds": 10,
        "interval_rounds": 10,
        "damage_ability": "dex",
        "damage_amount": 1,
    }


def _rng(rolls) -> mock.MagicMock:
    stream = mock.MagicMock()
    stream.randint.side_effect = list(rolls) + [10] * 50
    rng = mock.MagicMock()
    rng.stream.return_value = stream
    return rng


# ---------------------------------------------------------------------------
# PP-01: is_immune_to_poison — undead
# ---------------------------------------------------------------------------

def test_pp01_undead_immune_to_poison():
    entity = _entity()
    entity[EF.IS_UNDEAD] = True
    assert is_immune_to_poison(entity) is True


# ---------------------------------------------------------------------------
# PP-02: is_immune_to_poison — paladin level 3+ is NOT immune to poison
# (Paladin has Divine Health = disease immunity, NOT poison immunity per PHB p.44)
# WO-ENGINE-CLASS-IMMUNITY-001: corrected pre-existing bug
# ---------------------------------------------------------------------------

def test_pp02_paladin3_not_immune_to_poison():
    entity = _entity()
    entity[EF.CLASS_LEVELS] = {"paladin": 3}
    assert is_immune_to_poison(entity) is False


# ---------------------------------------------------------------------------
# PP-03: apply_poison emits poison_save_initial event
# ---------------------------------------------------------------------------

def test_pp03_apply_poison_emits_save_event():
    entity = _entity()
    rng = _rng([15])  # roll 15 → total 15+4+2=21 > dc 14 → saved
    entity_out, events = apply_poison(
        entity=entity,
        target_id="fighter",
        source_id="wasp",
        poison_stat=_poison_stat(dc=14),
        current_round=1,
        rng=rng,
        next_event_id=1,
        timestamp=0.0,
    )
    event_types = [ev["event_type"] for ev in events]
    assert "poison_save_initial" in event_types
    save_ev = next(ev for ev in events if ev["event_type"] == "poison_save_initial")
    assert save_ev["payload"]["target_id"] == "fighter"
    assert save_ev["payload"]["dc"] == 14


# ---------------------------------------------------------------------------
# PP-04: apply_poison on failed save applies initial ability damage + queues secondary
# ---------------------------------------------------------------------------

def test_pp04_apply_poison_failure_applies_damage():
    entity = _entity()
    entity[EF.SAVE_FORT] = 0
    entity[EF.CON_MOD] = 0
    # Roll 1 → total 1 < dc 14 → failed save
    rng = _rng([1])
    entity_out, events = apply_poison(
        entity=entity,
        target_id="fighter",
        source_id="wasp",
        poison_stat=_poison_stat(dc=14),
        current_round=1,
        rng=rng,
        next_event_id=1,
        timestamp=0.0,
    )
    # Ability damage applied
    event_types = [ev["event_type"] for ev in events]
    assert "ability_damaged" in event_types
    # Secondary queued
    assert len(entity_out.get(EF.ACTIVE_POISONS, [])) == 1
    secondary = entity_out[EF.ACTIVE_POISONS][0]
    assert secondary["secondary_due_round"] == 11  # round 1 + 10


# ---------------------------------------------------------------------------
# PP-05: process_poison_secondaries fires at secondary_due_round
# ---------------------------------------------------------------------------

def test_pp05_secondary_fires_at_due_round():
    entity = _entity()
    entity[EF.ACTIVE_POISONS] = [{
        "poison_id": "giant_wasp_poison",
        "dc": 14,
        "initial_done": True,
        "secondary_due_round": 11,
        "secondary_ability": "dex",
        "secondary_amount": 1,
    }]
    # Roll 15 → total 15+4+2=21 > 14 → saved
    rng = _rng([15])
    entity_out, events = process_poison_secondaries(
        entity=entity,
        target_id="fighter",
        current_round=11,
        rng=rng,
        next_event_id=1,
        timestamp=0.0,
    )
    event_types = [ev["event_type"] for ev in events]
    assert "poison_save_secondary" in event_types


# ---------------------------------------------------------------------------
# PP-06: process_poison_secondaries clears poison from ACTIVE_POISONS after resolving
# ---------------------------------------------------------------------------

def test_pp06_secondary_clears_poison():
    entity = _entity()
    entity[EF.ACTIVE_POISONS] = [{
        "poison_id": "giant_wasp_poison",
        "dc": 14,
        "initial_done": True,
        "secondary_due_round": 11,
        "secondary_ability": "dex",
        "secondary_amount": 1,
    }]
    rng = _rng([15])
    entity_out, events = process_poison_secondaries(
        entity=entity,
        target_id="fighter",
        current_round=11,
        rng=rng,
        next_event_id=1,
        timestamp=0.0,
    )
    # Secondary resolved — poison should be removed
    assert len(entity_out.get(EF.ACTIVE_POISONS, [])) == 0


# ---------------------------------------------------------------------------
# PP-07: apply_disease_exposure on failed save adds disease to ACTIVE_DISEASES
# ---------------------------------------------------------------------------

def test_pp07_disease_exposure_failure_contracts_disease():
    entity = _entity()
    entity[EF.SAVE_FORT] = 0
    entity[EF.CON_MOD] = 0
    # Roll 1 → total 1 < dc 12 → failed → contracted
    rng = _rng([1])
    entity_out, events = apply_disease_exposure(
        entity=entity,
        target_id="fighter",
        source_id="rat",
        disease_stat=_disease_stat(dc=12),
        current_round=1,
        rng=rng,
        next_event_id=1,
        timestamp=0.0,
    )
    event_types = [ev["event_type"] for ev in events]
    assert "disease_contracted" in event_types
    assert len(entity_out.get(EF.ACTIVE_DISEASES, [])) == 1
    disease = entity_out[EF.ACTIVE_DISEASES][0]
    assert disease["disease_id"] == "filth_fever"
    assert disease["next_save_round"] == 11  # round 1 + incubation 10


# ---------------------------------------------------------------------------
# PP-08: process_disease_ticks fires and applies damage on failed save
# ---------------------------------------------------------------------------

def test_pp08_disease_tick_applies_damage_on_fail():
    entity = _entity()
    entity[EF.SAVE_FORT] = 0
    entity[EF.CON_MOD] = 0
    entity[EF.ACTIVE_DISEASES] = [{
        "disease_id": "filth_fever",
        "dc": 12,
        "interval_rounds": 10,
        "next_save_round": 11,
        "consecutive_successes": 0,
        "damage_ability": "dex",
        "damage_amount": 1,
    }]
    # Roll 1 → total 1 < dc 12 → failed save → damage applied
    rng = _rng([1])
    entity_out, events = process_disease_ticks(
        entity=entity,
        target_id="fighter",
        current_round=11,
        rng=rng,
        next_event_id=1,
        timestamp=0.0,
    )
    event_types = [ev["event_type"] for ev in events]
    assert "disease_save" in event_types
    assert "ability_damaged" in event_types
    # Disease remains scheduled for next round
    assert len(entity_out.get(EF.ACTIVE_DISEASES, [])) == 1


# ---------------------------------------------------------------------------
# PP-09: process_disease_ticks tracks consecutive_successes
# ---------------------------------------------------------------------------

def test_pp09_disease_ticks_consecutive_successes():
    entity = _entity()
    entity[EF.ACTIVE_DISEASES] = [{
        "disease_id": "filth_fever",
        "dc": 12,
        "interval_rounds": 10,
        "next_save_round": 11,
        "consecutive_successes": 1,  # Already 1 success
        "damage_ability": "dex",
        "damage_amount": 1,
    }]
    # Roll 15 → total 15+4+2=21 > 12 → saved → consecutive = 2 → cured
    rng = _rng([15])
    entity_out, events = process_disease_ticks(
        entity=entity,
        target_id="fighter",
        current_round=11,
        rng=rng,
        next_event_id=1,
        timestamp=0.0,
    )
    event_types = [ev["event_type"] for ev in events]
    assert "disease_cured" in event_types
    # Cured — removed from list
    assert len(entity_out.get(EF.ACTIVE_DISEASES, [])) == 0


# ---------------------------------------------------------------------------
# PP-10: disease_cured event and disease removed from ACTIVE_DISEASES
# ---------------------------------------------------------------------------

def test_pp10_disease_cured_event_and_removal():
    entity = _entity()
    entity[EF.ACTIVE_DISEASES] = [{
        "disease_id": "filth_fever",
        "dc": 8,  # low DC — easy to succeed
        "interval_rounds": 10,
        "next_save_round": 5,
        "consecutive_successes": 0,
        "damage_ability": "dex",
        "damage_amount": 1,
    }]
    # Two separate ticks, first success then second success → cured
    # But process_disease_ticks processes only the current round; let's
    # simulate one tick that pushes consecutive to 2 by starting at 1.
    entity[EF.ACTIVE_DISEASES][0]["consecutive_successes"] = 1
    rng = _rng([10])  # roll 10 → total 10+4+2=16 > 8 → saved → consecutive = 2
    entity_out, events = process_disease_ticks(
        entity=entity,
        target_id="fighter",
        current_round=5,
        rng=rng,
        next_event_id=1,
        timestamp=0.0,
    )
    cured_events = [ev for ev in events if ev["event_type"] == "disease_cured"]
    assert len(cured_events) == 1
    assert cured_events[0]["payload"]["disease_id"] == "filth_fever"
    assert len(entity_out.get(EF.ACTIVE_DISEASES, [])) == 0
