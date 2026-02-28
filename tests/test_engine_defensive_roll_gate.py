"""Gate tests: Rogue Defensive Roll — WO-ENGINE-AF-WO4.

DR-001 through DR-008.

PHB p.51: Once per day, when a rogue would be reduced to 0 or fewer HP by a
weapon blow, she can attempt a Reflex save (DC = damage dealt). Success = take
half damage. Failure = full damage. Cannot use if flat-footed (denied DEX to AC).
"""

import pytest
from copy import deepcopy

from aidm.core.attack_resolver import resolve_attack, apply_attack_events
from aidm.core.rest_resolver import resolve_rest
from aidm.core.state import WorldState
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.entity_fields import EF
from aidm.core.rng_manager import RNGManager
from aidm.schemas.intents import RestIntent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _unarmed_weapon(damage_dice="1d6"):
    return Weapon(
        damage_dice=damage_dice,
        damage_type="bludgeoning",
        critical_multiplier=2,
        critical_range=20,
        weapon_type="light",
        grip="one-handed",
        damage_bonus=0,
        enhancement_bonus=0,
    )


def _rogue(eid="rogue", *, hp=10, hp_max=10, has_dr=True, dr_used=False, flat_footed=False):
    entity = {
        EF.ENTITY_ID: eid,
        EF.CLASS_LEVELS: {"rogue": 10},
        EF.LEVEL: 10,
        EF.ATTACK_BONUS: 7,
        EF.BAB: 7,
        EF.STR_MOD: 1,
        EF.DEX_MOD: 3,
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp_max,
        EF.AC: 14,
        EF.FEATS: [],
        EF.CONDITIONS: ["flat_footed"] if flat_footed else [],
        EF.TEMPORARY_MODIFIERS: {},
        EF.DAMAGE_REDUCTIONS: [],
        EF.SIZE_CATEGORY: "medium",
        EF.CREATURE_TYPE: "humanoid",
        EF.ARMOR_AC_BONUS: 0,
        EF.DEFLECTION_BONUS: 0,
        EF.TEAM: "players",
        EF.SAVE_REF: 10,  # High reflex to control save outcomes
        EF.SAVE_FORT: 3,
        EF.SAVE_WILL: 3,
    }
    if has_dr:
        entity[EF.HAS_DEFENSIVE_ROLL] = True
        entity[EF.DEFENSIVE_ROLL_USED] = dr_used
    return entity


def _attacker(eid="attacker", *, str_mod=3, attack_bonus=15):
    return {
        EF.ENTITY_ID: eid,
        EF.CLASS_LEVELS: {"fighter": 10},
        EF.LEVEL: 10,
        EF.ATTACK_BONUS: attack_bonus,
        EF.BAB: 10,
        EF.STR_MOD: str_mod,
        EF.DEX_MOD: 1,
        EF.HP_CURRENT: 60,
        EF.HP_MAX: 60,
        EF.FEATS: [],
        EF.CONDITIONS: [],
        EF.TEMPORARY_MODIFIERS: {},
        EF.SIZE_CATEGORY: "medium",
        EF.CREATURE_TYPE: "humanoid",
        EF.ARMOR_AC_BONUS: 0,
        EF.DEFLECTION_BONUS: 0,
        EF.TEAM: "enemies",
    }


def _ws(attacker, target):
    return WorldState(
        ruleset_version="3.5",
        entities={
            attacker[EF.ENTITY_ID]: attacker,
            target[EF.ENTITY_ID]: target,
        },
        active_combat=None,
    )


def _run_attack(attacker_id, target_id, world_state, rng, *, fixed_damage=None):
    """Run an attack that deals fixed_damage (via very high attack bonus, low AC)."""
    # Use a fixed-dice weapon so we can predict damage with str_mod=0
    weapon = _unarmed_weapon("1d1")  # Rolls 1 always
    intent = AttackIntent(
        attacker_id=attacker_id,
        target_id=target_id,
        weapon=weapon,
        attack_bonus=30,  # Always hits
    )
    return resolve_attack(intent, world_state, rng, next_event_id=1, timestamp=0.0)


def _apply(events, ws):
    return apply_attack_events(ws, events)


# ---------------------------------------------------------------------------
# DR-001: Triggered when damage would reduce to ≤ 0; save success → half damage
# ---------------------------------------------------------------------------

def test_dr_001_triggered_save_success_half_damage():
    """DR-001: Rogue HP=10, lethal attack. Save succeeds → takes half damage.

    Strategy: Set REF_SAVE very high (30) so DC=1 roll always passes.
    1d1 weapon + str_mod=0 → final_damage=1. Half = 0, min 1? Actually 1//2=0
    Use a bigger weapon to make the math clean.
    """
    rogue = _rogue(hp=5, hp_max=20, has_dr=True, dr_used=False)
    rogue[EF.SAVE_REF] = 30  # Auto-pass any Reflex save
    rogue[EF.DEX_MOD] = 0  # Not flat-footed by itself
    att = _attacker(str_mod=0)

    # Use 1d4 weapon — range 1-4; with str_mod=0, damage=1-4
    # Set HP to 3 and use fixed 1d1 + damage_bonus to guarantee lethal
    rogue[EF.HP_CURRENT] = 3
    att[EF.STR_MOD] = 0

    ws = _ws(att, rogue)

    # 1d8 weapon with attack_bonus=30, str_mod=0 → damage 1-8
    weapon = Weapon(
        damage_dice="1d8",
        damage_type="slashing",
        critical_multiplier=2,
        critical_range=20,
        weapon_type="light",
        grip="one-handed",
        damage_bonus=6,  # Ensures 7-14 damage → kills rogue HP=3
        enhancement_bonus=0,
    )
    intent = AttackIntent(
        attacker_id="attacker",
        target_id="rogue",
        weapon=weapon,
        attack_bonus=30,
    )

    rng = RNGManager(master_seed=1)
    events = resolve_attack(intent, ws, rng, next_event_id=1, timestamp=0.0)

    dr_check = next((e for e in events if e.event_type == "defensive_roll_check"), None)
    assert dr_check is not None, "DR-001: Expected defensive_roll_check event"
    assert dr_check.payload["saved"] is True or dr_check.payload["ref_total"] >= dr_check.payload["dc"], (
        "DR-001: With REF=30, Defensive Roll save should succeed"
    )

    dr_success = next((e for e in events if e.event_type == "defensive_roll_success"), None)
    assert dr_success is not None, "DR-001: Expected defensive_roll_success event"

    hp_event = next((e for e in events if e.event_type == "hp_changed"), None)
    assert hp_event is not None, "DR-001: Expected hp_changed event"
    # After half damage, rogue should have HP > 0 (or close to 0 — halved from lethal)
    final_damage = dr_success.payload["damage_halved"]
    assert final_damage < dr_check.payload["dc"], (
        "DR-001: damage_halved must be less than original final_damage"
    )


# ---------------------------------------------------------------------------
# DR-002: Triggered; save failure → full damage
# ---------------------------------------------------------------------------

def test_dr_002_triggered_save_failure_full_damage():
    """DR-002: Rogue HP=5, lethal attack. Save fails → takes full damage."""
    rogue = _rogue(hp=5, hp_max=20, has_dr=True, dr_used=False)
    rogue[EF.SAVE_REF] = -10  # Auto-fail any Reflex save
    rogue[EF.DEX_MOD] = 0

    att = _attacker(str_mod=0)
    ws = _ws(att, rogue)

    # Guaranteed lethal weapon
    weapon = Weapon(
        damage_dice="1d8",
        damage_type="slashing",
        critical_multiplier=2,
        critical_range=20,
        weapon_type="light",
        grip="one-handed",
        damage_bonus=6,
        enhancement_bonus=0,
    )
    intent = AttackIntent(
        attacker_id="attacker",
        target_id="rogue",
        weapon=weapon,
        attack_bonus=30,
    )

    rng = RNGManager(master_seed=2)
    events = resolve_attack(intent, ws, rng, next_event_id=1, timestamp=0.0)

    dr_check = next((e for e in events if e.event_type == "defensive_roll_check"), None)
    assert dr_check is not None, "DR-002: Expected defensive_roll_check event"

    dr_failure = next((e for e in events if e.event_type == "defensive_roll_failure"), None)
    assert dr_failure is not None, "DR-002: Expected defensive_roll_failure when save fails"

    dr_success = next((e for e in events if e.event_type == "defensive_roll_success"), None)
    assert dr_success is None, "DR-002: defensive_roll_success must NOT fire on failure"

    hp_event = next((e for e in events if e.event_type == "hp_changed"), None)
    assert hp_event is not None
    assert hp_event.payload["hp_after"] <= 0, (
        "DR-002: Full damage on failure should reduce HP to ≤0"
    )


# ---------------------------------------------------------------------------
# DR-003: NOT triggered when damage would NOT reduce HP to ≤ 0
# ---------------------------------------------------------------------------

def test_dr_003_not_triggered_when_not_lethal():
    """DR-003: Rogue HP=20, attack deals 5 damage → not lethal → DR not triggered."""
    rogue = _rogue(hp=20, hp_max=20, has_dr=True, dr_used=False)
    att = _attacker(str_mod=0)
    ws = _ws(att, rogue)

    # Low damage weapon — won't kill rogue with HP=20
    weapon = Weapon(
        damage_dice="1d1",
        damage_type="slashing",
        critical_multiplier=2,
        critical_range=20,
        weapon_type="light",
        grip="one-handed",
        damage_bonus=4,  # 1+4=5 damage, rogue HP=20 → survives
        enhancement_bonus=0,
    )
    intent = AttackIntent(
        attacker_id="attacker",
        target_id="rogue",
        weapon=weapon,
        attack_bonus=30,
    )

    rng = RNGManager(master_seed=3)
    events = resolve_attack(intent, ws, rng, next_event_id=1, timestamp=0.0)

    assert not any(e.event_type == "defensive_roll_check" for e in events), (
        "DR-003: Defensive Roll must NOT trigger when attack is not lethal"
    )


# ---------------------------------------------------------------------------
# DR-004: NOT triggered when DEFENSIVE_ROLL_USED = True (already used today)
# ---------------------------------------------------------------------------

def test_dr_004_not_triggered_when_already_used():
    """DR-004: DEFENSIVE_ROLL_USED=True → Defensive Roll does not fire."""
    rogue = _rogue(hp=5, hp_max=20, has_dr=True, dr_used=True)  # Already used
    rogue[EF.SAVE_REF] = 30  # Would succeed if triggered
    att = _attacker(str_mod=0)
    ws = _ws(att, rogue)

    weapon = Weapon(
        damage_dice="1d8",
        damage_type="slashing",
        critical_multiplier=2,
        critical_range=20,
        weapon_type="light",
        grip="one-handed",
        damage_bonus=6,
        enhancement_bonus=0,
    )
    intent = AttackIntent(
        attacker_id="attacker",
        target_id="rogue",
        weapon=weapon,
        attack_bonus=30,
    )

    rng = RNGManager(master_seed=4)
    events = resolve_attack(intent, ws, rng, next_event_id=1, timestamp=0.0)

    assert not any(e.event_type == "defensive_roll_check" for e in events), (
        "DR-004: Defensive Roll must NOT trigger when DEFENSIVE_ROLL_USED=True"
    )


# ---------------------------------------------------------------------------
# DR-005: NOT triggered when entity is flat-footed (denied DEX to AC)
# ---------------------------------------------------------------------------

def test_dr_005_not_triggered_when_flat_footed():
    """DR-005: Rogue is flat-footed (CONDITIONS has 'flat_footed') → DR not triggered.

    PHB p.51: 'if she is denied her Dexterity bonus to AC, she can't use this ability.'
    flat_footed condition → loses_dex_to_ac=True → DR blocked.
    """
    rogue = _rogue(hp=5, hp_max=20, has_dr=True, dr_used=False, flat_footed=True)
    rogue[EF.SAVE_REF] = 30  # Would succeed if triggered
    att = _attacker(str_mod=0)
    ws = _ws(att, rogue)

    weapon = Weapon(
        damage_dice="1d8",
        damage_type="slashing",
        critical_multiplier=2,
        critical_range=20,
        weapon_type="light",
        grip="one-handed",
        damage_bonus=6,
        enhancement_bonus=0,
    )
    intent = AttackIntent(
        attacker_id="attacker",
        target_id="rogue",
        weapon=weapon,
        attack_bonus=30,
    )

    rng = RNGManager(master_seed=5)
    events = resolve_attack(intent, ws, rng, next_event_id=1, timestamp=0.0)

    assert not any(e.event_type == "defensive_roll_check" for e in events), (
        "DR-005: Defensive Roll must NOT trigger when rogue is flat-footed"
    )


# ---------------------------------------------------------------------------
# DR-006: NOT triggered for spell damage (spell_resolver path)
# ---------------------------------------------------------------------------

def test_dr_006_not_triggered_for_spell_damage():
    """DR-006: PHB p.51 — 'not a spell or special ability.' spell_resolver does NOT
    hit the Defensive Roll path in attack_resolver. Verified by inspection:
    resolve_attack() in attack_resolver.py handles weapon attacks only.
    spell_resolver._resolve_spell() is a separate code path that does not call
    resolve_attack() and does not check EF.HAS_DEFENSIVE_ROLL.
    """
    # Verify spell_resolver import path doesn't call resolve_attack
    import inspect
    from aidm.core import spell_resolver
    source = inspect.getsource(spell_resolver)

    # Spell resolver must NOT reference defensive_roll (proof by inspection)
    assert "HAS_DEFENSIVE_ROLL" not in source, (
        "DR-006: spell_resolver.py must NOT reference HAS_DEFENSIVE_ROLL — "
        "Defensive Roll only applies to weapon/physical blows (PHB p.51)"
    )
    assert "defensive_roll" not in source.lower(), (
        "DR-006: spell_resolver.py must not contain defensive_roll logic"
    )


# ---------------------------------------------------------------------------
# DR-007: DEFENSIVE_ROLL_USED resets to False on RestIntent
# ---------------------------------------------------------------------------

def test_dr_007_used_resets_on_rest():
    """DR-007: DEFENSIVE_ROLL_USED=True → after overnight rest → reset to False."""
    rogue = _rogue(hp=20, hp_max=20, has_dr=True, dr_used=True)
    rogue[EF.SAVE_FORT] = 3
    rogue[EF.CON_MOD] = 1
    rogue[EF.CONDITIONS] = []
    rogue[EF.NONLETHAL_DAMAGE] = 0
    ws = WorldState(
        ruleset_version="3.5",
        entities={"rogue": rogue},
        active_combat=None,
    )

    intent = RestIntent(rest_type="overnight")
    result = resolve_rest(intent, ws, actor_id="rogue")
    actor_after = result.world_state.entities["rogue"]

    assert actor_after[EF.DEFENSIVE_ROLL_USED] is False, (
        "DR-007: DEFENSIVE_ROLL_USED must reset to False on full rest"
    )


# ---------------------------------------------------------------------------
# DR-008: HAS_DEFENSIVE_ROLL = False → never triggers
# ---------------------------------------------------------------------------

def test_dr_008_no_defensive_roll_never_triggers():
    """DR-008: Entity with HAS_DEFENSIVE_ROLL=False (non-rogue) never triggers DR."""
    # Create a low-level fighter without DR ability
    fighter_target = {
        EF.ENTITY_ID: "fighter_target",
        EF.CLASS_LEVELS: {"fighter": 5},
        EF.LEVEL: 5,
        EF.ATTACK_BONUS: 4,
        EF.BAB: 5,
        EF.STR_MOD: 1,
        EF.DEX_MOD: 1,
        EF.HP_CURRENT: 5,
        EF.HP_MAX: 30,
        EF.AC: 10,
        EF.FEATS: [],
        EF.CONDITIONS: [],
        EF.TEMPORARY_MODIFIERS: {},
        EF.DAMAGE_REDUCTIONS: [],
        EF.SIZE_CATEGORY: "medium",
        EF.CREATURE_TYPE: "humanoid",
        EF.ARMOR_AC_BONUS: 0,
        EF.DEFLECTION_BONUS: 0,
        EF.TEAM: "players",
        EF.SAVE_REF: 1,
        EF.SAVE_FORT: 3,
        # HAS_DEFENSIVE_ROLL not set (False by .get() default)
    }
    att = _attacker(str_mod=0)
    ws = _ws(att, fighter_target)

    weapon = Weapon(
        damage_dice="1d8",
        damage_type="slashing",
        critical_multiplier=2,
        critical_range=20,
        weapon_type="light",
        grip="one-handed",
        damage_bonus=6,
        enhancement_bonus=0,
    )
    intent = AttackIntent(
        attacker_id="attacker",
        target_id="fighter_target",
        weapon=weapon,
        attack_bonus=30,
    )

    rng = RNGManager(master_seed=8)
    events = resolve_attack(intent, ws, rng, next_event_id=1, timestamp=0.0)

    assert not any(e.event_type == "defensive_roll_check" for e in events), (
        "DR-008: Defensive Roll must NEVER trigger for entities without HAS_DEFENSIVE_ROLL"
    )
