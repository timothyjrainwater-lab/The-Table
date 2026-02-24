# WO-UI-HANDOUT-READ-001 — Handout Read View

**Issued:** 2026-02-23
**Authority:** Anvil visual QA gap — click returns handout ID but no read view exists. Handout system is 50% complete.
**Gate:** UI-HANDOUT-READ (new). Target: 6 tests.
**Blocked by:** Nothing. Parallel-safe with other P1 WOs.

---

## 1. Gap

Clicking a handout mesh in the fanstack returns the handout ID. There is no overlay or view that displays the handout content. Players receive handouts but cannot read them.

## 2. Binary Decisions

| # | Decision | Choice |
|---|---|---|
| 1 | Display mechanism | Fullscreen `<div>` overlay injected into document body. No Three.js involvement — HTML overlay is correct for readable text/image content |
| 2 | Content source | `handout_display` WS event carries `{title, body, image_url?}`. Overlay renders this. Click on fanstack handout mesh → request server to push `handout_display` event via `REQUEST_HANDOUT_READ` WS message |
| 3 | Dismiss | Escape key or click-outside closes overlay |
| 4 | Styling | Dark parchment background (`#2a1e0a`), cream text (`#e8dcc0`), matches table aesthetic. Max width 600px, centered |

## 3. Contract Spec

### handout-object.ts additions

```typescript
export function showHandoutOverlay(data: { title: string; body: string; image_url?: string }): void {
  // Create + inject overlay div
  // Populate with title + body + optional image
  // Esc / click-outside → removeOverlay()
}

export function hideHandoutOverlay(): void { ... }
```

### main.ts additions

```typescript
// In raycast click handler — when hit is fanstack handout mesh:
bridge.send('REQUEST_HANDOUT_READ', { handout_id: hit.object.userData.handoutId });

// WS event handler:
bridge.on('handout_display', (data) => {
  showHandoutOverlay(data as { title: string; body: string; image_url?: string });
});
```

## 4. Test Spec (Gate UI-HANDOUT-READ — 6 tests)

File: `tests/test_ui_gate_cupholder.py` or new `tests/test_ui_gate_handout_read.py`

| ID | Test |
|----|------|
| HR-01 | `showHandoutOverlay()` exported from `handout-object.ts` |
| HR-02 | `hideHandoutOverlay()` exported from `handout-object.ts` |
| HR-03 | `main.ts` sends `REQUEST_HANDOUT_READ` on handout click |
| HR-04 | `main.ts` handles `handout_display` WS event |
| HR-05 | Overlay div created on `showHandoutOverlay()` call |
| HR-06 | Escape key calls `hideHandoutOverlay()` |

## 5. Implementation Plan

1. Read `handout-object.ts` (fanstack click handling), `main.ts` (raycast + WS bridge wiring)
2. Add `showHandoutOverlay()` + `hideHandoutOverlay()` to `handout-object.ts`
3. Wire fanstack click → `REQUEST_HANDOUT_READ` in `main.ts`
4. Wire `handout_display` WS event → `showHandoutOverlay()` in `main.ts`
5. Write 6 tests
6. `pytest` — 6/6 PASS
7. `npm run build --prefix client` — exits 0
8. Full regression — zero new failures

## 6. Deliverables

- [ ] `showHandoutOverlay()` / `hideHandoutOverlay()` in `handout-object.ts`
- [ ] Fanstack click → `REQUEST_HANDOUT_READ` WS message
- [ ] `handout_display` event → overlay display
- [ ] Escape dismisses overlay
- [ ] Gate UI-HANDOUT-READ: 6/6 PASS
- [ ] Zero regressions

## 7. Integration Seams

- **Files modified:** `client/src/handout-object.ts`, `client/src/main.ts`
- **Do not modify:** Engine files, `entity-renderer.ts`, `notebook-object.ts`

## Preflight

```bash
npm run build --prefix client
pytest tests/test_ui_gate_handout_read.py -v
pytest tests/ -x -q --ignore=tests/test_ui_gate_handout_read.py
```
