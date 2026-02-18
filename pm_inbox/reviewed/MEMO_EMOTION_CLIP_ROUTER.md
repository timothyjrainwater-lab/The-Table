# MEMO: Emotion Clip Router — Phase 1 Complete

**Date:** 2026-02-18
**From:** Builder (Operator-directed research + implementation)
**Status:** INFORMATIONAL — no PM action required

## What Was Built

Deterministic mood-to-reference-clip router for Chatterbox TTS. When the narration pipeline passes a scene mood (neutral/tense/combat/dramatic), the router selects a different acted reference clip per persona instead of always using the same one.

- **Module:** `aidm/immersion/emotion_router.py`
- **Adapter wired:** `chatterbox_tts_adapter.py` now accepts `mood` and `scene_tag` params
- **Reference clips:** 16 human-acted clips (CREMA-D dataset, ODbL license) in `models/voices/`
- **Tests:** 20 new tests in `tests/immersion/test_emotion_router.py`, 75/75 total immersion tests PASS

## Key Finding

Chatterbox voice cloning transfers emotional prosody from reference clips — but only from genuinely human-acted source material. Self-generated bootstrapped clips (Chatterbox cloning its own output with different exaggeration) produce no audible variation. Real acted clips from CREMA-D confirmed audible emotion differences by Operator ear test.

## Not Yet Wired

The narration pipeline caller does not yet pass `mood` from `SceneAudioState` to `synthesize()`. This is the remaining integration seam — one call site change, but touches the play loop.

## Phase 1 Scope

4 personas × 4 registers = 16 clips. Expansion to Phase 2 (3 more personas) deferred pending Operator direction.
