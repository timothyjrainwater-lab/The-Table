# Documentation Authority Index
## Single Source of Truth Map for AIDM

**Project:** AIDM — Deterministic D&D 3.5e Engine
**Document Type:** Governance / Documentation Control
**Status:** ACTIVE
**Audience:** Project Authority, Implementers, Auditors

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

1. **Acceptance Records override all other docs**
2. **Implementation Packets override Design Decisions**
3. **Design Decisions override Progress / Feedback**
4. **Governance docs override local comments**
5. **Rules Coverage Ledger overrides assumptions**

If uncertainty remains → escalate.

---

## 3. CORE RULES & MECHANICS

| Topic | Authoritative Document |
|-----|------------------------|
| Combat maneuvers | `docs/cp18/CP18_COMBAT_MANEUVERS_DECISIONS.md` |
| Environment & terrain | `docs/cp19/CP19_ENVIRONMENT_TERRAIN_DECISIONS.md` |
| Environmental damage | `docs/cp20/CP20_ENVIRONMENTAL_DAMAGE_DECISIONS.md` |
| Conditions (simple) | `docs/cp16/CP16_CONDITIONS_DECISIONS.md` |
| Forced movement | `docs/cp18/` + `docs/cp19/` |
| Falling damage | `docs/cp19/CP19_ENVIRONMENT_TERRAIN_DECISIONS.md` |

---

## 4. IMPLEMENTATION AUTHORITY

| Topic | Document |
|-----|----------|
| CP-19 implementation | `docs/cp19/CP19_IMPLEMENTATION_PACKET_FINAL.md` |
| CP-19 acceptance | `docs/cp19/CP19_ACCEPTANCE_RECORD_FINAL.md` |
| CP-20 implementation | `docs/cp20/CP20_IMPLEMENTATION_PACKET.md` |
| File touch boundaries | Relevant CP implementation packet |

---

## 5. GOVERNANCE & SAFETY

| Topic | Document |
|-----|----------|
| Capability gates | `CAPABILITY_GATE_ESCALATION_PLAYBOOKS.md` |
| Gate pressure | `docs/GATE_PRESSURE_MAP.md` |
| Determinism audit | `docs/DETERMINISM_AUDIT_PLAYBOOK.md` |
| Determinism threats | `docs/DETERMINISM_THREAT_PATTERNS.md` |
| RAW alignment | `docs/RAW_FIDELITY_AUDIT.md` |
| Coverage status | `docs/RULES_COVERAGE_LEDGER.md` |

---

## 6. KERNEL DESIGN AUTHORITY

| Kernel | Document |
|------|----------|
| Relational Conditions | `docs/skr/SKR-005_RELATIONAL_CONDITIONS_DESIGN.md` |
| SKR-005 risk analysis | `docs/skr/SKR-005_FAILURE_MODE_ANALYSIS.md` |
| Kernel dependencies | `docs/skr/SKR_DEPENDENCY_GRAPH.md` |

No kernel may be implemented without explicit authorization.

---

## 7. PLANNING & ROADMAP

| Topic | Document |
|-----|----------|
| CP-21 feasibility | `docs/cp21/CP21_FEASIBILITY_ANALYSIS.md` |
| Test scope (CP-20) | `docs/cp20/CP20_TEST_CASE_CATALOG.md` |

---

## 8. CONFLICT RESOLUTION EXAMPLE

**Question:**
"Soft cover geometry seems different in code vs comments."

**Resolution Order:**
1. CP-19 Acceptance Record
2. CP-19 Implementation Packet
3. CP-19 Design Decisions
4. Feedback / Progress reports

If still unclear → escalate.

---

## 9. MAINTENANCE RULE

- Update this index whenever:
  - A CP is finalized
  - A kernel is approved
  - A governance document is added
- Do not remove historical entries
- Broken links are treated as defects

---

## 10. CONCLUSION

This index is the **map of the project's truth**.

If you are unsure which document governs a decision,
**start here**.

---

## END OF DOCUMENTATION AUTHORITY INDEX
