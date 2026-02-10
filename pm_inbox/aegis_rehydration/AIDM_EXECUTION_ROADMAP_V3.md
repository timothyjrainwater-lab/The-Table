# AIDM Execution Roadmap v3.2
## Milestone-Driven Implementation Plan

**Document ID:** EXEC-ROADMAP-V3
**Version:** 3.2.0
**Date:** 2026-02-11
**Status:** CANONICAL (Supersedes Action Plan v2.0)
**Authority:** Binding Project Specification
**Changelog:**
- v3.2.0 (2026-02-11): Updated M3 Audio Pipeline language to clarify generative-primary strategy for music (ACE-Step) with curated fallback, based on R1 Technology Stack Validation findings
- v3.1.1 (2026-02-10): Original post-M0 version

> **REHYDRATION COPY:** After editing this file, also update `pm_inbox/aegis_rehydration/AIDM_EXECUTION_ROADMAP_V3.md`

---

## STATUS NOTICE

This document supersedes `AIDM_PROJECT_ACTION_PLAN_V2.md` following:
- Completion of CP-20 (Discrete Environmental Damage)
- Adoption of six core design documents into the authority index
- Strategic realignment toward solo-first, voice-first, prep-first product vision
- Design layer formally FROZEN (see `DESIGN_LAYER_ADOPTION_RECORD.md`)

---

## Non-Negotiables (Reaffirmed)

1. **Determinism is sacred.** Engine outcomes must be replay-identical under identical inputs.
2. **Authority split is sacred.** Engine defines reality; LLM describes reality.
3. **Gates remain closed unless explicitly opened.** Current operating gate: **G-T1 only**.
4. **Design layer is frozen.** No philosophical relitigation during build.
5. **Solo-first, prep-first, voice-first.** Grid is contextual; sheet is primary UI.

---

## Project State Summary

### What Exists (Completed)

**Deterministic Rules Engine (Layer 1):**
- CP-09 through CP-20: FROZEN
- 751 tests passing in <2 seconds
- Determinism verified (10× replay)
- RNG isolation verified (combat, initiative, saves streams)
- Event sourcing verified (all mutations via events)

**Design Doctrine (FROZEN):**
- Six canonical design documents adopted
- Design Layer Adoption Record created
- No changes without formal amendment

### What Does Not Exist Yet

- LLM integration runtime
- Voice I/O subsystem
- Campaign preparation pipeline
- Image/audio generation tooling
- Character sheet UI renderer
- Contextual grid renderer
- World export/import

---

## Milestone Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  M0 — Design Closeout                                           │
│  Batch clarification edits, adoption record, freeze declaration │
│  Status: ✅ COMPLETE                                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  M1 — Solo Vertical Slice v0                                    │
│  Intent → Clarification → Resolution → Narration → Sheet Update │
│  Status: NOT STARTED                                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  M2 — Campaign Prep Pipeline v0                                 │
│  Session Zero → Prep Phase → Assets → Playable Session          │
│  Status: PERSISTENCE LAYER COMPLETE (v1.1)                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  M3 — Immersion Layer v1                                        │
│  Local Voice + Images + Audio + Contextual Grid                 │
│  Status: NOT STARTED                                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  M4 — Offline Packaging + Shareability                          │
│  Single-machine bundle, world export/import                     │
│  Status: NOT STARTED                                            │
└─────────────────────────────────────────────────────────────────┘
```

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

## M1 — Solo Vertical Slice v0

**Status:** NOT STARTED
**Goal:** Player can declare intent (text/voice), get clarification, engine resolves, narration delivered, sheet updates.

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

4. **Voice/Text Input v0**
   - Text input with structured fallback templates
   - STT adapter stub with same interface (plug later)

5. **Narration v0**
   - If LLM present: narrate from engine events
   - If LLM missing/timeout: deterministic template narration

### Acceptance Criteria

- [ ] Complete "declare → clarify → resolve → narrate → update sheet" loop
- [ ] Determinism replay passes (≥10×)
- [ ] Runtime within budget (<2s test suite)
- [ ] No unauthorized file touches
- [ ] No gate pressure

### Supporting Tasks

| Task | Description |
|------|-------------|
| M1.1 | Define inter-process communication protocol |
| M1.2 | Create Intent Object schema |
| M1.3 | Create Engine Result schema |
| M1.4 | Create Narration Request/Response schema |
| M1.5 | Define LLM context window contract |
| M1.6 | Define LLM failure mode handlers |
| M1.7 | Create process launcher skeleton |
| M1.8 | Implement intent extraction from natural language |
| M1.9 | Implement clarification loop |
| M1.10 | Implement intent confirmation flow |
| M1.11 | Connect intent to engine resolution |
| M1.12 | Implement narration generation |
| M1.13 | Implement basic character sheet UI |
| M1.14 | Connect UI to event stream |
| M1.15 | Implement timeout handling |
| M1.16 | Implement text fallback mode |
| M1.17 | End-to-end integration test |

---

## M2 — Campaign Prep Pipeline v0

**Status:** PERSISTENCE LAYER COMPLETE (v1.1)
**Goal:** "Start Campaign" triggers a preparation phase producing campaign scaffolding + assets.

**Architecture Status:** M2 Persistence Architecture is **FROZEN** (v1.1 — see `pm_inbox/reviewed/SONNET_WO-M2-01_M2_PERSISTENCE_ARCHITECTURE_FREEZE.md`)

**Amendment Note (2026-02-10):** Files `aidm/core/event_log.py` and `aidm/core/session_log.py` were modified during WO-M1-02 (BL-017/018 remediation). Changes documented in M2 freeze amendment 1.1. No schema changes, determinism improvements only.

### Deliverables

1. **Campaign Creation Contract**
   - Session Zero config captured and versioned
   - Campaign manifest created (pins engine + model + tool versions)

2. **Prep Job Orchestration**
   - Queue of prep tasks (NPCs, factions, locations, encounters)
   - User-facing prep status (ambient feedback, not necessarily %)
   - Ambient visuals/audio during prep (avoid "frozen" feel)

3. **Asset Store + Reuse Rules**
   - Per-campaign asset directory
   - Optional shared "generic cache" (tavern, road, forest, etc.)
   - Missing assets regenerate on demand (deterministic IDs)

4. **World Export/Import**
   - Export: manifests + events + assets (configurable)
   - Import restores identical play state

### Acceptance Criteria

- [ ] Player can start a campaign, wait through prep, then begin session 1
- [ ] Assets persist across sessions
- [ ] Campaign can be exported and imported
- [ ] Prep phase shows ambient feedback (not dead/frozen)

### Asset Generation Clarifications

**Reuse Strategy:**
- Generic images (tavern, road, forest) are shared across campaigns
- Character portraits regenerated on-demand based on NPC templates
- Music and sound effects curated but can be generated based on scene tone

**Audio Sourcing:**
- Local music generation prioritizes sound design integrity
- Avoid direct mimicry of copyrighted works
- Sound effects curated from public domain or licensed assets

### Supporting Tasks

| Task | Description |
|------|-------------|
| M2.1 | Design campaign data schema |
| M2.2 | Implement Session Zero loader |
| M2.3 | Implement campaign persistence |
| M2.4 | Implement DM Agent orchestrator |
| M2.5 | Implement NPC generation |
| M2.6 | Implement location generation |
| M2.7 | Implement encounter scaffolding |
| M2.8 | Create preparation progress UX |
| M2.9 | Implement asset request system |
| M2.10 | Implement campaign resume flow |
| M2.11 | Implement world export |
| M2.12 | Implement world import |
| M2.13 | End-to-end preparation test |

---

## M3 — Immersion Layer v1

**Status:** NOT STARTED
**Goal:** Add atmosphere without turning into a video game UI.

### Deliverables

1. **Voice Pipeline**
   - Local STT adapter (pluggable)
   - Local TTS voice persona

2. **Image Pipeline**
   - Local image generator adapter (or bundled placeholders)
   - NPC portraits + scene backdrops generated in prep
   - No mechanical dependence on images

3. **Audio Pipeline**
   - **Music:** AI-generated (ACE-Step) during prep for capable hardware (≥6 GB VRAM); curated royalty-free library as fallback for minimum spec
   - **SFX:** Curated library (primary); generative remains blocked by licensing until permissively-licensed model emerges
   - Licensing/attribution tracked for bundled assets via `AttributionLedger`

4. **Contextual Grid**
   - Grid appears only when spatial precision matters
   - Grid disappears when no longer needed
   - Theatre-of-the-mind is the default

### Acceptance Criteria

- [ ] Offline voice I/O functional
- [ ] Audio transitions tied to scene state
- [ ] Images are atmospheric only (no mechanics depend on them)
- [ ] Grid appears for combat, disappears after
- [ ] Licensing/attribution record for bundled assets

### Supporting Tasks

| Task | Description |
|------|-------------|
| M3.1 | Evaluate and select local STT library |
| M3.2 | Integrate STT adapter |
| M3.3 | Evaluate and select local TTS library |
| M3.4 | Integrate TTS adapter |
| M3.5 | Evaluate and select local image generation |
| M3.6 | Implement image generation adapter |
| M3.7 | Implement NPC portrait generation |
| M3.8 | Implement location backdrop generation |
| M3.9 | Implement image caching |
| M3.10 | Integrate audio playback system |
| M3.11 | Implement ambient sound selection |
| M3.12 | Implement music transitions |
| M3.13 | Bundle initial sound effects |
| M3.14 | Implement contextual grid renderer |
| M3.15 | Implement grid show/hide logic |

---

## M4 — Offline Packaging + Shareability

**Status:** NOT STARTED
**Goal:** A single-machine bundle that someone else can run.

### Deliverables

1. **Hardware Tiers**
   - Baseline: CPU-only, smaller model (7B quantized), text
   - Recommended: GPU, 7B–13B model, voice
   - Document expected disk footprint

2. **Version Pinning**
   - Campaign pins engine + model + tool versions
   - Upgrades don't invalidate old logs

3. **Distribution**
   - Offline install or single-directory bundle
   - No cloud dependencies
   - No telemetry

### Acceptance Criteria

- [ ] Offline install works on fresh machine
- [ ] Export/import preserves deterministic replay
- [ ] Hardware requirements documented
- [ ] Version pinning verified

### Hardware Requirements

| Tier | LLM Size | RAM | Storage | GPU |
|------|----------|-----|---------|-----|
| Baseline | 7B (quantized) | 16GB | 20GB | Optional (CPU inference) |
| Recommended | 13B | 32GB | 40GB | 8GB VRAM |
| Enhanced | 30B+ | 64GB+ | 80GB+ | 16GB+ VRAM |

---

## Capability Gates & Constraints

### Current Gate Status

| Gate | Name | Status |
|------|------|--------|
| G-T1 | Tier 1 Mechanics | ✅ OPEN |
| G-T2A | Permanent Stat Mutation | 🔒 CLOSED |
| G-T2B | XP Economy | 🔒 CLOSED |
| G-T3A | Entity Forking | 🔒 CLOSED |
| G-T3B | Agency Delegation | 🔒 CLOSED |
| G-T3C | Relational Conditions | 🔒 CLOSED |
| G-T3D | Transformation History | 🔒 CLOSED |

### Constraint Enforcement

All implementation must respect:
1. **Gate Compliance**: No mechanics requiring closed gates
2. **Determinism**: Identical inputs → identical outputs
3. **Event Sourcing**: All state changes via events
4. **LLM Cage**: LLM cannot override engine results
5. **Local Execution**: No cloud dependencies

---

## Explicit Deferrals (Do Not Do)

- ❌ Multiplayer voice coordination / speaker diarization
- ❌ Relational kernels (SKR-005) without gate opening
- ❌ Persistent deity favor / bidirectional relations
- ❌ "Always-on grid" tactical UI
- ❌ Real-time "instant campaign" generation
- ❌ New RNG streams without explicit approval
- ❌ LLM deciding mechanics or modifying intent after freeze

---

## Governance & Quality Gates

### Per-Milestone Requirements

- Tier-1 unit tests required for all new logic
- Tier-2 integration tests for end-to-end loop
- Determinism tests mandatory (replay harness)
- Runtime budget enforced (<2s test suite)

### Freeze Protocol

After each milestone:
1. Update Rules Coverage Ledger
2. Use CP Completion Review Template
3. Declare milestone freeze
4. No retroactive changes without amendment

---

## References

### Canonical Design Documents

All located in `docs/design/`:

| Document | ID |
|----------|-----|
| Session Zero Ruleset & Boundary Config | SZ-RBC-001 |
| Character Sheet UI Contract | CS-UI-001 |
| Voice Intent & Clarification Protocol | VICP-001 |
| LLM–Engine Boundary Contract | LEB-001 |
| Local Runtime Packaging Strategy | LRP-001 |
| Solo-First Preparatory DM Model | SF-PDM-001 |
| Design Layer Adoption Record | DLAR-001 |

### Supporting Documents

| Document | Location |
|----------|----------|
| Next Steps Execution Packet | `docs/NEXT_STEPS_EXECUTION_PACKET_PM.md` |
| Post-CP20 Decision Analysis | `docs/POST_CP20_DECISION_ANALYSIS.md` |
| SKR-005 Gate Opening Decision | `docs/skr/SKR-005_GATE_OPENING_DECISION_MEMO.md` |

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 3.0 | 2026-02-09 | Initial v3 release |
| 3.1 | 2026-02-09 | Adopted M0-M4 milestone naming, streamlined structure |

---

## END OF EXECUTION ROADMAP V3.1
