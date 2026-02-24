# WO-UI-VISUAL-QA-002 — Composition Lock + Golden Frame Commit

**Issued:** 2026-02-24
**Authority:** PM — Thunder approval (Option C: QA pass after optics fix)
**Sequence:** Depends on WO-UI-CAMERA-OPTICS-001 (ACCEPTED). Must not run until per-posture FOV is confirmed live.
**Gate:** UI-VISUAL-QA-002 (new gate, defined below). Unblocks WO-UI-GATES-V1.
**Predecessor:** WO-UI-VISUAL-QA-001 (ACCEPTED — 27 findings), WO-UI-CAMERA-OPTICS-001 (optics fix)

---

## 1. Target Lock

With per-posture optics live (WO-UI-CAMERA-OPTICS-001 ACCEPTED), the composition should now match physical grounding intent. This WO is the acceptance inspection that:

1. Verifies each posture earns its acceptance criteria (not by assertion, by visual evidence)
2. Produces the Inspection Pack V2 with legibility crops, MP4 transition, runtime optics dump, room geometry evidence (ROOM_WIDE + scene_graph_dump), and interaction clips
3. Obtains Thunder approval on each posture
4. Commits four golden frames to `docs/design/LAYOUT_PACK_V1/golden/`
5. Records commit hash + branch in README (non-negotiable)
6. Unblocks WO-UI-GATES-V1 (screenshot diff gate requires committed golden frames)

**Done means:** 4 PNGs committed, Thunder has approved all 4 postures, gate UI-VISUAL-QA-002 passes (legibility checks, orb visibility, vault state, room geometry, commit hash), and WO-UI-GATES-V1 is unblocked.

---

## 2. Acceptance Criteria Per Posture

These are the authoritative pass/fail bars. Each posture must earn ALL of its criteria before golden frame is committed.

### STANDARD
- [ ] Orb visible in upper frame (not clipped, not dominant)
- [ ] Far rail visible (DM side has depth)
- [ ] Vault recess visible (table has dimension, not flat)
- [ ] Shelf barely present at bottom edge (presence, not legibility — that's DOWN's job)
- [ ] Reads as "seated at a real poker table" — not aerial, not drone, not floor-level

### DOWN
- [ ] Character sheet primary stat numbers readable at 1920×1080 (full screenshot)
- [ ] Notebook body text readable at 1920×1080
- [ ] Rulebook heading readable at 1920×1080
- [ ] Not orthographic — slight perspective (embodied lean, not true top-down)
- [ ] Shelf objects fill majority of frame

### LEAN_FORWARD
- [ ] Vault recess unmistakably recessed (the bowl/well is visible)
- [ ] Orb present and framed (not clipped, not at edge)
- [ ] Not true top-down (slight perspective angle)
- [ ] DM zone visible in upper portion of frame

### DICE_TRAY
- [ ] Tray visible and dominant in frame (≥ 40% frame width)
- [ ] Tower visible (full or near-full height), tower mouth legible
- [ ] Tray + tower occupy majority of frame width
- [ ] **Orb 0% visible — 5% safe margin (96px from any edge at 1920×1080)** — hard gate, no partial credit
- [ ] Camera looking downward (lookAt.y < position.y) — drop plausibility
- [ ] No debug overlays visible (grid, axes, zone bounds all OFF)
- [ ] No stray dice outside tray bounds

---

## 3. Inspection Pack V2 — Required Deliverables

The builder produces ALL of the following. Thunder reviews and approves. Only after Thunder approval are golden frames committed.

### 3.1 Posture PNGs (debug OFF)

4 screenshots at exactly 1920×1080, debug mode OFF (`?debug=1` must NOT be in URL):

```
docs/design/LAYOUT_PACK_V1/inspection_v2/standard.png
docs/design/LAYOUT_PACK_V1/inspection_v2/down.png
docs/design/LAYOUT_PACK_V1/inspection_v2/lean_forward.png
docs/design/LAYOUT_PACK_V1/inspection_v2/dice_tray.png
```

Playwright capture script (new file `scripts/capture_inspection_v2.mjs`):

```javascript
import { chromium } from 'playwright';

const POSTURES = ['STANDARD', 'DOWN', 'LEAN_FORWARD', 'DICE_TRAY'];
const HOTKEYS  = { STANDARD: '1', DOWN: '2', LEAN_FORWARD: '3', DICE_TRAY: '4' };
const OUT_DIR  = 'docs/design/LAYOUT_PACK_V1/inspection_v2';

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();
await page.setViewportSize({ width: 1920, height: 1080 });
await page.goto('http://localhost:3000');       // debug=1 NOT included
await page.waitForTimeout(1500);                // initial load settle

for (const posture of POSTURES) {
  await page.keyboard.press(HOTKEYS[posture]);
  await page.waitForTimeout(600);              // 350ms transition + 250ms settle
  await page.screenshot({ path: `${OUT_DIR}/${posture.toLowerCase()}.png` });
}

await browser.close();
```

### 3.2 Legibility Crops (DOWN posture only)

Three 400×200px crops from `down.png`:

```
docs/design/LAYOUT_PACK_V1/inspection_v2/down_crop_sheet.png    — character sheet stats block
docs/design/LAYOUT_PACK_V1/inspection_v2/down_crop_notebook.png — notebook body text
docs/design/LAYOUT_PACK_V1/inspection_v2/down_crop_rulebook.png — rulebook heading + first paragraph
```

Playwright crop script appended to `capture_inspection_v2.mjs` (after DOWN screenshot):

```javascript
// Crop the sheet stats block (adjust region to actual mesh UV position)
const sheetRegion = { x: 200, y: 600, width: 400, height: 200 };
// ... use sharp or canvas to crop and save
```

If Playwright-native crop is not available, produce crops via ImageMagick:
```bash
magick docs/design/LAYOUT_PACK_V1/inspection_v2/down.png \
  -crop 400x200+200+600 \
  docs/design/LAYOUT_PACK_V1/inspection_v2/down_crop_sheet.png
```
Exact pixel regions TBD by visual inspection — builder must verify crop actually contains the readable text.

### 3.3 Framing Crops (STANDARD + LEAN_FORWARD)

Two crops confirming specific acceptance criteria:

```
docs/design/LAYOUT_PACK_V1/inspection_v2/standard_crop_orb.png         — orb upper-frame region
docs/design/LAYOUT_PACK_V1/inspection_v2/lean_forward_crop_orb.png     — orb in lean_forward (not clipped)
```

### 3.4 Runtime Optics Dump (JSON)

A JSON file proving actual runtime values match `camera_poses.json`:

```json
{
  "captured_at": "2026-02-24T...",
  "source": "window.__cameraController__",
  "postures": {
    "STANDARD":      { "fov": 50.0, "near": 0.5,  "far": 50.0, "pos": [0,1.30,7.5],  "lookAt": [0,0.05,-1.0] },
    "DOWN":          { "fov": 45.0, "near": 0.3,  "far": 30.0, "pos": [-1.2,1.5,6.5], "lookAt": [-1.2,0.02,4.9] },
    "LEAN_FORWARD":  { "fov": 65.0, "near": 0.1,  "far": 40.0, "pos": [0,2.5,3.5],   "lookAt": [0,-0.5,-1.5] },
    "DICE_TRAY":     { "fov": 55.0, "near": 0.3,  "far": 30.0, "pos": [3.5,1.4,4.5],  "lookAt": [5.5,0.2,1.5] },
    "BOOK_READ":     { "fov": 40.0, "near": 0.1,  "far": 20.0, "pos": [2.2,1.0,5.4],  "lookAt": [2.2,0.07,4.5] }
  }
}
```

Saved to: `docs/design/LAYOUT_PACK_V1/inspection_v2/runtime_optics_dump.json`

Playwright extraction appended to capture script:

```javascript
const optics = await page.evaluate(() => {
  const ctrl = window.__cameraController__;
  const postures = ['STANDARD', 'DOWN', 'LEAN_FORWARD', 'DICE_TRAY', 'BOOK_READ'];
  const result = {};
  for (const p of postures) {
    ctrl.setPosture(p);
    await new Promise(r => setTimeout(r, 400));
    result[p] = {
      fov: ctrl.camera.fov,
      near: ctrl.camera.near,
      far: ctrl.camera.far,
      pos: ctrl.camera.position.toArray(),
      lookAt: [/* current lookAt */],
    };
  }
  return result;
});
```

### 3.5 Vault State Screenshots

Two screenshots confirming vault cover toggle:

```
docs/design/LAYOUT_PACK_V1/inspection_v2/vault_rest.png    — LEAN_FORWARD with vaultCoverMesh.visible=true (walnut covers felt)
docs/design/LAYOUT_PACK_V1/inspection_v2/vault_combat.png  — LEAN_FORWARD with vaultCoverMesh.visible=false (felt exposed)
```

Playwright: toggle via `window.__debugToggleVaultCover()` (add this to main.ts in dev mode) or via existing `?combat=1` demo flag.

### 3.6 Room Geometry Evidence Pack

Three deliverables establishing room presence as a binary gate, not a visual judgment.

#### 3.6a ROOM_WIDE.png (debug ON)

One screenshot with debug overlay active, confirming room geometry is live:

```
docs/design/LAYOUT_PACK_V1/inspection_v2/room_wide.png
```

Requirements:
- STANDARD posture
- `?debug=1` in URL — debug overlay ON, object names visible in scene graph panel
- `roomEnabled=true` must appear in the debug overlay (or equivalent scene flag)
- Back wall plane and floor plane visible behind/beneath table geometry
- Object name list in overlay must include entries for: `room_floor`, `room_back_wall`, and at least one room light

Playwright capture (appended to `capture_inspection_v2.mjs`, after posture screenshots):

```javascript
// Room wide — debug ON
await page.goto('http://localhost:3000?debug=1');
await page.waitForTimeout(1500);
await page.keyboard.press('1');  // STANDARD posture
await page.waitForTimeout(600);
await page.screenshot({ path: `${OUT_DIR}/room_wide.png` });
await page.goto('http://localhost:3000');  // return to debug OFF
await page.waitForTimeout(1000);
```

#### 3.6b scene_graph_dump.json

A machine-readable boolean report extracted from the running scene:

```
docs/design/LAYOUT_PACK_V1/inspection_v2/scene_graph_dump.json
```

Required schema:

```json
{
  "captured_at": "2026-02-24T...",
  "room_floor_present": true,
  "room_back_wall_present": true,
  "room_lights_present": true,
  "postprocess_enabled": true,
  "exposure": 1.0
}
```

All boolean flags must be `true` for gate QA2-11 to pass.

Playwright extraction appended to capture script:

```javascript
const sceneGraph = await page.evaluate(() => {
  const scene = window.__scene__;  // or however the scene is exposed
  return {
    captured_at: new Date().toISOString(),
    room_floor_present:    !!scene.getObjectByName('room_floor'),
    room_back_wall_present: !!scene.getObjectByName('room_back_wall'),
    room_lights_present:   scene.children.some(o => o.isLight && o.name?.startsWith('room')),
    postprocess_enabled:   !!window.__composer__?.enabled,
    exposure:              window.__renderer__?.toneMappingExposure ?? null,
  };
});
fs.writeFileSync(`${OUT_DIR}/scene_graph_dump.json`, JSON.stringify(sceneGraph, null, 2));
```

**Void detection — pixel mass check:** Run after capturing `room_wide.png` (debug ON):

```python
# In test_ui_visual_qa_002_gate.py
from PIL import Image
import numpy as np

img = Image.open('docs/design/LAYOUT_PACK_V1/inspection_v2/room_wide.png').convert('RGB')
arr = np.array(img)
near_black = np.all(arr < 15, axis=2)
void_fraction = near_black.mean()
assert void_fraction < 0.70, f"room_wide.png is {void_fraction:.1%} near-black — room geometry absent (void)"
```

A frame with > 70% near-black pixels (RGB < 15 in all channels) fails the gate unconditionally.

### 3.7 Interaction Clips (KINEMATIC_DRAG verification)

Four 10-second MP4 clips, one per draggable shelf object, each showing:
1. Hover highlight appears on object
2. Click and drag within SHELF_ZONE
3. Zone clamp behavior — object stops at zone boundary, does not enter DM zone
4. Release — object eases back to shelf Y with lerp settle

```
docs/design/LAYOUT_PACK_V1/inspection_v2/clip_drag_sheet.mp4
docs/design/LAYOUT_PACK_V1/inspection_v2/clip_drag_notebook.mp4
docs/design/LAYOUT_PACK_V1/inspection_v2/clip_drag_rulebook.mp4
docs/design/LAYOUT_PACK_V1/inspection_v2/clip_drag_dicebag.mp4
```

If screen recording is not automated, use OBS/browser record at 1920×1080. Each clip must show the zone clamp — drag the object to the zone boundary and confirm it stops. This is the acceptance evidence for `WO-UI-PHYSICALITY-BASELINE-V1` (already ACCEPTED, clips are retroactive verification).

### 3.8 Transition MP4 (posture switching)

10–15 second clip showing: STANDARD → DOWN → LEAN_FORWARD → DICE_TRAY → STANDARD.
Hold each posture 2 seconds after transition completes.

If Playwright recording is not available: use OBS/screen record with browser in windowed 1920×1080.

---

## 4. Golden Frame Commit Procedure

Once Thunder reviews Inspection Pack V2 and approves all 4 postures:

1. Copy 4 approved PNGs to `docs/design/LAYOUT_PACK_V1/golden/`:
   - `golden/standard.png`
   - `golden/down.png`
   - `golden/lean_forward.png`
   - `golden/dice_tray.png`

2. Commit with message: `golden frames: STANDARD / DOWN / LEAN_FORWARD / DICE_TRAY — approved by Thunder`

3. Update `docs/design/LAYOUT_PACK_V1/README.md` with capture metadata — **mandatory, non-negotiable**:
   - Date captured
   - Browser: Chromium (Playwright)
   - Viewport: 1920×1080
   - **Commit hash** of the repo at time of capture (full 40-char SHA)
   - **Branch name** at time of capture
   - Example entry:
     ```
     Captured: 2026-02-24
     Commit: abc1234...def5678 (full SHA)
     Branch: master
     Viewport: 1920×1080, Chromium (Playwright headless)
     ```
   - Gate QA2-12 verifies README contains a valid 40-char hex commit hash — missing or placeholder hash fails the gate.

4. WO-UI-GATES-V1 is now unblocked — dispatch immediately after commit.

**Note:** `BOOK_READ` posture golden frame is NOT required for GATES-V1. The 4-posture gate spec (CAMERAS-V1) covers STANDARD/DOWN/LEAN_FORWARD/DICE_TRAY only.

---

## 5. Gate Spec

**Gate name:** `UI-VISUAL-QA-002`
**Test file:** `tests/test_ui_visual_qa_002_gate.py`

Automated checks (Playwright-driven, debug OFF):

| # | Test | Check |
|---|------|-------|
| QA2-01 | STANDARD: orb mesh visible (not occluded, alpha > 0.1) | `?dump=1` scene dump: crystal_ball_outer mesh visible=true |
| QA2-02 | STANDARD: far rail present — back wall mesh in scene | scene dump: back_wall mesh exists |
| QA2-03 | DOWN: upper-left and upper-right regions have shelf-object pixel presence | pixelmatch region check vs known shelf region |
| QA2-04 | LEAN_FORWARD: orb mesh visible (not clipped) | scene dump: orb visible=true |
| QA2-05 | LEAN_FORWARD: vault felt mesh visible through open cover | scene dump: vaultCoverMesh visible=false in combat mode |
| QA2-06 | DICE_TRAY: no debug elements (zone bounds, axes) visible | static grep: `?debug=1` not in index.html default URL |
| QA2-07 | DICE_TRAY: dice_tray mesh in scene | scene dump: dice_tray mesh exists |
| QA2-08 | Golden frames directory has exactly 4 PNGs | `glob docs/design/LAYOUT_PACK_V1/golden/*.png == 4` |
| QA2-09 | Each golden frame is 1920×1080 (correct dimensions) | Python PIL: `Image.open(f).size == (1920, 1080)` |
| QA2-10 | Runtime optics dump matches JSON values within ±0.5 | parse `runtime_optics_dump.json`, compare to `camera_poses.json` |
| QA2-11 | Room geometry present — not a void | `room_wide.png`: pixel mass < 70% near-black (RGB<15); `scene_graph_dump.json`: all 3 boolean flags true |
| QA2-12 | README contains valid commit hash + branch | grep `docs/design/LAYOUT_PACK_V1/README.md` for 40-char hex SHA and branch name — missing/placeholder fails |

**Test count target:** 12 checks → Gate `UI-VISUAL-QA-002` 12/12.

---

## 6. Operator Actions (Thunder)

These cannot be delegated to the builder:

1. **Review Inspection Pack V2** — open `docs/design/LAYOUT_PACK_V1/inspection_v2/` and evaluate each posture against acceptance criteria in §2.
2. **Approve or reject postures** — if any posture fails, provide specific feedback. Builder will amend `camera_poses.json` (position, lookAt, OR fov_deg/near/far) and regenerate.
3. **Commit golden frames** — after approving all 4, confirm golden frames are committed per §4 procedure.

This is the final operator gate in the Layout Pack chain.

---

## 7. Dependencies

- **WO-UI-CAMERA-OPTICS-001 ACCEPTED** — per-posture optics must be live before pack is produced
- **Vite dev server running** — `npm run dev` in `client/`
- **`__cameraController__` exposed on window** (implemented by CAMERA-OPTICS-001)
- **`scripts/capture_inspection_v2.mjs`** — new file created by this WO
- **Playwright** — already installed (`client/playwright.config.ts`)
- **Golden frames directory** — builder creates `docs/design/LAYOUT_PACK_V1/golden/` if absent

---

## 8. Preflight

```bash
cd f:/DnD-3.5
# Confirm CAMERA-OPTICS-001 is live
python -m pytest tests/test_ui_gate_camera_optics.py -v

# Generate inspection pack
npm run dev --prefix client &
node scripts/capture_inspection_v2.mjs

# Run QA gate
python -m pytest tests/test_ui_visual_qa_002_gate.py -v
# QA2-01 through QA2-10 must pass (except QA2-08/09 — those pass after Thunder commits golden frames)
```
