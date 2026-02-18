# PM Briefing — Current

**Last updated:** 2026-02-18 (WO-UI-01 DISPATCH-READY. Table UI Phase 1: Client Bootstrap + Slice 0 + One PENDING Round Trip.)

---

## Stoplight: GREEN (infrastructure) / GREEN (integration)

5,840 unit tests pass (5,640 excluding pre-existing TTS/inbox failures). Smoke test passes 49/49 stages + 12 hooligan scenarios (5 PASS, 7 FINDING, 0 CRASH) + 20-scenario fuzzer (19 PASS, 1 FINDING). **Oracle Gate A: 22/22 PASS. Gate B: 23/23 PASS. Gate C: 24/24 PASS. Gate D: 18/18 PASS. Gate E: 14/14 PASS. No-backflow: PASS. Integration board clear.**

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
| WO-UI-01 | _(pending PM verdict)_ — 10/10 Gate F PASS, 0 regressions (111/111 total). 7/7 contract changes delivered. Frontend bootstrap (Three.js+TS+Vite), 3 camera postures, PENDING/REQUEST types, PENDING round trip, BeatIntent display. Field Manual #28 added. | `d172999` |
| WO-DIRECTOR-02 | **ACCEPTED** — 14/14 Gate E PASS, 0 regressions. All 7 contract changes delivered. invoke_director() orchestrates full pipeline. EV-033/EV-034 live. BeatHistory reconstructible from events. Field Manual #27 added. | `0834f4e` |
| WO-DIRECTOR-01 | **ACCEPTED** — 18/18 Gate D PASS, 0 regressions. 6/7 contract changes delivered. EV-033/EV-034 deferred (no invocation site — Phase 2). Field Manual #26 added. | `d38b988` |
| WO-ORACLE-03 | **ACCEPTED** — 24/24 Gate C PASS, 0 regressions. Oracle event reducer parallel to replay_runner. No EventLog modifications. Field Manual #25 added. | `6029236` |
| WO-ORACLE-02 | **ACCEPTED** — 23/23 Gate B PASS, 0 regressions. canonical.py updated to handle MappingProxyType via `Mapping` ABC. Field Manual #24 added. | `4245e38` |
| WO-ORACLE-01 | **ACCEPTED** — 22/22 Gate A PASS, no-backflow PASS, 0 regressions. Builder used `canonical_short_hash` for fact_id (defensible deviation from ambiguous spec). | `4c5526a` |
| WO-SMOKE-TEST-003 | **ACCEPTED** — 5 PASS, 7 FINDING (6 coverage gap + 1 schema gap), 0 CRASH | `4b3168f` |
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

1. **Dispatch WO-UI-01 to a builder.**

   [WO-UI-01_DISPATCH.md](pm_inbox/WO-UI-01_DISPATCH.md) — Table UI Phase 1: Client Bootstrap + Slice 0 + One PENDING Round Trip. Three.js + TypeScript + Vite in `client/`, 3 camera postures, PENDING/REQUEST handshake types, one end-to-end PENDING round trip over WebSocket, BeatIntent display on table surface. 7 contract changes. 10 Gate F tests + 0 regressions on Gates A-E.

### Previous Dispatches (All Accepted)

- ~~WO-DIRECTOR-02~~ — ACCEPTED (`0834f4e`). 14/14 Gate E. Field Manual #27 added.
- ~~WO-DIRECTOR-01~~ — ACCEPTED (`d38b988`). 18/18 Gate D. Field Manual #26 added.
- ~~WO-ORACLE-03~~ — ACCEPTED (`6029236`). 24/24 Gate C. Field Manual #25 added.
- ~~WO-ORACLE-02~~ — ACCEPTED (`4245e38`). 23/23 Gate B. Field Manual #24 added.
- ~~WO-ORACLE-01~~ — ACCEPTED (`4c5526a`). 22/22 Gate A. Field Manual #22-23 added.
- ~~WO-SMOKE-FUZZER~~ — ACCEPTED (`ac67327`)
- ~~WO-FUZZER-DETERMINISM-GATES~~ — ACCEPTED (`e128342`).
- ~~WO-ORACLE-SURVEY~~ — ACCEPTED (`7b4268f`).
- ~~WO-SMOKE-TEST-003~~ — ACCEPTED (`4b3168f`).

## Oracle Implementation Direction (Aegis Memo, 2026-02-18)

**THIN SPINE FIRST, then add organs one at a time.**

| Phase | Scope | Gate |
|---|---|---|
| **Phase 1: Oracle Spine** ← COMPLETE | FactsLedger, UnlockState, minimal StoryState. Canonical profile. | Gate A: store determinism — **22/22 PASS** |
| **Phase 2: WorkingSet** ← COMPLETE | Deterministic compiler pass from stores → WorkingSet bytes + PromptPack compiler | Gate B: cold boot byte-equality — **23/23 PASS** |
| **Phase 3: Compactions + Cold Boot** ← COMPLETE | Prove byte-equal rebuild from stores only | Gate C: cold boot + compaction repro + pin assert — **24/24 PASS** |

**Hard stops (must pin before or during Phase 1):** Hash algorithm, canonical JSON bytespec profile, mask_level/mask_matrix schema.

**One-line success:** Cold boot reconstructs same bytes, no backflow possible.

## Doctrine Adoption (2026-02-18)

**GT v12 adopted as product doctrine.** Subsystem memos (Oracle v5.2, UI v4, ImageGen v4) accepted as plans-under-GT. Audio pillar adopted on paper, deferred in code until BURST-001. See kernel for full adoption record.

**Build order:** ~~Smoke fuzzer~~ → ~~Oracle survey~~ → ~~Hooligan~~ → ~~Oracle Phase 1~~ → ~~Oracle Phase 2 (WorkingSet)~~ → ~~Oracle Phase 3 (Compactions)~~ **ORACLE COMPLETE** → ~~Director Phase 1~~ → ~~Director Phase 2 (Integration)~~ **DIRECTOR COMPLETE** → **UI Phase 1 (Table Surface)** ← CURRENT → UI Phase 2+ → Roleplay

**Doctrine files** (in `pm_inbox/doctrine/`):
- [DOCTRINE_01_FINAL_DELIVERABLE.txt](pm_inbox/doctrine/DOCTRINE_01_FINAL_DELIVERABLE.txt) — Anchor index + gap register
- [DOCTRINE_02_GOLDEN_TICKET_V12.txt](pm_inbox/doctrine/DOCTRINE_02_GOLDEN_TICKET_V12.txt) — Product doctrine
- [DOCTRINE_03_ORACLE_MEMO_V52.txt](pm_inbox/doctrine/DOCTRINE_03_ORACLE_MEMO_V52.txt) — Oracle subsystem spec
- [DOCTRINE_04_TABLE_UI_MEMO_V4.txt](pm_inbox/doctrine/DOCTRINE_04_TABLE_UI_MEMO_V4.txt) — UI spec
- [DOCTRINE_05_IMAGE_GEN_MEMO_V4.txt](pm_inbox/doctrine/DOCTRINE_05_IMAGE_GEN_MEMO_V4.txt) — Image gen spec
- [DOCTRINE_06_LENS_SPEC_V0.txt](pm_inbox/doctrine/DOCTRINE_06_LENS_SPEC_V0.txt) — Lens subsystem spec
- [DOCTRINE_07_SESSION_LIFECYCLE_V0.txt](pm_inbox/doctrine/DOCTRINE_07_SESSION_LIFECYCLE_V0.txt) — Session Lifecycle spec
- [DOCTRINE_08_DIRECTOR_SPEC_V0.txt](pm_inbox/doctrine/DOCTRINE_08_DIRECTOR_SPEC_V0.txt) — Director spec

## PM Action Queue — Doctrine Memo Formalization

**Source:** [MEMO_DOCTRINE_HOLES_ANSWER_PACKET.md](pm_inbox/reviewed/MEMO_DOCTRINE_HOLES_ANSWER_PACKET.md) — 8 formalized decisions from Aegis/Anvil (archived).

**Sequencing rule:** None of these block WO-ORACLE-01 (Phase 1). Lens memo must exist before WO-ORACLE-02 (Phase 2). Session lifecycle must exist before WO-ORACLE-03 (Phase 3). The rest follow the build order.

| # | Memo | Source Section | Blocks | Status |
|---|---|---|---|---|
| 1 | **Lens spec** (WorkingSet → PromptPack, mask enforcement) | §4 | WO-ORACLE-02 | **DONE** — [DOCTRINE_06_LENS_SPEC_V0.txt](pm_inbox/doctrine/DOCTRINE_06_LENS_SPEC_V0.txt) |
| 2 | **Session lifecycle spec** (save/load/cold-boot/resume) | §2 | WO-ORACLE-03 | **DONE** — [DOCTRINE_07_SESSION_LIFECYCLE_V0.txt](pm_inbox/doctrine/DOCTRINE_07_SESSION_LIFECYCLE_V0.txt) |
| 3 | **CampaignManifest spec** (intake, PDF compile) | §1 | Worldgen pipeline | PENDING |
| 4 | **Worldgen pipeline spec** (worldgen/sessiongen boundary) | §3 | Worldgen WO | PENDING |
| 5 | **Director spec** (beat selector, read-only) | §5 | Director WO | **DONE** — [DOCTRINE_08_DIRECTOR_SPEC_V0.txt](pm_inbox/doctrine/DOCTRINE_08_DIRECTOR_SPEC_V0.txt) |
| 6 | **Companion Mode + Teaching Nudges spec** | §6 + §7 | Companion WO | PENDING |

Packaging (§8) remains a lightweight "ship posture" doc — deferred until closer to distribution.

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
- **WO-ORACLE-01** — Oracle Spine: FactsLedger, UnlockState, StoryState, canonical JSON profile, Gate A (22/22 PASS)
- **WO-ORACLE-02** — WorkingSet compiler + PromptPack compiler + AllowedToSayEnvelope, Gate B (23/23 PASS)
- **WO-ORACLE-03** — SaveSnapshot + Compaction + CompactionRegistry + cold_boot(), Gate C (24/24 PASS)
- **WO-DIRECTOR-01** — Director Phase 1: BeatIntent + NudgeDirective + DirectorPolicy + DirectorPromptPack, Gate D (18/18 PASS)
- **WO-DIRECTOR-02** — Director Phase 2: BeatIntent→Lens integration + EV-033/EV-034 + BeatHistory.from_events(), Gate E (14/14 PASS)

## Active Operational Files

**Root** (6 files — cap: 10):
- [PM_BRIEFING_CURRENT.md](pm_inbox/PM_BRIEFING_CURRENT.md) — This file
- [REHYDRATION_KERNEL_LATEST.md](pm_inbox/REHYDRATION_KERNEL_LATEST.md) — PM rehydration block
- [README.md](pm_inbox/README.md) — Inbox hygiene rules
- [WO-UI-01_DISPATCH.md](pm_inbox/WO-UI-01_DISPATCH.md) — UI Phase 1 dispatch (transient — archives with verdict)
- [BURST_INTAKE_QUEUE.md](pm_inbox/BURST_INTAKE_QUEUE.md) — BURST-001 thru 004 (parked)
- [MEMO_SPARK_LLM_SELECTION.md](pm_inbox/MEMO_SPARK_LLM_SELECTION.md) — H2 blocker, parked

**Doctrine** (8 files in `pm_inbox/doctrine/` — permanent reference):
- DOCTRINE_01 through DOCTRINE_08 (see Doctrine files section above)

**Archived this cycle:** WO-DIRECTOR-01 + WO-DIRECTOR-02 dispatch + debrief → `pm_inbox/reviewed/archive_director/`. Previous Oracle/smoke/fuzzer artifacts in `pm_inbox/reviewed/archive_smoke_oracle/`. Dispositioned memos in `pm_inbox/reviewed/`.

## Persistent Files

- `README.md` — Inbox hygiene rules
- `PM_BRIEFING_CURRENT.md` — This file
- `REHYDRATION_KERNEL_LATEST.md` — PM rehydration block
