# CP-21 — Feasibility Analysis
## Post-CP-20 Tier-1 Advancement Options

**Project:** AIDM — Deterministic D&D 3.5e Engine
**CP ID:** CP-21
**Document Type:** Feasibility & Roadmap Analysis
**Status:** ANALYSIS COMPLETE
**Audience:** Project Authority, Architects

---

## 1. PURPOSE

This document evaluates **viable next Capability Packets (CPs)** after CP-20,
restricted to **Tier-1 (G-T1)** mechanics only.

Its goal is to:
- Prevent roadmap stall after CP-20
- Avoid premature gate pressure
- Identify diminishing returns within Tier-1
- Clarify when kernel work becomes unavoidable

This document does **not** authorize implementation.

---

## 2. CONSTRAINTS

All CP-21 candidates must:

- Remain strictly within **G-T1**
- Introduce no relational state
- Introduce no persistence or history
- Preserve global determinism invariants
- Avoid overlap with SKR-005 responsibilities

---

## 3. CANDIDATE CP-21 OPTIONS

### 3.1 Ready / Delay Action Refinement

**Description**
- Clarify ready triggers
- Standardize delay/initiative interactions
- Remove ambiguous timing edge cases

**Pros**
- Improves tactical clarity
- Low implementation risk
- No new data models

**Cons**
- Limited player-visible impact
- Mostly rules polish

**Gate Status:** G-T1 safe

---

### 3.2 Threatened Area & Reach Clarification (Non-Relational)

**Description**
- Explicit threatened-square determination
- Reach weapon edge cases
- AoO trigger clarity

**Pros**
- Improves AoO correctness
- Synergizes with CP-15/CP-18

**Cons**
- Easy to accidentally drift into relational territory
- Requires careful audit

**Gate Status:** G-T1 (with discipline)

---

### 3.3 Initiative Tie-Breaking & Ordering Formalization

**Description**
- Deterministic tie-breaking rules
- Explicit initiative ordering guarantees

**Pros**
- Improves replay clarity
- Very low risk

**Cons**
- Narrow scope
- Mostly invisible to players

**Gate Status:** G-T1 safe

---

### 3.4 Facing / Orientation (Degraded)

**Description**
- Introduce simplified facing rules without relational dependencies

**Pros**
- Adds tactical depth
- Can be degraded heavily

**Cons**
- High complexity risk
- Easily pressures G-T3C

**Gate Status:** Risky (likely defer)

---

## 4. OPTIONS EXPLICITLY REJECTED

| Option | Reason |
|------|--------|
| Full flanking | Requires G-T3C |
| Opportunity zones | Relational participants |
| Persistent overwatch | Time/state persistence |
| Spell-like abilities | Spell kernel dependency |

---

## 5. STRATEGIC RECOMMENDATION

### Best CP-21 Candidates (If Tier-1 Continues)
1. **Ready / Delay Action Refinement**
2. **Initiative Ordering Formalization**

These provide:
- Clean closure to core combat loop
- Minimal rework risk
- Strong determinism guarantees

### Strategic Inflection Point
After CP-20 and one small CP-21:
- Tier-1 returns diminish sharply
- Kernel work (SKR-005) becomes the dominant value path

---

## 6. CONCLUSION

CP-21 exists mainly as a **decision checkpoint**, not a guaranteed next step.

The project is approaching the **end of safe Tier-1 expansion**, and further
progress will require deliberate gate openings and kernel investment.

---

## END OF CP-21 FEASIBILITY ANALYSIS
