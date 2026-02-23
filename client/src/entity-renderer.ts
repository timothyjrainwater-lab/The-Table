/**
 * EntityRenderer — WO-UI-06: WebSocket → Three.js live entity bridge.
 *
 * Manages faction-colored cylinder tokens and HP bars for all entities.
 * Receives engine events (entity_state, entity_delta) and updates the scene.
 *
 * Authority: WO-UI-06.
 * Integration: main.ts registers bridge handlers that call syncRoster() / upsert() / remove().
 */

import * as THREE from 'three';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const GRID_SCALE = 0.5; // 1 grid unit = 0.5 Three.js scene units

const TOKEN_RADIUS   = 0.18;
const TOKEN_HEIGHT   = 0.06;
const TOKEN_SEGMENTS = 16;
const TOKEN_Y        = 0.08; // sit just above table surface (top ≈ 0.0)

const HP_BAR_WIDTH   = 0.32;
const HP_BAR_HEIGHT  = 0.04;
const HP_BAR_Y_ABOVE = 0.12; // above token center

const FACTION_COLORS: Record<string, number> = {
  player: 0xd4a820, // warm gold
  enemy:  0x8b1a1a, // deep red
  npc:    0x4a6a8a, // slate blue
};
const FALLBACK_COLOR = 0x888888;

const HP_COLOR_FULL = new THREE.Color(0x22aa22); // green
const HP_COLOR_ZERO = new THREE.Color(0xaa2222); // red

// Shared geometry (built once, reused per token)
const _tokenGeo = new THREE.CylinderGeometry(TOKEN_RADIUS, TOKEN_RADIUS, TOKEN_HEIGHT, TOKEN_SEGMENTS);
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
}

// ---------------------------------------------------------------------------
// EntityRenderer
// ---------------------------------------------------------------------------

export class EntityRenderer {
  private tokens: Map<string, EntityToken> = new Map();

  constructor(private scene: THREE.Scene) {}

  /**
   * Spawn or update a token for the given entity data.
   * If a token with the same id already exists it is updated in-place (no duplicate).
   */
  upsert(entity: EntityData): void {
    const existing = this.tokens.get(entity.id);

    if (existing) {
      // Update position
      if (entity.position !== undefined) {
        const pos = EntityRenderer.gridToScene(entity.position.x, entity.position.y);
        existing.mesh.position.copy(pos);
        existing.hpBar.position.set(pos.x, pos.y + HP_BAR_Y_ABOVE, pos.z);
      }

      // Update HP
      const hpCurrent = entity.hp_current;
      const hpMax     = entity.hp_max ?? existing.hpMax;
      if (hpCurrent !== undefined) {
        existing.hpMax = hpMax;
        this._updateHpBar(existing, hpCurrent, hpMax);
      }
      return;
    }

    // Spawn new token
    const faction = entity.faction ?? 'npc';
    const color   = FACTION_COLORS[faction] ?? FALLBACK_COLOR;

    const tokenMat = new THREE.MeshStandardMaterial({
      color,
      roughness: 0.6,
      metalness: 0.2,
    });
    const tokenMesh = new THREE.Mesh(_tokenGeo, tokenMat);

    const hpBarMat = new THREE.MeshBasicMaterial({
      color: HP_COLOR_FULL.clone(),
      side: THREE.DoubleSide,
    });
    const hpBarMesh = new THREE.Mesh(_hpBarGeo, hpBarMat);
    // Rotate flat (PlaneGeometry is vertical by default)
    hpBarMesh.rotation.x = -Math.PI / 2;

    // Position
    const pos = entity.position
      ? EntityRenderer.gridToScene(entity.position.x, entity.position.y)
      : new THREE.Vector3(0, TOKEN_Y, 0);

    tokenMesh.position.copy(pos);
    hpBarMesh.position.set(pos.x, pos.y + HP_BAR_Y_ABOVE, pos.z);

    tokenMesh.castShadow = true;
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
    };
    this.tokens.set(entity.id, token);

    // Set initial HP bar state
    const hpCurrent = entity.hp_current ?? hpMax;
    this._updateHpBar(token, hpCurrent, hpMax);
  }

  /**
   * Remove a token (entity defeated or left combat).
   */
  remove(id: string): void {
    const token = this.tokens.get(id);
    if (!token) return;
    this.scene.remove(token.mesh);
    this.scene.remove(token.hpBar);
    // Dispose materials to avoid leaks
    (token.mesh.material as THREE.Material).dispose();
    (token.hpBar.material as THREE.Material).dispose();
    this.tokens.delete(id);
  }

  /**
   * Sync full roster — remove tokens for entities no longer present, upsert all provided.
   */
  syncRoster(entities: EntityData[]): void {
    const incomingIds = new Set(entities.map(e => e.id));

    // Remove stale tokens
    for (const id of this.tokens.keys()) {
      if (!incomingIds.has(id)) {
        this.remove(id);
      }
    }

    // Upsert all provided
    for (const entity of entities) {
      this.upsert(entity);
    }
  }

  /**
   * Convert engine grid position to Three.js scene position.
   * 1 grid unit = GRID_SCALE (0.5) Three.js units.
   * Y is fixed at TOKEN_Y (0.08) so token sits above the table surface.
   */
  static gridToScene(x: number, y: number): THREE.Vector3 {
    return new THREE.Vector3(x * GRID_SCALE, TOKEN_Y, y * GRID_SCALE);
  }

  /**
   * Return current token count (for testing).
   */
  get tokenCount(): number {
    return this.tokens.size;
  }

  /**
   * Check if a token exists for the given id (for testing).
   */
  hasToken(id: string): boolean {
    return this.tokens.has(id);
  }

  /**
   * Get a token by id (for testing).
   */
  getToken(id: string): EntityToken | undefined {
    return this.tokens.get(id);
  }

  /**
   * Return all live token meshes for raycasting (Slice 7 targeting).
   */
  getTokenMeshes(): THREE.Mesh[] {
    return Array.from(this.tokens.values()).map(t => t.mesh);
  }

  /**
   * Return the entity id for a token mesh (Slice 7 targeting).
   * Returns null if the mesh is not a known token.
   */
  getEntityIdByMesh(mesh: THREE.Mesh): string | null {
    for (const token of this.tokens.values()) {
      if (token.mesh === mesh) return token.id;
    }
    return null;
  }

  /**
   * Return the faction of an entity by id (Slice 7 — target-intent sends faction context).
   */
  getEntityFaction(id: string): string | null {
    return this.tokens.get(id)?.faction ?? null;
  }

  // ---------------------------------------------------------------------------
  // Private
  // ---------------------------------------------------------------------------

  /**
   * Update HP bar color (green→red lerp) and scale width by HP fraction.
   */
  private _updateHpBar(token: EntityToken, hpCurrent: number, hpMax: number): void {
    const fraction = hpMax > 0 ? Math.max(0, Math.min(1, hpCurrent / hpMax)) : 0;

    // Color lerp: full HP = green, 0 HP = red
    const color = new THREE.Color();
    color.lerpColors(HP_COLOR_ZERO, HP_COLOR_FULL, fraction);
    (token.hpBar.material as THREE.MeshBasicMaterial).color.copy(color);

    // Scale bar width by fraction (shrinks left-to-right)
    token.hpBar.scale.x = Math.max(fraction, 0.01); // never fully invisible
  }
}
