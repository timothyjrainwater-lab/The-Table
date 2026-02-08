# AIDM Project Action Plan (REVISED)
## Governance-Driven Deterministic Rules Engine + Local Voice-First Solo Product Layer

**Version:** 3.0 (Post Product-Layer Doctrine Integration)  
**Date:** 2026-02-08  
**Status:** 🟡 DRAFT (Pending PM sign-off)  
**Supersedes:** AIDM_PROJECT_ACTION_PLAN_V2.md (Conceptual spine complete; product-layer milestones added)

---

## STATUS NOTICE

This plan updates V2 to reflect the newly frozen product-layer doctrine:
- Solo-first, prep-first, voice-first
- Character sheet as primary UI
- Contextual grid only when necessary
- Local-only: LLM + STT/TTS + image + audio tooling
- LLM caged: engine is mechanical authority; LLM narrates only
- Preparation phase is first-class and expected to take time

---

## 1) Operating Constraints (Binding)

- **Capability Gate:** G‑T1 only (no gate crossings without explicit authorization)
- **Determinism:** replay-identical outcomes under identical inputs
- **Event-sourcing:** append-only authoritative log
- **Design layer:** frozen after clarification edits + adoption record
- **Solo-first:** multiplayer deferred

---

## 2) Near-Term Milestones (Updated)

### M0 — Design Closeout (Batch Clarifications + Adoption)
**Deliverables**
- Updated design docs (5 core + preparatory doctrine) per agreed clarifications
- `docs/design/DESIGN_LAYER_ADOPTION_RECORD.md`
- Updated `docs/DOCUMENTATION_AUTHORITY_INDEX.md`
- Freeze declaration

**Acceptance**
- All clarifications merged
- Authority index marks canonical docs
- Freeze declared

---

### M1 — Solo Vertical Slice v0 (Playable Loop)
**Goal:** Player can declare intent (text/voice stub), get clarification, engine resolves, narration delivered, sheet updates.

**Deliverables**
- Intent lifecycle (`pending→clarifying→confirmed→resolved`) implemented
- Event store append-only + replay harness
- Character sheet UI v0 (base/persistent/derived/consumables)
- Narration v0 (LLM optional; deterministic templates as fallback)

**Acceptance**
- Determinism replay passes (≥10×)
- Runtime within budget
- No unauthorized file touches / no gate pressure

---

### M2 — Campaign Prep Pipeline v0 (Prep-First Becomes Real)
**Goal:** “Start Campaign” triggers a preparation phase producing campaign scaffolding + assets.

**Deliverables**
- Session Zero config capture + version pinning
- Prep job orchestration queue
- Asset persistence rules: per-campaign + optional shared generic cache
- Prep-phase visibility (ambient/feedback; avoid “frozen” feel)

**Acceptance**
- Campaign can be created, prepped, then played
- Assets persist across sessions
- Export/import includes manifests + events + assets (configurable)

---

### M3 — Immersion Layer v1 (Local Voice + Atmosphere)
**Deliverables**
- Local STT adapter (pluggable), local TTS voice persona
- Ambient audio + SFX (bundled library acceptable)
- Optional local music generation; otherwise curated generative-safe loops
- Image pipeline: NPC portraits + scene backdrops generated in prep

**Acceptance**
- Offline voice I/O functional
- Audio transitions tied to scene state
- Images are atmospheric only (no mechanics depend on them)
- Licensing/attribution record for bundled assets

---

### M4 — Offline Packaging + Shareability
**Deliverables**
- Hardware tiers documented (baseline vs recommended)
- Installer or single-directory bundle
- World export/import with version pinning

**Acceptance**
- Offline install works
- Export/import preserves deterministic replay

---

## 3) Roadmap Notes (Explicit Deferrals)

- Multiplayer voice coordination / speaker diarization → **Deferred**
- Relational kernels (SKR-005) → **Requires gate opening**
- Persistent deity favor / bidirectional relations → **Forbidden at G‑T1**
- “Always-on grid” tactical UI → **Not in scope**
- Real-time “instant campaign” generation → **Not a goal**

---

## 4) Governance & Quality Gates (Carry-Forward)

- Tier-1 unit tests required for all new logic
- Tier-2 integration tests for end-to-end loop
- Determinism tests mandatory (replay harness)
- Runtime budget enforced

---

## 5) References (Canonical Once Adopted)

- `docs/design/SESSION_ZERO_RULESET_AND_BOUNDARY_CONFIG.md`
- `docs/design/CHARACTER_SHEET_UI_CONTRACT.md`
- `docs/design/VOICE_INTENT_AND_CLARIFICATION_PROTOCOL.md`
- `docs/design/LLM_ENGINE_BOUNDARY_CONTRACT.md`
- `docs/design/LOCAL_RUNTIME_PACKAGING_STRATEGY.md`
- `docs/design/SOLO_FIRST_PREPARATORY_DM_MODEL.md`

---

## END
