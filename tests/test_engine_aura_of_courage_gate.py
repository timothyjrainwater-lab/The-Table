"""Gate tests: Paladin Aura of Courage — WO-ENGINE-AURA-OF-COURAGE-001.

AOC-001: Paladin L2, ally within 10 ft — ally fear save gets +4
AOC-002: Paladin L2, ally 15 ft away — no bonus (out of range)
AOC-003: Paladin L2 — paladin immune to fear (bonus >= 999)
AOC-004: Paladin L2 unconscious (DYING) — ally gets no bonus (aura down)
AOC-005: Paladin L1 — below threshold, no aura (no FEAR_IMMUNE)
AOC-006: Paladin L2, ally within 10 ft — non-fear save (no AoC bonus)
AOC-007: Two allies within 10 ft — both get +4 morale
AOC-008: Inspire Courage +2 morale + AoC +4 morale → only +4 (morale non-stacking)
"""

import pytest
from aidm.core.save_resolver import get_save_bonus
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.schemas.saves import SaveType


def _make_ws(entities: dict) -> WorldState:
    return WorldState(
        ruleset_version="3.5",
        entities=entities,
        active_combat=None,
    )


def _paladin(level: int, pos: dict, team: str = "party", *, dying: bool = False) -> dict:
    return {
        EF.CLASS_LEVELS: {"paladin": level},
        EF.SAVE_FORT: 3,
        EF.SAVE_REF: 1,
        EF.SAVE_WILL: 2,
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 30,
        EF.DEFEATED: False,
        EF.DYING: dying,
        EF.CONDITIONS: [],
        EF.FEATS: [],
        EF.TEAM: team,
        EF.POSITION: pos,
        EF.FEAR_IMMUNE: level >= 2,
        EF.INSPIRE_COURAGE_ACTIVE: False,
        EF.INSPIRE_COURAGE_BONUS: 0,
        EF.RACIAL_SAVE_BONUS: 0,
        EF.SAVE_BONUS_POISON: 0,
        EF.SAVE_BONUS_SPELLS: 0,
        EF.SAVE_BONUS_ENCHANTMENT: 0,
        EF.CHA_MOD: 0,
        EF.TEMPORARY_MODIFIERS: {},
    }


def _ally(pos: dict, team: str = "party", *, ic_active: bool = False, ic_bonus: int = 0) -> dict:
    return {
        EF.CLASS_LEVELS: {"fighter": 3},
        EF.SAVE_FORT: 2,
        EF.SAVE_REF: 1,
        EF.SAVE_WILL: 1,
        EF.HP_CURRENT: 25,
        EF.HP_MAX: 25,
        EF.DEFEATED: False,
        EF.DYING: False,
        EF.CONDITIONS: [],
        EF.FEATS: [],
        EF.TEAM: team,
        EF.POSITION: pos,
        EF.FEAR_IMMUNE: False,
        EF.INSPIRE_COURAGE_ACTIVE: ic_active,
        EF.INSPIRE_COURAGE_BONUS: ic_bonus,
        EF.RACIAL_SAVE_BONUS: 0,
        EF.SAVE_BONUS_POISON: 0,
        EF.SAVE_BONUS_SPELLS: 0,
        EF.SAVE_BONUS_ENCHANTMENT: 0,
        EF.CHA_MOD: 0,
        EF.TEMPORARY_MODIFIERS: {},
    }


def _fear_bonus(ws: WorldState, actor_id: str) -> int:
    """Get the fear-specific save bonus (Will save with fear descriptor)."""
    return get_save_bonus(ws, actor_id, SaveType.WILL, save_descriptor="fear")


def _nonfear_bonus(ws: WorldState, actor_id: str) -> int:
    """Get a plain Will save bonus (no descriptor)."""
    return get_save_bonus(ws, actor_id, SaveType.WILL)


# ── AOC-001: Ally within 10 ft gets +4 morale ───────────────────────────────

def test_aoc001_ally_within_10ft_gets_plus4():
    """Paladin L2 at (0,0), ally at (2,0) = 10 ft: ally fear save +4."""
    pal = _paladin(2, pos={"x": 0, "y": 0})
    ally = _ally(pos={"x": 2, "y": 0})
    ws = _make_ws({"paladin": pal, "ally": ally})
    # Ally's base Will = 1. With AoC: 1 + 4 = 5.
    bonus = _fear_bonus(ws, "ally")
    base = ally[EF.SAVE_WILL]
    assert bonus == base + 4, f"Expected {base+4} (base+AoC+4), got {bonus}"


# ── AOC-002: Ally 15 ft away — no bonus ──────────────────────────────────────

def test_aoc002_ally_15ft_no_bonus():
    """Paladin L2 at (0,0), ally at (3,0) = 15 ft (>10): no AoC bonus."""
    pal = _paladin(2, pos={"x": 0, "y": 0})
    ally = _ally(pos={"x": 3, "y": 0})  # 3 squares = 15 ft
    ws = _make_ws({"paladin": pal, "ally": ally})
    bonus = _fear_bonus(ws, "ally")
    base = ally[EF.SAVE_WILL]
    assert bonus == base, f"Expected {base} (no AoC, 15 ft), got {bonus}"


# ── AOC-003: Paladin immune to fear (auto-pass sentinel) ──────────────────────

def test_aoc003_paladin_immune_to_fear():
    """Paladin L2 is immune to fear: get_save_bonus returns >= 999 for fear save."""
    pal = _paladin(2, pos={"x": 0, "y": 0})
    ws = _make_ws({"paladin": pal})
    bonus = _fear_bonus(ws, "paladin")
    assert bonus >= 999, f"Expected immunity sentinel (>=999), got {bonus}"


# ── AOC-004: Unconscious paladin — aura drops ─────────────────────────────────

def test_aoc004_unconscious_paladin_no_aura():
    """Paladin L2 with DYING=True: ally within 10 ft gets no AoC bonus."""
    pal = _paladin(2, pos={"x": 0, "y": 0}, dying=True)
    ally = _ally(pos={"x": 1, "y": 0})
    ws = _make_ws({"paladin": pal, "ally": ally})
    bonus = _fear_bonus(ws, "ally")
    base = ally[EF.SAVE_WILL]
    assert bonus == base, f"Expected {base} (dying paladin, no aura), got {bonus}"


# ── AOC-005: Paladin L1 — no aura ─────────────────────────────────────────────

def test_aoc005_paladin_l1_no_aura():
    """Paladin L1 has no Aura of Courage yet: no fear immunity, no ally bonus."""
    pal = _paladin(1, pos={"x": 0, "y": 0})
    # Paladin L1 should NOT have FEAR_IMMUNE
    assert not pal.get(EF.FEAR_IMMUNE, False), "L1 paladin should not be fear immune"
    ally = _ally(pos={"x": 1, "y": 0})
    ws = _make_ws({"paladin": pal, "ally": ally})
    bonus = _fear_bonus(ws, "ally")
    base = ally[EF.SAVE_WILL]
    assert bonus == base, f"Expected {base} (L1 paladin, no aura), got {bonus}"


# ── AOC-006: Non-fear save — no AoC bonus ─────────────────────────────────────

def test_aoc006_nonfear_save_no_aoc():
    """Paladin nearby but non-fear save descriptor: AoC does not apply."""
    pal = _paladin(2, pos={"x": 0, "y": 0})
    ally = _ally(pos={"x": 1, "y": 0})
    ws = _make_ws({"paladin": pal, "ally": ally})
    # Non-fear Will save: AoC does not fire
    bonus = _nonfear_bonus(ws, "ally")
    base = ally[EF.SAVE_WILL]
    assert bonus == base, f"Expected {base} (no descriptor, AoC inactive), got {bonus}"


# ── AOC-007: Two allies within 10 ft — both get +4 ───────────────────────────

def test_aoc007_two_allies_both_get_plus4():
    """Paladin L2 at center; two allies within 10 ft: both get +4 morale."""
    pal = _paladin(2, pos={"x": 0, "y": 0})
    ally1 = _ally(pos={"x": 1, "y": 0})
    ally2 = _ally(pos={"x": 0, "y": 2})
    ws = _make_ws({"paladin": pal, "ally1": ally1, "ally2": ally2})
    for aid in ("ally1", "ally2"):
        bonus = _fear_bonus(ws, aid)
        base = ws.entities[aid][EF.SAVE_WILL]
        assert bonus == base + 4, f"Entity {aid}: expected {base+4}, got {bonus}"


# ── AOC-008: Inspire Courage + AoC — morale doesn't stack ────────────────────

def test_aoc008_inspire_courage_plus_aoc_no_stack():
    """Inspire Courage +2 morale + AoC +4 morale: only +4 applies (higher wins).

    PHB p.136: same-type bonuses from different sources don't stack.
    Ally has Inspire Courage (+2) active. Paladin is nearby (+4 AoC).
    Result: +4 total morale bonus (AoC supersedes IC for fear saves).
    """
    pal = _paladin(2, pos={"x": 0, "y": 0})
    ally = _ally(pos={"x": 1, "y": 0}, ic_active=True, ic_bonus=2)
    ws = _make_ws({"paladin": pal, "ally": ally})
    bonus = _fear_bonus(ws, "ally")
    base = ally[EF.SAVE_WILL]
    # Expect base + 4 (AoC wins), NOT base + 2 + 4 = base + 6
    assert bonus == base + 4, (
        f"Expected {base+4} (morale non-stacking, AoC wins), got {bonus}"
    )
