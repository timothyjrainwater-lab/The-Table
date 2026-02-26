# DEBRIEF — WO-UI-LAYOUT-001
**Dispatched:** 2026-02-25
**Gate:** LO 10/10 PASS
**Regression:** 28 pre-existing failures, 0 new failures. Full suite 7715 pass.

---

## Pass 1 — Per-File Breakdown

### `client2d/index.html`

**Changes:**
- `<body class="posture-standard">` → `<body class="mode-explore">`
- Added `#combat-strip` div inside `#right-col` between `#speaker-panel` and `#orb-transcript`:
  ```html
  <div id="combat-strip">
    <div id="initiative-stub" class="combat-label">— INITIATIVE —</div>
  </div>
  ```
- Removed `<span id="posture-label">STANDARD</span>` from `#shelf-zone`

**Open findings:**

| ID | Severity | Finding | Status |
|----|----------|---------|--------|
| LO-F1 | INFO | WO spec referenced `#battle-canvas` as combat canvas ID; actual ID in HTML is `#scene-canvas` | No impact — implementation uses correct `#scene-canvas` |

### `client2d/main.js`

**Changes (complete rewrite):**
- Removed: `POSTURE_MAP`, `POSTURE_LABEL_MAP`, `ALL_POSTURE_CLASSES`, `setPosture()`, keydown posture handler (keys 1–4)
- Preserved: `player-input` focus/blur guard (lines 18–19), Enter keydown handler (lines 28–33), `submitInput()`, WsBridge instantiation, `speaking_start`/`speaking_stop` orb toggle, narration handler, wildcard stub, `window.__ws` exposure
- Added: `LAYOUT_SOUNDS` stub, `_playLayoutSound(key)`, `ws.on('combat_start', ...)` handler, `ws.on('combat_end', ...)` handler

### `client2d/style.css`

**Changes:**
- Added to `:root`: `--layout-speed: 0.5s`, skin tokens (`--skin-table-surface`, `--skin-drawer-face`, `--skin-drawer-handle`, `--skin-felt-surface`, `--skin-shelf-rail`, `--skin-parchment`)
- Removed: `#posture-label` CSS rule
- Removed: Section 12 posture classes (4 rules: `body.posture-standard`, `body.posture-lean`, `body.posture-down`, `body.posture-dice`)
- Added: `body.mode-explore` and `body.mode-combat` rules for `#right-col`, `#speaker-panel`, `#scene-canvas`, `#combat-strip`
- Added: `#combat-strip` base rule and `.combat-label` styles

---

## Pass 2 — PM Summary (≤100 words)

WO-UI-LAYOUT-001 delivered. Three files changed. `index.html` body class changed to `mode-explore`; `#combat-strip` added to `#right-col`; `#posture-label` removed. `main.js` rewritten: posture system removed, `combat_start`/`combat_end` WS handlers added; focus guard and speaking handlers preserved. `style.css`: posture classes removed, `mode-explore`/`mode-combat` rules added, skin token stubs declared. One ID drift found (`#battle-canvas` spec vs `#scene-canvas` actual) — no functional impact. LO 10/10 gate pass. Regression clean (28 pre-existing).

---

## Pass 3 — Retrospective

**Drift caught:**
- `#battle-canvas` (spec assumption #1) vs `#scene-canvas` (actual HTML). Implementation correctly used `#scene-canvas`. WO spec should have verified the ID before dispatch.

**Gate test bug caught:**
- LO-05 and LO-06 searched for `'combat_start'` string from first occurrence, which landed in a comment block. The 300-char window didn't reach the `ws.on(...)` binding. Fixed by using regex search for `ws\.on\(['"]combat_start['"]` to locate the handler binding specifically.

**Patterns:**
- The mode-switch approach (engine-driven body class toggle) is structurally cleaner than the old keydown posture system. No client-side state to track — body class is the single source of truth.
- `_playLayoutSound()` stub follows the same pattern as orb's `ORB_STANCE_CONFIG` — asset paths are empty strings by default, ready for a future WO to populate.
- Skin tokens (`--skin-*`) declared as empty stubs in `:root`. They have no visual effect until assigned. This is intentional — they define the hook points for a future texture/skin WO.

**Recommendations:**
- When WO specs reference DOM IDs by assumption, the spec should carry a `VERIFY:` annotation. ID drift (`#battle-canvas` vs `#scene-canvas`) is a low-cost mistake to catch pre-dispatch.
- `#combat-strip` initiative slot is a stub (`— INITIATIVE —` label only). The real initiative order population belongs in a future WO.
- Gate tests that search comment text first should use a targeted regex (e.g., `ws\.on\(`) rather than `.index()` on the raw event string.
