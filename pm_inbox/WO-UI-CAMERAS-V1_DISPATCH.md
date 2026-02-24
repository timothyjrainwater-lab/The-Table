# WO-UI-CAMERAS-V1 — Camera Posture System + Golden Frames

**Issued:** 2026-02-23
**Authority:** PM — AI2AI Exec Packet (TABLE UI NORTH STAR)
**Sequence:** 2 of 6. Depends on WO-UI-LAYOUT-PACK-V1 ACCEPTED.
**Gate:** UI-CAMERAS (new gate, defined below)

---

## 0. Hand-off note

**"Stop tuning by eye in code. Camera postures are data. Read them from `camera_poses.json`. If the golden frame looks wrong, explain why in terms of posture intent — then update the JSON, not the code."**

---

## 1. Target Lock

Wire `camera.ts` to load postures from `docs/design/LAYOUT_PACK_V1/camera_poses.json` (committed by WO-UI-LAYOUT-PACK-V1). Implement smooth butter transitions (350ms, interruptible). Add hotkeys 1–5 for posture switching. Capture four golden PNGs at 1920×1080 and commit them.

**Done means:** Four golden frames committed to `docs/design/LAYOUT_PACK_V1/golden/`. Hotkeys functional. Transitions smooth and interruptible. Gate passes.

---

## 2. Binary Decisions — Locked

| Decision | Answer |
|----------|--------|
| Posture source | `camera_poses.json` — no hardcoded values in camera.ts |
| Transition duration | 350ms (read from `transition_ms` field) |
| Easing | Smoothstep (existing) |
| Interruptible? | Yes — existing behavior preserved |
| Hotkeys | 1=STANDARD, 2=DOWN, 3=LEAN_FORWARD, 4=DICE_TRAY, 5=BOOK_READ |
| Golden frame resolution | 1920×1080 exactly |

---

## 3. Posture Reference (from camera_poses.json)

These values are already in `camera_poses.json` (committed by WO-UI-LAYOUT-PACK-V1). Reproduced here for clarity:

```
STANDARD:      position(0, 1.30, 7.5)   lookAt(0, 0.05, 1.5)
DOWN:          position(0, 5.5,  7.5)   lookAt(0, 0.0,  4.5)
LEAN_FORWARD:  position(0, 2.0,  2.0)   lookAt(0, 0.2,  -2.5)
DICE_TRAY:     position(3.5, 1.1, 5.5)  lookAt(4.5, 0.08, 1.75)
BOOK_READ:     position(2.2, 1.0, 5.4)  lookAt(2.2, 0.07, 4.5)
```

Physical derivation:
- **STANDARD:** Seated eye 1.3m above table surface. Camera body at z=7.5 (behind shelf). lookAt mid-table (z=1.5) puts orb in upper third of frame.
- **DOWN:** Overhead reading. y=5.5 arm's length above shelf. z=7.5 keeps body over shelf zone. lookAt z=4.5 = shelf center. Slight Z offset = embodied, not orthographic.
- **LEAN_FORWARD:** Player physically leans across. y=2.0, z=2.0 = mid-table crouch. lookAt z=−2.5 points into DM side.
- **DICE_TRAY:** Turn right (x=3.5), tabletop sightline (y=1.1), stay over shelf (z=5.5). lookAt at tray center.
- **BOOK_READ:** Drop to page level. Eye at book position + forward offset.

---

## 4. Implementation Spec

### 4.1 `client/src/camera.ts` — JSON-driven

```typescript
// Load postures from JSON at module init (Vite JSON import)
import rawPoses from '../../../docs/design/LAYOUT_PACK_V1/camera_poses.json';

// Build POSTURES map from JSON
const POSTURES: Record<PostureName, PostureConfig> = {} as any;
for (const [name, cfg] of Object.entries(rawPoses.postures)) {
  POSTURES[name as PostureName] = {
    position: new THREE.Vector3(cfg.position.x, cfg.position.y, cfg.position.z),
    lookAt: new THREE.Vector3(cfg.lookAt.x, cfg.lookAt.y, cfg.lookAt.z),
  };
}

const TRANSITION_DURATION_S = rawPoses.transition_ms / 1000;
```

Remove the hardcoded `POSTURES` const. Keep all other logic (interpolation, `setPosture`, `update`) unchanged.

### 4.2 Transition speed

Current implementation uses `speed: 3.0` (rate in posture-progress per second). Replace with duration-based interpolation:

```typescript
// progress advances at 1 / TRANSITION_DURATION_S per second
this.progress = Math.min(1, this.progress + dt / TRANSITION_DURATION_S);
```

This makes 350ms transitions deterministic regardless of frame rate.

### 4.3 Hotkeys in `main.ts`

Add to the `keydown` listener (or create one if needed):

```typescript
const POSTURE_KEYS: Record<string, PostureName> = {
  'Digit1': 'STANDARD',
  'Digit2': 'DOWN',
  'Digit3': 'LEAN_FORWARD',
  'Digit4': 'DICE_TRAY',
  'Digit5': 'BOOK_READ',
};

window.addEventListener('keydown', (e) => {
  const posture = POSTURE_KEYS[e.code];
  if (posture) {
    _cameraPosture.setPosture(posture);
    return;
  }
  // ... existing keydown handlers
});
```

---

## 5. Golden Frame Capture Procedure

After implementing and confirming the postures visually:

1. `npm run dev --prefix client`
2. Open `http://localhost:5173` in Chrome
3. Resize browser window to exactly **1920×1080** (use DevTools device emulation if needed)
4. Press `1` — wait for STANDARD transition to complete
5. Take OS screenshot → save as `docs/design/LAYOUT_PACK_V1/golden/STANDARD_1080.png`
6. Press `2` → `DOWN_1080.png`
7. Press `3` → `LEAN_FORWARD_1080.png`
8. Press `4` → `DICE_TRAY_1080.png`
9. Commit all four PNGs

**Acceptance check before committing each golden frame:**

| Posture | Must pass visual check |
|---------|------------------------|
| STANDARD | Orb visible in upper half. Far rail visible. Vault depth cue (darker recess visible). Shelf barely at bottom (edge visible, objects not prominent). Does NOT show green dice tray under camera. |
| DOWN | All three shelf objects visible and clearly separated. Sheet/notebook/rulebook distinctly readable as three objects. |
| LEAN_FORWARD | Vault recess unmistakably visible (darker felt recessed below rail level). Orb visible in frame. Not looking straight down. |
| DICE_TRAY | Tower and tray occupy at least 40% of frame. Tower opening visible from this angle. |

If a posture does not pass its visual check:
1. Identify which JSON field is wrong (position or lookAt)
2. Update `camera_poses.json` with corrected value
3. Confirm updated result passes visual check
4. Re-capture golden frame

**Do not iterate on code. Only iterate on `camera_poses.json`.**

---

## 6. Gate Spec

**Gate name:** `UI-CAMERAS`
**Test file:** `client/tests/camera_postures.spec.ts`

Gate passes when:

1. Four golden PNGs exist in `docs/design/LAYOUT_PACK_V1/golden/` at 1920×1080
2. Camera loads `camera_poses.json` (confirm via: transition_ms value reflected in transition speed)
3. Hotkeys 1–4 switch postures without console error
4. STANDARD → DOWN transition completes in 350ms ± 50ms (measured via Playwright timing)
5. Transition is interruptible: press 1, immediately press 2, camera transitions from mid-point
6. Each posture's camera position matches JSON values (read via `window.__CAMERA_DEBUG__` if exposed, or via scene dump)

**Test count target:** 6 checks → Gate `UI-CAMERAS` 6/6.

---

## 7. What This WO Does NOT Do

- Does not move objects (WO-UI-OBJECT-LAYOUT-V1)
- Does not change lighting (WO-UI-LIGHTING-V1)
- Does not add physics (WO-UI-PHYSICALITY-BASELINE-V1)
- Does not add screenshot diff tests (WO-UI-GATES-V1)

---

## 8. Preflight

```bash
npm run dev --prefix client
# Press 1-4 to cycle postures
# Confirm smooth transitions
# Confirm each posture matches visual acceptance criteria above
# Capture golden frames
```
