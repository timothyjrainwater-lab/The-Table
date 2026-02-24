# Visual QA Findings — Pass 001
**Date:** 2026-02-23
**Build:** 81a39cf7ca508360a57488179af2778e8419dab5
**Inspector:** Slate (second pair of eyes, alongside Anvil)
**Method:** Live dev server (`npm run dev`, port 3000), all four camera postures inspected, source code cross-referenced for object inventory and geometry details.

---

## Summary

The scene is structurally sound and much healthier than the pre-fix screenshots in `ANVIL_UI_BRIEF_20260223.md` suggested — the book/notebook rotation fix landed correctly, objects are flat on the shelf. Approximately 8 findings across P0–Cosmetic severity. The two dominant issues are: the dice tower cluster is visually crowded and confusing at STANDARD posture (PM flagged this already), and the battle map is always-present as a static felt vault rather than a rolled-up scroll. Lighting is warm and atmospheric — no issues there. Most missing features (fog of war, token chip style, crystal ball portrait) are already wired and waiting for backend events, not absent from the codebase.

**Findings count (Pass 1): P0 × 1 | P1 × 3 | P2 × 2 | Cosmetic × 2**
**Findings count (Pass 2 addendum): P1 × 2 | P2 × 1 | Cosmetic × 1 | Pass-1 correction × 1**
**Findings count (Pass 3 addendum): P0 × 2 | P1 × 5 | P2 × 2**
**Findings count (Pass 4 addendum): P0 × 2 | P1 × 4**
**Combined total: P0 × 5 | P1 × 14 | P2 × 5 | Cosmetic × 3**

---

## Findings

### [FINDING-VQ-001] Battle map felt vault always visible — scroll metaphor absent
**Severity:** P0
**Section:** The Battle Map (Magical Scroll)
**Observed:** A large recessed dark-felt vault (`felt_vault`, position `0, -0.04, -0.5`, 6.2 × 4.2 world units) is permanently visible at all times, occupying the entire DM-side center of the table. The `BattleScrollObject` scroll surface exists in code and correctly starts at `scale.z = 0.001` (rolled state), but the felt vault beneath it is always present and dark, making the DM side look like a permanently open battle map zone even when not in combat.
**Expected:** Vision says the felt vault should not read as a "battle map waiting area." Out of combat, the DM side should feel like open table space. The scroll appears only when `combat_start` fires. The permanent dark rectangle breaks the physical table metaphor at rest.
**Screenshot:** `06_down_full_table.png` — the large dark-red/maroon rectangle dominating the center-left.
**Notes:** `BattleScrollObject` is correctly implemented (unroll animation via `scale.z` lerp, scroll rod visual). The fix is not removing the felt vault — it's ensuring the vault color matches the walnut table surface when scroll is in rolled state, so it reads as table, not as an empty map frame. Alternatively, hide/show the vault on `combat_start`/`combat_end` alongside the scroll.

---

### [FINDING-VQ-002] Dice tower area — spatial crowding and depth confusion at STANDARD posture
**Severity:** P1
**Section:** Dice Tower + Dice Bag (Dice area / player shelf right)
**Observed:** At STANDARD camera angle, the right side of the scene shows: dice tower body (tall box, z=0.5), dice bag cluster (z=4.8), d20 (on tray), tray itself (z=1.75 area), trash ring (z=3.6), and brass cup (z=5.5). These objects are distributed across a large Z-range but from the seated camera angle they appear stacked and overlapping. The tower reads as a dark box; the dice bag's small decorative dice are invisible from this angle; the d20 in the tray is tiny relative to the tower. The overall impression is a cluster of dark shapes of unclear purpose.
**Expected:** Vision: player picks up d20, drops into tower top, hears tumble, sees result emerge in tray. The physical flow (bag → pick up → tower top → tray) should be legible from the default view.
**Screenshot:** `08_standard_final.png` (right cluster), `07_dice_tray_closeup.png` (DICE_TRAY posture — clearer but the tray view still shows overlapping dark shapes).
**Notes:** DICE_TRAY posture (`[4]`) is a dedicated camera that zooms in — it resolves most of the readability problem. The root issue is that STANDARD posture doesn't make the flow legible. Consider: (1) slight separation between tower and bag on X-axis; (2) brighter tray felt color so the result-zone reads clearly; (3) tower opening gap geometry (currently the top is a solid cap mesh — the "opening" is implied but not visible).

---

### [FINDING-VQ-003] Dice tower has no visible opening
**Severity:** P1
**Section:** Dice Tower
**Observed:** The tower body is a solid box (`BoxGeometry`, `position 4.5, 0.62, 0.5`) topped with a second "top" mesh. There is no geometry cut, slot, or visual affordance indicating where a die is dropped in. From any angle the tower reads as a closed wooden box.
**Expected:** Vision: "Opening at the top, slot at the bottom with a tray. Player drags a die to the top opening and releases." The opening is a core affordance — it tells the player where to drop the die.
**Screenshot:** `07_dice_tray_closeup.png` — tower visible, top is solid.
**Notes:** Fix is either: (a) replace top cap with a hollow frame geometry (box with hole), or (b) use a dark material for the top face only to imply an opening. This is the primary reason the dice tower reads as a "jumbled wedge" at STANDARD — there is no clear interactive affordance.

---

### [FINDING-VQ-004] Notebook visible as `stub_notebook` (static box) — live NotebookObject may be z-fighting or mis-positioned
**Severity:** P1
**Section:** Notebook
**Observed:** `main.ts` hides `stub_notebook` (`visible = false`) and adds the live `NotebookObject` at z=4.8. In DOWN posture, the player shelf shows a small dark rectangle that appears to be the live notebook at the correct position. However at STANDARD posture, the notebook is barely visible — a thin dark sliver at the near-left edge, largely occluded by the shelf front rail. The character sheet (yellow, `position -2.0, 0.005, 4.8`) is the dominant player-shelf object in all views.
**Expected:** Vision: "Physical 3D book object on the player side. Cover is visible. Positioned correctly relative to other objects." The notebook should be the most prominent player-side object, legible from STANDARD.
**Screenshot:** `08_standard_final.png` — notebook barely visible lower-left; `06_down_full_table.png` — small dark rectangle at z=4.8 center, dwarfed by felt vault.
**Notes:** The shelf rail (z=0.7, y=0.03) at the near edge may be clipping the view. The notebook at z=4.8 is behind the rail from the STANDARD camera angle. Consider pushing the notebook slightly further from the rail or adjusting shelf Z so objects on the shelf are visible from seated posture. This may be a camera FOV issue rather than object misplacement.

---

### [FINDING-VQ-005] Crystal ball pulse not tied to TTS state — pulses constantly
**Severity:** P2
**Section:** Crystal Ball (DM Presence)
**Observed:** `CrystalBallController.tick()` pulses continuously at all times (`speakingIntensity` starts at 0 but the ambient orb glow `(0x4455dd, intensity 10.0)` is always on). The glow light is always present and blue-purple regardless of TTS state.
**Expected:** Vision: "Pulses/glows when the AI speaks (TTS output)." At rest, the orb should be dim/dormant. The pulse event is correctly wired (`tts_speaking_start` / `tts_speaking_stop` both handled in main.ts), but since the backend is offline the ball never enters speaking state — it just idles at ambient glow.
**Screenshot:** `08_standard_final.png` — orb glows blue-purple even with WS disconnected.
**Notes:** This is a backend-offline artifact and will self-correct when TTS events flow. However, the idle state needs a "resting" visual — currently idle = bright blue-purple glow, which reads as "always speaking." Recommend: reduce `orbGlow` intensity to ~1.5 at idle, only ramp to 10 on `tts_speaking_start`. Low-effort fix.

---

### [FINDING-VQ-006] Character sheet too prominent — reads as a UI panel, not paper
**Severity:** P2
**Section:** Character Sheet
**Observed:** The character sheet stub (`position -2.0, 0.005, 4.8`, `BoxGeometry` with canvas texture) is the most visually legible player-shelf object at all postures — bright yellow-cream, large. It correctly has a D&D 3.5e template rendered on it. However, the placeholder values (`STR: 14`, `HP: 32`, etc.) and the sheet's brightness make it feel like a floating UI panel rather than a piece of paper on a dark table.
**Expected:** Vision: "Physical paper object(s) on the table — looks like paper, not a UI panel."
**Screenshot:** `06_down_full_table.png` — sheet is the brightest object on the player side, reading as a glowing UI element rather than parchment.
**Notes:** Two fixes: (1) reduce canvas background brightness from near-white to aged parchment (`#d4c08a`-range), similar to the `stub_parchment` material (`0xd4c8a4`); (2) reduce roughness value so it reads matte/paper. The live `CharacterSheetController` (`character-sheet-controller.ts`) handles live updates — this is purely a texture/material tweak.

---

### [FINDING-VQ-007] Trash hole ring visible as bright gold ring at player shelf — no context
**Severity:** Cosmetic
**Section:** Player Shelf / Table
**Observed:** The trash hole ring (`trashRingMesh`, brass material, `position 2.7, 0.065, 3.6`) is clearly visible as a golden ring at the player side in STANDARD posture. There is no visual cue (shadow, depth, downward funnel) that reads it as a "hole" rather than a decorative ring sitting on the table surface.
**Expected:** Vision: "A spot at the edge of the table (or a small hole/slot). Drop zone detection." The ring should read as the rim of a hole, not an ornament.
**Screenshot:** `08_standard_final.png` — bright gold ring lower-center.
**Notes:** Consider adding a dark inner fill circle (black felt disc slightly below the ring) to reinforce the "hole" read. Very low effort.

---

### [FINDING-VQ-008] Debug HUD text permanently visible at top-left
**Severity:** Cosmetic
**Section:** Overall scene
**Observed:** Four lines of text are always rendered at top-left: `[1] Standard [2] Down [3] Lean Forward [4] Dice Tray` and `Posture: STANDARD` and `WS: connecting...`. These are DOM overlays, not gated by `?debug=1`.
**Expected:** Vision: "The system NEVER displays persistent on-screen text/HUD overlays." The camera posture switcher is a dev tool and should either be hidden behind `?debug=1` or removed from production build.
**Screenshot:** All screenshots — HUD labels visible in every frame.
**Notes:** The WS status line is similarly always visible. Both should be dev-only. The text input bar at the bottom (`Type a command or message…`) is also always visible — this is the text fallback channel mentioned in the vision doc as "somewhere unobtrusive," but it's quite prominent at the bottom of the frame. Flag for PM: does the text input bar belong in the finished product's STANDARD posture, or is it a dev affordance?

---

## What Looks Good

- **Lighting:** Warm candlelight atmosphere is convincing. Multiple PointLights with different color temperatures (orange lanterns `0xff8833`, DM candle `0xff6020`, cooler map spot `0xffaa44`) produce good depth. Flicker animation on lanterns works. Hemisphere + ambient underfill prevents harsh blacks. No areas read as too bright or too cold.
- **Table surface material:** Walnut texture with subtle grain reads correctly as a real table. Shadow casting works.
- **Crystal ball geometry:** The orb + pedestal + brass base reads as a crystal ball on a stand. Shape and proportions are correct.
- **Camera posture system:** All four postures (`STANDARD`, `DOWN`, `LEAN_FORWARD`, `DICE_TRAY`) work correctly with smooth interpolation. The DICE_TRAY posture is a well-chosen dedicated angle for die-rolling legibility.
- **Book/notebook rotation fix confirmed:** The catastrophic tipping issue reported in the brief is resolved. Objects on the player shelf are flat and correctly positioned.
- **Battle scroll infrastructure:** `BattleScrollObject` is implemented correctly — rolls up/unrolls via `scale.z` lerp, scroll rod visual is present. Awaiting `combat_start` event to demo.
- **Token infrastructure:** `EntityRenderer` uses flat `PlaneGeometry` chips (WO-UI-TOKEN-CHIP-001 landed). Canvas-texture with faction color + name initial. Slide animation implemented. Cannot assess visually without backend entity events.
- **Fog of war infrastructure:** `FogOfWarManager` is implemented with grid-cell opacity, vision-type differentiation (normal/low_light/darkvision), and fade animation. Awaiting `fog_update` events from backend. Per-cell reveal/dim states look correct in code.
- **Dice bag:** Present, positioned correctly at player-side (`-2.4, -0.10, 4.8`), contains decorative full die set (d4/d6/d8/d10/d12/d20), open/close animation wired. Click-to-toggle functional.
- **Rulebook (tome):** Stub present (`position 2.0, 0.04, 4.8`), live `BookObject` replaces it. Readable from DOWN posture.
- **Trash hole:** Present, correct zone position.
- **Scene fog:** `THREE.Fog` configured so table floats in darkness — correct atmospheric effect.

---

---

## Secondary Pass Addendum — Pass 002
**Date:** 2026-02-23 (same session, second sweep)
**Method:** Additional source code cross-reference + targeted screenshots of LEAN_FORWARD posture and player shelf zone.

### Pass-1 Correction

**VQ-008 is already resolved.** The `#hud` div (posture labels + WS status) now has `display: none` by default in `index.html`, with a script tag showing it only when `?debug=1` is present. Anvil addressed this between the brief and the live build. The text input bar remains always-visible — that part of VQ-008 stands as a question for PM (see VQ-008 below, updated).

---

### [FINDING-VQ-009] LEAN_FORWARD camera clips crystal ball top
**Severity:** P1
**Section:** Camera / Crystal Ball
**Observed:** LEAN_FORWARD posture (`position: 0, 4.5, 1.5` / `lookAt: 0, 0, -0.5`) places the camera close to the orb's Z position from above at a steep angle. The orb (ORB_Y=1.45, ORB_Z=-3.2) fills most of the viewport and its top quarter is clipped by the top edge of the screen. The crystal ball is the DM presence anchor — it should be fully visible and legible in this posture.
**Expected:** Vision: "The angled seated view should be designed so the DM side content is still comprehensible without switching perspective." LEAN_FORWARD is the DM-side engagement view. The orb should be fully framed, not truncated.
**Screenshot:** `p2_05_lean_forward_orb_crop.png` — top of orb clearly cut off.
**Notes:** Two possible fixes: (a) raise the camera Y slightly (4.5 → 5.5) and pull back Z (1.5 → 2.5) to give more headroom above the orb; (b) adjust lookAt downward (0, -0.5, -0.5) so the orb sits in the lower-center of frame with map space above it. Option (b) is probably better — it would show orb + felt vault in the same frame, making the DM side readable. Low-risk tweak.

---

### [FINDING-VQ-010] Parchment stub (stub_parchment) not hidden — orphan geometry on open work zone
**Severity:** P1
**Section:** Table Layout / Open Work Zone
**Observed:** `stub_parchment` is built in `buildObjectStubs()` at `position(-3.5, 0.005, 3.8)` and added to the `objectStubs` group. Unlike `stub_tome` and `stub_notebook`, it is never set to `visible = false` in `main.ts`. There is no live object replacing it. In the DOWN posture it appears as a faint cream-coloured rectangle on the far left of the player zone — at x=-3.5 it is off the character sheet's area and into no-man's-land.
**Expected:** If this is meant to represent a "loose paper" as a lived-in prop, it should be intentional and at a consistent position. If it is a placeholder, it should be hidden. Currently it appears to be an unconsumed stub that was never cleaned up when HandoutManager was wired — the HandoutManager generates its own paper objects at runtime.
**Screenshot:** `p2_04_down_player_shelf.png` — faint rectangle upper-left, distinct from the character sheet.
**Notes:** Either (a) hide it: `_stubParch.visible = false` in main.ts, or (b) promote it to a deliberate "loose handout" prop with a proper position on the player shelf. If (b), z=4.8 (shelf surface) is more natural than z=3.8 (open work zone). Recommend (a) for now — HandoutManager owns this role.

---

### [FINDING-VQ-011] Notebook too small relative to character sheet — size hierarchy inverted
**Severity:** P2
**Section:** Notebook / Player Shelf
**Observed:** The live `NotebookObject` group is at `(-0.2, 0.05, 4.8)`. Its cover geometry uses `1.1 × 0.08 × 1.5` world units (stub reference). The character sheet stub is a larger, brighter rectangle at `(-2.0, 0.005, 4.8)`. In DOWN posture the notebook reads as a small dark object dwarfed by the sheet. In STANDARD posture the notebook is nearly invisible — the shelf front rail and the distance combine to make it a thin dark sliver.
**Expected:** Vision: "The notebook is the most important player object." It should be the dominant visual presence on the player shelf — larger or at least equal in apparent size to the character sheet, and with a more readable cover texture.
**Screenshot:** `p2_04_down_player_shelf.png` — small dark rectangle center vs large bright sheet upper-left.
**Notes:** The notebook is `1.1 wide × 1.5 deep`. The character sheet is roughly the same footprint but brighter. The imbalance is material contrast (dark leather vs bright parchment) plus position — the notebook is centered while the sheet is offset left, giving the sheet more visual real estate from the angled STANDARD camera. Suggest: (a) increase notebook cover texture brightness slightly (not dramatically — leather should stay dark, but a visible cover design/label helps); (b) shift notebook X slightly negative (-0.5 → -0.8) so it's more front-and-center from STANDARD angle.

---

### [FINDING-VQ-012] No visual separator between player zone and map/open-work zone
**Severity:** Cosmetic
**Section:** Table Layout
**Observed:** The shelf edge strip (`edgeMesh`, `position 0, 0.03, 4.1`, walnut color) is present and meant to mark the step between the main table surface and the player shelf. However in STANDARD posture this edge is nearly flush with the table surface and reads as a subtle line, not a clear zone boundary. The player zone (shelf) and the open work zone (z=0 to z=4.1) blur together visually.
**Expected:** Two clearly distinct zones — player side vs table center — should be legible at a glance from STANDARD.
**Screenshot:** `p2_01_standard_wide.png` — no visible step or zone break between the two areas.
**Notes:** The shelf is at `y=-0.09` (slightly recessed below the table surface). The edge strip is at `y=0.03`. This geometry is correct but at STANDARD camera angle the perspective nearly eliminates the apparent height difference. A subtle felt material change on the shelf vs the main surface, or a slightly taller edge strip, would reinforce the zone boundary. Low priority — cognition still works because of object placement.

---

---

## Pass 3 Addendum — User Feedback + Fresh Eye
**Date:** 2026-02-23 (third sweep, incorporating direct user observations)
**Screenshots:** `p3_05_fresh_standard.png`, `p3_06_down.png`

---

### [FINDING-VQ-013] STANDARD posture does not show the player side at all — fundamental camera failure
**Severity:** P0
**Section:** Camera / Table Layout
**Observed:** STANDARD posture (`position: 0, 1.4, 4.0` / `lookAt: 0, 0.05, 0.5`) points the camera forward across the empty center of the table toward the crystal ball in the far distance. The player shelf (z=4.8–6.0) is behind and below the camera. The character sheet, notebook, dice bag, and rulebook are completely invisible in STANDARD — they fall outside the frustum. 80% of the frame is empty brown table surface.
**Expected:** Vision: "Default view — seated at the player side, looking across the table at a slight angle." Seated means you can see your own stuff. The player should be looking DOWN slightly at their shelf first, with the DM side visible in the upper half of the frame. The shelf with all objects should be legible without switching posture.
**Screenshot:** `p3_05_fresh_standard.png` — empty table, no player objects visible whatsoever.
**Notes:** This is the single most important camera fix. The STANDARD lookAt of `z=0.5` points the gaze too far forward into the empty work zone. The position at `y=1.4` is too low and too close — it puts the camera at seated eye level but aimed at the table center, not at the player's own objects. A correct seated posture should have position around `(0, 2.2, 6.5)` and lookAt around `(0, 0, 2.0)` — high enough to see the shelf laid out below, angled forward enough to see the DM side in the distance. The player should feel like they're looking at their own stuff with the ball visible across the table — not staring at an empty brown plain.

---

### [FINDING-VQ-014] DOWN posture camera is severely tilted — player shelf readable but at a wrong angle
**Severity:** P0
**Section:** Camera / Player Shelf
**Observed:** DOWN posture (`position: 0, 3.2, 5.5` / `lookAt: 0, 0, 3.8`) aims the camera so steeply forward that the felt vault wall and handout slot appear as vertical surfaces filling the right half of the frame. The character sheet and notebook are visible bottom-left but severely perspective-distorted — they read as tall rectangles standing up rather than flat papers lying on a table. Text on the character sheet is unreadable at this angle.
**Expected:** Vision: DOWN is the reading/writing posture. The player should be looking almost straight down at their shelf — enough angle to see the full shelf laid out like a bird's-eye view, close enough to read size-12 font on the character sheet without leaning in. The current angle is about 45° when it should be closer to 70–75° from horizontal.
**Screenshot:** `p3_06_down.png` — character sheet visible but severely foreshortened, felt vault wall fills frame.
**Notes:** Fix: raise position Y to ~5.5 and pull Z back to ~7.5, lookAt at `(0, 0, 4.5)`. This gives a steeper top-down angle directly over the shelf. At 512×512 canvas texture resolution the sheet labels will be legible if the camera is at roughly 2 world units above the object — current distance is too great and the foreshortening is too severe.

---

### [FINDING-VQ-015] Table floats in a black void — no room environment
**Severity:** P1
**Section:** Overall Scene / Atmosphere
**Observed:** `scene.background = new THREE.Color(0x08060a)` — pure near-black. `scene.fog` fades to the same near-black at distance 14–22. The table exists in complete darkness with no walls, floor, ceiling, or any environmental context. In STANDARD posture the upper 40% of the frame is pure black void. This reads as unfinished and breaks the "sitting at a real table" metaphor.
**Expected:** Vision: "One-to-one recreation of sitting at a real tabletop RPG table." A real table is in a room — probably a dimly lit tavern, dungeon chamber, or study. Even a rough suggestion of walls and floor would ground the scene. The table should feel like it's somewhere, not floating.
**Screenshot:** `p3_05_fresh_standard.png` — upper half is pure black.
**Notes:** Doesn't need full room geometry. Options: (a) a dark environment cube map (pre-baked stone/wood room texture) as `scene.background`; (b) subtle geometry planes for floor + back wall just outside the fog distance, textured with stone or rough plaster; (c) a `THREE.PMREMGenerator` environment with a warm interior HDRI. Option (b) is most controllable and cheapest. The fog at z=14–22 means walls only need to be geometry stubs — the fog does the work of hiding edges. A back wall at z=-8 and side walls at x=±9 with a rough stone texture and one or two dim point lights suggesting windows/torches would transform the atmosphere.

---

### [FINDING-VQ-016] Gold bar behind crystal ball — far rail reads as a floating shelf artifact
**Severity:** P1
**Section:** DM Side / Table Rail
**Observed:** The far rail (`rail_far`, `BoxGeometry(12.4, 0.18, 0.3)`, `position 0, 0.09, -4.1`, walnut material) is visible as a bright wood-colored horizontal bar behind and below the crystal ball in STANDARD posture. Because there's no room geometry behind it, it appears to float in the black void — it looks like a separate shelf or ledge rather than the far edge of the table.
**Expected:** The far rail should read as the back edge of the table, not a floating artifact. With a room environment (VQ-015 fix), a wall behind it would anchor it correctly. Without it, the rail looks disconnected.
**Screenshot:** `p3_05_fresh_standard.png` — orange-gold horizontal bar spanning the full width behind the orb.
**Notes:** Partially resolves with VQ-015 room environment fix. Additionally: the rail at z=-4.1 with y=0.09 creates a step that catches light strongly. Reducing its material brightness (use `WALNUT_COLOR` not `WALNUT_LIGHT`) would reduce its visual prominence until room geometry provides context.

---

### [FINDING-VQ-017] Left and right table rails have visible gaps at corners
**Severity:** P1
**Section:** Table Rail / Table Geometry
**Observed:** Side rails (`BoxGeometry(0.3, 0.18, 9.0)` at `x=±6.2, z=0.7`) and far rail (`BoxGeometry(12.4, 0.18, 0.3)` at `z=-4.1`) do not meet at the corners — the side rail Z center is at 0.7, spanning from z=-3.8 to z=4.7. The far rail is at z=-4.1. There is a gap of ~0.3 world units at each back corner where the rails don't overlap. In the DOWN posture at the right edge of the table this gap is visible as a notch in the border.
**Expected:** Rails should form a continuous frame with no visible gaps or seams at corners.
**Screenshot:** `p3_06_down.png` — visible corner notch upper-right.
**Notes:** Fix: extend side rails by 0.3 at the far end (`BoxGeometry(0.3, 0.18, 9.3)` centered at z=0.55), or overlap the far rail ends into the side rail positions. Simple geometry fix.

---

### [FINDING-VQ-018] Battle map is a featureless dark maroon square — no map content visible
**Severity:** P1
**Section:** Battle Map
**Observed:** The felt vault (`BoxGeometry(6.2, 0.08, 4.2)`) is a solid dark maroon rectangle with no grid, no texture, no visual content. Even if the battle scroll unrolls on top of it, the underlying vault is always visible around the edges and between combat states. It reads as a dead zone — a placeholder — not a magical map surface.
**Expected:** Vision: "Completely flat 2D surface. Topographical markings. Grid." Even at rest (no combat, scroll rolled up), the map zone should suggest a surface that something interesting could happen on — perhaps a faint grid etched into the felt, or a subtle texture implying use. When the scroll unrolls, it should display actual grid content.
**Screenshot:** `p3_06_down.png` — plain dark maroon rectangle, no content.
**Notes:** Two separate issues: (1) the felt vault base has no texture — add a faint canvas-drawn grid (`ctx.strokeStyle = 'rgba(255,255,255,0.04)'`) as its material; (2) the `BattleScrollObject` scroll surface texture (`buildScrollCanvas()` in battle-scroll.ts) needs to render grid lines and some basic parchment feel, not just solid color. Both are canvas texture changes.

---

### [FINDING-VQ-019] No spawn affordance for dice — player cannot tell where to get dice from
**Severity:** P1
**Section:** Dice Bag / Dice Tower
**Observed:** The dice bag is present and clickable, but from STANDARD posture it is invisible (off-screen, player shelf not in view — see VQ-013). From DICE_TRAY posture the tray contains a d20 but there is no visual cue that: (a) you click the bag to open it and get dice, (b) you drag dice to the tower top. The tower has no opening affordance (VQ-003, still outstanding). There is no "pick up" interaction hint anywhere.
**Expected:** Vision: "Player picks up d20 from bag (or tray). Player drops d20 into dice tower." The flow bag → pick up → tower → tray should be physically obvious.
**Notes:** Resolves partially when VQ-013 camera fix lands (shelf becomes visible). VQ-003 (tower opening) still needed. Consider adding a faint glow or highlight on the bag and tower opening to reinforce affordance.

---

### [FINDING-VQ-020] Walnut grain texture not reading — table surface appears flat single color
**Severity:** P2
**Section:** Table Surface / Material
**Observed:** The `makeWalnutTexture()` function generates a 512×512 canvas with 180 grain lines and knot streaks. However in-engine at STANDARD and DOWN postures the table reads as a flat dark brown — the grain is not perceptible. The texture repeats at `(2, 1.5)` across a 12×8 world unit surface, meaning each repeat covers 6×5.3 world units — too large a scale for grain lines to register at any camera distance used.
**Expected:** Vision: "Textured plane with lighting and shadows." The table should look like wood — visible grain, depth from the PBR roughness map.
**Screenshot:** `p3_05_fresh_standard.png` — flat brown surface, no visible grain.
**Notes:** Two fixes: (a) increase texture repeat to `(6, 4)` so grain lines are denser and closer to real wood scale; (b) add a roughnessMap using a second canvas pass so PBR lighting catches the grain differently from different angles. The grain exists in the code — it just needs to tile smaller. Low-effort, high-impact.

---

### [FINDING-VQ-021] Character sheet text too small to read from any usable camera posture
**Severity:** P2
**Section:** Character Sheet
**Observed:** The character sheet canvas is rendered at `800×1100` pixels mapped onto a mesh `1.2 × 0.005 × 1.6` world units. Labels are drawn at font size 8–9px, values at 12–18px. At DOWN posture (camera at y=3.2, z=5.5 looking at z=3.8), the sheet is approximately 1.6 world units tall viewed from ~2 world units above — the rendered text is 1–2 screen pixels per character, completely unreadable. Even at maximum zoom the font is too small.
**Expected:** Vision: "Player can click spells/abilities on the character sheet to initiate actions" (accessibility path). Vision also says the sheet is readable — this is a reference document. A real character sheet held at arm's length has readable ~10pt text.
**Screenshot:** `p3_06_down.png` — character sheet visible but text illegible.
**Notes:** The 800×1100 canvas texture has sufficient resolution — the problem is the physical mesh is too small in world units and the camera is too far. Fix requires either: (a) increase mesh size (1.2×1.6 → 1.8×2.4 world units) so it occupies more of the viewport; (b) add a dedicated READ_SHEET camera posture that drops close to the sheet surface (similar to the `BOOK_READ` posture already defined in camera.ts); or (c) implement the fullscreen sheet overlay (like `handout-read-overlay`) triggered by clicking the sheet. Option (c) is most vision-aligned — physical object on table, click to "pick it up and read it."

---

### Summary of Remaining Root Problems (PM Priority View)

The build has real infrastructure — fog, tokens, scroll, notebook, crystal ball wiring are all present. The failures are presentation-layer and almost entirely in three buckets:

**Bucket 1 — Camera (blocks everything else):** STANDARD posture doesn't show the player zone. DOWN posture shows it but at an unreadable angle. Both need to be re-tuned before any other player-side polish is meaningful. Fix VQ-013 and VQ-014 first — everything else looks better once the camera is correct.

**Bucket 2 — Room context (breaks immersion):** The void background (VQ-015) and the resulting floating-artifact reads (VQ-016) are one fix — add minimal room geometry. Without it the scene reads as a tech demo, not a place.

**Bucket 3 — Player zone legibility (the "looks like trash" problem):** Even from DOWN posture the player shelf is chaotic because: the felt vault (P0, VQ-001) dominates the center at full saturation, the parchment stub (VQ-010) is an orphan, the character sheet is too bright and too close to the vault edge, and the notebook is too dark to read as the primary object. These are 3–4 targeted fixes that would transform the player side from chaos to legible.

Everything else — dice affordance, text readability, rail gaps, table texture — flows downstream from these three buckets.

---

## Pass 4 Addendum — All Four Postures, Latest Camera Build
**Date:** 2026-02-23 (fourth sweep, after camera.ts was updated)
**Screenshots:** `p3_07_standard_latest.png`, `p3_08_down_latest.png`, `p3_09_lean_forward_latest.png`, `p3_10_dice_tray_latest.png`
**Camera build at time of inspection:** STANDARD `(0, 0.75, 6.5)→(0, 0.1, 0.0)` / DOWN `(0, 2.8, 6.0)→(0, 0, 4.2)` / LEAN_FORWARD `(0, 1.2, 1.5)→(0, 0.1, -2.0)` / DICE_TRAY `(3.5, 1.2, 4.5)→(4.5, 0.08, 1.75)`

---

### [FINDING-VQ-022] STANDARD camera eye is too low — lying-on-table perspective, not seated
**Severity:** P0
**Section:** Camera
**Observed:** Updated STANDARD `(0, 0.75, 6.5)` puts the eye at y=0.75 — barely above the table surface. A seated person's eyes are approximately 1.2–1.4m above a table (~1.2–1.4 world units at current scale). At y=0.75 the foreground objects (character sheet, notebook edge, dice tray) loom huge and the camera grazes across the table surface like a drone hovering 6 inches off the floor. The orb appears small and far. The player objects dominate in a confusing way — not from the "looking at your stuff" angle but from a near-floor angle.
**Expected:** Seated eye height is y≈1.3. Camera should be pulled back further from the shelf (z≈7.5) and raised (y≈1.3) with lookAt around `(0, 0.05, 1.5)`. That gives a natural seated perspective: shelf below in the lower third, open table center in the mid-frame, orb across the table in the upper-center. This is the "sitting at a real table" view.
**Screenshot:** `p3_07_standard_latest.png` — foreground objects loom at eye level, feels like camera is on the table surface.

---

### [FINDING-VQ-023] Player objects are overlapping and spatially incoherent in DOWN posture
**Severity:** P0
**Section:** Player Shelf Layout
**Observed:** In DOWN `p3_08_down_latest.png`: the notebook is sitting visually on top of the character sheet. The notebook (`-0.2, 0.05, 4.8`) and the character sheet (`-2.0, 0.005, 4.8`) are at the same Z but the character sheet extends from x≈-3.2 to x≈-0.8 and the notebook is at x=-0.2 — they nearly touch. From the DOWN camera angle the foreshortening makes them read as stacked on top of each other, not side by side. The felt vault right edge bleeds into the shelf creating a wall. The handout slot bar at z=3.82 cuts the frame horizontally. The result is a cluttered, unreadable mess.
**Expected:** At a real table, a person's character sheet is to one side, their notebook is in front of them, and there is clear empty space between objects. Objects should have deliberate separation — at least 0.4 world units of clear table between them — so each item reads as a distinct object, not a pile.
**Screenshot:** `p3_08_down_latest.png` — notebook sits on character sheet, no clear separation, objects pile up.
**Notes:** Requires layout redesign of the player shelf. Suggested positions: character sheet at `(-3.0, 0.005, 4.9)`, notebook at `(-0.8, 0.05, 5.0)`, rulebook at `(1.5, 0.04, 4.9)`, dice bag at `(-2.0, 0.10, 5.4)`. Increases lateral spread and pushes objects deeper into shelf space so they read as distinct items from DOWN posture.

---

### [FINDING-VQ-024] LEAN_FORWARD and DICE_TRAY postures appear identical — DICE_TRAY not switching
**Severity:** P1
**Section:** Camera / Posture System
**Observed:** Screenshots `p3_09_lean_forward_latest.png` and `p3_10_dice_tray_latest.png` are visually identical. Both show the same frame: orb clipped top-left, tray center, tower right, red cube lower-right. The key binding is wired (`case '4': target = 'DICE_TRAY'`) but the canvas was losing focus between posture key presses during this test session. Likely a focus management bug — after the screenshot tool interacts with the page, the canvas loses keyboard focus, so subsequent key presses don't register.
**Expected:** Each posture key press should reliably switch posture regardless of what last interacted with the page.
**Notes:** The canvas click-to-focus workaround (`document.querySelector('canvas').click()`) resolves it in the test harness but won't exist for real users. The keydown listener is on `window` not `canvas` — this should already be focus-independent. Needs investigation: possibly another DOM element (text input bar) is capturing the key event when focused.

---

### [FINDING-VQ-025] Loose red die visible outside the dice tray — orphan geometry
**Severity:** P1
**Section:** Dice / Player Shelf
**Observed:** In LEAN_FORWARD and DICE_TRAY postures, a small red cube is visible on the bare table surface at approximately `(5.5, 0.1, 2.5)` — outside the tray bounds. This is not the d20 (which spawns at `4.5, 0.3, 1.75`, inside the tray) and not a dice bag decorative die. It reads as a stray geometry stub that has no owner.
**Expected:** No loose objects outside intended zones.
**Screenshot:** `p3_09_lean_forward_latest.png` — red cube lower-right, clearly outside tray.
**Notes:** Likely a `d6` stub from `buildObjectStubs()` — the code places several d6 decorative cubes at offsets from position `(4.5, ...)`. Check `buildObjectStubs()` d6 positions and confirm all are inside tray bounds or inside the dice bag group.

---

### [FINDING-VQ-026] LEAN_FORWARD posture still clips crystal ball — orb top cut off
**Severity:** P1
**Section:** Camera / Crystal Ball
**Observed:** Updated LEAN_FORWARD `(0, 1.2, 1.5)→(0, 0.1, -2.0)` still clips the orb. Eye at y=1.2 looking at z=-2.0 with the orb at z=-3.2, y=1.45 means the camera is looking slightly upward at the orb, which sits above the lookAt point. The orb top extends to approximately y=2.45 (center 1.45 + radius ~1.0) and fills the upper frame.
**Expected:** LEAN_FORWARD should be the "lean over the table to look at the map and orb" posture. The orb should be fully visible, ideally in the lower-center of frame with the map/battle area above it.
**Screenshot:** `p3_09_lean_forward_latest.png` — orb top-left, clipped, far rail ("gold bar") cuts across top of frame.
**Notes:** Raise camera further: `position (0, 2.0, 2.0)`, `lookAt (0, 0.2, -2.5)`. This looks down and across at the DM side with the orb in the upper-center of frame and the map below it.

---

### Honest Assessment — What "Sitting at the Table" Requires

The fundamental problem is that every posture has been tuned by trial and error rather than starting from physical reality. A real person sitting at a table:

- **STANDARD:** Eyes at ~y=1.3, body at z≈7 (behind the shelf). Looking forward at a slight downward angle. They can see their own stuff in the lower half of their vision and the far side of the table in the upper half. The shelf isn't prominent — it's just where their hands are. The orb sits across the table at mid-height.

- **DOWN (leaning to read):** They tilt their head down toward their character sheet. Eye moves to ~y=0.9, z≈6.5. Looking almost straight down at z≈4.5. The sheet fills the lower center of view. They can still see the table edges in their peripheral vision.

- **LEAN_FORWARD (studying the map):** They lean forward, chest over the table. Eye at ~y=1.0, z≈2.5. Looking forward and slightly down at the map/orb. The orb is at mid-height in their vision, not looming above them.

- **DICE_TRAY (rolling):** They turn right. Eye shifts to x≈3.5, y≈1.1, z≈5.5. Looking at the tray at z≈1.75. The tray is clearly below them, the tower is to the side.

Every posture needs to be validated against this physical description, not just coordinates on a number line.

| Item | Reason |
|------|--------|
| **Token visual quality (chips)** | `EntityRenderer` is landed and uses flat chips. Cannot assess rendered appearance without backend sending `entity_delta` events to populate the map. |
| **Fog of war visual** | `FogOfWarManager` is implemented. Cannot assess without `fog_update` events from backend. WO-UI-FOG-VISION-001 (vision-type differentiation) is wired in code. |
| **Crystal ball NPC portrait** | `CrystalBallController` handles `npc_portrait_display`. Cannot assess portrait texture rendering without backend events. |
| **Crystal ball TTS pulse** | Wired to `tts_speaking_start`/`tts_speaking_stop`. Cannot assess speak-state visual without TTS backend running. |
| **Bestiary images** | `NotebookObject` bestiary section uses progressive reveal. Image binding not wired — placeholder procedural fill. Blocked on asset pipeline WOs. |
| **Handout fanstack >5** | Cannot assess without 5+ simultaneous handout events from backend. |
| **Battle scroll unroll animation** | Correctly implemented (`onCombatStart()`/`onCombatEnd()`). Cannot assess animation quality without `combat_start` event. |
| **Character sheet live values** | `CharacterSheetController` handles `character_sheet_update`. All values currently hardcoded placeholder. Needs backend. |
| **Session zero / notebook cover** | Cover customization framework exists. No WS events defined yet. Blocked on session-zero WO. |
| **Notebook persistence** | Drawing strokes in-memory only. Blocked on WO-NOTEBOOK-PERSIST. |
| **Entity movement slide** | Lerp animation implemented in `EntityRenderer`. Cannot verify without backend movement events. |
