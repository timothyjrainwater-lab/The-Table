# WO-UI-CAMERA-OPTICS-001 — Per-Posture Camera Optics

**Issued:** 2026-02-24
**Authority:** PM — Thunder approval (Option C: optics fix before golden frames)
**Sequence:** Must ACCEPT before WO-UI-VISUAL-QA-002 runs (QA-002 produces golden frames).
**Gate:** UI-CAMERA-OPTICS (new gate, defined below)
**Predecessor:** WO-UI-CAMERAS-V1 (ACCEPTED — wired position/lookAt from JSON)

---

## 1. Target Lock

`camera_poses.json` currently specifies only `position` and `lookAt` per posture. FOV, near clip, and far clip are global defaults set at Three.js camera construction and never updated per posture. This is the root cause of:

- **LEAN_FORWARD orb clip**: FOV too narrow — orb visible in the scene at `z≈−3.2` clips out of frame
- **STANDARD "drone at tabletop"**: FOV mismatch makes seated height read as ground-level
- **DOWN foreshortening**: FOV too wide at overhead angle distorts paper-on-table read

**Done means:** each posture's `fov_deg`, `near`, and `far` are loaded from JSON, applied to the Three.js camera on posture switch (including during transition interpolation), and `updateProjectionMatrix()` is called. A runtime debug overlay exposes the active optics. Gate UI-CAMERA-OPTICS passes. QA-002 can then produce golden frames with stable composition.

---

## 2. Current State

| File | Current state |
|------|--------------|
| `docs/design/LAYOUT_PACK_V1/camera_poses.json` | 5 postures — `position` + `lookAt` only. No `fov_deg`, `near`, `far`. |
| `client/src/camera.ts` — `PostureConfig` interface | `{ position: THREE.Vector3; lookAt: THREE.Vector3 }` — no optics fields |
| `client/src/camera.ts` — constructor | `this.camera.position.copy(cfg.position); this.camera.lookAt(cfg.lookAt)` — no fov/near/far set |
| `client/src/camera.ts` — `setPosture()` | Sets `endPos` + `endLookAt`, no optics transition |
| `client/src/camera.ts` — `update()` | Lerps position + lookAt only. Never calls `updateProjectionMatrix()`. |
| Global camera defaults (main.ts) | `new THREE.PerspectiveCamera(60, aspect, 0.1, 100)` — FOV=60, near=0.1, far=100 for all postures |

---

## 3. Authoritative Optics Values

These values are physically grounded and are locked by this WO. Edit `camera_poses.json` to change them — do not hardcode anywhere.

| Posture | fov_deg | near | far | Rationale |
|---------|---------|------|-----|-----------|
| STANDARD | 55 | 0.5 | 50 | Seated human peripheral view. Wider than 60 default reads cramped. Near=0.5 clears shelf edge without clip. |
| DOWN | 45 | 0.3 | 30 | Narrower avoids overhead barrel distortion. Looking down at paper — tight focus. |
| LEAN_FORWARD | 65 | 0.1 | 40 | Wider to keep orb (z≈−3.2) in frame while leaning close over vault. Eliminates orb clip. |
| DICE_TRAY | 60 | 0.3 | 30 | Lateral station view. Standard FOV. Near tight for station proximity. |
| BOOK_READ | 40 | 0.1 | 20 | Tight close-up read. Narrow FOV = page fills frame without distortion. |

**Amendment note:** these values supersede the implicit global defaults inherited from WO-UI-CAMERAS-V1. CAMERAS-V1 spec is amended: "Per-posture optics (fov_deg/near/far) are part of the posture definition, not global defaults. Global camera construction values are starting placeholders only."

---

## 4. Implementation Spec

### 4.1 Extend `camera_poses.json`

Add `fov_deg`, `near`, `far` to every posture object:

```json
{
  "schema": "layout-pack-v1",
  "transition_ms": 350,
  "postures": {
    "STANDARD": {
      "position":  { "x": 0.0,  "y": 1.30, "z": 7.5  },
      "lookAt":    { "x": 0.0,  "y": 0.05, "z": 1.5  },
      "fov_deg":   55,
      "near":      0.5,
      "far":       50,
      "intent": "Seated poker-table view. Orb visible upper frame. Vault depth cue. Shelf barely visible at bottom. No green felt tray in frame.",
      "acceptance": ["orb visible", "far rail visible", "vault recess visible", "reads like sitting at real table"]
    },
    "DOWN": {
      "position":  { "x": 0.0,  "y": 5.5,  "z": 7.5  },
      "lookAt":    { "x": 0.0,  "y": 0.0,  "z": 4.5  },
      "fov_deg":   45,
      "near":      0.3,
      "far":       30,
      "intent": "Belly/reading posture. Shelf artifacts fill frame. Slightly off-perpendicular — embodied, not orthographic.",
      "acceptance": ["sheet primary numbers readable", "notebook page readable", "rulebook headings readable"]
    },
    "LEAN_FORWARD": {
      "position":  { "x": 0.0,  "y": 2.0,  "z": 2.0  },
      "lookAt":    { "x": 0.0,  "y": 0.2,  "z": -2.5 },
      "fov_deg":   65,
      "near":      0.1,
      "far":       40,
      "intent": "Study the vault. Look down into recessed felt. Never true top-down. Orb remains visible and framed.",
      "acceptance": ["vault recess unmistakable", "orb still in frame", "not clipping orb"]
    },
    "DICE_TRAY": {
      "position":  { "x": 3.5,  "y": 1.1,  "z": 5.5  },
      "lookAt":    { "x": 4.5,  "y": 0.08, "z": 1.75 },
      "fov_deg":   60,
      "near":      0.3,
      "far":       30,
      "intent": "Turn right to dice station. Tray + tower dominate frame. Feels like turning, not teleporting.",
      "acceptance": ["tray visible", "tower visible", "tray+tower occupy majority of frame"]
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

### 4.2 Extend `PostureConfig` interface in `camera.ts`

```typescript
interface PostureConfig {
  position: THREE.Vector3;
  lookAt:   THREE.Vector3;
  fovDeg:   number;
  near:     number;
  far:      number;
}
```

### 4.3 Extend JSON parsing block

The `_poses` cast and `POSTURES` build block must include the new fields:

```typescript
const _poses = (cameraPosesJson as {
  postures: Record<string, {
    position: { x: number; y: number; z: number };
    lookAt:   { x: number; y: number; z: number };
    fov_deg:  number;
    near:     number;
    far:      number;
  }>;
}).postures;

(Object.keys(_poses) as PostureName[]).forEach((name) => {
  const p = _poses[name];
  POSTURES[name] = {
    position: new THREE.Vector3(p.position.x, p.position.y, p.position.z),
    lookAt:   new THREE.Vector3(p.lookAt.x,   p.lookAt.y,   p.lookAt.z),
    fovDeg:   p.fov_deg,
    near:     p.near,
    far:      p.far,
  };
});
```

### 4.4 Extend `CameraPostureController` for optics interpolation

Add optics interpolation fields and update `setPosture()` + `update()`:

```typescript
export class CameraPostureController {
  private camera: THREE.PerspectiveCamera;
  private currentPosture: PostureName = 'STANDARD';
  private targetPosture: PostureName = 'STANDARD';
  private progress: number = 1;
  private readonly transitionDuration: number = TRANSITION_MS / 1000;

  // Position / lookAt interpolation state (existing)
  private startPos    = new THREE.Vector3();
  private startLookAt = new THREE.Vector3();
  private endPos      = new THREE.Vector3();
  private endLookAt   = new THREE.Vector3();
  private currentLookAt = new THREE.Vector3();

  // NEW — Optics interpolation state
  private startFov:  number = 55;
  private startNear: number = 0.5;
  private startFar:  number = 50;
  private endFov:    number = 55;
  private endNear:   number = 0.5;
  private endFar:    number = 50;

  constructor(camera: THREE.PerspectiveCamera) {
    this.camera = camera;
    const cfg = POSTURES.STANDARD;
    this.camera.position.copy(cfg.position);
    this.camera.lookAt(cfg.lookAt);
    this.currentLookAt.copy(cfg.lookAt);
    // Apply STANDARD optics immediately on construction
    this._applyOptics(cfg.fovDeg, cfg.near, cfg.far);
    // Seed interpolation state
    this.startFov  = this.endFov  = cfg.fovDeg;
    this.startNear = this.endNear = cfg.near;
    this.startFar  = this.endFar  = cfg.far;
  }

  setPosture(name: PostureName): void {
    if (name === this.targetPosture && this.progress >= 1) return;

    // Interruptible: capture current interpolated state as new start.
    this.startPos.copy(this.camera.position);
    this.startLookAt.copy(this.currentLookAt);
    // Capture current optics as start (mid-transition safe)
    this.startFov  = this.camera.fov;
    this.startNear = this.camera.near;
    this.startFar  = this.camera.far;

    const cfg = POSTURES[name];
    this.endPos.copy(cfg.position);
    this.endLookAt.copy(cfg.lookAt);
    this.endFov  = cfg.fovDeg;
    this.endNear = cfg.near;
    this.endFar  = cfg.far;

    this.currentPosture = this.targetPosture;
    this.targetPosture = name;
    this.progress = 0;
  }

  update(dt: number): void {
    if (this.progress >= 1) return;

    this.progress = Math.min(1, this.progress + dt / this.transitionDuration);
    const t = smoothstep(this.progress);

    this.camera.position.lerpVectors(this.startPos, this.endPos, t);
    this.currentLookAt.lerpVectors(this.startLookAt, this.endLookAt, t);
    this.camera.lookAt(this.currentLookAt);

    // NEW — interpolate optics and push to camera
    const fov  = this.startFov  + (this.endFov  - this.startFov)  * t;
    const near = this.startNear + (this.endNear - this.startNear) * t;
    const far  = this.startFar  + (this.endFar  - this.startFar)  * t;
    this._applyOptics(fov, near, far);
  }

  /** Apply optics and call updateProjectionMatrix(). */
  private _applyOptics(fov: number, near: number, far: number): void {
    this.camera.fov  = fov;
    this.camera.near = near;
    this.camera.far  = far;
    this.camera.updateProjectionMatrix();
  }
}
```

### 4.5 Debug overlay extension (`debug-overlay.ts`)

Add an `addCameraDebugHUD()` function (callable from `mountDebugOverlay()`) that renders a DOM overlay showing:

```
POSTURE:  STANDARD          [SOURCE: camera_poses.json]
POS:      (0.00, 1.30, 7.50)
LOOK_AT:  (0.00, 0.05, 1.50)
FOV:      55.0°
NEAR:     0.50
FAR:      50.0
TRANSIT:  100% (arrived)
```

- Updates every frame (requestAnimationFrame or render loop call)
- Shows `TRANSIT: 63%` during mid-transition
- `SOURCE: camera_poses.json` always (no override path exists)
- Toggle: existing `?debug=1` flag enables it
- DOM element: `id="camera-debug-hud"`, position fixed top-left, monospace font, semi-transparent dark bg, white text, 12px

Implementation: export `updateCameraDebugHUD(controller: CameraPostureController)` from `debug-overlay.ts`. Call it from the main render loop after `controller.update(dt)` if `isDebugMode()`.

---

## 5. Gate Spec

**Gate name:** `UI-CAMERA-OPTICS`
**Test file:** `tests/test_ui_gate_camera_optics.py`

| # | Test | Check |
|---|------|-------|
| CO-01 | STANDARD posture applied → `camera.fov == 55` within ±0.1 | scene dump or Playwright eval |
| CO-02 | DOWN posture applied → `camera.fov == 45` within ±0.1 | |
| CO-03 | LEAN_FORWARD posture applied → `camera.fov == 65` within ±0.1 | Orb clip eliminated |
| CO-04 | DICE_TRAY posture applied → `camera.fov == 60` within ±0.1 | |
| CO-05 | BOOK_READ posture applied → `camera.fov == 40` within ±0.1 | |
| CO-06 | STANDARD near/far: `camera.near == 0.5`, `camera.far == 50` | |
| CO-07 | `updateProjectionMatrix()` called on posture switch (projectionMatrix changes) | compare matrix before/after |
| CO-08 | `camera_poses.json` has `fov_deg`, `near`, `far` for all 5 postures (schema validation) | pytest JSON load + assert |
| CO-09 | Mid-transition FOV is interpolated (not snapped): after 50% transition, fov between start and end | Playwright: rapid switch, sample at 175ms |
| CO-10 | Constructor applies STANDARD optics immediately (not 60° default) | check fov at scene init before any hotkey |

**Test count target:** 10 checks → Gate `UI-CAMERA-OPTICS` 10/10.

**Implementation note:** CO-01 through CO-07 and CO-09 use Playwright to eval `window.__cameraController__.camera.fov` (expose controller on window in dev mode). CO-08 is pure Python JSON parse. CO-10 is Playwright page load check.

Export from `camera.ts` for test access:

```typescript
// Dev/test only — exposes controller for Playwright gate
export let __devCameraController__: CameraPostureController | null = null;
```

In `main.ts`, after constructing the controller:
```typescript
if (import.meta.env.DEV) {
  (window as any).__cameraController__ = cameraController;
}
```

---

## 6. What This WO Does NOT Do

- Does not change `position` or `lookAt` values (those are locked by CAMERAS-V1 JSON; visual QA may propose amendments in QA-002)
- Does not produce golden frames (that is WO-UI-VISUAL-QA-002)
- Does not implement aspect ratio handling per posture (all postures use window aspect ratio)
- Does not add a per-posture `depth_of_field` effect

---

## 7. Preflight

```bash
cd f:/DnD-3.5
python -m pytest tests/test_ui_gate_camera_optics.py -v
# All 10 checks must pass.
# Run full suite: python -m pytest tests/ -x --tb=short
# Zero new regressions expected.
# Confirm: browser at localhost:3000?debug=1 shows camera-debug-hud overlay.
```
