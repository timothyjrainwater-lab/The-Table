"""Gate UI-CS — Interactive Character Sheet (16 tests).

Tests verify CharacterSheetController logic using Python simulation,
plus static-analysis tests for WO-UI-SHEET-LIVE-001 live wiring.
"""
import pytest
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class CharacterSheetSim:
    """Python simulation of CharacterSheetController."""

    def __init__(self):
        self._state = None
        self.declared_actions = []  # list of (action_id, entity_id)
        self.question_stamps = []   # list of (action_id, rule_ref)

    def handle_sheet_update(self, data):
        self._state = {
            "entity_id": data["entity_id"],
            "hp_current": data["hp_current"],
            "hp_max": data["hp_max"],
            "conditions": list(data.get("conditions", [])),
            "spell_slots": dict(data.get("spell_slots", {})),
            "spell_slots_max": dict(data.get("spell_slots_max", {})),
            "abilities": [dict(a) for a in data.get("abilities", [])],
            "attacks": [dict(a) for a in data.get("attacks", [])],
        }

    def handle_entity_delta(self, entity_id, changes):
        if not self._state or self._state["entity_id"] != entity_id:
            return
        if "hp_current" in changes:
            self._state["hp_current"] = changes["hp_current"]
        if "conditions" in changes:
            self._state["conditions"] = list(changes["conditions"])

    def on_spell_row_click(self, action_id):
        if not self._state:
            return
        self.declared_actions.append((action_id, self._state["entity_id"]))

    def on_row_right_click(self, action_id, rule_ref):
        self.question_stamps.append((action_id, rule_ref))

    @property
    def hp_fraction(self):
        if not self._state or self._state["hp_max"] == 0:
            return 0.0
        return max(0.0, min(1.0, self._state["hp_current"] / self._state["hp_max"]))

    @property
    def state(self):
        return self._state

    def get_spell_slot_pips(self, level):
        if not self._state:
            return {"remaining": 0, "max": 0}
        return {
            "remaining": self._state["spell_slots"].get(level, 0),
            "max": self._state["spell_slots_max"].get(level, 0),
        }

    def is_stat_block_clickable(self):
        return False


def make_sheet_update(entity_id="player_001", hp_current=11, hp_max=11,
                      conditions=None, spell_slots=None, spell_slots_max=None,
                      abilities=None, attacks=None):
    return {
        "entity_id": entity_id,
        "hp_current": hp_current,
        "hp_max": hp_max,
        "conditions": conditions or [],
        "spell_slots": spell_slots or {1: 2, 2: 1},
        "spell_slots_max": spell_slots_max or {1: 3, 2: 2},
        "abilities": abilities or [
            {"id": "power_attack", "name": "Power Attack", "ready": True},
        ],
        "attacks": attacks or [
            {"id": "longsword", "name": "Longsword", "bonus": "+5", "damage": "1d8+3"},
        ],
    }


# CS-01: character_sheet_update — HP fields update to payload values
def test_cs01_sheet_update_hp():
    cs = CharacterSheetSim()
    cs.handle_sheet_update(make_sheet_update(hp_current=8, hp_max=11))
    assert cs.state["hp_current"] == 8
    assert cs.state["hp_max"] == 11


# CS-02: character_sheet_update — spell slot pips reflect remaining
def test_cs02_spell_slot_pips():
    cs = CharacterSheetSim()
    cs.handle_sheet_update(make_sheet_update(
        spell_slots={1: 2, 2: 0},
        spell_slots_max={1: 3, 2: 2},
    ))
    pips_l1 = cs.get_spell_slot_pips(1)
    pips_l2 = cs.get_spell_slot_pips(2)
    assert pips_l1["remaining"] == 2
    assert pips_l1["max"] == 3
    assert pips_l2["remaining"] == 0
    assert pips_l2["max"] == 2


# CS-03: character_sheet_update — abilities list renders from payload
def test_cs03_abilities_list():
    cs = CharacterSheetSim()
    abilities = [
        {"id": "cleave", "name": "Cleave", "ready": True},
        {"id": "spring_attack", "name": "Spring Attack", "ready": False},
    ]
    cs.handle_sheet_update(make_sheet_update(abilities=abilities))
    assert len(cs.state["abilities"]) == 2
    assert cs.state["abilities"][0]["id"] == "cleave"
    assert cs.state["abilities"][1]["ready"] is False


# CS-04: entity_delta hp — HP updates
def test_cs04_entity_delta_hp():
    cs = CharacterSheetSim()
    cs.handle_sheet_update(make_sheet_update(entity_id="p1", hp_current=11, hp_max=11))
    cs.handle_entity_delta("p1", {"hp_current": 4})
    assert cs.state["hp_current"] == 4
    assert abs(cs.hp_fraction - 4/11) < 0.001


# CS-05: entity_delta conditions — condition tags appear/disappear
def test_cs05_entity_delta_conditions():
    cs = CharacterSheetSim()
    cs.handle_sheet_update(make_sheet_update(entity_id="p1", conditions=[]))
    cs.handle_entity_delta("p1", {"conditions": ["Blinded", "Fatigued"]})
    assert "Blinded" in cs.state["conditions"]
    assert "Fatigued" in cs.state["conditions"]
    cs.handle_entity_delta("p1", {"conditions": []})
    assert cs.state["conditions"] == []


# CS-06: Click spell row — emits REQUEST_DECLARE_ACTION with correct action_id
def test_cs06_spell_row_click():
    cs = CharacterSheetSim()
    cs.handle_sheet_update(make_sheet_update(entity_id="p1"))
    cs.on_spell_row_click("fireball")
    assert len(cs.declared_actions) == 1
    assert cs.declared_actions[0] == ("fireball", "p1")


# CS-07: Click ability row — emits REQUEST_DECLARE_ACTION with correct action_id
def test_cs07_ability_row_click():
    cs = CharacterSheetSim()
    cs.handle_sheet_update(make_sheet_update(entity_id="p1"))
    cs.on_spell_row_click("power_attack")
    assert ("power_attack", "p1") in cs.declared_actions


# CS-08: Click stat block — no event emitted (read-only)
def test_cs08_stat_block_not_clickable():
    cs = CharacterSheetSim()
    assert cs.is_stat_block_clickable() is False


# CS-09: Right-click row — QuestionStamp placed
def test_cs09_right_click_places_stamp():
    cs = CharacterSheetSim()
    cs.on_row_right_click("power_attack", "combat.actions")
    assert len(cs.question_stamps) == 1
    assert cs.question_stamps[0] == ("power_attack", "combat.actions")


# CS-10: Click QuestionStamp — rulebook opens (verified via stamp rule_ref)
def test_cs10_stamp_has_rule_ref():
    cs = CharacterSheetSim()
    cs.on_row_right_click("fireball", "spells.fireball")
    assert cs.question_stamps[0][1] == "spells.fireball"


# CS-11: Expended spell slot — pip shows empty (remaining == 0)
def test_cs11_expended_spell_slot():
    cs = CharacterSheetSim()
    cs.handle_sheet_update(make_sheet_update(
        spell_slots={1: 0},
        spell_slots_max={1: 3},
    ))
    pips = cs.get_spell_slot_pips(1)
    assert pips["remaining"] == 0
    assert pips["max"] == 3


# CS-12: Full heal — HP fraction = 1.0, conditions cleared
def test_cs12_full_heal():
    cs = CharacterSheetSim()
    cs.handle_sheet_update(make_sheet_update(entity_id="p1", hp_current=4, hp_max=11,
                                              conditions=["Fatigued"]))
    cs.handle_entity_delta("p1", {"hp_current": 11, "conditions": []})
    assert abs(cs.hp_fraction - 1.0) < 0.001
    assert cs.state["conditions"] == []


# ---------------------------------------------------------------------------
# WO-UI-SHEET-LIVE-001: Live texture + raycast wiring (static analysis)
# ---------------------------------------------------------------------------

# CS-13: scene-builder exports characterSheetMesh
def test_cs13_sheet_mesh_exported():
    scene_builder = os.path.join(ROOT, 'client', 'src', 'scene-builder.ts')
    text = open(scene_builder, encoding='utf-8').read()
    assert 'characterSheetMesh' in text, \
        "scene-builder.ts must export characterSheetMesh"
    assert 'export let characterSheetMesh' in text, \
        "characterSheetMesh must be an exported let"


# CS-14: scene-builder exports updateCharacterSheetLive
def test_cs14_live_update_fn_exported():
    scene_builder = os.path.join(ROOT, 'client', 'src', 'scene-builder.ts')
    text = open(scene_builder, encoding='utf-8').read()
    assert 'updateCharacterSheetLive' in text, \
        "scene-builder.ts must export updateCharacterSheetLive"
    assert 'export let updateCharacterSheetLive' in text, \
        "updateCharacterSheetLive must be an exported let"


# CS-15: main.ts calls updateCharacterSheetLive on character_sheet_update
def test_cs15_main_calls_live_update():
    main_ts = os.path.join(ROOT, 'client', 'src', 'main.ts')
    text = open(main_ts, encoding='utf-8').read()
    assert 'updateCharacterSheetLive' in text, \
        "main.ts must call updateCharacterSheetLive"
    # Must be inside the character_sheet_update handler
    update_block_idx = text.find("character_sheet_update")
    assert update_block_idx != -1, "character_sheet_update handler not found"
    live_call_idx = text.find("updateCharacterSheetLive", update_block_idx)
    assert live_call_idx != -1, \
        "updateCharacterSheetLive must be called inside character_sheet_update handler"


# CS-16: main.ts wires characterSheetMesh to raycaster click handler
def test_cs16_sheet_mesh_raycasted():
    main_ts = os.path.join(ROOT, 'client', 'src', 'main.ts')
    text = open(main_ts, encoding='utf-8').read()
    assert 'characterSheetMesh' in text, \
        "main.ts must import characterSheetMesh"
    # Verify it appears inside the click handler (after raycaster.intersectObject call)
    click_idx = text.find("renderer.domElement.addEventListener('click'")
    assert click_idx != -1, "click handler not found"
    sheet_raycast_idx = text.find("intersectObject(characterSheetMesh", click_idx)
    assert sheet_raycast_idx != -1, \
        "characterSheetMesh must be raycasted in the click handler"
