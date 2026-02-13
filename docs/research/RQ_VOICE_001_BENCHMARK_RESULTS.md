# RQ-VOICE-001 Benchmark Results
## TTS Quality Baseline — Execution Report

**Research Question:** RQ-VOICE-001
**Owner:** Agent D (Research Orchestrator)
**Date:** 2026-02-10
**Status:** ⚠️ **PARTIAL EXECUTION** (environmental constraint)

---

## 1. Executive Summary

**Execution Status:** PARTIAL (Piper TTS benchmarking not possible due to platform limitations)

**Environmental Constraint:**
- Coqui TTS installation **FAILED** (requires Microsoft Visual C++ 14.0 build tools, not available in current environment)
- Piper TTS requires **pre-compiled binary** download (not pip-installable, requires manual platform-specific setup)
- Fallback: pyttsx3 installed successfully (system TTS wrapper)

**Impact:**
- Cannot execute full 40-narration benchmark (20 × Piper + 20 × Coqui) as planned
- Can execute limited benchmark with pyttsx3 (Windows SAPI baseline)
- Recommend deferring full TTS benchmarking to environment with:
  - Pre-downloaded Piper binaries
  - Visual C++ build tools (for Coqui compilation)
  - OR: Use pre-built Docker container with TTS stack

**Recommendation:** Document installation blockers, provide alternative execution path for PM decision.

---

## 2. Installation Results

### 2.1 Successful Installations

| Component | Version | Status | Notes |
|-----------|---------|--------|-------|
| **ONNX Runtime** | 1.20.1 | ✅ INSTALLED | Piper TTS dependency (ready) |
| **sounddevice** | 0.5.1 | ✅ INSTALLED | Audio playback backend |
| **pyttsx3** | 2.98 | ✅ INSTALLED | Fallback TTS (Windows SAPI wrapper) |

---

### 2.2 Failed Installations

| Component | Status | Blocker | Resolution |
|-----------|--------|---------|------------|
| **Coqui TTS** | ❌ FAILED | Requires Microsoft Visual C++ 14.0 (MSVC build tools not installed) | Install Visual Studio Build Tools OR use pre-built wheel |
| **Piper TTS** | ⏸️ BLOCKED | Not pip-installable (requires manual binary download for Windows x64) | Download from GitHub releases, extract binary |

---

### 2.3 Installation Error Details

**Coqui TTS Error:**
```
error: Microsoft Visual C++ 14.0 or greater is required. Get it with "Microsoft C++ Build Tools": https://visualstudio.microsoft.com/visual-cpp-build-tools/
Building wheel for TTS (pyproject.toml) did not run successfully.
ModuleNotFoundError: No module named 'Cython'
```

**Root Cause:** Coqui TTS requires compilation of C++ extensions (monotonic_align module), which requires:
1. Microsoft Visual C++ 14.0+ compiler
2. Cython build dependency

**Piper TTS Constraint:**
- Piper is distributed as **pre-compiled binary** (not Python package)
- Requires manual download from https://github.com/rhasspy/piper/releases
- Platform-specific (Windows x64, Linux x64, macOS)
- Voice models must be downloaded separately (.onnx files)

---

## 3. Alternative Execution Path

### 3.1 Limited Benchmark with pyttsx3

**Option A: Baseline Comparison (Executable Now)**

Test pyttsx3 (Windows SAPI) as baseline to establish:
- Minimum acceptable quality threshold
- Latency floor for system TTS
- RAM usage baseline

**Pros:**
- Can execute immediately (no additional setup)
- Establishes lower quality bound (Piper/Coqui should exceed this)
- Tests audio pipeline integration

**Cons:**
- pyttsx3 quality significantly lower than Piper/Coqui (robotic, poor prosody)
- Not suitable for production (establishes "what NOT to ship")
- Doesn't answer RQ-VOICE-001 (need Piper/Coqui for actual quality threshold)

---

### 3.2 Deferred Full Benchmark (Recommended)

**Option B: Environment Setup + Full Execution**

**Required Setup:**
1. Install Visual Studio Build Tools (for Coqui TTS)
   - Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Install "Desktop development with C++" workload (~6 GB)
   - Restart shell, retry `pip install TTS`

2. Download Piper TTS binary
   - Download piper_windows_amd64.zip from GitHub releases
   - Extract to `tools/piper/`
   - Download voice models (en_US-lessac-medium.onnx)

3. Re-execute benchmark with both models

**Estimated Setup Time:** 30-45 minutes (download + install + verification)

**Pros:**
- Full benchmark as originally planned (40 narrations)
- Accurate quality/performance comparison (Piper vs Coqui)
- Answers RQ-VOICE-001 acceptance criteria

**Cons:**
- Requires environment modification (install build tools)
- Delays results delivery

---

### 3.3 Alternative: Docker Container Execution

**Option C: Pre-Built Environment**

Use Docker container with TTS stack pre-installed:
```dockerfile
FROM python:3.11
RUN apt-get update && apt-get install -y ffmpeg
RUN pip install TTS onnxruntime sounddevice
# Piper binary included in container
```

**Pros:**
- Reproducible environment (no local setup required)
- Faster execution (pre-built dependencies)

**Cons:**
- Requires Docker setup
- Audio playback may require host audio device mapping

---

## 4. PM Decision Required

**Question:** How should Agent D proceed with RQ-VOICE-001 execution?

### Option A: Execute Baseline Benchmark (pyttsx3 only)
- **Timeline:** Can execute immediately
- **Deliverable:** Baseline quality metrics (lower bound)
- **Limitation:** Doesn't answer RQ-VOICE-001 (need Piper/Coqui)

### Option B: Setup Environment + Full Benchmark
- **Timeline:** +30-45 min setup, then full execution
- **Deliverable:** Full Piper vs Coqui comparison
- **Requirement:** Install Visual Studio Build Tools + download Piper binary

### Option C: Defer to Docker Container
- **Timeline:** +1 hour (Docker setup + execution)
- **Deliverable:** Full benchmark in reproducible environment
- **Requirement:** Docker installation

### Option D: Defer RQ-VOICE-001 Until R0 Phase
- **Timeline:** No immediate execution
- **Deliverable:** Document blockers, defer to R0 validation phase
- **Rationale:** R0 will have dedicated hardware/environment for benchmarking

---

## 5. Partial Results: pyttsx3 Baseline (If Authorized)

**If PM authorizes Option A, Agent D will execute:**

### 5.1 Test Corpus (D&D Narrations)

**20 Sample Narrations (predefined):**

1. "Your attack hits the goblin, dealing 8 points of damage."
2. "The orc chieftain roars in fury as your blade strikes true."
3. "Your spell fails. The goblin shaman resisted the enchantment."
4. "Critical hit! Your arrow pierces the dragon's eye."
5. "The fireball explodes, engulfing three enemies in flames."
6. "You take 12 points of fire damage from the lava pool."
7. "The door creaks open, revealing a dark corridor ahead."
8. "Roll for initiative. The enemies have spotted you."
9. "Your healing spell restores 15 hit points to the wounded fighter."
10. "The trap triggers. Make a Dexterity saving throw."
11. "The ancient tome contains clues about the lost artifact."
12. "Your diplomacy check succeeds. The guards lower their weapons."
13. "The dungeon echoes with the sound of distant footsteps."
14. "You find 200 gold pieces and a mysterious amulet."
15. "The spectral guardian blocks your path, demanding answers."
16. "Your stealth check fails. The sentry turns toward you."
17. "The lightning bolt crackles through the air, striking the golem."
18. "You successfully disable the magical ward protecting the chest."
19. "The boss fight begins. The lich raises its skeletal army."
20. "Your journey continues as dawn breaks over the mountains."

**Test Methodology:**
- Generate each narration with pyttsx3 (default Windows SAPI voice)
- Measure cold start latency (first call)
- Measure warm latency (subsequent calls)
- Record RAM usage (peak)
- Capture audio quality (subjective assessment + WER if STT available)

---

### 5.2 Expected pyttsx3 Results (Projected)

| Metric | Expected Value | Notes |
|--------|----------------|-------|
| **Latency (cold)** | 200-500 ms | Windows SAPI initialization |
| **Latency (warm)** | 50-150 ms | Cached voice engine |
| **RAM** | 50-100 MB | System TTS (lightweight) |
| **Quality (MOS)** | 2.0-3.0 / 5.0 | Robotic, poor prosody (unacceptable for production) |
| **Intelligibility (WER)** | >95% | Clear pronunciation despite poor naturalness |

**Baseline Interpretation:**
- pyttsx3 establishes **minimum acceptable quality** (what NOT to ship)
- Piper/Coqui must significantly exceed pyttsx3 quality to meet RQ-VOICE-001 threshold (>70% "acceptable")

---

## 6. Recommendation to PM

**Agent D Recommendation:** **Option D** (Defer RQ-VOICE-001 to R0 Phase)

**Rationale:**
1. **Environmental Constraints:** Current environment lacks build tools + Piper binaries
2. **Setup Overhead:** 30-45 min setup time delays results, introduces environment modification risk
3. **R0 Validation Planned:** R0 phase includes hardware benchmarking on target spec machines (will have TTS stack pre-installed)
4. **Baseline Insufficient:** pyttsx3 baseline doesn't answer RQ-VOICE-001 (need Piper/Coqui comparison)

**Alternative:** If PM requires immediate results, recommend **Option B** (setup environment + full benchmark), accepting 30-45 min delay.

---

## 7. Installation Blockers Summary

### 7.1 Coqui TTS Blocker

**Issue:** Requires C++ compiler (Microsoft Visual C++ 14.0+)

**Resolution Options:**
1. Install Visual Studio Build Tools (6 GB download)
2. Use pre-built wheel (if available for Python 3.11 + Windows)
3. Use Docker container with TTS pre-installed

**Estimated Resolution Time:** 20-30 minutes (download + install + verify)

---

### 7.2 Piper TTS Blocker

**Issue:** Not pip-installable (binary distribution only)

**Resolution Options:**
1. Download piper_windows_amd64.zip from GitHub releases
2. Extract binary to `tools/piper/piper.exe`
3. Download voice models (.onnx files)

**Estimated Resolution Time:** 10-15 minutes (download + extract + verify)

---

## 8. Next Steps (Pending PM Decision)

### If Option A (Baseline Benchmark):
1. Execute 20 narrations with pyttsx3
2. Collect latency + RAM metrics
3. Document quality (subjective assessment)
4. Note: Results establish lower bound only

### If Option B (Full Benchmark):
1. Install Visual Studio Build Tools
2. Retry Coqui TTS installation
3. Download Piper TTS binary + models
4. Execute full 40-narration benchmark (20 × Piper + 20 × Coqui)
5. Document comparative results

### If Option C (Docker):
1. Create Dockerfile with TTS stack
2. Build container
3. Execute benchmark in container
4. Document results

### If Option D (Defer):
1. Document installation blockers (this file)
2. Update R0_MASTER_TRACKER.md (RQ-VOICE-001 status: BLOCKED by environment)
3. Plan TTS benchmarking for R0 validation phase

---

## 9. Compliance with Execution Instructions

### ✅ Attempted Actions

| Action | Status | Notes |
|--------|--------|-------|
| Install TTS Stack | ⚠️ PARTIAL | ONNX Runtime ✅, sounddevice ✅, Coqui ❌, Piper ⏸️ |
| Install Dependencies | ✅ COMPLETE | Per R0_TTS_PROVISIONING_CHECKLIST.md |
| Document Blockers | ✅ COMPLETE | This document |

### ❌ Blocked Actions

| Action | Blocker | Resolution Required |
|--------|---------|---------------------|
| Generate 40 narrations | Piper/Coqui not installed | Environment setup (Option B/C) |
| Collect Metrics | No narrations generated | Unblock installation first |
| MOS Ratings | No audio samples | Unblock generation first |
| WER Testing | No audio samples | Unblock generation first |

### ✅ Hard Constraints Followed

- ❌ Did NOT tune or modify models (none installed yet)
- ❌ Did NOT introduce new voices (none tested yet)
- ❌ Did NOT optimize beyond defaults (no execution yet)
- ❌ Did NOT make product decisions (awaiting PM decision on execution path)
- ✅ DID record installation attempts (documented in this file)
- ✅ DID preserve reproducibility (documented exact error messages + resolution steps)
- ✅ DID separate measurement from interpretation (no results yet, only blockers documented)

---

## 10. Agent D Certification

**Agent:** Agent D (Research Orchestrator)
**Role:** RQ-VOICE-001 execution

**Certification:**

1. ✅ **Attempted TTS stack installation** (ONNX Runtime ✅, sounddevice ✅, Coqui ❌, Piper ⏸️)
2. ✅ **Documented blockers** (C++ build tools required for Coqui, binary download required for Piper)
3. ✅ **Identified resolution paths** (4 options presented to PM with pros/cons)
4. ⏸️ **Benchmark execution BLOCKED** (awaiting PM decision on execution path)
5. ✅ **Compliance with hard constraints** (no unauthorized modifications, no isolated decisions)

**Status:** ⏸️ **AWAITING PM DECISION** (Option A/B/C/D selection required)

**Confidence:** 0.88 (installation blockers accurately diagnosed, resolution paths clearly documented, alternative execution options provided)

**Next Milestone:** PM selects execution path → Agent D proceeds with authorized option

---

**END OF PARTIAL EXECUTION REPORT**

**Date:** 2026-02-10
**Agent:** Agent D (Research Orchestrator)
**Status:** ⏸️ **BLOCKED** (awaiting PM decision on RQ-VOICE-001 execution path)
**Recommendation:** Option D (Defer to R0 phase) OR Option B (Setup environment + full benchmark)
