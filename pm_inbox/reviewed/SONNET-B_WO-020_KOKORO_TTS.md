# WO-020 Completion Report — Real TTS Backend (Kokoro)

**Work Order:** WO-020
**Agent:** SONNET-B
**Status:** ✅ COMPLETE
**Date:** 2026-02-11

---

## Deliverables

### 1. aidm/immersion/kokoro_tts_adapter.py (510 lines)
- `KokoroTTSAdapter` class implementing `TTSAdapter` protocol
- ONNX model loading with lazy initialization (no import-time deps)
- `synthesize(text, persona)` → WAV bytes (16kHz mono 16-bit PCM)
- `list_personas()` → 8 voice personas
- `is_available()` → True only if kokoro-onnx and onnxruntime present
- Helper functions: `_encode_wav()`, `_resample_simple()`, `_float_to_int16()`
- Factory function: `create_kokoro_adapter()`

### 2. tests/immersion/test_kokoro_tts.py (559 lines)
- 42 tests total (38 pass, 4 skipped when Kokoro not installed)
- Test classes:
  - `TestProtocolCompliance` (4 tests)
  - `TestPersonaListing` (8 tests)
  - `TestDefaultPersona` (3 tests)
  - `TestSynthesisMocked` (5 tests)
  - `TestWavFormatValidation` (4 tests)
  - `TestAvailability` (3 tests)
  - `TestVoiceResolution` (3 tests)
  - `TestFactoryFunction` (3 tests)
  - `TestKokoroIntegration` (4 tests, skipped without Kokoro)
  - `TestAudioQualitySanity` (2 tests)
  - `TestErrorHandling` (3 tests)

### 3. Updated tts_adapter.py
- Added lazy registry `_TTS_LAZY_REGISTRY` for backends with heavy deps
- Registered `KokoroTTSAdapter` at key `"kokoro"`
- Updated `create_tts_adapter()` to check both registries

### 4. Updated aidm/immersion/__init__.py
- Added export for `KokoroTTSAdapter`
- Added to `__all__` list

---

## Voice Personas (8 total)

| Persona ID | Name | Voice Model | Speed | Pitch |
|------------|------|-------------|-------|-------|
| dm_narrator | Dungeon Master | af_bella | 1.0 | 1.0 |
| dm_narrator_male | Dungeon Master (Male) | am_adam | 1.0 | 1.0 |
| npc_male | NPC Male | am_michael | 1.0 | 1.0 |
| npc_female | NPC Female | af_nicole | 1.0 | 1.0 |
| npc_elderly | NPC Elderly | bm_george | 0.9 | 0.95 |
| npc_young | NPC Young | af_sky | 1.05 | 1.05 |
| villainous | Villain | bm_lewis | 0.95 | 0.9 |
| heroic | Hero | am_adam | 1.0 | 1.0 |

---

## Test Results

```
tests/immersion/test_kokoro_tts.py: 38 passed, 4 skipped
Total test suite: 3102 tests collected
Existing TTS tests: All pass (no regressions)
```

---

## Acceptance Criteria Checklist

- [x] `KokoroTTSAdapter` passes protocol check (`isinstance(adapter, TTSAdapter)`)
- [x] Factory `create_tts_adapter("kokoro")` returns working adapter
- [x] At least 3 voice personas defined (8 provided)
- [x] All existing TTS tests pass (19+ in test_immersion_integration.py)
- [x] New tests pass (target 15+, actual 38+)
- [x] No VRAM usage (CPU-only, lazy ONNX loading)

---

## Design Notes

### Lazy Loading
- Zero import-time dependencies on ONNX or kokoro_onnx
- `_KokoroLoader` class manages lazy initialization
- Dependencies only loaded when first synthesis requested

### Graceful Fallback
- `is_available()` returns False if deps missing
- Error messages guide user to install: `pip install kokoro-onnx onnxruntime`
- Integration tests skipped via `@requires_kokoro` marker

### Audio Format
- Kokoro outputs 24kHz by default
- Resampled to 16kHz for STT compatibility
- WAV format with RIFF header, 16-bit mono PCM

### CPU-Only Inference
- No GPU/CUDA dependencies
- Uses ONNX Runtime CPU provider
- Meets R1 stack requirement: 0 GB VRAM

---

## Files Changed

| File | Lines | Change |
|------|-------|--------|
| aidm/immersion/kokoro_tts_adapter.py | 510 | Created |
| tests/immersion/test_kokoro_tts.py | 559 | Created |
| aidm/immersion/tts_adapter.py | +18 | Added lazy registry |
| aidm/immersion/__init__.py | +5 | Added export |
| pyproject.toml | +2 | Added markers |

**Total new code:** ~1,069 lines

---

**Status:** Ready for PM review
