"""
Gate tests: UI-2D-DM-PANEL (DMP-01 through DMP-10)
Tests use Python string search. No browser required.
"""
import os

CLIENT2D = os.path.join(os.path.dirname(__file__), '..', 'client2d')


def read(filename):
    path = os.path.join(CLIENT2D, filename)
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


# ---------------------------------------------------------------------------
# DMP-01  client2d/dm-panel.js exists
# ---------------------------------------------------------------------------
def test_dmp_01_dm_panel_js_exists():
    path = os.path.join(CLIENT2D, 'dm-panel.js')
    assert os.path.isfile(path), "client2d/dm-panel.js does not exist"


# ---------------------------------------------------------------------------
# DMP-02  dm-panel.js contains panel-active
# ---------------------------------------------------------------------------
def test_dmp_02_dm_panel_js_has_panel_active():
    js = read('dm-panel.js')
    assert 'panel-active' in js, "dm-panel.js missing 'panel-active' class reference"


# ---------------------------------------------------------------------------
# DMP-03  dm-panel.js contains transcript-active
# ---------------------------------------------------------------------------
def test_dmp_03_dm_panel_js_has_transcript_active():
    js = read('dm-panel.js')
    assert 'transcript-active' in js, "dm-panel.js missing 'transcript-active' class reference"


# ---------------------------------------------------------------------------
# DMP-04  dm-panel.js contains combat-active
# ---------------------------------------------------------------------------
def test_dmp_04_dm_panel_js_has_combat_active():
    js = read('dm-panel.js')
    assert 'combat-active' in js, "dm-panel.js missing 'combat-active' class reference"


# ---------------------------------------------------------------------------
# DMP-05  dm-panel.js contains speaking_start
# ---------------------------------------------------------------------------
def test_dmp_05_dm_panel_js_has_speaking_start():
    js = read('dm-panel.js')
    assert 'speaking_start' in js, "dm-panel.js missing 'speaking_start' event reference"


# ---------------------------------------------------------------------------
# DMP-06  dm-panel.js contains speaking_stop
# ---------------------------------------------------------------------------
def test_dmp_06_dm_panel_js_has_speaking_stop():
    js = read('dm-panel.js')
    assert 'speaking_stop' in js, "dm-panel.js missing 'speaking_stop' event reference"


# ---------------------------------------------------------------------------
# DMP-07  dm-panel.js contains narration
# ---------------------------------------------------------------------------
def test_dmp_07_dm_panel_js_has_narration():
    js = read('dm-panel.js')
    assert 'narration' in js, "dm-panel.js missing 'narration' event reference"


# ---------------------------------------------------------------------------
# DMP-08  index.html contains dm-panel.js
# ---------------------------------------------------------------------------
def test_dmp_08_index_html_has_dm_panel_js():
    html = read('index.html')
    assert 'dm-panel.js' in html, "index.html missing dm-panel.js script tag"


# ---------------------------------------------------------------------------
# DMP-09  index.html script order: orb.js before dm-panel.js before main.js
# ---------------------------------------------------------------------------
def test_dmp_09_script_load_order():
    html = read('index.html')
    orb_pos   = html.find('orb.js')
    dmp_pos   = html.find('dm-panel.js')
    main_pos  = html.find('main.js')
    assert orb_pos != -1,  "index.html missing orb.js"
    assert dmp_pos != -1,  "index.html missing dm-panel.js"
    assert main_pos != -1, "index.html missing main.js"
    assert orb_pos < dmp_pos, "index.html: orb.js must come before dm-panel.js"
    assert dmp_pos < main_pos, "index.html: dm-panel.js must come before main.js"


# ---------------------------------------------------------------------------
# DMP-10  style.css contains panel-active
# ---------------------------------------------------------------------------
def test_dmp_10_css_has_panel_active():
    css = read('style.css')
    assert 'panel-active' in css, "style.css missing panel-active selector"
