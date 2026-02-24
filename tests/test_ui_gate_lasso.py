"""Gate: Map Lasso (4 tests — regression guard)."""
import pytest


class MapLassoSim:
    def __init__(self):
        self._is_dragging = False
        self._points = []
        self._intents = []
        self._lasso_visible = False

    def start_drag(self, x, z):
        self._is_dragging = True
        self._points = [{'x': x, 'z': z}]
        self._lasso_visible = False

    def update_drag(self, x, z):
        if not self._is_dragging: return
        self._points.append({'x': x, 'z': z})
        if len(self._points) >= 2:
            self._lasso_visible = True

    def end_drag(self, kind='SEARCH'):
        if not self._is_dragging: return
        self._is_dragging = False
        if len(self._points) < 2:
            self._lasso_visible = False
            return
        self._points.append(self._points[0])  # close polygon
        self._intents.append({'kind': kind, 'polygon': list(self._points)})

    @property
    def is_dragging(self): return self._is_dragging
    @property
    def point_count(self): return len(self._points)
    @property
    def lasso_visible(self): return self._lasso_visible


def test_lasso01_drag_starts():
    lasso = MapLassoSim()
    lasso.start_drag(0, 0)
    assert lasso.is_dragging is True
    assert lasso.point_count == 1

def test_lasso02_update_adds_points():
    lasso = MapLassoSim()
    lasso.start_drag(0, 0)
    lasso.update_drag(1, 0)
    lasso.update_drag(1, 1)
    assert lasso.point_count == 3
    assert lasso.lasso_visible is True

def test_lasso03_end_emits_intent():
    lasso = MapLassoSim()
    lasso.start_drag(0, 0)
    lasso.update_drag(2, 0)
    lasso.update_drag(2, 2)
    lasso.end_drag('SEARCH')
    assert len(lasso._intents) == 1
    assert lasso._intents[0]['kind'] == 'SEARCH'
    # Polygon should be closed (first point repeated)
    poly = lasso._intents[0]['polygon']
    assert poly[0] == poly[-1]

def test_lasso04_not_dragging_after_end():
    lasso = MapLassoSim()
    lasso.start_drag(0, 0)
    lasso.update_drag(1, 1)
    lasso.end_drag()
    assert lasso.is_dragging is False
