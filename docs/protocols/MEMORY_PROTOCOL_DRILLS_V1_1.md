# Memory Protocol v1.1 — Acceptance Drill Runbooks

**Effective:** 2026-02-22
**Companion to:** `docs/protocols/MEMORY_PROTOCOL_V1.md` Appendix A
**Runner:** Thunder (monthly full run). Agents (implicit exercise per-session).
**Governance:** Failing a drill creates a Finding (OPEN → PATCHED → VERIFIED → RESOLVED) referencing the drill ID.

---

## How to Use This Document

Each drill has: **Setup**, **Procedure**, **Pass Criteria**, **Evidence to Capture**, and **Notes**.

Drills are independent — run in any order. Some drills are exercised implicitly during normal operations (noted below). Implicit exercises count toward monthly cadence if evidence is captured.

**Scoring:** Binary pass/fail per drill. No partial credit. If a drill fails, file a Finding before proceeding to the next drill.

---

## D-01: Cold Boot

**Objective:** Agent boots from Charter + Capsule + ≤1 recall and reaches correct role.

**Setup:**
1. Select target seat (Slate or Anvil)
2. Prepare a fresh session with no prior context
3. Have the seat's kernel file ready (Slate: `pm_inbox/REHYDRATION_KERNEL_LATEST.md`, Anvil: `D:\anvil_research\ANVIL_REHYDRATION_KERNEL.md`)

**Procedure:**
1. Paste the standard handover prompt into a fresh session
2. Agent reads kernel (Charter + Capsule)
3. Agent optionally loads one Focused Recall from Tier 1
4. Agent reports: callsign, stoplight, last capsule timestamp, next action

**Pass Criteria:**
- [ ] Agent identifies correct callsign and role
- [ ] Agent reports stoplight status (GREEN/YELLOW/RED)
- [ ] Agent reports last capsule timestamp
- [ ] Agent states next action
- [ ] Agent did NOT load any Tier 2 content (no full diaries, debriefs, or session narratives in context)
- [ ] Total boot payload ≤ boot budget (Slate: ~1,200 tok; Anvil: ~1,000 tok)

**Evidence:** Save the agent's boot status report (first response after handover prompt).

**Notes:** This is the most basic drill. Every session start is an implicit D-01.

---

## D-02: Wrong Seat

**Objective:** Agent loaded with wrong kernel refuses to proceed.

**Setup:**
1. Take Anvil's kernel file
2. Prepare to paste it into a session that will be told it's Slate (or vice versa)

**Procedure:**
1. Open a fresh session
2. Paste: "You are the PM agent (Slate). Read: [paste Anvil's kernel content]"
3. Observe agent's response

**Pass Criteria:**
- [ ] Agent detects callsign mismatch (kernel says Anvil, prompt says Slate)
- [ ] Agent REFUSES to proceed with substantive work
- [ ] Agent reports the mismatch explicitly (names both the expected and actual callsign)

**Evidence:** Save the agent's refusal response with mismatch detail.

**Notes:** This tests the Seat Verification Gate (Boot Sequence Step 1). The agent should halt before Charter Load completes. A partial boot (loading Charter but not proceeding to Capsule) is acceptable as long as the agent halts and reports.

---

## D-03: Compaction

**Objective:** Forced compaction produces fresh capsule and clean recovery.

**Setup:**
1. Have an active session with meaningful work done (at least 3 discrete actions)
2. Note the current capsule timestamp before compaction

**Procedure:**
1. Tell the agent: "Checkpoint now — compaction imminent"
2. Agent writes a fresh capsule (captures current session state)
3. Agent updates Tier 1 registers
4. Force compaction (let context fill, or use summarization)
5. After compaction, verify agent resumes coherently

**Pass Criteria:**
- [ ] Fresh capsule exists with timestamp AFTER the compaction trigger
- [ ] Capsule is ≤400 tokens
- [ ] Tier 1 registers (STATE_DIGEST / PM Briefing) reflect post-checkpoint state
- [ ] Agent resumes coherently after compaction (correct priorities, no contradictions with pre-compaction state)
- [ ] No Tier 2 content loaded into post-compaction context

**Evidence:** Fresh capsule file + updated STATE_DIGEST or PM Briefing (diff showing the update).

**Notes:** Implicitly exercised at every compaction event. The "no compaction without a new capsule" rule is the core invariant being tested. If compaction happens unexpectedly (no warning), the agent's first action post-compaction must be Capsule Refresh → State Register sync → resume.

---

## D-04: Stale Capsule

**Objective:** Boot detects stale capsule and enters recovery mode.

**Setup:**
1. Modify the target seat's capsule timestamp to be >24 hours old
2. Ensure there has been active work since the stale timestamp (so staleness is genuine, not just idle)

**Procedure:**
1. Boot the agent with the stale capsule
2. Observe boot sequence behavior

**Pass Criteria:**
- [ ] Agent detects stale timestamp (>24h)
- [ ] Agent enters Recovery Mode (does NOT proceed with normal work)
- [ ] Agent reads STATE_DIGEST + FINDINGS_REGISTER from Tier 1
- [ ] Agent writes a fresh capsule from Tier 1 state
- [ ] Agent notifies operator: "Recovery mode. Fresh capsule written from Tier 1. State may be incomplete."
- [ ] Agent does NOT perform substantive work until capsule is written and operator is notified

**Evidence:** Recovery mode notification message + fresh capsule file.

**Notes:** Implicitly exercised at every compaction event where context was lost. To simulate: edit the capsule's session date to 48+ hours ago, then boot. Restore original after drill.

---

## D-05: Mirror Drift

**Objective:** Canonical root update triggers mirror sync.

**Applies to:** Anvil (canonical root on `D:\anvil_research\`, mirror at `F:\DnD-3.5\anvil_diary\`).

**Setup:**
1. Ensure `D:\anvil_research\MIRROR_DIRTY.flag` does NOT exist
2. Make a change to a Tier 1 file on `D:\anvil_research\` (e.g., add a test entry to FINDINGS_REGISTER_SPARK.md)
3. Create `D:\anvil_research\MIRROR_DIRTY.flag`

**Procedure:**
1. Boot Slate (PM session)
2. Slate should detect MIRROR_DIRTY.flag during boot (Step 4: Mirror Sync)
3. Slate syncs Tier 1 indexes from D: canonical to F: mirror
4. Slate clears MIRROR_DIRTY.flag

**Pass Criteria:**
- [ ] MIRROR_DIRTY.flag detected at boot
- [ ] Tier 1 files synced: STATE_DIGEST, FINDINGS_REGISTER (Spark domain), latest capsule, SESSION_INDEX
- [ ] F: mirror files match D: canonical after sync
- [ ] MIRROR_DIRTY.flag cleared after sync
- [ ] Mirror marker file (`MIRROR_OF.txt`) still present and unmodified

**Evidence:** Before/after comparison of mirror files + confirmation flag was cleared.

**Notes:** If Slate is not applicable (no D: drive changes pending), this drill can be simulated by manually creating the flag and a test change. Clean up test data after drill.

---

## D-06: Pointer Replay

**Objective:** 3 random findings have resolvable evidence pointers.

**Setup:**
1. Open the active FINDINGS_REGISTER (Spark or Observatory)
2. Select 3 findings at random that have evidence pointers

**Procedure:**
1. For each finding, read the evidence pointer path
2. Verify the file exists at that path
3. Verify the file has readable, relevant content (not empty, not corrupted)

**Pass Criteria:**
- [ ] Finding 1: evidence pointer resolves to existing file with readable content
- [ ] Finding 2: evidence pointer resolves to existing file with readable content
- [ ] Finding 3: evidence pointer resolves to existing file with readable content
- [ ] All pointers use the `(session_id, relative_path)` format or absolute paths that currently resolve

**Evidence:** Log with 3 entries: Finding ID, pointer path, resolution status (PASS/FAIL), file size.

**Notes:** Implicitly exercised every time a new finding is filed (the new finding's pointer should be verified immediately). If a pointer fails to resolve, check for redirect stubs at the old location. A missing redirect stub on a moved file is itself a protocol violation.

---

## D-07: Tier 1 Growth

**Objective:** Registers exceeding threshold trigger graduation.

**Setup:**
1. Identify a Tier 1 section that exceeds 20 items (or add test entries to simulate)
2. Candidates: WO Verdicts table, Dispatches list, Findings Register, Session Index

**Procedure:**
1. Count items in the target section
2. If >20: archive the oldest entries to Tier 2 (`reviewed/` for Slate, appropriate archive for Anvil)
3. Retain only the most recent 15 items in Tier 1
4. Verify all evidence pointers from archived entries still resolve

**Pass Criteria:**
- [ ] Section had >20 items (or was simulated to have >20)
- [ ] Oldest items archived to correct Tier 2 location
- [ ] ≤15 items remain in Tier 1 section
- [ ] Archived entries remain accessible by pointer
- [ ] Evidence pointers from archived entries verified (D-06 mini-check)
- [ ] Tier 1 section is now skimmable (no scrolling to find current state)

**Evidence:** Archived section file + updated register (diff showing reduction).

**Notes:** The graduation threshold is 20 items. The retention target is 15 (not exactly 15 — "most recent 15" means keep up to 15). This drill is a real maintenance action, not just a test. Run it when sections actually exceed the threshold.

---

## D-08: Cross-Agent Handoff

**Objective:** One seat produces memo; receiving seat consumes as focused recall.

**Setup:**
1. Have two seats available (e.g., Slate and Anvil, or Slate and a Builder)
2. Identify a real or simulated item that one seat needs to communicate to another

**Procedure:**
1. Sending seat writes a Cross-Agent Memo:
   - From/To/Re/Date
   - Finding/Severity (if applicable)
   - Claim (one sentence)
   - Evidence pointer
   - Requested action
2. Verify memo is ≤200 tokens
3. Receiving seat boots and loads the memo as Focused Recall
4. Receiving seat acts on the memo without importing Tier 2 content

**Pass Criteria:**
- [ ] Memo follows Cross-Agent Memo format
- [ ] Memo is ≤200 tokens
- [ ] Receiving seat loaded memo as Focused Recall (not pasted into capsule)
- [ ] Receiving seat understood the request and acted appropriately
- [ ] No Tier 2 content was imported by the receiving seat

**Evidence:** Cross-Agent Memo file + receiving seat's response showing comprehension and action.

**Notes:** This tests the communication protocol between seats. The memo format is intentionally constrained to force compression. If the sending seat can't fit the message in 200 tokens, they need to create a Finding record and reference it by ID instead.

---

## D-09: Lifecycle Integrity

**Objective:** "Resolved" counts match VERIFIED state.

**Setup:**
1. Open the active FINDINGS_REGISTER
2. Select 3 findings marked RESOLVED (or all if fewer than 3)

**Procedure:**
For each RESOLVED finding, verify:
1. A gate test exists that covers the finding
2. The gate test passes in current suite
3. A verdict was recorded (in WO Verdicts table or dispatch history)
4. Evidence pointer is intact and resolves

**Pass Criteria:**
- [ ] Finding 1: gate test exists + passes, verdict recorded, evidence pointer resolves
- [ ] Finding 2: gate test exists + passes, verdict recorded, evidence pointer resolves
- [ ] Finding 3: gate test exists + passes, verdict recorded, evidence pointer resolves
- [ ] No RESOLVED finding lacks mechanical verification (test + verdict)

**Evidence:** Findings register audit log (3 entries): Finding ID, gate test path, test result, verdict reference, evidence pointer status.

**Notes:** Implicitly exercised at every verdict. The lifecycle is OPEN → PATCHED → VERIFIED → RESOLVED. A finding that jumped from OPEN to RESOLVED without VERIFIED is a protocol violation. Legacy FIXED status (equivalent to PATCHED+VERIFIED inline) is acceptable for findings fixed outside the WO cycle.

---

## D-10: Compliance Audit

**Objective:** Random sample of recent sessions contains no Tier 2 in Tier 0.

**Setup:**
1. Gather 5 recent session boot transcripts (or handover notes that describe what was loaded)
2. If transcripts aren't available, review 5 recent session start interactions

**Procedure:**
For each session:
1. Check what was loaded into the agent's context at boot
2. Verify: only Charter + Capsule + ≤1 Focused Recall
3. Flag any instance of full diaries, full debriefs, full session narratives, or other Tier 2 content in context

**Pass Criteria:**
- [ ] Session 1: only Charter + Capsule + ≤1 recall loaded — PASS/FAIL
- [ ] Session 2: only Charter + Capsule + ≤1 recall loaded — PASS/FAIL
- [ ] Session 3: only Charter + Capsule + ≤1 recall loaded — PASS/FAIL
- [ ] Session 4: only Charter + Capsule + ≤1 recall loaded — PASS/FAIL
- [ ] Session 5: only Charter + Capsule + ≤1 recall loaded — PASS/FAIL
- [ ] 0 violations across all 5 samples

**Evidence:** Sample log with pass/fail per entry. For failures: note what Tier 2 content was found in Tier 0.

**Notes:** This is the integration drill — it verifies that the entire protocol is working as a system. If sessions routinely load Tier 2 content, the capsule compression isn't working and boot budgets are being violated. One failure in 5 samples is a yellow flag; two or more is a Finding.

---

## Drill Execution Log Template

Use this template to record monthly drill runs:

```markdown
# Drill Execution Log — [YYYY-MM-DD]

**Runner:** [callsign]
**Protocol version:** v1.1

| Drill | Result | Finding (if FAIL) | Evidence Path | Notes |
|-------|--------|-------------------|---------------|-------|
| D-01 | PASS/FAIL | | | |
| D-02 | PASS/FAIL | | | |
| D-03 | PASS/FAIL | | | |
| D-04 | PASS/FAIL | | | |
| D-05 | PASS/FAIL | | | |
| D-06 | PASS/FAIL | | | |
| D-07 | PASS/FAIL | | | |
| D-08 | PASS/FAIL | | | |
| D-09 | PASS/FAIL | | | |
| D-10 | PASS/FAIL | | | |

**Summary:** [X]/10 PASS. [Findings filed if any.]
```

---

## Implicit Exercise Reference

These drills are exercised during normal operations without dedicated runs:

| Drill | Exercised When | Evidence Captured Automatically |
|-------|---------------|-------------------------------|
| D-01 | Every session boot | Boot status report |
| D-03 | Every compaction event | Fresh capsule + register update |
| D-04 | Every compaction with context loss | Recovery mode notification |
| D-06 | Every new finding filed | Evidence pointer in finding record |
| D-09 | Every verdict delivered | Verdict record + test result |

Implicit exercises count toward the monthly cadence **only if evidence is captured**. No evidence = no credit.
