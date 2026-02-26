# WO-UI-CLIENT-PATCH-001 — Client Structural Patch + Hard Law Cleanup

**Issued:** 2026-02-25
**Lifecycle:** ACCEPTED — debrief filed 2026-02-25
**Track:** UI
**Priority:** CRITICAL — client cannot connect to backend in current state
**WO type:** PATCH (targeted fixes only — no new features, no new architecture)
**Gate:** UI-CLIENT-PATCH-001 (9 tests)

**Source:** ANVIL_CLIENT_HOOLIGAN_001.md — Violations 001–006

---

## 0. Doctrine Hard Stops

**Hard bans — if any of these appear in your implementation, it is an automatic REJECT:**
- NO tooltips, popovers, hover cards, or floating info windows
- NO snippets anywhere
- NO roll buttons. No click-to-roll. No radial roll.
- NO autowrite to notebook. No silent logging. (GT NB-004 absolute ban)
- NO app chrome. No modal dialogs. No software panels.
- NO new features. This WO is deletions and one-line fixes only.

**Builder checklist (include in debrief Pass 1):**
- [ ] No roll buttons or click-to-roll patterns introduced
- [ ] No tooltips or floating UI elements introduced
- [ ] No hardcoded color values — all surfaces use `--skin-*` tokens
- [ ] No posture class references introduced or retained
- [ ] All fixes are exactly as specified — no scope creep

---

## 1. Target Lock

Six targeted fixes from the Anvil hooligan run. Three are structural blockers that
prevent the client from ever connecting to the backend. Two are hard law deletions
(GT NB-004, GT HL-004) already on the findings board. One is dead code removal.

No design decisions required. No new architecture. Every fix is a deletion or a
one-string change. Do exactly what is specified. Nothing more.

---

## 2. Fixes

### FIX-001 — Wrong WebSocket port
**File:** `client2d/main.js` line 42
**Violation:** VIOLATION-004 (CRITICAL)

Change:
```javascript
const ws = new WsBridge('ws://localhost:8765/ws');
```
To:
```javascript
const ws = new WsBridge('ws://localhost:8000/ws');
```

---

### FIX-002 — Wrong message type for player text input
**File:** `client2d/main.js` line 24
**Violation:** VIOLATION-003 (HIGH)

Change:
```javascript
ws.send({ msg_type: 'player_input', text: text });
```
To:
```javascript
ws.send({ msg_type: 'player_utterance', text: text });
```

---

### FIX-003 — Combat detection checks wrong class
**File:** `client2d/dm-panel.js` line 17
**Violation:** VIOLATION-006 (HIGH)

Change:
```javascript
return document.body.classList.contains('combat-active');
```
To:
```javascript
return document.body.classList.contains('mode-combat');
```

---

### FIX-004 — Delete narration autowrite from notebook.js
**File:** `client2d/notebook.js` lines 55–71
**Violation:** VIOLATION-001 (CRITICAL — GT NB-004)

Delete the entire `bridge.on('narration', ...)` block. The full block to remove:

```javascript
bridge.on('narration', function (d) {
  var text = (d && d.text) ? d.text : '';
  if (!text) return;
  var line = document.createElement('div');
  line.className = 'nb-transcript-line';
  line.textContent = text;
  transcriptPanel.appendChild(line);
  // Cap at MAX_TRANSCRIPT
  while (transcriptPanel.children.length > MAX_TRANSCRIPT) {
    transcriptPanel.removeChild(transcriptPanel.firstChild);
  }
  // Auto-scroll if transcript tab is active
  var tBtn = drawer.querySelector('[data-tab="transcript"]');
  if (tBtn && tBtn.classList.contains('active')) {
    transcriptPanel.scrollTop = transcriptPanel.scrollHeight;
  }
});
```

Do not replace it with anything. The transcript panel stays in the DOM as an
empty placeholder. Write path will be implemented in WO-UI-NOTEBOOK-001 with
a full consent handshake. Until then: nothing writes to it.

---

### FIX-005 — Delete bestiary handler from notebook.js
**File:** `client2d/notebook.js` lines 73–83
**Violation:** VIOLATION-002 (HIGH — GT HL-004)

Delete the entire `bridge.on('bestiary_entry', ...)` block:

```javascript
bridge.on('bestiary_entry', function (d) {
  var card = document.createElement('div');
  card.className = 'nb-bestiary-card';
  card.innerHTML =
    '<div class="nb-bestiary-name">' + (d.name || 'Unknown') + '</div>' +
    '<div class="nb-bestiary-stat">CR ' + (d.cr || '?') +
      ' &nbsp;|&nbsp; HP ' + (d.hp || '?') +
      ' &nbsp;|&nbsp; AC ' + (d.ac || '?') + '</div>' +
    (d.attacks ? '<div class="nb-bestiary-stat">' + d.attacks + '</div>' : '');
  bestiaryPanel.appendChild(card);
});
```

Beast Journal belongs in WO-UI-RULEBOOK-001. Do not replace this with anything.

---

### FIX-006 — Remove dead narration handler from main.js
**File:** `client2d/main.js` lines 84–95
**Violation:** VIOLATION-005 (MEDIUM — dead code)

The `narration` handler in `main.js` targets `#transcript-area` which does not
exist in `index.html`. It always no-ops. Remove the entire block. `dm-panel.js`
is the correct owner of narration display.

Builder: read `main.js` lines 84–95 to confirm the exact block before deleting.
The block will be a `ws.on('narration', ...)` handler that references
`transcriptArea` (which was initialized via `getElementById('transcript-area')`).

---

### FIX-007 — Sanitize innerHTML in dm-panel.js portrait_url
**File:** `client2d/dm-panel.js` — portrait handler
**Violation:** XSS / CSS injection surface (SECURITY)

The portrait handler sets:
```javascript
panelPortrait.style.backgroundImage = 'url(' + data.portrait_url + ')';
```
A `portrait_url` containing `)` breaks out of the CSS string. Strip everything
except safe URL characters before assignment:

```javascript
var safeUrl = (data.portrait_url || '').replace(/[^a-zA-Z0-9\-._~:/?#[\]@!$&'*+,;=%]/g, '');
panelPortrait.style.backgroundImage = 'url(' + safeUrl + ')';
```

Builder: locate the exact line in `dm-panel.js` that assigns `backgroundImage`
from WS data and apply this sanitization pattern.

---

### FIX-008 — Remove innerHTML from future bestiary/DM panel handlers
**Note:** FIX-005 already deletes the `notebook.js` bestiary handler which used
`innerHTML` with unsanitized WS data (`d.name`, `d.attacks`). No additional action
needed for notebook — the delete is sufficient.

For `dm-panel.js`: builder scans for any remaining `innerHTML` assignments that
take values directly from WS message fields. Each one must either:
- Use `textContent` instead (for text values), or
- Sanitize with `DOMPurify` or the strip-regex pattern (for HTML values)

Report all occurrences found in debrief Pass 1.

---

## 3. What Builder Does NOT Touch

- `slip.js` — VIOLATION-007 (roll_confirm click) is WO-UI-DICE-001 scope. Do not touch.
- `sheet.js` — Not in scope for this WO.
- `orb.js` — Not in scope.
- `style.css` / `index.html` dead posture attributes — cosmetic noise, separate cleanup.
- No new event handlers. No new CSS. No new HTML beyond the sanitization fixes.

---

## 4. Gate Tests

**File:** `tests/test_ui_client_patch_001_gate.py`
**Gate:** UI-CLIENT-PATCH-001 — 9 tests

| ID | Test |
|----|------|
| CP-01 | `main.js` contains `ws://localhost:8000/ws` |
| CP-02 | `main.js` does not contain `ws://localhost:8765` |
| CP-03 | `main.js` contains `player_utterance` (submit handler) |
| CP-04 | `main.js` does not contain `player_input` as a msg_type string |
| CP-05 | `dm-panel.js` contains `mode-combat` in `isCombat()` |
| CP-06 | `notebook.js` does not contain `nb-transcript-line` (autowrite class removed) |
| CP-07 | `notebook.js` does not contain `nb-bestiary-card` (bestiary handler removed) |
| CP-08 | `dm-panel.js` does not contain `'url(' + data.portrait_url` (raw CSS injection pattern gone) |
| CP-09 | `dm-panel.js` contains `replace(` near `backgroundImage` (sanitization present) |

Tests are static source scans — no browser required.

---

## 5. Integration Seams

**Files touched:**
- `client2d/main.js` — FIX-001, FIX-002, FIX-006
- `client2d/dm-panel.js` — FIX-003, FIX-007, FIX-008 (innerHTML audit)
- `client2d/notebook.js` — FIX-004, FIX-005

**Files NOT touched:**
- `client2d/slip.js`
- `client2d/sheet.js`
- `client2d/orb.js`
- `client2d/style.css`
- `client2d/index.html`
- Engine files
- `ws_bridge.py`

---

## 6. Assumptions to Validate

1. `main.js` line 42 is exactly `new WsBridge('ws://localhost:8765/ws')` — builder
   confirms before changing.
2. `main.js` line 24 is the only place `player_input` is sent as a msg_type — builder
   scans for other occurrences before patching.
3. `dm-panel.js` has no other references to `combat-active` beyond `isCombat()` —
   builder confirms.
4. The `narration` and `bestiary_entry` handlers in `notebook.js` are the complete
   blocks as shown in the hooligan report — builder reads before deleting.
5. No existing gate test checks for `ws://localhost:8765` or `player_input` msg_type
   presence — if any do, they must be updated in this WO.

---

## 7. Preflight

```bash
python scripts/verify_session_start.py
python -m pytest tests/ -q --tb=no 2>&1 | tail -5
```

After implementation:
```bash
python -m pytest tests/test_ui_client_patch_001_gate.py -v
python -m pytest tests/ -q --tb=no 2>&1 | tail -5
```

No new failures permitted. Pre-existing baseline: 28.

---

## Delivery Footer

**Deliverables:**
- [ ] `client2d/main.js` — port fixed, msg_type fixed, dead handler removed
- [ ] `client2d/dm-panel.js` — `isCombat()` class fixed, portrait_url sanitized, innerHTML audit complete
- [ ] `client2d/notebook.js` — autowrite deleted, bestiary handler deleted
- [ ] `tests/test_ui_client_patch_001_gate.py` — 9/9

**Gate:** UI-CLIENT-PATCH-001 9/9
**Regression bar:** No new failures. Pre-existing count ≤ 28.

---

## Debrief Required

Builder files debrief to `pm_inbox/reviewed/DEBRIEF_WO-UI-CLIENT-PATCH-001.md`.

**Three-pass format:**
- Pass 1: per-file breakdown, confirmed assumptions, any additional findings discovered
- Pass 2: PM summary ≤100 words
- Pass 3: retrospective — anything that didn't match spec, recommendations

Missing debrief or missing Pass 3 = REJECT.

---

## Audio Cue

```bash
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```
