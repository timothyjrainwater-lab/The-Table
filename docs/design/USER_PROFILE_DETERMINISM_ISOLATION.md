# User Profile & Determinism Isolation

**Status:** M0 / DESIGN / BINDING
**Type:** Architecture Specification
**Last Updated:** 2026-02-10
**Owner:** Agent C (UX/Integration)

---

## Purpose

This document specifies the user profile system for AIDM, with **absolute determinism isolation** guarantees. The user profile stores presentation-layer preferences (artifact name, UI settings) that must **NEVER** affect BOX mechanics or determinism-critical systems.

---

## Critical Constraint: Determinism Isolation

**MANDATORY:** User profile data is **presentation-only**. It must have **ZERO impact** on:

- RNG state
- Combat resolution
- Movement calculations
- Event-sourced logs
- Replay behavior
- Determinism hashes

**Verification:** All changes to user profile must pass determinism isolation regression tests (see [tests/test_user_profile.py](tests/test_user_profile.py:243-361)).

---

## User Profile Schema

### File Location

```
config/user_profile.yaml
```

**Rationale:**
- Placed in `config/` (app-level, NOT `aidm/core/`)
- Isolated from BOX mechanics (combat, movement, RNG)
- Never committed to VCS (added to `.gitignore`)

###  Schema

```yaml
# Artifact/Companion Name (user-chosen name for AIDM instance)
artifact_name: "Artificer"  # Default: "Artificer"

# First-Run Onboarding State
first_run_complete: false  # Triggers naming prompt on startup

# Profile Version (for migration support)
schema_version: 1  # v1: Initial release
```

### Field Specifications

#### `artifact_name: str`

**Purpose:** User-chosen name for their local AIDM instance
**Usage:** UI headers, greetings, narration wrapper text **ONLY**
**Constraints:**
- Max length: 32 characters (truncated if longer)
- Whitespace trimmed
- Empty/whitespace-only defaults to "Artificer"

**Rename:** Via Settings UI or CLI command `aidm set-name "NewName"`

#### `first_run_complete: bool`

**Purpose:** Tracks whether first-run onboarding has been shown
**Behavior:**
- `false`: Triggers artifact naming prompt on next startup
- `true`: Skip onboarding (already completed)

#### `schema_version: int`

**Purpose:** Profile schema version for migration support
**Current Version:** 1 (v1: artifact_name + first_run_complete)

---

## First-Run Onboarding

### Trigger Condition

```python
profile = UserProfile.load()
if profile.needs_first_run_prompt():
    # Show onboarding
    run_first_run_onboarding()
```

### Prompt Flow

```
==========================================
FIRST-RUN SETUP
==========================================

What would you like to call me?
(Press Enter to use default: 'Artificer')

> [User input]

Great! You can call me '[chosen name]'.
(You can change this later via Settings or CLI: 'aidm set-name "NewName"')
```

**Default Behavior:**
- Empty input → use "Artificer"
- Non-interactive environment → use "Artificer"

**Persistence:**
- Name saved to `config/user_profile.yaml`
- `first_run_complete` set to `true`
- Prompt never shown again (unless user resets config)

---

## Rename Capability

### Via CLI

```bash
python -m aidm.user_profile set-name "Merlin"
```

### Via Settings UI

_(Future implementation: M1+)_

Settings → "Name" field → Enter new name → Save

### Behavior

- Name normalized (trimmed, truncated to 32 chars)
- Profile saved immediately
- Takes effect on next UI render

---

## Determinism Isolation Guarantees

### Architecture Enforcement

**User profile module is ISOLATED from BOX mechanics:**

1. **Module placement:** `aidm/user_profile.py` (NOT in `aidm/core/`)
2. **Import prohibition:** BOX mechanics modules (RNG, combat, movement) **MUST NOT** import `user_profile`
3. **Usage restriction:** `artifact_name` used **ONLY** in presentation layer (UI, narration wrappers)

### Regression Tests

**Location:** [tests/test_user_profile.py](tests/test_user_profile.py:243-361)

**Test Suite:** `TestDeterminismIsolation`

**Critical Tests:**

1. `test_artifact_name_not_in_rng_seed`
   Verifies `aidm.core.rng_manager` does NOT import `user_profile`

2. `test_artifact_name_not_in_combat_resolution`
   Verifies `aidm.core.attack_resolver` does NOT import `user_profile`

3. `test_artifact_name_not_in_event_log_schema`
   Verifies `aidm.core.event_log` does NOT import `user_profile`

4. `test_replay_determinism_with_different_artifact_names` **(CANARY TEST)**
   **CRITICAL:** Same RNG seed produces identical outputs with different artifact names

5. `test_combat_determinism_with_different_artifact_names` **(CANARY TEST)**
   **CRITICAL:** Combat dice rolls identical with different artifact names

**Failure Condition:**
If ANY canary test fails, determinism isolation is **BROKEN** and artifact_name has leaked into BOX mechanics.

**Acceptance Criteria:**
All 5 determinism isolation tests must pass (green) before merging any user profile changes.

---

## Usage Examples

### First-Run Onboarding

```python
from aidm.user_profile import UserProfile, run_first_run_onboarding

profile = UserProfile.load()

if profile.needs_first_run_prompt():
    profile = run_first_run_onboarding()

print(f"Welcome back! Your {profile.artifact_name} is ready.")
```

### UI Greeting

```python
from aidm.user_profile import UserProfile

profile = UserProfile.load()

# SAFE: artifact_name used in UI greeting only
ui.show_greeting(f"Welcome, {profile.artifact_name}!")
```

### Narration Wrapper

```python
from aidm.user_profile import UserProfile

profile = UserProfile.load()

# SAFE: artifact_name used in narration wrapper (presentation layer)
narration_prefix = f"[{profile.artifact_name}]: "
ui.show_narration(narration_prefix + event_narration)
```

### PROHIBITED Usage

```python
# ❌ NEVER DO THIS: artifact_name affecting RNG
from aidm.user_profile import UserProfile

profile = UserProfile.load()
seed = hash(profile.artifact_name)  # ❌ BREAKS DETERMINISM
rng = DeterministicRNG(seed=seed)
```

```python
# ❌ NEVER DO THIS: artifact_name in event log
from aidm.user_profile import UserProfile

profile = UserProfile.load()
event = AttackEvent(
    attacker_id="fighter_1",
    artifact_name=profile.artifact_name  # ❌ BREAKS EVENT SOURCING
)
```

---

## CLI Commands

### Show Current Profile

```bash
python -m aidm.user_profile show
```

**Output:**
```
Artifact Name: Artificer
First Run Complete: False
Schema Version: 1
```

### Set Artifact Name

```bash
python -m aidm.user_profile set-name "Gandalf"
```

**Output:**
```
Artifact renamed to: 'Gandalf'
```

### Trigger First-Run Onboarding

```bash
python -m aidm.user_profile first-run
```

**Output:**
```
==========================================
FIRST-RUN SETUP
==========================================

What would you like to call me?
(Press Enter to use default: 'Artificer')

> Merlin

Great! You can call me 'Merlin'.
(You can change this later via Settings or CLI: 'aidm set-name "NewName"')

Profile saved: Merlin
```

---

## File Structure

```
DnD-3.5/
├── config/
│   ├── models.yaml            # LLM model registry (committed)
│   └── user_profile.yaml      # User profile (NEVER committed, in .gitignore)
├── aidm/
│   ├── core/                  # BOX mechanics (MUST NOT import user_profile)
│   │   ├── rng_manager.py
│   │   ├── attack_resolver.py
│   │   └── event_log.py
│   └── user_profile.py        # User profile module (presentation-only)
├── tests/
│   └── test_user_profile.py   # Determinism isolation regression tests
└── .gitignore                 # Includes: config/user_profile.yaml
```

---

## Acceptance Criteria

**Pre-Merge Checklist:**

- [x] User profile schema defined (`config/user_profile.yaml`)
- [x] Python module created (`aidm/user_profile.py`)
- [x] First-run onboarding implemented (`prompt_artifact_name()`, `run_first_run_onboarding()`)
- [x] Rename capability implemented (`rename_artifact()`)
- [x] CLI commands functional (`set-name`, `show`, `first-run`)
- [x] `.gitignore` updated (`config/user_profile.yaml` excluded from VCS)
- [x] Determinism isolation tests created (27 tests, 5 critical canary tests)
- [x] All tests pass (27/27 green)
- [x] **Determinism canary tests pass** (5/5 green)
- [x] No BOX mechanics files import `user_profile` (verified by tests)
- [x] Documentation complete (this file)

**Determinism Verification:**

```bash
# Run determinism isolation tests
pytest tests/test_user_profile.py::TestDeterminismIsolation -v

# Expected output:
# test_artifact_name_not_in_rng_seed PASSED
# test_artifact_name_not_in_combat_resolution PASSED
# test_artifact_name_not_in_event_log_schema PASSED
# test_replay_determinism_with_different_artifact_names PASSED (CANARY)
# test_combat_determinism_with_different_artifact_names PASSED (CANARY)
# 5 passed
```

**If ANY canary test fails:** STOP, investigate, fix before merging.

---

## Future Work (M1+)

1. **Settings UI:** Visual interface for renaming artifact
2. **Advanced Preferences:** Voice TTS selection, narration style, UI theme
3. **Profile Export/Import:** Share profiles across machines (optional)
4. **Voice Personas:** Link artifact_name to TTS voice persona (presentation-only)

**CONSTRAINT:** All future user profile additions must pass determinism isolation regression tests.

---

## Status

**Current:** COMPLETE (M0)
**Next:** First-run onboarding integration into main application entry point (M0+)

---

## References

- Implementation: [aidm/user_profile.py](../aidm/user_profile.py)
- Tests: [tests/test_user_profile.py](../tests/test_user_profile.py)
- Config: [config/user_profile.yaml](../config/user_profile.yaml)
- UX Constraints: [R1_UX_CONSTRAINTS_FOR_DETERMINISM.md](research/R1_UX_CONSTRAINTS_FOR_DETERMINISM.md)
