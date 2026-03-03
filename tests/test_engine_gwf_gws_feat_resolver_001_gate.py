"""Gate tests: WO-ENGINE-GWF-GWS-FEAT-RESOLVER-001 (Batch AZ WO1).

GWF-001..008 — Greater Weapon Focus/Specialization branches in feat_resolver:
  GWF-001: weapon_focus_longsword → get_attack_modifier returns +1 (regression)
  GWF-002: greater_weapon_focus_longsword alone → get_attack_modifier returns +1
  GWF-003: weapon_focus + greater_weapon_focus same weapon → stacks to +2
  GWF-004: greater_weapon_focus_longsword but weapon=dagger → returns 0 (weapon-specific)
  GWF-005: weapon_specialization_longsword → get_damage_modifier returns +2 (regression)
  GWF-006: greater_weapon_specialization_longsword alone → get_damage_modifier returns +2
  GWF-007: weapon_spec + greater_weapon_spec same weapon → stacks to +4
  GWF-008: Coverage map updated — GWF/GWS row references WO-ENGINE-GWF-GWS-FEAT-RESOLVER-001

PHB p.94: Greater Weapon Focus +1 attack (stacks with WF).
PHB p.94: Greater Weapon Specialization +2 damage (stacks with WS).
AUDIT-015 finding closed.
"""
from __future__ import annotations

import os
import pytest

from aidm.core.feat_resolver import get_attack_modifier, get_damage_modifier
from aidm.schemas.entity_fields import EF


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _attacker(feats: list) -> dict:
    return {EF.FEATS: feats}


def _context(weapon: str = "longsword") -> dict:
    return {
        "weapon_name": weapon,
        "range_ft": 5,
        "is_ranged": False,
        "is_twf": False,
        "power_attack_penalty": 0,
        "is_two_handed": False,
    }


def _target() -> dict:
    return {EF.FEATS: [], EF.CONDITIONS: {}}


# ---------------------------------------------------------------------------
# GWF-001: weapon_focus regression
# ---------------------------------------------------------------------------

def test_GWF001_weapon_focus_attack_bonus_regression():
    """GWF-001: weapon_focus_longsword still grants +1 attack (regression check)."""
    attacker = _attacker(["weapon_focus_longsword"])
    mod = get_attack_modifier(attacker, _target(), _context("longsword"))
    assert mod == 1, (
        f"GWF-001: weapon_focus_longsword must grant +1 attack. Got {mod}"
    )


# ---------------------------------------------------------------------------
# GWF-002: greater_weapon_focus alone → +1
# ---------------------------------------------------------------------------

def test_GWF002_greater_weapon_focus_plus1():
    """GWF-002: greater_weapon_focus_longsword alone grants +1 attack."""
    attacker = _attacker(["greater_weapon_focus_longsword"])
    mod = get_attack_modifier(attacker, _target(), _context("longsword"))
    assert mod == 1, (
        f"GWF-002: greater_weapon_focus_longsword must grant +1 attack. Got {mod}"
    )


# ---------------------------------------------------------------------------
# GWF-003: WF + GWF stacks to +2
# ---------------------------------------------------------------------------

def test_GWF003_wf_plus_gwf_stacks():
    """GWF-003: weapon_focus + greater_weapon_focus same weapon → +2 total (stacks)."""
    attacker = _attacker(["weapon_focus_longsword", "greater_weapon_focus_longsword"])
    mod = get_attack_modifier(attacker, _target(), _context("longsword"))
    assert mod == 2, (
        f"GWF-003: WF+GWF must stack to +2 attack. Got {mod}"
    )


# ---------------------------------------------------------------------------
# GWF-004: GWF weapon-specific (wrong weapon → 0)
# ---------------------------------------------------------------------------

def test_GWF004_gwf_weapon_specific():
    """GWF-004: greater_weapon_focus_longsword does NOT apply to dagger attacks."""
    attacker = _attacker(["greater_weapon_focus_longsword"])
    mod = get_attack_modifier(attacker, _target(), _context("dagger"))
    assert mod == 0, (
        f"GWF-004: GWF_longsword must not apply to dagger. Got {mod}"
    )


# ---------------------------------------------------------------------------
# GWF-005: weapon_specialization regression
# ---------------------------------------------------------------------------

def test_GWF005_weapon_spec_damage_regression():
    """GWF-005: weapon_specialization_longsword still grants +2 damage (regression)."""
    attacker = _attacker(["weapon_specialization_longsword"])
    mod = get_damage_modifier(attacker, _target(), _context("longsword"))
    assert mod == 2, (
        f"GWF-005: weapon_specialization_longsword must grant +2 damage. Got {mod}"
    )


# ---------------------------------------------------------------------------
# GWF-006: greater_weapon_spec alone → +2
# ---------------------------------------------------------------------------

def test_GWF006_greater_weapon_spec_plus2():
    """GWF-006: greater_weapon_specialization_longsword alone grants +2 damage."""
    attacker = _attacker(["greater_weapon_specialization_longsword"])
    mod = get_damage_modifier(attacker, _target(), _context("longsword"))
    assert mod == 2, (
        f"GWF-006: greater_weapon_specialization_longsword must grant +2 damage. Got {mod}"
    )


# ---------------------------------------------------------------------------
# GWF-007: WS + GWS stacks to +4
# ---------------------------------------------------------------------------

def test_GWF007_ws_plus_gws_stacks():
    """GWF-007: weapon_spec + greater_weapon_spec same weapon → +4 total (stacks)."""
    attacker = _attacker(["weapon_specialization_longsword", "greater_weapon_specialization_longsword"])
    mod = get_damage_modifier(attacker, _target(), _context("longsword"))
    assert mod == 4, (
        f"GWF-007: WS+GWS must stack to +4 damage. Got {mod}"
    )


# ---------------------------------------------------------------------------
# GWF-008: Coverage map updated
# ---------------------------------------------------------------------------

def test_GWF008_coverage_map_updated():
    """GWF-008: ENGINE_COVERAGE_MAP.md references WO-ENGINE-GWF-GWS-FEAT-RESOLVER-001."""
    cov_path = os.path.join(os.path.dirname(__file__), "..", "docs", "ENGINE_COVERAGE_MAP.md")
    with open(cov_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "WO-ENGINE-GWF-GWS-FEAT-RESOLVER-001" in content, (
        "GWF-008: ENGINE_COVERAGE_MAP.md must contain 'WO-ENGINE-GWF-GWS-FEAT-RESOLVER-001'"
    )
