# MEMO: TTS Audio Pipeline Architecture — How It Works Now

**Lifecycle:** NEW
**From:** BS Buddy (Gravel) — 2026-02-18
**To:** PM
**Priority:** READ THIS BEFORE ISSUING VOICE-RELATED WOs

---

## Why This Memo Exists

The voice pipeline has been restructured. If you issue WOs that touch audio output without understanding the current architecture, you will waste builder context and operator patience. This is the reference doc.

---

## Architecture (current, validated 2026-02-18)

### Signal Flow

```
Text → speak.py → Chatterbox TTS Engine → Audio Output
                      ↑
              Reference Clip (determines voice identity + room acoustics)
                      ↑
              Emotion Router (selects clip based on persona + mood)
                      ↑
              Tavern-Baked CREMA-D Clips (16 active, 4 personas × 4 registers)
```

### The Key Insight You Need To Internalize

**Chatterbox clones the ENTIRE acoustic environment from the reference clip, not just the voice.**

This means:
- If the reference was recorded in a dry studio booth → output sounds clinical/dry
- If the reference has room ambience → output sounds like it's in a room
- Post-processing the OUTPUT with reverb/room effects does NOT work. It stacks spaces. The booth is already baked into the signal.
- Pre-processing the REFERENCE with room ambience DOES work. Chatterbox clones the room along with the voice.

This was validated empirically on 2026-02-18 across multiple A/B tests with operator confirmation.

### Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `speak.py` | `scripts/speak.py` | CLI entry point. Accepts `--persona`, `--reference`, `--exaggeration`, `--speed` |
| Chatterbox TTS Adapter | `aidm/immersion/chatterbox_tts_adapter.py` | 8 persona presets (speed/pitch/exaggeration). Interfaces with Chatterbox engine |
| Emotion Router | `aidm/immersion/emotion_router.py` | Deterministic mood→register→clip mapping. No LLM involvement |
| Reference Clips (active) | `models/voices/*__v1.wav` | 16 tavern-baked CREMA-D clips. 4 personas × 4 emotion registers |
| Reference Clips (dry backup) | `models/voices/dry_backup/` | Original dry CREMA-D clips. DO NOT use these — they have booth bleed |
| Legacy Persona Refs | `models/voices/{persona_id}.wav` | Fallback if no emotion-register clip found |
| Signal Refs | `models/voices/signal_reference_*.wav` | michael (Arbor reserved), george, default |

### Emotion Router Mapping

```
Mood "neutral"  → register "neutral"  → {persona}__neutral__v1.wav
Mood "peaceful" → register "neutral"  → {persona}__neutral__v1.wav
Mood "tense"    → register "tense"    → {persona}__tense__v1.wav
Mood "combat"   → register "angry"    → {persona}__angry__v1.wav
Mood "dramatic" → register "grief"    → {persona}__grief__v1.wav
                   (override: dramatic + triumph → neutral)
```

### Phase 1 Personas With Multi-Register Clips

`dm_narrator`, `npc_male`, `npc_female`, `villainous`

### Tavern Bake Recipe (frozen — do not change without operator validation)

Medium intensity. Synthetic IR with:
- Early reflections at 5/8/12/17/22/28/35ms, amplitudes -8 to -22dB
- Diffuse tail 40-200ms, RT60=200ms, tail gain 0.015, LP 4kHz
- Seed=7 for reproducibility
- Correlation to dry original: ~0.85-0.91 range (varies by clip)

Applied to the CREMA-D reference clips BEFORE they go to Chatterbox. Not applied to output.

---

## What Still Doesn't Work

1. **Monster/non-human voices.** Pitch-shifting human refs doesn't fool Chatterbox. Need actual guttural source material. CC-BY candidates identified on Freesound, download pending.
2. **Wide emotional range.** CREMA-D actors are academic, not theatrical. Emotion is present but narrow. "Actor sounds a little bored." Higher-performance source clips would fix this.
3. **Cold start latency.** Each speak.py invocation cold-loads the model (~3-4s). Persistent server would solve.
4. **Audio overlap.** No playback queue. Multiple concurrent calls play simultaneously. One-call-per-response rule in effect.

---

## What You Must Not Do

- **Do NOT issue WOs to post-process Chatterbox output with reverb/room effects.** This was tested exhaustively and does not work. The booth is in the signal. The fix is upstream.
- **Do NOT touch the tavern bake recipe** without operator ears-on validation. Correlation metrics don't measure speaker identity — only the operator's ears gate this.
- **Do NOT use Arbor's exact profile** (michael ref + speed 0.88 + pitch 1.0 + exaggeration 0.15) for any non-signal purpose.
- **Do NOT replace the active `__v1.wav` files** with dry clips. The dry originals are in `dry_backup/` for reference only.

---

## What You Should Do

When the operator tells you to play audio — play the audio. The pipeline is wired, validated, and deployed. `speak.py` works. The emotion router works. The tavern-baked refs are in place. There is no technical blocker preventing voice output on every narration event.

Wire it up. Use it. That's the whole point.

---

*Filed by Tharrik "Gravel" Ashbone. Seven wisdom, zero regrets.*

---

## Retrospective

**Fragility:** `speak.py` depends on the chatterbox model being loaded and GPU memory being available. Long sessions can exhaust GPU memory if audio generation is called repeatedly without cooldown. Monitor for OOM errors in production.

**Process feedback:** This memo was filed because a WO was nearly issued that would have wired audio output in the wrong layer. The memo pattern (file first, then issue WO) saved builder context. The pattern works — use it for any subsystem with non-obvious constraints.

**Methodology insight:** The "tavern bake" reference approach (baking ambient room tone into the reference audio rather than adding it in post) solved a purity problem elegantly. This pattern (bake the context into the reference, not the generation) is worth reapplying to other audio scenarios.

**Concern:** The emotion router is wired but sparsely tested across the full persona × content-type matrix. High exaggeration values still produce clipping on some reference combos. Systematic coverage testing (not just happy-path) is outstanding.
