# M3.5 — RAW Compliance Gate

## Milestone Amendment Proposal

**Document ID:** MILESTONE-M3.5-PROPOSAL
**Version:** 1.0.0
**Date:** 2026-02-11
**Status:** PROPOSED (Requires PM Approval)
**Authority:** Amends EXEC-ROADMAP-V3 (v3.2.0 → v3.3.0)
**Proposed By:** Opus (Acting PM)

---

## Rationale

The AIDM engine currently has **2003 passing tests** and claims **FULL RAW fidelity** across 15+ combat mechanics (movement, terrain, cover, conditions, damage). However, no systematic verification has ever been performed that validates these implementations against **specific PHB/DMG citations line-by-line**.

The existing audit infrastructure identifies **what** is implemented and **what risk** it carries, but does not validate **correctness**:

| Document | What It Does | What It Doesn't Do |
|----------|-------------|---------------------|
| Core Ruleset Audit (210 subsystems) | Catalogues mechanics and risk levels | Does not verify implementation correctness |
| RAW Fidelity Audit | Records FULL/DEGRADED/DEFERRED status | Does not prove FULL claims with test evidence |
| Rules Coverage Ledger | Tracks which CP owns what | Does not cross-reference PHB page numbers to test assertions |

**Gap:** We claim FULL coverage on 15+ mechanics but have no formal verification that our implementation matches RAW. If a mechanic is subtly wrong (e.g., cover bonus applied to wrong AC type, flanking geometry off by one cell, bull rush resolution order incorrect), it will silently produce wrong results that compound through spellcasting and advanced combat.

**Risk without M3.5:** Spellcasting (CP-18A) and kernel development (SKR-001+) build on top of existing mechanics. If the foundation has RAW errors, every layer built on it inherits those errors. Fixing them retroactively after M4 would require cascading changes through event logs, replays, and potentially shipped campaigns.

**Conclusion:** A dedicated compliance gate between M3 and M4 is **architecturally mandatory**.

---

## Position in Roadmap

```
M0 — Design Closeout                     [✅ COMPLETE]
       ↓
M1 — Solo Vertical Slice v0              [NOT STARTED]
       ↓
M2 — Campaign Prep Pipeline v0           [PERSISTENCE v1.1]
       ↓
M3 — Immersion Layer v1                  [NOT STARTED]
       ↓
┌────────────────────────────────────────────────────────────┐
│  M3.5 — RAW Compliance Gate            [PROPOSED]          │
│  Systematic PHB/DMG verification of all FULL mechanics     │
│  Prove-or-fix every RAW claim before distribution          │
└────────────────────────────────────────────────────────────┘
       ↓
M4 — Offline Packaging + Shareability    [NOT STARTED]
```

**Why between M3 and M4:**
- M1 adds the intent/resolution loop — new mechanics may be added
- M2 adds campaign persistence — no new mechanics
- M3 adds immersion layers — no new mechanics, but grid renderer exercises spatial logic
- **M3.5 validates everything before it gets packaged and shipped** (M4)
- Fixing RAW errors after M4 (distribution) means breaking shipped campaigns

**Why not earlier:**
- Engine mechanics may still evolve during M1 (spellcasting scoping, intent resolution edge cases)
- M3 contextual grid may surface spatial reasoning bugs (cover lines, adjacency, etc.)
- Running the audit before all mechanics are stable wastes effort on things that change

---

## Scope

### IN SCOPE: Validate all FULL-status mechanics

Every mechanic currently marked **FULL** in the RAW Fidelity Audit must pass verification:

| Mechanic | RAW Reference | Owner CP | Verification Method |
|----------|--------------|----------|---------------------|
| Normal movement | PHB 144–147 | Core | Unit tests with PHB examples |
| Difficult terrain | PHB 148–150 | CP-19 | Terrain cost assertions |
| Running | PHB 144 | Core | Movement rules + terrain interaction |
| Charging | PHB 154 | Core | Line/path/AC bonus validation |
| 5-foot step | PHB 144 | Core | Terrain restriction verification |
| Forced movement | PHB 154 | CP-18/19 | Hazard trigger assertions |
| Cover (standard/improved/total) | PHB 150–152 | CP-19 | Geometry + AC/Reflex bonus |
| Higher ground | PHB 151 | CP-19 | +1 melee attack verification |
| Falling damage | DMG 304 | CP-19 | 1d6/10ft + max cap |
| Pits & ledges | DMG 71–72 | CP-19 | Hazard trigger + save DCs |
| Prone | PHB 311 | CP-16 | Attack modifier verification |
| Stunned | PHB 315 | CP-16 | Action denial + AC penalty |
| Trip | PHB 158 | CP-18 | Opposed check + AoO rules |
| Bull Rush | PHB 154 | CP-18 | Opposed check + movement |
| Overrun | PHB 157 | CP-18 | Opposed check + prone |
| Weapon damage | PHB 134 | Core | Damage formula verification |

### IN SCOPE: Document all DEGRADED deviations

Every mechanic marked **DEGRADED** must have:
1. Explicit citation of the RAW rule being deviated from
2. Technical justification for the deviation
3. A filed issue or future CP target for full compliance
4. Test proving the degraded behavior is at least internally consistent

| Mechanic | RAW Reference | Current State | Required Documentation |
|----------|--------------|---------------|----------------------|
| Steep slopes | DMG 89–90 | Placeholder DC | Document actual RAW DC, file fix target |
| Flanking | PHB 157 | Simplified | Document exact simplification vs RAW |
| Mounted combat | PHB 157 | CP-18A partial | Document what's missing vs RAW |
| Grapple | PHB 155–157 | Lite only | Document which grapple rules are omitted |
| Soft cover | PHB 150–152 | Simplified geometry | Document geometry simplification |
| Shallow water | DMG 89 | Difficult terrain only | Document missing swim/depth rules |

### IN SCOPE: Verify no 5e contamination

Confirm absence of:
- Advantage/disadvantage mechanic
- Concentration mechanic
- Short/long rest terminology
- "Heavily obscured" (5e term)
- Bounded accuracy assumptions
- Any 5e-specific terminology in code, comments, or test names

### OUT OF SCOPE

- **DEFERRED mechanics** — Not implemented, nothing to verify
- **FORBIDDEN mechanics** — Blocked by closed gates, not testable
- **Kernel development** — SKR-001 through SKR-012 are future work
- **Spellcasting** — Blocked pending kernel infrastructure
- **LLM behavior** — M3.5 validates the engine, not the narration
- **Immersion layer correctness** — Images/audio are non-mechanical

---

## Entry Criteria (ALL required before M3.5 begins)

1. **M3 complete and frozen** — All immersion acceptance criteria met
2. **Test suite green** — 0 failures, all tests passing
3. **RAW Fidelity Audit current** — Updated after last CP closure
4. **Rules Coverage Ledger current** — Updated after last CP closure
5. **No open engine PRs** — All in-flight engine changes merged or abandoned

---

## Exit Criteria (ALL required to pass M3.5)

### Tier 1: Correctness Proof (MANDATORY)

1. **Every FULL mechanic has ≥1 test citing PHB/DMG page number**
   - Test name or docstring includes citation (e.g., `# PHB p.154: Charging`)
   - Test validates specific RAW rule, not just "code doesn't crash"

2. **Every FULL mechanic verified against 3+ RAW edge cases**
   - Edge cases derived from actual PHB/DMG rules text
   - e.g., "Charging through difficult terrain is not allowed" (PHB p.154)
   - e.g., "A prone defender grants +4 to melee attacks against them" (PHB p.311)

3. **Zero silent RAW deviations**
   - Every deviation from RAW is either:
     - Fixed (mechanic updated to match RAW), or
     - Formally DEGRADED with documented justification

### Tier 2: Deviation Registry (MANDATORY)

4. **DEGRADED Deviation Register complete**
   - Every DEGRADED mechanic has a formal entry with:
     - RAW citation (PHB/DMG page + rule text)
     - Current behavior description
     - Justification for deviation
     - Target CP or kernel for future compliance
     - Test proving internal consistency

5. **No undocumented deviations**
   - If a mechanic is found to deviate from RAW during audit, it must be either fixed or formally DEGRADED before exit

### Tier 3: Contamination Check (MANDATORY)

6. **5e contamination scan passes**
   - Automated grep for 5e-specific terms across codebase
   - Manual review of any hits
   - Zero confirmed contamination

### Tier 4: Regression Lock (MANDATORY)

7. **RAW compliance test suite tagged**
   - All RAW-specific tests marked with `@pytest.mark.raw_compliance`
   - CI/pre-commit hook prevents RAW compliance tests from being deleted or weakened
   - Test count baseline recorded (cannot decrease)

---

## Deliverables

| Artifact | Description |
|----------|-------------|
| `RAW_COMPLIANCE_REPORT.md` | Final compliance report: every FULL mechanic verified, every DEGRADED mechanic documented |
| `RAW_DEVIATION_REGISTER.md` | Complete registry of intentional RAW deviations with justifications |
| `5E_CONTAMINATION_SCAN.md` | Results of 5e terminology scan |
| Updated `RAW_FIDELITY_AUDIT.md` | Refreshed with M3.5 audit findings |
| Updated `RULES_COVERAGE_LEDGER.md` | Refreshed with M3.5 coverage status |
| `@pytest.mark.raw_compliance` tagged tests | All RAW-specific tests tagged for regression protection |

---

## Execution Strategy

### Phase 1: Automated Scan

1. Generate list of all mechanics marked FULL in `RAW_FIDELITY_AUDIT.md`
2. Cross-reference against existing test suite — identify tests that cover each mechanic
3. Identify gaps: mechanics claimed FULL with insufficient test coverage
4. Run 5e contamination scan (grep for specific terms)

### Phase 2: PHB/DMG Verification

For each FULL mechanic:
1. Read the actual RAW rule text (PHB/DMG page citation)
2. Compare against current implementation
3. Write/update tests with explicit PHB/DMG citations in docstrings
4. Identify edge cases from the rules text
5. Verify edge case handling matches RAW

### Phase 3: Deviation Documentation

For each DEGRADED mechanic:
1. Document the exact RAW rule being deviated from
2. Document current behavior
3. Document justification
4. File target CP for future compliance
5. Write internal consistency test

### Phase 4: Compliance Report

1. Compile results into `RAW_COMPLIANCE_REPORT.md`
2. Tag all RAW tests with `@pytest.mark.raw_compliance`
3. Update `RAW_FIDELITY_AUDIT.md` and `RULES_COVERAGE_LEDGER.md`
4. Declare M3.5 exit

---

## Work Order Estimate

Based on current FULL mechanic count (16 mechanics) and DEGRADED mechanic count (6 mechanics):

| Phase | Scope | Agent Capacity |
|-------|-------|----------------|
| Phase 1: Automated Scan | Cross-reference tests ↔ mechanics | 1 agent, single WO |
| Phase 2: PHB/DMG Verification | 16 FULL mechanics × 3+ edge cases each | 2–3 agents, parallel WOs by mechanic group |
| Phase 3: Deviation Documentation | 6 DEGRADED mechanics | 1 agent, single WO |
| Phase 4: Compliance Report | Compilation + tagging | 1 agent, single WO |

**Total estimated WOs:** 4–6

**Agent assignment strategy:**
- Group mechanics by CP ownership for coherent work orders
- Movement mechanics (Core): 1 WO
- Terrain mechanics (CP-19): 1 WO
- Combat maneuvers (CP-18): 1 WO
- Conditions (CP-16): 1 WO
- Deviation documentation: 1 WO
- Final compilation + tagging: 1 WO

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| RAW errors found in FULL mechanics | MEDIUM | HIGH — requires engine fixes before M4 | Fix immediately during M3.5, regression tests prevent reintroduction |
| 5e contamination found | LOW | MEDIUM — terminology cleanup | Grep scan + manual review |
| Scope creep into DEFERRED mechanics | MEDIUM | LOW — delays M3.5 exit | Strict scope boundary: FULL + DEGRADED only |
| Edge cases reveal kernel needs | LOW | HIGH — could block M3.5 exit | Document as DEGRADED + file future kernel dependency, don't block gate |

---

## Governance

- M3.5 exit requires **PM sign-off** (Aegis or designated acting PM)
- RAW compliance tests become **protected artifacts** — cannot be removed without formal amendment
- Any RAW error discovered post-M3.5 triggers a **compliance incident** requiring:
  1. Immediate fix
  2. Updated compliance report
  3. Root cause analysis (why was it missed?)
  4. Regression test added

---

## Amendment to Execution Roadmap

If approved, this proposal amends `AIDM_EXECUTION_ROADMAP_V3.md` from v3.2.0 to **v3.3.0** with:

1. New milestone `M3.5 — RAW Compliance Gate` inserted between M3 and M4
2. M4 entry criteria updated to require M3.5 exit
3. Revision history updated

---

## Approval

- [ ] PM Review (Aegis / Acting PM)
- [ ] User Approval (Thunder)
- [ ] Roadmap v3.3.0 amendment committed

---

## END OF M3.5 PROPOSAL
