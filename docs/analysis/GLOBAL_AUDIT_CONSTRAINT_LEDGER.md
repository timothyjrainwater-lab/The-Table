# Global Audit Constraint Ledger
## Immovable Constraints Across All Design Documents

**Audit Session:** GLOBAL-AUDIT-001
**Date:** 2026-02-10
**CP-001 Baseline:** ✅ FROZEN (treated as immovable constraint)

---

## Purpose

This ledger extracts and consolidates all **immovable constraints** from the design corpus to:
1. Prevent constraint violations during implementation
2. Establish clear boundaries for architectural decisions
3. Document non-negotiable requirements from multiple sources
4. Enable constraint-driven implementation planning

**Note:** CP-001 (Position Type Unification) is treated as a fixed, non-negotiable constraint per user directive.

---

## Constraint Classification

| Symbol | Type | Enforcement |
|--------|------|-------------|
| 🔴 | **SACRED** | Violation invalidates entire architecture |
| 🟠 | **CRITICAL** | Violation requires architecture rework |
| 🟡 | **IMPORTANT** | Violation requires explicit justification |
| 🔵 | **PREFERENCE** | Violation requires documentation |

---

## Section A: Sacred Constraints (Non-Negotiable Architecture)

### A1. Determinism (🔴 SACRED)

**Source:** Execution Roadmap v3.1, Generative Presentation Architecture, Secondary Audit
**Statement:** "Determinism is sacred. Engine outcomes must be replay-identical under identical inputs."

**Enforcement Rules:**
- Identical inputs → identical outputs (ALWAYS)
- All randomness seeded and logged
- Event logs are replayable independent of presentation layer
- No floating-point drift in position/distance calculations ✅ (CP-001 verified)
- Presentation changes CANNOT affect: legality of actions, numeric outcomes, state transitions

**Implications:**
- LLM narration may vary, but engine resolution cannot
- Asset generation must be deterministic or cached by canonical ID
- Player modeling affects presentation only, not mechanics

**Verification:**
- ✅ CP-001: Position distance_to() uses integer math (1-2-1-2 diagonal), no float drift
- ✅ Existing: 1393 tests include 10× replay verification
- ⚠️ TODO: M1/M2 must maintain determinism when adding LLM narration

---

### A2. Authority Split: Engine vs LLM (🔴 SACRED)

**Source:** Execution Roadmap, Generative Presentation Architecture, Secondary Audit
**Statement:** "Authority split is sacred. Engine defines reality; LLM describes reality."

**Enforcement Rules:**
- Canonical IDs are the only truth for mechanics
- LLM operates ONLY in presentation layer
- LLM cannot: override engine results, modify intent after freeze, decide mechanics
- Generative AI is never an authority over mechanics
- If LLM missing/timeout → deterministic template narration (fallback required)

**Boundaries:**
```
┌────────────────────────────────────────────┐
│ ENGINE (Authoritative)                     │
│ - Canonical IDs                            │
│ - Rules, numbers, legality                 │
│ - State transitions                        │
│ - Event log (append-only)                  │
└────────────────────────────────────────────┘
                  ↓
┌────────────────────────────────────────────┐
│ LLM (Descriptive Only)                     │
│ - Narration                                │
│ - Names, descriptions                      │
│ - Tone, pacing, explanation depth          │
│ - Intent clarification (before freeze)     │
└────────────────────────────────────────────┘
```

**Implications:**
- M1 must implement intent freeze BEFORE engine resolution
- Narration failure cannot block gameplay (fallback templates required)
- Player modeling affects LLM behavior, not engine outcomes

---

### A3. Canonical IDs (🔴 SACRED)

**Source:** Generative Presentation Architecture, Secondary Audit
**Statement:** "All mechanically relevant entities must be defined by stable, language-agnostic identifiers."

**Enforcement Rules:**
- Items, spells, monsters, conditions, actions, events = canonical IDs
- Rules engine, logs, validation, replay operate EXCLUSIVELY on IDs
- Human-readable strings are NEVER authoritative
- Alias tables map localized input → canonical IDs
- Canonical engine never processes localized strings

**Implications:**
- ✅ CP-001: Position uses integer coordinates (x, y) — canonical representation
- M2 must define canonical ID schema for all mechanical entities
- Skin Packs decorate IDs but cannot redefine mechanics
- Import validation must reject aliases that conflict with existing IDs

---

### A4. Event Sourcing (🔴 SACRED)

**Source:** Execution Roadmap v3.1
**Statement:** "All state changes via events. Event log is append-only."

**Enforcement Rules:**
- Append-only event store
- No in-place mutations
- Replay must reconstruct identical state
- Events are the source of truth, not derived state

**Implications:**
- M1 event store schema must be immutable
- Position changes are events (e.g., StepMoveIntent → PositionChangedEvent)
- Character sheet UI subscribes to event stream (not direct state mutation)

---

### A5. Gate Compliance (🔴 SACRED)

**Source:** Execution Roadmap v3.1
**Statement:** "Gates remain closed unless explicitly opened. Current operating gate: G-T1 only."

**Current Gate Status:**
| Gate | Status | Forbidden Mechanics |
|------|--------|---------------------|
| G-T1 | ✅ OPEN | (baseline combat, movement, dice) |
| G-T2A | 🔒 CLOSED | Permanent stat mutation |
| G-T2B | 🔒 CLOSED | XP economy |
| G-T3A | 🔒 CLOSED | Entity forking |
| G-T3B | 🔒 CLOSED | Agency delegation |
| G-T3C | 🔒 CLOSED | Relational conditions |
| G-T3D | 🔒 CLOSED | Transformation history |

**Enforcement Rules:**
- No mechanics requiring closed gates
- New RNG streams require explicit approval
- Relational kernels (SKR-005) forbidden at G-T1

---

## Section B: Critical Constraints (Architecture-Level)

### B1. Mechanics vs Presentation Separation (🟠 CRITICAL)

**Source:** Chronological Design Record, Generative Presentation Architecture
**Statement:** "If mechanics are stable, fiction is interchangeable."

**Enforcement Rules:**
- Skin Packs are declarative, validated, hot-swappable at presentation level
- Skin Packs CANNOT: alter mechanics, add modifiers, introduce new action legalities
- Reskinning is cosmetic unless explicitly extended later
- No genre-implied mechanics (e.g., cyberpunk hacking) without explicit implementation

**Implications:**
- M2 must define Skin Pack schema and validation rules
- Import safety: reject Skin Packs that attempt mechanical changes
- Terminology locking required to prevent synonym drift mid-session

---

### B2. Local-Only Execution (🟠 CRITICAL)

**Source:** Execution Roadmap v3.1, Local Runtime Packaging
**Statement:** "No cloud dependencies. No telemetry."

**Enforcement Rules:**
- All models run locally (LLM, STT, TTS, image gen, critique)
- Hardware baseline: Steam Hardware Survey median consumer hardware
- CPU fallback paths required (GPU cannot be assumed)
- Offline install must work on fresh machine

**Implications:**
- Model selection constrained by: size, latency, RAM/VRAM footprint
- M3 must evaluate models for offline compatibility
- M4 packaging must include all dependencies (no download-on-demand)

---

### B3. Voice-First Philosophy (🟠 CRITICAL)

**Source:** Chronological Design Record, Minimal UI Addendum
**Statement:** "Voice output quality is more immersion-critical than voice input accuracy."

**Enforcement Rules:**
- TTS quality > STT accuracy (priority ordering)
- Poor TTS breaks trust immediately; STT errors are recoverable
- Text input/output MUST always be available (accessibility)
- Voice is primary, NOT required

**Implications:**
- M3 TTS evaluation must prioritize naturalness, control, expression
- STT errors require confirmation flows for high-impact commands
- Onboarding must not assume audio capability

---

### B4. Prep-First Asset Generation (🟠 CRITICAL)

**Source:** Chronological Design Record, Secondary Audit, Generative Presentation
**Statement:** "Most generation happens during campaign/session prep, not during live play."

**Enforcement Rules:**
- Assets generated during prep: NPC portraits, scene backdrops, sound palettes
- Runtime presentation is compositing (portrait/sprite over background)
- Live generation may exist as fallback but must be bounded
- Assets are: archived, tagged, retrievable, reusable across sessions

**Implications:**
- M2 prep pipeline must orchestrate asset generation
- Asset logging required (prevent repeated generation)
- Continuity: NPCs use static anchor images (generated once)

---

### B5. Image Critique Gate (🟠 CRITICAL)

**Source:** Chronological Design Record, Secondary Audit
**Statement:** "Image generation without image quality evaluation is unacceptable."

**Enforcement Rules:**
- Image generation MUST be paired with critique/quality evaluation
- Critique checklist: readability at UI size, centering, artifacting, style adherence, identity match
- Regeneration loop must be bounded (avoid infinite loops)
- Poor image quality breaks immersion immediately

**Implications:**
- M3 image pipeline requires: generator + critic (heuristics first, model second)
- Output caching keyed to canonical IDs to prevent drift
- Prep-time generation allows time for critique/regeneration

---

## Section C: Important Constraints (Requires Justification)

### C1. Multimodal Equivalence (🟡 IMPORTANT)

**Source:** Minimal UI Addendum, Secondary Audit
**Statement:** "Text parity is mandatory."

**Enforcement Rules:**
- Voice-only lock-in is forbidden
- All gameplay must be accessible via text
- Screen-reader compatibility required
- Font size, contrast adjustable

**Implications:**
- M1 must support text input with structured fallback templates
- M3 TTS must have text equivalents
- Onboarding cannot assume audio

---

### C2. Multi-Language Input (🟡 IMPORTANT)

**Source:** Generative Presentation Architecture, Secondary Audit
**Statement:** "Players may speak or type in multiple languages."

**Enforcement Rules:**
- Alias tables map localized input → canonical IDs
- Aliases are language-specific and Skin Pack–specific
- Ambiguity handling and disambiguation must be explicit
- This is a design requirement, not a post-launch feature

**Implications:**
- M1 intent resolution must support alias tables
- M2 Skin Pack schema must include language-specific aliases
- STT must include multilingual support or graceful degradation

---

### C3. Memory Indexing (🟡 IMPORTANT)

**Source:** Chronological Design Record, Secondary Audit
**Statement:** "LLM coherence degrades when forced to 'remember everything.' Truth lives outside the LLM."

**Enforcement Rules:**
- Memory = structured records: entity cards, event timelines, relationships, inventory
- LLM queries indexed records instead of holding state
- Session recap as proof of memory (DM can reference specific moments)

**Implications:**
- M1 must implement memory indexing layer
- M2 campaign state includes: NPCs, locations, factions, open threads
- Narration queries memory instead of synthesizing from context window

---

### C4. Ceremony as Consent (🟡 IMPORTANT)

**Source:** Secondary Audit
**Statement:** "Dice and other ritual elements must be skippable, adjustable, chosen conversationally."

**Enforcement Rules:**
- Dice animation quality is crucial (fairness + anticipation)
- Dice customization expressive only (no mechanical impact)
- Must never misrepresent randomness

**Implications:**
- M1 dice UI must support: skip, size, color, effects
- Preferences persist across sessions
- Dice state must accurately reflect RNG output (no desyncs)

---

### C5. Player Modeling is Persistent (🟡 IMPORTANT)

**Source:** Player Modeling Specification
**Statement:** "Player categorization is not an onboarding artifact. It is a persistent, evolving model."

**Enforcement Rules:**
- Player profile continuously updated (explicit + implicit signals)
- Tags have confidence weights and may decay over time
- Player modeling affects presentation only, NOT mechanics
- Explicit overrides trump inferred tags

**Implications:**
- M2 campaign state must include player profile schema
- M1 narration must query player profile for tone/pacing/explanation depth
- Player can always override (e.g., "Explain more", "Skip this")

---

## Section D: Preferences (Requires Documentation)

### D1. Solo-First (🔵 PREFERENCE)

**Source:** Execution Roadmap v3.1
**Statement:** "Multiplayer deferred."

**Rationale:** Simplifies initial implementation; multiplayer requires voice coordination, speaker diarization, turn arbitration.

---

### D2. Theatre-of-the-Mind Default (🔵 PREFERENCE)

**Source:** Execution Roadmap v3.1, Character Sheet UI Contract
**Statement:** "Grid appears only when spatial precision matters."

**Rationale:** Character sheet is primary UI; grid is contextual (appears for combat, disappears after).

---

### D3. UI Should Be Available, Not Demanding (🔵 PREFERENCE)

**Source:** Minimal UI Addendum
**Statement:** "Interface exists to support interaction, not to visually dominate it."

**Rationale:** Voice-first philosophy; text window is quiet, reliable fallback.

---

## Section E: CP-001 as Fixed Constraint

### E1. Position Type Unification (FROZEN)

**Status:** ✅ COMPLETE (1393 tests passing, TD-001 resolved)
**Treatment:** IMMOVABLE CONSTRAINT (per user directive)

**Frozen Contracts:**
- Canonical Position type at `aidm/schemas/position.py`
- Distance calculation: 1-2-1-2 diagonal movement (PHB p.148)
- Distance units: **feet** (multiples of 5), NOT squares
- Immutable: `frozen=True` dataclass (hashable, usable in sets/dicts)
- Adjacency: 8-directional (orthogonal + diagonal)
- Legacy types deprecated: GridPoint (intents.py, targeting.py), GridPosition (attack.py)
- Legacy removal deferred to CP-002 (BLOCKED pending audit approval)

**Integration Points:**
- ✅ StepMoveIntent uses Position (attack.py:149-153)
- ✅ All position tests use feet (test_position.py)
- ⚠️ M1 contextual grid must render Position (x, y) coordinates
- ⚠️ M2 NPC positions stored as Position, not legacy types
- ⚠️ CP-002 must complete legacy removal before M1 ships

---

## Section F: Constraint Conflicts & Resolutions

### F1. Detected Conflicts

**NONE.** All constraints from Roadmap and Inbox documents are mutually consistent.

### F2. Constraint Tensions (Require Design Attention)

1. **TTS Quality vs Hardware Baseline**
   - Constraint B3: TTS quality is critical
   - Constraint B2: Must run on median consumer hardware
   - Tension: High-quality TTS models may exceed baseline hardware
   - Resolution: M3 must evaluate TTS models for quality/footprint tradeoff

2. **Image Critique vs Prep Time**
   - Constraint B4: Prep-first generation
   - Constraint B5: Image critique required
   - Tension: Critique loops may extend prep time significantly
   - Resolution: Bounded regeneration attempts; accept "good enough" outputs

3. **Multi-Language Input vs Offline Execution**
   - Constraint C2: Multi-language input required
   - Constraint B2: Local-only execution
   - Tension: Multilingual STT models are large
   - Resolution: M3 must support language pack downloads OR single multilingual model OR graceful degradation

---

## Section G: Constraint Enforcement Checklist

Use this checklist during milestone implementation:

### M1 — Solo Vertical Slice v0
- [ ] Intent freeze BEFORE engine resolution (A2)
- [ ] Deterministic template narration fallback if LLM fails (A2)
- [ ] Event store is append-only (A4)
- [ ] Text input always available (C1)
- [ ] Memory indexing layer implemented (C3)
- [ ] Player profile queried for narration adaptation (C5)
- [ ] Position type used for all spatial calculations (E1)

### M2 — Campaign Prep Pipeline v0
- [ ] Canonical ID schema defined (A3)
- [ ] Skin Pack schema with validation (B1)
- [ ] Alias tables for multi-language input (C2)
- [ ] Prep-time asset generation orchestrated (B4)
- [ ] Asset logging with canonical IDs (B4)
- [ ] Player profile schema stored in campaign state (C5)

### M3 — Immersion Layer v1
- [ ] TTS quality prioritized over STT accuracy (B3)
- [ ] Image critique gate enforced (B5)
- [ ] Offline-compatible models selected (B2)
- [ ] Voice has text equivalents (C1)
- [ ] Dice customization expressive only (C4)
- [ ] Position (x, y) rendered on contextual grid (E1)

### M4 — Offline Packaging
- [ ] No cloud dependencies (B2)
- [ ] CPU fallback paths functional (B2)
- [ ] Hardware requirements documented (B2)
- [ ] Export/import preserves deterministic replay (A1)

---

## Section H: Constraint Violation Protocol

If a constraint must be violated:

1. **Sacred (🔴):** REQUIRES PROJECT HALT and architectural review
2. **Critical (🟠):** REQUIRES milestone replanning and PM approval
3. **Important (🟡):** REQUIRES explicit justification in design doc
4. **Preference (🔵):** REQUIRES documentation in milestone closeout

---

**END OF CONSTRAINT LEDGER**
