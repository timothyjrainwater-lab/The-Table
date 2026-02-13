# Immersion Layer Boundary Contract

## What This Document Is

Authoritative scope boundary for the M3 Immersion Layer (`aidm/immersion/`).
Any future agent or contributor working on immersion **must** read this document.

## What Immersion MAY Do

- **Read** WorldState, SceneCard, and AssetRecord data (read-only)
- Compute atmospheric outputs: mood, audio tracks, grid visibility, image placeholders
- Provide pluggable adapter interfaces (STT, TTS, image, audio mixer)
- Return stub/placeholder results when no real backend is installed
- Save/load attribution records as JSON
- Produce deterministic output from deterministic input

## What Immersion MUST NEVER Do

- **Mutate WorldState** — immersion functions receive WorldState as input and must not modify it
- **Affect engine decisions** — no immersion output may influence attack rolls, saving throws, legality checks, or any mechanical resolution
- **Consume RNG streams** — immersion uses no randomness; outputs must be fully deterministic
- **Appear in replay hash** — immersion outputs are excluded from deterministic replay verification
- **Require external dependencies** — all adapters must have a stub default that works with zero external libraries installed
- **Write to AssetStore directly** — image/audio adapters return results; the caller decides whether to store them
- **Block engine execution** — if an adapter fails or is unavailable, engine continues unaffected

## Adapter Rules

1. **Protocol pattern**: All adapters use `typing.Protocol` with `@runtime_checkable`
2. **Stub default**: Every adapter type has a `Stub*Adapter` that is always available
3. **Factory pattern**: `create_*_adapter(backend="stub")` returns the stub by default
4. **Lazy loading**: Real backends (e.g., Whisper, Coqui) are imported inside the factory, never at module level
5. **Unknown backends**: Factory raises `ValueError` for unrecognized backend names
6. **Missing libraries**: If a real backend's library is not installed, factory raises `ImportError` with a clear message

## Pure Function Contract

`compute_scene_audio_state()` and `compute_grid_state()` are **pure functions**:
- No side effects
- No I/O
- No RNG
- Same inputs always produce same outputs (verified 10× in tests)
- Output depends only on the function arguments

## Mood Priority Rules

Checked in order (first match wins):
1. `active_combat is not None` → mood = `"combat"`
2. `scene_card.environmental_hazards` is non-empty → mood = `"tense"`
3. `scene_card.ambient_light_level == "dark"` → mood = `"tense"`
4. Otherwise → mood = `"peaceful"`

## Grid Visibility Rules

1. `active_combat is not None` → `visible=True, reason="combat_active"`
2. `active_combat is None` and previous was visible → `visible=False, reason="combat_ended"`
3. `active_combat is None` and previous was not visible → `visible=False, reason="no_combat"`

## Test Coverage

Hardening tests (`tests/test_immersion_hardening.py`) verify:
- Package and import integrity (C-01)
- Extended determinism proofs across all moods (C-02)
- Zero external dependency requirement (C-03)
- Non-authority enforcement with deep equality checks (C-04)
- Attribution validation edge cases (C-05)

## Scope for Future Milestones

- Real STT/TTS backends: add to factory registry, never modify stub behavior
- Real image generation: add adapter implementation, caller orchestrates AssetStore writes
- Audio file playback: implement `AudioMixerAdapter`, stub records history only
- Attribution expansion: add license types, but schema_version remains "1.0" unless breaking changes
