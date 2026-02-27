"""
Gate tests: ENGINE-RACIAL-DODGE-AC-001
WO-ENGINE-RACIAL-DODGE-AC-001

PHB p.15 (Dwarf): +4 dodge bonus to Armor Class against monsters of the giant type.
PHB p.17 (Gnome): +4 dodge bonus to Armor Class against creatures of the giant type.
PHB p.179: Dodge bonuses lost when flat-footed.

Tests RDAC-001 through RDAC-008.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from copy import deepcopy

from aidm.schemas.entity_fields import EF
from aidm.core.state import WorldState
from aidm.core.attack_resolver import resolve_attack
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.core.rng_manager import RNGManager
from aidm.schemas.conditions import create_flat_footed_condition


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_world_state(entities):
    return WorldState(ruleset_version="3.5", entities=entities)


def _make_attacker(entity_id, team="enemy", creature_type="giant", bab=5):
    return {
        EF.ENTITY_ID: entity_id,
        EF.HP_CURRENT: 40,
        EF.HP_MAX: 40,
        EF.AC: 14,
        EF.TEAM: team,
        EF.SAVE_FORT: 4,
        EF.SAVE_REF: 2,
        EF.SAVE_WILL: 2,
        EF.POSITION: {"x": 0, "y": 0},
        EF.CONDITIONS: {},
        EF.CREATURE_TYPE: creature_type,
        EF.STR_MOD: 4,
        EF.DEX_MOD: 0,
        EF.BAB: bab,
        EF.FEATS: [],
    }


def _make_defender(entity_id, team="party", race="dwarf", dodge_bonus_vs_giants=0,
                   ac=14, flat_footed=False, dex_mod=1):
    cond = {}
    if flat_footed:
        ff_cond = create_flat_footed_condition(source="test", applied_at_event_id=1)
        cond["flat_footed"] = ff_cond.to_dict()
    e = {
        EF.ENTITY_ID: entity_id,
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 30,
        EF.AC: ac,
        EF.TEAM: team,
        EF.SAVE_FORT: 3,
        EF.SAVE_REF: 2,
        EF.SAVE_WILL: 2,
        EF.POSITION: {"x": 1, "y": 0},
        EF.CONDITIONS: cond,
        EF.RACE: race,
        EF.CREATURE_TYPE: "humanoid",
        EF.STR_MOD: 0,
        EF.DEX_MOD: dex_mod,
        EF.BAB: 2,
        EF.FEATS: [],
    }
    if dodge_bonus_vs_giants > 0:
        e[EF.DODGE_BONUS_VS_GIANTS] = dodge_bonus_vs_giants
    return e


_MELEE_WEAPON = Weapon(
    damage_dice="2d6",
    damage_bonus=0,
    damage_type="bludgeoning",
    weapon_type="two-handed",
)


def _make_intent(attacker_id, target_id, attack_bonus=5):
    return AttackIntent(
        attacker_id=attacker_id,
        target_id=target_id,
        weapon=_MELEE_WEAPON,
        attack_bonus=attack_bonus,
    )


def _get_target_ac_from_events(events):
    """Extract target_ac from attack_roll event."""
    for e in events:
        if e.event_type == "attack_roll":
            return e.payload.get("target_ac", None)
    return None


# ---------------------------------------------------------------------------
# RDAC-001: Dwarf defender vs. giant attacker: AC +4 vs. dwarf vs. non-giant
# ---------------------------------------------------------------------------

def test_rdac_001_dwarf_vs_giant():
    """RDAC-001: Dwarf defender gets +4 AC when attacker is giant vs. non-giant same attack."""
    giant = _make_attacker("giant_atk", creature_type="giant")
    human_atk = _make_attacker("human_atk", creature_type="humanoid")
    dwarf = _make_defender("dwarf_def", dodge_bonus_vs_giants=4, dex_mod=1)

    ws_giant = _make_world_state({"giant_atk": giant, "dwarf_def": deepcopy(dwarf)})
    ws_human = _make_world_state({"human_atk": human_atk, "dwarf_def": deepcopy(dwarf)})

    events_g = resolve_attack(_make_intent("giant_atk", "dwarf_def"), ws_giant,
                               RNGManager(master_seed=5), next_event_id=1, timestamp=0.0)
    events_h = resolve_attack(_make_intent("human_atk", "dwarf_def"), ws_human,
                               RNGManager(master_seed=5), next_event_id=1, timestamp=0.0)

    ac_vs_giant = _get_target_ac_from_events(events_g)
    ac_vs_human = _get_target_ac_from_events(events_h)

    assert ac_vs_giant == ac_vs_human + 4, (
        f"Dwarf AC vs giant should be +4 vs non-giant: giant={ac_vs_giant}, non-giant={ac_vs_human}"
    )


# ---------------------------------------------------------------------------
# RDAC-002: Gnome defender vs. giant attacker: AC +4
# ---------------------------------------------------------------------------

def test_rdac_002_gnome_vs_giant():
    """RDAC-002: Gnome defender gets +4 AC vs. giant attacker."""
    giant = _make_attacker("giant_atk", creature_type="giant")
    human_atk = _make_attacker("human_atk", creature_type="humanoid")
    gnome = _make_defender("gnome_def", race="gnome", dodge_bonus_vs_giants=4, dex_mod=1)

    ws_giant = _make_world_state({"giant_atk": giant, "gnome_def": deepcopy(gnome)})
    ws_human = _make_world_state({"human_atk": human_atk, "gnome_def": deepcopy(gnome)})

    events_g = resolve_attack(_make_intent("giant_atk", "gnome_def"), ws_giant,
                               RNGManager(master_seed=5), next_event_id=1, timestamp=0.0)
    events_h = resolve_attack(_make_intent("human_atk", "gnome_def"), ws_human,
                               RNGManager(master_seed=5), next_event_id=1, timestamp=0.0)

    ac_vs_giant = _get_target_ac_from_events(events_g)
    ac_vs_human = _get_target_ac_from_events(events_h)

    assert ac_vs_giant == ac_vs_human + 4, (
        f"Gnome AC vs giant should be +4 vs non-giant: giant={ac_vs_giant}, non-giant={ac_vs_human}"
    )


# ---------------------------------------------------------------------------
# RDAC-003: Dwarf vs. non-giant (orc, goblin, human): NO dodge bonus
# ---------------------------------------------------------------------------

def test_rdac_003_dwarf_vs_non_giant_no_bonus():
    """RDAC-003: Dwarf gets no racial dodge bonus vs. non-giant attacker."""
    orc_atk = _make_attacker("orc_atk", creature_type="humanoid")
    human_atk = _make_attacker("human_atk", creature_type="humanoid")
    dwarf = _make_defender("dwarf_def", dodge_bonus_vs_giants=4, dex_mod=1)

    ws_orc = _make_world_state({"orc_atk": orc_atk, "dwarf_def": deepcopy(dwarf)})
    ws_human = _make_world_state({"human_atk": human_atk, "dwarf_def": deepcopy(dwarf)})

    events_o = resolve_attack(_make_intent("orc_atk", "dwarf_def"), ws_orc,
                               RNGManager(master_seed=5), next_event_id=1, timestamp=0.0)
    events_h = resolve_attack(_make_intent("human_atk", "dwarf_def"), ws_human,
                               RNGManager(master_seed=5), next_event_id=1, timestamp=0.0)

    ac_vs_orc = _get_target_ac_from_events(events_o)
    ac_vs_human = _get_target_ac_from_events(events_h)

    assert ac_vs_orc == ac_vs_human, (
        f"Dwarf AC vs orc should equal vs human (no racial dodge): orc={ac_vs_orc}, human={ac_vs_human}"
    )


# ---------------------------------------------------------------------------
# RDAC-004: Non-dwarf/gnome vs. giant: NO dodge bonus
# ---------------------------------------------------------------------------

def test_rdac_004_human_vs_giant_no_bonus():
    """RDAC-004: Human defender gets no racial dodge AC bonus vs. giant."""
    giant = _make_attacker("giant_atk", creature_type="giant")
    human_def = _make_defender("human_def", race="human", dodge_bonus_vs_giants=0, dex_mod=1)

    ws = _make_world_state({"giant_atk": giant, "human_def": human_def})
    human_atk2 = _make_attacker("human_atk", creature_type="humanoid")
    ws2 = _make_world_state({"human_atk": human_atk2, "human_def": deepcopy(human_def)})

    events_g = resolve_attack(_make_intent("giant_atk", "human_def"), ws,
                               RNGManager(master_seed=5), next_event_id=1, timestamp=0.0)
    events_h = resolve_attack(_make_intent("human_atk", "human_def"), ws2,
                               RNGManager(master_seed=5), next_event_id=1, timestamp=0.0)

    ac_vs_giant = _get_target_ac_from_events(events_g)
    ac_vs_human = _get_target_ac_from_events(events_h)

    assert ac_vs_giant == ac_vs_human, (
        f"Human AC vs giant should equal vs human (no racial dodge): giant={ac_vs_giant}, non-giant={ac_vs_human}"
    )


# ---------------------------------------------------------------------------
# RDAC-005: Dwarf flat-footed vs. giant: NO dodge bonus
# ---------------------------------------------------------------------------

def test_rdac_005_dwarf_flat_footed_no_dodge():
    """RDAC-005: Flat-footed dwarf loses racial dodge bonus vs. giant."""
    giant = _make_attacker("giant_atk", creature_type="giant")
    dwarf_ff = _make_defender("dwarf_ff", dodge_bonus_vs_giants=4, flat_footed=True, dex_mod=1)
    dwarf_normal = _make_defender("dwarf_norm", dodge_bonus_vs_giants=4, flat_footed=False, dex_mod=0)

    ws_ff = _make_world_state({"giant_atk": giant, "dwarf_ff": dwarf_ff})
    ws_norm = _make_world_state({"giant_atk": deepcopy(giant), "dwarf_norm": dwarf_normal})

    events_ff = resolve_attack(_make_intent("giant_atk", "dwarf_ff"), ws_ff,
                                RNGManager(master_seed=5), next_event_id=1, timestamp=0.0)
    events_norm = resolve_attack(_make_intent("giant_atk", "dwarf_norm"), ws_norm,
                                  RNGManager(master_seed=5), next_event_id=1, timestamp=0.0)

    ac_ff = _get_target_ac_from_events(events_ff)
    ac_norm = _get_target_ac_from_events(events_norm)

    # Flat-footed: -dex_mod penalty + no dodge. Normal: +4 dodge.
    # dwarf_ff: ac=14, dex_mod=1 → loses dex → ac_ff = 14 - 1 = 13
    # dwarf_norm: ac=14, dex_mod=0, not ff → +4 dodge → ac_norm = 18
    # Key: ac_ff should be < ac_norm (no dodge bonus when flat-footed)
    assert ac_ff < ac_norm, (
        f"Flat-footed dwarf AC should be lower than non-flat-footed (dodge lost): ff={ac_ff}, norm={ac_norm}"
    )
    # Also confirm flat-footed dwarf does NOT get the +4 racial dodge bonus
    # (ac_ff should equal base_ac - dex_penalty = 14 - 1 = 13)
    assert ac_ff == 13, f"Flat-footed dwarf AC vs giant should be 13 (no dodge), got {ac_ff}"


# ---------------------------------------------------------------------------
# RDAC-006: Dwarf not flat-footed vs. giant: +4 AC bonus applies
# ---------------------------------------------------------------------------

def test_rdac_006_dwarf_not_flat_footed_gets_dodge():
    """RDAC-006: Non-flat-footed dwarf gets +4 racial dodge AC vs. giant."""
    giant = _make_attacker("giant_atk", creature_type="giant")
    human_atk = _make_attacker("human_atk", creature_type="humanoid")
    dwarf = _make_defender("dwarf_def", dodge_bonus_vs_giants=4, flat_footed=False, dex_mod=0)

    ws_giant = _make_world_state({"giant_atk": giant, "dwarf_def": deepcopy(dwarf)})
    ws_human = _make_world_state({"human_atk": human_atk, "dwarf_def": deepcopy(dwarf)})

    events_g = resolve_attack(_make_intent("giant_atk", "dwarf_def"), ws_giant,
                               RNGManager(master_seed=5), next_event_id=1, timestamp=0.0)
    events_h = resolve_attack(_make_intent("human_atk", "dwarf_def"), ws_human,
                               RNGManager(master_seed=5), next_event_id=1, timestamp=0.0)

    ac_vs_giant = _get_target_ac_from_events(events_g)
    ac_vs_human = _get_target_ac_from_events(events_h)

    assert ac_vs_giant == ac_vs_human + 4, (
        f"Non-flat-footed dwarf AC vs giant should be +4: giant={ac_vs_giant}, non-giant={ac_vs_human}"
    )


# ---------------------------------------------------------------------------
# RDAC-007: Dodge bonus stacks with other AC bonuses
# ---------------------------------------------------------------------------

def test_rdac_007_dodge_stacks_with_other_bonuses():
    """RDAC-007: Racial dodge vs giants stacks with natural armor, shield, etc."""
    giant = _make_attacker("giant_atk", creature_type="giant")
    # Dwarf with extra AC from base (simulating natural armor)
    dwarf_high_ac = _make_defender("dwarf_high", dodge_bonus_vs_giants=4, ac=16, dex_mod=0)

    ws = _make_world_state({"giant_atk": giant, "dwarf_high": dwarf_high_ac})
    events = resolve_attack(_make_intent("giant_atk", "dwarf_high"), ws,
                             RNGManager(master_seed=5), next_event_id=1, timestamp=0.0)

    ac = _get_target_ac_from_events(events)
    # ac=16 base + 4 dodge = 20
    assert ac == 20, f"Dwarf AC 16 + 4 dodge vs giant should be 20, got {ac}"


# ---------------------------------------------------------------------------
# RDAC-008: Giant creature type correctly identified
# ---------------------------------------------------------------------------

def test_rdac_008_giant_creature_type_identified():
    """RDAC-008: EF.CREATURE_TYPE == 'giant' triggers dodge bonus (not just any non-humanoid)."""
    dragon_atk = _make_attacker("dragon_atk", creature_type="dragon")
    giant_atk = _make_attacker("giant_atk", creature_type="giant")
    dwarf = _make_defender("dwarf_def", dodge_bonus_vs_giants=4, dex_mod=0)

    ws_dragon = _make_world_state({"dragon_atk": dragon_atk, "dwarf_def": deepcopy(dwarf)})
    ws_giant = _make_world_state({"giant_atk": giant_atk, "dwarf_def": deepcopy(dwarf)})

    events_dragon = resolve_attack(_make_intent("dragon_atk", "dwarf_def"), ws_dragon,
                                    RNGManager(master_seed=5), next_event_id=1, timestamp=0.0)
    events_giant = resolve_attack(_make_intent("giant_atk", "dwarf_def"), ws_giant,
                                   RNGManager(master_seed=5), next_event_id=1, timestamp=0.0)

    ac_vs_dragon = _get_target_ac_from_events(events_dragon)
    ac_vs_giant = _get_target_ac_from_events(events_giant)

    # Dragon is not giant type — no dodge bonus
    # Giant is giant type — +4 dodge
    assert ac_vs_giant == ac_vs_dragon + 4, (
        f"Only 'giant' type triggers dodge bonus: giant={ac_vs_giant}, dragon={ac_vs_dragon}"
    )
