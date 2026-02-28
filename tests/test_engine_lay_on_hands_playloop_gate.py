"""Gate tests: Paladin Lay on Hands — play_loop path — WO-ENGINE-AF-WO1.

LOH-WO1-001 through LOH-WO1-008.

Tests the same resolve_lay_on_hands() path that play_loop.execute_turn invokes
(via LayOnHandsIntent branch at play_loop.py:2965). Confirms end-to-end
consume-site chain: builder.py (write) → lay_on_hands_resolver (read) → rest_resolver (reset).

PHB p.44: Paladin can heal (paladin_level × CHA_mod) HP per day.
Standard action, touch range, self or ally.
"""

import pytest

from aidm.core.lay_on_hands_resolver import resolve_lay_on_hands
from aidm.core.rest_resolver import resolve_rest
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.schemas.intents import LayOnHandsIntent, RestIntent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _paladin(eid="paladin", level=5, cha_mod=3, loh_pool=None, loh_used=0):
    pool = loh_pool if loh_pool is not None else (level * cha_mod if cha_mod > 0 else 0)
    return {
        EF.ENTITY_ID: eid,
        EF.CLASS_LEVELS: {"paladin": level},
        EF.CHA_MOD: cha_mod,
        EF.HP_CURRENT: 25,
        EF.HP_MAX: 40,
        EF.LEVEL: level,
        EF.LAY_ON_HANDS_POOL: pool,
        EF.LAY_ON_HANDS_USED: loh_used,
        EF.SAVE_FORT: 4,
        EF.CON_MOD: 1,
        EF.CONDITIONS: [],
        EF.NONLETHAL_DAMAGE: 0,
    }


def _ally(eid="ally", hp=10, hp_max=20):
    return {
        EF.ENTITY_ID: eid,
        EF.CLASS_LEVELS: {},
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp_max,
    }


def _ws(*entities):
    return WorldState(
        ruleset_version="3.5",
        entities={e[EF.ENTITY_ID]: e for e in entities},
        active_combat=None,
    )


# ---------------------------------------------------------------------------
# LOH-WO1-001: non-paladin actor → lay_on_hands_invalid
# ---------------------------------------------------------------------------

def test_loh_wo1_001_non_paladin_invalid():
    """LOH-WO1-001: Fighter using LayOnHandsIntent → lay_on_hands_invalid."""
    fighter = {
        EF.ENTITY_ID: "fighter",
        EF.CLASS_LEVELS: {"fighter": 10},
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 50,
    }
    ally = _ally()
    ws = _ws(fighter, ally)

    intent = LayOnHandsIntent(actor_id="fighter", target_id="ally", amount=5)
    events, ws2 = resolve_lay_on_hands(intent, ws, next_event_id=1, timestamp=0.0)

    assert any(e.event_type == "lay_on_hands_invalid" for e in events), (
        "Expected lay_on_hands_invalid for non-paladin actor"
    )
    assert not any(e.event_type == "lay_on_hands_heal" for e in events)
    assert ws2.entities["ally"][EF.HP_CURRENT] == 10  # unchanged


# ---------------------------------------------------------------------------
# LOH-WO1-002: pool = 0 (CHA_mod ≤ 0) → lay_on_hands_exhausted
# ---------------------------------------------------------------------------

def test_loh_wo1_002_cha_mod_zero_pool_exhausted():
    """LOH-WO1-002: Paladin with CHA_mod=0 → pool=0 → lay_on_hands_exhausted."""
    paladin = _paladin(level=5, cha_mod=0, loh_pool=0, loh_used=0)
    ally = _ally()
    ws = _ws(paladin, ally)

    intent = LayOnHandsIntent(actor_id="paladin", target_id="ally", amount=5)
    events, ws2 = resolve_lay_on_hands(intent, ws, next_event_id=1, timestamp=0.0)

    assert any(e.event_type == "lay_on_hands_exhausted" for e in events), (
        "Expected lay_on_hands_exhausted when pool=0"
    )
    assert not any(e.event_type == "lay_on_hands_heal" for e in events)
    assert ws2.entities["ally"][EF.HP_CURRENT] == 10  # unchanged


# ---------------------------------------------------------------------------
# LOH-WO1-003: normal heal dispatched via resolver (play_loop path)
# ---------------------------------------------------------------------------

def test_loh_wo1_003_normal_heal():
    """LOH-WO1-003: Paladin L5/CHA+3, heals 8 HP ally. lay_on_hands_heal emitted."""
    paladin = _paladin(level=5, cha_mod=3)  # pool=15
    ally = _ally(hp=7, hp_max=20)
    ws = _ws(paladin, ally)

    intent = LayOnHandsIntent(actor_id="paladin", target_id="ally", amount=8)
    events, ws2 = resolve_lay_on_hands(intent, ws, next_event_id=1, timestamp=0.0)

    heal_event = next((e for e in events if e.event_type == "lay_on_hands_heal"), None)
    assert heal_event is not None, "Expected lay_on_hands_heal event"
    assert heal_event.payload["hp_healed"] == 8
    assert heal_event.payload["pool_remaining"] == 7  # 15 - 8
    assert ws2.entities["ally"][EF.HP_CURRENT] == 15
    assert ws2.entities["paladin"][EF.LAY_ON_HANDS_USED] == 8


# ---------------------------------------------------------------------------
# LOH-WO1-004: amount clamped to pool remaining
# ---------------------------------------------------------------------------

def test_loh_wo1_004_amount_clamped_to_remaining():
    """LOH-WO1-004: Request 12 HP with only 4 remaining → heals 4, not 12."""
    paladin = _paladin(level=5, cha_mod=3, loh_pool=15, loh_used=11)  # 4 remaining
    ally = _ally(hp=3, hp_max=20)
    ws = _ws(paladin, ally)

    intent = LayOnHandsIntent(actor_id="paladin", target_id="ally", amount=12)
    events, ws2 = resolve_lay_on_hands(intent, ws, next_event_id=1, timestamp=0.0)

    heal_event = next(e for e in events if e.event_type == "lay_on_hands_heal")
    assert heal_event.payload["amount_spent"] == 4
    assert heal_event.payload["hp_healed"] == 4
    assert ws2.entities["paladin"][EF.LAY_ON_HANDS_USED] == 15
    assert ws2.entities["ally"][EF.HP_CURRENT] == 7


# ---------------------------------------------------------------------------
# LOH-WO1-005: HP_CURRENT clamped to HP_MAX (can't overheal)
# ---------------------------------------------------------------------------

def test_loh_wo1_005_hp_clamped_to_max():
    """LOH-WO1-005: Ally at 18/20 HP, heal 10 → clamped to 20, healed only 2."""
    paladin = _paladin(level=5, cha_mod=3)  # pool=15
    ally = _ally(hp=18, hp_max=20)
    ws = _ws(paladin, ally)

    intent = LayOnHandsIntent(actor_id="paladin", target_id="ally", amount=10)
    events, ws2 = resolve_lay_on_hands(intent, ws, next_event_id=1, timestamp=0.0)

    heal_event = next(e for e in events if e.event_type == "lay_on_hands_heal")
    assert heal_event.payload["hp_after"] == 20
    assert heal_event.payload["hp_healed"] == 2
    assert heal_event.payload["amount_spent"] == 10  # pool consumed by request, HP capped
    assert ws2.entities["ally"][EF.HP_CURRENT] == 20


# ---------------------------------------------------------------------------
# LOH-WO1-006: pool exhausted on second use after depleting remaining
# ---------------------------------------------------------------------------

def test_loh_wo1_006_second_use_exhausts_pool():
    """LOH-WO1-006: First use depletes pool → second use returns lay_on_hands_exhausted."""
    paladin = _paladin(level=2, cha_mod=3, loh_pool=6)  # pool=6 (2×3)
    ally = _ally(hp=5, hp_max=20)
    ws = _ws(paladin, ally)

    # First use: consume all 6 HP
    intent1 = LayOnHandsIntent(actor_id="paladin", target_id="ally", amount=6)
    events1, ws2 = resolve_lay_on_hands(intent1, ws, next_event_id=1, timestamp=0.0)
    assert any(e.event_type == "lay_on_hands_heal" for e in events1)
    assert ws2.entities["paladin"][EF.LAY_ON_HANDS_USED] == 6

    # Second use: pool exhausted
    intent2 = LayOnHandsIntent(actor_id="paladin", target_id="ally", amount=3)
    events2, ws3 = resolve_lay_on_hands(intent2, ws2, next_event_id=2, timestamp=1.0)
    assert any(e.event_type == "lay_on_hands_exhausted" for e in events2)
    assert not any(e.event_type == "lay_on_hands_heal" for e in events2)


# ---------------------------------------------------------------------------
# LOH-WO1-007: pool resets on RestIntent (rest_resolver path — PHB p.44)
# ---------------------------------------------------------------------------

def test_loh_wo1_007_pool_resets_on_rest():
    """LOH-WO1-007: RestIntent → lay_on_hands_used reset to 0, pool recalculated.
    Tests rest_resolver.py path directly (consume-site chain: reset at rest_resolver.py:130).
    """
    paladin = _paladin(level=6, cha_mod=4, loh_pool=24, loh_used=20)  # pool=24, used=20
    # rest_resolver needs these fields
    paladin[EF.HP_CURRENT] = paladin[EF.HP_MAX]  # full HP
    ws = _ws(paladin)

    intent = RestIntent(rest_type="overnight")
    result = resolve_rest(intent, ws, actor_id="paladin")
    actor_after = result.world_state.entities["paladin"]

    assert actor_after[EF.LAY_ON_HANDS_USED] == 0
    assert actor_after[EF.LAY_ON_HANDS_POOL] == 24  # 6 × 4


# ---------------------------------------------------------------------------
# LOH-WO1-008: paladin heals self (actor_id == target_id, PHB p.44 allows)
# ---------------------------------------------------------------------------

def test_loh_wo1_008_paladin_heals_self():
    """LOH-WO1-008: actor_id == target_id → valid. Paladin heals self."""
    paladin = _paladin(level=4, cha_mod=2)  # pool=8
    paladin[EF.HP_CURRENT] = 10
    paladin[EF.HP_MAX] = 30
    ws = _ws(paladin)

    intent = LayOnHandsIntent(actor_id="paladin", target_id="paladin", amount=5)
    events, ws2 = resolve_lay_on_hands(intent, ws, next_event_id=1, timestamp=0.0)

    heal_event = next(e for e in events if e.event_type == "lay_on_hands_heal")
    assert heal_event.payload["hp_healed"] == 5
    assert ws2.entities["paladin"][EF.HP_CURRENT] == 15
    assert ws2.entities["paladin"][EF.LAY_ON_HANDS_USED] == 5
