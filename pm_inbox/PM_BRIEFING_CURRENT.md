# PM Briefing — Current

**Last updated:** 2026-02-18 (WO-SMOKE-TEST-003 DELIVERED. Hooligan Protocol: 12 adversarial scenarios, 5 PASS, 7 FINDING, 0 CRASH.)

---

## Stoplight: GREEN (infrastructure) / GREEN (integration)

5,804 unit tests pass. Smoke test passes 49/49 stages + 12 hooligan scenarios (5 PASS, 7 FINDING, 0 CRASH) + 20-scenario fuzzer (19 PASS, 1 FINDING). **Integration board clear.**

## Smoke Test Results (post WO-SMOKE-FUZZER)

**44/44 stages PASS. Hooligan: 5/12 PASS, 7/12 FINDING, 0 CRASH. Fuzzer: 19/20 PASS, 1 FINDING. Determinism: 6/6 meta-tests PASS.** Modular structure: `scripts/smoke_scenarios/` with common.py, manual.py, fuzzer.py, hooligan.py. Orchestrator: `scripts/smoke_test.py`.

| Section | Result |
|---|---|
| Regression (14 original stages) | 14/14 PASS |
| Gap verification (4 fixes) | 4/4 CONFIRMED |
| Scenario B: Melee attack | PASS |
| Scenario C: Multi-target fireball | PASS |
| Scenario D: Hold Person + NarrationValidator | PASS |
| Scenario E: Self-buff (Shield) | PASS |
| Scenario F: Healing (Cure Light Wounds) | PASS |
| Scenario G: Spell on dead entity | PASS |
| Scenario H: Sequential combat | PASS |
| **Hooligan H-002: Grapple spell effect (Tier B)** | **PASS** — correctly denied |
| **Hooligan H-003: Fireball self (Tier A)** | **PASS** — caster took 27 self-damage |
| **Hooligan H-004: Full attack corpse (Tier A)** | **PASS** — correctly denied |
| **Hooligan H-010: 10-buff stack (Tier A)** | **PASS** — 8 buffs, 16 conditions, 0 errors |
| **Hooligan H-011: Fireball party (Tier A)** | **PASS** — 4 friendlies hit |
| **Fuzzer (20 random spells, seed=42)** | **19 PASS, 1 FINDING** |

**Hooligan findings (7):**

| Scenario | Severity | Description |
|---|---|---|
| H-001 | coverage_gap | No ReadyIntent resolver (PHB p.160) |
| H-005 | coverage_gap | No DelayIntent resolver (PHB p.160) |
| H-006 | coverage_gap | No DropItem/Unequip resolver (PHB p.142) |
| H-007 | coverage_gap | No ChargeIntent resolver (PHB p.154) |
| H-008 | missing_mechanic | CLW on undead: no creature_type in entity schema (PHB p.215-216) |
| H-009 | coverage_gap | No CoupDeGraceIntent resolver (PHB p.153) |
| H-012 | coverage_gap | Weapon schema rejects weapon_type='improvised' (PHB p.113) |

**Fuzzer findings (1):**

1. **Cone of Cold: damage_type is None** — Spell has damage_dice=10d6 but NarrativeBrief.damage_type is not populated. Likely an assembler gap for AoE damage spells where no hp_changed event fires (targets may save for zero or take damage but damage_type extraction misses the path).

**Remaining findings from manual scenarios (1):**

1. **Multi-target template gap** — Design boundary, not bug. Templates reference primary target only.

## WO Verdicts This Session

| WO | Verdict | Commit |
|---|---|---|
| WO-SMOKE-TEST-003 | **DELIVERED** — awaiting PM review | `3372207` |
| WO-FUZZER-DETERMINISM-GATES | **ACCEPTED** | `e128342` |
| WO-ORACLE-SURVEY | **ACCEPTED** (research, no code) | `7b4268f` |
| WO-SMOKE-FUZZER | **ACCEPTED** (determinism gates now landed) | `ac67327` |
| WO-AOE-DEFEATED-FILTER | **ACCEPTED** | `4bba1eb` |
| WO-CONDITION-EXTRACTION-FIX | **ACCEPTED** | `acdf410` |
| WO-SMOKE-TEST-002 | **ACCEPTED** | `84301f3` |
| WO-SMOKE-TEST-001 | **ACCEPTED** | `d0d9dc2` |
| WO-SPELL-NARRATION-POLISH | **ACCEPTED** | `2b2a47b` |
| WO-CONTENT-ID-POPULATION | **ACCEPTED** | `532ae16` |
| WO-FRAMEWORK-UPDATE-001 | **ACCEPTED** | `d62b37a` (pushed to framework repo) |
| WO-FRAMEWORK-UPDATE-002 | **ACKNOWLEDGED** — not PM-drafted, Operator-executed | `aaecfef` (PR #1) |

## Requires Operator Action (NOW)

1. ~~**Dispatch WO-SMOKE-FUZZER**~~ — **ACCEPTED** (`ac67327`). Modular structure landed. 19/20 PASS, 1 Cone of Cold finding. Determinism gates (Change 2a) not implemented — patch WO drafted.

2. ~~**Dispatch WO-FUZZER-DETERMINISM-GATES**~~ — **ACCEPTED.** ScenarioID hashes, event log digests, FUZZ RECEIPT, stop-on-failure, `--collect-all`, `--replay`. 6/6 meta-tests PASS. **FINDING:** `payload.cast_id` uses `uuid4()` (not RNG-seeded), stripped from digest. PM decision needed: determinize cast_id in future WO?

3. ~~**Dispatch WO-ORACLE-SURVEY**~~ — **COMPLETE.** Survey delivered: [SURVEY_ORACLE_OVERLAP.md](pm_inbox/SURVEY_ORACLE_OVERLAP.md). 7/7 sections. Strongest overlap: WorkingSet (PromptPack), Event Sourcing (EventLog + replay_runner). Weakest: StoryState (no threads/clocks). Key finding: provenance.py W3C PROV-DM exists but not wired to EventLog.

4. ~~**Dispatch WO-SMOKE-TEST-003**~~ — **DELIVERED.** Hooligan Protocol: 12 adversarial scenarios, 5 PASS, 7 FINDING (6 coverage gaps + 1 missing mechanic), 0 CRASH. See [DEBRIEF_WO-SMOKE-TEST-003.md](pm_inbox/DEBRIEF_WO-SMOKE-TEST-003.md).

## Doctrine Adoption (2026-02-18)

**GT v12 adopted as product doctrine.** Subsystem memos (Oracle v5.2, UI v4, ImageGen v4) accepted as plans-under-GT. Audio pillar adopted on paper, deferred in code until BURST-001. See kernel for full adoption record.

**Build order:** Smoke fuzzer → Oracle survey (parallel) → Hooligan (after fuzzer) → Oracle implementation → Lens/Director → UI → Roleplay

**Doctrine files:**
- [DOCTRINE_01_FINAL_DELIVERABLE.txt](pm_inbox/DOCTRINE_01_FINAL_DELIVERABLE.txt) — Anchor index + gap register
- [DOCTRINE_02_GOLDEN_TICKET_V12.txt](pm_inbox/DOCTRINE_02_GOLDEN_TICKET_V12.txt) — Product doctrine
- [DOCTRINE_03_ORACLE_MEMO_V52.txt](pm_inbox/DOCTRINE_03_ORACLE_MEMO_V52.txt) — Oracle subsystem spec
- [DOCTRINE_04_TABLE_UI_MEMO_V4.txt](pm_inbox/DOCTRINE_04_TABLE_UI_MEMO_V4.txt) — UI spec
- [DOCTRINE_05_IMAGE_GEN_MEMO_V4.txt](pm_inbox/DOCTRINE_05_IMAGE_GEN_MEMO_V4.txt) — Image gen spec

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
| NarrationValidator wiring | **RESOLVED** | Invoked in WO-SMOKE-TEST-002 Scenarios D and H. Importable + callable. Returns PASS/WARN/FAIL. |

## H1+Smoke Batch Complete

- WO-TTS-COLD-START-RESEARCH — 6 RQs, persistent server recommended
- WO-RNG-PROTOCOL-001 — 19 files, Protocol extraction
- WO-WEAPON-PLUMBING-001 — 34 tests, 3 dormant fixes live
- WO-TTS-CHUNKING-001 — Adapter-level sentence chunking
- WO-BRIEF-WIDTH-001 — Multi-target + causal chains + conditions
- WO-COMPILE-VALIDATE-001 — CT-001–007 + content_id emission + contraindications (`fb05aef`)
- WO-NARRATION-VALIDATOR-001 — P0 negative rules + narration persistence (`2d923ed`)
- **WO-SMOKE-TEST-001** — End-to-end integration demo, 14/14 PASS (`d0d9dc2`)
- **WO-SMOKE-TEST-002** — Post-fix regression + 7 exploratory scenarios, 43/44→44/44 PASS
- **WO-CONDITION-EXTRACTION-FIX** — Condition event key alignment, 44/44 PASS
- **WO-AOE-DEFEATED-FILTER** — AoE skips defeated entities, 44/44 PASS

- **WO-SMOKE-FUZZER** — Generative fuzzer, modular smoke infrastructure (`ac67327`)
- **WO-FUZZER-DETERMINISM-GATES** — Provable reproducibility gates for fuzzer (`e128342`)
- **WO-ORACLE-SURVEY** — Oracle v5.2 overlap mapping, research only (`7b4268f`)
- **WO-SMOKE-TEST-003** — The Hooligan Protocol, 12 adversarial edge cases (5 PASS, 7 FINDING, 0 CRASH)

## Active Operational Files

- [DOCTRINE_01_FINAL_DELIVERABLE.txt](pm_inbox/DOCTRINE_01_FINAL_DELIVERABLE.txt) — Anchor index + gap register
- [DOCTRINE_02_GOLDEN_TICKET_V12.txt](pm_inbox/DOCTRINE_02_GOLDEN_TICKET_V12.txt) — Product doctrine (TRUTH)
- [DOCTRINE_03_ORACLE_MEMO_V52.txt](pm_inbox/DOCTRINE_03_ORACLE_MEMO_V52.txt) — Oracle subsystem spec
- [DOCTRINE_04_TABLE_UI_MEMO_V4.txt](pm_inbox/DOCTRINE_04_TABLE_UI_MEMO_V4.txt) — UI spec
- [DOCTRINE_05_IMAGE_GEN_MEMO_V4.txt](pm_inbox/DOCTRINE_05_IMAGE_GEN_MEMO_V4.txt) — Image gen spec
- [BURST_INTAKE_QUEUE.md](pm_inbox/BURST_INTAKE_QUEUE.md) — BURST-001 thru 004 (parked pending Oracle-first)
- [MEMO_SPARK_LLM_SELECTION.md](pm_inbox/MEMO_SPARK_LLM_SELECTION.md) — H2 blocker, parked

All H1 + smoke test dispatches and debriefs archived to `pm_inbox/reviewed/archive_h1_smoke/`.

## Persistent Files

- `README.md` — Inbox hygiene rules
- `PM_BRIEFING_CURRENT.md` — This file
- `REHYDRATION_KERNEL_LATEST.md` — PM rehydration block
