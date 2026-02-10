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

### 2026-02-10 — Post WO-M1-01/WO-M1-02 Session

**1. WO-M1-01 (Event-Sourced Replay): Implemented, Needs Classification Audit**

Sonnet C implemented replay_runner.py with the full reducer. Tests pass. However, several events I flagged as potentially state-mutating ended up in INFORMATIONAL_EVENTS: `bull_rush_success`, `trip_success`, `grapple_success`, `overrun_success`, `ability_score_death`, `derived_stats_recalculated`. This is defensible today — those events don't currently mutate state directly; the actual mutations happen via separate `move`, `hp_changed`, or `condition_applied` events. But it's a design assumption worth documenting: if any maneuver result ever needs to directly mutate state, it must be promoted from INFORMATIONAL to MUTATING and get a reducer handler. Not a bug, but a future-proofing note.

**2. WO-M1-02 (Deterministic IDs & Clocks): Decision Delivered, Not Yet Executed**

I chose option (a): inject-only, no deterministic service. Rationale: only ~5 call sites use `uuid.uuid4()` or `datetime.utcnow()` as defaults. Remove `default_factory` so callers get `TypeError` if they forget — fail-loud beats silent nondeterminism. Sonnet D has the decision but hasn't started execution yet.

**3. GAP-01 (Payload Schema Divergence): Open, Low Priority**

`permanent_stats.py` emits `hp_changed` with `{old_hp, new_hp, cause}` while every other emitter uses `{hp_before, hp_after, delta, source}`. The reducer accepts both as a workaround. Good candidate for a small cleanup work order — 1-2 files, low risk. Suggest WO-M1-03 or similar.

**4. Test Count Inconsistency in Agent Instructions**

`projectInstructions` says "expect 594+ tests" but onboarding checklist says "1331+ tests." The latter is correct post-audit. 594 still works as a floor but may confuse new agents. Low priority — flag if you want me to bump it.

**5. pm_inbox Workflow Live**

Drop zone is set up. Sonnet agents have rule (6) in projectInstructions and Step 8 in the onboarding checklist. They'll auto-drop deliverables on their next fresh session.

---

## Delivered

_(Thunder moves consumed notes here after relaying to GPT)_
