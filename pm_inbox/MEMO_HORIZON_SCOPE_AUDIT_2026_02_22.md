# MEMO: Horizon Scope Audit — Remaining Work to Final Release

**From:** Builder (Opus 4.6), at Thunder's request
**Date:** 2026-02-22
**Lifecycle:** NEW
**Priority:** MEDIUM — no immediate action blocks; strategic visibility gap

---

## Purpose

Thunder requested an honest assessment of how much work remains between current state and final release. During review, it became clear that **sprint-level tracking is excellent** (BURST-001 Tier 4 is well-scoped), but there is no single view of remaining scope at the strategic level. This memo documents what was found so the PM can decide how to address it.

This is **not** a request to pre-build 50 work orders. The project's practice of creating WOs as each phase begins is sound. The gap is **visibility** — Thunder cannot currently look at one document and see the full remaining path to release.

---

## What Is Well-Tracked (No Action Needed)

- **BURST-001 Tiers 1-3:** Complete. 275 gate tests. 9 WOs integrated.
- **BURST-001 Tier 4:** In progress. 4.1 accepted (31 Gate S tests). 4.2 dispatched. 4.3-4.4 sequenced. Clear chain to completion.
- **BURST-001 Tier 5:** 5.1-5.4 already complete. Only 5.5 (Playtest v1) remains, blocked on 4.4. Known dependency.
- **WO-CHARGEN-FOUNDATION-001:** Dispatched. Covers GAP-CG-001, GAP-CG-002, GAP-CG-003.
- **Open findings:** FINDING-HOOLIGAN-03, FINDING-GRAMMAR-01, GAP-A, GAP-B all tracked in briefing.
- **Test health:** 6,299 passing. All skips are conditional (missing assets/dependencies), not hidden bugs.

---

## Strategic Gaps: Known Work Without WO Decomposition

These are items that have been **researched and documented** but exist only as task checklists or gap lists — not as WO sequences. No one is asking for the WOs to be created now. The ask is: **does the PM have a consolidated view of these, and is sequencing/dependency roughly understood?**

### 1. Chargen — 12 of 15 Gaps Unassigned

Source: `pm_inbox/reviewed/WO-CHARGEN-RESEARCH-001_DELIVERABLES.md`

WO-CHARGEN-FOUNDATION-001 covers GAP-CG-001 (ability scores), GAP-CG-002 (races), GAP-CG-003 (weapon/armor catalog). The remaining 12:

| Gap | Description | Severity | WO Exists? |
|-----|-------------|----------|------------|
| GAP-CG-004 | Masterwork modifier system | MEDIUM | No |
| GAP-CG-005 | Ammunition tracking | MEDIUM | No |
| GAP-CG-006 | Skill point allocation | HIGH | No |
| GAP-CG-007 | Chargen wizard/pipeline | HIGH | No |
| **GAP-CG-008** | **Spellcasting system** | **CRITICAL** | **No** |
| GAP-CG-009 | Animal companion system | MEDIUM | No |
| GAP-CG-010 | Mounted combat system | MEDIUM | No |
| GAP-CG-011 | Condition application pipeline | MEDIUM | No |
| GAP-CG-012 | Multiclass XP penalties | LOW | No |
| GAP-CG-013 | Character persistence | LOW | No |
| GAP-CG-014 | Masterwork tool ruling | MEDIUM | No |
| GAP-CG-015 | Summon creature system | MEDIUM | No |

**Critical note from research deliverable:** GAP-CG-008 (spellcasting) was flagged as the single most critical gap. Without it, Druid, Cleric, and Wizard are mechanically inert. This also blocks several source-code TODOs (ranged AoO provocation, spellcasting provocation in `aoo.py`).

**PM action:** No WOs needed now. But the chargen gap list should be visible in whatever horizon document exists, with GAP-CG-008 and GAP-CG-006 marked as critical-path.

### 2. Milestone M1 — Solo Vertical Slice (17 Tasks, 0 WOs)

Source: `docs/AIDM_EXECUTION_ROADMAP_V3.md`

M1 defines the end-to-end loop: a player sits down, creates a character, enters a session, plays, and exits. The roadmap lists 17 supporting tasks (M1.1-M1.17) covering intent lifecycle, character sheet UI, voice/text input, narration pipeline, and E2E testing. None have been decomposed into WOs.

**Relationship to current work:** BURST-001 (voice reliability) and chargen (character data) are both prerequisites for M1 but do not fulfill it. M1 is the integration layer that connects them into a playable experience.

**PM action:** M1 doesn't need WOs yet, but its 17 tasks should appear on the horizon view with a note that it's blocked on BURST-001 completion and chargen progress.

### 3. Milestone M2 — Campaign Prep Pipeline (11 Tasks Unassigned)

Source: `docs/AIDM_EXECUTION_ROADMAP_V3.md`

The persistence layer (M2.1) was completed during earlier work. The remaining 11 tasks cover: Session Zero loader, DM agent orchestration, NPC generation, encounter scaffolding, asset request system, export/import, and prep UX.

**PM action:** Note on horizon view. Blocked on M1.

### 4. Milestone M3 — Immersion Layer (15 Tasks, 0 WOs)

Source: `docs/AIDM_EXECUTION_ROADMAP_V3.md`

Covers STT/TTS model selection, image generation, audio pipeline, contextual grid overlay. 15 tasks listed. BURST-001 is a prerequisite (reliable voice foundation) but is not M3 itself.

**PM action:** Note on horizon view. Partially unblocked by BURST-001 completion.

### 5. Milestone M4 — Offline Packaging (4 Tasks, 0 WOs)

Source: `docs/AIDM_EXECUTION_ROADMAP_V3.md`

Covers hardware tiers, version pinning, distribution, acceptance criteria.

**PM action:** Note on horizon view. Relationship to PRS-01 should be clarified (overlapping scope vs. sequential).

### 6. PRS-01 — Publishing Readiness (Spec Drafted, 6 Builder WOs Estimated, 0 Dispatched)

Source: `docs/contracts/PUBLISHING_READINESS_SPEC.md`

The spec defines gates P1-P9 and estimates 6 builder WOs in Appendix A:
1. WO-PRS-SCAN-001 (asset/secret/IP scans)
2. WO-PRS-LICENSE-001 (license ledger + lint)
3. WO-PRS-OFFLINE-001 (offline guarantee)
4. WO-PRS-FIRSTRUN-001 (fail-closed first run)
5. WO-PRS-DOCS-001 (privacy statement + OGL notice)
6. WO-PRS-ORCHESTRATOR-001 (RC packet builder)

**Status:** Spec awaiting Thunder review. No WOs can be dispatched until approved.

**PM action:** Already on the briefing as "PRS-01 spec review." No additional action unless Thunder wants to accelerate.

### 7. BURST-002, 003, 004

| Burst | Status | Remaining |
|-------|--------|-----------|
| BURST-002 (Model/Runtime) | Not started | 3 binary decisions pending, no research WO drafted |
| BURST-003 (Tactical Grid) | ~60% done | AoE preview pending (1 binary decision, ~1 WO) |
| BURST-004 (Workflow Friction) | Deferred | Intentionally waiting for 3+ recurrences |

**PM action:** BURST-003's remaining AoE work should be on the horizon view. BURST-002 and BURST-004 are correctly deferred.

### 8. Source Code TODOs (17 Items)

17 TODO/FIXME markers exist in the codebase. Most are symptoms of chargen gaps (no spellcasting, no proficiency checks, no ranged AoO). These will resolve naturally as chargen WOs are executed. Not separately actionable.

### 9. Governance Infrastructure (Counter-Thesis Items)

Source: `docs/planning/COUNTER_THESIS_OPERATIONAL_REALITY_2026_02_13.md`

8 proposed items (SOURCES_OF_TRUTH.md, CONTRIBUTING.md, CHANGELOG.md, verify_session_start.py, test_document_budget.py, test_architecture_coverage.py, CI pipeline, docs/STATE.md consolidation) — none exist yet. These are process improvements, not feature work. Low priority relative to feature delivery.

**PM action:** Optional. Could be a post-M1 housekeeping pass or folded into PRS-01.

---

## Recommended PM Action

**One deliverable requested:** A single-page **Horizon Scope Summary** added to the roadmap or briefing infrastructure. Contents:

1. Remaining scope grouped by layer (Engine / Experience / Ship It)
2. Each item listed with: name, source document, rough dependency, and whether it's on the critical path
3. No WO detail — just the chunk names and ordering

This gives Thunder a bird's-eye view without requiring premature WO creation. It can be updated as phases complete and new information emerges.

**This is not urgent.** BURST-001 Tier 4 execution should continue uninterrupted. The horizon summary can be drafted during the next PM cycle after Tier 4.2 dispatch settles.

---

## Summary Table

| Area | Items Identified | WOs Exist | Critical Path? |
|------|-----------------|-----------|----------------|
| BURST-001 (remaining) | 3-4 WOs | Yes | Yes |
| Chargen (remaining gaps) | 12 | No | Yes (GAP-CG-008 especially) |
| M1 Vertical Slice | 17 tasks | No | Yes |
| M2 Campaign Prep | 11 tasks | No | After M1 |
| M3 Immersion | 15 tasks | No | After BURST-001 |
| M4 Packaging | 4 tasks | No | After M2 |
| PRS-01 Builder WOs | 6 estimated | No (spec drafted) | Final gate |
| BURST-003 AoE | 1 WO | No | No |
| Governance infra | 8 items | No | No |
| Source TODOs | 17 markers | N/A (symptom) | Resolves with chargen |
