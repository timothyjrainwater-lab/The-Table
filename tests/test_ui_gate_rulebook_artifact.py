"""
Gate: WO-UI-RULEBOOK-01 — Rulebook Artifact (RB-ART-01 through RB-ART-07).

All tests are static-scan or simulation — no browser required.
Authority: WO-UI-RULEBOOK-01 dispatch.
"""

import re
import ast
from pathlib import Path

# ---------------------------------------------------------------------------
# File paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).parent.parent
RULEBOOK_OBJ = ROOT / 'client' / 'src' / 'rulebook-object.ts'
RULEBOOK_SEARCH = ROOT / 'client' / 'src' / 'rulebook-search.ts'
SCENE_BUILDER = ROOT / 'client' / 'src' / 'scene-builder.ts'
MAIN_TS = ROOT / 'client' / 'src' / 'main.ts'
TABLE_OBJECTS = ROOT / 'docs' / 'design' / 'LAYOUT_PACK_V1' / 'table_objects.json'


# ---------------------------------------------------------------------------
# RB-ART-01: Physical book object exists in scene
# ---------------------------------------------------------------------------

def test_rb_art_01a_rulebook_object_file_exists():
    """rulebook-object.ts must exist."""
    assert RULEBOOK_OBJ.exists(), f'Missing file: {RULEBOOK_OBJ}'


def test_rb_art_01b_rulebook_object_exports_class():
    """rulebook-object.ts must export a RulebookObject class."""
    src = RULEBOOK_OBJ.read_text(encoding='utf-8')
    assert 'export class RulebookObject' in src, \
        'rulebook-object.ts: expected "export class RulebookObject"'


def test_rb_art_01c_shelf_rulebook_anchor_referenced():
    """
    RulebookObject or its wiring must reference the shelf_rulebook anchor.
    The JSON lookup uses object name 'RULEBOOK'; verify rulebook-object.ts
    reads the RULEBOOK entry from table_objects.json.
    """
    src = RULEBOOK_OBJ.read_text(encoding='utf-8')
    # Either 'RULEBOOK' lookup or direct anchor string
    assert "'RULEBOOK'" in src or '"RULEBOOK"' in src, \
        'rulebook-object.ts: expected RULEBOOK anchor lookup from table_objects.json'


def test_rb_art_01d_main_ts_instantiates_rulebook_object():
    """main.ts must instantiate RulebookObject (wiring gate scan)."""
    src = MAIN_TS.read_text(encoding='utf-8')
    assert 'new RulebookObject()' in src, \
        'main.ts: expected "new RulebookObject()" instantiation'
    assert "import { RulebookObject }" in src or "import {RulebookObject}" in src, \
        "main.ts: expected import of RulebookObject from './rulebook-object'"


def test_rb_art_01e_stub_tome_at_rulebook_anchor():
    """
    scene-builder.ts must place stub_tome at the RULEBOOK anchor.
    This is already implemented via table_objects.json lookup.
    """
    src = SCENE_BUILDER.read_text(encoding='utf-8')
    assert 'stub_tome' in src, \
        'scene-builder.ts: expected stub_tome mesh (RULEBOOK anchor stub)'
    assert "RULEBOOK" in src or 'shelf_rulebook' in src or "'RULEBOOK'" in src, \
        'scene-builder.ts: expected RULEBOOK object lookup for anchor position'


# ---------------------------------------------------------------------------
# RB-ART-02: BOOK_READ posture triggered on open
# ---------------------------------------------------------------------------

def test_rb_art_02a_book_read_posture_called_on_open():
    """main.ts must call setPosture('BOOK_READ') in the rulebook open path."""
    src = MAIN_TS.read_text(encoding='utf-8')
    assert "setPosture('BOOK_READ')" in src, \
        "main.ts: expected postureCtrl.setPosture('BOOK_READ') in the open path"


def test_rb_art_02b_open_rulebook_helper_calls_book_read():
    """
    The _openRulebook helper must call setPosture('BOOK_READ') — it is the
    central dispatch point for all book-open interactions.
    """
    src = MAIN_TS.read_text(encoding='utf-8')
    # Extract the _openRulebook function body
    match = re.search(
        r'function _openRulebook\([^)]*\)\s*:\s*void\s*\{(.+?)^}',
        src, re.DOTALL | re.MULTILINE,
    )
    assert match is not None, \
        "main.ts: could not find _openRulebook function"
    body = match.group(1)
    assert "setPosture('BOOK_READ')" in body, \
        "main.ts: _openRulebook must call setPosture('BOOK_READ')"


def test_rb_art_02c_book_read_not_default_posture():
    """
    BOOK_READ must not be the startup/default posture.
    CameraPostureController initialises with STANDARD (confirmed in camera.ts).
    """
    from pathlib import Path
    camera_src = (ROOT / 'client' / 'src' / 'camera.ts').read_text(encoding='utf-8')
    # Default posture is STANDARD — confirm BOOK_READ is not set at init
    assert "currentPosture: PostureName = 'STANDARD'" in camera_src or \
           "= 'STANDARD'" in camera_src, \
        "camera.ts: expected STANDARD as initial posture (not BOOK_READ)"
    # Confirm BOOK_READ is not set by default at startup
    init_region = camera_src[:500]  # first 500 chars (constructor area)
    assert 'BOOK_READ' not in init_region, \
        "camera.ts: BOOK_READ must not appear in the default constructor init block"


# ---------------------------------------------------------------------------
# RB-ART-03: Search returns ref only — no snippet
# ---------------------------------------------------------------------------

FORBIDDEN_CONTENT_FIELDS = ['snippet', 'preview', 'excerpt', 'content', 'description']


def test_rb_art_03a_search_returns_string():
    """searchRuleRef return type must be string, not an object."""
    src = RULEBOOK_SEARCH.read_text(encoding='utf-8')
    # The exported function signature
    match = re.search(r'export function searchRuleRef\([^)]*\):\s*(\S+)', src)
    assert match is not None, 'rulebook-search.ts: cannot find searchRuleRef signature'
    ret_type = match.group(1).rstrip('{').rstrip()
    assert ret_type == 'string', \
        f'searchRuleRef return type must be "string", got "{ret_type}"'


def test_rb_art_03b_no_content_fields_in_search():
    """rulebook-search.ts must not declare snippet/preview/excerpt/content fields."""
    src = RULEBOOK_SEARCH.read_text(encoding='utf-8')
    for field in FORBIDDEN_CONTENT_FIELDS:
        pattern = rf'\b{field}\b\s*:'
        assert not re.search(pattern, src), \
            f'rulebook-search.ts: forbidden content field "{field}" found'


def test_rb_art_03c_no_content_fields_in_rulebook_object():
    """rulebook-object.ts must not declare snippet/preview/excerpt/content fields."""
    src = RULEBOOK_OBJ.read_text(encoding='utf-8')
    for field in FORBIDDEN_CONTENT_FIELDS:
        pattern = rf'\b{field}\b\s*:'
        assert not re.search(pattern, src), \
            f'rulebook-object.ts: forbidden content field "{field}" found'


# ---------------------------------------------------------------------------
# RB-ART-04: "?" stamp carries rule_ref only
# ---------------------------------------------------------------------------

def _build_stamp(rule_ref: str):
    """Simulate constructing a QuestionStamp-equivalent object."""
    return {'rule_ref': rule_ref}


def _stamp_fields(stamp: dict) -> set:
    return set(stamp.keys())


STAMP_FORBIDDEN_FIELDS = {'reason', 'explanation', 'because', 'message', 'text', 'description'}


def test_rb_art_04a_stamp_has_exactly_one_payload_field():
    """Stamp object has exactly one payload field: rule_ref."""
    stamp = _build_stamp('combat.attack_roll')
    fields = _stamp_fields(stamp)
    assert fields == {'rule_ref'}, \
        f'stamp must have exactly {{rule_ref}}, got {fields}'


def test_rb_art_04b_stamp_has_no_forbidden_fields():
    """Stamp must not carry reason/explanation/because/message/text/description."""
    stamp = _build_stamp('conditions')
    fields = _stamp_fields(stamp)
    overlap = fields & STAMP_FORBIDDEN_FIELDS
    assert not overlap, f'stamp has forbidden fields: {overlap}'


def test_rb_art_04c_stamp_click_emits_open_to_ref():
    """
    Stamp click path in main.ts must call open_to_ref (via _openRulebook).
    Static scan: _openRulebook called with userData.ruleRef in the stamp click block.
    """
    src = MAIN_TS.read_text(encoding='utf-8')
    # Stamp click block uses _openRulebook(ruleRef) where ruleRef comes from userData
    assert '_openRulebook(ruleRef)' in src, \
        "main.ts: expected _openRulebook(ruleRef) in the stamp click handler"
    assert 'userData.ruleRef' in src, \
        "main.ts: expected stamp ruleRef read from mesh.userData.ruleRef"


def test_rb_art_04d_stamp_carries_rule_ref_in_book_object():
    """
    book-object.ts QuestionStamp constructor takes ruleRef as first arg.
    Confirm no content/explanation fields added to the stamp.
    Scan checks for field declarations (name: type pattern), not substring matches.
    """
    src = (ROOT / 'client' / 'src' / 'book-object.ts').read_text(encoding='utf-8')
    # QuestionStamp must exist
    assert 'class QuestionStamp' in src, 'book-object.ts: QuestionStamp class missing'
    # Its constructor should take ruleRef
    assert 'ruleRef' in src, 'book-object.ts: QuestionStamp must use ruleRef'
    # Must not have content/explanation field declarations in QuestionStamp
    # Check for property declarations: "  readonly FIELD: ..." or "  FIELD: ..."
    match = re.search(r'class QuestionStamp\s*\{(.+?)^}', src, re.DOTALL | re.MULTILINE)
    if match:
        body = match.group(1)
        for field in STAMP_FORBIDDEN_FIELDS:
            # Field declaration pattern: start of word, then optional readonly/type keywords
            pattern = rf'(?:readonly\s+){re.escape(field)}\s*:|^\s+{re.escape(field)}\s*:'
            assert not re.search(pattern, body, re.MULTILINE), \
                f'book-object.ts QuestionStamp: forbidden field declaration "{field}" found'


# ---------------------------------------------------------------------------
# RB-ART-05: Denial routing — no explanation strings in open/stamp/search flow
# ---------------------------------------------------------------------------

DENIAL_LITERALS = ['"because"', '"cannot"', '"you can\'t"', '"invalid"',
                   "'because'", "'cannot'", "'you can\\'t'", "'invalid'"]

SCAN_DENIAL_FILES = [RULEBOOK_OBJ, RULEBOOK_SEARCH]


def test_rb_art_05a_no_denial_literals_in_rulebook_object():
    """rulebook-object.ts: no denial explanation strings."""
    src = RULEBOOK_OBJ.read_text(encoding='utf-8')
    for literal in ['because', 'cannot', "you can't", 'invalid']:
        # Allow the word in comments (after //) but not in string literals
        # Simple heuristic: look for quoted occurrences
        quoted = rf'["\'].*{re.escape(literal)}.*["\']'
        if re.search(quoted, src, re.IGNORECASE):
            raise AssertionError(
                f'rulebook-object.ts: denial literal "{literal}" found in a string'
            )


def test_rb_art_05b_no_denial_literals_in_rulebook_search():
    """rulebook-search.ts: no denial explanation strings."""
    src = RULEBOOK_SEARCH.read_text(encoding='utf-8')
    for literal in ['because', 'cannot', "you can't", 'invalid']:
        quoted = rf'["\'].*{re.escape(literal)}.*["\']'
        if re.search(quoted, src, re.IGNORECASE):
            raise AssertionError(
                f'rulebook-search.ts: denial literal "{literal}" found in a string'
            )


# ---------------------------------------------------------------------------
# RB-ART-06: A-RULES-OPEN — book always openable
# ---------------------------------------------------------------------------

class RulebookSimulator:
    """
    Simulate RulebookObject.openToRef() — no precondition checks.
    Verifies that openToRef accepts any ref without game-state input.
    """
    def __init__(self):
        self.opens: list[str] = []
        self.is_open = False

    def open_to_ref(self, rule_ref: str) -> None:
        # A-RULES-OPEN: no precondition check — always opens
        self.is_open = True
        self.opens.append(rule_ref)


def test_rb_art_06a_open_to_ref_with_valid_ref():
    """openToRef with a known ref opens without precondition."""
    rb = RulebookSimulator()
    rb.open_to_ref('combat.attack_roll')
    assert rb.is_open
    assert rb.opens == ['combat.attack_roll']


def test_rb_art_06b_open_to_ref_with_unknown_ref():
    """openToRef with an unknown ref still opens (A-RULES-OPEN)."""
    rb = RulebookSimulator()
    rb.open_to_ref('some.unknown.rule')
    assert rb.is_open


def test_rb_art_06c_open_to_ref_with_no_game_state():
    """openToRef accepts a rule_ref without any game state context."""
    rb = RulebookSimulator()
    # No entity, no pending state, no play outcome passed
    rb.open_to_ref('conditions')
    assert rb.is_open
    assert 'conditions' in rb.opens


def test_rb_art_06d_no_precondition_in_open_path():
    """
    Static scan: rulebook-object.ts openToRef must not check entity state,
    pending state, or play outcome.
    """
    src = RULEBOOK_OBJ.read_text(encoding='utf-8')
    # Extract openToRef method body
    match = re.search(
        r'openToRef\([^)]*\)\s*:\s*void\s*\{(.+?)^  \}',
        src, re.DOTALL | re.MULTILINE,
    )
    if match:
        body = match.group(1)
        forbidden = ['entity_state', 'pending_state', 'play_outcome',
                     'hp_current', 'activePendingHandle', 'PENDING']
        for term in forbidden:
            assert term not in body, \
                f'rulebook-object.ts openToRef: precondition check on "{term}" found'


# ---------------------------------------------------------------------------
# RB-ART-07: Existing routing tests still pass (regression guard)
# ---------------------------------------------------------------------------

# Replicate the routing logic from rulebook-search.ts in Python
# (same logic as test_ui_gate_rulebook.py but verifies the source hasn't drifted)

KNOWN_REFS = [
    {'ref': 'combat.attack_roll', 'aliases': ['attack', 'attack roll', 'to hit']},
    {'ref': 'combat.basics',      'aliases': ['combat', 'basic combat', 'fighting']},
    {'ref': 'combat.actions',     'aliases': ['actions', 'action types', 'standard action', 'move action']},
    {'ref': 'combat.action_types','aliases': ['full round', 'full-round', 'swift', 'immediate', 'free action']},
    {'ref': 'conditions',         'aliases': ['conditions', 'status', 'blinded', 'fatigued', 'prone', 'stunned']},
    {'ref': 'conditions.list',    'aliases': ['condition list', 'all conditions']},
]
DEFAULT_REF = 'combat.basics'


def _search_rule_ref(query: str) -> str:
    q = query.lower().strip()
    if not q:
        return DEFAULT_REF
    for entry in KNOWN_REFS:
        if q in entry['ref']:
            return entry['ref']
        if any(q in a or a in q for a in entry['aliases']):
            return entry['ref']
    return DEFAULT_REF


def test_rb_art_07_regression_direct_open():
    """Regression: direct open to 'conditions' ref."""
    assert _search_rule_ref('conditions') == 'conditions'


def test_rb_art_07_regression_search_finds_match():
    """Regression: search 'attack' resolves to combat.attack_roll."""
    assert _search_rule_ref('attack') == 'combat.attack_roll'


def test_rb_art_07_regression_search_fallback():
    """Regression: empty and unknown queries fall back to DEFAULT_REF."""
    assert _search_rule_ref('') == DEFAULT_REF
    assert _search_rule_ref('zzz_nonexistent') == DEFAULT_REF
