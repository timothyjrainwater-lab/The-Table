# MEMO: STT Cleanup Layer v0

**Lifecycle:** NEW
**Origin:** Anvil (BS Buddy) + Aegis (Co-PM), 2026-02-19
**Classification:** OPS-FRICTION

---

## Summary

Thunder's primary input method is Win+H voice typing (~99% of operator inputs). The transcription quality is degrading his signal — homophones, filler noise, missing proper nouns, profanity censorship. We built a v0 fix.

## What Was Done

Two changes to the existing `scripts/listen.py` dictation tool:

1. **Model upgrade:** Default Whisper model bumped from `small.en` to `medium.en`. Better accuracy on homophones and garble at the source.

2. **Post-transcription cleanup layer** (`scripts/stt_cleanup.py`):
   - **Tier A (structural):** Remove filler words (um, uh, you know, I mean), collapse duplicate words, normalize whitespace, capitalize sentences. Fully deterministic.
   - **Tier B (project dictionary):** Fix known proper nouns and terms — "ages" → "Aegis", "windows H" → "Win+H", "stt" → "STT", "mrs slate" → "Mrs. Slate", D&D terms, architecture names. Deterministic word replacement.

Cleanup runs automatically after every transcription. Bypass with `--no-cleanup` flag. When cleanup changes text, raw transcript is printed to console for auditability.

## Gate Contract

1. Meaning preserved — no new facts, no deletions of intent
2. All TERM and CAPS fixes applied deterministically
3. No silent rewrites — uncertain tokens left as raw

## Failure Taxonomy (10 categories observed)

A) FILLER, B) RUNON, C) PUNCT, D) HOMOPHONE, E) DUP, F) CAPS, G) TERM, H) SEGMENT, I) FILTER (Win+H profanity censorship), J) GARBLE (model hallucination)

Tiers A+B handle categories A, C, E, F, G. Model upgrade targets D, I, J. Categories B and H are partially addressed.

## PM Relevance

- **No WO needed.** This is operator tooling, not product code. Does not touch `aidm/` or `tests/`.
- **Doctrine alignment:** STT output is input telemetry, not canon (Aegis framing). Matches Wisdom #1 (truth first) and #7 (protect the operator).
- **Future consideration:** If STT becomes a product feature (player voice input at The Table), the cleanup layer taxonomy and gate contract are the spec seed. Aegis recommended a three-output model: raw transcript, clean transcript, intent parse.
- **Dictionary is extensible.** As new terms enter the project, add them to `PROJECT_TERMS` in `stt_cleanup.py`.

## Files

- `scripts/listen.py` — modified (model default, cleanup integration, `--no-cleanup` flag)
- `scripts/stt_cleanup.py` — new (standalone cleanup module with CLI test mode)
