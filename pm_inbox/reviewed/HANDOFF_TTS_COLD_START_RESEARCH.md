# HANDOFF: TTS Cold Start Latency — Research Packet for Assistant

**From:** BS Buddy (Opus 4.6), advisory session
**Date:** 2026-02-14
**Lifecycle:** NEW
**For:** Assistant role (next session)
**Not for:** PM (this is pre-PM research — don't consume PM context until findings are organized)

---

## Problem

Every `scripts/speak.py` invocation cold-loads the entire Chatterbox model into VRAM before inference begins. This adds 3-4 seconds of dead air before any audio plays. For single signals ("the forge is quiet") this is acceptable. For sequential narration in combat — where multiple lines need to play back-to-back — the gap kills pacing.

**Discovered during:** BS Buddy session testing voice output. Two consecutive speak.py calls had a noticeable dead gap between them. The model reloaded from scratch on the second call.

**Why it matters for the product:** The DM narration system will need continuous voice output during combat. A fighter attacks, narration plays. A spell resolves, narration plays. If each narration line has a 3-4 second reload penalty, the voice system feels broken even if the audio quality is perfect.

---

## What Needs Research

### 1. Persistent Model Server
Can Chatterbox run as a daemon that stays loaded in VRAM and accepts text over a socket, pipe, or HTTP endpoint? First call pays the load cost, every subsequent call is just inference (~10 seconds for a sentence at ~40 it/s).

**Key questions:**
- Does Chatterbox's API support this natively?
- What's the VRAM footprint when idle? (Measure on the 3080 Ti)
- Can it handle concurrent requests or is it single-threaded?
- **NEW (BS Buddy QA finding):** Multiple concurrent speak.py calls overlay audio on the same device — no playback queue, no mutex. A persistent server with a sequential playback queue would solve both cold start AND audio overlap in one shot.

### 2. Subprocess Keep-Alive
Lighter alternative: keep the Python process alive between calls. speak.py currently loads, synthesizes, plays, exits. Could it instead loop on stdin, reading lines and synthesizing without reloading?

**Key questions:**
- How much of the 3-4 second startup is model loading vs. Python/torch initialization?
- Can the model be loaded once and reused across multiple synthesize() calls? (The `ChatterboxTTSAdapter` already supports this — it's the CLI wrapper that doesn't)

### 3. Streaming Output
Can Chatterbox generate audio while playing the beginning of the utterance? Instead of "generate all 1000 steps, then play," can it "generate 200 steps, start playing, generate more while audio plays"?

**Key questions:**
- Does the Chatterbox sampling loop support chunk-level output?
- What's the minimum viable chunk size before audio quality degrades?
- Does this interact with the sentence-boundary chunker in speak.py?

### 4. Kokoro Fallback Comparison
Kokoro is the CPU fallback. Does it have the same cold start problem, or is ONNX runtime fast enough that it doesn't matter?

**Key questions:**
- Measure Kokoro cold start time
- Compare audio quality at conversational lengths (not just short signals)
- Is Kokoro viable as the "fast path" for sequential lines while Chatterbox handles single high-quality outputs?

### 5. External Prior Art
Other TTS engines have solved this. What can we learn?

**Check:**
- XTTS v2 — has a server mode (TTS-server). How does it handle persistent loading?
- Bark — any daemon/server patterns in the community?
- Tortoise-TTS — known for being slow. How did projects work around it?
- Piper — lightweight, fast. Different architecture but may inform the "fast path" option.

---

## Current Infrastructure (for context)

- `scripts/speak.py` — CLI entry point. Loads model, synthesizes, plays, exits. 452 lines.
- `aidm/immersion/chatterbox_tts_adapter.py` — Adapter class. Already supports multiple synthesize() calls on a single instance (model loaded once via lazy loader). The problem is the CLI, not the adapter.
- `aidm/immersion/kokoro_tts_adapter.py` — CPU fallback adapter. ONNX-based.
- `models/voices/` — 3 reference WAV files for voice cloning.
- Sentence chunker in speak.py splits text at `. ` boundaries, max 55 words per chunk. Each chunk currently triggers a separate model call (but within one process, so the model stays loaded for `--signal --full` mode).

**Important detail:** The `--signal --full` mode already handles multiple chunks within a single process invocation — the model loads once and synthesizes each chunk sequentially. The cold start problem only hits when speak.py is called as separate processes (which is how the BS buddy and idle signals invoke it).

---

## Expected Output

A research memo with:
1. Measured cold start time breakdown (Python init vs. torch init vs. model load vs. first inference)
2. VRAM measurement of Chatterbox idle in memory
3. Recommendation: server daemon vs. keep-alive subprocess vs. other
4. Prototype if straightforward (e.g., a `speak_server.py` that wraps the existing adapter)
5. Interaction notes with WO-TTS-CHUNKING (Horizon 1) — how does this affect the chunking WO's scope?

---

## Routing

This is assistant-level research. When findings are organized:
1. Assistant writes a research memo
2. BS buddy reviews it (optional second pass)
3. Consolidated findings go to PM as input for WO-TTS-CHUNKING drafting
4. PM decides whether this becomes a separate WO or gets folded into TTS-CHUNKING

Do NOT send raw research to the PM. Filter first.

---

*End of handoff.*
