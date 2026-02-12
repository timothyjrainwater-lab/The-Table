# Research Finding Schema — RAW Silence & Ambiguity Catalog

**Version:** 1.0
**Date:** 2026-02-12
**Authority:** PM (Opus) + PO (Thunder)
**Purpose:** Standardized format for cataloging RAW silences, ambiguities, and contradictions discovered through research sprints.

---

## Finding Record Format

Every research finding from FAQ parsing, community mining, Skip Williams articles, Pathfinder delta analysis, or errata review must conform to this schema.

```
Finding ID: RQ-<domain>-<sequence>-F-<number>
    Format: RQ-BOX-002-F-0001 (first finding from RQ-BOX-002)
            RQ-BOX-002-A-F-0001 (first finding from community survey sub-sprint)

Source: <document, page, URL, or article reference>
Source Authority: OFFICIAL_FAQ | OFFICIAL_ERRATA | DESIGNER_INTENT | COMMUNITY_CONSENSUS | COMMUNITY_DISPUTED
    OFFICIAL_FAQ      — WotC FAQ PDF (June 2008 final)
    OFFICIAL_ERRATA   — PHB/DMG/MM errata PDFs
    DESIGNER_INTENT   — Skip Williams "Rules of the Game", Sage Advice columns
    COMMUNITY_CONSENSUS — EN World, GitP, RPGStackExchange with strong majority agreement
    COMMUNITY_DISPUTED  — Active community debate, no consensus

Category: EQUIPMENT_STORAGE | MOVEMENT_TERRAIN | SPELLCASTING_TARGETING |
          COMBAT_INTERACTIONS | ENVIRONMENTAL_PHYSICS | SOCIAL_NPC |
          OBJECT_IDENTITY | MOUNT_MOUNTED | ACTION_ECONOMY

Question: <The specific question RAW does not deterministically answer>

RAW References:
    - <Book p.XXX — what RAW says (quote or paraphrase)>
    - <Book p.XXX — conflicting text if CONTRADICTORY>

RAW Answer: SILENT | AMBIGUOUS | CONTRADICTORY | RESOLVED_BY_ERRATA
    SILENT         — No rule exists. RAW says nothing.
    AMBIGUOUS      — A rule exists but admits multiple valid readings.
    CONTRADICTORY  — Two or more rules directly conflict.
    RESOLVED_BY_ERRATA — An errata PDF addresses this (finding is informational).

RAW Data Available: <What inputs exist in the written rules>
RAW Data Missing: <What inputs would be needed for a deterministic answer>

Mechanical Relevance: <What game-mechanical decision depends on this answer>
    Examples: "cover calculation", "spell targeting", "action legality",
              "damage computation", "sunder resolution"

Disposition: RAW_SUFFICIENT | ERRATA_RESOLVED | NEEDS_HOUSE_POLICY |
             BOX_RESOLVER_DECISION | OUT_OF_SCOPE
    RAW_SUFFICIENT        — RAW actually answers this; people argue about the reading
    ERRATA_RESOLVED       — WotC published a correction
    NEEDS_HOUSE_POLICY    — RAW is genuinely silent; needs a trigger family template
    BOX_RESOLVER_DECISION — Ambiguous RAW; Box picks one reading at design time
    OUT_OF_SCOPE          — Mechanically irrelevant to v1 scope (defer)

Trigger Family: <FAMILY_ID from AD-006 registry, or NONE, or NEW_FAMILY_NEEDED>
Silence ID: <SIL-XXX if cataloged in RQ-BOX-002, or PENDING>

Frequency: RARE | SOMETIMES | OFTEN | ALWAYS
    RARE      — Unusual situation, most sessions never encounter it
    SOMETIMES — Comes up in specific builds or scenarios
    OFTEN     — Common combat/exploration interaction
    ALWAYS    — Affects every session (e.g., every magic item)

Exploit Severity: NONE | MILD | MAJOR
    NONE  — No exploit vector
    MILD  — Exploitable but low game impact
    MAJOR — Exploitable with significant game balance impact

Community Consensus: <Brief summary of community position, if any>
PM Recommendation: <PM's recommended resolution, if applicable>
PO Decision: <PENDING | text of PO ruling>
```

---

## Disposition Decision Tree

```
Does RAW provide a deterministic answer?
├── YES → RAW_SUFFICIENT (document the correct reading, no House Policy needed)
├── ERRATA exists → ERRATA_RESOLVED (adopt errata, document citation)
├── RAW is AMBIGUOUS (multiple valid readings)
│   ├── Affects game state? → BOX_RESOLVER_DECISION (pick reading, log choice)
│   └── Narrative only? → Not cataloged (Spark handles it)
├── RAW is SILENT (no rule)
│   ├── In v1 scope? → NEEDS_HOUSE_POLICY (map to trigger family)
│   └── Out of scope? → OUT_OF_SCOPE (defer)
└── RAW is CONTRADICTORY (two rules conflict)
    └── Always → NEEDS_HOUSE_POLICY (pick one, log as House Policy with both citations)
```

---

## Authority Hierarchy for Findings

When multiple sources address the same question, resolution priority:

| Priority | Source | Provenance Tag |
|----------|--------|----------------|
| 1 | Core rulebook text (PHB/DMG/MM) | RAW |
| 2 | Official errata PDFs | RAW (corrected) |
| 3 | WotC FAQ (June 2008) | OFFICIAL_FAQ |
| 4 | Rules Compendium (2007) | OFFICIAL_COMPILATION |
| 5 | Skip Williams "Rules of the Game" | DESIGNER_INTENT |
| 6 | Community consensus (strong majority) | COMMUNITY |
| 7 | Pathfinder 1e delta (what Paizo changed) | EXTERNAL_EVIDENCE |

Sources at priority 1-2 are binding. Sources at 3-5 inform which RAW reading we choose. Sources at 6-7 provide evidence for House Policy design but do not determine it.

---

## Relationship to Project Governance

- Findings with disposition `NEEDS_HOUSE_POLICY` feed into the **Template Family Registry** (AD-006)
- Findings with disposition `BOX_RESOLVER_DECISION` feed into **resolver implementation** (documented in test docstrings per AD-004)
- Findings with disposition `ERRATA_RESOLVED` feed into **RAW implementation** (standard WO)
- Findings with disposition `OUT_OF_SCOPE` are logged for **future scope expansion**

All findings are stored in `docs/research/findings/` as individual markdown files or collected in domain-specific catalogs.
