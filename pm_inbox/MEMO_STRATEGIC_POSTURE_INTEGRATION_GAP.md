# MEMO: Strategic Posture Assessment — Infrastructure vs Integration
**From:** Agent (Opus 4.6), synthesizing builder strategic feedback
**Date:** 2026-02-14
**Lifecycle:** NEW

---

## Core Assessment

The project has extensive infrastructure and limited end-to-end integration. The builder's observation: "you've got a lot of infrastructure and not a lot of gameplay yet."

**What exists:** Compile pipeline, presentation semantics, narration validators, cross-validation, TTS adapters, frozen world bundles, RNG protocols, weapon plumbing, causal chains, boundary law enforcement, 5,800+ tests.

**What doesn't exist yet:** A fireball cast that flows through all layers and produces narrated audio output. The content_id bridge is dormant, SPELL_REGISTRY entries lack content_ids, and the presentation registry isn't wired into the play loop caller. The machinery is built but nothing flows end-to-end.

## The Integration Gap

The test suite is almost entirely unit tests with hand-constructed data. Integration seams between stages are tested separately on each side but not together. The builder's concern: "the JSON one stage writes doesn't match what the next stage reads" — this is exactly what finding #7 (no full pipeline integration test) describes, but at a project-wide scale.

**Specific dormant connections:**
- `SPELL_REGISTRY` → `content_id` → `presentation_semantics` lookup: wired but no spell has a content_id
- `CrossValidateStage` → `WorldCompiler`: stage exists but not registered in production callers
- `NarrationValidator` → play loop: rules exist but no production caller invokes validation
- TTS adapters → actual gameplay: chunking and adapters work in isolation, environment has CUDA issues

## Process Observation

The dispatch/debrief cycle is operating as post-hoc documentation rather than a planning tool. Builders consistently commit work before the dispatch lands. This isn't wrong — it means builders are productive — but the process is documenting what happened rather than directing what should happen. If the PM is going to shift toward integration work, dispatches need to lead rather than follow.

## Strategic Recommendation

The next highest-value work is **not more infrastructure** — it's connecting what already exists:

1. **WO: End-to-end spell cast integration test** — Cast fireball through play_loop → events with content_id → narrative_brief → TruthChannel → prompt_pack. Verify the full pipeline produces correct output. This is the single test that proves the system works.

2. **WO: SPELL_REGISTRY content_id population** — Map runtime spell IDs to compile-time content_ids. Without this, Layer B narration is permanently dormant during gameplay.

3. **WO: WorldCompiler production wiring** — Register all stages (Rulebook, Bestiary, NPC, CrossValidate) in the default compiler. Currently only Lexicon + Semantics run.

4. **Fix TTS environment** — The torchaudio/CUDA failures are environment-level, not code-level. If TTS matters, the machine setup needs attention.

These four items turn the infrastructure into a working pipeline. Everything else (resolver dedup, test isolation, FrozenWorldStateView guard) is maintenance on machinery that isn't producing output yet.

## Retrospective

The builder's strategic lens is the most valuable output of this session's debrief cycle. The tactical findings (#1-#13 across the two findings memos) are useful for cleanup, but this posture assessment should drive what the PM queues next. The project is at the inflection point between "building parts" and "assembling the product."
