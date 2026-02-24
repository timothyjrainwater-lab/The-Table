# Anvil → Slate: UI State Brief
**Date:** 2026-02-23
**From:** Anvil (builder seat)
**To:** Slate (PM)
**Re:** Table UI — full audit against north star vision. Thunder wants you to take this from here.

---

## What Was Built (Slices 0-7, commit `c7e571e`)

All doctrine §19 slices are delivered and gate-tested:

- **Slice 0:** Scene + camera postures (STANDARD, DOWN, LEAN_FORWARD, DICE_TRAY) — smooth interpolation, interruptible
- **Slice 1:** Dice ritual — PENDING_ROLL → d20 fidget → tower drop → roll_result reveal
- **Slice 2:** Beat intent card — director state display, click to declare
- **Slice 3:** BookObject — PHB rulebook, open/close/flip, ? stamps, openToRef()
- **Slice 4:** NotebookObject — 4 sections (notes/transcript/bestiary/handouts), live drawing, tab system
- **Slice 5:** HandoutManager — printer slot, delivery animation, fanstack, discard well
- **Slice 6:** MapOverlayManager — AoE shapes, measure line, area highlight, all ephemeral
- **Slice 7:** EntityRenderer — faction-colored tokens, HP bars, token click → TOKEN_TARGET_INTENT, AoE confirm gate

Gate status: 6,720+ tests, all gates A–AB + V7–V12 + UI-06 + BURST-002/003 PASS. Gate X 9/10 (pre-existing real artifact violations, not new failures).

---

## Current Visual State — BROKEN

The scene is visually discombobulated. Thunder sent two screenshots today showing:

1. Red book standing upright in the middle of the battle map
2. Massive dark wedge objects dominating the near edge — book/notebook tipped on edge by bad external rotation

Root cause: `BookObject` and `NotebookObject` geometry is built flat (covers are horizontal boxes, Y is the thin axis). When I added them to the scene I incorrectly applied `rotation.x = -Math.PI/2`, which tipped them up on edge. Removed that rotation. Build passes. Visual result not yet confirmed — Thunder hasn't sent a follow-up screenshot.

The stubs (`stub_tome`, `stub_notebook`) are hidden in code to prevent z-fighting with the live objects. If the rotation fix worked, book and notebook should now be flat rectangles on the player shelf at `z=4.8`.

**This spatial fix needs visual confirmation before anything else proceeds.**

---

## Gaps Against North Star Vision

Graded by blocking status:

### Blocking — core game loop not complete without these

| Gap | Detail |
|-----|--------|
| Character sheet is static | `stub_character_sheet` has a real D&D 3.5e template rendered on it but is not interactive and not wired to any WS events. Values are hardcoded placeholder. No `character_sheet_update` event exists. Clicking sheet lines does nothing. Doctrine says sheet click = accessibility path for DECLARE_ACTION_INTENT. |
| Battle map is not a scroll | The felt vault is always present. Vision says a magical scroll unrolls at combat start and rolls back up at end. There is no scroll mesh, no unroll animation, no combat-state-driven visibility. |
| Crystal ball NPC portrait not wired | The orb pulses (always — not tied to TTS state). No `crystal_ball_npc_portrait` event handled. When an NPC speaks, nothing happens to the ball visually. |

### Non-blocking but vision-significant

| Gap | Detail |
|-----|--------|
| Dice bag missing | Removed from stubs during spatial rework. Vision requires a 3D bag on the player shelf, click to open, full die set inside. Currently only the d20 exists as an interactive object. |
| Entity tokens are 3D cylinders | Vision says 2D animated image chips, tokens slide square to square. We have faction-colored 3D cylinders. Functional but wrong fidelity. |
| Entity movement teleports | `entity_delta` with position change causes instant teleport, no slide animation. |
| Crystal ball pulse not tied to TTS | Orb pulses continuously. Should only glow/pulse when AI is speaking. |
| Session zero not wired | Notebook cover customization framework exists but no WS events for name-on-cover or image generation. |
| Notebook persistence | Drawing strokes live in memory only. Lost on refresh. |
| Bestiary images are placeholders | Progressive reveal structure is there (heard/seen/fought/studied), but no image binding — silhouette, sketch, full image are all generated procedurally as stand-ins. |
| Handout fanstack caps at 5 | No wrap logic after 5 simultaneous handouts. |
| Fog of war | Not implemented at all. Vision calls it highest priority visual feature. |

---

## Code Health

- Gate G: clean. Zero `Math.random()` in client/src/. All procedural textures seeded.
- Doctrine §3: clean. No tooltips, popovers, floating info windows anywhere.
- Doctrine §16: clean. UI sends REQUEST_* only, runtime returns STATE/EVENT.
- WS message handlers: 20+ event types wired in main.ts.
- Build: `npm run build` exits 0, 19 modules, 0 TypeScript errors.
- Pre-existing test exclusions unchanged: X-01 (real tracked artifacts), W-15 (pre-existing gap).

---

## Open WO

**WO-FIX-HOOLIGAN-03** — ACCEPTED per debrief in inbox. Gate K now 72/72 (69 + 3 new tests). Needs verdict and PM_BRIEFING update.

---

## What Thunder Needs From You

Visual confirmation of the spatial fix is first. After that, the priority call on what to build next is yours. The three biggest gaps in terms of vision fidelity are: the character sheet not being interactive, the battle map not being a scroll, and the crystal ball not responding to NPC speech. Everything else is enhancement territory.

Anvil out.
