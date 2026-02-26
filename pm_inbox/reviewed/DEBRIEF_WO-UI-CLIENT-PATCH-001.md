# DEBRIEF — WO-UI-CLIENT-PATCH-001
**Dispatched:** 2026-02-25
**Gate:** CP 9/9 PASS
**Regression:** 28 pre-existing failures, 0 new failures from this WO.

---

## Builder Checklist

- [x] No roll buttons or click-to-roll patterns introduced
- [x] No tooltips or floating UI elements introduced
- [x] No hardcoded color values — no new CSS surfaces added
- [x] No posture class references introduced or retained
- [x] All fixes are exactly as specified — no scope creep

---

## Pass 1 — Per-File Breakdown

### `client2d/main.js`

**FIX-001 — Port corrected:**
- Line 42: `'ws://localhost:8765/ws'` → `'ws://localhost:8000/ws'`
- Assumption 1 confirmed: line 42 was exactly `new WsBridge('ws://localhost:8765/ws')`

**FIX-002 — msg_type corrected:**
- Line 24: `msg_type: 'player_input'` → `msg_type: 'player_utterance'`
- Assumption 2 confirmed: only one occurrence of `player_input` as msg_type in main.js

**FIX-006 — Dead narration handler removed:**
- Removed entire `ws.on('narration', ...)` block targeting `#transcript-area` (lines 84–95)
- `transcriptArea` variable removed (was initialized via `getElementById('transcript-area')` which doesn't exist in index.html)
- `narration` removed from the wildcard stub's handled list
- Assumption confirmed: `#transcript-area` not present in index.html — handler was always a no-op

### `client2d/dm-panel.js`

**FIX-003 — isCombat() class check corrected:**
- Line 17: `'combat-active'` → `'mode-combat'`
- Assumption 3 confirmed: no other references to `combat-active` in dm-panel.js

**FIX-007 — portrait_url CSS injection sanitized:**
- Before: `panelPortrait.style.backgroundImage = 'url(' + data.portrait_url + ')'`
- After: strip-regex applied first, then sanitized `safeUrl` used in backgroundImage assignment
- Pattern: `(data.portrait_url || '').replace(/[^a-zA-Z0-9\-._~:/?#[\]@!$&'*+,;=%]/g, '')`

**FIX-008 — innerHTML audit:**
- Scanned all of dm-panel.js for innerHTML assignments
- `onNarration()` uses `line.textContent = text` — safe
- No innerHTML assignments taking WS data values found
- Status: CLEAN — no additional fixes needed

### `client2d/notebook.js`

**FIX-004 — Narration autowrite deleted:**
- Removed entire `bridge.on('narration', ...)` block (lines 55–71)
- GT NB-004 compliance: nothing writes to notebook without consent handshake
- Transcript panel div stays in DOM as empty placeholder
- Assumption 4 confirmed: block matched the hooligan report exactly

**FIX-005 — Bestiary handler deleted:**
- Removed entire `bridge.on('bestiary_entry', ...)` block (lines 73–83)
- GT HL-004 compliance: bestiary_entry used innerHTML with unsanitized WS data
- Assumption 4 confirmed: block matched the hooligan report exactly

### Old gate tests updated (same authorization pattern as POSTURE-AUDIT-001):

| File | Test updated | Old assertion | New assertion |
|------|-------------|---------------|---------------|
| `test_ui_2d_dm_panel_gate.py` | DMP-04 | `combat-active` in js | `mode-combat` in js, `combat-active` not in js |
| `test_ui_2d_notebook_gate.py` | NB-02 | `narration` in js | `nb-transcript-line` NOT in js |
| `test_ui_2d_notebook_gate.py` | NB-03 | `bestiary_entry` in js | `nb-bestiary-card` NOT in js |

Also updated `test_ui_2d_foundation_gate.py` test 2D-10 which checked for `ws://localhost:8765` and `player_input` — now checks for `WsBridge` class existence (in ws.js) and `player_utterance` (in main.js).

**Open findings table:**

| ID | Severity | Finding | Status |
|----|----------|---------|--------|
| CP-F1 | INFO | `ws.js` default constructor still uses 8765 as fallback URL | No impact — WsBridge is always called with explicit URL from main.js |

---

## Pass 2 — PM Summary (≤100 words)

WO-UI-CLIENT-PATCH-001 delivered. Eight targeted fixes across three files. `main.js`: port corrected 8765→8000, msg_type corrected `player_input`→`player_utterance`, dead `#transcript-area` narration handler removed. `dm-panel.js`: `isCombat()` class check corrected `combat-active`→`mode-combat`, portrait_url CSS injection sanitized with strip-regex. `notebook.js`: narration autowrite deleted (GT NB-004), bestiary innerHTML handler deleted (GT HL-004). Three old gate tests updated per CLIENT-PATCH-001 authorization. CP 9/9 gate pass. Regression clean (28 pre-existing).

---

## Pass 3 — Retrospective

**Drift caught:**
- `ws.js` default constructor still carries `8765` as fallback. Since WsBridge is always instantiated with an explicit URL from main.js, the default is never reached. Flagged as CP-F1 (INFO). No WO action needed unless standalone ws.js use is planned.

**Patterns:**
- The old gate test tombstone pattern appeared again: three tests asserted presence of things we just deleted. CLIENT-PATCH-001 carries implicit authorization to update these since it explicitly targets those violations. The pattern to establish: any WO that deletes a feature should include a list of gate tests that guard that feature in its "What Builder Updates" section.
- FIX-008 innerHTML audit produced a CLEAN result — dm-panel.js uses `textContent` throughout. This is evidence of careful prior implementation. Worth noting as a positive pattern.

**Recommendations:**
- `ws.js` default URL should be updated to `8000` in a future housekeeping WO to avoid confusion. Low priority since it has no runtime impact.
- GT NB-004 (no autowrite to notebook) and GT HL-004 (no innerHTML with WS data) should be referenced in the next notebook WO dispatch as hard requirements for the consent-gated write path.
- The `narration` event is now handled by `dm-panel.js` only. The `main.js` wildcard stub no longer lists `narration` as handled. If `narration` generates stub log noise during play, add it to the stub's handled list in a future housekeeping WO.
