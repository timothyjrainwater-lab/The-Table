# AIDM Next-Steps Execution Packet (PM)
**Version:** 1.0  
**Date:** 2026-02-08  
**Audience:** Implementing agent(s) (Clog/Claw/Successors)  
**Purpose:** Step-by-step execution sequence from “design spine complete” to first solo-playable vertical slice, with governance locks.

---

## 0) Non‑Negotiables (Reaffirmed)
1. **Determinism is sacred.** Engine outcomes must be replay-identical under identical inputs.
2. **Authority split is sacred.** **Engine defines reality; LLM describes reality.**
3. **Gates remain closed unless explicitly opened.** Current operating gate: **G‑T1 only**.
4. **Design layer is frozen after clarification edits + adoption.** No philosophical relitigation during build.
5. **Solo-first, prep-first, voice-first.** Grid is contextual; sheet is primary UI.

---

## 1) Close Out the Design Layer (Batch Clarification Edits)
**Goal:** Convert the five design documents + additive prep doctrine into “adoptable canonical” form.

### Step 1.1 — Apply the agreed clarifications (minimal, surgical edits)
**Documents to update:**
- `docs/design/SESSION_ZERO_RULESET_AND_BOUNDARY_CONFIG.md`
  - Add `config_schema_version`
  - Define `ruleset_history` (append-only amendments with version bumps)
  - Default behavior: **fail-open to RAW** when keys missing
  - Variants: declared at Session Zero; mid-campaign changes only via amendment/version
  - Specify manifest editability (tool-generated recommended; human-editable allowed with schema validation)
- `docs/design/CHARACTER_SHEET_UI_CONTRACT.md`
  - Condition visibility: configurable (default: owning player sees; DM-hidden allowed via Session Zero)
  - Derived value caching: allowed with strict invalidation (derived values remain non-authoritative)
  - Historical view: read-only “as-of turn” snapshot supported
  - Alignment effect indicators: **derived evaluation only** (no persistent “divine favor” state)
- `docs/design/VOICE_INTENT_AND_CLARIFICATION_PROTOCOL.md`
  - Add intent lifecycle: `pending → clarifying → confirmed → resolved`
  - Timeout handling: cancel intent gracefully; log partial intent for debugging if enabled
  - Retraction: allowed until intent is frozen/confirmed
  - Multiplayer coordination: explicitly deferred (solo-first)
- `docs/design/LLM_ENGINE_BOUNDARY_CONTRACT.md`
  - Add “LLM failure modes & fallbacks” section (timeout/invalid output/unexpected refusal)
  - Define LLM context window policy (summarized state by default; raw logs on demand)
  - Narration regeneration policy (regen from events; no re-resolution)
- `docs/design/LOCAL_RUNTIME_PACKAGING_STRATEGY.md`
  - Add minimum hardware tiers (baseline vs recommended)
  - Define adapter selection (STT/TTS pluggable config)
  - Define upgrade path (campaign pins engine+model versions; upgrades don’t invalidate old logs)
  - Clarify world export contents (events/intents required; optional LLM convo cache)

**Additive doctrine to keep consistent:**
- `docs/design/SOLO_FIRST_PREPARATORY_DM_MODEL.md`
  - Add prep-phase visibility guidance (ambient visuals/audio; avoid “frozen” feel)
  - Add asset persistence (per-campaign + optional shared generic asset cache)
  - Add audio sourcing note (generated vs bundled assets; licensing)

### Step 1.2 — Produce a one-page “Design Adoption Record”
Create: `docs/design/DESIGN_LAYER_ADOPTION_RECORD.md` containing:
- Exact list of canonical docs + versions
- Gate assumptions (G‑T1 only)
- “Freeze declaration” (no changes without amendment)

### Step 1.3 — Update Authority Index
Update: `docs/DOCUMENTATION_AUTHORITY_INDEX.md` to mark:
- The six design docs + adoption record as **CANONICAL**
- Any older overlapping philosophy docs as “historical / superseded”

**Exit Criteria (Design Closeout):**
- All edits applied and reviewed
- Authority index updated
- Design layer **declared frozen** in writing

---

## 2) Update the Action Plan (V3) to Reflect Product-Layer Doctrine
**Goal:** Ensure roadmap sequencing matches the frozen design: solo-first + prep pipeline + contextual grid + asset tooling.

### Step 2.1 — Produce `AIDM_PROJECT_ACTION_PLAN_V3.md`
Actions:
- Add a **Product Layer Track** (voice, sheet UI, contextual board, prep pipeline)
- Reframe near-term milestones around a **solo vertical slice**
- Explicitly defer multiplayer and any gate-pressuring kernels (SKR work gated)
- Add tool selection/evaluation tasks (local LLM, STT/TTS, image gen, audio)
- Add acceptance criteria per milestone (determinism, runtime, event log completeness)

### Step 2.2 — Add “No-Relitigation” governance to plan
- Design docs are reference authority
- Any new feature proposal must cite a doc or request an amendment

**Exit Criteria (Plan Update):**
- V3 action plan written and reviewed
- V2 marked superseded
- Plan signed off by PM authority

---

## 3) Build the First Solo Vertical Slice (Minimal but Real)
**Goal:** A player can speak/enter intent, have the engine resolve, and receive narration + sheet updates. No grid unless required.

### Step 3.1 — Establish runtime skeleton (local orchestration)
Deliverables:
- Process boundary or in-proc modules: Engine / DM-LLM / UI / Store
- Contract: `intent → engine → events → narration → UI`
- Deterministic event store: append-only

### Step 3.2 — Implement “Intent Lifecycle” in code
- Store partial/clarifying intents
- Freeze intent before engine resolution
- Log clarification dialogue (for audit/debug)

### Step 3.3 — UI v0: Character Sheet as the primary surface
- Render base + persistent + derived + consumables
- Subscribe to event stream to update view
- Provide “as-of turn” read-only history (minimal)

### Step 3.4 — Voice/text input v0 (text first, voice adapter pluggable)
- Implement structured text fallback templates
- Add STT adapter stub with same interface (plug later)

### Step 3.5 — Narration v0 (LLM optional at first)
- If LLM present: narrate from engine events
- If LLM missing/timeout: deterministic template narration

**Exit Criteria (Vertical Slice):**
- A complete “declare → clarify → resolve → narrate → update sheet” loop
- Determinism replay passes
- Runtime within budget
- No new gate crossings

---

## 4) Prep Pipeline v0 (Prep-First Philosophy Becomes Real)
**Goal:** “Start Campaign” triggers a preparation phase that produces reusable assets and scaffolding.

### Step 4.1 — Campaign creation contract
- Session Zero config is captured and versioned
- Campaign manifest created (pins engine + model + tool versions)

### Step 4.2 — Prep job orchestration
- A queue of prep tasks (NPCs, factions, locations, encounters)
- Provide user-facing prep status (not necessarily %)

### Step 4.3 — Asset store + reuse rules
- Per-campaign asset directory
- Optional shared “generic cache” (tavern, road, forest, etc.)
- Missing assets regenerate on demand (deterministic IDs for references)

**Exit Criteria (Prep v0):**
- Player can start a campaign, wait through prep, then begin session 1
- Assets persist across sessions
- World export includes manifests + events + assets (as configured)

---

## 5) Immersion Layer v1 (Local Images + Local Audio)
**Goal:** Add atmosphere without turning into a video game UI.

### Step 5.1 — Image pipeline
- Local image generator adapter (or bundled placeholder assets first)
- NPC portraits + scene backdrops generated in prep
- No mechanical dependence on images

### Step 5.2 — Audio pipeline
- Local TTS (voice persona)
- Ambient loops + SFX (bundled library acceptable)
- Optional local music generator; otherwise curated generative-safe library
- Licensing/attribution tracked for bundled assets

**Exit Criteria (Immersion v1):**
- TTS voice works locally
- Ambient audio supports scene transitions
- Asset licensing record present (if bundled)

---

## 6) Packaging & Shareability (Offline Product)
**Goal:** A single-machine bundle that someone else can run.

### Step 6.1 — Hardware tiers
- Baseline (CPU-only, smaller model, text)
- Recommended (GPU, 7B–13B, voice)
- Document expected disk footprint

### Step 6.2 — Version pinning + world export
- Export: ruleset manifest + event log + state snapshots + assets (configurable)
- Import restores identical play (mechanical determinism)

**Exit Criteria (Packaging):**
- Offline install or single-directory bundle
- A campaign can be exported/imported and replayed deterministically

---

## 7) Governance Close
- Update Rules Coverage Ledger after each CP/major product milestone
- Use CP Completion Review Template
- Declare freeze for each milestone

---

## Appendix A — “Do Not Do”
- Do not let LLM decide mechanics or modify intent after freeze
- Do not add multiplayer, speaker diarization, or shared state now
- Do not add persistent deity favor or relational state (gate pressure)
- Do not add new RNG streams without explicit approval
