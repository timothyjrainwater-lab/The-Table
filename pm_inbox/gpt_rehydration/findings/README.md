# GPT Research Findings — Intake Structure

Five parallel GPT instances, each analyzing the same project docs through a different lens.
Drop each instance's raw output into its corresponding folder.

## Folder Map

| Folder | GPT Instance Focus | What Goes Here |
|--------|-------------------|----------------|
| `01_architecture_integration/` | Architecture & Integration Gaps | Boundary seams, undefined handoffs, Box↔Lens↔Spark↔Immersion protocols |
| `02_rules_compliance/` | D&D 3.5e Rules Compliance | 5e contamination risks, missing RAW coverage, mechanical correctness |
| `03_performance_hardware/` | Performance, Hardware & VRAM | Unbenchmarked assumptions, latency, VRAM budget, minimum spec risks |
| `04_ux_playability/` | UX, Playability & Session Flow | Player experience holes, onboarding gaps, error recovery, first session |
| `05_research_debt/` | Research Debt & Knowledge Gaps | Partial deliveries, unanswered RQs, R0 GO criteria, missing synthesis |

## Filing Convention

Name the output file with the date and a brief tag:
```
01_architecture_integration/2026-02-12_raw_findings.md
02_rules_compliance/2026-02-12_raw_findings.md
```

If you run the same instance multiple times, append a version:
```
01_architecture_integration/2026-02-12_raw_findings_v2.md
```

## After All 5 Complete

Bring the findings back to Claude Opus (PM). The PM will:
1. Deduplicate across all 5 reports
2. Rank by impact and dependency chain
3. Produce a consolidated Research Gap Register
4. Convert top items into formal research work orders for the agent fleet
