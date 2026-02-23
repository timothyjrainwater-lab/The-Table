/**
 * Camera posture management for the D&D table scene.
 *
 * Three postures (UI doctrine §5):
 * - STANDARD: Seated table view (default on load)
 * - DOWN: Reading/writing view (looking down at player-edge)
 * - LEAN_FORWARD: Map engagement view (angled toward center)
 *
 * Transitions are smooth (lerp) and interruptible.
 */

import * as THREE from 'three';

export type PostureName = 'STANDARD' | 'DOWN' | 'LEAN_FORWARD' | 'DICE_TRAY';

interface PostureConfig {
  position: THREE.Vector3;
  lookAt: THREE.Vector3;
}

const POSTURES: Record<PostureName, PostureConfig> = {
  // Seated at the near edge — looking across the open work zone toward the crystal ball.
  // lookAt z=1.0 puts natural gaze on the open walnut work area; shelf is below sightline.
  STANDARD: {
    position: new THREE.Vector3(0, 2.4, 5.8),
    lookAt: new THREE.Vector3(0, 0.1, 1.0),
  },
  // Looking down at the player shelf — sheet, notebook, tome fill the view.
  // Eye raised slightly, lookAt at shelf surface level so objects are centered.
  DOWN: {
    position: new THREE.Vector3(0, 2.2, 5.6),
    lookAt: new THREE.Vector3(0, -0.03, 4.8),
  },
  // Steep overhead angle over the vault — map study view.
  // Eye pulled high and back over the player side, looking down into the vault center.
  LEAN_FORWARD: {
    position: new THREE.Vector3(0, 4.5, 1.5),
    lookAt: new THREE.Vector3(0, 0, -0.5),
  },
  // Looking right at the dice station — player turns head toward the tray.
  // Eye stays near the shelf edge (z≈5.0), shifts right (x≈3.5), drops to
  // tabletop sightline (y≈1.6). lookAt aims at the tray center so the tower,
  // felt floor, and loose d6s all read clearly inside the framed tray.
  DICE_TRAY: {
    position: new THREE.Vector3(3.5, 1.6, 5.0),
    lookAt: new THREE.Vector3(4.5, 0.08, 3.2),
  },
};

export class CameraPostureController {
  private camera: THREE.PerspectiveCamera;
  private currentPosture: PostureName = 'STANDARD';
  private targetPosture: PostureName = 'STANDARD';
  private progress: number = 1; // 1 = arrived
  private speed: number = 3.0;

  // Interpolation state
  private startPos = new THREE.Vector3();
  private startLookAt = new THREE.Vector3();
  private endPos = new THREE.Vector3();
  private endLookAt = new THREE.Vector3();
  private currentLookAt = new THREE.Vector3();

  constructor(camera: THREE.PerspectiveCamera) {
    this.camera = camera;
    const cfg = POSTURES.STANDARD;
    this.camera.position.copy(cfg.position);
    this.camera.lookAt(cfg.lookAt);
    this.currentLookAt.copy(cfg.lookAt);
  }

  get posture(): PostureName {
    return this.progress >= 1 ? this.targetPosture : this.currentPosture;
  }

  setPosture(name: PostureName): void {
    if (name === this.targetPosture && this.progress >= 1) return;

    // Interruptible: capture current interpolated state as new start.
    this.startPos.copy(this.camera.position);
    this.startLookAt.copy(this.currentLookAt);

    const cfg = POSTURES[name];
    this.endPos.copy(cfg.position);
    this.endLookAt.copy(cfg.lookAt);

    this.currentPosture = this.targetPosture;
    this.targetPosture = name;
    this.progress = 0;
  }

  update(dt: number): void {
    if (this.progress >= 1) return;

    this.progress = Math.min(1, this.progress + dt * this.speed);
    const t = smoothstep(this.progress);

    this.camera.position.lerpVectors(this.startPos, this.endPos, t);
    this.currentLookAt.lerpVectors(this.startLookAt, this.endLookAt, t);
    this.camera.lookAt(this.currentLookAt);
  }
}

function smoothstep(t: number): number {
  return t * t * (3 - 2 * t);
}
