# WO-ORACLE-SURVEY: Map Oracle v5.2 Onto Existing Codebase

**From:** PM (Aegis)
**To:** Builder (via Operator dispatch)
**Date:** 2026-02-18
**Lifecycle:** DISPATCH-READY
**Horizon:** 2 (Research — no code changes)
**Priority:** P1 — Blocks WO-ORACLE-01 drafting. PM cannot scope Oracle implementation without knowing what already exists.
**Source:** DOCTRINE_03_ORACLE_MEMO_V52.txt, Operator + GPT directive ("identify existing code that satisfies Oracle contract vs greenfield gaps")

---

## Target Lock

Oracle v5.2 defines 5 core data objects: FactsLedger, StoryState, Compactions, UnlockState, WorkingSet. The existing codebase has event sourcing, a Lens layer, NarrativeBrief assembly, and various state management. Before we draft implementation WOs, we need to know what already exists that satisfies (or partially satisfies) the Oracle contract, and what is truly greenfield.

**This is a research WO. No code changes. No production modifications.**

## Deliverable

A single markdown file: `pm_inbox/SURVEY_ORACLE_OVERLAP.md`

For each of the 5 Oracle v5.2 data objects, provide:

### Per-object section format:

```
## [Object Name] (e.g., FactsLedger)

**Oracle v5.2 contract:** [1-2 sentence summary of what the spec requires]

**Existing code overlap:**
- [file path]:[line range] — [what it does, how it maps to the contract]
- [file path]:[line range] — [what it does, how it maps to the contract]

**Covering tests:**
- [test file path]::[test class/function] — [what it tests]

**Gap assessment:**
- SATISFIED: [aspects of the contract that existing code already handles]
- PARTIAL: [aspects that exist but need modification]
- GREENFIELD: [aspects with no existing code at all]

**Notes:** [any observations about compatibility, naming differences, or architectural decisions that affect implementation]
```

### Objects to survey:

1. **FactsLedger** — append-only canon facts with provenance. Look for: event log, fact storage, provenance tracking, content-addressed hashing.

2. **StoryState** — evented pointers (world_id, campaign_id, scene_id, threads, clocks, mode). Look for: session/campaign state management, scene tracking, mode separation.

3. **Compactions** — non-canon accelerators, reproducible from inputs. Look for: any caching, summarization, or derived view logic.

4. **UnlockState** — precision + artifact unlocks, default deny. Look for: visibility gating, unlock tracking, mask safety.

5. **WorkingSet** — deterministic bytes, built from stores, byte-equal rebuild. Look for: NarrativeBrief assembly (closest analog), PromptPack construction, any deterministic serialization.

### Also survey:

6. **Event sourcing infrastructure** — the Box emits events (spell_cast, hp_changed, entity_defeated, etc.). How close is this to Oracle's EventLog (append-only, provenance-linked)?

7. **Canonical serialization** — does any existing code do deterministic JSON serialization with stable ordering? Or is this fully greenfield?

## Constraints

- **NO CODE CHANGES.** Read-only survey. Do not modify any files in `aidm/`, `tests/`, or `scripts/`.
- Do not read the GT v12 or Oracle v5.2 memo directly — the PM has summarized the relevant contracts above. If you need clarification, note it in the survey rather than guessing.
- Focus on `aidm/` directory (core engine) and `tests/` (covering tests). Ignore `scripts/`, `docs/`, and `pm_inbox/`.
- Be honest about gaps. "No existing code" is a valid and useful answer. Don't stretch partial overlaps into false matches.

## Success Criteria

- [ ] `pm_inbox/SURVEY_ORACLE_OVERLAP.md` exists
- [ ] All 7 sections (5 objects + event sourcing + canonical serialization) are completed
- [ ] Each section has: contract summary, existing code overlap (with file paths + line ranges), covering tests, gap assessment (SATISFIED/PARTIAL/GREENFIELD)
- [ ] No code changes made to any file in `aidm/` or `tests/`

## Integration Seams

No integration seams — this is a read-only survey.

## Assumptions to Validate

1. The `aidm/` directory contains the core engine code — confirm the top-level structure before diving deep.
2. Event emission happens in `play_loop.py` and related modules — confirm where events are created and stored.
3. NarrativeBrief assembly in `aidm/lens/narrative_brief.py` is the closest existing analog to WorkingSet construction — confirm or identify alternatives.
4. There may be session/campaign state management that the PM isn't aware of (PM doesn't read source) — look beyond the obvious modules.

---

## Delivery

After all success criteria pass:
1. Write your debrief (`pm_inbox/DEBRIEF_WO-ORACLE-SURVEY.md`, Section 15.5) — 500 words max. Four mandatory sections:
   - **Scope Accuracy** — one sentence: "WO scope was [accurate / partially accurate / missed X]"
   - **Discovery Log** — what you checked, what you learned, what you rejected
   - **Methodology Challenge** — one thing to push back on
   - **Field Manual Entry** — one ready-to-paste tradecraft entry
2. Update `pm_inbox/PM_BRIEFING_CURRENT.md`
3. `git add` all changed/new files — survey, debrief, AND briefing update
4. `git commit -m "research: WO-ORACLE-SURVEY — Oracle v5.2 overlap mapping"`
5. Record the commit hash and add it to the debrief header (`**Commit:** <hash>`)
6. `git add pm_inbox/DEBRIEF_WO-ORACLE-SURVEY.md && git commit --amend --no-edit`

Everything in the working tree — code AND documents — is at risk of loss if uncommitted.
Do NOT edit BUILDER_FIELD_MANUAL.md — the PM curates tradecraft from your debrief.

---

*End of WO-ORACLE-SURVEY*
