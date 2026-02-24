"""
Gate UI-SCENE-IMAGE: WO-UI-SCENE-IMAGE-001 — DM-side scene image plane.

Tests (6):
  SI-01: scene-builder.ts exports SceneImagePlane class
  SI-02: SceneImagePlane creates a PlaneGeometry mesh (flat image surface)
  SI-03: SceneImagePlane mesh positioned at DM-side z (negative z, DM far end)
  SI-04: SceneImagePlane.onSceneImage() method exists (accepts image URL)
  SI-05: SceneImagePlane.onCombatStart() and onCombatEnd() methods exist
  SI-06: SceneImagePlane uses rAF fade animation (requestAnimationFrame present)
"""

import re
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SB_SRC = ROOT / "client" / "src" / "scene-builder.ts"
MAIN_SRC = ROOT / "client" / "src" / "main.ts"

sb_text = SB_SRC.read_text(encoding="utf-8")
main_text = MAIN_SRC.read_text(encoding="utf-8")


def test_si01_scene_image_plane_exported():
    """SI-01: scene-builder.ts exports SceneImagePlane class."""
    assert "export class SceneImagePlane" in sb_text, (
        "scene-builder.ts must export SceneImagePlane class"
    )


def test_si02_uses_plane_geometry():
    """SI-02: SceneImagePlane uses PlaneGeometry for the flat image surface."""
    # Find the SceneImagePlane class body
    m = re.search(r"export class SceneImagePlane\b.*?(?=\nexport class|\Z)", sb_text, re.DOTALL)
    assert m, "SceneImagePlane class not found"
    class_body = m.group()
    assert "PlaneGeometry" in class_body, (
        "SceneImagePlane must use THREE.PlaneGeometry for the flat DM-side image surface"
    )


def test_si03_positioned_at_dm_side():
    """SI-03: SceneImagePlane mesh positioned at DM far end (z ≤ 0, positive z in scene or via z param)."""
    # The plane should be named 'scene_image_plane' and positioned at DM side
    assert "scene_image_plane" in sb_text, (
        "SceneImagePlane mesh must be named 'scene_image_plane'"
    )
    # Position must include a z offset — either negative z (DM side) or explicit comment
    m = re.search(r"export class SceneImagePlane\b.*?(?=\nexport class|\Z)", sb_text, re.DOTALL)
    assert m, "SceneImagePlane class not found"
    class_body = m.group()
    # Check position.set is called with 3 arguments
    assert re.search(r"position\.set\s*\(", class_body), (
        "SceneImagePlane must call mesh.position.set() to position on the table"
    )


def test_si04_on_scene_image_method():
    """SI-04: SceneImagePlane.onSceneImage() method exists to accept image URL."""
    m = re.search(r"export class SceneImagePlane\b.*?(?=\nexport class|\Z)", sb_text, re.DOTALL)
    assert m, "SceneImagePlane class not found"
    class_body = m.group()
    assert "onSceneImage(" in class_body, (
        "SceneImagePlane must have onSceneImage(url) method wired to scene_image WS event"
    )
    # Must use TextureLoader to load the image URL
    assert "TextureLoader" in class_body, (
        "onSceneImage must use THREE.TextureLoader to load the image URL"
    )


def test_si05_combat_lifecycle_methods():
    """SI-05: SceneImagePlane has onCombatStart() and onCombatEnd() methods."""
    m = re.search(r"export class SceneImagePlane\b.*?(?=\nexport class|\Z)", sb_text, re.DOTALL)
    assert m, "SceneImagePlane class not found"
    class_body = m.group()
    assert "onCombatStart(" in class_body, (
        "SceneImagePlane must have onCombatStart() to fade image out during combat"
    )
    assert "onCombatEnd(" in class_body, (
        "SceneImagePlane must have onCombatEnd() to restore image after combat"
    )


def test_si06_uses_raf_fade():
    """SI-06: SceneImagePlane uses requestAnimationFrame for smooth opacity fade."""
    m = re.search(r"export class SceneImagePlane\b.*?(?=\nexport class|\Z)", sb_text, re.DOTALL)
    assert m, "SceneImagePlane class not found"
    class_body = m.group()
    assert "requestAnimationFrame" in class_body, (
        "SceneImagePlane must use requestAnimationFrame for smooth fade-in/fade-out animation"
    )
