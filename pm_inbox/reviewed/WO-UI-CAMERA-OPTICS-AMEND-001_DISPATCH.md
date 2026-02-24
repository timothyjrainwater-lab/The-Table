# WO-UI-CAMERA-OPTICS-AMEND-001 — Pose Amendment + Vault Grid Removal

**Issued:** 2026-02-24
**Authority:** Thunder — visual audit findings (QA-002 Inspection Pack V1 review)
**Gate:** UI-CAMERA-OPTICS (amends existing gate — re-run, same 10/10 target)
**Prerequisite:** WO-UI-CAMERA-OPTICS-001 must be ACCEPTED (optics live). This WO amends `camera_poses.json` values only + removes vault grid. No structural code changes.

---

## 1. Findings Driving This Amendment

Thunder reviewed the Inspection Pack V1 posture captures and issued four camera corrections plus two scene-state blockers:

| # | Finding | Posture | Severity |
|---|---------|---------|----------|
| F-01 | Vault surface shows digital grid in REST — reads as game HUD | All (visual) | **P0 blocker** |
| F-02 | STANDARD lookAt aimed at shelf, not DM anchor — shelf dominates | STANDARD | P0 |
| F-03 | DOWN reads as top-down drone — no embodiment | DOWN | P0 |
| F-04 | LEAN_FORWARD reads as orb close-up, not vault study | LEAN_FORWARD | P0 |
| F-05 | DICE_TRAY — orb still dominant, tray does not own frame | DICE_TRAY | P0 |
| F-06 | Legibility crops were edge/blank areas — did not show actual text | DOWN crops | Non-blocking (recapture task) |

All 4 camera fixes are `camera_poses.json` edits only. The vault grid fix is a one-line removal in `scene-builder.ts`.

---

## 2. Vault Grid Removal (F-01)

### Root cause

`makeVaultTexture()` in `scene-builder.ts` draws a `rgba(80,120,60,0.25)` grid over the felt:

```typescript
// Faint grid — 1 unit cells  ← REMOVE THIS BLOCK
ctx.strokeStyle = 'rgba(80,120,60,0.25)';
ctx.lineWidth = 1;
const cellW = W / 6.2;
const cellH = H / 4.2;
for (let x = 0; x <= W; x += cellW) { ... }
for (let y = 0; y <= H; y += cellH) { ... }
```

In COMBAT (cover off, felt visible) this grid reads as a digital game map overlay, not physical felt. In REST the vault cover (walnut plane) should hide it, but z-fighting at the cover plane boundary makes the grid visible at grazing angles from STANDARD/LEAN_FORWARD camera.

### Fix

Remove the grid drawing block entirely from `makeVaultTexture()`. Keep only the base fill:

```typescript
function makeVaultTexture(): THREE.CanvasTexture {
  const W = 512, H = 512;
  const canvas = document.createElement('canvas');
  canvas.width = W; canvas.height = H;
  const ctx = canvas.getContext('2d')!;

  // Base: dark green felt — plain, no grid
  ctx.fillStyle = '#162210';
  ctx.fillRect(0, 0, W, H);

  // Subtle noise pass (optional — see §2.1)
  // ...

  const tex = new THREE.CanvasTexture(canvas);
  return tex;
}
```

### §2.1 Optional: subtle felt noise instead of grid

If plain `#162210` reads as a flat digital surface, add a low-opacity noise pass (no grid lines — purely organic):

```typescript
// Organic felt micro-texture — random low-opacity specks
const imageData = ctx.getImageData(0, 0, W, H);
const data = imageData.data;
for (let i = 0; i < data.length; i += 4) {
  const noise = (Math.random() - 0.5) * 8;  // ±4 brightness variance
  data[i]     = Math.max(0, Math.min(255, data[i]     + noise));
  data[i + 1] = Math.max(0, Math.min(255, data[i + 1] + noise));
  data[i + 2] = Math.max(0, Math.min(255, data[i + 2] + noise));
}
ctx.putImageData(imageData, 0, 0);
```

Builder chooses whether to include the noise pass based on visual result. Grid removal is **mandatory**; noise pass is judgment call.

---

## 3. Camera Pose Amendments (F-02 through F-05)

All changes are to `docs/design/LAYOUT_PACK_V1/camera_poses.json`. No TypeScript changes.

### 3.1 STANDARD — lookAt amendment (F-02)

**Current:** `lookAt = { x: 0.0, y: 0.05, z: 1.5 }` — aimed at table center/shelf area. Shelf dominates.

**Amended:** `lookAt = { x: 0.0, y: 0.8, z: -2.6 }` — aimed at the DM anchor above the vault. Pulls eye up, pushes shelf out of dominance, makes orb the upper-frame anchor.

**Intent (updated):** "Seated poker-table view. Eye looks across the table at the DM zone. Orb visible upper-center. Far rail and back wall visible. Vault depth cue in mid-frame. Shelf barely present at bottom edge."

| Field | Old | New |
|-------|-----|-----|
| `lookAt.y` | 0.05 | 0.8 |
| `lookAt.z` | 1.5 | −2.6 |
| `position` | unchanged | unchanged |
| `fov_deg` | 55 | 55 |

### 3.2 DOWN — position + lookAt amendment (F-03)

**Current:** `position = {0, 5.5, 7.5}`, `lookAt = {0, 0, 4.5}` — near-perpendicular overhead. Reads as drone.

**Amended:** Bring camera down and forward to feel like looking at your own lap/shelf from a leaned-forward seated position:
- `position = { x: 0.0, y: 1.6, z: 6.8 }`
- `lookAt   = { x: 0.0, y: 0.0, z: 5.1 }`

**Intent (updated):** "Belly/reading posture. Player looks down at shelf from seated height — angled, not perpendicular. Shelf objects readable. Back of notebook/sheet clearly in view. Slightly off-axis embodied angle."

| Field | Old | New |
|-------|-----|-----|
| `position.y` | 5.5 | 1.6 |
| `position.z` | 7.5 | 6.8 |
| `lookAt.z` | 4.5 | 5.1 |
| `fov_deg` | 45 | 45 |

### 3.3 LEAN_FORWARD — lookAt amendment (F-04)

**Current:** `lookAt = { x: 0.0, y: 0.2, z: -2.5 }` — aimed past the vault, makes orb dominate.

**Amended:** Aim at vault center, not past it:
- `position = { x: 0.0, y: 2.0, z: 1.6 }` (moved slightly back from z=2.0 → z=1.6 to open angle)
- `lookAt   = { x: 0.0, y: -0.2, z: -0.6 }` (vault center, slightly below surface = emphasizes recess)

**Intent (updated):** "Leaning over the table, studying the vault. Vault recess fills mid-frame. Orb visible and framed in upper portion. Never true top-down — slight perspective angle. Not an orb close-up."

| Field | Old | New |
|-------|-----|-----|
| `position.z` | 2.0 | 1.6 |
| `lookAt.y` | 0.2 | −0.2 |
| `lookAt.z` | −2.5 | −0.6 |
| `fov_deg` | 65 | 65 |

### 3.4 DICE_TRAY — position + lookAt amendment (F-05)

**Current:** `position = {3.5, 1.1, 5.5}`, `lookAt = {4.5, 0.08, 1.75}` — orb still in frame, tray doesn't own.

**Amended:** Move closer to station, aim directly at tray+tower:
- `position = { x: 5.0, y: 1.0, z: 3.9 }`
- `lookAt   = { x: 4.5, y: 0.4, z: 1.2 }`

**Intent (updated):** "Turned right to the dice station. Tray and tower fill the majority of frame. No orb in view. Tower opening legible. Tray walls and felt dominant. Feels like turning your chair, not teleporting."

| Field | Old | New |
|-------|-----|-----|
| `position.x` | 3.5 | 5.0 |
| `position.z` | 5.5 | 3.9 |
| `lookAt.y` | 0.08 | 0.4 |
| `lookAt.z` | 1.75 | 1.2 |
| `fov_deg` | 60 | 60 |

---

## 4. Complete Amended `camera_poses.json`

```json
{
  "schema": "layout-pack-v1",
  "transition_ms": 350,
  "postures": {
    "STANDARD": {
      "position":  { "x": 0.0,  "y": 1.30, "z": 7.5  },
      "lookAt":    { "x": 0.0,  "y": 0.8,  "z": -2.6 },
      "fov_deg":   55,
      "near":      0.5,
      "far":       50,
      "intent": "Seated poker-table view. Eye looks across table at DM zone. Orb visible upper-center. Far rail and back wall in frame. Vault depth cue mid-frame. Shelf barely present at bottom edge.",
      "acceptance": ["orb visible upper frame", "far rail visible", "vault depth cue", "reads like sitting across a real table"]
    },
    "DOWN": {
      "position":  { "x": 0.0,  "y": 1.6,  "z": 6.8  },
      "lookAt":    { "x": 0.0,  "y": 0.0,  "z": 5.1  },
      "fov_deg":   45,
      "near":      0.3,
      "far":       30,
      "intent": "Belly/reading posture. Looking down at shelf from seated height — angled, not perpendicular. Shelf objects in clear view. Embodied angle, not drone.",
      "acceptance": ["sheet primary numbers readable", "notebook page readable", "rulebook headings readable", "not orthographic"]
    },
    "LEAN_FORWARD": {
      "position":  { "x": 0.0,  "y": 2.0,  "z": 1.6  },
      "lookAt":    { "x": 0.0,  "y": -0.2, "z": -0.6 },
      "fov_deg":   65,
      "near":      0.1,
      "far":       40,
      "intent": "Leaning over the table, studying the vault recess. Vault fills mid-frame. Orb visible and framed above vault. Slight perspective — not top-down.",
      "acceptance": ["vault recess unmistakable", "orb still in frame", "not an orb close-up", "not clipping orb"]
    },
    "DICE_TRAY": {
      "position":  { "x": 5.0,  "y": 1.0,  "z": 3.9  },
      "lookAt":    { "x": 4.5,  "y": 0.4,  "z": 1.2  },
      "fov_deg":   60,
      "near":      0.3,
      "far":       30,
      "intent": "Turned right to dice station. Tray and tower fill majority of frame. No orb. Tower opening legible. Tray walls and felt dominant.",
      "acceptance": ["tray visible and dominant", "tower visible full height", "tray+tower majority of frame", "no orb in frame"]
    },
    "BOOK_READ": {
      "position":  { "x": 2.2,  "y": 1.0,  "z": 5.4  },
      "lookAt":    { "x": 2.2,  "y": 0.07, "z": 4.5  },
      "fov_deg":   40,
      "near":      0.1,
      "far":       20,
      "intent": "Close-up book reading. Eye drops to page level.",
      "acceptance": ["rulebook page text legible at 1080p"]
    }
  }
}
```

---

## 5. Legibility Crop Fix (F-06)

The three DOWN crops in the inspection pack were cut to edge/blank areas. After re-running the capture script with the amended DOWN pose, the builder must verify crops actually contain readable content:

- `down_crop_sheet.png` — must contain stat block area (HP, AC, attack numbers). Adjust `x/y` pixel offsets until numbers are visible.
- `down_crop_notebook.png` — must contain notebook body text area.
- `down_crop_rulebook.png` — must contain rulebook heading + first paragraph.

No fixed pixel offsets are specified here — builder must visually inspect the amended DOWN capture and find the correct regions. Tool: ImageMagick crop or Playwright screenshot clip.

---

## 6. Stray Die Cleanup (F-05 secondary)

The DICE_TRAY capture showed a stray red die outside tray bounds. This is a demo init artifact. In `_startDemoCombat()` or the demo dice setup, verify all seeded die positions are within the tray volume:

- Tray interior x: 3.39 to 5.61 (walls at 3.3/5.7, 0.06 lip)
- Tray interior z: 1.11 to 2.39
- Die y: just above felt floor (y ≈ 0.08)

If any demo die spawns outside these bounds, clamp its position into the tray or remove it from the demo set.

---

## 7. Operator Action After Recapture

After implementing §2 + §3 and re-running `capture_inspection_v2.mjs`:

1. Builder provides recaptured PNGs for Thunder review (same 4 postures + updated crops)
2. Thunder re-grades against acceptance criteria in WO-UI-VISUAL-QA-002 §2
3. If all 4 postures pass: commit golden frames per QA-002 §4 procedure
4. If any posture still fails: Thunder issues targeted amendment (camera value only — no structural change)

---

## 8. Gate Impact

**Re-run UI-CAMERA-OPTICS gate (10/10) after amending `camera_poses.json`.** The gate checks runtime optics values — position/lookAt are not directly gated (only fov/near/far are). Gate should pass without modification. The `runtime_optics_dump.json` in the inspection pack will reflect new lookAt values.

**UI-VISUAL-QA-002 gate:** QA2-10 checks `runtime_optics_dump.json` against `camera_poses.json` within ±0.5. After this amendment, regenerate `runtime_optics_dump.json` as part of the recapture run.

---

## 9. Preflight

```bash
cd f:/DnD-3.5

# 1. Apply vault grid removal in scene-builder.ts (remove grid drawing block)
# 2. Apply camera_poses.json amendments

# Confirm optics gate still passes
python -m pytest tests/test_ui_gate_camera_optics.py -v
# All 10 must pass (fov/near/far values unchanged, only position/lookAt changed)

# Recapture inspection pack
npm run dev --prefix client &
node scripts/capture_inspection_v2.mjs

# Zero new regressions
python -m pytest tests/ -x --tb=short
```
