"""
Gate UI-FOG-FADE: WO-UI-FOG-FADE-001 — Fog of war opacity fade transitions.

Tests (5):
  FF-01: fog-of-war.ts defines FADE_DURATION constant
  FF-02: FogCell interface has targetOpacity field
  FF-03: handleFogUpdate sets targetOpacity (not mat.opacity directly)
  FF-04: tick() method exists and lerps opacity toward targetOpacity
  FF-05: main.ts calls fogOfWar.tick(dt) in render loop
"""

import re
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
FOG_SRC  = ROOT / "client" / "src" / "fog-of-war.ts"
MAIN_SRC = ROOT / "client" / "src" / "main.ts"

fog_text  = FOG_SRC.read_text(encoding="utf-8")
main_text = MAIN_SRC.read_text(encoding="utf-8")


def test_ff01_fade_duration_constant():
    """FF-01: fog-of-war.ts defines FADE_DURATION constant."""
    assert "FADE_DURATION" in fog_text, (
        "fog-of-war.ts must define FADE_DURATION constant for opacity lerp duration"
    )
    # Should be a reasonable value (0.1 to 2.0 seconds)
    m = re.search(r"FADE_DURATION\s*=\s*([\d.]+)", fog_text)
    assert m, "FADE_DURATION must be assigned a numeric value"
    val = float(m.group(1))
    assert 0.1 <= val <= 2.0, f"FADE_DURATION={val} — expected between 0.1 and 2.0 seconds"


def test_ff02_fog_cell_has_target_opacity():
    """FF-02: FogCell interface has targetOpacity field."""
    assert "targetOpacity" in fog_text, (
        "FogCell interface must have a targetOpacity field for lerp destination"
    )


def test_ff03_handle_fog_update_sets_target_opacity():
    """FF-03: handleFogUpdate sets cell.targetOpacity, not mat.opacity directly."""
    assert "targetOpacity" in fog_text, "targetOpacity must be used in handleFogUpdate"
    # The handleFogUpdate method should assign to targetOpacity
    handle_block = re.search(
        r"handleFogUpdate\(.*?\}\s*\}",
        fog_text, re.DOTALL
    )
    assert handle_block, "handleFogUpdate method must be present"
    block = handle_block.group()
    assert "targetOpacity" in block, (
        "handleFogUpdate must set cell.targetOpacity for deferred opacity transitions"
    )


def test_ff04_tick_method_lerps_opacity():
    """FF-04: tick(dt) method exists and animates opacity toward targetOpacity."""
    assert "tick(" in fog_text, (
        "FogOfWarManager must have a tick(dt) method for per-frame opacity animation"
    )
    tick_block = re.search(
        r"tick\s*\(dt.*?\}\s*\}",
        fog_text, re.DOTALL
    )
    assert tick_block, "tick(dt) method must be present"
    block = tick_block.group()
    assert "targetOpacity" in block, "tick() must reference targetOpacity for lerp"
    assert "opacity" in block, "tick() must update mat.opacity"


def test_ff05_main_calls_tick():
    """FF-05: main.ts calls fogOfWar.tick(dt) in the render loop."""
    assert "fogOfWar.tick(" in main_text, (
        "main.ts render loop must call fogOfWar.tick(dt) to animate fog fade"
    )
