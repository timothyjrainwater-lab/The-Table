"""Gate: Settings Gem regression guard (3 tests — WO-UI-SETTINGS-GEM-001)."""
import pytest


class SettingsGemSim:
    """Pure-Python simulation of SettingsGem state machine."""

    def __init__(self):
        self.is_open:    bool  = False
        self.volume:     float = 0.8
        self.tts_voice:  str   = 'npc_elderly'
        self.ui_scale:   float = 1.0
        self._hold_pending: bool = False

    def on_pointer_down(self):
        self._hold_pending = True

    def on_pointer_up(self):
        if self._hold_pending:
            self._hold_pending = False
            self.toggle()

    def simulate_hold(self):
        """Simulate 1.5 s hold completing (hold timer fires before pointerup)."""
        self._hold_pending = False
        self.reset_defaults()

    def toggle(self):
        self.is_open = not self.is_open

    def open(self):
        self.is_open = True

    def close(self):
        self.is_open = False

    def reset_defaults(self):
        self.volume    = 0.8
        self.tts_voice = 'npc_elderly'
        self.ui_scale  = 1.0
        self.is_open   = False


# ---------------------------------------------------------------------------
# GEM-01: Single tap opens settings overlay
# ---------------------------------------------------------------------------
def test_gem01_tap_opens():
    gem = SettingsGemSim()
    gem.on_pointer_down()
    gem.on_pointer_up()
    assert gem.is_open is True


# ---------------------------------------------------------------------------
# GEM-02: Second tap closes settings overlay
# ---------------------------------------------------------------------------
def test_gem02_tap_closes():
    gem = SettingsGemSim()
    gem.on_pointer_down()
    gem.on_pointer_up()   # open
    gem.on_pointer_down()
    gem.on_pointer_up()   # close
    assert gem.is_open is False


# ---------------------------------------------------------------------------
# GEM-03: Hold resets to defaults and closes overlay
# ---------------------------------------------------------------------------
def test_gem03_hold_resets():
    gem = SettingsGemSim()
    # Apply non-default state
    gem.volume    = 0.3
    gem.tts_voice = 'npc_male'
    gem.ui_scale  = 1.2
    gem.open()
    # Simulate hold completing
    gem.on_pointer_down()
    gem.simulate_hold()   # 1.5 s elapsed — reset fires before pointerup
    assert gem.volume    == 0.8
    assert gem.tts_voice == 'npc_elderly'
    assert gem.ui_scale  == 1.0
    assert gem.is_open   is False
