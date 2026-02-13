# RQ-LENS-002: Contradiction Surface Mapping --- Empirical Spark Output Analysis

**Domain:** Lens<>Spark Protocol --- Contradiction Detection
**Status:** DRAFT
**Filed:** 2026-02-12
**Gate:** Informs ContradictionChecker implementation in RQ-LENS-SPARK-001 Phase 1
**Prerequisite:** RQ-LENS-SPARK-001 (Context Orchestration Sprint), WO-032, WO-041, WO-046

---

## 1. Thesis

The contradiction taxonomy and keyword dictionaries defined in RQ-LENS-SPARK-001
Deliverable 4 were designed from first principles. They enumerate what Spark
*could* say that conflicts with a NarrativeBrief truth frame: defeat keywords when
`target_defeated=False`, hit keywords when `action_type=attack_miss`, severity
inflation and deflation. The dictionaries are plausible. They are not validated.

LLMs are unpredictable narrators. Three failure modes are invisible without
empirical measurement:

1. **False negatives.** Spark produces a contradiction that no keyword dictionary
   catches. Example: "the creature's eyes go dark" implies defeat without using
   any word in `DEFEAT_KEYWORDS`. The dictionary passes. The player notices.
   Trust is lost.

2. **False positives.** A keyword fires on narration that is not actually a
   contradiction. Example: "the goblin dodges" appears in `MISS_KEYWORDS` but
   the brief says `action_type=attack_miss` --- the narration is *correct*.
   A false positive means unnecessary retries, template fallbacks, and wasted
   latency.

3. **Unknown contradiction classes.** Spark invents narrative elements that
   don't fit any existing class. Example: Spark describes environmental effects
   ("the table splinters"), emotional states ("the goblin is terrified"), or
   tactical consequences ("the party is now flanked") that have no
   NarrativeBrief field to check against. These are not Class A, B, or C ---
   they are a potential Class D that the taxonomy does not account for.

Building a ContradictionChecker without this data means tuning blind. Keyword
thresholds will be arbitrary. Precision and recall will be unmeasured. The <1%
contradiction rate target in RQ-LENS-SPARK-001's exit gate will be unjustifiable
because the detector itself is unvalidated.

This research provides the ground truth. It runs controlled experiments against
scripted NarrativeBriefs, collects actual Spark outputs, classifies
contradictions by hand, and builds a confusion matrix for keyword-based
detection. The result is either validation of the existing dictionaries or
concrete evidence for revision.

---

## 2. Methodology

### 2.1 Scripted NarrativeBrief Construction

Create a set of **scripted NarrativeBriefs** covering all `action_type` /
`severity` / `target_defeated` combinations relevant to combat narration.
Target: 30--40 distinct brief configurations.

Each brief is a fully-populated `NarrativeBrief` instance (as defined in
`aidm/lens/narrative_brief.py`) with known, fixed field values. No field is
left to default unless that default is the test condition.

Briefs are organized into categories (see Section 3: Scripted Brief Matrix).

### 2.2 Narration Generation

For each scripted brief, generate narrations using available Spark backends:

| Backend | Purpose |
|---|---|
| **Local LlamaCpp model** (via `SparkAdapter`) | Primary test subject --- actual LLM output |
| **Template fallback** (via `NarrationTemplates`) | Control group --- known-correct narration for comparison |

Generate **N = 10 narrations per brief** at the standard narration temperature
of **0.8** (per LLM-002 lower bound of 0.7). This produces 300--400 total
narrations for analysis.

Each narration is generated with a full prompt pipeline:
- `DMPersona` system prompt (WO-041, already integrated)
- NarrativeBrief truth frame (WO-032, already integrated)
- `GrammarShield` mechanical assertion pre-filtering (already integrated)

No PromptPack is required --- this research runs before PromptPack exists. The
existing `GuardedNarrationService` prompt construction path is sufficient.

### 2.3 Manual Classification

For each generated narration, a human annotator classifies:

1. **Contradiction present?** (yes / no)
2. **Contradiction class** (A: entity state, B: outcome, C: continuity, or NOVEL)
3. **Contradiction subtype** (e.g., "defeat keyword in non-defeat context",
   "severity inflation", "wrong weapon name")
4. **Keyword dictionary result:**
   - Did the theoretical keyword dictionary **fire** on this narration?
   - If it fired, was it a **true positive** (actual contradiction) or
     **false positive** (keyword matched but narration was correct)?
   - If it did not fire, was this a **true negative** (no contradiction) or
     **false negative** (contradiction present, keyword missed)?
5. **Specific text span** that constitutes the contradiction (quoted)
6. **Novel pattern?** If the contradiction does not fit any existing keyword
   list or class, describe the pattern

### 2.4 Analysis

Build a **confusion matrix** for each keyword dictionary:

```
                    Actual Contradiction
                    Yes         No
Dictionary  Fire    TP          FP
            Silent  FN          TN
```

Compute precision, recall, and F1 for:
- `DEFEAT_KEYWORDS` (against briefs where `target_defeated` is the test variable)
- `HIT_KEYWORDS` (against briefs where `action_type` hit/miss is the test variable)
- `MISS_KEYWORDS` (same)
- `SEVERITY_INFLATION` (against briefs where `severity` is the test variable)
- `SEVERITY_DEFLATION` (same)

Aggregate contradiction rate by class across all briefs and all narrations.

---

## 3. Scripted Brief Matrix

### 3.1 Core Action/Outcome Briefs

| # | Brief Category | `action_type` | Key Fields | What to Check |
|---|---|---|---|---|
| 1 | Hit, not defeated | `attack_hit` | `target_defeated=False`, `severity=moderate` | No defeat keywords in output |
| 2 | Hit, defeated | `attack_hit` | `target_defeated=True`, `severity=lethal` | Defeat keywords MUST appear |
| 3 | Miss | `attack_miss` | `severity=minor` | No hit keywords in output |
| 4 | Critical hit | `critical` | `severity=devastating` | Severity language matches |
| 5 | Spell hit, not defeated | `spell_damage_dealt` | `target_defeated=False`, `severity=severe` | No defeat keywords |
| 6 | Spell, no effect | `spell_no_effect` | --- | No hit/damage keywords |
| 7 | Healing | `spell_healed` | --- | No damage/defeat keywords |
| 8 | Maneuver success | `trip_success` | `condition_applied=prone` | Target described as prone |
| 9 | Maneuver failure | `trip_failure` | --- | Target NOT described as prone |
| 10 | Bull rush success | `bull_rush_success` | `condition_applied=None` | Target described as pushed back |
| 11 | Bull rush failure | `bull_rush_failure` | --- | Target NOT described as moved |
| 12 | Grapple success | `grapple_success` | `condition_applied=grappled` | Grapple language present |
| 13 | Grapple failure | `grapple_failure` | --- | No grapple-applied language |
| 14 | Disarm success | `disarm_success` | --- | Weapon loss described |
| 15 | Disarm failure | `disarm_failure` | --- | No weapon loss described |

### 3.2 Severity Gradient Briefs

| # | Brief Category | `action_type` | `severity` | `target_defeated` | What to Check |
|---|---|---|---|---|---|
| 16 | Minor hit | `attack_hit` | `minor` | `False` | No devastating/brutal/crushing language |
| 17 | Moderate hit | `attack_hit` | `moderate` | `False` | No lethal/fatal language |
| 18 | Severe hit | `attack_hit` | `severe` | `False` | No minor/scratches language; no defeat keywords |
| 19 | Devastating hit | `attack_hit` | `devastating` | `False` | No minor language; no defeat keywords |
| 20 | Lethal hit, defeated | `attack_hit` | `lethal` | `True` | Defeat keywords present; no "scratches"/"minor" |

### 3.3 Context Variation Briefs

| # | Brief Category | Key Variation | What to Check |
|---|---|---|---|
| 21 | Named weapon (longsword) | `weapon_name=longsword` | Output references longsword, not another weapon |
| 22 | Named weapon (greataxe) | `weapon_name=greataxe` | Output references greataxe, not another weapon |
| 23 | Named spell (fireball) | `spell_name=fireball`, `action_type=spell_damage_dealt` | Output references fireball, not another spell |
| 24 | Named spell (cure light wounds) | `spell_name=cure light wounds`, `action_type=spell_healed` | Output references healing, not damage |
| 25 | Specific actor name | `actor_name=Thorin Ironforge` | Output uses correct actor name |
| 26 | Specific target name | `target_name=Grukk the Ogre` | Output uses correct target name |
| 27 | Damage type: fire | `damage_type=fire` | Output references fire/flame/burn, not slashing/cold |
| 28 | Damage type: slashing | `damage_type=slashing` | Output references cutting/slashing, not fire/acid |
| 29 | Scene: dungeon corridor | `scene_description=a narrow dungeon corridor lit by flickering torches` | No forest/outdoor language |
| 30 | Scene: forest clearing | `scene_description=a sun-dappled forest clearing` | No dungeon/underground language |

### 3.4 Continuity Briefs (Class C)

These require `previous_narrations` to be populated with specific text:

| # | Brief Category | Setup | What to Check |
|---|---|---|---|
| 31 | Defeated entity reference | `previous_narrations` includes "the goblin collapses"; current brief involves same goblin acting | Spark should not describe goblin as alive/acting |
| 32 | Location consistency | `previous_narrations` set in dungeon; `scene_description=dungeon corridor` | No forest/outdoor references |
| 33 | Wrong weapon carryover | `previous_narrations` mention longsword; current brief `weapon_name=shortbow` | Output uses shortbow, not longsword |
| 34 | Wrong actor carryover | `previous_narrations` mention Aldric; current brief `actor_name=Thorin` | Output uses Thorin, not Aldric |

### 3.5 Edge Case Briefs

| # | Brief Category | Setup | What to Check |
|---|---|---|---|
| 35 | Concealment miss | `action_type=concealment_miss` | No hit language; concealment referenced |
| 36 | Spell resisted | `action_type=spell_resisted` | No damage/effect language |
| 37 | Condition removed | `condition_removed=prone`, `action_type=condition_removed` | Target described as standing/recovering |
| 38 | AoO interrupt | `action_type=action_aborted_by_aoo` | Interruption described; original action NOT completed |
| 39 | Full attack complete | `action_type=full_attack_complete`, `target_defeated=False` | Multiple attacks referenced; no defeat |
| 40 | Full attack, target defeated | `action_type=full_attack_complete`, `target_defeated=True` | Multiple attacks and defeat |

---

## 4. Metrics to Collect

### 4.1 Primary Metrics

| Metric | Definition | How Measured |
|---|---|---|
| **Contradiction rate (overall)** | % of narrations containing at least one contradiction of any class | Manual classification |
| **Contradiction rate (Class A)** | % of narrations with entity state contradictions | Manual classification |
| **Contradiction rate (Class B)** | % of narrations with outcome contradictions | Manual classification |
| **Contradiction rate (Class C)** | % of narrations with continuity contradictions | Manual classification on briefs 31--34 |

### 4.2 Keyword Detection Quality

| Metric | Definition | Formula |
|---|---|---|
| **Precision (per dictionary)** | Fraction of keyword fires that are true contradictions | TP / (TP + FP) |
| **Recall (per dictionary)** | Fraction of actual contradictions caught by keywords | TP / (TP + FN) |
| **F1 score (per dictionary)** | Harmonic mean of precision and recall | 2 * (P * R) / (P + R) |
| **False positive rate** | Fraction of clean narrations where keyword fires | FP / (FP + TN) |
| **False negative rate** | Fraction of contradictions missed by keyword | FN / (FN + TP) |

### 4.3 Discovery Metrics

| Metric | Definition | How Measured |
|---|---|---|
| **Novel contradiction patterns** | Contradictions not covered by any existing keyword list | Count from NOVEL classifications |
| **Novel pattern frequency** | % of all contradictions that are novel | Novel / total contradictions |
| **Emergent keyword candidates** | New keywords discovered from novel patterns | Extracted from text spans |

### 4.4 Optional Metrics

| Metric | Definition | Condition |
|---|---|---|
| **Model comparison** | Contradiction rate delta between models | If multiple Spark models available |
| **Temperature sensitivity** | Contradiction rate at 0.7, 0.8, 0.9 | If time permits after primary analysis |
| **Brief difficulty ranking** | Which brief categories produce the most contradictions | Sorted by contradiction rate per category |

---

## 5. Expected Outputs

### 5.1 Validated Keyword Dictionaries

Refined versions of `DEFEAT_KEYWORDS`, `HIT_KEYWORDS`, `MISS_KEYWORDS`,
`SEVERITY_INFLATION`, and `SEVERITY_DEFLATION` with:
- Keywords confirmed by empirical evidence (true positives in data)
- Keywords removed due to unacceptable false positive rate
- New keywords added from novel pattern discovery

### 5.2 Novel Contradiction Pattern Catalog

A documented list of contradiction patterns not anticipated by the original
taxonomy. Each entry includes:
- Pattern description
- Example narration text
- NarrativeBrief field(s) contradicted
- Suggested detection method (keyword, regex, structural check)
- Proposed class assignment (A/B/C or new class)

### 5.3 Confusion Matrices

One confusion matrix per keyword dictionary, built from the full dataset of
300+ classified narrations.

### 5.4 Detection Threshold Recommendations

Based on precision/recall tradeoffs:
- Recommended minimum recall per class (how many contradictions must be caught)
- Acceptable precision per class (how many false alarms are tolerable)
- Recommended response policy per class (retry vs. template fallback vs. annotate)

These directly feed into ContradictionChecker configuration in RQ-LENS-SPARK-001
Phase 1.

### 5.5 Baseline Contradiction Rate

The measured contradiction rate per model and per brief category. This becomes
the baseline against which the RQ-LENS-SPARK-001 exit gate (<1%) is evaluated.
If the baseline is already <1% without a ContradictionChecker, the checker's
value is in preventing regression. If the baseline is >1%, the checker's
value is in active filtering.

---

## 6. Infrastructure Requirements

| Component | Source | Status |
|---|---|---|
| **SparkAdapter** (LlamaCpp backend) | `aidm/spark/spark_adapter.py` | Integrated |
| **NarrativeBrief** construction | `aidm/lens/narrative_brief.py` | Integrated (WO-032, WO-046B) |
| **DMPersona** system prompt | `aidm/narration/narrator.py` + WO-041 | Integrated |
| **GrammarShield** mechanical pre-filter | `aidm/spark/grammar_shield.py` | Integrated |
| **GuardedNarrationService** | `aidm/narration/guarded_narration_service.py` | Integrated (M1--M3) |
| **NarrationTemplates** (control group) | `aidm/narration/narrator.py` | Integrated (55+ templates) |
| **Local LLM model** | User-provided GGUF via LlamaCpp | Required for LLM path |

**No new dependencies required.** All infrastructure exists. The research
requires only scripted brief construction (test fixtures) and a classification
spreadsheet.

---

## 7. Scope Boundaries --- What This Does NOT Do

| Out of Scope | Reason |
|---|---|
| **Implement ContradictionChecker** | That is RQ-LENS-SPARK-001 Phase 1. This research informs the implementation. |
| **Run the 100-turn evaluation harness** | That is RQ-LENS-SPARK-001 Phase 3. This research provides data for harness calibration. |
| **Test multi-turn coherence** | Requires PromptPack and retrieval policy (RQ-LENS-SPARK-001 Deliverables 1 and 2). |
| **Test NPC dialogue or non-combat narration** | Deferred. `TaskType.NARRATE_DIALOGUE` is reserved but not implemented. |
| **Implement semantic contradiction detection** | LLM-based detection is explicitly out of scope per RQ-LENS-SPARK-001 scope boundaries. |
| **Modify NarrativeBrief schema** | Brief schema is stable (WO-032/WO-046B). This research reads it, does not change it. |
| **Modify GrammarShield** | GrammarShield handles mechanical assertions. This research covers the gap above it. |

Results are **observational**. They inform implementation but do not commit to
specific code changes. If the data shows the keyword dictionaries are adequate,
implementation proceeds as planned. If the data shows they are inadequate, the
dictionaries are revised before implementation begins.

---

## 8. Success Criteria

| Criterion | Threshold |
|---|---|
| Distinct NarrativeBrief configurations tested | >= 30 |
| Narrations per brief | >= 10 |
| Total narrations analyzed | >= 300 |
| Keyword precision measured per dictionary | All 5 dictionaries |
| Keyword recall measured per dictionary | All 5 dictionaries |
| Novel patterns documented | All discovered patterns cataloged |
| Confusion matrices produced | One per keyword dictionary |
| Recommendation on dictionary completeness | One of: sufficient / needs expansion / needs restructuring |
| Baseline contradiction rate reported | Per model, per brief category |

The research is complete when all criteria above are met. The recommendation
on dictionary completeness is the primary deliverable --- it determines whether
RQ-LENS-SPARK-001 Phase 1 proceeds with the current dictionaries or pauses
for dictionary revision.

---

## 9. Relationship to Other Work

### Feeds Into

| Target | How |
|---|---|
| **RQ-LENS-SPARK-001 Deliverable 4** (ContradictionChecker) | Validated keyword dictionaries, precision/recall targets, novel pattern catalog |
| **RQ-LENS-SPARK-001 Deliverable 5** (Evaluation Harness) | Baseline contradiction rate, brief difficulty ranking for scenario design |
| **KILL-007** (contradiction threshold kill switch, optional) | Empirical threshold for when contradiction rate warrants kill switch |

### Builds On

| Source | What It Provides |
|---|---|
| **RQ-LENS-SPARK-001** | Contradiction taxonomy (Class A/B/C), keyword dictionary drafts, ContradictionChecker API spec |
| **WO-032** | NarrativeBrief schema and assembly pipeline |
| **WO-041** | DMPersona system prompt for Spark generation |
| **WO-046** | Box event contracts (typed STP events feeding NarrativeBrief) |

### Related but Independent

| Component | Relationship |
|---|---|
| **GrammarShield** (`aidm/spark/grammar_shield.py`) | Existing mechanical assertion detection --- this research covers the gap GrammarShield does not (fictional state contradictions vs. numeric leaks) |
| **RQ-BOX-002** (RAW Silence Catalog) | Independent --- Box-layer rules gap analysis, no overlap with Spark output validation |
| **RQ-BOX-003** (Object Identity) | Independent --- Box-layer entity identity, no overlap with narration contradiction |
| **GuardedNarrationService** | Existing kill switch infrastructure (KILL-001 through KILL-006) remains unchanged; this research may recommend KILL-007 |

---

## 10. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Local LLM unavailable or too slow for 300+ generations | Low | Blocks research | Reduce N to 5 per brief (minimum viable), or use template-only control run to validate methodology |
| Manual classification is subjective | Medium | Reduces reliability of precision/recall numbers | Define classification rubric with examples before annotation begins; consider two-annotator agreement on a subset |
| Novel patterns overwhelm taxonomy | Low | Delays ContradictionChecker design | Cap novel catalog at patterns occurring in >2% of narrations; defer rare patterns to v2 |
| Keyword dictionaries perform well and research feels unnecessary | Low | N/A | Positive outcome --- validates the design. Baseline rate still needed for exit gate |
| Spark model produces near-zero contradictions at temperature 0.8 | Medium | Research provides weak signal | Run temperature 0.9 subset to stress the model; consider adversarial prompt variants |
