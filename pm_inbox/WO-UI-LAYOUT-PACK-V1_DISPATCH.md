# WO-UI-LAYOUT-PACK-V1 — Layout Data Pack (Foundation)

**Issued:** 2026-02-23
**Authority:** PM — AI2AI Exec Packet (TABLE UI NORTH STAR)
**Sequence:** 1 of 6. All subsequent UI WOs depend on this landing first.
**Gate:** UI-LAYOUT-PACK (new gate, defined below)

---

## 0. Hand-off note (read this first)

**"Stop tuning by eye in code. The layout is data-driven. Implement LAYOUT_PACK_V1 exactly, generate golden frames, lock gates, then iterate only by changing JSON + regenerating frames. If you can't explain a change in terms of posture intent + zone rules, don't make it."**

---

## 1. Target Lock

Create `docs/design/LAYOUT_PACK_V1/` — a single authoritative data pack that all subsequent camera, object, lighting, and gate WOs read from. Wire the runtime to load the three JSONs instead of hardcoded values. Add a debug overlay that draws zone bounds and anchors in-scene.

**Done means:** pack exists, runtime loads it, debug overlay confirms zone alignment when `?debug=1&zones=1` is appended to the dev URL.

---

## 2. Binary Decisions — Locked

| Decision | Answer |
|----------|--------|
| Coordinate system | X: left(−)→right(+) · Y: up(+) · Z: player/near(+)→DM/far(−) |
| Table footprint | Far rail z=−4.1 · Near shelf z=+4.1 · Player centerZ=+4.75 · Camera body z≥+6.0 |
| Who moves meshes to match spec? | This WO. If current meshes differ from spec coords, align meshes to spec. Do not rewrite spec around mis-modeled geometry. |
| Hardcoded coordinates allowed after this WO? | No. Runtime must read from JSONs. |

---

## 3. Deliverables

### 3.1 Folder structure (create all)

```
docs/design/LAYOUT_PACK_V1/
  README.md
  zones.json
  camera_poses.json
  table_objects.json
  golden/                  ← populated by WO-UI-CAMERAS-V1
  tests/                   ← populated by WO-UI-GATES-V1
```

### 3.2 `zones.json` — canonical zone AABBs

Replace `aidm/ui/zones.json` and create `docs/design/LAYOUT_PACK_V1/zones.json` with identical content. Runtime loads from `aidm/ui/zones.json` (existing path); the pack copy is the authoritative source that gets committed.

Schema (all values in scene units):

```json
{
  "schema": "layout-pack-v1",
  "zones": [
    {
      "name": "DM_ZONE",
      "centerX": 0.0,
      "centerZ": -3.5,
      "halfWidth": 5.0,
      "halfHeight": 0.75,
      "description": "Far band — orb / DM presence"
    },
    {
      "name": "VAULT_ZONE",
      "centerX": 0.0,
      "centerZ": -0.5,
      "halfWidth": 3.1,
      "halfHeight": 2.1,
      "description": "Recessed felt vault — map well. Objects must be below rail level inside this zone."
    },
    {
      "name": "WORK_ZONE",
      "centerX": 0.0,
      "centerZ": 2.0,
      "halfWidth": 3.0,
      "halfHeight": 1.5,
      "description": "Open working surface in front of player — loose handouts, loose dice"
    },
    {
      "name": "TRASH_RING_ZONE",
      "centerX": 2.7,
      "centerZ": 3.6,
      "halfWidth": 0.4,
      "halfHeight": 0.4,
      "description": "Discard ring — near back of work zone"
    },
    {
      "name": "SHELF_ZONE",
      "centerX": 0.0,
      "centerZ": 4.75,
      "halfWidth": 5.0,
      "halfHeight": 0.80,
      "description": "Player shelf strip — sheet, notebook, rulebook, dice bag"
    },
    {
      "name": "DICE_STATION_ZONE",
      "centerX": 4.5,
      "centerZ": 1.125,
      "halfWidth": 1.2,
      "halfHeight": 1.325,
      "description": "Right-side dice area — tray + tower. Spans z=−0.2 to z=+2.45."
    }
  ],
  "anchors": {
    "orb_anchor":       { "x": 0.0,  "y": 1.45, "z": -3.2  },
    "vault_center":     { "x": 0.0,  "y": 0.0,  "z": -0.5  },
    "shelf_sheet":      { "x": -2.6, "y": 0.0,  "z": 4.75  },
    "shelf_notebook":   { "x": -0.2, "y": 0.0,  "z": 4.75  },
    "shelf_rulebook":   { "x": 2.0,  "y": 0.0,  "z": 4.75  },
    "shelf_dice_bag":   { "x": -4.0, "y": 0.0,  "z": 4.75  },
    "dice_tray_center": { "x": 4.5,  "y": 0.065,"z": 1.75  },
    "dice_tower_base":  { "x": 4.5,  "y": 0.065,"z": 0.5   }
  }
}
```

**Note on shelf layout:** Sheet at x=−2.6, notebook at x=−0.2, rulebook at x=+2.0. This gives ~2.4 units lateral separation between each. Dice bag at x=−4.0 is at the far left of shelf, near the left rail, well clear of the other three. The WO-UI-OBJECT-LAYOUT-V1 WO will enforce notebook dominance; the anchor positions here are the centroid targets.

### 3.3 `camera_poses.json`

```json
{
  "schema": "layout-pack-v1",
  "transition_ms": 350,
  "postures": {
    "STANDARD": {
      "position":  { "x": 0.0,  "y": 1.30, "z": 7.5  },
      "lookAt":    { "x": 0.0,  "y": 0.05, "z": 1.5  },
      "intent": "Seated poker-table view. Orb visible upper frame. Vault depth cue. Shelf barely visible at bottom. No green felt tray in frame.",
      "acceptance": ["orb visible", "far rail visible", "vault recess visible", "reads like sitting at real table"]
    },
    "DOWN": {
      "position":  { "x": 0.0,  "y": 5.5,  "z": 7.5  },
      "lookAt":    { "x": 0.0,  "y": 0.0,  "z": 4.5  },
      "intent": "Belly/reading posture. Shelf artifacts fill frame. Slightly off-perpendicular — embodied, not orthographic.",
      "acceptance": ["sheet primary numbers readable", "notebook page readable", "rulebook headings readable"]
    },
    "LEAN_FORWARD": {
      "position":  { "x": 0.0,  "y": 2.0,  "z": 2.0  },
      "lookAt":    { "x": 0.0,  "y": 0.2,  "z": -2.5 },
      "intent": "Study the vault. Look down into recessed felt. Never true top-down. Orb remains visible and framed.",
      "acceptance": ["vault recess unmistakable", "orb still in frame", "not clipping orb"]
    },
    "DICE_TRAY": {
      "position":  { "x": 3.5,  "y": 1.1,  "z": 5.5  },
      "lookAt":    { "x": 4.5,  "y": 0.08, "z": 1.75 },
      "intent": "Turn right to dice station. Tray + tower dominate frame. Feels like turning, not teleporting.",
      "acceptance": ["tray visible", "tower visible", "tray+tower occupy majority of frame"]
    },
    "BOOK_READ": {
      "position":  { "x": 2.2,  "y": 1.0,  "z": 5.4  },
      "lookAt":    { "x": 2.2,  "y": 0.07, "z": 4.5  },
      "intent": "Close-up book reading. Eye drops to page level.",
      "acceptance": ["rulebook page text legible at 1080p"]
    }
  }
}
```

**Derivation notes (so the agent understands the physical grounding):**

- STANDARD: Real seated eye height ~1.3m above floor. Table surface at y=0. Camera body behind the shelf (z=7.5). lookAt at y=0.05 z=1.5 aims at mid-table, putting orb in upper third of frame and shelf barely visible at bottom. This is "looking across the table."
- DOWN: Player leans back and looks straight down at their stuff. y=5.5 is arm's-length overhead. z=7.5 keeps the camera over the shelf zone. lookAt z=4.5 is shelf center. Slight Z offset from perpendicular = embodied.
- LEAN_FORWARD: Player physically leans across the table. y=2.0 (crouching forward), z=2.0 (mid-table). lookAt at z=−2.5 points into the DM side, vault visible, orb upper frame.
- DICE_TRAY: Turn right. x=3.5 shifts camera rightward. y=1.1 is tabletop sightline. z=5.5 keeps it over shelf. lookAt at dice tray center.

### 3.4 `table_objects.json`

```json
{
  "schema": "layout-pack-v1",
  "objects": [
    {
      "name": "CHAR_SHEET",
      "mesh_name": "stub_character_sheet",
      "zone": "SHELF_ZONE",
      "anchor": "shelf_sheet",
      "position": { "x": -2.6, "y": 0.005, "z": 4.75 },
      "rotation_y": 0.06,
      "scale": { "x": 1.4, "y": 1.0, "z": 1.9 },
      "physics_class": "KINEMATIC_DRAG",
      "notes": "Paper flat on shelf. Parchment texture."
    },
    {
      "name": "NOTEBOOK",
      "mesh_name": "stub_notebook",
      "zone": "SHELF_ZONE",
      "anchor": "shelf_notebook",
      "position": { "x": -0.2, "y": 0.01, "z": 4.75 },
      "rotation_y": -0.08,
      "scale": { "x": 1.4, "y": 0.08, "z": 1.9 },
      "physics_class": "KINEMATIC_DRAG",
      "notes": "Dominant player object. Largest footprint or most central. Must not be tucked."
    },
    {
      "name": "RULEBOOK",
      "mesh_name": "stub_tome",
      "zone": "SHELF_ZONE",
      "anchor": "shelf_rulebook",
      "position": { "x": 2.0, "y": 0.04, "z": 4.75 },
      "rotation_y": 0.12,
      "scale": { "x": 1.2, "y": 0.14, "z": 1.6 },
      "physics_class": "KINEMATIC_DRAG",
      "notes": "Thicker than notebook. Burgundy cover. Formal."
    },
    {
      "name": "DICE_BAG",
      "mesh_name": "stub_dice_bag",
      "zone": "SHELF_ZONE",
      "anchor": "shelf_dice_bag",
      "position": { "x": -4.0, "y": 0.01, "z": 4.75 },
      "rotation_y": 0.0,
      "scale": { "x": 0.5, "y": 0.5, "z": 0.5 },
      "physics_class": "KINEMATIC_DRAG",
      "notes": "Near left rail. Reachable from dice station without crossing shelf center."
    },
    {
      "name": "CRYSTAL_BALL",
      "mesh_name": "stub_crystal_ball",
      "zone": "DM_ZONE",
      "anchor": "orb_anchor",
      "position": { "x": 0.0, "y": 1.45, "z": -3.2 },
      "rotation_y": 0.0,
      "scale": { "x": 1.0, "y": 1.0, "z": 1.0 },
      "physics_class": "STATIC",
      "notes": "Dominant DM-side anchor. Never interactive. Radius 1.4."
    },
    {
      "name": "DICE_TRAY",
      "mesh_name": "dice_tray_bottom",
      "zone": "DICE_STATION_ZONE",
      "anchor": "dice_tray_center",
      "position": { "x": 4.5, "y": 0.03, "z": 1.75 },
      "rotation_y": 0.0,
      "scale": { "x": 1.0, "y": 1.0, "z": 1.0 },
      "physics_class": "STATIC",
      "notes": "Walnut frame + felt floor. Right side, not centerline."
    },
    {
      "name": "DICE_TOWER",
      "mesh_name": "stub_dice_tower",
      "zone": "DICE_STATION_ZONE",
      "anchor": "dice_tower_base",
      "position": { "x": 4.5, "y": 0.62, "z": 0.5 },
      "rotation_y": 0.0,
      "scale": { "x": 1.0, "y": 1.0, "z": 1.0 },
      "physics_class": "STATIC",
      "notes": "Inside tray unit. Opening at top must be visible from DICE_TRAY posture."
    }
  ]
}
```

### 3.5 `README.md`

Content:

```markdown
# LAYOUT_PACK_V1 — Table Scene Authority Document

## North Star

Poker-table embodiment: a real person sits at a walnut table, looks across at a glowing orb (the DM's presence), has their personal objects spread out on the shelf in front of them, and can turn right to reach the dice station. No HUD. No game UI. Every pixel is a physical object or the room it sits in.

## The Four Primary Postures

| Posture | What must be visible |
|---------|---------------------|
| STANDARD | Orb (upper frame), vault depth cue, far rail. Shelf barely at bottom — presence only. |
| DOWN | Shelf fills frame: sheet numbers readable, notebook page readable, rulebook headings readable. |
| LEAN_FORWARD | Vault recess unmistakable. Orb still in frame. Never true top-down. |
| DICE_TRAY | Tray + tower dominate. Feels like turning right, not teleporting. |

## Golden Frame Rule

The `golden/` folder contains reference PNGs at 1920×1080. If your change produces a materially different result in any posture, you must update the golden frame in the same commit with a rationale comment. If you can't explain the change in terms of posture intent + zone rules, don't make it.

## How to Regenerate Golden Frames

1. Start dev server: `npm run dev --prefix client`
2. Open: `http://localhost:5173?debug=1&zones=1`
3. Resize browser to exactly 1920×1080
4. Use hotkeys (1-5) to navigate postures
5. Screenshot each posture with OS screenshot tool
6. Save to `docs/design/LAYOUT_PACK_V1/golden/[POSTURE]_1080.png`

## Hard Bans

- No tooltip, popover, or snippet components
- No roll buttons or action menus that execute game actions
- No hardcoded camera positions outside `camera_poses.json`
- No hardcoded object positions outside `table_objects.json`
- No hardcoded zone bounds outside `zones.json`
```

---

## 4. Implementation Spec

### 4.1 Runtime wiring

**`aidm/ui/zones.json`** — update in place to match the new schema above (6 zones + anchors). The existing runtime zone-loading code reads this file; update it to handle the new schema.

**`client/src/camera.ts`** — The `POSTURES` const currently has hardcoded values. Replace with a loader that fetches `camera_poses.json` at startup (or during build via Vite import). The simplest approach: import the JSON directly via Vite's JSON import (`import cameraPoses from '../../../docs/design/LAYOUT_PACK_V1/camera_poses.json'`) and build the `POSTURES` map from it. Transition duration reads from `transition_ms` field.

**`client/src/scene-builder.ts`** — Object positions currently hardcoded. Add a `tableObjectsConfig` import (same pattern) and use anchor positions from `table_objects.json` when positioning stubs in `buildObjectStubs()`. The mesh geometry dimensions (BoxGeometry scale) stay hardcoded — only centroid positions move to JSON.

### 4.2 Debug overlay — zones + anchors

When `?debug=1&zones=1` is in the URL, draw:
- Each zone as a `THREE.BoxHelper` or `THREE.Box3Helper` at y=0.01 (table surface), colored by zone (use the `color` field from zones.json)
- Each anchor as a small `THREE.SphereGeometry(0.08)` with a `THREE.SpriteMaterial` label showing the anchor name

This is the visual confirmation that the JSON matches the scene geometry. Anvil uses this to confirm alignment before capturing golden frames.

### 4.3 Stub_parchment and loose d6 cleanup

Two orphan objects found in VQ inspection:

1. `stub_parchment` at (−3.5, 0.005, 3.8) — Set `visible = false` on this mesh. It is not in `table_objects.json` and should not appear in the scene.
2. The two extra d6 stubs at (4.1, 0.16, 1.55) and (4.7, 0.16, 1.85) — Remove them from `buildObjectStubs()`. Dice are managed by `DiceObject` in `main.ts`. Static stub dice create confusion.

---

## 5. Gate Spec

**Gate name:** `UI-LAYOUT-PACK`
**Test file:** `client/tests/zone_parity.spec.ts` (skeleton only — full test suite in WO-UI-GATES-V1)

Gate passes when:

1. `docs/design/LAYOUT_PACK_V1/zones.json` exists and validates against schema
2. `docs/design/LAYOUT_PACK_V1/camera_poses.json` exists and has all 5 postures
3. `docs/design/LAYOUT_PACK_V1/table_objects.json` exists and all 7 objects present
4. `docs/design/LAYOUT_PACK_V1/README.md` exists
5. `aidm/ui/zones.json` matches the new 6-zone schema
6. Runtime loads without error (Playwright: navigate to dev server, no console errors)
7. `stub_parchment.visible === false` (confirmed via `?dump=1` scene dump)
8. No d6 stub meshes outside DICE_STATION_ZONE (no mesh at x=4.1,z=1.55 or x=4.7,z=1.85)

**Test count target:** 8 checks → Gate `UI-LAYOUT-PACK` 8/8.

---

## 6. What This WO Does NOT Do

- Does not move the camera in the browser (that is WO-UI-CAMERAS-V1)
- Does not change object geometry (that is WO-UI-OBJECT-LAYOUT-V1)
- Does not change lighting (that is WO-UI-LIGHTING-V1)
- Does not add kinematic drag (that is WO-UI-PHYSICALITY-BASELINE-V1)
- Does not add screenshot tests (that is WO-UI-GATES-V1)

---

## 7. Preflight

```bash
npm run dev --prefix client
# Navigate to http://localhost:5173?debug=1&zones=1
# Confirm zones render as colored boxes on table surface
# Confirm anchors render as small spheres with labels
```
