<!--
AGENT ONBOARDING CHECKLIST — MANDATORY READING ORDER & VERIFICATION STEPS

This file tells new agents EXACTLY what to read, in what order, and what to verify
before writing a single line of code. It exists because the project has 9+ root-level
.md files and agents waste context reading them in the wrong order or skipping critical ones.

LAST UPDATED: Post-Audit Remediation COMPLETE (1331 tests, FIX-01 through FIX-18)
-->

# Agent Onboarding Checklist

**Read this file FIRST. Follow it step by step. Do not skip ahead.**

---

## Step 1: Read the Governance Documents (IN THIS ORDER)

Read these files completely before writing any code. The order matters.

| Order | File | Purpose | Critical Because |
|-------|------|---------|-----------------|
| 1 | `PROJECT_STATE_DIGEST.md` | What's built, test counts, module inventory | You need to know what exists before touching anything |
| 2 | `AGENT_DEVELOPMENT_GUIDELINES.md` | Coding standards, pitfall avoidance | Contains hard-won bug fixes — ignoring this causes regressions |
| 3 | `AGENT_COMMUNICATION_PROTOCOL.md` | How to flag concerns, gates, scope creep | Violations cause code reverts |
| 4 | `PROJECT_COHERENCE_DOCTRINE.md` | Architectural constraints, scope boundaries | Defines what you CAN'T do (no LLM at runtime, etc.) |
| 5 | `KNOWN_TECH_DEBT.md` | Things that look broken but are intentionally deferred | Prevents you from wasting work "fixing" deferred items |

**Do NOT read** `WORKSPACE_MANIFEST.md` — it is severely stale and will mislead you about project size. Use `PROJECT_STATE_DIGEST.md` for the current module inventory.

**Do NOT read** `docs/AIDM_PROJECT_MASTER_PLAN.md` — it is superseded by `docs/AIDM_PROJECT_ACTION_PLAN_V2.md`.

---

## Step 2: Verify the Project Compiles and Tests Pass

Before writing any code, run:

```bash
python -m pytest tests/ -v --tb=short
```

**Expected result:**
- 1331+ tests passing
- Runtime under 5 seconds
- Zero failures, zero errors

If this doesn't pass, STOP. Do not proceed. Report the failure.

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

---

## Step 6: CP Workflow

Every completion packet follows this process:

1. Define scope (what's in, what's out)
2. Write schemas first (data contracts before algorithms)
3. Write tests second (at least Tier-1 stubs before implementation)
4. Implement (fill in logic to make tests pass)
5. Run full test suite (`python -m pytest tests/ -v --tb=short`)
6. Verify 1225+ tests still pass in under 5 seconds
7. Update `PROJECT_STATE_DIGEST.md` (test counts, module inventory, CP history)
8. Update `AGENT_DEVELOPMENT_GUIDELINES.md` if new patterns or pitfalls were discovered
9. Use `CP_TEMPLATE.md` for the standard CP decisions document format

---

## Step 7: When in Doubt

| Situation | Action |
|-----------|--------|
| Unsure if feature crosses a capability gate | **STOP.** Flag as GATE VIOLATION per communication protocol |
| Multiple valid implementation approaches | Flag as ARCHITECTURAL AMBIGUITY, propose options, wait for approval |
| Something looks like a bug in existing code | Check `KNOWN_TECH_DEBT.md` first — it may be intentional |
| Need a new entity field | Add to `entity_fields.py` FIRST, then use the constant everywhere |
| Need a new RNG stream | Document it, add to guidelines, use a descriptive name |
| Test suite takes > 2 seconds | Flag as PERFORMANCE CONCERN per communication protocol |
| Not sure which GridPoint type to use | See `AGENT_DEVELOPMENT_GUIDELINES.md` Section 3 |

---

## Step 8: PM Review Inbox

When you complete a deliverable that needs PM (Aegis) review — work order output, design doc, spec, audit report, or any artifact the PM should evaluate — copy the output to `pm_inbox/` as a markdown file.

**Naming convention:** `{AGENT}_{WO-id}_{short_description}.md`
**Examples:**
- `SONNET-C_WO-M1-01_event_reducer_impl.md`
- `SONNET-A_WO-M1-02_deterministic_ids.md`
- `OPUS_WO-M1-01_event_reducer_spec.md`

**Required header block** (first lines of every deliverable file):
```
# [Work Order ID]: [Short Title]
**Agent:** [Your agent identifier, e.g. Sonnet-C, Sonnet-A, Opus]
**Work Order:** [WO-M1-01, WO-M1-02, etc.]
**Date:** [YYYY-MM-DD]
**Status:** [Complete | Partial | Blocked]

## Summary
[2-3 sentence summary of what was done]

## Details
[Full deliverable content below]
```

Thunder will drag-and-drop these files to the PM (Aegis/GPT) for review. After review, files are moved to `pm_inbox/reviewed/` or deleted.

**What goes to pm_inbox:**
- Completed work order deliverables
- Design decision documents
- Spec proposals that need PM sign-off
- Audit reports or analysis results

**What does NOT go to pm_inbox:**
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
