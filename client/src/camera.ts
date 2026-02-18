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

export type PostureName = 'STANDARD' | 'DOWN' | 'LEAN_FORWARD';

interface PostureConfig {
  position: THREE.Vector3;
  lookAt: THREE.Vector3;
}

const POSTURES: Record<PostureName, PostureConfig> = {
  STANDARD: {
    position: new THREE.Vector3(0, 5, 8),
    lookAt: new THREE.Vector3(0, 0, 0),
  },
  DOWN: {
    position: new THREE.Vector3(0, 8, 3),
    lookAt: new THREE.Vector3(0, 0, 1),
  },
  LEAN_FORWARD: {
    position: new THREE.Vector3(0, 4, 4),
    lookAt: new THREE.Vector3(0, 0, -2),
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
