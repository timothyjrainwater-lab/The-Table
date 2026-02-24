# WO-UI-2D-RELAYOUT-001 — 3-Region Layout, Speaker Panel Rail, Shelf-as-Posture-Trigger

**Type:** Builder WO
**Gate:** UI-2D-RELAYOUT
**Tests:** 14 (RL-01 through RL-14)
**Depends on:** WO-UI-2D-FOUNDATION-001 (ACCEPTED — `client2d/` skeleton exists)
**Blocks:** WO-UI-2D-MAP-001, WO-UI-2D-SLIP-001, WO-UI-2D-SHEET-001, WO-UI-2D-NOTEBOOK-001, WO-UI-2D-ORB-001
**Priority:** CRITICAL — must ship before any other 2D WO executes

---

## 1. Target Lock

The five-zone CSS grid shipped in WO-UI-2D-FOUNDATION-001 was ported from 3D design
thinking. Fix it now while `client2d/` is still small — before MAP-001, SLIP-001,
SHEET-001, NOTEBOOK-001 or ORB-001 build against the wrong structure.

**Architecture lock (Thunder + Slate, 2026-02-24):**

The table has three regions. Left: scene surface (display surface — DM puts things here:
battle grid, town painting, NPC portrait, dungeon map). Right: a single rail split
vertically into Speaker Panel (top) and Dice/Slip section (bottom). Bottom: shelf + input.

The **right rail is one column, two sections — not two columns.**

The **Speaker Panel is the DM's seat.** Like a dealer at a poker table, the seat is
always occupied. The scene surface shows what the DM places on the table. The Speaker
Panel shows who is sitting across from you. These are different things. The seat is never
empty, never collapses to nothing.

```
┌────────────────────────────┬──────────────────────┐
│                            │  SPEAKER PANEL        │
│    #scene-surface          │  #speaker-panel       │
│    (DM display area —      │  [portrait area]      │
│     battle grid OR town    │  [beat strip]         │
│     painting OR NPC        │  [orb heartbeat]      │
│     portrait OR map etc.)  ├──────────────────────┤
│                            │  DICE / SLIP SECTION  │
│                            │  #dice-section        │
│                            │  [#slip-tray]         │
│                            │  [#handout-tray]      │
├────────────────────────────┴──────────────────────┤
│ [Sheet] [Notebook] [Tome] [Dice Bag] [input]  STANDARD │
└────────────────────────────────────────────────────────┘
```

**Deliver:** Revised `client2d/` with:
- Scene surface region replacing old vault-zone / five-zone grid
- Right rail (`#right-col`) split into `#speaker-panel` (top) and `#dice-section` (bottom)
- Speaker Panel contains: `#speaker-portrait` placeholder, `#speaker-beats` beat strip, `#orb` (heartbeat — small, inside panel)
- Dice section contains: `#slip-tray` (scrollable), `#handout-tray` (on-demand)
- Posture-responsive CSS height split between the two sections
- Shelf buttons annotated with `data-posture` and `data-drawer`
- Posture label text wired in `main.js`
- Two-mode DM voice overlay skeleton (`#dm-panel`) in HTML — hidden by default, behavior deferred

**No drawer JS. No portrait swap JS. No beat rendering JS. No orb pulse JS.**
Structure, CSS layout, and three JS lines only.

---

## 2. Binary Decisions

| # | Question | Answer |
|---|----------|--------|
| BD-01 | Which old zone IDs are removed? | `dm-zone`, `work-zone`, `dice-zone` eliminated. `vault-zone` renamed to `scene-surface`. `shelf-zone` survives. |
| BD-02 | How is the right rail structured? | One `#right-col` div, two child sections: `#speaker-panel` (flex grows via posture) and `#dice-section` (flex grows via posture). Not two columns. Height split controlled by posture CSS. |
| BD-03 | Where does the orb go? | Inside `#speaker-panel` — it is the heartbeat indicator for the DM seat, not a standalone item. ID unchanged: `#orb`. Small size. Not the face. |
| BD-04 | What is `#speaker-portrait`? | A new empty placeholder div inside `#speaker-panel`. No src, no JS wiring in this WO. ORB-001 wires the portrait swap. |
| BD-05 | What is `#speaker-beats`? | A new empty div inside `#speaker-panel` below the portrait area. No content in this WO. ORB-001 wires beat rendering. |
| BD-06 | Where does slip tray go? | Inside `#dice-section`. ID unchanged: `#slip-tray`. |
| BD-07 | Where does handout tray go? | Inside `#dice-section`, below slip tray. ID unchanged: `#handout-tray`. Hidden by default. |
| BD-08 | How does posture control the rail split? | CSS height percentages on `#speaker-panel` and `#dice-section` change per posture class on `<body>`. STANDARD: speaker ~60%, dice ~40%. LEAN (battle): speaker ~30%, dice ~70%. DOWN: speaker minimized (~80px fixed), dice fills rest. DICE: speaker minimized (~80px fixed), dice fills rest. |
| BD-09 | What is the idle state of the Speaker Panel? | Always shows DM crest — a dim placeholder (text or CSS sigil). Seat is never empty. Orb glows softly at idle. Portrait div is empty in this WO — ORB-001 populates it. |
| BD-10 | What do shelf buttons emit? | `data-posture` and `data-drawer` HTML attributes. JS wiring for drawer behavior deferred. |
| BD-11 | What main.js touches are permitted? | Exactly three lines — see Contract Spec §3.3. No other main.js changes. `ws.js` not touched. |
| BD-12 | How is posture label updated? | Inside existing `setPosture()` in `main.js`. One line sets `#posture-label` textContent. LEAN posture label text is `'BATTLE'`, not `'MAP'`. STANDARD = `'STANDARD'`, DOWN = `'DOWN'`, DICE = `'DICE'`. |
| BD-13 | Is DM panel behavior wired here? | No. `#dm-panel` overlay HTML skeleton exists, hidden by default. JS mode-switching wired in WO-UI-2D-DM-PANEL-001. |
| BD-14 | Is `#ws-status` dot moved? | No. Cosmetic collision logged as FINDING-2D-STATUS-DOT-001 (LOW). Not addressed here. |

---

## 3. Contract Spec

### 3.1 HTML structure (`client2d/index.html`)

Old elements removed or renamed: `#dm-zone`, `#work-zone`, `#dice-zone`, `#vault-zone` (→ `#scene-surface`).

New structure required — all elements must be present in delivered `index.html`:

| Element | Parent | Default visibility | Notes |
|---------|--------|-------------------|-------|
| `#scene-surface` | `#layout` | visible | Dominant left region. Replaces `#vault-zone`. |
| `#scene-display` | `#scene-surface` | visible | Inner display div (canvas added by MAP-001) |
| `#scene-label` | `#scene-display` | visible | Placeholder text: `"Scene"` |
| `#right-col` | `#layout` | visible | Right rail wrapper |
| `#speaker-panel` | `#right-col` | visible | Top section — DM seat |
| `#speaker-portrait` | `#speaker-panel` | visible (empty) | Portrait placeholder — ORB-001 populates |
| `#speaker-beats` | `#speaker-panel` | visible (empty) | Beat strip placeholder — ORB-001 populates |
| `#orb` | `#speaker-panel` | visible | Heartbeat indicator. Small. Inside speaker panel. |
| `#orb-portrait` | `#orb` | visible (empty) | Already exists — stays inside orb |
| `#orb-transcript` | `#right-col` (below speaker-panel) | `display:none` | Combat-only compact strip |
| `#dice-section` | `#right-col` | visible | Bottom section — dice/slip |
| `#slip-tray` | `#dice-section` | visible | Roll slip tray |
| `#handout-tray` | `#dice-section` | `display:none` | On-demand handout area |
| `#dm-panel` | `body` (overlay) | `display:none` | Exploration-mode overlay. Wired DM-PANEL-001. |
| `#dm-panel-portrait` | `#dm-panel` | visible | Already exists — moves with panel |
| `#dm-panel-text` | `#dm-panel` | visible | Already exists — moves with panel |
| `#posture-label` | `#shelf-zone` | visible | Far right, plain text, low opacity |

Shelf buttons — required attributes (IDs optional but encouraged):

```html
<button class="shelf-item" id="shelf-sheet"
  data-posture="posture-down" data-drawer="sheet-drawer">Sheet</button>
<button class="shelf-item" id="shelf-notebook"
  data-posture="posture-down" data-drawer="notebook-drawer">Notebook</button>
<button class="shelf-item" id="shelf-tome"
  data-posture="posture-down" data-drawer="tome-drawer">Tome</button>
<button class="shelf-item" id="shelf-dice-bag"
  data-posture="posture-dice" data-drawer="dice-drawer">Dice Bag</button>
```

### 3.2 CSS (`client2d/style.css`)

Right rail top-level — use verbatim:

```css
#right-col {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  width: var(--right-col-width);
  background-color: var(--walnut-dark);
  border-left: 2px solid var(--walnut-warm);
  box-shadow: inset 2px 0 12px rgba(0,0,0,0.4);
  transition: width var(--posture-speed) ease-in-out;
}
```

Speaker Panel — top section, posture-responsive height:

```css
#speaker-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  overflow: hidden;
  transition: flex-basis var(--posture-speed) ease-in-out, max-height var(--posture-speed) ease-in-out;
  border-bottom: 1px solid rgba(92,61,34,0.5);
  padding: 12px 10px 8px;
  gap: 8px;
  /* Default (STANDARD): ~60% of rail height */
  flex: 6 0 0;
  min-height: 80px;
}

#speaker-portrait {
  width: 100%;
  flex: 0 0 auto;
  aspect-ratio: 3 / 4;
  max-height: 55%;
  background: var(--walnut-dark);
  border: 1px solid rgba(139,105,20,0.3);
  border-radius: 3px;
  /* Idle: DM crest placeholder text handled by CSS content or ORB-001 */
}

#speaker-beats {
  flex: 1;
  overflow-y: auto;
  width: 100%;
  font-size: 11px;
  line-height: 1.5;
  color: var(--parchment-aged);
  /* ORB-001 renders beat elements here */
}
```

Orb (heartbeat) inside speaker panel — small, not the face:

```css
#orb {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px;
}

#orb > div:first-child {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 35%, #d4aa48, #3a2800);
  box-shadow:
    0 0 12px 4px rgba(255, 180, 60, 0.35),
    0 0 4px 1px rgba(255, 200, 80, 0.15),
    0 2px 6px rgba(0,0,0,0.7);
  transition: box-shadow 0.4s ease;
}

#orb > div:first-child.speaking {
  box-shadow: 0 0 24px 8px var(--amber-speak), 0 2px 6px rgba(0,0,0,0.6);
  animation: orb-pulse 1.2s ease-in-out infinite;
}

@keyframes orb-pulse {
  0%, 100% { box-shadow: 0 0 24px 8px var(--amber-speak), 0 2px 6px rgba(0,0,0,0.6); }
  50%       { box-shadow: 0 0 36px 12px var(--amber-speak), 0 2px 6px rgba(0,0,0,0.6); }
}
```

Dice section — bottom section, posture-responsive:

```css
#dice-section {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: flex-basis var(--posture-speed) ease-in-out;
  /* Default (STANDARD): ~40% of rail height */
  flex: 4 0 0;
}

#slip-tray {
  flex: 1;
  overflow-y: auto;
  background: var(--walnut-mid);
  display: flex;
  flex-direction: column;
  padding: 8px;
  gap: 4px;
}

#handout-tray {
  flex: 0 0 auto;
  display: none;
  background: linear-gradient(145deg, var(--parchment) 0%, var(--parchment-aged) 100%);
  border-top: 2px solid var(--brass);
  padding: 8px;
  min-height: 80px;
}
```

Orb transcript — combat compact strip, below speaker-panel, outside dice-section:

```css
#orb-transcript {
  flex: 0 0 auto;
  display: none;
  max-height: 80px;
  overflow-y: auto;
  padding: 4px 10px;
  font-size: 11px;
  line-height: 1.4;
  color: var(--parchment-aged);
  border-bottom: 1px solid rgba(92,61,34,0.4);
  background: rgba(0,0,0,0.2);
}
```

Posture classes — height split between speaker and dice sections:

```css
/* STANDARD: Speaker ~60%, Dice ~40% */
body.posture-standard #speaker-panel { flex: 6 0 0; }
body.posture-standard #dice-section  { flex: 4 0 0; }
body.posture-standard #right-col     { width: var(--right-col-width); }

/* LEAN_FORWARD (battle): Speaker ~30%, Dice ~70% — map dominates, mechanical layer prominent */
body.posture-lean #speaker-panel { flex: 0 0 80px; max-height: 80px; }
body.posture-lean #dice-section  { flex: 1 0 0; }
body.posture-lean #right-col     { width: 220px; }

/* DOWN: Speaker collapses to presence marker, dice expands for reading */
body.posture-down #speaker-panel { flex: 0 0 80px; max-height: 80px; }
body.posture-down #dice-section  { flex: 1 0 0; }
body.posture-down #right-col     { width: 200px; }

/* DICE_TRAY: Right col widens, dice section prominent */
body.posture-dice #speaker-panel { flex: 0 0 80px; max-height: 80px; }
body.posture-dice #dice-section  { flex: 1 0 0; }
body.posture-dice #right-col     { width: 420px; }
```

Input focus state — shelf recedes:

```css
#shelf-zone.input-focused .shelf-item {
  opacity: 0.4;
  pointer-events: none;
}
```

Posture label — plain text, far right, low opacity:

```css
#posture-label {
  margin-left: auto;
  opacity: 0.35;
  font-size: 0.7rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--parchment);
  pointer-events: none;
  user-select: none;
}
```

All palette variables must be present (regression guard):
`--walnut-dark`, `--walnut-mid`, `--walnut-warm`, `--felt-deep`, `--parchment`,
`--parchment-aged`, `--ink`, `--leather-warm`, `--leather-dark`, `--brass`,
`--wax-red`, `--amber-idle`, `--amber-speak`

### 3.3 JS (`client2d/main.js`) — three lines, no more

**Lines 1 and 2** — input focus listeners (near input bar initialization):

```js
playerInput.addEventListener('focus', () => shelfZone.classList.add('input-focused'));
playerInput.addEventListener('blur',  () => shelfZone.classList.remove('input-focused'));
```

**Line 3** — inside existing `setPosture()`, add one line. Posture label text:
- STANDARD → `'STANDARD'`
- LEAN → `'BATTLE'`  ← not 'MAP'. Posture reflects what player is doing.
- DOWN → `'DOWN'`
- DICE → `'DICE'`

```js
// Inside setPosture():
document.getElementById('posture-label').textContent = postureLabel;
// postureLabel is derived from posture key: {'standard':'STANDARD','lean':'BATTLE','down':'DOWN','dice':'DICE'}
```

Builder determines exact derivation from the existing `setPosture()` logic. Do not add a new function.

`ws.js` is **not touched**. No portrait swap. No beat rendering. No orb pulse logic beyond CSS class on `.speaking`. No drawer wiring. These three lines are the only main.js changes.

---

## 4. Implementation Plan

1. **Read `client2d/index.html`** — identify current structure, note surviving IDs.

2. **Rewrite `client2d/index.html`** — replace with three-region layout:
   - `#scene-surface` replaces `#vault-zone` as the dominant left region
   - `#right-col` contains two child sections: `#speaker-panel` (top) and `#dice-section` (bottom)
   - `#speaker-panel` contains: `#speaker-portrait`, `#speaker-beats`, `#orb` (with `#orb-portrait` inside)
   - `#orb-transcript` goes between `#speaker-panel` and `#dice-section` in `#right-col` (or inside speaker panel footer — builder's call, gate only checks it exists inside `#right-col`)
   - `#dice-section` contains: `#slip-tray`, `#handout-tray`
   - `#dm-panel` as body-level overlay, `display:none`
   - `#posture-label` inside `#shelf-zone`
   - Shelf buttons with `data-posture` and `data-drawer` attributes

3. **Rewrite `client2d/style.css`** — implement Speaker Panel split rail layout:
   - Remove old CSS grid zone declarations
   - Add scene-surface flex layout
   - Add `#speaker-panel` and `#dice-section` flex sizing
   - Add orb (small heartbeat size, inside speaker panel)
   - Add posture classes controlling speaker/dice height split
   - Verify all palette variables present, all posture classes present

4. **Edit `client2d/main.js`** — three lines only:
   - Focus/blur listeners on `#player-input`
   - Posture-label textContent update inside `setPosture()` with correct label map

5. **Create `tests/test_ui_2d_relayout_gate.py`** — 14 gate tests (RL-01 through RL-14)

6. **Preflight:**
   - `pytest tests/test_ui_2d_relayout_gate.py -v` — 14/14 must pass
   - `pytest tests/test_ui_2d_foundation_gate.py -v` — 10/10 must still pass (regression)

7. **Visual confirmation:** Open `client2d/index.html` in browser. Confirm: scene surface dominant left, right col shows speaker panel section (top) and dice/slip section (bottom), shelf across full width. Include screenshot or description in debrief.

---

## 5. Gate Tests (UI-2D-RELAYOUT 14/14)

File: `tests/test_ui_2d_relayout_gate.py`

Tests use Python `html.parser` + string search. No browser required.

| ID | Description |
|----|-------------|
| RL-01 | `index.html` does NOT contain `id="dm-zone"` (old five-zone structure eliminated) |
| RL-02 | `index.html` does NOT contain `id="vault-zone"` — renamed to `scene-surface` |
| RL-03 | `index.html` contains `id="scene-surface"` |
| RL-04 | `index.html` contains `id="right-col"` |
| RL-05 | `index.html` contains `id="speaker-panel"` inside `id="right-col"` (parent nesting check) |
| RL-06 | `index.html` contains `id="dice-section"` inside `id="right-col"` (parent nesting check) |
| RL-07 | `index.html` contains `id="speaker-portrait"` inside `id="speaker-panel"` |
| RL-08 | `index.html` contains `id="speaker-beats"` inside `id="speaker-panel"` |
| RL-09 | `index.html` contains `id="slip-tray"` inside `id="dice-section"` |
| RL-10 | `index.html` contains `id="handout-tray"` inside `id="dice-section"` with `display:none` or hidden |
| RL-11 | `index.html` contains `id="posture-label"` inside `id="shelf-zone"` |
| RL-12 | `index.html` shelf items contain `data-posture` attributes |
| RL-13 | `style.css` contains all four posture classes: `posture-standard`, `posture-lean`, `posture-down`, `posture-dice` |
| RL-14 | `style.css` contains all palette variables: `--walnut-mid`, `--parchment`, `--amber-idle`, `--wax-red` |

---

## 6. Delivery Footer

**Files to modify:**

```
client2d/index.html    ← MODIFY (scene-surface, speaker-panel, dice-section, speaker-portrait, speaker-beats, data-attributes)
client2d/style.css     ← MODIFY (speaker panel split rail, orb small, posture height splits, palette intact)
client2d/main.js       ← MODIFY (three lines only: focus listener, blur listener, posture-label in setPosture with BATTLE label)
```

**Files to create:**

```
tests/test_ui_2d_relayout_gate.py    ← CREATE (14 gate tests, RL-01 through RL-14)
```

**Do not create any other files. Do not touch `ws.js`. Do not touch `client/`.**

**Commit requirement:**

```
feat: WO-UI-2D-RELAYOUT-001 — Speaker Panel split rail, scene-surface, shelf-as-posture — Gate UI-2D-RELAYOUT 14/14
```

**Preflight:**

```
pytest tests/test_ui_2d_relayout_gate.py -v
pytest tests/test_ui_2d_foundation_gate.py -v
```

Both suites must be green before commit.

---

## 7. Integration Seams

- `#speaker-panel` flex sizing must not clip the orb in LEAN/DOWN/DICE postures — 80px min-height must accommodate the orb at minimum. Builder verifies orb is visible at all postures.
- `#orb-transcript` placement: between speaker-panel and dice-section in DOM order, or as a last child of speaker-panel. Gate only checks it is inside `#right-col`. Builder chooses placement that makes visual sense.
- `#scene-surface` gate test RL-03 replaces old RL-05 (`#vault-zone`). Builder confirms no other file in `client2d/` references `vault-zone` — if any, rename those too.

---

## 8. Assumptions to Validate

- `client2d/main.js` already has a `setPosture()` function — builder reads it before modifying
- The existing posture key strings match the new label map (`'standard'`, `'lean'`, `'down'`, `'dice'`) — builder verifies and adjusts the label map accordingly
- `client2d/style.css` already has `--right-col-width` and `--posture-speed` CSS variables — builder preserves them

---

## 9. Open Findings (log on completion)

| ID | Severity | Description |
|----|----------|-------------|
| FINDING-2D-STATUS-DOT-001 | LOW | WS status dot position may collide with speaker panel after rail update. Address in ORB-001. |
| FINDING-2D-SPEAKER-CREST-001 | LOW | Idle Speaker Panel shows empty `#speaker-portrait` div in v1 — no DM crest rendered yet. ORB-001 populates portrait with crest or NPC image. |

---

## 10. Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```
