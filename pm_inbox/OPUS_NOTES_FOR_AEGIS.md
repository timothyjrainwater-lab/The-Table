# Opus Notes for Aegis

Persistent communication channel from the principal engineer (Opus) to the PM (Aegis).
Thunder relays this file to GPT when relevant, or on request.

**How this works:**
- Opus appends notes here during work sessions — observations, concerns, suggestions, audit findings, anything the PM should know.
- Each entry is timestamped with the session date.
- Thunder pastes or uploads this to GPT whenever he wants to sync.
- After GPT has consumed the notes, Thunder can clear the "delivered" entries or move them to a `## Delivered` section at the bottom.

---

## Active Notes

### 2026-02-10 — Post M1 Infrastructure + Spring Cleaning Session

**1. WO-M1-01 (Event-Sourced Replay): Classification Audit Note**

Sonnet C's replay_runner.py is live with full reducer (AC-09/AC-10 passing). Several events are classified as INFORMATIONAL that could become state-mutating in future CPs: `bull_rush_success`, `trip_success`, `grapple_success`, `overrun_success`, `ability_score_death`, `derived_stats_recalculated`. Current classification is correct — state changes flow through separate `move`/`hp_changed`/`condition_applied` events. But if any maneuver result ever needs to directly mutate state, it must be promoted from INFORMATIONAL to MUTATING and get a reducer handler. Documented as a migration rule in replay_runner.py comments.

**2. GAP-01 (Payload Schema Divergence): Open, Candidate for Next WO**

`permanent_stats.py` emits `hp_changed` with `{old_hp, new_hp, cause}` while every other emitter uses `{hp_before, hp_after, delta, source}`. The reducer accepts both via fallback. Clean fix: 1-2 files, low risk. Recommend scheduling as a work order.

**3. Documentation Spring Cleaning Complete**

Removed 17 superseded docs (6,775 lines) + fixed 58 stale cross-references across 13 files. All `AIDM_PROJECT_ACTION_PLAN_V2` references now point to `AIDM_EXECUTION_ROADMAP_V3`. Pre-global-audit analysis docs deleted (GLOBAL_AUDIT versions kept). Agent D analysis docs deleted (content captured in global audit). Non-FINAL CP19 variants deleted (FINAL versions kept). PROJECT_STATE_DIGEST and KNOWN_TECH_DEBT headers updated to 1712 tests.

**4. Agent Infrastructure Hardened**

- projectInstructions test count updated: 594 → 1700+ (was causing confusion)
- AGENT_DEVELOPMENT_GUIDELINES.md now documents BL-017, BL-018, BL-020 with code examples
- Onboarding checklist Step 2 updated: 1331+ → 1700+ tests, <5s → <10s
- .gitignore expanded: __pycache__, *.pyc, temp files now excluded
- Junk files cleaned from repo root (nul, =0.22.0, =0.4.6, =1.16.0, =2.90, =1.0.0)

**5. Commits Made This Session**

- `ad30e50` — M1 infrastructure checkpoint (338 files, 57K insertions)
- `53cadee` — Documentation spring cleaning (17 files deleted)
- `88e0457` — Reference fixes + scratch cleanup (58 refs, 3 scratch files)
- Next commit pending: boundary law docs + projectInstructions update

---

## Delivered

### 2026-02-10 — Items Resolved (Previously Active)

**WO-M1-02 decision** — Delivered to Sonnet D as inject-only pattern. Agent DI executed and delivered (report in pm_inbox/reviewed/).

**Test count inconsistency** — FIXED. projectInstructions, onboarding checklist, PSD, and tech debt headers all now say 1700+/1712.

**pm_inbox workflow** — LIVE and functioning. Multiple deliverables have flowed through the system (WO-M1-02 through WO-M1-05).

_(Thunder moves consumed notes here after relaying to GPT)_
