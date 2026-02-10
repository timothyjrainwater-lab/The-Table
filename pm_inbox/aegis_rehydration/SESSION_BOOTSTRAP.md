# Session Bootstrap

> Warm resume. Assume continuity. Current state banner below.

---

## STATE BANNER

```
PHASE:       M3 (Immersion Layer v1) — R1 research complete, corrective WOs in progress
FROZEN:      M0 (Design Closeout), M1 (Solo Vertical Slice v0), M2 (Persistence v1.1)
COMPLETED:   WO-M2-01 (Persistence Freeze), WO-M3-PREP-01 (Prep Pipeline Prototype)
IN PROGRESS: Audio strategy correction (Sonnet-D rewriting WOs), Image critique rescoping
IDLE:        Sonnet A/B/C
ESCALATION:  Opus auditing Sonnet-D deliverables for strategic drift
TESTS:       1777 passing (1770 pass, 7 pre-existing Spark adapter failures)
```

---

## Current Phase

**M3 — Immersion Layer v1.** R1 Technology Stack Validation is complete (all 7 technology areas resolved). Active work is correcting audio work orders and rescoping image critique WOs to align with R1 findings. Prep pipeline prototype exists (sequential model loading validated in stub mode).

## Critical Context: R1 Technology Stack Validation

**Read `pm_inbox/OPUS_R1_TECHNOLOGY_STACK_VALIDATION.md` (518 lines).** This is the single most important research document in the project. It resolves model selections for all 7 technology areas:

| Area | R1 Selection | Changed from R0? |
|------|-------------|------------------|
| Image Gen | SDXL Lightning NF4 (Apache 2.0, 3.5-4.5 GB VRAM) | YES (was SD 1.5) |
| Image Critique | Heuristics + ImageReward + SigLIP | YES (was CLIP B/32) |
| TTS | Kokoro (Apache 2.0, 150-300 MB) | YES (was Piper/Coqui) |
| STT | faster-whisper small.en (MIT, 400-700 MB) | YES (was Whisper Base) |
| LLM | Qwen3 14B/8B/4B (Apache 2.0) | YES (was Mistral 7B/Phi-3) |
| Music | ACE-Step (Apache 2.0, 6-8 GB VRAM, prep-time) | NEW |
| SFX | Curated library (generative blocked by licensing) | NEW |

**Key architecture correction:** AIDM is a **prep-time sequential pipeline**. Models load one at a time during campaign prep (LLM → Image → Critique → Music → SFX → TTS), each getting full GPU. Peak VRAM = single largest model. This makes generative music viable on 6+ GB VRAM hardware.

## Critical Context: Sonnet-D Audio Strategy Drift

Sonnet-D's reviewed audio work orders inverted the project's strategic intent:
- **Thunder's intent:** Generative music PRIMARY (ACE-Step) for capable hardware, curated FALLBACK for minimum spec
- **Sonnet-D's framing:** Curated PRIMARY, generative OPTIONAL

Correction is in progress. Sonnet-D acknowledged the issue and is rewriting WOs. Verify deliverables match generative-primary framing before approval.

**Full audit details:** Ask Thunder or Opus for the PM inbox audit report.

## Frozen Milestones

- **M0** — Design Closeout: COMPLETE, FROZEN
- **M1** — Solo Vertical Slice v0: COMPLETE, FROZEN (1725+ tests)
- **M2** — Campaign Prep Pipeline: PERSISTENCE LAYER COMPLETE, FROZEN (v1.1)
- **Post-Audit Remediation** — COMPLETE, FROZEN (18 fixes applied)
- **CP-001** — Position Type Unification: COMPLETE (both phases)

## Completed Work Orders (Since Last Rehydration)

| WO ID | Agent | Status | Key Output |
|-------|-------|--------|------------|
| WO-M2-01 | Sonnet A | COMPLETE | M2 Persistence Architecture Freeze v1.1 |
| WO-M3-PREP-01 | Sonnet B | COMPLETE | Prep pipeline prototype (sequential model loading, 17 tests) |
| WO-R1-RESEARCH-UPDATE-01 | Opus | COMPLETE | R1 Technology Stack Validation, R0 reconciliation, prep timing study |

## Active / Pending Work

| Item | Agent | Status | Notes |
|------|-------|--------|-------|
| Audio WO correction | Sonnet D | IN PROGRESS | Rewriting AUDIO-EVAL-01 and AUDIO-INT-01 with generative-primary framing |
| Image critique rescoping | Sonnet D | PENDING | WO needs rescoping — infrastructure already exists, model selections outdated (should use ImageReward + SigLIP, not "Spark vision + CLIP") |
| Roadmap v3.2 amendment | TBD | PENDING | Update M3 audio language, R1 model references |
| Stale model reference cleanup | TBD | PENDING | Several governance docs still reference Mistral 7B / Phi-2 / Coqui |

## Authority Map

| Role | Agent | Decides |
|------|-------|---------|
| Project Owner | Thunder | Dispatch, acceptance, scope changes, gate openings |
| PM | Aegis (GPT) | Sequencing, WO drafting, delivery acceptance pass |
| Principal Engineer | Opus (Claude 4.6) | Audits, architectural adjudication, irreversible decisions |
| Implementers | Sonnet A/B/C/D | Bounded execution per WO scope only |

**No role blending.** PM does not audit. Opus does not draft WOs. Sonnet does not make architectural decisions.

## What Is In Scope Right Now

1. Reviewing Sonnet-D's corrected audio work orders (verify generative-primary framing)
2. Rescoping WO-M3-IMAGE-CRITIQUE-01 (align with R1 model selections)
3. Planning roadmap v3.2 amendment (M3 audio language + R1 model references)
4. R0 research completion — 6 critical questions remain open (see R0_MASTER_TRACKER.md Section 10)

## What Is NOT In Scope

- Any new CPs or SKRs
- Spellcasting (CP-18A not greenlit)
- Code implementation of real model adapters (design/evaluation first)
- Modifying the prep pipeline prototype (WO-M3-PREP-01 is complete)

---

## Key Reference Files

- `pm_inbox/OPUS_R1_TECHNOLOGY_STACK_VALIDATION.md` — **READ FIRST** — R1 model selections for all 7 areas
- `docs/research/R0_PREP_PIPELINE_TIMING_STUDY.md` — Prep pipeline timing (~9 min median, ~17 min minimum)
- `docs/research/R0_MASTER_TRACKER.md` Section 10 — R1 reconciliation of 49 research questions
- `docs/research/R0_DECISION_REGISTER.md` — All R0 decisions with R1 revision notes
- `SESSION_BOOTSTRAP.md` — this file (posture reset)
- `STANDING_OPS_CONTRACT.md` — behavioral rules (20 bullets)
- `PROJECT_STATE_DIGEST.md` — canonical project state
- `KNOWN_TECH_DEBT.md` — intentionally deferred issues
- `docs/AIDM_EXECUTION_ROADMAP_V3.md` — canonical roadmap (pending v3.2 amendment)

---

## Protocol

When Aegis opens a new context window, Thunder drops the `aegis_rehydration/` folder contents. Aegis should:
1. Read `SESSION_BOOTSTRAP.md` first (this file — posture + state banner)
2. Read `AEGIS_REHYDRATION_STATE.md` second (pipeline details)
3. Read `STANDING_OPS_CONTRACT.md` third (behavioral rules)
4. Read `pm_inbox/OPUS_R1_TECHNOLOGY_STACK_VALIDATION.md` fourth (R1 model selections — CRITICAL)
5. Confirm: "I see [N] active items, waiting on [X]. State: [status]."
6. Resume from the current state — do NOT re-plan anything already planned
