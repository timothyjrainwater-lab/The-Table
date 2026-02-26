"""Gate tests: WO-ENGINE-INTIMIDATE-DEMORALIZE-001 — Demoralize Opponent (PHB p.76).

Standard action opposed check. Intimidate vs. target HD + WIS mod.
Success: SHAKEN condition applied with duration. Already-Shaken: refresh duration.
Failure: skill_check_failed event, no condition.

Gate label: ENGINE-INTIMIDATE-DEMORALIZE-001
KERNEL-07 (Social Consequence) touch.
"""

import pytest
from copy import deepcopy
from unittest.mock import MagicMock, patch

from aidm.schemas.intents import DemoralizeIntent
from aidm.schemas.entity_fields import EF
from aidm.core.skill_resolver import resolve_demoralize
from aidm.core.state import WorldState


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_world(actor_id: str = "actor_01", target_id: str = "target_01",
                actor_cha_mod: int = 3, actor_intimidate_ranks: int = 4,
                target_hd: int = 2, target_wis_mod: int = 0,
                target_conditions: dict = None) -> WorldState:
    return WorldState(
        ruleset_version="3.5e",
        entities={
            actor_id: {
                EF.ENTITY_ID: actor_id,
                EF.HP_CURRENT: 20,
                EF.HP_MAX: 20,
                EF.TEAM: "players",
                EF.DEFEATED: False,
                EF.CONDITIONS: {},
                EF.CHA_MOD: actor_cha_mod,
                EF.SKILL_RANKS: {"intimidate": actor_intimidate_ranks},
                EF.HD_COUNT: 5,
            },
            target_id: {
                EF.ENTITY_ID: target_id,
                EF.HP_CURRENT: 15,
                EF.HP_MAX: 15,
                EF.TEAM: "monsters",
                EF.DEFEATED: False,
                EF.CONDITIONS: target_conditions or {},
                EF.HD_COUNT: target_hd,
                EF.WIS_MOD: target_wis_mod,
            },
        },
        active_combat={
            "initiative_order": ["actor_01", "target_01"],
            "aoo_used_this_round": [],
            "flat_footed_actors": [],
            "feint_flat_footed": [],
        },
    )


def _make_rng(d20_roll: int = 15):
    rng = MagicMock()
    stream = MagicMock()
    stream.randint.return_value = d20_roll
    rng.stream.return_value = stream
    return rng


def _run_demoralize(actor_id="actor_01", target_id="target_01",
                    actor_cha_mod=3, actor_intimidate_ranks=4,
                    target_hd=2, target_wis_mod=0,
                    d20_roll=15, target_conditions=None):
    """Run resolve_demoralize and return (ws_after, next_event_id, events)."""
    ws = _make_world(
        actor_id=actor_id, target_id=target_id,
        actor_cha_mod=actor_cha_mod, actor_intimidate_ranks=actor_intimidate_ranks,
        target_hd=target_hd, target_wis_mod=target_wis_mod,
        target_conditions=target_conditions,
    )
    intent = DemoralizeIntent(actor_id=actor_id, target_id=target_id)
    rng = _make_rng(d20_roll)
    ws_after, next_id, events = resolve_demoralize(ws, intent, 0, rng)
    return ws_after, next_id, events


# ---------------------------------------------------------------------------
# ID-001: Roll beats DC → condition_applied event, condition=shaken
# ---------------------------------------------------------------------------

def test_id_001_success_applies_shaken():
    """ID-001: DemoralizeIntent; roll beats DC → condition_applied with condition=shaken."""
    # actor: CHA+3, intimidate 4, d20=15 → total=22. DC: hd=2 + wis=0 = 2. Beats by 20.
    ws, nid, events = _run_demoralize(d20_roll=15, actor_cha_mod=3, actor_intimidate_ranks=4,
                                      target_hd=2, target_wis_mod=0)
    event_types = [e.event_type for e in events]
    assert "condition_applied" in event_types, f"ID-001: Expected condition_applied; got {event_types}"
    ce = next(e for e in events if e.event_type == "condition_applied")
    assert ce.payload["condition"] == "shaken", f"ID-001: Expected shaken; got {ce.payload}"
    # Shaken should be in target conditions
    target_conds = ws.entities["target_01"].get(EF.CONDITIONS, {})
    assert "shaken" in target_conds, f"ID-001: shaken not in target conditions: {target_conds}"


# ---------------------------------------------------------------------------
# ID-002: Roll beats DC by 5 → SHAKEN duration = 2 rounds
# ---------------------------------------------------------------------------

def test_id_002_duration_2_on_5_margin():
    """ID-002: Roll beats DC by exactly 5 → SHAKEN duration = 2 rounds."""
    # DC = hd=2 + wis=0 = 2. Need margin=5 → total=7. d20=2, cha=2, ranks=3 → 7. Beats by 5.
    ws, nid, events = _run_demoralize(d20_roll=2, actor_cha_mod=2, actor_intimidate_ranks=3,
                                      target_hd=2, target_wis_mod=0)
    ce = next((e for e in events if e.event_type == "condition_applied"), None)
    if ce is None:
        pytest.fail(f"ID-002: No condition_applied event. Events: {[e.event_type for e in events]}")
    duration = ce.payload.get("duration_rounds")
    assert duration == 2, f"ID-002: Expected duration=2; got {duration}"


# ---------------------------------------------------------------------------
# ID-003: Roll beats DC by 10+ → SHAKEN duration = 3 rounds
# ---------------------------------------------------------------------------

def test_id_003_duration_3_on_10_margin():
    """ID-003: Roll beats DC by exactly 10 → SHAKEN duration = 3 rounds."""
    # DC=2, need margin=10 → total=12. d20=7, cha=2, ranks=3 → 12.
    ws, nid, events = _run_demoralize(d20_roll=7, actor_cha_mod=2, actor_intimidate_ranks=3,
                                      target_hd=2, target_wis_mod=0)
    ce = next((e for e in events if e.event_type == "condition_applied"), None)
    if ce is None:
        pytest.fail(f"ID-003: No condition_applied event.")
    duration = ce.payload.get("duration_rounds")
    assert duration == 3, f"ID-003: Expected duration=3; got {duration}"


# ---------------------------------------------------------------------------
# ID-004: Roll fails DC → skill_check_failed, no SHAKEN
# ---------------------------------------------------------------------------

def test_id_004_fail_no_shaken():
    """ID-004: Roll fails DC → skill_check_failed event; SHAKEN not applied."""
    # DC = hd=10 + wis=4 = 14. Roll: d20=1, cha=0, ranks=0 → 1. Fails.
    ws, nid, events = _run_demoralize(d20_roll=1, actor_cha_mod=0, actor_intimidate_ranks=0,
                                      target_hd=10, target_wis_mod=4)
    event_types = [e.event_type for e in events]
    assert "skill_check_failed" in event_types, f"ID-004: Expected skill_check_failed; got {event_types}"
    assert "condition_applied" not in event_types, f"ID-004: condition_applied should not fire on failure"
    target_conds = ws.entities["target_01"].get(EF.CONDITIONS, {})
    assert "shaken" not in target_conds, f"ID-004: shaken applied despite failed check"


# ---------------------------------------------------------------------------
# ID-005: Standard action consumed (events imply action was taken)
# ---------------------------------------------------------------------------

def test_id_005_action_consumed():
    """ID-005: DemoralizeIntent resolves without error; events confirm action processed."""
    ws, nid, events = _run_demoralize(d20_roll=15)
    # At minimum one event should have been emitted (either condition_applied or skill_check_failed)
    assert len(events) >= 1, "ID-005: No events emitted for DemoralizeIntent"


# ---------------------------------------------------------------------------
# ID-006: Failure → target HP unchanged
# ---------------------------------------------------------------------------

def test_id_006_fail_hp_unchanged():
    """ID-006: DemoralizeIntent fails → no HP delta on target."""
    ws, nid, events = _run_demoralize(d20_roll=1, actor_cha_mod=0, actor_intimidate_ranks=0,
                                      target_hd=10, target_wis_mod=4)
    hp_events = [e for e in events if e.event_type == "hp_changed"]
    assert len(hp_events) == 0, f"ID-006: Unexpected HP events: {hp_events}"


# ---------------------------------------------------------------------------
# ID-007: Target already Shaken → duration refreshed (no escalation to Frightened)
# ---------------------------------------------------------------------------

def test_id_007_already_shaken_refreshes_duration():
    """ID-007: Target already Shaken → SHAKEN refreshed, not escalated to Frightened."""
    # Pre-set shaken condition on target
    existing_shaken = {"condition_type": "shaken", "source": "old", "duration_rounds": 1}
    ws, nid, events = _run_demoralize(d20_roll=15, actor_cha_mod=3, actor_intimidate_ranks=4,
                                      target_hd=2, target_wis_mod=0,
                                      target_conditions={"shaken": existing_shaken})
    # Should still produce condition_applied (refresh), not frightened
    event_types = [e.event_type for e in events]
    assert "condition_applied" in event_types, f"ID-007: Expected condition_applied (refresh); got {event_types}"
    assert "frightened" not in str(ws.entities["target_01"].get(EF.CONDITIONS, {})), \
        "ID-007: Target escalated to frightened (should only refresh)"


# ---------------------------------------------------------------------------
# ID-008: High-WIS/HD target — DC reflects HD + WIS mod
# ---------------------------------------------------------------------------

def test_id_008_dc_reflects_hd_and_wis():
    """ID-008: High-WIS/HD target → DC = HD + WIS mod; roll must beat it correctly."""
    # DC = hd=8 + wis_mod=3 = 11. Roll: d20=10, cha=0, ranks=0 → 10. Fails (10 < 11).
    ws, nid, events = _run_demoralize(d20_roll=10, actor_cha_mod=0, actor_intimidate_ranks=0,
                                      target_hd=8, target_wis_mod=3)
    failed = next((e for e in events if e.event_type == "skill_check_failed"), None)
    assert failed is not None, f"ID-008: Expected skill_check_failed; got {[e.event_type for e in events]}"
    assert failed.payload["dc"] == 11, f"ID-008: DC should be 11 (HD=8 + WIS=3); got {failed.payload['dc']}"
