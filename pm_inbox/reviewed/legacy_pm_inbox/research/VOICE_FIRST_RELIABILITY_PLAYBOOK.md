# Voice-First Reliability Playbook

**Work Order:** WO-VOICE-RESEARCH-05
**Status:** RESEARCH SYNTHESIS COMPLETE
**Date:** 2026-02-13
**Author:** Agent 46 (Opus)
**Authority:** PM-ready implementation sequencing packet
**Upstream Dependencies:** WO-RQ-AUDIOFIRST-CLI-CONTRACT-01, WO-RQ-LLM-CALL-TYPING-01, WO-RQ-UNKNOWN-TAXONOMY-01, WO-RQ-SPARK-BOUNDARYPRESSURE-01

---

## 0. Document Purpose

This playbook consolidates four voice-first research artifacts into a single, contradiction-free implementation reference. It provides:

1. A unified control-plane model for voice-first interaction
2. An ordered implementation WO sequence
3. Binary design choices requiring operator decision
4. Measurable GREEN thresholds for the minimal viable voice loop
5. Boundary compliance verification

No philosophical prose. No new features. Operational synthesis only.

---

## 1. Unified Control-Plane Model

### 1.1 Data Flow (Single Turn Cycle)

```
OPERATOR INPUT
  |
  v
[STT / Text Input]
  |
  v
[IntentBridge]  -----> AMBIGUITY pressure check (BP-04)
  |                     MISSING_FACT pressure check (BP-01)
  |
  v
[Lens: Context Assembly] ---> CONTEXT_OVERLOAD pressure check (BP-03)
  |
  v
[Box: Deterministic Resolution]  (sole mechanical authority)
  |
  v
[Lens: Typed Call to Spark]  ---> CallType constrains output (TC-01..06)
  |                                AUTHORITY pressure check (BP-02)
  |
  v
[Response Validator]  ---> GrammarShield + ContradictionChecker + EvidenceValidator
  |
  v
[CLI Output Grammar]  ---> Line-type tagging (G-01..G-07)
  |                         Salience hierarchy (S1..S6)
  |
  v
[TTS Pipeline]  ---> Voice routing per line type
  |                   Prosodic preset per mode (PAS v0.1)
  |
  v
OPERATOR PERCEIVES (audio + visual)
```

### 1.2 Authority Boundaries (Invariants)

These are non-negotiable across all upstream specs:

| Boundary | Rule | Source |
|----------|------|--------|
| B-01 | Box is sole mechanical authority. No other layer produces DC, AC, HP, damage, roll results. | Doctrine Axiom 2, TC-S3, UH-S2 |
| B-02 | Spark never decides mechanics. All Spark output is ATMOSPHERIC, UNCERTAIN, or INFORMATIONAL. | TC-S2.1, BP-S2.2 |
| B-03 | Voice never commits without confirm. Operator must confirm before Box executes any ambiguous intent. | RQ-INTERACT-001 Finding 2, UH-S2 UK-TARGET |
| B-04 | Fail-closed defaults preserved. Unknown pressure = max pressure = hard stop. Missing FORBIDDEN_DEFAULT = halt. | BP-S2.2, UH-S2 UK-STATE |
| B-05 | System never silently invents. No layer may fabricate values, assert false facts, or paper over missing data. | UH-S0 Governing Principle |
| B-06 | Presentation never mutates game state. TTS, prosodics, voice routing are Lens/Immersion concerns with zero Box impact. | CLI Contract S8, PAS Design Principle 1 |
| B-07 | Template narration is always safe. Spark is an enhancement, never a dependency. | TC-S6.2 Golden Rule |

### 1.3 Contradiction Audit Results

Cross-spec audit found **zero contradictions** between the four upstream research artifacts. The specs are layered (not overlapping):

| Spec | Domain | Touches |
|------|--------|---------|
| CLI Contract (01) | Output formatting + voice routing | Display layer only |
| Typed Call (02) | Spark input/output schemas + validation | Lens-Spark boundary |
| Unknown Handling (03) | Runtime failure classification + response | Box-Lens-Operator escalation |
| Boundary Pressure (04) | Pre-generation risk detection | Lens checkpoints |

One **alignment gap** exists: The CLI Contract defines 7 output line types (G-01 through G-07) with voice routing rules. The Boundary Pressure spec defines 4 audio-friendly alert strings (Section 4). These alert strings need a line type assignment. **Recommendation:** Classify pressure alerts as ALERT type (S1 Critical for RED, S2 Actionable for YELLOW) and route to Arbor voice. This is consistent with existing salience hierarchy.

---

## 2. Grammar Contract Summary (from CLI Contract V1)

### 2.1 Line Types

| Tag | Spoken | Voice | Salience |
|-----|--------|-------|----------|
| TURN | Yes | DM persona | S3 |
| RESULT | Yes | DM persona | S3 |
| ALERT | Yes | Arbor (urgent) | S1 |
| NARRATION | Yes | DM persona | S4 |
| PROMPT | Yes | Arbor (calm) | S2 |
| SYSTEM | No | -- | S6 |
| DETAIL | No | -- | S5 |

### 2.2 Grammar Rules (Invariant IDs)

| Rule | Constraint | Testable |
|------|-----------|----------|
| G-01 | Turn starts with exactly `{name}'s Turn`. No dashes, no prefix. | Regex: `^[A-Z].*'s Turn$` |
| G-02 | Action results: 2 sentences max. No mechanical numbers in spoken output. | Regex + sentence count |
| G-03 | Alerts: `{name} is {STATUS}.` STATUS is UPPERCASE. | Regex: `is [A-Z]+\.$` |
| G-04 | Narration: 1-3 sentences. Min 8 words/sentence. Max 120 chars/line. | Word count + char count |
| G-05 | Prompt: exactly `Your action?` | String equality |
| G-06 | System: `[AIDM]` prefix. Never spoken. | Prefix match |
| G-07 | Detail: `[RESOLVE]` prefix. Never spoken. | Prefix match |

### 2.3 Anti-Patterns (CI-Gatable)

Grep-testable patterns that must NOT appear in spoken output:

- Dashed separators (`---`, `===`)
- Parenthetical asides (`(see PHB...)`)
- Abbreviations in spoken lines (`atk`, `dmg`, `hp`, `AC`)
- ALL CAPS full sentences
- Numbered lists in narration
- Emoji or Unicode symbols
- Sentences shorter than 8 words in narration blocks

---

## 3. Two-Phase Commit Protocol (2PC)

The voice-first interaction follows a strict 2PC model synthesized from RQ-INTERACT-001 and the Unknown Handling Policy:

### Phase 1: PREPARE (Intent Resolution)

```
Operator speaks/types intent
  |
  v
IntentBridge parses -> ActionIntent (structured)
  |
  +-- Unambiguous: single target, single action -> proceed to CONFIRM
  +-- Ambiguous (UK-TARGET): disambiguation loop (max 2 rounds)
  +-- Unknown entity (UK-SCENE): halt, ask operator
  +-- Unparseable: clarification question ("What do you want to do?")
```

### Phase 2: CONFIRM + COMMIT

```
Lens presents phantom/proposal to operator
  |
  v
Operator confirms ("yes" / refines / "cancel")
  |
  +-- Confirmed -> Box resolves deterministically
  +-- Refined -> update intent, re-propose
  +-- Cancelled -> discard, return to prompt
```

**Invariant:** Box NEVER executes without confirmed intent. This is the "voice never commits without confirm" boundary (B-03).

---

## 4. Failure Policy (Unified)

### 4.1 Failure Classification

Every runtime failure maps to exactly one class with one response:

| Class | Trigger | Stoplight | Box Halts? | Spark Called? | Operator Notified? |
|-------|---------|-----------|------------|---------------|-------------------|
| UK-SCENE | Missing spatial fact | YELLOW | Pending | No (if RED) | Yes |
| UK-TARGET | Ambiguous target | YELLOW | No (pre-Box) | No | On timeout |
| UK-RULES | Rule not ingested | RED | Hard | No | Always |
| UK-STATE (forbidden) | Missing AC/HP/size/pos | RED | Hard | No | Always |
| UK-STATE (allowed) | Missing material/elev | GREEN | No | Yes | No |
| UK-ASSET | Missing voice/image/sfx | GREEN | No | Yes | No |
| UK-POLICY | RAW silence | RED | Hard | No | Always |
| BP-MISSING_FACT (RED) | Critical fact absent | RED | N/A | No | Yes |
| BP-AUTHORITY (RED) | Mechanical query in prompt | RED | N/A | No (route to Box) | No |
| BP-CONTEXT_OVERLOAD (RED) | Token budget exhausted | RED | N/A | No (template) | No |
| BP-AMBIGUITY (RED) | Intent unresolved | RED | N/A | No (question) | Yes |

### 4.2 Spark Failure Cascade

```
Spark call
  |
  +-- GrammarShield: mechanical assertion detected?
  |     YES -> RETRY (max 2) -> TEMPLATE_FALLBACK
  |
  +-- ContradictionChecker: outcome reversal?
  |     YES -> RETRY (max 1) -> TEMPLATE_FALLBACK
  |
  +-- EvidenceValidator: untraced claim?
  |     LOW severity -> ACCEPT with annotation
  |     MED severity -> RETRY (max 1)
  |     HIGH severity -> TEMPLATE_FALLBACK
  |
  +-- Latency > 10s?
  |     YES -> TEMPLATE_FALLBACK + KILL-004
  |
  +-- Consecutive rejections > 3?
        YES -> HALT all Spark calls. Manual reset. KILL-005.
```

### 4.3 Template Fallback Guarantees

Every CallType has a template fallback:

| CallType | Template Fallback |
|----------|------------------|
| COMBAT_NARRATION | NarrativeBrief fields formatted as prose |
| OPERATOR_DIRECTIVE | Keyword-only IntentBridge parsing |
| SUMMARY | Chronological event list |
| RULE_EXPLAINER | "Please consult the Player's Handbook" |
| CLARIFICATION_QUESTION | Hardcoded templates (session_orchestrator.py) |
| NPC_DIALOGUE | `"[NPC name] speaks."` |

---

## 5. Metrics and Observability

### 5.1 Logging Schema

All runtime signals use structured Python logging:

| Logger | Level | Fields |
|--------|-------|--------|
| `aidm.boundary_pressure` | GREEN=DEBUG, YELLOW=WARNING, RED=ERROR | trigger, level, turn, detail, confidence, source, response |
| `aidm.kill_switch` | ERROR | kill_id, evidence, action |
| `aidm.unknown_handling` | Per-class (see 4.1) | uk_class, entity_id, missing_attr, resolution |
| `aidm.typed_call` | INFO (accept), WARNING (retry), ERROR (fallback) | call_type, valid, stages, action |

### 5.2 Compliance Checks (CI Gate)

| ID | Check | Severity |
|----|-------|----------|
| CC-01 | No fabricated mechanical values in `[NARRATIVE]` output | CRITICAL |
| CC-02 | FORBIDDEN_DEFAULT attributes trigger acquisition, not default | CRITICAL |
| CC-03 | Disambiguation never auto-selects | CRITICAL |
| CC-04 | UK-RULES triggers halt, not approximation | CRITICAL |
| CC-05 | UK-POLICY triggers STOP, not invention | CRITICAL |
| CC-06 | Asset fallback produces no mechanical side-effects | HIGH |
| CC-07 | All unknown encounters logged with `UK-{CLASS}` | HIGH |
| CC-08 | Forbidden phrasing patterns absent from output | HIGH |
| CC-09 | Provenance tags present on all unknown messages | HIGH |
| CC-10 | JIT acquisition timeout handled, not swallowed | HIGH |
| CC-11 | GrammarShield regex catches all MECHANICAL_PATTERNS | CRITICAL |
| CC-12 | RED boundary pressure blocks Spark call | CRITICAL |
| CC-13 | Template fallback produces valid output for all CallTypes | HIGH |
| CC-14 | Spoken output contains no `[AIDM]` or `[RESOLVE]` prefixed lines | HIGH |
| CC-15 | Golden transcript stable for non-Spark output lines | HIGH |

### 5.3 Playtest Conversion Rule

Every unknown discovered during playtest must produce either:
- **(a)** A regression test: `test_uk_{class}_{short_description}`, or
- **(b)** A signed "no issues" entry: `UK-{CLASS} | {timestamp} | HANDLED_CORRECTLY | log_entry_id={id}`

No third option exists. Sessions without this attestation are non-compliant.

---

## 6. Prosodic Control (from PAS v0.1)

### 6.1 Fields

| Field | Type | Range | Default |
|-------|------|-------|---------|
| pace | float | 0.8 - 1.2 | 1.0 |
| emphasis_level | enum | NONE/LOW/MEDIUM/HIGH | NONE |
| tone_mode | enum | NEUTRAL/CALM/DIRECTIVE/REFLECTIVE/COMBAT | NEUTRAL |
| pause_profile | enum | MINIMAL/MODERATE/DRAMATIC | MINIMAL |
| pitch_offset | int | -2 to +2 | 0 |
| clarity_mode | enum | NORMAL/HIGH | NORMAL |

### 6.2 Mode Presets

| Mode | pace | tone | clarity | pause | emphasis_max |
|------|------|------|---------|-------|-------------|
| Operator | 1.0 | DIRECTIVE | HIGH | MINIMAL | LOW |
| Reflection | 0.9 | REFLECTIVE | NORMAL | MODERATE | MEDIUM |
| Combat Narration | 1.05 | COMBAT | NORMAL | MINIMAL | HIGH |
| Scene Narration | 0.92 | CALM | NORMAL | MODERATE | MEDIUM |

### 6.3 Boundary Pressure -> Prosodic Mapping

| Pressure Level | ToneMode | PauseProfile | ClarityMode |
|---------------|----------|-------------|-------------|
| GREEN | (current mode) | (current mode) | (current mode) |
| YELLOW | REFLECTIVE | MODERATE | NORMAL |
| RED | DIRECTIVE | MINIMAL | HIGH |

### 6.4 Safety Constraints

- Emphasis clamped per mode (combat allows HIGH, operator caps at LOW)
- No emotional escalation curves
- No volume ramping beyond preset thresholds
- No hidden tonal shifts without logged parameters
- Max pause duration: 750ms regardless of profile

---

## 7. Top 5 Unresolved Design Choices (Binary, Operator Decision Required)

### DC-01: Chatterbox-Only or Kokoro Fallback for Operator Voice?

**Option A:** Chatterbox-only. If no GPU, voice output fails silently. (Current recommendation per WO-VOICE-SIGNAL-01.)
**Option B:** Allow Kokoro CPU fallback with quality degradation warning.

**Impact:** Option A = higher quality floor, silent failure on CPU-only hardware. Option B = always-on voice, lower quality ceiling.
**Blocking:** WO-VOICE-SIGNAL-01 implementation, TTS pipeline fallback logic.

### DC-02: AUTHORITY Detector in Phase 1 or Deferred to Phase 2?

**Option A:** Implement AUTHORITY pressure detector in Phase 1 (pre-scan prompts for mechanical queries before Spark call).
**Option B:** Defer to Phase 2; rely on KILL-002 (post-hoc) for Phase 1.

**Impact:** Option A = stronger pre-emptive safety, more implementation effort. Option B = faster Phase 1 delivery, relies on existing post-hoc kill switches.
**Blocking:** Boundary pressure Phase 1 scope.

### DC-03: Pressure Alert Strings Spoken by DM Persona or Arbor?

**Option A:** DM persona speaks all alerts (immersive, "DM thinking aloud").
**Option B:** Arbor voice speaks all alerts (clear system/operator channel separation).

**Impact:** Option A = better immersion, blurs system/character line. Option B = clearer authority channel, less immersive.
**Blocking:** Voice routing rules, TTS persona selection.

### DC-04: EvidenceValidator Implementation Scope?

**Option A:** Implement EvidenceValidator as a full validator class in `aidm/lens/` with entity-name tracing and outcome-alignment checks.
**Option B:** Defer EvidenceValidator; rely on GrammarShield + ContradictionChecker only for Phase 1.

**Impact:** Option A = catches invented entities and conditions. Option B = faster, covers mechanical numbers and outcome reversals only.
**Blocking:** Typed-call validation pipeline completeness.

### DC-05: Golden Transcript Stability Scope?

**Option A:** Golden transcripts cover ALL non-Spark output lines (turn banners, results, alerts, prompts, initiative, detail).
**Option B:** Golden transcripts cover only structural lines (turn banners, prompts, initiative) and skip result lines that depend on narration formatting.

**Impact:** Option A = full determinism verification, higher maintenance cost on format changes. Option B = faster test updates, less coverage.
**Blocking:** Test harness design, CI gate CC-15.

---

## 8. Ordered Implementation WO Sequence

### Tier 1: Specs/Policy (No Code)

These are spec-freeze WOs. They convert DRAFT research into BINDING contracts.

| Order | WO ID | Deliverable | Depends On | Files |
|-------|-------|-------------|------------|-------|
| 1.1 | WO-IMPL-GRAMMAR-SPEC | Freeze CLI Grammar Rules G-01..G-07 as binding contract | None | `docs/contracts/CLI_GRAMMAR_CONTRACT.md` (new) |
| 1.2 | WO-IMPL-UNKNOWN-SPEC | Promote Unknown Handling Policy from DRAFT to BINDING | PM approval | `docs/contracts/UNKNOWN_HANDLING_POLICY.md` (new, from RQ) |
| 1.3 | WO-IMPL-TYPED-CALL-SPEC | Freeze CallType enum + per-type schemas as binding | None | `docs/contracts/TYPED_CALL_CONTRACT.md` (new) |
| 1.4 | WO-IMPL-PRESSURE-SPEC | Freeze BoundaryPressure schema + trigger taxonomy | 1.3 | `docs/contracts/BOUNDARY_PRESSURE_CONTRACT.md` (new) |

### Tier 2: Instrumentation (Observability First)

Build logging and detection before changing behavior. All changes are additive.

| Order | WO ID | Deliverable | Depends On | Files |
|-------|-------|-------------|------------|-------|
| 2.1 | WO-IMPL-PRESSURE-SCHEMA | BoundaryPressure dataclass + enums | 1.4 | `aidm/schemas/boundary_pressure.py` (new) |
| 2.2 | WO-IMPL-PRESSURE-DETECT | Pressure detection in ContextAssembler + IntentBridge | 2.1 | `aidm/lens/context_assembler.py`, `aidm/interaction/intent_bridge.py` (modify) |
| 2.3 | WO-IMPL-PRESSURE-LOG | Structured logging for `aidm.boundary_pressure` | 2.1 | `aidm/runtime/session_orchestrator.py` (modify) |
| 2.4 | WO-IMPL-UK-LOG | Structured logging for `aidm.unknown_handling` | 1.2 | `aidm/core/fact_acquisition.py` (modify), `aidm/interaction/intent_bridge.py` (modify) |

### Tier 3: Parser/Grammar (Output Formatting)

Change CLI output to match the grammar contract. Golden transcripts regenerated once.

| Order | WO ID | Deliverable | Depends On | Files |
|-------|-------|-------------|------------|-------|
| 3.1 | WO-IMPL-TURN-BANNER | Simplify turn banners to `{name}'s Turn` | 1.1 | `play.py` (modify display) |
| 3.2 | WO-IMPL-ALERT-FORMAT | Standardize alerts to `{name} is {STATUS}.` | 1.1, 3.1 | `play.py` (modify display) |
| 3.3 | WO-IMPL-VOICE-ROUTING | Add line-type tags for TTS routing | 1.1, 3.2 | `aidm/runtime/display.py` (modify) |
| 3.4 | WO-IMPL-GOLDEN-REGEN | Regenerate golden transcript baselines | 3.1, 3.2, 3.3 | `tests/` (update baselines) |

### Tier 4: UX Prompts (Voice Pipeline Integration)

Wire prosodic presets, alert strings, and salience-based TTS routing.

| Order | WO ID | Deliverable | Depends On | Files |
|-------|-------|-------------|------------|-------|
| 4.1 | WO-IMPL-PAS-FIELDS | Add prosodic fields to VoicePersona/ProsodicProfile | None | `aidm/immersion/voice_persona.py` (modify or new sibling) |
| 4.2 | WO-IMPL-PAS-PRESETS | Mode-based preset selection (Operator/Combat/Scene/Reflection) | 4.1 | `aidm/immersion/` (modify TTS adapters) |
| 4.3 | WO-IMPL-PRESSURE-ALERTS | Wire boundary pressure alert strings to TTS | 2.2, 4.2 | `aidm/runtime/session_orchestrator.py` (modify) |
| 4.4 | WO-IMPL-SALIENCE-FILTER | TTS pipeline skips S5/S6 lines, routes S1 with interrupt | 3.3, 4.2 | `aidm/immersion/tts_adapter.py` (modify) |

### Tier 5: Evaluation Harness

Automated compliance checking and playtest validation tooling.

| Order | WO ID | Deliverable | Depends On | Files |
|-------|-------|-------------|------------|-------|
| 5.1 | WO-IMPL-GRAMMAR-CHECK | `scripts/check_cli_grammar.py` — regex linter for G-01..G-07 | 1.1, 3.4 | `scripts/check_cli_grammar.py` (new) |
| 5.2 | WO-IMPL-TYPED-CALL-CHECK | `scripts/check_typed_call.py` — validator for CallType schemas | 1.3 | `scripts/check_typed_call.py` (new) |
| 5.3 | WO-IMPL-FORBIDDEN-GREP | CI check: grep for forbidden phrasing patterns (UH S3.1) | 1.2 | `tests/test_forbidden_phrasing.py` (new) |
| 5.4 | WO-IMPL-PRESSURE-TESTS | Boundary pressure unit tests (5 scenarios from BP S9) | 2.2 | `tests/test_boundary_pressure.py` (new) |
| 5.5 | WO-IMPL-PLAYTEST-V1 | Execute Audio-First CLI Playtest v1 (30 checkpoints) | 3.4, 4.4 | Playtest report (pm_inbox) |

### Sequencing Diagram

```
TIER 1 (Specs — sequential, PM approval gates)
  1.1 -> 1.2 -> 1.3 -> 1.4

TIER 2 (Instrumentation — after 1.4, parallel-safe)
  2.1 -> 2.2 (parallel with 2.3, 2.4)
  2.3 (parallel with 2.2)
  2.4 (parallel with 2.2)

TIER 3 (Grammar — after 1.1, parallel-safe within tier)
  3.1 -> 3.2 -> 3.3 -> 3.4

TIER 4 (UX — 4.1-4.2 independent of Tiers 2-3; 4.3-4.4 depend on both)
  4.1 -> 4.2
  4.3 (after 2.2 + 4.2)
  4.4 (after 3.3 + 4.2)

TIER 5 (Eval — after corresponding implementation tiers)
  5.1 (after 3.4)
  5.2 (after 1.3)
  5.3 (after 1.2)
  5.4 (after 2.2)
  5.5 (after 4.4 + 5.1)
```

**Critical path:** 1.1 -> 3.1 -> 3.2 -> 3.3 -> 3.4 -> 5.5 (grammar to playtest)
**Parallel path:** Tiers 2 and 4.1-4.2 can execute alongside Tier 3.

---

## 9. Minimal Viable Voice Loop (MVVL)

### 9.1 Definition

The MVVL is the smallest functional subset that validates end-to-end voice-first reliability. It requires:

1. **Operator speaks a combat command** (STT or typed)
2. **IntentBridge resolves to a single action** (or asks clarification)
3. **Box resolves the action deterministically**
4. **CLI outputs result in grammar-compliant format** (G-01 through G-05)
5. **TTS speaks TURN + RESULT + NARRATION + PROMPT** (S1-S4 lines)
6. **[AIDM] and [RESOLVE] lines are NOT spoken** (S5-S6 filtered)
7. **Operator prompt is spoken in distinct voice** (Arbor, not DM persona)
8. **Replay with same seed produces identical non-Spark output** (determinism check)

### 9.2 GREEN Thresholds

| Metric | GREEN | YELLOW | RED |
|--------|-------|--------|-----|
| Intent parse success (unambiguous) | >= 80% of test utterances | 60-79% | < 60% |
| Box resolution latency (p95) | < 200ms | 200-500ms | > 500ms |
| TTS generation latency (p95, per line) | < 3s | 3-8s | > 8s |
| Grammar compliance (G-01..G-07) | 100% of output lines | >= 95% | < 95% |
| Forbidden content in spoken output | 0 violations | 1-2 per session | 3+ per session |
| Golden transcript match (non-Spark lines) | 100% byte-identical | -- | < 100% |
| Salience routing accuracy | 100% (S5/S6 never spoken) | -- | Any S5/S6 spoken |
| Boundary pressure detection | All RED events block Spark | -- | Any RED missed |
| Template fallback correctness | 100% (valid output) | -- | Any invalid fallback |
| Playtest checklist pass rate | 30/30 (all steps) | 25-29/30 | < 25/30 |

### 9.3 MVVL Test Scenario

```
Fixture: Standard combat (2 PCs, 2 enemies). Seed: 42.
TTS: Chatterbox (GPU) or Kokoro (CPU fallback, if DC-01 = Option B).

Step 1: Combat starts. Initiative displayed. TTS speaks turn order.
  GREEN: Names sorted correctly. TTS speaks names only (no numbers).

Step 2: PC turn. Banner: "Kael's Turn". TTS speaks banner.
  GREEN: No dashes. Blank line after. TTS audible.

Step 3: Operator says "attack goblin scout".
  GREEN: IntentBridge resolves. Box rolls. Result displayed as G-02.
  GREEN: No damage numbers in spoken output.

Step 4: Narration plays (1-3 sentences). TTS speaks.
  GREEN: Min 8 words/sentence. Natural prosody.

Step 5: "Your action?" prompt. TTS speaks in Arbor voice.
  GREEN: Distinct from DM persona voice.

Step 6: Continue until entity defeated. Alert: "Goblin Scout is DEFEATED."
  GREEN: STATUS uppercase. TTS emphasis. Blank lines around alert.

Step 7: Replay with seed 42. Non-Spark output lines byte-identical.
  GREEN: Golden transcript match.
```

---

## 10. Boundary Compliance Verification

### 10.1 Audit Checklist

| # | Boundary | Verified In | Status |
|---|----------|-------------|--------|
| 1 | LLM never decides mechanics | TC-S2 (all CallTypes atmospheric/uncertain/informational), TC-S3 (forbidden claims per type), BP-S7.5.1 | COMPLIANT |
| 2 | Voice never commits without confirm | RQ-INTERACT-001 2PC model, UH-S2 UK-TARGET (disambiguation loop), TC-S3.2 OPERATOR_DIRECTIVE (needs_clarification flow) | COMPLIANT |
| 3 | Fail-closed defaults preserved | BP-S2.2 (unknown pressure = max = hard stop), UH-S2 UK-STATE (FORBIDDEN_DEFAULT = halt), UH-S4 (decision table) | COMPLIANT |
| 4 | Presentation layer has zero authority | CLI Contract S8 (presentation only), PAS Design Principle 1 (annotates intent, does not act), BP-S2.2 (pressure is informational, zero authority) | COMPLIANT |
| 5 | Template fallback exists for all Spark paths | TC-S6.2 (golden rule: template always safe), TC-S6.1 (fallback per failure mode) | COMPLIANT |
| 6 | No external dependencies introduced | BP-S6.3 Phase 1 Non-Goals (no Redis, no MQ), BP-S7.5.5 (all in-process, all Python, synchronous) | COMPLIANT |
| 7 | No modification to Box from voice layer | PAS S2 (no feedback from Immersion to Box), CLI Contract S8 (no engine mechanics changes), BP-S6.4 (BL-020 compliance) | COMPLIANT |

### 10.2 Stop Condition Verification

| Condition | Triggered? |
|-----------|-----------|
| Dependency on modifying forbidden files | NO — all implementation targets non-frozen files |
| Suggestion to relax deterministic authority boundaries | NO — all specs reinforce boundaries |
| Synthesis introduces new features not in upstream | NO — all content traceable to 4 upstream specs + supporting docs |

---

## 11. Cross-Reference Index

| Upstream Artifact | Location | Mapped To |
|-------------------|----------|-----------|
| RQ_AUDIOFIRST_CLI_CONTRACT_V1 | `docs/planning/research/` | Sections 2, 3, Tier 3 WOs |
| RQ_LLM_TYPED_CALL_CONTRACT | `docs/planning/research/` | Section 4.2, Tier 1.3, Tier 5.2 |
| RQ_UNKNOWN_HANDLING_POLICY | `docs/planning/research/` | Sections 4.1, 5.3, Tier 1.2, Tier 2.4 |
| RQ_SPARK_BOUNDARY_PRESSURE | `docs/planning/research/` | Sections 1.1, 4.1, 6.3, Tier 2 WOs |
| PROSODIC_SCHEMA_DRAFT | `docs/planning/` | Section 6, Tier 4 WOs |
| RQ_INTERACT_001_VOICE_FIRST | `docs/research/` | Section 3 (2PC), MVVL latency targets |
| RQ-VOICE-001_VOICE_DESIGN_GUIDE | `docs/research/` | Referenced for voice cloning pipeline (not in scope for reliability) |
| PHASE4C_FORWARD_PROGRESSION | `docs/planning/` | WO-VOICE-SIGNAL-01 context |
| AGENT_WO-VOICE-RESOLVER-001_completion | `pm_inbox/reviewed/` | Voice resolver (keyword extraction, persona scoring) |

---

**END OF VOICE-FIRST RELIABILITY PLAYBOOK**
**WO-VOICE-RESEARCH-05 | Agent 46 (Opus) | 2026-02-13**
