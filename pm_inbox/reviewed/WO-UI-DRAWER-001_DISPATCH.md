# WO-UI-DRAWER-001 — Slide-Up Drawer System + Voice-First Shelf Redesign

**Issued:** 2026-02-25
**Lifecycle:** ACCEPTED — debrief filed 2026-02-25
**Track:** UI
**Priority:** HIGH — blocked on WO-UI-LAYOUT-001 ACCEPTED before dispatch
**WO type:** IMPLEMENTATION
**Gate:** UI-DRAWER-001 (10 tests)

**Dependency:** WO-UI-LAYOUT-001 must be ACCEPTED before this WO is dispatched. The
two-mode layout skeleton must be in place before drawers are wired into it.

---

## 0. Doctrine Hard Stops

**Read before writing a single line of code. These are non-negotiable.**

Sources: `DOCTRINE_04_TABLE_UI_MEMO_V4.txt` + `DOCTRINE_02_GOLDEN_TICKET_V12.txt`

**Design rule:** Every "how should this behave?" question resolves to: *what happens at a real D&D table?*

**Hard bans — if any of these appear in your implementation, it is an automatic REJECT:**
- NO tooltips, popovers, hover cards, or floating info windows
- NO snippets anywhere
- NO gamy action menus or software-style buttons inside drawer interiors
- NO roll buttons. No "click to roll." No radial roll. (Dice WO is separate — that constraint applies there too.)
- NO autowrite to notebook. No silent logging. (GT NB-004 absolute ban)
- NO app chrome. No modal dialogs. No software panels. Drawers are furniture.

**3D camera postures — DEAD.** Do not reference `posture-standard / posture-lean / posture-down / posture-dice`. Do not bind drawer open/close to posture classes. The drawer system replaces posture switching entirely.

**Physical object set — drawers contain physical objects, not software panels:**
Notebook = physical page-turn book · Rulebook = read-only canon book · Character Sheet = read-only sheets · Dice Bag = felt-lined bag with dice inside

**Builder checklist (include in debrief Pass 1):**
- [ ] No roll buttons or click-to-roll patterns introduced
- [ ] No tooltips or floating UI elements introduced
- [ ] No hardcoded color values — all surfaces use `--skin-*` tokens (from WO-UI-LAYOUT-001)
- [ ] No posture class references introduced or retained
- [ ] Drawer open/close is handle-driven only — no programmatic open except mutual-exclusion close
- [ ] Sound stubs (`window.DRAWER_SOUNDS`) present even if assets are empty strings

---

## 1. Target Lock

Covers FIND-POLISH-001, FIND-POLISH-003.

The current shelf zone (`#shelf-zone`) has four buttons that toggle posture classes on
`<body>`. This is not the intended design. Each button should open a **slide-up drawer**
from the bottom of the screen — a physical wooden drawer with a pull handle, felt or
wood interior, mutually exclusive with other drawers. The text input bar currently
dominates the shelf zone; it should be small and tucked, subordinate to voice input.

---

## 2. Binary Decisions

| # | Decision | Answer |
|---|----------|--------|
| 1 | Where do drawers attach? | Each drawer is a fixed-position div that slides up from the bottom edge, above the shelf rail. Bottom: shelf height (~52px). Height: ~40–50% of viewport when open. |
| 2 | How does open/close work? | CSS `transform: translateY(100%)` (closed) → `transform: translateY(0)` (open). Transition: `var(--drawer-speed)` with ease-out curve (fast open, slow settle). Class `.drawer-open` applied to the drawer div. |
| 3 | Mutual exclusion? | Yes. Only one drawer open at a time. Opening a drawer closes any currently open drawer (remove `.drawer-open` from all, add to target). Clicking the same handle again closes it. |
| 4 | What is the handle? | A `<button class="drawer-handle">` element with visible weight. Each drawer gets its own handle embedded in the shelf rail. Not a text label — a styled element that reads as graspable. See Section 3 for handle spec. |
| 5 | What does `#shelf-zone` become? | A rail of drawer handles along the bottom. No dominant text input. Voice orb button (or mic icon) is the primary element. Text input: `#player-input` stays but is restyled as a small secondary element. |
| 6 | Which drawers are built in this WO? | Four: Sheet, Notebook, Tome, Dice Bag. Battle Mat drawer is FIND-POLISH-002 scope (WO-UI-LAYOUT-001 or a follow-up). |
| 7 | Drawer interior styling? | Each drawer gets a base interior style. Sheet/Notebook/Tome: parchment-toned interior. Dice Bag: green felt (`--skin-felt-surface`) — felt nap texture stub. Interior uses `--skin-*` tokens (defined in WO-UI-LAYOUT-001). |
| 8 | Sound? | On drawer open: `assets/sounds/drawer-open.wav` (wood slide). On close: `assets/sounds/drawer-close.wav` (soft thud). If assets don't exist: `window.DRAWER_SOUNDS = { open: '', close: '' }` stub — same pattern as `window.ORB_STANCE_CONFIG`. |
| 9 | Does the posture system get removed? | No. WO-UI-POSTURE-AUDIT-001 handles posture cleanup. The old `data-posture` attributes on shelf buttons are removed by this WO (they no longer serve a function), but `body.posture-*` classes in CSS are not touched. |
| 10 | Tome drawer contents? | Empty interior with label "TOME" for now. Rulebook content is a separate WO. |

---

## 3. Handle Spec

Each drawer handle in `#shelf-zone`:

```html
<button class="drawer-handle" data-drawer="sheet-drawer" aria-label="Character Sheet">
  <span class="handle-label">SHEET</span>
</button>
```

CSS requirements:
- Minimum height: 44px (touch target)
- Minimum width: 80px
- Background: `--skin-drawer-handle` (defined in WO-UI-LAYOUT-001 skin tokens)
- Border: 1px solid with warm wood tone
- Box shadow: subtle drop shadow + inset highlight to suggest depth/emboss
- Font: small caps, brass-toned label
- `:active` state: slight inset (transform: translateY(1px) or box-shadow inset) — physical press feel
- No browser default button chrome

---

## 4. Drawer Structure

### HTML additions to index.html

Replace existing shelf-item buttons. New structure:

```html
<div id="shelf-zone">
  <!-- Drawer handles -->
  <button class="drawer-handle" data-drawer="sheet-drawer" aria-label="Character Sheet">
    <span class="handle-label">SHEET</span>
  </button>
  <button class="drawer-handle" data-drawer="notebook-drawer" aria-label="Notebook">
    <span class="handle-label">NOTEBOOK</span>
  </button>
  <button class="drawer-handle" data-drawer="tome-drawer" aria-label="Tome">
    <span class="handle-label">TOME</span>
  </button>
  <button class="drawer-handle" data-drawer="dice-drawer" aria-label="Dice Bag">
    <span class="handle-label">DICE BAG</span>
  </button>

  <!-- Voice-first input zone -->
  <div id="voice-zone">
    <button id="voice-btn" aria-label="Speak">&#9679;</button>
    <input id="player-input" type="text" placeholder="or type…" autocomplete="off" />
    <button id="send-btn">&#9654;</button>
  </div>

  <!-- Posture label (kept for now, POSTURE-AUDIT-001 will evaluate removal) -->
  <span id="posture-label">STANDARD</span>
</div>

<!-- Drawers (above shelf zone, slide up from bottom) -->
<div id="sheet-drawer" class="drawer" role="region" aria-label="Character Sheet">
  <div class="drawer-interior drawer-parchment">
    <!-- Character sheet content — populated by future WO -->
    <p class="drawer-placeholder">CHARACTER SHEET</p>
  </div>
</div>

<div id="notebook-drawer" class="drawer" role="region" aria-label="Notebook">
  <div class="drawer-interior drawer-parchment">
    <p class="drawer-placeholder">NOTEBOOK</p>
  </div>
</div>

<div id="tome-drawer" class="drawer" role="region" aria-label="Tome">
  <div class="drawer-interior drawer-parchment">
    <p class="drawer-placeholder">TOME</p>
  </div>
</div>

<div id="dice-drawer" class="drawer" role="region" aria-label="Dice Bag">
  <div class="drawer-interior drawer-felt">
    <!-- Dice content — WO-UI-DICE-001 scope -->
    <p class="drawer-placeholder">DICE BAG</p>
  </div>
</div>
```

### CSS additions

```css
:root {
  --drawer-speed: 0.35s;
  --shelf-height: 52px;
  --drawer-height: 45vh;
}

/* Base drawer — closed by default */
.drawer {
  position: fixed;
  left: 0;
  right: 0;
  bottom: var(--shelf-height);
  height: var(--drawer-height);
  transform: translateY(100%);
  transition: transform var(--drawer-speed) cubic-bezier(0.25, 0.46, 0.45, 0.94);
  z-index: 100;
  overflow: hidden;
  border-top: 2px solid var(--skin-drawer-face, #3d2b1a);
  box-shadow: 0 -4px 20px rgba(0,0,0,0.5);
}

/* Open state */
.drawer.drawer-open {
  transform: translateY(0);
}

/* Interior styles */
.drawer-interior {
  width: 100%;
  height: 100%;
  padding: 16px;
  overflow-y: auto;
}

.drawer-parchment {
  background: var(--skin-parchment, #f4ead5);
  color: #2a1a0a;
}

.drawer-felt {
  background: var(--skin-felt-surface, #1a4a2e);
  color: #d4f0c0;
}

/* Drawer handle */
.drawer-handle {
  height: 44px;
  min-width: 80px;
  background: var(--skin-drawer-handle, #5c3d22);
  border: 1px solid #8b6914;
  border-radius: 3px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.1);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.1s, box-shadow 0.1s;
}

.drawer-handle:active {
  transform: translateY(1px);
  box-shadow: 0 1px 2px rgba(0,0,0,0.4), inset 0 1px 0 rgba(0,0,0,0.1);
}

.handle-label {
  font-size: 11px;
  font-variant: small-caps;
  letter-spacing: 0.08em;
  color: var(--skin-parchment, #f4ead5);
  pointer-events: none;
}

/* Voice zone — text input subordinate */
#voice-zone {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  justify-content: flex-end;
}

#player-input {
  width: 160px;  /* was dominant — now small and tucked */
  font-size: 12px;
}

#voice-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--skin-drawer-handle, #5c3d22);
  border: 1px solid #8b6914;
  color: var(--skin-parchment, #f4ead5);
  font-size: 16px;
  cursor: pointer;
}
```

### JavaScript additions to main.js

```javascript
// Drawer system
const DRAWER_SOUNDS = window.DRAWER_SOUNDS || { open: '', close: '' };

function _playDrawerSound(type) {
  const src = DRAWER_SOUNDS[type];
  if (src) { const a = new Audio(src); a.play().catch(() => {}); }
}

function _closeAllDrawers() {
  document.querySelectorAll('.drawer.drawer-open').forEach(d => {
    d.classList.remove('drawer-open');
  });
}

document.querySelectorAll('.drawer-handle').forEach(btn => {
  btn.addEventListener('click', () => {
    const drawerId = btn.dataset.drawer;
    const drawer = document.getElementById(drawerId);
    if (!drawer) return;

    const isOpen = drawer.classList.contains('drawer-open');
    _closeAllDrawers();
    if (!isOpen) {
      drawer.classList.add('drawer-open');
      _playDrawerSound('open');
    } else {
      _playDrawerSound('close');
    }
  });
});
```

---

## 5. Gate Tests

**File:** `tests/test_ui_drawer_001_gate.py`
**Gate:** UI-DRAWER-001 — 10 tests

| ID | Test |
|----|------|
| DR-01 | All four drawer divs exist in DOM: `#sheet-drawer`, `#notebook-drawer`, `#tome-drawer`, `#dice-drawer` |
| DR-02 | All four drawers have class `drawer` and do not have class `drawer-open` on page load |
| DR-03 | All four `.drawer-handle` buttons exist in `#shelf-zone` with correct `data-drawer` attributes |
| DR-04 | Clicking handle opens corresponding drawer (adds `drawer-open` class) |
| DR-05 | Clicking an open drawer handle closes it (removes `drawer-open` class) |
| DR-06 | Opening drawer A while drawer B is open closes B and opens A (mutual exclusion) |
| DR-07 | `#dice-drawer .drawer-interior` has class `drawer-felt` |
| DR-08 | `#sheet-drawer`, `#notebook-drawer`, `#tome-drawer` interiors have class `drawer-parchment` |
| DR-09 | `window.DRAWER_SOUNDS` object exists with `open` and `close` keys |
| DR-10 | `#player-input` width is ≤ 200px (text input is small and tucked, not dominant) |

---

## 6. Integration Seams

**Files touched:**
- `client2d/index.html` — replace shelf buttons, add drawer divs, add `#voice-zone`
- `client2d/main.js` — add drawer system JavaScript, add `window.DRAWER_SOUNDS` stub
- `client2d/style.css` — add drawer CSS, handle CSS, voice zone CSS

**Files NOT touched:**
- `orb.js` — posture system intact (WO-UI-POSTURE-AUDIT-001 scope)
- Engine files
- `ws_bridge.py`

**Existing drawers in HTML:** `sheet-drawer` and `notebook-drawer` divs already exist in
some form per prior WOs. Builder confirms their current markup before replacing.

---

## 7. Assumptions to Validate

1. `#shelf-zone` ID exists in current `index.html` — confirmed by PM audit.
2. `#player-input` and `#send-btn` exist and must be preserved (just restyled/relocated).
3. Existing `data-posture` attributes on shelf buttons are safe to remove — they only
   triggered posture switches which this WO is replacing with drawer opens.
4. `--skin-*` CSS tokens are defined in `:root` by WO-UI-LAYOUT-001 before this WO runs —
   this WO depends on them but does not define them.
5. No existing gate test checks for `data-posture` attribute presence on shelf buttons.

---

## 8. Preflight

```bash
python scripts/verify_session_start.py
python -m pytest tests/test_ui_layout_001_gate.py -x -q  # WO-UI-LAYOUT-001 must be ACCEPTED
```

After implementation:
```bash
python -m pytest tests/test_ui_drawer_001_gate.py -v
python -m pytest tests/ -q --tb=no 2>&1 | tail -5
```

---

## Delivery Footer

**Deliverables:**
- [ ] `client2d/index.html` — shelf handles, drawer divs, voice zone
- [ ] `client2d/main.js` — drawer open/close/sound logic, `window.DRAWER_SOUNDS` stub
- [ ] `client2d/style.css` — drawer CSS, handle CSS, voice zone CSS
- [ ] `tests/test_ui_drawer_001_gate.py` — 10/10

**Gate:** UI-DRAWER-001 10/10
**Regression bar:** No new failures. Pre-existing count ≤ 44.

---

## Debrief Required

Builder files debrief to `pm_inbox/reviewed/DEBRIEF_WO-UI-DRAWER-001.md` on completion.

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
