# WO-UI-06 — WebSocket → Three.js Live Scene Bridge

**Issued:** 2026-02-23
**Authority:** UI parallel track. PM dispatch.
**Gate:** UI-06 (new gate). Target: 8–12 tests (integration + unit). Visual review by Thunder.
**Blocked by:** WO-UI-05 ACCEPTED (scene-builder.ts delivered — ✓).
**Track:** UI parallel track — no conflict with BURST-003/BURST-002/CHARGEN.

---

## 1. Target Lock

WO-UI-05 gave us a physically believable table. It's inert — the Three.js scene has no live data. WO-UI-06 wires the WebSocket bridge to the scene so that engine state drives visible updates: entity tokens appear, move, and die; HP changes register; combat overlays respond to `PENDING_ROLL` / `roll_result`; AoE previews (once BURST-003 lands) have a surface to render on.

The golden signal: **engine fires an event → table responds without a page refresh.**

Scope: message handler wiring only. No new backend messages. No new engine code. Client-side only.

---

## 2. Binary Decisions

| # | Decision | Choice | Rationale |
|---|---|---|---|
| 1 | Token representation | Flat cylinder (CylinderGeometry, r=0.18, h=0.06) per entity | Simple, readable, zone-correct scale |
| 2 | Token color coding | Player = warm gold (0xd4a820), Enemy = deep red (0x8b1a1a), NPC = slate blue (0x4a6a8a) | Instant visual classification |
| 3 | Token position mapping | Entity `EF.POSITION` {x, y} → table grid coords (scale factor from grid units to Three.js units) | Existing show_map() uses same x/y schema |
| 4 | HP bar | Thin strip above token (PlaneGeometry, color lerp green→red) | At-a-glance health without numbers |
| 5 | Dead entity | Token removed from scene on `hp_current ≤ 0` | Matches show_map() `defeated` exclusion logic |
| 6 | Message type for entity state | `state_update` (already wired, line 135 main.ts) + new `entity_state` type | `state_update` carries delta; `entity_state` carries full roster |
| 7 | Deterministic replay | Accept `replay_mode: true` flag on messages — identical message sequence = identical scene state | Required for test gate |
| 8 | Token registry | Extend existing `TableObjectRegistry` in `table-object.ts` | Reuse existing single-selection + lifecycle model |
| 9 | Zone overlay suppression | Zone wireframes already off (WO-UI-05) — do not re-enable | Consistent with WO-UI-05 decision |
| 10 | Grid-to-scene coordinate scale | 1 grid unit = 0.5 Three.js units | Table is 12×8 units; 24×16 grid squares fits comfortably |

---

## 3. Contract Spec

### 3.1 New Message Types

Two new message types the client will handle (engine must emit these — see Integration Seams):

**`entity_state`** — Full roster sync (on connect or session resume):
```typescript
interface EntityStateMessage {
  msg_type: "entity_state";
  entities: Array<{
    id: string;
    name: string;
    faction: "player" | "enemy" | "npc";
    position: { x: number; y: number };
    hp_current: number;
    hp_max: number;
    conditions: string[];
  }>;
}
```

**`entity_delta`** — Single entity update (on any state change):
```typescript
interface EntityDeltaMessage {
  msg_type: "entity_delta";
  entity_id: string;
  changes: Partial<{
    position: { x: number; y: number };
    hp_current: number;
    conditions: string[];
    defeated: boolean;
  }>;
}
```

### 3.2 New Module: `entity-renderer.ts`

New file `client/src/entity-renderer.ts`. Owns all entity visual logic.

```typescript
export interface EntityToken {
  id: string;
  mesh: THREE.Mesh;        // Token cylinder
  hpBar: THREE.Mesh;       // HP strip
  faction: string;
}

export class EntityRenderer {
  private tokens: Map<string, EntityToken> = new Map();

  constructor(private scene: THREE.Scene) {}

  /** Spawn or update a token for the given entity data. */
  upsert(entity: EntityData): void { ... }

  /** Remove token (entity defeated or left combat). */
  remove(id: string): void { ... }

  /** Sync full roster — remove stale, upsert all provided. */
  syncRoster(entities: EntityData[]): void { ... }

  /** Convert engine grid position to Three.js scene position. */
  static gridToScene(x: number, y: number): THREE.Vector3 {
    return new THREE.Vector3(x * 0.5, 0.08, y * 0.5);
  }

  /** Update HP bar color and scale (green→red lerp). */
  private updateHpBar(token: EntityToken, hpCurrent: number, hpMax: number): void { ... }
}
```

### 3.3 main.ts Additions

Add to `main.ts` (after existing bridge.on() calls):

```typescript
const entityRenderer = new EntityRenderer(scene);

bridge.on('entity_state', (data: EntityStateMessage) => {
  entityRenderer.syncRoster(data.entities);
});

bridge.on('entity_delta', (data: EntityDeltaMessage) => {
  if (data.changes.defeated) {
    entityRenderer.remove(data.entity_id);
  } else {
    entityRenderer.upsert({ id: data.entity_id, ...data.changes });
  }
});
```

### 3.4 Coordinate Scale

```typescript
// Grid unit → Three.js scene unit
const GRID_SCALE = 0.5;

// Entity at grid (4, 3) → scene position (2.0, 0.08, 1.5)
// Y = 0.08 so token sits just above table surface (surface top ≈ 0.0)
```

### 3.5 Token Geometry

```typescript
const TOKEN_GEO = new THREE.CylinderGeometry(0.18, 0.18, 0.06, 16);

const FACTION_COLORS = {
  player: 0xd4a820,   // warm gold
  enemy:  0x8b1a1a,   // deep red
  npc:    0x4a6a8a,   // slate blue
};

// HP bar: thin plane above token
const HP_BAR_GEO = new THREE.PlaneGeometry(0.32, 0.04);
// Rotate flat, position slightly above token top
// Color: lerp from 0x22aa22 (full HP) to 0xaa2222 (0 HP)
```

### 3.6 Deterministic Replay Mode

```typescript
// If message contains replay_mode: true, suppress any non-deterministic behavior.
// Entity renderer must produce identical scene state for identical message sequences.
// No random positioning, no animation on initial spawn in replay mode.
```

---

## 4. Implementation Plan

1. **Read** `client/src/main.ts`, `client/src/ws-bridge.ts`, `client/src/table-object.ts`, `client/src/scene-builder.ts` — understand existing wiring before touching anything.
2. **Create** `client/src/entity-renderer.ts` — `EntityRenderer` class with `upsert()`, `remove()`, `syncRoster()`, `gridToScene()`, `updateHpBar()`.
3. **Update** `client/src/main.ts` — add `EntityRenderer` import, instantiate it, register `entity_state` and `entity_delta` handlers on bridge.
4. **Token materials** — `MeshStandardMaterial` per faction color, roughness 0.6, metalness 0.2. HP bar uses `MeshBasicMaterial` (unlit, always readable).
5. **HP lerp** — `THREE.Color.lerpColors(green, red, 1 - hpFraction)` for bar color. Scale bar width by hp fraction.
6. **Build verify** — `cd client && npm run build` must exit 0. No TypeScript errors.
7. **Test suite** — write `tests/test_ui_gate_ui06.py` (or TypeScript tests if builder prefers) verifying coordinate transform, upsert/remove lifecycle, and roster sync.
8. **Visual verify** — open browser, run demo script (see §8), confirm tokens appear and update on engine events.

---

## 5. Test Spec (Gate UI-06 — target 10 tests)

| ID | Test | Assertion |
|----|------|-----------|
| UI06-01 | `gridToScene(0, 0)` | Returns `(0, 0.08, 0)` |
| UI06-02 | `gridToScene(4, 3)` | Returns `(2.0, 0.08, 1.5)` |
| UI06-03 | `upsert()` adds token to scene | Scene children count increases by 2 (token + HP bar) |
| UI06-04 | `upsert()` same id twice | No duplicate tokens — updates existing |
| UI06-05 | `remove()` clears token | Scene children reduced; token map empty for id |
| UI06-06 | `syncRoster([A, B, C])` then `syncRoster([A, C])` | B removed; A and C updated |
| UI06-07 | HP bar at full HP | Bar color near green (R < 50, G > 150) |
| UI06-08 | HP bar at 0 HP | Bar color near red (R > 150, G < 50) |
| UI06-09 | `defeated: true` in delta | Token removed from scene |
| UI06-10 | `entity_state` message → `syncRoster()` called | All provided entities appear in scene |

**Note:** Tests may be Python (testing coordinate math via import) or TypeScript (vitest/jest). Builder's choice — gate criterion is 10+ PASS.

---

## 6. Deliverables Checklist

- [ ] `client/src/entity-renderer.ts` — `EntityRenderer` class, full implementation
- [ ] `client/src/main.ts` — `entity_state` + `entity_delta` handlers registered
- [ ] Token geometry: faction-colored cylinders, HP bars
- [ ] `gridToScene()` coordinate transform correct (1 grid = 0.5 scene units)
- [ ] HP bar lerps green→red with hp fraction
- [ ] Defeated entity removed from scene
- [ ] `client && npm run build` exits 0
- [ ] Gate UI-06: 10+ tests PASS
- [ ] Visual review: Thunder opens browser, tokens visible and responsive

---

## 7. Integration Seams

- **client/src only** — No Python changes, no engine changes, no test infrastructure changes
- **Do not modify** `ws-bridge.ts` — existing pub/sub is correct; just register new handlers in `main.ts`
- **Do not modify** `table-object.ts` — `TableObjectRegistry` is for interactive objects (dice, etc.); entity tokens are managed by `EntityRenderer` separately
- **Do not modify** `scene-builder.ts` — table geometry is settled; entity tokens layer on top
- **Do not modify** `zones.ts` — zone positions unchanged
- **Engine note:** The engine does NOT currently emit `entity_state` or `entity_delta` messages. This WO wires the **client-side receiver only**. A future WO will wire the engine emitter. Builder should use a demo script (hardcoded test messages via WebSocket) to validate visual output.

---

## 8. Demo Script

Builder provides a small demo script that sends synthetic WebSocket messages to the client for visual validation:

```python
# scripts/demo_entity_tokens.py
import asyncio, websockets, json

MESSAGES = [
    {"msg_type": "entity_state", "entities": [
        {"id": "p1", "name": "Kira", "faction": "player",
         "position": {"x": 2, "y": 3}, "hp_current": 11, "hp_max": 11, "conditions": []},
        {"id": "e1", "name": "Goblin", "faction": "enemy",
         "position": {"x": 8, "y": 5}, "hp_current": 7, "hp_max": 7, "conditions": []},
    ]},
    # Simulate damage
    {"msg_type": "entity_delta", "entity_id": "e1",
     "changes": {"hp_current": 3}},
    # Simulate defeat
    {"msg_type": "entity_delta", "entity_id": "e1",
     "changes": {"hp_current": 0, "defeated": True}},
]

async def main():
    async with websockets.connect("ws://localhost:8765") as ws:
        for msg in MESSAGES:
            await ws.send(json.dumps(msg))
            await asyncio.sleep(1.5)

asyncio.run(main())
```

---

## 9. Debrief Focus

1. **Coordinate scale** — does 1 grid unit = 0.5 scene units produce readable token spacing on the table surface? What did you use if you adjusted it?
2. **Token visibility** — do tokens read clearly against the dark walnut surface under warm candlelight? Any material adjustments needed?
3. **HP bar** — at what HP fraction does the bar become "visually alarming"? Was the lerp threshold tuned?

---

## Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```
