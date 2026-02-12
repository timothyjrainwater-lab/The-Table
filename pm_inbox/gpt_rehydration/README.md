# GPT Rehydration Packet

Curated file set for onboarding an external LLM (GPT or similar) to assist with AIDM project research, design, or implementation tasks.

Files are prefixed by tier (T1-T4) indicating priority. Read in order.

## How to Use

1. Copy the contents of `SYSTEM_PROMPT_FOR_GPT.md` into GPT's system prompt / custom instructions
2. Feed the T1 files first, then T2, T3, T4 as needed
3. Ask GPT to produce the Research Gap Register as defined in the system prompt

---

## Tier 1 — Must Read (Project Identity + Current State)

| File | What It Contains |
|------|-----------------|
| `T1_README.md` | Project vision, determinism principles, full architecture overview |
| `T1_PROJECT_COHERENCE_DOCTRINE.md` | Governance, no-LLM-in-runtime rule, fail-closed design, canonical scope |
| `T1_AGENT_ONBOARDING_CHECKLIST.md` | Required reading order, verification steps, 5 most common mistakes |
| `T1_AGENT_DEVELOPMENT_GUIDELINES.md` | Coding standards, entity field conventions, determinism constraints |
| `T1_PROJECT_STATE_DIGEST.md` | Current project state snapshot (test counts, WO status, module inventory) |
| `T1_EXECUTION_PLAN_DRAFT_2026_02_11.md` | 7-step execution plan (CLOSED), all WOs complete, audit framework |
| `T1_EXECUTION_PLAN_V2_POST_AUDIT.md` | 4-phase AI integration plan (ACTIVE), Phase 1 complete, Phases 2-4 future |

**Tier 1 alone gives ~80% of the context needed.**

---

## Tier 2 — Architecture Understanding

| File | What It Contains |
|------|-----------------|
| `T2_STANDING_OPS_CONTRACT.md` | Agent behavioral rules (PM/Sonnet/Thunder roles and posture) |
| `T2_OPUS_PM_REHYDRATION.md` | PM methodology, dispatch format, velocity mode, key references |
| `T2_VERTICAL_SLICE_V1.md` | First runnable milestone definition (event sourcing, determinism proof) |
| `T2_SPARK_PROVIDER_CONTRACT.md` | LLM integration spec (request/response schema, capability manifest) |

**Tiers 1+2 covers ~95% of project context.**

---

## Tier 3 — Voice/Immersion Specific

| File | What It Contains |
|------|-----------------|
| `T3_WO-051_VOICE_DESIGN_RESEARCH.md` | Research WO: voice cloning best practices, archetype recipes |
| `T3_WO-052_LENS_VOICE_RESOLVER.md` | Code WO: Lens voice resolver, prompt script, VoiceRoster cache |
| `T3_IMMERSION_BOUNDARY.md` | Immersion layer scope boundary (what it may/must never do) |
| `T3_KNOWN_TECH_DEBT.md` | Intentionally deferred issues (DO NOT fix without approval) |

**Only needed if doing voice/immersion work.**

---

## Tier 4 — Schema Reference (Skim)

| File | What It Contains |
|------|-----------------|
| `T4_immersion_schema.py` | VoicePersona, AudioTrack, ImageRequest, GridRenderState, Attribution |
| `T4_intents_schema.py` | Voice intent contracts (CastSpell, Move, Attack, Buy, Rest) |
| `T4_bundles_schema.py` | SessionBundle, SceneCard, EncounterSpec, CampaignBundle |

**Reference as needed. Don't full-ingest unless working on schema changes.**

---

## Key Architectural Concepts

- **Box**: Deterministic combat engine (melee, ranged, spells, conditions, terrain)
- **Lens**: Data membrane between Spark and Box (indexing, provenance, fact acquisition)
- **Spark**: LLM integration (narration, scene generation, voice characterization)
- **Immersion**: Atmospheric layer (TTS, STT, image gen, audio mixer) — never mechanical authority
- **Event Sourcing**: All state changes flow through deterministic event log
- **Fail-Closed**: Invalid inputs blocked by validators, no silent fallbacks

## Critical Rules

1. Immersion outputs NEVER affect mechanical game state
2. No LLM calls in the runtime combat loop
3. All entity field access uses EF.* constants
4. All state mutations use deepcopy()
5. Replay from event log must produce identical state hash
