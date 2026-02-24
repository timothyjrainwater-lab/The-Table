import * as THREE from 'three';

const BAG_COLOR  = 0x3d2008;  // dark brown leather
const KNOT_COLOR = 0x5a3010;  // lighter brown for knot/seam

// ---------------------------------------------------------------------------
// TowerPlaque — dice formula display surface near the tower.
//
// Visibility rule: visible ONLY when a PendingRoll is active.
// Content rule:    shows the dice spec string only (e.g. "1d20+4").
//                  NEVER shows DC, difficulty, armor class, or target values.
//
// Gate DICE-RITUAL-01: plaque.setPending(spec) shows formula; plaque.clear() hides.
// Gate DICE-RITUAL-06: no DC / difficulty / armor class / target string in this class.
// ---------------------------------------------------------------------------

/**
 * TowerPlaque — a flat 3D surface mounted on the face of the dice tower.
 * Displays the roll spec (formula) when a PENDING_ROLL is active.
 * Hidden at all other times.
 *
 * Geometry: PlaneGeometry(0.38, 0.16) mounted vertically on the tower front face.
 * Anchor: dice_tower_base = (4.5, 0.065, 0.5). Plaque sits at y≈0.72 (eye-level on tower).
 */
export class TowerPlaque {
  readonly mesh: THREE.Mesh;
  private _mat: THREE.MeshBasicMaterial;
  private _canvas: HTMLCanvasElement;
  private _ctx: CanvasRenderingContext2D;
  private _tex: THREE.CanvasTexture;

  constructor(towerBaseX: number, towerBaseY: number, towerBaseZ: number) {
    this._canvas = document.createElement('canvas');
    this._canvas.width = 256;
    this._canvas.height = 96;
    this._ctx = this._canvas.getContext('2d')!;

    this._tex = new THREE.CanvasTexture(this._canvas);
    this._mat = new THREE.MeshBasicMaterial({
      map: this._tex,
      transparent: true,
      opacity: 0.0,
      side: THREE.DoubleSide,
      depthWrite: false,
    });

    const geo = new THREE.PlaneGeometry(0.38, 0.16);
    this.mesh = new THREE.Mesh(geo, this._mat);
    this.mesh.name = 'tower_plaque';
    // Mount on the south face of the tower (facing +Z, toward player)
    this.mesh.position.set(towerBaseX, towerBaseY + 0.655, towerBaseZ + 0.278);
    // No rotation needed — PlaneGeometry faces +Z by default
    this._renderBlank();
  }

  /**
   * Activate the plaque with the given dice spec formula.
   * Shows the formula string only — no DC, no difficulty, no target.
   */
  setPending(spec: string): void {
    this._renderSpec(spec);
    this._mat.opacity = 1.0;
    this._mat.needsUpdate = true;
  }

  /**
   * Clear and hide the plaque. Called when PENDING_ROLL is resolved or cancelled.
   */
  clear(): void {
    this._mat.opacity = 0.0;
    this._mat.needsUpdate = true;
    this._renderBlank();
  }

  private _renderSpec(spec: string): void {
    const ctx = this._ctx;
    const W = this._canvas.width;
    const H = this._canvas.height;
    ctx.clearRect(0, 0, W, H);
    // Dark parchment background
    ctx.fillStyle = 'rgba(18, 10, 4, 0.88)';
    ctx.fillRect(0, 0, W, H);
    ctx.strokeStyle = '#c8a040';
    ctx.lineWidth = 2;
    ctx.strokeRect(2, 2, W - 4, H - 4);
    // Formula text only — spec is the dice formula string (e.g. "1d20+4")
    ctx.fillStyle = '#ffe066';
    ctx.font = 'bold 36px Consolas, monospace';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(spec, W / 2, H / 2);
    this._tex.needsUpdate = true;
  }

  private _renderBlank(): void {
    const ctx = this._ctx;
    ctx.clearRect(0, 0, this._canvas.width, this._canvas.height);
    this._tex.needsUpdate = true;
  }
}

/** Simple linear lerp. */
function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

/**
 * Local seeded PRNG (LCG) — same algorithm as scene-builder.ts makePrng.
 * Gate G compliant — seeded only.
 */
export function makePrng(seed: number): () => number {
  let state = seed >>> 0;
  return (): number => {
    state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
    return (state & 0x7fffffff) / 0x7fffffff;
  };
}

/**
 * DiceBagObject — leather dice bag on player shelf.
 *
 * Click bag body → open animation (lid lifts).
 * Decorative d4/d6/d8/d10/d12 visible when open.
 * d20 is always present (magical bag — picking up d20 doesn't empty the bag).
 *
 * Gate UI-DICE: 6 tests.
 * Seeded PRNG only (Gate G compliant).
 */
export class DiceBagObject {
  readonly group: THREE.Group;
  private _lidMesh: THREE.Mesh;
  private _bodyMesh: THREE.Mesh;
  private _decorDice: THREE.Mesh[] = [];
  private _isOpen: boolean = false;
  private _animHandle: number | null = null;

  constructor(private scene: THREE.Scene, private prng: () => number) {
    this.group = new THREE.Group();
    this.group.name = 'dice_bag';

    const bagMat = new THREE.MeshStandardMaterial({
      color: BAG_COLOR,
      roughness: 0.9,
      metalness: 0.05,
    });

    // Bag body — rounded box approximation using BoxGeometry
    const bodyGeo = new THREE.BoxGeometry(0.4, 0.3, 0.5);
    this._bodyMesh = new THREE.Mesh(bodyGeo, bagMat);
    this._bodyMesh.name = 'dice_bag_body';
    this._bodyMesh.position.set(0, 0, 0);
    this._bodyMesh.castShadow = true;
    this._bodyMesh.receiveShadow = true;
    this.group.add(this._bodyMesh);

    // Bag lid — top cap that lifts during open animation
    const lidGeo = new THREE.BoxGeometry(0.42, 0.08, 0.52);
    const lidMat = new THREE.MeshStandardMaterial({
      color: KNOT_COLOR,
      roughness: 0.85,
      metalness: 0.05,
    });
    this._lidMesh = new THREE.Mesh(lidGeo, lidMat);
    this._lidMesh.name = 'dice_bag_lid';
    this._lidMesh.position.set(0, 0.19, 0);  // sits on top of body
    this._lidMesh.castShadow = true;
    this.group.add(this._lidMesh);

    // Knot/seam strip
    const knotGeo = new THREE.BoxGeometry(0.44, 0.04, 0.08);
    const knotMat = new THREE.MeshStandardMaterial({ color: KNOT_COLOR, roughness: 0.95 });
    const knot = new THREE.Mesh(knotGeo, knotMat);
    knot.name = 'dice_bag_knot';
    knot.position.set(0, 0.15, 0.2);
    this.group.add(knot);

    // Decorative dice (hidden until open)
    this._decorDice = this._buildDecorDice(prng);
    for (const d of this._decorDice) {
      d.visible = false;
      this.group.add(d);
    }

    // Position on player shelf (left of notebook at x=-0.2)
    this.group.position.set(-2.4, -0.10, 4.8);
  }

  get isOpen(): boolean {
    return this._isOpen;
  }

  /** Opens the bag — lifts lid and reveals decorative dice. */
  open(): void {
    if (this._isOpen) return;
    this._isOpen = true;
    for (const d of this._decorDice) d.visible = true;
    this._animateLid(this._lidMesh.position.y, 0.55, 400);
  }

  /** Closes the bag — lowers lid and hides decorative dice. */
  close(): void {
    if (!this._isOpen) return;
    this._isOpen = false;
    const self = this;
    this._animateLid(this._lidMesh.position.y, 0.19, 300, () => {
      for (const d of self._decorDice) d.visible = false;
    });
  }

  /** Toggle open/close. */
  toggle(): void {
    if (this._isOpen) this.close();
    else this.open();
  }

  /** Returns the body mesh for raycasting / click detection. */
  get bodyMesh(): THREE.Mesh {
    return this._bodyMesh;
  }

  dispose(): void {
    if (this._animHandle !== null) {
      cancelAnimationFrame(this._animHandle);
      this._animHandle = null;
    }
  }

  private _animateLid(
    fromY: number,
    toY: number,
    durationMs: number,
    onComplete?: () => void,
  ): void {
    if (this._animHandle !== null) {
      cancelAnimationFrame(this._animHandle);
    }
    const startTime = performance.now();
    const animate = (now: number) => {
      const elapsed = now - startTime;
      const t = Math.min(elapsed / durationMs, 1.0);
      this._lidMesh.position.y = lerp(fromY, toY, t);
      if (t < 1.0) {
        this._animHandle = requestAnimationFrame(animate);
      } else {
        this._animHandle = null;
        if (onComplete) onComplete();
      }
    };
    this._animHandle = requestAnimationFrame(animate);
  }

  private _buildDecorDice(prng: () => number): THREE.Mesh[] {
    const dice: THREE.Mesh[] = [];
    const diceMat = () => new THREE.MeshStandardMaterial({
      color: this._diceColor(prng),
      roughness: 0.4,
      metalness: 0.1,
    });

    // d4 — tetrahedron
    const d4 = new THREE.Mesh(new THREE.TetrahedronGeometry(0.05), diceMat());
    d4.name = 'decor_d4'; d4.position.set(-0.12, 0.06, -0.12); dice.push(d4);

    // d6 — box
    const d6 = new THREE.Mesh(new THREE.BoxGeometry(0.07, 0.07, 0.07), diceMat());
    d6.name = 'decor_d6'; d6.position.set(0.0, 0.06, -0.08); dice.push(d6);

    // d8 — octahedron
    const d8 = new THREE.Mesh(new THREE.OctahedronGeometry(0.055), diceMat());
    d8.name = 'decor_d8'; d8.position.set(0.12, 0.06, -0.1); dice.push(d8);

    // d10 — icosahedron approximation
    const d10 = new THREE.Mesh(new THREE.IcosahedronGeometry(0.05, 0), diceMat());
    d10.name = 'decor_d10'; d10.position.set(-0.10, 0.06, 0.05); dice.push(d10);

    // d12 — dodecahedron
    const d12 = new THREE.Mesh(new THREE.DodecahedronGeometry(0.055), diceMat());
    d12.name = 'decor_d12'; d12.position.set(0.10, 0.06, 0.08); dice.push(d12);

    return dice;
  }

  private _diceColor(prng: () => number): number {
    // Seeded color from ivory/cream palette
    const hueBase = 30;
    const hueRange = Math.floor(prng() * 40);  // 0–39
    const hue = hueBase + hueRange;
    const sat = 0.4 + prng() * 0.3;
    const val = 0.8 + prng() * 0.2;
    return new THREE.Color().setHSL(hue / 360, sat, val).getHex();
  }
}
