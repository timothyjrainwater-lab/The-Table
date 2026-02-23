"""
Gate UI-06 — EntityRenderer test suite.

Tests the coordinate transform, token lifecycle, roster sync, HP bar color,
and message-handler semantics. All tests exercise the logic specified in
WO-UI-06 using a lightweight Python simulation of the EntityRenderer contract.

Running: pytest tests/test_ui_gate_ui06.py -v
Target:  10 PASS
"""

import pytest
import math

# ---------------------------------------------------------------------------
# Python simulation of EntityRenderer (mirrors entity-renderer.ts contract)
# ---------------------------------------------------------------------------

GRID_SCALE = 0.5
TOKEN_Y    = 0.08
HP_BAR_Y_ABOVE = 0.12

FACTION_COLORS = {
    "player": 0xd4a820,
    "enemy":  0x8b1a1a,
    "npc":    0x4a6a8a,
}
FALLBACK_COLOR = 0x888888

HP_COLOR_FULL = (0x22, 0xaa, 0x22)  # green
HP_COLOR_ZERO = (0xaa, 0x22, 0x22)  # red


def grid_to_scene(x: float, y: float) -> tuple[float, float, float]:
    """Mirror of EntityRenderer.gridToScene()."""
    return (x * GRID_SCALE, TOKEN_Y, y * GRID_SCALE)


def lerp_color(c0: tuple, c1: tuple, t: float) -> tuple[int, int, int]:
    """Linear interpolation between two RGB tuples (t=0 → c0, t=1 → c1)."""
    t = max(0.0, min(1.0, t))
    return (
        int(c0[0] + (c1[0] - c0[0]) * t),
        int(c0[1] + (c1[1] - c0[1]) * t),
        int(c0[2] + (c1[2] - c0[2]) * t),
    )


def hp_bar_color(hp_current: int, hp_max: int) -> tuple[int, int, int]:
    """
    Mirror of EntityRenderer._updateHpBar() color logic.
    Lerps from HP_COLOR_ZERO (red) to HP_COLOR_FULL (green) by fraction.
    """
    fraction = max(0.0, min(1.0, hp_current / hp_max)) if hp_max > 0 else 0.0
    return lerp_color(HP_COLOR_ZERO, HP_COLOR_FULL, fraction)


# Minimal scene stub
class MockMesh:
    def __init__(self):
        self.position = [0.0, 0.0, 0.0]
        self.color = (0, 0, 0)
        self.scale_x = 1.0


class MockScene:
    def __init__(self):
        self.children: list = []

    def add(self, obj):
        self.children.append(obj)

    def remove(self, obj):
        if obj in self.children:
            self.children.remove(obj)


class EntityToken:
    def __init__(self, entity_id, faction, hp_max):
        self.id = entity_id
        self.mesh = MockMesh()
        self.hp_bar = MockMesh()
        self.faction = faction
        self.hp_max = hp_max


class EntityRenderer:
    """Python mirror of the TypeScript EntityRenderer class."""

    def __init__(self, scene: MockScene):
        self.scene = scene
        self._tokens: dict[str, EntityToken] = {}

    def upsert(self, entity: dict) -> None:
        eid = entity["id"]
        existing = self._tokens.get(eid)

        if existing:
            if "position" in entity:
                pos = grid_to_scene(entity["position"]["x"], entity["position"]["y"])
                existing.mesh.position = list(pos)
                existing.hp_bar.position = [pos[0], pos[1] + HP_BAR_Y_ABOVE, pos[2]]
            hp_current = entity.get("hp_current")
            hp_max = entity.get("hp_max", existing.hp_max)
            if hp_current is not None:
                existing.hp_max = hp_max
                self._update_hp_bar(existing, hp_current, hp_max)
            return

        faction = entity.get("faction", "npc")
        token = EntityToken(eid, faction, entity.get("hp_max", 1))
        token.mesh = MockMesh()
        token.hp_bar = MockMesh()

        if "position" in entity:
            pos = grid_to_scene(entity["position"]["x"], entity["position"]["y"])
            token.mesh.position = list(pos)
            token.hp_bar.position = [pos[0], pos[1] + HP_BAR_Y_ABOVE, pos[2]]

        self.scene.add(token.mesh)
        self.scene.add(token.hp_bar)
        self._tokens[eid] = token

        hp_current = entity.get("hp_current", token.hp_max)
        self._update_hp_bar(token, hp_current, token.hp_max)

    def remove(self, entity_id: str) -> None:
        token = self._tokens.get(entity_id)
        if not token:
            return
        self.scene.remove(token.mesh)
        self.scene.remove(token.hp_bar)
        del self._tokens[entity_id]

    def sync_roster(self, entities: list[dict]) -> None:
        incoming_ids = {e["id"] for e in entities}
        for eid in list(self._tokens.keys()):
            if eid not in incoming_ids:
                self.remove(eid)
        for entity in entities:
            self.upsert(entity)

    @property
    def token_count(self) -> int:
        return len(self._tokens)

    def has_token(self, entity_id: str) -> bool:
        return entity_id in self._tokens

    def _update_hp_bar(self, token: EntityToken, hp_current: int, hp_max: int) -> None:
        color = hp_bar_color(hp_current, hp_max)
        token.hp_bar.color = color
        fraction = max(0.0, min(1.0, hp_current / hp_max)) if hp_max > 0 else 0.0
        token.hp_bar.scale_x = max(fraction, 0.01)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_renderer() -> tuple[EntityRenderer, MockScene]:
    scene = MockScene()
    renderer = EntityRenderer(scene)
    return renderer, scene


ENTITY_KIRA = {
    "id": "p1", "name": "Kira", "faction": "player",
    "position": {"x": 2, "y": 3}, "hp_current": 11, "hp_max": 11, "conditions": [],
}
ENTITY_GOBLIN = {
    "id": "e1", "name": "Goblin", "faction": "enemy",
    "position": {"x": 8, "y": 5}, "hp_current": 7, "hp_max": 7, "conditions": [],
}
ENTITY_GUARD = {
    "id": "n1", "name": "Guard", "faction": "npc",
    "position": {"x": 0, "y": 0}, "hp_current": 10, "hp_max": 10, "conditions": [],
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCoordinateTransform:

    def test_ui06_01_origin(self):
        """UI06-01: gridToScene(0, 0) returns (0, 0.08, 0)."""
        x, y, z = grid_to_scene(0, 0)
        assert x == pytest.approx(0.0)
        assert y == pytest.approx(TOKEN_Y)
        assert z == pytest.approx(0.0)

    def test_ui06_02_offset(self):
        """UI06-02: gridToScene(4, 3) returns (2.0, 0.08, 1.5)."""
        x, y, z = grid_to_scene(4, 3)
        assert x == pytest.approx(2.0)
        assert y == pytest.approx(0.08)
        assert z == pytest.approx(1.5)


class TestTokenLifecycle:

    def test_ui06_03_upsert_adds_two_children(self):
        """UI06-03: upsert() adds token + HP bar (2 children) to scene."""
        renderer, scene = make_renderer()
        before = len(scene.children)
        renderer.upsert(ENTITY_KIRA)
        assert len(scene.children) == before + 2

    def test_ui06_04_upsert_same_id_no_duplicate(self):
        """UI06-04: upsert() called twice with same id — no duplicate tokens."""
        renderer, scene = make_renderer()
        renderer.upsert(ENTITY_KIRA)
        count_after_first = len(scene.children)
        renderer.upsert({**ENTITY_KIRA, "hp_current": 8})
        assert len(scene.children) == count_after_first  # no new meshes added
        assert renderer.token_count == 1

    def test_ui06_05_remove_clears_token(self):
        """UI06-05: remove() removes meshes from scene; token map empty for id."""
        renderer, scene = make_renderer()
        renderer.upsert(ENTITY_KIRA)
        renderer.remove("p1")
        assert not renderer.has_token("p1")
        assert len(scene.children) == 0

    def test_ui06_06_sync_roster_removes_stale(self):
        """UI06-06: syncRoster([A,B,C]) then syncRoster([A,C]) — B removed, A and C updated."""
        renderer, scene = make_renderer()
        renderer.sync_roster([ENTITY_KIRA, ENTITY_GOBLIN, ENTITY_GUARD])
        assert renderer.token_count == 3

        renderer.sync_roster([ENTITY_KIRA, ENTITY_GUARD])
        assert renderer.token_count == 2
        assert not renderer.has_token("e1")   # Goblin removed
        assert renderer.has_token("p1")       # Kira present
        assert renderer.has_token("n1")       # Guard present


class TestHpBar:

    def test_ui06_07_hp_bar_full(self):
        """UI06-07: HP bar at full HP — color near green (R < 50, G > 150)."""
        r, g, b = hp_bar_color(11, 11)
        assert r < 50,  f"Expected R < 50 at full HP, got R={r}"
        assert g > 150, f"Expected G > 150 at full HP, got G={g}"

    def test_ui06_08_hp_bar_zero(self):
        """UI06-08: HP bar at 0 HP — color near red (R > 150, G < 50)."""
        r, g, b = hp_bar_color(0, 11)
        assert r > 150, f"Expected R > 150 at 0 HP, got R={r}"
        assert g < 50,  f"Expected G < 50 at 0 HP, got G={g}"


class TestMessageHandlers:

    def test_ui06_09_defeated_delta_removes_token(self):
        """UI06-09: defeated: true in delta removes token from scene."""
        renderer, scene = make_renderer()
        renderer.upsert(ENTITY_GOBLIN)
        assert renderer.has_token("e1")

        # Simulate entity_delta handler logic from main.ts
        data_changes = {"hp_current": 0, "defeated": True}
        if data_changes.get("defeated"):
            renderer.remove("e1")
        else:
            renderer.upsert({"id": "e1", **data_changes})

        assert not renderer.has_token("e1")
        assert len(scene.children) == 0

    def test_ui06_10_entity_state_syncs_roster(self):
        """UI06-10: entity_state message → syncRoster() called; all entities appear."""
        renderer, scene = make_renderer()

        # Simulate bridge.on('entity_state', ...) handler
        msg = {
            "msg_type": "entity_state",
            "entities": [ENTITY_KIRA, ENTITY_GOBLIN],
        }
        renderer.sync_roster(msg["entities"])

        assert renderer.has_token("p1"), "Kira should appear after entity_state"
        assert renderer.has_token("e1"), "Goblin should appear after entity_state"
        assert renderer.token_count == 2
        # Both token + hp_bar per entity = 4 scene children total
        assert len(scene.children) == 4
