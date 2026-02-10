# Global Audit Action Plan Revisions
## Concrete Diffs to Integrate Inbox Requirements into Roadmap

**Audit Session:** GLOBAL-AUDIT-001
**Date:** 2026-02-10
**Target Document:** `docs/AIDM_EXECUTION_ROADMAP_V3.md`
**Proposed Version:** v3.2 (Post-Audit Integration)

---

## Purpose

This document proposes specific, actionable changes to the Execution Roadmap v3.1 to:
1. Integrate 7 Inbox design documents
2. Close 10 identified gaps (GAP-001 through GAP-010)
3. Mitigate 5 determinism risks (DET-001 through DET-005)
4. Resolve 3 constraint violations
5. Clarify 3 scope ambiguities

**Format:** Each revision is presented as a concrete diff that can be directly applied to the Roadmap.

---

## Section A: New Milestone Addition — M0.6

### A1. Rationale

**Gaps Addressed:** GAP-001 (Canonical IDs), GAP-002 (Skin Packs), GAP-003 (Alias Tables)
**Severity:** 🔴 CRITICAL (blocks M1, M2, M3)
**Constraint:** A3 (Canonical IDs are sacred), B1 (Mechanics/Presentation split)

**Justification:**
Canonical ID schema and Skin Pack architecture are foundational prerequisites for all milestones. Without these, M1 intent extraction, M2 entity generation, and M3 asset keying will invent ad-hoc entity representations, creating technical debt.

---

### A2. Proposed Diff

**Location:** After M0 section (lines 96-112), before M1 section (line 115)

```diff
---

 ## M0 — Design Closeout

 **Status:** ✅ COMPLETE

 ### Deliverables

 - [x] Updated design docs with agreed clarifications
 - [x] `DESIGN_LAYER_ADOPTION_RECORD.md` created
 - [x] `DOCUMENTATION_AUTHORITY_INDEX.md` updated
 - [x] Freeze declaration

 ### Acceptance Criteria

 - [x] All clarifications merged
 - [x] Authority index marks canonical docs
 - [x] Design layer declared frozen

 ---
+
+## M0.6 — Canonical Foundation Packet
+
+**Status:** NOT STARTED
+**Goal:** Define canonical ID schema, Skin Pack architecture, and alias table system as frozen baseline.
+
+### Deliverables
+
+1. **Canonical ID Schema**
+   - Document ID format and namespace conventions (e.g., `spell.fireball`, `item.longsword`, `monster.goblin`)
+   - Create authoritative ID registry for all mechanical entities:
+     - Items (weapons, armor, consumables)
+     - Spells and abilities
+     - Monsters and NPC archetypes
+     - Conditions and status effects
+     - Actions (attack, move, grapple, etc.)
+   - Define ID immutability rules (IDs never change; deprecated IDs remain valid)
+   - Specify ID namespacing to prevent collisions (e.g., `item.*`, `spell.*`, `condition.*`)
+
+2. **Skin Pack Schema**
+   - Define Skin Pack manifest format (JSON or YAML)
+   - Schema fields:
+     - `id`: Unique Skin Pack identifier (e.g., `fantasy-default`, `cyberpunk-reskin`)
+     - `display_names`: Map canonical IDs → localized display names
+     - `aliases`: Map input text/voice → canonical IDs (language-specific)
+     - `descriptions`: Short and long text for entities
+     - `tone_constraints`: Stylistic guidelines for LLM narration
+     - `visual_prompts`: Image generation prompts keyed to entity IDs
+     - `audio_profiles`: Sound and voice parameters keyed to entity IDs
+   - Define validation rules:
+     - Reject Skin Packs that attempt mechanical changes (damage, range, legality)
+     - Detect alias conflicts (two aliases map to different IDs)
+     - Verify all referenced canonical IDs exist in registry
+   - Define hot-swap rules (when can Skin Packs change mid-campaign?)
+
+3. **Alias Table System**
+   - Define alias table structure:
+     - Language-specific (e.g., English, French, Spanish)
+     - Case-insensitive matching
+     - Synonym handling (e.g., "long sword" and "longsword" → `item.longsword`)
+   - Ambiguity resolution:
+     - If multiple IDs match → trigger clarification dialogue
+     - Log ambiguous inputs for debugging
+   - Terminology locking:
+     - Once an alias is used in a session, lock it to prevent drift
+     - Example: If player says "Fireball" → `spell.fireball`, don't later resolve "Fireball" → `spell.meteor_swarm`
+
+4. **Documentation**
+   - `docs/CANONICAL_ID_REGISTRY.md` — Authoritative ID list
+   - `docs/SKIN_PACK_SCHEMA_V1.md` — Schema specification and examples
+   - `docs/ALIAS_TABLE_DESIGN.md` — Alias lookup and disambiguation rules
+
+### Acceptance Criteria
+
+- [ ] Canonical ID registry includes all baseline D&D 3.5e entities (weapons, spells, monsters, conditions)
+- [ ] Skin Pack schema validated with example: `fantasy-default.json`
+- [ ] Alias table supports English synonyms (e.g., "long sword", "longsword", "long-sword")
+- [ ] Validation rejects Skin Pack with mechanical change (e.g., changing fireball damage)
+- [ ] Validation detects alias conflict (e.g., "bow" → both `item.longbow` and `item.shortbow`)
+
+### Dependencies
+
+**Blocks:** M1.8 (intent extraction needs IDs), M2.1 (campaign schema needs Skin Pack refs), M3.7 (image gen needs IDs)
+**Depends on:** M0 (design layer frozen)
+
+---

 ## M1 — Solo Vertical Slice v0
```

---

## Section B: M1 Revisions

### B1. Add Player Profile to M1 Deliverables

**Gap Addressed:** GAP-004 (Player Profile Schema)
**Severity:** 🟠 HIGH

**Location:** M1 Deliverables section (lines 120-145)

```diff
 ### Deliverables

 1. **Runtime Skeleton**
    - Process boundaries: Engine / DM-LLM / UI / Store
    - Contract: `intent → engine → events → narration → UI`
    - Deterministic event store (append-only)

 2. **Intent Lifecycle Implementation**
    - States: `pending → clarifying → confirmed → resolved`
    - Store partial/clarifying intents
    - Freeze intent before engine resolution
    - Log clarification dialogue for audit/debug

 3. **Character Sheet UI v0**
    - Render base + persistent + derived + consumables
    - Subscribe to event stream for updates
    - Support "as-of turn" read-only history (minimal)
+   - Include mechanics ledger window:
+     - Lightweight scrollable panel (peripheral placement)
+     - Displays: dice type, raw roll, modifiers, final result
+     - Font size and contrast adjustable
+     - No interaction required (observe-only)

 4. **Voice/Text Input v0**
    - Text input with structured fallback templates
+   - Chat window UI pattern (MMO-style, bottom corner)
+   - Optional clickable text (spell names, items) — subtle, discoverable
    - STT adapter stub with same interface (plug later)

 5. **Narration v0**
    - If LLM present: narrate from engine events
    - If LLM missing/timeout: deterministic template narration
+   - Query player profile for tone, pacing, explanation depth
+   - Adaptive narration based on player preferences
+
+6. **Player Profile System**
+   - Define player profile schema with 5 dimensions:
+     - Experience level (new / experienced / system-mastery)
+     - Pacing (slow-ceremonial / balanced / fast-outcome)
+     - Explanation depth (teach-all / explain-when-needed / no-explanations)
+     - Tone preference (serious / playful / dark / cozy / dramatic)
+     - Modality (voice-first / text-first / mixed)
+   - Implement explicit tagging (DM asks questions, stores answers)
+   - Implement implicit inference (behavior signals → confidence-weighted tags)
+   - Player profile stored in campaign state (exported with campaign)
+   - Explicit overrides trump inferred tags ("Explain more", "Skip this")
+
+7. **Memory Indexing Layer**
+   - Structured records for: entity cards, event timeline, relationships, inventory
+   - LLM queries indexed records instead of holding state
+   - Session recap capability (DM can reference specific moments)
```

---

### B2. Add Onboarding to M1 Acceptance Criteria

**Gap Addressed:** GAP-006 (Onboarding Flow)
**Severity:** 🟠 HIGH

**Location:** M1 Acceptance Criteria (lines 146-153)

```diff
 ### Acceptance Criteria

 - [ ] Complete "declare → clarify → resolve → narrate → update sheet" loop
+- [ ] Onboarding flow functional:
+  - [ ] DM-first greeting on app launch
+  - [ ] Persona switch demo within first 60 seconds
+  - [ ] Dice ritual: visual dice + audio + customization (size, color, effects)
+  - [ ] Dice preferences persist across sessions
+  - [ ] Character creation as guided conversation (DM rolls stats, player assigns by intent)
 - [ ] Determinism replay passes (≥10×)
+  - [ ] Identical mechanics: dice results, damage, HP changes, positions
+  - [ ] Variable presentation: narration wording, tone, verbosity (allowed)
+  - [ ] Player profile included in replay inputs (campaign metadata)
 - [ ] Runtime within budget (<2s test suite)
 - [ ] No unauthorized file touches
 - [ ] No gate pressure
+- [ ] Canonical ID usage verified:
+  - [ ] All entity references use canonical IDs from M0.6 registry
+  - [ ] Alias table lookup functional (e.g., "long sword" → `item.longsword`)
+  - [ ] No hard-coded entity strings in engine code
+- [ ] Player profile queried by narration system
+- [ ] Mechanics ledger window visible and functional
+- [ ] Session recap functional (load campaign → DM recaps last session)
```

---

### B3. Add Tasks to M1 Supporting Tasks Table

**Gap Addressed:** GAP-004, GAP-005, GAP-006, GAP-009
**Severity:** 🟠 HIGH

**Location:** M1 Supporting Tasks table (lines 154-175)

```diff
 | M1.15 | Implement timeout handling |
 | M1.16 | Implement text fallback mode |
 | M1.17 | End-to-end integration test |
+| M1.18 | Implement player profile schema + query layer |
+| M1.19 | Implement mechanics ledger window |
+| M1.20 | Implement session recap system |
+| M1.21 | Implement memory indexing layer |
+| M1.22 | Implement DM-first onboarding flow |
+| M1.23 | Implement dice ritual + customization UI |
+| M1.24 | Implement character creation conversation |
```

---

## Section C: M2 Revisions

### C1. Add M2.0 Prerequisite (Canonical Foundation)

**Gap Addressed:** GAP-001, GAP-002, GAP-003 (already covered by M0.6 above)
**Note:** M2.0 is now M0.6 (moved earlier to unblock M1)

---

### C2. Clarify Asset Generation Scope in M2

**Gap Addressed:** GAP-010 (Sound Palette), DET-003 (Asset Seeding)
**Severity:** 🔴 CRITICAL (determinism risk)

**Location:** M2 Deliverables section (lines 183-208)

```diff
 3. **Asset Store + Reuse Rules**
    - Per-campaign asset directory
    - Optional shared "generic cache" (tavern, road, forest, etc.)
-   - Missing assets regenerate on demand (deterministic IDs)
+   - Asset generation strategy (CHOOSE ONE):
+     - **Option A (Deterministic Seeding):** Seed generation with canonical ID + campaign ID
+       - Enables reproducible generation without storing large files
+       - Requires deterministic image/audio models (verify before selecting)
+     - **Option B (Asset Export):** Store all generated assets in campaign export
+       - Guarantees identical replay (no generation variance)
+       - Increases export file size significantly
+     - **Option C (Hybrid Hashing):** Export asset manifests with hashes, regenerate on import, verify match
+       - Detects drift if generation is non-deterministic
+       - Requires hash verification logic in import flow
+   - Asset tagging and retrieval:
+     - All assets tagged with: canonical ID, type (portrait/backdrop/sound), generation timestamp
+     - Retrieval API: query by canonical ID (e.g., "get portrait for `monster.goblin`")
+     - Continuity enforcement: NPCs use static anchor images (generated once, reused)
+   - Sound palette generation during prep:
+     - Monster vocalizations (keyed to monster IDs)
+     - Weapon impact sounds (keyed to weapon IDs)
+     - UI stings (success/failure/level-up)
+     - Ambience loops (forest/dungeon/tavern)
+     - Music themes (exploration/combat/tension)
+   - Image generation during prep:
+     - NPC portraits (keyed to NPC IDs)
+     - Location backdrops (keyed to location IDs)

 4. **World Export/Import**
    - Export: manifests + events + assets (configurable)
+   - Export includes: Skin Pack references, canonical ID mappings, asset determinism strategy
    - Import restores identical play state
+   - Import validation:
+     - Verify Skin Pack compatibility (reject if Skin Pack alters mechanics)
+     - Verify canonical IDs exist (reject if unknown IDs referenced)
+     - Verify asset integrity (hash check if using Option C)
```

---

### C3. Update M2 Acceptance Criteria

**Gap Addressed:** DET-003, GAP-010
**Severity:** 🔴 CRITICAL

**Location:** M2 Acceptance Criteria (lines 204-209)

```diff
 ### Acceptance Criteria

 - [ ] Player can start a campaign, wait through prep, then begin session 1
 - [ ] Assets persist across sessions
 - [ ] Campaign can be exported and imported
 - [ ] Prep phase shows ambient feedback (not dead/frozen)
+- [ ] Deterministic asset replay verified:
+  - [ ] Export campaign → Import on different machine → Verify identical: NPC portraits, sounds
+  - [ ] OR: Document that asset appearance may vary (presentation layer variability)
+- [ ] Asset tagging verified:
+  - [ ] Query "get portrait for `monster.goblin`" returns correct image
+  - [ ] Asset retrieval API functional
+- [ ] Sound palette generated during prep (not runtime)
+- [ ] Skin Pack validation functional:
+  - [ ] Import rejects Skin Pack with mechanical changes
+  - [ ] Import detects alias conflicts
+- [ ] Prep contract messaging visible:
+  - [ ] DM tells player "Prep will take ~1 hour"
+  - [ ] Prep shows ambient visuals/audio (not frozen screen)
```

---

### C4. Add Tasks to M2 Supporting Tasks Table

**Gap Addressed:** GAP-010, DET-003
**Severity:** 🔴 CRITICAL

**Location:** M2 Supporting Tasks table (lines 222-239)

```diff
 | M2.11 | Implement world export |
 | M2.12 | Implement world import |
 | M2.13 | End-to-end preparation test |
+| M2.14 | Implement sound palette generation |
+| M2.15 | Implement asset tagging and retrieval API |
+| M2.16 | Implement Skin Pack import validation |
+| M2.17 | Implement asset determinism strategy (A, B, or C) |
+| M2.18 | Implement prep contract messaging UX |
```

---

## Section D: M3 Revisions

### D1. Add Image Critique to M3 Deliverables

**Gap Addressed:** GAP-007 (Image Critique)
**Severity:** 🔴 CRITICAL (violates constraint B5)

**Location:** M3 Deliverables, Image Pipeline section (lines 248-257)

```diff
 2. **Image Pipeline**
    - Local image generator adapter (or bundled placeholders)
    - NPC portraits + scene backdrops generated in prep
+   - Image critique pipeline:
+     - Heuristic checks: image size, aspect ratio, brightness/darkness
+     - Optional critic model: readability at UI size, centering, artifacting
+     - Bounded regeneration loop (max 3 attempts)
+     - Fallback: use placeholder image if all attempts fail
+   - Output caching keyed to canonical IDs (prevent drift)
+   - Continuity enforcement: NPCs use static anchor images (generated once)
    - No mechanical dependence on images
```

---

### D2. Add Player Artifacts to M3 Deliverables

**Gap Addressed:** GAP-008 (Player Artifacts)
**Severity:** 🟡 MEDIUM

**Location:** M3 Deliverables, after Contextual Grid section (lines 264-267)

```diff
 4. **Contextual Grid**
    - Grid appears only when spatial precision matters
    - Grid disappears when no longer needed
    - Theatre-of-the-mind is the default
+   - Grid uses Position (x, y) from `aidm.schemas.position` (CP-001 integration)
+   - Grid displays 1-2-1-2 diagonal distance correctly
+
+5. **Player-Owned Artifacts**
+   - Personal Notebook:
+     - Freeform drawing, handwritten-style text input, simple shapes
+     - Pen/brush/eraser tools (minimal, tactile UI)
+     - Non-authoritative (player memory, not objective truth)
+     - DM can add notes conversationally ("DM, make a note of that")
+   - Player Handbook:
+     - Searchable rules reference (indexed, glossary-style)
+     - Rephrased rule explanations (non-copyrighted)
+     - Clickable references from narration or ledger
+     - DM can direct players conversationally ("Check your handbook under 'Grappling'")
+   - Knowledge Tome:
+     - Living record of character knowledge (not system knowledge)
+     - Discovered monsters (descriptive, not full stat blocks)
+     - Learned spell effects (only if identified)
+     - Known locations, factions, NPCs
+     - Progressive detail (entries evolve with experience)
+   - All artifacts support text-only, screen-reader compatible, font size/contrast adjustable
```

---

### D3. Update M3 Acceptance Criteria

**Gap Addressed:** GAP-007, GAP-008
**Severity:** 🔴 CRITICAL (GAP-007), 🟡 MEDIUM (GAP-008)

**Location:** M3 Acceptance Criteria (lines 269-275)

```diff
 ### Acceptance Criteria

 - [ ] Offline voice I/O functional
 - [ ] Audio transitions tied to scene state
 - [ ] Images are atmospheric only (no mechanics depend on them)
+- [ ] Image quality verified:
+  - [ ] Generate 100 NPC portraits → 0 rejected on visual inspection
+  - [ ] Critique pipeline detects low-quality images and regenerates
+  - [ ] Critique loops are bounded (max 3 attempts, then fallback)
 - [ ] Grid appears for combat, disappears after
+- [ ] Grid uses CP-001 Position type (x, y coordinates)
+- [ ] Grid displays 1-2-1-2 diagonal distance correctly (PHB p.148)
 - [ ] Licensing/attribution record for bundled assets
+- [ ] Player artifacts functional:
+  - [ ] Notebook: draw, write, retrieve later
+  - [ ] Handbook: search "grappling", see rules explanation
+  - [ ] Knowledge Tome: shows only encountered monsters (not full bestiary)
```

---

### D4. Add Tasks to M3 Supporting Tasks Table

**Gap Addressed:** GAP-007, GAP-008
**Severity:** 🔴 CRITICAL (GAP-007), 🟡 MEDIUM (GAP-008)

**Location:** M3 Supporting Tasks table (lines 277-295)

```diff
 | M3.13 | Bundle initial sound effects |
 | M3.14 | Implement contextual grid renderer |
 | M3.15 | Implement grid show/hide logic |
+| M3.16 | Implement image critique pipeline (heuristics + optional critic model) |
+| M3.17 | Verify Position integration in grid renderer |
+| M3.18 | Implement personal notebook UI (pen/brush/eraser tools) |
+| M3.19 | Implement player handbook (searchable rules reference) |
+| M3.20 | Implement knowledge tome (progressive discovery system) |
+| M3.21 | Implement voice profile plugin schema |
```

---

## Section E: New Section Addition — Inbox Integration Record

### E1. Rationale

Add a section documenting which Inbox documents were integrated and where, for future auditability.

---

### E2. Proposed Diff

**Location:** After "References" section (line 415), before "Revision History" (line 419)

```diff
 ---

+## Inbox Integration Record
+
+This roadmap integrates requirements from 7 Inbox design documents processed during GLOBAL-AUDIT-001 (2026-02-10):
+
+| Inbox Document | Integration Points | Gaps Closed |
+|----------------|-------------------|-------------|
+| **Chronological Design Record** | M0.6 (canonical IDs), M3.16 (image critique), M4 (hardware tiers) | GAP-007 (critique gate) |
+| **Generative Presentation Architecture** | M0.6 (Skin Packs, canonical IDs, alias tables), M2.16 (import validation) | GAP-001, GAP-002, GAP-003 |
+| **Secondary Pass Audit Checklist** | M1.22-M1.24 (onboarding), M2.18 (prep contract), M3.16 (image critique) | GAP-006, GAP-007 |
+| **Player Modeling Specification** | M1.18 (player profile), M1 narration (adaptive) | GAP-004 |
+| **Transparent Mechanics Ledger** | M1.13 (ledger window), M1.19 (explicit task) | GAP-005 |
+| **Minimal UI Design Addendum** | M1.4 (chat window), M3 (accessibility) | None (clarifications) |
+| **Player Artifacts Specification** | M3.18-M3.20 (notebook, handbook, knowledge tome) | GAP-008 |
+
+**Determinism Risks Addressed:**
+- DET-003 (Asset Seeding): M2.17 requires explicit determinism strategy (Option A/B/C)
+- DET-002 (Player Modeling): M1.18 stores player profile in campaign metadata (part of replay inputs)
+
+**Constraint Violations Resolved:**
+- B5 (Image Critique): M3.16 adds critique pipeline
+- A3 (Canonical IDs): M0.6 defines canonical ID schema
+- B1 (Skin Packs): M0.6 defines Skin Pack schema
+
+---
+
 ## Revision History

 | Version | Date | Changes |
 |---------|------|---------|
 | 3.0 | 2026-02-09 | Initial v3 release |
 | 3.1 | 2026-02-09 | Adopted M0-M4 milestone naming, streamlined structure |
+| 3.2 | 2026-02-10 | Integrated 7 Inbox design docs (GLOBAL-AUDIT-001), added M0.6, expanded M1-M3 |

 ---
```

---

## Section F: Proposed Roadmap v3.2 Summary

### F1. Major Changes

| Change Type | Count | Examples |
|-------------|-------|----------|
| New Milestones | 1 | M0.6 (Canonical Foundation Packet) |
| New Deliverables | 7 | Player Profile, Ledger Window, Onboarding, Image Critique, Player Artifacts, Sound Palette, Skin Pack Validation |
| New Tasks | 17 | M1.18-M1.24, M2.14-M2.18, M3.16-M3.21 |
| Updated Acceptance Criteria | 3 | M1 (determinism + onboarding), M2 (asset determinism), M3 (image quality + Position integration) |
| Clarifications | 5 | M1.4 (chat window), M1.13 (ledger), M2.3 (asset tagging), M3.6 (critique), M3.14 (Position) |

---

### F2. Gaps Closed by Revisions

| Gap ID | Severity | Description | Closed By |
|--------|----------|-------------|-----------|
| GAP-001 | 🔴 CRITICAL | Canonical ID Schema | M0.6 deliverable 1 |
| GAP-002 | 🔴 CRITICAL | Skin Pack Schema | M0.6 deliverable 2 |
| GAP-003 | 🔴 CRITICAL | Alias Table System | M0.6 deliverable 3 |
| GAP-004 | 🟠 HIGH | Player Profile Schema | M1 deliverable 6 (new) |
| GAP-005 | 🟠 HIGH | Mechanics Ledger Window | M1.13 clarification + M1.19 task |
| GAP-006 | 🟠 HIGH | Onboarding Flow | M1.22-M1.24 tasks, M1 acceptance criteria |
| GAP-007 | 🔴 CRITICAL | Image Critique Pipeline | M3.16 task, M3 deliverable 2 expansion |
| GAP-008 | 🟡 MEDIUM | Player Artifacts | M3 deliverable 5 (new), M3.18-M3.20 tasks |
| GAP-009 | 🟡 MEDIUM | Session Recap | M1.20 task, M1 deliverable 7 (memory indexing) |
| GAP-010 | 🟡 MEDIUM | Sound Palette Timing | M2.14 task, M2 deliverable 3 expansion |

---

### F3. Determinism Risks Mitigated

| Risk ID | Threat | Mitigation |
|---------|--------|-----------|
| DET-001 | LLM narration variance | M1 acceptance criteria clarifies mechanics-only determinism |
| DET-002 | Player modeling affects replay | M1.18 stores profile in campaign metadata (replay input) |
| DET-003 | Asset generation non-determinism | M2.17 requires explicit strategy (A/B/C), M2 acceptance verifies |
| DET-004 | RNG stream mixing | ✅ Already handled in CP-001 baseline |
| DET-005 | Position float drift | ✅ Already handled in CP-001 (integer math) |

---

### F4. Constraint Violations Resolved

| Constraint | Violation | Resolution |
|------------|-----------|-----------|
| A3 (Canonical IDs) | Missing ID schema | M0.6 defines canonical ID registry |
| B1 (Skin Packs) | Missing Skin Pack schema | M0.6 defines Skin Pack architecture |
| B5 (Image Critique) | Generation without critique | M3.16 adds critique pipeline |
| C2 (Multi-Language) | No alias tables | M0.6 defines alias table system |
| C5 (Player Modeling) | No player profile | M1.18 implements player profile schema |

---

## Section G: Implementation Recommendations

### G1. Sequencing

**Critical Path:**
1. **M0.6 (Canonical Foundation)** — MUST complete before starting M1.8 or M2.1
2. **M1 with expanded scope** — Includes onboarding (enables real testing)
3. **M2 with asset strategy** — Choose determinism strategy (A/B/C) during planning
4. **M3 with critique + artifacts** — Quality gates enforce constraint B5

**Parallel Work Opportunities:**
- M1.18 (Player Profile) can develop in parallel with M1.1-M1.10 (intent lifecycle)
- M1.19 (Ledger Window) can develop in parallel with M1.13 (Character Sheet UI)
- M3.18-M3.20 (Player Artifacts) can develop in parallel with M3.1-M3.15 (voice/image/audio)

---

### G2. Acceptance Testing Focus

**M0.6 Tests:**
- Canonical ID registry is complete (all baseline entities covered)
- Skin Pack validation rejects mechanical changes
- Alias table resolves synonyms correctly

**M1 Tests:**
- Determinism replay: mechanics identical, narration may vary
- Onboarding flow completable in <5 minutes
- Player profile queried by narration system

**M2 Tests:**
- Asset determinism verified (export/import preserves or documents variance)
- Skin Pack import validation functional

**M3 Tests:**
- Image critique detects low-quality outputs
- Grid uses CP-001 Position type
- Player artifacts functional (notebook, handbook, tome)

---

### G3. Risk Monitoring

**During M1:**
- Monitor player profile implementation for inadvertent mechanical effects (VIOLATES C5)
- Monitor ledger window placement for visual intrusiveness (VIOLATES Minimal UI principle)

**During M2:**
- Monitor asset generation for determinism (DET-003 risk)
- Monitor Skin Pack import for mechanical smuggling (VIOLATES B1)

**During M3:**
- Monitor image critique for infinite loops (bounded to 3 attempts)
- Monitor grid renderer for CP-001 Position integration (VIOLATES E1 if ad-hoc coords used)

---

## Section H: Document Status

**Audit Completion:**
- ✅ DOC_INDEX.md (corpus inventory)
- ✅ CONSTRAINT_LEDGER.md (immovable constraints)
- ✅ CONSISTENCY_AUDIT.md (drift detection)
- ✅ GAP_AND_RISK_REGISTER.md (missing requirements)
- ✅ ACTION_PLAN_REVISIONS.md (this document)
- ⏭️ SYNTHESIS_AND_RECOMMENDATIONS.md (CP-002 go/no-go decision surface)

**Recommended Next Steps:**
1. Review proposed revisions with PM
2. Approve Roadmap v3.2 or request adjustments
3. Create SYNTHESIS_AND_RECOMMENDATIONS.md with CP-002 go/no-go decision
4. If approved: Begin M0.6 (Canonical Foundation Packet)

---

**END OF ACTION PLAN REVISIONS**
