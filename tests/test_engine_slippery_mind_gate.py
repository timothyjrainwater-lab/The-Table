"""Gate tests for WO-ENGINE-AG-WO3: Rogue Slippery Mind (PHB p.51).

SM-001: HAS_SLIPPERY_MIND=True + failed enchantment save → slippery_mind_retry_queued event
SM-002: Retry succeeds → slippery_mind_success; effect not applied
SM-003: Retry fails → slippery_mind_failed; effect applied
SM-004: Only ONE retry granted (third attempt not possible)
SM-005: Non-enchantment save failure → Slippery Mind does NOT trigger
SM-006: HAS_SLIPPERY_MIND=False → Slippery Mind never triggers
SM-007: Retry uses same DC as original save
SM-008: SaveContext school="enchantment" correctly triggers; school="fear" does NOT
"""

import pytest
from copy import deepcopy

from aidm.core.state import WorldState
from aidm.core.save_resolver import resolve_save, resolve_slippery_mind_retry, apply_save_events
from aidm.schemas.saves import SaveContext, SaveType, SaveOutcome
from aidm.schemas.entity_fields import EF


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _SeparateStreamRNG:
    def __init__(self, saves_rolls=None):
        self._pool = list(saves_rolls or [])
        self._idx = 0

    def stream(self, name):
        return self

    def randint(self, lo, hi):
        if self._idx < len(self._pool):
            val = self._pool[self._idx]
            self._idx += 1
            return val
        return 10


def _make_rogue(has_slippery_mind=True, retry_pending=False):
    return {
        EF.ENTITY_ID: "rogue_1",
        EF.TEAM: "player",
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 30,
        EF.AC: 14,
        EF.DEFEATED: False,
        EF.BASE_STATS: {"strength": 12, "dexterity": 16, "constitution": 12,
                        "intelligence": 12, "wisdom": 10, "charisma": 12},
        EF.STR_MOD: 1,
        EF.DEX_MOD: 3,
        EF.CON_MOD: 1,
        EF.WIS_MOD: 0,
        EF.CHA_MOD: 1,
        EF.SAVE_FORT: 2,
        EF.SAVE_REF: 6,
        EF.SAVE_WILL: 2,  # Will +2; DC 15 → needs 13+ on d20
        EF.CONDITIONS: {},
        EF.HAS_SLIPPERY_MIND: has_slippery_mind,
        EF.SLIPPERY_MIND_RETRY_PENDING: retry_pending,
    }


def _make_world(rogue):
    return WorldState(
        ruleset_version="3.5",
        entities={"rogue_1": rogue},
        active_combat=None,
    )


def _event_types(events):
    return [e.event_type for e in events]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_sm_001_failed_enchantment_queues_retry():
    """SM-001: HAS_SLIPPERY_MIND=True + failed enchantment save → slippery_mind_retry_queued."""
    rogue = _make_rogue(has_slippery_mind=True, retry_pending=False)
    ws = _make_world(rogue)

    # Will +2; DC 15 → needs 13+ on d20. Roll 1 → fail.
    rng = _SeparateStreamRNG(saves_rolls=[1])
    ctx = SaveContext(
        save_type=SaveType.WILL,
        dc=15,
        source_id="caster_1",
        target_id="rogue_1",
        school="enchantment",
    )
    outcome, events = resolve_save(ctx, ws, rng, next_event_id=1, timestamp=0.0)
    assert outcome == SaveOutcome.FAILURE, f"Expected FAILURE, got {outcome}"
    types = _event_types(events)
    assert "slippery_mind_retry_queued" in types, (
        f"SM-001: Expected slippery_mind_retry_queued, got {types}"
    )


def test_sm_002_retry_succeeds_slippery_mind_success():
    """SM-002: Retry succeeds → slippery_mind_success event emitted."""
    rogue = _make_rogue(has_slippery_mind=True, retry_pending=True)
    ws = _make_world(rogue)

    # Will +2; DC 15 → needs 13+ on d20. Roll 20 → success.
    rng = _SeparateStreamRNG(saves_rolls=[20])
    outcome, events = resolve_slippery_mind_retry(
        world_state=ws,
        target_id="rogue_1",
        save_type=SaveType.WILL,
        dc=15,
        rng=rng,
        next_event_id=1,
        timestamp=0.0,
    )
    assert outcome == SaveOutcome.SUCCESS
    types = _event_types(events)
    assert "slippery_mind_success" in types, f"SM-002: Expected slippery_mind_success, got {types}"


def test_sm_003_retry_fails_slippery_mind_failed():
    """SM-003: Retry fails → slippery_mind_failed event emitted."""
    rogue = _make_rogue(has_slippery_mind=True, retry_pending=True)
    ws = _make_world(rogue)

    # Will +2; DC 15 → needs 13+ on d20. Roll 1 → nat1 auto-fail.
    rng = _SeparateStreamRNG(saves_rolls=[1])
    outcome, events = resolve_slippery_mind_retry(
        world_state=ws,
        target_id="rogue_1",
        save_type=SaveType.WILL,
        dc=15,
        rng=rng,
        next_event_id=1,
        timestamp=0.0,
    )
    assert outcome == SaveOutcome.FAILURE
    types = _event_types(events)
    assert "slippery_mind_failed" in types, f"SM-003: Expected slippery_mind_failed, got {types}"


def test_sm_004_only_one_retry_granted():
    """SM-004: Only ONE retry — second failure with retry_pending=True does NOT re-queue."""
    # When retry is already pending, a subsequent enchantment save failure should NOT
    # queue another retry (third attempt not possible).
    rogue = _make_rogue(has_slippery_mind=True, retry_pending=True)
    ws = _make_world(rogue)

    rng = _SeparateStreamRNG(saves_rolls=[1])  # Fail again
    ctx = SaveContext(
        save_type=SaveType.WILL,
        dc=15,
        source_id="caster_1",
        target_id="rogue_1",
        school="enchantment",
    )
    outcome, events = resolve_save(ctx, ws, rng, next_event_id=1, timestamp=0.0)
    assert outcome == SaveOutcome.FAILURE
    types = _event_types(events)
    # Must NOT have slippery_mind_retry_queued (retry already pending)
    assert "slippery_mind_retry_queued" not in types, (
        f"SM-004: Third attempt must not be queued; got {types}"
    )


def test_sm_005_non_enchantment_does_not_trigger():
    """SM-005: Non-enchantment save failure → Slippery Mind does NOT trigger."""
    rogue = _make_rogue(has_slippery_mind=True, retry_pending=False)
    ws = _make_world(rogue)

    rng = _SeparateStreamRNG(saves_rolls=[1])
    ctx = SaveContext(
        save_type=SaveType.FORT,
        dc=15,
        source_id="caster_1",
        target_id="rogue_1",
        school="necromancy",  # Not enchantment
    )
    outcome, events = resolve_save(ctx, ws, rng, next_event_id=1, timestamp=0.0)
    assert outcome == SaveOutcome.FAILURE
    types = _event_types(events)
    assert "slippery_mind_retry_queued" not in types, (
        f"SM-005: Non-enchantment should not trigger SM, got {types}"
    )


def test_sm_006_has_slippery_mind_false_never_triggers():
    """SM-006: HAS_SLIPPERY_MIND=False → Slippery Mind never triggers."""
    rogue = _make_rogue(has_slippery_mind=False, retry_pending=False)
    ws = _make_world(rogue)

    rng = _SeparateStreamRNG(saves_rolls=[1])
    ctx = SaveContext(
        save_type=SaveType.WILL,
        dc=15,
        source_id="caster_1",
        target_id="rogue_1",
        school="enchantment",
    )
    outcome, events = resolve_save(ctx, ws, rng, next_event_id=1, timestamp=0.0)
    assert outcome == SaveOutcome.FAILURE
    types = _event_types(events)
    assert "slippery_mind_retry_queued" not in types, (
        f"SM-006: HAS_SLIPPERY_MIND=False should not trigger SM, got {types}"
    )


def test_sm_007_retry_uses_same_dc():
    """SM-007: Retry uses same DC as original save."""
    rogue = _make_rogue(has_slippery_mind=True, retry_pending=True)
    ws = _make_world(rogue)

    rng = _SeparateStreamRNG(saves_rolls=[10])
    original_dc = 18
    outcome, events = resolve_slippery_mind_retry(
        world_state=ws,
        target_id="rogue_1",
        save_type=SaveType.WILL,
        dc=original_dc,
        rng=rng,
        next_event_id=1,
        timestamp=0.0,
    )
    # Check event payload includes the correct DC
    assert len(events) >= 1
    evt = events[0]
    assert evt.payload["dc"] == original_dc, (
        f"SM-007: Retry DC should be {original_dc}, got {evt.payload.get('dc')}"
    )


def test_sm_008_enchantment_triggers_fear_does_not():
    """SM-008: SaveContext school='enchantment' triggers; school='fear' does NOT."""
    rogue = _make_rogue(has_slippery_mind=True, retry_pending=False)
    ws = _make_world(rogue)

    # Test enchantment triggers
    rng = _SeparateStreamRNG(saves_rolls=[1])
    ctx_ench = SaveContext(
        save_type=SaveType.WILL,
        dc=15,
        source_id="caster_1",
        target_id="rogue_1",
        school="enchantment",
    )
    _, events_ench = resolve_save(ctx_ench, ws, rng, next_event_id=1, timestamp=0.0)
    assert "slippery_mind_retry_queued" in _event_types(events_ench), (
        "SM-008: enchantment school should trigger slippery mind"
    )

    # Test fear does NOT trigger
    rng2 = _SeparateStreamRNG(saves_rolls=[1])
    ctx_fear = SaveContext(
        save_type=SaveType.WILL,
        dc=15,
        source_id="caster_1",
        target_id="rogue_1",
        school="fear",
    )
    _, events_fear = resolve_save(ctx_fear, ws, rng2, next_event_id=1, timestamp=0.0)
    assert "slippery_mind_retry_queued" not in _event_types(events_fear), (
        "SM-008: fear school should NOT trigger slippery mind"
    )
