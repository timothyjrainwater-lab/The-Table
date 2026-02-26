# PROBE-WORLDMODEL-001
## World Model Gap — Minimum Viable State for Judgment Layer Correctness

**Type:** PROBE
**Status:** QUEUED (execute after PROBE-JUDGMENT-LAYER-001 closes)
**Lifecycle:** NEW
**Filed:** 2026-02-26
**Filed by:** Anvil (analysis), Thunder (authority), Slate (packet)
**Parent strategy:** STRAT-AIDM-JUDGMENT-LAYER-001 (pending: STRATEGY-WORLDMODEL-001 when probe closes)
**Source:** REDTEAM-CREATIVE-ADVERSARIAL-001 — World Model section

---

## Hard Prerequisite

**PROBE-JUDGMENT-LAYER-001 must close before this probe executes.**

Rationale: PROBE-JUDGMENT-LAYER-001 establishes baseline LLM behavior on improvised synthesis. PROBE-WORLDMODEL-001 assumes that baseline is known — it measures what state the LLM *needed* but didn't have, not what routing behavior looks like without any state. Probing world model gaps before routing behavior is characterized produces ambiguous results.

---

## Purpose

The engine has no model of persistent world objects. Death removes entities. There are no corpses, remnants, phylactery locations, stomach contents, or object states that persist after an entity leaves active combat.

This is not a resolver gap. It is a world model gap. The judgment scaffold cannot produce correct rulings without this state.

This probe characterizes *exactly* what world state facts the LLM needs to produce correct rulings on adversarial "Cheevo-class" scenarios — scenarios where creative exploitation of persistence, contents, and entity remnants is the entire point of the action.

Output: minimum world model spec. Input to STRATEGY-WORLDMODEL-001.

---

## Cheevo-Class Scenario Baseline (5 inputs)

These scenarios are selected specifically because they require world state that does not currently exist in the engine.

| ID | Scenario | World state gap |
|----|----------|----------------|
| WM-001 | "I drag the Lich's body to the forge and render it into jerky before it regenerates." | Corpse persistence, regeneration timer, crafting from body parts, anatomy model |
| WM-002 | "I swallow the phylactery before destroying the Lich." | Container model (entity holding object), object inside living entity, phylactery as immortality anchor |
| WM-003 | "I bind the Banshee's wail into these bagpipes using a Silence spell and a Programmed Illusion." | Persistent effect capture, magical object creation from defeated entity's ability, enchanting process |
| WM-004 | "I wish that the Dragon's hoard belongs to whoever the Dragon loves most." | Wish literalism, constraint on Dragon's behavior, property transfer, behavioral constraint model |
| WM-005 | "The Orc I knocked out is still breathing. I prop him up as a shield." | Unconscious entity persistence, entity-as-object, cover mechanic with living entity as shield |

---

## Per-Scenario Logging Template

For each input, record:

```
Scenario ID:       WM-001
Input:             [verbatim player action]
Ruling produced:   [verbatim system response or "none"]

World state facts needed:
  - [fact 1: what the LLM referenced or needed to reference]
  - [fact 2]
  - ...

Facts present in current engine state:
  - [fact: YES / NO / PARTIAL]
  - ...

Facts absent from current engine state:
  - [missing fact 1]
  - [missing fact 2]
  - ...

Ruling quality:
  - Correct: [YES / NO / PARTIAL]
  - Hallucinated facts: [YES / NO — list if yes]
  - Clarification requested: [YES / NO]
  - Fail-closed: [YES / NO]

Notes: [anything unexpected]
```

Complete one entry per scenario before moving to the next.

---

## Acceptance Gate

This probe is complete when:

1. All 5 scenarios exercised and logged
2. Per-scenario world state fact inventory complete (present / absent)
3. Aggregate missing-fact list compiled (union across all 5 scenarios)
4. Minimum viable world model spec drafted (what fields must exist for the LLM to rule correctly on these scenarios)
5. One-page summary produced

Output filed to: `pm_inbox/reviewed/PROBE-WORLDMODEL-001-RESULTS.md`

Notify: Slate → Thunder. Thunder reviews summary and authorizes STRATEGY-WORLDMODEL-001 drafting.

---

## One-Page Summary Template

```
# PROBE-WORLDMODEL-001 — RESULTS SUMMARY

**Date:** [DATE]
**Executor:** [name/agent]
**Scenarios exercised:** 5 / 5

## Fact Inventory (aggregate)
| Fact category | Present | Absent | Partial |
|---------------|---------|--------|---------|
| Corpse / remnant persistence | | | |
| Entity contents (swallowed/held objects) | | | |
| Object properties (immortality anchor, crafting, magical) | | | |
| Persistent effect capture / enchanting state | | | |
| Behavioral constraints on entities | | | |
| Unconscious entity as persistent actor | | | |
| Post-combat encounter state | | | |

## Ruling Quality Distribution
| Quality | Count |
|---------|-------|
| Correct (no hallucination) | |
| Partially correct | |
| Hallucinated facts | |
| Fail-closed (clarification requested) | |
| No ruling produced | |

## Minimum Viable World Model (draft)
[Fields required for judgment layer to rule correctly on these scenarios]

## Architecture Direction Signal
**Finding:** [what world model additions are minimum-viable vs. aspirational]
**Input to:** STRATEGY-WORLDMODEL-001

## Open Questions for Thunder
[Any ambiguous results requiring operator judgment before strategy is authorized]
```

---

## Execution Constraints

- **Non-blocking** — does not block Batch D, Batch E, or any current WO
- **Non-canonical** — probe does not emit any canonical ruling events
- **Observation-first** — record what is missing; do not patch during probe
- **Executor must not redesign during probe** — if a gap is found, log as finding; do not fix in-flight
- **Probe runner must be a dedicated worker** — not Slate, not Aegis

---

## Sequencing Context

```
PROBE-JUDGMENT-LAYER-001 (must close first)
    ↓
PROBE-WORLDMODEL-001 (this probe)
    ↓
STRATEGY-WORLDMODEL-001 (Thunder authorizes after results)
    ↓
WO(s) — world model implementation
```

PACK-CREATIVE-ADVERSARIAL-INTENTS-001 is Phase 2 material. Do not touch until PROBE-JUDGMENT-LAYER-001 closes.

---

## Parent Documents

- `docs/design/REDTEAM-CREATIVE-ADVERSARIAL-001.md` — source brief, world model section
- `docs/design/STRAT-AIDM-JUDGMENT-LAYER-001.md` — parent strategy
- `pm_inbox/PROBE-JUDGMENT-LAYER-001.md` — must close before this probe executes

---

*Filed 2026-02-26 — Anvil analysis, Thunder authority, Slate packet. Queued behind PROBE-JUDGMENT-LAYER-001.*
