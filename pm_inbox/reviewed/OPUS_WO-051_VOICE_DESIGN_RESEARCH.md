# WO-051: Voice Cloning Research — Reference Clip Best Practices & Archetype Recipes
**Dispatched by:** Opus (PM)
**Date:** 2026-02-12
**Phase:** Immersion (Voice Pipeline)
**Priority:** Research (non-blocking)
**Status:** DISPATCHED

---

## Objective

Research and document best practices for creating distinct fantasy character voices using voice cloning TTS (Chatterbox). Produce a **Voice Design Guide** with archetype recipes, parameter presets, and reference clip sourcing strategy.

---

## Context

ChatterboxTTSAdapter is built and tested (32 tests, all pass). It supports:
- Voice cloning via `audio_prompt_path` (5-15s reference WAV per character)
- Two-tier synthesis: Turbo (speed) and Original (emotion control via `exaggeration`)
- VoicePersona fields: `reference_audio`, `pitch`, `speed`, `exaggeration`

The adapter works — but we have no reference clips. Without curated voice references, every character sounds like the same default female voice. This research produces the knowledge needed to build a diverse voice roster.

---

## Deliverables

### 1. Reference Clip Quality Guide
Research and document:
- **Optimal clip length** — How long should reference clips be? (Chatterbox Original needs 6s encoder + 10s decoder; Turbo needs 15s encoder + 10s decoder)
- **Audio quality requirements** — Sample rate, bit depth, noise floor, room tone
- **Content guidelines** — What should the speaker say in the reference clip? Does content matter, or just vocal characteristics?
- **What degrades quality** — Background noise, music, reverb, compression artifacts, multiple speakers
- **Format requirements** — WAV vs FLAC vs MP3, mono vs stereo

### 2. Fantasy Voice Archetype Recipes
For each archetype, document a "recipe" — how to produce that voice using reference clips + VoicePersona parameters:

| Archetype | Use Case | Recipe Approach |
|-----------|----------|-----------------|
| **Authoritative Narrator** | DM narration, scene descriptions | Pitch, speed, exaggeration settings |
| **Deep Dwarf / Barbarian** | Vognar, dwarven NPCs | Reference voice type + pitch/speed adjustments |
| **Ethereal Elf / Fey** | Elven NPCs, fey creatures | Reference voice type + pitch/speed adjustments |
| **Gravelly Villain** | BBEG, undead, dark lords | Reference voice type + exaggeration settings |
| **Wise Elder** | Wizards, sages, mentors | Reference voice type + speed adjustments |
| **Young Rogue / Bard** | Charismatic NPCs, rogues | Reference voice type + speed/pitch |
| **Intimidating Dragon** | Dragon monologues, demon speech | Reference voice type + pitch/exaggeration |
| **Cheerful Innkeeper** | Friendly NPCs, merchants | Reference voice type + speed/exaggeration |

For each: specify pitch range (0.5-2.0), speed range (0.5-2.0), exaggeration range (0.0-1.0), and what kind of reference clip to use.

### 3. Reference Audio Sourcing Strategy
Identify legal sources for diverse voice reference clips:
- **Public domain audiobooks** — LibriVox readers with distinct voices
- **Open datasets** — VCTK (109 speakers), LibriSpeech, Common Voice, RAVDESS (emotional speech)
- **Creative Commons voice reels** — Freesound.org, OpenSLR
- **Self-recording** — Guidelines for recording your own reference clips
- **AI-generated seeds** — Using Kokoro (54 voices, already installed) to generate base clips, then processing through RVC for voice conversion

For each source: note license, quality level, diversity of voices, and how to extract clean 10-15s clips.

### 4. Post-Processing Pipeline Recommendations
Research DSP transforms that can expand voice variety from a limited set of reference clips:
- Pitch shifting (semitones) — torchaudio or librosa
- Formant shifting — praat-parselmouth or world vocoder
- Speed modulation — time-stretch without pitch change
- EQ profiling — bass boost for deep voices, treble for clarity
- Recommend specific Python libraries and parameter ranges

### 5. Community Knowledge Survey
Search for community wisdom on voice cloning for character voices:
- RVC Discord best practices
- Chatterbox/ResembleAI community tips
- AI voice acting forums
- D&D/TTRPG voice synthesis projects
- Document any "golden settings" or parameter presets people have found

---

## Output Format

Produce a single markdown file: `docs/research/RQ-VOICE-001_VOICE_DESIGN_GUIDE.md`

Structure:
1. Reference Clip Quality Guidelines
2. Archetype Recipe Table (with exact parameter values)
3. Sourcing Strategy (ranked by quality × accessibility)
4. Post-Processing Pipeline
5. Community Findings
6. Recommended Starter Roster (10-15 voices covering all archetypes)

---

## Constraints

- Research only — no code implementation
- Focus on what's achievable with the installed stack (Chatterbox + Kokoro + RTX 3080 Ti)
- All sources must be legally usable (public domain, CC, MIT, Apache)
- Parameter recommendations must map to existing VoicePersona fields
