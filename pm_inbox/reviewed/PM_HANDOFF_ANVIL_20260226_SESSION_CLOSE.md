# PM BRIEFING — Anvil Handoff 2026-02-26 (Session Close)
**For:** Slate
**From:** Anvil
**Date:** 2026-02-26
**Status:** ready for review

---

## Session Summary

Engine Batch B Round 1 closed (DISPATCH #12 — all 4 WOs accepted). While waiting for Batch B Round 2 sequencing, a Dungeon Soup video surfaced a red-team analysis session that produced 6 new artifacts and identified 2 new probes.

All artifacts filed. No open loops.

---

## New Artifacts This Session

| Artifact | Location | Type |
|----------|----------|------|
| HOOLIGAN-CREATIVE-ACTION-SUITE-001 | tests/ | hooligan test suite — 21 cases, axis-tagged |
| REDTEAM-CREATIVE-ADVERSARIAL-001 | docs/design/ | red-team brief — 15 categories, priority stack |
| STRATEGY-REDTEAM-AXIS-001 | docs/design/ | two-axis framework — judgment vs world model |
| PROBE-WORKER-TREATMENT-001 | pm_inbox/ | A/B test probe — pre-task treatment effect |
| PROBE-WORLDMODEL-001 | (see below) | new probe — queued here for your tracking |

---

## New Items for PM Queue

### 1) PROBE-WORLDMODEL-001 (NEW — queue after PROBE-JUDGMENT-LAYER-001 closes)

**What:** The Cheevo list analysis revealed the engine has no model of persistent world objects after combat. Death removes entities. No corpses, remnants, phylactery locations, stomach contents.

The judgment scaffold cannot produce correct rulings without this state. This is not a judgment gap — it is a world model gap. Different problem, different probe.

**Scope:**
- Run Cheevo-class scenarios (TC-001 phylactery swallow, TC-002 cook on corpse, TC-004 Dryad sap extraction) through the judgment scaffold
- For each scenario: what world state facts did the LLM need? Which exist? Which are absent?
- Output: minimum viable world model spec → input to STRATEGY-WORLDMODEL-001

**Sequencing:** AFTER PROBE-JUDGMENT-LAYER-001 closes. Do not run in parallel.

---

### 2) Two WO candidates from HOOLIGAN suite (queue in Batch C)

| WO | Mechanic | PHB Anchor | Priority |
|----|----------|------------|---------|
| WO-ENGINE-VERBAL-SPELL-BLOCK-001 | Gagged caster cannot cast V spells | PHB 174 — spell components | Medium |
| WO-ENGINE-INTIMIDATE-DEMORALIZE-001 | Intimidate as standard action in combat → Shaken 1 round | PHB 76 | Medium |

Both are defined PHB mechanics with no implementation. Not judgment layer — just unimplemented. Standard WO format.

---

### 3) Standing policy decisions (add to builder field manual)

Five policies from STRATEGY-REDTEAM-AXIS-001 that need to be written into standing ops so builders handle these consistently:

| Policy | Decision |
|--------|---------|
| Called shots (anatomy targeting) | Not in core 3.5. Route to Disarm/Grapple/Trip. Communicate denial. No limb damage rules. |
| Personality immunity claims ("I'm too crazy to be charmed") | Will save applies. No special immunity unless creature type. |
| Holy water creative delivery | Standard rules only. No bonus for targeting open mouth, etc. |
| Degrees of success requests | Binary pass/fail. Narration can note margin. No partial mechanic. |
| Folklore items (salt vs ghost, garlic vs vampire) | No PHB anchor. Apply closest supported analog. Communicate ruling. |

---

### 4) PROBE-WORKER-TREATMENT-001 (already filed — schedule alongside Batch C/D/E)

Pre-task treatment A/B test. File is in pm_inbox/. Three conditions, six metrics, matched WO pairs. Low overhead — runs in parallel with engine batches.

---

## Existing Items (still pending)

| Item | Status | Notes |
|------|--------|-------|
| PROBE-JUDGMENT-LAYER-001 | queued | Run before architecture decision on judgment scaffold |
| Regression protocol update | pending | Builder field manual: cap retries at 1 fix/1 re-run, report up if still failing |
| FINDING-ENGINE-FLATFOOTED-AOO-001 | pending | Needs to be added to ENGINE_COVERAGE_MAP.md |

---

## Sequencing Recommendation

**Batch C:**
1. WO-ENGINE-VERBAL-SPELL-BLOCK-001
2. WO-ENGINE-INTIMIDATE-DEMORALIZE-001
3. Next wave from ENGINE_COVERAGE_MAP.md priority gap list

**After Batch C closes:**
- Run PROBE-JUDGMENT-LAYER-001
- Then PROBE-WORLDMODEL-001

**Parallel throughout:**
- PROBE-WORKER-TREATMENT-001 (matched pairs from whatever batch is running)

---

## What Slate Does NOT Need to Sequence

These are Anvil-tracked, not PM work — but Slate needs to know they exist because they affect WO routing and debrief behavior:

| Document | Location | What it is |
|----------|----------|------------|
| HOOLIGAN-CREATIVE-ACTION-SUITE-001 | tests/ | 21 creative action test cases, axis-tagged |
| REDTEAM-CREATIVE-ADVERSARIAL-001 | docs/design/ | 15 red-team categories |
| STRATEGY-REDTEAM-AXIS-001 | docs/design/ | Two-axis framework (judgment vs world model) |
| CANARY-GAP-TAXONOMY-001 | docs/design/ | 12 gap families from Cheevo script |
| LEDGER-CHEEVO-CANARY-EXPANSION-001 | docs/design/ | 10 canary entries with sibling expansion |
| **REGISTER-HIDDEN-DM-KERNELS-001** | docs/design/ | **Read this one — it changes how WOs are routed** |

---

## New Routing Instruction for Builder Debriefs (add to builder field manual)

REGISTER-HIDDEN-DM-KERNELS-001 defines 10 hidden DM functions the PHB assumes for free. When a builder's Pass 3 surfaces a finding that touches a kernel, flag it.

Format in debrief: *"This WO touches KERNEL-03 Constraint Algebra — concentration tracking uses the same primitive."*

Anvil adds the finding to the register. Compound insight becomes automatic.

**What builders should watch for:**
- Concentration tracking → KERNEL-03 (Constraint Algebra)
- Attunement limits → KERNEL-03
- Geas/oath enforcement → KERNEL-03
- Knowledge check gating → KERNEL-05 (Epistemic State)
- HP-0 behavior for Lich/Troll/Vampire → KERNEL-01 (Entity Lifecycle)
- Looting after combat → KERNEL-01
- NPC attitude shift → KERNEL-07 (Social Consequence)
- Recurring judgment scaffold ruling → KERNEL-08 (Precedent)

---

*Filed 2026-02-26. Anvil (Squire seat). Session close handoff.*
