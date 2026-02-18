<!--
AGENT DEVELOPMENT GUIDELINES — CODING STANDARDS & PITFALL AVOIDANCE

This file is MANDATORY READING for all agents before writing code on this project.
It documents hard-won lessons from audits, discovered bugs, and architectural patterns
that MUST be followed to maintain project integrity.

REHYDRATION COPY: After editing this file, also update pm_inbox/aegis_rehydration/AGENT_DEVELOPMENT_GUIDELINES.md

LAST UPDATED: 2026-02-14 (5,144 tests, BL-017/018/020, Section 15 context boundary protocol, pm_inbox hygiene enforcement)
-->

# Agent Development Guidelines

## 0. Project Roles (Canonical Roster)

All agents operate within a six-role architecture. Know your role and its boundaries.

| Role | Callsign | Authority | Context Cost | Boundary |
|------|----------|-----------|-------------|----------|
| **Operator** | Thunder | Absolute. Dispatch, overrides. | N/A (human) | Routes work between all agents. |
| **PM** | Slate | Delegated. Verdicts, WOs, sequencing. | Irreplaceable | Never touches code. Documents only. Kernel owner. |
| **Agent** | — | Delegated (ops). Serves Operator. | Disposable | Chief of staff. Translates Operator intent, relays to PM, catches process failures, codifies governance, formats deliverables. Inbox janitor. Never writes kernel. |
| **Builders** | Per-WO | WO scope only. | Disposable | Code, tests, completion reports. No upstream visibility. |
| **BS Buddy** | Anvil (seat) | Advisory only. | Disposable | Brainstorming + TTS QA. No execution, no governance. Produces memos and conversation. |
| **Co-PM / Advisor** | Aegis | Advisory. No repo access. | External | Design audits, spec drafts, GT co-author. GPT (OpenAI). |

**Key constraint:** PM context is irreplaceable. Every other role is disposable. Protect PM context above all else.

## 1. Entity Field Names — CANONICAL CONSTANTS REQUIRED

### The Problem
Entity data is stored as `Dict[str, Any]`. Multiple modules reach into these dicts
with string literal keys. A bug was discovered where `permanent_stats.py` used
`"current_hp"` while every other module used `"hp_current"`. This was a silent failure
that caused HP clamping to never trigger after CON drain.

### The Rule
**ALWAYS use constants from `aidm.schemas.entity_fields` when reading or writing entity fields.**

```python
# CORRECT
from aidm.schemas.entity_fields import EF

hp = entity.get(EF.HP_CURRENT, 0)
entity[EF.DEFEATED] = True

# WRONG — bare string literals
hp = entity.get("hp_current", 0)
entity["defeated"] = True
```

### Adding New Entity Fields
1. Add the constant to `aidm/schemas/entity_fields.py` FIRST
2. Document which CP introduced the field
3. Use the constant in ALL code that touches the field
4. Update this guidelines document if the field has special semantics

### Current Canonical Fields
See `aidm/schemas/entity_fields.py` for the complete list. Key fields:
- `EF.HP_CURRENT` / `EF.HP_MAX` — Hit points (NOT "current_hp")
- `EF.AC` — Armor class
- `EF.DEFEATED` — Boolean defeat status
- `EF.POSITION` — Grid position dict with "x", "y" keys
- `EF.CONDITIONS` — Dict keyed by condition type string
- `EF.TEAM` — Team identifier string

---

## 2. Two Attack Pipelines — DO NOT CONFUSE

### Voice/Interaction Layer
- **Class**: `DeclaredAttackIntent` in `aidm.schemas.intents`
- **Fields**: `target_ref` (string name), `weapon` (string name)
- **Used by**: `interaction.py`, voice intent parsing
- **Purpose**: Captures player declaration ("I attack the goblin with my longsword")

### Combat Resolution Layer
- **Class**: `AttackIntent` in `aidm.schemas.attack`
- **Fields**: `attacker_id`, `target_id`, `attack_bonus` (int), `weapon` (Weapon dataclass)
- **Used by**: `attack_resolver.py`, `play_loop.py`, `combat_controller.py`
- **Purpose**: Fully resolved combat data for deterministic resolution

### The Bridge (NOT YET IMPLEMENTED)
When wiring the interaction engine to combat, a translation layer is needed:
1. `DeclaredAttackIntent` → look up character weapon stats → calculate attack bonus → `AttackIntent`
2. This bridge should be its own CP with tests
3. **NEVER** import `AttackIntent` from `aidm.schemas.intents` — that class was renamed to
   `DeclaredAttackIntent` specifically to prevent name collisions

---

## 3. Grid Position Types — USE THE RIGHT ONE

Three position-related types exist. Use the correct one for your context:

| Type | Module | Has `distance_to()` | Has `is_adjacent_to()` | Use For |
|------|--------|---------------------|----------------------|---------|
| `GridPoint` | `schemas/targeting.py` | Yes | No | Targeting/range checks |
| `GridPoint` | `schemas/intents.py` | No | No | Voice intent coordinates |
| `GridPosition` | `schemas/attack.py` | No | Yes | AoO adjacency checks |

### Future Plan
These should be unified into a single canonical type. Until then:
- For **range calculations** and **targeting**: use `targeting.GridPoint`
- For **AoO and adjacency**: use `attack.GridPosition`
- For **voice intents**: use `intents.GridPoint`
- **NEVER** assume these types are interchangeable

---

## 4. JSON Serialization Rules

### No Python `set()` in State
Python `set` objects are **not JSON-serializable**. The `WorldState.state_hash()` method
calls `json.dumps()`, which will crash on sets.

```python
# WRONG — will crash state_hash()
"flat_footed_actors": set(initiative_order)

# CORRECT
"flat_footed_actors": list(initiative_order)
```

### Sorted Keys Always
All JSON serialization MUST use `sort_keys=True` for deterministic output:
```python
json.dumps(data, sort_keys=True)
```

### No Floating Point in State
Integer arithmetic only in all deterministic paths. Floating point breaks
reproducibility across platforms.

---

## 5. RNG Stream Isolation

Four RNG streams exist. NEVER cross-contaminate them:

| Stream | Purpose | Used By |
|--------|---------|---------|
| `"combat"` | Attack rolls, damage rolls, AoO resolution | attack_resolver, full_attack_resolver, aoo |
| `"initiative"` | Initiative rolls | initiative.py |
| `"policy"` | Tactical variety selection | tactical_policy.py |
| `"saves"` | Saving throw rolls | save_resolver.py |

### Rules
- Each resolver MUST document which RNG stream it uses
- RNG consumption order within a stream MUST be deterministic and documented
- New resolvers that need randomness MUST use an existing stream or create a new named stream
- Streams that DON'T exist yet but may be needed: `"loot"`, `"encounter"`, `"narration"`

---

## 6. Event-Sourced State Mutation

### How State Actually Works
Despite the doctrine saying "mutations only through replay runner's single reducer," the actual
pattern in this codebase is:

1. **Resolvers** (attack_resolver, save_resolver, etc.) produce event lists but do NOT mutate state
2. **Apply functions** (apply_attack_events, apply_save_effects) create new WorldState instances from events
3. **Replay runner** handles only entity management events (add/remove/set_field), NOT combat events

### Rules for New Resolvers
1. Your resolver function MUST return events only — never mutate the WorldState passed to it
2. Create a corresponding `apply_X_events()` function that builds a new WorldState from events
3. The play loop calls your resolver, then your apply function
4. Add your event types to replay_runner.py's reducer if they need replay support

### Combat Replay Strategy
Combat replay uses **re-execution** (same seed → same output), NOT event reduction through
the replay runner. This is by design. If you need to test determinism, run the same scenario
twice with the same seed and compare outputs.

---

## 7. D&D 3.5e Rules Accuracy

### Common 5e Contamination Risks
This is a **D&D 3.5e** project. Do NOT introduce 5e concepts:

| 5e Concept | 3.5e Equivalent |
|------------|-----------------|
| Short rest / Long rest | 8-hour rest / Full day bed rest |
| Advantage / Disadvantage | Does not exist (use numeric modifiers) |
| Proficiency bonus | Base Attack Bonus (BAB) + feat/class bonuses |
| Cantrips at will | 0-level spells use spell slots |
| Concentration (5e style) | Different concentration rules in 3.5e |
| Electric damage | **Electricity** damage (PHB p.309) |

### Damage Types (3.5e Canonical List)
```
Physical: slashing, piercing, bludgeoning, nonlethal
Energy: fire, cold, acid, electricity, sonic
Other: force, positive, negative
```
The validated set is in `aidm/schemas/attack.py` `Weapon.__post_init__()`.

### Rest Types (3.5e)
```python
rest_type: Literal["overnight", "full_day"]
```
- `"overnight"`: 8-hour rest (PHB p.146) — natural healing, spell preparation
- `"full_day"`: Complete bed rest — 3× natural healing rate

---

## 8. Test Requirements

### Before Submitting Any CP
1. **ALL existing tests must pass** — zero regressions allowed
2. **Runtime must stay under 2 seconds** for the full suite
3. **New features must have tests** — minimum Tier-1 coverage
4. Run: `python -m pytest tests/ -v --tb=short`

### Test Organization
- One test file per module/feature: `tests/test_{module_name}.py`
- Tier-1 tests: Core correctness (blocking — must pass to merge)
- Tier-2 tests: Edge cases, boundary conditions, integration
- PBHA tests: Deterministic replay verification (10× identical results)

### Determinism Verification Pattern
```python
def test_determinism():
    """Same inputs → identical outputs across multiple runs."""
    results = []
    for seed in range(10):
        result = run_scenario(seed=42)  # SAME seed each time
        results.append(hash_result(result))
    assert len(set(results)) == 1  # All identical
```

---

## 9. Conditions System

### Storage Format
Conditions are stored as a **dict** keyed by condition type string:
```python
entity["conditions"] = {
    "prone": { "source": "trip_attack", ... },
    "shaken": { "source": "intimidate", ... }
}
```

### Querying Conditions
Use `get_condition_modifiers()` from `aidm.core.conditions`:
```python
modifiers = get_condition_modifiers(actor_id, world_state, context=None)
# modifiers.ac_modifier, modifiers.attack_modifier, etc.
```

### Default Value Consistency
When checking conditions on an entity:
```python
# CORRECT — conditions is a dict, default should be dict
conditions = entity.get(EF.CONDITIONS, {})

# WRONG — default is a list, but conditions is stored as a dict
conditions = entity.get("conditions", [])
```

---

## 10. File Organization

### Where New Code Goes
| Type | Directory | Naming |
|------|-----------|--------|
| Data contracts / schemas | `aidm/schemas/` | `{concept}.py` |
| Core logic / resolvers | `aidm/core/` | `{concept}.py` or `{concept}_resolver.py` |
| Validation rules | `aidm/rules/` | `{concept}_checker.py` |
| Tests | `tests/` | `test_{module}.py` |
| CP decisions | `docs/` | `CP{XX}_{NAME}_DECISIONS.md` |

### Deliverable File Routing (MANDATORY)

When you produce a deliverable (report, audit, completion doc, design spec), route it correctly:

| Destination | Who writes | Purpose |
|-------------|-----------|---------|
| `pm_inbox/` | Agents | New deliverables awaiting PM review |
| `pm_inbox/reviewed/` | PM/Thunder ONLY | Already-reviewed documents — **agents NEVER write here** |
| `pm_inbox/aegis_rehydration/` | PM/Thunder ONLY | PM system context — **agents NEVER write deliverables here** (exception: syncing canonical files like PSD, dev guidelines per their header instructions) |

**If you write to `pm_inbox/reviewed/`, your deliverable will be misrouted and may be missed or rejected.** Always write to `pm_inbox/` and let Thunder move it after review.

### Import Conventions
```python
# Schemas first, then core, then rules
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.entity_fields import EF
from aidm.core.attack_resolver import resolve_attack
from aidm.rules.legality_checker import LegalityChecker
```

---

## 11. Common Pitfalls Checklist

Before submitting any code change, verify:

- [ ] No bare string literals for entity field access (use `EF.*` constants)
- [ ] No Python `set()` objects stored in WorldState or active_combat
- [ ] No floating point arithmetic in deterministic code paths
- [ ] All JSON serialization uses `sort_keys=True`
- [ ] RNG streams are not cross-contaminated
- [ ] Resolver functions return events only, never mutate state
- [ ] New entity fields are added to `entity_fields.py` first
- [ ] D&D 3.5e terminology used (not 5e)
- [ ] All 594+ tests pass in under 2 seconds
- [ ] `DeclaredAttackIntent` (voice) vs `AttackIntent` (combat) — correct one used
- [ ] Grid position type matches the context (targeting vs AoO vs voice)
- [ ] Shallow copies of entity dicts don't accidentally share nested references
- [ ] TTS/model commands use `HF_HUB_OFFLINE=1` prefix (see Section 11a)

---

## 11a. Environment: Clash Proxy / HuggingFace Offline Mode

The operator runs **Clash** (proxy client) on `127.0.0.1:7890`. All external downloads (HuggingFace, GitHub, CivitAI, pip) must route through this proxy. The proxy environment variables are set system-wide (`HTTP_PROXY`, `HTTPS_PROXY` in bashrc, pip.ini, Windows user env, and git config).

**For HuggingFace model loads:** Even with the proxy configured, the `huggingface_hub` library does HEAD requests to verify cached weights on every load, adding latency. Use `HF_HUB_OFFLINE=1` to skip this when models are already cached:

```bash
# CORRECT — skips network verification, uses local cache
HF_HUB_OFFLINE=1 python scripts/speak.py --persona villainous "Your text here"

# WORKS but slow — does HEAD request through proxy on every load
python scripts/speak.py --persona villainous "Your text here"
```

**What this affects:**
- `scripts/speak.py` (Chatterbox TTS — loads from HuggingFace cache)
- Any direct use of `faster_whisper` model loading (though `scripts/listen.py` uses a local model path and is unaffected)
- Any `from_pretrained()` or `WhisperModel()` call that resolves to a HuggingFace repo

**First-time downloads:** Require the proxy to be active (Clash running). If Clash is stopped, use `proxy_off` in bash to disable proxy env vars and connect directly, or restart Clash.

**Proxy convenience functions** (in `~/.bashrc`):
- `proxy_on` — enable proxy env vars
- `proxy_off` — disable proxy env vars

**For curl/wget downloads:** Explicitly pass the proxy if env vars aren't picked up:
```bash
curl -x http://127.0.0.1:7890 -L -o output.file "https://example.com/file"
```

## 11b. Voice Pipeline: Piper→Chatterbox Reference Clips

Voice persona reference clips are generated by **Piper TTS** (clean CPU synthesis) and then cloned by **Chatterbox** (GPU, expressive voice cloning) at runtime. This two-stage pipeline produces cleaner output than using Kokoro-generated reference clips.

**Piper models location:** `models/piper/` (ONNX format, ~61MB each)
**Reference clips location:** `models/voices/{persona_id}.wav` (auto-discovered by Chatterbox adapter)

**Current persona→Piper voice mapping:**

| Persona | Piper Voice | Character Archetype |
|---|---|---|
| `dm_narrator` | en_GB-alan-medium | British male narrator |
| `npc_female` | en_GB-jenny_dioco-medium | British female NPC |
| `villainous` | en_GB-northern_english_male-medium | Gruff villain/guard |
| `npc_elderly` | en_GB-cori-medium | Noble/priestess |
| `npc_young` | en_US-amy-medium | Young/cute NPC |
| `heroic` | en_US-lessac-medium | Scholar/sage |

**To regenerate a reference clip:**
```python
from piper import PiperVoice
import wave
voice = PiperVoice.load("models/piper/en_GB-alan-medium.onnx")
with wave.open("models/voices/dm_narrator.wav", "wb") as wf:
    voice.synthesize_wav("Your reference text here — use diverse phonemes.", wf)
```

**Additional Piper voices available** (not currently assigned to personas):
- `en_GB-alba-medium` — Scottish female (fast talker, needs speed 0.85)
- `en_US-joe-medium` — US male
- `en_US-libritts_r-medium` — Multi-speaker (dozens of voices, use `--speaker N`)

**XTTS-v2 backup venv:** An isolated Python venv at `.venvs/xtts/` has Coqui XTTS-v2 installed (torch 2.5.1+cu121, coqui-tts 0.27.5, transformers 4.57.6). Call via subprocess bridge: `.venvs/xtts/Scripts/python.exe scripts/xtts_synth.py --ref REF.wav --text "..." --out OUT.wav`. Operator A/B tested XTTS-v2 against Chatterbox — Chatterbox won on both male (Alan) and female (Jenny) voices. XTTS-v2 is available as fallback only.

**TTS engine ranking (operator A/B tested, 2026-02-18):** Chatterbox > XTTS-v2 > F5-TTS > Piper > Kokoro. This ranking is closed — no further engine exploration unless new releases ship.

---

## 12. PROJECT_STATE_DIGEST.md Maintenance

The PSD is the single source of truth for any new agent joining the project. It MUST be
updated at the end of every CP with:

1. New locked systems added to the top section
2. Updated test count (total + breakdown by subsystem)
3. New modules added to module inventory
4. New test files added to test inventory
5. CP history entry with full details

**Stale PSD = confused agents = wasted work.**

---

## 13. Completion Packet (CP) Protocol

Every CP must follow this process:

1. **Define scope** — What exactly is being built, what's out of scope
2. **Write schemas first** — Data contracts before algorithms
3. **Write tests second** — At least Tier-1 test stubs before implementation
4. **Implement** — Fill in the logic to make tests pass
5. **Verify determinism** — Run full suite, check no regressions
6. **Update PSD** — Add CP to packet history, update counts
7. **Update this guidelines file** — If new patterns or pitfalls were discovered

### CP Naming Convention
- `CP-{XX}`: Standard completion packet (sequential numbering)
- `CP-{XX}{letter}`: Sub-packet (e.g., CP-18A for spellcasting part A)
- `SKR-{XXX}`: Structural Kernel Register entry (cross-cutting concerns)
- `CP-{XX}D`: Documentation/coherence cleanup packet

---

## 14. Boundary Laws (M1+)

Boundary laws are hard constraints enforced by tests in `tests/test_boundary_law.py`. Violating any of these will cause test failures. Full specifications live in `docs/governance/`.

### BL-017: UUID Injection Only

**No `uuid.uuid4()` in dataclass default_factory.** All IDs must be injected by the caller, never auto-generated. This ensures replay determinism — auto-generated UUIDs produce different values on each replay.

```python
# WRONG — breaks replay
@dataclass
class IntentObject:
    intent_id: str = field(default_factory=lambda: str(uuid.uuid4()))

# CORRECT — caller injects
@dataclass
class IntentObject:
    intent_id: str  # Required, no default
```

### BL-018: Timestamp Injection Only

**No `datetime.utcnow()` in dataclass default_factory.** Same rationale as BL-017 — timestamps must be injected, never auto-captured. A replay at a different wall-clock time must produce identical state.

```python
# WRONG — breaks replay
@dataclass
class Event:
    timestamp: float = field(default_factory=time.time)

# CORRECT — caller injects
@dataclass
class Event:
    timestamp: float  # Required, no default
```

### BL-020: WorldState Immutability at Non-Engine Boundaries

**No module outside the engine boundary may mutate WorldState or anything reachable from it.** This is the most important boundary law for day-to-day coding.

**Engine boundary (authorized mutators):**
- `aidm/core/play_loop.py`
- `aidm/core/replay_runner.py`
- `aidm/core/combat_controller.py`
- `aidm/core/prep_orchestrator.py`
- `aidm/core/interaction.py`

**Everything else** (narration, immersion, UI, spark adapters, IPC consumers) receives a `FrozenWorldStateView` — a read-only snapshot. If you need state in a non-engine module, use the frozen view.

```python
# WRONG — mutates state in a non-engine module
def format_hp(world_state):
    world_state.entities["pc1"]["hp"] = 0  # BL-020 VIOLATION

# CORRECT — read-only access
def format_hp(frozen_view: FrozenWorldStateView):
    hp = frozen_view.entities["pc1"]["hp"]  # Read-only, no mutation
```

**Full spec:** `docs/governance/BL-020_WORLDSTATE_IMMUTABILITY_AT_NON_ENGINE_BOUNDARIES.md`

### BL-021: Events Record Results, Not Formulas

**No event payload key may encode a formula, expression, or calculation.** Events are the immutable record of what happened. The engine computes; the event records the outcome. If a payload key contains `formula`, `expression`, `calculation`, `equation`, or `compute`, it is encoding process instead of result.

```python
# WRONG — payload encodes a formula
Event(event_type="damage_applied", payload={"damage_formula": "2d6+4", "target_id": "orc"})

# CORRECT — payload records the resolved result
Event(event_type="damage_applied", payload={"damage": 11, "target_id": "orc"})
```

**Enforced by:** `tests/test_boundary_law.py` — AST scan of all `payload={}` dict literals in `aidm/`.

---

## 15. Context Boundary Protocol

Agents have perfect recall within a context window and zero recall across context boundaries. These rules ensure institutional knowledge survives rotation.

### 15.1 Artifact Primacy Rule

Any fact that must survive a context boundary **MUST** be written to a file. Conversational knowledge not pinned to an artifact is assumed lost at next context rotation.

This includes:
- Reclassification decisions and their rationale
- Bug IDs and their current status
- Strategic findings that affect future work
- Cross-domain dependencies discovered during implementation

### 15.1a Re-Entry After Context Compaction

When resuming after a context compaction (session continuation), **do not** open with a clinical "Continuing from previous session" preamble. Come in with energy. The Operator works long sessions and context rotations are frequent — a flat procedural re-entry kills momentum. Lead with personality, then resume work immediately. Example: "I'm back. Let's pick up where we left off" — not a five-paragraph summary of what was discussed.

### 15.2 Handoff Checklist (Before Context Window Closes)

Before a session ends or approaches context limits, verify:

- [ ] State summaries updated (checklist, master lists, iteration log)
- [ ] PM memo written if strategic findings emerged
- [ ] Any mid-session reclassifications reflected in ALL affected files
- [ ] Uncommitted work documented in a handoff file (`pm_inbox/HANDOFF_*.md`)
- [ ] No implicit knowledge required — next agent can execute from artifacts alone

### 15.3 Dispatch Self-Containment Rule

Every dispatch or work order must be executable by an agent with zero prior context. The dispatch plus the files it cites must contain everything needed. No reliance on "the previous agent will have explained this."

Test: Could a fresh agent with no conversation history execute this dispatch using only the dispatch file and the files it references? If not, add the missing context.

**External dependency rule:** When a WO depends on external APIs, tool schemas, or documentation that isn't in the repo (e.g., Claude Code hooks spec, third-party library APIs, platform-specific schemas), the WO drafter must inline the relevant reference material directly in the dispatch doc or in a companion reference file cited by the dispatch. Builders should not need to web-search for specs mid-implementation — that burns disposable context on research instead of execution. If the drafter doesn't have the reference material, route a pre-research task to the assistant or BS Buddy first, then incorporate the findings into the dispatch.

**Mandatory delivery footer:** Every WO dispatch must end with a `## Delivery` section containing:

```
## Delivery

After all success criteria pass:
1. Write your debrief (`pm_inbox/DEBRIEF_WO-XXX.md`, Section 15.5) — 500 words max. Five mandatory sections:
   - **Section 0: Scope Accuracy** — one sentence: "WO scope was [accurate / partially accurate / missed X]"
   - **Section 1: Discovery Log** — what you checked, what you learned, what you rejected (even if efficient)
   - **Section 2: Methodology Challenge** — one thing to push back on
   - **Section 3: Field Manual Entry** — one ready-to-paste tradecraft entry
   - **Section 4: Builder Radar** — MANDATORY, 3 labeled lines exactly:
     - Line 1: **Trap.** Hidden dependency or trap — what almost burned you.
     - Line 2: **Drift.** Current drift risk — what is most likely to slide next.
     - Line 3: **Near stop.** What got close to triggering a stop condition, and why it didn't.
     - All 3 lines MUST be present with their labels. Write "none identified" if a line has no content. Do NOT omit lines.
     - **REJECTION GATE:** Debriefs with missing or unlabeled Radar lines are REJECTED and re-issued. No partial accept.
   - **Section 5: Focus Questions** — answer PM-selected questions from `## Debrief Focus` if present in dispatch
2. Update `pm_inbox/PM_BRIEFING_CURRENT.md`
3. `git add` all changed/new files — code, tests, debrief, AND briefing update
4. `git commit -m "feat: WO-XXX — [short description]"`
5. Record the commit hash and add it to the debrief header (`**Commit:** <hash>`)
6. `git add pm_inbox/DEBRIEF_WO-XXX.md && git commit --amend --no-edit`
7. **FIRE AUDIO CUE (MANDATORY):**
   Primary: `python scripts/speak.py --persona builder_signal "Work order complete. Awaiting Thunder."`
   Fallback: `powershell -c "(New-Object Media.SoundPlayer 'C:/Windows/Media/tada.wav').PlaySync()"`
   The Operator works on other tasks and cannot see your output. This cue is the ONLY notification that you are done. Missing it stalls the entire pipeline. The primary command exercises the full TTS pipeline (Chatterbox + emotion router + tavern-baked refs) — this is intentional QA.

Everything in the working tree — code AND documents — is at risk of loss if uncommitted.
Do NOT edit BUILDER_FIELD_MANUAL.md — the PM curates tradecraft from your debrief.
```

This footer is mandatory for all dispatches. The PM must include it. Builders who receive a dispatch without this footer should still commit (it's in the onboarding checklist and projectInstructions), but the footer makes the expectation explicit at point of dispatch.

**Integration seam checklist (added 2026-02-14):** Every WO dispatch must answer these questions in the Contract Spec or a dedicated `## Integration Seams` section:

1. **Does this WO consume data produced by another module?** If yes, name the source module, the field/key consumed, and who populates it. Example: "NarrativeBrief.presentation_semantics is populated by GAP-B-001 via content_id lookup in narrative_brief.py:612-615."
2. **Does this WO produce data consumed by another module?** If yes, name the consumer, the field/key produced, and the contract (type, default, when populated). Example: "Spell resolver events now emit content_id in payload, consumed by narrative_brief.py assembler."
3. **Is there an existing test that exercises this seam?** If no, the WO must include one. A seam without a test is a seam that will break silently.
4. **What happens if the upstream data is missing/None?** The WO must specify graceful degradation behavior. Example: "If content_id is not in event payload, presentation_semantics remains None. Validator rules that consume it no-op."

If a WO has zero cross-module dependencies (pure refactor, pure addition), state "No integration seams" explicitly. This checklist exists because constraints produce consistency within modules but cannot produce integration across modules.

**Assumptions to Validate section (added 2026-02-14):** Every WO dispatch should include an `## Assumptions to Validate` section listing 3-5 assumptions the builder should confirm before implementing. This forces critical engagement instead of blind execution. Examples: "Assumption: SPELL_REGISTRY entries have a content_id field. Confirm before wiring the lookup." If an assumption is wrong, the builder flags it in the Methodology Challenge section of their debrief before building the wrong thing. If a WO has no non-obvious assumptions, state "No assumptions to validate — spec is fully determined."

### 15.4 Cross-File Consistency Gate

When a status, count, verdict, or classification changes, update **ALL** files that reference it in the same commit. Partial updates create inconsistencies that compound across context boundaries.

**Evidence:** Domain A re-verification updated the checklist and WRONG_VERDICTS_MASTER but missed `DOMAIN_C_VERIFICATION.md`, creating an inconsistency that required a separate fix commit. The next agent saw conflicting numbers and couldn't determine which was correct without re-reading source files.

### 15.4.1 pm_inbox Hygiene Protocol (added 2026-02-18)

**pm_inbox root must stay clean.** Cap: 10 files max. The PM enforces this during every verdict cycle.

**Lifecycle rules:**
1. **Archive-on-verdict:** When the PM accepts a debrief, both the debrief AND its dispatch move to `pm_inbox/reviewed/archive_[phase]/` immediately. Reviewed files do not stay in root.
2. **Archive-on-triage for memos:** Dispositioned memos (ACCEPTED/PARKED/REJECTED) move to `reviewed/` immediately. Only memos blocking active work stay in root.
3. **Phase archive folders:** Each phase gets a subfolder under `reviewed/` (e.g., `archive_h1_smoke/`, `archive_oracle/`).
4. **Naming convention:** Root files must match: `PM_BRIEFING_*.md`, `REHYDRATION_KERNEL_*.md`, `README.md`, `DEBRIEF_WO-*.md`, `WO-*_DISPATCH.md`, `MEMO_*.md`, `BURST_*.md`, `SURVEY_*.md`, `DOCTRINE_*.txt`.
5. **Doctrine files are permanent root residents** while their doctrine version is active.

**Builder impact:** Your debrief will be archived after PM review. This is normal. The PM extracts your Field Manual entry and archives the file. Your debrief is not lost — it's in `reviewed/`.

### 15.5 Builder Debrief Protocol (Post-WO Batch)

After completing a work order or WO batch, the builder agent MUST produce a debrief before the session closes. **This is a standing obligation that applies to every WO, regardless of the WO's scope restrictions.** A read-only WO, an audit WO, or a WO that says "do not modify files" does not exempt you from the debrief — the debrief is a separate deliverable about the work, not part of the work itself.

**Single deliverable** (`pm_inbox/DEBRIEF_[WO_ID].md`):

**500-word cap.** The debrief is a compression artifact, not a narrative. Four mandatory sections plus header:

**Header:** Commit hash, success criteria met/unmet (one line each), blockers if any.

**Scope Accuracy (one line):** "WO scope was [accurate / partially accurate / missed X]." This gives the PM a fast signal on dispatch quality. Examples: "WO scope was accurate — all 6 success criteria mapped directly to implementation." or "WO scope was partially accurate — Change 2 was already implemented." or "WO scope missed condition_removed handler (same bug pattern, not called out)."

**Section 1 — Discovery Log:** What did you check, what did you learn, and what alternatives did you consider and reject? Not just friction — the full exploration path. Even efficient WOs have decision points. Examples: "Read play_loop.py line 340, confirmed key names matched WO spec, proceeded to fix" or "Considered fixing the producer instead of the consumer, rejected because producer keys are consistent with other event types" or "Validated Assumption #2 — entity_id key exists in payload, confirmed at play_loop.py:412." The question isn't "what went wrong" — it's "what did you check and what did you learn."

**Section 2 — Methodology Challenge:** One thing the dispatch got wrong, or one assumption in the system you would push back on. **This is mandatory even if you agree with everything.** Pick the weakest point. This turns every session from pure labor into a stress test of the methodology. Example: "RV-005 is marked FAIL severity but it's dormant — is that intentional?"

**Section 3 — Field Manual Entry:** One concrete addition to `BUILDER_FIELD_MANUAL.md`, written in the exact format the manual uses (numbered, with heading, 2-3 sentences). Not a suggestion — an actual entry ready to paste in. This closes the loop: every session makes the next session cheaper. If you genuinely have nothing to add, write "No new tradecraft" — but try harder first.

Implementation details, file inventories, and pipeline diagrams go in a `## Details` appendix if you have word budget remaining. The four sections above are the extracted fuel. Everything else is exhaust.

The PM reads this file, extracts the Field Manual Entry into `BUILDER_FIELD_MANUAL.md`, and archives. Every word beyond 500 is PM context wasted.

**Required header** (enforced by `tests/test_pm_inbox_hygiene.py`):
```
# DEBRIEF: [WO ID]
**From:** [Agent identifier]
**Date:** [YYYY-MM-DD]
**Lifecycle:** NEW
**Commit:** [hash] or UNCOMMITTED (see below)
```

**Commit-hash requirement:** The `**Commit:**` line is mandatory. If you committed your code changes, include the hash. If the session is ending before you can commit, write `UNCOMMITTED` and list the affected files so the Operator can recover the work. A completion report with no commit hash and no `UNCOMMITTED` marker is invalid — it leaves the PM unable to verify what actually shipped.

**After writing the debrief, update `pm_inbox/PM_BRIEFING_CURRENT.md`** with a one-line entry. This is the PM's entry point — files not in the briefing may be missed.

**After delivering your debrief, if no further work is queued,** trigger the idle notification: `echo "=== SIGNAL: REPORT_READY ===" && echo "Thunder, the forge is quiet." | python scripts/speak.py --signal`. This signals the Operator that the agent is idle and awaiting direction. See Standing Ops Rule 22.

### 15.6 Methodology Maintenance Protocol

The `methodology/` directory contains a domain-independent extract of this project's multi-agent coordination patterns. It is also published as a standalone repo at:

**https://github.com/timothyjrainwater-lab/multi-agent-coordination-framework**

**When to update `methodology/`:**
- A new coordination failure is discovered → add to `patterns/COORDINATION_FAILURE_TAXONOMY.md`
- A new pattern is codified (new section in this file, new template, new enforcement rule) → create or update the corresponding pattern/template in `methodology/`
- An existing pattern is revised based on experience → update the methodology version

**When to sync to the standalone repo:**
- After any commit that modifies files in `methodology/` in this repo
- Sync command: from `methodology/` directory, copy files to the standalone repo clone and push
- The PM or PO is responsible for triggering the sync — builder agents do NOT push to external repos without explicit instruction

**What does NOT go in `methodology/`:**
- D&D-specific rules, schemas, or verification details
- Project-specific file paths, bug IDs, or WO identifiers (use generic examples instead)
- Anything that requires knowledge of this project's architecture to understand
