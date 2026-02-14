# WO-TTS-COLD-START-RESEARCH: TTS Cold Start Latency — Research Sprint

**From:** Advisor (Opus 4.6)
**To:** Builder (next session)
**Date:** 2026-02-14
**Lifecycle:** PM-REVIEWED (ACCEPTED with amendments — see below)
**Status:** DISPATCH-READY
**Scope:** Research + prototype — no production code changes without PM review.

---

## Context

Every invocation of `scripts/speak.py` cold-loads the entire Chatterbox model into VRAM before inference begins. This adds 3-4 seconds of dead air before any audio plays. For single operator signals ("Thunder, the forge is quiet") this is tolerable. For sequential narration in combat — where multiple lines need to play back-to-back — the gap kills pacing.

**Root cause:** The CLI wrapper (`scripts/speak.py`) creates a new `ChatterboxTTSAdapter` on every process invocation. The adapter uses lazy loading (`_ChatterboxLoader`), which means each process pays the full cost: Python import, torch initialization, CUDA context creation, and model weight loading into VRAM.

**The adapter is not the problem.** `ChatterboxTTSAdapter` already supports multiple `synthesize()` calls on a single instance — the model loads once and stays in memory. The `--signal --full` mode already demonstrates this: it chunks text at sentence boundaries and calls `speak()` for each chunk within a single process, and only the first chunk pays the load cost. The problem is that external callers (BS buddy, idle signals, future combat narration) invoke `speak.py` as separate processes.

**Why it matters:** The DM narration system will need continuous voice output during combat. A fighter attacks, narration plays. A spell resolves, narration plays. If each narration line has a 3-4 second reload penalty, the voice system feels broken even if the audio quality is perfect.

**Origin:** Discovered during BS Buddy session testing voice output. Two consecutive `speak.py` calls had a noticeable dead gap between them. Handoff filed at `pm_inbox/HANDOFF_TTS_COLD_START_RESEARCH.md`.

---

## Research Questions

---

### RQ-TTS-001: Cold Start Time Breakdown

**Problem:** The 3-4 second cold start is a single number. We need to know where the time goes to know what we can eliminate.

**Scope:**
- Instrument `speak.py` startup to measure each phase independently:
  - Python interpreter startup + module imports (non-torch)
  - `import torch` time
  - CUDA context initialization (`torch.cuda.is_available()` first call)
  - Model weight loading (`ChatterboxTTS.from_pretrained()` or `from_local()`)
  - First inference pass (model warm-up — first call is often slower than subsequent)
- Measure on target hardware: RTX 3080 Ti, Windows 11
- Run 5 iterations of each phase, report mean + stdev
- Compare: model loaded from HuggingFace cache vs. local weights directory
- Measure the same breakdown for Kokoro (ONNX runtime init + model load)

**Deliverable:** `docs/research/RQ-TTS-001_COLD_START_BREAKDOWN.md` — Timing table with per-phase breakdown for both backends.

**Key question:** Is the bottleneck torch import, CUDA init, or model loading — and which can be amortized?

---

### RQ-TTS-002: VRAM Footprint and Persistence Feasibility

**Problem:** If we keep Chatterbox loaded in VRAM between calls, we need to know the cost. The 3080 Ti has 12GB VRAM. Other GPU consumers include potential future image generation (SDXL) and LLM inference (Spark).

**Scope:**
- Measure VRAM consumed by Chatterbox when idle (model loaded, no active inference):
  - Original tier only
  - Turbo tier only
  - Both tiers loaded simultaneously (current lazy-load pattern loads one at a time)
- Measure VRAM during active synthesis (peak allocation)
- Document remaining VRAM after Chatterbox is loaded on the 3080 Ti
- Assess: can Chatterbox coexist with a 7B LLM (Spark narration) in 12GB VRAM?
- Assess: can Chatterbox coexist with SDXL image generation?
- Measure VRAM release behavior: does `del model` + `torch.cuda.empty_cache()` reliably free VRAM, or do fragments persist?

**Deliverable:** `docs/research/RQ-TTS-002_VRAM_FOOTPRINT.md` — VRAM measurements, coexistence analysis, and VRAM management recommendations.

**Key question:** Can we afford to keep Chatterbox resident, or do we need a load/unload strategy?

---

### RQ-TTS-003: Persistent Server Architecture

**Problem:** The highest-value fix is a persistent TTS server that loads the model once and accepts synthesis requests over IPC. The first call pays the cold start; every subsequent call is inference-only (~10 seconds for a sentence at ~40 it/s on Chatterbox Original).

**Scope:**
- **Design a `speak_server.py`** that wraps the existing `ChatterboxTTSAdapter`:
  - Loads model on startup, stays resident
  - Accepts text + persona configuration over a local transport
  - Returns WAV bytes to the caller
  - Handles graceful shutdown (VRAM release)
- **Transport evaluation** — assess each option for this use case:
  - Named pipe (Windows native, low overhead, no port conflicts)
  - TCP localhost socket (cross-platform, familiar, but port management)
  - HTTP/REST on localhost (highest overhead, but can use existing tooling like `requests`)
  - Shared memory (lowest latency, highest complexity)
- **Client changes to `speak.py`:**
  - If server is running: send request, receive WAV bytes, play
  - If server is not running: fall back to current behavior (cold load)
  - Detection mechanism: how does speak.py know if the server is up?
- **Lifecycle management:**
  - Who starts the server? (Agent on first speak? Operator manually? System service?)
  - Auto-shutdown after idle timeout? (Free VRAM when not needed)
  - What happens if the server crashes during synthesis?
- **Prototype:** If the design is straightforward, build a working prototype. The `ChatterboxTTSAdapter` already has the right API surface — the server is essentially `adapter = ChatterboxTTSAdapter(); while True: text = receive(); wav = adapter.synthesize(text, persona); send(wav)`.

**Deliverable:** `docs/research/RQ-TTS-003_PERSISTENT_SERVER.md` — Architecture design, transport comparison, prototype (if built), lifecycle management spec.

**Key question:** What's the simplest architecture that eliminates cold start for sequential calls?

---

### RQ-TTS-004: Subprocess Keep-Alive Alternative

**Problem:** A lighter alternative to a server: keep the speak.py Python process alive between calls, reading synthesis requests from stdin or a pipe. This avoids the complexity of a server daemon but still amortizes the cold start.

**Scope:**
- **Modify speak.py to support a `--daemon` or `--listen` mode:**
  - Load model once
  - Read lines from stdin (or a named pipe) in a loop
  - Synthesize and play each line
  - Exit on EOF or explicit shutdown command
- **Compare with server approach:**
  - Complexity: simpler (no IPC protocol, no client/server split)
  - Flexibility: less (single consumer, blocking I/O, harder to query status)
  - Reliability: process lifetime tied to parent shell
- **Assess interaction with agent invocation patterns:**
  - How do Claude Code agents currently call speak.py? (Bash tool → subprocess)
  - Can an agent keep a speak.py subprocess alive across multiple Bash calls?
  - If not, does the subprocess approach actually solve anything?
- **Edge cases:**
  - What happens if the process is killed mid-synthesis? (VRAM leak?)
  - Can the keep-alive process handle persona changes between lines?
  - Buffer management: does stdin buffering cause delays?

**Deliverable:** `docs/research/RQ-TTS-004_SUBPROCESS_KEEPALIVE.md` — Design, comparison with server approach, agent integration feasibility, edge case analysis.

**Key question:** Is subprocess keep-alive viable given how agents invoke speak.py, or does the process boundary make it moot?

---

### RQ-TTS-005: Kokoro as Fast Path

**Problem:** Kokoro (CPU, ONNX) is the fallback backend. If its cold start is negligible, it could serve as the "fast path" for sequential lines while Chatterbox handles single high-quality outputs. This is a tiered strategy: Kokoro for speed, Chatterbox for quality.

**Scope:**
- **Measure Kokoro cold start time** using the same phase breakdown as RQ-TTS-001:
  - Python imports + ONNX runtime init
  - Model loading
  - First inference
- **Compare audio quality** at conversational lengths (not just short signals):
  - Synthesize 5 sentences of combat narration with both backends
  - Subjective quality comparison: is Kokoro "good enough" for rapid sequential lines?
  - Note: Kokoro outputs 24kHz, resampled to 16kHz — any quality loss from resampling?
- **Hybrid strategy design:**
  - Kokoro for rapid sequential lines (combat narration, back-to-back events)
  - Chatterbox for single high-quality outputs (scene descriptions, dramatic moments, voice-cloned NPC dialogue)
  - Selection logic: who decides which backend to use per utterance?
- **Kokoro persistence:** Does Kokoro also benefit from persistent loading, or is ONNX fast enough that cold start is irrelevant?

**Deliverable:** `docs/research/RQ-TTS-005_KOKORO_FAST_PATH.md` — Timing comparison, quality assessment, hybrid strategy design, persistence analysis.

**Key question:** Is Kokoro fast enough that persistence is unnecessary, making it the natural choice for sequential narration?

---

### RQ-TTS-006: Streaming TTS Output

**Problem:** Even with cold start eliminated, Chatterbox Original takes ~10 seconds to synthesize a sentence (~40 it/s, ~400 steps). The player waits for the entire generation before hearing anything. Streaming could start playback after a partial generation, reducing perceived latency.

**Scope:**
- **Assess Chatterbox's generation loop:**
  - Does `model.generate()` return audio all at once, or can it yield chunks?
  - Is there a callback or hook mechanism in the sampling loop?
  - Does the denoising diffusion process produce usable audio at intermediate steps?
- **Minimum viable chunk size:**
  - What's the shortest audio chunk that sounds acceptable (not clipped, no artifacts)?
  - Does chunk-boundary stitching cause audible glitches?
- **Interaction with sentence-boundary chunking (TD-023):**
  - Current chunker in speak.py splits text at `. ` boundaries, max 55 words
  - If streaming is viable, does the chunker still need to exist?
  - Or does streaming replace chunking (stream within a long utterance rather than splitting into short ones)?
- **Turbo tier streaming:**
  - Does Chatterbox Turbo support partial output? (Different architecture from Original)
- **External prior art:**
  - XTTS v2 server mode: how does it handle streaming?
  - Bark: any community streaming implementations?
  - Tortoise-TTS: known for being slow — what workarounds exist?
  - Piper: lightweight, fast — different architecture but may inform "fast path" thinking

**Deliverable:** `docs/research/RQ-TTS-006_STREAMING_OUTPUT.md` — Chatterbox streaming feasibility, chunk size analysis, chunker interaction notes, prior art survey.

**Key question:** Can we start playing audio before generation is complete, and if so, what's the perceived latency reduction?

---

## Execution Protocol

### Priority Order

| Priority | RQ | Area | Rationale |
|----------|----|------|-----------|
| P0 | RQ-TTS-001 | Measurement | Must know where time goes before choosing a fix. All other RQs depend on this data. |
| P0 | RQ-TTS-002 | Measurement | VRAM budget determines whether persistence is even feasible. Gates RQ-TTS-003. |
| P1 | RQ-TTS-003 | Architecture | Persistent server is the highest-value fix if VRAM allows. Primary recommendation path. |
| P1 | RQ-TTS-004 | Architecture | Lightweight alternative to server. May be simpler if agent integration works. |
| P1 | RQ-TTS-005 | Strategy | Kokoro as fast path is complementary to persistence. Informs backend selection logic. |
| P2 | RQ-TTS-006 | Optimization | Streaming is a deeper optimization. Valuable but not required for MVP cold start fix. |

### Dispatch Model

P0 items (RQ-TTS-001, RQ-TTS-002) must be completed first — they produce the measurements that gate all architectural decisions. They can run in parallel (timing measurements don't interfere with VRAM measurements).

P1 items (RQ-TTS-003, RQ-TTS-004, RQ-TTS-005) depend on P0 data. RQ-TTS-003 and RQ-TTS-004 are alternative approaches — findings from one inform the other. RQ-TTS-005 can run in parallel with either.

P2 (RQ-TTS-006) can run anytime but benefits from P0 context.

All 6 RQs can be executed by a single builder in one session if the measurements are taken first.

### Success Criteria

The sprint is complete when:
1. All 6 deliverables exist in `docs/research/`
2. Each deliverable contains measured data (not estimates) where applicable
3. A clear recommendation is made: server daemon vs. keep-alive subprocess vs. Kokoro fast path vs. hybrid
4. If the recommended approach is straightforward, a working prototype exists
5. Interaction notes with WO-TTS-CHUNKING (Horizon 1) are documented — does this research change the chunking WO's scope?

---

## Relationship to Existing Work

| Existing Artifact | This Sprint's Relationship |
|-------------------|---------------------------|
| `scripts/speak.py` | The file being optimized. No production changes in this sprint — research only. |
| `aidm/immersion/chatterbox_tts_adapter.py` | The adapter's API surface is the foundation for any server/keep-alive design. Its lazy loader pattern is part of the problem (per-process loading). |
| `aidm/immersion/kokoro_tts_adapter.py` | RQ-TTS-005 evaluates this as a fast path alternative. |
| `HANDOFF_TTS_COLD_START_RESEARCH.md` | The research handoff that originated this sprint. This dispatch operationalizes the handoff into structured RQs. |
| WO-TTS-CHUNKING (Horizon 1) | Sentence-boundary chunking. This sprint may affect its scope — if streaming TTS is viable, chunking strategy changes. |
| RQ-SPRINT-009 (Voice Loop Latency) | Completed research that identified STT as 50-80% of pipeline latency. TTS cold start is a separate, additive latency on top of that finding. |

---

## Retrospective

- **Process:** This dispatch follows the same structure as WO-RESEARCH-SPRINT-001. The format worked well there — 11 RQs all completed in a single session. This sprint is smaller (6 RQs) and more focused (single subsystem), which should allow deeper investigation per question.

- **Scope control:** The handoff (HANDOFF_TTS_COLD_START_RESEARCH.md) listed 5 research areas. This dispatch restructures them into 6 RQs — splitting "persistent model server" and "subprocess keep-alive" into separate questions because they represent genuinely different architectural approaches with different trade-offs. "External prior art" was folded into RQ-TTS-006 (streaming) where it's most relevant rather than standing alone.

- **Risk:** The primary risk is that VRAM budget (RQ-TTS-002) kills the persistence approach entirely. If Chatterbox + future LLM + future SDXL don't fit in 12GB, the server approach becomes a VRAM management problem rather than a simple "keep it loaded" solution. RQ-TTS-005 (Kokoro fast path) provides a fallback strategy in that case.

---

---

## PM Amendments (2026-02-14)

1. **Horizon assignment:** H1-adjacent (not H0). Does not gate RED block lift. Parallel-safe with H0 WOs — can dispatch immediately.
2. **WO-TTS-CHUNKING interaction:** If RQ-TTS-003 (persistent server) or RQ-TTS-006 (streaming) findings change the chunking strategy, those findings must be explicitly flagged in the deliverable so PM can adjust WO-TTS-CHUNKING scope before it ships.
3. **No production code changes:** Prototypes go in `scripts/` or `docs/research/`, not in `aidm/`. Promotion to production requires a separate WO.
4. **All 6 RQs approved as scoped.** Priority ordering, single-builder-session model, and deliverable paths approved without changes.

---

*End of dispatch.*
