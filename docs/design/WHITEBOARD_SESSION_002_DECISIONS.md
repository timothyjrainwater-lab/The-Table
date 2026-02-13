# Whiteboard Session 002 — Decision Log
## PM (Thunder) + Opus (Acting PM) — Architecture & UI Deep Dive

**Document Type:** Decision Record
**Status:** BINDING (Product Owner decisions captured verbatim)
**Date:** 2026-02-11
**Session Participants:** Thunder (Product Owner), Opus (Acting PM)
**Context:** Flow-state whiteboarding session following design archaeology of 7 golden egg documents. Thunder corrected multiple GPT hallucinations and established fundamental architectural and UI decisions.

---

## PART 1: FOUNDATIONAL CORRECTIONS

### Decision FC-01: Skin Packs Are Not Real
**Status:** BINDING
**Source:** Thunder (verbatim)

The "Skin Pack" concept from the GPL document was a GPT hallucination / translation error. Thunder's actual intent:

- The DM can call anything whatever it wants because the engine uses canonical IDs
- A crossbow can be called a "laser blaster" — that's just narration, not a "skin pack"
- Dice can be reskinned by the onboard image generator — personalization, not imports
- **"There's no skin packs. I don't know where skin packs came into this."**

**Action:** All Skin Pack schema, validation, sandboxing, and import requirements (REQ-GPL-014, 015, 050, 057, and related) are INVALIDATED. The underlying canonical ID / presentation separation principle remains valid.

---

### Decision FC-02: Nothing From Outside Goes In
**Status:** BINDING (Holy Doctrine)
**Source:** Thunder (verbatim)

**"The whole construct of this entire thing is that nothing from the outside needs to go in ever at all for any reason. It is the holy doctrine."**

- No imports of any kind: no Skin Packs, Language Packs, Voice Packs, Adventure imports
- Everything generated internally is original and the player's own
- The system is self-contained — the LLM generates all content

**Action:** All import/extensibility requirements (REQ-GPL-035–039, 054, 062) are INVALIDATED. GAP-03 from the Master Requirement Register is dissolved.

---

### Decision FC-03: Language Packs Are Not Real
**Status:** BINDING
**Source:** Thunder (verbatim)

Language Packs were another GPT overengineering artifact. The real intent:

- The DM can rename anything because the engine uses canonical IDs
- "Reskinning" is just the DM telling any story it wants with the canonical bricks
- This is inherent in the architecture, not a separate "Language Pack" feature

**Action:** All localization infrastructure requirements (REQ-CDR-039, CDR-041, GPL-025, GPL-026, GPL-065) are INVALIDATED as standalone systems. The canonical ID architecture already provides this capability natively.

---

### Decision FC-04: Knowledge Homes Are Already Solved
**Status:** BINDING
**Source:** Thunder (verbatim)

D&D solved the knowledge location problem 50 years ago:

- **Tome** = authoritative reference (rules, spells, monsters — things learned through play)
- **Notebook** = player memory (session notes, NPC names, quest details — things you wrote down)
- **"Where does the knowledge about the thieves guild come in? Well, that's what the notebook is for. Because you wrote it down. Or you didn't."**
- DM should prompt: "That seems important, want me to put that in your notebook?"

**Action:** Knowledge location gaps (GAP-PA-01 through GAP-PA-04) are resolved by the existing Notebook/Tome model. No new systems needed.

---

### Decision FC-05: Accessibility Is Built Into the Metaphor
**Status:** BINDING
**Source:** Thunder (verbatim)

**"The book gets bigger in your face. Mouse scroll wheel makes the entire object bigger. Done."**

- No font settings panel, no accessibility control panel
- Zoom is applied to physical table objects — the book gets bigger because you're looking at it closer
- Text chat window on the side with basic readability
- Accessibility is a natural consequence of the table metaphor, not a bolt-on system

**Action:** Dedicated accessibility task items (ACC-01, ACC-02) are dissolved. Accessibility is an inherent property of the table surface zoom mechanic.

---

### Decision FC-06: The Roadmap Is Trash
**Status:** BINDING
**Source:** Thunder (verbatim)

**"Yes, the road map is trash. That's why we're taking this time now to readjust before absolutely messing everything up."**

- Current roadmap (AIDM_EXECUTION_ROADMAP_V3.md) needs complete rework from scratch
- Thunder is bringing Opus in as PM to redefine the roadmap
- All milestone structures are subject to change

**Action:** Complete roadmap rewrite is required. Current V3 is retained as historical reference only.

---

## PART 2: SPARK / LENS / BOX ARCHITECTURE

### Decision SLB-01: The Lens Is the Product
**Status:** BINDING
**Source:** Thunder + Opus (collaborative)

- The Box is done (2003 tests passing, deterministic engine built)
- The Spark is a commodity (rent an LLM, configure it)
- **The Lens is what we're actually building**
- The Lens is the biggest weakness right now — needs in-depth tiered scaffolding

---

### Decision SLB-02: The Crystal Ball Metaphor
**Status:** BINDING
**Source:** Thunder (verbatim)

**"I want you to think of this as a crystal ball. A magical crystal ball where the intelligence lives beneath the glass."**

- Players touch the outside of the lens — their contact shapes it
- The intelligence (Spark) lives beneath the glass
- The Lens is the glass surface — transparent, shaped by both sides, owned by neither

---

### Decision SLB-03: Rigorous Three-Way Separation
**Status:** BINDING (Reinforces existing doctrine)
**Source:** Thunder (verbatim)

**"The lens has no contact with what the box is. The lens just focuses the spark. And the spark operates the box through the lens."**

- Box guards itself — validates its own rules, its own math
- Lens ONLY focuses the Spark — context assembly, player model, campaign memory, alignment tracking
- Spark operates the Box THROUGH the Lens
- The Spark never talks to the Box directly. The Box never talks to the Spark directly.

---

### Decision SLB-04: Box Provides Go/No-Go Options to Lens
**Status:** BINDING
**Source:** Thunder (verbatim)

**"The box needs to present solid go/no-go options that are available so that the lens can present the spark with its appropriate context window."**

- The Box advertises valid actions, available abilities, mechanical constraints
- The Lens uses these options to build focused context for the Spark
- This filtration prevents Spark overload — the Spark doesn't see the entire universe of possibility
- The information flow: Box advertises → Lens filters → Spark receives focused context

---

### Decision SLB-05: Lens Is Stateful (Doctrine Amendment)
**Status:** BINDING (Amends existing doctrine definition)
**Source:** Thunder (verbatim) + Opus analysis

The existing doctrine defines the Lens as "stateless presentation logic." Thunder's whiteboarding reveals the Lens is significantly more than that. The Lens:

- Keeps track of the campaign
- Keeps track of session notes
- Keeps track of what happened yesterday, a year ago, 10 years ago
- Needs a very structured and rigorous logging, documenting, indexing, and searchable record history
- Holds the alignment tracker (constant tracking, constant measurement, evaluation)
- Holds the player model
- Assembles context windows for the Spark

**"That lens system is what's like keeping track of the campaign. It's keeping track of the session notes. It's keeping track of what happened yesterday, a year ago, 10 years ago. It needs to have a very structured and rigorous logging documenting indexing and searchable record history so that the LLM is never overpowered."**

**Doctrine impact:** The LENS definition in `SPARK_LENS_BOX_DOCTRINE.md` must be amended to reflect that the Lens is a stateful focus system, not stateless presentation logic. The trust/authority separation principles are preserved — the Lens still cannot invent mechanical authority — but it is now understood to be the data membrane between Spark and Box.

---

### Decision SLB-06: Spark Feeds World-Knowledge to Lens
**Status:** BINDING
**Source:** Thunder (verbatim)

**"At any point in time there might be missing gaps in the calculations for the box. The box isn't going to know the height of the table."**

- The Spark knows the world — it knows a tavern table is 3 foot 6
- The Box knows the rules — it knows what 3 foot 6 means for cover calculations
- The Lens holds the data so they never have to talk to each other directly
- The Spark writes world-knowledge to the Lens. The Box reads it from the Lens.

Flow:
1. Spark generates scene → creates world-knowledge (object dimensions, materials, positions)
2. Lens captures, structures, indexes this data
3. Box queries the Lens when it needs physical properties for mechanical resolution
4. Spark can point the Box to the position on the Lens for the information it needs

**"The lens needs to be that barrier that keeps the balance between the spark and the box... the spark is creating something, the lens in itself is holding in all that data and information that's categorized, indexed and labeled. So when the box calls on that, it can easily grab it as it's needed."**

---

## PART 3: WINDOW & TABLE SURFACE

### Decision UI-01: Window Starts Small
**Status:** BINDING
**Source:** Thunder (verbatim)

- The application does not open full screen
- It starts as a small window on purpose — you're approaching a table
- **No maximize button** — the player expands it themselves
- When expanded, the content doesn't scale up — it reveals more table surface
- Objects inside maintain their size; you're pulling the camera back to see more table

**"I don't want a maximize button. I want the player having to expand it themselves. And when they do expand that window, I don't mean that everything inside the window just gets larger and fills in. I want it to be able like it's pulling back and just exposing more surface table."**

---

### Decision UI-02: Minimize Exists, Maximize Does Not, Close Exists
**Status:** BINDING
**Source:** Thunder (verbatim)

- **Minimize** — table goes to the side, processing continues. This is where a progress bar may live (outside the table metaphor). When minimized, you've closed the gate to the table, so OS-level UI conventions are acceptable.
- **Close** — shut it down
- **No maximize** — never. You approach the table, you don't become the table.

---

### Decision UI-03: The DM Is Always Present
**Status:** BINDING
**Source:** Thunder (verbatim)

The LLM receives behavioral cues about everything the player is doing on the table surface:

- Drawing in the notebook → DM might say "Taking some notes?"
- Fiddling with dice → DM notices
- Idle on the table surface → DM can engage
- Moving the notebook → DM might say "Oh, are you working on something?"
- Reading the Player's Handbook → DM knows the player is studying

**"There needs to be a streamlined connection to all of the actions that the player is interacting with, whether he's drawing, whether he's fiddling with the dice... the LLM is getting prompts and cues about what the player is doing."**

This is presence, not surveillance. The DM is at the table with you.

---

### Decision UI-04: Pre-Session Space Is Sacred
**Status:** BINDING
**Source:** Thunder (verbatim)

When the player opens the application:

1. DM greets them: "Are you ready for a session?"
2. Player can say **NO** — and that's fine
3. Player can sit at the table and:
   - Ask questions about rules
   - Recap last session's events
   - Discuss story elements
   - Challenge alignment changes ("Hey DM, you changed my alignment. Why?")
   - Have a coherent back-and-forth discussion
   - Read their Player's Handbook
   - Sketch in their Notebook
   - Just hang out

**"The player can sit there and just interact with the DM, whether they're asking questions about the rules, whether they're just kind of recapping a story or maybe they're just sharing a conversation about specific events."**

The DM must be able to reference evidence: "Well, you did this at that point. You did this at that point. That's pretty [clear]." — requiring the alignment evidence chain from the Lens.

---

### Decision UI-05: First Interaction
**Status:** BINDING
**Source:** Thunder (verbatim)

**"The very first prompt that has to come out is: 'Hi. My name is [DM name]. What's yours?'"**

- When the player gives a name, that name appears on the cover of their Notebook
- Player can draw on the Notebook cover
- This is persistent — the first assertion of ownership
- This is the onboarding moment

---

### Decision UI-06: No Fixed Object Positions
**Status:** BINDING
**Source:** Thunder (verbatim)

- There are no set spots for anything on the table
- The player arranges objects wherever they want
- Character sheet on the left, notebook on the right — or vice versa
- Positions are persistent between sessions
- The window expansion gives you your "spot at the table"

**"There's no dedicated area... the spots that you make are what presents."**

---

## PART 4: TABLE OBJECTS

### Decision TO-01: Dice Bag
**Status:** BINDING
**Source:** Thunder (verbatim)

- A container object on the table
- Pull it open, take dice out
- Not all dice everywhere all the time — organized storage
- Physics-enabled (you can nudge it, move it)

---

### Decision TO-02: Dice Physics
**Status:** BINDING
**Source:** Thunder (verbatim)

- Dice are the ONE place where physical simulation matters
- You can fiddle with dice on the table — pick them up, set them down, nudge them around
- This is the tactile element
- Low overhead, but it needs to feel real enough
- Physics also applies to: books (page turning), the gemstone, moving objects around the table

**"If the only thing in this whole thing is like super physical, it's the dice physics."**

---

### Decision TO-03: Dice Rolling Tower
**Status:** BINDING
**Source:** Thunder (verbatim)

- The roll trigger is the dice tower — drop dice in the top, they tumble down, land in the tray
- You don't click dice and they scatter randomly — that's "nonsensical and whimsical"
- The tower IS the "roll button" but doesn't feel like a button
- Dice stay in the tray until you're ready for them again — table stays clean

**"When do you roll the dice? When you drop them in the dice rolling tower."**

---

### Decision TO-04: Notebook
**Status:** BINDING (Extends TABLE_METAPHOR spec)
**Source:** Thunder (verbatim)

- Player-owned, freeform drawing/writing space
- Pages accept parchment inserts (images from the DM)
- Parchment can be used as bookmarks
- Parchment can be ripped back out
- Cover shows player's name (from first interaction)
- Cover is drawable — player personalization
- Cover can be generated by the image generator
- Infinite pages
- Persistent across sessions

---

### Decision TO-05: Tome
**Status:** BINDING (Extends TABLE_METAPHOR spec)
**Source:** Thunder (verbatim)

- Vault-backed reference book
- Rulebook section (Player's Handbook pages, searchable)
- Bestiary section (progressive discovery gated by combat/Knowledge checks)
- Accepts parchment inserts (images from the DM)
- Pre-generated images categorized and indexed by the DM during prep time

---

### Decision TO-06: Character Sheet Is the Action Bar
**Status:** BINDING
**Source:** Thunder (verbatim)

- No separate hotbar, ability tray, or MMO-style cast bar
- The character sheet IS the interface for abilities and spells
- Spells listed on the sheet are clickable (secondary input mode)
- The character sheet carries the weight of all UI interface

**"The character sheet is our cast bar because we do have to think about accessibility... it handles in phases, goes back to the character sheet holding the weights of all of the UI interface because it's already there."**

---

### Decision TO-07: Settings Gemstone
**Status:** BINDING
**Source:** Thunder (verbatim)

- Settings is a small red gemstone on the table
- Physics-enabled (you can nudge it, pick it up, move it around)
- Two-phase activation: you can pick it up and move it (physical), but to open settings you must hold it and press an activation key
- No gear icon, no hamburger menu — a fantasy-themed table object

**"It's a gemstone, right? Like it's just a small red gemstone, again physics enabled."**

---

### Decision TO-08: Two-Phase Activation System
**Status:** BINDING
**Source:** Thunder (verbatim)

All activatable table objects use a two-phase system:

1. **Physical manipulation** — pick up, move, nudge (single action)
2. **Functional activation** — hold the object + press activation key (deliberate two-step)

This prevents accidental activation while maintaining tactile feel. Applies to: gemstone (settings), dice bag (open), books (open to read vs. just move).

**"You could pick it up, you can move the setting button around, but you have to hold it and then hit the activation button for it to trigger. Kind of a two-phase system just to make sure that we're not breaking anything there."**

---

### Decision TO-09: Parchment (Generated Images)
**Status:** BINDING
**Source:** Thunder (verbatim)

- When the DM generates an image (or the player requests one), it appears as a piece of parchment on the table
- Fantasy-themed — not a floating JPEG, not a lightbox
- Parchment is a physical table object — moveable, arrangeable
- Can be filed: drag into Notebook (becomes a page), drag into Tome (becomes a page)
- Can be ripped back out of a book
- Can be used as a bookmark (tuck into a page)
- DM can share preview parchments during prep: "Hey, want to see what I just made?"

**"The player can ask for it. 'Hey, can you create me an image of this?' And then we can present that as pieces of parchment. Let's keep it the fantasy theme."**

---

### Decision TO-10: Cup Holder (Soft Delete)
**Status:** BINDING
**Source:** Thunder (verbatim)

- No trash can icon — that breaks the metaphor
- A cup holder — a recessed spot at the corner of the table
- Drag things in to declutter, but they're not permanently gone
- Functions as a recycle bin in fantasy terms
- Prevents clutter anxiety and permanence anxiety simultaneously

**"A cup holder hole on the corner of the table where you can drag stuff in and then it's just... that's your delete. Or maybe it's not delete, right? Because you just... it's in the trash can for now."**

---

### Decision TO-11: DM's Area
**Status:** BINDING
**Source:** Thunder (verbatim)

- Dedicated area on the far side of the table
- Player can't interact with it unless they choose to
- This is where the battle map lives
- Transition mechanic: "Are you ready to see the map?" or a keybind to "lean up"
- Leaning up shifts your view to the DM's area; coming back returns to your spot

---

## PART 5: BATTLE MAP & COMBAT

### Decision BM-01: Battle Map Is Box Territory
**Status:** BINDING
**Source:** Thunder (verbatim)

**"The battle map is fundamentally without equivocal doubt a part of the box layer."**

- The battle map is the physical manifestation of the Box's mechanical authority
- Movement rules, spell geometry, line of sight, cover, flanking, threatened squares, AoE — all Box-enforced
- Every distance measured in 5-foot squares, by the book
- The Spark NEVER overrides the map. The Spark narrates what happens; the Box owns what IS.

**"It has to be audited. It has to be triple triple checked to make sure that everything is accurate because once again if the system fails in any way the entire trust layer is broken and everything falls apart."**

---

### Decision BM-02: Battle Map Scroll Metaphor
**Status:** BINDING
**Source:** Thunder (verbatim)

- The battle map is a scroll the DM unrolls
- Matt Mercer "roll initiative" moment — scroll unfurls, battlefield appears
- Minimal graphics — circles and grids on a flat surface
- Not a 3D rendered dungeon — just enough to be functional
- Low graphical overhead by design

---

### Decision BM-03: Fog of War Is Mandatory
**Status:** BINDING
**Source:** Thunder (verbatim)

- Fog of war follows 3.5e rules: visibility radius, line of sight, darkvision ranges
- Content loads progressively behind the fog — fog IS the loading strategy
- As fog clears, assets load in
- Box-level enforcement — you see what your character can see, nothing more

---

### Decision BM-04: Dynamic Battlefield
**Status:** BINDING
**Source:** Thunder (verbatim)

- The environment is destructible, moveable, interactive
- Player flips a table → map updates with overturned table object facing a direction
- The Spark narrates the action, the Box resolves mechanics, the map updates
- The Spark can modify the battle map (place new objects, update terrain)
- If the Spark needs time to generate visual assets: "Hold on, wasn't expecting that" — natural pacing

**"The spark has to be able to make adjustments to that battle mat because a battlefield is always fluid. It's always dynamic."**

---

### Decision BM-05: Cover Is Geometric, Not Binary
**Status:** BINDING
**Source:** Thunder (verbatim)

Cover depends on:
- Size of the character seeking cover (halfling = 3ft tall vs human = 6ft tall)
- Size of the object providing cover (chair vs table vs wall)
- Facing/angle relative to the attacker
- Whether the character is standing, crouching, or prone

**"If I'm playing a halfling and by rules as written I can be 3 foot tall. That means I can hide behind a full chair."**

The Box must calculate actual height vs object height vs attacker angle. Not approximate — calculate.

---

### Decision BM-06: Elevation Notation Is Required
**Status:** BINDING
**Source:** Thunder (verbatim)

- The battle map is 2D but the world has elevation
- Topographic-style elevation markers on terrain (contour lines, height indicators)
- "Under the table" is a valid position because the Box knows character height vs table height
- High ground advantage, low ground disadvantage — all Box-calculated
- Trees marked as solid objects with height
- Furniture has clearance measurements

**"There needs to be a slight notation somewhere for elevation because elevation matters."**

---

### Decision BM-07: Environmental Objects Have Material Properties
**Status:** BINDING
**Source:** Thunder (verbatim)

Every object on the battlefield has full mechanical properties:
- Material (wood, stone, iron — determines hardness per 3.5e rules)
- Hit points (per thickness, per material)
- Vulnerability to damage types (wood burns, stone doesn't)
- Destructibility (objects can be destroyed, creating new terrain)
- Fall physics (destroyed trees fall, create difficult terrain or cover)

**"If you hit a tree with a fireball, trees would have hardness according to the rules as written. Trees are wood. So they have HP. You can blow them up. If they fall over, you can hide behind them as cover or they create impaired terrain."**

---

### Decision BM-08: Physical Vectors Per Battlefield Object
**Status:** BINDING
**Source:** Opus (derived from Thunder's requirements)

Every object and creature on the battle map must track:
- Position (grid coordinates)
- Elevation
- Size category (Fine through Colossal)
- Height (exact measurement, for cover geometry)
- Facing (for directional cover)
- Material (for hardness, HP, vulnerability)
- Condition (intact, damaged, destroyed, prone, upright)
- Mobility (fixed, moveable, destroyed-into-difficult-terrain)
- Opacity (blocks line of sight or doesn't)
- Solidity (blocks line of effect or doesn't)

---

### Decision BM-09: Spark Provides World-Knowledge for Box Resolution
**Status:** BINDING
**Source:** Thunder (verbatim)

**"The box isn't going to know the height of the table, and this is where we need to rely on the intelligence aspect of the spark to be able to know a table is 3 foot 6 inches."**

- The Spark knows the physical world (common-sense dimensions, materials, weights)
- The Box knows the rules (hardness values, cover calculations, break DCs)
- The Lens holds the data — structured, indexed, queryable
- The Spark writes world-knowledge to the Lens; the Box reads it from the Lens
- They never communicate directly

---

## PART 6: COMBAT INPUT MODEL

### Decision CI-01: Two Input Modes (Voice Primary, Click Secondary)
**Status:** BINDING
**Source:** Thunder (verbatim)

**Primary mode (voice/text):** Tell the DM what you want to do.
- "I want to cast fireball and try to catch all three goblins"
- DM interprets, coordinates, confirms
- DM moves your piece
- DM shows area of effect
- Player confirms

**Secondary mode (direct interaction):**
- Click spell on character sheet
- "Lean up" to the battle map
- Place spell/movement with mouse
- Visual feedback: radius circles, ray lines, movement paths

**"There's a distinction. There's 'I click the spell if you need to.' But again that's secondary versus like you just tell the DM 'I cast a fireball.'"**

---

### Decision CI-02: DM Coordinates Combat Actions
**Status:** BINDING
**Source:** Thunder (verbatim)

- The DM shows the effect radius/area overlay (like physical plastic stencils on a real table)
- The DM adjusts placement based on player description: "Not at the feet — I want all three"
- The DM confirms: "This covers goblins 1, 2, and 3. Goblin 4 is just outside. Drop it here?"
- Player confirms → Box resolves

This confirmation loop is trust-building. The DM doesn't just act — the DM shows and asks.

---

### Decision CI-03: Lean-Up Mechanic
**Status:** BINDING
**Source:** Thunder (verbatim)

A single interaction pattern for:
- Viewing the battle map (from your spot at the table)
- Placing a spell or moving your token during combat
- Coming back to your spot when done

**"You lean up to the map and then that's when you can see your spell radius or maybe you have a ray."**

---

## PART 7: DM BEHAVIOR

### Decision DM-01: DM Teases During Prep
**Status:** BINDING
**Source:** Thunder (verbatim)

When the Spark is generating a campaign and the player is waiting:

- DM can slide a parchment across: "Hey, want to see what I just made?"
- Player gets a glimpse — monster portrait, location sketch, NPC face
- "Nope, you can't keep this one. But it's coming."
- DM can also just chat: "Oh, this battle is going to be fun."
- This is the feedback loop — the player knows the system is working

**"Hey, want to see what I just made? If it can share it, right, as like a tantalizing element... 'Nope, you can't have it but you can see it.' That way the player knows that the system is working on something."**

---

### Decision DM-02: Natural Loading / No Rush
**Status:** BINDING
**Source:** Thunder (verbatim)

- Loading times become DM moments, not progress bars
- "Give me a moment, I want to draw this up for you"
- DM can give narration lines while image pipeline processes
- There is no rush at the table — design principle
- System latency is masked by DM personality

**"There's no rush, right? You never rush at a table. But the DM is gonna draw you a cool picture of what the monster is gonna look like. OK, let me give you a second here. I'm in no hurry."**

---

### Decision DM-03: Player Can Read/Sketch During Prep
**Status:** BINDING
**Source:** Thunder (verbatim)

While the DM preps a campaign:
- Player doesn't have to leave the table
- Player can read their Player's Handbook (Tome)
- Player can sketch in their Notebook
- Player can look at previously generated images in their books
- Player can observe the DM working
- The table is always available, even when no session is active

---

## PART 8: PHILOSOPHICAL FOUNDATION

### Decision PH-01: This Is a Place, Not an App
**Status:** BINDING
**Source:** Thunder + Opus (collaborative)

Every design decision must pass one test: **does this happen at a real D&D table?**

- If it doesn't, it doesn't belong
- If it does, we already know how it should work — it's been working for 50 years
- The product is the table itself, not an AI DM simulator

The window starts small because you approach a table. There's no maximize because you don't become the table. The notebook has your name because it's yours. The DM says "are you ready" because that's what DMs do.

**"What is D&D? Why is it so important? Why has it been fundamental over all these years? What are the key elements that keep people engaged, locked in, and always coming back? Why is it so timeless? When we understand all of those key important elements, then you truly understand what this project is trying to represent."**

---

### Decision PH-02: D&D Is Not Just a Game
**Status:** BINDING
**Source:** Thunder (verbatim)

D&D endures because:
- It's relationships built around shared fiction
- It's emotional connections to the story
- It's imagination with stakes and rules
- It's creativity and freedom — do literally anything
- It's trust — you trust the DM, the DM trusts the dice
- It's the only game where the referee also cares about your story

**"It is a fundamental without a doubt unequivocal engine for D&D that is trusted beyond belief."**

The product serves someone sitting alone at 11 PM who doesn't have a group but wants the real experience — not a simulation of it.

---

### Decision PH-03: Better Than a Real Table (In Some Ways)
**Status:** BINDING
**Source:** Thunder (verbatim)

The system can be MORE rigorous than a human DM because:
- It measures every single vector that is truly present
- A halfling's 3-foot height against a 3.5-foot table — calculated, not hand-waved
- Environmental object hardness, fall direction, terrain generation — all by the book
- No human DM calculates tree hardness and fall direction in real time. The Box can.

**"These measurements matter. These are important elements that are actually missing for most tables. And that's another inspiration for the system is that you are measuring every single vector that is truly present."**

---

## PART 9: COMPLETE TABLE OBJECT INVENTORY

As defined by this whiteboarding session, the table surface contains exactly these objects:

| # | Object | Physics | Activatable | Container | Notes |
|---|--------|---------|-------------|-----------|-------|
| 1 | Dice Bag | Yes | Two-phase | Yes (holds dice) | Pull open to access dice |
| 2 | Dice (set) | Yes (primary) | Drop in tower = roll | No | Fiddle-able, tactile |
| 3 | Dice Tower | Yes (minimal) | Automatic (dice in = roll) | Yes (tray catches) | THE roll trigger |
| 4 | Notebook | Yes | Two-phase (open) | Yes (pages, inserts) | Player name on cover, drawable cover |
| 5 | Tome | Yes | Two-phase (open) | Yes (pages, inserts) | Rulebook + Bestiary sections |
| 6 | Character Sheet | Yes | Always readable | No | IS the action bar for spells/abilities |
| 7 | Settings Gemstone | Yes | Two-phase (hold + key) | No | Small red gemstone, opens settings |
| 8 | Parchment (images) | Yes | View on table | No | Generated images, insertable into books |
| 9 | Cup Holder | No (fixed) | Drop target | Yes (recycle bin) | Corner of table, soft delete |
| 10 | DM's Area | No (fixed) | Lean-up to view | Yes (holds battle map) | Far side of table |
| 11 | Battle Map Scroll | Yes (DM-controlled) | DM unrolls for combat | Yes (contains battlefield) | Fog of war, circles + grids |
| 12 | Text Chat | No (fixed) | Always active | No | Side of window, conversation with DM |

**No menus. No toolbars. No settings panels. No modal dialogs. Just things on a table.**

---

## END OF WHITEBOARD SESSION 002 DECISION LOG

**Date:** 2026-02-11
**Captured by:** Opus (Acting PM)
**Authority:** Thunder (Product Owner) — all decisions marked BINDING reflect verbatim product owner direction
**Status:** BINDING
