# WO-M3-AUDIO-INT-01: Audio Pipeline Integration (DRAFT)

**Agent:** TBD (assigned after WO-M3-AUDIO-EVAL-01 completion)
**Work Order:** WO-M3-AUDIO-INT-01
**Date:** 2026-02-10
**Status:** BLOCKED — Awaiting WO-M3-AUDIO-EVAL-01 Results
**Depends On:** WO-M3-AUDIO-EVAL-01 (evaluation must complete first)
**Blocks:** M3 Immersion Layer completion

---

## Objective

Implement M3 Audio Pipeline integration based on approved approach from **WO-M3-AUDIO-EVAL-01** evaluation. This work order integrates audio playback, scene state transitions, and licensing/attribution tracking into the M3 immersion layer.

**NOTE:** This work order is a **DRAFT TEMPLATE**. Specific implementation tasks will be defined after WO-M3-AUDIO-EVAL-01 evaluation results are approved by PM.

---

## Background

Per Execution Roadmap v3.1 M3 Deliverables (lines 265-267):

> **3. Audio Pipeline**
> - Ambient loops + SFX (bundled library acceptable)
> - Optional local music generator; otherwise curated generative-safe library
> - Licensing/attribution tracked for bundled assets

Per M3 Acceptance Criteria (lines 274-280):

> - [ ] Offline voice I/O functional
> - [ ] **Audio transitions tied to scene state**
> - [ ] Images are atmospheric only (no mechanics depend on them)
> - [ ] Grid appears for combat, disappears after
> - [ ] **Licensing/attribution record for bundled assets**

This work order implements the **runtime integration** of audio (M3), NOT prep-time generation (M2).

---

## Scope (Provisional — Finalize After Evaluation)

### In Scope

1. **Audio Playback System** (M3.10-equivalent):
   - Integrate audio mixer/queue (reuse existing `aidm/immersion/audio_queue.py`)
   - Handle ambient loops + SFX playback
   - Crossfade between tracks

2. **Scene State → Audio Transitions** (M3.11-M3.12):
   - Read scene state from `WorldState` (combat/exploration/dialogue)
   - Select appropriate ambient loop based on scene state
   - Trigger music transitions on scene state changes
   - Handle silence (theatre-of-the-mind default)

3. **Asset Management**:
   - If curated approach: Bundle initial sound effects (M3.13)
   - If generative approach: Implement adapter pattern (stub + real)
   - Create licensing/attribution ledger

4. **Testing**:
   - Verify audio transitions tied to scene state (M3 acceptance criteria)
   - Verify licensing/attribution record exists (M3 acceptance criteria)
   - Verify audio is atmospheric only (no mechanics depend on it)

### Out of Scope

- **Prep-time audio generation** (M2 work, not M3)
- **Model loading/training** (evaluation only)
- **Audio editing tools** (use curated/generated assets as-is)

---

## Implementation Approach (Provisional)

### If Curated Approach Approved (Approach A):

1. **Bundle Curated Library:**
   - Add 20-30 ambient loops to `assets/audio/music/`
   - Add 20-30 SFX to `assets/audio/sfx/`
   - Create `assets/audio/attribution.json` ledger

2. **Implement Scene State → Audio Selection:**
   ```python
   # aidm/immersion/audio_selector.py
   def select_ambient_loop(scene_state: str) -> str:
       """Map scene state to appropriate ambient loop."""
       mapping = {
           "combat": "assets/audio/music/combat_01.ogg",
           "exploration": "assets/audio/music/exploration_01.ogg",
           "dialogue": "assets/audio/music/dialogue_01.ogg",
           "tension": "assets/audio/music/tension_01.ogg",
       }
       return mapping.get(scene_state, None)  # None = silence
   ```

3. **Integrate with Immersion Layer:**
   - Hook into existing `compute_scene_audio_state()` (already exists)
   - Update `AudioQueueState` with selected loop
   - Test transitions (combat → exploration → silence)

### If Generative Approach Approved (Approach B or C):

1. **Implement Adapter Pattern:**
   ```python
   # aidm/immersion/audio_adapter.py
   class AudioGeneratorProtocol(Protocol):
       def generate_music(self, prompt: str, duration: int) -> Path: ...
       def generate_sfx(self, prompt: str) -> Path: ...

   class StubAudioAdapter:
       """Returns curated library assets (no generation)."""
       def generate_music(self, prompt: str, duration: int) -> Path:
           return Path("assets/audio/music/generic_combat.ogg")

   class MusicGenAdapter:
       """Real MusicGen integration (loads model, generates)."""
       def __init__(self, model_path: Path):
           self.model = load_musicgen_model(model_path)

       def generate_music(self, prompt: str, duration: int) -> Path:
           # Generate track using MusicGen
           # Save to campaign-specific directory
           # Return path
   ```

2. **Factory Pattern:**
   ```python
   # aidm/immersion/audio_factory.py
   def create_audio_adapter(backend: str = "stub") -> AudioGeneratorProtocol:
       if backend == "stub":
           return StubAudioAdapter()
       elif backend == "musicgen":
           return MusicGenAdapter(model_path=...)
       else:
           raise ValueError(f"Unknown backend: {backend}")
   ```

3. **Integrate with Immersion Layer:**
   - Hook into existing `compute_scene_audio_state()`
   - Use adapter to select/generate audio
   - Test on multiple hardware tiers (baseline, recommended, enhanced)

---

## Tasks (Provisional — Finalize After Evaluation)

### Phase 1: Asset Integration

- [ ] **Task 1.1**: Bundle curated library (if Approach A) OR install models (if Approach B/C)
- [ ] **Task 1.2**: Create licensing/attribution ledger (`assets/audio/attribution.json`)
- [ ] **Task 1.3**: Verify asset quality (spot-check 10 tracks/SFX)

### Phase 2: Runtime Integration

- [ ] **Task 2.1**: Implement `audio_selector.py` (scene state → audio selection)
- [ ] **Task 2.2**: Integrate with `compute_scene_audio_state()` (existing function)
- [ ] **Task 2.3**: Implement crossfade logic (smooth transitions)
- [ ] **Task 2.4**: Handle silence (theatre-of-the-mind default)

### Phase 3: Testing

- [ ] **Task 3.1**: Unit tests for audio selection logic
- [ ] **Task 3.2**: Integration test (scene state changes → audio transitions)
- [ ] **Task 3.3**: Verify M3 acceptance criteria:
  - [ ] Audio transitions tied to scene state
  - [ ] Licensing/attribution record exists
  - [ ] Audio is atmospheric only (no mechanics depend on it)

### Phase 4: Documentation

- [ ] **Task 4.1**: Update `IMMERSION_BOUNDARY.md` (audio adapter contract)
- [ ] **Task 4.2**: Update `PROJECT_STATE_DIGEST.md` (M3 audio complete)
- [ ] **Task 4.3**: Document hardware tier recommendations (if generative)

---

## Acceptance Criteria

- [ ] Audio transitions tied to scene state (M3 acceptance criteria)
- [ ] Licensing/attribution record exists (M3 acceptance criteria)
- [ ] Audio is atmospheric only (no mechanics depend on it)
- [ ] All tests pass (zero regressions)
- [ ] Integration works on approved hardware tiers (per evaluation)

---

## Dependencies

- **WO-M3-AUDIO-EVAL-01**: Must complete evaluation before defining specific tasks
- **PM Approval**: Must approve evaluation results before integration begins
- **Existing Infrastructure**: `aidm/immersion/audio_queue.py` already exists (reuse)

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Evaluation recommends approach not in template | Medium | Update this work order after evaluation |
| Audio adapter pattern too complex | Low | Follow existing voice/image adapter patterns |
| Scene state transitions not well-defined | Medium | Coordinate with M1 runtime integration |

---

## Timeline Estimate

**BLOCKED** — Cannot estimate until WO-M3-AUDIO-EVAL-01 completes.

Provisional estimates:
- **Curated approach (A)**: 4-6 hours (bundling + integration + testing)
- **Generative approach (B/C)**: 8-12 hours (adapter + models + integration + testing)

---

## References

- [AIDM_EXECUTION_ROADMAP_V3.md](../docs/AIDM_EXECUTION_ROADMAP_V3.md) (M3 Deliverables)
- [WO-M3-AUDIO-EVAL-01](./SONNET-D_WO-M3-AUDIO-EVAL-01_DRAFT.md) (Evaluation phase)
- [IMMERSION_BOUNDARY.md](../docs/IMMERSION_BOUNDARY.md) (Adapter contract)
- [aidm/immersion/audio_queue.py](../aidm/immersion/audio_queue.py) (Existing audio queue)

---

**Next Step**: Wait for WO-M3-AUDIO-EVAL-01 completion and PM approval, then finalize this work order with specific implementation tasks.
