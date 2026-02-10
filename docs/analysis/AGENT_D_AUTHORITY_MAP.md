# AIDM Authority Map — Agent D Audit
## Document Authority Resolution Matrix

**Agent:** Agent D (Archivist/Librarian)
**Audit Mode:** READ-ONLY GLOBAL AUDIT
**Date:** 2026-02-10
**Purpose:** Establish conflict resolution hierarchy for AIDM documentation corpus

---

## Authority Resolution Rules

When multiple documents address the same topic, authority is determined by this hierarchy:

1. **Design Doctrine** (FROZEN) > All other docs for their respective domains
2. **Acceptance Records** > Implementation Packets
3. **Implementation Packets** > Design Decisions
4. **Design Decisions** > Progress / Feedback
5. **Governance docs** > Local comments
6. **Rules Coverage Ledger** > Assumptions

**Source:** docs/DOCUMENTATION_AUTHORITY_INDEX.md

---

## Authority Levels Defined

| Level | Definition | Modification Requires |
|-------|------------|----------------------|
| **BINDING** | Immutable constraint, enforceable | Formal CP amendment with full audit |
| **CANONICAL** | Official source of truth | Formal decision record (DR-XXX) |
| **ADVISORY** | Recommended guidance | Team consensus, documented |
| **HISTORICAL** | Informational only | N/A (not prescriptive) |

---

## A. BINDING DOCUMENTS (Highest Authority)

### A1. CP-001 Frozen Baseline
**Authority:** BINDING (Immutable)
**Modification:** Requires new CP with full regression testing

| Document | Domain | Cannot Be Overridden By |
|----------|--------|------------------------|
| aidm/schemas/position.py | Position type implementation | Any other document |
| CP001_POSITION_UNIFICATION_DECISIONS.md | Position design decisions | Any other document |
| Test baseline (1393 tests passing) | System correctness proof | Any other document |

**Conflicts:** NONE ALLOWED. CP-001 baseline is immutable fact.

---

### A2. Design Layer (Frozen 2026-02-09)
**Authority:** BINDING
**Modification:** Requires formal decision record (DR-XXX) + version bump

| Doc ID | File | Domain | Overrides |
|--------|------|--------|-----------|
| SZ-RBC-001 | SESSION_ZERO_RULESET_AND_BOUNDARY_CONFIG.md | Campaign initialization | All campaign setup discussions |
| CS-UI-001 | CHARACTER_SHEET_UI_CONTRACT.md | Character sheet UI | All UI implementation specs |
| VICP-001 | VOICE_INTENT_AND_CLARIFICATION_PROTOCOL.md | Voice I/O | All voice implementation specs |
| LEB-001 | LLM_ENGINE_BOUNDARY_CONTRACT.md | LLM authority | All LLM integration specs |
| LRP-001 | LOCAL_RUNTIME_PACKAGING_STRATEGY.md | Offline execution | All packaging/runtime specs |
| SF-PDM-001 | SOLO_FIRST_PREPARATORY_DM_MODEL.md | Solo play experience | All solo/prep discussions |

---

### A3. Execution Roadmap v3.1
**Authority:** BINDING (Supersedes Action Plan v2.0)
**File:** docs/AIDM_EXECUTION_ROADMAP_V3.md
**Domain:** Project milestones, sequencing, constraints

---

## B. INBOX AUTHORITY STATUS

### Issue: Unauthorized Authority Claims

**Documents Making "Locked"/"Binding" Claims:**
- Generative Presentation Architecture: Claims "binding input for Action Plan"
- Player Artifacts Specification: Claims "locks player-owned artifacts as core systems"
- Player Modeling Specification: Claims "elevates player modeling to a core system"
- Transparent Mechanics Ledger: Claims "locks mechanics output window as core trust system"
- Minimal UI Addendum: Claims "locks minimal UI presence"

**Current Official Status:** ADVISORY (pending formal adoption)

**Resolution:** These documents have NOT been formally adopted into the canonical documentation. They are research/design artifacts awaiting integration.

---

## C. CONFLICT RESOLUTION EXAMPLES

### Example 1: Position Distance (feet vs squares)
**Question:** Should distance return squares or feet?

**Resolution:**
1. Check CP-001: "Returns feet" (BINDING)
2. Check implementation: distance_to() returns feet
3. **Answer:** Feet (CP-001 is immutable)

### Example 2: Player Modeling Required?
**Question:** Is player modeling required for M1?

**Resolution:**
1. Check Roadmap M1: NO mention of player modeling (BINDING)
2. Check Inbox: Player Modeling Spec claims "core system" (ADVISORY)
3. **Answer:** NOT currently required (Roadmap wins)
4. **Action:** Flag for integration review

### Example 3: Image Critique Gate
**Question:** Must image generation include critique?

**Resolution:**
1. Check Design Layer: No mention (BINDING)
2. Check Roadmap M3: No critique requirement (BINDING)
3. Check Inbox: Chronological Record claims "required" (ADVISORY)
4. **Answer:** NOT currently required (Design Layer/Roadmap win)
5. **Action:** IF needed, requires Design Layer amendment

---

## D. AUTHORITY HIERARCHY SUMMARY

| Document Category | Authority | Overrides |
|-------------------|-----------|-----------|
| CP-001 Baseline | BINDING | Everything |
| Design Layer (6 docs) | BINDING | Everything except CP-001 |
| Execution Roadmap v3.1 | BINDING | Action Plans, informal plans |
| Governance Docs | CANONICAL | Informal claims |
| Project State Docs | CANONICAL | Stale status |
| Inbox Design Corpus | ADVISORY | Nothing (pending adoption) |

---

## E. ESCALATION CRITERIA

**Escalate to Orchestrator when:**
- Two BINDING docs conflict
- Inbox doc blocks implementation
- CP-001 compliance unclear
- Implementation needs feature NOT in Roadmap

**Do NOT escalate when:**
- Inbox (ADVISORY) conflicts with Roadmap (BINDING) → Roadmap wins
- Historical doc conflicts with current spec → Current spec wins

---

**END OF AUTHORITY MAP**