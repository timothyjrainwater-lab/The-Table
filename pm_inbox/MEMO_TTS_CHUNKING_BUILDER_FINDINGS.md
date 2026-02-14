# MEMO: WO-TTS-CHUNKING-001 Builder Findings
**From:** Agent (Opus 4.6), relaying builder debrief
**Date:** 2026-02-14
**Lifecycle:** NEW

---

## Findings

### 1. _concatenate_wav Duplication (Code Smell)

Identical WAV concatenation logic exists in both `chatterbox_tts_adapter.py` and `kokoro_tts_adapter.py`. Builder followed WO spec faithfully, but this will drift silently — a bug fix in one won't propagate to the other. Risk increases when a third backend arrives or when streaming (RQ-TTS-006) needs a fallback concat path.

**Recommendation:** Extract to shared utility (e.g., `aidm/immersion/audio_utils.py`). Could bundle into WO-SPEAK-SERVER or a standalone micro-WO.

### 2. Oversized Single-Sentence Passthrough

`chunk_by_sentence` returns sentences whole even if they exceed `max_words`. A single 80-word sentence with no periods passes through unchunked, and Chatterbox will truncate it. Builder left this per WO scope ("port exactly, no algorithmic changes").

**Fix if needed:** Secondary split on clause boundaries (commas, semicolons, dashes) when a single sentence exceeds ceiling. Separate WO if it matters in practice.

### 3. speak.py --full Mode Behavioral Change

Previously: each chunk was a separate `speak()` call with potential gaps between chunks. Now: adapter concatenates all chunks into one WAV blob. Better for audio continuity, but removes per-chunk interruptibility. Builder assessed no one relies on per-chunk playback. Low risk.

### 4. test_speak_signal.py Overlap

`test_speak_signal.py` now imports `chunk_by_sentence` from the new `tts_chunking` module, but its chunking tests overlap with the canonical `tests/immersion/test_tts_chunking.py`. Not broken — just redundant. Prune in a future cleanup pass.

---

## Retrospective

Builder executed cleanly within WO scope, flagged 4 items without over-stepping. The `_concatenate_wav` duplication is the highest-signal item — it's the kind of silent drift that compounds. The oversized sentence issue is real but unlikely in practice (D&D narration text is typically well-punctuated).

## Builder Process Feedback (Second Pass)

### What the builder validated:
- **WO "Binary Decisions" section** eliminates the biggest builder time sink (ambiguity). Decision #5 ("Does speak.py keep its chunker? No.") and Decision #6 ("Build it anyway — streaming is not guaranteed") each prevented a round-trip clarification. Builder called this "the best-structured dispatch I've worked from."
- **"Files NOT to Change" section** is an effective scope guardrail — keep in every WO template.
- **Adapter pattern** (Kokoro/Chatterbox) is consistent enough that "same pattern as Change 2" was actually executable.
- **Test infrastructure** (mock fixtures, skip markers, unit/integration split) required zero scaffolding work.

### One additional finding:

**5. tests/immersion/ vs tests/ split inconsistency.** TTS tests are split between `tests/immersion/test_kokoro_tts.py` and root-level `tests/test_speak_signal.py`. The speak signal tests now import from `aidm.immersion.tts_chunking` but live outside the immersion test directory. Minor — but as immersion-layer tests grow, a consistent home reduces hunting. Candidate for a future cleanup pass alongside finding #4.
