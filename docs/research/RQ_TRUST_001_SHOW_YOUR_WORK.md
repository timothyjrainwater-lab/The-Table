# RQ-TRUST-001: "Show Your Work" Without Becoming a Debug UI

**Research Track:** 6 of 7
**Domain:** Trust & Transparency
**Status:** FINDINGS RECEIVED
**Filed:** 2026-02-11
**Source:** Thunder (Product Owner) — Deep Research prompt

---

## Problem Statement

Your core failure mode is trust collapse: one wrong AoO, one off-by-one square, one bad cover result, and the player suspects the system is cheating or sloppy. You need auditability and explainability that:

- Proves Box is authoritative and correct
- Exposes the minimum necessary reasoning to the player
- Does not add panels, toolbars, or "debug overlays" that break the table metaphor
- Keeps Spark from contaminating mechanical truth

**This is not generic "explainable AI." It's rules engine explainability in an immersive UI.**

---

## Research Objective

Design a trust system that lets players verify outcomes (rolls, distances, LOS/LOE, cover, AoOs, damage vs hardness) with high confidence, using table-native affordances (parchment slips, DM verbal confirmation, minimal overlays) rather than traditional UI.

Must propose concrete mechanisms, data flows, and UX patterns that preserve the "table" experience while making the system provably honest.

---

## Research Sub-Questions

### (1) Define "Trust-Critical Events"

Research and enumerate the event types that most commonly trigger distrust:
- Distance + movement legality
- AoO triggers and threatened squares
- Cover and concealment (including relative height cases)
- LOS vs LOE
- Area-of-effect inclusion/exclusion
- Damage application vs hardness/DR/resistance
- Randomness integrity (dice)

Deliverable: prioritized list + why each matters.

### (2) Minimal Explain Payloads from Box

Research how Box should generate an "explain packet" that is:
- Deterministic
- Concise
- Structured (not prose)
- Replayable

Examples:
- "Fireball: center at (x,y); radius=20ft; included squares=[...]; goblin3 excluded because pillar blocks LOE"
- "Cover: 50% (soft cover) because line passes through table volume above halfling's prone height threshold"

Deliverable: explain schema + examples per event type.

### (3) Table-Native UX for Transparency

Research UI patterns that preserve metaphor:
- DM verbally summarizing key facts
- "Plastic stencil" overlay for AoE (temporary, lean-up only)
- Parchment receipt slips ("Combat Receipt") that can be filed into Tome
- Dice tray as the persistent truth source for randomness
- Optional "ask why" interaction: player taps a result → DM offers the receipt

Deliverable: 3-5 concrete UX patterns + when to use each.

### (4) Audit Trails + Receipts (Non-negotiable for trust)

Research how to store and expose:
- Roll provenance (seed, dice, modifiers, timestamps)
- Rule references (SRD/PHB page refs where applicable)
- The exact geometry inputs used (positions, elevations, object dimensions)

This is for disputes and self-verification.

Deliverable: audit log design + "receipt" generation spec.

### (5) Anti-Hallucination Boundary for Explanations

Research how to ensure Spark never invents mechanical explanations:
- Only Box produces explain packets
- Spark may paraphrase but must not alter facts
- Lens serves explain packets to Spark as read-only material

Deliverable: boundary rules + enforcement patterns.

### (6) Player-Controlled Transparency Levels (Without UI Bloat)

Research a small set of modes (e.g., "default," "high transparency," "tournament mode") that change:
- How often receipts are offered
- Whether AoE overlays are shown automatically
- Whether mechanical citations are included

But must be invoked via table objects (gemstone settings) and stored in Lens.

Deliverable: 2-3 modes + behavior definitions.

### (7) Validation & Regression Strategy to Protect Trust

Research test and verification strategies that materially reduce trust-breaking bugs:
- Property-based tests for geometry edge cases
- Golden test fixtures for combat scenarios
- Fuzzing for AoE/LOS/cover calculations
- Replay verification (10x runs) as a CI gate

Deliverable: test plan specifically tied to trust-critical events.

### (8) Output: Trust Framework Spec

Synthesize into an implementable spec:
- Trust-critical events list
- Explain packet schema
- Receipt/audit log format
- UI delivery patterns (table-native)
- Transparency modes
- Validation gates

---

## Research Findings

### Preamble

The core failure mode is trust collapse. One wrong AoO, one off-by-one square, one bad cover result, and the player suspects the system is cheating or sloppy. The following framework establishes "Provenance & Proof" — a system that makes the engine provably honest using table-native affordances rather than debug UI.

---

### Finding 1: Trust-Critical Events (The "Distrust" Hierarchy)

Failures in these categories break the "magic circle" of the game. Prioritized by impact on player agency:

| Event Category | Why it Triggers Distrust |
|---|---|
| **1. Movement & AoO** | Players feel "cheated" if they unknowingly trigger a reaction or miss a square. |
| **2. Cover & LOS** | The most subjective area; players often disagree with a computer's "vision." |
| **3. AoE Boundary** | "That goblin was definitely in the blast!" (The pixel-perfect vs. grid-snap conflict). |
| **4. Damage Mitigation** | Hidden math (DR/Hardness) can make enemies feel "immortal" or bugged. |
| **5. Die Integrity** | The suspicion of "weighted" digital dice is a fundamental barrier to entry. |

---

### Finding 2: Box "Explain Packets" — Structured Truth Packets (STP)

Box does not output prose. It outputs a **Structured Truth Packet (STP)**. This allows the system to remain deterministic and replayable.

**Example: AoE Fireball Packet**

```json
{
  "event_id": "EV-9921",
  "origin": {"x": 12, "y": 8, "z": 0},
  "geometry": {"type": "sphere", "radius": 20},
  "eval_grid": ["sq_11_7", "sq_12_7", "..."],
  "exclusions": [
    {"target": "orc_2", "reason": "LOE_BLOCK", "blocker_id": "pillar_A4"}
  ],
  "rules_ref": "SRD_v5.1_p190"
}
```

---

### Finding 3: Table-Native UX for Transparency

Avoids "pop-up windows." Uses physicalized metaphors instead:

- **The Combat Receipt (The Slip):** When a complex calculation occurs (e.g., a multi-target save), a small **parchment slip** animates into the corner of the table or is "filed" into the **Tome**. It shows the raw math.
- **The Ghost Stencil:** For AoEs, instead of a permanent red glow, a "plastic" translucent stencil briefly drops onto the table, showing the exact hexes/squares affected, then fades.
- **The "Judge's Lens":** A physical loupe or magnifying glass object on the table. Hovering it over a character reveals their current status (Cover: 1/2, Resist: Fire) in handwritten script on the table surface.

---

### Finding 4: Audit Trails & Provenance

To ensure the system isn't "fudging," every roll is tied to a **Universal Seed**.

- **The Dice Tray:** All digital rolls land in a visible tray. Tapping a die shows its **Entropy Source ID** and the timestamp.
- **The Ledger:** A hidden, append-only log stores every STP. If a player disputes a move, the DM can "rewind" the visual state to the exact geometry used for that specific calculation.

---

### Finding 5: The Spark-Box Boundary (Anti-Hallucination — One-Way Knowledge Valve)

To prevent Spark from lying about rules, the system implements a **One-Way Knowledge Valve**:

1. **Box** calculates the truth and generates the STP.
2. **Lens** translates the STP into a "Narrative Brief" for Spark.
3. **Spark** is strictly forbidden from accessing the raw Rules Engine. It can only narrate what is in the Brief.

**Correction Pattern:** If Spark says "The Orc dodged," but the STP says "The Orc has Fire Resistance," Lens triggers a "System Correction" that re-writes Spark's prompt before the player sees it.

---

### Finding 6: Transparency Modes (The Gemstone Settings)

The table features a small **Tri-Gem Socket** that toggles the "vibe" of the rules enforcement:

- **Immersion Mode (Ruby):** No receipts unless requested. Spark narrates everything. Minimal overlays.
- **Standard Mode (Sapphire):** Default. Receipts for crits and kills. Stencils appear during spell casting.
- **Tournament Mode (Diamond):** "Show Your Work." Every roll displays its modifiers. AoO threatened zones are permanently visible as faint chalk lines.

---

### Finding 7: Validation & Regression Strategy

To protect trust, uses **Property-Based Testing (PBT)** for the geometry engine:

- **The "Thousand-Fold Fireball":** A CI test that drops 1,000 fireballs at random coordinates against 1,000 random obstacle configurations. It compares Box's output against a "Golden Reference" (a simplified, slow, but mathematically perfect version of the rules).
- **Replay Fuzzing:** Takes historical player sessions and re-runs the logic. If a 1.1 update produces a different "Cover" result for the same coordinates than version 1.0 did, the build is rejected.

---

### Finding 8: Trust Framework Summary

- **Authoritative Source:** Box (Rules Engine).
- **Visual Witness:** Lens (The physical UI).
- **Narrator:** Spark (The flavor text).
- **Verification:** The "Combat Receipt" is the ultimate source of truth for the player.

---

## Cross-References

- `docs/doctrine/SPARK_LENS_BOX_DOCTRINE.md` — Trust repair axiom, provenance labeling standard
- `docs/design/TABLE_SURFACE_UI_SPECIFICATION.md` — Table objects, parchment receipts
- `docs/design/BATTLE_MAP_AND_ENVIRONMENTAL_PHYSICS.md` — Cover, LOS/LOE, AoE calculations
