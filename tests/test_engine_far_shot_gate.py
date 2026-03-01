"""Gate tests for Far Shot range penalty utility (PHB p.94). WO-ENGINE-AI-WO2.
Gate IDs: FSHOT-001 through FSHOT-008.

Tests call compute_range_penalty() directly. No WorldState required.
"""

import pytest
from aidm.core.attack_resolver import compute_range_penalty


# --- FSHOT-001: far_shot + projectile (longbow 60ft) at 80ft → 0 (within 1.5× = 90ft) ---

def test_fshot_001_far_shot_longbow_within_increment():
    """FSHOT-001: far_shot + longbow (60ft increment) at 80ft → 0 penalty (90ft effective)."""
    feats = ["far_shot"]
    weapon = {"range_increment": 60, "weapon_type": "ranged"}
    # effective_increment = 60 * 3 // 2 = 90
    # penalty = -2 * ((80 - 1) // 90) = -2 * 0 = 0
    result = compute_range_penalty(feats, 80, weapon)
    assert result == 0, f"Expected 0, got {result}"


# --- FSHOT-002: no far_shot + longbow at 80ft → -2 (in 2nd 60ft increment) ---

def test_fshot_002_no_far_shot_longbow_second_increment():
    """FSHOT-002: no far_shot + longbow (60ft) at 80ft → -2 (in 2nd increment)."""
    feats = []
    weapon = {"range_increment": 60, "weapon_type": "ranged"}
    # effective_increment = 60
    # penalty = -2 * ((80 - 1) // 60) = -2 * 1 = -2
    result = compute_range_penalty(feats, 80, weapon)
    assert result == -2, f"Expected -2, got {result}"


# --- FSHOT-003: far_shot + thrown (10ft) at 15ft → 0 (within 2× = 20ft) ---

def test_fshot_003_far_shot_thrown_within_increment():
    """FSHOT-003: far_shot + thrown (10ft) at 15ft → 0 (within 20ft effective)."""
    feats = ["far_shot"]
    weapon = {"range_increment": 10, "weapon_type": "thrown"}
    # effective_increment = 10 * 2 = 20
    # penalty = -2 * ((15 - 1) // 20) = -2 * 0 = 0
    result = compute_range_penalty(feats, 15, weapon)
    assert result == 0, f"Expected 0, got {result}"


# --- FSHOT-004: far_shot + thrown (10ft) at 25ft → -2 (2nd 20ft increment) ---

def test_fshot_004_far_shot_thrown_second_increment():
    """FSHOT-004: far_shot + thrown (10ft) at 25ft → -2 (in 2nd 20ft increment)."""
    feats = ["far_shot"]
    weapon = {"range_increment": 10, "weapon_type": "thrown"}
    # effective_increment = 20
    # penalty = -2 * ((25 - 1) // 20) = -2 * 1 = -2
    result = compute_range_penalty(feats, 25, weapon)
    assert result == -2, f"Expected -2, got {result}"


# --- FSHOT-005: no far_shot, at exact increment boundary → 0 ---

def test_fshot_005_no_far_shot_at_increment_boundary():
    """FSHOT-005: no far_shot, at exactly 30ft (within first 30ft increment) → 0."""
    feats = []
    weapon = {"range_increment": 30, "weapon_type": "ranged"}
    # penalty = -2 * ((30 - 1) // 30) = -2 * 0 = 0
    result = compute_range_penalty(feats, 30, weapon)
    assert result == 0, f"Expected 0, got {result}"


# --- FSHOT-006: far_shot + projectile, third increment → -4 ---

def test_fshot_006_far_shot_third_increment():
    """FSHOT-006: far_shot + 30ft-increment ranged at 140ft → -4 (3rd 45ft increment)."""
    feats = ["far_shot"]
    weapon = {"range_increment": 30, "weapon_type": "ranged"}
    # effective_increment = 30 * 3 // 2 = 45
    # penalty = -2 * ((140 - 1) // 45) = -2 * 3 = -6
    # Actually: 139 // 45 = 3 → -6
    result = compute_range_penalty(feats, 140, weapon)
    assert result == -6, f"Expected -6, got {result}"


# --- FSHOT-007: integer arithmetic only — no floats ---

def test_fshot_007_integer_arithmetic_no_floats():
    """FSHOT-007: result is an int, not float; 3//2 rounding correct."""
    feats = ["far_shot"]
    weapon = {"range_increment": 30, "weapon_type": "ranged"}  # 30 * 3 // 2 = 45
    result = compute_range_penalty(feats, 50, weapon)
    assert isinstance(result, int), f"Result must be int, got {type(result)}"
    # penalty = -2 * ((50 - 1) // 45) = -2 * 1 = -2
    assert result == -2, f"Expected -2, got {result}"


# --- FSHOT-008: default range_increment (30) used when key missing ---

def test_fshot_008_default_increment_fallback():
    """FSHOT-008: weapon_dict without range_increment defaults to 30ft."""
    feats = []
    weapon = {}  # no range_increment key
    # default = 30
    # penalty at 45ft = -2 * ((45 - 1) // 30) = -2 * 1 = -2
    result = compute_range_penalty(feats, 45, weapon)
    assert result == -2, f"Expected -2, got {result}"
