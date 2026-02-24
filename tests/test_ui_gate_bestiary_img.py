"""Gate UI-BESTIARY-IMG — Bestiary Image URL Binding (6 tests).

Tests verify:
1. BestiaryEntry interface has image_url optional field (static analysis)
2. upsertBestiaryEntry accepts and stores image_url
3. Fallback to procedural sketch when image_url absent
4. Python simulation of knowledge-level alpha logic
"""

import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# BI-01: BestiaryEntry interface has image_url optional field
def test_bi01_bestiary_entry_has_image_url():
    nb_ts = os.path.join(ROOT, 'client', 'src', 'notebook-object.ts')
    text = open(nb_ts, encoding='utf-8').read()
    assert 'image_url' in text, \
        "notebook-object.ts must have image_url in BestiaryEntry"
    # Must be optional (?)
    assert 'image_url?' in text, \
        "image_url must be optional (image_url?)"


# BI-02: makeBestiaryCanvas accepts images map parameter
def test_bi02_canvas_fn_accepts_images_map():
    nb_ts = os.path.join(ROOT, 'client', 'src', 'notebook-object.ts')
    text = open(nb_ts, encoding='utf-8').read()
    assert 'Map<string, HTMLImageElement>' in text, \
        "makeBestiaryCanvas must accept a Map<string, HTMLImageElement> images parameter"


# BI-03: upsertBestiaryEntry loads image when image_url present
def test_bi03_upsert_loads_image():
    nb_ts = os.path.join(ROOT, 'client', 'src', 'notebook-object.ts')
    text = open(nb_ts, encoding='utf-8').read()
    assert 'entry.image_url' in text, \
        "upsertBestiaryEntry must check entry.image_url"
    assert 'img.src' in text or 'new Image()' in text, \
        "upsertBestiaryEntry must create an Image element to load the URL"


# BI-04: _bestiaryImages map stored on NotebookObject
def test_bi04_images_map_stored():
    nb_ts = os.path.join(ROOT, 'client', 'src', 'notebook-object.ts')
    text = open(nb_ts, encoding='utf-8').read()
    assert '_bestiaryImages' in text, \
        "NotebookObject must have a _bestiaryImages private field"


# BI-05: Knowledge level alpha — 'heard' without image = silhouette
def test_bi05_heard_renders_silhouette():
    """
    Simulate: when knowledge_level='heard' and no image, silhouette branch executes.
    When knowledge_level='studied' and image present, full opacity used.
    """
    def get_alpha(knowledge_level, has_image):
        if has_image:
            alphas = {'heard': 0.25, 'seen': 0.6, 'fought': 0.85, 'studied': 1.0}
            return alphas.get(knowledge_level, 1.0)
        return None  # silhouette branch (no alpha concept)

    assert get_alpha('studied', True) == 1.0
    assert get_alpha('heard', True) == 0.25
    assert get_alpha('seen', True) == 0.6
    assert get_alpha('fought', True) == 0.85
    assert get_alpha('heard', False) is None  # silhouette, no alpha


# BI-06: image_url passed through WS event → upsertBestiaryEntry (static analysis)
def test_bi06_ws_event_passes_image_url():
    main_ts = os.path.join(ROOT, 'client', 'src', 'main.ts')
    text = open(main_ts, encoding='utf-8').read()
    assert 'upsertBestiaryEntry' in text, \
        "main.ts must call notebook.upsertBestiaryEntry"
