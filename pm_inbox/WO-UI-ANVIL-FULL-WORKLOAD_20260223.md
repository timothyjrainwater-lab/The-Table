# Anvil UI Full Workload — 2026-02-23

**Issued by:** Slate (PM)
**To:** Anvil (builder)
**Scope:** All remaining UI gaps against north star vision. Execute sequentially in priority order. Visual gate (Thunder opens browser) required before advancing to next tier.

---

## PREREQUISITE: Spatial Fix Visual Confirm

**Before starting any WO below:** Confirm the `rotation.x = -Math.PI/2` removal fixed book/notebook orientation. Book and notebook should be flat on the player shelf at z=4.8, not standing on edge. Send Thunder a screenshot or flag for visual gate. Do not proceed until confirmed.

---

## TIER 1 — P1 BLOCKING (execute in order)

---

### WO-UI-CRYSTAL-BALL-001 — Crystal Ball NPC Integration

**Gate:** UI-CB (new gate). Target: 8 tests.

**Target Lock:** The crystal ball currently pulses continuously regardless of state. Vision requires it to (1) only glow/pulse when AI is actively speaking via TTS, and (2) display the speaking NPC's portrait inside the orb when an NPC speaks. This is the primary "DM presence" signal on the table.

**Binary Decisions:**

| # | Decision | Choice |
|---|---|---|
| 1 | TTS pulse trigger | New `tts_speaking_start` / `tts_speaking_stop` WS events → toggle pulse on/off |
| 2 | NPC portrait display | New `npc_portrait_display` WS event → texture swap on orb interior mesh |
| 3 | Portrait format | URL or base64 image string on event payload |
| 4 | Default state | Orb dim (ambient only) when no speech. Warm glow pulse only during TTS. |
| 5 | Pulse intensity | Scaled by `intensity` float (0.0–1.0) on event payload — DM narration vs. NPC speech may differ |

**Contract:**

```typescript
interface TtsSpeakingStartMessage {
  msg_type: "tts_speaking_start";
  speaker: "dm" | "npc";
  npc_id?: string;
  intensity?: number;  // 0.0-1.0, default 1.0
}

interface TtsSpeakingStopMessage {
  msg_type: "tts_speaking_stop";
}

interface NpcPortraitDisplayMessage {
  msg_type: "npc_portrait_display";
  npc_id: string;
  image_url: string;     // or base64
  clear?: boolean;       // true = remove portrait, show empty orb
}
```

**Deliverables:**
- [ ] Crystal ball pulse STOPS when no `tts_speaking_start` active
- [ ] `tts_speaking_start` triggers pulse with correct intensity
- [ ] `tts_speaking_stop` dims orb to ambient state
- [ ] `npc_portrait_display` swaps orb interior texture
- [ ] `npc_portrait_display` with `clear: true` removes portrait
- [ ] Demo script: `scripts/demo_crystal_ball.py`
- [ ] Gate UI-CB: 8 tests
- [ ] `npm run build` exits 0

**Tests:**
| ID | Test | Assertion |
|----|------|-----------|
| CB-01 | Initial state | Orb material emissiveIntensity < 0.1 (dim) |
| CB-02 | `tts_speaking_start` (dm) | Pulse activates, intensity matches payload |
| CB-03 | `tts_speaking_stop` | Pulse stops, orb returns to dim |
| CB-04 | `tts_speaking_start` (npc) | Pulse activates |
| CB-05 | `npc_portrait_display` | Orb interior texture changed |
| CB-06 | `npc_portrait_display` clear:true | Texture cleared, orb interior default |
| CB-07 | Pulse does not run without event | 5s elapsed, no pulse if no event fired |
| CB-08 | Rapid start/stop | No stuck pulse state after 10 rapid toggles |

---

### WO-UI-BATTLE-SCROLL-001 — Battle Map Scroll

**Gate:** UI-SCROLL (new gate). Target: 8 tests.

**Target Lock:** The felt vault is always visible. Vision requires a magical scroll that unrolls when combat starts and rolls back up when combat ends. This is the primary dramatic state change that signals to the player that the game has shifted into tactical mode.

**Binary Decisions:**

| # | Decision | Choice |
|---|---|---|
| 1 | Trigger | `combat_start` / `combat_end` WS events |
| 2 | Scroll mesh | Cylinder that scales Z-axis from 0→full to simulate unroll |
| 3 | Felt vault relationship | Scroll appears ON TOP of felt vault. Vault stays. |
| 4 | Unroll duration | 1.2s linear tween (not too fast, dramatic) |
| 5 | Roll-up duration | 0.8s (slightly faster than unroll) |
| 6 | Grid visibility | Entity tokens + map overlay only visible when scroll is unrolled |
| 7 | Idle state | Scroll visible but rolled at session start; stays rolled until `combat_start` |

**Contract:**

```typescript
interface CombatStartMessage {
  msg_type: "combat_start";
  encounter_id: string;
  map_width: number;
  map_height: number;
}

interface CombatEndMessage {
  msg_type: "combat_end";
  encounter_id: string;
  outcome: "victory" | "defeat" | "retreat" | "dissolved";
}
```

**Deliverables:**
- [ ] Scroll mesh (rolled cylinder) visible at session start
- [ ] `combat_start` triggers unroll animation (1.2s)
- [ ] `combat_end` triggers roll-up animation (0.8s)
- [ ] Entity tokens only appear after scroll is unrolled
- [ ] Map overlay only visible on unrolled scroll
- [ ] Seeded PRNG for scroll texture grain (Gate G)
- [ ] Gate UI-SCROLL: 8 tests
- [ ] `npm run build` exits 0

**Tests:**
| ID | Test | Assertion |
|----|------|-----------|
| SC-01 | Initial state | Scroll mesh visible, scaleZ ≈ 0 (rolled) |
| SC-02 | `combat_start` | Scroll unrolls (scaleZ goes 0→1 over 1.2s) |
| SC-03 | `combat_end` | Scroll rolls up (scaleZ goes 1→0 over 0.8s) |
| SC-04 | Tokens hidden before unroll | EntityRenderer tokens not in scene before combat_start |
| SC-05 | Tokens visible after unroll | EntityRenderer tokens appear after combat_start |
| SC-06 | Map overlay hidden before unroll | MapOverlayManager inactive before combat_start |
| SC-07 | No Math.random | Scroll texture uses seeded PRNG |
| SC-08 | Double combat_start safe | Second combat_start while unrolled doesn't break state |

---

### WO-UI-CHARACTER-SHEET-001 — Interactive Character Sheet

**Gate:** UI-CS (new gate). Target: 12 tests.

**Target Lock:** The character sheet is currently a static read-only display with hardcoded placeholder values. Vision requires: (1) sheet fields bound to live entity data via `character_sheet_update` WS events, (2) clicking a spell or ability line emits `DECLARE_ACTION_INTENT` (accessibility path), (3) conditions/HP visible and updating.

**Binary Decisions:**

| # | Decision | Choice |
|---|---|---|
| 1 | Update event | New `character_sheet_update` WS event carries full entity snapshot |
| 2 | Clickable elements | Spell rows, ability rows, attack rows only. Stat blocks read-only. |
| 3 | Click action | Emit `REQUEST_DECLARE_ACTION` with `{action_id, entity_id}` |
| 4 | HP display | Numeric HP (current/max) + visual bar. Updates on `entity_delta`. |
| 5 | Conditions | Condition tags appear below HP. Populated from `conditions` array on entity. |
| 6 | Spell slot pips | Small circles per slot level, filled = available, empty = expended |
| 7 | "?" stamp placement | Right-click any row → places QuestionStamp → click opens rulebook to rule_ref |

**Contract:**

```typescript
interface CharacterSheetUpdateMessage {
  msg_type: "character_sheet_update";
  entity_id: string;
  hp_current: number;
  hp_max: number;
  conditions: string[];
  spell_slots: Record<number, number>;       // level → remaining
  spell_slots_max: Record<number, number>;   // level → max
  abilities: Array<{ id: string; name: string; ready: boolean; }>;
  attacks: Array<{ id: string; name: string; bonus: string; damage: string; }>;
}

// Emitted by client on click:
interface RequestDeclareActionMessage {
  msg_type: "REQUEST_DECLARE_ACTION";
  action_id: string;
  entity_id: string;
}
```

**Deliverables:**
- [ ] `character_sheet_update` populates all sheet fields
- [ ] HP bar updates on `entity_delta` hp_current change
- [ ] Conditions list updates on `entity_delta` conditions change
- [ ] Spell slot pips reflect remaining slots
- [ ] Clicking spell/ability row emits `REQUEST_DECLARE_ACTION`
- [ ] Right-click row → QuestionStamp placed → click stamp → rulebook opens to rule_ref
- [ ] Gate UI-CS: 12 tests
- [ ] `npm run build` exits 0

**Tests:**
| ID | Test | Assertion |
|----|------|-----------|
| CS-01 | `character_sheet_update` | HP fields update to payload values |
| CS-02 | `character_sheet_update` | Spell slot pips reflect remaining |
| CS-03 | `character_sheet_update` | Abilities list renders from payload |
| CS-04 | `entity_delta` hp | HP bar and numeric update |
| CS-05 | `entity_delta` conditions | Condition tags appear/disappear |
| CS-06 | Click spell row | Emits `REQUEST_DECLARE_ACTION` with correct action_id |
| CS-07 | Click ability row | Emits `REQUEST_DECLARE_ACTION` with correct action_id |
| CS-08 | Click stat block | No event emitted (stat blocks read-only) |
| CS-09 | Right-click row | QuestionStamp placed on sheet |
| CS-10 | Click QuestionStamp | Rulebook opens (BookObject.openToRef called) |
| CS-11 | Expended spell slot | Pip shows empty (not filled) |
| CS-12 | Full heal | All HP pips filled, conditions cleared |

---

## TIER 2 — P2 HIGH IMPACT

---

### WO-UI-FOG-OF-WAR-001 — Fog of War

**Gate:** UI-FOG (new gate). Target: 10 tests.
**Note:** Vision calls this "highest priority visual feature." Scoped conservatively here — grid-based reveal only (no raycasting). Full light-radius simulation is a future WO.

**Target Lock:** Currently the map shows all entities and terrain. Vision requires explored areas to be revealed, unexplored areas hidden. Player characters' vision radius determines what's currently visible.

**Binary Decisions:**

| # | Decision | Choice |
|---|---|---|
| 1 | Implementation approach | Grid-cell opacity overlay (PlaneGeometry per cell, black, opacity 0=revealed, 1=hidden) |
| 2 | Vision types | Normal (30ft), darkvision (60ft), low-light (60ft in dim light) — read from entity EF fields |
| 3 | Reveal trigger | `fog_update` WS event carries full `revealed_cells` array |
| 4 | Persistence | Revealed cells accumulate (once seen, stays visible). Server owns state. |
| 5 | Currently visible | `visible_cells` on event = currently in vision range (brighter). `revealed_cells` = ever seen (dimmer). |
| 6 | Cell scale | 1 grid unit = 0.5 scene units (same as entity grid scale) |

**Contract:**

```typescript
interface FogUpdateMessage {
  msg_type: "fog_update";
  revealed_cells: Array<{x: number; y: number}>;   // ever seen (dim)
  visible_cells: Array<{x: number; y: number}>;    // currently in vision (bright)
  map_bounds: {x: number; y: number; width: number; height: number};
}
```

**Deliverables:**
- [ ] `FogOfWarManager` class in new `client/src/fog-of-war.ts`
- [ ] Black overlay grid, cell opacity controlled per-cell
- [ ] `fog_update` handler: revealed_cells → dim (opacity 0.3), visible_cells → clear (opacity 0), unrevealed → dark (opacity 0.9)
- [ ] Cells accumulate (revealed stays dim even if not in visible)
- [ ] Gate UI-FOG: 10 tests
- [ ] `npm run build` exits 0

**Tests:**
| ID | Test | Assertion |
|----|------|-----------|
| FOG-01 | Initial state | All cells dark (opacity 0.9) |
| FOG-02 | `fog_update` revealed | Revealed cells → dim (opacity ~0.3) |
| FOG-03 | `fog_update` visible | Visible cells → clear (opacity 0) |
| FOG-04 | Accumulation | Second update without prior cell → cell stays dim |
| FOG-05 | Cell count | Manager creates correct cell count for map_bounds |
| FOG-06 | Cell position | Cell at (4,3) maps to correct scene coords |
| FOG-07 | Visible subset of revealed | Visible cells are subset of revealed (or equal) |
| FOG-08 | Empty update | No crash on empty revealed/visible arrays |
| FOG-09 | Large map | 24×16 grid (384 cells) without performance issue |
| FOG-10 | Dispose | FogOfWarManager.dispose() removes all meshes from scene |

---

### WO-UI-DICE-BAG-001 — Dice Bag

**Gate:** UI-DICE (new gate). Target: 6 tests.

**Target Lock:** Dice bag was removed during spatial rework. Vision requires a 3D leather bag on the player shelf, click to open, revealing full die set inside (d4, d6, d8, d10, d12, d20).

**Binary Decisions:**

| # | Decision | Choice |
|---|---|---|
| 1 | Mesh | Rounded box (leather-look MeshStandardMaterial, dark brown) on player shelf |
| 2 | Open trigger | Click bag → open animation (lid lifts or bag expands), reveals dice set |
| 3 | Die set | 6 dice (d4, d6, d8, d10, d12, d20). Only d20 is interactive. Others are decorative. |
| 4 | "Magical bag" rule | Picking up d20 for roll doesn't remove it from the bag |
| 5 | Position | Player shelf (z=4.8), left of notebook |
| 6 | Seeded PRNG | Bag texture uses seeded PRNG (Gate G) |

**Deliverables:**
- [ ] `DiceBagObject` in new `client/src/dice-bag.ts`
- [ ] Leather bag mesh on player shelf
- [ ] Click → open animation → die set visible
- [ ] d4, d6, d8, d10, d12 decorative inside bag when open
- [ ] d20 remains functional (existing dice ritual intact)
- [ ] Seeded PRNG for texture
- [ ] Gate UI-DICE: 6 tests
- [ ] `npm run build` exits 0

---

### WO-UI-TOKEN-SLIDE-001 — Entity Token Slide Animation

**Gate:** Regression guard only (Gate UI-06 must still PASS). Target: 3 new tests.

**Target Lock:** `entity_delta` with position change currently teleports token instantly. Vision requires a smooth 0.3-0.5s slide from old position to new.

**Binary Decisions:**

| # | Decision | Choice |
|---|---|---|
| 1 | Animation duration | 0.35s linear tween |
| 2 | Tween library | Manual lerp in requestAnimationFrame loop (no new dependency) |
| 3 | Queue behavior | If second move arrives during tween, snap to current delta target and start new tween |
| 4 | Replay mode | In `replay_mode: true`, snap instantly (deterministic) |

**Deliverables:**
- [ ] `EntityRenderer.upsert()` with position change → lerp over 0.35s
- [ ] Replay mode snaps instantly
- [ ] Gate UI-06 still 10/10
- [ ] 3 new tests: slide duration, replay snap, mid-tween update

---

### WO-UI-SESSION-ZERO-001 — Session Zero Notebook Flow

**Gate:** UI-SZ (new gate). Target: 6 tests.

**Target Lock:** When a new session starts, the DM introduces itself and asks the player's name. The player's name should appear on the notebook cover. The player can then request cover art customization.

**Binary Decisions:**

| # | Decision | Choice |
|---|---|---|
| 1 | Trigger | `session_zero_start` WS event |
| 2 | Name display | `notebook_cover_name` event → renders player name as text on notebook cover mesh |
| 3 | Cover art | `notebook_cover_image` event → texture swap on notebook cover |
| 4 | Persistence | Cover name + image URL stored in localStorage keyed by session_id |
| 5 | Load on return | On `session_resume`, reload cover from localStorage |

**Deliverables:**
- [ ] `session_zero_start` handler exists
- [ ] `notebook_cover_name` updates cover text
- [ ] `notebook_cover_image` updates cover texture
- [ ] Cover persists in localStorage, reloads on session_resume
- [ ] Gate UI-SZ: 6 tests

---

### WO-UI-NOTEBOOK-PERSIST-001 — Notebook Stroke Persistence

**Gate:** Regression guard (NotebookObject tests must pass). Target: 4 new tests.

**Target Lock:** Drawing strokes on notebook pages are lost on refresh. Vision requires persistence across sessions.

**Binary Decisions:**

| # | Decision | Choice |
|---|---|---|
| 1 | Storage | localStorage, keyed by `session_id + section_id` |
| 2 | Format | JSON array of stroke objects `{points: [{x,y}], color, width}` |
| 3 | Save trigger | Debounced 2s after last stroke (not on every point) |
| 4 | Load trigger | On NotebookObject init, load from localStorage for current session |
| 5 | Max size guard | If localStorage entry > 500KB, drop oldest strokes |

**Deliverables:**
- [ ] Strokes saved to localStorage on draw (debounced)
- [ ] Strokes reloaded on notebook init
- [ ] Max size guard implemented
- [ ] 4 new tests: save, load, debounce, size guard

---

## TIER 3 — P3 POLISH

---

### WO-UI-SETTINGS-GEM-001 — Settings Gemstone

**Gate:** Regression guard. Target: 3 tests.

Small red gemstone on table surface. Two-phase activation: single tap = open settings overlay, hold (1.5s) = confirm+reset. Settings overlay: volume, TTS voice, UI scale. No maximize button — expansion via camera pull.

---

### WO-UI-MAP-LASSO-001 — Map Area Indication Lasso

**Gate:** Regression guard. Target: 4 tests.

Click-hold + drag on map → ephemeral lasso overlay indicating area. Emits `MAP_AREA_INTENT(kind=SEARCH|AIM|DISCUSS, polygon)`. Overlay lingers 8s then fades. No permanent mark.

---

### WO-UI-CUP-HOLDER-001 — Cup Holder / Soft Delete

**Gate:** Regression guard. Target: 3 tests.

Recessed cup holder visible as 3D object (already in scene-builder geometry — confirm visibility). Drag any object to cup holder = soft delete (object dims, stored in `SoftDeleteStack`). Click cup holder = retrieve last deleted object. Max 5 items.

---

### WO-UI-BESTIARY-BIND-001 — Bestiary Image Binding

**Gate:** Regression guard. Target: 4 tests.

`bestiary_entry_reveal` WS event: `{creature_id, knowledge_state: "heard"|"seen"|"fought"|"studied", image_url}`. Swap bestiary left-page image texture. Text panel on right updates with creature name + known traits. Progressive reveal: heard=silhouette, seen=sketch, fought=partial, studied=full art.

---

### WO-UI-RULEBOOK-SEARCH-001 — Rulebook Navigation

**Gate:** Regression guard. Target: 3 tests.

New `rulebook_open` WS event: `{rule_ref: string, page?: number}`. Calls `BookObject.openToRef(rule_ref)`. Also: `rulebook_search` event with query string — opens to closest matching ref. Enables "show me the rule for grappling" from voice command.

---

## INTEGRATION SEAMS (ALL WOs)

- **`client/src/` only** unless noted. No Python changes, no engine changes.
- **Do not modify** `ws-bridge.ts` — register new handlers in `main.ts` only.
- **Do not modify** `scene-builder.ts` — table geometry settled; new objects layer on top.
- **Gate G** (`test_ui_gate_g.py`) must stay 22/22 after each WO.
- **No `Math.random()`** anywhere in client/src/. Use `makePrng()` from scene-builder.ts.
- **`npm run build` exits 0** after each WO.

---

## EXECUTION ORDER

```
PREREQUISITE: Visual confirm spatial fix (book/notebook flat on shelf)
    ↓
TIER 1 (sequential — each needs visual confirm before next):
  WO-UI-CRYSTAL-BALL-001   → visual gate
  WO-UI-BATTLE-SCROLL-001  → visual gate
  WO-UI-CHARACTER-SHEET-001 → visual gate
    ↓
TIER 2 (can pipeline — no visual dependencies between them):
  WO-UI-FOG-OF-WAR-001
  WO-UI-DICE-BAG-001
  WO-UI-TOKEN-SLIDE-001
  WO-UI-SESSION-ZERO-001
  WO-UI-NOTEBOOK-PERSIST-001
    ↓
TIER 3 (polish — execute when Tier 2 clear):
  WO-UI-SETTINGS-GEM-001
  WO-UI-MAP-LASSO-001
  WO-UI-CUP-HOLDER-001
  WO-UI-BESTIARY-BIND-001
  WO-UI-RULEBOOK-SEARCH-001
```

---

## DEBRIEF FORMAT (each WO)

For each completed WO, drop `WO-UI-[NAME]_DEBRIEF.md` in `pm_inbox/` with:
1. Gate test count (X/X PASS)
2. Visual gate result (screenshot description or "pending Thunder confirm")
3. Any findings or deviations from spec
4. `npm run build` exit code

---

*Anvil out when ready.*
