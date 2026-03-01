"""Gate tests: WO-ENGINE-WF-SCHEMA-FIX-001 — Weapon Focus schema unification.

Root cause fixed: Two independent WF implementations with incompatible key schemas.
  Path A (feat_resolver.get_attack_modifier): weapon_focus_{weapon_name} — now canonical
  Path B (attack_resolver._wf_bonus): weapon_focus_{weapon_type} — REMOVED

Canonical key: f"weapon_focus_{weapon_name}" where weapon_name = EF.WEAPON["name"].lower()

Tests:
  WFS-001: Path A fires correctly — weapon_focus_longsword + longsword entity → +1
  WFS-002: Path B is gone — weapon_focus_longsword (not weapon_focus_one-handed) is the key
  WFS-003: EF.WEAPON is dict with name key → name extracted, feat fires
  WFS-004: EF.WEAPON with spaces → normalized (lowered, spaces→underscores)
  WFS-005: weapon_focus_active event payload has weapon_name (not weapon_type)
  WFS-006: Name mismatch (feat_name ≠ entity weapon name) → no +1 (PHB p.102 specificity)
  WFS-007: Full attack resolver uses canonical path — both attacks get +1
  WFS-008: No name in EF.WEAPON dict → no WF bonus (graceful degradation)
"""

import unittest.mock as mock
from typing import Any, Dict

from aidm.core.attack_resolver import resolve_attack
from aidm.core.full_attack_resolver import resolve_full_attack, FullAttackIntent
from aidm.core.state import WorldState
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.entity_fields import EF


# ---------------------------------------------------------------------------
# Weapon fixtures
# ---------------------------------------------------------------------------

_ONE_HANDED = Weapon(
    damage_dice="1d8", damage_bonus=0, damage_type="slashing",
    critical_multiplier=2, critical_range=20,
    is_two_handed=False, grip="one-handed", weapon_type="one-handed",
    range_increment=0, enhancement_bonus=0,
)

_LIGHT = Weapon(
    damage_dice="1d6", damage_bonus=0, damage_type="slashing",
    critical_multiplier=2, critical_range=20,
    is_two_handed=False, grip="one-handed", weapon_type="light",
    range_increment=0, enhancement_bonus=0,
)


# ---------------------------------------------------------------------------
# Entity builders
# ---------------------------------------------------------------------------

def _attacker(feats=None, weapon_ef=None, bab=6) -> Dict[str, Any]:
    return {
        EF.ENTITY_ID: "att",
        EF.TEAM: "party",
        EF.HP_CURRENT: 50, EF.HP_MAX: 50, EF.AC: 15,
        EF.ATTACK_BONUS: bab, EF.BAB: bab,
        EF.STR_MOD: 2, EF.DEX_MOD: 1,
        EF.DEFEATED: False, EF.DYING: False, EF.STABLE: False, EF.DISABLED: False,
        EF.CONDITIONS: {},
        EF.FEATS: feats or [],
        EF.POSITION: {"x": 0, "y": 0},
        EF.SIZE_CATEGORY: "medium",
        EF.INSPIRE_COURAGE_ACTIVE: False,
        EF.NEGATIVE_LEVELS: 0,
        EF.WEAPON_BROKEN: False,
        EF.FAVORED_ENEMIES: [],
        EF.CLASS_LEVELS: {"fighter": 6},
        EF.WEAPON: weapon_ef if weapon_ef is not None else {"name": "longsword", "enhancement_bonus": 0, "tags": [], "material": "steel", "alignment": "none"},
    }


def _attacker2(feats=None, weapon_ef=None, bab=6) -> Dict[str, Any]:
    d = _attacker(feats=feats, weapon_ef=weapon_ef, bab=bab)
    d[EF.ENTITY_ID] = "att2"
    return d


def _target() -> Dict[str, Any]:
    return {
        EF.ENTITY_ID: "tgt",
        EF.TEAM: "monsters",
        EF.HP_CURRENT: 100, EF.HP_MAX: 100, EF.AC: 10,
        EF.DEFEATED: False, EF.DYING: False, EF.STABLE: False, EF.DISABLED: False,
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.POSITION: {"x": 1, "y": 0},
        EF.SIZE_CATEGORY: "medium",
        EF.DAMAGE_REDUCTIONS: [],
        EF.SAVE_FORT: 2, EF.CON_MOD: 1,
        EF.CREATURE_TYPE: "humanoid",
        EF.INSPIRE_COURAGE_ACTIVE: False,
        EF.CLASS_LEVELS: {},
        EF.DEX_MOD: 1,
    }


def _ws(att, tgt) -> WorldState:
    return WorldState(
        ruleset_version="3.5e",
        entities={att[EF.ENTITY_ID]: att, tgt[EF.ENTITY_ID]: tgt},
        active_combat={"initiative_order": [att[EF.ENTITY_ID], tgt[EF.ENTITY_ID]]},
    )


def _rng(d20=15, dmg=3):
    stream = mock.MagicMock()
    stream.randint.side_effect = [d20, dmg] + [dmg] * 20
    rng = mock.MagicMock()
    rng.stream.return_value = stream
    return rng


def _intent(attacker_id="att", weapon=None, attack_bonus=8) -> AttackIntent:
    return AttackIntent(
        attacker_id=attacker_id,
        target_id="tgt",
        attack_bonus=attack_bonus,
        weapon=weapon or _ONE_HANDED,
        power_attack_penalty=0,
    )


def _atk_total(events) -> int:
    for e in events:
        if e.event_type == "attack_roll":
            return e.payload["total"]
    return None


# ---------------------------------------------------------------------------
# WFS-001: Path A fires — weapon_focus_longsword + longsword entity → +1 attack
# ---------------------------------------------------------------------------

def test_wfs001_canonical_path_fires():
    """WFS-001: weapon_focus_longsword + EF.WEAPON["name"]="longsword" → +1 attack (Path A canonical)."""
    weapon_ef = {"name": "longsword", "enhancement_bonus": 0, "tags": [], "material": "steel", "alignment": "none"}
    a_wf = _attacker(feats=["weapon_focus_longsword"], weapon_ef=weapon_ef)
    a_no = _attacker2(feats=[], weapon_ef=weapon_ef)
    t = _target()

    events_wf = resolve_attack(_intent("att", _ONE_HANDED), _ws(a_wf, t), _rng(15), next_event_id=0, timestamp=0.0)
    events_no = resolve_attack(_intent("att2", _ONE_HANDED), _ws(a_no, t), _rng(15), next_event_id=0, timestamp=0.0)

    assert _atk_total(events_wf) == _atk_total(events_no) + 1, (
        f"WFS-001: weapon_focus_longsword + longsword entity should give +1; "
        f"got {_atk_total(events_wf)} vs {_atk_total(events_no)}"
    )


# ---------------------------------------------------------------------------
# WFS-002: weapon_focus_one-handed no longer fires (Path B removed)
# ---------------------------------------------------------------------------

def test_wfs002_old_weapon_type_key_no_longer_fires():
    """WFS-002: weapon_focus_one-handed (old Path B format) no longer gives +1 after schema fix."""
    weapon_ef = {"name": "longsword", "enhancement_bonus": 0, "tags": [], "material": "steel", "alignment": "none"}
    # Old-style key: weapon_focus_{weapon_type} — Path B is deleted; this should NOT grant +1
    a_old_key = _attacker(feats=["weapon_focus_one-handed"], weapon_ef=weapon_ef)
    a_no = _attacker2(feats=[], weapon_ef=weapon_ef)
    t = _target()

    events_old = resolve_attack(_intent("att", _ONE_HANDED), _ws(a_old_key, t), _rng(15), next_event_id=0, timestamp=0.0)
    events_no = resolve_attack(_intent("att2", _ONE_HANDED), _ws(a_no, t), _rng(15), next_event_id=0, timestamp=0.0)

    assert _atk_total(events_old) == _atk_total(events_no), (
        f"WFS-002: weapon_focus_one-handed (old type-based key) should NOT fire after schema fix; "
        f"got {_atk_total(events_old)} vs {_atk_total(events_no)}"
    )


# ---------------------------------------------------------------------------
# WFS-003: EF.WEAPON is dict with name → name extracted, feat fires
# ---------------------------------------------------------------------------

def test_wfs003_weapon_ef_dict_name_extracted():
    """WFS-003: EF.WEAPON = {"name": "rapier", ...} → feat_context["weapon_name"]="rapier" → WF fires."""
    weapon_ef = {"name": "rapier", "enhancement_bonus": 0, "tags": [], "material": "steel", "alignment": "none"}
    a_wf = _attacker(feats=["weapon_focus_rapier"], weapon_ef=weapon_ef)
    a_no = _attacker2(feats=[], weapon_ef=weapon_ef)
    t = _target()

    events_wf = resolve_attack(_intent("att", _LIGHT), _ws(a_wf, t), _rng(15), next_event_id=0, timestamp=0.0)
    events_no = resolve_attack(_intent("att2", _LIGHT), _ws(a_no, t), _rng(15), next_event_id=0, timestamp=0.0)

    assert _atk_total(events_wf) == _atk_total(events_no) + 1, (
        f"WFS-003: weapon_focus_rapier with rapier entity dict should give +1; "
        f"got {_atk_total(events_wf)} vs {_atk_total(events_no)}"
    )


# ---------------------------------------------------------------------------
# WFS-004: EF.WEAPON name with spaces → normalized to underscores
# ---------------------------------------------------------------------------

def test_wfs004_weapon_name_spaces_normalized():
    """WFS-004: EF.WEAPON["name"]="Hand Axe" → normalized to "hand_axe" → weapon_focus_hand_axe fires."""
    weapon_ef = {"name": "Hand Axe", "enhancement_bonus": 0, "tags": [], "material": "steel", "alignment": "none"}
    a_wf = _attacker(feats=["weapon_focus_hand_axe"], weapon_ef=weapon_ef)
    a_no = _attacker2(feats=[], weapon_ef=weapon_ef)
    t = _target()

    events_wf = resolve_attack(_intent("att", _LIGHT), _ws(a_wf, t), _rng(15), next_event_id=0, timestamp=0.0)
    events_no = resolve_attack(_intent("att2", _LIGHT), _ws(a_no, t), _rng(15), next_event_id=0, timestamp=0.0)

    assert _atk_total(events_wf) == _atk_total(events_no) + 1, (
        f"WFS-004: 'Hand Axe' should normalize to 'hand_axe'; weapon_focus_hand_axe should fire; "
        f"got {_atk_total(events_wf)} vs {_atk_total(events_no)}"
    )


# ---------------------------------------------------------------------------
# WFS-005: weapon_focus_active event has weapon_name (not weapon_type)
# ---------------------------------------------------------------------------

def test_wfs005_event_payload_uses_weapon_name():
    """WFS-005: weapon_focus_active event payload has key weapon_name, not weapon_type."""
    weapon_ef = {"name": "longsword", "enhancement_bonus": 0, "tags": [], "material": "steel", "alignment": "none"}
    a = _attacker(feats=["weapon_focus_longsword"], weapon_ef=weapon_ef)
    t = _target()

    events = resolve_attack(_intent("att", _ONE_HANDED), _ws(a, t), _rng(15), next_event_id=0, timestamp=0.0)

    wf_ev = next((e for e in events if e.event_type == "weapon_focus_active"), None)
    assert wf_ev is not None, "WFS-005: weapon_focus_active event should fire when WF active"
    assert "weapon_name" in wf_ev.payload, (
        f"WFS-005: payload must have 'weapon_name' key; got keys: {list(wf_ev.payload.keys())}"
    )
    assert "weapon_type" not in wf_ev.payload, (
        f"WFS-005: old 'weapon_type' key must be absent from event payload; got: {wf_ev.payload}"
    )
    assert wf_ev.payload["weapon_name"] == "longsword", (
        f"WFS-005: weapon_name should be 'longsword'; got: {wf_ev.payload['weapon_name']}"
    )


# ---------------------------------------------------------------------------
# WFS-006: Name mismatch → no bonus (PHB p.102 specificity — must choose one weapon type)
# ---------------------------------------------------------------------------

def test_wfs006_name_mismatch_no_bonus():
    """WFS-006: weapon_focus_shortsword but entity wields longsword → 0 bonus (PHB p.102)."""
    weapon_ef_longsword = {"name": "longsword", "enhancement_bonus": 0, "tags": [], "material": "steel", "alignment": "none"}
    a_mismatch = _attacker(feats=["weapon_focus_shortsword"], weapon_ef=weapon_ef_longsword)
    a_no = _attacker2(feats=[], weapon_ef=weapon_ef_longsword)
    t = _target()

    events_mismatch = resolve_attack(_intent("att", _ONE_HANDED), _ws(a_mismatch, t), _rng(15), next_event_id=0, timestamp=0.0)
    events_no = resolve_attack(_intent("att2", _ONE_HANDED), _ws(a_no, t), _rng(15), next_event_id=0, timestamp=0.0)

    assert _atk_total(events_mismatch) == _atk_total(events_no), (
        f"WFS-006: feat for shortsword should NOT apply when wielding longsword; "
        f"got {_atk_total(events_mismatch)} vs {_atk_total(events_no)}"
    )
    wf_events = [e for e in events_mismatch if e.event_type == "weapon_focus_active"]
    assert len(wf_events) == 0, "WFS-006: weapon_focus_active must not fire on name mismatch"


# ---------------------------------------------------------------------------
# WFS-007: Full attack resolver uses canonical path — both attacks get +1
# ---------------------------------------------------------------------------

def test_wfs007_full_attack_canonical_path():
    """WFS-007: FullAttackIntent with weapon_focus_longsword → all iterative attacks get +1."""
    weapon_ef = {"name": "longsword", "enhancement_bonus": 0, "tags": [], "material": "steel", "alignment": "none"}
    a_wf = _attacker(feats=["weapon_focus_longsword"], weapon_ef=weapon_ef, bab=11)
    a_no = _attacker2(feats=[], weapon_ef=weapon_ef, bab=11)
    t = _target()
    t[EF.AC] = 30  # High AC → all attacks miss, all iteratives run

    fa_wf = FullAttackIntent(attacker_id="att", target_id="tgt", weapon=_ONE_HANDED, base_attack_bonus=11, power_attack_penalty=0)
    fa_no = FullAttackIntent(attacker_id="att2", target_id="tgt", weapon=_ONE_HANDED, base_attack_bonus=11, power_attack_penalty=0)

    events_wf = resolve_full_attack(fa_wf, _ws(a_wf, t), _rng(5, 1), next_event_id=0, timestamp=0.0)
    events_no = resolve_full_attack(fa_no, _ws(a_no, t), _rng(5, 1), next_event_id=0, timestamp=0.0)

    atks_wf = [e.payload["total"] for e in events_wf if e.event_type == "attack_roll"]
    atks_no = [e.payload["total"] for e in events_no if e.event_type == "attack_roll"]

    assert len(atks_wf) >= 2 and len(atks_wf) == len(atks_no), (
        f"WFS-007: need ≥2 iterative attacks; got wf={atks_wf} no={atks_no}"
    )
    for i, (tw, tn) in enumerate(zip(atks_wf, atks_no)):
        assert tw == tn + 1, f"WFS-007: attack {i}: expected +1 from WF; got {tw} vs {tn}"


# ---------------------------------------------------------------------------
# WFS-008: No name in EF.WEAPON dict → no WF bonus (graceful degradation)
# ---------------------------------------------------------------------------

def test_wfs008_missing_name_in_weapon_dict_no_bonus():
    """WFS-008: EF.WEAPON dict has no 'name' key → weapon_name="" → no WF bonus fires."""
    weapon_ef_no_name = {"enhancement_bonus": 0, "tags": [], "material": "steel", "alignment": "none"}
    # Feat can't match "" — so no bonus
    a = _attacker(feats=["weapon_focus_longsword"], weapon_ef=weapon_ef_no_name)
    a_no = _attacker2(feats=[], weapon_ef=weapon_ef_no_name)
    t = _target()

    events_a = resolve_attack(_intent("att", _ONE_HANDED), _ws(a, t), _rng(15), next_event_id=0, timestamp=0.0)
    events_no = resolve_attack(_intent("att2", _ONE_HANDED), _ws(a_no, t), _rng(15), next_event_id=0, timestamp=0.0)

    # No bonus because weapon_name="" → weapon_focus_ not in feats, AND guard "_weapon_name and ..." fires
    assert _atk_total(events_a) == _atk_total(events_no), (
        f"WFS-008: missing name in EF.WEAPON → no WF bonus; "
        f"got {_atk_total(events_a)} vs {_atk_total(events_no)}"
    )
    wf_events = [e for e in events_a if e.event_type == "weapon_focus_active"]
    assert len(wf_events) == 0, "WFS-008: weapon_focus_active must not fire when name is missing"
