# Determinism Threat Model — CP-18 & CP-19

## Combat Maneuvers, Environment & Terrain

**Project:** Deterministic D&D 3.5e AI Dungeon Master (AIDM)
**Authority:** Governance / Quality Assurance (Design-Blocking)
**Status:** Canonical Reference
**Applies To:** CP-18 (Combat Maneuvers), CP-19 (Environment & Terrain)

---

## 0. PURPOSE

This document enumerates **replay-breaking determinism threats** expected in CP-18 and CP-19 and prescribes **allowed patterns** and **forbidden patterns** to mitigate them.

It exists to prevent:

* Nondeterministic ordering
* Hidden RNG consumption drift
* Branch-dependent event emission
* Late-stage replay divergence

This document **does not authorize mechanics**.

---

## 1. GLOBAL DETERMINISM RULES (BINDING)

1. **One action → one resolution window.** No multi-round state machines.
2. **Fixed RNG stream.** Use `"combat"` only unless explicitly authorized.
3. **Fixed RNG order.** Consumption order must be identical on all branches.
4. **Ordered event emission.** Deterministic sort keys before emission.
5. **No hidden iteration.** Never iterate over unordered collections.

Violation of any rule = acceptance failure.

---

## 2. CP-18 THREAT CATALOG — COMBAT MANEUVERS

### T-18-01: Opposed Roll Ordering Drift

**Description:** Attacker/defender rolls consumed in different orders based on branch (success/failure).

* **Allowed Pattern:**

  * Always consume attacker roll, then defender roll, regardless of outcome.
* **Forbidden Pattern:**

  * Consuming defender roll only on success.

**Applies To:** Bull Rush, Trip, Overrun, Disarm, Grapple-lite

---

### T-18-02: AoO Cascade Nondeterminism

**Description:** Variable AoO counts or ordering based on movement path or threat set iteration.

* **Allowed Pattern:**

  * Use CP-15 AoO ordering (initiative → entity id lexicographic).
* **Forbidden Pattern:**

  * Iterating over a `set()` of threatening entities.

**Applies To:** All maneuvers that provoke AoOs

---

### T-18-03: Conditional Event Emission

**Description:** Emitting different numbers of events on success vs failure.

* **Allowed Pattern:**

  * Emit placeholder / null events to preserve event count.
* **Forbidden Pattern:**

  * Emitting fewer events on failure.

**Applies To:** Trip (counter-trip), Disarm (counter-disarm)

---

### T-18-04: Grapple-Lite Leakage

**Description:** Accidental bidirectional state or hidden relational coupling.

* **Allowed Pattern:**

  * Apply `Grappled` to defender only; attacker has no condition.
* **Forbidden Pattern:**

  * Attacker flag like `is_grappling` or shared references.

**Applies To:** Grapple-lite only

---

## 3. CP-19 THREAT CATALOG — ENVIRONMENT & TERRAIN

### T-19-01: Forced Movement Path Ambiguity

**Description:** Multiple valid displacement paths (e.g., diagonal vs orthogonal).

* **Allowed Pattern:**

  * Require explicit path declaration or deterministic tie-breaker.
* **Forbidden Pattern:**

  * Letting engine choose any valid path.

**Applies To:** Bull Rush into terrain, Overrun displacement

---

### T-19-02: Terrain-Dependent Branch Explosion

**Description:** Terrain checks introducing branch-specific logic paths.

* **Allowed Pattern:**

  * Normalize terrain effects into numeric modifiers applied pre-resolution.
* **Forbidden Pattern:**

  * Terrain-specific resolution code paths.

**Applies To:** Difficult terrain, slopes, shallow water

---

### T-19-03: Falling Trigger Ordering

**Description:** Ambiguous ordering between forced movement, AoOs, and falling.

* **Allowed Pattern:**

  * Order: AoOs → movement → fall resolution.
* **Forbidden Pattern:**

  * Resolving fall mid-movement.

**Applies To:** Ledges, pits, elevation changes

---

### T-19-04: Environmental RNG Leakage

**Description:** Terrain introducing new randomness sources.

* **Allowed Pattern:**

  * Deterministic thresholds only; no RNG.
* **Forbidden Pattern:**

  * Random slip/fall chances.

**Applies To:** All CP-19 features

---

## 4. CROSS-CUTTING THREATS

### T-X-01: Unordered Data Structures

**Description:** Using unordered containers in world state or iteration.

* **Allowed Pattern:**

  * Lists sorted by stable keys.
* **Forbidden Pattern:**

  * Sets, dict iteration without sorting.

---

### T-X-02: Floating-Point Drift

**Description:** FP math causing divergence across platforms.

* **Allowed Pattern:**

  * Integer arithmetic only.
* **Forbidden Pattern:**

  * Floats or decimals in resolution.

---

## 5. VERIFICATION CHECKLIST

Before acceptance of CP-18 or CP-19 implementation:

* [ ] RNG consumption order documented and matched
* [ ] Event counts identical across branches
* [ ] AoO ordering verified
* [ ] No unordered iteration
* [ ] 10× replay hash stability verified

---

## 6. HOW TO USE THIS DOCUMENT

* Designers: consult during design to avoid illegal patterns.
* Implementers: follow allowed patterns strictly.
* Auditors: use as a rejection checklist.

Silence is not allowed—explicitly document mitigations.

---

## 7. FINAL NOTE

Determinism failures are **systemic**, not local.

Fixing them early is cheap. Fixing them late is expensive.
