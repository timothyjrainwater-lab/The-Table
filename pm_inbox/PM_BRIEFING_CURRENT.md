# PM Briefing — Current

**Last updated:** 2026-02-19 (WO-SPARK-LLM-SELECTION ACCEPTED with findings. Qwen2.5 7B Instruct selected. 4 findings surfaced: GAP-B toolchain gap, tight budget margin, S4 load spikes, DLL directory fix. Dispatch + debrief archived.)

---

## Inbox

- **[READ] [MEMO_TTS_AUDIO_PIPELINE_ARCHITECTURE.md](pm_inbox/MEMO_TTS_AUDIO_PIPELINE_ARCHITECTURE.md)** — Full TTS pipeline reference. Remains in root while voice work is adjacent.
- **[READ] [MEMO_BUILDER_PREFLIGHT_CANARY.md](pm_inbox/MEMO_BUILDER_PREFLIGHT_CANARY.md)** — Builder preflight canary system. Script: `scripts/preflight_canary.py`. Log: `pm_inbox/PREFLIGHT_CANARY_LOG.md`.
- **[NEW] [MEMO_TABLE_VISION_SPATIAL_SPEC.md](pm_inbox/MEMO_TABLE_VISION_SPATIAL_SPEC.md)** — Table visual identity: recessed vault poker table, three camera postures, mood rules. Candidate for doctrine adoption. Parked until visual pass.

**Archived this pass (11 files):** DEBRIEF_WO-COMEDY-STINGERS-P1 + WO-COMEDY-STINGERS-P1_DISPATCH + MEMO_COMEDY_STINGER_REPO_MAPPING + MEMO_NPC_COMEDY_LOADOUT_SYSTEM → `reviewed/archive_comedy_stingers/`. MEMO_IMAGE_GEN_WALKTHROUGH + MEMO_TTS_MONOLOGUE_WALKTHROUGH + MEMO_TTS_GHOST_FOG_RESEARCH + MEMO_SPARK_LLM_SELECTION → `reviewed/`. WO-SPARK-LLM-SELECTION_DISPATCH + WO-SPARK-LLM-SELECTION_RESEARCH_PREP + DEBRIEF_WO-SPARK-LLM-SELECTION → `reviewed/archive_spark_llm/`.

## Stoplight: GREEN (infrastructure) / GREEN (integration)

5,978 unit tests pass (excluding pre-existing TTS/inbox failures). **Oracle Gate A: 22/22 PASS. Gate B: 23/23 PASS. Gate C: 24/24 PASS. Gate D: 18/18 PASS. Gate E: 14/14 PASS. Gate F: 10/10 PASS. Gate G: 22/22 PASS (incl. UI-G5 drift guards + UI-G6 zone authority + UI-G7 dice/handshake + UI-G8 protocol registry). Gate H: 16/16 PASS (TableMood + StyleCapsule + scene lifecycle + cold boot + compilation rules + boundary). Gate I: 13/13 PASS (comedy stinger validator + selector + bank integrity). No-backflow: PASS. Integration board clear.**

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
| WO-SPARK-LLM-SELECTION | **ACCEPTED with findings** — Research + evaluation WO (no code changes). 6/6 deliverables. Qwen2.5 7B Instruct (Q4_K_M) selected — only candidate to pass all 5 gates (5/5). Quality 24.0/25, load time 2.69s, VRAM 5,818 MB. Scope deviation: Qwen3→Qwen2.5, Gemma3→Gemma2 (llama-cpp-python 0.3.4 arch gap — defensible). Radar compliant. **4 findings:** (1) GAP-B HIGH — llama-cpp-python blocks Qwen3/Gemma3, need VS Build Tools; (2) Budget margin 0.55s — Chatterbox swap times estimated not measured; (3) S4 load spikes in loops 2-3; (4) GAP-C DLL directory fix needed. Eval infra (`scripts/spark_eval.py`) retained for Qwen3 re-eval. | (research WO, no commit) |
| WO-COMEDY-STINGERS-P1 | **ACCEPTED** — 162/162 gate tests (149 existing + 13 new Gate I). 0 regressions (5,978 suite). 6/6 deliverables landed. Frozen `Stinger` dataclass with `__post_init__` immutability, 3 public functions (validate/select/render), 21 stingers (3×7 archetypes), 13 gate tests. Immutability gate caught mutable containers — fixed via `__post_init__`. Duration ceiling (6.0s) enforces staccato rhythm as designed. Builder Radar fully compliant. Field Manual #35 needed (immutability gate). | `e4ac5c1` |
| WO-DIRECTOR-03 | **ACCEPTED** — 149/149 gate tests (133 existing + 16 new Gate H). 0 regressions (5,893 suite). 7/7 contract changes delivered (Change 5 scene lifecycle already existed). TableMood store in `aidm/oracle/table_mood.py`, StyleCapsule in `aidm/lens/style_capsule.py`, DirectorPromptPack extended with optional style_capsule, pacing modulation via `_resolve_pacing_mode()`, cold_boot reducer extended for mood_observation events. Field Manual #34 added. | `9705298` |
| WO-UI-04 | **ACCEPTED** — 133/133 gate tests (130 existing + 3 new UI-G8). 0 regressions (5,877 suite). 6/6 contract changes delivered. `RollResult` frozen dataclass in new `ws_protocol.py`, `MESSAGE_REGISTRY` + `parse_message()` dispatcher, wildcard handler migrated to typed, UI-G8 gates (protocol registry, roll roundtrip, wildcard removal). Builder Radar fully compliant (first since rejection gate codified). Field Manual #33 added. | `db66426` |
| WO-UI-03 | **ACCEPTED** — 130/130 gate tests (127 existing + 3 new UI-G7). 0 regressions (5,669 suite). 6/6 contract changes delivered. DiceObject d20, dice tray/tower zones, PENDING_ROLL→CONFIRMED handshake, deterministic result-reveal, fidget idle animation. Invented `roll_result` message type (not yet formalized in ws_protocol.py — Field Manual #32). Builder Radar present but format non-compliant (substantive content, wrong labels — enforcement tightened for next WO). Field Manual #32 added. | `f149d2d` |
| WO-UI-ZONE-AUTHORITY | **ACCEPTED** — 127/127 gate tests (124 existing + 3 new UI-G6). 0 regressions (5,871 suite). 6/6 contract changes delivered. zones.json single source of truth, Python loader, TS import, validate_zone_position → bool, zone parity gate, camera frustum gate. Two defensible divergences: color field added to schema, tsconfig rootDir removed for cross-root import. Builder Radar incomplete (first WO under new format — tolerated). Field Manual #29 updated, #31 added. | `40fa32a` |
| WO-UI-DRIFT-GUARD | **ACCEPTED** — 3/3 UI-G5 drift guard tests, Gate G 13/13 PASS, 0 regressions (124/124 total). No production code changes. No canonical path, no backflow imports, no teaching strings — all confirmed. Field Manual #30 added. `validate_zone_position` returns `Optional[str]` internally (noted, not user-facing). | `04058c3` |
| WO-UI-02 | **ACCEPTED** — 10/10 Gate G PASS (core contracts), 0 regressions (121/121 total). 8/8 contract changes delivered. TableObject base system, pick/drag/drop, card as first object, zone constraints, keyboard path. 3 UI-G5 drift guard tests not implemented — invariants likely hold but unguarded. Field Manual #29 added. **Note:** Next WO touching `aidm/ui/table_objects.py` must include drift guard tests. | `7449bc5` |
| WO-UI-01 | **ACCEPTED** — 10/10 Gate F PASS, 0 regressions (111/111 total). 7/7 contract changes delivered. Frontend bootstrap (Three.js+TS+Vite), 3 camera postures, PENDING/REQUEST types, PENDING round trip, BeatIntent display. Field Manual #28 added. | `6237845` |
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

**SPARK LLM SELECTION COMPLETE.** Qwen2.5 7B Instruct (Q4_K_M) selected as interim Spark cage model. Sequential VRAM posture confirmed. Path B (batch-per-turn) is the operational architecture.

**Before BURST-001, two things must be measured (not estimated):**
1. **Chatterbox swap timing** — Actual load time and time-to-first-audio under sequential lifecycle. The 8.0s stall budget uses 1.5s estimates for both phases. If actual is 2.0s+, the budget busts. (FINDING-2 from verdict.)
2. **llama-cpp-python upgrade path** — Install VS Build Tools on command deck and compile llama-cpp-python 0.3.16 from source. This unblocks Qwen3 8B and Gemma 3 12B evaluation. (GAP-B from debrief.)

**Integration follow-up (WO scope):** Wire Qwen2.5 into Spark cage — models.yaml entry, DLL directory fix (GAP-C), `n_ctx=2048` for narration, sequential lifecycle manager (load/unload orchestration). This is BURST-001 scope or a pre-BURST wiring WO.

**GAP-A (low priority):** `dm_persona.py:83` references `NarrativeBrief` without importing it. Runtime-functional (duck typing), static analysis only.

**Planned sequence:** ~~Director Phase 3~~ → ~~Comedy Stingers Phase 1~~ (ACCEPTED) → ~~Spark LLM Selection~~ (ACCEPTED) → **BURST-001**

### Previous Dispatches (All Accepted)

- ~~WO-SPARK-LLM-SELECTION~~ — ACCEPTED with findings (research WO, no commit). Qwen2.5 7B Instruct selected (5/5 gates). Sequential VRAM confirmed. Eval infra retained. 4 findings surfaced. **SPARK LLM SELECTION COMPLETE.**
- ~~WO-COMEDY-STINGERS-P1~~ — ACCEPTED (`e4ac5c1`). 162/162 gate tests (149 + 13 Gate I). Frozen Stinger schema, 21 stingers (3×7), validate/select/render, immutability gate caught and fixed. Builder Radar fully compliant. Field Manual #35 needed.
- ~~WO-DIRECTOR-03~~ — ACCEPTED (`9705298`). 149/149 gate tests. TableMood store, StyleCapsule, Director pacing modulation, cold_boot mood reducer, Gate H 16/16. Field Manual #34 added. Builder Radar fully compliant. **DIRECTOR PHASE 3 COMPLETE.**
- ~~WO-UI-04~~ — ACCEPTED (`db66426`). 133/133 gate tests. `RollResult` frozen dataclass, message registry, typed handler migration, UI-G8 gates. Field Manual #33 added. Builder Radar fully compliant.
- ~~WO-UI-03~~ — ACCEPTED (`f149d2d`). 130/130 gate tests. Dice tray/tower, PENDING_ROLL handshake, UI-G7 gates. Field Manual #32 added.
- ~~WO-UI-ZONE-AUTHORITY~~ — ACCEPTED (`40fa32a`). 127/127 gate tests. zones.json single source of truth, 3 UI-G6 gates. Field Manual #29 updated, #31 added.
- ~~WO-UI-DRIFT-GUARD~~ — ACCEPTED (`04058c3`). 3/3 UI-G5 drift guards. Gate G 13/13. Field Manual #30 added.
- ~~WO-UI-01~~ — ACCEPTED (`6237845`). 10/10 Gate F. Field Manual #28 added.
- ~~WO-DIRECTOR-02~~ — ACCEPTED (`0834f4e`). 14/14 Gate E. Field Manual #27 added.
- ~~WO-DIRECTOR-01~~ — ACCEPTED (`d38b988`). 18/18 Gate D. Field Manual #26 added.
- ~~WO-ORACLE-03~~ — ACCEPTED (`6029236`). 24/24 Gate C. Field Manual #25 added.
- ~~WO-ORACLE-02~~ — ACCEPTED (`4245e38`). 23/23 Gate B. Field Manual #24 added.
- ~~WO-ORACLE-01~~ — ACCEPTED (`4c5526a`). 22/22 Gate A. Field Manual #22-23 added.
- ~~WO-SMOKE-FUZZER~~ — ACCEPTED (`ac67327`)
- ~~WO-FUZZER-DETERMINISM-GATES~~ — ACCEPTED (`e128342`).
- ~~WO-ORACLE-SURVEY~~ — ACCEPTED (`7b4268f`).
- ~~WO-SMOKE-TEST-003~~ — ACCEPTED (`4b3168f`).

## Oracle Implementation Direction (Aegis/GPT Memo, 2026-02-18)

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

**Build order:** ~~Smoke fuzzer~~ → ~~Oracle survey~~ → ~~Hooligan~~ → ~~Oracle Phase 1~~ → ~~Oracle Phase 2 (WorkingSet)~~ → ~~Oracle Phase 3 (Compactions)~~ **ORACLE COMPLETE** → ~~Director Phase 1~~ → ~~Director Phase 2 (Integration)~~ → ~~UI Phase 1 (Table Surface)~~ → ~~UI Phase 2 (TableObject + Drag)~~ → ~~UI Drift Guards~~ → ~~UI Zone Authority~~ → ~~UI Phase 3 (Dice Tray + Tower)~~ → ~~UI Phase 4 (Protocol Formalization)~~ **UI PHASE 4 COMPLETE** → ~~Director Phase 3 (TableMood + StyleCapsule)~~ **DIRECTOR PHASE 3 COMPLETE** → ~~Comedy Stingers Phase 1~~ **COMEDY STINGERS P1 COMPLETE** → ~~Spark LLM Selection~~ **SPARK LLM SELECTION COMPLETE** → **BURST-001**

**Doctrine files** (in `pm_inbox/doctrine/` — 10 files, permanent reference):

*Subsystem specs (SPEC):*
- [DOCTRINE_01_FINAL_DELIVERABLE.txt](pm_inbox/doctrine/DOCTRINE_01_FINAL_DELIVERABLE.txt) — `SPEC` Anchor index + gap register
- [DOCTRINE_02_GOLDEN_TICKET_V12.txt](pm_inbox/doctrine/DOCTRINE_02_GOLDEN_TICKET_V12.txt) — `SPEC` Product doctrine
- [DOCTRINE_03_ORACLE_MEMO_V52.txt](pm_inbox/doctrine/DOCTRINE_03_ORACLE_MEMO_V52.txt) — `SPEC` Oracle subsystem
- [DOCTRINE_04_TABLE_UI_MEMO_V4.txt](pm_inbox/doctrine/DOCTRINE_04_TABLE_UI_MEMO_V4.txt) — `SPEC` UI subsystem
- [DOCTRINE_05_IMAGE_GEN_MEMO_V4.txt](pm_inbox/doctrine/DOCTRINE_05_IMAGE_GEN_MEMO_V4.txt) — `SPEC` Image gen subsystem
- [DOCTRINE_06_LENS_SPEC_V0.txt](pm_inbox/doctrine/DOCTRINE_06_LENS_SPEC_V0.txt) — `SPEC` Lens subsystem
- [DOCTRINE_07_SESSION_LIFECYCLE_V0.txt](pm_inbox/doctrine/DOCTRINE_07_SESSION_LIFECYCLE_V0.txt) — `SPEC` Session lifecycle
- [DOCTRINE_08_DIRECTOR_SPEC_V0.txt](pm_inbox/doctrine/DOCTRINE_08_DIRECTOR_SPEC_V0.txt) — `SPEC` Director subsystem

*Governance (GOV):*
- [DOCTRINE_09_SEVEN_WISDOM.txt](pm_inbox/doctrine/DOCTRINE_09_SEVEN_WISDOM.txt) — `GOV` Foundational decision principles (Anvil + Aegis, 2026-02-19)

*Process (PROC):*
- [DOCTRINE_10_SEVEN_WISDOM_DEBRIEF.txt](pm_inbox/doctrine/DOCTRINE_10_SEVEN_WISDOM_DEBRIEF.txt) — `PROC` Research WO debrief format — 7 slots + routing tags + 4-line Radar (2026-02-19)

## PM Action Queue — Doctrine Memo Formalization

**Source:** [MEMO_DOCTRINE_HOLES_ANSWER_PACKET.md](pm_inbox/reviewed/MEMO_DOCTRINE_HOLES_ANSWER_PACKET.md) — 8 formalized decisions from Aegis (GPT)/Anvil (archived).

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
- **WO-UI-01** — Table UI Phase 1: Client Bootstrap + Slice 0 + One PENDING Round Trip, Gate F (10/10 PASS)
- **WO-UI-02** — Table UI Phase 2: TableObject Base System + Pick/Drag/Drop, Gate G (10/10 PASS)
- **WO-UI-DRIFT-GUARD** — 3 UI-G5 drift guard tests, Gate G now 13/13 PASS, total 124 gate tests
- **WO-UI-ZONE-AUTHORITY** — zones.json single source of truth, validate_zone_position → bool, 3 UI-G6 gates, Gate G now 16/16 PASS, total 127 gate tests
- **WO-UI-03** — Dice tray + dice tower + PENDING_ROLL handshake, 3 UI-G7 gates, Gate G now 19/19 PASS, total 130 gate tests
- **WO-UI-04** — WebSocket protocol formalization + roll_result freeze, 3 UI-G8 gates, Gate G now 22/22 PASS, total 133 gate tests
- **WO-DIRECTOR-03** — Director Phase 3: TableMood + StyleCapsule + pacing modulation + cold_boot mood reducer, 16 Gate H tests, total 149 gate tests
- **WO-COMEDY-STINGERS-P1** — Comedy stinger content subsystem: frozen Stinger schema, 21 stingers (3×7 archetypes), validate/select/render, 13 Gate I tests, total 162 gate tests
- **WO-SPARK-LLM-SELECTION** — Local LLM selection for Spark cage: Qwen2.5 7B Instruct (Q4_K_M) selected, 5/5 gates, sequential VRAM posture confirmed, eval infra retained for Qwen3 re-eval

## Active Operational Files

**Root** (8 files — 2 under cap):
- [PM_BRIEFING_CURRENT.md](pm_inbox/PM_BRIEFING_CURRENT.md) — This file
- [REHYDRATION_KERNEL_LATEST.md](pm_inbox/REHYDRATION_KERNEL_LATEST.md) — PM rehydration block
- [README.md](pm_inbox/README.md) — Inbox hygiene rules
- [BURST_INTAKE_QUEUE.md](pm_inbox/BURST_INTAKE_QUEUE.md) — BURST-001 thru 004 (parked)
- [MEMO_TTS_AUDIO_PIPELINE_ARCHITECTURE.md](pm_inbox/MEMO_TTS_AUDIO_PIPELINE_ARCHITECTURE.md) — TTS pipeline reference
- [MEMO_BUILDER_PREFLIGHT_CANARY.md](pm_inbox/MEMO_BUILDER_PREFLIGHT_CANARY.md) — Preflight canary system
- [MEMO_TABLE_VISION_SPATIAL_SPEC.md](pm_inbox/MEMO_TABLE_VISION_SPATIAL_SPEC.md) — Table vision (parked until visual pass)
- [PREFLIGHT_CANARY_LOG.md](pm_inbox/PREFLIGHT_CANARY_LOG.md) — Builder preflight log

**Note:** Root is at 8 files. 2 slots available for BURST-001 dispatch + debrief.

**Doctrine** (10 files in `pm_inbox/doctrine/` — permanent reference, type-labeled SPEC/GOV/PROC):
- DOCTRINE_01 through DOCTRINE_10 (see Doctrine files section above)

**Archived this cycle:** WO-COMEDY-STINGERS-P1 dispatch + debrief + MEMO_COMEDY_STINGER_REPO_MAPPING + MEMO_NPC_COMEDY_LOADOUT_SYSTEM → `pm_inbox/reviewed/archive_comedy_stingers/`. MEMO_IMAGE_GEN_WALKTHROUGH + MEMO_TTS_MONOLOGUE_WALKTHROUGH + MEMO_TTS_GHOST_FOG_RESEARCH + MEMO_SPARK_LLM_SELECTION → `pm_inbox/reviewed/`. WO-UI-* dispatch + debrief → `archive_ui/`. WO-DIRECTOR-* → `archive_director/`. Oracle/smoke/fuzzer → `archive_smoke_oracle/`. Legacy → `legacy_pm_inbox/`.

## Persistent Files

- `README.md` — Inbox hygiene rules
- `PM_BRIEFING_CURRENT.md` — This file
- `REHYDRATION_KERNEL_LATEST.md` — PM rehydration block
