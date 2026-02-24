"""
Gate UI-FOG-VISION: WO-UI-FOG-VISION-001 — Vision type differentiation in FogOfWarManager.

Tests (5):
  FV-01: fog-of-war.ts exports VisionType union ('normal' | 'low_light' | 'darkvision')
  FV-02: FogOfWarManager has setEntityVision(entityId, visionType) method
  FV-03: FogOfWarManager has getRevealRadius() that returns 2× for low_light
  FV-04: FOG_COLOR_DARKVISION constant defined (dark blue-gray tint for darkvision)
  FV-05: main.ts extracts VISION_TYPE from entity_state and calls fog.setEntityVision()
"""

import re
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
FOG_SRC = ROOT / "client" / "src" / "fog-of-war.ts"
MAIN_SRC = ROOT / "client" / "src" / "main.ts"

fog_text = FOG_SRC.read_text(encoding="utf-8")
main_text = MAIN_SRC.read_text(encoding="utf-8")


def test_fv01_vision_type_exported():
    """FV-01: fog-of-war.ts exports VisionType union type."""
    assert "export type VisionType" in fog_text, (
        "fog-of-war.ts must export VisionType union type"
    )
    # Must include all three vision modes
    assert "'normal'" in fog_text or '"normal"' in fog_text, (
        "VisionType must include 'normal' vision mode"
    )
    assert "'low_light'" in fog_text or '"low_light"' in fog_text, (
        "VisionType must include 'low_light' vision mode"
    )
    assert "'darkvision'" in fog_text or '"darkvision"' in fog_text, (
        "VisionType must include 'darkvision' vision mode"
    )


def test_fv02_set_entity_vision_method():
    """FV-02: FogOfWarManager has setEntityVision() method."""
    assert "setEntityVision(" in fog_text, (
        "FogOfWarManager must have setEntityVision(entityId, visionType) method"
    )
    # Must store the vision in a map or similar structure
    assert "entityVisions" in fog_text, (
        "FogOfWarManager must maintain an entityVisions registry"
    )


def test_fv03_get_reveal_radius_low_light():
    """FV-03: getRevealRadius() returns 2× base radius for low_light entities."""
    assert "getRevealRadius(" in fog_text, (
        "FogOfWarManager must have getRevealRadius(entityId, baseRadius) method"
    )
    # low_light gives 2× multiplier
    assert re.search(r"low_light.*2|2.*low_light", fog_text, re.DOTALL), (
        "getRevealRadius must return 2× baseRadius when entity vision is 'low_light'"
    )
    m = re.search(r"baseRadius\s*\*\s*(\d+)", fog_text)
    assert m, "getRevealRadius must multiply baseRadius by a factor"
    assert m.group(1) == "2", (
        f"low_light radius multiplier must be 2, got {m.group(1)}"
    )


def test_fv04_darkvision_color_constant():
    """FV-04: FOG_COLOR_DARKVISION constant defined as dark blue-gray tint."""
    assert "FOG_COLOR_DARKVISION" in fog_text, (
        "fog-of-war.ts must define FOG_COLOR_DARKVISION constant for darkvision tint"
    )
    # Must be distinct from the normal black fog color
    assert "FOG_COLOR_NORMAL" in fog_text, (
        "fog-of-war.ts must define FOG_COLOR_NORMAL (black) for standard vision"
    )
    # Values must differ
    dv_m = re.search(r"FOG_COLOR_DARKVISION\s*=\s*(0x[0-9a-fA-F]+)", fog_text)
    nm_m = re.search(r"FOG_COLOR_NORMAL\s*=\s*(0x[0-9a-fA-F]+)", fog_text)
    assert dv_m and nm_m, "Both fog color constants must have hex values"
    assert dv_m.group(1).lower() != nm_m.group(1).lower(), (
        "FOG_COLOR_DARKVISION must be a different color than FOG_COLOR_NORMAL"
    )


def test_fv05_main_wires_vision_type():
    """FV-05: main.ts extracts VISION_TYPE from entity_state and calls fogOfWar.setEntityVision()."""
    assert "setEntityVision(" in main_text, (
        "main.ts must call fogOfWar.setEntityVision() when entity_state contains VISION_TYPE"
    )
    assert "VISION_TYPE" in main_text, (
        "main.ts must extract VISION_TYPE field from entity_state event data"
    )
