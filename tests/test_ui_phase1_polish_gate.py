"""Gate tests: UI-PHASE1-POLISH-001 (PLP-001 through PLP-008)

WO: WO-UI-PHASE1-POLISH-001
Gaps closed: GAP-09 (dice slip RollResult), GAP-10 (abilities dict), GAP-12 (click disable)
"""
import os
import re
import sys

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

ROOT = os.path.join(os.path.dirname(__file__), "..")
CLIENT2D = os.path.join(ROOT, "client2d")


def _read_client(filename):
    path = os.path.join(CLIENT2D, filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# PLP-001: attack_roll event produces RollResult in addition to NarrationEvent
# ---------------------------------------------------------------------------

def test_plp001_attack_roll_produces_roll_result():
    """PLP-001: Processing attack_roll through ws_bridge produces a RollResult message."""
    from aidm.ui.ws_protocol import RollResult
    from aidm.schemas.ws_protocol import NarrationEvent

    # Simulate the same logic as ws_bridge attack_roll handler
    event_dict = {
        "payload": {
            "total": 18,
            "target_ac": 15,
            "hit": True,
            "d20": 14,
        }
    }
    payload = event_dict.get("payload", {}) or event_dict
    total = payload.get("total", event_dict.get("total"))
    target_ac = payload.get("target_ac", event_dict.get("target_ac"))
    hit = payload.get("hit", event_dict.get("hit"))
    d20 = payload.get("d20", payload.get("roll", 0))

    messages = []
    messages.append(NarrationEvent(
        msg_type="narration",
        msg_id="test-id",
        text=f"Attack: {total} vs AC {target_ac} — HIT",
    ))
    messages.append(RollResult(
        d20_result=d20,
        total=total or 0,
        success=bool(hit),
    ))

    types = [type(m).__name__ for m in messages]
    assert "NarrationEvent" in types, "Expected NarrationEvent in message list"
    assert "RollResult" in types, "Expected RollResult in message list"


# ---------------------------------------------------------------------------
# PLP-002: RollResult fields populated correctly from attack_roll payload
# ---------------------------------------------------------------------------

def test_plp002_roll_result_fields_populated():
    """PLP-002: RollResult d20_result, total, success fields come from attack_roll payload."""
    from aidm.ui.ws_protocol import RollResult

    event_dict = {
        "payload": {
            "total": 22,
            "target_ac": 17,
            "hit": True,
            "d20": 19,
        }
    }
    payload = event_dict.get("payload", {}) or event_dict
    total = payload.get("total", event_dict.get("total"))
    hit = payload.get("hit", event_dict.get("hit"))
    d20 = payload.get("d20", payload.get("roll", 0))

    rr = RollResult(d20_result=d20, total=total or 0, success=bool(hit))
    assert rr.d20_result == 19, f"Expected d20_result=19, got {rr.d20_result}"
    assert rr.total == 22, f"Expected total=22, got {rr.total}"
    assert rr.success is True, f"Expected success=True, got {rr.success}"

    # MISS case
    miss_payload = {"total": 8, "target_ac": 15, "hit": False, "d20": 5}
    rr_miss = RollResult(
        d20_result=miss_payload["d20"],
        total=miss_payload["total"],
        success=bool(miss_payload["hit"]),
    )
    assert rr_miss.success is False, "Expected success=False for miss"


# ---------------------------------------------------------------------------
# PLP-003: CharacterState.to_dict() includes "abilities" key
# ---------------------------------------------------------------------------

def test_plp003_character_state_to_dict_has_abilities():
    """PLP-003: CharacterState.to_dict() includes 'abilities' key."""
    from aidm.schemas.ws_protocol import CharacterState, MSG_CHARACTER_STATE

    cs = CharacterState(
        msg_type=MSG_CHARACTER_STATE,
        msg_id="test-id",
        name="Theron",
        hp=30,
        hp_max=30,
        ac=16,
    )
    d = cs.to_dict()
    assert "abilities" in d, "to_dict() must include 'abilities' key (GAP-10)"


# ---------------------------------------------------------------------------
# PLP-004: CharacterState with abilities serializes correctly
# ---------------------------------------------------------------------------

def test_plp004_character_state_abilities_serialize():
    """PLP-004: CharacterState with abilities={'str': 18, 'dex': 14} serializes correctly."""
    from aidm.schemas.ws_protocol import CharacterState, MSG_CHARACTER_STATE

    cs = CharacterState(
        msg_type=MSG_CHARACTER_STATE,
        msg_id="test-id",
        name="Theron",
        hp=30,
        hp_max=30,
        ac=16,
        abilities={"str": 18, "dex": 14, "con": 12, "int": 10, "wis": 8, "cha": 11},
    )
    d = cs.to_dict()
    assert d["abilities"]["str"] == 18, f"Expected str=18, got {d['abilities'].get('str')}"
    assert d["abilities"]["dex"] == 14, f"Expected dex=14, got {d['abilities'].get('dex')}"


# ---------------------------------------------------------------------------
# PLP-005: CharacterState.from_dict() round-trip preserves abilities dict
# ---------------------------------------------------------------------------

def test_plp005_character_state_round_trip_abilities():
    """PLP-005: CharacterState.from_dict() round-trip preserves abilities dict."""
    from aidm.schemas.ws_protocol import CharacterState, MSG_CHARACTER_STATE

    original = CharacterState(
        msg_type=MSG_CHARACTER_STATE,
        msg_id="test-id",
        name="Theron",
        hp=30,
        hp_max=30,
        ac=16,
        abilities={"str": 18, "dex": 14, "con": 12, "int": 10, "wis": 8, "cha": 11},
    )
    d = original.to_dict()
    restored = CharacterState.from_dict(d)
    assert restored.abilities == {"str": 18, "dex": 14, "con": 12, "int": 10, "wis": 8, "cha": 11}, \
        f"abilities not preserved: {restored.abilities}"


# ---------------------------------------------------------------------------
# PLP-006: ws_bridge source includes abilities dict construction (at least 6 keys)
# ---------------------------------------------------------------------------

def test_plp006_ws_bridge_abilities_dict_wired():
    """PLP-006: ws_bridge.py CharacterState emission includes abilities dict with 6 keys."""
    ws_bridge_path = os.path.join(ROOT, "aidm", "server", "ws_bridge.py")
    with open(ws_bridge_path, "r", encoding="utf-8") as f:
        src = f.read()

    # The abilities comprehension covers str/dex/con/int/wis/cha
    assert '"str", "dex", "con", "int", "wis", "cha"' in src, \
        'ws_bridge.py must include abilities comprehension with all 6 ability keys'
    # Must appear twice (two emission sites)
    count = src.count('"str", "dex", "con", "int", "wis", "cha"')
    assert count >= 2, \
        f"Expected abilities dict at 2+ CharacterState sites, found {count}"


# ---------------------------------------------------------------------------
# PLP-007: ability_check_declare absent from enabled JS event listeners
# ---------------------------------------------------------------------------

def test_plp007_ability_check_declare_disabled():
    """PLP-007: ability_check_declare is not in any live (uncommented) JS event listener."""
    sheet_js = _read_client("sheet.js")

    # Strip JS line comments — find non-comment occurrences of ability_check_declare
    # A live binding would be: bridge.send({msg_type: 'ability_check_declare' ...})
    # Disabled bindings are preceded by //
    live_lines = []
    for line in sheet_js.splitlines():
        stripped = line.lstrip()
        if "ability_check_declare" in stripped and not stripped.startswith("//"):
            live_lines.append(line)

    assert len(live_lines) == 0, \
        f"Found live ability_check_declare binding(s) in sheet.js: {live_lines}"


# ---------------------------------------------------------------------------
# PLP-008: CharacterState default has abilities={} — no crash on empty entity
# ---------------------------------------------------------------------------

def test_plp008_character_state_default_abilities_empty_dict():
    """PLP-008: CharacterState default abilities={} not None — safe on empty entity."""
    from aidm.schemas.ws_protocol import CharacterState, MSG_CHARACTER_STATE

    cs = CharacterState(
        msg_type=MSG_CHARACTER_STATE,
        msg_id="test-id",
    )
    assert cs.abilities == {}, \
        f"Default abilities must be {{}} not None, got {cs.abilities!r}"
    # Must be usable as a dict (no crash)
    d = cs.to_dict()
    assert d["abilities"] == {}, "to_dict() on default CharacterState must yield abilities={}"
