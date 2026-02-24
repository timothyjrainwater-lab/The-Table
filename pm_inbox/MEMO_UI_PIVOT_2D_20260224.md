# MEMO — UI Surface Pivot: 3D Table Sim → 2D Illustrated Tabletop
**Date:** 2026-02-24
**From:** Slate (PM)
**To:** All builders, all agents, future Slate instances
**Authority:** Thunder (PO) — decision made 2026-02-24 whiteboard session with Slate + Aegis

---

## Decision (sealed)

The project surface layer is transitioning from a **3D Three.js table simulator**
to a **2D illustrated tabletop client**. This decision is locked. Do not reopen it.

**Reason:** Agent execution reliability. The 3D client required builders to hold
Three.js scene state, camera math, raycasting, and physics simultaneously across
context windows. Drift was accumulating faster than gates could contain it. The
2D client reduces builder scope to surgical single-file WOs with deterministic
gate tests. Same vision, dramatically lower execution complexity.

---

## What did NOT change

- **Authority chain:** Box is truth. Oracle/Lens gate canon. Spark renders only.
  UI/Immersion embodies only. No backflow. Unchanged.
- **Interaction grammar:** DECLARE → POINT → CONFIRM → RECORD (consent-gated).
  Unchanged.
- **UI bans:** No tooltips, popovers, hover cards, snippets, gamy menus. Unchanged.
- **Notebook sacred:** Write-locked default. Deterministic consent handshake. Unchanged.
- **WS protocol:** Same `msg_type` strings, same JSON shapes. No adapter dialect.
  The 2D client speaks the exact same protocol as the 3D client.
- **The table metaphor:** Still a candlelit tavern table. Still physical objects
  on a surface. Still diegetic only. The rendering changed; the concept did not.

---

## What changed

- **Renderer:** Three.js + WebGL → HTML5 Canvas 2D + CSS + vanilla JS
- **Client folder:** `client/` (frozen, do not touch) → `client2d/` (active)
- **Build system:** Vite + TypeScript + npm → no build step, no bundler, no npm
- **Camera postures:** 3D camera frustum math → CSS class swap on `<body>`
- **Dice system:** 3D physics tower → Roll Slip + Wax Seal ritual
- **Asset pipeline:** Three.js materials/textures → CSS gradients + illustrated sprites

---

## Locked design decisions (do not reopen)

| Decision | Answer |
|----------|--------|
| Single table or tabbed locations? | Single table. No tabs. One scene always. |
| Dice replacement | Roll Slip + Wax Seal. PENDING_ROLL → slip prints formula → player stamps → result archives. |
| Visual style | Ink-sprite hybrid. Artifact-first. Illustrated, not photographed. CSS-driven materials. |
| LEAN_FORWARD posture | Flat top-down zoom. No perspective transform. No `rotateX`. Depth is v2 polish if ever. |
| Scene surface | `#scene-surface` — DM display area: battle grid, town painting, NPC portrait, dungeon map, etc. Not a "battle map." Renamed from `#vault-zone`. The DM puts things on it. |
| Right rail architecture | Single `#right-col` column. Two vertical sections: `#speaker-panel` (top, DM seat) and `#dice-section` (bottom, slip + handouts). Not two columns. Height split is posture-responsive. |
| Speaker Panel — dealer seat rule | Speaker Panel is the DM seat. The seat is always visible. The scene surface shows what the DM places on the table. The Speaker Panel shows who is sitting across from you. These are different things. The seat is never empty. |
| Speaker Panel — idle portrait | DM crest / neutral DM portrait, dimmed (~40–60% contrast). Not last-NPC-faded. Not empty. Idle state = always occupied. ORB-001 populates portrait; RELAYOUT-001 delivers empty placeholder div. |
| Speaker Panel — crest behavior | Non-interactive. Not a button. No click handler in v1. No tooltip. Purely visual ambient presence. Any click wiring is a v2 decision requiring its own WO. Builder must not add a click handler. |
| Speaker Panel — speaking rule | Speaking never overrides posture. `speaking_start` does NOT expand the panel against the player's posture choice. Panel adapts to posture; posture does not adapt to speaking. In all compressed postures (LEAN/DOWN/DICE): orb pulses, one beat appends, portrait stays at posture-limited size. Player decides whether to change posture and look up. |
| Posture label text | STANDARD → `'STANDARD'`, LEAN → `'BATTLE'`, DOWN → `'DOWN'`, DICE → `'DICE'`. Label reflects player intent, not zone name. |
| Orb role | Heartbeat indicator only. Small (36px), inside `#speaker-panel`. Not the face. Not the DM seat. Ambient amber glow at idle. Pulses on `speaking_start`. Does not expand. |
| Posture height splits | STANDARD: speaker ~60%, dice ~40%. LEAN (BATTLE): speaker 80px fixed, dice fills rest. DOWN: speaker 80px fixed, dice fills rest. DICE: speaker 80px fixed, dice fills rest. |
| Point gesture | Token click + ephemeral lasso/ghost. Never executes. Execution only after runtime CONFIRM. |
| File structure | Four files: `index.html`, `style.css`, `ws.js`, `main.js`. Each subsequent WO adds one `.js` file. |

---

## Palette (canonical — all 2D WOs use these variables)

```css
:root {
  --walnut-dark:    #2a1f14;
  --walnut-mid:     #3d2b1a;
  --walnut-warm:    #5c3d22;
  --felt-deep:      #1a2a1a;
  --parchment:      #f4ead5;
  --parchment-aged: #e8d5b0;
  --ink:            #1a1208;
  --leather-warm:   #6b3d2e;
  --leather-dark:   #3d1f14;
  --brass:          #8b6914;
  --wax-red:        #8b1a1a;
  --amber-idle:     rgba(255, 180, 60, 0.3);
  --amber-speak:    rgba(255, 200, 80, 0.7);
}
```

All builders use these. Never introduce new color values without adding them here first.

---

## 3D client status

`client/` is **frozen**. Not deleted. Preserved as reference.

- Do not add new features to `client/`
- Do not run gate tests against `client/` as active gates
- The Three.js gate tests (cameras, layout pack, visual QA chain) are suspended —
  they are not failures, they are parked
- If the 3D client is ever revived, it gets its own WO track at that time

3D design documents archived to: `docs/design/archive_3d/`
- `TABLE_METAPHOR_AND_PLAYER_ARTIFACTS.md`
- `TABLE_SURFACE_UI_SPECIFICATION.md`
- `LAYOUT_PACK_V1_README.md`

These are preserved reference, not active doctrine.

---

## Active 2D WO track

**Sequencing is hard — RELAYOUT-001 blocks all others after FOUNDATION-001.**

| WO | Status | Scope |
|----|--------|-------|
| WO-UI-2D-FOUNDATION-001 | ACCEPTED | Skeleton: 4 files, zones, postures, orb, WS, input bar |
| WO-UI-2D-RELAYOUT-001 | ACCEPTED | 3-region layout, scene-surface, shelf data-attributes, orb in right-col, 12/12 gate |
| WO-UI-2D-RELAYOUT-002 | READY TO DISPATCH | Speaker Panel split rail (`#speaker-panel` + `#dice-section`), 36px heartbeat orb, BATTLE posture label. Blocks ORB-001. |
| WO-UI-2D-ORB-001 | Blocked on RELAYOUT-002 — scope locked | Speaker Panel wiring: DM crest idle (CSS filter: `brightness(0.5) sepia(0.4) saturate(0.6)` — warm sepia underexposure, not grey wash; clears to `brightness(1) sepia(0) saturate(1)` on `speaking_start` with ~400ms transition), NPC portrait swap on `speaking_start`, beat strip (opacity-only aging via CSS `nth-last-child` selectors — no timers, no slide, no scroll, no reflow; newest at bottom; oldest at ~0.15 opacity; DOM capped ~8 beats), orb pulse on `speaking_start`, posture-responsive compression. Crest non-interactive (no click handler). Speaking never overrides posture. |
| WO-UI-2D-DM-PANEL-001 | Blocked on ORB-001 | Two-mode DM voice overlay: exploration panel vs combat transcript strip |
| WO-UI-2D-MAP-001 | Blocked on RELAYOUT | Scene canvas: grid, fog, tokens, AoE. Crossfade transition (300–400ms) on scene swap. |
| WO-UI-2D-SLIP-001 | Blocked on RELAYOUT | Roll slip ritual: PENDING_ROLL → stamp → archive |
| WO-UI-2D-SHEET-001 | Blocked on RELAYOUT | Character sheet: live WS data, clickable abilities |
| WO-UI-2D-NOTEBOOK-001 | Blocked on RELAYOUT | Notebook: draw, transcript, bestiary tabs |

**After RELAYOUT accepts:** MAP, SLIP, SHEET, NOTEBOOK, ORB unblock — can dispatch in parallel.

---

## Open Findings

| Finding | Severity | Description |
|---------|----------|-------------|
| FINDING-2D-STATUS-DOT-001 | LOW | WS status dot (`#ws-status`) position may collide with orb in right-col after RELAYOUT. Not a blocker — cosmetic call when right rail is rendered. Address in ORB-001 or as a standalone style fix.

All WOs after foundation are unblocked from each other — parallel dispatch possible.

---

## For future Slate instances

If you are rehydrating and see this memo: the 2D pivot is done and locked.
The active client is `client2d/`. Do not dispatch work to `client/`.
The WS protocol is unchanged — backend serves same endpoint, same messages.
The palette above is canonical. All 2D UI WOs reference this memo as style authority.
