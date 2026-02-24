"""
Gate tests: UI-2D-SLIP (SLIP-01 through SLIP-10)
Tests use Python string search. No browser required.
"""
import os

CLIENT2D = os.path.join(os.path.dirname(__file__), '..', 'client2d')


def read(filename):
    path = os.path.join(CLIENT2D, filename)
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


# ---------------------------------------------------------------------------
# SLIP-01  slip.js exists
# ---------------------------------------------------------------------------
def test_slip_01_slip_js_exists():
    path = os.path.join(CLIENT2D, 'slip.js')
    assert os.path.isfile(path), "client2d/slip.js does not exist"


# ---------------------------------------------------------------------------
# SLIP-02  slip.js contains pending_roll
# ---------------------------------------------------------------------------
def test_slip_02_slip_js_has_pending_roll():
    js = read('slip.js')
    assert 'pending_roll' in js, "slip.js missing 'pending_roll' event reference"


# ---------------------------------------------------------------------------
# SLIP-03  slip.js contains roll_result
# ---------------------------------------------------------------------------
def test_slip_03_slip_js_has_roll_result():
    js = read('slip.js')
    assert 'roll_result' in js, "slip.js missing 'roll_result' event reference"


# ---------------------------------------------------------------------------
# SLIP-04  slip.js contains roll_confirm
# ---------------------------------------------------------------------------
def test_slip_04_slip_js_has_roll_confirm():
    js = read('slip.js')
    assert 'roll_confirm' in js, "slip.js missing 'roll_confirm' WS send"


# ---------------------------------------------------------------------------
# SLIP-05  slip.js contains roll-slip
# ---------------------------------------------------------------------------
def test_slip_05_slip_js_has_roll_slip_class():
    js = read('slip.js')
    assert 'roll-slip' in js, "slip.js missing 'roll-slip' class reference"


# ---------------------------------------------------------------------------
# SLIP-06  slip.js contains archived
# ---------------------------------------------------------------------------
def test_slip_06_slip_js_has_archived():
    js = read('slip.js')
    assert 'archived' in js, "slip.js missing 'archived' class reference"


# ---------------------------------------------------------------------------
# SLIP-07  slip.js contains MAX_SLIPS
# ---------------------------------------------------------------------------
def test_slip_07_slip_js_has_max_slips():
    js = read('slip.js')
    assert 'MAX_SLIPS' in js, "slip.js missing MAX_SLIPS constant"


# ---------------------------------------------------------------------------
# SLIP-08  index.html contains slip.js
# ---------------------------------------------------------------------------
def test_slip_08_index_html_has_slip_js():
    html = read('index.html')
    assert 'slip.js' in html, "index.html missing slip.js script tag"


# ---------------------------------------------------------------------------
# SLIP-09  style.css contains roll-slip
# ---------------------------------------------------------------------------
def test_slip_09_css_has_roll_slip():
    css = read('style.css')
    assert 'roll-slip' in css, "style.css missing .roll-slip selector"


# ---------------------------------------------------------------------------
# SLIP-10  style.css contains wax-red
# ---------------------------------------------------------------------------
def test_slip_10_css_has_wax_red():
    css = read('style.css')
    assert 'wax-red' in css, "style.css missing --wax-red reference in roll slip styles"
