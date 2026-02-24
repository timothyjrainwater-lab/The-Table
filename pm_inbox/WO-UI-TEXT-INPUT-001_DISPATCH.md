# WO-UI-TEXT-INPUT-001 — Text Input Fallback

**Issued:** 2026-02-23
**Authority:** North Star gap audit — no text input area exists anywhere in the UI. STT is not provisioned (FINDING-PLAYTEST-F01 open). Without text input, the system is inaccessible when voice is unavailable.
**Gate:** UI-TEXT-INPUT (new). Target: 5 tests.
**Blocked by:** Nothing. Parallel-safe with all current WOs.

---

## 1. Gap

All player input currently requires STT (voice). STT depends on Chatterbox/Kokoro (FINDING-PLAYTEST-F01 — not installed). No keyboard text fallback exists. Vision explicitly includes text input area on the table as an accessibility path.

## 2. Fix Spec

A minimal HTML text input area — not Three.js — rendered as a fixed-position overlay at the bottom of the viewport:

1. **Element:** `<div id="text-input-bar">` containing a text `<input>` and a Send button.
2. **Styling:** Fixed bottom, dark background, low-profile (height ~48px). Does not obscure the 3D scene significantly.
3. **Submit action:** On Enter key or Send click, read `input.value`, send via WebSocket as `{ type: "player_input", text: input.value }`, clear field.
4. **Show/hide:** Visible at all times (always-on fallback). Not toggled — permanent accessibility feature.
5. **Focus management:** `input.blur()` after submit so keyboard doesn't capture 3D navigation keys.

### WS message contract

```typescript
// player_input message (sends to engine)
{ type: "player_input", text: string }
```

## 3. Test Spec (Gate UI-TEXT-INPUT — 5 tests)

File: `tests/test_ui_gate_text_input.py` (new)

| ID | Test |
|----|------|
| TI-01 | `#text-input-bar` div exists in `index.html` |
| TI-02 | Text `<input>` element inside `#text-input-bar` |
| TI-03 | Submit sends WS message with type `player_input` and text field |
| TI-04 | Input cleared after submit |
| TI-05 | `input.blur()` called after submit (no key capture after send) |

## 4. Implementation Plan

1. Read `client/index.html` (current structure), `client/src/main.ts` (WS send pattern)
2. Add `#text-input-bar` div to `index.html` with input + button, basic CSS
3. Add event listeners in `main.ts`: Enter key + button click → `ws.send()` + clear + blur
4. Write 5 tests to `tests/test_ui_gate_text_input.py`
5. `pytest tests/test_ui_gate_text_input.py -v` — 5/5 PASS
6. `npm run build --prefix client` — exits 0
7. Full regression — zero new failures

## 5. Deliverables

- [ ] `#text-input-bar` in `index.html` — always visible
- [ ] Enter/Send → WS `player_input` message → clear + blur
- [ ] Gate UI-TEXT-INPUT: 5/5 PASS
- [ ] Zero regressions

## 6. Integration Seams

- **Files modified:** `client/index.html`, `client/src/main.ts`
- **Do not modify:** Any Three.js scene files, engine files
- **CSS:** Inline or in `index.html` `<style>` block — no new stylesheet

## Preflight

```bash
npm run build --prefix client
pytest tests/test_ui_gate_text_input.py -v
pytest tests/ -x -q --ignore=tests/test_ui_gate_text_input.py
```
