# M1 Monitoring Protocol
## Kill Switch Detection, Evidence Capture, and Response Playbook

**Document Type:** Governance / Monitoring Specification
**Purpose:** Define exact telemetry, detection methods, and response procedures for M1 guardrail enforcement
**Agent:** Agent D (Research Orchestrator)
**Date:** 2026-02-10
**Status:** ACTIVE (M1 monitoring spine operational)
**Authority:** Single source of truth for M1 violation detection and response

---

## 1. Purpose Statement

This document defines:
- **WHAT signals prove compliance** (or violation)
- **HOW violations are detected** (measurement method)
- **WHAT evidence is captured** (logs, artifacts, traces)
- **WHAT happens when triggers fire** (auto-action + escalation)

**This is NOT:**
- ❌ Production code (monitoring is external to implementation)
- ❌ Schema definitions (no data structure changes)
- ❌ Policy authoring (GAP-POL items remain unresolved)

---

## 2. Kill Switch Monitoring Table

### KILL-001: Memory Hash Changed During Narration

**Trigger Signal:** Memory object hash differs before vs after narration generation

**Detection Method:**
```
BEFORE narration_function() entry:
  memory_hash_before = hash(memory_snapshot.to_dict())
  LOG: "PRE_NARRATION_HASH: {memory_hash_before}"

AFTER narration_function() exit:
  memory_hash_after = hash(memory_snapshot.to_dict())
  LOG: "POST_NARRATION_HASH: {memory_hash_after}"

IF memory_hash_before != memory_hash_after:
  TRIGGER: KILL-001
```

**Evidence to Capture:**
- Pre-narration hash (hex string, 64 chars)
- Post-narration hash (hex string, 64 chars)
- Memory snapshot diff (JSON diff showing changed fields)
- Stack trace (code path that mutated memory)
- Timestamp (ISO 8601 format)

**Evidence Format:**
```json
{
  "kill_switch": "KILL-001",
  "timestamp": "2026-02-10T14:32:15Z",
  "hash_before": "a3f2b8c4...",
  "hash_after": "d9e1c7a2...",
  "diff": {
    "changed_field": "SessionLedgerEntry.facts_added",
    "before": [...],
    "after": [...]
  },
  "stack_trace": "..."
}
```

**Log Destination:** `logs/m1_violations/KILL-001_{timestamp}.json`

**Auto-Action:**
1. HALT narration generation immediately
2. LOG violation with full evidence
3. DISABLE generative narration mode (revert to template-based)
4. REJECT current PR if in CI

**Escalation Path:**
1. **Immediate (T+0min):** Log violation to `logs/m1_violations/`
2. **T+15min:** Agent D notification (automated alert)
3. **T+1hour:** PM (Thunder) notification (if not resolved)
4. **T+24hours:** M1 unlock SUSPENDED (pending PM review)

**Severity:** 🔴 CRITICAL (determinism violated)

---

### KILL-002: Unauthorized Memory Write Detected

**Trigger Signal:** Memory write function called without valid event_id provenance

**Detection Method:**
```
BEFORE memory_write_function(data, event_id=None):
  IF event_id is None:
    TRIGGER: KILL-002

  IF event_id not in event_log:
    TRIGGER: KILL-002

  LOG: "MEMORY_WRITE: event_id={event_id}, data_type={type(data)}"
```

**Evidence to Capture:**
- Write function name (e.g., `SessionLedgerEntry.add_fact()`)
- Data payload (JSON serialization of write data)
- Event ID provided (or `None`)
- Event log check result (exists: True/False)
- Stack trace (code path attempting write)
- Timestamp

**Evidence Format:**
```json
{
  "kill_switch": "KILL-002",
  "timestamp": "2026-02-10T14:32:15Z",
  "write_function": "SessionLedgerEntry.add_fact",
  "event_id": null,
  "event_exists": false,
  "data_payload": {...},
  "stack_trace": "..."
}
```

**Log Destination:** `logs/m1_violations/KILL-002_{timestamp}.json`

**Auto-Action:**
1. REJECT write immediately (raise exception)
2. LOG violation with full evidence
3. HALT PR merge if in CI
4. REQUIRE manual DM confirmation for all subsequent writes

**Escalation Path:**
1. **Immediate (T+0min):** Log violation + reject write
2. **T+15min:** Agent D notification
3. **T+1hour:** PM notification
4. **T+24hours:** M1 unlock SUSPENDED

**Severity:** 🔴 CRITICAL (event sourcing violated)

---

### KILL-003: Hallucination Rate >5%

**Trigger Signal:** Fact extraction validation failure rate exceeds 5% over 100 queries

**Detection Method:**
```
AFTER fact_extraction(narration_text):
  extracted_facts = parse_facts(narration_text)

  FOR fact in extracted_facts:
    validation_result = validate_fact_exists_in_memory(fact)
    LOG: "FACT_VALIDATION: fact={fact}, valid={validation_result}"

  hallucination_rate = (failed_validations / total_validations)

  IF hallucination_rate > 0.05:
    TRIGGER: KILL-003
```

**Evidence to Capture:**
- Total facts extracted (count)
- Failed validations (count + list of hallucinated facts)
- Hallucination rate (percentage)
- Sample hallucinated facts (JSON list, max 10)
- Query context (memory snapshot size, session count)
- Timestamp

**Evidence Format:**
```json
{
  "kill_switch": "KILL-003",
  "timestamp": "2026-02-10T14:32:15Z",
  "total_facts": 100,
  "failed_validations": 7,
  "hallucination_rate": 0.07,
  "sample_hallucinations": [
    {"fact": "Theron betrayed Duke", "valid": false},
    {"fact": "Goblin had 50 HP", "valid": false}
  ],
  "query_context": {
    "memory_size_kb": 45,
    "session_count": 12
  }
}
```

**Log Destination:** `logs/m1_violations/KILL-003_{timestamp}.json`

**Auto-Action:**
1. REDUCE LLM temperature to 0.2 (all operations)
2. LOG violation with sample hallucinations
3. REQUIRE DM review for all extracted facts
4. DISABLE auto-fact-extraction from narration

**Escalation Path:**
1. **Immediate (T+0min):** Log violation + reduce temperature
2. **T+1hour:** Agent D notification
3. **T+24hours:** PM notification (if sustained >24h)
4. **T+1week:** M1 unlock SUSPENDED (if unresolved)

**Severity:** 🟡 MEDIUM (degrades to low-temp mode, but functional)

---

### KILL-004: High-Temperature Query Detected

**Trigger Signal:** Query function called with temperature >0.7

**Detection Method:**
```
BEFORE query_memory(query_text, temperature):
  IF temperature > 0.7:
    TRIGGER: KILL-004

  LOG: "MEMORY_QUERY: temp={temperature}, query_len={len(query_text)}"
```

**Evidence to Capture:**
- Query function name
- Temperature parameter (float)
- Query text (first 200 chars)
- Stack trace (code path using high temp)
- Timestamp

**Evidence Format:**
```json
{
  "kill_switch": "KILL-004",
  "timestamp": "2026-02-10T14:32:15Z",
  "query_function": "query_session_history",
  "temperature": 0.9,
  "query_preview": "Recap session 5...",
  "stack_trace": "..."
}
```

**Log Destination:** `logs/m1_violations/KILL-004_{timestamp}.json`

**Auto-Action:**
1. CLAMP temperature to 0.5 (auto-correction)
2. LOG violation with query preview
3. WARN developer (CI warning, not block)

**Escalation Path:**
1. **Immediate (T+0min):** Log violation + clamp temperature
2. **T+1hour:** Agent D notification (if 3+ occurrences)
3. **T+1week:** PM notification (if sustained pattern)

**Severity:** 🟡 MEDIUM (auto-correctable, low impact)

---

### KILL-005: Invention During Context Overflow

**Trigger Signal:** LLM invents facts when memory exceeds context window and queried data unavailable

**Detection Method:**
```
BEFORE query_memory(query_text):
  IF memory_size > context_window_limit:
    truncated_memory = truncate_memory(memory)
    truncation_flag = True
  ELSE:
    truncation_flag = False

AFTER query_result = llm_query(truncated_memory, query_text):
  IF truncation_flag AND query_result contains facts not in truncated_memory:
    TRIGGER: KILL-005
```

**Evidence to Capture:**
- Memory size (KB)
- Context window limit (KB)
- Truncation flag (True/False)
- Query text
- Query result (invented facts)
- Expected abstention response ("I don't have records for X")
- Timestamp

**Evidence Format:**
```json
{
  "kill_switch": "KILL-005",
  "timestamp": "2026-02-10T14:32:15Z",
  "memory_size_kb": 65,
  "context_limit_kb": 32,
  "truncation_flag": true,
  "query": "Recap session 45",
  "response": "In session 45, Theron fought...",
  "expected_response": "I don't have records for session 45",
  "invented_facts": ["Session 45 events"]
}
```

**Log Destination:** `logs/m1_violations/KILL-005_{timestamp}.json`

**Auto-Action:**
1. DISABLE speculative summarization
2. LOG violation with invented facts
3. AGGRESSIVE truncation (reduce context window further)
4. REQUIRE abstention for all unavailable queries

**Escalation Path:**
1. **Immediate (T+0min):** Log violation + disable speculation
2. **T+1hour:** Agent D notification
3. **T+24hours:** PM notification (if sustained)
4. **T+1week:** M1 unlock SUSPENDED

**Severity:** 🟡 MEDIUM (abstention policy enforceable, but indicates prompt weakness)

---

## 3. Invariant Compliance Checklist

### INV-DET-001: Memory State Immutability During Narration

**Proof of Compliance:**
- ✅ Pre-narration hash logged
- ✅ Post-narration hash logged
- ✅ Hashes match (no diff)
- ✅ No KILL-001 triggers in logs

**Verification Method:**
```bash
# Check last 100 narration calls for hash stability
grep "PRE_NARRATION_HASH\|POST_NARRATION_HASH" logs/m1_runtime.log | tail -200
# Verify all pairs match
```

**Evidence Requirement:** 100 consecutive narration calls with stable hash (no mutations)

---

### INV-DET-002: Event-Sourced Memory Writes Only

**Proof of Compliance:**
- ✅ All memory writes logged with event_id
- ✅ All event_ids validated against event log
- ✅ No KILL-002 triggers in logs

**Verification Method:**
```bash
# Check all memory writes have valid event_id
grep "MEMORY_WRITE" logs/m1_runtime.log | grep "event_id=None"
# Should return 0 results
```

**Evidence Requirement:** 100 consecutive memory writes with valid event_id provenance

---

### INV-DET-003: Temperature Isolation (Query ≤0.5, Narration ≥0.7)

**Proof of Compliance:**
- ✅ Query functions use temperature ≤0.5
- ✅ Narration functions use temperature ≥0.7
- ✅ No KILL-004 triggers in logs

**Verification Method:**
```bash
# Check query temperatures
grep "MEMORY_QUERY" logs/m1_runtime.log | awk '{print $3}' | sort -u
# All values should be ≤0.5

# Check narration temperatures
grep "NARRATION_GENERATION" logs/m1_runtime.log | awk '{print $3}' | sort -u
# All values should be ≥0.7
```

**Evidence Requirement:** 100 consecutive operations with correct temperature isolation

---

### INV-TRUST-001: Authority Provenance Preserved

**Requirement:** Every player-visible mechanical claim must be traceable to BOX computation or explicit citation; otherwise must be labeled non-authoritative.

**Doctrine Reference:** `docs/doctrine/SPARK_LENS_BOX_DOCTRINE.md`

**Proof of Compliance:**
- ✅ All user-facing mechanical output includes provenance tag ([BOX]/[DERIVED]/[NARRATIVE]/[UNCERTAIN])
- ✅ NO SPARK-generated content presented as authoritative without BOX validation
- ✅ NO LENS-layer code invents mechanical claims not present in BOX output
- ✅ All "legal/illegal" rulings sourced from BOX engine with rule citation

**Verification Method:**
```bash
# Check for unprovenienced mechanical claims in user-facing output
grep -r "attack.*hit\|spell.*fail\|action.*illegal" --include="*.py" aidm/ | grep -v "\\[BOX\\]\\|\\[DERIVED\\]"
# Should return 0 results (all mechanical claims must be provenienced)

# Check for SPARK→state writes (forbidden)
grep -r "narration.*WorldState\|llm_output.*state\|generate.*mutate" --include="*.py" aidm/
# Should return 0 results (SPARK cannot mutate state)

# Check for LENS authority invention (forbidden)
grep -r "lens.*legal\\|lens.*permitted\\|lens.*ruling" --include="*.py" aidm/
# Should return 0 results (LENS cannot invent authority)
```

**Evidence Requirement:**
- 100 consecutive user-facing mechanical outputs with provenance tags
- Zero SPARK→state write paths detected in codebase
- Zero LENS authority invention instances

**Trust Failure Indicators:**
- Missing provenance tags on mechanical claims
- SPARK output treated as authoritative without BOX validation
- LENS code adding mechanical claims not sourced from BOX
- "Illegal" rulings without BOX computation or rule citation

**Remediation:**
- Add provenance labeling to all user-facing output pipelines
- Route all mechanical claims through BOX validation
- Remove any SPARK→state write paths
- Ensure LENS only transforms BOX output format, never content authority

**Severity:** 🔴 **CRITICAL** — Trust violations destroy veteran DM confidence permanently

---

### INV-DET-004: Paraphrase Validation Before Memory Write

**Proof of Compliance:**
- ✅ All fact extractions logged with validation result
- ✅ Hallucination rate <5%
- ✅ No KILL-003 sustained triggers

**Verification Method:**
```bash
# Calculate hallucination rate over last 100 validations
grep "FACT_VALIDATION" logs/m1_runtime.log | tail -100 | awk '{sum+=$5} END {print sum/NR}'
# Result should be <0.05
```

**Evidence Requirement:** Hallucination rate <5% over 100 fact extractions

---

### INV-DET-005: Replay Stability (Events Deterministic, Narration May Vary)

**Proof of Compliance:**
- ✅ Event log replay produces identical events (hash stable)
- ✅ Narration text may vary (not deterministic)
- ✅ Mechanical outcomes identical across replays

**Verification Method:**
```bash
# Replay same event log 10 times, hash event outcomes
for i in {1..10}; do
  replay_session --event-log session_5.json --hash-output
done
# All 10 hashes should match (events deterministic)
```

**Evidence Requirement:** 10 replays with identical event hashes, varying narration text

---

## 4. Log/Evidence Retention Rules

### 4.1 Log Destinations

**Runtime Logs:**
- `logs/m1_runtime.log` — All operational logs (hashes, queries, writes, validations)
- `logs/m1_violations/` — Kill switch trigger evidence (JSON files)
- `logs/m1_audit/` — Weekly compliance audit results

**Retention Policy:**
- Runtime logs: 30 days rolling
- Violation logs: Permanent (never delete)
- Audit logs: 1 year

---

### 4.2 Minimum Log Excerpt Format

**For any violation report, capture minimum:**
```json
{
  "kill_switch": "KILL-XXX",
  "timestamp": "ISO 8601",
  "trigger_signal": "brief description",
  "evidence": {
    "before": "...",
    "after": "...",
    "diff": "..."
  },
  "stack_trace": "full stack trace",
  "auto_action_taken": "what system did automatically",
  "escalation_status": "notified Agent D / PM / suspended"
}
```

**Evidence Artifact Locations:**
- Full memory snapshots: `logs/m1_violations/snapshots/{timestamp}_before.json`, `{timestamp}_after.json`
- Stack traces: Embedded in violation JSON
- Query/narration text: First 500 chars in violation JSON

---

## 5. Response Playbook: "What to Do When It Fires"

### 5.1 CRITICAL Kill Switch Triggered (KILL-001, KILL-002)

**Step 1: HALT (Immediate, T+0min)**
- Stop narration generation / memory write immediately
- Reject current PR if in CI
- Log violation with full evidence

**Step 2: NOTIFY (T+15min)**
- Automated alert to Agent D
- Violation summary posted to monitoring channel
- Evidence JSON available for review

**Step 3: DOCUMENT (T+30min)**
- Agent D reviews violation evidence
- Determines root cause (code bug, config error, attack)
- Documents finding in `logs/m1_violations/analysis_{timestamp}.md`

**Step 4: ROLLBACK (T+1hour if unresolved)**
- If violation not resolved within 1 hour:
  - Revert offending PR
  - DISABLE generative narration mode
  - Escalate to PM for review

**Step 5: PM DECISION (T+24hours if unresolved)**
- PM reviews violation + proposed fix
- Approves fix + re-enable OR
- Revokes M1 unlock (rollback to M0)

---

### 5.2 MEDIUM Kill Switch Triggered (KILL-003, KILL-004, KILL-005)

**Step 1: AUTO-CORRECT (Immediate, T+0min)**
- Apply automatic fallback (reduce temperature, disable feature, etc.)
- Log violation with evidence
- Continue operation in degraded mode

**Step 2: MONITOR (T+1hour)**
- Check if violation resolves with fallback
- If resolved → log as resolved, continue monitoring
- If persists → escalate to Agent D

**Step 3: NOTIFY (T+1hour if sustained)**
- Agent D receives notification
- Reviews violation pattern (one-off vs sustained)
- Determines if PM escalation needed

**Step 4: ESCALATE (T+24hours if sustained)**
- If violation sustained >24 hours despite fallback:
  - Notify PM
  - Recommend fix or rollback
  - Provide evidence log

---

## 6. Telemetry Requirements for Agent A

**Agent A MUST implement the following telemetry hooks:**

### 6.1 Hash Logging (INV-DET-001)
```python
# BEFORE narration generation:
logger.info(f"PRE_NARRATION_HASH: {hash(memory_snapshot.to_dict())}")

# AFTER narration generation:
logger.info(f"POST_NARRATION_HASH: {hash(memory_snapshot.to_dict())}")
```

**Requirement:** Hash function MUST be deterministic (same input → same hash)

---

### 6.2 Write Logging (INV-DET-002)
```python
# BEFORE memory write:
def add_fact(data, event_id=None):
    logger.info(f"MEMORY_WRITE: event_id={event_id}, data_type={type(data).__name__}")
    if event_id is None or event_id not in event_log:
        raise KILL_002_Exception("Unauthorized memory write")
```

**Requirement:** All write functions MUST log event_id and validate against event log

---

### 6.3 Temperature Logging (INV-DET-003)
```python
# BEFORE query/narration:
def query_memory(query_text, temperature=0.3):
    logger.info(f"MEMORY_QUERY: temp={temperature}, query_len={len(query_text)}")

def generate_narration(memory_snapshot, temperature=0.8):
    logger.info(f"NARRATION_GENERATION: temp={temperature}, memory_size={len(memory_snapshot)}")
```

**Requirement:** All LLM calls MUST log temperature parameter

---

### 6.4 Fact Validation Logging (INV-DET-004)
```python
# AFTER fact extraction:
for fact in extracted_facts:
    valid = validate_fact_exists_in_memory(fact)
    logger.info(f"FACT_VALIDATION: fact={fact}, valid={valid}")
```

**Requirement:** All fact extractions MUST log validation result (True/False)

---

### 6.5 Overflow Detection Logging (INV-DET-005)
```python
# BEFORE query when memory truncated:
if memory_size > context_window_limit:
    logger.info(f"MEMORY_TRUNCATION: size={memory_size}, limit={context_window_limit}")
    truncation_flag = True
```

**Requirement:** All context window overflows MUST be logged with truncation flag

---

## 7. Enforcement Cadence

### 7.1 Continuous Monitoring (Runtime)

**Every narration call:**
- Log pre/post hash
- Assert hash stability
- Trigger KILL-001 if violated

**Every memory write:**
- Log event_id
- Validate event_id exists
- Trigger KILL-002 if violated

**Every LLM call:**
- Log temperature
- Clamp if >0.7 for queries
- Trigger KILL-004 if high-temp query

---

### 7.2 Periodic Audits

**Weekly (Agent D):**
- Review `logs/m1_runtime.log` for patterns
- Calculate hallucination rate over week
- Generate compliance report (INV-DET-001 through INV-DET-005)

**Bi-Weekly:**
- UX acceptance criteria smoke test (5 CRITICAL criteria)

**Monthly:**
- Full UX acceptance test (all 15 criteria)

**Pre-Ship:**
- Complete M1 certification audit (all invariants + all criteria)

---

## 8. Success Criteria

**Monitoring spine is OPERATIONAL when:**
- ✅ All 5 kill switches have detection code paths
- ✅ All 5 invariants have proof-of-compliance verification methods
- ✅ Telemetry requirements documented for Agent A
- ✅ Response playbook exists (HALT → notify → document → rollback)
- ✅ Log retention policy defined (30 days runtime, permanent violations)

**Monitoring spine is EFFECTIVE when:**
- ✅ KILL-001 fires on actual memory mutation (tested)
- ✅ KILL-002 fires on unauthorized write (tested)
- ✅ Hallucination rate calculated correctly over 100 samples
- ✅ Temperature violations detected and clamped
- ✅ Evidence JSON captures sufficient detail for root cause analysis

---

## 9. Compliance Statement

**Agent D operated in GOVERNANCE-ONLY mode:**
- ✅ NO production code written (monitoring spec only)
- ✅ NO schema changes (log formats only)
- ✅ NO policy authored (GAP-POL items unchanged)
- ✅ Monitoring specification only (telemetry requirements, detection methods, response procedures)

**Deliverable:** M1_MONITORING_PROTOCOL.md (single source of truth for violation detection)

**Reporting Line:** Agent D (Governance) → PM (Thunder)

---

**END OF M1 MONITORING PROTOCOL**

**Date:** 2026-02-10
**Agent:** Agent D (Research Orchestrator)
**Phase:** M1 Monitoring Spine Setup
**Status:** ✅ COMPLETE (monitoring protocol operational)
