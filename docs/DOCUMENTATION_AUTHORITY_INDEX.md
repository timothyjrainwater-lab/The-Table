# Documentation Authority Index
## Single Source of Truth Map for AIDM

**Project:** AIDM — Deterministic D&D 3.5e Engine
**Document Type:** Governance / Documentation Control
**Status:** ACTIVE
**Audience:** Project Authority, Implementers, Auditors
**Last Updated:** 2026-02-09

---

## 1. PURPOSE

This index defines the **authoritative document** for every major rules,
architecture, and governance topic in the AIDM project.

Its goals are to:
- Eliminate conflicting guidance
- Prevent re-litigation of settled decisions
- Speed onboarding and audits
- Provide a deterministic "where do I look?" answer

If two documents conflict, **this index determines which one wins**.

---

## 2. AUTHORITY RULES (BINDING)

1. **Design Doctrine overrides all other docs** (for their respective domains)
2. **Acceptance Records override Implementation Packets**
3. **Implementation Packets override Design Decisions**
4. **Design Decisions override Progress / Feedback**
5. **Governance docs override local comments**
6. **Rules Coverage Ledger overrides assumptions**

If uncertainty remains → escalate.

---

## 3. DESIGN DOCTRINE (FROZEN)

The design layer is **FROZEN** as of 2026-02-09.

See `docs/design/DESIGN_LAYER_ADOPTION_RECORD.md` for the formal freeze declaration.

| Topic | Authoritative Document |
|-------|------------------------|
| Design freeze declaration | `docs/design/DESIGN_LAYER_ADOPTION_RECORD.md` |
| Campaign initialization | `docs/design/SESSION_ZERO_RULESET_AND_BOUNDARY_CONFIG.md` |
| Character sheet UI contract | `docs/design/CHARACTER_SHEET_UI_CONTRACT.md` |
| Voice input & clarification | `docs/design/VOICE_INTENT_AND_CLARIFICATION_PROTOCOL.md` |
| LLM–Engine authority | `docs/design/LLM_ENGINE_BOUNDARY_CONTRACT.md` |
| Local runtime & packaging | `docs/design/LOCAL_RUNTIME_PACKAGING_STRATEGY.md` |
| Solo-first experience | `docs/design/SOLO_FIRST_PREPARATORY_DM_MODEL.md` |

Changes to these documents require formal decision records (DR-XXX).

---

## 4. PROJECT PLANNING & ROADMAP

| Topic | Authoritative Document |
|-------|------------------------|
| Execution roadmap (M0-M4) | `docs/AIDM_EXECUTION_ROADMAP_V3.md` |
| Execution packet (PM) | `docs/NEXT_STEPS_EXECUTION_PACKET_PM.md` |
| Post-CP20 decision analysis | `docs/POST_CP20_DECISION_ANALYSIS.md` |
| Tier-1 exhaustion analysis | `docs/TIER1_EXHAUSTION_ANALYSIS.md` |
| CP-21 disqualification | `docs/CP21_DISQUALIFICATION_CRITERIA.md` |

**Superseded:** `AIDM_PROJECT_ACTION_PLAN_V2.md` → use `AIDM_EXECUTION_ROADMAP_V3.md`

---

## 5. CORE RULES & MECHANICS

| Topic | Authoritative Document |
|-------|------------------------|
| Combat maneuvers | `docs/CP18_COMBAT_MANEUVERS_DECISIONS.md` |
| Environment & terrain | `docs/cp19/CP19_ENVIRONMENT_TERRAIN_DECISIONS.md` |
| Environmental damage | `docs/cp20/CP20_ENVIRONMENTAL_DAMAGE_DECISIONS.md` |
| Conditions (simple) | `docs/CP16_CONDITIONS_DECISIONS.md` |
| Forced movement | `docs/cp18/` + `docs/cp19/` |
| Falling damage | `docs/cp19/CP19_ENVIRONMENT_TERRAIN_DECISIONS.md` |

---

## 6. IMPLEMENTATION AUTHORITY

| Topic | Document |
|-------|----------|
| CP-19 implementation | `docs/cp19/CP19_IMPLEMENTATION_PACKET_FINAL.md` |
| CP-19 acceptance | `docs/cp19/CP19_ACCEPTANCE_RECORD_FINAL.md` |
| CP-20 implementation | `docs/cp20/CP20_IMPLEMENTATION_PACKET.md` |
| File touch boundaries | Relevant CP implementation packet |

---

## 7. GOVERNANCE & SAFETY

| Topic | Document |
|-------|----------|
| Capability gates | `docs/CAPABILITY_GATE_ESCALATION_PLAYBOOKS.md` |
| Gate pressure | `docs/GATE_PRESSURE_MAP.md` |
| Determinism audit | `docs/DETERMINISM_AUDIT_PLAYBOOK.md` |
| Determinism threats | `docs/DETERMINISM_THREAT_PATTERNS.md` |
| RAW alignment | `docs/RAW_FIDELITY_AUDIT.md` |
| Coverage status | `docs/RULES_COVERAGE_LEDGER.md` |
| CP freeze process | `docs/CP_FREEZE_AND_CLOSURE_PLAYBOOK.md` |
| CP completion template | `docs/CP_COMPLETION_REVIEW_TEMPLATE.md` |
| Edge case traceability | `docs/EDGE_CASE_TRACEABILITY_INDEX.md` |

---

## 8. KERNEL DESIGN AUTHORITY

| Kernel | Document |
|--------|----------|
| Relational Conditions (SKR-005) | `docs/skr/SKR-005_RELATIONAL_CONDITIONS_DESIGN.md` |
| SKR-005 risk analysis | `docs/skr/SKR-005_FAILURE_MODE_ANALYSIS.md` |
| SKR-005 gate opening | `docs/skr/SKR-005_GATE_OPENING_DECISION_MEMO.md` |
| SKR-005 impact map | `docs/skr/SKR-005_IMPACT_MAP.md` |
| SKR-005 audit readiness | `docs/skr/SKR-005_AUDIT_READINESS_CHECKLIST.md` |
| Kernel dependencies | `docs/skr/SKR_DEPENDENCY_GRAPH.md` |

No kernel may be implemented without explicit authorization.

---

## 9. CONFLICT RESOLUTION EXAMPLE

**Question:**
"Soft cover geometry seems different in code vs comments."

**Resolution Order:**
1. CP-19 Acceptance Record
2. CP-19 Implementation Packet
3. CP-19 Design Decisions
4. Feedback / Progress reports

If still unclear → escalate.

---

## 10. MAINTENANCE RULE

- Update this index whenever:
  - A CP is finalized
  - A kernel is approved
  - A governance document is added
  - A design document is adopted
- Do not remove historical entries
- Broken links are treated as defects

---

## 11. CONCLUSION

This index is the **map of the project's truth**.

If you are unsure which document governs a decision,
**start here**.

---

## END OF DOCUMENTATION AUTHORITY INDEX
