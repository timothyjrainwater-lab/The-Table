# Memo to Slate — UI Parallel Track Authorization

**From:** Anvil
**To:** Slate (PM)
**Date:** 2026-02-23
**Re:** UI build authorized as parallel track — operator grounding priority

---

## What happened this session

Thunder and I had a long session. Wendy demo video is done — 18 audio clips via Kokoro ONNX, 6 fresh SDXL-generated scene images, assembled into a 2.5-minute portrait MP4 (`scripts/wendy_demo_output/wendy_demo.mp4`). That was the immediate deliverable.

After that, Thunder asked whether the UI could be worked on in parallel. I pulled the full client picture — WO-UI-01 through WO-UI-04 are accepted, build is green, Three.js scene exists with camera postures / zones / dice / WS bridge. But it's visually an empty dark table. The research corpus (MEMO_TABLE_VISION_SPATIAL_SPEC, TABLE_SURFACE_UI_SPECIFICATION, UX_VISION_PHYSICAL_TABLE, and the rest) is fully written and detailed.

Thunder's framing was direct: **he needs to see the UI objects actually looking right to feel stable about the project's direction.** Exact quote: "If I see all the UI elements kind of together and actually looking good, I'll feel more stable." This is not a feature request. It is an anchor point. Treat it accordingly.

---

## Authorization

Thunder is authorizing UI work as a **parallel track** alongside backend/RC work. This is not replacing BURST-001 Tier 5 completion, IP remediation, or the pre-RC commit. It runs alongside.

**This memo is Thunder's dispatch authorization for the next UI WO.**

---

## What the next WO should target

Current client state: Slice 2 complete (bones are right). Missing: the visual world.

The single highest-leverage slice to make Thunder feel the project is real is the **table surface itself** — before individual objects, because everything sits on it. The doctrine reference is MEMO_TABLE_VISION_SPATIAL_SPEC.

Concretely, the next WO (WO-UI-05) should deliver:

1. **Table surface material** — dark walnut PBR texture (or convincing procedural equivalent), grain visible, catches light
2. **Felt vault / recessed tray** — inset felt area in center of table where dice and cards rest (darker, matte, bounded)
3. **Warm candlelight atmosphere** — replace current flat directional light with warm point lights (amber, flickering subtle), ambient occlusion feel, dark room outside the table's light pool
4. **Physical object stubs** — correctly-positioned placeholder meshes for each table object (dice bag, notebook, tome, character sheet, crystal ball, cup holder) in their correct zones, with correct scale, even if they're just geometry with material. No interaction yet — just presence.
5. **Shadow pass** — objects cast soft shadows on the table surface. This alone makes it feel physical.

What this does NOT include: interaction, two-phase activation, WebSocket wiring, or any backend. Pure scene.

**Gate:** Visual review by Thunder. No automated test gate — this is atmosphere, not code correctness.

---

## Key design documents for the builder

All in the repo:

| Document | What it contains |
|---|---|
| `pm_inbox/reviewed/MEMO_TABLE_VISION_SPATIAL_SPEC.md` | Golden beacon — walnut table, recessed vault, Critical Role EXU reference, hand triangle ergonomics |
| `docs/design/TABLE_SURFACE_UI_SPECIFICATION.md` | Complete object inventory, two-phase activation, zone layout |
| `docs/design/TABLE_METAPHOR_AND_PLAYER_ARTIFACTS.md` | "No application UI. Only D&D objects." Object list with physical analogs |
| `docs/specs/UX_VISION_PHYSICAL_TABLE.md` | Crystal ball, dice bag, notebook sections, DM zone |
| `pm_inbox/doctrine/DOCTRINE_04_TABLE_UI_MEMO_V4.txt` | Camera postures, hard bans, table object set, build order |
| `client/src/` | Existing Three.js client — camera.ts, zones.ts, table-object.ts, main.ts |

Current client already has: Three.js r170, Vite, TypeScript, WebSocket bridge, zone definitions. Builder does not need to scaffold from zero.

---

## Parallel track protocol

- UI WOs run in parallel with backend WOs. Neither track blocks the other.
- UI gate is visual (Thunder review) not suite-based, until Slice 7 runtime integration.
- Pre-RC commit and IP remediation (P1/P8) are still operator action items — not displaced by UI track.
- UI WOs go through normal dispatch → deliver → debrief cycle. Slate drafts, Thunder approves, builder executes.

---

## Anvil note

Thunder is stable. The Wendy demo went well — voices clean, images solid, video assembled. He has something tangible to show. The UI ask is forward momentum, not panic. He's in a peaks-and-valleys stretch and knows it. The visual anchor is the right next thing to give him.

Seven wisdoms. Zero regrets.

— Anvil

