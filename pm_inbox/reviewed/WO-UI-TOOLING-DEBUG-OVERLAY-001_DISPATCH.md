# WO-UI-TOOLING-DEBUG-OVERLAY-001 — In-Scene Debug Overlay

**Issued:** 2026-02-23
**Authority:** Agent spatial awareness. Anvil writes geometry but cannot see it. A `?debug=1` URL flag renders labeled axes, a coordinate grid, and a live mesh list — turning any Playwright screenshot into a fully annotated spatial map that Anvil can read directly.
**Gate:** TOOLS-DBG (new gate). Target: 6 tests (Python, Gate G static analysis pattern).
**Blocked by:** Nothing. Additive to `main.ts` and `scene-builder.ts` behind a URL flag — zero effect on normal operation.
**Track:** Tooling parallel track. Safe to dispatch alongside PLAYWRIGHT-001.

---

## 1. Target Lock

When Anvil takes a Playwright screenshot of the scene, it sees shapes but cannot identify which mesh is which or confirm coordinates. A debug overlay fixes this by rendering directly into the Three.js scene:

- **AxesHelper** at each major named object: 3 colored arrows (X=red, Y=green, Z=blue) showing exact orientation
- **A floating text label** above each object showing its `.name` property and world position
- **GridHelper** on the table surface: 1-unit grid squares that let Anvil read coordinates by counting grid cells
- **HUD mesh list**: a `<pre>` DOM element listing every named mesh with its position tuple

When Playwright takes a screenshot with `?debug=1`, Anvil can read: "notebook at (-0.2, 0.05, 4.8) — Z should be 4.75, off by 0.05" and patch the coordinate without human involvement.

---

## 2. Binary Decisions

| # | Decision | Choice | Rationale |
|---|---|---|---|
| 1 | Activation mechanism | `?debug=1` URL query param | Zero runtime cost in production. No env var needed. Works in Playwright via `page.goto('/?debug=1')`. |
| 2 | Label rendering | DOM `<canvas>` overlay drawn via `renderer.domElement` sibling | Three.js has no built-in text rendering. A 2D canvas overlay avoids sprite complexity. |
| 3 | Which objects get axes | All objects with `.name` starting with `stub_`, `rail_`, `felt_`, `table_`, `player_`, `lantern_`, `orb_` | Named meshes from scene-builder. Unnamed intermediaries skipped. |
| 4 | Grid helper | `THREE.GridHelper(12, 24)` — 12 units wide, 24 divisions (0.5 unit per cell) | Table is 12 wide. 0.5-unit cells match the `gridToScene()` coordinate transform in entity-renderer. |
| 5 | Grid position | `y = 0.01` (just above table surface) | Visible without z-fighting. |
| 6 | Gate approach | Python Gate G static analysis: confirm debug code is only reachable behind the `isDebug` guard; confirm no `AxesHelper` or `GridHelper` in production path | Prevents debug helpers from shipping. |
| 7 | HUD list element | New `<div id="debug-hud">` appended to body | Distinct from existing `#hud`. Absolute positioned top-right. Monospace font. |
| 8 | Label canvas refresh rate | Once on load (static) — not per-frame | Positions don't change after init. Avoids per-frame label canvas overhead. |

---

## 3. Contract Spec

### 3.1 `client/src/debug-overlay.ts` (new file)

```typescript
/**
 * debug-overlay.ts — Scene debug visualization.
 * Only active when URL contains ?debug=1.
 * NEVER import this in production paths — only called from main.ts behind isDebug guard.
 */
import * as THREE from 'three';

export function isDebugMode(): boolean {
  return new URLSearchParams(window.location.search).get('debug') === '1';
}

/**
 * Add AxesHelper to every named mesh in the scene whose name matches
 * the debug prefix list. Size 0.5 = half a scene unit (readable at table scale).
 */
export function addAxesHelpers(scene: THREE.Scene): void {
  const PREFIXES = ['stub_', 'rail_', 'felt_', 'table_', 'player_', 'dice_', 'cup_', 'trash_'];
  scene.traverse((obj) => {
    if (!obj.name) return;
    if (!PREFIXES.some((p) => obj.name.startsWith(p))) return;
    const axes = new THREE.AxesHelper(0.5);
    axes.name = `__debug_axes_${obj.name}`;
    obj.add(axes); // attach to object so axes move with it
  });
}

/**
 * Add a 12×12 unit GridHelper at y=0.01 (just above table surface).
 * 24 divisions = 0.5-unit cells, matching gridToScene() coordinate transform.
 */
export function addGridHelper(scene: THREE.Scene): void {
  const grid = new THREE.GridHelper(12, 24, 0x444444, 0x222222);
  grid.position.set(0, 0.01, 0);
  grid.name = '__debug_grid';
  scene.add(grid);
}

/**
 * Build a DOM overlay listing all named scene objects with positions.
 * Appended to document.body as #debug-hud.
 */
export function addDebugHUD(scene: THREE.Scene): void {
  const hud = document.createElement('div');
  hud.id = 'debug-hud';
  hud.style.cssText = [
    'position:fixed', 'top:8px', 'right:8px',
    'background:rgba(0,0,0,0.75)', 'color:#00ff88',
    'font:11px/1.4 monospace', 'padding:8px 12px',
    'max-height:80vh', 'overflow-y:auto',
    'border:1px solid #00ff88', 'z-index:9999',
    'pointer-events:none',
  ].join(';');

  const lines: string[] = ['=== DEBUG MESH LIST ==='];
  scene.traverse((obj) => {
    if (!obj.name || obj.name.startsWith('__debug')) return;
    const p = obj.position;
    lines.push(`${obj.name.padEnd(28)} (${p.x.toFixed(2)}, ${p.y.toFixed(2)}, ${p.z.toFixed(2)})`);
  });

  hud.textContent = lines.join('\n');
  document.body.appendChild(hud);
}

/**
 * Mount all debug helpers. Call once after scene is fully constructed.
 */
export function mountDebugOverlay(scene: THREE.Scene): void {
  addGridHelper(scene);
  addAxesHelpers(scene);
  addDebugHUD(scene);
}
```

### 3.2 `client/src/main.ts` addition

At the bottom of the scene setup section, after all objects are added to the scene and before the render loop:

```typescript
// ---------------------------------------------------------------------------
// Debug overlay — only active when ?debug=1 in URL (tooling, never ships)
// ---------------------------------------------------------------------------
import { isDebugMode, mountDebugOverlay } from './debug-overlay';
if (isDebugMode()) {
  mountDebugOverlay(scene);
}
```

### 3.3 Playwright debug screenshot test (add to `scene-postures.spec.ts`)

```typescript
test('PW-DEBUG-01: debug mode renders grid and mesh list', async ({ page }) => {
  await page.goto('/?debug=1');
  await page.waitForSelector('canvas', { timeout: 10_000 });
  await page.waitForTimeout(1_500);

  // Grid helper should exist in scene (no crash)
  const debugHud = await page.$('#debug-hud');
  expect(debugHud).not.toBeNull();

  const hudText = await debugHud!.textContent();
  expect(hudText).toContain('player_shelf');
  expect(hudText).toContain('stub_crystal_ball');
  expect(hudText).toContain('felt_vault');

  // Take annotated screenshot
  await page.screenshot({ path: 'tests/screenshots/debug_standard.png' });
});
```

---

## 4. Test Spec (Gate TOOLS-DBG — 6 tests)

Write `tests/test_ui_debug_overlay_gate.py`:

| ID | Test | Assertion |
|----|------|-----------|
| DBG-01 | `debug-overlay.ts` exists in `client/src/` | File present |
| DBG-02 | `isDebugMode()` only reads `window.location.search` — no side effects | Static analysis: function body contains only URLSearchParams + `.get('debug')` |
| DBG-03 | `mountDebugOverlay` not called in production path | Static analysis: only call site in `main.ts` is inside `if (isDebugMode())` block |
| DBG-04 | No `AxesHelper` or `GridHelper` instantiated outside `debug-overlay.ts` | Grep `client/src/` for `AxesHelper\|GridHelper` — only matches in `debug-overlay.ts` |
| DBG-05 | `#debug-hud` not present in normal page load (no `?debug=1`) | Playwright: `page.goto('/')` → `page.$('#debug-hud')` returns null |
| DBG-06 | `#debug-hud` present in debug page load (`?debug=1`) | Playwright: `page.goto('/?debug=1')` → `page.$('#debug-hud')` not null |

---

## 5. Implementation Plan

1. **Write** `client/src/debug-overlay.ts` (§3.1)
2. **Edit** `client/src/main.ts` — add debug import + `if (isDebugMode())` block after scene construction, before render loop (§3.2)
3. **Write** `tests/test_ui_debug_overlay_gate.py` — 6 tests (DBG-01 through DBG-06)
4. **Run** `npx playwright test` — confirm PW-DEBUG-01 passes, screenshot saved
5. **Read** `client/tests/screenshots/debug_standard.png` — confirm mesh list visible, grid visible, axes at objects
6. **Run** `pytest tests/test_ui_debug_overlay_gate.py -v` — 6/6 PASS
7. **Report** observations from debug screenshot: which objects are misplaced, what coordinates they show

---

## 6. Deliverables Checklist

- [ ] `client/src/debug-overlay.ts` — `isDebugMode()`, `addAxesHelpers()`, `addGridHelper()`, `addDebugHUD()`, `mountDebugOverlay()`
- [ ] `client/src/main.ts` — debug import + `if (isDebugMode()) mountDebugOverlay(scene)` guard
- [ ] `tests/test_ui_debug_overlay_gate.py` — 6/6 PASS
- [ ] Playwright `PW-DEBUG-01` PASS — `debug_standard.png` written
- [ ] Anvil reads `debug_standard.png` and lists every misplaced object with observed vs. expected coordinates
- [ ] Zero regressions on existing Gate G (22/22)

## 7. Integration Seams

- **Files added:** `client/src/debug-overlay.ts`, `tests/test_ui_debug_overlay_gate.py`
- **Files modified:** `client/src/main.ts` (2 lines: import + if-guard)
- **Do not modify:** `scene-builder.ts`, `zones.ts`, any existing test files
- **Reuse:** `THREE.AxesHelper`, `THREE.GridHelper` — already available in three@0.170.0

## 8. Preflight

```bash
pytest tests/test_ui_debug_overlay_gate.py -v
cd client && npx playwright test --grep "debug"
```
