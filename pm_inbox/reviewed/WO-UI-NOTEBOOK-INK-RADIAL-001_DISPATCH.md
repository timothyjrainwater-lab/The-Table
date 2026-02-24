# WO-UI-NOTEBOOK-INK-RADIAL-001 — Notebook Ink: Pencil Cursor + Radial Tool Wheel + Text Input

**Issued:** 2026-02-24
**Authority:** DOCTRINE_04_TABLE_UI_MEMO_V4 §8, §14; TABLE_METAPHOR_AND_PLAYER_ARTIFACTS.md §Part 2; TABLE_SURFACE_UI_SPECIFICATION.md §4.4
**Gate:** UI-NB-INK (new). Target: 12 tests.
**Blocked by:** WO-UI-NOTEBOOK-DRAW-WIRE-001 (drawing wire must be in place — it is).
**Priority:** P0 — Product owner escalation. This is the core notebook UX.

---

## 0. Context & Gap

The drawing wire (`startStroke`/`continueStroke`/`endStroke`) is wired in `main.ts`.
The notebook opens, sections switch, and strokes persist.

**What is missing per doctrine:**

| Feature | Doctrine Source | Status |
|---------|---------------|--------|
| Pencil cursor when hovering open notebook page | TABLE_METAPHOR §Part 2 §3 | ❌ Missing |
| Radial tool wheel (keybind or right-click at pen tip) | TABLE_METAPHOR §Part 2 §5; DOCTRINE_04 §8 | ❌ Missing |
| Tool selection via radial: pen / brush / eraser | DOCTRINE_04 §8 (MARK wedge) | ❌ Missing |
| Text input mode (click to place text block, keyboard types to it) | TABLE_METAPHOR §Part 2 "Text input"; §184 accessibility | ❌ Missing |
| API mismatch: `addTranscriptEntry` called in main.ts, does not exist | main.ts:534 → no method | ❌ Bug |
| API mismatch: `upsertBestiaryEntry` called in main.ts, does not exist | main.ts:549 → no method | ❌ Bug |

---

## 1. Doctrine Extraction (Exact Text)

**TABLE_METAPHOR_AND_PLAYER_ARTIFACTS.md §Part 2 — The Notebook:**

> 3. Open state: A blank page (or the last page they were on). **A pen cursor.**
> 4. Drawing: Click and drag to draw. The pen draws lines on the page.
> 5. Color/tool selection: A **key bind** (configurable) opens a **radial color wheel** at the current pen tip position.
>    - The radial wheel appears centered on the pen tip — not in a toolbar, not in a sidebar
>    - Wheel segments for colors (full spectrum)
>    - Optional: pen thickness in the center of the wheel or as a secondary radial
>    - Release or click to select; wheel dismisses immediately
>    - Total interaction: key bind → radial appears → select → radial vanishes → continue drawing
> 7. Eraser: A key bind or radial option for eraser mode.

**DOCTRINE_04 §8 — RADIAL FINGER MENU (LAST RESORT / TOOL-SUBSTITUTION ONLY):**

> Radial exists only to replace physical tools you'd use at a table:
> - MARK: **notebook ink tools only** (pen/highlighter/eraser); **never on map**
>
> Forbidden wedges:
> - ROLL / CAST/ATTACK/END TURN / ANY "do the action" verbs

**TABLE_METAPHOR_AND_PLAYER_ARTIFACTS.md §184 — Accessibility:**

> Text-only mode: For players who cannot use a drawing pad, the Notebook degrades to a **simple text input** (keyboard typing, plain text, no formatting)

---

## 2. Binary Decisions

| # | Decision | Choice |
|---|---|---|
| 1 | Radial trigger | Right-click on open notebook page (no keybind complexity needed for MVP; right-click is natural) |
| 2 | Radial position | At the cursor position when right-click fires |
| 3 | Radial wedges (MVP) | 5 wedges: Pen / Brush / Eraser / Text / Cancel |
| 4 | Radial rendering | HTML overlay (div + CSS conic-gradient or SVG), not Three.js — simpler, reliable |
| 5 | Text block placement | Left-click while in Text tool → places a `<textarea>` overlay at UV position; typing inserts there; pressing Escape or clicking elsewhere commits |
| 6 | Text block persistence | Stored as `TextBlock[]` on the page canvas — rendered as black text at (x,y) on `_drawCanvas` using `fillText()` |
| 7 | Pencil cursor | CSS `cursor: url('/pencil.cur') 0 32, crosshair` when hovering `notebook.pageRightMesh` and notebook is open |
| 8 | Cursor fallback | `crosshair` if custom cursor fails |
| 9 | API mismatch fix | Add `addTranscriptEntry()` wrapper + `upsertBestiaryEntry()` wrapper to `NotebookObject` matching what main.ts already calls |
| 10 | Radial dismiss | Click outside radial, or press Escape, or select a wedge |

---

## 3. Contract Spec

### 3.1 Pencil Cursor

In `main.ts`, inside the existing notebook pointer move handler:

```typescript
// Pencil cursor when hovering the open page
renderer.domElement.addEventListener('pointermove', (ev) => {
  const uv = _nbUvFromEvent(ev);
  if (uv && notebook.isOpen && notebook.section === 'notes') {
    renderer.domElement.style.cursor = "url('/pencil.cur') 0 32, crosshair";
  } else {
    renderer.domElement.style.cursor = '';   // restore default
  }
  // ... existing drawing logic
});
```

A pencil cursor PNG/CUR asset at `client/public/pencil.cur` (32×32, hotspot at tip).
If asset is absent, `crosshair` is the fallback — acceptable.

### 3.2 Radial Tool Wheel (HTML overlay)

Add to `client/index.html` (or create `client/src/notebook-radial.ts`):

```typescript
// notebook-radial.ts
export type RadialTool = 'pen' | 'brush' | 'eraser' | 'text' | null;

export class NotebookRadial {
  private _el: HTMLElement;
  private _visible = false;
  private _onSelect: (tool: RadialTool) => void;

  constructor(onSelect: (tool: RadialTool) => void) {
    this._onSelect = onSelect;
    this._el = document.createElement('div');
    this._el.id = 'nb-radial';
    this._el.style.cssText = `
      display:none; position:fixed; width:160px; height:160px;
      border-radius:50%; background:rgba(30,20,10,0.92);
      border:2px solid #c0a060; z-index:9999; pointer-events:auto;
    `;
    this._buildWedges();
    document.body.appendChild(this._el);

    document.addEventListener('pointerdown', (ev) => {
      if (this._visible && !this._el.contains(ev.target as Node)) this.hide();
    });
    document.addEventListener('keydown', (ev) => {
      if (ev.key === 'Escape') this.hide();
    });
  }

  show(x: number, y: number): void {
    this._el.style.left = `${x - 80}px`;
    this._el.style.top  = `${y - 80}px`;
    this._el.style.display = 'block';
    this._visible = true;
  }

  hide(): void {
    this._el.style.display = 'none';
    this._visible = false;
  }

  get isVisible(): boolean { return this._visible; }

  private _buildWedges(): void {
    const wedges: { label: string; tool: RadialTool; angle: number }[] = [
      { label: '✏️ Pen',    tool: 'pen',    angle: 270 },
      { label: '🖌️ Brush', tool: 'brush',  angle: 342 },
      { label: '⬜ Erase', tool: 'eraser', angle: 54  },
      { label: '📝 Text',  tool: 'text',   angle: 126 },
      { label: '✕ Cancel', tool: null,     angle: 198 },
    ];
    const R = 55; // px from center
    wedges.forEach(({ label, tool, angle }) => {
      const btn = document.createElement('button');
      const rad = (angle * Math.PI) / 180;
      const bx = 80 + R * Math.cos(rad) - 28;
      const by = 80 + R * Math.sin(rad) - 14;
      btn.textContent = label;
      btn.style.cssText = `
        position:absolute; left:${bx}px; top:${by}px;
        width:56px; height:28px; font-size:10px; line-height:1.1;
        background:rgba(60,40,10,0.85); color:#d4b878;
        border:1px solid #8a6a30; border-radius:4px; cursor:pointer;
        white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
        padding:2px 4px;
      `;
      btn.addEventListener('pointerdown', (ev) => {
        ev.stopPropagation();
        this.hide();
        this._onSelect(tool);
      });
      this._el.appendChild(btn);
    });
  }
}
```

### 3.3 Text Input Mode

When the user selects 'text' from the radial, the notebook enters text mode.
On next left-click on the page, a `<textarea>` is positioned at that UV location.

```typescript
// In main.ts — text input overlay
let _nbTextMode = false;
let _nbTextOverlay: HTMLTextAreaElement | null = null;

function _commitTextOverlay(): void {
  if (!_nbTextOverlay) return;
  const text = _nbTextOverlay.value.trim();
  if (text) {
    // Parse the data-x / data-y attributes set when the overlay was placed
    const cx = parseFloat(_nbTextOverlay.dataset.cx ?? '0');
    const cy = parseFloat(_nbTextOverlay.dataset.cy ?? '0');
    notebook.addTextBlock(cx, cy, text);
  }
  _nbTextOverlay.remove();
  _nbTextOverlay = null;
}

// pointerdown handler (notes section, text mode)
if (_nbTextMode && notebook.isOpen && notebook.section === 'notes') {
  const uv = _nbUvFromEvent(ev);
  if (uv) {
    _commitTextOverlay(); // commit any existing
    const cvPt = notebook.uvToCanvas(uv.u, uv.v);
    // Position overlay relative to canvas element on screen
    // ...create textarea, set dataset.cx/cy = cvPt.x/y, append to body
  }
}
```

### 3.4 `NotebookObject.addTextBlock()` API addition

Add to `notebook-object.ts`:

```typescript
/** Add a typed text block to the notes canvas at canvas coordinates (cx, cy). */
addTextBlock(cx: number, cy: number, text: string): void {
  // Render directly to _drawCanvas
  this._drawCtx.font = '14px Georgia, serif';
  this._drawCtx.fillStyle = INK_DEF;
  this._drawCtx.textAlign = 'left';
  this._drawCtx.fillText(text, cx, cy);
  // Update texture
  this._notesTexture = new THREE.CanvasTexture(this._drawCanvas);
  if (this._section === 'notes') this._refreshPageTextures();
  // Persist: store text blocks alongside strokes (debounced save)
  this.saveStrokes('notes', this._strokes);
}
```

### 3.5 API Mismatch Fixes in `NotebookObject`

Add two wrapper methods to `NotebookObject` to match what `main.ts` already calls:

```typescript
/** Alias for setTranscriptFeedTexture used by ws-bridge via main.ts. */
addTranscriptEntry(_entry: TranscriptEntry): void {
  // Transcript display is READ-ONLY feed — entries are rendered externally.
  // This method is a no-op stub so main.ts callers don't throw.
  // The actual feed texture is set via setTranscriptFeedTexture().
}

/** Alias for applyBestiaryUpsert matching main.ts BestiaryBindController wire. */
upsertBestiaryEntry(entry: BestiaryEntry): boolean {
  // Must go through consent chain — same as applyBestiaryUpsert.
  // Caller (BestiaryBindController) must have called consentChain.requestConsent()
  // and consentChain.grant() first.
  return this.applyBestiaryUpsert(entry);
}
```

---

## 4. Test Spec (Gate UI-NB-INK — 12 tests)

File: `tests/test_ui_gate_nb_ink.py` (new file)

| ID | Test |
|----|------|
| NB-I-01 | `NotebookObject` has `cycleDrawTool()` returning 'pen' → 'brush' → 'eraser' |
| NB-I-02 | `NotebookObject.drawTool` property exists and returns current tool |
| NB-I-03 | `NotebookRadial` class (or equivalent) exported from `notebook-radial.ts` |
| NB-I-04 | Radial has 5 entries: pen, brush, eraser, text, cancel |
| NB-I-05 | `main.ts` handles right-click (`contextmenu`) event on renderer domElement |
| NB-I-06 | `contextmenu` default prevented when notebook is open on notes section |
| NB-I-07 | `NotebookObject.addTextBlock(cx, cy, text)` method exists |
| NB-I-08 | `addTextBlock` writes text to draw canvas (ctx.fillText called) |
| NB-I-09 | `addTranscriptEntry()` method exists on `NotebookObject` (API compat) |
| NB-I-10 | `upsertBestiaryEntry()` method exists on `NotebookObject` (API compat) |
| NB-I-11 | Pencil cursor CSS applied when notebook is open and section is 'notes' |
| NB-I-12 | `npm run build --prefix client` exits 0 with all changes |

---

## 5. Implementation Plan

**Step 1** — `notebook-object.ts` additions (no breaking changes):
- Add `addTextBlock(cx, cy, text)` method
- Add `addTranscriptEntry()` no-op stub
- Add `upsertBestiaryEntry()` alias

**Step 2** — Create `client/src/notebook-radial.ts`:
- `NotebookRadial` class with HTML overlay
- 5 wedges: Pen / Brush / Eraser / Text / Cancel
- `show(x, y)` / `hide()` / `isVisible`
- Exported

**Step 3** — `client/public/pencil.cur` (or `pencil.png` 32×32):
- A simple pencil icon, hotspot at tip
- If not available, `crosshair` is acceptable fallback

**Step 4** — `main.ts` wiring:
- Import `NotebookRadial`; instantiate once
- Add `contextmenu` listener on `renderer.domElement`: if notebook open + notes → `preventDefault()`, show radial at `(ev.clientX, ev.clientY)`, set tool on selection
- Add pencil cursor logic in existing `pointermove` handler
- Add text mode click logic in `pointerdown`
- Text `<textarea>` overlay: create on click, commit on blur/Escape/next click

**Step 5** — Tests:
- Write `tests/test_ui_gate_nb_ink.py` — 12 tests

**Step 6** — Build + test:
- `npm run build --prefix client` — exits 0
- `pytest tests/test_ui_gate_nb_ink.py -v` — 12/12 PASS
- Full regression: zero new failures

---

## 6. Scope Guardrails

**In scope:**
- Pencil cursor CSS
- Right-click radial (HTML overlay, 5 wedges)
- Tool selection wired to `notebook.cycleDrawTool()` / direct tool set
- Text block input (typed text rendered to canvas)
- API compat stubs (`addTranscriptEntry`, `upsertBestiaryEntry`)

**Out of scope (deferred):**
- Color picker in radial (doctrine says "full spectrum" — defer to WO-UI-NOTEBOOK-COLOR-001)
- Clippings / paste-in (parchment → notebook page) — WO-UI-NOTEBOOK-CLIP-001
- Multi-page model (infinite pages, page turn) — WO-UI-NOTEBOOK-PAGES-001
- Highlighter tool (distinct from brush) — add to radial in color WO
- Page tear animation — WO-UI-NOTEBOOK-PAGES-001
- Consent slip diegetic UI — WO-UI-NOTEBOOK-CONSENT-SLIP-001
- Vector erase (stroke proximity hit-test) — keep raster erase for now

**Absolute hard bans (DOCTRINE_04 §3, §8):**
- NO tooltip, popover, or floating info window
- Radial NEVER contains ROLL / CAST / ATTACK / END TURN wedges
- Radial NEVER appears on the map
- Text blocks are NOT formatted (no markdown, no rich text, no validation)

---

## 7. Deliverables

- [ ] `notebook-object.ts`: `addTextBlock()`, `addTranscriptEntry()`, `upsertBestiaryEntry()` added
- [ ] `client/src/notebook-radial.ts`: `NotebookRadial` class, 5 wedges
- [ ] `client/public/pencil.cur` (or `.png`): pencil cursor asset
- [ ] `main.ts`: `contextmenu` handler, pencil cursor, text mode, radial wiring
- [ ] `tests/test_ui_gate_nb_ink.py`: 12/12 PASS
- [ ] Build: `npm run build --prefix client` exits 0
- [ ] Zero regressions

---

## 8. Integration Seams

- **Files modified:** `client/src/notebook-object.ts`, `client/src/main.ts`
- **Files created:** `client/src/notebook-radial.ts`, `client/public/pencil.cur`
- **Files created (tests):** `tests/test_ui_gate_nb_ink.py`
- **Do not modify:** `notebook-object.ts` consent chain, `NotebookConsentChain` class, EV-010..EV-013 constants

---

## Preflight

```bash
npm run build --prefix client
pytest tests/test_ui_gate_nb_ink.py -v
pytest tests/ -x -q --ignore=tests/test_ui_gate_nb_ink.py
```
