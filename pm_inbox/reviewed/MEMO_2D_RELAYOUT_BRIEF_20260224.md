# MEMO — 2D Client Relayout Brief
**Date:** 2026-02-24
**From:** Thunder (PO) + Squire session
**To:** Slate (PM)
**Action:** Draft and dispatch WO-UI-2D-RELAYOUT-001 before any other 2D WO executes

---

## Decision (sealed)

The five-zone grid shipped in WO-UI-2D-FOUNDATION-001 is structurally wrong for the 2D
surface. It was ported from 3D design thinking. Revise it now — one file touch while the
surface is still small — before MAP-001, SLIP-001, SHEET-001, NOTEBOOK-001 or ORB-001
are dispatched. If those WOs build against the current grid, RELAYOUT tears them out and
creates the same drift pattern that burned the 3D track.

---

## Sequencing (hard)

```
WO-UI-2D-RELAYOUT-001   ← MUST go first. Blocks all other 2D WOs.
        ↓
WO-UI-2D-MAP-001
WO-UI-2D-SLIP-001       ← These are unblocked from each other after RELAYOUT accepts.
WO-UI-2D-SHEET-001
WO-UI-2D-NOTEBOOK-001
WO-UI-2D-ORB-001
```

Update MEMO_UI_PIVOT_2D_20260224.md WO track table to reflect this sequencing.

---

## Sealed Design Decisions (resolved in pre-flight — do not reopen)

### 1. Shelf buttons ARE posture triggers

Shelf buttons are not decoration. Each one triggers a posture AND opens its drawer:

| Button | Posture triggered | Drawer opened |
|--------|------------------|---------------|
| Sheet | `posture-down` | Character sheet full-screen overlay |
| Notebook | `posture-down` | Notebook full-screen overlay |
| Tome | `posture-down` | Rulebook full-screen overlay |
| Dice Bag | `posture-dice` | Dice tray expands (right rail widens) |
| Map (implicit / key 2) | `posture-lean` | No drawer — map expands |

Clicking the active button again (or pressing Escape) closes the drawer and returns to
`posture-standard`. This is self-documenting — the player discovers postures by using
the shelf, not by reading docs or finding keyboard shortcuts.

Keyboard keys 1-4 still work as before. Shelf clicks are additive, not a replacement.

A subtle current-posture label (e.g. `STANDARD`, `MAP`, `DICE`) in the bottom rail at
far right gives keyboard users feedback without chrome. Plain text, low opacity, no icon.

**This changes what the shelf buttons are in RELAYOUT-001.** They need `data-posture`
and `data-drawer` attributes on the HTML elements. The JS wiring for actual
drawer open/close happens in later WOs — RELAYOUT ships the attributes only.

### 2. Right rail CSS layout is prescribed — builder does not invent this

```css
#right-col {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  width: 280px;
}

#slip-tray {
  flex: 1;
  overflow-y: auto;  /* scrolls internally when slips stack */
}

#handout-tray {
  flex: 0 0 auto;    /* collapses when display:none, pushes below slip tray when visible */
  display: none;     /* default: hidden */
}
```

Builder must use this structure verbatim. Do not invent alternative overflow handling.

### 3. Bottom bar focus states: input focused → shelf recedes

When `#player-input` receives focus, add class `input-focused` to `#shelf-zone`.
When it loses focus, remove the class. CSS handles the visual shift:

```css
#shelf-zone.input-focused .shelf-item {
  opacity: 0.4;
  pointer-events: none;
}
```

This is a two-line JS addition to `main.js` (focus/blur event listeners on
`#player-input`). This is the ONE permitted `main.js` touch in RELAYOUT-001.
It is small, isolated, and necessary to ship the bottom bar correctly.

### 4. DM voice mode: two behaviors, context-dependent (LOCKED)

| Context | DM voice behavior |
|---------|------------------|
| Exploration / roleplay (`combat_start` not fired) | Full panel drop: portrait left, text right, overlays top ~25% of map. Slides down on `speaking_start`, slides up on `speaking_stop`. |
| Combat (`combat_start` fired, `combat_end` not yet) | No panel drop. Text appends to a compact transcript strip below the orb in the right rail. Map stays clean. Panel does not interrupt. |

The `#dm-panel` and `#orb-transcript` HTML elements both exist in the RELAYOUT-001
skeleton. Both are hidden by default. The JS wiring that switches between modes based on
`combat_start`/`combat_end` state is implemented in WO-UI-2D-DM-PANEL-001, not here.

RELAYOUT-001 ships the skeleton only. The two-mode behavioral decision is locked here
so ORB-001 and DM-PANEL-001 builders don't invent their own answer.

---

## Target Architecture

```
┌────────────────────────────┬──────────────────┐
│                            │  [orb] ambient   │
│    BATTLE MAP / SCENE      │  [transcript]    │  ← compact, combat-only
│    (dominant, full height) │  ────────────    │
│                            │  ROLL SLIP TRAY  │
│                            │  (scrollable)    │
│                            │  ────────────    │
│                            │  HANDOUT TRAY    │
│                            │  (on demand,     │
│                            │   collapses when │
│                            │   empty)         │
├────────────────────────────┴──────────────────┤
│ [Sheet] [Notebook] [Tome] [Dice Bag]  [input] STANDARD │
└─────────────────────────────────────────────────────────┘

  [DM panel — slides down from top, exploration/roleplay only]
  ┌───────────────────────────────────────────┐
  │  [portrait]  narration text scrolls here  │
  └───────────────────────────────────────────┘
```

**Three regions, not five zones:**
- Left/center: battle map — dominant, full height
- Right column (~280px): orb (top), roll slip tray (middle), handout tray (on demand, collapses when empty)
- Bottom rail: shelf tool objects + text input — single unified bar

**DM panel:** hidden by default. Slides down from top of viewport when `speaking_start`
fires, overlays top ~25% of map, portrait left + text right. Slides back up on
`speaking_stop`. Does not eat a permanent zone.

**Handout zone:** eliminated. Handouts are a physical behavior, not a permanent zone
and not a tab. When the DM pushes a handout, it prints into a tray that appears in the
right column (below the roll slip tray). When nothing is printing, that area collapses —
it is gone. No permanent strip. No tab. No navigation chrome. This is the same pattern
as the DM panel: exists on demand, invisible otherwise.
The work zone row is gone. That real estate goes to the map.

---

## What is changing

| Element | Old (FOUNDATION-001) | New (RELAYOUT-001) |
|---------|---------------------|--------------------|
| Layout | 5-zone CSS grid | 3-region: map / right col / bottom rail |
| DM zone | Permanent 130px top row | Hidden overlay panel, triggered by WS |
| Vault zone | 1fr row (shares space) | Full height left region |
| Work zone | 160px row (handout area) | Eliminated — handout tray in right col, on-demand only |
| Dice zone | 280px column stub | Right column, full height below orb |
| Shelf zone | 80px bottom row | Single unified bottom bar (shelf objects + input) |
| Crystal orb | 120px centered in DM zone | Small ambient element, top of right column |

---

## Scope constraint (hard boundary)

**RELAYOUT-001 touches: `index.html`, `style.css`, and one focused addition to `main.js`.**

Do NOT touch `ws.js`. Do not add WS message handlers. Do not wire drawers open/close.

**The one permitted `main.js` addition:** focus/blur listeners on `#player-input` that
toggle class `input-focused` on `#shelf-zone`. Two event listeners, no WS involvement,
no posture logic. Everything else in `main.js` is untouched.

Shelf button `data-posture` and `data-drawer` attributes are set in `index.html` — the
actual posture-switching and drawer JS is wired in later WOs. RELAYOUT ships attributes
and structure, not behavior.

New HTML elements required in this WO:
- `#right-col` — right column wrapper
- `#orb` — small, repositioned to top of right col (element already exists, moves)
- `#orb-transcript` — compact transcript strip, hidden by default, combat-only
- `#slip-tray` — inside right col (element already exists, moves)
- `#handout-tray` — inside right col, hidden by default
- `#dm-panel` — full overlay panel, hidden by default, exploration mode
- `#posture-label` — plain text in bottom rail, far right, shows current posture name

---

## Gate requirement

Gate: UI-2D-RELAYOUT (12 tests)

Tests must verify:
- No `dm-zone` as a grid row (old five-zone structure gone)
- `#right-col` element exists in index.html
- `#dm-panel` exists and is hidden by default
- `#orb-transcript` exists and is hidden by default
- `#vault-zone` exists and is inside the left region (not a grid row)
- `#slip-tray` is inside `#right-col`
- `#handout-tray` exists inside `#right-col` and is hidden by default
- `#posture-label` exists in the bottom bar
- Shelf items have `data-posture` attributes (shelf-as-posture-trigger)
- All four posture classes still present in style.css
- No Three.js references (regression guard)
- Palette variables intact (regression guard)

---

## What does NOT change

- WS protocol — unchanged
- Posture key hotkeys (1-4) — unchanged, but posture CSS classes remap to new grid
- Palette variables — unchanged
- `ws.js` — do not touch
- `main.js` — do not touch (except if orb element ID changes, update the one reference)
- `client/` frozen — do not touch

---

## Files to create/modify

```
client2d/index.html     ← MODIFY (new structure: right-col, dm-panel, orb-transcript, posture-label, shelf data-attributes)
client2d/style.css      ← MODIFY (new grid, right-col flex column, focus states, posture label)
client2d/main.js        ← MODIFY (two lines only: focus/blur listeners on #player-input)
tests/test_ui_2d_relayout_gate.py  ← CREATE (12 tests)
```

---

## Commit requirement

```
feat: WO-UI-2D-RELAYOUT-001 — 3-region layout, shelf-as-posture, two-mode DM voice — Gate UI-2D-RELAYOUT 12/12
```

---

## Audio cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```
