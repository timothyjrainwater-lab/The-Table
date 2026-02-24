/**
 * DiceObject — a TableObject representing a d20 die on the table surface.
 *
 * Visual states: idle (in dice tray, fidget animation), held (picked up),
 * rolling (in tower, result-reveal animation). No mechanical authority —
 * all roll results come from Box.
 *
 * Authority: WO-UI-03, DOCTRINE_04_TABLE_UI_MEMO_V4 §7, §19 Slice 2.
 */

import * as THREE from 'three';
import { TableObject, TableObjectPosition } from './table-object';

export type DiceVisualState = 'idle' | 'held' | 'rolling' | 'result';

let diceCounter = 0;

/**
 * DiceObject — d20 die as a TableObject.
 *
 * Spawns in the dice_tray zone. Can be picked and dropped into
 * the dice_tower zone to resolve a PENDING_ROLL.
 */
export class DiceObject implements TableObject {
  readonly id: string;
  readonly kind = 'die';
  position: TableObjectPosition;
  zone: string;
  pickable: boolean;
  readonly object3D: THREE.Object3D;

  private mesh: THREE.Mesh;
  private baseMaterial: THREE.MeshStandardMaterial;
  private scene: THREE.Scene;
  private visualState: DiceVisualState = 'idle';
  private fidgetTime = 0;
  private resultFace: number | null = null;

  // Result-reveal animation state
  private revealStartTime = 0;
  private revealDuration = 0.8; // seconds
  private revealComplete = false;
  private targetRotation: THREE.Euler | null = null;

  // Canvas for face number display
  private textCanvas: HTMLCanvasElement;
  private textCtx: CanvasRenderingContext2D;
  private texture: THREE.CanvasTexture;

  constructor(scene: THREE.Scene, id?: string) {
    this.id = id ?? `die_${++diceCounter}`;
    this.scene = scene;

    // Canvas for rendering the result number on the die face
    this.textCanvas = document.createElement('canvas');
    this.textCanvas.width = 128;
    this.textCanvas.height = 128;
    this.textCtx = this.textCanvas.getContext('2d')!;
    this.texture = new THREE.CanvasTexture(this.textCanvas);

    // d20 represented as an icosahedron — radius 0.12 (die-sized, ~0.24 unit diameter)
    const geo = new THREE.IcosahedronGeometry(0.12, 0);
    this.baseMaterial = new THREE.MeshStandardMaterial({
      color: 0x2244aa,
      roughness: 0.3,
      metalness: 0.2,
      map: this.texture,
    });
    this.mesh = new THREE.Mesh(geo, this.baseMaterial);
    this.mesh.castShadow = true;
    this.mesh.name = `dice_${this.id}`;

    // Wrap in a group so rotation doesn't conflict with table-plane rotation
    this.object3D = new THREE.Group();
    this.object3D.add(this.mesh);

    // Default position: dice_tray felt floor (player zone — moved with tray to z=3.8)
    this.position = { x: 4.5, y: 0.12, z: 3.8 };  // y=0.12 = radius, sits on felt floor
    this.zone = 'dice_tray';
    this.object3D.position.set(this.position.x, this.position.y, this.position.z);
    this.pickable = false; // Not pickable until a PENDING_ROLL activates it

    this._renderFace(null);
  }

  onSpawn(): void {
    this.scene.add(this.object3D);
  }

  onPick(): void {
    this.visualState = 'held';
    this.fidgetTime = 0;
    this.baseMaterial.emissive.setHex(0x334466);
    this.baseMaterial.emissiveIntensity = 0.6;
    this.object3D.position.y = this.position.y + 0.15;
  }

  onDrag(position: TableObjectPosition): void {
    this.object3D.position.set(position.x, position.y, position.z);
  }

  onDrop(zone: string): void {
    this.object3D.position.set(this.position.x, this.position.y, this.position.z);
    this.baseMaterial.emissive.setHex(0x000000);
    this.baseMaterial.emissiveIntensity = 0;
    this.visualState = 'idle';
  }

  onDestroy(): void {
    if (this.object3D.parent) {
      this.object3D.parent.remove(this.object3D);
    }
    this.baseMaterial.dispose();
    this.mesh.geometry.dispose();
    this.texture.dispose();
  }

  // -----------------------------------------------------------------------
  // Dice-specific methods
  // -----------------------------------------------------------------------

  /** Activate the die for a pending roll — make it pickable and start fidget. */
  activate(): void {
    this.pickable = true;
    this.visualState = 'idle';
    this.resultFace = null;
    this.revealComplete = false;
    this.targetRotation = null;
    this._renderFace(null);
  }

  /** Deactivate the die — return to tray, not pickable. */
  deactivate(): void {
    this.pickable = false;
    this.visualState = 'idle';
    this.resultFace = null;
    this.revealComplete = false;
    this.targetRotation = null;
    this.position = { x: 4.5, y: 0.3, z: 1.75 };
    this.zone = 'dice_tray';
    this.object3D.position.set(this.position.x, this.position.y, this.position.z);
    this.mesh.rotation.set(0, 0, 0);
    this._renderFace(null);
  }

  /** Start the result-reveal animation with the authoritative result from Box. */
  showResult(face: number): void {
    this.resultFace = face;
    this.visualState = 'rolling';
    this.revealStartTime = performance.now() / 1000;
    this.revealComplete = false;
    // Deterministic target rotation derived from face value (no RNG)
    const angle = (face / 20) * Math.PI * 2;
    this.targetRotation = new THREE.Euler(angle, angle * 1.3, angle * 0.7);
    this._renderFace(null); // Show blank during tumble
  }

  /** Whether the result reveal animation is done. */
  get isRevealComplete(): boolean {
    return this.revealComplete;
  }

  /** Current visual state. */
  get state(): DiceVisualState {
    return this.visualState;
  }

  /**
   * Update per-frame animation. Call from render loop.
   * @param dt Delta time in seconds.
   */
  updateAnimation(dt: number): void {
    if (this.visualState === 'idle' && this.pickable) {
      // Fidget: gentle rock animation (cosmetic only)
      this.fidgetTime += dt;
      const rock = Math.sin(this.fidgetTime * 2.0) * 0.05;
      const bob = Math.sin(this.fidgetTime * 1.5) * 0.02;
      this.mesh.rotation.z = rock;
      this.mesh.rotation.x = rock * 0.5;
      this.object3D.position.y = this.position.y + bob;
      // Subtle glow pulse
      const glow = 0.1 + Math.sin(this.fidgetTime * 3.0) * 0.05;
      this.baseMaterial.emissive.setHex(0x223344);
      this.baseMaterial.emissiveIntensity = glow;
    }

    if (this.visualState === 'rolling' && this.targetRotation) {
      // Result-reveal tumble animation
      const now = performance.now() / 1000;
      const elapsed = now - this.revealStartTime;
      const t = Math.min(elapsed / this.revealDuration, 1.0);
      // Smoothstep easing
      const s = t * t * (3 - 2 * t);

      // Tumble: fast spin decelerating to target
      const spin = (1 - s) * Math.PI * 4;
      this.mesh.rotation.x = this.targetRotation.x * s + spin;
      this.mesh.rotation.y = this.targetRotation.y * s + spin * 0.7;
      this.mesh.rotation.z = this.targetRotation.z * s + spin * 0.3;

      if (t >= 1.0 && !this.revealComplete) {
        this.revealComplete = true;
        this.visualState = 'result';
        this.mesh.rotation.copy(this.targetRotation);
        this._renderFace(this.resultFace);
        // Flash on reveal
        this.baseMaterial.emissive.setHex(0xffcc00);
        this.baseMaterial.emissiveIntensity = 0.8;
      }
    }

    if (this.visualState === 'result') {
      // Fade glow after reveal
      if (this.baseMaterial.emissiveIntensity > 0.1) {
        this.baseMaterial.emissiveIntensity -= dt * 0.5;
        if (this.baseMaterial.emissiveIntensity < 0.1) {
          this.baseMaterial.emissiveIntensity = 0.1;
        }
      }
    }
  }

  // -----------------------------------------------------------------------
  // Private rendering
  // -----------------------------------------------------------------------

  private _renderFace(face: number | null): void {
    const ctx = this.textCtx;
    const w = this.textCanvas.width;
    const h = this.textCanvas.height;

    // Transparent background (the material color shows through)
    ctx.clearRect(0, 0, w, h);

    if (face !== null) {
      // Draw the result number
      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 64px Consolas, monospace';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(String(face), w / 2, h / 2);
    }

    this.texture.needsUpdate = true;
  }
}
