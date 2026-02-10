# Agent A Deliverables Summary
## R0 Research Phase: Canonical Foundations Complete

**Agent:** Agent A (Canonical Foundations Architect)
**Date:** 2026-02-10
**Mode:** R0 Research (docs + proposals only, no mainline refactors)
**Status:** ✅ DELIVERABLES COMPLETE, AWAITING REVIEW

---

## Deliverables

### 1. R0 Canonical ID Schema ✅
**File:** `docs/research/R0_CANONICAL_ID_SCHEMA.md`
**Size:** ~1,100 lines
**Status:** Structured spec, unambiguous, ready for implementation

**Contents:**
- 7 ID namespaces defined (mechanical, entity, asset, session, event, campaign, prepjob)
- Format specifications with regex validation patterns
- Determinism guarantees documented
- Collision resistance analyzed (8-char vs 12-char hashes)
- 30 reference ID examples provided
- Bad ID examples cataloged
- Python implementation stubs included
- 30 open questions from draft resolved

**Key Decisions:**
- Mechanical IDs: `spell.fireball` (human-readable, no hashes)
- Entity IDs: `entity_<camp_id>_<12_char_hash>` (campaign-scoped)
- Asset IDs: `asset_<camp_id>_<type>_<12_char_hash>` (content-addressed)
- Session IDs: `session_<camp_id>_<seq>_<8_char_hash>` (sequential + hash)
- Event IDs: `event_<session_id>_<seq>_<8_char_hash>` (append-only)

**Resolved Gaps:**
- GAP-001 (🔴 CRITICAL): Canonical ID schema undefined
- Constraint A3 (🔴 SACRED): Canonical IDs for all mechanical entities

---

### 2. R0 Determinism Contract ✅
**File:** `docs/research/R0_DETERMINISM_CONTRACT.md`
**Size:** ~950 lines
**Status:** Structured spec, enforceable, ready for validation

**Contents:**
- Layer boundaries (mechanical vs presentation vs metadata)
- RNG stream isolation (combat, initiative, saves, skill_checks, weather)
- Seed management (campaign seed + event-specific seeds)
- Forbidden non-deterministic sources (timestamps, UUIDs, unseeded random)
- Event sourcing contract (all state changes via events)
- Asset generation determinism (3 strategies: A, B, C)
- Player modeling determinism (profile stored in campaign metadata)
- Determinism verification protocol (10× replay test)

**Key Decisions:**
- Mechanical outcomes MUST be identical (dice, damage, HP, positions)
- Presentation MAY vary (LLM narration, asset appearance, UI animations)
- RNG streams MUST be isolated (prevent accidental coupling)
- Timestamps FORBIDDEN in mechanical logic (use turn counters)
- Floating-point math FORBIDDEN (use CP-001 integer math)
- Asset determinism strategy: Recommend **Strategy B (Asset Export)** for M2

**Resolved Risks:**
- DET-001 (🟡 MEDIUM): LLM narration variance (presentation layer, allowed)
- DET-002 (🟡 MEDIUM): Player modeling (stored in campaign metadata, deterministic)
- DET-003 (🔴 CRITICAL): Asset generation (strategy B guarantees determinism)
- DET-004 (🟢 LOW): RNG stream isolation (already verified in CP-001 baseline)
- DET-005 (🟢 LOW): Position float drift (CP-001 integer math, verified)

---

### 3. R0 Import and Skin Pack Validation ✅
**File:** `docs/research/R0_IMPORT_AND_SKINPACK_VALIDATION.md`
**Size:** ~780 lines
**Status:** Structured spec, enforceable, ready for implementation

**Contents:**
- Skin Pack schema (display names, aliases, descriptions, tone constraints)
- 8 validation rules with enforcement checks
- Campaign import validation (manifest integrity, version compatibility, entity IDs)
- Rejection criteria (critical vs warnings)
- Security checks (no code execution, resource limits)
- Hot-swap rules (safe times to change Skin Packs)
- Validation test harness examples
- 3 rejection examples (mechanical smuggling, alias conflict, unknown ID)

**Key Decisions:**
- Skin Packs are **decorators**, not **overrides** (presentation only)
- Forbidden fields: damage, range, area_of_effect, duration, saving_throw, attack_bonus, etc.
- Alias conflicts MUST be rejected (ambiguous input mappings)
- Resource limits enforced (10MB file, 10k display names, 50k aliases/language)
- Code execution patterns rejected (eval, exec, <script>, javascript:)
- Hot-swap allowed between sessions, FORBIDDEN mid-combat

**Resolved Gaps:**
- GAP-002 (🔴 CRITICAL): Skin Pack schema undefined
- Constraint B1 (🟠 CRITICAL): Skin Packs cannot alter mechanics

---

## Exit Criteria Status

### Deliverable 1: Canonical ID Schema

- [x] Format specifications unambiguous
- [x] Validation rules defined with regex patterns
- [x] Determinism guarantees documented
- [x] Collision resistance analyzed
- [x] 30 reference examples provided
- [x] Bad ID examples documented
- [x] Integration with existing code defined
- [ ] Cross-agent review complete (awaiting Agent B, C, D)
- [ ] PM approval obtained

**Ready for:** Cross-agent review

---

### Deliverable 2: Determinism Contract

- [x] Determinism definition unambiguous
- [x] Layer boundaries documented (mechanical vs presentation vs metadata)
- [x] RNG stream isolation specified
- [x] Forbidden sources cataloged
- [x] Event sourcing contract defined
- [x] Verification protocol defined (10× replay test)
- [x] Asset generation strategy specified (recommend Strategy B)
- [x] Player modeling determinism clarified
- [ ] Cross-agent review complete (awaiting Agent B, C, D)
- [ ] PM approval obtained

**Ready for:** Cross-agent review

---

### Deliverable 3: Import and Skin Pack Validation

- [x] Skin Pack schema defined
- [x] Validation rules unambiguous (8 rules documented)
- [x] Rejection criteria specified (critical vs warnings)
- [x] Security checks defined (no code execution)
- [x] Campaign import validation specified
- [x] Hot-swap rules defined
- [x] Test harness examples provided
- [x] Rejection examples documented
- [ ] Cross-agent review complete (awaiting Agent B, C, D)
- [ ] PM approval obtained

**Ready for:** Cross-agent review

---

## Key Trade-Offs Documented

### Trade-Off 1: ID Namespace Complexity

**Decision:** Use 7 distinct namespaces (mechanical, entity, asset, session, event, campaign, prepjob)

**Pros:**
- ✅ Type safety (no cross-namespace collisions)
- ✅ Enables type-based queries (e.g., "all assets of type portrait")
- ✅ Human-readable prefixes aid debugging

**Cons:**
- ❌ More complex ID system (vs single namespace)
- ❌ More validation rules to enforce

**Rationale:** Type safety and debuggability outweigh complexity cost.

---

### Trade-Off 2: Asset Determinism Strategy

**Decision:** Recommend Strategy B (Asset Export) for M2

**Pros:**
- ✅ Guaranteed determinism (identical assets)
- ✅ No generation model dependency
- ✅ Works with any generation model (even non-deterministic)

**Cons:**
- ❌ Large export files (~500MB-2GB for 100 assets)
- ❌ Cannot regenerate if assets lost

**Alternative:** Strategy A (Deterministic Seeding) — HIGH RISK until generation determinism verified

**Rationale:** Safety first. Can migrate to Strategy A later if generation models proven deterministic.

---

### Trade-Off 3: Mechanical ID Format

**Decision:** Use human-readable format (`spell.fireball`) instead of hashes

**Pros:**
- ✅ Debugging-friendly (logs are readable)
- ✅ No generation required (name = ID)
- ✅ Deterministic by definition

**Cons:**
- ❌ Name changes require ID updates (but IDs should be immutable)
- ❌ Requires manual curation of canonical names

**Rationale:** Debuggability and simplicity outweigh curation cost.

---

## Open Questions for Cross-Agent Review

### Question 1: Hash Length Trade-Off
**Q:** Should we use 8-char or 12-char hashes for entity/asset IDs?
**Current Decision:** 12-char (collision probability ~1 in 281 trillion)
**Feedback Needed:** Is 12-char overkill? Would 10-char suffice?

### Question 2: Asset Determinism for M3
**Q:** Should M3 implement Strategy A (Deterministic Seeding) or stick with Strategy B (Asset Export)?
**Current Recommendation:** Strategy B (safe)
**Feedback Needed:** Is there time to verify generation model determinism before M3?

### Question 3: Skin Pack Hot-Swap Mid-Session
**Q:** Should we allow Skin Pack swaps between encounters (not just between sessions)?
**Current Decision:** No (FORBIDDEN mid-combat, allowed between sessions)
**Feedback Needed:** Is this too restrictive? Should we allow between encounters?

### Question 4: Cross-Language Alias Consistency
**Q:** Should cross-language alias inconsistency be an error (reject) or warning (allow)?
**Current Decision:** Warning (allow, but log)
**Feedback Needed:** Is this permissive enough, or should we enforce stricter consistency?

---

## Integration Points with Other Agents

### Agent B (If Assigned)
**Potential Responsibilities:**
- Implement `aidm/schemas/canonical_ids.py` (ID generation functions)
- Add validation helpers (regex patterns from R0 spec)
- Write unit tests for ID determinism

**Handoff Requirements:**
- Review R0_CANONICAL_ID_SCHEMA.md for format specs
- Use provided Python stubs as starting point

---

### Agent C (If Assigned)
**Potential Responsibilities:**
- Implement Skin Pack loader + validator
- Campaign import validation logic
- Asset determinism strategy implementation

**Handoff Requirements:**
- Review R0_IMPORT_AND_SKINPACK_VALIDATION.md for validation rules
- Use provided validation check examples

---

### Agent D (If Assigned - Already Completed Audit)
**Potential Responsibilities:**
- Update AGENT_D_TOPIC_INDEX.md with new canonical ID references
- Verify R0 specs align with GLOBAL-AUDIT-001 findings
- Cross-check R0 specs against existing codebase

**Handoff Requirements:**
- Review all 3 R0 deliverables
- Confirm no contradictions with audit findings

---

## Gaps Closed by R0 Deliverables

| Gap ID | Description | Closed By |
|--------|-------------|-----------|
| GAP-001 | Canonical ID Schema missing | R0_CANONICAL_ID_SCHEMA.md |
| GAP-002 | Skin Pack Schema missing | R0_IMPORT_AND_SKINPACK_VALIDATION.md |
| GAP-003 | Alias Table System missing | R0_CANONICAL_ID_SCHEMA.md (aliases in Skin Packs) |
| DET-001 | LLM narration variance | R0_DETERMINISM_CONTRACT.md (presentation layer) |
| DET-002 | Player modeling affects replay | R0_DETERMINISM_CONTRACT.md (profile in metadata) |
| DET-003 | Asset generation non-determinism | R0_DETERMINISM_CONTRACT.md (Strategy B) |

---

## Next Steps

### For PM/Lead
1. **Review all 3 R0 deliverables**
2. **Make 4 strategic decisions:**
   - Hash length (8-char, 10-char, or 12-char)?
   - Asset determinism strategy for M2 (B) and M3 (A or B)?
   - Skin Pack hot-swap rules (between sessions only, or between encounters)?
   - Cross-language alias consistency (warning or error)?
3. **Approve R0 specs** OR request adjustments
4. **Assign implementation agents** (Agent B for IDs, Agent C for validation)

### For Agent B (ID Implementation)
1. Create `aidm/schemas/canonical_ids.py`
2. Implement 7 ID generator functions (mechanical, entity, asset, session, event, campaign, prepjob)
3. Add validation functions (regex patterns from R0 spec)
4. Write 100+ unit tests (determinism, collision detection, format validation)

### For Agent C (Validation Implementation)
1. Create `aidm/schemas/skin_pack.py`
2. Implement 8 validation rules (from R0 spec)
3. Add campaign import validator
4. Write 50+ unit tests (rejection criteria, security checks)

### For Agent D (Cross-Agent Review)
1. Update AGENT_D_TOPIC_INDEX.md with canonical ID references
2. Cross-check R0 specs against GLOBAL-AUDIT-001 findings
3. Identify any contradictions or missing requirements

---

## Hard Constraints Observed

✅ **DO NOT modify engine behavior** — All R0 deliverables are proposals/specs only
✅ **Experiments in docs/research/** — All 3 files created in research directory
✅ **Decisions as proposals** — All decisions documented with trade-offs, not silently adopted

---

## Completion Statement

**Agent A (Canonical Foundations Architect) has completed R0 research phase deliverables.**

**Status:** ✅ ALL DELIVERABLES COMPLETE
**Total Output:** 3 structured specs (~2,800 lines)
**Gaps Closed:** GAP-001, GAP-002, GAP-003, DET-001, DET-002, DET-003
**Constraints Satisfied:** A3 (Canonical IDs), B1 (Skin Pack safety), A1 (Determinism)

**Ready for:** Cross-agent review (Agent B, C, D) + PM approval

**Awaiting:** Strategic decisions on 4 open questions + implementation assignment

---

**END OF AGENT A SUMMARY**
