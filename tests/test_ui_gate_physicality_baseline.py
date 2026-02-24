"""Gate UI-PHYSICALITY-BASELINE — Kinematic drag + shelf constraints (8 checks).

Verifies:
1.  shelf-drag.ts exists with ShelfDragController class
2.  lerpFactor default is 0.18
3.  settleFrames default is 8
4.  register() sets userData.draggable = true
5.  _onPointerDown only responds to button 0 (left mouse)
6.  ShelfDragController clamps to shelf bounds (minX/maxX/minZ/maxZ)
7.  main.ts imports ShelfDragController and calls shelfDrag.register()
8.  shelfDrag.update() is called in the animation loop
"""

import os
import re

ROOT      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DRAG     = os.path.join(ROOT, 'client', 'src', 'shelf-drag.ts')
_MAIN     = os.path.join(ROOT, 'client', 'src', 'main.ts')


def _src(path: str) -> str:
    with open(path) as f:
        return f.read()


# ---------------------------------------------------------------------------
# CHECK 1: shelf-drag.ts exists, exports ShelfDragController
# ---------------------------------------------------------------------------

def test_shelf_drag_module_exists():
    assert os.path.isfile(_DRAG), \
        "client/src/shelf-drag.ts must exist (WO-UI-PHYSICALITY-BASELINE-V1)"
    src = _src(_DRAG)
    assert 'export class ShelfDragController' in src, \
        "shelf-drag.ts must export class ShelfDragController"


# ---------------------------------------------------------------------------
# CHECK 2: lerpFactor default is 0.18
# ---------------------------------------------------------------------------

def test_lerp_factor_default():
    src = _src(_DRAG)
    # DEFAULT_CONFIG must have lerpFactor: 0.18
    assert 'lerpFactor' in src, "shelf-drag.ts must define lerpFactor"
    match = re.search(r'lerpFactor\s*:\s*([\d.]+)', src)
    assert match, "lerpFactor must have a numeric value in DEFAULT_CONFIG"
    val = float(match.group(1))
    assert abs(val - 0.18) < 1e-9, \
        f"DEFAULT_CONFIG lerpFactor must be 0.18, got {val}"


# ---------------------------------------------------------------------------
# CHECK 3: settleFrames default is 8
# ---------------------------------------------------------------------------

def test_settle_frames_default():
    src = _src(_DRAG)
    assert 'settleFrames' in src, "shelf-drag.ts must define settleFrames"
    match = re.search(r'settleFrames\s*:\s*(\d+)', src)
    assert match, "settleFrames must have a numeric value in DEFAULT_CONFIG"
    val = int(match.group(1))
    assert val == 8, \
        f"DEFAULT_CONFIG settleFrames must be 8, got {val}"


# ---------------------------------------------------------------------------
# CHECK 4: register() sets userData.draggable = true
# ---------------------------------------------------------------------------

def test_register_sets_draggable():
    src = _src(_DRAG)
    assert 'userData.draggable = true' in src or "userData['draggable'] = true" in src, \
        "ShelfDragController.register() must set mesh.userData.draggable = true"
    # Zone must also be set
    assert "userData.zone = 'SHELF_ZONE'" in src or 'userData.zone = "SHELF_ZONE"' in src, \
        "ShelfDragController.register() must set mesh.userData.zone = 'SHELF_ZONE'"


# ---------------------------------------------------------------------------
# CHECK 5: _onPointerDown guards on button === 0 (left mouse only)
# ---------------------------------------------------------------------------

def test_pointer_down_left_button_only():
    src = _src(_DRAG)
    # Must have a button check — e.button !== 0 or e.button != 0
    assert 'e.button !== 0' in src or 'e.button != 0' in src, \
        "_onPointerDown must guard: if (e.button !== 0) return"


# ---------------------------------------------------------------------------
# CHECK 6: shelf bounds clamp enforced (minX, maxX, minZ, maxZ)
# ---------------------------------------------------------------------------

def test_shelf_bounds_clamp():
    src = _src(_DRAG)
    # Must clamp to minX and maxX
    assert 'minX' in src and 'maxX' in src, \
        "ShelfDragController must compute and clamp to minX/maxX (SHELF_ZONE.centerX ± halfWidth)"
    assert 'minZ' in src and 'maxZ' in src, \
        "ShelfDragController must compute and clamp to minZ/maxZ (SHELF_ZONE.centerZ ± halfHeight)"
    # Math.max/Math.min clamp pattern
    assert 'Math.max' in src and 'Math.min' in src, \
        "_onPointerMove must use Math.max/Math.min to clamp position to shelf bounds"


# ---------------------------------------------------------------------------
# CHECK 7: main.ts imports ShelfDragController and registers shelf objects
# ---------------------------------------------------------------------------

def test_main_registers_shelf_objects():
    src = _src(_MAIN)
    # Import
    assert 'ShelfDragController' in src, \
        "main.ts must import ShelfDragController from './shelf-drag'"
    assert "from './shelf-drag'" in src, \
        "main.ts must import from './shelf-drag'"
    # Registration calls
    assert 'shelfDrag.register(' in src, \
        "main.ts must call shelfDrag.register() to register draggable shelf objects"
    # Must register at least 3 objects (sheet, notebook/book, diceBag)
    register_count = src.count('shelfDrag.register(')
    assert register_count >= 3, \
        f"main.ts must register at least 3 shelf objects, found {register_count} calls"


# ---------------------------------------------------------------------------
# CHECK 8: shelfDrag.update() called in animation loop
# ---------------------------------------------------------------------------

def test_shelf_drag_update_in_animate():
    src = _src(_MAIN)
    assert 'shelfDrag.update(' in src, \
        "main.ts animate loop must call shelfDrag.update(dt)"
    # Confirm it's near other per-frame calls (updateFlicker, etc.)
    # Look for shelfDrag.update in the animate function body
    animate_idx = src.rfind('function animate()')
    assert animate_idx != -1, "main.ts must have animate() function"
    animate_body = src[animate_idx:]
    assert 'shelfDrag.update(' in animate_body, \
        "shelfDrag.update() must be called inside the animate() function"
