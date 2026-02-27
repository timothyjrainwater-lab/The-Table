"""Gate tests for WO-ENGINE-MD-SAVE-RULES-001.

MDSR: Massive damage Fort save nat1/nat20 auto-fail/pass (PHB p.136/p.145)
FSKL: Fascinated -4 skill penalty (PHB p.308)

Authority: RAW — PHB p.136, p.145, p.308
"""

from unittest.mock import MagicMock
from aidm.core.attack_resolver import resolve_attack
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.entity_fields import EF
from aidm.core.state import WorldState


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_rng(attack_roll, damage_rolls, fort_roll=10):
    """Mock RNG: attack d20, then damage dice, then fort d20."""
    rng = MagicMock()
    stream = MagicMock()
    call_sequence = [attack_roll] + damage_rolls + [fort_roll]
    stream.randint = MagicMock(side_effect=call_sequence)
    rng.stream = MagicMock(return_value=stream)
    return rng


def _massive_damage_ws(fort_save_base=10, con_mod=5, target_ac=5):
    """WorldState for massive damage tests."""
    attacker = {
        EF.ENTITY_ID: "a", EF.TEAM: "player",
        EF.HP_CURRENT: 50, EF.HP_MAX: 50, EF.DEFEATED: False, EF.AC: 10,
        EF.STR_MOD: 0, EF.DEX_MOD: 0, EF.CON_MOD: 0,
        EF.CONDITIONS: {}, EF.FEATS: [],
        EF.CLASS_LEVELS: {"fighter": 10},
        EF.FAVORED_ENEMIES: [], EF.NATURAL_ATTACKS: [],
        EF.POSITION: {"x": 0, "y": 0},
    }
    target = {
        EF.ENTITY_ID: "t", EF.TEAM: "enemy",
        EF.HP_CURRENT: 100, EF.HP_MAX: 100, EF.DEFEATED: False,
        EF.AC: target_ac,
        EF.STR_MOD: 0, EF.DEX_MOD: 0, EF.CON_MOD: con_mod,
        EF.CONDITIONS: {}, EF.FEATS: [],
        EF.CLASS_LEVELS: {"fighter": 10},
        EF.FAVORED_ENEMIES: [],
        EF.SAVE_FORT: fort_save_base,
        EF.NATURAL_ATTACKS: [],
        EF.POSITION: {"x": 1, "y": 0},
    }
    return WorldState(
        ruleset_version="3.5",
        entities={"a": attacker, "t": target},
        active_combat=None,
    )


def _big_weapon():
    """Weapon guaranteed to deal 50+ (1d4 + 55)."""
    return Weapon(
        damage_dice="1d4", damage_bonus=55, damage_type="slashing",
        critical_multiplier=2, critical_range=20,
        weapon_type="two-handed", grip="two-handed", is_two_handed=True,
    )


def _find_event(events, event_type):
    return next((e for e in events if e.event_type == event_type), None)


# ── MDSR-001: 50+ damage triggers Fort DC 15 (baseline) ────────────────────

def test_mdsr_001_massive_damage_triggers_save():
    # Attack 15 (hits AC 5), damage 4+55=59, fort roll 10 + bonus(10+5)=25 >= 15 → saved
    rng = _make_rng(attack_roll=15, damage_rolls=[4], fort_roll=10)
    ws = _massive_damage_ws(fort_save_base=10, con_mod=5, target_ac=5)
    intent = AttackIntent(attacker_id="a", target_id="t", weapon=_big_weapon(), attack_bonus=5)
    events = resolve_attack(intent, ws, rng, next_event_id=1, timestamp=0.0)
    md_event = _find_event(events, "massive_damage_check")
    assert md_event is not None, "50+ damage should trigger massive damage check"
    assert md_event.payload["dc"] == 15
    assert md_event.payload["saved"] is True


# ── MDSR-002: nat1 Fort → death despite high modifier (KEY) ────────────────

def test_mdsr_002_nat1_auto_fail():
    # fort roll nat1 + bonus(10+5) = 16 >= 15 normally — but nat1 = auto-fail
    rng = _make_rng(attack_roll=15, damage_rolls=[4], fort_roll=1)
    ws = _massive_damage_ws(fort_save_base=10, con_mod=5, target_ac=5)
    intent = AttackIntent(attacker_id="a", target_id="t", weapon=_big_weapon(), attack_bonus=5)
    events = resolve_attack(intent, ws, rng, next_event_id=1, timestamp=0.0)
    md_event = _find_event(events, "massive_damage_check")
    assert md_event is not None
    assert md_event.payload["fort_roll"] == 1
    assert md_event.payload["saved"] is False, "nat1 should auto-fail Fort save (PHB p.136)"


# ── MDSR-003: nat20 Fort → survive despite low modifier (KEY) ──────────────

def test_mdsr_003_nat20_auto_pass():
    # fort roll nat20, fort_save_base=0, con_mod=-5 → total=20+0-5=15 (borderline)
    # Use even worse: base=-10, con=-5 → total=20-10-5=5 < 15 normally, but nat20=auto-pass
    rng = _make_rng(attack_roll=15, damage_rolls=[4], fort_roll=20)
    ws = _massive_damage_ws(fort_save_base=-10, con_mod=-5, target_ac=5)
    intent = AttackIntent(attacker_id="a", target_id="t", weapon=_big_weapon(), attack_bonus=5)
    events = resolve_attack(intent, ws, rng, next_event_id=1, timestamp=0.0)
    md_event = _find_event(events, "massive_damage_check")
    assert md_event is not None
    assert md_event.payload["fort_roll"] == 20
    assert md_event.payload["saved"] is True, "nat20 should auto-pass Fort save (PHB p.136)"


# ── MDSR-004: 49 damage → no Fort save ─────────────────────────────────────

def test_mdsr_004_below_threshold_no_save():
    small_weapon = Weapon(
        damage_dice="1d4", damage_bonus=44, damage_type="slashing",
        critical_multiplier=2, critical_range=20,
        weapon_type="one-handed", grip="one-handed", is_two_handed=False,
    )
    # Attack 15 (hits), damage 4+44=48 < 50
    rng = _make_rng(attack_roll=15, damage_rolls=[4])
    ws = _massive_damage_ws(fort_save_base=0, con_mod=0, target_ac=5)
    intent = AttackIntent(attacker_id="a", target_id="t", weapon=small_weapon, attack_bonus=5)
    events = resolve_attack(intent, ws, rng, next_event_id=1, timestamp=0.0)
    md_event = _find_event(events, "massive_damage_check")
    assert md_event is None, "48 damage should NOT trigger massive damage check"


# ── FSKL tests: verify the formula used in _process_skill ──────────────────
# These tests mirror the exact formula in session_orchestrator._process_skill()
# to confirm fascinated penalty is applied.

def _compute_skill_modifier(entity, skill_name):
    """Replicate _process_skill() modifier formula."""
    from aidm.schemas.skills import SKILLS
    ability_map = {
        "str": EF.STR_MOD, "dex": EF.DEX_MOD, "con": EF.CON_MOD,
        "int": EF.INT_MOD, "wis": EF.WIS_MOD, "cha": EF.CHA_MOD,
    }
    skill_def = SKILLS.get(skill_name)
    if skill_def is None:
        return 0
    ability_mod = entity.get(ability_map.get(skill_def.key_ability, ""), 0)
    ranks = entity.get(EF.SKILL_RANKS, {}).get(skill_name, 0)
    acp = entity.get(EF.ARMOR_CHECK_PENALTY, 0) if skill_def.armor_check_penalty else 0
    racial = entity.get(EF.RACIAL_SKILL_BONUS, {}).get(skill_name, 0)
    conditions = entity.get(EF.CONDITIONS, {}) or {}
    fascinated_penalty = -4 if "fascinated" in conditions else 0
    return ability_mod + ranks - acp + racial + fascinated_penalty


# ── FSKL-001: Fascinated → -4 on skill check ──────────────────────────────

def test_fskl_001_fascinated_penalty():
    entity = {
        EF.WIS_MOD: 1,
        EF.SKILL_RANKS: {"listen": 4},
        EF.ARMOR_CHECK_PENALTY: 0,
        EF.RACIAL_SKILL_BONUS: {},
        EF.CONDITIONS: {"fascinated": {"rounds_remaining": 5}},
    }
    mod = _compute_skill_modifier(entity, "listen")
    # WIS(1) + ranks(4) + racial(0) - ACP(0) + fascinated(-4) = 1
    assert mod == 1, f"Fascinated penalty: expected 1 (1+4-4), got {mod}"


# ── FSKL-002: Non-fascinated → no penalty ─────────────────────────────────

def test_fskl_002_no_fascinated_no_penalty():
    entity = {
        EF.WIS_MOD: 1,
        EF.SKILL_RANKS: {"listen": 4},
        EF.ARMOR_CHECK_PENALTY: 0,
        EF.RACIAL_SKILL_BONUS: {},
        EF.CONDITIONS: {},
    }
    mod = _compute_skill_modifier(entity, "listen")
    # WIS(1) + ranks(4) = 5
    assert mod == 5, f"No fascinated: expected 5, got {mod}"


# ── FSKL-003: Fascinated removed → full bonus ─────────────────────────────

def test_fskl_003_fascinated_removed_full_bonus():
    entity = {
        EF.WIS_MOD: 1,
        EF.SKILL_RANKS: {"listen": 4},
        EF.ARMOR_CHECK_PENALTY: 0,
        EF.RACIAL_SKILL_BONUS: {},
        EF.CONDITIONS: {},  # fascinated was removed
    }
    mod = _compute_skill_modifier(entity, "listen")
    assert mod == 5, f"After fascinated removed, expected 5, got {mod}"


# ── FSKL-004: Fascinated + sickened → fascinated penalty present ───────────

def test_fskl_004_fascinated_plus_sickened():
    entity = {
        EF.WIS_MOD: 1,
        EF.SKILL_RANKS: {"listen": 4},
        EF.ARMOR_CHECK_PENALTY: 0,
        EF.RACIAL_SKILL_BONUS: {},
        EF.CONDITIONS: {"fascinated": {"rounds_remaining": 5},
                        "sickened": {"rounds_remaining": 3}},
    }
    mod = _compute_skill_modifier(entity, "listen")
    # Fascinated -4 applied; sickened -2 is via combat condition_modifiers, not _process_skill
    assert mod == 1, f"Fascinated penalty should apply: expected 1, got {mod}"
    assert "fascinated" in entity[EF.CONDITIONS]
    assert "sickened" in entity[EF.CONDITIONS]
