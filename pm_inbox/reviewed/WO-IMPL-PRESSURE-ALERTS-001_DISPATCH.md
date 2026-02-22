# WO-IMPL-PRESSURE-ALERTS-001 — Pressure-to-Prosodic Modulation

**Type:** CODE
**Priority:** BURST-001 Tier 4.3
**Depends on:** WO-VOICE-PAS-PRESETS-001 (ACCEPTED), WO-VOICE-PRESSURE-IMPL-001 (ACCEPTED)
**Blocked by:** Nothing — ready to dispatch
**Lifecycle:** NEW

---

## Target Lock

Wire the existing boundary pressure evaluation (GREEN/YELLOW/RED) into the prosodic preset pipeline so that voice delivery shifts automatically when the system is under pressure. GREEN = no change. YELLOW = boost clarity and emphasis floor. RED = directive tone, maximum clarity, minimal pauses (theoretical — Spark doesn't fire on RED, but the template fallback still speaks).

This is the second-to-last BURST-001 WO. After this and 4.4, only 5.5 (Playtest v1) remains.

## Binary Decisions (all resolved)

| # | Question | Answer | Source |
|---|----------|--------|--------|
| 1 | Where does the pressure→prosodic mapping live? | New method `apply_pressure_modulation()` on `ProsodicPresetManager` | Same class that owns mode presets |
| 2 | How does `_synthesize_tts()` get the pressure level? | Pass `pressure_level` as new parameter from `_narrate_and_output()` | Cleanest seam — no instance state |
| 3 | Does RED modulation matter if Spark doesn't fire? | Yes — template fallback text is still spoken via TTS | Belt-and-suspenders |
| 4 | Should pressure override mode presets or compose? | Compose — pressure applies AFTER mode preset, uses `dataclasses.replace()` | Same pattern as existing preset overlay |

## Contract Spec

**Source:** Boundary Pressure Contract §6.3 (pressure→response mapping), Prosodic Schema Draft §5-6 (mode presets + emphasis clamping), VoicePersona fields in `aidm/schemas/immersion.py`

### Pressure-to-Prosodic Mapping

| Pressure | tone_mode | clarity_mode | emphasis_level | pause_profile | pace | Rationale |
|----------|-----------|-------------|----------------|---------------|------|-----------|
| **GREEN** | (no change) | (no change) | (no change) | (no change) | (no change) | System healthy — trust mode preset |
| **YELLOW** | (no change) | **HIGH** | **floor MEDIUM** | (no change) | (no change) | Advisory — boost clarity, ensure emphasis isn't below MEDIUM |
| **RED** | **DIRECTIVE** | **HIGH** | **LOW** | **MINIMAL** | **1.0** | Fail-closed signal — clear, concise, no drama |

"Floor MEDIUM" means: if the mode preset already set emphasis >= MEDIUM, keep it. If emphasis is below MEDIUM (e.g., operator mode sets LOW), raise it to MEDIUM.

### Integration Seam: `_synthesize_tts()` Signature Change

Current signature (line 1021-1022):
```python
def _synthesize_tts(self, narration_text: str, brief: NarrativeBrief) -> Optional[bytes]:
```

New signature:
```python
def _synthesize_tts(
    self, narration_text: str, brief: NarrativeBrief,
    pressure_level: PressureLevel = PressureLevel.GREEN,
) -> Optional[bytes]:
```

### Integration Seam: `_narrate_and_output()` Plumbing

`_generate_narration()` already computes `pressure_result` (line 890). Currently it only uses the result for RED gate (skip Spark) and logging. The result needs to be returned alongside `(narration_text, provenance)` so `_narrate_and_output()` can pass it to `_synthesize_tts()`.

Option: Change `_generate_narration()` to return a 3-tuple `(narration_text, provenance, pressure_level)`. The caller at line 843-845 unpacks accordingly.

```python
# Before (line 843-845):
narration_text, provenance = self._generate_narration(
    brief, session_context, events, segment_summaries=segment_summaries,
)

# After:
narration_text, provenance, pressure_level = self._generate_narration(
    brief, session_context, events, segment_summaries=segment_summaries,
)

# Before (line 848):
narration_audio = self._synthesize_tts(narration_text, brief)

# After:
narration_audio = self._synthesize_tts(narration_text, brief, pressure_level=pressure_level)
```

### New Method: `ProsodicPresetManager.apply_pressure_modulation()`

```python
def apply_pressure_modulation(
    self, persona: VoicePersona, pressure_level: PressureLevel,
) -> VoicePersona:
    """Overlay pressure-based prosodic adjustments AFTER mode preset.

    GREEN: no-op (return persona unchanged).
    YELLOW: clarity → HIGH, emphasis floor → MEDIUM.
    RED: tone → DIRECTIVE, clarity → HIGH, emphasis → LOW,
         pause → MINIMAL, pace → 1.0.

    Args:
        persona: VoicePersona with mode preset already applied.
        pressure_level: Current boundary pressure level.

    Returns:
        New VoicePersona with pressure modulation applied.
    """
```

### Wire into `_synthesize_tts()`

Insert between existing preset application (line 1057) and TTS call (line 1061):

```python
# Line 1057 (existing):
persona = self._preset_manager.apply_preset(persona, preset_mode)

# NEW — WO-IMPL-PRESSURE-ALERTS-001:
persona = self._preset_manager.apply_pressure_modulation(persona, pressure_level)

# Line 1061 (existing):
return self._tts.synthesize(narration_text, persona=persona)
```

### Logging

Add to `_log_pressure_event()` extra dict:
```python
"prosodic_modulation": pressure_level.value,  # "GREEN", "YELLOW", "RED"
```

## Implementation Plan

1. Add `apply_pressure_modulation()` to `ProsodicPresetManager` — pure function, uses `dataclasses.replace()`
2. Change `_generate_narration()` return type to 3-tuple `(str, str, PressureLevel)`
3. Update `_narrate_and_output()` to unpack 3-tuple and pass pressure_level to `_synthesize_tts()`
4. Add `pressure_level` parameter to `_synthesize_tts()` with `PressureLevel.GREEN` default
5. Wire `apply_pressure_modulation()` call into `_synthesize_tts()` after preset application
6. Add `"prosodic_modulation"` field to pressure event log
7. Write gate tests (see gate spec below)
8. Run full suite regression

### Out of Scope

- Verbal ALERT lines (e.g., "The boundary is under pressure") — not in this WO
- Pressure level display in CLI output — already handled by existing logging
- Changes to pressure evaluation logic — that's ACCEPTED (Tier 2)
- Changes to mode preset definitions — that's ACCEPTED (Tier 4.2)

## Gate Specification

**New gate:** Gate V (Pressure Alerts)

| Test ID | Assertion | Type |
|---------|-----------|------|
| V-01 | `apply_pressure_modulation(persona, GREEN)` returns persona unchanged | identity |
| V-02 | `apply_pressure_modulation(persona, YELLOW)` sets clarity_mode=HIGH | field check |
| V-03 | `apply_pressure_modulation(persona, YELLOW)` raises emphasis from LOW to MEDIUM | floor check |
| V-04 | `apply_pressure_modulation(persona, YELLOW)` keeps emphasis at HIGH if already HIGH | ceiling check |
| V-05 | `apply_pressure_modulation(persona, RED)` sets tone_mode=DIRECTIVE | field check |
| V-06 | `apply_pressure_modulation(persona, RED)` sets clarity_mode=HIGH, pause_profile=MINIMAL | field check |
| V-07 | `apply_pressure_modulation(persona, RED)` sets emphasis_level=LOW, pace=1.0 | field check |
| V-08 | Full pipeline: mode preset + GREEN pressure = same as mode preset alone | composition |
| V-09 | Full pipeline: combat preset + YELLOW pressure = combat fields + HIGH clarity + MEDIUM+ emphasis | composition |
| V-10 | Full pipeline: operator preset + YELLOW pressure = operator fields + HIGH clarity + MEDIUM emphasis (floor applied) | composition |
| V-11 | Full pipeline: reflection preset + RED pressure = RED overrides all prosodic fields | composition |
| V-12 | `_generate_narration()` returns 3-tuple (text, provenance, pressure_level) | return type |
| V-13 | `_synthesize_tts()` accepts pressure_level parameter, defaults to GREEN | signature |
| V-14 | Full suite regression | regression |

**Expected test count:** 14 (13 functional + regression run).

## Integration Seams

- `aidm/immersion/prosodic_preset_manager.py` — Add `apply_pressure_modulation()` method
- `aidm/runtime/session_orchestrator.py:843-845` — Unpack 3-tuple from `_generate_narration()`
- `aidm/runtime/session_orchestrator.py:848` — Pass pressure_level to `_synthesize_tts()`
- `aidm/runtime/session_orchestrator.py:1021-1064` — Add pressure_level param, wire modulation call
- `aidm/runtime/session_orchestrator.py:858-906` — Return pressure_level as 3rd element of tuple

## Files to Read

1. `aidm/immersion/prosodic_preset_manager.py` — Existing preset application pattern
2. `aidm/runtime/session_orchestrator.py` — `_synthesize_tts()`, `_generate_narration()`, `_narrate_and_output()`
3. `aidm/schemas/boundary_pressure.py` — PressureLevel enum
4. `aidm/schemas/immersion.py` — VoicePersona, ToneMode, ClarityMode, EmphasisLevel, PauseProfile

## Preflight

```bash
python scripts/preflight_canary.py
python -m pytest tests/test_prosodic_presets.py -v
python -m pytest tests/ -x --ignore=tests/test_heuristics_image_critic.py --ignore=tests/test_ws_bridge.py
```

## Delivery Footer

**Commit requirement:** After all tests pass, commit changes with a descriptive message referencing this WO ID.
**Debrief format:** CODE — 500 words max, 5 sections + Radar (3 lines).
**Radar bank:** (1) Anything that broke unexpectedly, (2) Anything that was harder than expected, (3) Anything the next WO should know.
