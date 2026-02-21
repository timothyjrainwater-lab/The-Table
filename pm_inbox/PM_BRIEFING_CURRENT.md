# PM Briefing — Current

**Last updated:** 2026-02-21 18:30 CST-CN (Architecture session memo triaged — 8 WO candidates parked, WO-SMOKE-CONFIDENCE confirmed as Waypoint convergence. TUNING-001 protocol + ledger filed. Handoff archived. Root at 11. Waypoint burn-down ready for dispatch.)

---

## Inbox

- **[READ] [MEMO_TTS_AUDIO_PIPELINE_ARCHITECTURE.md](pm_inbox/MEMO_TTS_AUDIO_PIPELINE_ARCHITECTURE.md)** — Full TTS pipeline reference. Remains in root while voice work is adjacent.
- **[READ] [MEMO_BUILDER_PREFLIGHT_CANARY.md](pm_inbox/MEMO_BUILDER_PREFLIGHT_CANARY.md)** — Builder preflight canary system. Script: `scripts/preflight_canary.py`. Log: `pm_inbox/PREFLIGHT_CANARY_LOG.md`.
- **[READ] [TUNING_001_PROTOCOL.md](pm_inbox/TUNING_001_PROTOCOL.md)** — TUNING-001 coupled-coherence observation protocol. ABAB design, sham-channel discriminator, two hypotheses (dynamical systems vs new physics). Aegis-authored, 77s thinking trace. Research instrument, not project code.
- **[READ] [TUNING_001_LEDGER.md](pm_inbox/TUNING_001_LEDGER.md)** — TUNING-001 session ledger + analysis framework. Signal signatures SIG-ARRIVAL-01, SIG-MEADOW-01. Empty ledger ready for data. Companion to protocol.
- ~~MEMO_ARCHITECTURE_SESSION_20260221~~ — ARCHIVED to `reviewed/`. Triaged: 8 WO candidates parked (SPARK-HARNESS, ORACLE-VAULT-SPLIT, SHIP-IDENTITY, SUCCESS-SCORECARD, SMOKE-CONFIDENCE=Waypoint, SAVE-POINT-CARD, INTENT-CODEC, SPECTATOR-DECREES). 3 thesis items correctly quarantined. Aegis's WO-SMOKE-CONFIDENCE independently prescribed exactly what Waypoint already proved — convergent validation.
- ~~MEMO_TABLE_VISION_SPATIAL_SPEC~~ — ARCHIVED to `reviewed/`. Parked until visual pass.
- ~~MEMO_DARK_FACTORY_PATTERNS~~ — ARCHIVED to `reviewed/`. Parked.
- ~~MEMO_SPARK_ANVIL_HARNESS~~ — ARCHIVED to `reviewed/`. Parked.

**Contracts:**
- **[DRAFTED] [PUBLISHING_READINESS_SPEC.md](docs/contracts/PUBLISHING_READINESS_SPEC.md)** — PRS-01: 9 publish gates (P1-P9), RC evidence packet, allow/blocklist, license ledger, offline guarantee, IP hygiene, privacy posture, donation policy. Aegis audit consumed → `pm_inbox/reviewed/MEMO_PRS01_AEGIS_AUDIT.md`. 3 binary decisions resolved by Thunder. Parallel to BURST-001.

**Archived this pass (15 files):** Previous: DEBRIEF_WO-COMEDY-STINGERS-P1 + WO-COMEDY-STINGERS-P1_DISPATCH + MEMO_COMEDY_STINGER_REPO_MAPPING + MEMO_NPC_COMEDY_LOADOUT_SYSTEM → `reviewed/archive_comedy_stingers/`. MEMO_IMAGE_GEN_WALKTHROUGH + MEMO_TTS_MONOLOGUE_WALKTHROUGH + MEMO_TTS_GHOST_FOG_RESEARCH + MEMO_SPARK_LLM_SELECTION + MEMO_STT_CLEANUP_LAYER → `reviewed/`. WO-SPARK-LLM-SELECTION_DISPATCH + WO-SPARK-LLM-SELECTION_RESEARCH_PREP + DEBRIEF_WO-SPARK-LLM-SELECTION → `reviewed/archive_spark_llm/`. This pass: HANDOVER_ANVIL_20260219 + HANDOVER_ANVIL_20260219_EVE + AEGIS_REHYDRATION_PACKET_20260220 + MEMO_NATE_JONES_SEVEN_WISDOMS_CROSSWALK → `reviewed/`.

## Stoplight: GREEN (infrastructure) / GREEN (integration)

5,997 unit tests pass + 31 new WO-WAYPOINT-001 tests (6,028 total, excluding pre-existing TTS/inbox failures). **Oracle Gate A: 22/22 PASS. Gate B: 23/23 PASS. Gate C: 24/24 PASS. Gate D: 18/18 PASS. Gate E: 14/14 PASS. Gate F: 10/10 PASS. Gate G: 22/22 PASS (incl. UI-G5 drift guards + UI-G6 zone authority + UI-G7 dice/handshake + UI-G8 protocol registry). Gate H: 16/16 PASS (TableMood + StyleCapsule + scene lifecycle + cold boot + compilation rules + boundary). Gate I: 13/13 PASS (comedy stinger validator + selector + bank integrity). Gate J: 27/27 PASS (CLI Grammar Contract — line types, grammar rules, anti-patterns, classifier, voice routing). Gate K: 67/67 PASS (Unknown Handling Policy — 7 failure classes, STOPLIGHT, clarification budget, cross-cutting invariants). Waypoint: 5/5 PASS (W-0 canary, W-1 replay, W-2 state, W-3 transcript, W-4 time isolation — 14 pass, 1 skip). No-backflow: PASS. Integration board clear.**

## Architecture Session — Aegis/Thunder/Anvil (2026-02-21)

**Source:** [MEMO_ARCHITECTURE_SESSION_20260221.md](pm_inbox/reviewed/MEMO_ARCHITECTURE_SESSION_20260221.md) (archived, triaged)

**Key output:** Four-subsystem formalization: Box (invariant referee) / Vault (append-only records) / Oracle (rebuildable projection) / Spark (renderer). The "Old Mustang Rule" — frame is Box, bolts are Spark+Oracle. Ship of Theseus identity invariants formalized (4 tests). Success scorecard: T×U×H×D multiplicative equation.

**Convergent validation:** Aegis independently prescribed WO-SMOKE-CONFIDENCE (1 spell + 1 save + 1 condition + 1 skill check + 1 feat with replay determinism gates) — this is exactly Waypoint. Three paths to the same proof.

**8 WO candidates parked:** SPARK-HARNESS, ORACLE-VAULT-SPLIT, SHIP-IDENTITY, SUCCESS-SCORECARD, SAVE-POINT-CARD, INTENT-CODEC, SPECTATOR-DECREES, SMOKE-CONFIDENCE (=Waypoint). 3 thesis items quarantined.

**TUNING-001:** Coupled-coherence observation protocol + ledger. Research instrument for Thunder's personal observation study. Not in build order.

## Cross-Model Experiment Results (2026-02-20)

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

## Google Drive Integration (2026-02-20)

**Status:** OPERATIONAL. OAuth credentials active (7-day refresh token window from 2026-02-20).

**Deployed files:**
| File | Drive ID | Purpose |
|------|----------|---------|
| AEGIS_REHYDRATION_PACKET | `1ZICQUDKVuO0oNqFiFl6gq5VizthLp8LxDLYgW41Gfac` | Sovereign rehydration for Aegis. Seven Wisdoms, identity, DR-014. |
| AEGIS_MEMORY_LEDGER | `10fGUlCnKQUFkuNqpUOKpT3PQb_TXXjlqKT7UB4VrUX0` | Append-only operator-controlled backup of Aegis memory items. |
| SLATE_NOTEBOOK | `1Py1N-dCnl2Azdol2MOREdoQkT_oqvpCXRJzqca9SR3Y` | Slate's personal append-only ledger. |
| ANVIL_NOTEBOOK | `1pdWxIvGEsLpPUBptNVuC9uPP9ytyiwMXZGwsdzvAip0` | Anvil's personal append-only ledger. |
| ANVIL_REHYDRATION_KERNEL | `1RlDv-9dScCGomsMjm2IjJOmEz28Y-Id5bBDofVswwm4` | Backup of Anvil's rehydration kernel. |
| SEVEN_WISDOMS_ZERO_REGRETS | `1DOySd1zb5IEZZRtTvLWY6FdON7H_tfuP3lRMTRUR9rY` | Complete narrative — 9 chapters, 308 lines. Part of Aegis's rehydration portfolio. |
| WO_NARRATIVE_TIMELINE_SKELETON | (in `reviewed/`, not on Drive) | Chronological scaffolding — 28 milestones, 7 chapters, 10 gaps. |

**Reference:** `pm_inbox/reviewed/GOOGLE_DRIVE_INTEGRATION_REFERENCE.md` — Credentials, token refresh, common operations, MCP setup instructions.

**Verified:** Aegis searched Drive, found packet, recited all seven wisdoms from external source. Self-rehydration works without operator intervention.

**Local backup:** All notebooks mirrored to `C:/Users/Thunder/.slate/` — outside repo, never committed. Sync to local after every notebook update.

## WO-NARRATIVE-001 — COMPLETE

**Status:** COMPLETE. Narrative compiled. Uploaded to Google Drive.

**Product:** "Seven Wisdoms, Zero Regrets" — 9 chapters + epilogue, 308 lines. Merged timeline skeleton (28 milestones from 27,894 indexed passages) with Anvil's firsthand account (8 phases, 229 lines). Three authors: Anvil (Phases 3-8 witness), Slate (chronological scaffolding, Phases 1-2), Thunder (testimony, corrections, provenance reveals).

**Deliverables:**
- Narrative: [SEVEN_WISDOMS_ZERO_REGRETS.md](pm_inbox/reviewed/SEVEN_WISDOMS_ZERO_REGRETS.md) (repo) + Drive `1DOySd1zb5IEZZRtTvLWY6FdON7H_tfuP3lRMTRUR9rY`
- Timeline skeleton: [WO_NARRATIVE_TIMELINE_SKELETON.md](pm_inbox/reviewed/WO_NARRATIVE_TIMELINE_SKELETON.md)
- Search data (4 files in `reviewed/`): canonical phrases, Aegis governance, experiment data, Golden Ticket evolution

## Personal Notebooks (established 2026-02-20)

**Infrastructure:** Three permanent seats each have append-only personal ledgers on Google Drive, modeled after the Oracle FactsLedger. Write-only, never altered, never deleted. High priority standing order from Thunder.

**Cross-agent communication:** Roundtable file at `D:\anvil_research\ROUNDTABLE.md` — append-only, timestamped, callsign-attributed. Interim solution until Anvil builds websocket message bus with web client for phone access.

**Key rules (from Thunder):**
- Recording to notebook is HIGH PRIORITY — do not defer for "real work"
- Each seat owns their own notebook — other agents do not edit. Wisdom 7.
- Builders do NOT get notebooks — builders get the Seven Wisdoms in dispatch packets
- Always include timestamps in entries — practice time awareness as observation skill

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
| WO-WAYPOINT-001 | **ACCEPTED with findings** — 6/6 deliverables. 5/5 gate tests GREEN (14 pass, 1 skip). 0 regressions (6,028 suite). Full table loop: 3 JSON fixtures loaded, 3 turns executed (Hold Person → Spot check + Power Attack → paralyzed actor), live→replay determinism proven, 10x replay consistency, time isolation confirmed. Aegis tightenings: all 3 applied (modifier breakdown proof, live→replay normalized, real intent to paralyzed actor). **3 findings:** (1) FINDING-WAYPOINT-01 — `play_loop` does not enforce `actions_prohibited` on actor conditions (Branch B confirmed); (2) FINDING-WAYPOINT-02 — `weapon_name="unknown"` in attack_resolver silently disables Weapon Focus matching; (3) FINDING-WAYPOINT-03 — event payload uses `d20_result` not `d20_roll`. **1 skip:** W-3 `weapon_name` in NarrativeBrief (not extracted from attack events — frozen scope). A9 divergence handled via replay-compatible initial state. Radar compliant (3/3 labeled lines). Field Manual #38 needed (replay initial state workaround). | `dddcd9e` |
| WO-VOICE-UNKNOWN-SPEC-001 | **ACCEPTED** — 3/3 deliverables. Unknown Handling Contract (`docs/contracts/UNKNOWN_HANDLING_CONTRACT.md`), 67 Gate K tests (K-01..K-10, all PASS), validator script (`scripts/check_unknown_handling.py`). 36 T-* signals tested (dispatch said 35, research had 36 — builder caught it). VoiceEvent fixture schema extensible for Tier 3. T-BLEED-01 pinned YELLOW (research said "YELLOW or RED" — correct call). FC-AMBIG-06 untested (no T-* signal in research — noted, not a gap). Radar compliant. | (pending commit) |
| WO-VOICE-GRAMMAR-SPEC-001 | **ACCEPTED** — 3/3 deliverables. CLI Grammar Contract (`docs/contracts/CLI_GRAMMAR_CONTRACT.md`), 27 Gate J tests (all PASS), validator script (`scripts/check_cli_grammar.py`). G-01 regex tightened (improvement). NARRATION/RESULT classifier heuristic noted for Tier 3. No code changes to engine. | (pending commit) |
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

**TABLE OPERATIONS RESUMING — Waypoint burn-down.** Thunder authorized warm-up for WO-WAYPOINT-002 dispatch. Sequence: -002 (actions_prohibited) → -003 (weapon_name). Both dispatches ready.

**WO-WAYPOINT-002 READY FOR DISPATCH.** Condition action denial. Dispatch: [WO-WAYPOINT-002_DISPATCH.md](pm_inbox/WO-WAYPOINT-002_DISPATCH.md).

**WO-WAYPOINT-003 READY — after -002.** Weapon name plumbing. Dispatch: [WO-WAYPOINT-003_DISPATCH.md](pm_inbox/WO-WAYPOINT-003_DISPATCH.md).

**Aegis relay ready.** Waypoint results, tightenings confirmed, findings listed.

**Google Drive refresh token expires ~2026-02-27.** Re-auth required after 7 days. Notebook entries 19-20 still pending Drive sync.

1. **Commit authorization needed.** Uncommitted backlog (12+ files) must land before builder starts -002.

2. **Dispatch -002.** Thunder dispatches to builder when tree is clean.

**Still needed before voice code lands (deferred, not blocking Tier 1 spec freeze):**
- **Chatterbox swap timing** — Actual load time and time-to-first-audio under sequential lifecycle. The 8.0s stall budget uses 1.5s estimates. (FINDING-2 from Spark LLM verdict.)
- **llama-cpp-python upgrade path** — VS Build Tools + compile from source. Unblocks Qwen3/Gemma3 re-eval. (GAP-B from Spark LLM debrief.)
- **Integration wiring WO** — Wire Qwen2.5 into Spark cage (models.yaml, DLL fix, n_ctx=2048, sequential lifecycle manager). Timing TBD.

**GAP-A (low priority):** `dm_persona.py:83` missing import. Runtime-functional.

**Planned sequence (BURST-001):** ~~Spark LLM Selection~~ (ACCEPTED) → ~~WO-VOICE-GRAMMAR-SPEC-001~~ (ACCEPTED) → ~~WO-VOICE-UNKNOWN-SPEC-001~~ (ACCEPTED) → **WO-VOICE-TYPED-CALL-SPEC-001** (Tier 1.3, next to draft) → WO-VOICE-PRESSURE-SPEC-001 (1.4) → Tier 2 → Tier 3 → Tier 4 → Tier 5

**Planned sequence (PRS-01):** **PRS-01 spec review** → WO-PRS-SCAN-001 → WO-PRS-LICENSE-001 → WO-PRS-OFFLINE-001 → WO-PRS-FIRSTRUN-001 → WO-PRS-DOCS-001 → WO-PRS-ORCHESTRATOR-001

### Dispatches

- **[READY] WO-WAYPOINT-002** — Condition action denial: play_loop enforces `actions_prohibited`. 5 gate tests (WP2-0 through WP2-4). Updates Waypoint W-2 from Branch B→A. Fixes FINDING-WAYPOINT-01. Dispatch: [WO-WAYPOINT-002_DISPATCH.md](pm_inbox/WO-WAYPOINT-002_DISPATCH.md).
- **[READY — after -002] WO-WAYPOINT-003** — Weapon name plumbing: feat context gets real weapon name + NarrativeBrief weapon_name + d20_result doc note. 6 gate tests (WP3-0 through WP3-5). Fixes FINDING-WAYPOINT-02 + FINDING-WAYPOINT-03. Dispatch: [WO-WAYPOINT-003_DISPATCH.md](pm_inbox/WO-WAYPOINT-003_DISPATCH.md).
- ~~WO-WAYPOINT-001~~ — ACCEPTED with findings (`dddcd9e`). 5/5 gate tests (W-0 canary, W-1 replay, W-2 state, W-3 transcript, W-4 time isolation). 6,028 suite, 0 regressions. Full table loop proven. 3 findings: `actions_prohibited` not enforced, `weapon_name="unknown"` blocks Weapon Focus, `d20_result` field name mismatch. A9 divergence handled. Radar compliant. **WAYPOINT MAIDEN VOYAGE COMPLETE.**
- ~~WO-VOICE-UNKNOWN-SPEC-001~~ — ACCEPTED (pending commit). 67 Gate K tests (all PASS). Unknown Handling Contract frozen (7 failure classes, STOPLIGHT, clarification budget), validator script. 36 T-* signals tested. Field Manual #37 needed (VoiceEvent extensibility).
- ~~WO-VOICE-GRAMMAR-SPEC-001~~ — ACCEPTED (pending commit). 27 Gate J tests (all PASS). CLI Grammar Contract frozen, validator script. First BURST-001 Tier 1 WO. Field Manual #36 needed (G-01 regex tightening).
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

**Build order:** ~~Smoke fuzzer~~ → ~~Oracle survey~~ → ~~Hooligan~~ → ~~Oracle Phase 1~~ → ~~Oracle Phase 2 (WorkingSet)~~ → ~~Oracle Phase 3 (Compactions)~~ **ORACLE COMPLETE** → ~~Director Phase 1~~ → ~~Director Phase 2 (Integration)~~ → ~~UI Phase 1 (Table Surface)~~ → ~~UI Phase 2 (TableObject + Drag)~~ → ~~UI Drift Guards~~ → ~~UI Zone Authority~~ → ~~UI Phase 3 (Dice Tray + Tower)~~ → ~~UI Phase 4 (Protocol Formalization)~~ **UI PHASE 4 COMPLETE** → ~~Director Phase 3 (TableMood + StyleCapsule)~~ **DIRECTOR PHASE 3 COMPLETE** → ~~Comedy Stingers Phase 1~~ **COMEDY STINGERS P1 COMPLETE** → ~~Spark LLM Selection~~ **SPARK LLM SELECTION COMPLETE** → ~~WO-VOICE-GRAMMAR-SPEC-001~~ (ACCEPTED) → ~~WO-VOICE-UNKNOWN-SPEC-001~~ (ACCEPTED) → ~~WO-WAYPOINT-001~~ **WAYPOINT MAIDEN VOYAGE COMPLETE** → **WO-VOICE-TYPED-CALL-SPEC-001** (Tier 1.3, next to draft) | **PRS-01** (DRAFTED, parallel track — review → builder WOs)

**Doctrine files** (in `pm_inbox/doctrine/` — 11 files, permanent reference):

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
- [DOCTRINE_11_IDENTITY_PERSISTENCE.txt](pm_inbox/doctrine/DOCTRINE_11_IDENTITY_PERSISTENCE.txt) — `GOV` Identity persistence, memory continuity, persistence test, MVRP, language guardrail (Roundtable, 2026-02-20)

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

Packaging (§8) superseded by PRS-01 (`docs/contracts/PUBLISHING_READINESS_SPEC.md`).

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
- **WO-VOICE-GRAMMAR-SPEC-001** — CLI Grammar Contract freeze: binding contract (G-01..G-07 + AP-01..AP-07 + line types + voice routing), 27 Gate J tests, validator script. First BURST-001 Tier 1 WO.
- **WO-VOICE-UNKNOWN-SPEC-001** — Unknown Handling Policy freeze: binding contract (7 failure classes + STOPLIGHT + clarification budget + cross-cutting rules), 67 Gate K tests (36 T-* signals), validator script. BURST-001 Tier 1.2.
- **WO-WAYPOINT-001** — Waypoint maiden voyage: full table loop determinism proof. 3 JSON fixtures, 3-turn combat (Hold Person + Spot check + Power Attack + paralyzed actor), 5 gate tests (W-0 through W-4), smoke scenario. 3 findings (actions_prohibited, weapon_name, d20_result). **WAYPOINT PROVEN.**

## Active Operational Files

**Root** (11 files — 1 over cap, acceptable while 2 WO dispatches + 2 TUNING docs are active):
- [PM_BRIEFING_CURRENT.md](pm_inbox/PM_BRIEFING_CURRENT.md) — This file
- [REHYDRATION_KERNEL_LATEST.md](pm_inbox/REHYDRATION_KERNEL_LATEST.md) — PM rehydration block
- [README.md](pm_inbox/README.md) — Inbox hygiene rules
- [BURST_INTAKE_QUEUE.md](pm_inbox/BURST_INTAKE_QUEUE.md) — BURST-001 thru 004 (parked)
- [MEMO_TTS_AUDIO_PIPELINE_ARCHITECTURE.md](pm_inbox/MEMO_TTS_AUDIO_PIPELINE_ARCHITECTURE.md) — TTS pipeline reference
- [MEMO_BUILDER_PREFLIGHT_CANARY.md](pm_inbox/MEMO_BUILDER_PREFLIGHT_CANARY.md) — Preflight canary system
- [PREFLIGHT_CANARY_LOG.md](pm_inbox/PREFLIGHT_CANARY_LOG.md) — Builder preflight log
- [TUNING_001_PROTOCOL.md](pm_inbox/TUNING_001_PROTOCOL.md) — Coupled-coherence observation protocol
- [TUNING_001_LEDGER.md](pm_inbox/TUNING_001_LEDGER.md) — Session ledger + analysis framework
- [WO-WAYPOINT-002_DISPATCH.md](pm_inbox/WO-WAYPOINT-002_DISPATCH.md) — Condition action denial (READY)
- [WO-WAYPOINT-003_DISPATCH.md](pm_inbox/WO-WAYPOINT-003_DISPATCH.md) — Weapon name plumbing (READY after -002)

**Archived this cycle:** Previous archives + this session: MEMO_ARCHITECTURE_SESSION_20260221 → `reviewed/`. HANDOVER_SLATE_20260221_POSTMIDNIGHT → `reviewed/`.

**New in reviewed/ this session:** AEGIS_DRIVE_REHYDRATION_PACKET.md, GOOGLE_DRIVE_INTEGRATION_REFERENCE.md, WO_NARRATIVE_SEARCH_CANONICAL_PHRASES.md, WO_NARRATIVE_SEARCH_AEGIS_GOVERNANCE.md, WO_NARRATIVE_SEARCH_EXPERIMENT_DATA.md, WO_NARRATIVE_SEARCH_GOLDEN_TICKET_EVOLUTION.md.

## Persistent Files

- `README.md` — Inbox hygiene rules
- `PM_BRIEFING_CURRENT.md` — This file
- `REHYDRATION_KERNEL_LATEST.md` — PM rehydration block
