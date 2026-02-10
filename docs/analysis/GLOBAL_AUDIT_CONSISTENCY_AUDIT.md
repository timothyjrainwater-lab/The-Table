# Global Audit Consistency Analysis
## Cross-Check: Roadmap vs Inbox for Drift, Conflicts, and Alignment

**Audit Session:** GLOBAL-AUDIT-001
**Date:** 2026-02-10
**Scope:** Execution Roadmap v3.1 vs 7 Inbox Design Documents

---

## Purpose

This document performs systematic cross-checks to detect:
1. **Drift:** Requirements in Inbox not reflected in Roadmap
2. **Conflicts:** Contradictory statements between documents
3. **Orphaned Requirements:** Inbox features with no Roadmap milestone
4. **Implicit Dependencies:** Inbox docs that affect Roadmap but aren't mentioned
5. **Version Alignment:** Ensure all docs reference same architectural baseline

---

## Executive Summary

**Overall Alignment:** 🟡 MOSTLY ALIGNED with SIGNIFICANT GAPS

**Key Findings:**
- ✅ **No architectural conflicts** detected (all docs consistent on core principles)
- ⚠️ **70+ micro-requirements** from Secondary Audit NOT in Roadmap acceptance criteria
- ⚠️ **4 major UX systems** (Player Artifacts, Player Modeling, Ledger, Minimal UI) NOT in Roadmap deliverables
- ⚠️ **Generative Presentation Architecture** (Skin Packs, canonical IDs) NOT in M2 deliverables
- ✅ Chronological Design Record aligns with Roadmap philosophy (historical record of decisions)

**Risk Assessment:**
- 🔴 HIGH: Secondary Audit checklist contains critical gates (image critique, asset logging) not in M2/M3
- 🟠 MEDIUM: Player Modeling affects M1 narration but not mentioned in M1 deliverables
- 🟠 MEDIUM: Transparent Ledger affects M1 UI but only vaguely mentioned
- 🟡 LOW: Player Artifacts can be added to M3 without major disruption

---

## Section A: Milestone-by-Milestone Consistency Check

### A1. M0 — Design Closeout

**Roadmap Status:** ✅ COMPLETE
**Inbox Alignment:** ✅ ALIGNED

**Findings:**
- Chronological Design Record documents 11 phases ending with research phase (aligns with M0 freeze)
- Generative Presentation Architecture emerged from Phase 1-2 insights (mechanics/presentation split)
- No conflicts detected

---

### A2. M1 — Solo Vertical Slice v0

**Roadmap Deliverables:**
1. Runtime Skeleton (Engine / DM-LLM / UI / Store)
2. Intent Lifecycle (pending → clarifying → confirmed → resolved)
3. Character Sheet UI v0 (base + persistent + derived + consumables)
4. Voice/Text Input v0 (text input + STT stub)
5. Narration v0 (LLM optional, deterministic template fallback)

**Inbox Cross-Check:**

#### A2.1 Player Modeling Specification
**Status:** ⚠️ MISSING FROM M1

**Inbox Requirements:**
- Persistent player profile (5 dimensions: experience, pacing, explanation depth, tone, modality)
- Continuous updating (explicit + implicit signals)
- Adaptive narration based on player profile

**Roadmap Gap:**
- M1.12 "Implement narration generation" has NO mention of player modeling
- No player profile schema in M1 deliverables
- No "query player profile" step in narration flow

**Drift Analysis:**
```
Inbox Says:               Roadmap Says:
┌──────────────────┐      ┌──────────────────┐
│ DM narration     │      │ Narration v0     │
│ must adapt to    │      │ (LLM optional)   │
│ player profile   │      │                  │
│ (tone, pacing,   │      │ No mention of    │
│ verbosity)       │      │ adaptation       │
└──────────────────┘      └──────────────────┘
```

**Impact:** MEDIUM
- Narration will feel generic/inconsistent without player modeling
- Onboarding may capture profile but narration won't use it
- Fix: Add M1.18 "Implement player profile schema + query layer"

---

#### A2.2 Transparent Mechanics Ledger
**Status:** ⚠️ PARTIALLY MISSING FROM M1

**Inbox Requirements:**
- Mechanics output window showing: dice results, modifiers, stat values, success/failure
- Lightweight, scrollable, peripheral placement
- Supports visual accessibility, trust/fairness proof, passive learning

**Roadmap Mention:**
- M1.13 "Implement basic character sheet UI" (vague — may or may not include ledger)

**Drift Analysis:**
```
Inbox Says:               Roadmap Says:
┌──────────────────┐      ┌──────────────────┐
│ Ledger window    │      │ Character Sheet  │
│ displays dice +  │      │ UI v0 (base +    │
│ modifiers for    │      │ persistent +     │
│ trust/fairness   │      │ derived)         │
│                  │      │                  │
│ Separate from    │      │ No explicit      │
│ character sheet  │      │ ledger mention   │
└──────────────────┘      └──────────────────┘
```

**Impact:** MEDIUM
- Without ledger, no trust/fairness proof (violates design intent)
- New players have no passive learning mechanism
- Fix: Clarify M1.13 to include ledger OR add M1.19 "Implement mechanics ledger window"

---

#### A2.3 Minimal UI Design Addendum
**Status:** ⚠️ PARTIALLY MISSING FROM M1

**Inbox Requirements:**
- Lightweight text interaction window (MMO-style chat)
- Clickable text (spell names, items, conditions) — subtle, discoverable
- Font customization, high-contrast modes

**Roadmap Mention:**
- M1.4 "Voice/Text Input v0" (mentions text input but not chat window)

**Drift Analysis:**
```
Inbox Says:               Roadmap Says:
┌──────────────────┐      ┌──────────────────┐
│ Chat window must │      │ Text input with  │
│ always be        │      │ structured       │
│ available        │      │ fallback         │
│ (accessibility)  │      │ templates        │
│                  │      │                  │
│ Clickable text   │      │ No mention of    │
│ for assistance   │      │ chat window or   │
│                  │      │ clickable text   │
└──────────────────┘      └──────────────────┘
```

**Impact:** LOW-MEDIUM
- Text input may be implemented as form fields instead of chat window
- Accessibility users may lack expected UI pattern
- Fix: Clarify M1.4 to specify "chat window" UI pattern

---

#### A2.4 Secondary Pass Audit Checklist — M1 Items
**Status:** 🔴 CRITICAL GAPS

**Inbox M1-Related Requirements NOT in Roadmap:**
1. **Intent Freeze Proof:** Clarification dialogue must be logged for audit/debug (M1.2 covers intent schema but not logging)
2. **Confirmation for High-Impact STT:** STT errors require confirmation flows (M1.9 covers clarification but not STT-specific safety)
3. **DM-First Onboarding:** DM speaks first, persona switch demo in first 60 seconds (NO onboarding flow in M1)
4. **Dice Ritual:** Visual dice + audio + customization (big/small, color, effects) — persist choices (NO dice UI in M1)
5. **Character Creation as Conversation:** DM rolls stats, player assigns by intent (NO character creation in M1)
6. **Session Recap on Launch:** DM greets user, offers recap/notes, discusses sheet changes (NO launch greeting in M1)

**Drift Analysis:**
- Roadmap M1 focuses on "declare intent → resolve → narrate → update sheet" technical loop
- Secondary Audit requires full Session Zero onboarding + dice ritual + launch greeting
- This is a **MAJOR SCOPE GAP** — M1 delivers technical loop but not player-facing experience

**Impact:** 🔴 HIGH
- M1 acceptance criteria say "complete loop" but don't define what "complete" means experientially
- Dice ritual is identified as critical trust-building mechanism (Chronological Phase 6)
- Without onboarding, M1 is a tech demo, not a playable experience

**Recommendation:**
- **Option A:** Add M0.5 "Onboarding & Ceremony UX" deliverable before M1
- **Option B:** Expand M1 to include onboarding (renames M1 → "Solo Playable Experience v0")
- **Option C:** Defer onboarding to M3 (risk: M1/M2 testing without real UX flow)

---

### A3. M2 — Campaign Prep Pipeline v0

**Roadmap Deliverables:**
1. Campaign Creation Contract (Session Zero config, version pinning)
2. Prep Job Orchestration (NPC/location/encounter generation, ambient feedback)
3. Asset Store + Reuse Rules (per-campaign + shared generic cache)
4. World Export/Import (manifests + events + assets)

**Inbox Cross-Check:**

#### A3.1 Generative Presentation Architecture
**Status:** 🔴 CRITICAL MISSING FROM M2

**Inbox Requirements:**
- **Skin Pack schema:** declarative bundles keyed to canonical IDs
- **Canonical ID schema:** all mechanical entities defined by stable IDs
- **Alias tables:** language-specific input mapping to canonical IDs
- **Import safety rules:** validation, rejection criteria
- **Terminology locking:** prevent synonym drift mid-session

**Roadmap Gap:**
- M2.1 "Design campaign data schema" does NOT mention Skin Packs or canonical IDs
- M2.5 "Implement NPC generation" has no canonical ID architecture
- M2.11/M2.12 "World export/import" has no mention of import validation rules

**Drift Analysis:**
```
Inbox Says:                      Roadmap Says:
┌───────────────────────┐        ┌───────────────────────┐
│ Skin Pack = primary   │        │ Campaign manifest +   │
│ abstraction for       │        │ assets + events       │
│ presentation layer    │        │                       │
│                       │        │ No Skin Pack schema   │
│ Canonical IDs are     │        │ No canonical ID def   │
│ foundation for all    │        │                       │
│ mechanics             │        │ No alias tables       │
│                       │        │                       │
│ Import validation     │        │ No import rules       │
│ REQUIRED for safety   │        │                       │
└───────────────────────┘        └───────────────────────┘
```

**Impact:** 🔴 CRITICAL
- M2 deliverables describe WHAT to generate (NPCs, locations) but not HOW to represent them
- Without canonical IDs, M2 implementation will invent ad-hoc entity keys → tech debt
- Without Skin Pack schema, presentation layer will be hard-coded → violates sacred constraint B1
- Without import validation, M2.12 "world import" is unsafe

**Recommendation:**
- **MANDATORY:** Add M2.0 "Define canonical ID schema + Skin Pack architecture" BEFORE M2.1
- Update M2.1 to reference canonical ID schema
- Update M2.11/M2.12 to include import validation using Skin Pack rules

---

#### A3.2 Secondary Pass Audit Checklist — M2 Items
**Status:** 🔴 CRITICAL GAPS

**Inbox M2-Related Requirements NOT in Roadmap:**
1. **Asset Logging & Reuse:** Generated assets must be archived, tagged, retrievable (M2.3 covers persistence but not tagging/retrieval API)
2. **Continuity Handling:** NPCs use static anchor images generated once, scenes use background plates (M2.5 mentions NPC generation but not continuity strategy)
3. **Prep Contract & Anticipation:** DM sets expectation for ~1 hour prep, "taste of possibility" reduces abandonment (NO user-facing prep messaging in M2)
4. **Image Critique Gate:** Image generation MUST be paired with quality evaluation (NO critique in M2 deliverables)
5. **Sound Palette Generation:** Generate and tag sound palette during prep (NO audio in M2 — deferred to M3)

**Drift Analysis:**
- Roadmap M2 focuses on prep orchestration infrastructure
- Secondary Audit requires user-facing prep experience + asset quality gates
- Image critique is identified as **hard requirement** but M2 has no image generation deliverables

**Impact:** 🟠 MEDIUM-HIGH
- M2.8 "Create preparation progress UX" is vague — needs explicit prep contract messaging
- Asset generation without critique violates sacred constraint B5
- Sound palette should be in M2 (prep-time) not M3 (immersion layer) per constraint B4

**Recommendation:**
- Add M2.13 "Implement image generation + critique pipeline" (if images in M2)
- OR ensure M3 image pipeline includes critique (if images deferred to M3)
- Clarify M2.8 to include explicit "prep contract" messaging per Secondary Audit

---

### A4. M3 — Immersion Layer v1

**Roadmap Deliverables:**
1. Voice Pipeline (local STT, local TTS)
2. Image Pipeline (generator, NPC portraits, scene backdrops)
3. Audio Pipeline (ambient, SFX, music)
4. Contextual Grid (appears/disappears per spatial precision need)

**Inbox Cross-Check:**

#### A4.1 Player Artifacts Specification
**Status:** ⚠️ MISSING FROM M3

**Inbox Requirements:**
- **Personal Notebook:** freeform drawing, handwritten text, doodling, non-authoritative
- **Player Handbook:** searchable rules reference, indexed, conversationally linked
- **Knowledge Tome:** progressive discovery, character knowledge (not system knowledge)

**Roadmap Gap:**
- M3 deliverables focus on DM output (voice, image, audio, grid)
- No player-owned artifacts in M3 deliverables

**Drift Analysis:**
```
Inbox Says:                      Roadmap Says:
┌───────────────────────┐        ┌───────────────────────┐
│ Player must own       │        │ Voice + Image +       │
│ artifacts:            │        │ Audio + Grid          │
│ - Notebook            │        │                       │
│ - Handbook            │        │ No player-owned       │
│ - Knowledge Tome      │        │ artifacts             │
│                       │        │                       │
│ "The player must own  │        │ (DM-centric focus)    │
│ something."           │        │                       │
└───────────────────────┘        └───────────────────────┘
```

**Impact:** 🟡 MEDIUM
- Player Artifacts are described as "foundational to immersion, learning, trust, emotional engagement"
- However, they are independent systems that don't block voice/image/audio implementation
- Can be added as M3 stretch goals or M3.5 deliverables

**Recommendation:**
- Add M3.16-M3.18 tasks for notebook, handbook, knowledge tome
- OR create M3.5 "Player-Owned Artifacts" mini-milestone after M3

---

#### A4.2 Secondary Pass Audit Checklist — M3 Items
**Status:** 🔴 CRITICAL GAPS

**Inbox M3-Related Requirements NOT in Roadmap:**
1. **Image Critique Checklists:** Readability at UI size, centering, artifacting, style adherence, identity match (M3.6-M3.9 mention generation but not critique)
2. **Bounded Regeneration Loops:** Avoid infinite critique loops (no mention in M3)
3. **Output Caching Keyed to Canonical IDs:** Prevent drift (M3.9 mentions caching but not canonical ID keying)
4. **Sound Selection/Mixing Runtime:** Runtime uses selection/mixing, not constant generation (M3.10-M3.12 unclear if runtime generates or selects)
5. **Voice Profiles as Plugins:** Importable/swappable without affecting mechanics (M3.3-M3.4 mention TTS but not plugin architecture)

**Drift Analysis:**
- Roadmap M3 focuses on integration of tools (STT, TTS, image gen, audio)
- Secondary Audit requires quality gates, plugin architectures, caching strategies
- This affects M3 ARCHITECTURE, not just features

**Impact:** 🟠 MEDIUM
- Image generation without critique violates constraint B5
- Audio generation vs selection affects runtime performance (prep-first constraint B4)
- Voice plugin architecture affects future Skin Pack extensibility

**Recommendation:**
- Expand M3.6 "Implement image generation adapter" → "...adapter + critique pipeline"
- Clarify M3.10-M3.12 audio tasks to specify "selection and mixing" (not live generation)
- Add M3.4b "Define voice profile plugin schema"

---

### A5. M4 — Offline Packaging + Shareability

**Roadmap Deliverables:**
1. Hardware Tiers (baseline, recommended, enhanced)
2. Version Pinning (campaign pins engine + model + tool versions)
3. Distribution (offline install, no cloud, no telemetry)

**Inbox Cross-Check:**

#### A5.1 Chronological Design Record — Hardware Reality Check
**Status:** ✅ ALIGNED

**Inbox Requirements (Phase 10):**
- System must run on median consumer hardware (Steam Hardware Survey)
- Model size and latency matter
- GPU cannot be assumed, CPU fallback required

**Roadmap Alignment:**
- M4 hardware tiers explicitly define baseline (CPU-only, 7B quantized)
- Matches Chronological Phase 10 intent

**No gaps detected.**

---

## Section B: Architectural Principle Alignment

### B1. Determinism

**Chronological Record:** Phase 1 insight (mechanics are invariant)
**Generative Presentation:** "Identical inputs → identical outputs" (sacred)
**Roadmap:** "Determinism is sacred" (M1 acceptance criteria includes replay test)

**Alignment:** ✅ PERFECT ALIGNMENT

---

### B2. Mechanics vs Presentation Split

**Chronological Record:** Phase 1-2 (if mechanics stable, fiction interchangeable)
**Generative Presentation:** "Engine defines reality; LLM describes reality"
**Roadmap:** "Authority split is sacred" (M1 enforces LLM cage)

**Alignment:** ✅ PERFECT ALIGNMENT

---

### B3. Prep-First Generation

**Chronological Record:** Phase 8 (sound as prep-time pipeline), Phase 5 (sprite model)
**Secondary Audit:** "Most generation during prep, not live play"
**Roadmap:** M2 entire milestone (prep pipeline)

**Alignment:** ✅ PERFECT ALIGNMENT

---

### B4. Voice-First Philosophy

**Chronological Record:** Phase 7 (voice output quality > input accuracy)
**Minimal UI:** "Voice remains primary; text is fallback"
**Roadmap:** M3.1-M3.4 (voice pipeline)

**Alignment:** ✅ ALIGNED (but text chat window clarity needed per A2.3)

---

### B5. Local-Only Execution

**Chronological Record:** Phase 10 (median hardware, no GPU assumed)
**Roadmap:** M4 (offline install, no cloud, no telemetry)

**Alignment:** ✅ PERFECT ALIGNMENT

---

## Section C: Feature Coverage Matrix

| Inbox Feature | M1 | M2 | M3 | M4 | Status |
|---------------|----|----|----|----|--------|
| **Core Engine** |
| Intent lifecycle | ✅ | - | - | - | M1.2-M1.10 |
| Event store | ✅ | - | - | - | M1.1 |
| Character sheet UI | ✅ | - | - | - | M1.13-M1.14 |
| Narration (LLM + fallback) | ✅ | - | - | - | M1.12 |
| **Canonical Architecture** |
| Canonical ID schema | ❌ | 🔴 | - | - | MISSING (should be M2.0) |
| Skin Pack schema | ❌ | 🔴 | - | - | MISSING (should be M2.0) |
| Alias tables | ❌ | 🔴 | - | - | MISSING (should be M2.1) |
| Import validation | ❌ | 🔴 | - | - | MISSING (should be M2.11-M2.12) |
| **Player Modeling** |
| Player profile schema | ⚠️ | ⚠️ | - | - | MISSING (should be M1 or M2) |
| Adaptive narration | ⚠️ | - | - | - | MISSING (should be M1.12) |
| **Onboarding & UX** |
| DM-first greeting | ❌ | - | - | - | MISSING (should be M1 or M0.5) |
| Persona switch demo | ❌ | - | - | - | MISSING (should be M1 or M0.5) |
| Dice ritual + customization | ❌ | - | - | - | MISSING (should be M1) |
| Character creation convo | ❌ | - | - | - | MISSING (should be M1 or M2) |
| Session recap on launch | ❌ | - | - | - | MISSING (should be M1) |
| **Trust & Learning** |
| Mechanics ledger window | ⚠️ | - | - | - | VAGUE (M1.13 may or may not include) |
| Clickable text assistance | ⚠️ | - | - | - | VAGUE (M1.4 doesn't specify) |
| **Memory & Indexing** |
| Memory indexing layer | ⚠️ | - | - | - | IMPLIED (M1.1 may include) |
| Entity cards | - | ⚠️ | - | - | VAGUE (M2.1 may include) |
| Session recap capability | ❌ | - | - | - | MISSING |
| **Prep Pipeline** |
| Campaign manifest | - | ✅ | - | - | M2.1-M2.2 |
| NPC generation | - | ✅ | - | - | M2.5 |
| Location generation | - | ✅ | - | - | M2.6 |
| Encounter scaffolding | - | ✅ | - | - | M2.7 |
| Asset persistence | - | ✅ | - | - | M2.3 |
| Prep progress UX | - | ✅ | - | - | M2.8 |
| Asset tagging/retrieval | - | ⚠️ | - | - | PARTIAL (M2.3 doesn't specify tagging) |
| **Image Pipeline** |
| Image generation | - | - | ✅ | - | M3.6 |
| Image critique | - | - | 🔴 | - | MISSING (should be M3.6b) |
| NPC portrait continuity | - | - | ⚠️ | - | VAGUE (M3.7 doesn't specify static anchors) |
| Output caching | - | - | ✅ | - | M3.9 |
| **Audio Pipeline** |
| Ambient sound | - | - | ✅ | - | M3.11 |
| SFX library | - | - | ✅ | - | M3.13 |
| Music transitions | - | - | ✅ | - | M3.12 |
| Sound palette prep | - | 🟠 | ⚠️ | - | UNCLEAR (should be M2, not M3?) |
| **Voice Pipeline** |
| Local STT | - | - | ✅ | - | M3.1-M3.2 |
| Local TTS | - | - | ✅ | - | M3.3-M3.4 |
| Voice profile plugins | - | - | ⚠️ | - | VAGUE (M3.4 doesn't specify plugin schema) |
| Multilingual STT | - | - | ⚠️ | - | UNCLEAR (deferred or included?) |
| **Player Artifacts** |
| Personal notebook | - | - | ❌ | - | MISSING (should be M3.16?) |
| Player handbook | - | - | ❌ | - | MISSING (should be M3.17?) |
| Knowledge tome | - | - | ❌ | - | MISSING (should be M3.18?) |
| **Contextual Grid** |
| Grid renderer | - | - | ✅ | - | M3.14 |
| Show/hide logic | - | - | ✅ | - | M3.15 |
| Position (x,y) integration | - | - | ⚠️ | - | IMPLIED (must use CP-001 Position) |
| **Packaging** |
| Hardware tiers | - | - | - | ✅ | M4 deliverable 1 |
| Version pinning | - | - | - | ✅ | M4 deliverable 2 |
| Offline install | - | - | - | ✅ | M4 deliverable 3 |

**Legend:**
- ✅ Explicitly covered in milestone
- ⚠️ Vaguely mentioned or implied
- 🔴 Critical missing feature (violates constraint)
- 🟠 Important missing feature (violates design intent)
- ❌ Not mentioned at all

---

## Section D: Critical Gaps Summary

### D1. Must-Fix Before M1 Ships

1. **Canonical ID Schema** (🔴 CRITICAL)
   - Blocks: M1 intent resolution, M2 entity generation, M3 asset keying
   - Action: Add M0.6 "Define canonical ID schema" OR M2.0

2. **Player Profile Schema** (🟠 MEDIUM)
   - Blocks: M1 adaptive narration, player modeling
   - Action: Add to M1.2 Intent Object schema OR create M1.18

3. **Mechanics Ledger Window** (🟠 MEDIUM)
   - Blocks: Trust/fairness proof, passive learning
   - Action: Clarify M1.13 to include ledger OR add M1.19

4. **Image Critique Gate** (🔴 CRITICAL)
   - Blocks: Quality assurance, violates constraint B5
   - Action: Add M3.6b "Implement image critique pipeline"

5. **Onboarding Flow** (🟠 MEDIUM-HIGH)
   - Blocks: M1 acceptance ("complete loop" ambiguous without onboarding)
   - Action: Add M0.5 OR expand M1 scope to include onboarding

### D2. Should-Fix Before M2 Ships

1. **Skin Pack Schema** (🔴 CRITICAL)
   - Blocks: Presentation layer extensibility, import safety
   - Action: Add M2.0 "Define Skin Pack architecture"

2. **Asset Tagging/Retrieval** (🟠 MEDIUM)
   - Blocks: Asset reuse, continuity
   - Action: Expand M2.3 to include tagging API

3. **Prep Contract Messaging** (🟡 LOW-MEDIUM)
   - Blocks: User expectation management
   - Action: Clarify M2.8 to include explicit prep messaging

### D3. Should-Fix Before M3 Ships

1. **Voice Profile Plugin Schema** (🟡 MEDIUM)
   - Blocks: Future voice extensibility
   - Action: Add M3.4b "Define voice profile plugin architecture"

2. **Player Artifacts** (🟡 MEDIUM)
   - Blocks: Emotional engagement, learning support
   - Action: Add M3.16-M3.18 OR create M3.5

3. **Sound Palette Prep** (🟡 LOW)
   - Blocks: Prep-first constraint adherence
   - Action: Clarify if sound generation belongs in M2 or M3

---

## Section E: Recommendations

### E1. Immediate Actions (Before Any Milestone Work)

1. **Create Canonical Foundation Packet (M0.6 or M2.0)**
   - Define canonical ID schema for: items, spells, monsters, conditions, actions
   - Define Skin Pack schema with validation rules
   - Define alias table structure for multi-language input
   - Publish as authoritative baseline (like CP-001)

2. **Clarify M1 Scope Ambiguity**
   - EITHER: Expand M1 to include onboarding (renames to "Solo Playable Experience v0")
   - OR: Create M0.5 "Onboarding & Ceremony UX" before M1
   - OR: Explicitly document M1 as "technical loop only" (no player-facing UX)

3. **Integrate Secondary Audit Checklist**
   - Extract all 70+ micro-requirements
   - Map to specific milestone acceptance criteria
   - Flag critical gates (image critique, asset logging, dice ritual)

### E2. Roadmap Revision Priorities

| Priority | Change | Rationale |
|----------|--------|-----------|
| 🔴 P0 | Add canonical ID + Skin Pack schema (M2.0 or M0.6) | Blocks all entity generation |
| 🔴 P0 | Add image critique to M3.6 | Violates sacred constraint B5 |
| 🟠 P1 | Clarify M1 scope (onboarding vs technical loop) | Acceptance criteria ambiguous |
| 🟠 P1 | Add player profile to M1 or M2 | Required for adaptive narration |
| 🟠 P1 | Clarify mechanics ledger in M1.13 | Trust/fairness proof missing |
| 🟡 P2 | Add player artifacts to M3 | Emotional engagement system |
| 🟡 P2 | Clarify asset tagging in M2.3 | Reuse strategy unclear |
| 🟡 P2 | Clarify sound palette timing (M2 vs M3) | Prep-first constraint alignment |

---

## Section F: Version Alignment Check

### F1. CP-001 Integration

**Status:** ✅ VERIFIED

All documents reference tactical combat and spatial positioning, consistent with CP-001's Position type:
- Chronological Record: Phase 5 (sprite/portrait model implies positioning)
- Generative Presentation: Canonical IDs include "Actions" (movement is an action)
- Secondary Audit: "Contextual grid" requires position rendering
- Roadmap M3.14-M3.15: Contextual grid deliverables

**No conflicts with CP-001's (x, y) integer coordinate system or 1-2-1-2 diagonal distance.**

### F2. Design Layer Freeze

**Status:** ⚠️ PARTIAL ALIGNMENT

- Roadmap references 6 canonical design docs (Session Zero, Character Sheet UI, etc.)
- These docs are marked as adopted in `DESIGN_LAYER_ADOPTION_RECORD.md`
- However, Inbox docs are NEW inputs NOT in adoption record
- Question: Are Inbox docs **additions** to frozen design layer, or **clarifications** of already-adopted principles?

**Recommendation:** Treat Inbox docs as **elaborations** of adopted design principles (not new philosophy). Integration into Roadmap does NOT require unfreezing design layer—just adding detail to implementation plan.

---

**END OF CONSISTENCY AUDIT**
