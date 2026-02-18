# WO-SMOKE-TEST-001: End-to-End Integration Demo

**From:** PM (Aegis)
**To:** Builder (via Operator dispatch)
**Date:** 2026-02-14
**Lifecycle:** DISPATCH-READY
**Horizon:** 1 (HIGHEST PRIORITY — blocks all further WO drafting)
**Priority:** P0 — This is the only WO that matters right now.
**Source:** Operator strategic directive, MEMO_STRATEGIC_POSTURE_INTEGRATION_GAP, builder findings #1/#2/#6/#7

---

## Target Lock

We have 5,775 unit tests proving individual bricks are solid. We have zero tests proving the building stands up. This WO creates one script that runs the full chain: content pack → world compile → session → cast fireball at a goblin → print the narration. Whatever breaks during this exercise IS the bug list. Whatever works proves the system is real.

This is not a test-writing WO. This is a "be the user" WO. The builder's job is to play the game and report what happened.

## Binary Decisions

1. **What is the script?** A single Python script: `scripts/smoke_test.py`. Not a pytest file — a runnable demo that prints output a human can read.
2. **What does it do?** Load or create a minimal content pack with one spell (Fireball, content_id populated). Compile a world. Start a session with one caster and one goblin. Cast fireball. Print every intermediate artifact: events, NarrativeBrief, TruthChannel, narration text (or template fallback).
3. **Does it need TTS?** No. Print the narration text. TTS is an environment dependency that obscures the integration test.
4. **Does it need an LLM?** No. Use template fallback narration. The point is whether the pipeline produces output, not whether Spark writes good prose.
5. **What if it breaks?** Document exactly where and why. Each break point becomes a finding in the debrief. Do NOT fix the breaks in this WO — just report them. Exception: if the fix is < 10 lines and required to proceed (e.g., wiring a missing content_id), do it and document it.
6. **What about the compile pipeline?** Register ALL compile stages in the WorldCompiler for this script (Lexicon, Semantics, CrossValidate, Rulebook, Bestiary — whatever exists). If a stage fails, document why and skip it.

## Contract Spec

### Deliverable: `scripts/smoke_test.py`

The script does this, in order:

```
1. Create minimal content pack:
   - 1 spell: Fireball (content_id: "spell.fireball_003", damage: 6d6 fire, area: 20ft burst, range: 400ft+40ft/level)
   - 1 caster entity with the spell prepared
   - 1 goblin target entity

2. Compile world:
   - Register all available compile stages
   - Run compiler
   - Print: which stages ran, which failed, what artifacts were produced

3. Start session:
   - Initialize RNG, WorldState, EventLog
   - Place entities on grid

4. Execute combat:
   - Cast fireball at goblin's position
   - Print: raw events emitted (event_type, payload keys, content_id present?)

5. Assemble narration:
   - Build NarrativeBrief from events
   - Print: brief fields populated vs None (especially presentation_semantics)
   - Build TruthChannel from brief
   - Print: TruthChannel fields populated vs None

6. Generate narration:
   - Use template fallback (no LLM required)
   - Print: narration text

7. Summary:
   - Print PASS/FAIL for each stage
   - Print total: "X of Y stages passed end-to-end"
   - List every break point with module, line, error
```

### What to fix in-WO (< 10 line fixes only):

- If SPELL_REGISTRY entries need `content_id` populated → add it to Fireball
- If WorldCompiler needs CrossValidateStage registered → register it
- If content_id isn't flowing from spell resolver events → add it to the payload
- If any import or wiring is missing to connect stages → wire it

Document every fix in the debrief.

### What NOT to fix in-WO:

- CUDA / TTS environment issues
- Test pollution / phantom failures
- Dead code cleanup
- Anything requiring > 10 lines of production code changes

### Constraints

- Script must be runnable with `python scripts/smoke_test.py` — no pytest, no fixtures, no mocking
- Script must print human-readable output showing what worked and what didn't
- Script must not require network, GPU, or LLM API access
- Zero changes to gold masters
- Existing tests must pass

## Success Criteria

- [ ] `scripts/smoke_test.py` exists and runs without crashing
- [ ] Script attempts all 7 stages (content → compile → session → combat → brief → truth → narration)
- [ ] Each stage prints PASS or FAIL with detail
- [ ] Every break point documented in debrief with module, line, and error
- [ ] Any < 10-line fixes applied are documented in debrief
- [ ] Debrief includes: "the system can / cannot produce narration from a spell cast end-to-end"

## Files Expected to Change

- New: `scripts/smoke_test.py`
- Possibly: `aidm/schemas/spell_definitions.py` (content_id on Fireball) — if needed
- Possibly: WorldCompiler caller (stage registration) — if needed
- Possibly: spell resolver event payload (content_id) — if needed

## Files NOT to Change

- Gold masters
- Test files (this is not a test WO)
- Boundary law docs
- PM inbox files

## Integration Seams

This WO exercises every integration seam in the system. It does not introduce new seams — it tests existing ones. The break points it finds ARE the integration seam failures.

## Assumptions to Validate

Before implementing, confirm these assumptions. If any are wrong, flag in your Methodology Challenge section.

1. `WorldCompiler` accepts stage registration at runtime (not hardcoded) — confirm you can register CrossValidateStage without modifying the compiler itself.
2. Spell resolver (`spell_resolver.py` or equivalent) emits events with a payload dict that can accept a `content_id` key — confirm the event shape before wiring.
3. `NarrativeBrief` assembly can be triggered from raw events without a running play loop — confirm the assembler has a standalone entry point.
4. Template fallback narration works without Spark/LLM configuration — confirm the fallback path exists and is importable.

---

## Delivery

After all success criteria pass:
1. `git add` all changed/new files
2. `git commit -m "feat: WO-SMOKE-TEST-001 — end-to-end integration demo"`
3. Record the commit hash
4. Write your debrief (Section 15.5) — 500 words max. Three mandatory sections:
   - **Friction Log** — where you wasted cycles
   - **Methodology Challenge** — one thing to push back on
   - **Field Manual Entry** — one ready-to-paste tradecraft entry
5. Update `pm_inbox/PM_BRIEFING_CURRENT.md`

Code that exists only in the working tree is unverifiable and at risk of loss.
Do NOT edit BUILDER_FIELD_MANUAL.md — the PM curates tradecraft from your debrief.

---

*End of WO-SMOKE-TEST-001*
