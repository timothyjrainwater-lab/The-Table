"""
Gate tests: UI-2D-ORB — Speaker Panel wiring (ORB-01 through ORB-12)
WO-UI-2D-ORB-001

Uses Python file content search only. No browser required.
"""
import pathlib
import pytest

ROOT = pathlib.Path(__file__).parent.parent
ORB_JS   = ROOT / 'client2d' / 'orb.js'
INDEX    = ROOT / 'client2d' / 'index.html'
STYLE    = ROOT / 'client2d' / 'style.css'


def read(p: pathlib.Path) -> str:
    return p.read_text(encoding='utf-8')


# ORB-01: orb.js exists
def test_orb_01_orb_js_exists():
    assert ORB_JS.exists(), 'client2d/orb.js does not exist'


# ORB-02: index.html references orb.js script tag
def test_orb_02_index_html_loads_orb_js():
    html = read(INDEX)
    assert 'src="orb.js"' in html, 'index.html missing <script src="orb.js">'


# ORB-03: orb.js references speaking_start
def test_orb_03_speaking_start():
    src = read(ORB_JS)
    assert 'speaking_start' in src, 'orb.js missing speaking_start reference'


# ORB-04: orb.js references speaking_stop
def test_orb_04_speaking_stop():
    src = read(ORB_JS)
    assert 'speaking_stop' in src, 'orb.js missing speaking_stop reference'


# ORB-05: orb.js references speaker-portrait
def test_orb_05_speaker_portrait():
    src = read(ORB_JS)
    assert 'speaker-portrait' in src, 'orb.js missing speaker-portrait reference'


# ORB-06: orb.js references speaker-beats
def test_orb_06_speaker_beats():
    src = read(ORB_JS)
    assert 'speaker-beats' in src, 'orb.js missing speaker-beats reference'


# ORB-07: orb.js defines idle filter (IDLE_FILTER or brightness(0.5))
def test_orb_07_idle_filter_defined():
    src = read(ORB_JS)
    assert 'IDLE_FILTER' in src or 'brightness(0.5)' in src, \
        'orb.js missing idle filter definition (IDLE_FILTER or brightness(0.5))'


# ORB-08: orb.js defines DOM cap (MAX_BEATS or value 8)
def test_orb_08_dom_cap_present():
    src = read(ORB_JS)
    assert 'MAX_BEATS' in src or '= 8' in src or '> 8' in src, \
        'orb.js missing DOM cap (MAX_BEATS or numeric 8 cap)'


# ORB-09: orb.js does NOT add click or mousedown event listener
def test_orb_09_no_click_handler():
    src = read(ORB_JS)
    assert 'addEventListener(\'click\'' not in src, \
        'orb.js must not add a click event listener (crest must be non-interactive)'
    assert 'addEventListener("click"' not in src, \
        'orb.js must not add a click event listener (crest must be non-interactive)'
    assert 'addEventListener(\'mousedown\'' not in src, \
        'orb.js must not add a mousedown event listener'
    assert 'addEventListener("mousedown"' not in src, \
        'orb.js must not add a mousedown event listener'


# ORB-10: style.css contains .beat selector
def test_orb_10_beat_selector_in_css():
    css = read(STYLE)
    assert '.beat' in css, 'style.css missing .beat selector'


# ORB-11: style.css contains nth-last-child (beat aging)
def test_orb_11_nth_last_child_in_css():
    css = read(STYLE)
    assert 'nth-last-child' in css, 'style.css missing nth-last-child beat aging rules'


# ORB-12: style.css contains speaker-portrait with transition
def test_orb_12_speaker_portrait_transition_in_css():
    css = read(STYLE)
    # Both the selector and transition keyword must be present in the file
    assert '#speaker-portrait' in css, 'style.css missing #speaker-portrait selector'
    # Find the block containing #speaker-portrait and verify it has a transition rule
    idx = css.find('#speaker-portrait')
    block_end = css.find('}', idx)
    portrait_block = css[idx:block_end]
    assert 'transition' in portrait_block, \
        'style.css #speaker-portrait block missing transition property'
