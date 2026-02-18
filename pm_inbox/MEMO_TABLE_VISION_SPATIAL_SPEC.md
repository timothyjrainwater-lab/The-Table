# MEMO: Table Vision — Spatial Spec & Camera Postures

**Lifecycle:** NEW
**From:** Thunder (vision), Aegis (synthesis), Slate (capture)
**Date:** 2026-02-19
**Status:** Product vision — candidate for doctrine adoption
**Reference images:** `C:\Users\Thunder\Desktop\New folder (3)\`
- `il_1140xN.2514632592_sy39.webp` — Full table overhead: dark walnut, recessed red felt vault, fold-down player stations, brass cup holders
- `il_1140xN.2514632638_f4jc.webp` — Dice tower + blue felt tray detail: peripheral ritual station
- `il_1140xN.2562297903_g930.webp` — Corner/player station detail: fold-down surface, engraved medallion
- `gamingTable_4.webp` — Digital gaming table: screen embedded in recessed vault, same rail geometry, miniatures on glass
- `EXU_Divergence_E001_TableShot_Landscape.avif` — Critical Role (Exandria Unlimited) DM perspective: warm lantern lighting, dark timber, physical clutter (sheets, dice trays, miniatures, books). This is the mood and atmosphere target. The player-to-DM spatial relationship across a working table surface.

---

## The Golden Beacon

**What would it be like to play at Matt Mercer's table?**

That's the product. Everything below — the geometry, the zones, the camera postures, the mood rules — exists to answer that question. Every design decision that doesn't serve this beacon is waste. Every feature that makes you forget you're looking at a screen is correct.

## The Core Illusion

You are not looking at a game UI. You are seated at a real, high-end gaming table in a dim, quiet library. The table itself is the interface. Everything the system can do is expressed as a physical object, in a physical place, with realistic occlusion, depth, and reach.

## The Table Geometry

The reference table (dark walnut, recessed vault, fold-down player stations) explains the trick: the play surface is recessed and the rail is thick and dominant. That creates depth for the map without needing any fantasy framing.

In a seated view, your eyes naturally catch the rail, the far end, and the recessed felt below. The map is present, but it lives down inside the table, so it never feels like a flat HUD pasted onto your face.

**Physical reference:** Board game table with fold-down player stations. Dark walnut frame, brass cup holders, recessed felt vault, separate dice tray with blue felt and wooden dice tower. Three reference photos on file.

## Zone Layout (as physical table)

| Zone | Surface | Depth | What Lives Here |
|---|---|---|---|
| **Center well** (recessed felt) | Communal | Below rail — primary shared surface | Battle map. Physically lower than the rail, reads as "at depth." |
| **Rail and corners** | Stations, not overlays | Rail height | Dice tray, handouts, tokens, cups, tools, ritual items. Peripheral affordances. |
| **Near side** (your edge) | Personal | At or below rail | Character sheet, notebook, rule book. Partly visible in STANDARD, fully readable in DOWN. Slide-out shelf or lap board feel. |
| **Far side** (across table) | DM presence | Across the well | Crystal ball focal prop. In STANDARD, attention is drawn forward like a poker player looks toward the dealer. |
| **Dice station** | Ritual object | On the rail, peripheral | Felt-lined tray with lip + wooden tower. Dice land in the tray. Bounded, tactile. Not a widget. |

## The Three Camera Postures (as embodied human motion)

### STANDARD — Sitting Posture
Slight tilt. Looking across the table. The rail dominates the near field. The map is visible but recessed. The crystal ball across the table is the primary focal anchor. You only see partial edges of your personal books and sheets. Dice station is at the periphery.

**Real-world analog:** Sitting at a poker table, looking across at the dealer.

### DOWN — Belly Posture
Looking toward your lap and the near edge of the table. The readable management view. Character sheet, notebook, and rulebook become legible because your gaze is now normal to them. This is the only posture where under-edge storage and the felt tray under the lip are visible, because your sightline crosses the table edge.

**Real-world analog:** Looking down at your own lap and the table edge in front of you.

### LEAN FORWARD — Study Posture
Leaning over the recessed well to examine the map. Approaches top-down but never becomes a perfect orthographic god-cam. The rail lip and perspective stay slightly present to preserve embodiment. Still a couple degrees off true vertical.

**Real-world analog:** Craning your neck over a real table to study the battle map.

## Mood and Realism Rules

1. **No floating UI.** Information lives on physical artifacts: paper, books, tokens, trays, printed handouts.
2. **Nothing appears out of thin air.** Things are placed, slid, handed, dropped, or printed.
3. **Occlusion is a feature.** In STANDARD you should not get full readability of everything. You get presence and edges. Full readability belongs to DOWN.
4. **The map is always a physical plane in a recessed well.** Even in LEAN FORWARD it stays slightly angled — leaning over a table, not switching to a drone camera.
5. **No perfect perpendicular.** Every camera posture maintains a couple degrees of tilt to preserve the seated-at-a-real-table feeling.
6. **Atmosphere:** Dim library, smoky, polished wood, brass fittings. High-quality poker simulator translated to D&D. Warm pools of lantern light on dark timber. The wood glows, the background fades. Physical clutter is the design language — loose sheets, pencils, scattered dice, water-stained coasters. Nothing is pristine. This is a working table, not a showroom.

## Atmosphere Reference (Critical Role / EXU Divergence)

The EXU table shot is the mood target. What it teaches:
- **Warm directional lighting** from overhead lanterns. Dark everywhere else. Faces lit, room fades.
- **Physical clutter is identity.** Character sheets loose on the table. Pencil cups. Dice trays at each station. Books stacked on the DM side. Nothing organized, everything reachable.
- **The DM side is denser.** More objects, more vertical elements (DM screen, book stacks, miniature staging area). The player side is more open — breathing room to work.
- **Wood catches light.** The polished surface reflects warm tones. This is the key material shader target for Three.js — the wood must glow under warm light, not read as flat matte.
- **The table is the room.** You don't see walls or ceiling in detail. The table and its objects ARE the environment. Everything beyond the table edge is atmosphere and shadow.

## The Player-Seat Experience (Aegis, 2026-02-19)

What makes it feel real instead of gamey:

**What you see immediately.** A wide expanse of polished wood, lit low and warm. The table surface is mostly clear where your hands want to go, but ringed with tools: trays, papers, pencils, dice, small piles of props. Across from you, other players each have their own island of character sheet space and a dice tray.

**The DM screen is the first strong visual.** A physical barrier and a stage prop. From the player side: a wall of panels and paper references. It sets the tone — there is a referee here, and the world is being run from behind that screen. In our version, this is the crystal ball zone.

**What is in front of you.** Character sheet laid flat, a pencil, maybe an eraser. Dice tray close enough to roll without reaching. You can see other people's trays and sheets but can't read them unless you lean. The center stays open so shared focus can snap there fast.

**What you can touch and how it feels.** Wood, everywhere. Smooth rail, solid weight. Paper that rustles. Dice that clack. A tray that catches the roll and keeps it contained. You are not clicking UI elements. You are handling objects with friction, sound, and minor resistance.

**The hand triangle.** Your hands naturally live in a triangle: sheet, dice tray, pencil. This is the ergonomic anchor of the player station.

**What makes it feel real.** Nothing floats. Everything has a place. The shared space is deliberately clean, so when the DM places something, it matters. The table itself is the interface: **posture changes what you can see, reach changes what you can do, and attention changes what feels important.**

## What This Means for Existing UI Code

The current Three.js scene (UI Phases 1-4) has zone contracts, drag-drop, dice handshake, and protocol formalization — all gate-tested. But the spatial layout and atmosphere have not been visually validated against this vision. The scene may have placeholder positions that don't match the recessed vault model.

**Required visual pass:** Thunder inspects the running client against this spec. Findings become the basis for a UI spatial polish WO.

---

*"You sit at a polished table in a dim library. The DM is across from you as a crystal ball presence. The battle map lies down in the table well. Your books and sheet are near you, partly visible unless you look down. Dice live in a corner station with a tower and felt tray. Camera changes are not 'modes' but natural shifts of posture."* — Aegis synthesis, 2026-02-19
