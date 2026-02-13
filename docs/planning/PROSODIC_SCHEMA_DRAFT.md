# AIDM Prosodic Annotation Schema (PAS) v0.1

**Work Order:** WO-RQ-PROSODIC-001
**Layer:** Lens -> Immersion (TTS)
**Status:** Design Draft — research complete, implementation not yet scoped
**Date:** 2026-02-13
**Origin:** GPT cross-model review, refined against running AIDM stack

---

## 1. Design Principles

1. **Declarative, not expressive.**
   The model does not act. It annotates intent.

2. **Bounded control.**
   Only predefined prosodic dimensions may be modified. All fields are clamped.

3. **Prosodic intent determinism.**
   Given identical text + identical prosodic parameters + identical reference voice + identical seed, the resulting acoustic envelope must remain within an acceptable tolerance band. Waveform hash equality is not required. Envelope similarity is.

4. **Non-manipulative defaults.**
   Emotional amplification is not permitted unless explicitly tagged. Safety clamps apply per-mode.

5. **Human-auditable.**
   Prosodic parameters must be inspectable in structured logs. No hidden tonal shifts.

6. **Reference voice as constraint surface.**
   The reference audio seed defines the baseline cadence, tonal bias, and dynamic envelope. Prosodic adjustments operate as bounded deviations from that baseline, not replacements.

---

## 2. Architectural Placement

```
Box   -> generates semantic output
Lens  -> selects prosodic preset based on intent classification
Immersion/TTS -> applies prosodic parameters during synthesis
```

No feedback loop from Immersion back into Lens.
No feedback loop from Immersion back into Box.

---

## 3. Control Model

PAS uses **structured dataclass fields**, not inline markup.

Phase 1 extends `VoicePersona` (or a sibling `ProsodicProfile`) with bounded fields. No XML parsing layer. No markup language. Box-clean structured data only.

---

## 4. Prosodic Fields

### 4.1 Pace (tempo control)

```python
pace: float  # 0.8 - 1.2, default 1.0
```

Hard-clamped by TTS layer. Values outside range are silently clamped.

### 4.2 Emphasis Level

```python
class EmphasisLevel(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"       # context-gated, see Section 6

emphasis_level: EmphasisLevel  # default: NONE
```

### 4.3 Tone Mode

```python
class ToneMode(str, Enum):
    NEUTRAL = "neutral"
    CALM = "calm"
    DIRECTIVE = "directive"
    REFLECTIVE = "reflective"
    COMBAT = "combat"

tone_mode: ToneMode  # default: NEUTRAL
```

These map to preset pitch + intensity envelopes inside TTS. They are bounded presets, not free-form.

### 4.4 Pause Profile

```python
class PauseProfile(str, Enum):
    MINIMAL = "minimal"     # operator readback, tight pacing
    MODERATE = "moderate"   # scene narration, natural breathing
    DRAMATIC = "dramatic"   # reveals, tension, key moments

pause_profile: PauseProfile  # default: MINIMAL
```

Max pause duration hard-capped at 750ms regardless of profile.

### 4.5 Pitch Offset

```python
pitch_offset: int  # -2 to +2, default 0
```

Subtle grounding shifts only. Not voice transformation.

### 4.6 Clarity Mode

```python
class ClarityMode(str, Enum):
    NORMAL = "normal"
    HIGH = "high"       # slower articulation, rule explanations

clarity_mode: ClarityMode  # default: NORMAL
```

---

## 5. Mode-Based Presets

Instead of setting every field manually, Lens selects a preset bundle based on system state:

### Operator Mode
- pace: 1.0
- tone: directive
- clarity: high
- pause: minimal
- emphasis_max: LOW

### Reflection Mode
- pace: 0.9
- tone: reflective
- pause: moderate
- emphasis_max: MEDIUM

### Combat Narration Mode
- pace: 1.05
- tone: combat
- pause: minimal
- emphasis_max: HIGH

### Scene Narration Mode
- pace: 0.92
- tone: calm
- pause: moderate
- emphasis_max: MEDIUM

---

## 6. Context-Gated Safety Constraints

Emphasis level is bounded per mode, not globally:

```python
_EMPHASIS_CEILING = {
    "operator":  EmphasisLevel.LOW,
    "reflection": EmphasisLevel.MEDIUM,
    "combat":    EmphasisLevel.HIGH,
    "scene":     EmphasisLevel.MEDIUM,
}

def clamp_emphasis(mode: str, requested: EmphasisLevel) -> EmphasisLevel:
    ceiling = _EMPHASIS_CEILING.get(mode, EmphasisLevel.LOW)
    if requested.value > ceiling.value:
        return ceiling
    return requested
```

### Globally Disallowed

- Emotional escalation curves (progressive amplification across turns)
- Volume ramping beyond preset thresholds
- Persuasive amplification markers
- Hidden tonal shifts without logged parameters
- Dynamic emotional drift mid-sentence unless explicitly parameterized

If a parameter violates constraints, TTS clamps to safe default. Silently. No error, no drama.

---

## 7. Reference Voice Integration

The reference audio clip is a first-class prosodic control surface:

- **Baseline cadence**: The reference clip's natural speaking rhythm anchors all pace adjustments. `pace: 1.0` means "match the reference."
- **Tonal bias**: The reference clip's pitch contour biases all pitch_offset adjustments. Offsets are deviations from the reference, not absolute values.
- **Dynamic envelope**: The reference clip's energy profile constrains exaggeration. High exaggeration on a calm reference produces moderate output, not theatrical output.

Voice cloning fidelity depends on reference clip quality:
- 24kHz native sample rate (no resample)
- 5-15 seconds of clean speech
- fp32 model output preferred over quantized
- Single speaker, minimal background

Current production reference: `models/voices/signal_reference_michael_24k.wav`
Pipeline: Kokoro am_michael fp32 24kHz -> Chatterbox Original voice clone

---

## 8. Implementation Status

### Current Stack

| Backend     | Device | Prosody Support | Status |
|------------|--------|-----------------|--------|
| Chatterbox | GPU    | tempo, pitch, exaggeration via VoicePersona | Running |
| Kokoro     | CPU    | speed, voice selection | Running (fallback) |
| Orpheus    | TBD    | TBD | Not integrated |

### What Exists Today

- `VoicePersona` dataclass with: speed, pitch, exaggeration, reference_audio
- Arbor voice profile: speed=0.88, pitch=1.0, exaggeration=0.15
- Voice cloning pipeline: Kokoro -> Chatterbox via reference clip
- `scripts/speak.py`: operator signal voice using Arbor profile

### What's Missing

- Prosodic fields beyond speed/pitch/exaggeration (no pause, clarity, tone_mode, emphasis)
- Mode-based preset selection (currently hardcoded to Arbor)
- Context-gated emphasis clamping
- Prosodic parameter logging in event stream

---

## 9. Implementation Path

### Phase 1: Vocabulary

Extend `VoicePersona` or create sibling `ProsodicProfile` with:
- pace (float, clamped)
- emphasis_level (enum)
- tone_mode (enum)

Hardcode 3-4 preset bundles. Wire into speak.py.

### Phase 2: Integration

- Add pause_profile and clarity_mode
- Add pitch_offset (bounded)
- Wire preset selection to play loop state (combat vs narration vs operator)
- Log prosodic parameters alongside events

### Phase 3: Verification

- Prosodic envelope comparison tooling (not waveform hash, envelope similarity)
- A/B testing harness for preset tuning
- Listening fatigue metrics (session duration before operator requests volume change)

---

## 10. Design Rationale

This schema increases signal fidelity between system intent and human perception without:
- Breaking authority split (Box never controls voice)
- Introducing emotional manipulation (all amplification is bounded and logged)
- Adding parsing overhead (structured data, not markup)
- Requiring new dependencies (extends existing VoicePersona)

The reference voice as constraint surface ensures that prosodic adjustments stay grounded in a known acoustic baseline rather than drifting into unconstrained synthesis space.

Building vocabulary first. Implementation second.
