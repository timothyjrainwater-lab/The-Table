"""Gate tests: Monk Diamond Soul (SR = level + 10) — WO-ENGINE-DIAMOND-SOUL-001.

DS-001: Monk L13 — EF.SR = 23
DS-002: Monk L20 — EF.SR = 30
DS-003: Monk L13, CL 15 + roll 10 = 25 ≥ 23 — SR passed
DS-004: Monk L13, CL 10 + roll 5 = 15 < 23 — SR blocked
DS-005: Monk L12 — no SR (SR = 0 or absent)
DS-006: Monk 13 / Fighter 7 — SR = 23 (monk levels only)
DS-007: Monk L13 vs caster with Spell Penetration — +2 CL on SR check
DS-008: level_up() Monk L12 → L13 — delta["spell_resistance"] = 23
"""

import pytest
from aidm.chargen.builder import build_character, level_up
from aidm.core.save_resolver import check_spell_resistance
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.schemas.saves import SRCheck


class _FixedRNG:
    def __init__(self, value: int = 10):
        self._value = value

    def stream(self, name):
        return self

    def randint(self, lo, hi):
        return min(max(self._value, lo), hi)


def _make_ws(monk: dict, caster: dict, monk_id: str = "monk", caster_id: str = "caster") -> WorldState:
    return WorldState(
        ruleset_version="3.5",
        entities={monk_id: monk, caster_id: caster},
        active_combat=None,
    )


def _build_monk(level: int) -> dict:
    """Build a monk entity via build_character (uses real chargen)."""
    return build_character(
        race="human",
        class_name="monk",
        level=level,
        ability_overrides={"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10},
    )


def _build_monk_raw(monk_level: int, sr_override: int = 0) -> dict:
    """Build a minimal monk entity dict for SR checks."""
    return {
        EF.CLASS_LEVELS: {"monk": monk_level},
        EF.SR: sr_override,
        EF.FEATS: [],
        EF.HP_CURRENT: 50,
        EF.HP_MAX: 50,
        EF.DEFEATED: False,
        EF.TEAM: "party",
    }


def _caster_entity(feats: list | None = None) -> dict:
    return {
        EF.CLASS_LEVELS: {"wizard": 15},
        EF.FEATS: feats or [],
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 30,
        EF.DEFEATED: False,
        EF.TEAM: "monsters",
    }


# ── DS-001: Monk L13 — EF.SR = 23 ─────────────────────────────────────────────

def test_ds001_monk_l13_sr_23():
    """Monk L13 at chargen: EF.SR must equal 23 (13 + 10)."""
    entity = _build_monk(13)
    assert entity.get(EF.SR, 0) == 23, f"Expected SR=23, got {entity.get(EF.SR, 0)}"


# ── DS-002: Monk L20 — EF.SR = 30 ─────────────────────────────────────────────

def test_ds002_monk_l20_sr_30():
    """Monk L20 at chargen: EF.SR must equal 30 (20 + 10)."""
    entity = _build_monk(20)
    assert entity.get(EF.SR, 0) == 30, f"Expected SR=30, got {entity.get(EF.SR, 0)}"


# ── DS-003: CL 15 + roll 10 = 25 ≥ 23 — passes ───────────────────────────────

def test_ds003_cl15_roll10_passes_sr23():
    """CL=15 + d20=10 = 25 ≥ SR=23 → SR check passes."""
    monk = _build_monk_raw(13, sr_override=23)
    caster = _caster_entity()
    ws = _make_ws(monk, caster)
    sr_check = SRCheck(caster_level=15, source_id="caster")
    passed, events = check_spell_resistance(sr_check, ws, "monk", _FixedRNG(10), 1, 0.0)
    assert passed is True
    sr_event = next(e for e in events if e.event_type == "spell_resistance_checked")
    assert sr_event.payload["total"] == 25   # 15 + 10
    assert sr_event.payload["sr_passed"] is True


# ── DS-004: CL 10 + roll 5 = 15 < 23 — blocked ───────────────────────────────

def test_ds004_cl10_roll5_blocked_by_sr23():
    """CL=10 + d20=5 = 15 < SR=23 → SR check fails, spell blocked."""
    monk = _build_monk_raw(13, sr_override=23)
    caster = _caster_entity()
    ws = _make_ws(monk, caster)
    sr_check = SRCheck(caster_level=10, source_id="caster")
    passed, events = check_spell_resistance(sr_check, ws, "monk", _FixedRNG(5), 1, 0.0)
    assert passed is False
    sr_event = next(e for e in events if e.event_type == "spell_resistance_checked")
    assert sr_event.payload["total"] == 15   # 10 + 5
    assert sr_event.payload["sr_passed"] is False


# ── DS-005: Monk L12 — no SR ──────────────────────────────────────────────────

def test_ds005_monk_l12_no_sr():
    """Monk L12 has no Diamond Soul yet; EF.SR must be 0 or absent."""
    entity = _build_monk(12)
    assert entity.get(EF.SR, 0) == 0, f"Expected SR=0 for L12, got {entity.get(EF.SR, 0)}"


# ── DS-006: Monk 13 / Fighter 7 — SR uses monk levels only ───────────────────

def test_ds006_multiclass_monk13_fighter7_sr23():
    """Monk 13 / Fighter 7: SR = 13+10 = 23 (monk levels only, not total level 20)."""
    entity = build_character(
        race="human",
        class_name="monk",
        level=13,
        ability_overrides={"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10},
        class_mix={"monk": 13, "fighter": 7},
    )
    assert entity.get(EF.SR, 0) == 23, (
        f"Expected SR=23 (monk-levels-only formula), got {entity.get(EF.SR, 0)}"
    )


# ── DS-007: Spell Penetration feat → +2 CL on SR check ───────────────────────

def test_ds007_spell_penetration_adds_2_to_sr_check():
    """Caster with Spell Penetration: +2 bonus on SR check (CL+2 vs SR)."""
    monk = _build_monk_raw(13, sr_override=23)
    caster = _caster_entity(feats=["spell_penetration"])
    ws = _make_ws(monk, caster)
    sr_check = SRCheck(caster_level=10, source_id="caster")
    # Without SP: CL10 + roll12 = 22 < 23 → fail.
    # With SP: CL10 + roll12 + 2 = 24 ≥ 23 → pass.
    passed, events = check_spell_resistance(sr_check, ws, "monk", _FixedRNG(12), 1, 0.0)
    sr_event = next(e for e in events if e.event_type == "spell_resistance_checked")
    assert sr_event.payload["penetration_bonus"] == 2
    assert sr_event.payload["total"] == 24  # 10 + 12 + 2
    assert passed is True


# ── DS-008: level_up() L12 → L13 returns spell_resistance = 23 ───────────────

def test_ds008_level_up_monk_l12_to_l13_gains_sr():
    """level_up(monk, 13) delta must include spell_resistance=23 (first time SR is gained)."""
    entity = _build_monk(12)
    assert entity.get(EF.SR, 0) == 0, "Precondition: L12 monk has no SR"
    delta = level_up(entity, "monk", 13)
    assert delta["spell_resistance"] == 23, (
        f"Expected delta['spell_resistance']=23, got {delta.get('spell_resistance')}"
    )
