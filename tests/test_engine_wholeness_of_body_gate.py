"""Gate tests: Monk Wholeness of Body — WO-ENGINE-WHOLENESS-OF-BODY-001.

WOB-001: Monk L7, 10 HP down — heals up to pool (14), pool exhausted
WOB-002: Monk L10, 5 HP down — partial use (5), pool = 15 remaining
WOB-003: Monk L20 — pool = 40 (2 × 20)
WOB-004: Monk L6 — blocked (below L7 threshold)
WOB-005: Pool exhausted — second use blocked
WOB-006: At full HP — no_effect event
WOB-007: Monk 7 / Rogue 5 multiclass — pool = 14 (monk levels only)
WOB-008: Monk L7 unconscious (DYING=True) — blocked
"""

import pytest
from aidm.core.wholeness_of_body_resolver import WholenessOfBodyIntent, resolve_wholeness_of_body
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF


def _make_ws(entity: dict, eid: str = "monk") -> WorldState:
    return WorldState(
        ruleset_version="3.5",
        entities={eid: entity},
        active_combat=None,
    )


def _monk(
    monk_level: int,
    *,
    hp_current: int = 50,
    hp_max: int = 60,
    pool_override: int | None = None,
    used: int = 0,
    dying: bool = False,
    defeated: bool = False,
    class_mix: dict | None = None,
) -> dict:
    pool = pool_override if pool_override is not None else (monk_level * 2 if monk_level >= 7 else 0)
    entity = {
        EF.CLASS_LEVELS: class_mix or {"monk": monk_level},
        EF.HP_CURRENT: hp_current,
        EF.HP_MAX: hp_max,
        EF.DEFEATED: defeated,
        EF.DYING: dying,
        EF.CONDITIONS: [],
        EF.TEAM: "party",
        EF.WHOLENESS_OF_BODY_POOL: pool,
        EF.WHOLENESS_OF_BODY_USED: used,
    }
    return entity


def _resolve(entity: dict, amount: int, eid: str = "monk"):
    ws = _make_ws(entity, eid)
    intent = WholenessOfBodyIntent(actor_id=eid, amount=amount)
    events, ws_after = resolve_wholeness_of_body(intent, ws, 1, 0.0)
    return events, ws_after


# ── WOB-001: Monk L7, 10 HP down — heals 10, pool exhausted ──────────────────

def test_wob001_monk_l7_full_heal():
    """L7 monk with 10 HP deficit: heals 10 HP, pool exhausted (14-10=4 remaining)."""
    actor = _monk(7, hp_current=50, hp_max=60)  # 10 HP down, pool=14
    events, ws_after = _resolve(actor, amount=14)
    heal_events = [e for e in events if e.event_type == "wholeness_of_body_heal"]
    assert len(heal_events) == 1
    ev = heal_events[0]
    assert ev.payload["hp_healed"] == 10    # Clamped to HP_MAX - HP_CURRENT
    assert ev.payload["hp_after"] == 60
    assert ev.payload["pool_remaining"] == 4  # 14 - 10 spent
    assert ws_after.entities["monk"][EF.HP_CURRENT] == 60
    assert ws_after.entities["monk"][EF.WHOLENESS_OF_BODY_USED] == 10


# ── WOB-002: Monk L10, partial use — pool tracks correctly ───────────────────

def test_wob002_monk_l10_partial_use():
    """L10 monk, 5 HP deficit: heals exactly 5, pool drops from 20 to 15."""
    actor = _monk(10, hp_current=55, hp_max=60)  # 5 HP down, pool=20
    events, ws_after = _resolve(actor, amount=5)
    heal_events = [e for e in events if e.event_type == "wholeness_of_body_heal"]
    assert len(heal_events) == 1
    ev = heal_events[0]
    assert ev.payload["hp_healed"] == 5
    assert ev.payload["pool_remaining"] == 15
    assert ws_after.entities["monk"][EF.WHOLENESS_OF_BODY_USED] == 5


# ── WOB-003: Monk L20 pool check ──────────────────────────────────────────────

def test_wob003_monk_l20_pool_40():
    """L20 monk: Wholeness of Body pool = 40 (2 × 20)."""
    actor = _monk(20, pool_override=40)
    assert actor[EF.WHOLENESS_OF_BODY_POOL] == 40


# ── WOB-004: Monk L6 — blocked ────────────────────────────────────────────────

def test_wob004_monk_l6_blocked():
    """Monk L6 cannot use Wholeness of Body (requires L7+)."""
    actor = _monk(6, hp_current=50, hp_max=60)
    actor[EF.WHOLENESS_OF_BODY_POOL] = 0  # Not unlocked
    events, _ = _resolve(actor, amount=12)
    invalid = [e for e in events if e.event_type == "wholeness_of_body_invalid"]
    assert len(invalid) == 1
    assert invalid[0].payload["reason"] == "not_qualifying_monk"
    assert not any(e.event_type == "wholeness_of_body_heal" for e in events)


# ── WOB-005: Pool exhausted — second use blocked ─────────────────────────────

def test_wob005_pool_exhausted_blocked():
    """Monk with pool already fully consumed: second use is blocked."""
    actor = _monk(7, hp_current=50, hp_max=60, used=14)  # Pool=14, used=14 → 0 remaining
    events, _ = _resolve(actor, amount=5)
    exhausted = [e for e in events if e.event_type == "wholeness_of_body_exhausted"]
    assert len(exhausted) == 1
    assert exhausted[0].payload["pool"] == 14
    assert exhausted[0].payload["used"] == 14


# ── WOB-006: Already at full HP — no effect ───────────────────────────────────

def test_wob006_at_full_hp_no_effect():
    """Monk already at HP_MAX: wholeness_of_body_no_effect event, no healing."""
    actor = _monk(7, hp_current=60, hp_max=60)  # Full HP
    events, ws_after = _resolve(actor, amount=14)
    no_eff = [e for e in events if e.event_type == "wholeness_of_body_no_effect"]
    assert len(no_eff) == 1
    assert no_eff[0].payload["reason"] == "already_at_max_hp"
    assert not any(e.event_type == "wholeness_of_body_heal" for e in events)


# ── WOB-007: Monk 7 / Rogue 5 — pool = 14 (monk levels only) ─────────────────

def test_wob007_multiclass_monk7_rogue5_pool14():
    """Monk7/Rogue5: WoB pool = 14 (2 × 7 monk levels, not total level 12)."""
    actor = _monk(7, class_mix={"monk": 7, "rogue": 5})
    assert actor[EF.WHOLENESS_OF_BODY_POOL] == 14, (
        f"Expected pool 14 (monk-only), got {actor[EF.WHOLENESS_OF_BODY_POOL]}"
    )
    # Confirm functional: can heal with that pool
    actor[EF.HP_CURRENT] = 50
    actor[EF.HP_MAX] = 60
    events, _ = _resolve(actor, amount=5)
    assert any(e.event_type == "wholeness_of_body_heal" for e in events)


# ── WOB-008: Unconscious monk — blocked ───────────────────────────────────────

def test_wob008_unconscious_blocked():
    """Monk with DYING=True cannot use Wholeness of Body."""
    actor = _monk(7, hp_current=50, hp_max=60, dying=True)
    events, _ = _resolve(actor, amount=14)
    blocked = [e for e in events if e.event_type == "wholeness_of_body_blocked"]
    assert len(blocked) == 1
    assert blocked[0].payload["reason"] == "unconscious"
    assert not any(e.event_type == "wholeness_of_body_heal" for e in events)
