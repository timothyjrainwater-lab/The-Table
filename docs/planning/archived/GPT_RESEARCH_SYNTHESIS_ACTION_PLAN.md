# GPT Research Synthesis — Consolidated Action Plan

**Authority:** PM (Opus) | **Date:** 2026-02-12
**Source:** 5 GPT research instances × 4-5 rounds each = 21 substantive documents
**Purpose:** Deduplicated, prioritized research work orders for Claude agent fleet

---

## Executive Summary

Five parallel GPT instances analyzed the AIDM project through different lenses (architecture, rules compliance, performance, UX, research debt). After deduplication, the findings converge on **6 research tracks** containing **18 actionable work items**. This plan organizes them into a dependency-aware execution sequence.

### Key Cross-Instance Consensus

Every instance independently identified these as critical:
1. Voice reference roster + archetype recipes (WO-051) — blocks immersion credibility
2. RQ-SPARK-001 / RQ-NARR-001 synthesis — 6 sub-dispatches delivered, no synthesis
3. Seam protocol contracts are undefined at Box↔Lens, Lens↔Spark, Spark↔Immersion
4. VRAM residency policy is reactive only (OOM fallback), no steady-state arbitration
5. Canonical ID lifecycle policy missing
6. GPU performance tests skipped — VRAM/latency feasibility unproven

---

## Research Tracks

### Track A — Seam Protocol Contracts (Architecture)

**Source:** Instance 01 rounds 2-5 (strongest material)
**Why first:** Every other track depends on stable boundary contracts.

#### A1 — Enforce Strict Box→Lens Event Contract
- **Problem:** WO-046 allows unknown Box events to pass through as raw dicts, defeating typed boundary contracts
- **Evidence:** PSD WO-046 section; Instance 01 GAP-001
- **Deliverables:**
  - Inventory all registered event types
  - Replace permissive dict passthrough with fail-closed rejection or quarantined opaque type
  - Boundary validator before NarrativeBrief assembly
  - Tests: `test_unknown_event_rejected_at_boundary`, `test_registered_event_passes_validation`
- **Acceptance:** Unknown `event_type` fails deterministically before Lens consumption; no dict-based events reach NarrativeBrief; replay tests green
- **Stop condition:** If existing save logs rely on passthrough events → define migration plan first
- **Scope:** Small-Medium

#### A2 — Define LensPromptPack v1 Schema
- **Problem:** Spark Provider Contract defines transport fields (`prompt`, `max_tokens`) but not what Lens must include. No canonical prompt structure exists.
- **Evidence:** T2_SPARK_PROVIDER_CONTRACT.md §2.1-2.2; Instance 01 GAP-002
- **Deliverables:**
  - PromptPack v1 schema: sections (Facts / Constraints / OutputSchema / Tone / SchemaVersion)
  - Deterministic serialization order
  - Token budget partition policy across: turn events, scene context, campaign memory, persona config
  - Truncation policy (constraints section always preserved; facts truncated first)
  - Tests: `test_promptpack_deterministic_serialization`, `test_promptpack_truncation_preserves_constraints`
- **Acceptance:** Identical Box state → identical PromptPack string; truncation preserves constraints; Spark outputs validate against declared schema
- **Depends on:** A1 (stable Box payload)
- **Scope:** Medium

#### A3 — Complete Narrative Containment Policy Matrix
- **Problem:** NarrativeBrief bans IDs/raw HP/AC/coords and maps HP→severity, but no complete policy on spell names, distances, condition names, DC numbers
- **Evidence:** PSD WO-032; Instance 01 GAP-003
- **Deliverables:**
  - Full Allowed / Mapped / Forbidden matrix for mechanics-adjacent tokens
  - Validation layer enforcing the matrix
  - "Leak probe" test cases
  - Tests: `test_narrative_no_raw_hp_leak`, `test_narrative_distance_mapping_policy`, `test_condition_name_policy`, `test_spark_output_rejects_mechanics_leak`
- **Acceptance:** No forbidden tokens appear in Spark prompt; leak probes fail if forbidden tokens present
- **Depends on:** A1, A2
- **Scope:** Medium

#### A4 — Define ImmersionPlan v1 Orchestration Contract
- **Problem:** Immersion boundary says "caller orchestrates storage" but no turn-level plan object exists. Current seam is glue code.
- **Evidence:** T3_IMMERSION_BOUNDARY.md; Instance 01 GAP-004
- **Deliverables:**
  - ImmersionPlan v1 schema (TTS segments + voice persona refs + image requests + audio cues + bounded retries)
  - Non-authoritative, cacheable, with attribution hooks
  - Deterministic serialization for logging
  - Tests: `test_immersionplan_nonblocking_execution`, `test_immersionplan_no_engine_state_mutation`
- **Acceptance:** ImmersionPlan executes without blocking engine; no authoritative event log contains immersion artifacts; all retries bounded
- **Depends on:** A2 (stable output structure)
- **Scope:** Medium

#### A5 — Authoritative vs Atmospheric Log Partition
- **Problem:** Orchestrator sequences STT→IntentBridge→Box→Narration→TTS but no spec defines what enters the authoritative log vs atmospheric log
- **Evidence:** T3_IMMERSION_BOUNDARY.md; PSD WO-039/045; Instance 01 GAP-005
- **Deliverables:**
  - Strict partition spec: authoritative log = Box events + deterministic intent artifacts only
  - Separate non-authoritative log for STT/TTS/Narration with explicit schema_version
  - Tests: `test_replay_ignores_atmospheric_artifacts`, `test_replay_hash_invariant_under_stt_variance`
- **Acceptance:** Replay hash identical regardless of STT confidence variance and TTS availability
- **Depends on:** A1
- **Scope:** Medium

#### A6 — Schema Versioning & Compatibility Policy
- **Problem:** Multiple serialized contracts (JSONL events, bundles, Spark manifests) exist without a universal migration policy
- **Evidence:** Instance 01 GAP-007
- **Deliverables:**
  - Compatibility rules per artifact: strict version match vs backward-compatible parse
  - Migration location and upgrade path spec
  - Tests: loading mismatched schema_version fails with deterministic, actionable error
- **Depends on:** A2
- **Scope:** Small

---

### Track B — Mechanical Correctness (D&D 3.5e Rules)

**Source:** Instance 02 rounds 2-4 (code-line-level evidence)
**Why:** Mechanical gaps produce "plausible but wrong" outcomes invisible to players.

#### B1 — AoO Provocation Completeness
- **Problem:** AoO only covers movement triggers. Ranged attack and spellcasting provocation are explicitly TODO at `aoo.py:130` and `:193`
- **Evidence:** T3_KNOWN_TECH_DEBT.md TD-005
- **Deliverables:**
  - Canonical provocation event matrix (all RAW actions that provoke)
  - Ranged attack provocation path
  - Spellcasting provocation path
  - Damage-triggered concentration check integration
  - Tests: `test_aoo_spellcasting_provokes`, `test_aoo_ranged_provokes`, `test_concentration_after_aoo_damage`
- **Acceptance:** Casting/ranged in threatened square triggers AoO; concentration DC = 10 + damage; replay hash unchanged for prior corpus
- **Stop condition:** If spell intent cannot represent provoking action → escalate to intent schema design
- **Scope:** Medium
- **Blocked by:** Ranged/spellcasting intent schemas (CP-18A)

#### B2 — Weapon Range Model
- **Problem:** Hard-coded `max_range=100` at `attack_resolver.py:122` because weapon schema lacks range
- **Evidence:** T3_KNOWN_TECH_DEBT.md weapon range entry
- **Deliverables:**
  - Range increment + max range fields in weapon schema
  - Increment penalty logic
  - Max range rejection enforcement
  - Integration with LoS/cover gates
  - Tests: `test_range_increment_penalty`, `test_out_of_range_rejected`, `test_thrown_weapon_range`
- **Acceptance:** Increment penalties stack correctly; out-of-range attacks rejected; no melee regression
- **Stop condition:** If schema migration breaks serialization → escalate
- **Scope:** Medium

#### B3 — Temporary Modifier Integration
- **Problem:** `permanent_stats.py:279` stubs `temp_total = 0`. Ability buffs/debuffs don't affect derived stats.
- **Evidence:** T3_KNOWN_TECH_DEBT.md TD-006; CP-16 dependency
- **Deliverables:**
  - Replace stub with condition system lookup
  - Stacking precedence definition
  - Derived stat recalculation trigger
  - Tests: `test_temp_str_affects_attack`, `test_temp_dex_affects_ac`, `test_condition_stack_precedence`
- **Acceptance:** STR buff modifies attack/damage; DEX debuff modifies AC/Reflex; deterministic replay preserved
- **Stop condition:** If stacking rules ambiguous → escalate to rules decision log
- **Scope:** Medium

#### B4 — AC/HP Recompute System
- **Problem:** Full AC recomputation and HP calculation are explicit stubs at `permanent_stats.py:327` and `:375`
- **Evidence:** T3_KNOWN_TECH_DEBT.md TD-007
- **Deliverables:**
  - AC stacking matrix (armor/shield/natural/deflection/dodge/size)
  - Authoritative recompute function
  - HP recompute with CON changes
  - Tests: `test_ac_stacking_matrix`, `test_hp_recompute_on_con_change`
- **Depends on:** B3 (derived modifier source of truth)
- **Scope:** Medium-Large

#### B5 — RAW Spell Scenario Suite
- **Problem:** 53 spells have registry tests but no RAW scenario coverage. SpellResolver, DurationTracker, AoE Rasterizer not exercised end-to-end.
- **Evidence:** PSD spell pipeline sections
- **Deliverables:**
  - 10-20 canonical RAW spell scenarios (SR, save negates/half, AoE, buffs, damage)
  - Deterministic scenario tests with golden event logs
  - Tests: `test_spell_sr_block`, `test_spell_save_half_damage`, `test_spell_aoe_edge_case`, `test_spell_buff_duration_expires`
- **Depends on:** B1, B2, B3
- **Scope:** Medium

#### B6 — 5e Contamination Audit
- **Problem:** 5 contamination vectors identified: rest mechanics, concentration (skill vs global limiter), cantrips (0-level slots vs at-will), skill naming (Spot/Listen vs Perception), action economy (bonus action/reaction)
- **Evidence:** Instance 02 round 2 analysis
- **Deliverables:**
  - Terminology hardening: "0-level spells" not "cantrips" in code/docs
  - Explicit prohibition of 5e-style concentration global limiter
  - Review checklist for future implementers
- **Scope:** Small

---

### Track C — Performance & Hardware Validation

**Source:** Instance 03 rounds 2-4
**Why:** All performance claims are unmeasured. GPU tests are hardware-gated skips.

#### C1 — GPU Performance Gate Execution
- **Problem:** 4 Spark GPU performance tests are hardware-gated skips. VRAM/latency feasibility unproven.
- **Evidence:** PSD Spark stress tests section
- **Deliverables:**
  - Run full stress suite on RTX 3080 Ti
  - Capture: peak VRAM per turn, cold-start time, reload time, tokens/sec, p50/p95 latency
  - Run under fallback model scenario
  - Run under forced overflow condition
  - Benchmark artifact: `artifacts/perf/gpu_run_YYYYMMDD.json`
- **Acceptance:** No OOM under defined scenario; p95 latency recorded; artifact reproducible ±10%
- **Requires:** Physical hardware access
- **Scope:** Medium (execution), but blocks everything else in Track C

#### C2 — VRAM Residency / Eviction Policy
- **Problem:** Only reactive OOM fallback defined (unload → smaller model → templates). No steady-state policy.
- **Evidence:** T2_SPARK_PROVIDER_CONTRACT.md §6.2
- **Deliverables:**
  - Allowed co-residency matrix (which models can share GPU)
  - Priority order + eviction triggers + prefetch timing
  - "Unload failure" fallback behavior
  - Validated via 30-turn stress run with no load/unload oscillation
- **Depends on:** C1 (needs measured VRAM footprints)
- **Scope:** Medium

#### C3 — Latency SLAs by Hardware Tier
- **Problem:** No p50/p95 latency envelopes defined for any pipeline path
- **Evidence:** T2_SPARK_PROVIDER_CONTRACT.md SparkResponse metadata
- **Deliverables:**
  - Tier table: Target / Recommended / Minimum hardware
  - Max p95 turn latency per tier
  - Max reload latency
  - Feature availability per tier
  - Enforcement via release gating
- **Depends on:** C1 (real latency numbers)
- **Scope:** Small

#### C4 — OOM Recovery Validation
- **Problem:** Unload/reload VRAM reclamation never validated. Fragmentation risk unknown.
- **Evidence:** Instance 03 GAP-005
- **Deliverables:**
  - 20-cycle OOM injection test
  - VRAM before/after each cycle
  - Memory growth trend analysis
  - Reload latency per cycle
- **Depends on:** C1
- **Scope:** Small-Medium

---

### Track D — Research Synthesis (Abandoned Research Completion)

**Source:** All instances flagged this; Instance 05 round 4 has the best work packet
**Why:** Findings exist but no synthesis — policies remain non-canonical.

#### D1 — RQ-SPARK-001 Synthesis: Structured Fact Emission Contract
- **Problem:** 3 sub-dispatches delivered (schema/units, prompting validation, improvisation/NPCs). No final synthesis.
- **Deliverables:**
  - Single "Spark Emission Contract v1" document
  - Canonical structured output schema (reconciled with NarrativeBrief)
  - MUST / SHOULD / MUST-NOT statements
  - Failure taxonomy + repair/retry policy + hard stop conditions
  - Edge cases and adversarial examples
  - Test matrix mapping
- **Scope:** Medium

#### D2 — RQ-NARR-001 Synthesis: Narrative Balance Rubric
- **Problem:** 3 sub-dispatches delivered (output space, templates/confirmation, tone evaluation). No final synthesis.
- **Deliverables:**
  - Measurable narration rubric: mechanical fidelity checks, containment checks, tone targets
  - Alignment rules: narration must reflect Box outcome, must not leak forbidden details
  - Regression harness: curated scenarios to detect drift
  - Evaluation method (scoring without human-heavy processes)
- **Depends on:** D1 (facts/provenance shape)
- **Scope:** Medium

---

### Track E — Governance & Operations

**Source:** Instance 04 rounds 3-4 (unique contributions)
**Why:** Documentation drift creates bad dispatches and wrong audits.

#### E1 — Documentation Canonicalization
- **Problem:** Coherence Doctrine (2025) says "production voice integration out of scope" while PSD (2026) shows implemented STT/TTS/Image adapters. Vertical Slice V1 says "no combat resolver" while PSD shows full combat stack.
- **Deliverables:**
  - `CURRENT_CANON.md` referencing authoritative docs
  - Deprecation banners on superseded docs (Vertical Slice, historical plan sections)
  - `DOC_DRIFT_LEDGER.md` documenting resolved contradictions
  - Updated onboarding checklist pointing to correct sources
- **Scope:** Small

#### E2 — Determinism Allowlist Enforcement
- **Problem:** `uuid.uuid4()` cast_id exists in event payloads, excluded from equality checks. Load-bearing assumption it doesn't leak into replay keys.
- **Evidence:** PSD P1 Replay Stability finding
- **Deliverables:**
  - Authoritative nondeterministic fields allowlist
  - Central validator enforcing allowlist
  - Negative test: new nondeterministic field introduction triggers failure
  - Tests: `test_no_unapproved_nondeterminism`, `test_replay_payload_integrity`
- **Scope:** Small-Medium

#### E3 — Operator Quickstart & Failure Matrix
- **Problem:** No runbook exists. System is developer-only. Playtests will fail on setup friction.
- **Deliverables:**
  - `OPERATOR_QUICKSTART.md`: dependency installation, model acquisition, launch command, example session, expected outputs
  - `FAILURE_MATRIX.md`: STT/Spark/TTS/Image failure → user-visible behavior → recovery
  - Smoke test: `test_smoke_session_run`
- **Scope:** Medium

#### E4 — Narrative Determinism Policy
- **Problem:** Mechanics are deterministic on replay but narration may differ. This is undefined — players will file bugs for "expected behavior."
- **Deliverables:**
  - Policy document: what must match on replay (mechanics) vs what may vary (narration)
  - Whether narration is cached per session
  - Replay demo showing identical mechanics with narrative variance
  - Tests: `test_mechanics_replay_strict_equality`, `test_narrative_variance_allowed`
- **Scope:** Small

---

### Track F — Voice Pipeline Research (WO-051 Execution)

**Source:** All instances flagged; WO-051 already filed
**Why:** "Voice-first DM" is a core value proposition. Currently every character sounds the same.

#### F1 — Reference Audio Corpus & Sourcing Policy
- **Problem:** No legally usable reference clips exist. Chatterbox adapter works but has no distinct voices.
- **Deliverables:**
  - Clip quality rubric (noise floor, length, mono/stereo, sample rate, phoneme coverage)
  - Loudness normalization standard
  - Sourcing strategy (public domain, CC, generated, self-recorded)
  - Licensing compliance matrix per source
  - 10-15 starter clips with validated licenses
- **Scope:** Large

#### F2 — Archetype Recipe Table
- **Problem:** No mapping from character archetypes to VoicePersona parameter ranges
- **Deliverables:**
  - 8-12 archetype recipes (narrator, dwarf, elf, villain, innkeeper, etc.)
  - Numeric parameter ranges per archetype (pitch, speed, exaggeration)
  - Reference audio selection per archetype
  - Perceptual distinctness validation (A/B tests)
- **Depends on:** F1 (needs clips)
- **Scope:** Medium

#### F3 — Voice Resolver Stability Metrics
- **Problem:** WO-052 requires "deterministic enough" voice mapping but no measurable thresholds
- **Deliverables:**
  - Quantifiable stability metrics: % field stability across N runs
  - Persona assignment invariants (same character_id → same persona_id within session)
  - Cache invalidation triggers
  - Collision rate measurement (different characters → same persona)
- **Depends on:** F1, F2
- **Scope:** Medium

---

## Execution Order (Dependency-Aware)

### Phase 1 — Foundations (no dependencies, can run in parallel)

| Work Item | Track | Agent Type | Parallel? |
|-----------|-------|------------|-----------|
| A1 — Box→Lens event contract enforcement | Architecture | Code audit + implementation | Yes |
| B6 — 5e contamination terminology audit | Rules | Code audit | Yes |
| D1 — RQ-SPARK-001 synthesis | Research | Document synthesis | Yes |
| E1 — Documentation canonicalization | Governance | Document audit | Yes |
| E2 — Determinism allowlist | Governance | Code audit + implementation | Yes |
| C1 — GPU performance gate | Performance | Benchmark execution | Yes (requires hardware) |

### Phase 2 — Depends on Phase 1 outputs

| Work Item | Track | Depends On |
|-----------|-------|------------|
| A2 — LensPromptPack v1 | Architecture | A1 |
| A5 — Log partition spec | Architecture | A1 |
| D2 — RQ-NARR-001 synthesis | Research | D1 |
| E4 — Narrative determinism policy | Governance | E2 |
| C2 — VRAM residency policy | Performance | C1 |
| C3 — Latency SLAs | Performance | C1 |
| C4 — OOM recovery validation | Performance | C1 |

### Phase 3 — Depends on Phase 2 outputs

| Work Item | Track | Depends On |
|-----------|-------|------------|
| A3 — Containment policy matrix | Architecture | A1, A2 |
| A4 — ImmersionPlan v1 | Architecture | A2 |
| A6 — Schema versioning policy | Architecture | A2 |
| E3 — Operator quickstart | Governance | E1 |
| B1 — AoO provocation | Rules | Blocked by CP-18A (spellcasting intents) |
| B2 — Weapon range model | Rules | Independent but benefits from A2 |
| B3 — Temporary modifier integration | Rules | Independent |

### Phase 4 — Depends on Phase 3 outputs

| Work Item | Track | Depends On |
|-----------|-------|------------|
| B4 — AC/HP recompute | Rules | B3 |
| B5 — RAW spell scenario suite | Rules | B1, B2, B3 |

### Voice Track (parallel, independent timeline)

| Work Item | Track | Depends On |
|-----------|-------|------------|
| F1 — Reference audio corpus | Voice | Independent |
| F2 — Archetype recipe table | Voice | F1 |
| F3 — Voice resolver stability metrics | Voice | F1, F2 |

---

## Break Suite (from Instance 01, Round 5)

15 concrete failure scenarios were identified. The top 10 tests to add first:

| Test | Catches | Gap |
|------|---------|-----|
| `test_unknown_event_rejected_at_boundary` | Unknown event passthrough | A1 |
| `test_event_payload_serialization_stable` | Nondeterministic serialization | A1, E2 |
| `test_freeze_after_settlement_for_interrupt_chains` | Mid-turn narration | A5 |
| `test_promptpack_canonical_sections_present` | Prompt drift across call sites | A2 |
| `test_promptpack_truncation_preserves_constraints` | Constraint truncation → hallucination | A2 |
| `test_narrativebrief_no_forbidden_tokens` | Coordinate/stat leakage | A3 |
| `test_spark_output_rejects_mechanics_leak` | Post-generation containment | A3 |
| `test_spark_malformed_json_bounded_retry_then_fallback` | Retry loop hangs | A2 |
| `test_replay_hash_invariant_under_atmospheric_variance` | Atmospheric log contamination | A5 |
| `test_vram_contention_degrades_without_crash` | VRAM contention crash | A4, C2 |

---

## Discarded / False Findings

| Finding | Source | Why Discarded |
|---------|--------|---------------|
| RG-005 "Governance contradiction: who is PM?" | Instance 02 round 1 | False alarm — GPT confused by system prompt context vs PSD. PSD is authoritative. |
| Instance 04 round 1 register | Instance 04 | Didn't follow UX lens; duplicated voice/rules findings from other instances |
| Instance 05 round 1 register | Instance 05 | Identical duplicate of Instance 04 round 1 (filing error) |
| Instance 05 round 3 | Instance 05 | Empty file |

---

## GPT Instance Quality Assessment

| Instance | Best Output | Grade | Key Value |
|----------|-------------|-------|-----------|
| 01 Architecture | Round 5 (15 failure scenarios + break suite) | **A** | Seam protocol taxonomy, failure scenarios, break suite |
| 02 Rules | Round 4 (5 remediation work packets) | **A** | Code-line-level mechanical gaps, 5e contamination vectors |
| 03 Performance | Round 4 (5 benchmark work packets) | **B+** | Performance evidence gaps, OOM recovery validation |
| 04 UX | Round 4 (operator quickstart, narrative determinism) | **B** | Unique: operator runbook, narrative determinism policy |
| 05 Research Debt | Round 4 (cross-cutting synthesis) | **B** | Late start but good synthesis; mostly echoed other instances |

---

## Highest-Risk Unknowns (Resolve First)

1. **Whether authoritative logs currently contain STT transcripts or narration artifacts.** If true, replay determinism may already be compromised. Resolution: inspect one real JSONL event log + run replay with/without STT. (30-60 minutes)

2. **Whether RQ-SPARK-001 and RQ-NARR-001 sub-findings actually agree with each other.** If they contradict, synthesis will fail. Resolution: side-by-side matrix of output schema claims. (1-2 hours)

3. **Whether GPU unload/reload actually reclaims VRAM reliably.** If not, the entire VRAM arbitration plan collapses. Resolution: 20-cycle load/unload test on target GPU. (< 1 day)

4. **Whether Spell Resistance, Damage Reduction, concealment, and touch attacks are implemented.** If missing, the spell scenario suite will expose systemic failures. Resolution: grep for `SR`, `damage_reduction`, `concealment`, `touch_attack` in resolvers. (< 1 hour)

---

*This document synthesizes findings from 5 GPT research instances across 21 documents. It is the canonical input for Claude agent fleet research dispatches.*
