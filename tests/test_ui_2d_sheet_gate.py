"""
Gate tests: UI-2D-SHEET (SHEET-01 through SHEET-10)
Tests use Python string search. No browser required.
"""
import os

CLIENT2D = os.path.join(os.path.dirname(__file__), '..', 'client2d')


def read(filename):
    path = os.path.join(CLIENT2D, filename)
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


# ---------------------------------------------------------------------------
# SHEET-01  sheet.js exists
# ---------------------------------------------------------------------------
def test_sheet_01_sheet_js_exists():
    path = os.path.join(CLIENT2D, 'sheet.js')
    assert os.path.isfile(path), "client2d/sheet.js does not exist"


# ---------------------------------------------------------------------------
# SHEET-02  sheet.js contains character_state
# ---------------------------------------------------------------------------
def test_sheet_02_sheet_js_has_character_state():
    js = read('sheet.js')
    assert 'character_state' in js, "sheet.js missing 'character_state' event reference"


# ---------------------------------------------------------------------------
# SHEET-03  sheet.js contains ability_check_declare
# ---------------------------------------------------------------------------
def test_sheet_03_sheet_js_has_ability_check_declare():
    js = read('sheet.js')
    assert 'ability_check_declare' in js, "sheet.js missing 'ability_check_declare' WS send"


# ---------------------------------------------------------------------------
# SHEET-04  sheet.js contains ability-block
# ---------------------------------------------------------------------------
def test_sheet_04_sheet_js_has_ability_block():
    js = read('sheet.js')
    assert 'ability-block' in js, "sheet.js missing 'ability-block' class reference"


# ---------------------------------------------------------------------------
# SHEET-05  sheet.js contains sheet-drawer
# ---------------------------------------------------------------------------
def test_sheet_05_sheet_js_has_sheet_drawer():
    js = read('sheet.js')
    assert 'sheet-drawer' in js, "sheet.js missing 'sheet-drawer' element reference"


# ---------------------------------------------------------------------------
# SHEET-06  sheet.js contains drawer-open
# ---------------------------------------------------------------------------
def test_sheet_06_sheet_js_has_drawer_open():
    js = read('sheet.js')
    assert 'drawer-open' in js, "sheet.js missing 'drawer-open' class reference"


# ---------------------------------------------------------------------------
# SHEET-07  sheet.js contains MutationObserver
# ---------------------------------------------------------------------------
def test_sheet_07_sheet_js_has_mutation_observer():
    js = read('sheet.js')
    assert 'MutationObserver' in js, "sheet.js missing MutationObserver"


# ---------------------------------------------------------------------------
# SHEET-08  index.html contains sheet-drawer
# ---------------------------------------------------------------------------
def test_sheet_08_index_html_has_sheet_drawer():
    html = read('index.html')
    assert 'sheet-drawer' in html, "index.html missing sheet-drawer element"


# ---------------------------------------------------------------------------
# SHEET-09  index.html contains sheet.js
# ---------------------------------------------------------------------------
def test_sheet_09_index_html_has_sheet_js():
    html = read('index.html')
    assert 'sheet.js' in html, "index.html missing sheet.js script tag"


# ---------------------------------------------------------------------------
# SHEET-10  style.css contains ability-block
# ---------------------------------------------------------------------------
def test_sheet_10_css_has_ability_block():
    css = read('style.css')
    assert 'ability-block' in css, "style.css missing .ability-block selector"
