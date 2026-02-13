# Table Surface UI Specification
## The Digital D&D Table — Object Inventory, Interaction Model, and Window Behavior

**Document Type:** Design Specification
**Document ID:** TS-UI-001
**Version:** 1.0.0
**Status:** BINDING
**Date:** 2026-02-11
**Authority:** Thunder (Product Owner) + Opus (Acting PM)
**Source:** Whiteboard Session 002 (WHITEBOARD_SESSION_002_DECISIONS.md)
**Related:** TABLE_METAPHOR_AND_PLAYER_ARTIFACTS.md (superseded where conflicting)

---

## 1. Foundational Principle

**"There is no user interface. There are only D&D objects on a table."**

Every interaction the player has is with a physical object on a table surface. No menus, no toolbars, no modal dialogs, no settings panels, no status bars. The table IS the interface. If an interaction doesn't exist at a real D&D table, it doesn't belong here.

**Test for every design decision:** Does this happen at a real D&D table? If yes, we already know how it works. If no, it doesn't belong.

---

## 2. Window Behavior

### 2.1 Window Opens Small

The application opens as a small window. Not fullscreen. Not maximized. Small.

**Rationale:** You're approaching a table. You don't walk into a room and the table fills your vision. You walk up. You pull up a chair. You lean in.

### 2.2 No Maximize Button

The window has:
- **Minimize** — table goes to the side, processing continues in the background
- **Close** — shut it down
- **NO maximize button** — the player expands the window themselves by dragging edges

**Rationale:** You approach the table. You don't become the table.

### 2.3 Expansion Reveals, Not Scales

When the player expands the window:
- Objects on the table DO NOT grow larger
- The view pulls back to reveal MORE table surface
- It's like pulling back a camera — you see more area, objects stay the same size
- This is the player choosing how much table they want to see — their "spot" at the table

### 2.4 Minimize Behavior

When minimized:
- Processing continues (campaign prep, image generation, etc.)
- A progress indicator may appear on the minimized window/taskbar icon
- This is the ONE place where OS-level UI conventions are acceptable (progress bar)
- The progress bar exists OUTSIDE the table metaphor — you've closed the gate to the table

### 2.5 Object Position Persistence

- Where the player places objects on the table is saved between sessions
- When the player returns, their table looks exactly as they left it
- Character sheet on the left, notebook on the right? That's how it stays.

---

## 3. Interaction Model

### 3.1 Two-Phase Activation

All activatable objects on the table use a two-phase system:

**Phase 1: Physical Manipulation**
- Single-click and drag to pick up, move, nudge objects
- This is spatial organization — rearranging your table
- No functional side effects

**Phase 2: Functional Activation**
- Hold the object + press activation key to trigger its function
- This is deliberate — you meant to open it
- Prevents accidental activation while maintaining tactile interaction

**Objects that use two-phase activation:**
- Dice Bag (move vs. open)
- Notebook (move vs. open to read/draw)
- Tome (move vs. open to read)
- Settings Gemstone (move vs. open settings)

**Objects with implicit activation:**
- Dice Tower (dice dropped in automatically trigger roll)
- Cup Holder (object dragged in automatically stores/deletes)
- Chat Area (always active, typing into it is the activation)

### 3.2 Physics System

Physics simulation applies to a focused set of objects. This is NOT a full physics engine — it's targeted simulation for tactile feel.

**Full physics (the primary tactile layer):**
- Dice — rolling, tumbling, bouncing, resting. This is the ONE place where simulation really matters.
- Dice in the dice tower — tumbling down the tower into the tray

**Light physics (enough to feel real):**
- Books — page turning, weight when picked up/set down
- Dice bag — slight give when moved, opens with a pull
- Parchment — light, can be slid around, slight flutter
- Settings gemstone — small, nudge-able, rolls slightly

**No physics (fixed or structural):**
- Cup holder (fixed position, corner of table)
- DM's area (fixed, far side of table)
- Chat area (fixed, side of window)
- Table surface itself

### 3.3 Zoom (Accessibility)

**Mouse scroll wheel zooms individual objects on the table.**

- Scroll while hovering over the Notebook → Notebook gets bigger/smaller on the table
- Scroll while hovering over the Tome → Tome gets bigger/smaller
- Scroll while hovering over the character sheet → sheet gets bigger/smaller
- This IS the accessibility system — no font settings panel, no accessibility menu
- "The book gets bigger in your face" — zoom the object, not the text

**Zoom while hovering over empty table space → camera zoom (reveals more/less table area)**

---

## 4. Table Object Inventory

### 4.1 Dice Bag

**Type:** Container, Physics-enabled, Two-phase activation
**Description:** A leather-style dice bag sitting on the table. Contains the player's dice set.
**Interactions:**
- Move/nudge (Phase 1)
- Open to access dice (Phase 2 — hold + activate)
- Pull dice out of bag onto table
- Return dice to bag

**Behavior:**
- When open, dice are visible inside/spilling out
- Provides organized storage so dice aren't scattered everywhere
- Bag stays where the player places it

---

### 4.2 Dice Set

**Type:** Physics-enabled (PRIMARY), Fiddle-able
**Description:** Standard polyhedrals (d4, d6, d8, d10, d12, d20, percentile). These are the most physically simulated objects on the table.
**Interactions:**
- Pick up, set down, nudge, roll between fingers
- Drop into dice tower to trigger a roll
- Return to dice bag for storage

**Behavior:**
- Full physics simulation — these need to feel real
- Can be fiddled with on the table surface (idle behavior the DM notices)
- After rolling (via tower), dice rest in the tower tray
- Personalization: dice appearance can be generated by the image generator

---

### 4.3 Dice Rolling Tower

**Type:** Physics-enabled (minimal), Roll trigger, Contains tray
**Description:** A standard dice rolling tower. Drop dice in the top, they tumble down, land in the tray.
**Interactions:**
- Drop dice into the top → triggers roll → dice tumble to tray
- View dice results in tray

**Behavior:**
- This IS the "roll button" — but it doesn't feel like a button
- Dice dropped in the tower are rolled, resolved, and rest in the tray
- Tray keeps results visible and organized
- The tower exists because "when do you roll dice? When you drop them in the tower."
- No click-to-roll, no shake-the-screen — deliberate physical action

---

### 4.4 Notebook

**Type:** Container (pages), Physics-enabled, Two-phase activation, Persistent
**Description:** The player's personal notebook. Freeform drawing and writing space.
**Interactions:**
- Move/nudge (Phase 1)
- Open to read/draw (Phase 2)
- Turn pages
- Insert parchment (drag parchment onto open notebook → becomes a page)
- Remove parchment (rip out a page / remove an insert)
- Use parchment as bookmark (tuck into a page edge)
- Draw on cover

**Behavior:**
- Cover displays player's name (set during first interaction)
- Cover is drawable — player personalization
- Cover can be generated/customized via image generator
- Pages are infinite
- Accepts parchment inserts from the DM (generated images)
- Content persists across sessions
- DM notices when player is using the notebook ("Taking some notes?")

**First interaction sequence:**
1. DM: "Hi. My name is [DM name]. What's yours?"
2. Player provides name
3. Name appears on notebook cover
4. Player can immediately draw on the cover if they want

---

### 4.5 Tome

**Type:** Container (pages), Physics-enabled, Two-phase activation, Vault-backed
**Description:** The authoritative reference book. Contains the Rulebook (Player's Handbook) and Bestiary sections.
**Interactions:**
- Move/nudge (Phase 1)
- Open to read (Phase 2)
- Turn pages
- Search (DM-navigated or player can browse known sections)
- Insert parchment (generated images become pages)
- Remove parchment (pull inserts back out)
- Use parchment as bookmark

**Behavior:**
- **Rulebook section:** Vault-backed (reads from Obsidian markdown of PHB). Searchable. Player can browse rules they've encountered.
- **Bestiary section:** Progressive discovery. Monster entries appear only after combat encounter or successful Knowledge check. Pre-generated images indexed during prep time.
- Accepts parchment inserts (images DM has generated and shared)
- Content is authoritative — what's in the Tome is [BOX]-sourced or discovery-gated

---

### 4.6 Character Sheet

**Type:** Physics-enabled, Always readable, IS the action bar
**Description:** Standard D&D 3.5e character sheet matching the WotC template. This is the player's interface for abilities and spells.
**Interactions:**
- Move/nudge (spatial arrangement)
- Always readable (no two-phase — the sheet is always "open")
- Click spells/abilities (secondary combat input mode)
- View all character stats, inventory, conditions in real-time

**Behavior:**
- Live-updating via Box event stream (HP changes, conditions applied/removed, spell slots used)
- Spells and abilities listed on the sheet are clickable
- Clicking a spell initiates the "lean up to map" flow for targeting
- This carries the weight of all UI interface — no separate hotbar or cast bar
- Template matches WotC 3.5e PDF format for familiarity

---

### 4.7 Settings Gemstone

**Type:** Physics-enabled (light), Two-phase activation
**Description:** A small red gemstone sitting on the table. Opens settings when activated.
**Interactions:**
- Move/nudge (Phase 1)
- Hold + activation key → opens settings (Phase 2)

**Behavior:**
- Fantasy-themed — no gear icon, no hamburger menu
- Small, unobtrusive, doesn't dominate the table
- Settings include: audio preferences, voice settings, display preferences, account
- Settings panel appears as an in-world overlay (not a system dialog)

---

### 4.8 Parchment (Generated Images)

**Type:** Physics-enabled (light), Table object, Insertable
**Description:** Generated images appear as pieces of parchment on the table. Fantasy-themed.
**Interactions:**
- Move around the table
- View (look at the image)
- Insert into Notebook (drag onto open notebook → becomes a page)
- Insert into Tome (drag onto open tome → becomes a page)
- Use as bookmark (tuck into a page of an open book)
- Remove from book (rip back out)
- Discard (drag to cup holder)

**Behavior:**
- When the DM generates an image (or player requests one), it appears as parchment on the table
- Not a floating JPEG, not a lightbox, not a modal — a physical piece of paper
- Multiple parchments can accumulate on the table
- DM can share preview parchments during prep: "Hey, want to see what I just made?"
- Some parchments may be temporary (DM shows then takes back): "Nope, you can't have this one"

---

### 4.9 Cup Holder (Soft Delete Zone)

**Type:** Fixed position, Drop target, Recycle bin
**Description:** A recessed cup holder at the corner of the table. Drag objects in to declutter.
**Interactions:**
- Drag objects into it (parchment, loose items)
- Open to retrieve discarded items (if needed)

**Behavior:**
- Not a trash can — no trash can icon
- Items dragged in are removed from the table surface but NOT permanently deleted
- Functions as a recycle bin — items can be retrieved
- Prevents table clutter while avoiding permanence anxiety
- Fixed position — always in the same corner

---

### 4.10 DM's Area

**Type:** Fixed position, Restricted, Contains battle map
**Description:** The far side of the table. The DM's workspace. The player can see it but can't reach into it.
**Interactions:**
- "Lean up" to view (keybind or gesture shifts view to DM area)
- Come back to your spot (reverse the lean)
- During combat: interact with the battle map while leaned up

**Behavior:**
- The DM's area is where the battle map scroll lives
- The player can't manipulate objects in the DM's area
- The "lean up" mechanic shifts the player's view — like physically leaning forward at a table
- Transition can be triggered by: keybind, DM invitation ("Ready to see the map?"), or clicking a spell on the character sheet (auto-lean for targeting)

---

### 4.11 Battle Map Scroll

**Type:** DM-controlled, Contains battlefield, Fog of war
**Description:** A scroll that the DM unrolls to reveal the battlefield during combat.
**Interactions:**
- Observe (player views the map when leaned up)
- Move token (voice command to DM, or direct click-drag in secondary mode)
- Target abilities (after clicking spell on character sheet)
- View fog of war boundaries

**Behavior:**
- The DM unrolls the scroll for "roll initiative" moments
- Minimal graphics: circles for creatures, grids for squares, simple shapes for objects
- Fog of war enforced by the Box: player sees only what their character can see
- Elevation notation visible on terrain (topographic-style markers)
- Environment objects visible as simple shapes with labels
- Dynamic: objects can be added, destroyed, moved during combat
- The Spark can modify the map (add terrain, update conditions)
- AoE templates visible as overlays (radius circles, cone shapes, line rays)
- DM coordination: DM shows effect area, player confirms placement

**Detailed specification:** See `BATTLE_MAP_AND_ENVIRONMENTAL_PHYSICS.md`

---

### 4.12 Text Chat Area

**Type:** Fixed position, Always active
**Description:** The conversation with the DM. Located on the side of the window.
**Interactions:**
- Type messages to the DM
- Read DM responses
- Scroll through conversation history
- Voice input (speak instead of type — STT)

**Behavior:**
- Always visible (not hidden behind a tab or menu)
- Simple, unobtrusive — on the side, not dominating
- Supports both text input and voice input
- DM responses appear here (narration, dialogue, mechanical results)
- Provenance labels visible on mechanical content ([BOX], [NARRATIVE], etc.)
- Basic readability controls (zoom applies to this area too)

---

## 5. DM Presence System

### 5.1 Behavioral Cue Streaming

The table surface streams behavioral signals to the Lens, which includes them in Spark context when appropriate:

| Player Behavior | Signal to Lens | Possible DM Response |
|----------------|----------------|---------------------|
| Drawing in notebook | `PLAYER_DRAWING` | "Taking some notes?" |
| Fiddling with dice | `PLAYER_IDLE_DICE` | (Comfortable silence, or gentle prompt) |
| Moving notebook around | `PLAYER_ARRANGING` | "Getting organized?" |
| Idle on table surface | `PLAYER_IDLE` | "Everything okay?" / "Ready to continue?" |
| Reading the Tome | `PLAYER_READING_TOME` | (Leave them alone — they're studying) |
| Zooming into character sheet | `PLAYER_REVIEWING_SHEET` | "Checking your spells?" |
| Long pause in chat | `PLAYER_THINKING` | (Patient silence — good DMs wait) |

**These are NOT interrupts.** The DM uses judgment (Spark + player model) about when to speak and when to let silence be. A good DM knows when to engage and when to let the player think.

### 5.2 Pre-Session Space

When the player opens the application:

1. DM greets the player (uses session continuity from the Lens)
2. DM asks: "Are you ready for a session?"
3. Player can say **YES** → session begins
4. Player can say **NO** → pre-session space is active

**In pre-session space, the player can:**
- Chat with the DM about anything (rules questions, story recap, alignment discussion)
- Read the Player's Handbook (Tome)
- Sketch in the Notebook
- Look at previously generated images
- Review their character sheet
- Just exist at the table

**The DM is present and conversational during pre-session.** This is not a loading screen or a waiting room. This is sitting at the table before the game starts — which is often the best part.

### 5.3 Prep Time Behavior

When the DM is preparing a campaign (Spark generating content):

- Player stays at the table (does not need to leave)
- Player can use any table object (read, draw, fiddle with dice)
- DM can tease: "Hey, want to see what I just made?" (shares a preview parchment)
- DM can chat: "Oh, this battle is going to be fun. I've got something in store."
- DM can take time: "Give me a moment, I want to draw this up for you."
- No loading screens — DM personality masks system latency
- If the player minimizes, a progress indicator appears on the minimized window

---

## 6. Combat Interaction Flow

### 6.1 Initiative Transition

1. DM narrates the encounter trigger
2. DM says "Roll initiative" (Matt Mercer moment)
3. Battle map scroll unrolls in the DM's area
4. Player's view optionally shifts to see the map (lean-up, or DM invites)
5. Fog of war active — player sees only what their character sees
6. Content loads progressively behind the fog

### 6.2 Primary Combat Input (Voice/Text)

1. Player tells the DM what they want to do: "I cast fireball at the group of goblins"
2. DM (Spark) interprets intent via Lens
3. Lens translates to canonical intent for the Box
4. If targeting needed, DM shows the AoE overlay on the map
5. DM confirms: "This covers goblins 1, 2, and 3. Goblin 4 is just outside. Drop it here?"
6. Player confirms
7. Box resolves (rolls, damage, saves)
8. Spark narrates the result
9. Map updates (damage markers, removed creatures, terrain changes)

### 6.3 Secondary Combat Input (Click)

1. Player clicks a spell on their character sheet
2. View automatically shifts to "lean up" on the battle map
3. Player sees AoE template attached to their cursor (radius, cone, line)
4. Player clicks to place the effect
5. Box resolves
6. Spark narrates
7. Player can come back to their spot

### 6.4 Movement

**Primary:** "I want to move up behind the pillar" → DM moves the player's token → "Like this?" → Player confirms

**Secondary:** Click-drag token on the map → Box validates movement (speed, difficult terrain, AoO triggers) → Box highlights any mechanical consequences ("This provokes an AoO from the orc")

---

## 7. Non-Goals

This specification does NOT cover:
- Battle map mechanical rules (see `BATTLE_MAP_AND_ENVIRONMENTAL_PHYSICS.md`)
- Audio/voice pipeline (separate spec)
- Image generation pipeline (separate spec)
- Network/multiplayer (solo-first — future milestone)
- Internal settings panel layout (deferred to implementation)

---

## 8. Governance

- This specification is **BINDING** as of 2026-02-11
- Amendments require Product Owner (Thunder) approval
- Implementation must conform to both this spec and the Table Metaphor principle
- Where this spec conflicts with `TABLE_METAPHOR_AND_PLAYER_ARTIFACTS.md`, this spec takes precedence (it is more recent and reflects direct Product Owner whiteboarding)

---

## END OF TABLE SURFACE UI SPECIFICATION

**Date:** 2026-02-11
**Authors:** Thunder (Product Owner), Opus (Acting PM)
**Status:** BINDING
