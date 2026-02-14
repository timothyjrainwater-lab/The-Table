# PM Briefing — Current

**Last updated:** 2026-02-14 (2 H1 WOs drafted — WEAPON-PLUMBING-001, RNG-PROTOCOL-001)

---

## Stoplight: GREEN

H0 complete. 5,581 tests pass. RED block lifted. H1 WO drafting in progress.

## Requires Operator Action (NOW)

- [ ] **Dispatch WO-WEAPON-PLUMBING-001** — `pm_inbox/WO-WEAPON-PLUMBING-001_DISPATCH.md`. is_ranged + disarm mods + sunder grip. Highest-impact H1 item. Activates 3 dormant fixes.
- [ ] **Dispatch WO-RNG-PROTOCOL-001** — `pm_inbox/WO-RNG-PROTOCOL-001_DISPATCH.md`. RNGProvider Protocol extraction. Type-level refactor, zero logic changes. Parallel-safe.
- [ ] **Dispatch WO-TTS-COLD-START-RESEARCH** — `pm_inbox/WO-TTS-COLD-START-RESEARCH_DISPATCH.md`. 6 RQs. Parallel-safe.
- [ ] **XP table spot-check (P1-B)** — Non-blocking. 5+ cells from levels 14-20 vs physical DMG.

All 3 WOs are parallel-safe — dispatch to separate builders simultaneously.

## PM Action Queue (drafting in progress)

- [ ] **Draft WO-TTS-CHUNKING** — Sentence-boundary TTS chunking (TD-023).
- [ ] **Draft WO-BRIEF-WIDTH** — NarrativeBrief multi-target + causal chains + conditions.
- [ ] **Draft WO-NARRATION-VALIDATOR** — Runtime validation.
- [ ] **Draft WO-COMPILE-VALIDATE** — Compile-time Layer A vs B cross-validation.
- [ ] **Resolver deduplication** — P4 WO after weapon plumbing.

## PM Notes for Future WO Drafting

- WO-DISCOVERY-TIERS (H2): Cross-ref RQ-005/006/010 — three independent touches on DiscoveryLog.
- WO-RULEBOOK-GEN + WO-CONTAIN-PARAM (H2): Share template infrastructure, don't build two systems.

## Active Operational Files

- `BURST_INTAKE_QUEUE.md` — BURST-001 thru 004 (1 READY, 2 NOT STARTED, 1 PARTIAL)
- `WO-WEAPON-PLUMBING-001_DISPATCH.md` — **DISPATCH-READY**
- `WO-RNG-PROTOCOL-001_DISPATCH.md` — **DISPATCH-READY**
- `WO-TTS-COLD-START-RESEARCH_DISPATCH.md` — **PM-REVIEWED, DISPATCH-READY**

## Persistent Files

- `README.md` — Inbox hygiene rules
- `PM_BRIEFING_CURRENT.md` — This file
- `REHYDRATION_KERNEL_LATEST.md` — PM rehydration block
