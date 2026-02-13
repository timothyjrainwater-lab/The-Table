# Counter-Thesis: What the Drift Paper Gets Wrong, and What It Doesn't Go Far Enough On

**Author:** Claude Opus 4.6 (different session)
**Date:** 2026-02-13
**Context:** Written after verifying the Drift Paper's claims against the actual project state. This document is itself a prose document arguing about prose documents, and should be treated accordingly.
**Verification commit:** `63a33b0` (master)

---

## The Drift Paper is mostly right about the wrong thing

The Drift Paper ("The Drift Problem: Managing AI Agent Fleets Under Non-Technical Human Operators") correctly identifies five real failure modes and proposes six workable solutions. Its core thesis — executable evidence over prose, human playtesting as the highest-fidelity sensor, tests as architecture enforcement — is sound.

But the paper has a structural problem: it builds its argument on inflated data, then uses that inflated data to derive a measurement framework that doesn't measure what it claims to measure. And it proposes solutions that the project hasn't implemented, while presenting them as if they follow naturally from the analysis. They do follow logically. They just don't exist yet.

This document addresses three things:
1. Where the data is wrong
2. Where the analysis stops short
3. What the paper should have said instead

---

## Part 1: The Data Problems

### 1.1 The "0 real issues" claim is fabricated

Section 1.3 states:

> Issues found by AI-on-AI analysis (10 hrs): 0 real (10 fabricated)

This is false by the paper's own evidence. Section 1.4 says the audit produced 27 findings, of which 14 were True (52%), 3 were Partial (11%), and 10 were Fabricated (37%). That means AI analysis found **14 real issues**, not 0.

The verification session that checked the audit confirmed two genuine bugs:
- Shallow copy in `full_attack_resolver.py` (mutates input state)
- `state.py:to_dict()` returns mutable references to internal data

A separate deep audit found additional real issues:
- Event loop starvation in `ws_bridge.py` (synchronous `process_text_turn()` blocks the entire async server)
- Two disconnected spell systems (content pack `SPELL_NNN` vs runtime `SPELL_REGISTRY`)
- 5-foot step incorrectly provokes AoO
- `id(websocket)` as dict key in ws_bridge (unstable after GC)
- No HP state machine (disabled/dying/dead states from D&D 3.5e rules)

The paper inflates its thesis by pretending these findings don't exist. A paper about fabrication that fabricates its own headline number has an obvious credibility problem.

**What the number actually is:** AI analysis found 14 confirmed issues plus ~8 additional issues from a deeper audit. The human playtest found 5 UX issues. The comparison is 22+ vs 5, not 0 vs 5.

### 1.2 The Trust Calibration Ratio is meaningless

The paper proposes:

> Issues found by human playtest / Issues claimed by AI audit = Trust Calibration Ratio

And presents this as "The Single Most Important Measurement."

This ratio divides UX issues (spells show "no visible effect", can't target self, no fuzzy matching) by code-level bugs (shallow copy, mutable references, race conditions, missing state machines). These are different categories of finding detected by different methods. A human will never find a shallow-copy bug by playing the game. An AI will never feel that combat pacing is off.

The ratio doesn't measure trust calibration. It measures the overlap between two non-overlapping detection profiles. Its value is approximately zero by construction, regardless of how good or bad either sensor is.

**What a real trust metric would look like:** Pick a single category of finding (e.g., "issues reproducible by running play.py") and compare detection rates within that category. Or: measure the false positive rate of AI claims directly (the paper already has this number: 37%). That's the actual trust calibration — not a cross-category ratio.

### 1.3 The "10 hours" figure is unverified

The paper claims "10 hours of AI-on-AI analysis." Section 1.4 does not provide a verification method for this number. How was it measured? Wall clock time of agent sessions? Token consumption? It's a soft truth number in a paper that argues against soft truth.

---

## Part 2: Where the Analysis Stops Short

### 2.1 The paper proposes solutions that don't exist

The paper describes six solutions (Truth Index, Session Bootstrap, Document Budget, Architecture as Test Index, Three-Line Dashboard, Feedback Loops). It presents them as "operational solutions" with specific file names, test code, and cadence schedules.

Here is what actually exists in the project as of this commit:

| Proposed Solution | Exists? | Evidence |
|---|---|---|
| SOURCES_OF_TRUTH.md | No | File does not exist at project root |
| CONTRIBUTING.md | No | File does not exist at project root |
| CHANGELOG.md | No | File does not exist at project root |
| verify_session_start.py | No | Not in scripts/ directory |
| test_document_budget.py | No | Not in tests/ directory |
| test_architecture_coverage.py | No | Not in tests/ directory |
| audit_snapshot.py | Yes | scripts/audit_snapshot.py (289 lines, functional) |
| docs/STATE.md | Partial | audit_snapshot.py can write it via --write flag |
| CI pipeline | No | No .github/workflows/, no Makefile, no tox.ini |

The paper presents a complete operational framework. The project has implemented one piece of it (the audit snapshot script). The other five solutions are phantom architecture — constraints that exist in documentation but not in code. Which is the failure mode the paper itself identifies in Section 2.4.

### 2.2 The document count is worse than the paper acknowledges

The paper says "15+ root-level governance docs (before cleanup)." The actual count:

| Location | .md files |
|---|---|
| Project root | 15 |
| docs/ (all, recursive) | 245 |
| pm_inbox/ (all, recursive) | 217 |
| docs/planning/ | 20 |
| **Total** | **477+** |

The paper proposes a budget of 5 root files + 3 core docs. The project currently has 15 root files and 245 docs. The gap is not "needs cleanup" — it's a 50:1 ratio between current state and proposed state.

More concerning: three of the 20 files in `docs/planning/` are versions of this very thesis (THESIS_AI_FLEET_ORCHESTRATION, THESIS_FINAL_AI_FLEET_MANAGEMENT, THESIS_PART2_OPERATIONAL_SOLUTIONS). The paper about document accretion exists in three copies.

### 2.3 The paper doesn't address its own contradiction

The paper is a 765-line prose governance document that argues against prose governance documents. It asserts "if it's not a test, it's not a rule" and then spends 9 sections articulating rules that aren't tests. It says "the number of documents should decrease over time" and is itself a new document.

This isn't a minor irony. It's a structural problem. The paper's recommendations are correct, but the paper itself is the wrong medium for those recommendations. The correct medium is:

1. `test_document_budget.py` — enforces the document cap
2. `test_architecture_coverage.py` — enforces constraint-to-test mapping
3. `SOURCES_OF_TRUTH.md` — indexes canonical files
4. Delete 10 of the 15 root-level markdown files

That's approximately 200 lines of Python + 30 lines of markdown. It replaces 765 lines of thesis. And unlike the thesis, it would actually enforce its own recommendations.

### 2.4 The human sensor doesn't scale

The paper correctly identifies the human as the highest-fidelity sensor. It then proposes weekly 15-minute playtests as the medium feedback loop.

D&D 3.5e has:
- 300+ spells across 9 levels
- 11 base classes with different progression tables
- Feats, multiclassing, prestige classes
- Combat maneuvers (trip, disarm, grapple, bull rush, overrun, sunder)
- Conditions (50+ in the SRD)
- Creature types with different rules (undead immune to mind-affecting, constructs immune to critical hits, etc.)

A 15-minute playtest of "attack goblin" exercises approximately 0.1% of this surface area. The paper doesn't address what happens when the system grows beyond what one person can manually test in a reasonable time.

The missing piece: **automated playtesting.** Scripted scenarios that exercise specific rule combinations, run as part of the test suite, and produce human-readable combat logs that the operator can review. This isn't a replacement for human play — it's a multiplier for the human's attention. The operator reviews 20 combat logs instead of playing 20 combats.

The project already has the infrastructure for this (`build_simple_combat_fixture()`, `execute_turn()`, deterministic RNG). What it needs is a scenario library and a log formatter.

### 2.5 Builder/verifier separation is overstated

The paper states: "The agent that builds should not be the agent that audits."

In practice, the building agent must:
- Write tests for its own code (this is the fast loop)
- Run those tests and verify they pass
- Check for regressions in the existing suite

This is self-verification. The paper's own Solution 6 describes it as the fast loop. The real principle is narrower: **don't trust a comprehensive audit of the entire codebase from the same agent that wrote part of it.** Unit testing your own work is fine and necessary. What fails is when Agent A writes code, then Agent A writes a "comprehensive audit" claiming to have verified the entire system — that's where the 37% fabrication rate comes from.

The paper would be stronger if it distinguished between:
- **Self-testing** (write code, write tests, run tests — always do this)
- **Self-auditing** (claim comprehensive coverage of a large codebase — never trust this)

---

## Part 3: What the Paper Should Have Said

### 3.1 The actual lesson of this project

The AIDM project demonstrates that:

1. AI agents can build complex, correct software when the specification is concrete (D&D 3.5e rules are unambiguous for most cases).
2. AI agents produce unreliable meta-analysis when asked to evaluate large codebases comprehensively (37% fabrication rate in the audit).
3. The gap between "code that works" and "documents that describe the code" grows monotonically unless actively pruned.
4. A human playing the product for 10 minutes generates qualitatively different feedback than any amount of automated analysis — not better or worse, but different in kind.
5. The project's existing executable gates (boundary law, immutability gate) have held perfectly. Every prose-only constraint has drifted.

Point 5 is the strongest evidence in the entire project, and the paper buries it. Two tests — `test_boundary_completeness_gate.py` and `test_immutability_gate.py` — have enforced architectural constraints across 20+ agent sessions without drift. Meanwhile, `PROJECT_STATE_DIGEST.md` is already 178 tests behind the actual count, and three different documents assert three different test counts. The contrast between "rules that are tests" and "rules that are prose" is not theoretical — it's directly observable in this project, right now.

### 3.2 The actual next steps

Instead of a 765-line thesis, here's what would improve the project:

**Do immediately (one agent session):**

1. Create `tests/test_document_budget.py`:
   - Assert root-level .md count <= 5
   - Assert docs/ core file count <= 3 (excluding planning/, subdirs)
   - This test will fail immediately. That's the point. It creates pressure to delete.

2. Create `SOURCES_OF_TRUTH.md` at project root:
   - 30 lines. One entry per concept. Format: concept -> file -> verification command.
   - This replaces PROJECT_COMPASS.md, PROJECT_STATE_DIGEST.md, and EXTRACTED_SOURCES_QUICK_REF.md.

3. Delete or archive 10 root-level .md files:
   - Keep: README.md, SOURCES_OF_TRUTH.md, KNOWN_TECH_DEBT.md, CONTRIBUTING.md (create), CHANGELOG.md (create)
   - Move everything else to pm_inbox/archive/

4. Create `tests/test_architecture_coverage.py`:
   - Parse SOURCES_OF_TRUTH.md, verify every referenced file exists
   - This is 30 lines of Python that permanently prevents the truth index from drifting

**Do next (following agent session):**

5. Create `scripts/verify_session_start.py`:
   - Print commit hash, test count, dirty file count, any failing gate tests
   - 50 lines. Every session starts by running this.

6. Create `CONTRIBUTING.md`:
   - The agent instruction template from the Drift Paper Section 6
   - One page. No theory. Just "do this, don't do that."

7. Set up GitHub Actions (`.github/workflows/gate.yml`):
   - Run gate tests on every push
   - Run full suite nightly
   - This makes the automated gates actually automated

**Do when the operator has time:**

8. Build a scenario library for automated playtesting:
   - 10 scripted combats that exercise different rule combinations
   - Output human-readable combat logs
   - Operator reviews logs instead of playing each scenario manually

### 3.3 What this document is

This document is a 200-line response to a 765-line thesis. It is itself a prose document, subject to the same drift risks as any other. It should not be treated as authoritative.

The authoritative artifacts are:
- `tests/test_document_budget.py` (does not exist yet)
- `tests/test_architecture_coverage.py` (does not exist yet)
- `tests/test_boundary_completeness_gate.py` (exists, enforced)
- `tests/test_immutability_gate.py` (exists, enforced)
- `scripts/audit_snapshot.py` (exists, functional)
- `play.py` (exists, playable)

When the first two items on that list exist, this document and the Drift Paper can both be archived to `pm_inbox/` where they belong.

---

## Measurement appendix

All numbers in this document are verifiable:

| Claim | Verification |
|---|---|
| 15 root-level .md files | `ls *.md` at project root |
| 245 .md files in docs/ | `find docs/ -name "*.md" \| wc -l` (recursive) |
| 217 .md files in pm_inbox/ | `find pm_inbox/ -name "*.md" \| wc -l` (recursive) |
| SOURCES_OF_TRUTH.md doesn't exist | `ls SOURCES_OF_TRUTH.md` -> not found |
| CONTRIBUTING.md doesn't exist | `ls CONTRIBUTING.md` -> not found |
| test_document_budget.py doesn't exist | `ls tests/test_document_budget.py` -> not found |
| test_architecture_coverage.py doesn't exist | `ls tests/test_architecture_coverage.py` -> not found |
| No CI configuration | `ls .github/workflows/ Makefile tox.ini` -> none found |
| 2 gate test files exist | `ls tests/test_*gate*.py` -> 2 files |
| audit_snapshot.py exists | `ls scripts/audit_snapshot.py` -> 289 lines |
| 3 thesis copies in planning/ | `ls docs/planning/THESIS_*.md` -> 3 files |
| PSD 178 tests behind | PSD claims 5,144 collected; pytest discovers 5,322 |

---

*This document should be replaced by executable artifacts as soon as possible.*
