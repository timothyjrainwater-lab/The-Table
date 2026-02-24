"""
Gate UI-TEXT-INPUT: WO-UI-TEXT-INPUT-001 — Text input fallback bar.

Tests (5):
  TI-01: index.html contains #text-input-bar element
  TI-02: index.html contains #text-input-field input element
  TI-03: index.html contains #text-input-send button element
  TI-04: main.ts wires Enter key on #text-input-field to send player_input
  TI-05: main.ts calls bridge.send with msg_type 'player_input' from text input
"""

import re
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
HTML_SRC = ROOT / "client" / "index.html"
MAIN_SRC = ROOT / "client" / "src" / "main.ts"

html_text = HTML_SRC.read_text(encoding="utf-8")
main_text = MAIN_SRC.read_text(encoding="utf-8")


def test_ti01_text_input_bar_in_html():
    """TI-01: index.html contains #text-input-bar container element."""
    assert 'id="text-input-bar"' in html_text, (
        "index.html must contain <div id='text-input-bar'> as the accessibility text input bar"
    )


def test_ti02_text_input_field_in_html():
    """TI-02: index.html contains #text-input-field input element."""
    assert 'id="text-input-field"' in html_text, (
        "index.html must contain <input id='text-input-field'> for text entry"
    )
    # Should be a text input
    assert re.search(r'id="text-input-field"[^>]*type="text"', html_text) or \
           re.search(r'type="text"[^>]*id="text-input-field"', html_text), (
        "text-input-field must be type='text'"
    )


def test_ti03_text_input_send_button_in_html():
    """TI-03: index.html contains #text-input-send button."""
    assert 'id="text-input-send"' in html_text, (
        "index.html must contain <button id='text-input-send'> to trigger send action"
    )


def test_ti04_enter_key_wired_in_main():
    """TI-04: main.ts wires Enter key on text-input-field to submit."""
    assert "text-input-field" in main_text, (
        "main.ts must reference 'text-input-field' to wire keyboard events"
    )
    assert re.search(r"key.*Enter|Enter.*key", main_text), (
        "main.ts must listen for Enter key on the text input field"
    )
    assert "keydown" in main_text or "keyup" in main_text, (
        "main.ts must use a keydown/keyup listener to handle Enter submission"
    )


def test_ti05_sends_player_input_via_bridge():
    """TI-05: main.ts sends { msg_type: 'player_input', text } via bridge on submit."""
    assert "player_input" in main_text, (
        "main.ts must send msg_type: 'player_input' via bridge when text input is submitted"
    )
    # The send call should include the text value
    assert re.search(r"bridge\.send\s*\(", main_text), (
        "main.ts must call bridge.send() to dispatch the player_input message"
    )
