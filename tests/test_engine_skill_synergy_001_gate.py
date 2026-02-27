"""Gate tests: ENGINE-SKILL-SYNERGY-001

Skill synergy bonuses (PHB p.65): 5+ ranks in source skill → +2 circumstance bonus
to synergistic target skills. Multiple sources stack.

WO-ENGINE-SKILL-SYNERGY-001, Batch J (Dispatch #19).
"""

import pytest
from unittest.mock import MagicMock

from aidm.core.skill_resolver import resolve_skill_check
from aidm.schemas.entity_fields import EF


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_rng(roll=10):
    """Return a mock RNG that always rolls `roll` on d20."""
    rng = MagicMock()
    stream = MagicMock()
    stream.randint = MagicMock(return_value=roll)
    rng.stream = MagicMock(return_value=stream)
    return rng


def _entity(skill_ranks=None, dex_mod=0, str_mod=0, int_mod=0, wis_mod=0, cha_mod=0):
    """Minimal entity dict for skill checks."""
    return {
        EF.ENTITY_ID: "test_actor",
        EF.HP_CURRENT: 20,
        EF.HP_MAX: 20,
        EF.TEAM: "players",
        EF.CONDITIONS: {},
        EF.SKILL_RANKS: skill_ranks if skill_ranks is not None else {},
        EF.DEX_MOD: dex_mod,
        EF.STR_MOD: str_mod,
        EF.INT_MOD: int_mod,
        EF.WIS_MOD: wis_mod,
        EF.CHA_MOD: cha_mod,
        EF.ARMOR_CHECK_PENALTY: 0,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestEngineSkillSynergy001Gate:

    def test_SS001_tumble_5_grants_jump_synergy(self):
        """SS-001: Actor with 5+ Tumble ranks makes Jump check — +2 synergy bonus."""
        # Tumble → Jump (+2). Actor has 5 Tumble, 0 Jump ranks.
        entity = _entity(
            skill_ranks={"tumble": 5, "jump": 0},
            str_mod=2,  # Jump key ability is STR
        )
        rng = _make_rng(roll=10)
        dc = 99  # Very high DC — we just inspect total

        result_with_synergy = resolve_skill_check(entity, "jump", dc, rng)
        # total = 10 (roll) + 2 (str_mod) + 0 (jump ranks) + 2 (synergy from tumble) = 14

        entity_no_synergy = _entity(
            skill_ranks={"tumble": 0, "jump": 0},
            str_mod=2,
        )
        result_no_synergy = resolve_skill_check(entity_no_synergy, "jump", dc, _make_rng(roll=10))
        # total = 10 + 2 + 0 = 12

        assert result_with_synergy.total == result_no_synergy.total + 2, \
            f"Expected +2 synergy: {result_with_synergy.total} vs {result_no_synergy.total}"

    def test_SS002_tumble_4_no_synergy(self):
        """SS-002: Actor with 4 Tumble ranks makes Jump check — no synergy (below threshold)."""
        entity_4 = _entity(skill_ranks={"tumble": 4, "jump": 0}, str_mod=2)
        entity_5 = _entity(skill_ranks={"tumble": 5, "jump": 0}, str_mod=2)

        rng = _make_rng(roll=10)
        result_4 = resolve_skill_check(entity_4, "jump", 99, _make_rng(roll=10))
        result_5 = resolve_skill_check(entity_5, "jump", 99, _make_rng(roll=10))

        assert result_4.total < result_5.total, "4 ranks gives no synergy; 5 ranks gives +2"
        assert result_5.total - result_4.total == 2

    def test_SS003_knowledge_arcana_5_grants_spellcraft_synergy(self):
        """SS-003: Actor with 5+ Knowledge(Arcana) ranks makes Spellcraft check — +2 synergy."""
        entity = _entity(
            skill_ranks={"knowledge_arcana": 5, "spellcraft": 1},  # 1 rank: trained-only guard
            int_mod=3,  # Spellcraft key ability is INT
        )
        result = resolve_skill_check(entity, "spellcraft", 99, _make_rng(roll=10))
        # 10 + 3 + 1 + 2 (synergy) = 16

        entity_no = _entity(skill_ranks={"knowledge_arcana": 0, "spellcraft": 1}, int_mod=3)
        result_no = resolve_skill_check(entity_no, "spellcraft", 99, _make_rng(roll=10))
        # 10 + 3 + 1 = 14

        assert result.total == result_no.total + 2

    def test_SS004_bluff_5_grants_intimidate_synergy(self):
        """SS-004: Actor with 5+ Bluff ranks makes Intimidate check — +2 synergy."""
        entity = _entity(
            skill_ranks={"bluff": 5, "intimidate": 0},
            cha_mod=1,  # Intimidate key ability is CHA
        )
        result = resolve_skill_check(entity, "intimidate", 99, _make_rng(roll=10))

        entity_no = _entity(skill_ranks={"bluff": 0, "intimidate": 0}, cha_mod=1)
        result_no = resolve_skill_check(entity_no, "intimidate", 99, _make_rng(roll=10))

        assert result.total == result_no.total + 2

    def test_SS005_bluff_and_sense_motive_stack_on_diplomacy(self):
        """SS-005: Actor with 5+ Bluff AND 5+ Sense Motive makes Diplomacy — +4 total (both stack)."""
        entity = _entity(
            skill_ranks={"bluff": 5, "sense_motive": 5, "diplomacy": 0},
            cha_mod=2,  # Diplomacy key ability is CHA
        )
        result = resolve_skill_check(entity, "diplomacy", 99, _make_rng(roll=10))
        # 10 + 2 + 0 + 2 (bluff→diplomacy) + 2 (sense_motive→diplomacy) = 16

        entity_none = _entity(skill_ranks={"bluff": 0, "sense_motive": 0, "diplomacy": 0}, cha_mod=2)
        result_none = resolve_skill_check(entity_none, "diplomacy", 99, _make_rng(roll=10))
        # 10 + 2 = 12

        assert result.total == result_none.total + 4, \
            f"Expected +4 stacked synergy: {result.total} vs {result_none.total}"

    def test_SS006_tumble_5_grants_balance_synergy(self):
        """SS-006: Actor with 5+ Tumble ranks makes Balance check — +2 synergy."""
        entity = _entity(
            skill_ranks={"tumble": 5, "balance": 0},
            dex_mod=2,  # Balance key ability is DEX
        )
        result = resolve_skill_check(entity, "balance", 99, _make_rng(roll=10))

        entity_no = _entity(skill_ranks={"tumble": 0, "balance": 0}, dex_mod=2)
        result_no = resolve_skill_check(entity_no, "balance", 99, _make_rng(roll=10))

        assert result.total == result_no.total + 2

    def test_SS007_unrelated_source_no_bonus(self):
        """SS-007: Actor with 5+ ranks in non-synergy source makes unrelated check — no bonus."""
        # Knowledge(Arcana) (5) does NOT synergize with Intimidate
        entity = _entity(
            skill_ranks={"knowledge_arcana": 5, "intimidate": 0},
            cha_mod=1,
        )
        result = resolve_skill_check(entity, "intimidate", 99, _make_rng(roll=10))

        entity_no_source = _entity(skill_ranks={"intimidate": 0}, cha_mod=1)
        result_no = resolve_skill_check(entity_no_source, "intimidate", 99, _make_rng(roll=10))

        assert result.total == result_no.total, "No synergy between arcana and intimidate"

    def test_SS008_no_skill_ranks_field_no_crash(self):
        """SS-008: Actor with no SKILL_RANKS field — no crash; no synergy bonus applied."""
        entity = _entity(str_mod=2)
        del entity[EF.SKILL_RANKS]  # Remove SKILL_RANKS field entirely

        # Use "jump" (STR-based, not trained-only)
        result = resolve_skill_check(entity, "jump", 99, _make_rng(roll=10))
        assert result is not None, "Must not crash when SKILL_RANKS field is absent"

        # No synergy bonus (no ranks → no source qualifies)
        entity_with_ranks = _entity(skill_ranks={}, str_mod=2)
        result_with_empty = resolve_skill_check(entity_with_ranks, "jump", 99, _make_rng(roll=10))
        assert result.total == result_with_empty.total, "Missing SKILL_RANKS same as empty"
