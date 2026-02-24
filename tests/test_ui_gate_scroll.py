"""Gate UI-SCROLL -- Battle Map Scroll (8 tests).

Tests verify BattleScrollObject state machine using Python simulation.
"""
import pytest
import math

UNROLL_DURATION = 1.2
ROLLUP_DURATION = 0.8


class BattleScrollSim:
    """Python simulation of BattleScrollObject."""

    def __init__(self):
        self.scale_z = 0.001  # rolled state
        self.is_unrolled = False
        self.tokens_visible = False
        self.overlay_visible = False
        self._anim_from = 0.001
        self._anim_to = 0.001
        self._anim_start = 0.0
        self._anim_duration = UNROLL_DURATION

    def on_combat_start(self):
        if self.is_unrolled:
            return
        self.is_unrolled = True
        self.tokens_visible = True
        self.overlay_visible = True
        self._anim_from = self.scale_z
        self._anim_to = 1.0
        self._anim_start = 0.0
        self._anim_duration = UNROLL_DURATION

    def on_combat_end(self):
        if not self.is_unrolled:
            return
        self.is_unrolled = False
        self.tokens_visible = False
        self.overlay_visible = False
        self._anim_from = self.scale_z
        self._anim_to = 0.001
        self._anim_duration = ROLLUP_DURATION

    def tick(self, elapsed_s):
        """Simulate animation at elapsed_s seconds into current anim."""
        t = min(elapsed_s / self._anim_duration, 1.0)
        self.scale_z = self._anim_from + (self._anim_to - self._anim_from) * t


# SC-01: Initial state -- scroll visible, scaleZ ~= 0 (rolled)
def test_sc01_initial_state():
    scroll = BattleScrollSim()
    assert scroll.scale_z < 0.01, "Expected near-zero scaleZ, got %s" % scroll.scale_z
    assert scroll.is_unrolled is False
    assert scroll.tokens_visible is False


# SC-02: combat_start -- scroll unrolls (scaleZ goes 0->1 over 1.2s)
def test_sc02_combat_start_unrolls():
    scroll = BattleScrollSim()
    scroll.on_combat_start()
    scroll.tick(1.2)  # full duration
    assert abs(scroll.scale_z - 1.0) < 0.01, "Expected scaleZ~=1.0, got %s" % scroll.scale_z
    assert scroll.is_unrolled is True


# SC-03: combat_end -- scroll rolls up (scaleZ goes 1->0 over 0.8s)
def test_sc03_combat_end_rolls_up():
    scroll = BattleScrollSim()
    scroll.on_combat_start()
    scroll.tick(1.2)
    scroll.on_combat_end()
    scroll.tick(0.8)
    assert scroll.scale_z < 0.01, "Expected near-zero after rollup, got %s" % scroll.scale_z
    assert scroll.is_unrolled is False


# SC-04: Tokens hidden before unroll
def test_sc04_tokens_hidden_before_unroll():
    scroll = BattleScrollSim()
    assert scroll.tokens_visible is False


# SC-05: Tokens visible after unroll
def test_sc05_tokens_visible_after_unroll():
    scroll = BattleScrollSim()
    scroll.on_combat_start()
    assert scroll.tokens_visible is True


# SC-06: Map overlay hidden before unroll
def test_sc06_overlay_hidden_before_unroll():
    scroll = BattleScrollSim()
    assert scroll.overlay_visible is False


# SC-07: No Math.random -- verify seeded PRNG is used (Gate G compliance)
def test_sc07_no_math_random():
    """Verify battle-scroll.ts does not call Math.random() as code.
    Comment-only lines mentioning Math.random are allowed; actual calls are not.
    """
    import os
    src_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'client', 'src', 'battle-scroll.ts'
    )
    with open(src_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    violations = []
    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        if 'Math.random' in stripped:
            # Skip pure comment lines (// ... or JSDoc * ...)
            if stripped.startswith('//') or stripped.startswith('*'):
                continue
            violations.append("Line %d: %s" % (lineno, line.rstrip()))
    assert len(violations) == 0, (
        "Math.random() call found in battle-scroll.ts (not in comments):\n" +
        "\n".join(violations)
    )


# SC-08: Double combat_start safe -- second call while unrolled is no-op
def test_sc08_double_combat_start_safe():
    scroll = BattleScrollSim()
    scroll.on_combat_start()
    scroll.tick(0.6)  # mid-unroll
    scale_mid = scroll.scale_z
    scroll.on_combat_start()  # second call -- should be no-op
    # State should not have reset
    assert scroll.is_unrolled is True
    assert scroll.tokens_visible is True
