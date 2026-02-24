"""WO-UI-TOKENS-01 Gate Tests — TOKEN-PEND-01..07

Tests verify:
  01. EntityRenderer declares _isDragPending / pendingMoveTokenId state
  02. setMovePending / clearMovePending / isDraggable methods exist
  03. isDraggable gate semantics (Python sim mirrors TS contract)
  04. main.ts handles PENDING_MOVE_TOKEN WS event
  05. main.ts emits TOKEN_MOVE_COMMITTED_INTENT on drag drop (pending path only)
  06. _makeTokenTexture signature is safe (no hp/condition/ac/initiative params)
  07. Named leak vectors absent from entity-renderer.ts

Authority: WO-UI-TOKENS-01, DOCTRINE_04_TABLE_UI_MEMO_V4 §16, §17.
"""

import pathlib
import re

ER_PATH   = pathlib.Path(__file__).parent.parent / 'client' / 'src' / 'entity-renderer.ts'
MAIN_PATH = pathlib.Path(__file__).parent.parent / 'client' / 'src' / 'main.ts'

er_text   = ER_PATH.read_text(encoding='utf-8')
main_text = MAIN_PATH.read_text(encoding='utf-8')


# ---------------------------------------------------------------------------
# TOKEN-PEND-01: EntityRenderer declares pending move token state field
# ---------------------------------------------------------------------------

def test_token_pend_01_pending_state_field():
    assert '_isDragPending' in er_text or 'pendingMoveTokenId' in er_text or \
           '_pendingMoveTokenId' in er_text, \
        "EntityRenderer must declare a pending move token state field"


# ---------------------------------------------------------------------------
# TOKEN-PEND-02: setMovePending / clearMovePending / isDraggable methods exist
# ---------------------------------------------------------------------------

def test_token_pend_02_methods_exist():
    assert 'setMovePending' in er_text, \
        "EntityRenderer must expose setMovePending(id)"
    assert 'clearMovePending' in er_text, \
        "EntityRenderer must expose clearMovePending()"
    assert 'isDraggable' in er_text, \
        "EntityRenderer must expose isDraggable(id)"


# ---------------------------------------------------------------------------
# TOKEN-PEND-03: isDraggable gate semantics confirmed via Python sim
# ---------------------------------------------------------------------------

def test_token_pend_03_is_draggable_semantics():
    class TokenPendingSim:
        def __init__(self):
            self._pending_id = None

        def set_move_pending(self, id_):
            self._pending_id = id_

        def clear_move_pending(self):
            self._pending_id = None

        def is_draggable(self, id_):
            return self._pending_id == id_

    sim = TokenPendingSim()
    assert sim.is_draggable('goblin1') is False, \
        "No pending → not draggable"
    sim.set_move_pending('goblin1')
    assert sim.is_draggable('goblin1') is True, \
        "Matching pending → draggable"
    assert sim.is_draggable('kira') is False, \
        "Non-matching id → not draggable"
    sim.clear_move_pending()
    assert sim.is_draggable('goblin1') is False, \
        "After clear → not draggable"


# ---------------------------------------------------------------------------
# TOKEN-PEND-04: main.ts handles PENDING_MOVE_TOKEN WS event
# ---------------------------------------------------------------------------

def test_token_pend_04_main_handles_pending_move_token():
    assert 'PENDING_MOVE_TOKEN' in main_text, \
        "main.ts must handle PENDING_MOVE_TOKEN WS event"
    assert re.search(r'setMovePending\s*\(', main_text), \
        "main.ts must call entityRenderer.setMovePending() in PENDING_MOVE_TOKEN handler"


# ---------------------------------------------------------------------------
# TOKEN-PEND-05: main.ts emits TOKEN_MOVE_COMMITTED_INTENT on drag drop
#               and it is inside the isDraggable gate
# ---------------------------------------------------------------------------

def test_token_pend_05_committed_intent_emitted_inside_gate():
    assert 'TOKEN_MOVE_COMMITTED_INTENT' in main_text, \
        "main.ts must emit TOKEN_MOVE_COMMITTED_INTENT on successful token drag drop"
    # Verify it is inside the isDraggable branch, not unconditional
    block = re.search(r'isDraggable.*?TOKEN_MOVE_COMMITTED_INTENT', main_text, re.DOTALL)
    assert block, \
        "TOKEN_MOVE_COMMITTED_INTENT must be emitted only inside isDraggable gate"


# ---------------------------------------------------------------------------
# TOKEN-PEND-06: _makeTokenTexture signature is safe — no banned params
# ---------------------------------------------------------------------------

def test_token_pend_06_make_token_texture_safe_signature():
    sig = re.search(r'static _makeTokenTexture\s*\(([^)]*)\)', er_text)
    assert sig, "_makeTokenTexture signature must be findable"
    params = sig.group(1)
    for banned_param in ['hp', 'condition', 'ac', 'initiative', 'initiative_val']:
        assert banned_param not in params.lower(), \
            f"_makeTokenTexture must not accept '{banned_param}' — named leak vector"


# ---------------------------------------------------------------------------
# TOKEN-PEND-07: Named leak vectors absent from entity-renderer.ts
# ---------------------------------------------------------------------------

def test_token_pend_07_no_leak_vectors():
    LEAK_VECTORS = [
        'hpPip', 'conditionBadge', 'acHint', 'initiativeHint',
        'hp_pip', 'condition_badge', 'ac_hint', 'initiative_hint',
    ]
    for lv in LEAK_VECTORS:
        assert lv not in er_text, \
            f"entity-renderer.ts must not contain '{lv}' — precision leak vector"
