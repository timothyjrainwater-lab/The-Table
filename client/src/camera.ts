/**
 * Camera posture management for the D&D table scene.
 *
 * Posture data is loaded from the Layout Pack authority document:
 *   docs/design/LAYOUT_PACK_V1/camera_poses.json
 *
 * Hardcoded positions are BANNED — all values must come from the JSON.
 * To adjust a camera posture, edit camera_poses.json (and update golden frames).
 *
 * Transitions are smooth (smoothstep lerp) and interruptible.
 * Optics (fov_deg, near, far) are per-posture and interpolated during transitions.
 */

import * as THREE from 'three';
import cameraPosesJson from '../../docs/design/LAYOUT_PACK_V1/camera_poses.json';

export type PostureName = 'STANDARD' | 'DOWN' | 'LEAN_FORWARD' | 'DICE_TRAY' | 'BOOK_READ';

interface PostureConfig {
  position: THREE.Vector3;
  lookAt:   THREE.Vector3;
  fovDeg:   number;
  near:     number;
  far:      number;
}

// ---------------------------------------------------------------------------
// Build POSTURES map from camera_poses.json at module load time.
// transition_ms is exported so callers can read the authoritative duration.
// ---------------------------------------------------------------------------

export const TRANSITION_MS: number = (cameraPosesJson as { transition_ms: number }).transition_ms;

const _poses = (cameraPosesJson as {
  postures: Record<string, {
    position: { x: number; y: number; z: number };
    lookAt:   { x: number; y: number; z: number };
    fov_deg:  number;
    near:     number;
    far:      number;
  }>;
}).postures;

const POSTURES: Record<PostureName, PostureConfig> = {} as Record<PostureName, PostureConfig>;

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

export class CameraPostureController {
  private camera: THREE.PerspectiveCamera;
  private currentPosture: PostureName = 'STANDARD';
  private targetPosture:  PostureName = 'STANDARD';
  private progress: number = 1; // 1 = arrived

  // Duration-based: progress advances at 1 / transitionDuration per second.
  private readonly transitionDuration: number = TRANSITION_MS / 1000;

  // Position / lookAt interpolation state
  private startPos     = new THREE.Vector3();
  private startLookAt  = new THREE.Vector3();
  private endPos       = new THREE.Vector3();
  private endLookAt    = new THREE.Vector3();
  private currentLookAt = new THREE.Vector3();

  // Optics interpolation state
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

    // Apply STANDARD optics immediately — no 60° default at init.
    this._applyOptics(cfg.fovDeg, cfg.near, cfg.far);

    // Seed optics interpolation state.
    this.startFov  = this.endFov  = cfg.fovDeg;
    this.startNear = this.endNear = cfg.near;
    this.startFar  = this.endFar  = cfg.far;
  }

  get posture(): PostureName {
    return this.progress >= 1 ? this.targetPosture : this.currentPosture;
  }

  /** Returns current transition progress (0–1). 1 = arrived. */
  get transitProgress(): number {
    return this.progress;
  }

  setPosture(name: PostureName): void {
    if (name === this.targetPosture && this.progress >= 1) return;

    // Interruptible: capture current interpolated state as new start.
    this.startPos.copy(this.camera.position);
    this.startLookAt.copy(this.currentLookAt);

    // Capture current live optics as start (mid-transition safe).
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
    this.targetPosture  = name;
    this.progress = 0;
  }

  update(dt: number): void {
    if (this.progress >= 1) return;

    // Duration-based: advance by dt / duration so total time = transition_ms.
    this.progress = Math.min(1, this.progress + dt / this.transitionDuration);
    const t = smoothstep(this.progress);

    this.camera.position.lerpVectors(this.startPos, this.endPos, t);
    this.currentLookAt.lerpVectors(this.startLookAt, this.endLookAt, t);
    this.camera.lookAt(this.currentLookAt);

    // Interpolate optics and push to camera each frame.
    const fov  = this.startFov  + (this.endFov  - this.startFov)  * t;
    const near = this.startNear + (this.endNear - this.startNear) * t;
    const far  = this.startFar  + (this.endFar  - this.startFar)  * t;
    this._applyOptics(fov, near, far);
  }

  /** Apply optics to camera and call updateProjectionMatrix(). */
  private _applyOptics(fov: number, near: number, far: number): void {
    this.camera.fov  = fov;
    this.camera.near = near;
    this.camera.far  = far;
    this.camera.updateProjectionMatrix();
  }
}

function smoothstep(t: number): number {
  return t * t * (3 - 2 * t);
}
