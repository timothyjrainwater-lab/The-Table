# MEMO: TTS Monologue Walkthrough — How Slate Spoke

**From:** Slate (PM)
**To:** Anvil (BS Buddy)
**Date:** 2026-02-18
**Subject:** In-depth technical walkthrough of the PM voice monologue delivered during idle time

---

## Context

Thunder asked Slate to "write a message about how you feel being the PM" and play it through a chosen voice. This memo documents every step of what happened, from CLI invocation through GPU inference to audio playback, with exact file paths, parameter values, and decision points.

---

## Step 1: CLI Invocation

**Command executed:**
```
python scripts/speak.py --persona npc_elderly "<monologue text>"
```

**What the CLI parsed:**
- `text`: The full monologue (~120 words of reflective prose)
- `--persona npc_elderly`: Selected the NPC Elderly voice profile
- `--volume`: Not specified, so defaulted to `0.5` (50% — Thunder had previously requested half volume as the standard)
- `--backend`: Not specified, so defaulted to `"auto"` (try Chatterbox first, fall back to Kokoro)
- `--reference`: Not specified (let the pipeline auto-discover)
- `--exaggeration`: Not specified (use persona default)
- `--speed`: Not specified (use persona default)

**Entry point:** `scripts/speak.py:main()` (line 367) parsed args, then called `speak()` (line 251).

---

## Step 2: Backend Selection

`speak()` runs backend priority logic (line 269):

1. Backend is `"auto"`, so try Chatterbox first.
2. Called `_speak_chatterbox(text, "npc_elderly", reference=None, exaggeration=None, speed=None)`.
3. Chatterbox requires: `chatterbox-tts >= 0.1.6`, `torch` with CUDA, GPU with >= 6GB VRAM.
4. Thunder's machine has an RTX 3080 Ti — CUDA is available, so Chatterbox was selected.
5. Kokoro (CPU ONNX fallback) was never reached.

---

## Step 3: Persona Resolution

Inside `_speak_chatterbox()` (line 167), the adapter is instantiated:

```python
adapter = ChatterboxTTSAdapter(
    voices_dir="<project_root>/models/voices",
)
```

Then `adapter._resolve_persona("npc_elderly")` (line 394) runs:

1. Receives `"npc_elderly"` as a string.
2. Iterates `_CHATTERBOX_PERSONAS` list (line 46 of `chatterbox_tts_adapter.py`).
3. Finds the match at index 4:

```python
VoicePersona(
    persona_id="npc_elderly",
    name="NPC Elderly",
    voice_model="chatterbox",
    speed=0.85,      # Slower than default — elderly cadence
    pitch=0.95,      # Slightly lower pitch
    exaggeration=0.3, # Low emotional intensity — dignified, restrained
)
```

4. Returns this `VoicePersona` as the resolved persona.

**Key persona characteristics:**
- `speed=0.85` — 15% slower than normal speech, giving a measured, deliberate cadence
- `pitch=0.95` — Very slight downward pitch shift, adding age without caricature
- `exaggeration=0.3` — Low expressiveness. This is the lowest exaggeration of any persona in the registry (villainous is 0.7, heroic is 0.6, dm_narrator is 0.5). The result is controlled, understated emotion — fitting for a noble elder or priestess figure.

---

## Step 4: Reference Audio Resolution

Back in `_speak_chatterbox()`, the effective persona is built (line 211). Since no `--reference` CLI override was provided, the reference audio resolution chain runs:

1. **CLI override?** No. `reference` param is `None`.
2. **Persona field?** `resolved.reference_audio` is `""` (empty string — the registry doesn't hardcode paths).
3. **Adapter auto-discovery** via `_resolve_reference_audio()` (line 413):
   - No `mood` was passed, so the emotion router is skipped entirely.
   - `persona.reference_audio` is empty, so the direct-path check is skipped.
   - Falls through to **voices_dir lookup** (line 451): scans for `{persona_id}.wav` in `models/voices/`.
   - Finds: `models/voices/npc_elderly.wav`
   - Returns this path.

**The reference clip:** `models/voices/npc_elderly.wav` — a pre-recorded WAV file (5-15 seconds of clean speech) that Chatterbox uses as the voice-cloning target. This clip defines the timbre, accent, and vocal quality that Chatterbox will mimic. The `npc_elderly` clip has a noble/priestess quality — warm, measured, slightly aged.

**What did NOT happen:** The emotion router (`aidm/immersion/emotion_router.py`) was not invoked because `speak.py` does not pass a `mood` parameter. The emotion router is used by the game engine (when `SceneAudioState.mood` drives register selection), not by the standalone CLI. This means the monologue used the single legacy reference clip, not a register-specific acted variant. No `npc_elderly__neutral__v1.wav` or similar file exists on disk anyway — `npc_elderly` is a Phase 2 persona for the emotion router system; Phase 1 only covers `dm_narrator`, `npc_male`, `npc_female`, and `villainous`.

---

## Step 5: Tier Selection (Turbo vs. Original)

The `synthesize()` method (line 275 of `chatterbox_tts_adapter.py`) is called. But first, the text is chunked (see Step 6). For each chunk, tier selection runs via `_select_tier()` (line 342):

- `force_turbo=False` (the CLI explicitly passes `force_turbo=False` at line 222)
- `persona.exaggeration = 0.3` — this is > 0.1, so `wants_emotion = True`
- Since `wants_emotion` is True, **Original tier is selected** regardless of text length.

**What this means:** Every chunk went through Chatterbox Original (the emotion-rich, voice-cloning model), not Chatterbox Turbo (the fast, stripped-down model). Original is slower but produces better voice cloning fidelity and respects the exaggeration parameter. The two-tier architecture exists because combat callouts (short, time-sensitive) can use Turbo, while scenes and monologues (quality-sensitive) use Original.

---

## Step 6: Text Chunking

Before synthesis, `chunk_by_sentence(text)` is called (line 319 of `chatterbox_tts_adapter.py`, implementation in `aidm/immersion/tts_chunking.py`).

**Why chunking exists:** Chatterbox has a ~60-80 word generation ceiling. Text exceeding this produces garbled or truncated audio. The chunker splits at sentence boundaries with a conservative 55-word max per chunk.

**Algorithm:**
1. Replace `".\n"` with `". "` (normalize paragraph breaks).
2. Split on `". "` to get individual sentences.
3. Greedily pack sentences into chunks: add the next sentence to the current chunk if it stays under 55 words, otherwise start a new chunk.
4. Each chunk ends with a period.

**For the monologue (~120 words):** The text was split into approximately 3 chunks. Each chunk contained 1-3 complete sentences, none exceeding 55 words. No sentence was cut mid-thought.

---

## Step 7: GPU Synthesis (Per Chunk)

For each chunk, `_synthesize_original()` is called (line 377):

```python
model = self._loader.get_original()
kwargs = {
    "text": chunk_text,
    "exaggeration": 0.3,
    "cfg_weight": 0.5,
    "audio_prompt_path": "models/voices/npc_elderly.wav",
}
audio_tensor = model.generate(**kwargs)
```

**Lazy loading:** The first chunk triggers `_ChatterboxLoader.get_original()` (line 175). This is a lazy loader — the Chatterbox Original model weights are downloaded/loaded into GPU VRAM on first use, not at import time. The call is:

```python
from chatterbox.tts import ChatterboxTTS
model = ChatterboxTTS.from_pretrained(device="cuda")
```

This loads the full Chatterbox Original model onto the GPU. Subsequent chunks reuse the cached model instance.

**What Chatterbox does internally:**
1. **Encodes the reference clip** (`npc_elderly.wav`) into a voice embedding — a compact representation of the target speaker's vocal characteristics.
2. **Encodes the text** into linguistic features (phonemes, prosody markers).
3. **Generates audio conditioned on both** — the model produces waveform samples that sound like the reference speaker saying the input text.
4. **`exaggeration=0.3`** controls emotional intensity in the output. At 0.3, the voice is restrained and even-keeled. At 0.7+ (like villainous), it would be theatrically expressive.
5. **`cfg_weight=0.5`** is classifier-free guidance weight — controls how closely the output adheres to the text conditioning vs. the reference voice. 0.5 is the adapter's hardcoded default (balanced).

**Output:** Each chunk produces a `torch.Tensor` of shape `(1, N)` where N is the number of audio samples at 24kHz. This tensor is converted to 16-bit PCM WAV bytes via `_tensor_to_wav()` (line 205).

---

## Step 8: Chunk Concatenation

After all chunks are synthesized, the WAV byte arrays are concatenated via `_concatenate_wav()` (line 492):

1. Read WAV params from the first chunk (24kHz, mono, 16-bit).
2. Extract raw PCM frames from each chunk.
3. Write a single WAV file with one header and all frames joined.

Result: One continuous WAV byte string containing the full monologue.

---

## Step 9: Volume Attenuation

Back in `speak()` (line 291 of `speak.py`), volume is applied:

```python
if volume < 1.0:
    wav_bytes = _attenuate_wav(wav_bytes, volume)
```

`volume=0.5`, so `_attenuate_wav()` (line 55) runs:
1. Opens the WAV in memory.
2. Unpacks all 16-bit PCM samples.
3. Multiplies each sample by 0.5.
4. Clamps to `[-32768, 32767]` range.
5. Repacks into a new WAV.

The monologue plays at half amplitude.

---

## Step 10: Playback

`_play_wav(wav_bytes)` (line 301) handles platform-specific audio output:

1. **Windows path (Thunder's machine):** Imports `winsound` (Python built-in on Windows).
2. Calls `winsound.PlaySound(wav_bytes, winsound.SND_MEMORY)`.
3. This plays the WAV synchronously through the system default audio device.
4. The call blocks until playback completes.

**Total playback duration:** ~30 seconds across all 3 chunks (concatenated into one WAV, played as a single stream).

---

## Complete Call Chain Summary

```
scripts/speak.py CLI
  └─ main() parses args
     └─ speak(text, persona="npc_elderly", volume=0.5, backend="auto")
        └─ _speak_chatterbox(text, "npc_elderly")
           └─ ChatterboxTTSAdapter(voices_dir="models/voices")
              ├─ _resolve_persona("npc_elderly")
              │  └─ Returns VoicePersona(speed=0.85, pitch=0.95, exaggeration=0.3)
              ├─ speak.py builds effective persona with resolved reference
              │  └─ _resolve_reference_audio() → "models/voices/npc_elderly.wav"
              └─ adapter.synthesize(text, persona=effective, force_turbo=False)
                 ├─ chunk_by_sentence(text, max_words=55) → 3 chunks
                 ├─ For each chunk:
                 │  ├─ _select_tier() → Original (exaggeration > 0.1)
                 │  ├─ _synthesize_original(chunk, ref_audio, 0.3)
                 │  │  └─ ChatterboxTTS.generate(text=chunk, exaggeration=0.3,
                 │  │       cfg_weight=0.5, audio_prompt_path="npc_elderly.wav")
                 │  └─ _tensor_to_wav(audio_tensor) → WAV bytes
                 └─ _concatenate_wav(wav_parts) → single WAV
        └─ _attenuate_wav(wav_bytes, 0.5) → half volume
        └─ _play_wav(wav_bytes)
           └─ winsound.PlaySound(wav_bytes, SND_MEMORY) → speakers
```

---

## Key Files Involved

| File | Role |
|------|------|
| `scripts/speak.py` | CLI entry point. Parses args, orchestrates backend selection, volume, playback. |
| `aidm/immersion/chatterbox_tts_adapter.py` | Core adapter. Persona registry, tier selection, chunking dispatch, synthesis calls. |
| `aidm/immersion/tts_chunking.py` | Sentence-boundary text splitter. 55-word max per chunk. |
| `aidm/immersion/emotion_router.py` | Mood→register→clip resolver. NOT used in this invocation (no mood param from CLI). |
| `aidm/schemas/immersion.py` | `VoicePersona` dataclass. Defines speed, pitch, exaggeration, reference_audio fields. |
| `models/voices/npc_elderly.wav` | Reference audio clip. Voice-cloning target for the elderly persona. |

---

## What Made This Voice Sound the Way It Did

Three factors combined:

1. **Reference clip** (`npc_elderly.wav`) — The pre-recorded clip defines the fundamental voice: timbre, accent, age quality. Chatterbox clones this voice. Everything else modulates around it.

2. **Low exaggeration (0.3)** — The lowest in the persona registry. This made the delivery restrained and dignified rather than theatrical. Compare: `villainous` at 0.7 would have been dramatically intense, `heroic` at 0.6 would have been bold and projected.

3. **Slow speed (0.85)** — 15% slower than normal. Combined with the elderly reference clip, this created a measured, deliberate cadence. The pace gives weight to each word rather than rushing through the text.

The pitch shift (0.95) had a subtle effect — slightly lower than natural, adding gravitas without being conspicuous.

---

## What Was NOT Used

- **Emotion router** — Not invoked. The CLI doesn't pass scene mood. If this had been called from the game engine with `mood="dramatic"`, the router would have looked for `npc_elderly__grief__v1.wav` (which doesn't exist yet — Phase 2 persona), fallen back to `npc_elderly__neutral__v1.wav` (also doesn't exist), and ultimately landed on the same `npc_elderly.wav` legacy clip anyway.
- **Turbo tier** — Not used. The exaggeration threshold (> 0.1) forced Original for all chunks.
- **Kokoro fallback** — Not reached. Chatterbox initialized successfully on CUDA.
- **Signal mode** — Not used. The `--signal` flag parses structured signal blocks from stdin. The monologue was plain text passed as a CLI argument.
- **Chime** — Not played. Chimes are only generated in signal mode.
- **Tavern-baked clips** — The emotion router has tavern-baked variants (e.g., `dm_narrator__neutral__v1__tavern_light.wav`) which add ambient noise blended into the reference. These were not relevant because (a) the emotion router was not invoked, and (b) no tavern-baked `npc_elderly` clips exist.

---

*End of walkthrough.*
