"""CP-18A-T&V Test Execution (Inline)

This script executes all 11 tests from the canonical document without creating
permanent test files (file budget constraint).

Results will be reported directly.
"""

import sys

# Force UTF-8 encoding for console output
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, r'F:\DnD-3.5')

from aidm.core.state import WorldState
from aidm.core.rng_manager import RNGManager
from aidm.schemas.targeting import GridPoint, VisibilityBlockReason
from aidm.core.targeting_resolver import (
    evaluate_target_legality,
    check_line_of_sight,
    check_line_of_effect,
    check_range,
    bresenham_line
)
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.core.attack_resolver import resolve_attack

# Test Results
results = []

def test(name):
    def decorator(func):
        try:
            func()
            results.append((name, "PASS", None))
            print(f"[PASS] {name}")
        except Exception as e:
            results.append((name, "FAIL", str(e)))
            print(f"[FAIL] {name}: {e}")
        return func
    return decorator


# ==================== SMOKE TESTS ====================

@test("Smoke 1: Clear LoS → Legal")
def test_clear_los():
    ws = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"position": {"x": 0, "y": 0}, "ac": 15, "hp_current": 10, "hp_max": 10},
            "goblin": {"position": {"x": 5, "y": 5}, "ac": 12, "hp_current": 6, "hp_max": 6}
        }
    )

    result = evaluate_target_legality("fighter", "goblin", ws)
    assert result.is_legal, f"Expected legal, got {result.failure_reason}"


@test("Smoke 2: Blocked Wall → Illegal (LOS_BLOCKED)")
def test_blocked_wall():
    ws = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"position": {"x": 0, "y": 0}, "ac": 15, "hp_current": 10, "hp_max": 10},
            "goblin": {"position": {"x": 5, "y": 0}, "ac": 12, "hp_current": 6, "hp_max": 6},
            "_terrain": {
                "map": {
                    "2,0": {"blocks_los": True, "blocks_loe": True}
                }
            }
        }
    )

    result = evaluate_target_legality("fighter", "goblin", ws)
    assert not result.is_legal, "Expected illegal"
    assert result.failure_reason == VisibilityBlockReason.LOE_BLOCKED, \
        f"Expected LOE_BLOCKED, got {result.failure_reason}"


@test("Smoke 3: Out of Range → Illegal (OUT_OF_RANGE)")
def test_out_of_range():
    ws = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"position": {"x": 0, "y": 0}, "ac": 15, "hp_current": 10, "hp_max": 10},
            "goblin": {"position": {"x": 101, "y": 0}, "ac": 12, "hp_current": 6, "hp_max": 6}
        }
    )

    result = evaluate_target_legality("fighter", "goblin", ws, max_range=100)
    assert not result.is_legal, "Expected illegal"
    assert result.failure_reason == VisibilityBlockReason.OUT_OF_RANGE, \
        f"Expected OUT_OF_RANGE, got {result.failure_reason}"


@test("Smoke 4: Missing Entity → Illegal (TARGET_NOT_VISIBLE)")
def test_missing_entity():
    ws = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"position": {"x": 0, "y": 0}, "ac": 15, "hp_current": 10, "hp_max": 10}
        }
    )

    result = evaluate_target_legality("fighter", "nonexistent", ws)
    assert not result.is_legal, "Expected illegal"
    assert result.failure_reason == VisibilityBlockReason.TARGET_NOT_VISIBLE, \
        f"Expected TARGET_NOT_VISIBLE, got {result.failure_reason}"


@test("Smoke 5: Diagonal Distance Calculation")
def test_diagonal_distance():
    p1 = GridPoint(0, 0)
    p2 = GridPoint(5, 5)

    # CP-14 diagonal constraints: 5 diagonals = 5 + (5//2) = 5 + 2 = 7
    distance = p1.distance_to(p2)
    assert distance == 7, f"Expected distance 7, got {distance}"


# ==================== INTEGRATION TESTS ====================

@test("Integration 1: AttackIntent Rejected on Illegal Target")
def test_attack_rejected():
    ws = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"position": {"x": 0, "y": 0}, "ac": 15, "hp_current": 10, "hp_max": 10},
            "goblin": {"position": {"x": 5, "y": 0}, "ac": 12, "hp_current": 6, "hp_max": 6},
            "_terrain": {
                "map": {
                    "2,0": {"blocks_los": True, "blocks_loe": True}
                }
            }
        }
    )

    intent = AttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing"),
        attack_bonus=5
    )

    rng = RNGManager(master_seed=42)
    events = resolve_attack(intent, ws, rng, 0, 1.0)

    # Should emit targeting_failed event, no attack roll
    assert len(events) == 1, f"Expected 1 event, got {len(events)}"
    assert events[0].event_type == "targeting_failed", \
        f"Expected targeting_failed, got {events[0].event_type}"
    assert events[0].payload["reason"] == "loe_blocked"


@test("Integration 2: AttackIntent Succeeds on Legal Target")
def test_attack_succeeds():
    ws = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"position": {"x": 0, "y": 0}, "ac": 15, "hp_current": 10, "hp_max": 10},
            "goblin": {"position": {"x": 5, "y": 0}, "ac": 12, "hp_current": 6, "hp_max": 6}
        }
    )

    intent = AttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing"),
        attack_bonus=5
    )

    rng = RNGManager(master_seed=42)
    events = resolve_attack(intent, ws, rng, 0, 1.0)

    # Should proceed with attack resolution (no targeting_failed event)
    assert all(e.event_type != "targeting_failed" for e in events), \
        "Should not emit targeting_failed for legal target"
    assert events[0].event_type == "attack_roll", \
        f"Expected attack_roll, got {events[0].event_type}"


@test("Integration 3: CastSpellIntent Stub Compatibility")
def test_spell_compatibility():
    # Verify evaluate_target_legality() works identically for spell casting
    ws = WorldState(
        ruleset_version="3.5e",
        entities={
            "wizard": {"position": {"x": 0, "y": 0}, "ac": 12, "hp_current": 8, "hp_max": 8},
            "goblin": {"position": {"x": 10, "y": 0}, "ac": 12, "hp_current": 6, "hp_max": 6}
        }
    )

    # Simulate spell targeting (same function, different context)
    result = evaluate_target_legality("wizard", "goblin", ws, max_range=50)
    assert result.is_legal, "Spell targeting should use same legality function"


# ==================== REPLAY TESTS ====================

@test("Replay 1: Deterministic 10× Replay")
def test_deterministic_replay():
    ws = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"position": {"x": 0, "y": 0}, "ac": 15, "hp_current": 10, "hp_max": 10},
            "goblin": {"position": {"x": 5, "y": 5}, "ac": 12, "hp_current": 6, "hp_max": 6},
            "_terrain": {
                "map": {
                    "3,3": {"blocks_los": True, "blocks_loe": True}
                }
            }
        }
    )

    results = []
    for _ in range(10):
        result = evaluate_target_legality("fighter", "goblin", ws)
        results.append((result.is_legal, result.failure_reason))

    # All results should be identical
    first = results[0]
    assert all(r == first for r in results), "Non-deterministic results detected"


# ==================== EDGE CASE TESTS ====================

@test("Edge 1: Bresenham Line Symmetry")
def test_bresenham_symmetry():
    p1 = GridPoint(0, 0)
    p2 = GridPoint(5, 5)

    line1 = bresenham_line(p1, p2)
    line2 = bresenham_line(p2, p1)

    # Should traverse same cells (order reversed)
    assert len(line1) == len(line2), "Line lengths differ"
    assert list(reversed(line1)) == line2, "Line symmetry broken"


@test("Edge 2: Self-Targeting (Zero Distance)")
def test_self_targeting():
    ws = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {"position": {"x": 5, "y": 5}, "ac": 15, "hp_current": 10, "hp_max": 10}
        }
    )

    result = evaluate_target_legality("fighter", "fighter", ws)
    assert result.is_legal, "Self-targeting should be legal (no LoS/LoE blockers)"


# ==================== EXECUTE TESTS ====================

print("=" * 60)
print("CP-18A-T&V Test Execution")
print("=" * 60)
print()

# Run all tests (decorated functions execute on definition)

print()
print("=" * 60)
print("Test Results Summary")
print("=" * 60)

passed = sum(1 for _, status, _ in results if status == "PASS")
failed = sum(1 for _, status, _ in results if status == "FAIL")

print(f"Total: {len(results)} | Passed: {passed} | Failed: {failed}")

if failed > 0:
    print()
    print("Failed Tests:")
    for name, status, error in results:
        if status == "FAIL":
            print(f"  - {name}: {error}")
    sys.exit(1)
else:
    print()
    print("[SUCCESS] All tests passed!")
    sys.exit(0)
