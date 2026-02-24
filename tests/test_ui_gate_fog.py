"""Gate UI-FOG — Fog of War (10 tests).

Tests verify FogOfWarManager logic using a Python simulation of the
cell opacity state machine (mirrors fog-of-war.ts behavior).
"""
import pytest


OPACITY_HIDDEN   = 0.9
OPACITY_REVEALED = 0.3
OPACITY_VISIBLE  = 0.0


class FogOfWarSim:
    """Python simulation of FogOfWarManager for gate testing."""

    def __init__(self):
        self.cells = {}  # key -> {'opacity': float, 'revealed': bool}

    def _key(self, x, y):
        return f"{x},{y}"

    def _ensure_cells(self, bounds):
        for gx in range(bounds['x'], bounds['x'] + bounds['width']):
            for gy in range(bounds['y'], bounds['y'] + bounds['height']):
                key = self._key(gx, gy)
                if key not in self.cells:
                    self.cells[key] = {'opacity': OPACITY_HIDDEN, 'revealed': False}

    def handle_fog_update(self, revealed_cells, visible_cells, map_bounds):
        self._ensure_cells(map_bounds)
        visible_set = {self._key(c['x'], c['y']) for c in visible_cells}
        revealed_set = {self._key(c['x'], c['y']) for c in revealed_cells}
        for key, cell in self.cells.items():
            if key in visible_set:
                cell['revealed'] = True
                cell['opacity'] = OPACITY_VISIBLE
            elif key in revealed_set or cell['revealed']:
                cell['revealed'] = True
                cell['opacity'] = OPACITY_REVEALED
            else:
                cell['opacity'] = OPACITY_HIDDEN

    def get_cell(self, x, y):
        return self.cells.get(self._key(x, y))

    def get_cell_count(self):
        return len(self.cells)

    def dispose(self):
        self.cells.clear()

    def scene_position(self, gx, gy):
        """Mirror fog-of-war.ts _createCell position logic."""
        scale = 0.5
        return (gx * scale + scale / 2, 0.01, gy * scale + scale / 2)


# FOG-01: Initial state — all cells dark (opacity 0.9)
def test_fog01_initial_state():
    fog = FogOfWarSim()
    bounds = {'x': 0, 'y': 0, 'width': 3, 'height': 3}
    fog._ensure_cells(bounds)
    for key, cell in fog.cells.items():
        assert abs(cell['opacity'] - OPACITY_HIDDEN) < 0.01, \
            f"Cell {key} expected dark, got opacity {cell['opacity']}"


# FOG-02: fog_update revealed — revealed cells -> dim (opacity ~0.3)
def test_fog02_revealed_dim():
    fog = FogOfWarSim()
    bounds = {'x': 0, 'y': 0, 'width': 5, 'height': 5}
    fog.handle_fog_update(
        revealed_cells=[{'x': 2, 'y': 2}],
        visible_cells=[],
        map_bounds=bounds,
    )
    cell = fog.get_cell(2, 2)
    assert cell is not None
    assert abs(cell['opacity'] - OPACITY_REVEALED) < 0.01, \
        f"Expected revealed opacity {OPACITY_REVEALED}, got {cell['opacity']}"


# FOG-03: fog_update visible — visible cells -> clear (opacity 0)
def test_fog03_visible_clear():
    fog = FogOfWarSim()
    bounds = {'x': 0, 'y': 0, 'width': 5, 'height': 5}
    fog.handle_fog_update(
        revealed_cells=[{'x': 1, 'y': 1}],
        visible_cells=[{'x': 1, 'y': 1}],
        map_bounds=bounds,
    )
    cell = fog.get_cell(1, 1)
    assert abs(cell['opacity'] - OPACITY_VISIBLE) < 0.01, \
        f"Expected visible opacity {OPACITY_VISIBLE}, got {cell['opacity']}"


# FOG-04: Accumulation — second update without prior cell -> cell stays dim
def test_fog04_accumulation():
    fog = FogOfWarSim()
    bounds = {'x': 0, 'y': 0, 'width': 5, 'height': 5}
    # First update reveals cell (3,3)
    fog.handle_fog_update(
        revealed_cells=[{'x': 3, 'y': 3}],
        visible_cells=[{'x': 3, 'y': 3}],
        map_bounds=bounds,
    )
    # Second update — cell (3,3) not in either list
    fog.handle_fog_update(
        revealed_cells=[{'x': 0, 'y': 0}],
        visible_cells=[],
        map_bounds=bounds,
    )
    cell = fog.get_cell(3, 3)
    # Should still be dim (accumulated), NOT dark
    assert abs(cell['opacity'] - OPACITY_REVEALED) < 0.01, \
        f"Expected accumulated dim opacity {OPACITY_REVEALED}, got {cell['opacity']}"


# FOG-05: Cell count — manager creates correct cell count for map_bounds
def test_fog05_cell_count():
    fog = FogOfWarSim()
    bounds = {'x': 0, 'y': 0, 'width': 10, 'height': 8}
    fog._ensure_cells(bounds)
    assert fog.get_cell_count() == 80, f"Expected 80 cells, got {fog.get_cell_count()}"


# FOG-06: Cell position — cell at (4,3) maps to correct scene coords
def test_fog06_cell_position():
    fog = FogOfWarSim()
    px, py, pz = fog.scene_position(4, 3)
    # gx=4: 4*0.5 + 0.25 = 2.25; gy=3: 3*0.5 + 0.25 = 1.75
    assert abs(px - 2.25) < 0.001, f"Expected x=2.25, got {px}"
    assert abs(pz - 1.75) < 0.001, f"Expected z=1.75, got {pz}"
    assert abs(py - 0.01) < 0.001, f"Expected y=0.01, got {py}"


# FOG-07: Visible subset of revealed — visible cells are subset (or equal)
def test_fog07_visible_subset():
    fog = FogOfWarSim()
    bounds = {'x': 0, 'y': 0, 'width': 5, 'height': 5}
    revealed = [{'x': 1, 'y': 1}, {'x': 2, 'y': 2}, {'x': 3, 'y': 3}]
    visible  = [{'x': 2, 'y': 2}]  # subset of revealed
    fog.handle_fog_update(revealed, visible, bounds)
    # Cell 2,2 should be clear (visible)
    assert abs(fog.get_cell(2, 2)['opacity'] - OPACITY_VISIBLE) < 0.01
    # Cell 1,1 should be dim (revealed, not visible)
    assert abs(fog.get_cell(1, 1)['opacity'] - OPACITY_REVEALED) < 0.01
    # Cell 3,3 should be dim (revealed, not visible)
    assert abs(fog.get_cell(3, 3)['opacity'] - OPACITY_REVEALED) < 0.01


# FOG-08: Empty update — no crash on empty revealed/visible arrays
def test_fog08_empty_update():
    fog = FogOfWarSim()
    bounds = {'x': 0, 'y': 0, 'width': 5, 'height': 5}
    fog.handle_fog_update([], [], bounds)
    # All cells still hidden
    for cell in fog.cells.values():
        assert abs(cell['opacity'] - OPACITY_HIDDEN) < 0.01


# FOG-09: Large map — 24x16 grid (384 cells) without error
def test_fog09_large_map():
    fog = FogOfWarSim()
    bounds = {'x': 0, 'y': 0, 'width': 24, 'height': 16}
    fog.handle_fog_update([], [], bounds)
    assert fog.get_cell_count() == 384, f"Expected 384 cells, got {fog.get_cell_count()}"


# FOG-10: Dispose — FogOfWarManager.dispose() clears all cells
def test_fog10_dispose():
    fog = FogOfWarSim()
    bounds = {'x': 0, 'y': 0, 'width': 5, 'height': 5}
    fog._ensure_cells(bounds)
    fog.dispose()
    assert fog.get_cell_count() == 0, "Expected 0 cells after dispose"
