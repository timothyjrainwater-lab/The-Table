/**
 * EntityRenderer - WO-UI-06: WebSocket -> Three.js live entity bridge.
 *
 * Manages faction-colored cylinder tokens and HP bars for all entities.
 * Receives engine events (entity_state, entity_delta) and updates the scene.
 *
 * Authority: WO-UI-06.
 * Integration: main.ts registers bridge handlers that call syncRoster() / upsert() / remove().
 *
 * WO-UI-TOKEN-SLIDE-001: position changes lerp over 0.35 s (linear).
 * In replay_mode the lerp is skipped and the token snaps instantly.
 */

import * as THREE from 'three';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const GRID_SCALE = 0.5; // 1 grid unit = 0.5 Three.js scene units

const TOKEN_RADIUS   = 0.18;
const TOKEN_HEIGHT   = 0.06;
const TOKEN_SEGMENTS = 16;
const TOKEN_Y        = 0.002;   // flat chip sits just above table surface

const HP_BAR_WIDTH   = 0.32;
const HP_BAR_HEIGHT  = 0.04;
const HP_BAR_Y_ABOVE = 0.12;

// ---------------------------------------------------------------------------
// WO-ENGINE-MASK-DISPLAY-001 — Fail-closed label render guard
// ---------------------------------------------------------------------------

/**
 * Fail-closed render guard for server-provided label strings.
 * Returns label if safe, 'Unknown' if precision tokens detected.
 * This is an injection guard only — never edits the string, never infers knowledge.
 */
function _guardLabel(label: string): string {
  const FORBIDDEN = [
    /\(\s*\d+\s*[Hh][Pp]\s*\)/,
    /\(\s*[Hh][Pp]\s*\d+\s*\)/,
    /\(\s*\d+\s*\/\s*\d+\s*[Hh][Pp]\)/,
    /\b[Aa][Cc]\s*\d+\b/,
    /\b[Dd][Cc]\s*\d+\b/,
    /\b[Cc][Rr]\s*[\d/]+\b/,
    /\b[Ss][Rr]\s*\d+\b/,
    /\+\d+\s*to\s*hit/,
    /\d+d\d+\+\d+/,
  ];
  return FORBIDDEN.some(p => p.test(label)) ? 'Unknown' : label;
}
const TWEEN_DURATION_MS = 350; // WO-UI-TOKEN-SLIDE-001

const FACTION_COLORS: Record<string, number> = {
  player: 0xd4a820,
  enemy:  0x8b1a1a,
  npc:    0x4a6a8a,
};
const FALLBACK_COLOR = 0x888888;

const HP_COLOR_FULL = new THREE.Color(0x22aa22);
const HP_COLOR_ZERO = new THREE.Color(0xaa2222);

// WO-UI-TOKEN-CHIP-001: 2D flat chip replaces 3D cylinder per North Star vision.
// "Completely flat 2D surface — animated 2D tokens for entities (not 3D models)"
const TOKEN_CHIP_SIZE = 0.4;
const _tokenGeo = new THREE.PlaneGeometry(TOKEN_CHIP_SIZE, TOKEN_CHIP_SIZE);
const _hpBarGeo = new THREE.PlaneGeometry(HP_BAR_WIDTH, HP_BAR_HEIGHT);

// ---------------------------------------------------------------------------
// Public types
// ---------------------------------------------------------------------------

export interface EntityData {
  id: string;
  name?: string;
  faction?: string;
  position?: { x: number; y: number };
  hp_current?: number;
  hp_max?: number;
  conditions?: string[];
}

export interface EntityToken {
  id: string;
  mesh: THREE.Mesh;
  hpBar: THREE.Mesh;
  faction: string;
  hpMax: number;
  tweenFrom?: THREE.Vector3;
  tweenTo?: THREE.Vector3;
  tweenStart?: number;
  tweenDuration?: number;
  tweenHandle?: number | null;
}

// ---------------------------------------------------------------------------
// EntityRenderer
// ---------------------------------------------------------------------------

export class EntityRenderer {
  private tokens: Map<string, EntityToken> = new Map();

  // PENDING_MOVE_TOKEN state — drag is only permitted for the pending token id.
  // Authority: WO-UI-TOKENS-01, DOCTRINE_04_TABLE_UI_MEMO_V4 §16.
  private _pendingMoveTokenId: string | null = null;

  constructor(private scene: THREE.Scene) {}

  upsert(entity: EntityData, replayMode?: boolean): void {
    const existing = this.tokens.get(entity.id);

    if (existing) {
      if (entity.position !== undefined) {
        const targetPos = EntityRenderer.gridToScene(entity.position.x, entity.position.y);

        if (replayMode) {
          if (existing.tweenHandle !== null && existing.tweenHandle !== undefined) {
            cancelAnimationFrame(existing.tweenHandle);
            existing.tweenHandle = null;
          }
          existing.mesh.position.copy(targetPos);
          existing.hpBar.position.set(targetPos.x, targetPos.y + HP_BAR_Y_ABOVE, targetPos.z);
        } else {
          if (existing.tweenHandle !== null && existing.tweenHandle !== undefined) {
            cancelAnimationFrame(existing.tweenHandle);
            existing.tweenHandle = null;
          }

          const fromPos = existing.mesh.position.clone();
          const startTime = performance.now();

          const animate = (now: number): void => {
            const t = Math.min((now - startTime) / TWEEN_DURATION_MS, 1.0);
            existing.mesh.position.lerpVectors(fromPos, targetPos, t);
            existing.hpBar.position.set(
              existing.mesh.position.x,
              existing.mesh.position.y + HP_BAR_Y_ABOVE,
              existing.mesh.position.z,
            );
            if (t < 1.0) {
              existing.tweenHandle = requestAnimationFrame(animate);
            } else {
              existing.tweenHandle = null;
            }
          };

          existing.tweenFrom     = fromPos;
          existing.tweenTo       = targetPos;
          existing.tweenStart    = startTime;
          existing.tweenDuration = TWEEN_DURATION_MS;
          existing.tweenHandle   = requestAnimationFrame(animate);
        }
      }

      const hpCurrent = entity.hp_current;
      const hpMax     = entity.hp_max ?? existing.hpMax;
      if (hpCurrent !== undefined) {
        existing.hpMax = hpMax;
        this._updateHpBar(existing, hpCurrent, hpMax);
      }
      return;
    }

    const faction = entity.faction ?? 'npc';
    const color   = FACTION_COLORS[faction] ?? FALLBACK_COLOR;

    // WO-UI-TOKEN-CHIP-001 + WO-UI-TOKEN-LABEL-001: Canvas texture chip
    const chipTex = EntityRenderer._makeTokenTexture(color, entity.name ?? entity.id);
    const tokenMat = new THREE.MeshBasicMaterial({
      map: chipTex,
      transparent: true,
      side: THREE.DoubleSide,
    });
    const tokenMesh = new THREE.Mesh(_tokenGeo, tokenMat);
    // Rotate flat onto scene (PlaneGeometry is vertical by default)
    tokenMesh.rotation.x = -Math.PI / 2;

    const hpBarMat = new THREE.MeshBasicMaterial({
      color: HP_COLOR_FULL.clone(),
      side: THREE.DoubleSide,
    });
    const hpBarMesh = new THREE.Mesh(_hpBarGeo, hpBarMat);
    hpBarMesh.rotation.x = -Math.PI / 2;

    const pos = entity.position
      ? EntityRenderer.gridToScene(entity.position.x, entity.position.y)
      : new THREE.Vector3(0, TOKEN_Y, 0);

    tokenMesh.position.copy(pos);
    hpBarMesh.position.set(pos.x, pos.y + HP_BAR_Y_ABOVE, pos.z);

    tokenMesh.castShadow = false;
    tokenMesh.receiveShadow = true;

    this.scene.add(tokenMesh);
    this.scene.add(hpBarMesh);

    const hpMax = entity.hp_max ?? 1;
    const token: EntityToken = {
      id: entity.id,
      mesh: tokenMesh,
      hpBar: hpBarMesh,
      faction,
      hpMax,
      tweenHandle: null,
    };
    this.tokens.set(entity.id, token);

    const hpCurrent = entity.hp_current ?? hpMax;
    this._updateHpBar(token, hpCurrent, hpMax);
  }

  remove(id: string): void {
    const token = this.tokens.get(id);
    if (!token) return;
    if (token.tweenHandle !== null && token.tweenHandle !== undefined) {
      cancelAnimationFrame(token.tweenHandle);
      token.tweenHandle = null;
    }
    this.scene.remove(token.mesh);
    this.scene.remove(token.hpBar);
    (token.mesh.material as THREE.Material).dispose();
    (token.hpBar.material as THREE.Material).dispose();
    this.tokens.delete(id);
  }

  syncRoster(entities: EntityData[], replayMode?: boolean): void {
    const incomingIds = new Set(entities.map(e => e.id));

    for (const id of this.tokens.keys()) {
      if (!incomingIds.has(id)) {
        this.remove(id);
      }
    }

    for (const entity of entities) {
      this.upsert(entity, replayMode);
    }
  }

  static gridToScene(x: number, y: number): THREE.Vector3 {
    return new THREE.Vector3(x * GRID_SCALE, TOKEN_Y, y * GRID_SCALE);
  }

  /**
   * WO-UI-TOKEN-CHIP-001 + WO-UI-TOKEN-LABEL-001:
   * Renders a faction-colored circular chip with the entity name initial (up to 8 chars truncated).
   * Returns a CanvasTexture (128×128) for use on a flat PlaneGeometry.
   */
  static _makeTokenTexture(color: number, name: string): THREE.CanvasTexture {
    const SIZE = 128;
    const canvas = document.createElement('canvas');
    canvas.width = SIZE; canvas.height = SIZE;
    const ctx = canvas.getContext('2d')!;

    // Transparent background
    ctx.clearRect(0, 0, SIZE, SIZE);

    // Extract RGB from Three.js hex color
    const r = (color >> 16) & 0xff;
    const g = (color >>  8) & 0xff;
    const b =  color        & 0xff;
    const baseColor = `rgb(${r},${g},${b})`;
    const darkerColor = `rgb(${Math.max(0,r-40)},${Math.max(0,g-40)},${Math.max(0,b-40)})`;

    // Faction disc
    ctx.beginPath();
    ctx.arc(SIZE / 2, SIZE / 2, SIZE / 2 - 4, 0, Math.PI * 2);
    ctx.fillStyle = baseColor;
    ctx.fill();

    // Disc border (darker shade)
    ctx.strokeStyle = darkerColor;
    ctx.lineWidth = 4;
    ctx.stroke();

    // Fail-closed guard: if name contains precision tokens, render 'Unknown'
    const safeName = _guardLabel(name);
    // Name initial (up to 8 chars shown, first char large, rest as label)
    const label = safeName.slice(0, 8);
    const initial = safeName.charAt(0).toUpperCase();

    ctx.fillStyle = 'rgba(255,255,255,0.90)';
    ctx.font = 'bold 48px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(initial, SIZE / 2, SIZE / 2 - 6);

    // Full name label below initial (small, truncated to 8 chars)
    ctx.font = 'bold 14px sans-serif';
    ctx.fillStyle = 'rgba(255,255,255,0.80)';
    ctx.fillText(label, SIZE / 2, SIZE / 2 + 26);

    return new THREE.CanvasTexture(canvas);
  }

  /** Called by main.ts when PENDING_MOVE_TOKEN arrives from server. */
  setMovePending(entityId: string): void {
    this._pendingMoveTokenId = entityId;
  }

  /** Called by main.ts on drag commit, pending_cleared, or scene reset. */
  clearMovePending(): void {
    this._pendingMoveTokenId = null;
  }

  /**
   * Returns true only if a PENDING_MOVE_TOKEN is active for this specific entity.
   * Used by main.ts pointerdown to decide whether to begin a drag or emit click-only intent.
   * Without a matching pending, the chip is click-only (TOKEN_TARGET_INTENT path).
   */
  isDraggable(entityId: string): boolean {
    return this._pendingMoveTokenId === entityId;
  }

  get tokenCount(): number {
    return this.tokens.size;
  }

  hasToken(id: string): boolean {
    return this.tokens.has(id);
  }

  getToken(id: string): EntityToken | undefined {
    return this.tokens.get(id);
  }

  getTokenMeshes(): THREE.Mesh[] {
    return Array.from(this.tokens.values()).map(t => t.mesh);
  }

  getEntityIdByMesh(mesh: THREE.Mesh): string | null {
    for (const token of this.tokens.values()) {
      if (token.mesh === mesh) return token.id;
    }
    return null;
  }

  getEntityFaction(id: string): string | null {
    return this.tokens.get(id)?.faction ?? null;
  }

  private _updateHpBar(token: EntityToken, hpCurrent: number, hpMax: number): void {
    const fraction = hpMax > 0 ? Math.max(0, Math.min(1, hpCurrent / hpMax)) : 0;

    const color = new THREE.Color();
    color.lerpColors(HP_COLOR_ZERO, HP_COLOR_FULL, fraction);
    (token.hpBar.material as THREE.MeshBasicMaterial).color.copy(color);

    token.hpBar.scale.x = Math.max(fraction, 0.01);
  }
}
