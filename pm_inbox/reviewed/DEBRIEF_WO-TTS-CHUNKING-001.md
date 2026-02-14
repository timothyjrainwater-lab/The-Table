# DEBRIEF: WO-TTS-CHUNKING-001 — Sentence-Boundary TTS Chunking

**From:** Builder (Opus 4.6)
**To:** PM (Aegis), via PO (Thunder)
**Date:** 2026-02-14
**Lifecycle:** NEW
**WO:** WO-TTS-CHUNKING-001
**Result:** COMPLETED — all 7 success criteria met

---

## Pass 1 — Full Context Dump

### What Was Done

Extracted the sentence-boundary chunking logic from `scripts/speak.py` into a shared module at the adapter layer. Both Chatterbox and Kokoro adapters now auto-chunk input text before synthesis and concatenate WAV output, so callers see a single audio result regardless of input length. The CLI-level chunking loop in speak.py was removed — the adapter handles it now.

### Files Created

1. **`aidm/immersion/tts_chunking.py`** — Shared chunking utility:
   - `chunk_by_sentence(text, max_words=55) -> list[str]` — splits at `. ` boundaries, conservative 55-word ceiling under Chatterbox's ~60-80 word generation limit
   - Logic ported directly from `scripts/speak.py:167-199`, no algorithmic changes

2. **`tests/immersion/test_tts_chunking.py`** — 19 tests across 4 test classes:
   - `TestChunkBySentence` (9 tests): boundary logic, max_words enforcement, content preservation, empty/newline handling
   - `TestChatterboxChunking` (3 tests): multi-chunk generate calls, single-chunk passthrough, valid WAV output
   - `TestKokoroChunking` (3 tests): same pattern as Chatterbox with Kokoro's mock engine
   - `TestWavConcatenation` (4 tests): frame counts, header validity, passthrough on single part, playability

### Files Modified

1. **`aidm/immersion/chatterbox_tts_adapter.py`** — Two changes:
   - `synthesize()`: chunks input via `chunk_by_sentence()`, synthesizes each chunk sequentially, concatenates WAV via new `_concatenate_wav()` helper
   - Added `_concatenate_wav(wav_parts)`: reads PCM frames from each WAV part, writes single valid WAV with correct header (respects nchannels, sampwidth, framerate from first part)

2. **`aidm/immersion/kokoro_tts_adapter.py`** — Same pattern:
   - `synthesize()`: chunks input, synthesizes per-chunk, concatenates WAV
   - Added own `_concatenate_wav()` helper (uses Kokoro's `_encode_wav` for empty fallback)

3. **`scripts/speak.py`** — Two removals:
   - Deleted `_chunk_by_sentence()` function (was lines 167-199)
   - Replaced chunking loop in `--full` mode (~lines 464-468) with single `speak()` call — adapter handles chunking internally

4. **`tests/test_speak_signal.py`** — Import update:
   - Changed `from speak import ... _chunk_by_sentence` to `from aidm.immersion.tts_chunking import chunk_by_sentence as _chunk_by_sentence`

### Files NOT Changed (per WO constraints)

- `aidm/immersion/image_adapter.py` — unrelated
- All core resolver and mechanical layer files — unrelated
- Gold masters — unrelated

### Test Results

- **93 TTS-related tests passed** (chatterbox, kokoro, speak_signal suites combined)
- **19 new tests passed** (test_tts_chunking.py)
- **Zero regressions** — all existing tests pass without modification
- Chatterbox integration tests exercised real GPU synthesis with chunked input

### WAV Concatenation Approach

Both adapters use the same strategy: read WAV params (nchannels, sampwidth, framerate) from the first chunk's output, then iterate all parts extracting raw PCM frames via `wave.open().readframes()`, and write a single WAV with `b"".join(all_frames)`. This avoids the naive "append raw bytes" bug where you'd get multiple RIFF headers in the output. The `wave` module handles header construction correctly.

### Boundary Laws

- None affected. TTS is in the immersion layer, outside mechanical boundary laws.

---

## Pass 2 — PM Summary

**WO-TTS-CHUNKING-001: COMPLETED.** `chunk_by_sentence()` extracted to `aidm/immersion/tts_chunking.py`. Both ChatterboxTTSAdapter and KokoroTTSAdapter auto-chunk at the adapter layer and return single concatenated WAV. speak.py CLI-level chunking removed. 19 new tests, 93 existing tests pass. 100+ word input now produces complete narration — Chatterbox truncation defect (TD-023) is resolved at the adapter level.

---

## Retrospective (Pass 3 — Operational Judgment)

### Duplication

- `_concatenate_wav()` is duplicated in both adapter files. The WO spec said "New shared module `aidm/immersion/tts_chunking.py`" for the chunker but did not specify where WAV concatenation should live. I placed it in each adapter because each adapter's WAV parameters differ (Chatterbox: 24kHz, Kokoro: 16kHz) and the empty-WAV fallback differs (`_tensor_to_empty_wav` vs `_encode_wav`). If a third TTS backend appears, this helper should be extracted to a shared `tts_audio_utils.py`.

### Test Fixture Adjustment

- The Chatterbox `test_short_input_single_generate` test needed mocks for both `get_turbo` and `get_original` because tier selection routes through the real `_select_tier()` logic. The original test only mocked turbo, which broke when the default persona (exaggeration=0.5) routed to original. This is a sign that tier selection has real coupling to persona defaults — something to watch if persona config changes.

### Process Feedback

- The WO was well-structured. Binary decisions pre-made, line references to speak.py were accurate, and the "port exactly, no algorithmic changes" constraint prevented scope creep. The "build it anyway — streaming is not guaranteed" note in decision #6 was the right call.
- The constraint "Do NOT add chunking configuration (e.g., configurable max_words) — hardcode 55" was correct. Configuration would be premature until we know whether streaming (RQ-TTS-006) replaces chunking entirely.

### Concerns

- None. The refactor is clean and the test suite validates all success criteria. If RQ-TTS-006 streaming lands, the adapter-level chunking becomes the fallback path as the WO anticipated.
