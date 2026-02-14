# PM Briefing — Current

**Last updated:** 2026-02-14 (inbox hygiene — 10 files archived, 3/15 active)

---

## Requires Operator Action (NOW)

- [ ] **Relay H0 completion report to PM** — `pm_inbox/WO-H0-BUNDLE_COMPLETION.md`. All 3 H0 WOs committed (GAP-B-001, VERSION-MVP, GOV-SESSION-001). 5,581 tests pass. PM needs to review and approve gate lift.
- [ ] **XP table spot-check (P1-B)** — Non-blocking. 5+ cells from levels 14-20 vs physical DMG.
- [ ] **Dispatch WO-TTS-COLD-START-RESEARCH** — `pm_inbox/WO-TTS-COLD-START-RESEARCH_DISPATCH.md`. PM-REVIEWED (ACCEPTED). 6 RQs. H1-adjacent, parallel-safe. Can dispatch now.

## Awaiting Dispatch (BLOCKED behind PM review of H0 completion)

- [ ] **RED block lift** — After PM reviews H0 completion report. Preflight already PASSED. All code committed.
- [ ] **WO-WEAPON-PLUMBING-001** — Bundle: is_ranged + disarm mods + sunder grip. Horizon 1.
- [ ] **Resolver deduplication** — Second P4 WO after weapon plumbing. Horizon 1.

## Horizon 1 WOs (Draft After Gate Lift)

- [ ] WO-TTS-CHUNKING — Sentence-boundary TTS chunking (TD-023). Run parallel with or before BRIEF-WIDTH.
- [ ] WO-BRIEF-WIDTH — NarrativeBrief multi-target + causal chains + conditions. Acceptance: re-run RQ-003's 20 stress-test scenarios.
- [ ] WO-NARRATION-VALIDATOR — Runtime validation: P0 negative rules (RV-001/002/008) + P1 positive validation from RQ-004.
- [ ] WO-COMPILE-VALIDATE — Compile-time Layer A vs B cross-validation.
- [ ] WO-RNG-PROTOCOL — RNGProvider Protocol extraction.

## PM Notes for Future WO Drafting

- WO-DISCOVERY-TIERS (H2): Cross-ref RQ-005/006/010 — three independent touches on DiscoveryLog.
- WO-RULEBOOK-GEN + WO-CONTAIN-PARAM (H2): Share template infrastructure, don't build two systems.
- Multi-deliverable sprints: Add "cross-RQ gap analysis" as standard 4th pass after PM synthesis.

## Active Operational Files

- `BURST_INTAKE_QUEUE.md` — BURST-001 thru 004 (1 READY, 2 NOT STARTED, 1 PARTIAL)
- `WO-H0-BUNDLE_COMPLETION.md` — **H0 completion report. Awaiting PM review.**
- `WO-TTS-COLD-START-RESEARCH_DISPATCH.md` — **PM-REVIEWED, DISPATCH-READY** (H1-adjacent, parallel-safe)

## Recently Archived (this session)

10 files moved to `pm_inbox/reviewed/`:
- H0 dispatch docs (GAP-B-001, VERSION-MVP, GOV-SESSION-001, VOICE-HOOK-001) — all COMPLETE
- Research sprint docs (DISPATCH, COMPLETION, SYNTHESIS) — all consumed
- DEBRIEF_BS_BUDDY, DEBRIEF_RESEARCH_SPRINT_001 — consumed
- HANDOFF_TTS_COLD_START_RESEARCH — operationalized into WO dispatch

## Persistent Files

- `README.md` — Inbox hygiene rules
- `PM_BRIEFING_CURRENT.md` — This file
- `REHYDRATION_KERNEL_LATEST.md` — PM rehydration block
