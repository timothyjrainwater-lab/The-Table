# WO-UI-05 — Table Surface & Atmosphere

**Issued:** 2026-02-23
**Authority:** MEMO_TABLE_VISION_SPATIAL_SPEC, DOCTRINE_04_TABLE_UI_MEMO_V4, Thunder authorization via MEMO_ANVIL_TO_SLATE_UI_PARALLEL_TRACK
**Track:** UI parallel track (does not block or depend on PRS-01 / backend WOs)
**Gate:** Visual review by Thunder. No automated test gate.

---

## 1. Target Lock

Transform the current Three.js scene from a flat dark plane with wireframe zone overlays into a **physically believable tabletop environment**. Thunder needs to see the table and feel the project is real. This is an anchor point, not a feature request.

The golden beacon: **Matt Mercer's table. Dim library. Warm lanterns. Dark walnut. Recessed felt vault.**

Slice scope: scene materials + lighting + object stubs + shadows. No interaction, no WebSocket, no backend.

---

## 2. Binary Decisions

| # | Decision | Choice | Rationale |
|---|---|---|---|
| 1 | Table material | Procedural walnut (MeshStandardMaterial, dark brown, high roughness, subtle grain via normal map or bump) | No texture assets required; PBR feel achievable procedurally |
| 2 | Grain texture | Generate via Three.js canvas texture or DataTexture (noise-based grain pattern) | No external file dependency |
| 3 | Felt vault | Separate recessed PlaneGeometry or BoxGeometry inset below rail level, dark green/burgundy matte | Per reference: physically lower than the rail |
| 4 | Lighting | Replace flat dirLight with 2-3 warm PointLights (amber ~0xffaa44) + very low ambient | Per doctrine: "warm pools of lantern light on dark timber. The wood glows, the background fades." |
| 5 | Flickering | Subtle sinusoidal intensity variation on at least one point light (±5-10% amplitude, 0.5-2Hz) | Candlelight feel — not distracting, just alive |
| 6 | Shadow quality | renderer.shadowMap.type = THREE.PCFSoftShadowMap, soft shadow radius | Per spec: "objects cast soft shadows on the table surface" |
| 7 | Object stubs | BoxGeometry / CylinderGeometry placeholders, correct scale and zone placement | Presence first, geometry second |
| 8 | Zone overlays (wireframes) | Remove or make invisible — they break immersion | Zones still exist in zones.ts for backend; just don't render the outlines |
| 9 | Scene background | Very dark (nearly black with slight warm tint) or FogExp2 to fade edges | "The table is the room. Everything beyond the table edge is atmosphere and shadow." |
| 10 | Felt vault position | Y offset ~-0.05 to -0.1 below table surface, inset from rail | Recessed, not flush |

---

## 3. Contract Spec

### 3.1 Table surface

```typescript
// Dark walnut — rough, warm brown, catches light
const tableMat = new THREE.MeshStandardMaterial({
  color: 0x2d1b0e,      // dark walnut base
  roughness: 0.75,
  metalness: 0.05,
  // normalMap: <procedural grain texture>  — if achievable
});
```

Grain: generate a small (256×256) canvas texture with horizontal noise stripes and apply as normalMap or roughnessMap. The wood should visibly catch the warm pointlight — this is the key visual target.

### 3.2 Felt vault (recessed center)

```typescript
// Recessed felt area — center of table, below rail
// Dimensions: approximately 6×4 units (narrower than full table)
// Y position: -0.08 (slightly below table surface)
// Material: dark burgundy/forest green, very matte (roughness ~1.0, metalness 0)
const feltMat = new THREE.MeshStandardMaterial({
  color: 0x2d1a1a,  // or 0x1a2d1a for green felt — builder chooses per visual result
  roughness: 0.98,
  metalness: 0.0,
});
```

The felt area is where the battle map lives. It reads as "at depth" from STANDARD camera.

### 3.3 Lighting

Remove current dirLight (flat). Replace with:

```typescript
// Overhead lantern — primary warm light, above-center
const lantern1 = new THREE.PointLight(0xffaa44, 1.5, 25);
lantern1.position.set(0, 6, 0);
lantern1.castShadow = true;

// Secondary lantern — slight offset for asymmetry
const lantern2 = new THREE.PointLight(0xff9933, 0.8, 20);
lantern2.position.set(-3, 5, 2);
lantern2.castShadow = false;

// Very low ambient — prevents pitch black, stays moody
const ambient = new THREE.AmbientLight(0x1a1005, 0.15);

// Flickering: in animate loop, modulate lantern1.intensity
// lantern1.intensity = 1.5 + 0.1 * Math.sin(Date.now() * 0.002);
```

### 3.4 Physical object stubs

Per zone layout from MEMO_TABLE_VISION_SPATIAL_SPEC. Correct zones, correct scale, geometry only:

| Object | Geometry | Zone | Position (approx) | Notes |
|---|---|---|---|---|
| Dice bag | SphereGeometry r=0.2, slightly flattened | Rail, left | (-4, 0.2, -1) | Soft, round |
| Dice tray | BoxGeometry 1×0.1×0.8 with lip | Rail, right | (4, 0.05, 0) | Flat with raised edges |
| Notebook | BoxGeometry 1.2×0.05×0.9 | Near side (player) | (1, 0.025, 2.5) | Flat book |
| Rulebook (tome) | BoxGeometry 1.4×0.15×1.1 | Near side (player) | (-1, 0.075, 2.5) | Thicker, taller |
| Character sheet | PlaneGeometry 0.85×1.1 | Near side (player) | (0, 0.01, 3) | Flat paper |
| Crystal ball | SphereGeometry r=0.3 | Far side (DM) | (0, 0.3, -2.5) | Glass material, slight emissive |
| Cup holder | CylinderGeometry r=0.15, h=0.3 | Rail, corner | (4.5, 0.15, -2) | Brass-ish metalness ~0.8 |

Materials: all stubs use MeshStandardMaterial with rough dark textures appropriate to the object (leather for bag, paper for sheets, wood for tome cover, metal for cup, glass for crystal ball). No flat colors — everything should respond to the warm light.

Crystal ball: `MeshPhysicalMaterial` with `roughness: 0.0, metalness: 0.1, transmission: 0.8` if Three.js version supports it, else emissive glow.

### 3.5 Shadow pass

```typescript
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

// All stub objects: castShadow = true
// Table surface and felt: receiveShadow = true
// lantern1: castShadow = true, shadow.mapSize.width = 1024, radius = 4
```

Soft shadows from warm overhead light falling across the table surface.

### 3.6 Zone overlays

The wireframe zone outlines break immersion. Remove them (or set `visible = false`). The zone logic in `zones.ts` stays intact — just don't render boundaries during this slice.

### 3.7 Scene background / atmosphere

```typescript
scene.background = new THREE.Color(0x0a0805);  // near-black warm
// Optional: FogExp2 to fade edges
scene.fog = new THREE.FogExp2(0x0a0805, 0.08);
```

---

## 4. Implementation Plan

1. **Grain texture generator** — write a function `buildWalnutTexture(): THREE.CanvasTexture` that generates a 256×256 canvas with horizontal grain noise. Apply as `normalMap` or `roughnessMap` to table material.
2. **Replace table material** — update `tableMat` to MeshStandardMaterial with walnut values + grain texture.
3. **Add felt vault** — new PlaneGeometry, slightly recessed, dark matte felt material. Positioned inside the table surface bounds.
4. **Replace lighting** — remove flat dirLight, add two warm PointLights + very low ambient. Add flicker to primary in animate loop.
5. **Shadow quality** — set `renderer.shadowMap.type = THREE.PCFSoftShadowMap`.
6. **Object stubs** — add 7 stub objects (dice bag, tray, notebook, tome, sheet, crystal ball, cup) in correct positions, correct scale, material that responds to light.
7. **Disable zone overlays** — set zone wireframe objects to `visible = false` or remove from scene.
8. **Scene background** — dark warm color + optional fog.
9. **Build verify** — `cd client && npm run build` must exit 0. No regressions.

---

## 5. Deliverables Checklist

- [ ] `client/src/main.ts` updated with all scene changes
- [ ] Grain texture function added (separate utility or inline)
- [ ] Table surface: dark walnut, grain visible, catches warm light
- [ ] Felt vault: recessed center area, dark matte material
- [ ] Lighting: 2 warm PointLights + ambient + flicker in animate loop
- [ ] Shadow quality: PCFSoftShadowMap, soft radius
- [ ] 7 object stubs in correct positions, all castShadow = true
- [ ] Zone wireframes not rendered
- [ ] Scene background: near-black warm, optional fog
- [ ] `npm run build` exits 0
- [ ] No new TypeScript errors

---

## 6. Integration Seams

- All changes are confined to `client/src/main.ts` (and possibly a new texture utility file)
- `zones.ts`, `camera.ts`, `ws-bridge.ts`, `table-object.ts` — **do not modify**
- Zone positions (from `ZONES`) still used to place object stubs — import and use them
- The WS bridge, BeatIntentCard, DiceObject, and DragInteraction can stay wired — they don't conflict with scene changes
- No Python changes, no test changes, no backend changes

---

## 7. Assumptions to Validate

1. Three.js r170 supports `MeshPhysicalMaterial` with `transmission` — check if crystal ball glass is achievable; if not, fall back to emissive glow
2. Canvas-based grain texture: confirm `THREE.CanvasTexture` is available in the current import setup
3. Two shadow-casting lights: confirm GPU performance is acceptable (if not, one shadow caster is fine)

---

## 8. Gate

**Visual review by Thunder.** No automated test. Builder delivers, Thunder opens browser, looks at the table.

Success criteria (Thunder's words): *"If I see all the UI elements kind of together and actually looking good, I'll feel more stable."*

Builder should take a screenshot and include it in the debrief if possible.

---

## 9. Debrief Focus

1. **The wood** — does it actually glow under the warm light, or does it still read as flat? Describe the material values that worked.
2. **The felt vault** — does it read as recessed? What Y-offset and geometry produced the right depth illusion?

---

## Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```
