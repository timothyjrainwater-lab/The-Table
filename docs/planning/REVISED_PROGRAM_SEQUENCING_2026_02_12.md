# Revised Program Sequencing — Post-Whiteboard 2026-02-12

**Author:** PM (Opus)
**Date:** 2026-02-12
**Status:** PROPOSED (awaiting PO ratification)
**Supersedes:** EXECUTION_PLAN_V2_POST_AUDIT.md (not invalidated, but reframed)

---

## Context

The whiteboard session of 2026-02-12 produced three major shifts:

1. **Content independence is immediate, not aspirational.** All references to the source material's IP must be stripped from the codebase and public-facing documents. The product identity is a truthful imaginative instrument, not a specific game system implementation.

2. **The Presentation Semantics layer is the keystone.** AD-007 formalizes the missing contract between deterministic mechanics and ephemeral narration. This must exist before the play loop can produce stable, trustworthy output.

3. **The physical table UI is not decoration — it's the proof of doctrine.** The table metaphor makes the Box/Lens/Spark boundary tangible to players. A thin prototype should exist early.

---

## Revised Priority Ordering

### Phase 0: Foundation Alignment (NEW)

**Goal:** Align the codebase with the product identity.

| Order | Work | Description | Blocked By |
|-------|------|-------------|------------|
| 0.1 | **Strip source material references** | Remove all IP-specific names, citations, and identifiers from code, tests, docs. Replace with generic/abstract identifiers. | Nothing |
| 0.2 | **Update MANIFESTO.md** | Replace with content-independent merged version. Move old to docs/TECHNICAL_CASE.md. | Nothing |
| 0.3 | **AD-007: Presentation Semantics Schema** | Implement frozen dataclass, enum types, validation. The keystone contract. | Nothing |
| 0.4 | **Rulebook Object Model** | Storage format, indexing, query API. How the world-owned rulebook works. | 0.3 |

### Phase 1: World Compile (NEW — replaces old Phase 1)

**Goal:** A world compiler that outputs a frozen artifact set.

| Order | Work | Description | Blocked By |
|-------|------|-------------|------------|
| 1.1 | **World Model Schema** | Define what a "world" is: names registry, presentation semantics registry, bestiary templates, map seeds. | 0.3 |
| 1.2 | **Minimum World Compiler** | Takes mechanical templates + world theme → outputs frozen world bundle with names, semantics, rulebook entries. | 1.1 |
| 1.3 | **MVP World: "Ashenmoor"** | Hand-authored tiny world: 1 town, 1 shop, 1 encounter area, 3 NPCs, 3 abilities. Proves the compiler works. | 1.2 |

### Phase 2: Play Loop Integration (evolved from old Phase 1)

**Goal:** Voice-first intent → dice → resolution → narrated output → log.

| Order | Work | Description | Blocked By |
|-------|------|-------------|------------|
| 2.1 | **Wire Spark narration into game loop** | connect template/LLM narration to the turn cycle. Presentation semantics in NarrativeBrief. | 0.3, existing Spark work |
| 2.2 | **Voice pipeline integration** | STT → Intent Bridge → Box → Lens → Spark → TTS as one loop. | 2.1 |
| 2.3 | **Discovery Log backend** | Progressive monster revelation schema. Knowledge mask per player. Knowledge sources (encounter, skill, NPC). | 1.1 |
| 2.4 | **Session Zero flow** | Name → character substrate → stat rolling → world entry. Conversational AI guides the process. | 2.2 |

### Phase 3: Table UI Prototype (NEW)

**Goal:** Thin Three.js proof of the physical table metaphor.

| Order | Work | Description | Blocked By |
|-------|------|-------------|------------|
| 3.1 | **Table surface + camera** | Three.js scene, table surface, player/DM sides, smooth camera transitions. | Nothing |
| 3.2 | **Notebook** | 3D book object, canvas pages, drawing tools, page flipping, handout storage. | 3.1 |
| 3.3 | **Dice bag + tower** | 3D dice objects, bag open/close, tower drop, tray display, cosmetic animation over deterministic RNG. | 3.1 |
| 3.4 | **Crystal ball** | DM presence, glow-on-speak, NPC portrait display. | 3.1 |
| 3.5 | **Battle map scroll** | 2D scroll surface, fog of war, token display, AoE stencil overlays, tile swap for terrain changes. | 3.1 |
| 3.6 | **Character sheet** | Read-only paper object, system-populated, spell/ability click triggers. | 3.1 |
| 3.6b | **Rulebook** | World-owned reference book, AI-navigable, page lookup, bookmarking. Generated from Layer A + B at world compile. | 3.1, 0.4 |
| 3.7 | **WebSocket bridge** | Connect Three.js frontend to Python backend. | 3.1 |
| 3.8 | **Handout system** | DM-to-player paper objects, pick up, store in notebook, discard. | 3.2, 3.4 |

### Phase 4: MVP Integration

**Goal:** Session Zero → One Combat as described in MVP spec.

| Order | Work | Description | Blocked By |
|-------|------|-------------|------------|
| 4.1 | **End-to-end integration** | All phases connected. Player sits down and plays. | 2.4, 3.7, 1.3 |
| 4.2 | **Asset pipeline** | Pool-based rotation, generation queue, binding registry. | Image/voice generation infrastructure |
| 4.3 | **Acceptance testing** | All 10 MVP acceptance criteria verified. | 4.1 |

### Continuing: Mechanical Coverage (parallel track)

The existing mechanical extraction work continues in parallel. This is bone and muscle work — mining physics from the source material. It does not block any phase above but enriches the engine substrate.

| Work | Status |
|------|--------|
| Flanking geometry detection | COMPLETE (29 tests) |
| Sneak Attack (WO-050B) | Ready (flanking unblocked) |
| Evasion / Improved Evasion | Ready |
| Combat Expertise | Ready |
| Energy Resistance | Ready |
| Save Bonus Type Stacking | Ready |
| Additional mechanics | Ongoing |

---

## What Changed from the Old Plan

| Old Plan | New Plan | Why |
|----------|----------|-----|
| Phase 1: Wire Spark into game loop | Phase 0: Foundation alignment first | Can't build content-independent narration on content-dependent foundations |
| No world compile phase | Phase 1: World Compile | Presentation semantics require a world model to exist |
| No UI phase | Phase 3: Table UI Prototype | The physical metaphor is the proof of doctrine, not decoration |
| Mechanical coverage as main work | Parallel track | Still valuable but not the critical path to MVP |
| MVP undefined | MVP defined: Session Zero → One Combat | Clear acceptance criteria for thesis proof |

---

## Relationship to Existing Documents

- **EXECUTION_PLAN_V2_POST_AUDIT.md** — Not invalidated. Phase 2 WOs (WO-048 through WO-060) remain valid completions. The mechanical extraction work continues. But the *framing* shifts from "implement the game system" to "extract physics from the source material."
- **AD-001 through AD-006** — All remain binding. AD-007 (Presentation Semantics) extends the decision set.
- **RQ-LENS-SPARK-001** — Complete. The context orchestration sprint delivered the pipeline infrastructure. Presentation semantics will flow through this pipeline.
- **PM_SESSION_STATUS_2026_02_12.md** — Will be updated to reflect this resequencing.

---

*The critical path to MVP is: strip IP → presentation semantics schema → world compiler → play loop → table UI → integration. Mechanical coverage continues in parallel.*
