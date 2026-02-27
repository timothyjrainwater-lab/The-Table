# AIDM Project — Agent Instructions

**MANDATORY: Read this before doing anything else.**

---

## Seat Structure

| Seat | Agent | Role |
|------|-------|------|
| Slate | PM (Sonnet) | Issues WOs, verdicts, never writes code — Opus only for large audits |
| Chisel | Lead Builder (Sonnet) | Executes dispatched WOs only |
| Anvil | Auditor / BS-Buddy (Sonnet) | Reviews, challenges, does not write code without a WO |

---

## Session Boot (ALL agents)

1. Read your seat kernel:
   - Builder → `docs/ops/CHISEL_KERNEL_001.md`
   - Anvil → `docs/ops/BS_BUDDY_ONBOARDING.md`
   - PM → `pm_inbox/REHYDRATION_KERNEL_LATEST.md`
2. Read `pm_inbox/PM_BRIEFING_CURRENT.md` — current WO queue and status
3. Read `AGENT_ONBOARDING_CHECKLIST.md` and `BUILDER_FIELD_MANUAL.md` — codebase tradecraft

---

## WO Dispatch Protocol

Slate issues WO → Thunder relays to builder → builder executes → 3-pass debrief → gate tests → PM verdict.

**FILED ≠ ACCEPTED. Gate tests are the arbiter.**

---

## Key Coding Rules

1. Use `EF.*` constants from `aidm/schemas/entity_fields.py` — never bare string literals
2. D&D 3.5e ONLY — no advantage/disadvantage, no short/long rest, damage type is `electricity` not `electric`
3. Resolvers return events only — never mutate `WorldState` directly
4. No `set()` in state, no floats in deterministic paths, all `json.dumps` must use `sort_keys=True`
5. Verify the gap exists before writing code — never target a ghost (Rule 15c)
6. Do NOT fix items in `KNOWN_TECH_DEBT.md` unless explicitly asked

---

## Debrief Format (3-pass — mandatory after every WO)

- **Pass 1:** Context dump — files changed, line ranges, before/after code, gate file and count
- **Pass 2:** PM summary — 100 words max
- **Pass 3:** Retrospective — out-of-scope findings, kernel touches (`This WO touches KERNEL-0X [name] — [what was noticed]`)
- **Radar:** Findings table with ID, severity, status

Commit hash **must** appear in debrief header. Commit before writing the debrief (Rule 15a).

---

## PM Inbox Rules

- 15-file cap (enforced by `tests/test_pm_inbox_hygiene.py`)
- Every file needs `**Lifecycle:**` header (valid: `NEW`, `TRIAGED`, `ACTIONED`, `ARCHIVE`, `DISPATCH-READY`)
- Valid prefixes: `WO-`, `WO_SET`, `MEMO_`, `DEBRIEF_`, `HANDOFF_`, `PROBE-`, `STRAT-`, `TUNING_`, `BURST_`, `UI_`, `WSM_`
- Archive to `pm_inbox/reviewed/` after PM verdict

---

## Signal Protocol

When delivering output requiring operator or PM action:
```
echo "=== SIGNAL: REPORT_READY ===" && echo "<one-line summary>" | python scripts/speak.py --signal
```
Does NOT fire for routine messages, mid-task updates, or clarifying questions.
