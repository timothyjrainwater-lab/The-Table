# UX Vision Specification: The Physical Table

**Author:** PO (Thunder) + PM (Opus)
**Source:** Whiteboard session 2026-02-12
**Status:** APPROVED (PO-directed)

---

## Core Principle

The UI is a one-to-one recreation of sitting at a real tabletop RPG table. Every interaction maps to a physical object or action that would exist at a real table. When in doubt about any UX decision, the answer is: **what would it be like at an actual real-world tabletop?**

Voice is the primary action channel. Physical object manipulation is the exception, and every exception maps to something you'd physically do at a real table.

**Minimize physical interaction to maximize immersion.** Every physical interaction we can eliminate in favor of voice or AI handling it makes the experience more immersive. If the AI can do it for you the way a DM would, it should. The player speaks intent; the system handles execution. Clicking, dragging, and manipulating objects exist only where the physical analog demands it (rolling dice, drawing in a notebook, positioning items on your side of the table).

---

## Table Layout

### Two Zones

The table has two distinct zones:

- **Player Side:** Where the player's personal objects live — notebook, character sheets, dice bag, dice tower, loose papers/handouts
- **DM Side:** Where shared/DM content appears — crystal ball (DM presence), battle map scroll, scene images, town views

### Camera

- Default view: seated at the player side, looking across the table at a slight angle
- Perspective shift: smooth camera animation to "stand up" and look down at the DM side (top-down view of battle map, scene images)
- Triggered by: physical hotkey/gesture only, NEVER by voice commands (jarring perspective changes without player physical action break immersion)
- The angled seated view should be designed so the DM side content is still comprehensible without switching perspective

---

## The Crystal Ball (DM Presence)

The AI's physical anchor on the table. Sits on the DM side.

### Behavior
- Pulses/glows when the AI speaks (TTS output)
- All AI voice emanates from the crystal ball's direction
- When an NPC speaks, their portrait image appears inside the crystal ball — distorted, swirling, like looking through magical glass
- The crystal ball is the "face" of the DM — you look at it when the AI talks, but you don't manipulate it

### NPC Display
- NPC portraits are pre-generated assets from the asset library
- Each NPC gets a permanently bound portrait and voice profile
- When the AI voices an NPC, the crystal ball displays their image and the TTS voice shifts to that NPC's voice profile
- Multiple distinct voice profiles per NPC archetype (gruff shopkeeper, nervous merchant, snarling goblin, etc.)

---

## The Notebook (Central Player Artifact)

A physical 3D book object on the player side of the table. This is the most important player object.

### Session Zero Introduction
- AI asks the player's name
- Name appears on the notebook cover
- AI asks if the player wants to customize the cover
- Player describes what they want ("unicorns and rainbows")
- Image generator creates the cover art and applies it
- This is the first demonstration of the system's creative capability, within the first minute of interaction

### Sections

1. **Personal Pages (player-managed)**
   - Freehand drawing with pen/brush tools
   - Text input
   - Image pasting (from AI-generated images or other sources)
   - Radial menu at pen tip: colors, brushes, lines, text input, eraser
   - Pages can be torn out (animation: grab corner, drag, page detaches — opposite side tears too)
   - Torn pages become loose objects on the table
   - Pages can be flipped forward/back

2. **Transcript Section (system-managed)**
   - AI conversation log — everything the crystal ball says gets transcribed here
   - Player can pull out transcript pages and lay them beside the notebook for reference
   - Accessible but not in-your-face — you flip to it when needed
   - Provides accessibility for hearing-impaired players

3. **Bestiary / Discovery Log (system-managed, progressive)**
   - Pokedex-style progressive revelation system
   - Each monster entry is a page spread:
     - Left page: image (evolves as knowledge grows)
     - Right page: text details (name, known traits, known weaknesses, encounter history)
   - Progressive knowledge states:
     - **Heard of it:** Name only, full shadow silhouette
     - **Seen it:** Basic shape, size, coloring — rough sketch image
     - **Fought it:** Combat stats observed (AC range, damage range, abilities used)
     - **Studied it:** Full entry (skill check success or multiple encounters)
   - Knowledge sources: direct encounter, NPC description, identification skill checks, feats/abilities
   - Image generator updates the entry image at each knowledge level
   - Enforces DM/player information boundary — you only know what your character has learned
   - Reward system for investing in identification skills and exploration

4. **Handout Storage**
   - Any paper the DM gives you can be "glued" into the notebook
   - Loot lists, letters, quest text, map fragments, wanted posters, shop menus
   - Player curates what goes where

### Physical Properties
- Can be opened/closed
- Cover is a customizable texture (generated at session zero)
- Cover and potentially dice can be reskinned through image generation based on player request
- Pages flip with animation
- Pages tear with animation and sound
- The old-school 80s sparkly covered notebook is the default aesthetic before customization

---

## The Dice (Physical Rolling)

### Dice Bag
- 3D mesh object on the player side of the table
- Click/tap to open (animation reveals dice inside)
- Contains the player's set: d4, d6, d8, d10, d12, d20
- Dice remain in the bag until picked up — picking one up doesn't remove it from the set (magical bag)

### Dice Tower
- 3D structure on the player side
- Opening at the top, slot at the bottom with a tray
- Player drags a die to the top opening and releases
- Die "falls through" — tumbling sound, brief delay (opaque tower, can't see inside)
- Die emerges from the bottom into the tray with the result face-up
- **The actual random number comes from the backend deterministic RNG system**
- The physics/animation is cosmetic — the result is determined by the seed
- The experience is tactile: pick up → drop in → hear tumble → see result

### Dice in Tray
- Dice sit in the tray after rolling
- Can be picked up, examined, put back
- To roll again: pick up from tray, drop back in tower
- Dice persist in tray between rolls

### Dice Reskinning
- Each die face is a texture
- Image generator can produce custom face textures based on player preference
- Swap texture map to change die appearance

### Interaction Flow
- Crystal ball: "Roll initiative"
- Player picks up d20 from bag (or tray)
- Player drops d20 into dice tower
- Die tumbles, emerges with result
- System processes the deterministic result

---

## The Character Sheet (System-Managed Display)

### Properties
- Physical paper object(s) on the table — looks like paper, not a UI panel
- Two sheets (main stat block + spell/ability reference, or player arranges as preferred)
- Player can position them anywhere on their side of the table

### Read-Only with Action Triggers
- **The system writes to the character sheet. The player reads from it.**
- All mechanical state is system-managed: stats, HP, inventory, encumbrance, gold, XP
- When loot is acquired, items automatically appear on the sheet with all math tallied
- Weight, encumbrance, currency — all computed by Box, displayed on sheet

### Action Interface (Accessibility Path)
- Player can click spells/abilities on the character sheet to initiate actions
- This is the alternative to voice for players who can't or don't want to speak
- Clicking a spell triggers the targeting flow (stencil overlay on battle map, confirm target)
- This is the accessibility fallback, not the primary interaction

---

## The Rulebook (World-Owned Reference)

A physical book object on the player side of the table, thicker than the notebook. This is the world's rulebook — generated during world compile from Layer A (behavior) + Layer B (presentation semantics), then frozen.

### Appearance
- A 3D book object, visually distinct from the notebook (thicker, different cover, more formal)
- Sits on the player side of the table alongside the notebook and character sheets
- Can be opened, pages flipped, bookmarked

### AI Navigation
- Player asks: "Where's the rule for that?" or "Show me that fire ability"
- Crystal ball (AI) opens the book to the relevant page
- Pages contain formatted rulebook entries: ability name, type, range, area, effect description, residue
- Entries are generated from mechanical behavior + world presentation semantics — not copyrighted text
- Every entry is stable within a world — looking up the same ability always shows the same page

### Player Interaction
- Player can flip through pages manually
- Player can bookmark pages for quick reference
- Player can leave the book open beside them on the table while playing
- Player can ask the AI to find entries by name, type, or effect

### Relationship to Other Objects
- The rulebook is **read-only** — the system authors it during world compile, the player reads it
- The discovery log (bestiary section of the notebook) references rulebook entries as knowledge grows
- When a player "studies" a creature or ability, the corresponding rulebook entry becomes available
- The rulebook is **world-specific** — different worlds have different rulebooks with different names and descriptions for the same underlying mechanics

---

## The Battle Map (Magical Scroll)

### Appearance
- A magical scroll that unrolls on the DM side of the table when needed
- Completely flat 2D surface — NO 3D tokens, NO 3D terrain
- Topographical markings to indicate elevation
- Animated 2D tokens for entities (generated images, not 3D models)
- Tokens slide from square to square for movement
- Spell effects are animated 2D overlays on the flat surface

### When It Appears
- Combat start: scroll unrolls (animation)
- Combat end: scroll rolls back up
- Non-combat scenes: the same DM-side space can display scene images (town view, landscape, dungeon entrance)
- The DM puts the image "on the table" — like a DM laying out a map or picture at a real table

### Fog of War
- **Highest priority visual feature**
- Implements light ranges, vision types (darkvision, low-light vision, normal vision)
- Only reveals what the player character can actually see
- Progressive revelation as player explores
- This is the primary atmospheric tool

### Dynamic Terrain
- Terrain can change during combat (fireball destroys trees, wall is breached)
- Tile swap system: each object type has tiles for each state (standing tree → fallen tree → scorch mark)
- When Box resolves terrain destruction (object HP reaches 0), the map tile swaps
- Fallen objects become difficult terrain on the map
- Object HP, hardness, and break DCs are already implemented (WO-051B Policy Default Library)

### AoE Targeting
- When player declares an area effect, a translucent stencil overlay appears on the map
- Player confirms or redirects with voice: "a little more to the left" / "yeah, that's good"
- Stencil snaps to grid squares (backend AoE rasterizer works on grid coordinates)
- Ghost stencil system already built (ghost_stencil.py)

### Map Authoring
- The AI designs and implements battle maps during world compile / session prep
- Every significant location (town, shop, tavern, dungeon room) gets a pre-authored map layout
- Maps are stored and ready — when player enters a location, the scroll unrolls with the pre-authored map
- Unexpected combat (player attacks shopkeeper) uses the pre-stashed map for that location
- Wilderness encounters use procedurally generated maps (grid-based, deterministic from seed)
- AI-generated images are the *skin* on top of the procedural grid

### Interaction
- Player does NOT directly manipulate the battle map (at a real table, you don't draw on the DM's map)
- Player moves their own token via voice ("move me toward the lion in the top left") or by dragging their token only
- System enforces movement rules — can't move further than movement speed, can't move through walls
- NO AoO warnings — if you walk through a threatened square, you get hit. You learn by getting hit. No hand-holding, no "are you sure?" This is the No Mercy doctrine.

### Combat Initiation Doctrine
- Combat is **never initiated by AI discretion**. It is triggered mechanically.
- **Hostile intent detection:** When a player declares hostile action ("I attack the shopkeeper"), the system recognizes hostile intent and transitions to combat state.
- **Combat state machine activates:** Initiative is rolled, the battle map scroll unrolls with the pre-stashed map for the current location, tokens are placed.
- **NPC response is doctrine-driven, not AI-improvised:**
  - Each NPC has a **doctrine profile** defined at world compile, based on creature INT/WIS bands
  - Low INT/WIS (animal/bestial): fight or flee based on HP threshold, no tactical coordination
  - Medium INT/WIS (humanoid): may flee, call for help, surrender, or fight tactically depending on doctrine template
  - High INT/WIS (intelligent): may negotiate, set ambushes, coordinate with allies, retreat strategically
  - The doctrine profile is **deterministic** — given the same state and the same doctrine, the NPC makes the same decision
- **NPC-initiated combat:** When an NPC's doctrine prescribes hostility (bandit ambush, guard responding to alarm), the system transitions to combat state the same way — initiative, map, tokens
- **No AI judgment in the loop:** The AI narrator describes the transition to combat. It does not decide whether combat happens. The doctrine engine and the player's declared intent are the only triggers.
- **Unexpected combat uses pre-stashed maps:** If the player attacks a shopkeeper, the shop's pre-authored map is already stored. The system doesn't need to generate a map on the fly.

---

## DM Handouts (Physical Paper Objects)

### Delivery
- When the DM gives the player information, a piece of paper slides out from the crystal ball's side of the table toward the player
- Shop menus, loot lists, quest text, letters, wanted posters, contracts, map fragments

### Interaction
- Player can pick up a handout, read it, lay it beside them on the table
- Player can glue it into their notebook for permanent storage
- Player can tear it up or drop it in the trash hole (edge of table) to discard

### Shop Interaction
- Player enters shop, talks to shopkeeper (crystal ball displays shopkeeper, AI voices them)
- Shopkeeper provides a menu — paper slides across table with item list and prices
- Player says "I want the healing potion and the rope" or clicks on items
- Selected items automatically appear on character sheet, gold deducted, weight/encumbrance updated

### Loot
- After combat or searching, DM slides a loot paper across the table
- Player selects what to take (voice or click)
- Items appear on character sheet automatically

---

## Voice Interaction (Primary Channel)

### Player Voice Input (STT)
- Declare actions: "I attack the goblin," "I cast fireball at those three"
- Ask questions: "What happened in our last session?" "What do I know about owlbears?"
- Chat with the AI: "I'm not ready to start yet, tell me about this town"
- Direct the AI: "Move me toward the lion," "Can I see that monster image again?"
- Respond: "Yeah that targeting looks good," "No, I want the other one"
- Shopping: "I want to buy the longsword and three torches"

### AI Voice Output (TTS)
- Narration comes from the crystal ball
- NPC voices are distinct per character (pre-generated voice profiles from asset library)
- DM voice is the default/base voice
- Voice shifts when AI speaks as an NPC

### Conversational AI (Outside Gameplay)
- Player can sit at the table and just talk — not every interaction is gameplay
- Ask about previous sessions (event log provides provenance)
- Ask about rules (world-owned rulebook provides answers)
- Ask about campaign lore
- Ask about alignment changes ("Why did my alignment shift?" → AI cites specific recorded events)
- Ask for images ("Show me that monster from last time" → image generation → image appears on table)
- Doodle in notebook while chatting
- "Are you ready to start?" "No, I want to chat for a bit" — this is valid and encouraged

### Text Input (Fallback)
- Available for accessibility
- Secondary to voice
- Notebook text input is primarily for player's own notes, not for commanding the AI
- A text input area exists somewhere unobtrusive for players who need it

---

## Asset Library System

### Pool-Based Rotation
- Assets are organized by category: goblin_portrait, human_merchant_portrait, forest_battlemap_tile, gruff_voice, nervous_voice, etc.
- Each category maintains a pool of N ready assets
- When an asset is used (bound to an NPC, placed on a map), it is permanently bound to that entity
- Once used, the asset is removed from the pool and a replacement generation job is queued
- Every encounter is visually/aurally unique because the pool constantly rotates
- The system generates its own asset library — no external assets required

### Generation Pipeline (Priority Queue)
1. **Critical path assets:** Must exist before session starts. Current scene map, PC portraits, guaranteed encounter monsters. These block session start.
2. **Near-term assets:** Likely needed based on AI's session plan. Next dungeon room, next encounter monsters, destination town. Generated in background during play if compute headroom exists.
3. **Speculative assets:** Nice to have. Alternative encounter maps, variant monster images, environmental details. Generated during idle time.

### Background Processing
- While game is running, unused compute resources generate queued assets
- Session N+1 prep begins during Session N if resources allow
- "Come back tomorrow" is valid — the system needs prep time, just like a real DM
- Pool replenishment happens continuously in background

### Binding Registry
- NPC_042 is permanently bound to voice_profile_17 and portrait_goblin_09
- Once bound, that asset is that NPC's identity forever
- Bestiary images are tied to knowledge level, not individual asset binds

---

## The Trash Hole

- A spot at the edge of the table (or a small hole/slot)
- Drop torn pages, unwanted handouts, or discarded items into it
- Items are deleted from the file system
- Drop zone detection with brief confirmation
- Physical, not abstract — you're tossing paper into a wastebasket, not clicking "delete"

---

## Session Zero Flow

1. Player sits down at the table. Crystal ball glows.
2. AI (crystal ball): "Welcome. What's your name?"
3. Player speaks their name.
4. Name appears on the notebook cover.
5. AI: "Do you like your notebook? Would you like a different cover?"
6. Player describes preferences.
7. Image generator creates cover art, applies it to notebook.
8. AI: "Here you go. How's that?"
9. Player confirms or requests changes.
10. Character creation begins (stats rolled with physical dice, AI guides conversationally).
11. Character sheet populates as choices are made.
12. World entry when ready.

This demonstrates the system's creative capability within the first minute of interaction.

---

## What the Player NEVER Does

- Edit their own character sheet (system-managed)
- Move enemy tokens on the battle map
- Draw on the battle map
- Touch/manipulate DM-side objects (except looking via perspective shift)
- Receive AoO warnings or "are you sure?" prompts (No Mercy doctrine)

---

## What the System NEVER Does

- Yank the camera without player physical action
- Show mercy or warn about mechanical consequences
- Display persistent on-screen text/HUD overlays
- Use traditional game UI elements (health bars, action buttons, floating menus)
- Break the physical table metaphor

---

## Technology Stack (Current Assessment)

- **Rendering:** Three.js (browser-based 3D)
- **Table surface:** Textured plane with lighting and shadows
- **Objects:** 3D meshes with canvas textures (notebook pages, character sheets)
- **Drawing:** HTML5 Canvas API mapped onto 3D surfaces
- **Battle map:** 2D canvas overlay on scroll mesh
- **Dice:** Simple 3D meshes with cosmetic animation, deterministic RNG backend
- **Voice:** STT (Whisper adapter) + TTS (Kokoro adapter) via WebSocket to Python backend
- **Backend connection:** WebSocket bridge from Three.js frontend to Python engine
- **Performance budget:** Keep 3D rendering lightweight (low-poly, limited lights) to preserve GPU headroom for local LLM/TTS models

---

*This document captures the PO's design vision as articulated during the 2026-02-12 whiteboard session. It is the north star for all UI/UX decisions. When in doubt: what would it be like at an actual real-world tabletop?*
