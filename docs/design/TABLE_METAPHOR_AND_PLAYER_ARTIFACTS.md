# Table Metaphor & Player Artifacts — Unified Design Specification

**Document ID:** TM-PA-001
**Version:** 1.1.0
**Date:** 2026-02-11
**Status:** BINDING (Approved by Product Owner — Whiteboard Session 002)
**Amended:** 2026-02-11 — v1.1.0 incorporates Whiteboard Session 002 decisions (see WHITEBOARD_SESSION_002_DECISIONS.md)
**Authority:** Amends and supersedes Player Artifacts specification (inbox)
**Amends:** "Aidm Player Artifacts — Notebook, Handbook, And Knowledge Tome Specification"
**Proposed By:** Thunder (Product Owner) via Opus (Acting PM)

---

## Amendment Summary

This document consolidates the original three-artifact specification (Notebook, Handbook, Knowledge Tome) into a **two-artifact** design and establishes the **Table Metaphor** as the foundational UI principle for AIDM.

### What Changed

| Original Spec | This Amendment |
|---------------|---------------|
| Three artifacts: Notebook, Handbook, Knowledge Tome | Two artifacts: Notebook, Tome |
| Knowledge Tome as separate progressive-discovery book | Bestiary section integrated into the Tome |
| Handbook contains "non-copyrighted rephrasing" of rules | Tome is a **viewer** for the player's local Vault (OCR'd source material) |
| UI architecture unspecified | **Table Metaphor** established: no application UI, only D&D objects on a surface |

### Why

The original three-artifact decomposition over-engineered the design. The Knowledge Tome's progressive bestiary is naturally a section of the Tome, not a standalone book. The Tome itself should display the player's own source material (Vault) rather than containing rewritten content. And the entire UI should feel like a D&D table, not like software.

---

## Part 1: The Table Metaphor

### Principle

**There is no application UI. There are only D&D objects on a table.**

The player's screen is a **table surface** — a freeform canvas where game objects exist physically. There are no menus, no sidebars, no status bars, no toolbars, no settings panels. Every interaction happens through objects the player would recognize from a real D&D session.

### Objects on the Table

| # | Object | Physical Analog | Behavior |
|---|--------|----------------|----------|
| 1 | **Dice Bag** | Leather dice bag | Container for dice. Pull open to access. Physics-enabled. |
| 2 | **Dice Set** | Physical polyhedrals | Full physics simulation. Fiddle-able on the table. Drop into tower to roll. |
| 3 | **Dice Tower** | Dice rolling tower + tray | THE roll trigger. Drop dice in → tumble → land in tray. Results stay in tray. |
| 4 | **Notebook** | Blank notebook + pen | Player's personal space. Drawing, writing, doodles. Player name on cover. Drawable cover. |
| 5 | **Tome** | Player's Handbook + Monster Manual | Vault-backed reference. Rulebook section + progressive Bestiary. |
| 6 | **Character Sheet** | Paper character sheet | Live-updating, draggable. IS the action bar — spells/abilities are clickable. |
| 7 | **Settings Gemstone** | Small red gemstone | Physics-enabled. Hold + activation key to open settings. |
| 8 | **Parchment** | Loose paper / images | Generated images appear as parchment. Insertable into books, usable as bookmarks. |
| 9 | **Cup Holder** | Recessed cup holder | Corner of table. Drag objects in to declutter (soft delete / recycle bin). |
| 10 | **DM's Area** | Far side of the table | DM's workspace. Player "leans up" to view. Contains the battle map. |
| 11 | **Battle Map Scroll** | Grid mat + miniatures | DM unrolls for combat. Fog of war. Minimal circles-and-grids. Box-enforced. |
| 12 | **Text Chat** | Conversation | Side of window. Conversation with the DM. Voice or text input. |

**Detailed specification:** See `TABLE_SURFACE_UI_SPECIFICATION.md` for interaction model, physics, and two-phase activation system.

### What Does NOT Exist

- Menu bars or toolbars
- Maximize button (minimize and close only — see TABLE_SURFACE_UI_SPECIFICATION.md)
- Sidebar panels
- Status bars or progress indicators (exception: minimized window may show progress)
- Settings dialogs (settings lives in the gemstone table object)
- Health bar widgets (the number is on the character sheet)
- Inventory panels (inventory is a section on the character sheet)
- Combat log windows (the DM narrates; the player takes notes if they want)
- Monster info popups (the DM directs the Tome to the bestiary entry)
- Help buttons (the DM explains it; the Tome opens to the relevant page)
- Modal dialogs of any kind
- Hotbars, cast bars, ability trays (the character sheet IS the action bar)

### Interaction Model

| Player Wants To... | How It Works |
|--------------------|-------------|
| Check their stats | Look at their character sheet (always visible, always current) |
| Look up a rule | Open the Tome, search or browse the rulebook section |
| Learn about a monster they've fought | Check the Tome's bestiary section (entries unlock through play) |
| Take notes | Open the Notebook, draw or write |
| See the battlefield | Battle map appears automatically when combat starts |
| Change a setting | Activate the settings gemstone on the table (hold + activation key) |
| Get help | Ask the DM (voice or text) |

### Window Behavior

- **Starts small** — the application opens as a small window, not fullscreen
- **No maximize button** — the player expands the window by dragging edges
- **Expanding reveals more table** — objects don't scale up, the camera pulls back to show more surface
- **Minimize exists** — table goes to the side, processing continues; progress indicator may appear on taskbar
- **Close exists** — shuts down the application
- See `TABLE_SURFACE_UI_SPECIFICATION.md` for full window behavior spec.

### First Interaction (Onboarding)

1. The player opens the application for the first time
2. The DM greets them: **"Hi. My name is [DM name]. What's yours?"**
3. When the player provides their name, it appears on the **cover of their Notebook**
4. The player can draw on the Notebook cover immediately — first personalization moment
5. The Notebook cover can also be customized via the image generator

This is the first assertion of ownership. The player's name on their Notebook cover. Persistent across sessions.

### Spatial Freedom

All objects on the table are **freely arrangeable**:
- Drag objects anywhere on the table surface
- Stack or overlap objects
- Flip character sheets over (front/back for organizational flexibility)
- Resize objects (within reasonable bounds)
- Objects persist their position across sessions

The player arranges their table however they want. Some players will stack everything neatly. Some will spread sheets everywhere. Some will keep the Notebook open next to the battle map. This freedom is intentional — it mirrors how real players arrange their physical table space.

### Constraint: No UI Leakage

Any system that needs to communicate with the player must do so through one of the table objects or through the DM's voice/text. Examples:

| System Event | How It's Communicated |
|-------------|----------------------|
| HP changes | Character sheet number updates |
| New condition (poisoned, prone) | Character sheet condition section updates; DM narrates it |
| Level up | Character sheet updates; DM announces it |
| New monster knowledge | Bestiary entry appears/updates in the Tome |
| Rule clarification needed | DM explains verbally AND/OR Tome opens to relevant page |
| Combat starts | Battle map materializes; DM announces initiative |
| Combat ends | Battle map fades away; DM narrates resolution |
| Error / system issue | DM acknowledges it in-character or breaks the fourth wall minimally |

---

## Part 2: The Notebook

### Purpose

The Notebook is the player's **personal, non-authoritative, freeform space**. It is a blank book with a pen. The player owns it completely. The system never writes in it, never validates it, never corrects it.

### Physical Metaphor

A leather-bound notebook with blank pages and a pen.

**Cover:**
- Displays the player's name (set during first interaction — "What's yours?")
- The cover is drawable — player can personalize it with drawings, doodles, etc.
- The cover can be generated/customized via the onboard image generator
- Cover personalization is persistent across sessions

### Interaction

1. **Default state:** Closed book on the table. Two-phase activation: hold + activation key to open.
2. **Moving:** Single click and drag to reposition on the table (Phase 1 — no activation).
3. **Open state:** A blank page (or the last page they were on). A pen cursor.
4. **Drawing:** Click and drag to draw. The pen draws lines on the page.
5. **Color/tool selection:** A **key bind** (configurable) opens a **radial color wheel** at the current pen tip position.
   - The radial wheel appears centered on the pen tip — not in a toolbar, not in a sidebar
   - Wheel segments for colors (full spectrum)
   - Optional: pen thickness in the center of the wheel or as a secondary radial
   - Release or click to select; wheel dismisses immediately
   - Total interaction: key bind → radial appears → select → radial vanishes → continue drawing
6. **Pages:** Turn pages forward/back. Infinite pages (append new blank pages as needed).
7. **Eraser:** A key bind or radial option for eraser mode.
8. **Parchment inserts:** Drag a parchment (generated image) onto the open Notebook → it becomes a page.
9. **Remove inserts:** Rip a parchment back out of the Notebook → it returns to the table as loose parchment.
10. **Bookmarks:** Tuck a parchment into a page edge to use it as a bookmark.

### What the Notebook is NOT

- It is not a text editor (no formatted text, no markdown, no rich text)
- It is not a form (no fields, no validation)
- It is not searchable by the system (the player's memory, not the system's)
- It is not authoritative (the player can write "Goblin Chief AC = 30" — the system doesn't care)
- It does not have undo/redo (optional: could be added, but not required)

### DM Interaction

- The DM can **view** the Notebook (read-only) if the player shows it
- The DM can **add a brief note** (e.g., a quest marker, a name) with player permission
- The DM can **proactively prompt:** "That seems important, want me to put that in your notebook?"
- The DM **never edits or deletes** player-written content
- DM notes are visually distinct (different ink color or handwriting style)

### Accessibility

- **Text-only mode:** For players who cannot use a drawing pad, the Notebook degrades to a simple text input (keyboard typing, plain text, no formatting)
- **Screen reader:** Pages can be exported as text descriptions
- **Adjustable contrast/size:** Pen thickness and page background configurable

### Persistence

- Notebook content persists across sessions within a campaign
- Notebook exports with campaign data (world export)
- Notebook is per-campaign (new campaign = new notebook)

---

## Part 3: The Tome

### Purpose

The Tome is the player's **reference book** — a single integrated volume containing:
1. **Rulebook Section:** The D&D 3.5e rules, sourced from the player's local Vault
2. **Bestiary Section:** A progressive monster encyclopedia that fills in through play

### Physical Metaphor

A thick, leather-bound tome with two distinct sections divided by a ribbon bookmark or tab system.

### Architecture: Vault-Backed Viewer

The Tome is **not a container of rewritten content**. It is a **viewer** for the player's local Vault.

```
Player's Local Vault (Obsidian-format OCR'd pages)
    ├── PHB/           ← Rulebook section sources from here
    ├── DMG/           ← DM-only (not displayed in player Tome)
    └── MM/            ← Bestiary section sources from here (progressively revealed)
            ↓
    Vault Adapter (reads Obsidian markdown, resolves links)
            ↓
    Tome Viewer (renders pages in-game, page-turning UI)
```

**Key principle:** The Vault is **local-only, never committed to version control, never distributed**. It contains the player's own legally-owned source material. The Tome viewer is the software; the Vault is the player's content.

**Fallback:** If no Vault is present, the Tome displays "non-copyrighted rephrasing" placeholder content (system-generated summaries of rules concepts). This ensures the application functions without requiring the player to own/scan the source books.

### Section A: Rulebook

- Sourced from PHB pages in the Vault
- Always available — player can browse any rule at any time
- **Searchable:** Player can search by concept/term (e.g., "grapple", "flanking", "cover")
- **DM-directed navigation:** The DM can open the Tome to a specific page
  - Example: Player asks "How does grappling work?" → DM says "Check your Tome" → Tome automatically opens to PHB p.155
  - Example: During combat, DM narrates "You provoke an attack of opportunity" → Tome highlights the AoO section if the player is confused
- **Obsidian bidirectional links:** Rules pages link to related rules (grapple → AoO → threatened squares → reach)
- **Page-level display:** Renders the actual OCR'd page content, preserving the original layout where possible

### Section B: Bestiary (Progressive Discovery)

The bestiary implements the **Pokedex model** — entries start blank and fill in as the player's character encounters and learns about creatures.

**Discovery Levels:**

| Level | What the Player Sees | How It's Earned |
|-------|---------------------|-----------------|
| **0 — Unknown** | Empty entry. Silhouette or "???" | Default for all creatures |
| **1 — Encountered** | Name, general appearance, size category | First combat encounter or sighting |
| **2 — Observed** | Behavioral notes ("aggressive", "uses fire"), attack types observed | Extended combat (2+ rounds) or successful Knowledge check |
| **3 — Studied** | Approximate defenses ("tough hide", "resists fire"), observed abilities | Successful Knowledge check (DC varies by creature type) |
| **4 — Known** | Specific values (AC range, HP estimate, key abilities) | High Knowledge check result, extensive experience, or NPC/library research |

**Authority model:**
- The engine tracks what the **character** has learned (not what the player knows from meta-gaming)
- Discovery events are logged in the event store (deterministic, replayable)
- The DM can grant discovery levels through narration ("The sage tells you about trolls — they regenerate unless burned")
- The player's Notebook notes about monsters are **non-authoritative** (the player might write "AC = 20" when it's actually 18)
- The Tome's bestiary is **authoritative** (it only shows what the character has legitimately learned)

**Vault integration:**
- Bestiary entries source from MM pages in the Vault
- At discovery level 0–2: system-generated text (no Vault content shown — avoids spoiling full stat blocks)
- At discovery level 3–4: relevant Vault page sections revealed (filtered to match discovery level)
- DM-facing information (full stat blocks, tactics, treasure) is **never** shown in the player's Tome

### DM ↔ Tome Interaction

The DM has three powers over the player's Tome:

1. **Navigate:** Open the Tome to a specific page (rulebook or bestiary)
   - Triggered by DM narration context or player question
   - Implemented via `obsidian_links.py` URI resolution

2. **Reveal:** Unlock bestiary discovery levels
   - Triggered by engine events (combat encounter, Knowledge check, NPC information)
   - Logged in event store for determinism

3. **Annotate:** Add DM-authored notes to Tome margins (optional)
   - Visually distinct from Vault content
   - Example: "Your mentor warned you about these creatures" next to a bestiary entry

The DM **cannot** edit Vault content, modify discovery levels retroactively, or hide previously revealed information.

---

## Part 4: Character Sheets

### Origin

The character sheet is the **origin artifact** of the entire AIDM project. The project began with a single realization: the official WotC Interactive D&D 3.5 Character Sheet (a 2-page PDF with 651 fillable form fields and auto-calculating modifiers) proved that code could fill in a character sheet. If code can fill in the sheet, code can be the DM. Everything else — the engine, the narration, the Tome, the Notebook, the battle map — grew outward from that self-updating sheet.

### Canonical Visual Template

**Reference:** `F:\DnD books\Miscellaneous\Interactive_DnD_3.5_Character_Sheet_(1).pdf`

The AIDM character sheet MUST match the standard WotC 3.5e character sheet layout. This is not just a familiarity choice — it is the project's origin artifact. Every 3.5e player already knows where STR is, where AC is, where the skills list is. The engine makes those fields alive.

**Template structure (2 pages, 651 fields):**

Page 1:
- Character identity (name, class, race, alignment, deity, level, size, age, gender)
- Six ability scores + modifiers (+ temporary score/modifier columns)
- Saving throws (Fortitude/Reflex/Will: total = base + ability + magic + misc + temporary)
- HP, AC (total = 10 + armor + shield + dex + size + natural + deflection + misc), Speed
- Initiative (total = dex + misc), Grapple (total = BAB + STR + size + misc)
- Base Attack Bonus, Spell Resistance, Damage Reduction
- Attack entries (bonus, damage, critical, range, type, notes)
- Skills list (45 skills, each: class skill checkbox + modifier = ability mod + ranks + misc)

Page 2:
- Feats list
- Spell table (levels 0–9, save DC, spells per day, bonus spells, spell lists)
- Money (cp, sp, gp, pp)
- Other possessions (item + weight)
- Languages
- Campaign, Experience Points

### Purpose

The character sheet is the player's **live dashboard** — a paper-metaphor display of all character data that updates in real-time as the engine processes events. It is the central object on the table.

### Physical Metaphor

Standard D&D 3.5e character sheet (2 pages, matching the WotC layout). Paper on the table.

### Behavior

- **Live-updating:** When the engine emits events (HP change, condition applied, item used), the sheet updates immediately — the player watches the numbers change
- **Draggable:** Player can position the sheet anywhere on the table
- **Flippable:** Front/back (page 1 ↔ page 2), player flips between pages
- **Read-only to player:** The player cannot manually edit stats (the engine is the authority)
  - Exception: Freeform fields (character name, backstory, notes section) are player-editable
- **All derived stats auto-calculated:** Base stats + modifiers → AC, attack bonus, saves, etc. — exactly as the original interactive PDF does, but driven by engine events instead of manual input

### What the Sheet Shows

Per the existing `CS-UI-001` (Character Sheet UI Contract):
- Base ability scores + modifiers
- Persistent modifications (level-ups, permanent effects)
- Derived statistics (AC, BAB, saves, skills, initiative)
- Consumable resources (HP, spell slots, daily abilities)
- Equipment and inventory
- Conditions currently affecting the character
- "As-of turn" history (minimal, read-only — what changed last turn)

---

## Part 5: DM-Facing vs. Player-Facing Information Boundary

### The Core Rule

**The DM has full access to all game data. The player sees only what their character would know.**

| Information | DM Access | Player Access (via Tome) | Player Access (via Sheet) |
|------------|-----------|-------------------------|--------------------------|
| All rules (PHB) | Full | Full (Rulebook section) | N/A |
| All monsters (MM) | Full | Progressive (Bestiary, discovery-gated) | N/A |
| DM guidelines (DMG) | Full | None | N/A |
| Character stats | Full | N/A | Full (live sheet) |
| Monster stats (in combat) | Full | Only discovered info | N/A |
| Hidden DC values | Full | None | N/A |
| Trap locations | Full | None (until detected) | N/A |
| NPC motivations | Full | None (until revealed) | N/A |

### Vault Segmentation

| Vault Directory | DM Access | Player Tome Access |
|----------------|-----------|-------------------|
| `PHB/` | Full | Full (Rulebook section) |
| `DMG/` | Full | **None** (DM-only material) |
| `MM/` | Full | **Discovery-gated** (Bestiary section) |

---

## Part 6: Superseded Specifications

This document **supersedes** the following sections of the original Player Artifacts specification:

| Original Section | Disposition |
|-----------------|-------------|
| "Player Notebook" | **Replaced** by Part 2 of this document (adds radial wheel UX, clarifies drawing-first design) |
| "Player Handbook / Rules Tome" | **Replaced** by Part 3 Section A (Tome is now Vault-backed viewer, not rewritten content) |
| "Knowledge Tome" | **Merged** into Part 3 Section B (bestiary is a section of the Tome, not a separate artifact) |
| Three-artifact system | **Consolidated** to two artifacts (Notebook + Tome) |

The following principles from the original spec are **preserved unchanged:**
- Notebook is player-owned, non-authoritative
- Notebook supports accessibility (text-only mode, screen reader)
- DM can view but not edit player Notebook content
- Progressive discovery for monster knowledge
- No mechanical dependence on artifacts (presentation layer only)

---

## Part 7: Implementation Impact

### Roadmap Mapping

| Component | Original Roadmap Task | Updated Task |
|-----------|----------------------|--------------|
| Notebook | M3.18 | M3.18: Notebook with drawing pad + radial wheel |
| Handbook | M3.19 | M3.19: Tome viewer with Vault adapter (Rulebook section) |
| Knowledge Tome | M3.20 | M3.20: Tome bestiary section with progressive discovery |
| Table Metaphor | Not in roadmap | **NEW:** M1 foundational task — table surface renderer |
| Character Sheet | M1.13 | M1.13: Character sheet as draggable table object (not UI component) |

### New Infrastructure Required

| Component | Description | Milestone |
|-----------|-------------|-----------|
| Table Surface Renderer | Freeform canvas for draggable objects | M1 |
| Vault Adapter | Reads Obsidian markdown, resolves links, filters by access level | M3 |
| Drawing Pad Engine | Canvas-based freeform drawing with pen/eraser | M3 |
| Radial Menu System | Pen-tip radial color/tool wheel | M3 |
| Bestiary Discovery Tracker | Event-sourced progressive reveal system | M3 |
| Page-Turn Renderer | Book metaphor UI for Tome and Notebook | M3 |

### Dependencies

- **Vault Adapter** depends on Vault directory structure being standardized (PHB/, DMG/, MM/ subdirectories)
- **Bestiary Discovery** depends on engine event types for Knowledge checks and encounter logging
- **Table Surface Renderer** is a foundational M1 dependency — affects how character sheets are displayed
- **Drawing Pad Engine** has no dependencies (self-contained)

---

## Part 8: Extended Design Threads

The following design threads were identified during product owner review (2026-02-11) and require formal integration into the specification.

### 8.1: Voice-Commanded DM Note-Taking

The player can verbally ask the DM to write in their Notebook:
- "Hey DM, can you write this down for me?"
- "DM, make a note that the goblin chief mentioned a cave to the north"
- "Add that to my notebook for later"

This is a **first-class voice interaction pattern**, not an edge case. It extends the existing DM Notebook permission model (Part 2) with an explicit voice trigger. The DM writes the note in its distinct visual style (different ink/handwriting), and the player can see exactly what was written.

**Implementation requirement:** The voice intent extraction system (M1.8) must recognize note-taking delegation as a valid intent category alongside combat actions, movement, and skill checks.

### 8.2: Skill-Specific Bestiary Enrichment

The current discovery level model (Part 3, Section B) treats all Knowledge checks equally. In practice, **different skills reveal different types of information:**

| Skill Used | Information Revealed | Example |
|-----------|---------------------|---------|
| Knowledge (Nature) | Habitat, diet, behavior patterns, vulnerabilities | "Trolls regenerate — fire and acid stop it" |
| Knowledge (Arcana) | Magical abilities, spell-like abilities, resistances | "The beholder's central eye emits an antimagic cone" |
| Knowledge (Religion) | Undead properties, turning resistance, creation method | "Vampires are repelled by holy symbols and garlic" |
| Knowledge (Dungeoneering) | Underground ecology, aberration traits | "Mindflayers feed on brains — their tentacles grapple first" |
| Handle Animal | Temperament, domestication potential, mount suitability | "This dire wolf could be trained as a mount with patience" |
| Survival | Tracking signs, territorial range, pack behavior | "These tracks suggest a pack of 6–8, territory extends 2 miles" |
| Heal | Anatomy, weak points, injury treatment | "The creature's hide is thick but the joints are vulnerable" |

**Design principle:** A ranger with Handle Animal and Survival fills in *different bestiary fields* than a wizard with Knowledge (Arcana). Both contribute to the creature's overall discovery level, but the *content* of the entry reflects how the character learned about it.

**Narrative integration:** The bestiary entry should include *how* the knowledge was gained:
- "Goblins — aggressive, lightly armored. *You learned this when ambushed near the bridge.*"
- "Dire Wolf — can be trained as mount. *Assessed during your time with the Woodland Rangers.*"

This creates a personalized bestiary that reflects the character's unique journey and skillset.

### 8.3: Image Generation ↔ Bestiary Discovery

The AIDM's onboard image generator should produce bestiary artwork **gated by discovery level:**

| Discovery Level | Image Treatment |
|----------------|-----------------|
| 0 — Unknown | No image (silhouette or "???") |
| 1 — Encountered | Rough sketch style — vague shape, basic coloring, no detail |
| 2 — Observed | More detailed rendering — correct proportions, observed features |
| 3 — Studied | Full portrait — accurate coloring, visible defensive features |
| 4 — Known | Annotated illustration — key abilities labeled, weak points marked |

**Technical integration:** The image generator receives the creature's full data (DM-facing) but the **prompt is filtered by discovery level**. Level 1 prompt: "vague silhouette of a large reptilian creature." Level 4 prompt: "detailed anatomical illustration of a red dragon with labeled fire breath gland and vulnerable underbelly scales."

**Authority boundary:** The image generator uses DM-facing data to create the image, but the *visible detail* is filtered to match player-facing discovery level. The DM knows what the dragon looks like; the player sees only what their character has observed.

### 8.4: Player Examination Actions

Players can take **in-game actions** to learn about creatures and objects, unlocking information in the Tome's bestiary:

- **Examine:** "I want to look at the creature more closely" — passive observation, may reveal size, coloring, visible weapons/armor
- **Measure:** "How tall is it?" — requires proximity and time, reveals exact dimensions
- **Assess:** "Can I tell how tough it is?" — Knowledge check or Sense Motive, reveals approximate defenses
- **Research:** "I want to look up this creature in the library" — downtime activity, can jump directly to discovery level 3–4

Each action is processed by the engine as a standard intent → resolution → event cycle. The resulting discovery event updates the bestiary entry deterministically.

**Key constraint:** The player doesn't know a monster's height until they take the in-game action to measure it. Meta-knowledge (what the player knows from owning the Monster Manual) is irrelevant — only character actions unlock Tome entries.

---

## Part 9: Resolved Open Questions

1. **Character sheet template:** RESOLVED — The sheet MUST match the classic WotC 3.5e character sheet layout (see Part 4: Origin). This is the project's origin artifact and the canonical visual template.

## Part 10: Remaining Open Questions

1. **Vault structure standardization:** What is the current Obsidian directory layout in the Vault? Does it already separate PHB/DMG/MM, or does it need reorganization?

2. **Fallback content:** If no Vault is present, what level of rules summary should the Tome provide? Minimal (concept names only) or substantial (paraphrased rules)?

3. **Drawing pad input:** Is stylus/tablet input a first-class requirement, or is mouse-based drawing sufficient for initial implementation?

---

## Approval

- [x] Product Owner Review (Thunder) — Approved via Whiteboard Session 002 (2026-02-11)
- [x] PM Review (Opus, Acting PM) — Approved 2026-02-11
- [ ] Roadmap amendment (M1.13 table surface, M3.18–M3.20 updated tasks) — pending roadmap rewrite

**Related Specifications (written 2026-02-11):**
- `TABLE_SURFACE_UI_SPECIFICATION.md` — complete table interaction model, physics, two-phase activation
- `BATTLE_MAP_AND_ENVIRONMENTAL_PHYSICS.md` — Box-layer battlefield, cover geometry, environmental objects
- `SPARK_LENS_BOX_ARCHITECTURE.md` — operational architecture, interface contracts, Lens subsystems
- `WHITEBOARD_SESSION_002_DECISIONS.md` — raw decision log from Product Owner whiteboarding session

---

## END OF TABLE METAPHOR & PLAYER ARTIFACTS SPECIFICATION
