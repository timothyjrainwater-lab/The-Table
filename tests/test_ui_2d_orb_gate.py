"""
Gate tests: UI-2D-ORB (ORB-01 through ORB-12)
Tests use Python string search. No browser required.
"""
import os

CLIENT2D = os.path.join(os.path.dirname(__file__), '..', 'client2d')


def read(filename):
    path = os.path.join(CLIENT2D, filename)
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


# ---------------------------------------------------------------------------
# ORB-01  client2d/orb.js exists
# ---------------------------------------------------------------------------
def test_orb_01_orb_js_exists():
    path = os.path.join(CLIENT2D, 'orb.js')
    assert os.path.isfile(path), "client2d/orb.js does not exist"


# ---------------------------------------------------------------------------
# ORB-02  index.html contains <script src="orb.js">
# ---------------------------------------------------------------------------
def test_orb_02_index_html_has_orb_script():
    html = read('index.html')
    assert 'src="orb.js"' in html, \
        "index.html missing <script src=\"orb.js\"> tag"


# ---------------------------------------------------------------------------
# ORB-03  orb.js references speaking_start
# ---------------------------------------------------------------------------
def test_orb_03_orb_js_has_speaking_start():
    js = read('orb.js')
    assert 'speaking_start' in js, \
        "orb.js missing 'speaking_start' event reference"


# ---------------------------------------------------------------------------
# ORB-04  orb.js references speaking_stop
# ---------------------------------------------------------------------------
def test_orb_04_orb_js_has_speaking_stop():
    js = read('orb.js')
    assert 'speaking_stop' in js, \
        "orb.js missing 'speaking_stop' event reference"


# ---------------------------------------------------------------------------
# ORB-05  orb.js references speaker-portrait
# ---------------------------------------------------------------------------
def test_orb_05_orb_js_has_speaker_portrait():
    js = read('orb.js')
    assert 'speaker-portrait' in js, \
        "orb.js missing 'speaker-portrait' element reference"


# ---------------------------------------------------------------------------
# ORB-06  orb.js references speaker-beats
# ---------------------------------------------------------------------------
def test_orb_06_orb_js_has_speaker_beats():
    js = read('orb.js')
    assert 'speaker-beats' in js, \
        "orb.js missing 'speaker-beats' element reference"


# ---------------------------------------------------------------------------
# ORB-07  orb.js contains IDLE_FILTER or brightness(0.5) — idle filter defined
# ---------------------------------------------------------------------------
def test_orb_07_orb_js_has_idle_filter():
    js = read('orb.js')
    assert 'IDLE_FILTER' in js or 'brightness(0.5)' in js, \
        "orb.js missing IDLE_FILTER constant or brightness(0.5) value"


# ---------------------------------------------------------------------------
# ORB-08  orb.js contains MAX_BEATS or value 8 — DOM cap present
# ---------------------------------------------------------------------------
def test_orb_08_orb_js_has_max_beats():
    js = read('orb.js')
    assert 'MAX_BEATS' in js or '> 8' in js or '=== 8' in js or '== 8' in js, \
        "orb.js missing MAX_BEATS constant or beat DOM cap logic"


# ---------------------------------------------------------------------------
# ORB-09  orb.js does NOT add click or mousedown event listener on portrait
#         (crest non-interactive — BD-09)
# ---------------------------------------------------------------------------
def test_orb_09_orb_js_no_click_handler():
    js = read('orb.js')
    # Must not have any addEventListener for click or mousedown
    assert 'addEventListener(\'click\'' not in js, \
        "orb.js contains click event listener — portrait must be non-interactive"
    assert 'addEventListener("click"' not in js, \
        "orb.js contains click event listener — portrait must be non-interactive"
    assert 'addEventListener(\'mousedown\'' not in js, \
        "orb.js contains mousedown event listener — portrait must be non-interactive"
    assert 'addEventListener("mousedown"' not in js, \
        "orb.js contains mousedown event listener — portrait must be non-interactive"


# ---------------------------------------------------------------------------
# ORB-10  style.css contains .beat selector
# ---------------------------------------------------------------------------
def test_orb_10_css_has_beat_selector():
    css = read('style.css')
    assert '.beat' in css, \
        "style.css missing .beat selector"


# ---------------------------------------------------------------------------
# ORB-11  style.css contains nth-last-child — beat aging present
# ---------------------------------------------------------------------------
def test_orb_11_css_has_nth_last_child():
    css = read('style.css')
    assert 'nth-last-child' in css, \
        "style.css missing nth-last-child selectors for beat opacity aging"


# ---------------------------------------------------------------------------
# ORB-12  style.css contains speaker-portrait with transition — filter transition present
# ---------------------------------------------------------------------------
def test_orb_12_css_speaker_portrait_has_transition():
    css = read('style.css')
    assert 'speaker-portrait' in css, \
        "style.css missing #speaker-portrait block"
    assert 'transition' in css, \
        "style.css missing transition property (filter transition not present)"
    # Both must appear, and transition must come after speaker-portrait
    sp_pos = css.index('speaker-portrait')
    tr_pos = css.index('transition', sp_pos)
    assert tr_pos > sp_pos, \
        "style.css: transition not found within/after #speaker-portrait block"
