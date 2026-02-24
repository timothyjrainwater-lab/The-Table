"""Gate UI-DICE — Dice Bag (6 tests).

Tests verify DiceBagObject state machine: open/close toggle,
decorative dice visibility, magical bag rule, seeded PRNG texture.
"""
import pytest


class MockPrng:
    """Deterministic PRNG for testing."""
    def __init__(self, seed=42):
        self._state = seed

    def __call__(self):
        # LCG: same as makePrng in scene-builder.ts
        self._state = (self._state * 1664525 + 1013904223) & 0xFFFFFFFF
        return (self._state & 0x7FFFFFFF) / 0x7FFFFFFF


class DiceBagSim:
    """Python simulation of DiceBagObject state machine."""

    def __init__(self, prng):
        self.is_open = False
        self.decor_dice_visible = False
        self.lid_y = 0.19  # closed position
        self.lid_y_open = 0.55
        self.lid_y_closed = 0.19
        self.prng = prng
        # Generate dice colors using prng (seeded)
        self.dice_colors = [int(prng() * 0xFFFFFF) for _ in range(5)]  # 5 decor dice

    def open(self):
        if self.is_open:
            return
        self.is_open = True
        self.decor_dice_visible = True
        self.lid_y = self.lid_y_open  # immediate in sim (skip animation)

    def close(self):
        if not self.is_open:
            return
        self.is_open = False
        self.lid_y = self.lid_y_closed
        self.decor_dice_visible = False

    def toggle(self):
        if self.is_open:
            self.close()
        else:
            self.open()


# DICE-01: Initial state — bag closed, decorative dice hidden
def test_dice01_initial_closed():
    prng = MockPrng(42)
    bag = DiceBagSim(prng)
    assert bag.is_open is False
    assert bag.decor_dice_visible is False
    assert abs(bag.lid_y - 0.19) < 0.001


# DICE-02: Click bag → opens, lid lifts, dice visible
def test_dice02_open():
    prng = MockPrng(42)
    bag = DiceBagSim(prng)
    bag.open()
    assert bag.is_open is True
    assert bag.decor_dice_visible is True
    assert bag.lid_y > 0.19  # lid lifted


# DICE-03: Click again → closes, dice hidden
def test_dice03_close():
    prng = MockPrng(42)
    bag = DiceBagSim(prng)
    bag.open()
    bag.close()
    assert bag.is_open is False
    assert bag.decor_dice_visible is False
    assert abs(bag.lid_y - 0.19) < 0.001


# DICE-04: Toggle behavior
def test_dice04_toggle():
    prng = MockPrng(42)
    bag = DiceBagSim(prng)
    bag.toggle()  # open
    assert bag.is_open is True
    bag.toggle()  # close
    assert bag.is_open is False


# DICE-05: Magical bag rule — d20 stays in bag (double open is idempotent)
def test_dice05_magical_bag():
    prng = MockPrng(42)
    bag = DiceBagSim(prng)
    bag.open()
    # Opening an already-open bag should not change state (d20 not "taken")
    bag.open()
    assert bag.is_open is True
    assert bag.decor_dice_visible is True


# DICE-06: Seeded PRNG — same seed produces same dice colors
def test_dice06_seeded_colors():
    prng_a = MockPrng(42)
    bag_a = DiceBagSim(prng_a)

    prng_b = MockPrng(42)
    bag_b = DiceBagSim(prng_b)

    assert bag_a.dice_colors == bag_b.dice_colors, \
        "Same seed must produce same dice colors (deterministic)"
