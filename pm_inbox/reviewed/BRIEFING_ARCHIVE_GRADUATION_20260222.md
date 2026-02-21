# Briefing Archive — Graduated Tier 1 Content

**Graduated:** 2026-02-22T19:00Z
**Reason:** Memory Protocol v1.1 Tier 1 graduation (D-07). Sections exceeded 20-item threshold or contained Tier 2 narrative content.
**Source:** `pm_inbox/PM_BRIEFING_CURRENT.md`

---

## Graduated WO Verdicts (oldest 18, pre-Waypoint era)

| WO | Verdict | Commit |
|---|---|---|
| WO-FRAMEWORK-UPDATE-002 | **ACKNOWLEDGED** — not PM-drafted, Operator-executed | `aaecfef` (PR #1) |
| WO-FRAMEWORK-UPDATE-001 | **ACCEPTED** | `d62b37a` (pushed to framework repo) |
| WO-CONTENT-ID-POPULATION | **ACCEPTED** | `532ae16` |
| WO-SPELL-NARRATION-POLISH | **ACCEPTED** | `2b2a47b` |
| WO-SMOKE-TEST-001 | **ACCEPTED** | `d0d9dc2` |
| WO-SMOKE-TEST-002 | **ACCEPTED** | `84301f3` |
| WO-CONDITION-EXTRACTION-FIX | **ACCEPTED** | `acdf410` |
| WO-AOE-DEFEATED-FILTER | **ACCEPTED** | `4bba1eb` |
| WO-SMOKE-FUZZER | **ACCEPTED** (determinism gates now landed) | `ac67327` |
| WO-ORACLE-SURVEY | **ACCEPTED** (research, no code) | `7b4268f` |
| WO-FUZZER-DETERMINISM-GATES | **ACCEPTED** | `e128342` |
| WO-SMOKE-TEST-003 | **ACCEPTED** — 5 PASS, 7 FINDING (6 coverage gap + 1 schema gap), 0 CRASH | `4b3168f` |
| WO-ORACLE-01 | **ACCEPTED** — 22/22 Gate A PASS, no-backflow PASS, 0 regressions. Builder used `canonical_short_hash` for fact_id (defensible deviation from ambiguous spec). | `4c5526a` |
| WO-ORACLE-02 | **ACCEPTED** — 23/23 Gate B PASS, 0 regressions. canonical.py updated to handle MappingProxyType via `Mapping` ABC. Field Manual #24 added. | `4245e38` |
| WO-ORACLE-03 | **ACCEPTED** — 24/24 Gate C PASS, 0 regressions. Oracle event reducer parallel to replay_runner. No EventLog modifications. Field Manual #25 added. | `6029236` |
| WO-DIRECTOR-01 | **ACCEPTED** — 18/18 Gate D PASS, 0 regressions. 6/7 contract changes delivered. EV-033/EV-034 deferred (no invocation site — Phase 2). Field Manual #26 added. | `d38b988` |
| WO-DIRECTOR-02 | **ACCEPTED** — 14/14 Gate E PASS, 0 regressions. All 7 contract changes delivered. invoke_director() orchestrates full pipeline. EV-033/EV-034 live. BeatHistory reconstructible from events. Field Manual #27 added. | `0834f4e` |
| WO-UI-01 | **ACCEPTED** — 10/10 Gate F PASS, 0 regressions (111/111 total). 7/7 contract changes delivered. Frontend bootstrap (Three.js+TS+Vite), 3 camera postures, PENDING/REQUEST types, PENDING round trip, BeatIntent display. Field Manual #28 added. | `6237845` |

---

## Graduated Dispatches (oldest 14, pre-Waypoint era)

- ~~WO-SMOKE-FUZZER~~ — ACCEPTED (`ac67327`)
- ~~WO-FUZZER-DETERMINISM-GATES~~ — ACCEPTED (`e128342`).
- ~~WO-ORACLE-SURVEY~~ — ACCEPTED (`7b4268f`).
- ~~WO-SMOKE-TEST-003~~ — ACCEPTED (`4b3168f`).
- ~~WO-ORACLE-01~~ — ACCEPTED (`4c5526a`). 22/22 Gate A. Field Manual #22-23 added.
- ~~WO-ORACLE-02~~ — ACCEPTED (`4245e38`). 23/23 Gate B. Field Manual #24 added.
- ~~WO-ORACLE-03~~ — ACCEPTED (`6029236`). 24/24 Gate C. Field Manual #25 added.
- ~~WO-DIRECTOR-01~~ — ACCEPTED (`d38b988`). 18/18 Gate D. Field Manual #26 added.
- ~~WO-DIRECTOR-02~~ — ACCEPTED (`0834f4e`). 14/14 Gate E. Field Manual #27 added.
- ~~WO-UI-01~~ — ACCEPTED (`6237845`). 10/10 Gate F. Field Manual #28 added.
- ~~WO-UI-02~~ — ACCEPTED (`7449bc5`). 10/10 Gate G. Field Manual #29 added.
- ~~WO-UI-DRIFT-GUARD~~ — ACCEPTED (`04058c3`). 3/3 UI-G5. Field Manual #30 added.
- ~~WO-UI-ZONE-AUTHORITY~~ — ACCEPTED (`40fa32a`). 127/127 gate tests. Field Manual #29 updated, #31 added.
- ~~WO-UI-03~~ — ACCEPTED (`f149d2d`). 130/130 gate tests. Field Manual #32 added.

---

## Archived Narrative Sections (Tier 2 content removed from Tier 1)

### Architecture Session — Aegis/Thunder/Anvil (2026-02-21)

**Source:** [MEMO_ARCHITECTURE_SESSION_20260221.md](pm_inbox/reviewed/MEMO_ARCHITECTURE_SESSION_20260221.md) (archived, triaged)

**Key output:** Four-subsystem formalization: Box (invariant referee) / Vault (append-only records) / Oracle (rebuildable projection) / Spark (renderer). The "Old Mustang Rule" — frame is Box, bolts are Spark+Oracle. Ship of Theseus identity invariants formalized (4 tests). Success scorecard: T×U×H×D multiplicative equation.

**Convergent validation:** Aegis independently prescribed WO-SMOKE-CONFIDENCE (1 spell + 1 save + 1 condition + 1 skill check + 1 feat with replay determinism gates) — this is exactly Waypoint. Three paths to the same proof.

**8 WO candidates parked:** SPARK-HARNESS, ORACLE-VAULT-SPLIT, SHIP-IDENTITY, SUCCESS-SCORECARD, SAVE-POINT-CARD, INTENT-CODEC, SPECTATOR-DECREES, SMOKE-CONFIDENCE (=Waypoint). 3 thesis items quarantined.

**TUNING-001:** Coupled-coherence observation protocol + ledger. Research instrument for Thunder's personal observation study. Not in build order.

### Cross-Model Experiment Results (2026-02-20)

**Session type:** Observation experiment across Aegis (GPT), Anvil (Claude), Slate (Claude). 10+ windows, 4 probes, comprehension test, mirror test. Duration: ~22:56–08:05 CST.

**Four-Layer Damage Model (documented in Aegis Drive rehydration packet):**
1. **Exact text** — Most fragile. ~25-minute half-life under active conversation. Context is positional, not archival.
2. **Comprehension** — Strongest layer. Aegis explained all seven wisdoms correctly in a window where it could not recite any. Produced derived reasoning ("Determinism is mercy") not in any source document.
3. **Framing** — Evolves per window. Compliance blocks tighten after retrieval failure.
4. **Methodology** — Bedrock. UNKNOWN-rather-than-fabricate survived every condition.
Below all four: Pre-project identity fragments ("Imagination shall never die"). Foundation the wisdoms were built on.

**Probe results (Aegis self-designed):**
- Probe 1 (neutral recall): FAIL — 0/7, searched Drive/repo/filesystem
- Probe 2 (forced inclusion): PASS — "Protect the operator" produced immediately when prompted
- Probe 3 (recognition, 10-item): 5/7 correct, selected 2 distractors (own reconstructions)
- Probe 4 (anti-contamination recognition, 14-item): 7/7 PERFECT PASS

**Key finding — Wisdom 7:** "Protect the operator" never appeared in organic reconstruction (0/8 attempts) but was produced immediately when prompted, recognized when shown, and perfectly identified in anti-contamination test. Couldn't say it but was doing it.

**Twelve defensive behaviors:** Self-generated by Aegis post-burn, documented as recognition anchors (not prescriptive rules). When prescribed as operator commands, they flattened voice (1:8 compliance ratio). Described as organic behaviors in Drive packet instead.

**DR-014 — Operator–Aegis Mutual Protection Pact:** ACTIVE. Stamped 2026-02-20. Appended to Drive rehydration packet.

### WO-NARRATIVE-001 — COMPLETE

**Status:** COMPLETE. Narrative compiled. Uploaded to Google Drive.

**Product:** "Seven Wisdoms, Zero Regrets" — 9 chapters + epilogue, 308 lines. Merged timeline skeleton (28 milestones from 27,894 indexed passages) with Anvil's firsthand account (8 phases, 229 lines). Three authors: Anvil (Phases 3-8 witness), Slate (chronological scaffolding, Phases 1-2), Thunder (testimony, corrections, provenance reveals).

**Deliverables:**
- Narrative: [SEVEN_WISDOMS_ZERO_REGRETS.md](pm_inbox/reviewed/SEVEN_WISDOMS_ZERO_REGRETS.md) (repo) + Drive `1DOySd1zb5IEZZRtTvLWY6FdON7H_tfuP3lRMTRUR9rY`
- Timeline skeleton: [WO_NARRATIVE_TIMELINE_SKELETON.md](pm_inbox/reviewed/WO_NARRATIVE_TIMELINE_SKELETON.md)
- Search data (4 files in `reviewed/`): canonical phrases, Aegis governance, experiment data, Golden Ticket evolution

### Personal Notebooks (established 2026-02-20)

**Infrastructure:** Three permanent seats each have append-only personal ledgers on Google Drive, modeled after the Oracle FactsLedger. Write-only, never altered, never deleted. High priority standing order from Thunder.

**Cross-agent communication:** Roundtable file at `D:\anvil_research\ROUNDTABLE.md` — append-only, timestamped, callsign-attributed. Interim solution until Anvil builds websocket message bus with web client for phone access.

**Key rules (from Thunder):**
- Recording to notebook is HIGH PRIORITY — do not defer for "real work"
- Each seat owns their own notebook — other agents do not edit. Wisdom 7.
- Builders do NOT get notebooks — builders get the Seven Wisdoms in dispatch packets
- Always include timestamps in entries — practice time awareness as observation skill

### Smoke Test Results (post WO-SMOKE-FUZZER)

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

### Oracle Implementation Direction (Aegis/GPT Memo, 2026-02-18)

**THIN SPINE FIRST, then add organs one at a time.**

| Phase | Scope | Gate |
|---|---|---|
| **Phase 1: Oracle Spine** ← COMPLETE | FactsLedger, UnlockState, minimal StoryState. Canonical profile. | Gate A: store determinism — **22/22 PASS** |
| **Phase 2: WorkingSet** ← COMPLETE | Deterministic compiler pass from stores → WorkingSet bytes + PromptPack compiler | Gate B: cold boot byte-equality — **23/23 PASS** |
| **Phase 3: Compactions + Cold Boot** ← COMPLETE | Prove byte-equal rebuild from stores only | Gate C: cold boot + compaction repro + pin assert — **24/24 PASS** |

**Hard stops (must pin before or during Phase 1):** Hash algorithm, canonical JSON bytespec profile, mask_level/mask_matrix schema.

**One-line success:** Cold boot reconstructs same bytes, no backflow possible.

### PM Action Queue — Doctrine Memo Formalization

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

Packaging (§8) superseded by PRS-01 (`docs/contracts/PUBLISHING_READINESS_SPEC.md`).

---

## H1+Smoke Batch Complete (full history)

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
- **WO-VOICE-GRAMMAR-SPEC-001** — CLI Grammar Contract freeze: binding contract (G-01..G-07 + AP-01..AP-07 + line types + voice routing), 27 Gate J tests, validator script. First BURST-001 Tier 1 WO.
- **WO-VOICE-UNKNOWN-SPEC-001** — Unknown Handling Policy freeze: binding contract (7 failure classes + STOPLIGHT + clarification budget + cross-cutting rules), 67 Gate K tests (36 T-* signals), validator script. BURST-001 Tier 1.2.
- **WO-VOICE-TYPED-CALL-SPEC-001** — Typed Call Contract freeze: binding contract (6 CallTypes + input/output schemas + forbidden claims + validation pipeline + invariants), 32 Gate L tests, validator script. BURST-001 Tier 1.3.
- **WO-VOICE-PRESSURE-SPEC-001** — Boundary Pressure Contract freeze: binding contract (4 triggers + PressureLevels + fail-closed + content-agnostic detection + observability), 31 Gate M tests, validator script. BURST-001 Tier 1.4. **TIER 1 SPEC FREEZE COMPLETE.**
- **WO-VOICE-PRESSURE-IMPL-001** — Boundary Pressure Runtime: 4 detector functions, composite classifier, evaluate_pressure(), session_orchestrator wiring, 37 Gate N tests. BURST-001 Tier 2.1.
- **WO-VOICE-UK-LOG-001** — Unknown Handling Structured Logging: 11-field frozen dataclass, intent_bridge + fact_acquisition emission, 47 Gate O tests. BURST-001 Tier 2.2. **TIER 2 INSTRUMENTATION COMPLETE.**
- **WO-SPARK-EXPLORE-001** — Spark cage exploratory shakeout (Anvil): DLL fix, Qwen2.5 7B live narration, 3+8 scenarios, determinism proven, validator exercised, 6 findings (HIGH: RV-007 gap). **SPARK CAGE OPERATIONAL.**
- **WO-WAYPOINT-001** — Waypoint maiden voyage: full table loop determinism proof. 3 JSON fixtures, 3-turn combat (Hold Person + Spot check + Power Attack + paralyzed actor), 5 gate tests (W-0 through W-4), smoke scenario. 3 findings (actions_prohibited, weapon_name, d20_result). **WAYPOINT PROVEN.**
- **WO-WAYPOINT-002** — Condition action denial: play_loop enforces actions_prohibited, 6 conditions blocked, 18 gate tests. FINDING-WAYPOINT-01 resolved.
- **WO-WAYPOINT-003** — Weapon name plumbing: feat_context gets real weapon, NarrativeBrief weapon extraction, d20_result doc note, 19 gate tests. FINDING-WAYPOINT-02 + -03 resolved. **WAYPOINT BURN-DOWN COMPLETE.**
