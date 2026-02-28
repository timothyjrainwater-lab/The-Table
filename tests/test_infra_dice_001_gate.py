"""Gate tests — WO-INFRA-DICE-001
INFRA-DICE gate: 8 tests (DI-001 – DI-008)

Verifies aidm/core/dice.py wrapper over d20 (MIT).
Deterministic seeding uses random.Random — the same interface d20.Roller accepts.
"""

import random
import pytest
import d20 as _d20

from aidm.core.dice import roll_dice


# DI-001: basic roll returns int in valid range
def test_di_001_basic_roll_range():
    result = roll_dice("1d6")
    assert isinstance(result, int)
    assert 1 <= result <= 6, f"1d6 result {result} outside [1, 6]"


# DI-002: roll with positive modifier returns int in valid range
def test_di_002_roll_with_bonus():
    result = roll_dice("2d4+3")
    assert isinstance(result, int)
    assert 5 <= result <= 11, f"2d4+3 result {result} outside [5, 11]"


# DI-003: seeded roll is deterministic (same seed → same result)
def test_di_003_seeded_roll_deterministic():
    rng_a = random.Random(42)
    rng_b = random.Random(42)
    r1 = roll_dice("1d20", rng=rng_a)
    r2 = roll_dice("1d20", rng=rng_b)
    assert r1 == r2, f"Same seed produced different results: {r1} vs {r2}"


# DI-004: different seeds produce different sequences over 10 rolls
def test_di_004_different_seeds_diverge():
    rng_a = random.Random(42)
    rng_b = random.Random(99)
    rolls_a = [roll_dice("1d20", rng=rng_a) for _ in range(10)]
    rolls_b = [roll_dice("1d20", rng=rng_b) for _ in range(10)]
    assert rolls_a != rolls_b, (
        "Seeds 42 and 99 produced identical 10-roll sequences — extremely unlikely"
    )


# DI-005: 2d6 roll in valid range
def test_di_005_2d6_range():
    result = roll_dice("2d6")
    assert isinstance(result, int)
    assert 2 <= result <= 12, f"2d6 result {result} outside [2, 12]"


# DI-006: bare integer string does not crash, returns correct value
def test_di_006_flat_value():
    result = roll_dice("1")
    assert result == 1, f"roll_dice('1') should return 1, got {result}"


# DI-007: d20 library is installed and importable; can roll 1d20
def test_di_007_d20_library_importable():
    result = _d20.roll("1d20").total
    assert 1 <= result <= 20, f"d20.roll('1d20').total={result} out of range"


# DI-008: roll_dice returns consistent type (int) across multiple expressions
def test_di_008_return_type_consistency():
    exprs = ["1d4", "1d6", "1d8", "1d10", "1d12", "1d20", "2d6+3", "3d8+1"]
    for expr in exprs:
        result = roll_dice(expr)
        assert isinstance(result, int), (
            f"roll_dice('{expr}') returned {type(result).__name__}, expected int"
        )
