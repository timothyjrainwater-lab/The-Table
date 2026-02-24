import * as THREE from 'three';

const SCROLL_Y        = 0.002;  // just above table surface, visible over the felt vault
const SCROLL_W        = 12.0;   // full table width
const SCROLL_H_CLOSED = 0.0;    // Z scale when rolled (invisible thin cylinder)
const SCROLL_H_OPEN   = 8.0;    // Z extent when fully unrolled (8 grid units deep)

// Suppress unused-variable warning for the closed constant
void SCROLL_H_CLOSED;

const UNROLL_DURATION = 1.2;    // seconds
const ROLLUP_DURATION = 0.8;    // seconds

/** Seeded PRNG type (from scene-builder / dice-bag). */
type PrngFn = () => number;

/**
 * BattleScrollObject — magical scroll that unrolls on combat_start.
 *
 * Visual: a flat parchment plane that scales from Z=0 to full on unroll.
 * Entity tokens and map overlays should only be visible while scroll is unrolled.
 *
 * Gate UI-SCROLL: 8 tests.
 * Seeded PRNG only — no random calls.
 */
export class BattleScrollObject {
  readonly group: THREE.Group;

  private _scrollMesh: THREE.Mesh;
  private _scrollMat: THREE.MeshStandardMaterial;
  private _rod: THREE.Mesh | null = null;
  private _isUnrolled: boolean = false;
  private _animHandle: number | null = null;
  private _currentScaleZ: number = 0.001;
  private _targetScaleZ: number = 0.001;
  private _animStart: number = 0.0;
  private _animDuration: number = UNROLL_DURATION;

  // Groups to show/hide with scroll state
  private _tokenGroup: THREE.Object3D | null = null;
  private _overlayGroup: THREE.Object3D | null = null;

  constructor(prng: PrngFn) {
    this.group = new THREE.Group();
    this.group.name = 'battle_scroll';

    // Scroll surface — PlaneGeometry representing the unrolled parchment.
    // We scale scaleZ from 0 → 1 to simulate unrolling.
    const geo = new THREE.PlaneGeometry(SCROLL_W, SCROLL_H_OPEN);
    const tex = this._buildParchmentTexture(prng);
    this._scrollMat = new THREE.MeshStandardMaterial({
      map: tex,
      roughness: 0.85,
      metalness: 0.0,
      emissive: new THREE.Color(0x8a6a30),
      emissiveIntensity: 0.15,
      side: THREE.DoubleSide,
    });
    this._scrollMesh = new THREE.Mesh(geo, this._scrollMat);
    this._scrollMesh.name = 'battle_scroll_surface';
    this._scrollMesh.rotation.x = -Math.PI / 2;
    // Center Z offset: plane pivot is center, so shift back so unroll goes toward DM
    this._scrollMesh.position.set(0, SCROLL_Y, -SCROLL_H_OPEN / 2 + 0.5);
    this._scrollMesh.scale.z = 0.001; // Nearly zero — rolled state
    this._scrollMesh.visible = false;  // Hidden until combat_start unrolls
    this._currentScaleZ = 0.001;
    this.group.add(this._scrollMesh);

    // Rolled cylinder ornament (visual — the rolled-up scroll at the near edge)
    const cylGeo = new THREE.CylinderGeometry(0.12, 0.12, SCROLL_W, 16);
    const cylMat = new THREE.MeshStandardMaterial({
      color: 0xb87038,  // wood/scroll-rod color
      roughness: 0.7,
      metalness: 0.1,
    });
    const cylinder = new THREE.Mesh(cylGeo, cylMat);
    cylinder.name = 'battle_scroll_rod';
    cylinder.rotation.z = Math.PI / 2;  // lay horizontal
    // Rod sits at the player-near edge of the scroll when unrolled.
    // Hidden in rolled state — only visible when scroll is fully out.
    cylinder.position.set(0, SCROLL_Y + 0.12, 0.5);
    cylinder.visible = false;  // hidden until combat_start unrolls the scroll
    this.group.add(cylinder);
    this._rod = cylinder;
  }

  get isUnrolled(): boolean {
    return this._isUnrolled;
  }

  get scrollScaleZ(): number {
    return this._currentScaleZ;
  }

  /**
   * Link entity token group — will be shown/hidden with scroll state.
   * Pass the Three.js Object3D that contains all entity tokens.
   */
  linkTokenGroup(group: THREE.Object3D): void {
    this._tokenGroup = group;
    group.visible = false; // hidden until unrolled
  }

  /**
   * Link map overlay group — will be shown/hidden with scroll state.
   */
  linkOverlayGroup(group: THREE.Object3D): void {
    this._overlayGroup = group;
    group.visible = false;
  }

  /** Called on combat_start WS event. Unrolls scroll over 1.2s. */
  onCombatStart(): void {
    if (this._isUnrolled) return; // already unrolled — safe no-op
    this._isUnrolled = true;
    this._scrollMesh.visible = true;  // show before animating
    if (this._tokenGroup)  this._tokenGroup.visible = true;
    if (this._overlayGroup) this._overlayGroup.visible = true;
    if (this._rod) this._rod.visible = true;
    this._startAnim(1.0, UNROLL_DURATION);
  }

  /** Called on combat_end WS event. Rolls up scroll over 0.8s. */
  onCombatEnd(): void {
    if (!this._isUnrolled) return;
    this._isUnrolled = false;
    if (this._tokenGroup)  this._tokenGroup.visible = false;
    if (this._overlayGroup) this._overlayGroup.visible = false;
    if (this._rod) this._rod.visible = false;
    this._startAnim(0.001, ROLLUP_DURATION, () => {
      this._scrollMesh.visible = false;  // hide after roll-up completes
    });
  }

  dispose(): void {
    if (this._animHandle !== null) {
      cancelAnimationFrame(this._animHandle);
      this._animHandle = null;
    }
    this._scrollMat.dispose();
  }

  private _startAnim(targetScale: number, duration: number, onComplete?: () => void): void {
    if (this._animHandle !== null) {
      cancelAnimationFrame(this._animHandle);
      this._animHandle = null;
    }
    this._targetScaleZ = targetScale;
    this._animDuration = duration;
    this._animStart = performance.now();
    const fromScale = this._currentScaleZ;

    const animate = (now: number): void => {
      const elapsed = (now - this._animStart) / 1000;
      const t = Math.min(elapsed / this._animDuration, 1.0);
      this._currentScaleZ = fromScale + (this._targetScaleZ - fromScale) * t;
      this._scrollMesh.scale.z = this._currentScaleZ;
      if (t < 1.0) {
        this._animHandle = requestAnimationFrame(animate);
      } else {
        this._animHandle = null;
        onComplete?.();
      }
    };
    this._animHandle = requestAnimationFrame(animate);
  }

  private _buildParchmentTexture(prng: PrngFn): THREE.CanvasTexture {
    const canvas = document.createElement('canvas');
    canvas.width = 1024;
    canvas.height = 1024;
    const ctx = canvas.getContext('2d')!;

    // Parchment base — warm cream, bright enough to read over dark table
    ctx.fillStyle = '#f0e4c0';
    ctx.fillRect(0, 0, 1024, 1024);

    // Subtle aged vignette edges
    const vignette = ctx.createRadialGradient(512, 512, 200, 512, 512, 720);
    vignette.addColorStop(0, 'rgba(0,0,0,0)');
    vignette.addColorStop(1, 'rgba(60,35,5,0.35)');
    ctx.fillStyle = vignette;
    ctx.fillRect(0, 0, 1024, 1024);

    // Grain using seeded PRNG (Gate G compliant)
    for (let i = 0; i < 12000; i++) {
      const x = prng() * 1024;
      const y = prng() * 1024;
      const v = Math.floor(140 + prng() * 60);
      ctx.fillStyle = `rgba(${v},${v - 12},${v - 30},0.05)`;
      ctx.fillRect(x, y, 2, 2);
    }

    // Grid lines — strong dark ink, clearly visible on parchment
    ctx.strokeStyle = 'rgba(60,35,10,0.70)';
    ctx.lineWidth = 1.5;
    const cellSize = 1024 / 20; // 20 cells across the map
    for (let i = 0; i <= 20; i++) {
      ctx.beginPath();
      ctx.moveTo(i * cellSize, 0);
      ctx.lineTo(i * cellSize, 1024);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(0, i * cellSize);
      ctx.lineTo(1024, i * cellSize);
      ctx.stroke();
    }

    // Heavier lines every 5 cells (tactical grid zones)
    ctx.strokeStyle = 'rgba(60,35,10,0.90)';
    ctx.lineWidth = 2.5;
    for (let i = 0; i <= 20; i += 5) {
      ctx.beginPath();
      ctx.moveTo(i * cellSize, 0);
      ctx.lineTo(i * cellSize, 1024);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(0, i * cellSize);
      ctx.lineTo(1024, i * cellSize);
      ctx.stroke();
    }

    // Center cross marker
    ctx.strokeStyle = 'rgba(100,50,10,0.5)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(512 - 16, 512); ctx.lineTo(512 + 16, 512);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(512, 512 - 16); ctx.lineTo(512, 512 + 16);
    ctx.stroke();

    return new THREE.CanvasTexture(canvas);
  }
}
