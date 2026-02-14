# WO-TTS-CHUNKING-001: Sentence-Boundary TTS Chunking

**From:** PM (Aegis)
**To:** Builder (via Operator dispatch)
**Date:** 2026-02-14
**Lifecycle:** DISPATCH-READY
**Horizon:** 1
**Priority:** P2 — Quality-of-life. Chatterbox silently truncates long narration. Fix exists in scripts/, needs adapter integration.
**Source:** TD-023 defect (RQ-SPRINT-009), speak.py prototype

---

## Target Lock

Chatterbox silently truncates output at ~60-80 words. Players hear incomplete narration that cuts off mid-sentence. A working chunker already exists in `scripts/speak.py:167-199` (`_chunk_by_sentence`). This WO integrates that logic into the adapter layer so all TTS consumers get chunking automatically.

## Binary Decisions

1. **Where does the chunker live?** New shared module `aidm/immersion/tts_chunking.py`. Not inside any single adapter — both Chatterbox and Kokoro consume it.
2. **What is the chunk boundary?** Sentence boundaries (`. ` split). Max 55 words per chunk (conservative margin under Chatterbox's ~60-80 word ceiling).
3. **Does the adapter concatenate audio chunks?** Yes. `synthesize()` chunks the input, synthesizes each chunk, concatenates the WAV byte output. Caller sees a single audio result.
4. **Does Kokoro need chunking?** Yes for consistency. Kokoro doesn't truncate, but chunking improves latency on long narration (smaller synthesis calls return faster).
5. **Does speak.py keep its chunker?** No. Remove `_chunk_by_sentence` from speak.py and its CLI-level chunking loop. The adapter handles it now.
6. **What about streaming (RQ-TTS-006)?** If WO-TTS-COLD-START-RESEARCH finds that streaming replaces chunking, this WO's adapter-level chunking becomes the fallback path. Build it anyway — streaming is not guaranteed.

## Contract Spec

### Change 1: Shared Chunking Utility

New file `aidm/immersion/tts_chunking.py`:

```python
def chunk_by_sentence(text: str, max_words: int = 55) -> list[str]:
    """Split text at sentence boundaries, max_words per chunk."""
```

Port logic directly from `scripts/speak.py:167-199`. No algorithmic changes — this is a lift-and-shift.

### Change 2: ChatterboxTTSAdapter Integration

In `aidm/immersion/chatterbox_tts_adapter.py`, modify `synthesize()`:
- Import `chunk_by_sentence`
- Before synthesis: `chunks = chunk_by_sentence(text)`
- Synthesize each chunk sequentially
- Concatenate WAV byte output (respect WAV header — don't just append raw bytes)
- Return single WAV result to caller

### Change 3: KokoroTTSAdapter Integration

Same pattern as Change 2 in `aidm/immersion/kokoro_tts_adapter.py`.

### Change 4: Remove CLI-Level Chunking from speak.py

In `scripts/speak.py`:
- Remove `_chunk_by_sentence()` function
- Remove the chunking loop in `--full` mode (~lines 464-468)
- `speak()` now passes full text to the adapter; adapter handles chunking internally

### Constraints

- Do NOT change the chunking algorithm — port exactly from speak.py
- Do NOT implement streaming — that's a separate WO if research supports it
- Do NOT change WAV sample rate, bit depth, or channel count during concatenation
- Do NOT add chunking configuration (e.g., configurable max_words) — hardcode 55
- Existing speak.py tests must pass after the refactor

### Boundary Laws Affected

- None. TTS is in the immersion layer, outside mechanical boundary laws.

## Success Criteria

- [ ] `tts_chunking.py` module exists with `chunk_by_sentence()` function
- [ ] ChatterboxTTSAdapter.synthesize() auto-chunks input text
- [ ] KokoroTTSAdapter.synthesize() auto-chunks input text
- [ ] 100+ word input produces complete narration (no truncation)
- [ ] speak.py no longer contains `_chunk_by_sentence`
- [ ] Concatenated WAV output is valid (correct header, playable)
- [ ] Existing tests pass without modification

## Files Expected to Change

- New: `aidm/immersion/tts_chunking.py`
- `aidm/immersion/chatterbox_tts_adapter.py` — synthesize() chunking
- `aidm/immersion/kokoro_tts_adapter.py` — synthesize() chunking
- `scripts/speak.py` — remove chunker + CLI-level loop
- New: test file for chunking utility and adapter integration

## Files NOT to Change

- `aidm/immersion/image_adapter.py` — unrelated
- Any core resolver or mechanical layer files
- Gold masters

## Interaction Notes

- **WO-TTS-COLD-START-RESEARCH dependency:** If RQ-TTS-003 (persistent server) or RQ-TTS-006 (streaming) findings change the chunking strategy, PM will issue an amendment or supersede this WO. Build this as specified — it's the correct fallback path regardless.

---

*End of WO-TTS-CHUNKING-001*
