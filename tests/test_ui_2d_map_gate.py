"""
Gate tests: UI-2D-MAP (MAP-01 through MAP-12)
Tests use Python string search. No browser required.
"""
import os

CLIENT2D = os.path.join(os.path.dirname(__file__), '..', 'client2d')


def read(filename):
    path = os.path.join(CLIENT2D, filename)
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


# ---------------------------------------------------------------------------
# MAP-01  map.js exists
# ---------------------------------------------------------------------------
def test_map_01_map_js_exists():
    path = os.path.join(CLIENT2D, 'map.js')
    assert os.path.isfile(path), "client2d/map.js does not exist"


# ---------------------------------------------------------------------------
# MAP-02  map.js contains scene-canvas
# ---------------------------------------------------------------------------
def test_map_02_map_js_has_scene_canvas():
    js = read('map.js')
    assert 'scene-canvas' in js, "map.js missing 'scene-canvas' element reference"


# ---------------------------------------------------------------------------
# MAP-03  map.js contains scene_set
# ---------------------------------------------------------------------------
def test_map_03_map_js_has_scene_set():
    js = read('map.js')
    assert 'scene_set' in js, "map.js missing 'scene_set' event handler"


# ---------------------------------------------------------------------------
# MAP-04  map.js contains token_add
# ---------------------------------------------------------------------------
def test_map_04_map_js_has_token_add():
    js = read('map.js')
    assert 'token_add' in js, "map.js missing 'token_add' event handler"


# ---------------------------------------------------------------------------
# MAP-05  map.js contains fog_reveal
# ---------------------------------------------------------------------------
def test_map_05_map_js_has_fog_reveal():
    js = read('map.js')
    assert 'fog_reveal' in js, "map.js missing 'fog_reveal' event handler"


# ---------------------------------------------------------------------------
# MAP-06  map.js contains aoe_add
# ---------------------------------------------------------------------------
def test_map_06_map_js_has_aoe_add():
    js = read('map.js')
    assert 'aoe_add' in js, "map.js missing 'aoe_add' event handler"


# ---------------------------------------------------------------------------
# MAP-07  map.js contains ResizeObserver
# ---------------------------------------------------------------------------
def test_map_07_map_js_has_resize_observer():
    js = read('map.js')
    assert 'ResizeObserver' in js, "map.js missing ResizeObserver"


# ---------------------------------------------------------------------------
# MAP-08  map.js contains FACTION_COLOR
# ---------------------------------------------------------------------------
def test_map_08_map_js_has_faction_color():
    js = read('map.js')
    assert 'FACTION_COLOR' in js, "map.js missing FACTION_COLOR constant"


# ---------------------------------------------------------------------------
# MAP-09  index.html contains scene-canvas
# ---------------------------------------------------------------------------
def test_map_09_index_html_has_scene_canvas():
    html = read('index.html')
    assert 'scene-canvas' in html, "index.html missing scene-canvas element"


# ---------------------------------------------------------------------------
# MAP-10  index.html contains map.js
# ---------------------------------------------------------------------------
def test_map_10_index_html_has_map_js():
    html = read('index.html')
    assert 'map.js' in html, "index.html missing map.js script tag"


# ---------------------------------------------------------------------------
# MAP-11  index.html contains scene-img-a
# ---------------------------------------------------------------------------
def test_map_11_index_html_has_scene_img_a():
    html = read('index.html')
    assert 'scene-img-a' in html, "index.html missing scene-img-a image element"


# ---------------------------------------------------------------------------
# MAP-12  style.css contains scene-canvas
# ---------------------------------------------------------------------------
def test_map_12_css_has_scene_canvas():
    css = read('style.css')
    assert 'scene-canvas' in css, "style.css missing #scene-canvas rule"
