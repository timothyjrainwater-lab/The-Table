"""
Gate tests: UI-2D-NOTEBOOK (NB-01 through NB-10)
Tests use Python string search. No browser required.
"""
import os

CLIENT2D = os.path.join(os.path.dirname(__file__), '..', 'client2d')


def read(filename):
    path = os.path.join(CLIENT2D, filename)
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


# ---------------------------------------------------------------------------
# NB-01  notebook.js exists
# ---------------------------------------------------------------------------
def test_nb_01_notebook_js_exists():
    path = os.path.join(CLIENT2D, 'notebook.js')
    assert os.path.isfile(path), "client2d/notebook.js does not exist"


# ---------------------------------------------------------------------------
# NB-02  notebook.js contains narration
# ---------------------------------------------------------------------------
def test_nb_02_notebook_js_has_narration():
    js = read('notebook.js')
    assert 'narration' in js, "notebook.js missing 'narration' event reference"


# ---------------------------------------------------------------------------
# NB-03  notebook.js contains bestiary_entry
# ---------------------------------------------------------------------------
def test_nb_03_notebook_js_has_bestiary_entry():
    js = read('notebook.js')
    assert 'bestiary_entry' in js, "notebook.js missing 'bestiary_entry' event reference"


# ---------------------------------------------------------------------------
# NB-04  notebook.js contains nb-tab-btn
# ---------------------------------------------------------------------------
def test_nb_04_notebook_js_has_nb_tab_btn():
    js = read('notebook.js')
    assert 'nb-tab-btn' in js, "notebook.js missing 'nb-tab-btn' class reference"


# ---------------------------------------------------------------------------
# NB-05  notebook.js contains nb-draw-locked
# ---------------------------------------------------------------------------
def test_nb_05_notebook_js_has_nb_draw_locked():
    js = read('notebook.js')
    assert 'nb-draw-locked' in js, "notebook.js missing 'nb-draw-locked' class reference"


# ---------------------------------------------------------------------------
# NB-06  notebook.js contains drawer-open
# ---------------------------------------------------------------------------
def test_nb_06_notebook_js_has_drawer_open():
    js = read('notebook.js')
    assert 'drawer-open' in js, "notebook.js missing 'drawer-open' class reference"


# ---------------------------------------------------------------------------
# NB-07  notebook.js contains MAX_TRANSCRIPT
# ---------------------------------------------------------------------------
def test_nb_07_notebook_js_has_max_transcript():
    js = read('notebook.js')
    assert 'MAX_TRANSCRIPT' in js, "notebook.js missing MAX_TRANSCRIPT constant"


# ---------------------------------------------------------------------------
# NB-08  index.html contains notebook-drawer
# ---------------------------------------------------------------------------
def test_nb_08_index_html_has_notebook_drawer():
    html = read('index.html')
    assert 'notebook-drawer' in html, "index.html missing notebook-drawer element"


# ---------------------------------------------------------------------------
# NB-09  index.html contains notebook.js
# ---------------------------------------------------------------------------
def test_nb_09_index_html_has_notebook_js():
    html = read('index.html')
    assert 'notebook.js' in html, "index.html missing notebook.js script tag"


# ---------------------------------------------------------------------------
# NB-10  style.css contains nb-tab-btn
# ---------------------------------------------------------------------------
def test_nb_10_css_has_nb_tab_btn():
    css = read('style.css')
    assert 'nb-tab-btn' in css, "style.css missing .nb-tab-btn selector"
