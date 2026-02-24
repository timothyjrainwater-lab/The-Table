"""
Gate tests: UI-2D-RELAYOUT-002 (RL2-01 through RL2-14)
Tests use Python html.parser + string search. No browser required.
"""
import os

CLIENT2D = os.path.join(os.path.dirname(__file__), '..', 'client2d')


def read(filename):
    path = os.path.join(CLIENT2D, filename)
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


# ---------------------------------------------------------------------------
# RL2-01  Old five-zone structure eliminated — dm-zone must not exist
# ---------------------------------------------------------------------------
def test_rl2_01_dm_zone_eliminated():
    html = read('index.html')
    assert 'id="dm-zone"' not in html, \
        "index.html still contains id='dm-zone' — old five-zone structure not removed"


# ---------------------------------------------------------------------------
# RL2-02  vault-zone renamed to scene-surface — must not exist
# ---------------------------------------------------------------------------
def test_rl2_02_vault_zone_eliminated():
    html = read('index.html')
    assert 'id="vault-zone"' not in html, \
        "index.html still contains id='vault-zone' — must be renamed to scene-surface"


# ---------------------------------------------------------------------------
# RL2-03  #scene-surface exists
# ---------------------------------------------------------------------------
def test_rl2_03_scene_surface_exists():
    html = read('index.html')
    assert 'id="scene-surface"' in html, \
        "index.html missing id='scene-surface'"


# ---------------------------------------------------------------------------
# RL2-04  #right-col exists
# ---------------------------------------------------------------------------
def test_rl2_04_right_col_exists():
    html = read('index.html')
    assert 'id="right-col"' in html, \
        "index.html missing id='right-col'"


# ---------------------------------------------------------------------------
# RL2-05  #speaker-panel exists inside #right-col
# ---------------------------------------------------------------------------
def test_rl2_05_speaker_panel_inside_right_col():
    html = read('index.html')
    assert 'id="speaker-panel"' in html, \
        "index.html missing id='speaker-panel'"
    right_col_pos = html.index('id="right-col"')
    speaker_pos = html.index('id="speaker-panel"')
    assert speaker_pos > right_col_pos, \
        "#speaker-panel does not appear after #right-col opens"


# ---------------------------------------------------------------------------
# RL2-06  #dice-section exists inside #right-col
# ---------------------------------------------------------------------------
def test_rl2_06_dice_section_inside_right_col():
    html = read('index.html')
    assert 'id="dice-section"' in html, \
        "index.html missing id='dice-section'"
    right_col_pos = html.index('id="right-col"')
    dice_pos = html.index('id="dice-section"')
    assert dice_pos > right_col_pos, \
        "#dice-section does not appear after #right-col opens"


# ---------------------------------------------------------------------------
# RL2-07  #speaker-portrait exists inside #speaker-panel
# ---------------------------------------------------------------------------
def test_rl2_07_speaker_portrait_inside_speaker_panel():
    html = read('index.html')
    assert 'id="speaker-portrait"' in html, \
        "index.html missing id='speaker-portrait'"
    panel_pos = html.index('id="speaker-panel"')
    portrait_pos = html.index('id="speaker-portrait"')
    assert portrait_pos > panel_pos, \
        "#speaker-portrait does not appear after #speaker-panel opens"


# ---------------------------------------------------------------------------
# RL2-08  #speaker-beats exists inside #speaker-panel
# ---------------------------------------------------------------------------
def test_rl2_08_speaker_beats_inside_speaker_panel():
    html = read('index.html')
    assert 'id="speaker-beats"' in html, \
        "index.html missing id='speaker-beats'"
    panel_pos = html.index('id="speaker-panel"')
    beats_pos = html.index('id="speaker-beats"')
    assert beats_pos > panel_pos, \
        "#speaker-beats does not appear after #speaker-panel opens"


# ---------------------------------------------------------------------------
# RL2-09  #slip-tray exists inside #dice-section
# ---------------------------------------------------------------------------
def test_rl2_09_slip_tray_inside_dice_section():
    html = read('index.html')
    assert 'id="slip-tray"' in html, \
        "index.html missing id='slip-tray'"
    dice_pos = html.index('id="dice-section"')
    slip_pos = html.index('id="slip-tray"')
    assert slip_pos > dice_pos, \
        "#slip-tray does not appear after #dice-section opens"


# ---------------------------------------------------------------------------
# RL2-10  #handout-tray exists inside #dice-section and is hidden by default
# ---------------------------------------------------------------------------
def test_rl2_10_handout_tray_hidden_in_dice_section():
    html = read('index.html')
    assert 'id="handout-tray"' in html, \
        "index.html missing id='handout-tray'"
    dice_pos = html.index('id="dice-section"')
    handout_pos = html.index('id="handout-tray"')
    assert handout_pos > dice_pos, \
        "#handout-tray does not appear after #dice-section opens"
    tag_region = html[max(0, handout_pos - 20):handout_pos + 120]
    assert 'display:none' in tag_region or 'display: none' in tag_region, \
        "#handout-tray does not have display:none by default"


# ---------------------------------------------------------------------------
# RL2-11  #posture-label exists inside #shelf-zone
# ---------------------------------------------------------------------------
def test_rl2_11_posture_label_inside_shelf_zone():
    html = read('index.html')
    assert 'id="posture-label"' in html, \
        "index.html missing id='posture-label'"
    shelf_pos = html.index('id="shelf-zone"')
    label_pos = html.index('id="posture-label"')
    assert label_pos > shelf_pos, \
        "#posture-label does not appear after #shelf-zone opens"


# ---------------------------------------------------------------------------
# RL2-12  Shelf items have data-posture attributes
# ---------------------------------------------------------------------------
def test_rl2_12_shelf_items_have_data_posture():
    html = read('index.html')
    assert 'data-posture=' in html, \
        "index.html missing data-posture attributes on shelf items"
    assert 'posture-down' in html, \
        "data-posture='posture-down' missing from shelf items"
    assert 'posture-dice' in html, \
        "data-posture='posture-dice' missing from shelf items"


# ---------------------------------------------------------------------------
# RL2-13  All four posture classes present in style.css
# ---------------------------------------------------------------------------
def test_rl2_13_posture_classes_in_css():
    css = read('style.css')
    for cls in ('posture-standard', 'posture-lean', 'posture-down', 'posture-dice'):
        assert cls in css, f"Posture class '{cls}' missing from style.css"


# ---------------------------------------------------------------------------
# RL2-14  Palette variables intact — regression guard
# ---------------------------------------------------------------------------
def test_rl2_14_palette_variables_intact():
    css = read('style.css')
    for var in ('--walnut-mid', '--parchment', '--amber-idle', '--wax-red',
                '--walnut-dark', '--walnut-warm', '--felt-deep', '--parchment-aged',
                '--ink', '--leather-warm', '--leather-dark', '--brass', '--amber-speak'):
        assert var in css, f"Palette variable '{var}' missing from style.css"
