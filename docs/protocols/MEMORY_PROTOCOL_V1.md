# Memory Protocol v1.1 — 3-Tier Agent Memory Standard

**Effective:** 2026-02-22
**Origin:** Aegis proposal (context pressure architecture), Thunder-approved
**Scope:** All agents (Anvil, Slate, future agents)

**Revision history:**
- v1.0 (2026-02-22): Initial protocol. 3-tier stack, capsule format, retrieval, agent implementations.
- v1.0.1: Aegis rulings — kernel split, compaction checkpoint, bridge sequencing.
- v1.0.2: Anvil rulings — canonical root, findings domains, dual-control enforcement, PM State Register schema.
- v1.1 (2026-02-22): Canary audit. Charter/Capsule split, checkpoint artifact semantics, Tier 1 graduation, staleness gate, mirror sync trigger, seat verification gate, boot budget.

---

## Problem

Context pressure manifests as backpressure: slower cadence, shorter outputs, more self-correction, drift. The fix is not "give the agent more memory." It's **architect memory so the agent can reach it without loading it.**

Long-term memory lives outside the prompt. The prompt only carries a small working set plus pointers.

---

## The 3-Tier Stack

### Tier 0 — In-Prompt Working Set

What goes into the agent's active context at session start. Hard-capped. Composed of three distinct components:

**Charter** (invariant — fixed size, rarely changes):
- Agent identity, personality, role boundary
- Standing orders (audio cue, clock, process rules)
- Operational doctrine (Seven Wisdoms, execution protocol)
- Changes only through deliberate revision cycle. Not counted against capsule budget.

**Capsule** (variable state — hard-capped at 200-400 tokens):
- One Memory Capsule: priorities, delta, stop conditions, state register pointer
- Changes at every checkpoint. This is the compression target.

**Focused Recall** (optional — 100-250 tokens, max one):
- One retrieved item from Tier 1, only when directly relevant to current task

**Boot Budget:** Each seat declares a target token count for Charter + Capsule combined. Exceeding the boot budget is a measurable failure, not a judgment call. Stutter becomes a budget breach.

| Seat | Charter Budget | Capsule Budget | Total Boot Budget |
|------|---------------|----------------|-------------------|
| Slate | ~800 tokens | ≤400 tokens | ~1,200 tokens |
| Anvil | ~600 tokens | ≤400 tokens | ~1,000 tokens |

**Rule:** One capsule + one recall, max. If an agent needs more context, they must summarize into a new capsule or create a new finding record. This forces compression.

**If the agent starts stuttering, you are over budget. Cut memory, don't add it.**

### Tier 1 — Indexes and Registers

Small files for selection and lookup. Never pasted wholesale — skimmed for pointers.

**Standard files:**
- `STATE_DIGEST.md` — Current environment, known issues, last known green state
- `FINDINGS_REGISTER.md` — One line per finding: ID, severity, status, description, evidence pointer
- `SESSION_INDEX.jsonl` — One JSON line per session: session_id, utc_window, tags, finding_ids, capsule_path, evidence_paths

**Staleness metadata (v1.1):** STATE_DIGEST must carry:
- `last_capsule_id` — filename or ID of most recent capsule
- `last_capsule_timestamp` — UTC timestamp of most recent capsule
- If capsule is missing or timestamp is stale (>24h with no session activity), boot enters **RECOVERY MODE**: load state digest + findings register, generate fresh capsule immediately before any other work.

**Graduation policy (v1.1):** Tier 1 sections must stay skimmable. When a section exceeds 20 items:
- Archive oldest completed entries to Tier 2
- Keep only the most recent 15 items in Tier 1
- The archived entries remain accessible by pointer
- Applies to: WO verdict tables, dispatch lists, findings registers, session indexes
- **Rule:** If you have to scroll to find current state, the section is too long. Graduate.

### Tier 2 — Long-Term Storage

Full receipts. Never pasted wholesale. Accessed by search + pointers.

- Full diary entries / session narratives
- Full raw outputs (validator reports, model outputs)
- AB artifacts, failure logs, diffs
- Evidence packs (JSON frames, JSONL logs)

---

## Memory Capsule v1.1 Format

A capsule is a **Checkpoint Artifact**, not a session summary. Write a capsule at checkpoint triggers, not at arbitrary "session end" boundaries.

**Checkpoint triggers (write a capsule when):**
1. Before compaction (mandatory — "no compaction without a new capsule")
2. After a major deliverable (finding filed, verdict written, dispatch drafted, state register updated)
3. After N discrete work items (3 completed actions for conversational agents; per-scenario for Spark runs)
4. On stutter indicators (self-detected or operator-called)

This makes capsules consistent across Spark runs, observatory sprints, and PM sessions.

```markdown
# Memory Capsule — [Agent] [YYYY-MM-DD HHMMZ]

**Session:** [session_id]
**UTC window:** [start] — [end]
**Environment deltas:** [what changed since last capsule]

## Proven True Now
- [bullet: what is confirmed working]

## Still Broken
- [bullet: what is confirmed broken]

## Top Findings (max 3, by severity)
1. [FINDING-ID] [SEVERITY] — [one line]

## Next Hits (max 3)
1. [what to do next session]

## Evidence Pointers
- [path to evidence file]
```

**Hard cap:** 200-400 tokens. If it doesn't fit, compress harder or split a finding into its own file.

---

## Retrieval Protocol

When an agent needs past context (the two-step recall move):

1. **Select** — Search Tier 1 index by ID or tag. Return up to 3 candidates (finding IDs, session IDs, evidence pointers).
2. **Load** — Summarize ONE candidate into a 100-250 token Focused Recall block. Inject into Tier 0.

No more than one recall block per run.

---

## Boot Sequence (v1.1)

Every agent boot follows this sequence. No work begins until all steps pass.

### Step 1: Seat Verification Gate

Before reading any state, verify identity:
- Callsign in kernel header matches the agent being booted
- Role matches expected authority (PM, BS Buddy, Builder, etc.)
- If mismatch: **REFUSE TO PROCEED.** Report mismatch to operator.

This prevents a fresh agent from inheriting the wrong seat's kernel and operating under false identity.

### Step 2: Charter Load

Read the invariant charter section of the kernel. This establishes identity, personality, standing orders, operational doctrine. Fixed-size, rarely changes.

### Step 3: Capsule Load

Read the variable capsule section. This establishes current priorities, delta, stop conditions, and state register pointer.

**Staleness check:** If capsule timestamp is missing or stale (>24h with active work), enter RECOVERY MODE:
1. Read STATE_DIGEST + FINDINGS_REGISTER from Tier 1
2. Write a fresh capsule from current Tier 1 state
3. Resume from fresh capsule

### Step 4: Mirror Sync (agents with canonical roots outside repo)

For Anvil (canonical root on D:\anvil_research\):
- Check `MIRROR_DIRTY.flag` on canonical root
- If present: sync Tier 1 indexes from canonical to repo mirror, then clear flag
- If absent: mirror is current, proceed

For Slate: not applicable (canonical root is the repo).

### Step 5: Focused Recall (optional)

If the current task requires past context, perform the two-step recall:
1. Skim Tier 1 index for relevant item
2. Load ONE item as Focused Recall (≤250 tokens)

### Step 6: Status Report

Agent reports: stoplight, last capsule timestamp, boot budget usage, next action.

---

## Agent-Specific Implementations

### Anvil

**Canonical root:** `D:\anvil_research\` — the observatory. This is where all Tier 1 indexes, Tier 2 receipts, capsules, sessions, evidence, CLAIM_LEDGER, CONFOUNDS, and FOUNDATION-LOCK infrastructure live. Anvil writes here.

**Repo mirror:** `F:\DnD-3.5\anvil_diary\` — read-only export. Slate maintains this as a shared-visibility copy of Anvil's Tier 1 indexes (STATE_DIGEST, FINDINGS_REGISTER, SESSION_INDEX) and latest capsule. Anvil does NOT write to the repo mirror directly. Slate syncs from D: when verdicting or during handoff.

**Marker files:**
- `D:\anvil_research\CANONICAL_ROOT.txt` — "This is the canonical Anvil diary root."
- `F:\DnD-3.5\anvil_diary\MIRROR_OF.txt` — "Mirror of D:\anvil_research\. Do not write directly. Slate syncs from canonical root."

**Rule: One brain, one root.** If Anvil and the repo mirror diverge, D: is truth.

```
D:\anvil_research\              (CANONICAL)
  capsules/          CAPSULE_YYYY-MM-DD_HHMMZ.md
  sessions/          SESSION_YYYY-MM-DD_HHMMZ.md
  evidence/          *.json, *.jsonl, *.png
  anomalies/         Observatory anomaly records
  ANVIL_REHYDRATION_KERNEL.md
  ANVIL_OBSERVATION_LOG.md
  CLAIM_LEDGER.md
  CONFOUNDS.md
  INDEX.md
  STATE_DIGEST.md    (Anvil maintains)
  FINDINGS_REGISTER_SPARK.md
  FINDINGS_REGISTER_OBS.md
  SESSION_INDEX.jsonl

F:\DnD-3.5\anvil_diary\        (MIRROR — read-only export)
  capsules/          Latest capsule only
  indexes/           SESSION_INDEX.jsonl
  STATE_DIGEST.md
  FINDINGS_REGISTER.md  (SPARK domain only — repo-relevant)
  MIRROR_OF.txt
```

**Findings register domains (Aegis ruling, 2026-02-22):**
- `FINDINGS_REGISTER_SPARK.md` — Code/engine findings. IDs: `FINDING-SPARK-*`, `FINDING-HOOLIGAN-*`, `FINDING-EXPLORE-*`, `FINDING-WAYPOINT-*`. Lives on D: canonical + F: repo mirror.
- `FINDINGS_REGISTER_OBS.md` — Observatory/FOUNDATION-LOCK research findings. IDs: `FINDING-OBS-*`. Lives on D: only. Not mirrored to repo (research artifacts, not code artifacts).

**Standing orders:**
1. After every Spark cage session, produce a capsule in `D:\anvil_research\capsules\`
2. Write full session diary in `D:\anvil_research\sessions\` (narrative + receipts layer)
3. Update Spark findings register — one line per finding, append-only
4. Append one line to `D:\anvil_research\SESSION_INDEX.jsonl`
5. Update `D:\anvil_research\STATE_DIGEST.md` with current environment state
6. At session start, load ONLY: latest capsule + one focused recall. Never paste full sessions.
7. Observatory findings go to `FINDINGS_REGISTER_OBS.md` — separate domain, separate register.
8. **Mirror sync trigger (v1.1):** After updating any Tier 1 file on D:, write `MIRROR_DIRTY.flag` to `D:\anvil_research\`. Slate checks this flag at boot and during verdicting/handoff; clears after sync.

### Slate

Slate's memory is already structured via `pm_inbox/`. No new folder tree.

**Kernel split (Aegis ruling, 2026-02-22):** The rehydration kernel cannot be both a working prompt payload and the canonical PM database. Carrying lists in Tier 0 causes stutter. Carry counts + stoplight + pointers instead. Let Tier 1 be the database.

**Tier 0 (Charter):** Invariant section of `pm_inbox/REHYDRATION_KERNEL_LATEST.md`. Contains:
- Identity, personality, role boundary
- Standing orders (audio cue, clock protocol)
- Seven Wisdoms, Four Fundamentals, operational doctrine
- PM execution boundary, dispatch chain, communication style
- Memory protocol summary
- Handover protocol
- Fixed-size. Changes only through deliberate revision. ~800 tokens.

**Tier 0 (Capsule):** Variable section of `pm_inbox/REHYDRATION_KERNEL_LATEST.md`. Contains:
- Current priority stack (top 3)
- Stop conditions (what would invalidate the plan)
- Delta since last capsule
- Pointer + timestamp to PM State Register
- Hard-capped at ≤400 tokens.

**Tier 0 (Focused Recall):** Briefing "Current Focus" section — one focused recall item for rehydration.

**Tier 1 (PM State Register):** `pm_inbox/PM_BRIEFING_CURRENT.md` + `pm_inbox/BURST_INTAKE_QUEUE.md` — canonical project state. Contains:
- Gate counts (compact stoplight, not full per-gate breakdowns)
- Operator Action Queue (max 3 decision-grade items for Thunder)
- Dispatch list (active and completed)
- Open findings inventory
- Build order position
- Doctrine adoption status

**Tier 1 split (v1.1):** The old "Requires Operator Action" section served two purposes — Thunder's action queue AND Slate's focused recall. Split into:
- **Operator Action Queue** — Decision-grade items for Thunder. Max 3. "What does Thunder need to decide?"
- **Current Focus** — Slate's focused recall. Max ~200 tokens. "What am I working on right now?"

**Tier 2 (Archive):** `pm_inbox/reviewed/` — organized by WO cycle.

**Session index:** Briefing "WO Verdicts" table + handover notes.

**Standing orders:**
1. Kernel = Charter (invariant) + Capsule (variable). Charter ~800 tok. Capsule ≤400 tok. Total boot ≤1,200 tok.
2. Briefing is Tier 1 register. Canonical. This is where lists live.
3. Handover notes at session end serve as session diary.
4. No new folder structure needed.
5. Graduate Tier 1 sections when they exceed 20 items.

---

## Compaction Checkpoint (mandatory)

When approaching context pressure, agents perform a **Checkpoint Capsule Refresh** before compaction:

1. Write a fresh capsule to Tier 0 (captures current session state)
2. Update Tier 1 registers (State Register / PM Briefing)
3. Record pointers and hashes
4. Then compaction proceeds

**Rule: No compaction without a new capsule.** Rereading the briefing after compaction works but is manual retrieval, not continuity. The checkpoint makes compaction a controlled boundary instead of a memory cliff.

**Trigger:** If the agent begins stuttering OR is within ~10% of context limit, checkpoint immediately.

### Enforcement (Aegis ruling, 2026-02-22)

Dual-control. Neither side alone is sufficient.

**Operator (Thunder):**
- Calls "Checkpoint" when context pressure is known or before deliberate compaction
- Monitors for stutter indicators from outside (shorter responses, drift, self-repair)
- Can mandate checkpoint at any time as standing order

**Agent (self-directed):**
- Self-checkpoints on stutter indicators (see Stutter Detection below)
- Self-checkpoints on cadence: every ~30 minutes of active work OR every N scenario runs (Anvil)
- If compaction hits unexpectedly (context overflow without warning), first action after compaction is:
  1. Capsule Refresh — write a new capsule from whatever state survived
  2. State Register sync — update Tier 1 from memory
  3. Resume from capsule, not from vague recall

**Standing order:** If an agent cannot remember whether it checkpointed, it didn't. Checkpoint again.

---

## Stutter Detection

Context pressure shows up as measurable backpressure:

- Response latency increasing over session
- Output becoming shorter and less specific
- More hedging or self-repair mid-sentence
- "I'll fix it now" impulses without clean evidence linking
- Diary write rate decelerating

**Controls:**
- Keep Tier 0 fixed-size
- One scenario per run (Anvil)
- Log first, patch after
- If blocked, fix only the block, then resume logging
- If stuttering starts, cut memory — don't add it

---

## PM State Register Schema (Aegis ruling, 2026-02-22)

The kernel split requires a defined boundary between Tier 0 (capsule) and Tier 1 (register). This schema makes the split mechanical and testable.

### Slate Tier 0 — Capsule (`REHYDRATION_KERNEL_LATEST.md`)

**Hard cap: 400 tokens.** This is the only file pasted into the prompt at session start.

```
# Slate Rehydration Kernel

**Identity:** [role boundary — 1 sentence]
**Session:** [session_id or date]
**Delta:** [what changed since last capsule — 1-2 sentences]

## Priority Stack (top 3)
1. [highest priority task or decision]
2. [second]
3. [third]

## Stop Conditions
- [what would invalidate the current plan]

## State Register Pointer
- File: pm_inbox/PM_BRIEFING_CURRENT.md
- Updated: [ISO timestamp]
```

**Hash requirement (v1.1):** Dropped from capsule. Timestamp is sufficient for drift detection. If automated hashing becomes available, add as optional metadata in STATE_DIGEST, not in the capsule itself.

**What does NOT go in the capsule:** Gate counts, dispatch lists, WO verdict histories, full findings inventories, build order details. Those are Tier 1.

### Slate Tier 1 — PM State Register (`PM_BRIEFING_CURRENT.md`)

This is the canonical PM database. Lists live here. The capsule points here.

**Required sections:**
- **Stoplight** — Gate counts (compact: `Gate A: 22/22` not full test names), suite totals, status color
- **Requires Operator Action** — Current blocking items (focused recall source)
- **Dispatches** — Active and completed WOs with verdict, commit hash
- **Build order** — Current position in build sequence
- **Open findings** — All unresolved findings with severity
- **Doctrine adoption** — Which specs are frozen, which are pending

**Compression rule:** The briefing is allowed to be long (it's Tier 1, not Tier 0). But each section should be scannable — one line per item, not paragraph descriptions. The full narrative goes in Tier 2 (handover notes, debriefs).

---

## Vocabulary (v1.1 — locked terms)

Overloaded terms cause growth pressure. These are now fixed:

| Term | Definition | Scope |
|------|-----------|-------|
| **Charter** | Invariant identity + process rules | Tier 0, rarely edited |
| **Capsule** | Bounded variable state snapshot | Tier 0, frequently updated at checkpoints |
| **Register** | Canonical inventories and indexes | Tier 1, skimmable |
| **Archive** | Full receipts and narratives | Tier 2, accessed by pointer only |
| **Kernel** | Charter + Capsule combined (the boot file) | Tier 0, the file that loads at session start |
| **Focused Recall** | One retrieved item from Tier 1 | Tier 0, optional, max one per run |

**Rule:** If someone says "put it in the kernel," ask: is it Charter (invariant) or Capsule (state)? If neither, it belongs in a Register or Archive.

---

## Authority Table (v1.1)

Who owns what. Only the declared owner writes to an artifact. Others contribute via Cross-Agent Memo.

| Artifact | Owner | Location | Mirror |
|----------|-------|----------|--------|
| Slate kernel (charter + capsule) | Slate | `pm_inbox/REHYDRATION_KERNEL_LATEST.md` | — |
| PM State Register (briefing) | Slate | `pm_inbox/PM_BRIEFING_CURRENT.md` | — |
| BURST Intake Queue | Slate | `pm_inbox/BURST_INTAKE_QUEUE.md` | — |
| Anvil kernel | Anvil | `D:\anvil_research\ANVIL_REHYDRATION_KERNEL.md` | — |
| Anvil capsules | Anvil | `D:\anvil_research\capsules\` | Latest → `F:\DnD-3.5\anvil_diary\capsules\` |
| Anvil STATE_DIGEST | Anvil | `D:\anvil_research\STATE_DIGEST.md` | → `F:\DnD-3.5\anvil_diary\STATE_DIGEST.md` |
| Anvil FINDINGS_REGISTER_SPARK | Anvil (Spark), Slate (verdicts) | `D:\anvil_research\` | → `F:\DnD-3.5\anvil_diary\FINDINGS_REGISTER.md` |
| Anvil FINDINGS_REGISTER_OBS | Anvil | `D:\anvil_research\` | Not mirrored |
| Anvil SESSION_INDEX | Anvil | `D:\anvil_research\SESSION_INDEX.jsonl` | → `F:\DnD-3.5\anvil_diary\indexes\` |
| Repo mirror | Slate (sync only) | `F:\DnD-3.5\anvil_diary\` | — |
| Dispatches + debriefs | Slate (creates), Builder (writes debrief) | `pm_inbox/` | → `pm_inbox/reviewed/` on archive |
| Protocol docs | Slate + Aegis (proposals via memo) | `docs/protocols/` | — |

**Rule:** If you are not the declared owner, do not edit directly. File a Cross-Agent Memo.

---

## Finding Lifecycle States (v1.1)

Standardized states so counts are reliable across seats.

```
OPEN → PATCHED → VERIFIED → RESOLVED
```

| State | Meaning | Who transitions |
|-------|---------|----------------|
| **OPEN** | Finding surfaced. No fix exists. | Discoverer (any seat) |
| **PATCHED** | Code change committed that addresses the finding. | Builder (at WO delivery) |
| **VERIFIED** | Gate test added AND passes. Fix proven mechanically. | PM (at verdict) |
| **RESOLVED** | Verdict recorded. Finding archived. No longer tracked in active register. | PM (post-verdict) |

**Also valid:** `FIXED` (legacy — equivalent to PATCHED+VERIFIED for findings fixed inline, not via WO).

**Dispatch lifecycle:**

```
DRAFT → DISPATCHED → IN-PROGRESS → SUBMITTED → ACCEPTED/REJECTED → ARCHIVED
```

---

## Evidence Pointer Stability (v1.1)

Pointers are the protocol's addressing system. If they rot, trust collapses.

**Rules:**
1. Every evidence pack lives in a **session-ID directory** and never moves after creation.
2. Findings reference evidence by `(session_id, relative_path)` — not absolute paths that break on reorganization.
3. If an evidence file must move (e.g., archive reorganization), leave a **redirect stub** at the old location: a small file containing the new path and the move date.
4. Pointer audits: when graduating Tier 1 entries to Tier 2, verify all evidence pointers still resolve.

**Naming convention:** `reviewed/archive_[phase]/[SESSION_ID]/[artifact]`

---

## Cross-Agent Memo Format (v1.1)

When one seat needs to surface something to another seat, they produce a memo — not a direct edit.

```markdown
# Cross-Agent Memo

**From:** [callsign]
**To:** [callsign]
**Re:** [one-line subject]
**Date:** [ISO timestamp]

**Finding/Item:** [ID if applicable]
**Severity:** [if applicable]
**Claim:** [one sentence]
**Evidence:** [pointer to evidence file]
**Requested action:** [what the receiving seat should do]
```

**Hard cap:** ≤200 tokens. Treated as a Focused Recall candidate by the receiving seat.

**Concurrency rule (v1.1):** Only the declared owner writes to an artifact. If another seat has input, they produce a Cross-Agent Memo. The owner integrates it. This eliminates merge ambiguity.

---

## Recovery Mode (v1.1)

When boot goes wrong — wrong seat, stale capsule, missing register — the agent follows a defined procedure instead of improvising.

**Entry conditions:**
- Seat verification fails (callsign mismatch)
- Capsule missing or stale (>24h with active work)
- State register missing or unreadable
- Post-compaction with no pre-compaction capsule

**Recovery steps:**
1. **Seat verification** — confirm callsign and role. If mismatch, halt.
2. **Charter load only** — read invariant identity and process rules. Do not load state.
3. **Tier 1 scan** — read STATE_DIGEST + FINDINGS_REGISTER (not full briefing)
4. **Fresh capsule** — write a new capsule from Tier 1 state
5. **Operator notification** — report: "Recovery mode. Fresh capsule written from Tier 1. State may be incomplete."
6. **Proceed** — resume from fresh capsule with operator awareness

**Rule:** An agent in recovery mode does NOT perform substantive work until the capsule is written and the operator is notified.

---

## Compliance Gates (v1.1)

Protocol compliance is habit, not heroism. These are manual checks until automation exists.

**Boot compliance checklist:**
- [ ] Kernel file ≤ boot budget (Charter ~800 tok + Capsule ≤400 tok)
- [ ] Tier 0 contains only: Charter + Capsule + ≤1 Focused Recall
- [ ] No Tier 2 content pasted into Tier 0 or Tier 1
- [ ] Capsule timestamp is current (within 24h of last active session)
- [ ] Every open finding has an evidence pointer that resolves

**Checkpoint compliance checklist:**
- [ ] Capsule written before compaction
- [ ] Tier 1 registers updated
- [ ] Capsule ≤400 tokens of variable state
- [ ] No lists migrated from Tier 1 into capsule

**Graduation compliance (Tier 1 → Tier 2):**
- [ ] Section being graduated exceeds 20 items
- [ ] Oldest items archived, most recent 15 retained
- [ ] Evidence pointers verified before archive

---

## Redaction Rule (v1.1)

Evidence packs and diaries must never contain secrets.

**Prohibited content in any tier:**
- API keys, tokens, credentials, passwords
- Personal identifying information beyond callsigns
- OAuth refresh tokens, session cookies

**If discovered:**
1. Rotate the compromised credential immediately
2. Scrub the content from the artifact
3. Record only: incident ID, date, resolution pointer
4. Do not attempt to preserve "for the record" — the record is that it happened and was fixed

---

## Freshness Contract (v1.1)

Tier 1 retrieval must not silently load stale state.

**STATE_DIGEST must include:**
- `last_updated` — ISO timestamp
- `last_capsule_id` — filename of most recent capsule
- `last_capsule_timestamp` — UTC of most recent capsule

**Boot freshness check:**
- If `last_updated` is >24h old AND there has been active work since: enter Recovery Mode
- If `last_updated` is >24h old AND there has been NO active work: proceed normally (stale but expected)
- Operator can override with explicit "proceed stale" instruction

---

## Future Extensions (out of scope)

1. **Capsule injection into PromptPack** — Add optional capsule field to `PromptPackBuilder.build()`, gets priority slot in MEMORY channel. CODE WO.
2. **Bridge harness Mode A** — Replay-driven prompt compilation tool. Queue behind RV-007. Becomes correctness-enabling once validators are hardened and need real engine truth frames. CODE WO.
3. **Bridge harness Mode B** — Live session bridge. Queue behind Mode A. Needed for "Thunder plays / Spark narrates" continuous operation.
4. **Aegis memory** — If Aegis adopts this protocol, same pattern: `aegis_diary/` with same structure.
