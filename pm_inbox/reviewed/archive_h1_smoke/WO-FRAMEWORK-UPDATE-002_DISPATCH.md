# WO-FRAMEWORK-UPDATE-002: Framework Repo — 4 New Patterns, Metrics Update, Failure Catalog Extension

**From:** PM (Aegis)
**To:** Builder (via Operator dispatch)
**Date:** 2026-02-14
**Lifecycle:** COMPLETE
**Priority:** P1 — Operator directive. Six structural issues identified by internal roadmap auditor and operator feedback.
**Repo:** `timothyjrainwater-lab/multi-agent-coordination-framework` (GitHub)
**Source:** Operator feedback session (2026-02-14), builder combustion efficiency analysis, roadmap audit findings
**PR:** https://github.com/timothyjrainwater-lab/multi-agent-coordination-framework/pull/1
**Branch:** `update/framework-v2-patterns-and-metrics`

---

## Target Lock

Six issues in the framework repo identified by internal audit and operator feedback. Four missing patterns (Role Separation, Research-to-Build Pipeline, Plain English Pass, Debrief Integrity Boundary), frozen case study metrics, misplaced VPN section, and no non-technical translation layer in the debrief format.

## Binary Decisions

1. **Clone + branch + PR, or draft locally first?** RESOLVED: Clone + branch + PR.
2. **Metrics: update to current numbers, or add disclaimer only?** RESOLVED: Update to current numbers.
3. **Role model: full five-role, or core three + variants?** RESOLVED: Full five-role model (Operator, PM, Builder, Researcher, Auditor).

## Contract Spec

### Change 1: New Pattern — Role Separation

New file `patterns/ROLE_SEPARATION.md`. Documents the five-role model with:
- Explicit authorities and boundaries per role (table format)
- The relay pattern (Operator intent → PM → Researcher → PM → Builder → PM → Operator)
- Role boundary enforcement across all three tiers
- Protocol for when roles need to cross boundaries (don't; note in debrief; PM triages)
- Real example from the D&D project showing all five roles in a single cycle

### Change 2: New Pattern — Research-to-Build Pipeline

New file `patterns/RESEARCH_TO_BUILD_PIPELINE.md`. Documents the staged conversion pipeline:
- Five stages: Burst → Research WO → Findings Memo → Brick → Builder WO
- Brick composition: Target Lock + Binary Decisions + Contract Spec + Implementation Plan
- WIP limits (1-2 READY Bricks ahead)
- Why builders never see research (context window optimization, not information hiding)
- Real example: BURST-001 (Voice-First Reliability) → 5 research WOs → 1 playbook → 19 planned builder WOs

### Change 3: New Pattern — Plain English Pass

New file `patterns/PLAIN_ENGLISH_PASS.md`. Documents the non-technical translation layer:
- Three questions: What problem? What does it do? Why should anyone care?
- 150-word hard cap
- Quality check criteria (fails if it contains class names, rule IDs, programming terms)
- Upgrades debrief from 2-pass to 4-pass (Plain English → Full Dump → PM Summary → Retrospective)
- Two worked examples: WO-RNG-PROTOCOL-001 (62 words) and WO-ROADMAP-AUDIT (117 words)

### Change 4: New Pattern — Debrief Integrity Boundary

New file `patterns/DEBRIEF_INTEGRITY_BOUNDARY.md`. Names the trust boundary:
- Verification spectrum: Tier 1 (machine-verifiable: test counts, diff stats) → Tier 2 (process-verifiable: commit hashes, scope compliance) → Tier 3 (prose-only: retrospective, concerns)
- Four mitigation options: cross-agent audit, spot-check protocol, expand machine-verified surface, debrief-by-next-agent
- Minimum viable integrity gate (structured fields in debrief template)
- PM review checklist

### Change 5: Template Updates

**SESSION_MEMO_TEMPLATE.md:**
- Add Plain English Summary section (3 questions) to the template block, before Action Items
- Replace "Two-Pass Writing Process" with "Four-Pass Writing Process" (Pass 0 Plain English, Pass 1 Full Dump, Pass 2 PM Summary, Pass 3 Retrospective)
- Add cross-reference to Debrief Integrity Boundary pattern

**HANDOFF_TEMPLATE.md:**
- Add optional Plain English Summary section (2 questions: What was this session doing? Where did it leave off?)
- Add cross-reference to Plain English Pass pattern

### Change 6: Case Study Updates

**METRICS.md:**
- Add "Last Updated: 2026-02-14" header
- Agent sessions: 20+ → 40+
- Add rows: Total WOs dispatched (33), Builder debriefs archived (12), Research documents produced (19)
- H1 batch: tests passing 5,775+ → 5,774+

**PROJECT_OVERVIEW.md:**
- Add "Last Updated: 2026-02-14" header
- Update scale table to current numbers (5,774+ tests, 33 WOs, 40+ sessions, 12 debriefs, 19 research docs, 10+ governance docs)
- Move VPN/network section from README to here (case-study-specific context)

**FAILURE_CATALOG.md:**
- Add F-009: Constructor Replacement via Blanket Edit (from WO-RNG-PROTOCOL-001 debrief — `replace_all` hit constructor sites)
- Add F-010: Dead Validation Rule / Silent Pass (from roadmap audit — CT-006/RV-007 check empty field, report PASS)
- Update summary table (8 → 10 entries, new category "False Confidence")

**LESSONS_LEARNED.md:**
- Update header: "2 weeks" → "3+ weeks", "5,500+" → "5,774+"
- Add "What Worked" #6: Debriefs as a learning loop
- Add "What We'd Do Differently" #6: Plain English debrief pass from Day 1

### Change 7: README Updates

- Pattern table: add 4 new patterns (Role Separation, Research-to-Build Pipeline, Plain English Pass, Debrief Integrity Boundary) — table grows from 10 to 14
- Replace VPN section with 2-line pointer to case-study/PROJECT_OVERVIEW.md
- Update origin stats to current project numbers
- Update "What Makes This Different" stats (10 error patterns, 33 WOs, 40+ sessions)

## Constraints

- Do NOT change content of existing pattern files (only add new ones)
- Do NOT change the Integration Canary pattern or WO template (shipped in WO-FRAMEWORK-UPDATE-001)
- Do NOT remove the "former chef, English educator" framing
- Do NOT change the MIT license or closing quote

## Success Criteria

- [x] `patterns/ROLE_SEPARATION.md` exists with five roles, authorities, boundaries, relay pattern
- [x] `patterns/RESEARCH_TO_BUILD_PIPELINE.md` exists with 5-stage pipeline, Brick composition, real example
- [x] `patterns/PLAIN_ENGLISH_PASS.md` exists with 3 questions, 150-word cap, worked examples
- [x] `patterns/DEBRIEF_INTEGRITY_BOUNDARY.md` exists with verification spectrum, 4 mitigations
- [x] SESSION_MEMO_TEMPLATE has Plain English section and 4-pass process
- [x] HANDOFF_TEMPLATE has optional Plain English summary
- [x] Pattern table in README has 14 entries
- [x] VPN section moved from README to PROJECT_OVERVIEW.md
- [x] Case study metrics match current project state (5,774+ tests, 33 WOs, 40+ sessions)
- [x] F-009 and F-010 added to FAILURE_CATALOG.md following existing format
- [x] LESSONS_LEARNED has debrief-as-learning-loop and plain-english-from-day-1 entries
- [x] All internal markdown links resolve correctly

## Files Changed

**New (4):**
- `patterns/DEBRIEF_INTEGRITY_BOUNDARY.md`
- `patterns/ROLE_SEPARATION.md`
- `patterns/RESEARCH_TO_BUILD_PIPELINE.md`
- `patterns/PLAIN_ENGLISH_PASS.md`

**Modified (7):**
- `README.md`
- `templates/SESSION_MEMO_TEMPLATE.md`
- `templates/HANDOFF_TEMPLATE.md`
- `case-study/METRICS.md`
- `case-study/PROJECT_OVERVIEW.md`
- `case-study/FAILURE_CATALOG.md`
- `case-study/LESSONS_LEARNED.md`

## Delivery

- Branch: `update/framework-v2-patterns-and-metrics`
- Commit: `aaecfef` — `docs: add 4 patterns, update metrics, extend failure catalog`
- PR: https://github.com/timothyjrainwater-lab/multi-agent-coordination-framework/pull/1
- Total: 720 lines added, 32 removed across 11 files

---

*End of WO-FRAMEWORK-UPDATE-002*
