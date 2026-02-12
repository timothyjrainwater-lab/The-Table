# Document Drift Ledger

**Purpose:** Track known contradictions between project documents and record their resolutions. When a new agent finds a document saying X but reality is Y, this is where the discrepancy gets logged and resolved.

**Maintained by:** PM (Opus)
**Created:** 2026-02-12 (RWO-003: Documentation Canonicalization)

---

## How to Read This Ledger

Each entry has:
- **ID**: DRIFT-NNN for tracking
- **Documents**: Which documents contradict each other
- **Contradiction**: What they disagree about
- **Resolution**: How the contradiction is resolved
- **Status**: RESOLVED (no action needed) or OPEN (needs a work item)
- **Action**: What was done or what needs to be done

---

## DRIFT-001: Voice Integration Scope vs Immersion Layer Implementation

**Documents:**
- `PROJECT_COHERENCE_DOCTRINE.md` (Section: Scope Boundaries, "Out of Scope")
- `PROJECT_STATE_DIGEST.md` (Section: Locked Systems, "M3 Immersion Layer v1")

**Contradiction:** The Coherence Doctrine (Feb 2025) lists "Production Voice Integration" and "Production ASR/TTS" as explicitly out of scope. The PSD (2026-02-12) shows STT, TTS, Image, and AudioMixer adapters implemented under the M3 Immersion Layer, with real backend wiring (Kokoro TTS adapter with real model synthesis, Whisper STT adapter, SDXL Image adapter).

**Resolution:** RESOLVED -- no conflict exists once the boundary is properly understood.

The Doctrine's intent was that the **deterministic runtime** must not depend on voice processing. This remains true. The immersion adapters operate outside the deterministic boundary:
- They are non-authoritative (cannot mutate WorldState or affect replay)
- They are governed by `docs/IMMERSION_BOUNDARY.md`
- All adapters have stub defaults and are Protocol-based
- The deterministic engine functions identically with or without real backends

The Doctrine's "out of scope" language was written before the Immersion Layer design existed. The adapters are "production-capable infrastructure" but do not violate the Doctrine's core concern (deterministic runtime independence from voice/image processing).

**Action:** Scope clarification addendum added to `PROJECT_COHERENCE_DOCTRINE.md` (2026-02-12, RWO-003).

**Status:** RESOLVED

---

## DRIFT-002: Vertical Slice V1 Combat Exclusion vs Full Combat Stack

**Documents:**
- `VERTICAL_SLICE_V1.md` (Sections: "What This Excludes", "Non-Goals")
- `PROJECT_STATE_DIGEST.md` (Section: Locked Systems, "Combat Resolution Stack")

**Contradiction:** Vertical Slice V1 explicitly excludes combat resolution ("No full combat resolver: Tactic selection only, no damage/condition application"), movement resolution, action economy, spell effects, initiative order, and multi-round combat. The PSD shows all of these delivered: attack resolution (CP-10), full attack sequences (CP-11), initiative and action economy (CP-14), AoO (CP-15), conditions (CP-16), saves (CP-17), targeting/visibility (CP-18A), mounted combat (CP-18A), combat maneuvers (CP-18), environment/terrain (CP-19), spellcasting (WO-014/WO-015, 53 spells), scene management (WO-040), and multi-room dungeon persistence (P2).

**Resolution:** RESOLVED -- Vertical Slice V1 was the Phase 0 proof-of-concept. Its exclusions were accurate at the time of writing (Feb 2025, CP-07D/CP-09). All listed exclusions were subsequently delivered in later phases of the execution plan.

**Action:** HISTORICAL banner added to `VERTICAL_SLICE_V1.md` (2026-02-12, RWO-003).

**Status:** RESOLVED

---

## DRIFT-003: Test Runtime Gate ("<5 seconds") vs Actual Runtime (~51 seconds)

**Documents:**
- `PROJECT_COHERENCE_DOCTRINE.md` (Section 3: Test Runtime Invariant -- "< 5 seconds")
- `PROJECT_STATE_DIGEST.md` (Section: Critical Invariants -- "rule predates scale")
- `README.md` (Section: Contributing -- "Tests must run in < 2 seconds")

**Contradiction:** Three documents state different test runtime targets:
1. Coherence Doctrine: "Full test suite MUST complete in < 5 seconds"
2. README (Contributing): "Tests must run in < 2 seconds"
3. PSD (Critical Invariants): Acknowledges "currently ~51s at 3730 tests -- rule predates scale"

Actual runtime: ~51 seconds for 3,753 tests (~13.6ms per test average).

**Resolution:** OPEN -- the original gate needs re-baselining.

The original < 5 second / < 2 second targets were set when the suite had 435-1,225 tests. At 3,753 tests, meeting the original wall-clock target is not feasible without fundamentally changing the test strategy. The PSD already acknowledges this with the parenthetical "rule predates scale."

Options for re-baselining (requires PM decision):
- (a) Set a per-test-average gate (e.g., < 15ms per test) instead of wall-clock
- (b) Set a new wall-clock gate proportional to test count (e.g., < 60s for up to 4,000 tests)
- (c) Maintain the aspiration but downgrade from MUST to SHOULD

**Action:** Scope clarification addendum added to `PROJECT_COHERENCE_DOCTRINE.md`. Formal re-baselining deferred as a separate work item. The PSD already documents the actual state accurately.

**Status:** OPEN -- awaiting re-baseline decision

---

## DRIFT-004: README Test Count vs Actual Test Count

**Documents:**
- `README.md` (line 266): "All tests run in under 4 seconds (1331 tests total)"
- `README.md` (line 289): "Expected output: 453 passed in ~1.5s"
- `PROJECT_STATE_DIGEST.md`: "Total: 3753 tests"

**Contradiction:** The README reports two different historical test counts (1,331 and 453) and two different runtime claims (4 seconds and 1.5 seconds). Neither matches the current state (3,753 tests, ~51 seconds).

**Resolution:** RESOLVED (documented, low priority to fix).

The README is Tier 4 in document precedence for test counts. The PSD is authoritative. The README test counts are snapshots from earlier development periods (453 from initial foundation, 1,331 from an intermediate point). They are stale but not harmful -- a reader following the onboarding checklist reads the PSD first and gets the correct numbers.

**Action:** Logged here for awareness. README update deferred to a future documentation pass (not urgent -- the onboarding checklist directs agents to PSD first).

**Status:** RESOLVED (low-priority README update deferred)

---

## DRIFT-005: PSD "Non-Goals" Lists "Production ASR/TTS" but Kokoro TTS is Live

**Documents:**
- `PROJECT_STATE_DIGEST.md` (Section: Non-Goals): "Production ASR/TTS (structured intents only)"
- `PROJECT_STATE_DIGEST.md` (Section: Locked Systems): "WO-050: Kokoro TTS Wiring -- real model paths, CPU-only, ~1x real-time"

**Contradiction:** The PSD simultaneously lists "Production ASR/TTS" as a non-goal and describes a working Kokoro TTS adapter with real model synthesis.

**Resolution:** RESOLVED -- the non-goal is poorly worded, not actually violated.

The intent of the non-goal is that the **deterministic runtime** does not depend on ASR/TTS. The Kokoro TTS adapter is an immersion-layer component (atmospheric output only, non-authoritative, excluded from replay). "Production ASR/TTS" in the non-goals section should be understood as "ASR/TTS in the deterministic gameplay pipeline" rather than "no TTS implementation anywhere."

**Action:** Logged here. The PSD non-goals wording is a known imprecision. A future PSD revision should clarify this to: "ASR/TTS dependency in deterministic runtime (immersion-layer adapters are permitted)."

**Status:** RESOLVED (PSD wording refinement deferred)

---

## DRIFT-006: Coherence Doctrine "Current Status" Snapshot Stale

**Documents:**
- `PROJECT_COHERENCE_DOCTRINE.md` (Section 3): "Current Status: 1225 tests in ~3.7 seconds (~3.0ms/test)"
- `PROJECT_STATE_DIGEST.md`: "Total: 3753 tests"

**Contradiction:** The Doctrine shows a status line from Feb 2025 that reports 1,225 tests. The actual count is 3,753.

**Resolution:** RESOLVED -- the Doctrine's "Current Status" line is understood to be a point-in-time snapshot, not a live counter. It is marked as stale in the scope clarification addendum.

**Action:** Scope clarification addendum added to `PROJECT_COHERENCE_DOCTRINE.md` (2026-02-12, RWO-003). The line itself is not modified (the document is otherwise locked).

**Status:** RESOLVED

---

## Template for New Entries

```
## DRIFT-NNN: [Short Title]

**Documents:**
- [Document 1] (Section): "[Quoted claim]"
- [Document 2] (Section): "[Contradicting claim]"

**Contradiction:** [What they disagree about]

**Resolution:** [How to interpret the conflict]

**Action:** [What was done or needs to be done]

**Status:** RESOLVED | OPEN
```
