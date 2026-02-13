# Global Audit Gap & Risk Register
## Missing Requirements and Determinism Threat Analysis

**Audit Session:** GLOBAL-AUDIT-001
**Date:** 2026-02-10
**Focus:** Gaps, determinism risks, constraint violations, unimplemented requirements

---

## Purpose

This register documents:
1. **Feature Gaps:** Requirements in Inbox not covered by Roadmap
2. **Determinism Risks:** Threats to replay-identical outcomes
3. **Constraint Violations:** Roadmap plans that violate frozen constraints
4. **Dependency Risks:** Missing prerequisites that block milestones
5. **Scope Ambiguity:** Unclear deliverables that may cause rework

---

## Risk Severity Legend

| Symbol | Severity | Impact | Response Time |
|--------|----------|--------|---------------|
| 🔴 | CRITICAL | Blocks milestone / violates sacred constraint | Immediate |
| 🟠 | HIGH | Degrades experience / violates critical constraint | Before milestone ships |
| 🟡 | MEDIUM | Missing feature / violates important constraint | During milestone |
| 🔵 | LOW | Enhancement / violates preference | Post-milestone |

---

## Section A: Determinism Risk Analysis

### A1. LLM Narration Non-Determinism (MANAGED)

**Risk ID:** DET-001
**Severity:** 🟡 MEDIUM (controlled)
**Status:** MITIGATED BY DESIGN

**Threat:**
LLM narration for identical events may produce different text across replays, breaking strict determinism.

**Mitigation:**
- Roadmap M1.12: "If LLM missing/timeout: deterministic template narration"
- Constraint A2 (Ledger): "LLM operates ONLY in presentation layer"
- Constraint A1: "Event logs are replayable independent of presentation layer"

**Resolution:**
✅ Determinism applies to MECHANICS only (rolls, outcomes, state).
✅ Narration is presentation layer (allowed to vary).
✅ Template fallback ensures gameplay continuity if LLM fails.

**Verification:**
- [ ] M1 replay tests verify identical: dice results, damage, HP changes, position
- [ ] M1 replay tests allow different: narration wording, tone, verbosity

---

### A2. Player Modeling Affects Narration (POTENTIAL THREAT)

**Risk ID:** DET-002
**Severity:** 🟡 MEDIUM
**Status:** REQUIRES DESIGN CLARIFICATION

**Threat:**
Player profile (experience level, pacing, tone preference) affects narration. If player profile changes between replays, narration differs. Does this violate determinism?

**Analysis:**
```
Scenario: Player A (new) attacks goblin
- Engine: d20=15+3=18, hit for 1d8+2=7 damage
- LLM: "You swing your sword and strike the goblin!" (simple)

Scenario: Player B (veteran) attacks goblin
- Engine: d20=15+3=18, hit for 1d8+2=7 damage (IDENTICAL)
- LLM: "18 vs AC 14, 7 damage" (terse)

Question: Is this determinism violation?
```

**Resolution:**
✅ NOT a violation IF player profile is stored in campaign state (part of replay inputs).
❌ IS a violation IF player profile affects mechanics (FORBIDDEN by constraint C5).

**Requirements:**
- Player profile MUST be campaign metadata (serialized in export)
- Player profile affects ONLY: tone, verbosity, explanation depth (presentation)
- Player profile CANNOT affect: dice outcomes, legality, damage (mechanics)

**Verification:**
- [ ] M2 campaign export includes player profile
- [ ] M1 narration tests verify player profile changes ONLY presentation (not outcomes)

---

### A3. Asset Generation Seeding (CRITICAL)

**Risk ID:** DET-003
**Severity:** 🔴 CRITICAL
**Status:** UNMITIGATED IN CURRENT ROADMAP

**Threat:**
NPC portraits, location backdrops generated during prep. If generation is seeded randomly, exporting and re-importing a campaign will produce DIFFERENT images for the same NPC.

**Constraint Violation:**
- Constraint B4: "Assets are archived, tagged, retrievable, reusable"
- Constraint A1: "Export/import preserves deterministic replay"

**Current Roadmap Gap:**
- M2.3 "Asset persistence" doesn't specify seeding strategy
- M2.11 "World export" doesn't specify if assets are exported or regenerated on import

**Required Solution:**
1. **Option A (Deterministic Generation):** Seed asset generation with canonical ID + campaign ID
   - Pro: Reproducible without storing images
   - Con: Requires deterministic image models (not guaranteed)

2. **Option B (Asset Export):** Store generated assets in campaign export
   - Pro: Guaranteed identical replay
   - Con: Large export file sizes

3. **Option C (Hybrid):** Export asset manifests with hashes; regenerate on import, verify hash match
   - Pro: Detects drift
   - Con: Complex; requires deterministic generation

**Recommendation:**
🔴 **CRITICAL FIX REQUIRED:** M2.11 must explicitly choose Option A, B, or C.
- If Option A: Add "deterministic seeding" requirement to M3.6-M3.7
- If Option B: Add "asset bundling" requirement to M2.11
- If Option C: Add "asset hashing + verification" to M2.11-M2.12

**Verification:**
- [ ] Export campaign → Import on different machine → Verify identical: NPC portraits, locations, sounds
- [ ] OR: Document that asset appearance may differ (presentation layer variability)

---

### A4. RNG Stream Isolation (VERIFIED ✅)

**Risk ID:** DET-004
**Severity:** 🟢 LOW (already handled)
**Status:** VERIFIED IN CP-001 BASELINE

**Threat:**
Mixed RNG streams (combat, initiative, saves) could cause non-deterministic outcomes if stream ordering changes.

**Mitigation:**
- CP-001 baseline: "RNG isolation verified (combat, initiative, saves streams)"
- Constraint A1: "All randomness seeded and logged"

**Resolution:**
✅ Existing 751 tests verify RNG isolation.
✅ No additional M1-M4 risks detected.

---

### A5. Position Distance Calculation (VERIFIED ✅)

**Risk ID:** DET-005
**Severity:** 🟢 LOW (already handled)
**Status:** VERIFIED IN CP-001

**Threat:**
Floating-point distance calculations could cause non-deterministic position checks (e.g., "is target in range?").

**Mitigation:**
- CP-001: Position.distance_to() uses pure integer math (1-2-1-2 diagonal)
- CP-001: Returns feet (multiples of 5), no float operations
- 34 Position tests verify deterministic distance

**Resolution:**
✅ No floating-point drift possible in position system.

---

## Section B: Feature Gap Analysis

### B1. Canonical ID Schema (🔴 CRITICAL GAP)

**Gap ID:** GAP-001
**Severity:** 🔴 CRITICAL
**Status:** MISSING FROM ROADMAP

**Description:**
Generative Presentation Architecture defines canonical IDs as foundation for all mechanics. Roadmap has NO deliverable defining the canonical ID schema.

**Blocking Impact:**
- M1.8 "Implement intent extraction" — what IDs does it extract?
- M2.5 "Implement NPC generation" — what IDs represent NPCs?
- M3.7 "Implement NPC portrait generation" — how to key portraits to NPCs?

**Constraint Violated:**
- Constraint A3: "All mechanically relevant entities must be defined by stable, language-agnostic identifiers"

**Required Fix:**
Add deliverable **M0.6** or **M2.0**: "Define Canonical ID Schema"
- Document ID format (e.g., `spell.fireball`, `item.longsword`, `monster.goblin`)
- Create ID registry (authoritative list)
- Define ID namespacing rules (prevent collisions)
- Specify ID immutability rules (can IDs ever change?)

**Verification:**
- [ ] All M1-M3 code references canonical IDs from registry
- [ ] No hard-coded entity strings in engine code

---

### B2. Skin Pack Schema (🔴 CRITICAL GAP)

**Gap ID:** GAP-002
**Severity:** 🔴 CRITICAL
**Status:** MISSING FROM ROADMAP

**Description:**
Generative Presentation Architecture defines Skin Packs as primary abstraction for presentation layer. Roadmap has NO deliverable defining Skin Pack schema.

**Blocking Impact:**
- M2.1 "Design campaign data schema" — does it include Skin Pack references?
- M2.11 "Implement world export" — are Skin Packs exported?
- M3 "Immersion Layer" — are voice profiles, image prompts stored in Skin Packs?

**Constraint Violated:**
- Constraint B1: "Skin Packs are declarative, validated, hot-swappable"

**Required Fix:**
Add deliverable **M2.0**: "Define Skin Pack Schema and Validation Rules"
- Skin Pack manifest format (JSON/YAML?)
- Fields: display names, aliases, descriptions, tone constraints, visual prompts, audio profiles
- Validation rules: reject mechanical changes, detect alias conflicts
- Import/export integration with M2.11-M2.12

**Verification:**
- [ ] M2.11 can export Skin Packs
- [ ] M2.12 can import and validate Skin Packs
- [ ] M3 voice/image generation queries Skin Pack for parameters

---

### B3. Alias Table System (🔴 CRITICAL GAP)

**Gap ID:** GAP-003
**Severity:** 🔴 CRITICAL
**Status:** MISSING FROM ROADMAP

**Description:**
Generative Presentation Architecture requires alias tables for multi-language input (e.g., "Fireball" / "Boule de Feu" / "Feuerball" → `spell.fireball`). Roadmap M1.8 "intent extraction" doesn't mention aliases.

**Blocking Impact:**
- M1.8 "Implement intent extraction" — how does it map "Fireball" → `spell.fireball`?
- M1.9 "Implement clarification loop" — how to handle alias ambiguity?
- M3.1-M3.2 "Local STT" — multilingual input requires alias lookup

**Constraint Violated:**
- Constraint C2: "Alias tables map localized input → canonical IDs"

**Required Fix:**
Expand **M1.8** to include alias table lookup:
- Load aliases from Skin Pack (if active) or default English aliases
- Map player input (text/voice) → canonical ID via alias table
- Handle ambiguity (multiple aliases match) → trigger M1.9 clarification

**Verification:**
- [ ] M1 can resolve "longsword" and "long sword" to `item.longsword`
- [ ] M3 can resolve French voice input "épée longue" to `item.longsword` (if French Skin Pack loaded)

---

### B4. Player Profile Schema (🟠 HIGH GAP)

**Gap ID:** GAP-004
**Severity:** 🟠 HIGH
**Status:** MISSING FROM ROADMAP

**Description:**
Player Modeling Specification defines persistent player profile with 5 dimensions (experience, pacing, explanation, tone, modality). Roadmap has NO deliverable for player profile storage or usage.

**Blocking Impact:**
- M1.12 "Implement narration generation" — how to adapt tone/verbosity without player profile?
- M2.1 "Design campaign data schema" — does campaign store player profile?

**Constraint Violated:**
- Constraint C5: "Player profile continuously updated and queried by DM"

**Required Fix:**
Add **M1.18**: "Implement Player Profile Schema + Query Layer"
- Define schema: 5 dimensions (experience, pacing, explanation, tone, modality)
- Implement explicit tagging (DM asks questions, stores answers)
- Implement implicit inference (behavior signals → update confidence-weighted tags)
- M1.12 narration queries profile for tone/verbosity/explanation depth
- M2.1 campaign schema includes player profile

**Verification:**
- [ ] M1 onboarding captures player preferences
- [ ] M1 narration adapts to player profile
- [ ] M2 export includes player profile

---

### B5. Mechanics Ledger Window (🟠 HIGH GAP)

**Gap ID:** GAP-005
**Severity:** 🟠 HIGH
**Status:** VAGUE IN ROADMAP (M1.13 may or may not include)

**Description:**
Transparent Mechanics Ledger defines mechanics output window (dice, modifiers, outcomes) as trust/fairness proof and teaching system. Roadmap M1.13 "basic character sheet UI" doesn't explicitly mention ledger.

**Blocking Impact:**
- M1 "complete loop" — without ledger, no visible proof of fairness
- New players have no passive learning mechanism

**Constraint Violated:**
- (Implicit) Secondary Audit requirement: "Trust requires visibility"

**Required Fix:**
Clarify **M1.13** to explicitly include ledger window:
- Lightweight scrollable panel showing: dice type, raw roll, modifiers, final result
- Peripheral placement (side or corner)
- Font size/contrast adjustable
- No interaction required (observe-only)

OR add **M1.19**: "Implement Mechanics Ledger Window"

**Verification:**
- [ ] M1 displays dice results in ledger
- [ ] Ledger shows modifier breakdown (e.g., "d20=14 +3[STR] +2[magic] = 19")
- [ ] Ledger is readable and non-intrusive

---

### B6. Onboarding Flow (🟠 HIGH GAP)

**Gap ID:** GAP-006
**Severity:** 🟠 HIGH
**Status:** MISSING FROM ROADMAP

**Description:**
Secondary Audit Checklist defines complete onboarding experience:
- DM-first greeting
- Persona switch demo (first 60 seconds)
- Dice ritual + customization
- Character creation as guided conversation
- Explicit prep contract

Roadmap M1 has NONE of this.

**Blocking Impact:**
- M1 acceptance: "complete loop" — what is the entry point for a new player?
- Without onboarding, M1 is a tech demo (not playable experience)

**Constraint Violated:**
- Secondary Audit: "Onboarding is gameplay (Session Zero)"
- Constraint C4: "Dice ritual is crucial (fairness + anticipation)"

**Required Fix:**
**Option A:** Add **M0.5** "Onboarding & Ceremony UX" before M1
- DM greeting, persona selection, dice customization
- Character creation conversation
- Explicit prep contract messaging

**Option B:** Expand **M1** scope to include onboarding (rename to "Solo Playable Experience v0")

**Option C:** Defer to **M3** (risk: M1/M2 testing without real UX)

**Recommendation:** Option A (M0.5) — onboarding is prerequisite for M1 testing.

**Verification:**
- [ ] New user launches app → DM greets → persona demo → dice customization → character creation → prep
- [ ] Onboarding takes <5 minutes before prep phase

---

### B7. Image Critique Pipeline (🔴 CRITICAL GAP)

**Gap ID:** GAP-007
**Severity:** 🔴 CRITICAL
**Status:** MISSING FROM M3

**Description:**
Chronological Design Record (Phase 4) and Secondary Audit both identify image critique as HARD REQUIREMENT: "Image generation without quality evaluation is unacceptable."

Roadmap M3.6 "Implement image generation adapter" doesn't mention critique.

**Blocking Impact:**
- M3 image generation without critique produces unusable outputs
- Breaks immersion immediately (per Chronological Phase 4)

**Constraint Violated:**
- Constraint B5: "Image generation MUST be paired with critique/quality evaluation"

**Required Fix:**
Expand **M3.6** to include critique pipeline:
- Heuristic checks: image size, aspect ratio, darkness/brightness
- Optional critic model: readability, centering, artifacting
- Bounded regeneration loop (e.g., max 3 attempts)
- Fallback: use placeholder image if all attempts fail

**Verification:**
- [ ] M3 generates 100 NPC portraits → 0 rejected on visual inspection
- [ ] M3 regenerates low-quality images automatically
- [ ] M3 doesn't loop infinitely on bad outputs

---

### B8. Player Artifacts (🟡 MEDIUM GAP)

**Gap ID:** GAP-008
**Severity:** 🟡 MEDIUM
**Status:** MISSING FROM M3

**Description:**
Player Artifacts Specification defines:
- Personal Notebook (freeform drawing, handwritten text)
- Player Handbook (rules reference, searchable)
- Knowledge Tome (progressive discovery)

Roadmap M3 has NO mention of these.

**Blocking Impact:**
- M3 delivers DM output (voice, images, audio) but no player-owned tools
- Missing emotional engagement and learning support systems

**Constraint Violated:**
- Player Artifacts Specification: "The player must own something. Not everything belongs to the DM."

**Required Fix:**
Add **M3.16-M3.18** or create **M3.5** "Player-Owned Artifacts":
- M3.16: Implement freeform notebook (pen/brush/eraser tools)
- M3.17: Implement searchable handbook (rules reference)
- M3.18: Implement knowledge tome (progressive NPC/monster discovery)

**Verification:**
- [ ] Player can draw in notebook, retrieve later
- [ ] Player can search handbook for "grappling" and see rules explanation
- [ ] Knowledge tome shows only encountered monsters (not full bestiary)

---

### B9. Session Recap Capability (🟡 MEDIUM GAP)

**Gap ID:** GAP-009
**Severity:** 🟡 MEDIUM
**Status:** MISSING FROM M1

**Description:**
Secondary Audit: "On launch, DM can recap prior sessions. DM can reference specific moments."

Roadmap has NO session recap deliverable.

**Blocking Impact:**
- Multi-session campaigns have no continuity reminder
- DM can't prove memory (trust issue)

**Constraint Violated:**
- Constraint C3: "Session recap as proof of memory"

**Required Fix:**
Add **M1.20** or **M2.14**: "Implement Session Recap System"
- Query event log for last session's key events
- DM narrates 2-3 sentence recap on campaign load
- Player can request detailed recap ("What happened with the goblins?")

**Verification:**
- [ ] Load campaign after 1 week → DM recaps last session
- [ ] Ask "What did I learn about the innkeeper?" → DM queries notes, responds

---

### B10. Sound Palette in M2 vs M3 (🟡 MEDIUM AMBIGUITY)

**Gap ID:** GAP-010
**Severity:** 🟡 MEDIUM
**Status:** UNCLEAR MILESTONE ASSIGNMENT

**Description:**
Constraint B4: "Prep-first asset generation" — sound should be generated during prep (M2).
Roadmap: Sound generation is in M3 "Immersion Layer."

Is this a contradiction?

**Analysis:**
- Prep-first means: generate assets during campaign prep (M2.2)
- M3 focus: integrate tools (STT, TTS, image gen, audio playback)

**Possible Interpretations:**
1. M2 generates sound palette → M3 implements playback/mixing
2. M3 generates sounds on-demand during gameplay (violates prep-first?)

**Required Clarification:**
Update M2 to include sound palette generation OR explicitly document that sound generation is deferred to M3 with live selection (not live generation).

**Recommendation:**
- M2.9 "Implement asset request system" should include sound palette generation
- M3.10-M3.12 should focus on playback and mixing (not generation)

---

## Section C: Constraint Violation Analysis

### C1. No Sacred Constraint Violations Detected ✅

**Analysis:**
- Roadmap preserves determinism (M1 acceptance criteria)
- Roadmap enforces engine/LLM split (M1.12 fallback templates)
- Roadmap uses event sourcing (M1.1)
- Roadmap respects gate closure (no G-T2+ mechanics)
- Roadmap is local-only (M4 offline packaging)

**Result:** ✅ No sacred constraint violations.

---

### C2. Critical Constraint Violations Detected

#### C2.1 Image Generation Without Critique (Violates B5)
**Severity:** 🔴 CRITICAL
**Violation:** M3.6 "image generation" without critique
**Fix:** See GAP-007 above

#### C2.2 Missing Canonical ID Schema (Violates A3)
**Severity:** 🔴 CRITICAL
**Violation:** M1-M3 entity references without canonical ID definition
**Fix:** See GAP-001 above

#### C2.3 Missing Skin Pack Schema (Violates B1)
**Severity:** 🔴 CRITICAL
**Violation:** Presentation layer implementation without Skin Pack architecture
**Fix:** See GAP-002 above

---

### C3. Important Constraint Violations Detected

#### C3.1 Multi-Language Input Not Addressed (Violates C2)
**Severity:** 🟡 IMPORTANT
**Violation:** M1.8 intent extraction, M3.1-M3.2 STT with no alias table system
**Fix:** See GAP-003 above

#### C3.2 Memory Indexing Implied but Not Explicit (Violates C3)
**Severity:** 🟡 IMPORTANT
**Violation:** M1.1 may include memory but not specified
**Fix:** Add explicit "memory indexing" task to M1.1 or create M1.21

---

## Section D: Dependency Risk Analysis

### D1. M1 Blocked by Missing Prerequisites

**Blocker:** Canonical ID Schema (GAP-001)
**Impact:** M1.8 intent extraction cannot proceed without knowing what IDs to extract
**Severity:** 🔴 CRITICAL
**Mitigation:** Add M0.6 or M2.0 BEFORE starting M1.8

---

### D2. M2 Blocked by Missing Prerequisites

**Blocker:** Skin Pack Schema (GAP-002)
**Impact:** M2.1 campaign schema, M2.11 export cannot proceed without Skin Pack definition
**Severity:** 🔴 CRITICAL
**Mitigation:** Add M2.0 BEFORE starting M2.1

**Blocker:** Canonical ID Schema (GAP-001)
**Impact:** M2.5 NPC generation, M2.6 location generation need IDs
**Severity:** 🔴 CRITICAL
**Mitigation:** Add M0.6 or M2.0 BEFORE starting M2.5-M2.6

---

### D3. M3 Blocked by Missing Prerequisites

**Blocker:** Canonical ID Schema (GAP-001)
**Impact:** M3.7 NPC portraits, M3.9 output caching need canonical ID keys
**Severity:** 🔴 CRITICAL
**Mitigation:** Ensure M2.0 completes before M3

**Blocker:** Skin Pack Schema (GAP-002)
**Impact:** M3.4 TTS voice profiles, M3.7 image prompts should come from Skin Packs
**Severity:** 🟠 HIGH
**Mitigation:** Ensure M2.0 completes before M3

---

### D4. M4 Not Blocked

**Analysis:** M4 depends on M1-M3 completion but no additional prerequisites.

---

## Section E: Scope Ambiguity Risks

### E1. "Basic Character Sheet UI" (M1.13) — Unclear Scope

**Ambiguity:** Does "basic" include:
- Ledger window? (Unclear)
- Inventory display? (Unclear)
- Spell list? (Unclear)
- Conditions/buffs? (Unclear)

**Risk:** Implementation may omit critical features, causing rework.

**Mitigation:** Define "basic" explicitly:
- Tier-1: HP, AC, stats, level (MUST)
- Tier-2: Ledger window, inventory (SHOULD)
- Tier-3: Spell list, conditions (DEFER to M2 or M3)

---

### E2. "Prep Job Orchestration" (M2.2) — Unclear Asset Types

**Ambiguity:** What assets are generated during prep?
- Images? (Assumed yes per M3 dependency)
- Sounds? (Unclear — M3 has audio tasks)
- Voice profiles? (Unclear)
- Text descriptions? (Assumed yes)

**Risk:** M2 may omit sound palette, causing M3 to violate prep-first constraint.

**Mitigation:** Clarify M2.2 to list all prep-generated assets:
- NPC portraits (images)
- Location backdrops (images)
- NPC voice profiles (voice)
- Sound palette (audio)
- Text descriptions (text)

---

### E3. "Contextual Grid" (M3.14-M3.15) — Position Integration

**Ambiguity:** M3.14 "Implement contextual grid renderer" — does it use CP-001 Position?

**Risk:** May implement ad-hoc coordinate system, violating CP-001 baseline.

**Mitigation:** Add acceptance criterion to M3.14:
- [ ] Grid renderer uses Position (x, y) from `aidm.schemas.position`
- [ ] Grid shows 1-2-1-2 diagonal distance correctly

---

## Section F: Gap Summary Table

| Gap ID | Severity | Description | Milestone | Fix Priority |
|--------|----------|-------------|-----------|--------------|
| GAP-001 | 🔴 CRITICAL | Canonical ID Schema missing | M0.6 or M2.0 | P0 |
| GAP-002 | 🔴 CRITICAL | Skin Pack Schema missing | M2.0 | P0 |
| GAP-003 | 🔴 CRITICAL | Alias Table System missing | M1.8 | P0 |
| GAP-004 | 🟠 HIGH | Player Profile Schema missing | M1.18 or M2.1 | P1 |
| GAP-005 | 🟠 HIGH | Mechanics Ledger Window vague | M1.13 or M1.19 | P1 |
| GAP-006 | 🟠 HIGH | Onboarding Flow missing | M0.5 or M1 | P1 |
| GAP-007 | 🔴 CRITICAL | Image Critique Pipeline missing | M3.6b | P0 |
| GAP-008 | 🟡 MEDIUM | Player Artifacts missing | M3.16-M3.18 | P2 |
| GAP-009 | 🟡 MEDIUM | Session Recap missing | M1.20 or M2.14 | P2 |
| GAP-010 | 🟡 MEDIUM | Sound Palette timing unclear | M2.9 or M3 | P2 |

---

## Section G: Risk Mitigation Recommendations

### G1. Immediate Actions (Before M1 Starts)

1. **Create Canonical Foundation Packet (M0.6)**
   - Define canonical ID schema
   - Define Skin Pack schema
   - Define alias table structure
   - Publish as frozen baseline (like CP-001)

2. **Clarify M1 Scope**
   - Add onboarding deliverables OR document as "technical loop only"
   - Add player profile schema OR defer to M2
   - Clarify ledger window inclusion OR add M1.19

3. **Update M1 Acceptance Criteria**
   - Add determinism replay tests (mechanics only, narration may vary)
   - Add canonical ID usage verification
   - Add player profile query verification (if included)

### G2. M2 Planning Actions

1. **Add M2.0 Deliverable: Canonical Foundation**
   - Define all schemas from G1.1
   - Must complete BEFORE M2.1 starts

2. **Clarify Asset Generation Scope**
   - Document which assets are prep-time vs runtime
   - Specify deterministic seeding strategy OR asset export strategy

3. **Update M2 Acceptance Criteria**
   - Add Skin Pack validation tests
   - Add asset determinism tests (export/import preserves appearance OR documents variance)

### G3. M3 Planning Actions

1. **Add Image Critique to M3.6**
   - Heuristic checks + optional critic model
   - Bounded regeneration loops

2. **Add Player Artifacts**
   - M3.16-M3.18 OR M3.5 deliverable

3. **Update M3 Acceptance Criteria**
   - Add image quality verification (no rejected portraits on inspection)
   - Add Position integration verification (grid uses CP-001 Position)

---

**END OF GAP & RISK REGISTER**
