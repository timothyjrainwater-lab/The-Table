# WO-VOICE-RESEARCH-02 Completion Report

**Work Order:** WO-VOICE-RESEARCH-02
**Status:** COMPLETE
**Date:** 2026-02-13
**Agent:** Sonnet B
**Deliverable:** `docs/research/VOICE_FAILURE_TAXONOMY_AND_UNKNOWN_POLICY.md`

---

## Acceptance Criteria Verification

| # | Criterion | Status | Evidence |
|---|---|---|---|
| 1 | Taxonomy covers ASR errors, partial transcripts, homophones, timing/turn-taking, ambiguity (entity/spell/weapon), out-of-grammar, cross-mode bleed | PASS | Sections 1.1-1.7: FC-ASR, FC-HOMO, FC-PARTIAL, FC-TIMING, FC-AMBIG, FC-OOG, FC-BLEED |
| 2 | Each failure class defines required behavior + forbidden behavior | PASS | Every section has "Required behavior" and "Forbidden behavior" tables |
| 3 | STOPLIGHT bias rules (GREEN/YELLOW/RED) for voice control plane, fail-closed default | PASS | Section 2: STOPLIGHT Bias Rules with classification, promotion, demotion, and authority boundary rules |
| 4 | Deterministic clarification budget (max questions, escalation, cancel) | PASS | Section 3: MAX_CLARIFICATIONS=2, escalation ladder, cancel semantics, timeout policy |
| 5 | Operator-facing checklist convertible to unit tests | PASS | Section 5: 35 signal->behavior rows across 8 categories (T-ASR, T-HOMO, T-PART, T-TIME, T-AMBIG, T-OOG, T-BLEED, T-BUDGET) |
| 6 | No philosophical prose; operational guardrails only | PASS | Document contains tables, rules, and checklists. No narrative padding. |
| 7 | All tests pass | PENDING | Test run executed separately |

## Stop Conditions

| Condition | Triggered? |
|---|---|
| Need to modify file not in ALLOWED FILES | NO |
| Recommendation implies Box-layer authority leakage | NO — STOPLIGHT explicitly scoped to LENS; constraint filtering is read-only Box query |
| Recommendation requires changing doctrine files | NO — all doctrine references are read-only citations |

## Dependencies

- **Depends on:** WO-VOICE-RESEARCH-01 (voice signal/speak.py context) — READ ONLY, no modifications
- **Blocks:** WO-VOICE-RESEARCH-05 — this deliverable provides the failure taxonomy that WO-05 will reference

## Key Design Decisions

1. **Default RED until proven GREEN.** Every voice input starts at RED and must earn its way to GREEN through confidence thresholds and constraint filtering. This is the fail-closed posture.

2. **MAX_CLARIFICATIONS = 2.** Two questions, then menu, then cancel. Three questions means the system is failing, not the player. Prevents infinite loops.

3. **Single-weapon inference is the ONLY permitted auto-fill.** If a player says "hit the goblin" and has exactly one melee weapon equipped with the target in range, the system infers the weapon. All other fields require explicit input or clarification. Tagged `[INFERRED]`.

4. **STOPLIGHT operates in LENS, never in BOX.** The voice control plane governs presentation and interaction flow. It queries Box for constraint data (range, LOS, equipment) but never writes to game state. This preserves the Spark/Lens/Box separation.

5. **TTS is always interruptible.** Player speech pauses TTS. The player never waits for the system to finish talking.

6. **No LLM-based disambiguation.** Ambiguity resolution uses lexicon matching and deterministic game-state constraints only. LLM probability scores are forbidden for intent disambiguation.

## Files Created

| File | Purpose |
|---|---|
| `docs/research/VOICE_FAILURE_TAXONOMY_AND_UNKNOWN_POLICY.md` | Primary deliverable |
| `pm_inbox/research/WO-VOICE-RESEARCH-02_completion.md` | This completion report |

## Files Modified

None.
