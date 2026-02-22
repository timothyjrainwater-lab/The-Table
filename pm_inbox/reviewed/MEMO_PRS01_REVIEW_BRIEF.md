# MEMO: PRS-01 Review Brief — For Thunder
**Lifecycle:** NEW

**Purpose:** Executive summary of the Publishing Readiness Spec. Read this, decide approve/reject, then Slate can start dispatching builder WOs in parallel with BURST-001 closure.

**Full spec:** `docs/contracts/PUBLISHING_READINESS_SPEC.md` (410 lines, v1.0)

---

## What PRS-01 Is

A governance contract defining 9 publish gates (P1-P9) that must all PASS on a signed commit before any release. An orchestrator script runs all gates and produces an RC evidence packet. No release without full green board.

**Durable rule (DR-PRS-01):** "We do not consider publishing until all publish gates PASS on a signed commit and the RC evidence packet exists and matches that commit exactly."

## What PRS-01 Is NOT

- Not a blocker for BURST-001 or any development work
- Not a change to game mechanics, combat, or voice pipeline
- Not a license decision (license TBD — P4 just ensures whatever we pick is enforced)

---

## The 9 Gates

| Gate | What It Checks | New Script Needed? |
|------|----------------|-------------------|
| **P1: Clean Tree** | No uncommitted changes | No — `git status` |
| **P2: Test Suite** | All tests pass | No — `pytest` |
| **P3: Asset Scan** | No model weights, audio, images in repo | **Yes** |
| **P4: License Ledger** | Every dependency documented with SPDX license | **Yes** |
| **P5: Secret Scan** | No API keys/tokens in tracked files | **Yes** |
| **P6: Offline Guarantee** | No network calls in default config | **Yes** (static + runtime) |
| **P7: Fail-Closed Startup** | Missing assets → deterministic error + halt | **Yes** |
| **P8: IP Hygiene** | No trademarked game-system proper nouns | **Yes** |
| **P9: Privacy Statement** | `docs/PRIVACY.md` exists, covers all paths | **Yes** (validator) |

**P1 and P2 use existing tooling.** P3-P9 need builder WOs.

---

## Builder WO Sequence (6 WOs)

All depend on PRS-01 being approved (frozen). Order:

| # | WO | Covers | Can Parallel? |
|---|-----|--------|---------------|
| 1 | WO-PRS-SCAN-001 | P3 + P5 + P8 (asset scan, secret scan, IP scan) | Yes — first batch |
| 2 | WO-PRS-LICENSE-001 | P4 (license ledger + lint) | Yes — parallel with #1 |
| 3 | WO-PRS-OFFLINE-001 | P6 (offline guarantee, static + runtime) | Yes — parallel with #1 |
| 4 | WO-PRS-FIRSTRUN-001 | P7 (fail-closed first run) | Yes — parallel with #1 |
| 5 | WO-PRS-DOCS-001 | P9 (privacy statement + OGL notice) | Yes — parallel with #1 |
| 6 | WO-PRS-ORCHESTRATOR-001 | RC packet builder | **After all above** |

WOs 1-5 have no dependencies on each other — they can all run in parallel. WO 6 (orchestrator) runs after all scan WOs complete.

---

## Key Decisions Already Made

These were resolved during spec drafting (Aegis audit + Thunder decisions):

1. **Ship posture:** Source code + docs only. No model weights, no audio, no binaries.
2. **Runtime model:** Offline-first. Network is opt-in and default-off.
3. **Donation links:** Only appear after P1-P9 PASS on a tagged release. Non-transactional.
4. **pm_inbox publishing:** Curated excerpts only. Full pm_inbox is private. Doctrine files are published.
5. **Privacy model:** All data local. No telemetry. Microphone opt-in only.
6. **OGL/SRD compliance:** OGL notice required. IP scan (P8) enforces no non-OGL content.

## Decisions Still Open

1. **Project license:** MIT vs Apache-2.0 vs GPL-3.0. Decision needed before P4 ledger can assess compatibility. Not blocking spec approval — just blocking P4 *execution*.

---

## What Approval Means

If you approve:
- PRS-01 spec is FROZEN (v1.0 → v1.0 ACCEPTED)
- Slate can draft the first batch of builder WOs (starting with WO-PRS-SCAN-001)
- Builder WOs run in parallel with BURST-001 closure (no conflict)
- License decision needed before WO-PRS-LICENSE-001 can fully execute

If you reject:
- Specify what needs changing
- Slate revises, resubmits

---

## Slate's Assessment

The spec is thorough, self-consistent, and well-scoped. The boundary statement (§11) properly firewalls PRS-01 from game mechanics and development workflow. The 6-WO sequence is reasonable — WOs 1-5 are embarrassingly parallel.

One note: the project license decision (MIT/Apache/GPL) will need to happen before the license ledger WO can fully execute. That's a Thunder decision, not a spec issue. Spec approval can proceed independently.

**Recommendation:** Approve. Dispatch WO-PRS-SCAN-001 as the first parallel builder WO whenever you have builder bandwidth.
