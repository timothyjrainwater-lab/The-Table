# PM Briefing — Current

**Last updated:** 2026-02-14 (WO-SMOKE-TEST-002 delivered. 4/4 fixes confirmed, 3 new scenarios exercised.)

---

## Stoplight: GREEN (infrastructure) / GREEN (integration)

5,526 unit tests pass. Smoke test 002 passes 28/29 stages. 4/4 prior fixes confirmed in running system. Melee, multi-target, and condition paths exercised. **The building stands up, and the plumbing works.**

## Smoke Test Results (WO-SMOKE-TEST-002, commit pending)

**28/29 stages PASS.** Regression 14/14 PASS. Gap verification 4/4 CONFIRMED. 3 new scenarios exercised.

| Section | Result |
|---|---|
| Regression (14 original stages) | 14/14 PASS |
| Gap verification (4 fixes) | 4/4 CONFIRMED |
| Scenario B: Melee attack | PASS — fighter hits goblin, damage_type=slashing, entity names resolved |
| Scenario C: Multi-target fireball | PASS — 3 goblins hit, additional_targets captured in NarrativeBrief |
| Scenario D: Hold Person + NarrationValidator | PASS (28/29) — condition applied, validator invoked |

**New findings (2):**

1. **NarrativeBrief condition extraction bug** — `narrative_brief.py:537-547`. Assembler checks `payload.get("condition_type")` but play_loop emits `payload["condition"]`. Same issue for target: assembler checks `target_id`, event uses `entity_id`. Pure-debuff spells get `condition_applied=None` and `target_name=None`. ~4 line fix.
2. **Multi-target template gap** — Template narration references primary target only. `additional_targets` data is in the brief but templates don't use it. Design boundary, not bug.

**NarrationValidator status:** INVOKED. Returned PASS with 0 violations on template-generated narration for Hold Person. The validator is importable and callable — no longer "NOT TESTED."

## WO Verdicts This Session

| WO | Verdict | Commit |
|---|---|---|
| WO-SMOKE-TEST-002 | **DELIVERED** | `4801510` |
| WO-SMOKE-TEST-001 | **ACCEPTED** | `d0d9dc2` |
| WO-SPELL-NARRATION-POLISH | **ACCEPTED** | `2b2a47b` |
| WO-CONTENT-ID-POPULATION | **ACCEPTED** | `532ae16` |
| WO-FRAMEWORK-UPDATE-001 | **ACCEPTED** | `d62b37a` (pushed to framework repo) |
| WO-FRAMEWORK-UPDATE-002 | **ACKNOWLEDGED** — not PM-drafted, Operator-executed | `aaecfef` (PR #1) |

## Requires PM Decision

1. **Spark LLM Selection — what model goes in the chair?** — [MEMO_SPARK_LLM_SELECTION.md](pm_inbox/MEMO_SPARK_LLM_SELECTION.md)
   Architecture assumes an LLM in the Spark cage. No model has been selected. Blocks vertical slice completion. API vs local vs hybrid? Model size? Offline requirement? PM to decide.

## Requires Operator Action (NOW)

1. **Review WO-SMOKE-TEST-002 debrief** — [DEBRIEF_WO-SMOKE-TEST-002.md](pm_inbox/DEBRIEF_WO-SMOKE-TEST-002.md)
   28/29 PASS. 4/4 fixes confirmed. 1 new integration bug found (NarrativeBrief condition extraction). PM to decide if this warrants a follow-up WO.

2. **NarrativeBrief condition extraction fix** — ~4 lines in `aidm/lens/narrative_brief.py`. Condition-applying spells (Hold Person, Slow, etc.) produce empty brief fields. Should be a targeted fix WO.

## PM Action Queue — CLEARED

All 4 items from previous queue resolved:

- [x] **WO-CONTENT-ID-POPULATION** — DRAFTED → [WO-CONTENT-ID-POPULATION_DISPATCH.md](pm_inbox/WO-CONTENT-ID-POPULATION_DISPATCH.md)
- [x] **WO-SPELL-NARRATION-POLISH** — DRAFTED → [WO-SPELL-NARRATION-POLISH_DISPATCH.md](pm_inbox/WO-SPELL-NARRATION-POLISH_DISPATCH.md)
- [x] **Suspended WO evaluation** — All three remain suspended (see verdicts below)
- [x] **NarrationValidator wiring** — Deferred to future integration hardening WO (not standalone)

### Suspended WO Verdicts

| WO | Verdict | Reason |
|---|---|---|
| WO-SPEAK-SERVER | **REMAIN SUSPENDED** | Voice infrastructure, not integration. Belongs in BURST-001 Voice-First track. |
| WO-FROZEN-VIEW-GUARD | **REMAIN SUSPENDED** | Defensive hardening. Smoke test didn't surface as break point. Draft after integration fixes. |
| Resolver dedup | **REMAIN SUSPENDED** | Known duplication (Field Manual #5), not a correctness issue. |
| NarrationValidator wiring | **RESOLVED** | Invoked in WO-SMOKE-TEST-002 Scenario D. Importable + callable. Returns PASS/WARN/FAIL. |

## H1+Smoke Batch Complete

- WO-TTS-COLD-START-RESEARCH — 6 RQs, persistent server recommended
- WO-RNG-PROTOCOL-001 — 19 files, Protocol extraction
- WO-WEAPON-PLUMBING-001 — 34 tests, 3 dormant fixes live
- WO-TTS-CHUNKING-001 — Adapter-level sentence chunking
- WO-BRIEF-WIDTH-001 — Multi-target + causal chains + conditions
- WO-COMPILE-VALIDATE-001 — CT-001–007 + content_id emission + contraindications (`fb05aef`)
- WO-NARRATION-VALIDATOR-001 — P0 negative rules + narration persistence (`2d923ed`)
- **WO-SMOKE-TEST-001** — End-to-end integration demo, 14/14 PASS (`d0d9dc2`)
- **WO-SMOKE-TEST-002** — Post-fix regression + new scenarios, 28/29 PASS, 4/4 fixes confirmed

## Active Operational Files

- [WO-SMOKE-TEST-002_DISPATCH.md](pm_inbox/WO-SMOKE-TEST-002_DISPATCH.md) — DELIVERED
- [DEBRIEF_WO-SMOKE-TEST-002.md](pm_inbox/DEBRIEF_WO-SMOKE-TEST-002.md) — DELIVERED, awaiting PM review
- [WO-CONTENT-ID-POPULATION_DISPATCH.md](pm_inbox/WO-CONTENT-ID-POPULATION_DISPATCH.md) — DELIVERED
- [DEBRIEF_WO-CONTENT-ID-POPULATION.md](pm_inbox/DEBRIEF_WO-CONTENT-ID-POPULATION.md) — PM REVIEWED, ACCEPTED
- [WO-SPELL-NARRATION-POLISH_DISPATCH.md](pm_inbox/WO-SPELL-NARRATION-POLISH_DISPATCH.md) — DELIVERED
- [DEBRIEF_WO-SPELL-NARRATION-POLISH.md](pm_inbox/DEBRIEF_WO-SPELL-NARRATION-POLISH.md) — PM REVIEWED, ACCEPTED
- [DEBRIEF_WO-WEAPON-PLUMBING-001.md](pm_inbox/DEBRIEF_WO-WEAPON-PLUMBING-001.md) — COMMITTED (a9a3c8c), awaiting PM review
- [DEBRIEF_WO-SMOKE-TEST-001.md](pm_inbox/DEBRIEF_WO-SMOKE-TEST-001.md) — PM REVIEWED, ACCEPTED
- [DEBRIEF_WO-FRAMEWORK-UPDATE-001.md](pm_inbox/DEBRIEF_WO-FRAMEWORK-UPDATE-001.md) — PM REVIEWED, ACCEPTED
- [WO-FRAMEWORK-UPDATE-002_DISPATCH.md](pm_inbox/WO-FRAMEWORK-UPDATE-002_DISPATCH.md) — Operator-executed, COMPLETE
- [BURST_INTAKE_QUEUE.md](pm_inbox/BURST_INTAKE_QUEUE.md) — BURST-001 thru 004 (parked)

## Persistent Files

- `README.md` — Inbox hygiene rules
- `PM_BRIEFING_CURRENT.md` — This file
- `REHYDRATION_KERNEL_LATEST.md` — PM rehydration block
