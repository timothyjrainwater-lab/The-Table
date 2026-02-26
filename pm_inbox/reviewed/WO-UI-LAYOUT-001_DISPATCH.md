# WO-UI-LAYOUT-001 — Two-Mode Layout: Exploration Frame / Combat Frame

**Issued:** 2026-02-25
**Lifecycle:** DISPATCH-READY
**Track:** UI
**Priority:** HIGH — gates all other UI polish WOs (FIND-POLISH-002)
**WO type:** ARCHITECTURE + IMPLEMENTATION
**Gate:** UI-LAYOUT-001 (10 tests)

---

## 0. Doctrine Hard Stops

**Read before writing a single line of code. These are non-negotiable.**

Sources: `DOCTRINE_04_TABLE_UI_MEMO_V4.txt` + `DOCTRINE_02_GOLDEN_TICKET_V12.txt`

**Design rule:** Every "how should this behave?" question resolves to: *what happens at a real D&D table?*

**Interaction grammar (fixed):**
`DECLARE (voice or sheet-click) → POINT (token/area) → CONFIRM (runtime) → RECORD (consent only)`

**Hard bans — if any of these appear in your implementation, it is an automatic REJECT:**
- NO tooltips, popovers, hover cards, or floating info windows
- NO snippets anywhere
- NO permanent map marks — ephemeral overlays only
- NO gamy action menus (cast / attack / end turn / roll buttons)
- NO roll buttons. No "click to roll." No radial roll. Authoritative rolls via `PENDING_ROLL` → tower drop only.
- NO autowrite to notebook. No silent logging. (GT NB-004 absolute ban)
- NO app chrome. No modal dialogs. No software panels. Everything is furniture.

**3D camera postures — DEAD.** `STANDARD / DOWN / LEAN_FORWARD / DICE` as posture modes do not exist in 2D. Do not reference them. Do not reintroduce them.

**Physical object set — the only things on this table:**
Table surface · MagicMap plane (battle grid) · Tokens · Rulebook · Character Sheet · Notebook · Handout printer slot + tray · Recycle well · Dice tray (felt, fidget, cosmetic only) · Dice tower (ritual, authoritative rolls only)

**Builder checklist (include in debrief Pass 1):**
- [ ] No roll buttons or click-to-roll patterns introduced
- [ ] No tooltips or floating UI elements introduced
- [ ] No hardcoded color values — all surfaces use `--skin-*` tokens
- [ ] No posture class references (posture-standard / posture-lean / posture-down / posture-dice)
- [ ] Layout mode is engine-driven only (`combat_start` / `combat_end`) — no player toggle

---

## 1. Target Lock

The current `client2d/` layout has a single static state. The right column (`#right-col`)
width changes when posture keys 1/2/3/4 are pressed, but there is no mode-aware layout that
responds to the game state. `combat_start` and `combat_end` events arrive at `main.js` and
only toggle a red glow on `#scene-surface`. That is the entire current combat response.

**Required:** Two distinct physical layout modes — Exploration Frame and Combat Frame — that
the engine drives automatically. The player does not manage UI state. The game does.

**Known gap:** `combat_ended` (FINDING-COMBAT-ENDED-001 LOW OPEN) is never emitted by the
engine. The layout must be built for both transitions, but the return slide will be inert
until the engine emits `combat_ended`. This is an accepted known gap — wire it now, it
activates automatically when the engine catches up.

---

## 2. Binary Decisions

| # | Decision | Answer |
|---|----------|--------|
| 1 | How is layout mode stored? | `body` class: `body.mode-explore` (default) and `body.mode-combat`. Same pattern as existing posture classes. |
| 2 | What triggers the transition? | WS events `combat_start` → add `body.mode-combat`, remove `body.mode-explore`. `combat_end` → reverse. Handled in `main.js`. |
| 3 | What does Exploration Frame look like? | `#right-col` expands to dominant width (~420px or 40% viewport). `#speaker-panel` gets maximum flex — large portrait area, narration strip visible. `#scene-surface` de-emphasized (dimmed or partially hidden behind right col). Battle canvas hidden. |
| 4 | What does Combat Frame look like? | `#right-col` compresses to compact sidebar (~200px). `#scene-surface` / battle map is now dominant and exposed. Right strip shows orb, initiative region stub, quick stats. |
| 5 | What is the transition? | CSS transition on `#right-col` width (and any other affected elements), same `--posture-speed: 0.35s` variable but can use a longer dedicated `--layout-speed: 0.5s` for the bigger movement. ease-out curve — fast start, slow settle, physical mass feeling. |
| 6 | What sound plays? | On mode change: play `assets/sounds/drawer-slide.wav` (or equivalent wood-slide asset) — same audio language as drawers. If asset doesn't exist yet, stub: `window.LAYOUT_SOUNDS = { explore: '', combat: '' }` (same pattern as `window.ORB_STANCE_CONFIG`). |
| 7 | What replaces posture classes on `#right-col`? | The posture class system (`body.posture-*`) is NOT removed by this WO. It coexists for now. WO-UI-POSTURE-AUDIT-001 will evaluate what gets cut. This WO adds the two-mode system on top without destroying the posture system. |
| 8 | Skin token stubs — required? | Yes. CSS custom properties for texture assets must be stubbed in this WO even if values are empty strings or placeholder colors. See Section 4. No hardcoded colors for any surface that will eventually carry a texture asset. |
| 9 | Battle map visibility in Exploration Frame? | Hidden — `display: none` or `visibility: hidden` on the canvas container. Not de-emphasized, not just smaller. Hidden. |
| 10 | Does scene-surface move or just reflow? | The scene-surface stays left. The right column slides in width. The battle canvas (inside scene-surface) is hidden/shown based on mode. No absolute positioning tricks — pure flexbox width transition. |

---

## 3. Layout Architecture

### Current structure (confirmed by PM audit)

```
body.posture-standard (or lean/down/dice)
├── #scene-surface          (left, flex 1)
│   └── #battle-canvas      (combat canvas)
└── #right-col              (right, fixed width 280px default)
    ├── #speaker-panel      (portrait, beats, orb)
    └── #dice-section       (slip-tray, handout-tray)
```

### Target structure (after this WO)

```
body.mode-explore (default) | body.mode-combat
├── #scene-surface          (left, flex 1)
│   └── #battle-canvas      (hidden in explore, visible in combat)
└── #right-col              (right — wide in explore, narrow in combat)
    ├── #speaker-panel      (tall/dominant in explore, compressed in combat)
    ├── #combat-strip       (NEW — initiative stub, visible only in combat)
    └── #dice-section       (slip-tray, handout-tray)
```

### CSS rules to add

```css
/* Layout speed — longer than posture, heavier movement */
:root {
  --layout-speed: 0.5s;
}

/* Exploration frame — right col dominant */
body.mode-explore #right-col {
  width: 420px;
  transition: width var(--layout-speed) cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

body.mode-explore #speaker-panel {
  flex: 8 0 0;
  max-height: none;
  transition: flex-basis var(--layout-speed) cubic-bezier(0.25, 0.46, 0.45, 0.94),
              max-height var(--layout-speed) cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

body.mode-explore #battle-canvas {
  display: none;
}

body.mode-explore #combat-strip {
  display: none;
}

/* Combat frame — battle map dominant */
body.mode-combat #right-col {
  width: 200px;
  transition: width var(--layout-speed) cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

body.mode-combat #speaker-panel {
  flex: 0 0 80px;
  max-height: 80px;
}

body.mode-combat #battle-canvas {
  display: block;
}

body.mode-combat #combat-strip {
  display: flex;
  flex-direction: column;
  flex: 1 0 0;
  padding: 8px;
  gap: 4px;
}
```

### JavaScript changes in main.js

Replace the current `combat_start`/`combat_end` handlers:

```javascript
// Remove: vaultZone.classList.add/remove('combat-active')

// Add:
const LAYOUT_SOUNDS = window.LAYOUT_SOUNDS || { combat: '', explore: '' };

function _playLayoutSound(key) {
  const src = LAYOUT_SOUNDS[key];
  if (src) { const a = new Audio(src); a.play().catch(() => {}); }
}

ws.on('combat_start', function () {
  document.body.classList.remove('mode-explore');
  document.body.classList.add('mode-combat');
  _playLayoutSound('combat');
});

ws.on('combat_end', function () {
  document.body.classList.remove('mode-combat');
  document.body.classList.add('mode-explore');
  _playLayoutSound('explore');
});
```

Default body class (in index.html `<body>` tag): `class="mode-explore"`.

### New HTML element: #combat-strip

Add to `#right-col` between `#speaker-panel` and `#dice-section`:

```html
<div id="combat-strip">
  <div id="initiative-stub" class="combat-label">— INITIATIVE —</div>
  <!-- Initiative order populated by future WO -->
</div>
```

---

## 4. Skin Token Stubs (MANDATORY)

This is a hard requirement. The layout WO must introduce CSS custom properties for every
surface that will eventually carry a texture asset. Values may be placeholder colors now —
the token names must be correct and present.

```css
:root {
  /* Table surface — wood grain (walnut default) */
  --skin-table-surface:   #2a1f14;       /* placeholder — will point at texture asset */
  --skin-drawer-face:     #3d2b1a;       /* placeholder */
  --skin-drawer-handle:   #8b6914;       /* placeholder — brass */
  --skin-felt-surface:    #1a4a2e;       /* placeholder — green felt */
  --skin-shelf-rail:      #3d2b1a;       /* placeholder */
  --skin-parchment:       #f4ead5;       /* placeholder */

  /* These replace any hardcoded color values in existing rules for the listed surfaces.
     All new rules added by this WO must use these tokens, not raw hex values.
     Existing rules that use hardcoded --walnut-dark etc. are NOT changed by this WO —
     that migration is WO-UI-TEXTURE-001 scope. */
}
```

Builder must use `--skin-*` tokens for all new CSS written in this WO. Existing CSS that
uses `--walnut-dark`, `--walnut-warm`, etc. is left untouched.

---

## 5. Gate Tests

**File:** `tests/test_ui_layout_001_gate.py`
**Gate:** UI-LAYOUT-001 — 10 tests

| ID | Test |
|----|------|
| LO-01 | `body` element has `mode-explore` class by default (on page load) |
| LO-02 | `#right-col` has width ≥ 380px in `mode-explore` |
| LO-03 | `#battle-canvas` is not displayed in `mode-explore` |
| LO-04 | `#combat-strip` is not displayed in `mode-explore` |
| LO-05 | WS `combat_start` message → `body.classList` contains `mode-combat` and not `mode-explore` |
| LO-06 | WS `combat_end` message → `body.classList` contains `mode-explore` and not `mode-combat` |
| LO-07 | `#right-col` has width ≤ 220px in `mode-combat` |
| LO-08 | `#battle-canvas` is displayed in `mode-combat` |
| LO-09 | `#combat-strip` is displayed in `mode-combat` |
| LO-10 | CSS custom properties `--skin-table-surface`, `--skin-drawer-face`, `--skin-felt-surface` exist on `:root` |

Tests must not require a live WebSocket — mock the `ws` event dispatch in the test harness.
Tests are structural/DOM checks, not visual.

---

## 6. Integration Seams

**Files touched:**
- `client2d/index.html` — add `class="mode-explore"` to `<body>`, add `#combat-strip` div
- `client2d/main.js` — replace `combat_start`/`combat_end` handlers, add `_playLayoutSound`, add `window.LAYOUT_SOUNDS` stub
- `client2d/style.css` (or equivalent) — add `body.mode-explore` / `body.mode-combat` rules, add `--layout-speed`, add `--skin-*` token stubs

**Files NOT touched:**
- `orb.js` — posture system left intact pending WO-UI-POSTURE-AUDIT-001
- Engine files — no changes
- `ws_bridge.py` — events already wired; no changes needed

---

## 7. Assumptions to Validate

1. `#battle-canvas` is the ID of the combat canvas element in `index.html` — confirm exact ID.
2. The `ws` object in `main.js` exposes `.on(event, handler)` — confirmed from existing wiring.
3. No existing test depends on `combat_start` adding `combat-active` to `#scene-surface` — builder checks before removing that behavior.
4. `--posture-speed` variable exists and is `0.35s` — confirmed by PM audit.
5. `body.mode-explore` + `body.posture-standard` coexistence: both classes on body simultaneously is acceptable for the transition period — confirmed by decision #7 above.

---

## 8. Preflight

```bash
python scripts/verify_session_start.py
python -m pytest tests/test_ui_2d_wiring.py -x -q
```

After implementation:
```bash
python -m pytest tests/test_ui_layout_001_gate.py -v
python -m pytest tests/ -q --tb=no 2>&1 | tail -5
```

No new failures permitted. Pre-existing baseline: 44.

---

## Delivery Footer

**Deliverables:**
- [ ] `client2d/index.html` — `body` default class, `#combat-strip` div
- [ ] `client2d/main.js` — two-mode event handlers, `window.LAYOUT_SOUNDS` stub
- [ ] `client2d/style.css` — `body.mode-explore` / `body.mode-combat` rules, `--layout-speed`, `--skin-*` token stubs
- [ ] `tests/test_ui_layout_001_gate.py` — 10/10

**Gate:** UI-LAYOUT-001 10/10
**Regression bar:** No new failures. Pre-existing count ≤ 44.

---

## Debrief Required

Builder files debrief to `pm_inbox/reviewed/DEBRIEF_WO-UI-LAYOUT-001.md` on completion.

**Three-pass format:**
- Pass 1: per-file breakdown, confirmed assumptions table, open findings
- Pass 2: PM summary ≤100 words
- Pass 3: retrospective — drift caught, patterns, recommendations

Missing debrief or missing Pass 3 = REJECT.

---

## Audio Cue

```bash
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```
