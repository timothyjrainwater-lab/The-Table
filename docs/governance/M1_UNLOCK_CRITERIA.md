# M1 Unlock Criteria — Gated Progression Control

**Document Type:** Governance / Phase Gate Control
**Purpose:** Define explicit criteria for unlocking M1 (Immersion + Indexed Memory) after M0 completion
**Owner:** Agent D (Research Orchestrator)
**Status:** LOCKED (M0 planning in progress)
**Last Updated:** 2026-02-10

---

## Document Purpose

This document defines the **hard gates** that must be satisfied before M1 work can begin. M1 includes:
- Indexed memory implementation (RQ-LLM-001, RQ-LLM-002)
- Policy gap resolution (GAP-POL-01 through GAP-POL-04)
- Immersion layer enhancements
- Multi-session persistence

**M1 remains LOCKED until ALL unlock criteria are satisfied.**

---

## M1 Unlock Criteria (ALL Required)

### 1. M0 Completion Gate

**Requirement:** M0 must be SHIPPED and VALIDATED before M1 begins.

**Acceptance Criteria:**
- ✅ M0 shipped to production (or public beta)
- ✅ M0 playtest completed (minimum 10 sessions, 5+ users)
- ✅ M0 post-launch review completed (bugs triaged, critical fixes deployed)
- ✅ M0 performance validated (meets or exceeds targets)

**Evidence Required:**
- M0 release notes (version number, release date)
- Playtest report (session count, user feedback summary)
- Post-launch bug triage log
- Performance benchmarks (LLM tokens/sec, asset load times)

**NO-GO Trigger:**
- ❌ M0 not shipped or delayed >3 months from planned date
- ❌ M0 playtest reveals critical architectural issues
- ❌ M0 user feedback <50% "acceptable or better" rating

---

### 2. Policy Gap Resolution

**Requirement:** All M1-scoped policy gaps (GAP-POL-01 through GAP-POL-04) must be DOCUMENTED before M1 implementation.

**Acceptance Criteria:**
- ✅ GAP-POL-01 (Cache Invalidation Strategy) documented
- ✅ GAP-POL-02 (Entity Rename Propagation) documented
- ✅ GAP-POL-03 (Deleted Entity Handling) documented
- ✅ GAP-POL-04 (Multilingual Alias Resolution) documented

**Evidence Required:**
- `docs/policies/CACHE_INVALIDATION_POLICY.md` (GAP-POL-01)
- `docs/policies/ENTITY_RENAME_POLICY.md` (GAP-POL-02)
- `docs/policies/DELETED_ENTITY_POLICY.md` (GAP-POL-03)
- `docs/policies/MULTILINGUAL_ALIAS_POLICY.md` (GAP-POL-04)

**Document Format:**
Each policy must include:
- Problem statement
- Design constraints
- Accepted solution (with rationale)
- Alternatives considered (with rejection rationale)
- Test cases
- Edge cases

**NO-GO Trigger:**
- ❌ Policy documents incomplete or missing
- ❌ Policy documents lack rationale or test cases
- ❌ Policy conflicts unresolved (e.g., cache invalidation contradicts determinism)

---

### 3. M0 Lessons Learned

**Requirement:** M0 retrospective must be completed before M1 planning.

**Acceptance Criteria:**
- ✅ M0 retrospective meeting held (PM, Agent D, stakeholders)
- ✅ M0 lessons learned documented
- ✅ M0 architectural decisions reviewed (keep/change/pivot)
- ✅ M1 scope adjusted based on M0 feedback

**Evidence Required:**
- `docs/retrospectives/M0_RETROSPECTIVE.md` (meeting notes, action items)
- M1 scope revisions (if any)

**NO-GO Trigger:**
- ❌ M0 retrospective not held
- ❌ Critical M0 issues not addressed in M1 planning
- ❌ M1 scope expands without justification

---

### 4. Indexed Memory Architecture Validation

**Requirement:** Indexed memory architecture (RQ-LLM-001, RQ-LLM-002) must be VALIDATED in M0 context before M1 implementation.

**Acceptance Criteria:**
- ✅ M0 codebase reviewed for memory integration points
- ✅ Indexed memory schemas validated against M0 data structures
- ✅ Query interface prototyped and tested with M0 event logs
- ✅ Performance targets validated (retrieval <200ms, accuracy >90%)

**Evidence Required:**
- `docs/research/R0_INDEXED_MEMORY_VALIDATION.md` (prototype results)
- M0 integration analysis (affected modules, API changes)
- Performance benchmarks (query latency, retrieval accuracy)

**NO-GO Trigger:**
- ❌ Indexed memory incompatible with M0 architecture (requires major refactor)
- ❌ Performance targets not met (<200ms latency or <90% accuracy)
- ❌ Integration complexity exceeds budget (>1 month dev time for integration)

---

### 5. M1 Planning Approval

**Requirement:** M1 plan must be APPROVED by PM before M1 development begins.

**Acceptance Criteria:**
- ✅ M1 plan document created (`docs/milestones/M1_PLAN.md`)
- ✅ M1 scope locked (features, timeline, resources)
- ✅ M1 dependencies validated (no M0 blockers)
- ✅ M1 plan reviewed and approved by PM

**Evidence Required:**
- `docs/milestones/M1_PLAN.md` (scope, timeline, resources, risks)
- PM approval signature (document footer or approval log)

**NO-GO Trigger:**
- ❌ M1 plan incomplete or missing
- ❌ M1 plan not approved by PM
- ❌ M1 timeline exceeds 6 months (pivot to M2 or rescope)

---

### 6. M0 Critical Fixes Deployed

**Requirement:** All CRITICAL M0 bugs must be FIXED before M1 begins.

**Acceptance Criteria:**
- ✅ No open CRITICAL bugs in M0 bug tracker
- ✅ High-priority bugs triaged (defer to M1 or fix in M0 patch)
- ✅ M0 stability validated (no crashes, no data loss)

**Evidence Required:**
- Bug tracker report (CRITICAL bugs = 0)
- M0 patch release notes (if applicable)

**NO-GO Trigger:**
- ❌ CRITICAL bugs not fixed
- ❌ M0 unstable (crashes, data loss, unplayable)
- ❌ M0 requires major rework before M1

---

## M1 Unlock Decision Framework

### GO Criteria (Proceed to M1)

**MUST satisfy ALL 6 unlock criteria:**

1. ✅ M0 Completion Gate (shipped, playtested, validated)
2. ✅ Policy Gap Resolution (GAP-POL-01 through GAP-POL-04 documented)
3. ✅ M0 Lessons Learned (retrospective completed, lessons applied)
4. ✅ Indexed Memory Architecture Validation (compatible with M0, performance validated)
5. ✅ M1 Planning Approval (plan created, reviewed, approved by PM)
6. ✅ M0 Critical Fixes Deployed (no CRITICAL bugs, stable release)

**Timeline to GO:** 2-4 weeks after M0 ships

---

### NO-GO Criteria (Pause or Pivot)

**ANY ONE of the following triggers NO-GO:**

1. ❌ **M0 not shipped** (delayed >3 months or cancelled)
   - **Pivot:** Focus on M0 completion, defer M1 indefinitely

2. ❌ **Policy gaps unresolved** (GAP-POL-01 through GAP-POL-04 incomplete)
   - **Pivot:** Complete policy documentation before M1 unlock

3. ❌ **M0 lessons not learned** (retrospective skipped or ignored)
   - **Pivot:** Conduct retrospective, apply lessons before M1

4. ❌ **Indexed memory incompatible** (requires major M0 refactor)
   - **Pivot:** Redesign indexed memory or defer to M2

5. ❌ **M1 plan not approved** (PM rejects scope, timeline, or resources)
   - **Pivot:** Revise M1 plan or cancel M1

6. ❌ **M0 critical bugs unfixed** (crashes, data loss, unplayable)
   - **Pivot:** Fix M0 bugs before M1 unlock

---

## M1 Unlock Process

### Phase 1: M0 Closeout (Week 1-2 after M0 ships)

**Actions:**
1. Conduct M0 playtest (10 sessions, 5+ users)
2. Collect user feedback (surveys, interviews)
3. Triage M0 bugs (CRITICAL → fix immediately, HIGH → M0 patch or M1, LOW → defer)
4. Deploy M0 critical fixes (if needed)
5. Conduct M0 retrospective (PM, Agent D, stakeholders)
6. Document M0 lessons learned

**Deliverables:**
- M0 playtest report
- M0 bug triage log
- M0 retrospective notes
- M0 lessons learned document

---

### Phase 2: Policy Gap Resolution (Week 3-4 after M0 ships)

**Actions:**
1. Agent A authors policy documents (GAP-POL-01 through GAP-POL-04)
2. Agent D reviews policy documents for completeness
3. PM approves policy documents

**Deliverables:**
- `docs/policies/CACHE_INVALIDATION_POLICY.md`
- `docs/policies/ENTITY_RENAME_POLICY.md`
- `docs/policies/DELETED_ENTITY_POLICY.md`
- `docs/policies/MULTILINGUAL_ALIAS_POLICY.md`

---

### Phase 3: Indexed Memory Validation (Week 3-4 after M0 ships)

**Actions:**
1. Agent A prototypes indexed memory integration with M0
2. Agent D validates performance benchmarks (retrieval <200ms, accuracy >90%)
3. Agent A documents integration analysis (affected modules, API changes)

**Deliverables:**
- `docs/research/R0_INDEXED_MEMORY_VALIDATION.md`
- Performance benchmark report

---

### Phase 4: M1 Planning (Week 5-6 after M0 ships)

**Actions:**
1. Agent D drafts M1 plan (scope, timeline, resources, risks)
2. PM reviews M1 plan
3. PM approves or rejects M1 plan

**Deliverables:**
- `docs/milestones/M1_PLAN.md`

---

### Phase 5: M1 Unlock (Week 7+ after M0 ships)

**Trigger:** All 6 unlock criteria satisfied

**Actions:**
1. Agent D updates M1 status: LOCKED → UNLOCKED
2. Agent D notifies PM and all agents
3. M1 work authorized to begin

**Deliverables:**
- M1 unlock announcement (email, Slack, meeting)
- M1 status update in governance documents

---

## M1 Unlock Checklist

**Before M1 unlock, verify ALL of the following:**

- [ ] M0 shipped to production (or public beta)
- [ ] M0 playtest completed (10 sessions, 5+ users)
- [ ] M0 post-launch review completed (bugs triaged, critical fixes deployed)
- [ ] M0 performance validated (meets targets)
- [ ] GAP-POL-01 (Cache Invalidation Strategy) documented
- [ ] GAP-POL-02 (Entity Rename Propagation) documented
- [ ] GAP-POL-03 (Deleted Entity Handling) documented
- [ ] GAP-POL-04 (Multilingual Alias Resolution) documented
- [ ] M0 retrospective completed (lessons learned documented)
- [ ] M1 scope adjusted based on M0 feedback
- [ ] Indexed memory architecture validated (compatible with M0)
- [ ] Indexed memory performance validated (retrieval <200ms, accuracy >90%)
- [ ] M1 plan created (`docs/milestones/M1_PLAN.md`)
- [ ] M1 plan approved by PM
- [ ] No CRITICAL M0 bugs remaining
- [ ] M0 stable (no crashes, no data loss)

**If ALL checkboxes are checked:** M1 UNLOCKED → Proceed to M1 development

**If ANY checkbox is unchecked:** M1 LOCKED → Resolve blocker before M1 unlock

---

## Current M1 Status

**Status:** 🔴 **LOCKED** (M0 planning in progress)

**Rationale:**
- M0 not shipped (still in planning phase)
- Policy gaps not resolved (GAP-POL-01 through GAP-POL-04 pending)
- M0 lessons learned N/A (M0 not shipped)
- Indexed memory validation pending (M0 not implemented)
- M1 plan not created
- M0 bugs N/A (M0 not shipped)

**Next Unlock Check:** After M0 ships (estimated: 6-12 months from now)

---

## Governance Notes

### Agent D Stop Authority

**Agent D may HALT M1 unlock if:**
- Policy gaps incomplete or rushed (insufficient rationale, missing test cases)
- M0 lessons learned ignored (same mistakes repeated in M1)
- Indexed memory incompatible (requires major M0 refactor)
- M1 scope creep (features added without PM approval)
- M1 timeline unrealistic (>6 months for core features)

**Escalation:** If Agent D invokes HALT, PM must review and make final decision.

---

### PM Override Authority

**PM may override M1 unlock criteria if:**
- Business needs require M1 features urgently
- M0 delayed indefinitely (pivot to M1 instead)
- M1 scope reduced (policy gaps deferred to M2)

**Override Process:**
1. PM documents override rationale
2. PM explicitly accepts risks
3. PM approves revised M1 unlock criteria
4. Agent D records override in governance log

---

## Revision History

| Date | Version | Agent | Changes |
|------|---------|-------|---------|
| 2026-02-10 | 1.0 | Agent D | Initial M1 unlock criteria created |

---

**END OF M1 UNLOCK CRITERIA** — All gates defined, all NO-GO triggers documented.
