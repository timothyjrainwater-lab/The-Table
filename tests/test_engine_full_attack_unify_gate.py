"""ENGINE-FULL-ATTACK-UNIFY Gate — WO-ENGINE-FULL-ATTACK-UNIFY-001 (FAGU): 10 tests.

Gate: FAGU
Tests: FAGU-001 through FAGU-010
WO: WO-ENGINE-FULL-ATTACK-UNIFY-001 (Batch U WO1)
Source finding: FINDING-AUDIT-FULL-ATTACK-MODIFIER-DRIFT-001 (AUDIT-WO-001, HIGH)

After FAGU, resolve_full_attack() delegates per-iterative attack to resolve_attack().
This means all 21 mechanics in resolve_attack() now apply to full-attack sequences.
Tests prove the most critical of those previously-missing mechanics now fire per-hit.

Prior state (before FAGU): resolve_full_attack called resolve_single_attack_with_critical()
which was missing Inspire Courage, Weapon Finesse, Negative Levels, blinded attacker
50% miss, flat-footed AC, Monk WIS AC, Massive Damage, and others (21 total).

FAGU-001: Full attack + Inspire Courage active → attack bonus applies to each iterative
FAGU-002: Full attack + Inspire Courage active → damage bonus applies to each hit
FAGU-003: Full attack + Weapon Finesse (DEX > STR) → DEX delta applied per iterative
FAGU-004: Full attack, attacker Blinded → blinded_miss_check emitted per attack attempt
FAGU-005: Full attack, target flat-footed → DEX denied, lower AC vs all iterative attacks
FAGU-006: Full attack, target has Monk WIS AC → AC includes WIS bonus vs all attacks
FAGU-007: Full attack, attacker Negative Level → -1/level attack penalty per iterative
FAGU-008: Full attack, 50+ damage hit → massive_damage_check triggered per qualifying hit
FAGU-009: WFC-003 regression — weapon_focus still grants +1 per hit (no double-count)
FAGU-010: WSP-003 regression — weapon_specialization still grants +2 damage per hit (no double-count)
"""

from typing import Any, Dict

import pytest

from aidm.core.full_attack_resolver import resolve_full_attack, FullAttackIntent
from aidm.core.state import WorldState
from aidm.core.rng_manager import RNGManager
from aidm.schemas.attack import Weapon
from aidm.schemas.entity_fields import EF
from aidm.schemas.conditions import (
    ConditionInstance, ConditionType, ConditionModifiers,
    create_flat_footed_condition,
)
from aidm.core.conditions import apply_condition


# ---------------------------------------------------------------------------
# Shared weapon fixtures
# ---------------------------------------------------------------------------

_LIGHT_WEAPON = Weapon(
    damage_dice="1d6",
    damage_bonus=0,
    damage_type="slashing",
    weapon_type="light",
    grip="one-handed",
    is_two_handed=False,
    range_increment=0,
    enhancement_bonus=0,
    critical_multiplier=2,
    critical_range=20,
)

_HEAVY_WEAPON_50 = Weapon(
    # Minimum damage = 50 (1d4 + 49) — triggers Massive Damage on any hit
    damage_dice="1d4",
    damage_bonus=49,
    damage_type="bludgeoning",
    weapon_type="one-handed",
    grip="one-handed",
    is_two_handed=False,
    range_increment=0,
    enhancement_bonus=0,
    critical_multiplier=2,
    critical_range=20,
)


# ---------------------------------------------------------------------------
# Entity builders
# ---------------------------------------------------------------------------

def _attacker(
    eid: str = "attacker",
    bab: int = 11,  # 3 attacks: +11/+6/+1
    str_mod: int = 1,
    dex_mod: int = 1,
    feats: list = None,
    inspire_active: bool = False,
    inspire_bonus: int = 0,
    negative_levels: int = 0,
) -> Dict[str, Any]:
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: 40,
        EF.HP_MAX: 40,
        EF.AC: 15,
        EF.ATTACK_BONUS: bab,
        EF.BAB: bab,
        EF.STR_MOD: str_mod,
        EF.DEX_MOD: dex_mod,
        EF.DEFEATED: False,
        EF.DYING: False,
        EF.STABLE: False,
        EF.DISABLED: False,
        EF.CONDITIONS: {},
        EF.FEATS: feats or [],
        EF.POSITION: {"x": 0, "y": 0},
        EF.SIZE_CATEGORY: "medium",
        EF.INSPIRE_COURAGE_ACTIVE: inspire_active,
        EF.INSPIRE_COURAGE_BONUS: inspire_bonus,
        EF.NEGATIVE_LEVELS: negative_levels,
        EF.WEAPON_BROKEN: False,
        EF.FAVORED_ENEMIES: [],
        EF.CLASS_LEVELS: {},
        EF.WEAPON: {"name": "longsword", "enhancement_bonus": 0, "tags": [], "material": "steel", "alignment": "none"},
    }


def _target(
    eid: str = "target",
    hp: int = 100,
    ac: int = 10,
    dex_mod: int = 0,
    str_mod: int = 0,
    con_mod: int = 2,
    feats: list = None,
    class_levels: dict = None,
    armor_ac_bonus: int = 0,
    monk_wis_ac_bonus: int = 0,
    deflection_bonus: int = 0,
) -> Dict[str, Any]:
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "monsters",
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp,
        EF.AC: ac,
        EF.DEX_MOD: dex_mod,
        EF.STR_MOD: str_mod,
        EF.CON_MOD: con_mod,
        EF.SAVE_FORT: 4,
        EF.DEFEATED: False,
        EF.DYING: False,
        EF.STABLE: False,
        EF.DISABLED: False,
        EF.CONDITIONS: {},
        EF.FEATS: feats or [],
        EF.POSITION: {"x": 1, "y": 0},
        EF.SIZE_CATEGORY: "medium",
        EF.DAMAGE_REDUCTIONS: [],
        EF.CREATURE_TYPE: "humanoid",
        EF.INSPIRE_COURAGE_ACTIVE: False,
        EF.CLASS_LEVELS: class_levels or {},
        EF.ARMOR_AC_BONUS: armor_ac_bonus,
        EF.MONK_WIS_AC_BONUS: monk_wis_ac_bonus,
        EF.DEFLECTION_BONUS: deflection_bonus,
    }


def _ws(attacker: dict, target: dict) -> WorldState:
    return WorldState(
        ruleset_version="3.5e",
        entities={
            attacker[EF.ENTITY_ID]: attacker,
            target[EF.ENTITY_ID]: target,
        },
        active_combat={"initiative_order": [attacker[EF.ENTITY_ID], target[EF.ENTITY_ID]]},
    )


def _fa_intent(
    attacker_id: str = "attacker",
    target_id: str = "target",
    bab: int = 11,
    weapon: Weapon = None,
) -> FullAttackIntent:
    return FullAttackIntent(
        attacker_id=attacker_id,
        target_id=target_id,
        base_attack_bonus=bab,
        weapon=weapon or _LIGHT_WEAPON,
    )


# ---------------------------------------------------------------------------
# FAGU-001: Inspire Courage attack bonus applies to each iterative
# ---------------------------------------------------------------------------

def test_fagu001_inspire_courage_attack_bonus_per_iterative():
    """FAGU-001: Full attack + Inspire Courage active → +bonus applied to each iterative attack roll.

    Before FAGU: inspire courage was missing from resolve_single_attack_with_critical().
    After FAGU: resolve_attack() applies EF.INSPIRE_COURAGE_BONUS when EF.INSPIRE_COURAGE_ACTIVE.
    PHB p.29: morale bonus to attack and damage rolls.
    """
    weapon = _LIGHT_WEAPON
    a_no_inspire = _attacker(inspire_active=False, inspire_bonus=0)
    a_inspired = _attacker(inspire_active=True, inspire_bonus=2)
    t = _target(ac=10)  # Low AC so most attacks hit

    ws_clean = _ws(a_no_inspire, t)
    ws_inspired = _ws(a_inspired, t)

    # Same seed → same d20 rolls
    events_clean = resolve_full_attack(_fa_intent(), ws_clean, RNGManager(master_seed=7), 0, 1.0)
    events_inspired = resolve_full_attack(_fa_intent(), ws_inspired, RNGManager(master_seed=7), 0, 1.0)

    attacks_clean = [e for e in events_clean if e.event_type == "attack_roll"]
    attacks_inspired = [e for e in events_inspired if e.event_type == "attack_roll"]

    assert len(attacks_clean) > 0, "Should have attack_roll events"
    assert len(attacks_clean) == len(attacks_inspired), "Same number of attacks"

    for i, (clean, inspired) in enumerate(zip(attacks_clean, attacks_inspired)):
        d20_clean = clean.payload["d20_result"]
        d20_inspired = inspired.payload["d20_result"]
        assert d20_clean == d20_inspired, f"Attack {i}: same seed → same d20"
        assert inspired.payload["total"] == clean.payload["total"] + 2, (
            f"Attack {i}: Inspire Courage +2 must apply to total "
            f"(clean={clean.payload['total']}, inspired={inspired.payload['total']})"
        )


# ---------------------------------------------------------------------------
# FAGU-002: Inspire Courage damage bonus applies to each hit
# ---------------------------------------------------------------------------

def test_fagu002_inspire_courage_damage_bonus_per_hit():
    """FAGU-002: Full attack + Inspire Courage active → +bonus applied to damage roll per hit.

    Before FAGU: inspire courage damage was missing from resolve_single_attack_with_critical().
    After FAGU: resolve_attack() adds _inspire_dmg_bonus to base_damage_with_modifiers.
    PHB p.29: morale bonus to damage rolls.
    """
    a_no_inspire = _attacker(inspire_active=False, inspire_bonus=0)
    a_inspired = _attacker(inspire_active=True, inspire_bonus=2)
    t = _target(ac=10, hp=200)  # Low AC, high HP

    ws_clean = _ws(a_no_inspire, t)
    ws_inspired = _ws(a_inspired, t)

    seed = 7
    events_clean = resolve_full_attack(_fa_intent(), ws_clean, RNGManager(master_seed=seed), 0, 1.0)
    events_inspired = resolve_full_attack(_fa_intent(), ws_inspired, RNGManager(master_seed=seed), 0, 1.0)

    dmg_clean = [e for e in events_clean if e.event_type == "damage_roll"]
    dmg_inspired = [e for e in events_inspired if e.event_type == "damage_roll"]

    assert len(dmg_clean) > 0, "Need at least one hit"
    assert len(dmg_clean) == len(dmg_inspired), "Same number of hits"

    for i, (clean, inspired) in enumerate(zip(dmg_clean, dmg_inspired)):
        assert inspired.payload["damage_total"] == clean.payload["damage_total"] + 2, (
            f"Hit {i}: Inspire Courage +2 damage must apply per hit "
            f"(clean={clean.payload['damage_total']}, inspired={inspired.payload['damage_total']})"
        )


# ---------------------------------------------------------------------------
# FAGU-003: Weapon Finesse DEX delta applied per iterative
# ---------------------------------------------------------------------------

def test_fagu003_weapon_finesse_dex_delta_per_iterative():
    """FAGU-003: Full attack + Weapon Finesse, DEX > STR → DEX delta applied to each iterative.

    Before FAGU: Weapon Finesse DEX delta was missing from resolve_single_attack_with_critical().
    After FAGU: resolve_attack() computes _finesse_delta = DEX_MOD - STR_MOD for light weapons.
    PHB p.102: Weapon Finesse lets attacker use DEX instead of STR for light weapon attacks.
    """
    # STR_MOD=1, DEX_MOD=5 → finesse delta = +4
    a_no_finesse = _attacker(str_mod=1, dex_mod=5, feats=[])
    a_finesse = _attacker(str_mod=1, dex_mod=5, feats=["weapon_finesse"])
    t = _target(ac=10, hp=200)

    ws_no = _ws(a_no_finesse, t)
    ws_fin = _ws(a_finesse, t)

    seed = 3
    events_no = resolve_full_attack(_fa_intent(weapon=_LIGHT_WEAPON), ws_no, RNGManager(master_seed=seed), 0, 1.0)
    events_fin = resolve_full_attack(_fa_intent(weapon=_LIGHT_WEAPON), ws_fin, RNGManager(master_seed=seed), 0, 1.0)

    atks_no = [e for e in events_no if e.event_type == "attack_roll"]
    atks_fin = [e for e in events_fin if e.event_type == "attack_roll"]

    assert len(atks_no) > 0, "Need attack_roll events"
    assert len(atks_no) == len(atks_fin), "Same attack count"

    # Weapon Finesse: BAB is passed as `intent.attack_bonus` which already includes STR_MOD
    # from FAR's base_attack_bonus. AR adds finesse_delta = DEX - STR = +4. So total = +4 more.
    for i, (no, fin) in enumerate(zip(atks_no, atks_fin)):
        d20_no = no.payload["d20_result"]
        d20_fin = fin.payload["d20_result"]
        assert d20_no == d20_fin, f"Attack {i}: same seed → same d20"
        assert fin.payload["total"] == no.payload["total"] + 4, (
            f"Attack {i}: Finesse delta +4 must apply "
            f"(no={no.payload['total']}, fin={fin.payload['total']})"
        )


# ---------------------------------------------------------------------------
# FAGU-004: Blinded attacker — blinded_miss_check emitted per attack attempt
# ---------------------------------------------------------------------------

def test_fagu004_blinded_attacker_miss_check_per_attack():
    """FAGU-004: Full attack, attacker Blinded → blinded_miss_check emitted per iterative.

    Before FAGU: Blinded attacker 50% miss chance was missing from full-attack path.
    After FAGU: resolve_attack() checks _is_blinded() per-hit (lines 574-589 of AR).
    PHB p.309: Blinded character must succeed at a 50% miss chance on attacks.
    """
    blinded_cond = ConditionInstance(
        condition_type=ConditionType.BLINDED,
        source="test_spell",
        applied_at_event_id=0,
        modifiers=ConditionModifiers(attack_modifier=-2, ac_modifier=-2, loses_dex_to_ac=True),
        notes="Blinded",
    )

    attacker = _attacker()
    t = _target(ac=10, hp=300)  # Very high HP so target doesn't die
    ws_base = _ws(attacker, t)

    # Apply blinded condition to attacker
    ws_blinded = apply_condition(ws_base, "attacker", blinded_cond)

    # 3 iteratives: with BAB 11 → +11/+6/+1
    # Each resolves via resolve_attack() which checks blinded before d20
    events = resolve_full_attack(
        _fa_intent(bab=11), ws_blinded, RNGManager(master_seed=99), 0, 1.0
    )

    blind_checks = [e for e in events if e.event_type == "blinded_miss_check"]

    # Exactly 3 blinded_miss_check events — one per iterative attempt
    assert len(blind_checks) == 3, (
        f"Expected 3 blinded_miss_check events (one per iterative), got {len(blind_checks)}. "
        f"Events: {[e.event_type for e in events]}"
    )
    # Each check must identify the correct attacker
    for chk in blind_checks:
        assert chk.payload["attacker_id"] == "attacker"


# ---------------------------------------------------------------------------
# FAGU-005: Flat-footed target — DEX denied → lower AC vs all iterative attacks
# ---------------------------------------------------------------------------

def test_fagu005_flat_footed_target_dex_denied_all_attacks():
    """FAGU-005: Full attack, target flat-footed → DEX denied, lower AC for all iteratives.

    Before FAGU: flat-footed DEX denial was missing from resolve_single_attack_with_critical().
    After FAGU: resolve_attack() calls _target_retains_dex_via_uncanny_dodge() + dex_penalty.
    PHB p.311: A flat-footed character loses his Dex bonus to AC.
    """
    t_normal = _target(ac=14, dex_mod=3)   # AC 14 with DEX +3 already baked in
    t_flatfoot = _target(ac=14, dex_mod=3)  # Same AC, but flat-footed → DEX stripped

    attacker = _attacker()
    ws_normal = _ws(attacker, t_normal)
    ws_base_ff = _ws(attacker, t_flatfoot)

    # Apply flat-footed condition to the target in the second world state
    ff_cond = create_flat_footed_condition(source="surprise", applied_at_event_id=0)
    ws_ff = apply_condition(ws_base_ff, "target", ff_cond)

    seed = 5
    events_normal = resolve_full_attack(_fa_intent(), ws_normal, RNGManager(master_seed=seed), 0, 1.0)
    events_ff = resolve_full_attack(_fa_intent(), ws_ff, RNGManager(master_seed=seed), 0, 1.0)

    atks_normal = [e for e in events_normal if e.event_type == "attack_roll"]
    atks_ff = [e for e in events_ff if e.event_type == "attack_roll"]

    assert len(atks_normal) > 0, "Need attack_roll events"
    # Flat-footed target should have lower (or equal) target_ac vs all attacks
    for i, (norm, ff) in enumerate(zip(atks_normal, atks_ff)):
        assert ff.payload["target_ac"] <= norm.payload["target_ac"], (
            f"Attack {i}: flat-footed target AC must be <= normal AC "
            f"(normal={norm.payload['target_ac']}, ff={ff.payload['target_ac']})"
        )
        # Specifically: if DEX_MOD=3, AC should drop by 3
        assert ff.payload["target_ac"] == norm.payload["target_ac"] - 3, (
            f"Attack {i}: DEX +3 stripped → target_ac 3 lower for flat-footed"
        )


# ---------------------------------------------------------------------------
# FAGU-006: Monk WIS AC bonus included in target_ac for all iterative attacks
# ---------------------------------------------------------------------------

def test_fagu006_monk_wis_ac_bonus_applies_all_attacks():
    """FAGU-006: Full attack, target has Monk WIS AC bonus → AC includes WIS_MOD vs all attacks.

    Before FAGU: Monk WIS AC was missing from resolve_single_attack_with_critical().
    After FAGU: resolve_attack() adds _monk_wis_ac when target is unarmored monk (PHB p.41).
    PHB p.41: A monk adds WIS modifier as a bonus to AC when unarmored.
    """
    # Non-monk target: AC=12
    t_nonmonk = _target(ac=12)

    # Monk target: AC=12, monk L1, unarmored (armor_ac_bonus=0), monk_wis_ac_bonus=3
    t_monk = _target(
        ac=12,
        class_levels={"monk": 1},
        armor_ac_bonus=0,
        monk_wis_ac_bonus=3,
    )

    attacker = _attacker()
    ws_nonmonk = _ws(attacker, t_nonmonk)
    ws_monk = _ws(attacker, t_monk)

    seed = 11
    events_nm = resolve_full_attack(_fa_intent(), ws_nonmonk, RNGManager(master_seed=seed), 0, 1.0)
    events_mk = resolve_full_attack(_fa_intent(), ws_monk, RNGManager(master_seed=seed), 0, 1.0)

    atks_nm = [e for e in events_nm if e.event_type == "attack_roll"]
    atks_mk = [e for e in events_mk if e.event_type == "attack_roll"]

    assert len(atks_nm) > 0, "Need attack_roll events"
    assert len(atks_nm) == len(atks_mk), "Same attack count (same seed)"

    # Monk target should have AC = 12 + 3 = 15 vs all attacks
    for i, (nm, mk) in enumerate(zip(atks_nm, atks_mk)):
        assert mk.payload["target_ac"] == nm.payload["target_ac"] + 3, (
            f"Attack {i}: Monk WIS AC +3 must appear in target_ac for every iterative "
            f"(nonmonk={nm.payload['target_ac']}, monk={mk.payload['target_ac']})"
        )


# ---------------------------------------------------------------------------
# FAGU-007: Negative Level — -1/level attack penalty per iterative
# ---------------------------------------------------------------------------

def test_fagu007_negative_levels_attack_penalty_per_iterative():
    """FAGU-007: Full attack, attacker has Negative Level → -1 attack per level, per iterative.

    Before FAGU: Negative Levels -1/level was missing from resolve_single_attack_with_critical().
    After FAGU: resolve_attack() subtracts EF.NEGATIVE_LEVELS from attack_bonus_with_conditions.
    PHB p.215: Each negative level imposes a -1 penalty on attack rolls.
    """
    a_clean = _attacker(negative_levels=0)
    a_neglvl = _attacker(negative_levels=2)  # -2 to all attacks
    t = _target(ac=10, hp=200)

    ws_clean = _ws(a_clean, t)
    ws_nl = _ws(a_neglvl, t)

    seed = 13
    events_clean = resolve_full_attack(_fa_intent(), ws_clean, RNGManager(master_seed=seed), 0, 1.0)
    events_nl = resolve_full_attack(_fa_intent(), ws_nl, RNGManager(master_seed=seed), 0, 1.0)

    atks_clean = [e for e in events_clean if e.event_type == "attack_roll"]
    atks_nl = [e for e in events_nl if e.event_type == "attack_roll"]

    assert len(atks_clean) > 0
    assert len(atks_clean) == len(atks_nl), "Same seed → same attack count"

    for i, (clean, nl) in enumerate(zip(atks_clean, atks_nl)):
        d20_clean = clean.payload["d20_result"]
        d20_nl = nl.payload["d20_result"]
        assert d20_clean == d20_nl, f"Attack {i}: same seed → same d20"
        assert nl.payload["total"] == clean.payload["total"] - 2, (
            f"Attack {i}: 2 negative levels → -2 to attack total "
            f"(clean={clean.payload['total']}, nl={nl.payload['total']})"
        )


# ---------------------------------------------------------------------------
# FAGU-008: Massive Damage Fort save triggered per qualifying hit in full attack
# ---------------------------------------------------------------------------

def test_fagu008_massive_damage_fort_save_per_hit():
    """FAGU-008: Full attack with 50+ damage hit → massive_damage_check triggered per hit.

    Before FAGU: Massive Damage Fort save was missing from full-attack path.
    After FAGU: resolve_attack() fires massive_damage_check when final_damage >= 50 (per-hit).
    PHB p.145: If a single blow deals 50 or more damage, the target must make a DC 15 Fort save.

    Using weapon with damage_bonus=49, damage_dice=1d4 → min 50 damage per hit.
    """
    weapon_50 = _HEAVY_WEAPON_50
    attacker = _attacker()
    t = _target(ac=10, hp=500, con_mod=2)  # Very high HP; Fort save set in _target

    ws = _ws(attacker, t)

    events = resolve_full_attack(
        _fa_intent(weapon=weapon_50),
        ws,
        RNGManager(master_seed=42),
        0, 1.0,
    )

    dmg_events = [e for e in events if e.event_type == "damage_roll"]
    md_events = [e for e in events if e.event_type == "massive_damage_check"]

    assert len(dmg_events) > 0, "Weapon with damage_bonus=49 should hit and deal damage"
    # Every hit (damage_roll) should trigger massive_damage_check since min damage = 50
    assert len(md_events) == len(dmg_events), (
        f"Expected one massive_damage_check per hit ({len(dmg_events)} hits), "
        f"got {len(md_events)} massive_damage_check events"
    )
    for md in md_events:
        assert md.payload["damage"] >= 50
        assert md.payload["dc"] == 15


# ---------------------------------------------------------------------------
# FAGU-009: WFC-003 regression — weapon_focus still grants +1 per hit (no double-count)
# ---------------------------------------------------------------------------

def test_fagu009_weapon_focus_no_double_count():
    """FAGU-009: WFC-003 regression — Weapon Focus grants exactly +1 per hit after FAGU.

    The _wf_bonus block was removed from full_attack_resolver.py as part of FAGU cleanup
    (it would double-count since resolve_attack() also applies WF via AR's _wf_bonus).
    Verify: attack total differs by exactly +1 (WF) not +2 (double-count).
    PHB p.102: Weapon Focus grants +1 attack bonus.
    """
    a_no_wf = _attacker(feats=[])
    a_wf = _attacker(feats=["weapon_focus_longsword"])  # canonical name key
    t = _target(ac=10, hp=200)

    ws_no = _ws(a_no_wf, t)
    ws_wf = _ws(a_wf, t)

    seed = 17
    events_no = resolve_full_attack(
        _fa_intent(weapon=_LIGHT_WEAPON), ws_no, RNGManager(master_seed=seed), 0, 1.0
    )
    events_wf = resolve_full_attack(
        _fa_intent(weapon=_LIGHT_WEAPON), ws_wf, RNGManager(master_seed=seed), 0, 1.0
    )

    atks_no = [e for e in events_no if e.event_type == "attack_roll"]
    atks_wf = [e for e in events_wf if e.event_type == "attack_roll"]

    assert len(atks_no) > 0, "Need attack events"
    assert len(atks_no) == len(atks_wf), "Same attack count"

    for i, (no, wf) in enumerate(zip(atks_no, atks_wf)):
        d20_no = no.payload["d20_result"]
        d20_wf = wf.payload["d20_result"]
        assert d20_no == d20_wf, f"Attack {i}: same seed → same d20"
        # Exactly +1 — NOT +2 (double-count would give +2)
        assert wf.payload["total"] == no.payload["total"] + 1, (
            f"Attack {i}: WF must give exactly +1, not +2 (double-count check). "
            f"no={no.payload['total']}, wf={wf.payload['total']}"
        )


# ---------------------------------------------------------------------------
# FAGU-010: WSP-003 regression — weapon_specialization still grants +2 damage per hit (no double-count)
# ---------------------------------------------------------------------------

def test_fagu010_weapon_specialization_no_double_count():
    """FAGU-010: WSP-003 regression — Weapon Specialization grants exactly +2 damage per hit.

    The _wsp_bonus block was in resolve_single_attack_with_critical() (now retired via FAGU).
    resolve_attack() handles WSP via its own _wsp_bonus at line 849 of AR.
    Verify: damage total differs by exactly +2 (WSP) not +4 (double-count).
    PHB p.102: Weapon Specialization grants +2 damage bonus.
    """
    # WSP requires WF as prerequisite; WF key uses canonical weapon name (WO-ENGINE-WF-SCHEMA-FIX-001)
    a_no_wsp = _attacker(feats=["weapon_focus_longsword"])
    a_wsp = _attacker(feats=["weapon_focus_longsword", "weapon_specialization_light"])
    t = _target(ac=10, hp=300)

    ws_no = _ws(a_no_wsp, t)
    ws_wsp = _ws(a_wsp, t)

    seed = 19
    events_no = resolve_full_attack(
        _fa_intent(weapon=_LIGHT_WEAPON), ws_no, RNGManager(master_seed=seed), 0, 1.0
    )
    events_wsp = resolve_full_attack(
        _fa_intent(weapon=_LIGHT_WEAPON), ws_wsp, RNGManager(master_seed=seed), 0, 1.0
    )

    dmg_no = [e for e in events_no if e.event_type == "damage_roll"]
    dmg_wsp = [e for e in events_wsp if e.event_type == "damage_roll"]

    assert len(dmg_no) > 0, "Need at least one hit"
    assert len(dmg_no) == len(dmg_wsp), "Same hit count"

    for i, (no, wsp) in enumerate(zip(dmg_no, dmg_wsp)):
        # damage_total for non-critical: base_damage_with_modifiers (= dice + weapon_bonus + modifiers)
        # WSP adds +2 pre-crit (same as weapon enhancement) — so damage_total = no_wsp + 2
        no_val = no.payload["damage_total"]
        wsp_val = wsp.payload["damage_total"]
        if not no.payload.get("critical_multiplier", 1) > 1:
            # Normal hit: exactly +2 difference
            assert wsp_val == no_val + 2, (
                f"Hit {i}: WSP must give exactly +2 damage, not +4 (double-count check). "
                f"no={no_val}, wsp={wsp_val}"
            )
        else:
            # Critical hit: WSP +2 is multiplied by crit_mult (pre-crit bonus)
            # Just verify wsp > no by at least 2 (multiplied by crit_mult)
            assert wsp_val >= no_val + 2, (
                f"Hit {i} (critical): WSP +2 pre-crit must appear in damage_total"
            )
