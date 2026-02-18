<!--
AGENT ONBOARDING CHECKLIST — MANDATORY READING ORDER & VERIFICATION STEPS

This file tells new agents EXACTLY what to read, in what order, and what to verify
before writing a single line of code. It exists because the project has 9+ root-level
.md files and agents waste context reading them in the wrong order or skipping critical ones.

LAST UPDATED: 2026-02-14 — Wave 1-3 WOs integrated. 5,144 tests collected. VERIFICATION_GUIDELINES.md added. pm_inbox hygiene enforcement added.
-->

# Agent Onboarding Checklist

**Read this file FIRST. Follow it step by step. Do not skip ahead.**

---

## Step 0: Read the Project Compass

**Before anything else**, read `PROJECT_COMPASS.md`. It is the rehydration hub — a single document covering the project thesis, architecture, what's real vs paper, the roadmap, conventions, and pointers to every deep dive. If you only read one file, read that one.

---

## Step 1: Read the Governance Documents (IN THIS ORDER)

After the Compass, read these for operational detail. The order matters.

| Order | File | Purpose | Critical Because |
|-------|------|---------|-----------------|
| 1 | `PROJECT_COMPASS.md` | Rehydration hub — thesis, architecture, status, conventions, directory map | Single entry point. Covers everything at summary level. |
| 2 | `PROJECT_STATE_DIGEST.md` | Detailed operational state — locked systems, WO history, capability gates | Operational detail beyond what Compass covers |
| 3 | `AGENT_DEVELOPMENT_GUIDELINES.md` | Coding standards, pitfall avoidance | Contains hard-won bug fixes — ignoring this causes regressions |
| 4 | `AGENT_COMMUNICATION_PROTOCOL.md` | How to flag concerns, gates, scope creep | Violations cause code reverts |
| 5 | `KNOWN_TECH_DEBT.md` | Things that look broken but are intentionally deferred | Prevents you from wasting work "fixing" deferred items |
| 6 | `VERIFICATION_GUIDELINES.md` | Verification pitfalls, verdict decision tree, error taxonomy | Required for verification/re-verification work orders. Optional for pure coding WOs. |

**Do NOT read** superseded action plans — use `docs/planning/archived/REVISED_PROGRAM_SEQUENCING_2026_02_12.md` for the current roadmap.

---

## Step 1B: Read the Field Manual

Read `BUILDER_FIELD_MANUAL.md`. It contains operational tradecraft — codebase gotchas, test suite quirks, and environment friction points that cost previous builders debugging cycles. 10 entries, under 200 lines. This is not rules or architecture — it's "things you'll hit if nobody tells you."

---

## Step 2: Verify the Project Compiles and Tests Pass

Before writing any code, run:

```bash
python -m pytest tests/ -v --tb=short
```

**Expected result:**
- 5,100+ tests passing
- 7 failures (Chatterbox TTS — external dependency, expected)
- 16 skipped (hardware-gated)
- Runtime ~100 seconds for full suite (use `pytest -m "not slow"` for ~30s fast suite)

If this doesn't pass, STOP. Do not proceed. Report the failure.

---

## Step 2.5: Run Builder Preflight Canaries

After tests pass, run the preflight to validate GPU pipelines. Full spec: `pm_inbox/MEMO_BUILDER_PREFLIGHT_CANARY.md`.

### Pipeline Check (BLOCKING)

```bash
python scripts/preflight_canary.py
```

This runs fixed image + voice canaries twice each and prints PASS/FAIL. If either fails, STOP. Report the failure.

### Skill Artifacts (After Canaries Pass)

1. **Image:** Read prompt rules in `pm_inbox/MEMO_IMAGE_GEN_WALKTHROUGH.md`. Generate one portrait of any subject. No other guidance. Save to `image_cache/`.
2. **Voice:** Read persona registry in `aidm/immersion/chatterbox_tts_adapter.py` (lines 45-119). Choose any non-reserved persona. Write 1-2 sentences for any character. Generate via `speak.py`.

**Reserved profiles (off-limits):** `npc_elderly` (Mrs. Slate), Arbor signal reference, `builder_signal` (Builder Herald).

Log all results in `pm_inbox/PREFLIGHT_CANARY_LOG.md`.

---

## Step 3: Verify Your Understanding

Before writing code, confirm you understand these five rules. If any are unclear, re-read the relevant guideline section.

### Rule 1: Entity Fields Use Constants
```python
# CORRECT
from aidm.schemas.entity_fields import EF
hp = entity.get(EF.HP_CURRENT, 0)

# WRONG — bare string literal
hp = entity.get("hp_current", 0)
```
See: `AGENT_DEVELOPMENT_GUIDELINES.md` Section 1

### Rule 2: Two Attack Intents Exist — Use the Right One
- `DeclaredAttackIntent` (in `aidm.schemas.intents`) = voice/interaction layer
- `AttackIntent` (in `aidm.schemas.attack`) = combat resolution layer
- NEVER import `AttackIntent` from `aidm.schemas.intents` — it doesn't exist there

See: `AGENT_DEVELOPMENT_GUIDELINES.md` Section 2

### Rule 3: No Sets, No Floats, Sorted Keys
```python
# WRONG — set crashes json.dumps in state_hash()
"actors": set(ids)

# CORRECT
"actors": list(ids)

# ALL json.dumps calls MUST use sort_keys=True
json.dumps(data, sort_keys=True)
```
See: `AGENT_DEVELOPMENT_GUIDELINES.md` Section 4

### Rule 4: This is D&D 3.5e, NOT 5e
- No advantage/disadvantage (use numeric modifiers)
- No short rest/long rest (use "overnight"/"full_day")
- Damage type is "electricity" not "electric"
- 0-level spells use spell slots (not at-will cantrips)

See: `AGENT_DEVELOPMENT_GUIDELINES.md` Section 7

### Rule 5: Resolvers Return Events, Never Mutate State
```python
# CORRECT — resolver returns events only
def resolve_attack(world_state, intent) -> List[Dict]:
    events = []
    events.append({"event_type": "attack_roll", ...})
    return events  # NO state mutation

# WRONG — mutating world_state inside resolver
def resolve_attack(world_state, intent):
    world_state.entities["fighter"]["hp_current"] -= 10  # FORBIDDEN
```
See: `AGENT_DEVELOPMENT_GUIDELINES.md` Section 6

---

## Step 4: Quick-Reference "DO NOT" List

These are the five most common mistakes agents make on this project. Memorize them.

1. **DO NOT** use bare string literals for entity field access — use `EF.*` constants
2. **DO NOT** store `set()` objects in WorldState or active_combat dicts
3. **DO NOT** introduce 5e terminology (advantage, short rest, electric damage, cantrips at will)
4. **DO NOT** mutate WorldState inside resolver functions — return events only
5. **DO NOT** "fix" items listed in `KNOWN_TECH_DEBT.md` unless explicitly asked — they are intentionally deferred
6. **DO NOT** close a session after WO completion without writing a debrief — knowledge dies with your context window (Section 15.5). This applies even if the WO says "read-only" or "do not modify files" — the debrief is about the work, not part of it.
7. **DO NOT** add a file to `pm_inbox/` without also updating `pm_inbox/PM_BRIEFING_CURRENT.md` — the PM won't see it otherwise
8. **DO NOT** write a completion report or debrief without first running `git add` + `git commit` (Rule 15a). Code that exists only in the working tree is unverifiable and at risk of loss. If the session is ending and commit is impossible, write `UNCOMMITTED` in the debrief header and list all affected files.

---

## Step 5: Understand Where Things Live

| Question | Answer |
|----------|--------|
| "Where do I add a new schema/dataclass?" | `aidm/schemas/{concept}.py` |
| "Where do I add resolver logic?" | `aidm/core/{concept}_resolver.py` |
| "Where do I add validation rules?" | `aidm/rules/{concept}_checker.py` |
| "Where do I add tests?" | `tests/test_{module}.py` |
| "Where do I document design decisions?" | `docs/CP{XX}_{NAME}_DECISIONS.md` |
| "Where do I add a new entity field?" | `aidm/schemas/entity_fields.py` FIRST, then use it |
| "What RNG stream do I use?" | See `AGENT_DEVELOPMENT_GUIDELINES.md` Section 5 |
| "What capability gates are open?" | See `PROJECT_STATE_DIGEST.md` → Capability Gate Status |
| "What spells can I implement?" | Only Tier 1. See `docs/CP-18A-SPELL-TIER-MANIFEST.md` |
| "Where do coordination patterns live?" | `methodology/` — domain-independent extract, also published externally |
| "I discovered a new coordination pattern" | Add to `methodology/patterns/`, update `methodology/README.md`, note in debrief |

---

## Step 6: CP Workflow

Every completion packet follows this process:

1. Define scope (what's in, what's out)
2. Write schemas first (data contracts before algorithms)
3. Write tests second (at least Tier-1 stubs before implementation)
4. Implement (fill in logic to make tests pass)
5. Run full test suite (`python -m pytest tests/ -v --tb=short`)
6. Verify 5,100+ tests still pass
7. **`git add` + `git commit` all code changes.** This is mandatory — Rule 15a. Code that only exists in the working tree is invisible to the PM and at risk of being lost. Use a descriptive message: `feat: WO-XXX — [short description]`. Include the commit hash in your debrief.
8. Update `PROJECT_STATE_DIGEST.md` (test counts, module inventory, CP history)
9. Update `AGENT_DEVELOPMENT_GUIDELINES.md` if new patterns or pitfalls were discovered
10. Write post-completion debrief (Section 15.5 — three-pass: full dump, PM summary, then operational retrospective). Include the commit hash from step 7 in the header.
11. Update `pm_inbox/PM_BRIEFING_CURRENT.md` with entries for any new pm_inbox files
12. Use `CP_TEMPLATE.md` for the standard CP decisions document format

---

## Step 7: Dispatch Authority & When in Doubt

**When the operator hands you a WO dispatch, execute it immediately.** The dispatch is your authorization. Do not ask "shall I proceed?" or "want me to run this?" — the operator transferring the WO is the go signal. Read the dispatch, understand the scope, and start working.

| Situation | Action |
|-----------|--------|
| You received a WO dispatch from the operator | **Execute immediately.** The dispatch is your authorization. |
| Unsure if feature crosses a capability gate | **STOP.** Flag as GATE VIOLATION per communication protocol |
| Multiple valid implementation approaches within a WO | Pick the simplest approach that satisfies the spec. Note your choice in the debrief. Only escalate if the WO spec is ambiguous or contradictory. |
| Something looks like a bug in existing code | Check `KNOWN_TECH_DEBT.md` first — it may be intentional |
| Need a new entity field | Add to `entity_fields.py` FIRST, then use the constant everywhere |
| Need a new RNG stream | Document it, add to guidelines, use a descriptive name |
| Test suite takes > 2 seconds | Flag as PERFORMANCE CONCERN per communication protocol |
| Not sure which GridPoint type to use | See `AGENT_DEVELOPMENT_GUIDELINES.md` Section 3 |

---

## Step 8: PM Review Inbox

When you complete a deliverable that needs PM (Slate) review — work order output, design doc, spec, audit report, or any artifact the PM should evaluate — write it to `pm_inbox/` as a markdown file.

### FILE ROUTING (MANDATORY)

| Destination | Who writes there | Purpose |
|-------------|-----------------|---------|
| `pm_inbox/` | **Agents** | New deliverables awaiting PM review |
| `pm_inbox/reviewed/` | **Agents** (after PM verdict) | Archived documents — PM sets lifecycle to ARCHIVE, builder moves the file |
| `pm_inbox/aegis_rehydration/` | **PM/Thunder ONLY** | PM context files |

**The PM is a decision oracle, not an action taker.** The PM reads memos, writes verdicts (lifecycle changes, decision annotations), and nothing else. All resulting actions — file moves, briefing updates, doc changes — are executed by builders. The PM's context window is the most expensive resource in the system; every action the PM executes is judgment capacity lost.

**`pm_inbox/reviewed/`:** Builders move files here after the PM sets their lifecycle to ARCHIVE. Do not move files there on your own judgment — wait for the PM's verdict edit.

**DO NOT write deliverables to `pm_inbox/aegis_rehydration/`.** That folder contains PM system context. The only exception is **syncing canonical project files** that have rehydration copies (e.g., `AGENT_DEVELOPMENT_GUIDELINES.md`, `PROJECT_STATE_DIGEST.md`, `KNOWN_TECH_DEBT.md`) — those files have headers that explicitly say to sync the rehydration copy after editing.

**File type prefixes (ENFORCED by `tests/test_pm_inbox_hygiene.py`):**

| Prefix | Purpose |
|--------|---------|
| `WO-` | Work order dispatch |
| `WO_SET` | Batch of related WOs |
| `MEMO_` / `MEMO-` | Session findings/summary |
| `DEBRIEF_` / `DEBRIEF-` | Full context dump (Section 15.5) |
| `HANDOFF_` / `HANDOFF-` | Cross-session context transfer |
| `PO_REVIEW` | Product owner review doc |
| `BURST_` | Research intake queue |
| `FIX_WO` | Fix work order dispatch packet |

**Required header block** (first lines of every file):
```
# [Type]: [Short Title]
**From:** [Agent identifier]
**Date:** [YYYY-MM-DD]
**Status:** [Complete | Partial | Blocked | READY | PROPOSAL]
**Lifecycle:** NEW
```

The `**Lifecycle:**` field is **mandatory** (enforced by test). Valid values: `NEW`, `TRIAGED`, `ACTIONED`, `ARCHIVE`. Always set to `NEW` when you create the file.

**After creating a file in pm_inbox, you MUST:**
1. Add a one-line entry to `pm_inbox/PM_BRIEFING_CURRENT.md` under the appropriate section
2. This is the PM's entry point — if it's not in the briefing, the PM may not see your file
3. **Output an operator relay block** — a fenced code block in your chat output containing a **one-line pointer**: just the filename and verdict action (e.g., `MEMO_SESSION_FINDINGS — PM verdict needed`). Do NOT compress the memo into the relay block. The PM already has the briefing for context; if the PM needs detail, the PM opens the file. The relay block is a signal, not a summary. The Operator copy-pastes this one-liner into the PM's context window — one click, zero context waste.

**Inbox cap:** 15 active `.md` files maximum (enforced by test). If you're near the cap, note it in your debrief.

**What goes to `pm_inbox/`:**
- Completed work order deliverables
- Design decision documents, spec proposals, audit reports
- Session memos and debriefs (Section 15.5)
- Handoff documents for cross-session context transfer

**What does NOT go to `pm_inbox/`:**
- Code files (those stay where they belong in the source tree)
- Test files
- Intermediate scratch work

---

## Step 9: Agent Notes (Flagging Observations)

If you notice something during implementation that doesn't belong in a commit or test — a judgment call you made, an ambiguity you resolved, a possible bug outside your scope, a pattern violation in nearby code — append an entry to `pm_inbox/SONNET_AGENT_NOTES.md`.

**Entry format:**
```
### [DATE] — [AGENT LETTER] — [SHORT TITLE]
**Context:** What you were working on
**Observation:** What you noticed or decided
**Action taken:** What you did (or "none — flagging only")
```

Opus reads this file at the start of each session and triages entries. This is how you communicate observations upstream without needing to stop work or ask Thunder to relay a message.

**When to write here:**
- You made a judgment call that could have gone either way
- You found something that looks like a bug but isn't in your scope
- You hit an ambiguity in a work order and chose an interpretation
- You noticed a pattern violation in existing code while working nearby
- You have a suggestion for a future work order

---

**You are now ready to begin work. Follow the CP workflow for all implementation tasks.**
