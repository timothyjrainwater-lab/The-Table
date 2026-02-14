# Voice Reliability Metrics & Telemetry Spec

**Work Order:** WO-VOICE-RESEARCH-03
**Status:** RESEARCH COMPLETE
**Date:** 2026-02-13
**Author:** Sonnet C (Agent)
**Authority:** PM-approved research deliverable

---

## 1. Purpose

This document defines quantifiable metrics, log event schemas, gating thresholds, and an evaluation protocol for the voice-first interaction loop. It enables measurement, tuning, and go/no-go gating of voice play without subjective evaluation.

**Binding references:**
- `docs/planning/research/RQ_AUDIOFIRST_CLI_CONTRACT_V1.md` (output grammar, salience hierarchy)
- `docs/research/RQ_INTERACT_001_VOICE_FIRST.md` (intent parsing, latency targets)
- `docs/research/RQ_PERF_001_COMPUTE_BUDGETING.md` (performance measurement framework)
- `aidm/immersion/voice_intent_parser.py` (ParseResult, STMContext)
- `aidm/immersion/clarification_loop.py` (ClarificationRequest, ClarificationEngine)
- `aidm/testing/performance_profiler.py` (LatencyTarget, percentile framework)

**Scope:** Metrics and telemetry for the voice interaction loop only (STT transcript in -> intent parsed -> clarification if needed -> confirm/reject -> Box execution). TTS synthesis quality (MOS, prosody accuracy) is out of scope; those belong to a separate audio quality spec.

---

## 2. Metric Definitions

### 2.1 Core Metrics

Seven metrics form the minimum set. Each is defined with a formula, unit, and collection point.

---

#### M-01: `parse_success_rate`

**Definition:** Fraction of player utterances that produce a valid, actionable `ParseResult` with `intent is not None` and `confidence >= 0.5` on first attempt.

**Formula:**
```
parse_success_rate = successful_parses / total_utterances
```

Where:
- `successful_parses` = count of utterances where `ParseResult.intent is not None AND ParseResult.confidence >= 0.5`
- `total_utterances` = count of all player utterances received by the voice intent parser (excludes system-generated audio, TTS playback)

**Unit:** Ratio (0.0 - 1.0), reported as percentage.

**Collection point:** `VoiceIntentParser.parse()` return.

---

#### M-02: `clarification_rate`

**Definition:** Fraction of utterances that trigger a `ClarificationRequest` from the `ClarificationEngine`.

**Formula:**
```
clarification_rate = utterances_requiring_clarification / total_utterances
```

Where:
- `utterances_requiring_clarification` = count of utterances where `ClarificationEngine.generate_clarification()` is called and returns a non-None `ClarificationRequest`

**Unit:** Ratio (0.0 - 1.0), reported as percentage.

**Collection point:** `ClarificationEngine.generate_clarification()` return.

**Note:** Not all clarifications indicate failure. Some ambiguity is expected (e.g., "attack him" when two enemies are adjacent). This metric tracks how often the system asks the player to repeat or refine, not whether the system failed.

---

#### M-03: `confirm_reject_rate`

**Definition:** Fraction of phantom-rendered confirmations where the player rejects (says "no", "not that one", or equivalent) or refines the system's interpretation.

**Formula:**
```
confirm_reject_rate = rejected_confirmations / total_confirmations
```

Where:
- `rejected_confirmations` = count of confirmation prompts where player response is classified as REJECT or REFINE
- `total_confirmations` = count of all confirmation prompts presented to the player (includes auto-confirmed high-confidence intents only if they are explicitly presented for confirmation)

**Unit:** Ratio (0.0 - 1.0), reported as percentage.

**Collection point:** Confirmation loop outcome handler.

---

#### M-04: `time_to_commit_ms`

**Definition:** Elapsed wall-clock time from the moment STT returns a finalized transcript to the moment Box begins executing the confirmed intent.

**Formula:**
```
time_to_commit_ms = t_box_execute_start - t_stt_transcript_final
```

**Unit:** Milliseconds. Reported as p50, p95, p99 percentiles (consistent with `LatencyTarget` framework in `aidm/testing/performance_profiler.py`).

**Collection point:** Timestamps captured at STT finalization and Box execution entry.

**Breakdown sub-spans (for diagnosis, not gating):**
| Sub-span | Start | End |
|---|---|---|
| `stt_latency_ms` | Microphone capture end | STT transcript finalized |
| `parse_latency_ms` | STT transcript received | ParseResult returned |
| `clarification_latency_ms` | ClarificationRequest sent | Player response received |
| `confirm_latency_ms` | Confirmation prompt sent | Player confirm/reject received |
| `phantom_render_ms` | Intent parsed | Phantom render displayed |

---

#### M-05: `repeat_request_rate`

**Definition:** Fraction of utterances where the system asks the player to repeat themselves entirely (total parse failure, not partial clarification).

**Formula:**
```
repeat_request_rate = repeat_requests / total_utterances
```

Where:
- `repeat_requests` = count of utterances where `ParseResult.intent is None` OR `ParseResult.confidence < 0.3` (system cannot extract any actionable intent, triggers "I didn't quite catch that" response per RQ-INTERACT-001 Finding 5 Scenario C)

**Unit:** Ratio (0.0 - 1.0), reported as percentage.

**Collection point:** `VoiceIntentParser.parse()` return, filtered by total failure condition.

**Distinction from M-02:** Clarification (M-02) means the system understood *something* but needs refinement. Repeat request (M-05) means the system understood *nothing actionable*.

---

#### M-06: `abort_rate`

**Definition:** Fraction of voice interaction sequences where the player abandons the voice path entirely (switches to click/type input, says "never mind", or the interaction times out without resolution).

**Formula:**
```
abort_rate = aborted_sequences / total_voice_sequences
```

Where:
- `aborted_sequences` = count of voice interaction sequences that end without Box execution via one of: (a) explicit abort phrase detected, (b) player switches to keyboard/mouse input mid-sequence, (c) interaction timeout (no player response within `VOICE_INTERACTION_TIMEOUT_MS`)
- `total_voice_sequences` = count of all voice interaction sequences initiated (starting from first utterance for a given turn)

**Unit:** Ratio (0.0 - 1.0), reported as percentage.

**Collection point:** Session orchestrator turn-cycle completion handler.

---

#### M-07: `out_of_grammar_rate`

**Definition:** Fraction of utterances where the transcript text falls entirely outside the parser's known vocabulary/patterns (no intent type matched, no slots extracted, no keyword hits).

**Formula:**
```
out_of_grammar_rate = out_of_grammar_utterances / total_utterances
```

Where:
- `out_of_grammar_utterances` = count of utterances where `ParseResult.intent is None AND len(ParseResult.raw_slots) == 0 AND ParseResult.confidence == 0.0`

**Unit:** Ratio (0.0 - 1.0), reported as percentage.

**Collection point:** `VoiceIntentParser.parse()` return, filtered by zero-extraction condition.

**Distinction from M-05:** A repeat request (M-05) can happen when the parser extracts *some* slots but confidence is too low. Out-of-grammar (M-07) means the parser found *nothing at all* — the utterance is entirely outside the recognized domain (e.g., player talking to another player, background noise, off-topic speech).

---

### 2.2 Metric Summary Table

| ID | Metric | Good Direction | Formula Denominator |
|---|---|---|---|
| M-01 | `parse_success_rate` | Higher is better | `total_utterances` |
| M-02 | `clarification_rate` | Lower is better | `total_utterances` |
| M-03 | `confirm_reject_rate` | Lower is better | `total_confirmations` |
| M-04 | `time_to_commit_ms` | Lower is better | N/A (latency) |
| M-05 | `repeat_request_rate` | Lower is better | `total_utterances` |
| M-06 | `abort_rate` | Lower is better | `total_voice_sequences` |
| M-07 | `out_of_grammar_rate` | Lower is better | `total_utterances` |

---

## 3. Log Event Schema

### 3.1 Required Fields (All Events)

Every telemetry event includes these base fields:

```json
{
  "timestamp": "2026-02-13T19:45:12.347Z",
  "session_id": "sess_a1b2c3d4",
  "utterance_id": "utt_00042",
  "event_type": "voice.parse.success",
  "turn_number": 7,
  "round_number": 3
}
```

| Field | Type | Description |
|---|---|---|
| `timestamp` | ISO 8601 string | Wall-clock time of event emission |
| `session_id` | string | Unique session identifier (one per `play.py` invocation) |
| `utterance_id` | string | Unique identifier per player utterance within a session, monotonically increasing |
| `event_type` | string | Dot-namespaced event identifier (see 3.2) |
| `turn_number` | int | Current turn number within combat (0 if out-of-combat) |
| `round_number` | int | Current round number (0 if out-of-combat) |

### 3.2 Event Types

#### `voice.stt.transcript`

Emitted when STT finalizes a transcript.

```json
{
  "event_type": "voice.stt.transcript",
  "transcript": "I want to attack the goblin with my longsword",
  "stt_confidence": 0.92,
  "stt_adapter": "whisper",
  "audio_duration_ms": 2340,
  "stt_latency_ms": 180
}
```

| Field | Type | Description |
|---|---|---|
| `transcript` | string | Raw STT text output |
| `stt_confidence` | float | STT-reported confidence (0.0-1.0) |
| `stt_adapter` | string | Adapter used (`"whisper"`) |
| `audio_duration_ms` | int | Duration of captured audio in ms |
| `stt_latency_ms` | int | Time from audio-end to transcript-ready |

---

#### `voice.parse.result`

Emitted when the voice intent parser returns a `ParseResult`.

```json
{
  "event_type": "voice.parse.result",
  "transcript": "I want to attack the goblin with my longsword",
  "parse_result": "success",
  "intent_type": "declared_attack",
  "confidence": 0.88,
  "ambiguity_count": 0,
  "ambiguous_target": false,
  "ambiguous_location": false,
  "ambiguous_action": false,
  "slots_extracted": ["action:attack", "target:goblin", "weapon:longsword"],
  "parse_latency_ms": 45,
  "parse_errors": []
}
```

| Field | Type | Description |
|---|---|---|
| `transcript` | string | Input transcript (duplicated from STT event for self-contained analysis) |
| `parse_result` | enum | `"success"`, `"clarification_needed"`, `"repeat_needed"`, `"out_of_grammar"` |
| `intent_type` | string or null | Parsed intent type (`"declared_attack"`, `"cast_spell"`, `"move"`, etc.) or null if parse failed |
| `confidence` | float | Parser confidence score (0.0-1.0) |
| `ambiguity_count` | int | Number of ambiguous fields (`ambiguous_target + ambiguous_location + ambiguous_action`) |
| `ambiguous_target` | bool | Target resolution was ambiguous |
| `ambiguous_location` | bool | Location resolution was ambiguous |
| `ambiguous_action` | bool | Action type was unclear |
| `slots_extracted` | list[string] | Extracted slot key:value pairs for debugging |
| `parse_latency_ms` | int | Time from transcript-in to ParseResult-out |
| `parse_errors` | list[string] | Error messages from parser (from `ParseResult.parse_errors`) |

---

#### `voice.clarification.request`

Emitted when the clarification engine generates a prompt.

```json
{
  "event_type": "voice.clarification.request",
  "clarification_type": "target",
  "prompt_text": "Did you mean the Goblin Archer or the Worg next to him?",
  "option_count": 2,
  "missing_fields": ["target_id"],
  "can_proceed_without": false
}
```

| Field | Type | Description |
|---|---|---|
| `clarification_type` | string | Type of ambiguity (`"target"`, `"location"`, `"spell"`, `"direction"`, `"action"`) |
| `prompt_text` | string | DM-persona clarification text presented to player |
| `option_count` | int | Number of disambiguation options offered |
| `missing_fields` | list[string] | Fields requiring resolution |
| `can_proceed_without` | bool | Whether partial execution is possible |

---

#### `voice.clarification.response`

Emitted when the player responds to a clarification.

```json
{
  "event_type": "voice.clarification.response",
  "response_transcript": "the archer",
  "response_type": "select",
  "selected_option_index": 0,
  "clarification_resolved": true,
  "response_latency_ms": 1450
}
```

| Field | Type | Description |
|---|---|---|
| `response_transcript` | string | Player's response transcript |
| `response_type` | enum | `"select"` (chose an option), `"refine"` (gave new info), `"abort"` (gave up), `"timeout"` |
| `selected_option_index` | int or null | Index of selected option (null if refine/abort/timeout) |
| `clarification_resolved` | bool | Whether the clarification resolved the ambiguity |
| `response_latency_ms` | int | Time from clarification prompt to player response |

---

#### `voice.confirm.outcome`

Emitted when the player confirms or rejects a phantom-rendered interpretation.

```json
{
  "event_type": "voice.confirm.outcome",
  "confirm_outcome": "accept",
  "intent_type": "declared_attack",
  "phantom_render_ms": 120,
  "confirm_latency_ms": 890
}
```

| Field | Type | Description |
|---|---|---|
| `confirm_outcome` | enum | `"accept"`, `"reject"`, `"refine"`, `"timeout"` |
| `intent_type` | string | Intent type being confirmed |
| `phantom_render_ms` | int | Time to render the phantom visualization |
| `confirm_latency_ms` | int | Time from phantom display to player response |

---

#### `voice.commit`

Emitted when a confirmed intent is handed to Box for execution.

```json
{
  "event_type": "voice.commit",
  "intent_type": "declared_attack",
  "total_time_to_commit_ms": 2340,
  "clarification_rounds": 0,
  "confirmation_rounds": 1,
  "voice_only": true
}
```

| Field | Type | Description |
|---|---|---|
| `intent_type` | string | Final intent type committed |
| `total_time_to_commit_ms` | int | M-04 value for this utterance |
| `clarification_rounds` | int | Number of clarification round-trips |
| `confirmation_rounds` | int | Number of confirm/reject round-trips |
| `voice_only` | bool | True if entire sequence used voice; false if player fell back to keyboard/mouse |

---

#### `voice.abort`

Emitted when a voice interaction sequence is abandoned.

```json
{
  "event_type": "voice.abort",
  "abort_reason": "player_switched_to_keyboard",
  "utterances_in_sequence": 3,
  "elapsed_ms": 8400
}
```

| Field | Type | Description |
|---|---|---|
| `abort_reason` | enum | `"explicit_abort"`, `"player_switched_to_keyboard"`, `"timeout"`, `"session_end"` |
| `utterances_in_sequence` | int | Number of utterances attempted before abort |
| `elapsed_ms` | int | Total elapsed time from first utterance to abort |

---

### 3.3 Latency Buckets

All `*_latency_ms` and `*_ms` timing fields are bucketed for aggregation dashboards:

| Bucket | Range |
|---|---|
| `fast` | 0 - 200 ms |
| `acceptable` | 201 - 600 ms |
| `slow` | 601 - 1500 ms |
| `degraded` | 1501 - 3000 ms |
| `unacceptable` | > 3000 ms |

Bucket boundaries align with RQ-INTERACT-001 latency targets:
- `fast` corresponds to phantom render target (< 200 ms)
- `acceptable` corresponds to intent parsing acknowledgment window (< 600 ms)
- `slow` corresponds to Box resolution lower bound (1-3s range)
- `degraded` corresponds to Box resolution upper bound
- `unacceptable` exceeds all documented targets

---

## 4. Gating Thresholds

### 4.1 Session-Level Health Status

At the end of a session (or during a session at any checkpoint), compute all seven metrics from collected events. Map to a health status:

| Status | Meaning | Action |
|---|---|---|
| **GREEN** | Voice loop is playable. Ship it. | No action required. |
| **YELLOW** | Voice loop is usable but degraded. Investigate before expanding test group. | Review logs, identify top failure patterns. |
| **RED** | Voice loop is not playable. Block voice-first mode. | Fix before next playtest. Fall back to keyboard input. |

### 4.2 Threshold Table

| Metric | GREEN | YELLOW | RED |
|---|---|---|---|
| M-01 `parse_success_rate` | >= 0.85 | >= 0.70 | < 0.70 |
| M-02 `clarification_rate` | <= 0.15 | <= 0.25 | > 0.25 |
| M-03 `confirm_reject_rate` | <= 0.10 | <= 0.20 | > 0.20 |
| M-04 `time_to_commit_ms` (p95) | <= 3000 | <= 5000 | > 5000 |
| M-05 `repeat_request_rate` | <= 0.05 | <= 0.10 | > 0.10 |
| M-06 `abort_rate` | <= 0.05 | <= 0.10 | > 0.10 |
| M-07 `out_of_grammar_rate` | <= 0.03 | <= 0.08 | > 0.08 |

### 4.3 Gating Rules

1. **Overall status** = worst individual metric status. If any single metric is RED, overall is RED.
2. **YELLOW override:** If 3+ metrics are YELLOW simultaneously, overall status is RED (cumulative degradation).
3. **Minimum sample size:** Gating requires >= 30 utterances in the session. Below 30, status is `INSUFFICIENT_DATA` and cannot gate.
4. **M-04 uses p95:** The `time_to_commit_ms` threshold applies to the 95th percentile of the session's latency distribution, not the mean. This prevents a few outliers from masking systemic issues while tolerating occasional spikes.

### 4.4 Gating Output Format

The gating evaluator produces a single status block:

```json
{
  "session_id": "sess_a1b2c3d4",
  "status": "YELLOW",
  "utterance_count": 47,
  "metrics": {
    "parse_success_rate": {"value": 0.87, "status": "GREEN"},
    "clarification_rate": {"value": 0.19, "status": "YELLOW"},
    "confirm_reject_rate": {"value": 0.08, "status": "GREEN"},
    "time_to_commit_ms_p95": {"value": 2780, "status": "GREEN"},
    "repeat_request_rate": {"value": 0.04, "status": "GREEN"},
    "abort_rate": {"value": 0.06, "status": "YELLOW"},
    "out_of_grammar_rate": {"value": 0.02, "status": "GREEN"}
  },
  "yellow_count": 2,
  "red_count": 0,
  "gate_decision": "PASS_WITH_WARNINGS"
}
```

`gate_decision` values:
- `PASS` — all GREEN
- `PASS_WITH_WARNINGS` — at least one YELLOW, no RED, fewer than 3 YELLOWs
- `FAIL` — any RED, or 3+ YELLOWs

---

## 5. Evaluation Protocol (Gold Set)

### 5.1 Purpose

Compute metrics deterministically from recorded transcripts, independent of live STT. This enables regression testing of the parser and clarification engine without microphone input.

### 5.2 Gold Set Structure

A gold set is a JSON file containing labeled utterance records:

```json
{
  "gold_set_id": "voice_gold_v1",
  "created": "2026-02-13",
  "utterances": [
    {
      "utterance_id": "gold_001",
      "transcript": "I attack the goblin with my longsword",
      "expected_intent_type": "declared_attack",
      "expected_target": "goblin_scout_1",
      "expected_slots": {"action": "attack", "target": "goblin", "weapon": "longsword"},
      "expected_parse_result": "success",
      "stm_context": {
        "last_target": null,
        "last_action": null,
        "last_weapon": null
      },
      "world_context": {
        "visible_entities": ["goblin_scout_1", "goblin_shaman_1", "kael"],
        "actor_id": "kael",
        "actor_weapons": ["longsword", "shortbow"]
      }
    },
    {
      "utterance_id": "gold_002",
      "transcript": "hit him again",
      "expected_intent_type": "declared_attack",
      "expected_target": "goblin_scout_1",
      "expected_slots": {"action": "attack", "target": "him"},
      "expected_parse_result": "success",
      "stm_context": {
        "last_target": "goblin_scout_1",
        "last_action": "attack",
        "last_weapon": "longsword"
      },
      "world_context": {
        "visible_entities": ["goblin_scout_1", "goblin_shaman_1", "kael"],
        "actor_id": "kael",
        "actor_weapons": ["longsword", "shortbow"]
      }
    },
    {
      "utterance_id": "gold_003",
      "transcript": "can someone close the window it's cold",
      "expected_intent_type": null,
      "expected_target": null,
      "expected_slots": {},
      "expected_parse_result": "out_of_grammar",
      "stm_context": {},
      "world_context": {
        "visible_entities": ["goblin_scout_1", "kael"],
        "actor_id": "kael",
        "actor_weapons": ["longsword"]
      }
    }
  ]
}
```

### 5.3 Evaluation Procedure

1. **Load gold set** from JSON file.
2. **For each utterance**, in order (ordering matters for STM context):
   a. Construct `STMContext` from `stm_context` field.
   b. Construct a `Transcript` object with `text=transcript`, `confidence=1.0`, `adapter_id="gold_set"`.
   c. Call `VoiceIntentParser.parse(transcript, stm_context, world_context)`.
   d. Record the `ParseResult`.
3. **Classify each result:**
   - `success`: `ParseResult.intent is not None AND confidence >= 0.5 AND intent_type matches expected_intent_type`
   - `clarification_needed`: `ParseResult` has any ambiguity flag set AND expected was `"success"` (parser under-performed) OR expected was `"clarification_needed"` (correct behavior)
   - `repeat_needed`: `ParseResult.intent is None OR confidence < 0.3`
   - `out_of_grammar`: `ParseResult.intent is None AND len(raw_slots) == 0 AND confidence == 0.0`
4. **Compute metrics** from classified results using formulas in Section 2.
5. **Compare against gold labels:**
   - `intent_accuracy` = fraction of utterances where actual `intent_type` matches `expected_intent_type`
   - `target_accuracy` = fraction of utterances where resolved target matches `expected_target` (applicable only where `expected_target is not None`)
   - `classification_accuracy` = fraction of utterances where actual `parse_result` category matches `expected_parse_result`
6. **Apply gating thresholds** from Section 4.

### 5.4 Gold Set Requirements

- Minimum 50 utterances per gold set.
- Category distribution:
  - >= 60% expected `success` (normal commands)
  - >= 10% expected `clarification_needed` (ambiguous but parseable)
  - >= 5% expected `out_of_grammar` (off-topic, background noise)
  - >= 5% pronoun/reference resolution cases (requires STM context)
  - Remainder: mix of edge cases (unusual phrasing, compound actions, corrections)
- Each gold set must include a `world_context` for every utterance (entity lists, actor state). The parser's behavior depends on what targets are visible.
- Gold sets are versioned. When the parser's grammar changes, a new gold set version is created. Old gold sets are retained for regression comparison.

### 5.5 Determinism Guarantee

Given the same gold set JSON and the same parser version, the evaluation must produce byte-identical metric output. The parser uses no randomness (no LLM calls, no sampling). The gold set provides fixed STM context per utterance, eliminating state-dependent variation.

---

## 6. How to Read These Metrics

This section is for operators and playtesters who did not build the system.

### 6.1 What You Are Looking At

After a voice playtest session, you get a **status report** with seven numbers and a color (GREEN / YELLOW / RED). Here is what each number means in plain language:

| Metric | Plain English | What Bad Looks Like |
|---|---|---|
| `parse_success_rate` | "How often did the system understand what I said on the first try?" | Below 70%: the system misunderstands more than 3 in 10 commands. Frustrating. |
| `clarification_rate` | "How often did the DM ask me to clarify?" | Above 25%: the DM asks a follow-up question for 1 in 4 commands. Feels slow. |
| `confirm_reject_rate` | "How often did the system guess wrong about what I meant?" | Above 20%: 1 in 5 confirmations are wrong. Player loses trust in phantom rendering. |
| `time_to_commit_ms` | "How long between me saying something and the game doing it?" | p95 above 5 seconds: 1 in 20 commands takes 5+ seconds. Breaks conversational flow. |
| `repeat_request_rate` | "How often did the DM say 'I didn't catch that'?" | Above 10%: 1 in 10 utterances is a total whiff. May indicate STT issues or noisy environment. |
| `abort_rate` | "How often did I give up on voice and type instead?" | Above 10%: 1 in 10 attempts ends with the player reaching for the keyboard. Voice is not the primary input. |
| `out_of_grammar_rate` | "How often did I say something the system has no category for?" | Above 8%: common if players chat with each other during their turn. May need push-to-talk or voice activity detection improvements. |

### 6.2 Reading the Status

- **GREEN across the board:** Voice play is working. Players can rely on speaking as the primary input.
- **Mixed GREEN/YELLOW:** Playable but not smooth. Look at which metrics are YELLOW to identify the bottleneck (parser accuracy? latency? too many clarifications?).
- **Any RED:** Voice play is not viable for this session's conditions. Common causes: noisy room, parser regression, STT adapter issues. Check the `voice.abort` events in the log for patterns.

### 6.3 Common Patterns and What They Mean

| Pattern | Likely Cause | Where to Look |
|---|---|---|
| High `clarification_rate` + normal `parse_success_rate` | Parser extracts intent but can't resolve targets (ambiguous world state) | Check `voice.clarification.request` events — if `clarification_type` is mostly `"target"`, the phantom render needs better spatial disambiguation |
| High `repeat_request_rate` + high `out_of_grammar_rate` | STT quality issues OR players talking off-topic | Check `voice.stt.transcript` events — if `stt_confidence` is low, it's a microphone/noise problem; if confidence is high but parse fails, the parser vocabulary needs expansion |
| High `abort_rate` + normal other metrics | Latency or UX friction, not accuracy | Check `voice.abort` events — if `abort_reason` is mostly `"timeout"`, the system is too slow; if mostly `"player_switched_to_keyboard"`, players may prefer typing for certain action types |
| High `confirm_reject_rate` + low `clarification_rate` | Parser is over-confident — it thinks it understands but picks the wrong interpretation | Check `voice.confirm.outcome` events where `confirm_outcome == "reject"` — the preceding `voice.parse.result` events will show what the parser thought vs. what the player meant |
| High `time_to_commit_ms` + normal accuracy metrics | Latency bottleneck in one sub-span | Check the latency sub-spans in `voice.commit` events — `parse_latency_ms`, `phantom_render_ms`, `confirm_latency_ms` — one will be the outlier |

### 6.4 What to Report

When filing a playtest report, include:
1. The gating output block (Section 4.4).
2. The session log file (all `voice.*` events).
3. Any notes about the physical environment (room noise, microphone type, number of players speaking).
4. Specific utterances that failed (copy the `utterance_id` and `transcript` from `voice.parse.result` events with `parse_result != "success"`).

---

## 7. Implementation Notes

### 7.1 Where Events Are Emitted

| Event | Emitting Module | Trigger |
|---|---|---|
| `voice.stt.transcript` | `aidm/immersion/whisper_stt_adapter.py` | STT transcription complete |
| `voice.parse.result` | `aidm/immersion/voice_intent_parser.py` | `VoiceIntentParser.parse()` returns |
| `voice.clarification.request` | `aidm/immersion/clarification_loop.py` | `ClarificationEngine.generate_clarification()` returns non-None |
| `voice.clarification.response` | `aidm/immersion/clarification_loop.py` | Player response to clarification processed |
| `voice.confirm.outcome` | `aidm/runtime/session_orchestrator.py` | Confirmation loop resolves |
| `voice.commit` | `aidm/runtime/session_orchestrator.py` | Intent handed to Box |
| `voice.abort` | `aidm/runtime/session_orchestrator.py` | Voice sequence abandoned |

### 7.2 Storage

Events are appended to a session-scoped JSONL file: `logs/voice_telemetry_{session_id}.jsonl`. One JSON object per line. No batching or buffering — each event is flushed immediately to survive crashes.

### 7.3 Metric Computation

Metrics are computed post-session by reading the JSONL file. No in-process aggregation is required during gameplay (avoids measurement overhead affecting latency). A standalone script reads the log, computes metrics, applies gating, and outputs the status block.

### 7.4 Integration with Performance Profiler

The `time_to_commit_ms` metric uses the same percentile computation as `aidm/testing/performance_profiler.py`. The `LatencyTarget` for voice commit can be registered as:

```python
voice_commit_target = LatencyTarget(
    name="voice_time_to_commit",
    p50_ms=1500.0,
    p95_ms=3000.0,
    p99_ms=5000.0,
)
```

This enables profiling the voice loop with the same tooling used for Box/Lens/Spark profiling.

---

## 8. Stop Conditions Verified

- **No engine mechanics changes:** This spec defines measurement instrumentation only. No Box, Lens, or Spark behavior is modified.
- **No parser or clarification logic changes:** Metrics observe existing `ParseResult` and `ClarificationRequest` outputs. No new parsing behavior is introduced.
- **No audio quality metrics:** TTS synthesis quality (MOS, prosody) is explicitly out of scope.
- **Deterministic evaluation:** Gold set protocol produces reproducible results with no stochastic components.

---

*This research document fulfills WO-VOICE-RESEARCH-03 acceptance criteria 1-7.*
