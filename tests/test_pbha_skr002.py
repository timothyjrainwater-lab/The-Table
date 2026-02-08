"""SKR-002 PBHA: Deterministic Replay Verification

Per Action Plan V2 §5.2.4, verifies that SKR-002 produces identical results
across 10 independent replay runs with different RNG seeds.

ACCEPTANCE CRITERIA:
- All 10 replays produce identical event sequences
- All 10 replays produce identical final ability scores
- All 10 replays produce identical HP max values
- No hidden RNG consumption detected
"""

import hashlib
import json
from typing import Any, Dict, List

import pytest

from aidm.core.permanent_stats import (
    apply_permanent_modifier,
    calculate_effective_ability_score,
    restore_permanent_modifier,
)
from aidm.schemas.permanent_stats import (
    Ability,
    PermanentModifierType,
    PermanentStatModifiers,
)


def _compute_event_hash(events: List[Dict[str, Any]]) -> str:
    """Compute deterministic hash of event sequence."""
    serialized = json.dumps(events, sort_keys=True)
    return hashlib.sha256(serialized.encode()).hexdigest()


def _compute_state_hash(entity_state: Dict[str, Any]) -> str:
    """Compute deterministic hash of entity state."""
    # Extract relevant fields for hashing
    relevant_state = {
        "entity_id": entity_state["entity_id"],
        "base_stats": entity_state.get("base_stats", {}),
        "permanent_stat_modifiers": entity_state.get("permanent_stat_modifiers", {}),
        "hp_max": entity_state.get("hp_max"),
        "hp_current": entity_state.get("hp_current"),
    }
    serialized = json.dumps(relevant_state, sort_keys=True)
    return hashlib.sha256(serialized.encode()).hexdigest()


def _run_shadow_drain_scenario(seed: int) -> tuple[str, str, Dict[str, Any]]:
    """Run Shadow STR drain scenario with given seed.

    Returns: (event_hash, state_hash, final_state)
    """
    # Note: seed parameter is intentionally unused (no RNG in SKR-002)
    # Use same entity_id for all runs to verify determinism
    entity = {
        "entity_id": "fighter_pbha",
        "base_stats": {"str": 16, "dex": 14, "con": 14, "int": 10, "wis": 12, "cha": 10},
        "permanent_stat_modifiers": PermanentStatModifiers().to_dict(),
    }

    all_events = []

    # Shadow attacks (-2 STR)
    events1 = apply_permanent_modifier(
        entity, Ability.STR, PermanentModifierType.DRAIN, -2, "shadow_1"
    )
    all_events.extend(events1)

    # Second shadow attacks (-3 STR)
    events2 = apply_permanent_modifier(
        entity, Ability.STR, PermanentModifierType.DRAIN, -3, "shadow_2"
    )
    all_events.extend(events2)

    # Restoration removes 2 STR drain
    events3 = restore_permanent_modifier(
        entity, Ability.STR, 2, "lesser_restoration"
    )
    all_events.extend(events3)

    event_hash = _compute_event_hash(all_events)
    state_hash = _compute_state_hash(entity)

    return event_hash, state_hash, entity


def _run_vampire_con_drain_scenario(seed: int) -> tuple[str, str, Dict[str, Any]]:
    """Run Vampire CON drain scenario with given seed.

    Returns: (event_hash, state_hash, final_state)
    """
    entity = {
        "entity_id": "fighter_pbha",
        "base_stats": {"str": 16, "dex": 14, "con": 14, "int": 10, "wis": 12, "cha": 10},
        "permanent_stat_modifiers": PermanentStatModifiers().to_dict(),
        "hd_count": 5,
        "base_hp": 40,
        "hp_current": 50,
        "hp_max": 50,
    }

    all_events = []

    # Vampire drains 4 CON
    events1 = apply_permanent_modifier(
        entity, Ability.CON, PermanentModifierType.DRAIN, -4, "vampire"
    )
    all_events.extend(events1)

    # Restoration
    events2 = restore_permanent_modifier(entity, Ability.CON, 4, "restoration")
    all_events.extend(events2)

    event_hash = _compute_event_hash(all_events)
    state_hash = _compute_state_hash(entity)

    return event_hash, state_hash, entity


def _run_wish_stat_increase_scenario(seed: int) -> tuple[str, str, Dict[str, Any]]:
    """Run Wish stat increase scenario with given seed.

    Returns: (event_hash, state_hash, final_state)
    """
    entity = {
        "entity_id": "wizard_pbha",
        "base_stats": {"str": 8, "dex": 14, "con": 12, "int": 18, "wis": 10, "cha": 10},
        "permanent_stat_modifiers": PermanentStatModifiers().to_dict(),
    }

    all_events = []

    # Wish (+1 INT)
    events1 = apply_permanent_modifier(
        entity, Ability.INT, PermanentModifierType.INHERENT, +1, "wish"
    )
    all_events.extend(events1)

    # Later, INT drain
    events2 = apply_permanent_modifier(
        entity, Ability.INT, PermanentModifierType.DRAIN, -2, "feeblemind_partial"
    )
    all_events.extend(events2)

    event_hash = _compute_event_hash(all_events)
    state_hash = _compute_state_hash(entity)

    return event_hash, state_hash, entity


# -----------------------------------------------------------------------------
# PBHA Test: 10× Replay Verification
# -----------------------------------------------------------------------------


def test_pbha_shadow_drain_10x_replay():
    """PBHA: Shadow drain scenario produces identical results across 10 replays."""
    hashes = []

    for seed in range(10):
        event_hash, state_hash, final_state = _run_shadow_drain_scenario(seed)
        hashes.append((event_hash, state_hash))

        # Verify final state invariants
        effective_str = calculate_effective_ability_score(final_state, Ability.STR)
        assert effective_str == 13  # 16 (base) + (-5 drain) + 2 (restored) = 13

    # All 10 runs must produce identical hashes
    first_event_hash, first_state_hash = hashes[0]
    for i, (event_hash, state_hash) in enumerate(hashes[1:], start=1):
        assert event_hash == first_event_hash, f"Replay {i} event hash differs from replay 0"
        assert state_hash == first_state_hash, f"Replay {i} state hash differs from replay 0"


def test_pbha_vampire_con_drain_10x_replay():
    """PBHA: Vampire CON drain scenario produces identical results across 10 replays."""
    hashes = []

    for seed in range(10):
        event_hash, state_hash, final_state = _run_vampire_con_drain_scenario(seed)
        hashes.append((event_hash, state_hash))

        # Verify final state invariants
        assert final_state["hp_max"] == 50  # Restored
        assert final_state["hp_current"] == 40  # Not healed

    # All 10 runs must produce identical hashes
    first_event_hash, first_state_hash = hashes[0]
    for i, (event_hash, state_hash) in enumerate(hashes[1:], start=1):
        assert event_hash == first_event_hash, f"Replay {i} event hash differs from replay 0"
        assert state_hash == first_state_hash, f"Replay {i} state hash differs from replay 0"


def test_pbha_wish_stat_increase_10x_replay():
    """PBHA: Wish stat increase scenario produces identical results across 10 replays."""
    hashes = []

    for seed in range(10):
        event_hash, state_hash, final_state = _run_wish_stat_increase_scenario(seed)
        hashes.append((event_hash, state_hash))

        # Verify final state invariants
        effective_int = calculate_effective_ability_score(final_state, Ability.INT)
        assert effective_int == 17  # 18 (base) + 1 (inherent) + (-2 drain) = 17

        # Verify inherent bonus persists
        perm_mods = PermanentStatModifiers.from_dict(final_state["permanent_stat_modifiers"])
        assert perm_mods.int.inherent == 1
        assert perm_mods.int.drain == -2

    # All 10 runs must produce identical hashes
    first_event_hash, first_state_hash = hashes[0]
    for i, (event_hash, state_hash) in enumerate(hashes[1:], start=1):
        assert event_hash == first_event_hash, f"Replay {i} event hash differs from replay 0"
        assert state_hash == first_state_hash, f"Replay {i} state hash differs from replay 0"


# -----------------------------------------------------------------------------
# PBHA Test: No Hidden RNG Consumption
# -----------------------------------------------------------------------------


def test_pbha_no_rng_consumption():
    """PBHA: Verify SKR-002 does not consume RNG (INV-12)."""
    # Run scenarios with different "seeds" (intentionally not used)
    # If SKR-002 consumes RNG, results would vary

    results_shadow = [_run_shadow_drain_scenario(i) for i in range(5)]
    results_vampire = [_run_vampire_con_drain_scenario(i) for i in range(5)]
    results_wish = [_run_wish_stat_increase_scenario(i) for i in range(5)]

    # All results must be identical (no RNG variance)
    assert len(set(r[0] for r in results_shadow)) == 1, "Shadow scenario varies with seed"
    assert len(set(r[0] for r in results_vampire)) == 1, "Vampire scenario varies with seed"
    assert len(set(r[0] for r in results_wish)) == 1, "Wish scenario varies with seed"


# -----------------------------------------------------------------------------
# PBHA Test: Event Ordering Determinism
# -----------------------------------------------------------------------------


def test_pbha_event_ordering_deterministic():
    """PBHA: Verify event ordering is deterministic (INV-10)."""
    entity = {
        "entity_id": "test_entity",
        "base_stats": {"str": 16, "dex": 14, "con": 14, "int": 10, "wis": 12, "cha": 10},
        "permanent_stat_modifiers": PermanentStatModifiers().to_dict(),
        "hd_count": 5,
        "base_hp": 40,
        "hp_current": 50,
        "hp_max": 50,
    }

    # Apply CON drain (triggers multiple events)
    events = apply_permanent_modifier(
        entity, Ability.CON, PermanentModifierType.DRAIN, -4, "vampire"
    )

    # Verify event ordering (INV-10)
    event_types = [e["event_type"] for e in events]

    # Expected order: permanent_stat_modified → derived_stats_recalculated → hp_changed
    assert event_types[0] == "permanent_stat_modified"
    assert event_types[1] == "derived_stats_recalculated"
    assert event_types[2] == "hp_changed"

    # Verify this ordering is stable across multiple runs
    for _ in range(10):
        entity_copy = {
            "entity_id": "test_entity",
            "base_stats": {"str": 16, "dex": 14, "con": 14, "int": 10, "wis": 12, "cha": 10},
            "permanent_stat_modifiers": PermanentStatModifiers().to_dict(),
            "hd_count": 5,
            "base_hp": 40,
            "hp_current": 50,
            "hp_max": 50,
        }
        events_copy = apply_permanent_modifier(
            entity_copy, Ability.CON, PermanentModifierType.DRAIN, -4, "vampire"
        )
        assert [e["event_type"] for e in events_copy] == event_types
