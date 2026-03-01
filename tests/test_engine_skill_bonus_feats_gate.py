"""Gate tests: ENGINE-AH-WO1 — Skill-Bonus Feats (PHB p.91-102)

12 PHB feats each grant +2 untyped bonus to two specific skills.
Wired into skill_resolver.resolve_skill_check() via _get_feat_skill_bonus().

Authority: RAW — PHB p.91-102 (individual feat entries). Untyped bonus (PHB names no type).

Tests: SBF-001 through SBF-008
"""

import pytest
from unittest.mock import MagicMock

from aidm.core.skill_resolver import resolve_skill_check
from aidm.schemas.entity_fields import EF


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_rng(roll=10):
    rng = MagicMock()
    stream = MagicMock()
    stream.randint = MagicMock(return_value=roll)
    rng.stream = MagicMock(return_value=stream)
    return rng


def _entity(feats=None, skill_ranks=None, wis_mod=0, dex_mod=0, str_mod=0,
            int_mod=0, cha_mod=0):
    """Minimal entity dict for skill checks."""
    return {
        EF.ENTITY_ID: "test_actor",
        EF.HP_CURRENT: 20,
        EF.HP_MAX: 20,
        EF.TEAM: "players",
        EF.CONDITIONS: {},
        EF.FEATS: feats if feats is not None else [],
        EF.SKILL_RANKS: skill_ranks if skill_ranks is not None else {},
        EF.WIS_MOD: wis_mod,
        EF.DEX_MOD: dex_mod,
        EF.STR_MOD: str_mod,
        EF.INT_MOD: int_mod,
        EF.CHA_MOD: cha_mod,
        EF.ARMOR_CHECK_PENALTY: 0,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestEngineSkillBonusFeatsGate:

    def test_SBF001_alertness_listen_bonus(self):
        """SBF-001: Entity with Alertness feat → Listen check gets +2 bonus (PHB p.91)."""
        entity_with = _entity(feats=["alertness"], skill_ranks={"listen": 2}, wis_mod=1)
        entity_without = _entity(feats=[], skill_ranks={"listen": 2}, wis_mod=1)
        dc = 99

        result_with = resolve_skill_check(entity_with, "listen", dc, _make_rng(roll=10))
        result_without = resolve_skill_check(entity_without, "listen", dc, _make_rng(roll=10))

        # With Alertness: +2 feat bonus on top of base total
        assert result_with.total == result_without.total + 2, \
            f"Alertness Listen: expected +2. with={result_with.total}, without={result_without.total}"

    def test_SBF002_alertness_spot_bonus(self):
        """SBF-002: Entity with Alertness feat → Spot check gets +2 bonus (PHB p.91)."""
        entity_with = _entity(feats=["alertness"], skill_ranks={"spot": 2}, wis_mod=1)
        entity_without = _entity(feats=[], skill_ranks={"spot": 2}, wis_mod=1)
        dc = 99

        result_with = resolve_skill_check(entity_with, "spot", dc, _make_rng(roll=10))
        result_without = resolve_skill_check(entity_without, "spot", dc, _make_rng(roll=10))

        assert result_with.total == result_without.total + 2, \
            f"Alertness Spot: expected +2. with={result_with.total}, without={result_without.total}"

    def test_SBF003_no_alertness_no_listen_bonus(self):
        """SBF-003: Entity WITHOUT Alertness feat → no Listen bonus applied."""
        entity = _entity(feats=[], skill_ranks={"listen": 3}, wis_mod=2)
        dc = 99

        result = resolve_skill_check(entity, "listen", dc, _make_rng(roll=10))
        # total = 10 (roll) + 2 (wis_mod) + 3 (ranks) = 15 — no feat bonus
        expected = 10 + 2 + 3
        assert result.total == expected, \
            f"No feat, no bonus. Expected {expected}, got {result.total}"

    def test_SBF004_athletic_climb_bonus(self):
        """SBF-004: Entity with Athletic feat → Climb check gets +2 bonus (PHB p.91)."""
        entity_with = _entity(feats=["athletic"], skill_ranks={"climb": 1}, str_mod=2)
        entity_without = _entity(feats=[], skill_ranks={"climb": 1}, str_mod=2)
        dc = 99

        result_with = resolve_skill_check(entity_with, "climb", dc, _make_rng(roll=10))
        result_without = resolve_skill_check(entity_without, "climb", dc, _make_rng(roll=10))

        assert result_with.total == result_without.total + 2, \
            f"Athletic Climb: expected +2. with={result_with.total}, without={result_without.total}"

    def test_SBF005_stealthy_hide_bonus(self):
        """SBF-005: Entity with Stealthy feat → Hide check gets +2 bonus (PHB p.101)."""
        entity_with = _entity(feats=["stealthy"], skill_ranks={"hide": 4}, dex_mod=2)
        entity_without = _entity(feats=[], skill_ranks={"hide": 4}, dex_mod=2)
        dc = 99

        result_with = resolve_skill_check(entity_with, "hide", dc, _make_rng(roll=10))
        result_without = resolve_skill_check(entity_without, "hide", dc, _make_rng(roll=10))

        assert result_with.total == result_without.total + 2, \
            f"Stealthy Hide: expected +2. with={result_with.total}, without={result_without.total}"

    def test_SBF006_stealthy_move_silently_bonus(self):
        """SBF-006: Entity with Stealthy feat → Move Silently check gets +2 bonus (PHB p.101)."""
        entity_with = _entity(feats=["stealthy"], skill_ranks={"move_silently": 3}, dex_mod=1)
        entity_without = _entity(feats=[], skill_ranks={"move_silently": 3}, dex_mod=1)
        dc = 99

        result_with = resolve_skill_check(entity_with, "move_silently", dc, _make_rng(roll=10))
        result_without = resolve_skill_check(entity_without, "move_silently", dc, _make_rng(roll=10))

        assert result_with.total == result_without.total + 2, \
            f"Stealthy Move Silently: expected +2. with={result_with.total}, without={result_without.total}"

    def test_SBF007_persuasive_two_skills_independent(self):
        """SBF-007: Entity with Persuasive feat → Bluff AND Intimidate both get +2 (PHB p.98).

        Both skills from a single feat fire independently.
        """
        entity = _entity(feats=["persuasive"], skill_ranks={"bluff": 2, "intimidate": 2}, cha_mod=1)
        entity_no = _entity(feats=[], skill_ranks={"bluff": 2, "intimidate": 2}, cha_mod=1)
        dc = 99

        bluff_with = resolve_skill_check(entity, "bluff", dc, _make_rng(roll=10))
        bluff_without = resolve_skill_check(entity_no, "bluff", dc, _make_rng(roll=10))
        intr_with = resolve_skill_check(entity, "intimidate", dc, _make_rng(roll=10))
        intr_without = resolve_skill_check(entity_no, "intimidate", dc, _make_rng(roll=10))

        assert bluff_with.total == bluff_without.total + 2, \
            f"Persuasive Bluff: expected +2. with={bluff_with.total}, without={bluff_without.total}"
        assert intr_with.total == intr_without.total + 2, \
            f"Persuasive Intimidate: expected +2. with={intr_with.total}, without={intr_without.total}"

    def test_SBF008_multiple_feats_stack_independently(self):
        """SBF-008: Entity with Alertness + Investigator → Listen+2 and Search+2 don't interfere.

        Two separate skill-bonus feats: Alertness (Listen+2, Spot+2) and Investigator (Gather Info+2, Search+2).
        Neither feat should bleed into the other's bonuses.
        """
        entity = _entity(
            feats=["alertness", "investigator"],
            skill_ranks={"listen": 3, "search": 3, "spot": 2},
            wis_mod=1,
            int_mod=0,
        )
        entity_no = _entity(
            feats=[],
            skill_ranks={"listen": 3, "search": 3, "spot": 2},
            wis_mod=1,
            int_mod=0,
        )
        dc = 99

        listen_with = resolve_skill_check(entity, "listen", dc, _make_rng(roll=10))
        listen_without = resolve_skill_check(entity_no, "listen", dc, _make_rng(roll=10))
        search_with = resolve_skill_check(entity, "search", dc, _make_rng(roll=10))
        search_without = resolve_skill_check(entity_no, "search", dc, _make_rng(roll=10))

        # Alertness grants +2 to Listen; Investigator grants +2 to Search.
        # They are independent: no double-counting, no interference.
        assert listen_with.total == listen_without.total + 2, \
            f"Alertness Listen: expected +2. with={listen_with.total}, without={listen_without.total}"
        assert search_with.total == search_without.total + 2, \
            f"Investigator Search: expected +2. with={search_with.total}, without={search_without.total}"
        # Spot gets +2 from Alertness only (not Investigator)
        spot_with = resolve_skill_check(entity, "spot", dc, _make_rng(roll=10))
        spot_without = resolve_skill_check(entity_no, "spot", dc, _make_rng(roll=10))
        assert spot_with.total == spot_without.total + 2, \
            f"Alertness Spot: expected +2 (not +4). with={spot_with.total}, without={spot_without.total}"
