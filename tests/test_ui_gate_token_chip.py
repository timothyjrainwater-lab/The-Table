"""
Gate UI-TOKEN-CHIP + TOKEN-LABEL: WO-UI-TOKEN-CHIP-001 + WO-UI-TOKEN-LABEL-001.

Tests (10):
  TC-01: entity-renderer.ts uses PlaneGeometry (not CylinderGeometry) for tokens
  TC-02: TOKEN_CHIP_SIZE constant defined (flat chip dimensions)
  TC-03: Token mesh rotation.x = -Math.PI / 2 (flat on table surface)
  TC-04: _makeTokenTexture static method exists
  TC-05: Token material is MeshBasicMaterial with map (canvas texture)
  TC-06: Canvas texture draws a faction-colored disc (arc call present)
  TC-07: Token label renders the entity name (fillText for name/label)
  TC-08: Name is truncated to 8 chars maximum
  TC-09: Initial character rendered large (initial in canvas texture)
  TC-10: TOKEN_Y is ≤ 0.01 (flat chip sits just above surface, not floating)
"""

import re
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
ER_SRC = ROOT / "client" / "src" / "entity-renderer.ts"

er_text = ER_SRC.read_text(encoding="utf-8")


def test_tc01_plane_geometry_not_cylinder():
    """TC-01: entity-renderer.ts uses PlaneGeometry for tokens (not CylinderGeometry)."""
    assert "PlaneGeometry" in er_text, (
        "EntityRenderer must use THREE.PlaneGeometry for flat 2D token chips"
    )
    assert "CylinderGeometry" not in er_text, (
        "EntityRenderer must NOT use CylinderGeometry — tokens are flat 2D chips per North Star"
    )


def test_tc02_token_chip_size_constant():
    """TC-02: TOKEN_CHIP_SIZE constant defined for flat chip dimensions."""
    assert "TOKEN_CHIP_SIZE" in er_text, (
        "entity-renderer.ts must define TOKEN_CHIP_SIZE constant"
    )
    m = re.search(r"TOKEN_CHIP_SIZE\s*=\s*([\d.]+)", er_text)
    assert m, "TOKEN_CHIP_SIZE must have a numeric value"
    val = float(m.group(1))
    assert 0.1 <= val <= 1.0, f"TOKEN_CHIP_SIZE={val} — expected between 0.1 and 1.0 scene units"


def test_tc03_token_mesh_rotated_flat():
    """TC-03: Token mesh rotation.x = -Math.PI / 2 to lie flat on table."""
    assert "rotation.x = -Math.PI / 2" in er_text, (
        "Token mesh must have rotation.x = -Math.PI / 2 to orient flat on table surface"
    )


def test_tc04_make_token_texture_method():
    """TC-04: _makeTokenTexture static method exists on EntityRenderer."""
    assert "_makeTokenTexture" in er_text, (
        "EntityRenderer must have a static _makeTokenTexture method for canvas chip generation"
    )
    assert "static _makeTokenTexture" in er_text, (
        "_makeTokenTexture must be a static method"
    )


def test_tc05_mesh_basic_material_with_map():
    """TC-05: Token material uses MeshBasicMaterial with map (canvas texture)."""
    assert "MeshBasicMaterial" in er_text, (
        "Token must use THREE.MeshBasicMaterial with map for canvas texture rendering"
    )
    # map: chipTex or similar
    assert re.search(r"map\s*:\s*\w+[Tt]ex", er_text), (
        "MeshBasicMaterial must set map to the canvas texture"
    )


def test_tc06_canvas_draws_faction_disc():
    """TC-06: Canvas texture draws a faction-colored disc (ctx.arc present)."""
    assert "ctx.arc(" in er_text, (
        "_makeTokenTexture must draw a circular disc using ctx.arc()"
    )
    # fillStyle must be set with faction color
    assert "fillStyle" in er_text, (
        "_makeTokenTexture must set fillStyle with faction color for the disc"
    )


def test_tc07_canvas_renders_entity_name():
    """TC-07: Token label renders entity name via canvas fillText."""
    # fillText should be called with the name/label
    assert "fillText" in er_text, (
        "_makeTokenTexture must call ctx.fillText() to render entity name"
    )


def test_tc08_name_truncated_to_8_chars():
    """TC-08: Entity name truncated to 8 characters maximum."""
    assert re.search(r"slice\s*\(\s*0\s*,\s*8\s*\)", er_text), (
        "_makeTokenTexture must truncate name via .slice(0, 8)"
    )


def test_tc09_initial_character_rendered():
    """TC-09: Token renders first character (initial) large."""
    assert "charAt(0)" in er_text or "initial" in er_text, (
        "_makeTokenTexture must extract and render the first character as a large initial"
    )
    assert "initial" in er_text, (
        "_makeTokenTexture must use the 'initial' (first char) for the large center glyph"
    )


def test_tc10_token_y_near_surface():
    """TC-10: TOKEN_Y is ≤ 0.01 — flat chip sits just above table surface."""
    m = re.search(r"TOKEN_Y\s*=\s*([\d.]+)", er_text)
    assert m, "TOKEN_Y constant must be defined"
    val = float(m.group(1))
    assert val <= 0.01, (
        f"TOKEN_Y={val} — flat chip should be ≤ 0.01 (just above surface, not floating)"
    )
