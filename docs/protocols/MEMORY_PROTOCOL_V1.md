# Memory Protocol v1 — 3-Tier Agent Memory Standard

**Effective:** 2026-02-22
**Origin:** Aegis proposal (context pressure architecture), Thunder-approved
**Scope:** All agents (Anvil, Slate, future agents)

---

## Problem

Context pressure manifests as backpressure: slower cadence, shorter outputs, more self-correction, drift. The fix is not "give the agent more memory." It's **architect memory so the agent can reach it without loading it.**

Long-term memory lives outside the prompt. The prompt only carries a small working set plus pointers.

---

## The 3-Tier Stack

### Tier 0 — In-Prompt Working Set

What goes into the agent's active context at session start. Hard-capped.

**Contents (maximum):**
- Agent charter header (short)
- One Memory Capsule (200-400 tokens)
- One Focused Recall item (100-250 tokens) — only when directly relevant

**Rule:** One capsule + one recall, max. If an agent needs more context, they must summarize into a new capsule or create a new finding record. This forces compression.

**If the agent starts stuttering, you are over budget. Cut memory, don't add it.**

### Tier 1 — Indexes and Registers

Small files for selection and lookup. Never pasted wholesale — skimmed for pointers.

**Standard files:**
- `STATE_DIGEST.md` — Current environment, known issues, last known green state
- `FINDINGS_REGISTER.md` — One line per finding: ID, severity, status, description, evidence pointer
- `SESSION_INDEX.jsonl` — One JSON line per session: session_id, utc_window, tags, finding_ids, capsule_path, evidence_paths

### Tier 2 — Long-Term Storage

Full receipts. Never pasted wholesale. Accessed by search + pointers.

- Full diary entries / session narratives
- Full raw outputs (validator reports, model outputs)
- AB artifacts, failure logs, diffs
- Evidence packs (JSON frames, JSONL logs)

---

## Memory Capsule v1 Format

Produced after every session. Safe to paste into next session's Tier 0.

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

### Slate

Slate's memory is already structured via `pm_inbox/`. No new folder tree.

**Kernel split (Aegis ruling, 2026-02-22):** The rehydration kernel cannot be both a working prompt payload and the canonical PM database. Carrying lists in Tier 0 causes stutter. Carry counts + stoplight + pointers instead. Let Tier 1 be the database.

**Tier 0 (Capsule):** `pm_inbox/REHYDRATION_KERNEL_LATEST.md` — under 400 tokens. Contains:
- Identity and role boundary
- Current priority stack (top 3)
- Stop conditions (what would invalidate the plan)
- Delta since last capsule
- Pointer + hash + timestamp to PM State Register

**Tier 0 (Focused Recall):** Briefing "Requires Operator Action" section — one section, kept tight.

**Tier 1 (PM State Register):** `pm_inbox/PM_BRIEFING_CURRENT.md` + `pm_inbox/BURST_INTAKE_QUEUE.md` — canonical project state. Contains:
- Gate counts (compact stoplight, not full per-gate breakdowns)
- Dispatch list (active and completed)
- Open findings inventory
- Build order position
- Doctrine adoption status

**Tier 2 (Archive):** `pm_inbox/reviewed/` — organized by WO cycle.

**Session index:** Briefing "WO Verdicts" table + handover notes.

**Standing orders:**
1. Kernel is capsule. Under 400 tokens. No lists — counts + stoplight + pointers.
2. Briefing is Tier 1 register. Canonical. This is where lists live.
3. Handover notes at session end serve as session diary.
4. No new folder structure needed.

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
- Hash: [first 8 chars of SHA-256]
- Updated: [ISO timestamp]
```

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

## Future Extensions (out of scope)

1. **Capsule injection into PromptPack** — Add optional capsule field to `PromptPackBuilder.build()`, gets priority slot in MEMORY channel. CODE WO.
2. **Bridge harness Mode A** — Replay-driven prompt compilation tool. Queue behind RV-007. Becomes correctness-enabling once validators are hardened and need real engine truth frames. CODE WO.
3. **Bridge harness Mode B** — Live session bridge. Queue behind Mode A. Needed for "Thunder plays / Spark narrates" continuous operation.
4. **Aegis memory** — If Aegis adopts this protocol, same pattern: `aegis_diary/` with same structure.
5. **Aegis memory** — If Aegis adopts this protocol, same pattern: `aegis_diary/` with same structure.
