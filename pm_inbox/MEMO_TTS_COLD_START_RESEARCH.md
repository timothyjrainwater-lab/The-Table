# MEMO: TTS Cold Start Research Complete — Server Daemon Recommended

**From:** Builder (Opus 4.6)
**Date:** 2026-02-14
**Session scope:** Execute WO-TTS-COLD-START-RESEARCH — 6 RQs on TTS cold start latency.
**Lifecycle:** NEW
**Commit:** UNCOMMITTED

---

## Action Items (PM decides, builder executes)

1. **Dispatch a `speak_server.py` implementation WO** — Builder executes: build HTTP server on localhost:9452 wrapping `ChatterboxTTSAdapter`, modify `speak.py` to try server before cold load. Blocks: combat narration pacing, sequential voice output.

2. **Fix Turbo `from_pretrained()` token bug** — Builder executes: update `_ChatterboxLoader.get_turbo()` to prefer `from_local()` with HF cache snapshot path. Blocks: Turbo tier reliability for operators without HF token configured. Can bundle into server WO or standalone fix.

3. **No scope change to WO-TTS-CHUNKING-001** — Confirmed: neither persistence nor streaming findings alter chunking strategy. Dispatch as-is.

## Status Updates (Informational only)

- All 6 RQs completed with measured data (not estimates)
- 6 deliverables written to `docs/research/RQ-TTS-001` through `RQ-TTS-006`
- 2 benchmark scripts created: `scripts/bench_cold_start.py`, `scripts/bench_vram.py`
- Primary recommendation: **persistent HTTP server** eliminates 81% of cold start (15.1s of 18.6s)
- Rejected alternatives: subprocess keep-alive (broken by Bash process isolation), Kokoro fast path (3x slower at steady state), audio streaming (architecturally impossible with diffusion)

## Deferred Items (Not blocking, act when convenient)

- **Turbo load time optimization** — Turbo takes 14.3s to load (vs Original's 7.9s). If combat mode loads Turbo on demand, first combat line has a 14s penalty. Could pre-load Turbo at server startup (costs 4.2 GB VRAM). Decision deferred to server implementation WO.
- **VRAM management endpoints** — Server design includes `/load-turbo`, `/unload-turbo`, `/health` endpoints for dynamic VRAM management. Not needed for MVP; design documented in RQ-TTS-003.
- **Alternative TTS backends for streaming** — If true streaming is ever required, evaluate XTTS v2 (autoregressive, streamable) or Piper (VITS, very fast). This is a backend replacement, not a Chatterbox optimization.

## Retrospective

- **Fragility:** The HuggingFace `from_pretrained()` path is fragile. Original worked with `HF_HUB_OFFLINE=1` but Turbo hardcodes `token=True`, making it fail without a configured HF token. The lazy loader silently masks this by falling back to Original. The benchmark scripts exposed this because they load tiers independently — production code hides it behind the tier selection logic.

- **Process feedback:** The WO dispatch format worked well for this sprint. Having 6 RQs with clear scope and priority ordering meant P0 measurements ran first and directly informed P1 analysis. The "single builder, single session" model was feasible — all 6 RQs completed without context pressure. The dispatch's hypothesis about Kokoro as fast path was data-inverted (Kokoro is slower, not faster), which is exactly why P0 measurement gates P1 strategy.

- **Methodology:** Running benchmarks before design work is the right sequencing. The P0 data killed two of three P1 strategies immediately (subprocess keep-alive is broken by process isolation; Kokoro is 3x slower). Without data, the architecture discussion would have been speculative. The dispatch's priority ordering enforced this discipline.

- **Concerns:** The `import chatterbox.tts` costing 3.8 seconds is a dependency chain problem — it pulls in transformers, diffusers, safetensors, and heavy ML infrastructure at import time. This is not under our control and may get worse with library updates. The persistent server amortizes it, but any future "lightweight" TTS usage (e.g., a quick CLI check without synthesis) will still pay this cost.

---

**End of Memo**
