"""
Gate tests: UI-2D-FOUNDATION (2D-01 through 2D-10)
Tests use Python html.parser + string search. No browser required.
"""
import os
import re
from html.parser import HTMLParser

CLIENT2D = os.path.join(os.path.dirname(__file__), '..', 'client2d')


def read(filename):
    path = os.path.join(CLIENT2D, filename)
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


class HTMLValidator(HTMLParser):
    """Minimal validator: parses without raising — tracks open/close tags."""
    def __init__(self):
        super().__init__()
        self.errors = []
        self.parsed = True

    def handle_error(self, message):
        self.errors.append(message)
        self.parsed = False


# ---------------------------------------------------------------------------
# 2D-01  index.html exists and parses as valid HTML
# ---------------------------------------------------------------------------
def test_2d_01_index_html_exists_and_parses():
    path = os.path.join(CLIENT2D, 'index.html')
    assert os.path.isfile(path), "client2d/index.html does not exist"
    content = read('index.html')
    assert '<!DOCTYPE html>' in content or '<!doctype html>' in content.lower(), \
        "index.html missing DOCTYPE"
    validator = HTMLValidator()
    validator.feed(content)
    assert validator.parsed, f"index.html parse errors: {validator.errors}"


# ---------------------------------------------------------------------------
# 2D-02  style.css, ws.js, main.js all exist
# ---------------------------------------------------------------------------
def test_2d_02_required_files_exist():
    for fname in ('style.css', 'ws.js', 'main.js'):
        path = os.path.join(CLIENT2D, fname)
        assert os.path.isfile(path), f"client2d/{fname} does not exist"


# ---------------------------------------------------------------------------
# 2D-03  No Three.js references anywhere in client2d/
# ---------------------------------------------------------------------------
def test_2d_03_no_threejs_references():
    forbidden = ['THREE', 'WebGLRenderer', 'PerspectiveCamera']
    for fname in ('index.html', 'style.css', 'ws.js', 'main.js'):
        content = read(fname)
        for term in forbidden:
            assert term not in content, \
                f"Three.js reference '{term}' found in client2d/{fname}"


# ---------------------------------------------------------------------------
# 2D-04  No npm/node references in client2d/
# ---------------------------------------------------------------------------
def test_2d_04_no_npm_node_references():
    forbidden = ['require(', 'node_modules', 'import from']
    for fname in ('index.html', 'style.css', 'ws.js', 'main.js'):
        content = read(fname)
        for term in forbidden:
            assert term not in content, \
                f"npm/node reference '{term}' found in client2d/{fname}"


# ---------------------------------------------------------------------------
# 2D-05  style.css contains all required palette variables
# ---------------------------------------------------------------------------
def test_2d_05_palette_variables():
    css = read('style.css')
    required_vars = [
        '--walnut-mid',
        '--parchment',
        '--amber-idle',
        '--amber-speak',
        '--wax-red',
    ]
    for var in required_vars:
        assert var in css, f"Palette variable '{var}' missing from style.css"


# ---------------------------------------------------------------------------
# 2D-06  index.html contains core structural IDs
#        Updated by WO-UI-2D-RELAYOUT-001: dm-zone/work-zone/dice-zone removed.
#        Updated by scene-surface rename: vault-zone → scene-surface.
#        Now checks the surviving IDs that span both FOUNDATION and RELAYOUT.
# ---------------------------------------------------------------------------
def test_2d_06_zone_ids_present():
    html = read('index.html')
    required_ids = [
        'scene-surface',
        'shelf-zone',
        'player-input',
        'send-btn',
        'ws-status',
    ]
    for zone_id in required_ids:
        assert zone_id in html, f"Zone ID '{zone_id}' missing from index.html"


# ---------------------------------------------------------------------------
# 2D-07  style.css contains all four posture classes
# ---------------------------------------------------------------------------
def test_2d_07_posture_classes():
    css = read('style.css')
    required_classes = [
        'posture-standard',
        'posture-lean',
        'posture-down',
        'posture-dice',
    ]
    for cls in required_classes:
        assert cls in css, f"Posture class '{cls}' missing from style.css"


# ---------------------------------------------------------------------------
# 2D-08  main.js contains keydown handler and keys '1' '2' '3' '4'
# ---------------------------------------------------------------------------
def test_2d_08_keydown_handler_with_posture_keys():
    js = read('main.js')
    assert 'keydown' in js, "main.js missing 'keydown' event listener"
    for key in ("'1'", "'2'", "'3'", "'4'"):
        assert key in js, f"main.js missing posture key {key}"


# ---------------------------------------------------------------------------
# 2D-09  main.js contains speaking_start and speaking_stop handlers
# ---------------------------------------------------------------------------
def test_2d_09_speaking_handlers():
    js = read('main.js')
    assert 'speaking_start' in js, "main.js missing 'speaking_start' handler"
    assert 'speaking_stop' in js, "main.js missing 'speaking_stop' handler"
    # Verify orb class manipulation is present
    assert 'speaking' in js, "main.js missing orb 'speaking' class manipulation"


# ---------------------------------------------------------------------------
# 2D-10  ws.js contains WS URL and player_input send on submit
# ---------------------------------------------------------------------------
def test_2d_10_ws_url_and_player_input():
    js = read('ws.js')
    assert 'ws://localhost:8765/ws' in js, \
        "ws.js missing WebSocket URL 'ws://localhost:8765/ws'"
    main_js = read('main.js')
    assert 'player_input' in main_js, \
        "main.js missing 'player_input' msg_type in send call"
