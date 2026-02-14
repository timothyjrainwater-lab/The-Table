# MEMO: Builder Commit Gap — Root Cause and Fix + Session Findings
**From:** Agent (Opus 4.6)
**Date:** 2026-02-14
**Lifecycle:** NEW

---

## 1. Builder Commit Gap — Root Cause Analysis

**Problem:** 4 consecutive WOs (WEAPON-PLUMBING-001, RNG-PROTOCOL-001, BRIEF-WIDTH-001, TTS-CHUNKING-001) shipped with all code changes uncommitted in the working tree. This is the 4th occurrence of the orphaned builder work pattern. The Operator had to manually recover and commit 39 files / 4,049 insertions.

**Root cause:** Rule 15a (commit-before-report) was codified in Standing Ops and the debrief header template in AGENT_DEVELOPMENT_GUIDELINES.md Section 15.5. But **builders never read Standing Ops**, and the debrief header template reads as a formatting instruction ("fill in the hash field"), not an action instruction ("create the commit").

The three documents builders actually read — onboarding checklist, projectInstructions in `.claude/settings.json`, and the WO dispatch itself — contained zero mention of git commit.

**Fix applied (commit `0a10e80`):** Commit instructions added at every layer builders touch:

1. **AGENT_ONBOARDING_CHECKLIST.md** — CP Workflow step 7: `git add` + `git commit` before debrief. DO NOT list item #8: no debrief without commit.
2. **`.claude/settings.json` projectInstructions** — Rule (8): MANDATORY COMMIT RULE.
3. **AGENT_DEVELOPMENT_GUIDELINES.md Section 15.3** — Mandatory `## Delivery` footer template for all WO dispatches.
4. **REHYDRATION_KERNEL_LATEST.md** — Mandatory delivery footer rule so PM includes commit instructions in every dispatch.

**PM action required:** All future WO dispatches must include the `## Delivery` footer per Section 15.3. Existing dispatch-ready WOs in `pm_inbox/` do not have this footer and should be updated before dispatch.

---

## 2. Builder Findings — WO-BRIEF-WIDTH-001

### 2a. FrozenWorldStateView / MappingProxyType Trap (Recurring)

`isinstance(x, dict)` fails on MappingProxyType-wrapped state dicts. This is the 2nd occurrence in the Lens layer. Builder recommends a project-level `is_mapping()` utility or a docstring warning on FrozenWorldStateView.

**PM decision needed:** Add to KNOWN_TECH_DEBT.md as documented fragility, or draft a micro-WO for the utility function?

### 2b. Multi-Target Primary Selection Is Order-Dependent

The narrative_brief assembler picks whichever `target_id` was last set by a damage event as the "primary" target. For AoE, that's the last target in the event list — not necessarily the highest-damage one. The WO spec said "first or highest-damage" but the builder chose the simpler last-set approach since resolvers currently emit targets in a consistent order.

**Fragility:** If AoE resolver ordering changes, primary selection breaks silently. Flag for tech debt or accept as intentional simplification?

### 2c. WO-BRIEF-WIDTH-001 Was Partially Pre-Completed

A prior session completed the overrun/sunder/disarm/grapple causal chain propagation and play_loop.py chain_id generation. This session completed the narrative_brief + prompt_pack expansion. No conflict — layered cleanly. The existing debrief on disk covers the full final state.

---

## 3. Builder Findings — WO-WEAPON-PLUMBING-001

### 3a. Schema Was Pre-Existing

The Weapon dataclass already had `weapon_type`, `is_ranged`, etc. The builder's job was plumbing existing fields through to resolvers, not creating them. WO was accurate but could have noted the schema was already in place.

### 3b. max_range=100 Legacy Tech Debt

Hardcoded `max_range=100` in both attack resolvers is now replaced by `range_increment * 10` for ranged weapons, but the legacy default is still there for melee. This is a known simplification.

### 3c. Linter Race Condition (Unresolved)

Builder reported 5-6 failed edits from files being modified between read and write. Investigation found no `.vscode/settings.json`, no `.pre-commit-config.yaml`. The active `pre-commit` git hook only fires on commit, not during edits. Most likely cause: VSCode user-level format-on-save setting or another Claude Code instance modifying the same files. **Still unresolved.**

---

## 4. Process Validation

Builder praised the WO dispatch format: "cleanest WO format I've worked from — zero ambiguity meant zero clarification round-trips." This validates the Brick format (Target Lock + Binary Decisions + Contract Spec + Implementation Plan) as the correct WO structure.

---

## Retrospective

The builder commit gap is the most consequential process failure we've had — 4 WOs worth of code nearly lost. The fix is comprehensive (4 layers patched), but its effectiveness depends on the PM consistently including the `## Delivery` footer in dispatches. The kernel rule makes this a standing obligation. First test will be the next WO dispatch cycle.

The FrozenWorldStateView trap is a good candidate for a 15-minute micro-WO. It's bitten twice now and will bite again. The multi-target ordering fragility is lower priority — acceptable as tech debt for now.
