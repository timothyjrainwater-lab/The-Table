"""Gate tests — PCD-AE-001 through PCD-AE-004
WO-AE-WO1: Poison/disease Fort save CON double-count fix.
PHB p.443: poison Fort save uses standard saving throw mechanics.
Field contract: EF.SAVE_FORT = base class + CON + racial (Type 2). Resolver adds situational deltas only.
Fix: poison_disease_resolver.py — strip redundant CON addition at 4 call sites.
"""

import unittest.mock as mock
from copy import deepcopy

import pytest

from aidm.schemas.entity_fields import EF
from aidm.core.poison_disease_resolver import (
    apply_poison,
    process_poison_secondaries,
)


def _rng(rolls: list):
    stream = mock.MagicMock()
    stream.randint.side_effect = list(rolls) + [10] * 50
    rng = mock.MagicMock()
    rng.stream.return_value = stream
    return rng


def _base_entity(fort: int, con_mod: int = 2) -> dict:
    """Entity with EF.SAVE_FORT = base+CON (Type 2 field)."""
    return {
        EF.ENTITY_ID: "target",
        EF.SAVE_FORT: fort,  # Type 2: already includes CON
        EF.CON_MOD: con_mod,
        EF.HP_CURRENT: 20,
        EF.HP_MAX: 20,
        EF.FEATS: [],
        EF.RACE: "human",
        EF.CLASS_LEVELS: {},
        EF.ACTIVE_POISONS: [],
        EF.CONDITIONS: {},
        EF.IS_UNDEAD: False,
    }


def _poison_stat(dc: int) -> dict:
    """Poison stat dict using the actual keys expected by apply_poison."""
    return {
        "poison_id": "giant_wasp_venom",
        "dc": dc,
        "initial_ability": "dex",
        "initial_amount": 1,
        "secondary_ability": "dex",
        "secondary_amount": 1,
    }


def test_pcd_ae_001_poison_save_no_con_double_count():
    """PCD-AE-001: CON 14 entity (+2 mod) — poison Fort save total = roll + EF.SAVE_FORT (not + EF.SAVE_FORT + 2).
    EF.SAVE_FORT=5 already includes the +2 CON. DC=20.
    Roll pinned to 14: total = 19 < 20 → fail.
    Before fix: 14 + 5 + 2 = 21 ≥ 20 (wrong pass due to double-count).
    After fix:  14 + 5 = 19 < 20 (correct fail).
    """
    entity = _base_entity(fort=5, con_mod=2)
    poison = _poison_stat(dc=20)

    rng = _rng([14])  # roll = 14 → 14 + 5 = 19 < 20 → fail
    result_entity, events = apply_poison(
        entity, "target", "attacker", poison,
        current_round=1, rng=rng, next_event_id=1, timestamp=0.0
    )

    save_event = next(e for e in events if e["event_type"] == "poison_save_initial")
    assert not save_event["payload"]["saved"], (
        f"roll=14 + fort=5 (includes CON) = 19 should fail DC=20. "
        f"If passed, CON is double-counted. saved={save_event['payload']['saved']}"
    )


def test_pcd_ae_002_poison_save_passes_at_correct_threshold():
    """PCD-AE-002: Poison save passes when roll + fort_base ≥ DC (no double-count inflation)."""
    entity = _base_entity(fort=5, con_mod=2)
    poison = _poison_stat(dc=15)

    rng = _rng([10])  # 10 + 5 = 15 ≥ 15 → saved
    result_entity, events = apply_poison(
        entity, "target", "attacker", poison,
        current_round=1, rng=rng, next_event_id=1, timestamp=0.0
    )

    save_event = next(e for e in events if e["event_type"] == "poison_save_initial")
    assert save_event["payload"]["saved"], (
        f"roll=10 + fort=5 = 15 should meet DC=15. saved={save_event['payload']['saved']}"
    )


def test_pcd_ae_003_secondary_poison_save_no_con_double_count():
    """PCD-AE-003: Secondary poison save (process_poison_secondaries) also strips CON double-count."""
    entity = _base_entity(fort=5, con_mod=2)
    active_poison = {
        "poison_id": "giant_wasp_venom",
        "dc": 20,
        "secondary_ability": "dex",
        "secondary_amount": 1,
        "secondary_due_round": 1,
    }
    entity = deepcopy(entity)
    entity[EF.ACTIVE_POISONS] = [active_poison]

    # roll=14 → 14 + 5 = 19 < 20 → fail (if double-counted: 21 ≥ 20 → wrong pass)
    rng = _rng([14])
    result_entity, events = process_poison_secondaries(
        entity, "target", current_round=1, rng=rng, next_event_id=1, timestamp=0.0
    )

    secondary_events = [e for e in events if e["event_type"] == "poison_save_secondary"]
    assert secondary_events, "Expected poison_save_secondary event"
    assert not secondary_events[0]["payload"]["saved"], (
        f"Secondary save: roll=14 + fort=5 = 19 should fail DC=20. "
        f"saved={secondary_events[0]['payload']['saved']}"
    )


def test_pcd_ae_004_zero_con_mod_unaffected():
    """PCD-AE-004: Entity with CON_MOD=0 — removing double-count has no effect (no regression)."""
    entity = _base_entity(fort=4, con_mod=0)
    poison = _poison_stat(dc=15)

    rng = _rng([10])  # 10 + 4 = 14 < 15 → fail
    result_entity, events = apply_poison(
        entity, "target", "attacker", poison,
        current_round=1, rng=rng, next_event_id=1, timestamp=0.0
    )

    save_event = next(e for e in events if e["event_type"] == "poison_save_initial")
    assert not save_event["payload"]["saved"], (
        f"roll=10 + fort=4 = 14 should fail DC=15. saved={save_event['payload']['saved']}"
    )
