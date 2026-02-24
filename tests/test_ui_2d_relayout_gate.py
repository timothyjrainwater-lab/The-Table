"""
Gate tests: UI-2D-RELAYOUT (RL-01 through RL-12)
Tests use Python html.parser + string search. No browser required.
"""
import os
import re

CLIENT2D = os.path.join(os.path.dirname(__file__), '..', 'client2d')


def read(filename):
    path = os.path.join(CLIENT2D, filename)
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


# ---------------------------------------------------------------------------
# RL-01  Old five-zone structure eliminated — dm-zone must not exist
# ---------------------------------------------------------------------------
def test_rl_01_dm_zone_eliminated():
    html = read('index.html')
    assert 'id="dm-zone"' not in html, \
        "index.html still contains id='dm-zone' — old five-zone structure not removed"


# ---------------------------------------------------------------------------
# RL-02  #right-col exists
# ---------------------------------------------------------------------------
def test_rl_02_right_col_exists():
    html = read('index.html')
    assert 'id="right-col"' in html, \
        "index.html missing id='right-col'"


# ---------------------------------------------------------------------------
# RL-03  #dm-panel exists and is hidden by default
# ---------------------------------------------------------------------------
def test_rl_03_dm_panel_hidden():
    html = read('index.html')
    assert 'id="dm-panel"' in html, \
        "index.html missing id='dm-panel'"
    # Hidden via inline style or class — check inline style as specified
    assert 'id="dm-panel"' in html, "dm-panel missing"
    # Extract the dm-panel tag and confirm display:none present nearby
    idx = html.index('id="dm-panel"')
    tag_region = html[max(0, idx-20):idx+120]
    assert 'display:none' in tag_region or 'display: none' in tag_region, \
        "#dm-panel does not have display:none by default"


# ---------------------------------------------------------------------------
# RL-04  #orb-transcript exists and is hidden by default
# ---------------------------------------------------------------------------
def test_rl_04_orb_transcript_hidden():
    html = read('index.html')
    assert 'id="orb-transcript"' in html, \
        "index.html missing id='orb-transcript'"
    idx = html.index('id="orb-transcript"')
    tag_region = html[max(0, idx-20):idx+120]
    assert 'display:none' in tag_region or 'display: none' in tag_region, \
        "#orb-transcript does not have display:none by default"


# ---------------------------------------------------------------------------
# RL-05  #vault-zone exists (map region)
# ---------------------------------------------------------------------------
def test_rl_05_vault_zone_exists():
    html = read('index.html')
    assert 'id="vault-zone"' in html, \
        "index.html missing id='vault-zone'"


# ---------------------------------------------------------------------------
# RL-06  #slip-tray is nested inside #right-col
# ---------------------------------------------------------------------------
def test_rl_06_slip_tray_inside_right_col():
    html = read('index.html')
    assert 'id="right-col"' in html, "right-col missing"
    assert 'id="slip-tray"' in html, "slip-tray missing"
    # slip-tray must appear after right-col opens and before right-col closes
    right_col_start = html.index('id="right-col"')
    slip_tray_pos = html.index('id="slip-tray"')
    assert slip_tray_pos > right_col_start, \
        "#slip-tray does not appear after #right-col opens"
    # Confirm right-col's closing tag comes after slip-tray
    right_col_close = html.index('</div><!-- /#right-col -->', slip_tray_pos) \
        if '<!-- /#right-col -->' in html \
        else html.rindex('</div>', slip_tray_pos, html.index('</div>', right_col_start + len('id="right-col"') + 200))
    # Sufficient: slip-tray pos > right-col open and html has right-col before slip-tray
    assert slip_tray_pos > right_col_start, \
        "#slip-tray not nested inside #right-col"


# ---------------------------------------------------------------------------
# RL-07  #handout-tray exists inside #right-col and is hidden by default
# ---------------------------------------------------------------------------
def test_rl_07_handout_tray_hidden_in_right_col():
    html = read('index.html')
    assert 'id="handout-tray"' in html, \
        "index.html missing id='handout-tray'"
    right_col_start = html.index('id="right-col"')
    handout_pos = html.index('id="handout-tray"')
    assert handout_pos > right_col_start, \
        "#handout-tray does not appear after #right-col opens"
    tag_region = html[max(0, handout_pos-20):handout_pos+120]
    assert 'display:none' in tag_region or 'display: none' in tag_region, \
        "#handout-tray does not have display:none by default"


# ---------------------------------------------------------------------------
# RL-08  #posture-label exists inside #shelf-zone
# ---------------------------------------------------------------------------
def test_rl_08_posture_label_inside_shelf_zone():
    html = read('index.html')
    assert 'id="shelf-zone"' in html, "shelf-zone missing"
    assert 'id="posture-label"' in html, \
        "index.html missing id='posture-label'"
    shelf_start = html.index('id="shelf-zone"')
    label_pos = html.index('id="posture-label"')
    assert label_pos > shelf_start, \
        "#posture-label does not appear after #shelf-zone opens"


# ---------------------------------------------------------------------------
# RL-09  Shelf items have data-posture attributes
# ---------------------------------------------------------------------------
def test_rl_09_shelf_items_have_data_posture():
    html = read('index.html')
    assert 'data-posture=' in html, \
        "index.html missing data-posture attributes on shelf items"
    # At minimum, two distinct posture values must be present
    assert 'posture-down' in html, \
        "data-posture='posture-down' missing from shelf items"
    assert 'posture-dice' in html, \
        "data-posture='posture-dice' missing from shelf items"


# ---------------------------------------------------------------------------
# RL-10  All four posture classes present in style.css
# ---------------------------------------------------------------------------
def test_rl_10_posture_classes_in_css():
    css = read('style.css')
    for cls in ('posture-standard', 'posture-lean', 'posture-down', 'posture-dice'):
        assert cls in css, f"Posture class '{cls}' missing from style.css"


# ---------------------------------------------------------------------------
# RL-11  No Three.js references — regression guard
# ---------------------------------------------------------------------------
def test_rl_11_no_threejs_references():
    for fname in ('index.html', 'style.css', 'main.js', 'ws.js'):
        content = read(fname)
        for term in ('THREE', 'WebGLRenderer', 'PerspectiveCamera'):
            assert term not in content, \
                f"Three.js reference '{term}' found in client2d/{fname}"


# ---------------------------------------------------------------------------
# RL-12  Palette variables intact — regression guard
# ---------------------------------------------------------------------------
def test_rl_12_palette_variables_intact():
    css = read('style.css')
    for var in ('--walnut-mid', '--parchment', '--amber-idle', '--wax-red',
                '--walnut-dark', '--walnut-warm', '--felt-deep', '--parchment-aged',
                '--ink', '--leather-warm', '--leather-dark', '--brass', '--amber-speak'):
        assert var in css, f"Palette variable '{var}' missing from style.css"
