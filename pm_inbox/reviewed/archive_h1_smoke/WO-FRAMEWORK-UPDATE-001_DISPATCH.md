# WO-FRAMEWORK-UPDATE-001: Framework Repo — Reorder, Failure-First, Integration Canary

**From:** PM (Aegis)
**To:** Builder (via Operator dispatch)
**Date:** 2026-02-14
**Lifecycle:** DISPATCH-READY
**Priority:** P1 — Operator directive. Three structural changes to the public framework repo.
**Repo:** `timothyjrainwater-lab/multi-agent-coordination-framework` (GitHub)
**Source:** Operator strategic feedback session (2026-02-14), DnD engine integration reorientation

---

## Target Lock

Three changes to the multi-agent coordination framework repo, all driven by the same session that produced the DnD engine's integration reorientation. The framework documents coordination patterns discovered bottom-up. Today's session discovered a new pattern (Integration Canary) and revealed that the repo's current ordering undersells its strongest assets.

## Binary Decisions

1. **Does Enforcement Hierarchy move to Pattern 1?** Yes. It's currently pattern 9 (last). The operator identified it as the framework's most important contribution.
2. **Does the README lead with failure catalog stats?** Yes. "30 bugs in 8 error patterns" is more compelling than "9 patterns and 5 templates." Patterns support the failures, not the other way around.
3. **Is Integration Canary a new pattern file?** Yes. `patterns/INTEGRATION_CANARY.md`. Pattern 10.
4. **Do test counts update?** Yes. From 5,100+ to 5,775+ in README and case-study/METRICS.md. H1 WO batch stats added.
5. **Does any existing pattern content change?** No. Only ordering in README and new pattern file.

## Contract Spec

### Change 1: Reorder Patterns — Enforcement Hierarchy First

In `README.md`, move Enforcement Hierarchy from position 9 to position 1 in the patterns table. All other patterns shift down by one position. No content changes to pattern files — only the table ordering and any numbered references in README.

New pattern table order:
1. Enforcement Hierarchy (was 9)
2. Staged Context Loading (was 1)
3. Dispatch Self-Containment (was 2)
4. Artifact Primacy (was 3)
5. Cross-File Consistency Gate (was 4)
6. Session Bootstrap (was 5)
7. Concurrent Session Protocol (was 6)
8. PM Context Compression (was 7)
9. Coordination Failure Taxonomy (was 8)
10. Integration Canary (NEW)

### Change 2: README Restructure — Lead with Failure Catalog

Restructure the README opening to lead with the failure catalog's credibility signal. After "The Problem" section and before "Who This Is For", add a section:

```markdown
## What Makes This Different

Most AI coordination guides tell you what to do. This one shows you what went wrong.

**From the proving ground (D&D 3.5e combat engine):**
- 5,775+ automated tests across 9 verification domains
- 338 formulas verified against source rules
- 30 bugs found and categorized into 8 coordination error patterns
- 7 WO batches (H0 fixes + H1 features) coordinated across parallel agent sessions
- 3 of 7 parallel agents silently failed to commit in one dispatch — the fix became a governance pattern

Every pattern in this framework exists because something specific broke. The [failure catalog](case-study/FAILURE_CATALOG.md) has the receipts.
```

### Change 3: New Pattern — Integration Canary

New file `patterns/INTEGRATION_CANARY.md`:

```markdown
# Integration Canary

## Problem

Each agent builds and tests its piece in isolation. All unit tests pass. But nobody tries to use the product end-to-end. Constraints (boundary laws, frozen schemas, protocol interfaces) produce consistency within modules but cannot produce integration across modules.

**Symptoms:**
- "Works in isolation, fails in integration"
- Data bridges wired but dormant (code exists, data never flows)
- Validation rules that structurally cannot fire (the field they check is always empty)
- Compile stages that exist but aren't registered in production callers
- 5,000+ unit tests passing, zero integration tests

## Solution

Before dispatching new infrastructure WOs, run one script that exercises the full product path. Whatever breaks is your next WO.

**The script pattern:**
1. Set up minimal input (content pack, seed data, test fixture)
2. Run the full pipeline (compile → initialize → execute → output)
3. Print what worked and what didn't at each stage
4. Document every break point with module, line, and error

**The operational rule:**
- No new infrastructure WOs until the canary runs
- Each break point from the canary becomes a work order
- Each integration fix must include a test that exercises the seam (preventing regression)
- The canary script itself becomes a permanent CI artifact

## When to Use

- After completing a batch of module-scoped WOs
- Before transitioning from one project horizon to the next
- When unit test count is growing but confidence in the product isn't
- When architecture audits keep finding "theoretical gaps" — run the system instead

## When Not to Use

- During active development of a single module (unit tests are sufficient)
- When the product path doesn't exist yet (you need components before you can integrate them)

## Real Example

**D&D 3.5e engine, end of H1 WO batch (2026-02-14):**

7 WOs completed across parallel agents: weapon plumbing, RNG protocol extraction, TTS chunking, NarrativeBrief width extension, compile-time cross-validation, runtime narration validation, TTS cold start research. 5,775 unit tests passing.

The operator's directive: "You have 5800 tests that prove individual bricks are solid, but no test that proves the building stands up."

**Predicted break points (confirmed by smoke test):**
- `SPELL_REGISTRY` entries lack `content_id` — Layer B narration permanently dormant
- `CrossValidateStage` not registered in production `WorldCompiler` — cross-validation doesn't run
- `NarrationValidator` not wired into play loop — validation rules exist but never execute
- `content_id` bridge: events → lookup → presentation_semantics: wired but produces `None`

None of these were caught by unit tests. All were caught by trying to cast fireball at a goblin.

## Key Insight

> Constraints produce consistency. Integration produces a product. You need both, and they require different types of work — module-scoped WOs for constraints, cross-cutting WOs for integration.

## Related Patterns

- [Enforcement Hierarchy](ENFORCEMENT_HIERARCHY.md) — Integration seam tests are Tier 1 enforcement
- [Cross-File Consistency Gate](CROSS_FILE_CONSISTENCY.md) — Integration canary is the cross-module version of this
- [Dispatch Self-Containment](DISPATCH_SELF_CONTAINMENT.md) — Integration WOs need broader context than module WOs
```

### Change 4: Update Metrics

In `case-study/METRICS.md`, update:
- Tests passing: 5,100+ → 5,775+
- Add H1 WO batch metrics:
  - 7 H1 WOs completed
  - 4 builder commit failures recovered in one batch (governance fix shipped)
  - Integration Constraint Policy codified

In `README.md`, update "Project stats at time of extraction":
- 5,100+ → 5,775+ automated tests
- Add: "7 H1 feature WOs completed and integrated"
- Add: "Integration Canary pattern discovered and codified"

### Change 5: Add "Assumptions to Validate" to Dispatch Template

In `templates/WORK_ORDER_TEMPLATE.md`, add a new optional section between Contract Spec and Constraints:

```markdown
## Assumptions to Validate (Optional)

Before implementing, confirm these assumptions are correct. If any are wrong, flag in your debrief before building the wrong thing.

1. [Assumption about scope, data format, upstream dependency, or design intent]
2. [...]
3. [...]
```

This costs nothing in dispatch prep time but prevents wasted builder context on incorrect assumptions. Discovered from builder feedback: "I didn't push back on the dispatch at all. A higher-quality agent interaction would have flagged things before building."

### Constraints

- Do NOT change content of existing pattern files — only ordering references in README
- Do NOT change templates
- Do NOT change case-study/ files other than METRICS.md
- Do NOT remove the VPN section or any existing README content
- Keep the "former chef, English educator" framing — it's the differentiator

## Integration Seams

No integration seams. This WO modifies documentation files only in a standalone repo. No cross-module data dependencies.

## Assumptions to Validate

No assumptions to validate — spec is fully determined. All content is provided inline in the Contract Spec. The builder does not need to discover or infer anything.

## Success Criteria

- [ ] Enforcement Hierarchy is pattern 1 in README table
- [ ] README has "What Makes This Different" section with failure catalog stats
- [ ] `patterns/INTEGRATION_CANARY.md` exists with problem/solution/example
- [ ] Test counts updated to 5,775+ in README and METRICS.md
- [ ] Pattern table has 10 entries (Integration Canary added at position 10)
- [ ] All existing links still work
- [ ] No content changes to existing pattern files
- [ ] Dispatch template has "Assumptions to Validate" optional section

## Files Expected to Change

- `README.md` — reorder patterns, add section, update stats
- `case-study/METRICS.md` — update test counts, add H1 metrics
- New: `patterns/INTEGRATION_CANARY.md`
- `templates/WORK_ORDER_TEMPLATE.md` — add Assumptions to Validate section

---

## Delivery

After all success criteria pass:
1. `git add` all changed/new files
2. `git commit` with a descriptive message referencing WO-FRAMEWORK-UPDATE-001
3. `git push` to `timothyjrainwater-lab/multi-agent-coordination-framework`
4. Record the commit hash
5. Write your debrief to the DnD repo at `pm_inbox/DEBRIEF_WO-FRAMEWORK-UPDATE-001.md` — 500 words max. Three mandatory sections:
   - **Friction Log** — where you wasted cycles
   - **Methodology Challenge** — one thing to push back on
   - **Field Manual Entry** — one ready-to-paste tradecraft entry
6. Update `pm_inbox/PM_BRIEFING_CURRENT.md`

Code that exists only in the working tree is unverifiable and at risk of loss.
Do NOT edit BUILDER_FIELD_MANUAL.md — the PM curates tradecraft from your debrief.

---

*End of WO-FRAMEWORK-UPDATE-001*
