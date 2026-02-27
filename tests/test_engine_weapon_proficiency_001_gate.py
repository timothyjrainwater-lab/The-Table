"""Gate tests: WO-ENGINE-WEAPON-PROFICIENCY-001 — Non-proficiency attack penalty.

PHB p.113: A character who uses a weapon with which he or she is not proficient
takes a -4 penalty on attack rolls.

Proficiency rules:
- Simple: all classes proficient
- Martial: barbarian, fighter, paladin, ranger + martial_weapon_proficiency feat
- Exotic: requires exotic_weapon_proficiency* feat
- Natural: always proficient (weapon_type='natural')
- proficiency_category=None: assume proficient (backwards-compatible default)

FINDING: Weapon.proficiency_category field added to Weapon dataclass (default None).
Existing Weapon instances without this field are unaffected (None → proficient).
Gate label: ENGINE-WEAPON-PROF (WP2)
Tests: WP2-001 – WP2-008
"""

import pytest
from aidm.core.attack_resolver import resolve_attack, _is_weapon_proficient
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.entity_fields import EF
from aidm.core.state import WorldState


class _FixedRNG:
    """Fixed RNG that returns 15 for all rolls."""
    class _Stream:
        def randint(self, lo, hi): return 15
    def stream(self, name): return _FixedRNG._Stream()


def _weapon(prof_cat=None, weapon_type="one-handed"):
    return Weapon(
        damage_dice="1d8",
        damage_bonus=0,
        damage_type="slashing",
        weapon_type=weapon_type,
        proficiency_category=prof_cat,
    )


def _entity(class_levels, feats=None, entity_id="att", attack_bonus=5):
    return {
        EF.ENTITY_ID: entity_id, EF.TEAM: "enemy",
        EF.STR_MOD: 2, EF.DEX_MOD: 0, EF.WIS_MOD: 0,
        EF.FEATS: feats or [],
        EF.ATTACK_BONUS: attack_bonus,
        EF.HP_CURRENT: 30, EF.HP_MAX: 30, EF.AC: 14, EF.DEFEATED: False,
        EF.NEGATIVE_LEVELS: 0, EF.CONDITIONS: [],
        EF.INSPIRE_COURAGE_ACTIVE: False, EF.INSPIRE_COURAGE_BONUS: 0,
        EF.FAVORED_ENEMIES: [], EF.TEMPORARY_MODIFIERS: {},
        EF.POSITION: {"x": 0, "y": 0},
        EF.COMBAT_EXPERTISE_BONUS: 0,
        EF.CLASS_LEVELS: class_levels,
        EF.MONK_WIS_AC_BONUS: 0,
        EF.ARMOR_AC_BONUS: 0,
        EF.ARMOR_TYPE: "none",
        EF.ENCUMBRANCE_LOAD: "light",
    }


def _target():
    return {
        EF.ENTITY_ID: "tgt", EF.TEAM: "player",
        EF.HP_CURRENT: 50, EF.HP_MAX: 50, EF.AC: 10, EF.DEFEATED: False,
        EF.NEGATIVE_LEVELS: 0, EF.CONDITIONS: [],
        EF.POSITION: {"x": 1, "y": 0},
        EF.STR_MOD: 0, EF.DEX_MOD: 0, EF.WIS_MOD: 0,
        EF.FEATS: [], EF.TEMPORARY_MODIFIERS: {},
        EF.COMBAT_EXPERTISE_BONUS: 0,
        EF.CLASS_LEVELS: {"fighter": 1},
        EF.MONK_WIS_AC_BONUS: 0,
        EF.ARMOR_AC_BONUS: 0,
        EF.ARMOR_TYPE: "none",
        EF.ENCUMBRANCE_LOAD: "light",
    }


def _get_attack_bonus_used(attacker, weapon):
    """Run resolve_attack and return the total roll shown in attack_roll event."""
    ws = WorldState(
        ruleset_version="3.5",
        entities={"att": attacker, "tgt": _target()},
        active_combat={
            "initiative_order": ["att", "tgt"],
            "aoo_used_this_round": [], "aoo_count_this_round": {},
        },
    )
    intent = AttackIntent(
        attacker_id="att", target_id="tgt",
        attack_bonus=attacker[EF.ATTACK_BONUS],
        weapon=weapon,
    )
    events = resolve_attack(intent=intent, world_state=ws, rng=_FixedRNG(),
                            next_event_id=0, timestamp=0.0)
    for e in events:
        if e.event_type == "attack_roll":
            # total = d20(15) + attack_bonus_with_conditions
            # So attack_bonus_with_conditions = total - 15
            return e.payload["total"] - 15
    raise AssertionError("No attack_roll event found")


# ---------------------------------------------------------------------------
# WP2-001: Fighter (martial-proficient class) with longsword (martial) — no penalty
# ---------------------------------------------------------------------------
def test_wp2001_fighter_martial_weapon_proficient():
    fighter = _entity({"fighter": 1}, attack_bonus=5)
    longsword = _weapon(prof_cat="martial")
    effective_bonus = _get_attack_bonus_used(fighter, longsword)
    assert effective_bonus == 5, f"Fighter+martial: expected bonus 5 (no penalty), got {effective_bonus}"


# ---------------------------------------------------------------------------
# WP2-002: Wizard (non-martial class) with longsword (martial) — -4 penalty
# ---------------------------------------------------------------------------
def test_wp2002_wizard_martial_weapon_non_proficient():
    wizard = _entity({"wizard": 1}, attack_bonus=5)
    longsword = _weapon(prof_cat="martial")
    effective_bonus = _get_attack_bonus_used(wizard, longsword)
    assert effective_bonus == 1, \
        f"Wizard+martial: expected bonus 1 (5 -4 non-prof), got {effective_bonus}"


# ---------------------------------------------------------------------------
# WP2-003: Fighter WITH exotic weapon proficiency feat — no penalty
# ---------------------------------------------------------------------------
def test_wp2003_fighter_exotic_with_proficiency_feat():
    fighter = _entity({"fighter": 1},
                      feats=["exotic_weapon_proficiency_bastard_sword"],
                      attack_bonus=5)
    bastard_sword = _weapon(prof_cat="exotic")
    effective_bonus = _get_attack_bonus_used(fighter, bastard_sword)
    assert effective_bonus == 5, \
        f"Fighter+exotic feat: expected bonus 5 (no penalty), got {effective_bonus}"


# ---------------------------------------------------------------------------
# WP2-004: Fighter WITHOUT exotic weapon proficiency feat — -4 penalty
# ---------------------------------------------------------------------------
def test_wp2004_fighter_exotic_without_feat():
    fighter = _entity({"fighter": 1}, feats=[], attack_bonus=5)
    bastard_sword = _weapon(prof_cat="exotic")
    effective_bonus = _get_attack_bonus_used(fighter, bastard_sword)
    assert effective_bonus == 1, \
        f"Fighter+exotic no feat: expected bonus 1 (5 -4), got {effective_bonus}"


# ---------------------------------------------------------------------------
# WP2-005: Any class with simple weapon (dagger) — always proficient
# ---------------------------------------------------------------------------
def test_wp2005_wizard_simple_weapon_proficient():
    wizard = _entity({"wizard": 1}, attack_bonus=5)
    dagger = _weapon(prof_cat="simple", weapon_type="light")
    effective_bonus = _get_attack_bonus_used(wizard, dagger)
    assert effective_bonus == 5, \
        f"Wizard+simple: expected bonus 5 (always proficient), got {effective_bonus}"


# ---------------------------------------------------------------------------
# WP2-006: Barbarian with martial weapon — proficient (in martial class list)
# ---------------------------------------------------------------------------
def test_wp2006_barbarian_martial_weapon_proficient():
    barb = _entity({"barbarian": 1}, attack_bonus=5)
    greataxe = _weapon(prof_cat="martial", weapon_type="two-handed")
    effective_bonus = _get_attack_bonus_used(barb, greataxe)
    assert effective_bonus == 5, \
        f"Barbarian+martial: expected bonus 5 (no penalty), got {effective_bonus}"


# ---------------------------------------------------------------------------
# WP2-007: Natural attack — always proficient (weapon_type='natural')
# ---------------------------------------------------------------------------
def test_wp2007_natural_attack_always_proficient():
    # Even with exotic proficiency_category, natural weapon_type overrides
    beast = _entity({"monster": 1}, attack_bonus=3)
    claw = _weapon(prof_cat="exotic", weapon_type="natural")
    effective_bonus = _get_attack_bonus_used(beast, claw)
    assert effective_bonus == 3, \
        f"Natural attack: expected bonus 3 (always proficient), got {effective_bonus}"


# ---------------------------------------------------------------------------
# WP2-008: Non-proficiency stacks with existing negative modifiers
# ---------------------------------------------------------------------------
def test_wp2008_nonprof_penalty_applies_additively():
    # attack_bonus=3, martial weapon, wizard → total effective = 3 - 4 = -1
    wizard = _entity({"wizard": 1}, attack_bonus=3)
    longsword = _weapon(prof_cat="martial")
    effective_bonus = _get_attack_bonus_used(wizard, longsword)
    assert effective_bonus == -1, \
        f"Wizard+martial+low BAB: expected -1 (3 -4), got {effective_bonus}"


# ---------------------------------------------------------------------------
# WP2-UNIT: _is_weapon_proficient helper unit tests
# ---------------------------------------------------------------------------
def test_wp2_unit_none_proficiency_category_is_proficient():
    """proficiency_category=None → assume proficient (backwards compat)."""
    attacker = _entity({"wizard": 1})
    w = _weapon(prof_cat=None)
    assert _is_weapon_proficient(attacker, w) is True


def test_wp2_unit_martial_weapon_proficiency_feat():
    """martial_weapon_proficiency feat grants all martial proficiency."""
    attacker = _entity({"rogue": 1}, feats=["martial_weapon_proficiency"])
    w = _weapon(prof_cat="martial")
    assert _is_weapon_proficient(attacker, w) is True


def test_wp2_unit_rogue_not_martial_proficient_by_default():
    attacker = _entity({"rogue": 1})
    w = _weapon(prof_cat="martial")
    assert _is_weapon_proficient(attacker, w) is False
