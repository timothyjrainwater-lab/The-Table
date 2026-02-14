# PM Briefing — Current

**Last updated:** 2026-02-14 (WO-RNG-PROTOCOL-001 COMPLETED; 5 H1 WOs remain dispatch-ready)

---

## Stoplight: GREEN

H0 complete. 5,615 tests pass. RED block lifted. H1 WO batch in progress — WO-RNG-PROTOCOL-001 completed.

## Recently Completed

- **WO-TTS-COLD-START-RESEARCH** — COMPLETED. 6 RQs executed. Recommendation: persistent HTTP server (`speak_server.py`) eliminates 81% of cold start (15s of 18.6s). Subprocess keep-alive rejected, Kokoro fast path rejected, streaming infeasible. Memo filed: [MEMO_TTS_COLD_START_RESEARCH.md](pm_inbox/MEMO_TTS_COLD_START_RESEARCH.md)
- **WO-RNG-PROTOCOL-001** — COMPLETED. RNGProvider + RandomStream Protocols extracted. 19 files updated (type annotations only). Zero regressions. Debrief filed: [DEBRIEF_WO-RNG-PROTOCOL-001.md](pm_inbox/DEBRIEF_WO-RNG-PROTOCOL-001.md)

## Requires Operator Action (NOW)

1. **Dispatch WO-WEAPON-PLUMBING-001** — [WO-WEAPON-PLUMBING-001_DISPATCH.md](pm_inbox/WO-WEAPON-PLUMBING-001_DISPATCH.md)
   is_ranged + disarm mods + sunder grip. Highest-impact H1 item. Activates 3 dormant fixes.

2. **Dispatch WO-TTS-CHUNKING-001** — [WO-TTS-CHUNKING-001_DISPATCH.md](pm_inbox/WO-TTS-CHUNKING-001_DISPATCH.md)
   Sentence-boundary chunking into adapter layer. Fixes silent truncation (TD-023). Parallel-safe.

4. **Dispatch WO-BRIEF-WIDTH-001** — [WO-BRIEF-WIDTH-001_DISPATCH.md](pm_inbox/WO-BRIEF-WIDTH-001_DISPATCH.md)
   Multi-target + causal chains + condition stacking. Fixes 6/9 narration stress-test failures. Parallel-safe.

5. **Dispatch WO-NARRATION-VALIDATOR-001** — [WO-NARRATION-VALIDATOR-001_DISPATCH.md](pm_inbox/WO-NARRATION-VALIDATOR-001_DISPATCH.md)
   Runtime P0 negative rules (RV-001/002/008) + P1 structural rules. Depends on WO-BRIEF-WIDTH-001 for condition fields.

6. **Dispatch WO-COMPILE-VALIDATE-001** — [WO-COMPILE-VALIDATE-001_DISPATCH.md](pm_inbox/WO-COMPILE-VALIDATE-001_DISPATCH.md)
   CT-001 through CT-007 cross-validation + content_id emission in resolver events. Activates GAP-B-001 pipeline.

7. **XP table spot-check (P1-B)** — Non-blocking. 5+ cells from levels 14-20 vs physical DMG.

**Dispatch guidance:**
- WO-WEAPON-PLUMBING-001, WO-TTS-COLD-START-RESEARCH, WO-TTS-CHUNKING-001 — all parallel-safe, dispatch simultaneously.
- WO-BRIEF-WIDTH-001 — parallel-safe with all above.
- WO-NARRATION-VALIDATOR-001 — depends on WO-BRIEF-WIDTH-001 (condition fields). Dispatch after BRIEF-WIDTH completes, or in parallel if builder can stub the dependency.
- WO-COMPILE-VALIDATE-001 — parallel-safe with everything except WO-NARRATION-VALIDATOR-001 (both touch narration pipeline, but at different layers). Prefer parallel dispatch.

## PM Action Queue (drafting in progress)

- [x] ~~Draft WO-TTS-CHUNKING~~ — DONE → `WO-TTS-CHUNKING-001_DISPATCH.md`
- [x] ~~Draft WO-BRIEF-WIDTH~~ — DONE → `WO-BRIEF-WIDTH-001_DISPATCH.md`
- [x] ~~Draft WO-NARRATION-VALIDATOR~~ — DONE → `WO-NARRATION-VALIDATOR-001_DISPATCH.md`
- [x] ~~Draft WO-COMPILE-VALIDATE~~ — DONE → `WO-COMPILE-VALIDATE-001_DISPATCH.md`
- [ ] **Resolver deduplication** — P4 WO after weapon plumbing.

## PM Notes for Future WO Drafting

- WO-DISCOVERY-TIERS (H2): Cross-ref RQ-005/006/010 — three independent touches on DiscoveryLog.
- WO-RULEBOOK-GEN + WO-CONTAIN-PARAM (H2): Share template infrastructure, don't build two systems.
- Resolver deduplication: P4, sequence after WO-WEAPON-PLUMBING-001 completes.

## Active Operational Files

- [BURST_INTAKE_QUEUE.md](pm_inbox/BURST_INTAKE_QUEUE.md) — BURST-001 thru 004 (1 READY, 2 NOT STARTED, 1 PARTIAL)
- [WO-WEAPON-PLUMBING-001_DISPATCH.md](pm_inbox/WO-WEAPON-PLUMBING-001_DISPATCH.md) — **DISPATCH-READY**
- [WO-TTS-COLD-START-RESEARCH_DISPATCH.md](pm_inbox/WO-TTS-COLD-START-RESEARCH_DISPATCH.md) — **PM-REVIEWED, DISPATCH-READY**
- [WO-TTS-CHUNKING-001_DISPATCH.md](pm_inbox/WO-TTS-CHUNKING-001_DISPATCH.md) — **DISPATCH-READY**
- [WO-BRIEF-WIDTH-001_DISPATCH.md](pm_inbox/WO-BRIEF-WIDTH-001_DISPATCH.md) — **DISPATCH-READY**
- [WO-NARRATION-VALIDATOR-001_DISPATCH.md](pm_inbox/WO-NARRATION-VALIDATOR-001_DISPATCH.md) — **DISPATCH-READY**
- [WO-COMPILE-VALIDATE-001_DISPATCH.md](pm_inbox/WO-COMPILE-VALIDATE-001_DISPATCH.md) — **DISPATCH-READY**

## Persistent Files

- `README.md` — Inbox hygiene rules
- `PM_BRIEFING_CURRENT.md` — This file
- `REHYDRATION_KERNEL_LATEST.md` — PM rehydration block
