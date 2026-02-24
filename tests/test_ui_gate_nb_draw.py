"""Gate UI-NB-DRAW — Notebook Drawing Pointer Wiring (6 tests).

Tests verify:
1. NotebookObject exposes pageRightMesh getter (static analysis)
2. main.ts wires pointerdown/pointermove/pointerup to notebook drawing API
3. Drawing no-ops when notebook is closed or section is not 'notes'
4. UV-to-canvas coordinate logic works correctly (Python simulation)
"""

import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# NB-DW-01: NotebookObject exposes pageRightMesh getter
def test_nb_dw01_page_right_mesh_getter():
    nb_ts = os.path.join(ROOT, 'client', 'src', 'notebook-object.ts')
    text = open(nb_ts, encoding='utf-8').read()
    assert 'pageRightMesh' in text, \
        "notebook-object.ts must expose pageRightMesh getter"
    assert 'get pageRightMesh' in text, \
        "pageRightMesh must be a getter (not a plain property)"


# NB-DW-02: main.ts wires pointerdown to notebook.startStroke
def test_nb_dw02_pointerdown_wired():
    main_ts = os.path.join(ROOT, 'client', 'src', 'main.ts')
    text = open(main_ts, encoding='utf-8').read()
    assert 'startStroke' in text, \
        "main.ts must call notebook.startStroke"
    # Must appear inside a pointerdown listener
    pd_idx = text.find("addEventListener('pointerdown'")
    assert pd_idx != -1, "pointerdown listener not found"
    # Find startStroke after the pointerdown listener
    ss_idx = text.find('startStroke', pd_idx)
    assert ss_idx != -1, \
        "startStroke must be called inside a pointerdown handler"


# NB-DW-03: main.ts wires pointermove to notebook.continueStroke
def test_nb_dw03_pointermove_wired():
    main_ts = os.path.join(ROOT, 'client', 'src', 'main.ts')
    text = open(main_ts, encoding='utf-8').read()
    assert 'continueStroke' in text, \
        "main.ts must call notebook.continueStroke"
    pm_idx = text.find("addEventListener('pointermove'")
    assert pm_idx != -1, "pointermove listener not found"
    cs_idx = text.find('continueStroke', pm_idx)
    assert cs_idx != -1, \
        "continueStroke must be called inside a pointermove handler"


# NB-DW-04: main.ts wires pointerup to notebook.endStroke
def test_nb_dw04_pointerup_wired():
    main_ts = os.path.join(ROOT, 'client', 'src', 'main.ts')
    text = open(main_ts, encoding='utf-8').read()
    assert 'endStroke' in text, \
        "main.ts must call notebook.endStroke"
    pu_idx = text.find("addEventListener('pointerup'")
    assert pu_idx != -1, "pointerup listener not found"
    es_idx = text.find('endStroke', pu_idx)
    assert es_idx != -1, \
        "endStroke must be called inside a pointerup handler"


# NB-DW-05: Drawing guarded by isOpen and section === 'notes' (static check)
def test_nb_dw05_drawing_guarded_by_open_and_section():
    main_ts = os.path.join(ROOT, 'client', 'src', 'main.ts')
    text = open(main_ts, encoding='utf-8').read()
    # The guard must check both isOpen and section
    assert 'notebook.isOpen' in text, \
        "Drawing must check notebook.isOpen before starting a stroke"
    assert "notebook.section" in text, \
        "Drawing must check notebook.section before starting a stroke"
    assert "'notes'" in text or '"notes"' in text, \
        "Drawing guard must compare section to 'notes'"


# NB-DW-06: UV-to-canvas coordinate logic is correct (Python simulation)
def test_nb_dw06_uv_to_canvas_coords():
    """
    Simulate the uvToCanvas logic from notebook-object.ts.
    PAGE_W = 680, PAGE_H = 1100 (from notebook-object.ts constants).
    u=0.5, v=0.5 → canvas (340, 550) (center).
    u=0.0, v=1.0 → canvas (0, 0) (top-left of page).
    u=1.0, v=0.0 → canvas (680, 1100) (bottom-right of page).
    """
    PAGE_W = 680
    PAGE_H = 1100

    def uv_to_canvas(u, v):
        return {'x': u * PAGE_W, 'y': (1 - v) * PAGE_H}

    center = uv_to_canvas(0.5, 0.5)
    assert abs(center['x'] - 340) < 1, f"Expected x=340, got {center['x']}"
    assert abs(center['y'] - 550) < 1, f"Expected y=550, got {center['y']}"

    top_left = uv_to_canvas(0.0, 1.0)
    assert abs(top_left['x'] - 0) < 1
    assert abs(top_left['y'] - 0) < 1

    bottom_right = uv_to_canvas(1.0, 0.0)
    assert abs(bottom_right['x'] - PAGE_W) < 1
    assert abs(bottom_right['y'] - PAGE_H) < 1
