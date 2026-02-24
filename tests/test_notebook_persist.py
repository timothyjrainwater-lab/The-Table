"""Gate: Notebook Stroke Persistence (4 tests).

Tests verify the save/load/debounce/size-guard logic using a Python
simulation of the NotebookObject persistence methods.

WO: WO-UI-NOTEBOOK-PERSIST-001
"""
import json
import pytest


class MockLocalStorage:
    """Simulates browser localStorage."""

    def __init__(self):
        self._store = {}

    def setItem(self, key, value):
        self._store[key] = value

    def getItem(self, key):
        return self._store.get(key)

    def removeItem(self, key):
        self._store.pop(key, None)

    def __contains__(self, key):
        return key in self._store


class NotebookPersistSim:
    """Python simulation of NotebookObject persistence logic.

    Mirrors the TypeScript implementation in
    client/src/notebook-object.ts -- saveStrokes / loadStrokes.
    """

    SAVE_DEBOUNCE_MS = 2000
    MAX_STORAGE_BYTES = 500 * 1024  # 500 KB

    def __init__(self, session_id="test_session", storage=None):
        self._session_id = session_id
        self._storage = storage or MockLocalStorage()

    def _storage_key(self, section_id):
        return f"nb_strokes_{self._session_id}_{section_id}"

    def save_strokes_immediate(self, section_id, strokes):
        """Simulates the debounced save (without actual timer -- immediate for testing)."""
        key = self._storage_key(section_id)
        data = list(strokes)

        # Size guard: drop oldest strokes until payload fits within 500 KB
        json_str = json.dumps(data)
        while len(json_str.encode("utf-8")) > self.MAX_STORAGE_BYTES and len(data) > 0:
            data = data[1:]  # drop oldest
            json_str = json.dumps(data)

        self._storage.setItem(key, json_str)

    def load_strokes(self, section_id):
        key = self._storage_key(section_id)
        raw = self._storage.getItem(key)
        if not raw:
            return []
        try:
            return json.loads(raw)
        except Exception:
            return []

    def debounced_save(self, section_id, strokes, pending_dict):
        """Simulates debounce: records pending save, overwrites previous."""
        pending_dict[section_id] = list(strokes)


def make_stroke(n_points=5, color="#000000", width=2):
    return {
        "points": [{"x": i * 10, "y": i * 5} for i in range(n_points)],
        "color": color,
        "width": width,
    }


# ---------------------------------------------------------------------------
# NP-01: Save and load round-trip
# ---------------------------------------------------------------------------

def test_np01_save_load_roundtrip():
    """Strokes saved to localStorage can be loaded back identically."""
    storage = MockLocalStorage()
    nb = NotebookPersistSim(session_id="session_001", storage=storage)

    strokes = [make_stroke(5), make_stroke(3, "#ff0000", 3)]
    nb.save_strokes_immediate("notes", strokes)
    loaded = nb.load_strokes("notes")

    assert len(loaded) == 2, f"Expected 2 strokes, got {len(loaded)}"
    assert loaded[0]["color"] == "#000000"
    assert loaded[1]["color"] == "#ff0000"
    assert len(loaded[0]["points"]) == 5


# ---------------------------------------------------------------------------
# NP-02: Load returns empty list when no saved data exists
# ---------------------------------------------------------------------------

def test_np02_load_empty():
    """Loading from an empty store returns an empty list without error."""
    nb = NotebookPersistSim(session_id="empty_session")
    result = nb.load_strokes("notes")
    assert result == [], f"Expected [], got {result}"


# ---------------------------------------------------------------------------
# NP-03: Debounce -- rapid strokes only keep the last pending save
# ---------------------------------------------------------------------------

def test_np03_debounce():
    """Rapid successive save calls are coalesced; only the last value survives."""
    nb = NotebookPersistSim(session_id="session_003")
    pending = {}

    strokes_a = [make_stroke(3)]
    strokes_b = [make_stroke(3), make_stroke(4)]
    strokes_c = [make_stroke(3), make_stroke(4), make_stroke(2)]

    # Rapid calls -- each overwrites the previous pending entry
    nb.debounced_save("notes", strokes_a, pending)
    nb.debounced_save("notes", strokes_b, pending)
    nb.debounced_save("notes", strokes_c, pending)

    # Only the last call's data should be in pending
    assert len(pending.get("notes", [])) == 3, (
        f"Expected 3 strokes in pending (last call wins), "
        f"got {len(pending.get('notes', []))}"
    )


# ---------------------------------------------------------------------------
# NP-04: Size guard -- strokes exceeding 500 KB get oldest dropped
# ---------------------------------------------------------------------------

def test_np04_size_guard():
    """When persisted payload exceeds 500 KB, oldest strokes are dropped."""
    nb = NotebookPersistSim(session_id="session_004")

    # 240 strokes x 100 points each ~ 520+ KB (each stroke ~2.2 KB serialised)
    big_strokes = [make_stroke(100) for _ in range(240)]

    # Verify the raw payload exceeds 500 KB before the guard runs
    raw_json = json.dumps(big_strokes)
    assert len(raw_json.encode("utf-8")) > 500 * 1024, (
        "Test setup error: strokes should exceed 500 KB"
    )

    nb.save_strokes_immediate("notes", big_strokes)
    loaded = nb.load_strokes("notes")

    # Persisted payload must fit within 500 KB
    loaded_json = json.dumps(loaded)
    assert len(loaded_json.encode("utf-8")) <= 500 * 1024, (
        f"Loaded strokes exceed 500 KB: {len(loaded_json.encode('utf-8'))} bytes"
    )

    # Some strokes must have been dropped
    assert len(loaded) < len(big_strokes), (
        "Expected some strokes to be dropped by the size guard"
    )

    # Most recent strokes must be preserved (oldest are dropped first)
    if len(loaded) > 0:
        assert loaded[-1] == big_strokes[-1], (
            "Most recent stroke should be preserved after size guard"
        )
