# AUDIT RETRO SWEEP PLAN — Batch A Through T RAW Fidelity
**ID:** AUDIT-RETRO-SWEEP-PLAN-001
**Authority:** Thunder (PO) — directive 2026-02-27
**Status:** ACTIVE
**Sprint type:** Bounded audit freeze — no new feature dispatches during sprint (blockers/fixes only)
**Filed by:** Slate (PM) — 2026-02-27

---

## 1. Context

Batches A through T shipped 180+ gate-passing engine mechanics without referencing `docs/RAW_FIDELITY_AUDIT.md`, CP decision documents, or PHB citations. Gate tests confirm deterministic behavior, not source fidelity. The two are different guarantees. PA-2H (1.5× spec vs 2× PHB) is the confirmed case. Unknown number of others exist.

**This audit freeze sprint is not a rewrite and not an indefinite halt. It is a bounded confidence restoration operation triggered by a systemic process canary (PA-2H). The objective is to restore source-fidelity traceability across implemented mechanics, patch the WO process to prevent recurrence, and return to normal dispatch with a verified foundation.**

Timebox: 2–5 sessions. Clear exit gates. Then resume.

---

## 2. Ownership Model

| Role | Owns |
|------|------|
| **Slate (PM)** | Mechanic inventory, risk tier assignment, audit WO sequencing, tracker integrity (RAW_FIDELITY_AUDIT.md), finding filing discipline, sprint status, exit-gate enforcement |
| **Chisel / Audit Builder** | Source code inspection, PHB/SRD citation verification against implementation, mismatch identification, debrief evidence (file:line + citation + expected vs actual), patch WOs for confirmed deviations |
| **Thunder (PO)** | Policy calls on ambiguous/intentional deviations, stop/go decisions if audit uncovers deeper structural issues |
| **Aegis / Anvil (advisory)** | Ambiguity triage, methodology integrity, classification support, wording of findings/doctrine patches |

PM cannot read source code (hard boundary). All code inspection is delegated to the audit builder. PM owns everything before and after the code read.

---

## 3. Sprint Rules

- **No new feature WOs** during sprint
- **Allowed during sprint:** blockers, audit findings, corrective patches, process/template patching
- **Timebox:** 2–5 sessions
- **Scope guardrail:** This sprint covers **implemented mechanics only** (what is already live). Do not let raw data compilation (all 221 feats / all ~350 spells / full equipment table) swallow the sprint. Source fidelity for live mechanics first. Broader data packs are a separate track.

---

## 4. Exit Gates (sprint ends when ALL four pass)

### Gate 1 — Coverage status
Every implemented mechanic from Batch A–T has a fidelity status entry in `docs/RAW_FIDELITY_AUDIT.md`:
- FULL / DEGRADED / DEFERRED / FORBIDDEN
- No row marked PENDING without an assigned audit WO that will resolve it

### Gate 2 — High-risk domains audited
All Tier 0 mechanics have been checked against:
- PHB/SRD citations (exact page + value)
- Relevant CP decision documents (CP10–CP20+)
- Actual implementation behavior (builder code inspection)

### Gate 3 — Findings discipline complete
All discrepancies found during sprint are:
- Filed as FINDING artifacts with evidence (file:line + citation + expected vs actual)
- Linked to corrective WOs (or explicit Thunder-approved defer decisions)
- Not silently closed

### Gate 4 — Process wire-up active ✅ (already met)
WO template and acceptance criteria include:
- PHB/SRD citation block
- RAW_FIDELITY_AUDIT.md row reference
- CP decision reference (if applicable)
- Deviation status

Gate 4 is already met: PROTOCOL-WO-RAW-FIDELITY-WIREUP-001 filed 2026-02-27.

---

## 5. Mechanic Inventory — All Implemented (Batch A–T)

### Domain A: Attack Modifiers & Combat Feats (Tier 0)

| Mechanic | Gate | Batch | Risk | Audit Status |
|---------|------|-------|------|-------------|
| Power Attack 2H multiplier | PA | P | TIER 0 | IN PROGRESS — WO-ENGINE-PA-2H-FIX-001 |
| Power Attack 1H / off-hand | PA | P | TIER 0 | PENDING |
| Power Attack BAB cap | PA | P | TIER 1 | PENDING |
| Combat Expertise non-linear table | CEX | C | TIER 0 | PENDING |
| Rapid Shot penalty application | C | C | TIER 0 | PENDING |
| Weapon Finesse — qualifying weapons | WF | B R1 | TIER 1 | PENDING |
| Improved Critical — threat range doubling | IC | Batch I | TIER 0 | PENDING |
| Precise Shot — no-penalty threshold | PS | P | TIER 1 | PENDING |
| Blind-Fight — reroll rule | BF | O | TIER 2 | PENDING |

### Domain B: Two-Weapon Fighting Chain (Tier 0)

| Mechanic | Gate | Batch | Risk | Audit Status |
|---------|------|-------|------|-------------|
| TWF off-hand penalties (light vs. non-light) | WFC | Q | TIER 0 | PENDING (Q not yet dispatched) |
| Greater TWF — BAB≥10, third off-hand | GTWF | R | TIER 0 | PENDING |

### Domain C: Maneuver Feats & Bonuses (Tier 0/1)

| Mechanic | Gate | Batch | Risk | Audit Status |
|---------|------|-------|------|-------------|
| Improved Bull Rush +4 bonus | IMB | P | TIER 0 | PENDING |
| Improved Trip +4 bonus | IMB | P | TIER 0 | PENDING |
| Improved Disarm +4 bonus | IMB | P | TIER 0 | PENDING |
| Improved Grapple +4 bonus | IMB | P | TIER 0 | PENDING |
| Improved Sunder +4 bonus | IMB | P | TIER 0 | PENDING |
| Improved Overrun — defender-avoid suppression | IO | O | TIER 1 | PENDING |
| Improved Disarm Counter — margin ≥10 threshold | IDC | P | TIER 1 | PENDING |
| Improved Trip free attack path | IT | N | TIER 1 | PENDING |

### Domain D: Natural Attacks & Multiattack (Tier 0)

| Mechanic | Gate | Batch | Risk | Audit Status |
|---------|------|-------|------|-------------|
| Multiattack secondary penalty (-2 feat / -5 no feat) | MA | T | TIER 0 | PENDING |
| Improved Natural Attack die step table | INA | T | TIER 0 | PENDING |
| Natural attack base damage table | NA | Batch A | TIER 0 | PENDING |

### Domain E: Class Features — Martial (Tier 0)

| Mechanic | Gate | Batch | Risk | Audit Status |
|---------|------|-------|------|-------------|
| Barbarian Rage stat bonuses (+4 STR/CON, +2 will, -2 AC) | BR | A | TIER 0 | PENDING |
| Barbarian DR progression table | BDR | S | TIER 0 | PENDING |
| Barbarian Fast Movement — heavy armor suppression only | BFM | D | TIER 1 | PENDING |
| Rage HP gain/loss on rage end | BR | A | TIER 0 | PENDING |
| Favored Enemy bonus progression (+2/+4/+6...) | FE | A | TIER 0 | PENDING |
| Wild Shape HP/duration rules + form availability | WS | A | TIER 0 | PENDING |
| Uncanny Dodge — class level thresholds | UD | C | TIER 0 | PENDING |
| Sneak Attack immunity — creature type list | SI | M | TIER 0 | PENDING |

### Domain F: Class Features — Divine (Tier 0)

| Mechanic | Gate | Batch | Risk | Audit Status |
|---------|------|-------|------|-------------|
| Divine Grace — level ≥2 threshold, CHA to all saves | DG | B R1 | TIER 0 | PENDING |
| Lay on Hands — pool formula (paladin_level × CHA) | LOH | S | TIER 0 | PENDING |
| Smite Evil — bonus formula + uses/day | SE | A | TIER 0 | PENDING |
| Improved Turning — +1 effective level | ITN | T | TIER 1 | PENDING |
| Turn Undead — table and dice formula | TWD | Dispatch #7 | TIER 0 | PENDING |
| Extra Turning — +4 uses (stackable?) | ETN | S | TIER 1 | PENDING |
| Cleric Spontaneous — cure redirect rules | CS | Batch K | TIER 1 | PENDING |
| Divine Health — immunity threshold | DH | S | TIER 2 | PENDING |

### Domain G: Class Features — Arcane/Monk/Bard (Tier 1)

| Mechanic | Gate | Batch | Risk | Audit Status |
|---------|------|-------|------|-------------|
| Arcane Spell Failure — % by armor, V-only bypass | ASF | A | TIER 0 | PENDING |
| Evasion — class level thresholds, armor restriction | EV | B R1 | TIER 0 | PENDING |
| Monk WIS to AC — level threshold, max dex | MWA | D | TIER 0 | PENDING |
| Monk Unarmed Progression — damage table | MUP | S | TIER 0 | PENDING |
| Bardic Music — uses/day formula, duration | BM | A | TIER 1 | PENDING |
| Spell Penetration — SR check, no auto-fail | SP | R | TIER 1 | PENDING |
| Racial Save Bonuses — dwarf/halfling thresholds | RSV | S | TIER 1 | PENDING |

### Domain H: Spellcasting Constraints (Tier 1)

| Mechanic | Gate | Batch | Risk | Audit Status |
|---------|------|-------|------|-------------|
| Concentration DC formulas (vigorous, violent, distracted) | CV | Batch K | TIER 0 | PENDING |
| Spell slot table — all classes (cleric, wizard, sorcerer, etc.) | SS | Dispatch #5 | TIER 1 | PENDING |
| Metamagic slot cost table | MM | Dispatch #7 | TIER 1 | PENDING |
| Silent/Still Spell component bypass | SS/STS | D | TIER 1 | PENDING |

### Domain I: Static Combat Feats (Tier 2)

| Mechanic | Gate | Batch | Risk | Audit Status |
|---------|------|-------|------|-------------|
| Great Fortitude / Iron Will / Lightning Reflexes +2 | SF | A | TIER 2 | PENDING |
| Spell Focus / Greater Spell Focus +1/+2 DC | SFD | A | TIER 2 | PENDING |
| Toughness +3 HP | TG | O | TIER 2 | PENDING |
| Diehard — fight at 0 to -9 HP | DH | Batch K | TIER 2 | PENDING |
| Combat Reflexes — AoO count formula | CR | B R1 | TIER 1 | PENDING |
| Dazzled — attack penalty | DZ | Batch K | TIER 2 | PENDING |
| Cowering/Fascinated effects | CF | Batch K | TIER 2 | PENDING |
| Run action multiplier | RN | Batch K | TIER 2 | PENDING |
| Skill Synergy table | SS2 | Batch K | TIER 1 | PENDING |
| AoO from standing from prone | AP | Batch K | TIER 2 | PENDING |
| Staggered — single action type | SA | Batch I | TIER 2 | PENDING |
| Massive Damage — DC/threshold | MD | N | TIER 1 | PENDING |

### Domain J: Data Accuracy (separate from engine logic)

| Mechanic | Gate | Batch | Risk | Audit Status |
|---------|------|-------|------|-------------|
| Feat prerequisite data (221 feats) | FD | OSS | TIER 1 | PENDING |
| Equipment stats (ASF %, weapon damage, weight) | EQ | OSS | TIER 1 | PENDING |
| Spell data (DCs, components, durations, ~350 spells) | SP2 | OSS | TIER 1 | PENDING |
| Class BAB/save tables | CT | OSS | TIER 1 | PENDING |

---

## 4. Sprint Structure

### Session allocation (estimated 5–7 sessions)

| Session | Domains | Audit WO | Owner |
|---------|---------|---------|-------|
| 1 | A (Attack feats) + B (TWF chain) | AUDIT-WO-001 | Chisel |
| 2 | C (Maneuver feats) + D (Natural attacks) | AUDIT-WO-002 | Builder |
| 3 | E (Martial class features) | AUDIT-WO-003 | Builder |
| 4 | F (Divine class features) | AUDIT-WO-004 | Builder |
| 5 | G (Arcane/Monk/Bard) + H (Spellcasting constraints) | AUDIT-WO-005 | Builder |
| 6 | I (Static feats) + J (Data accuracy spot check) | AUDIT-WO-006 | Builder |
| +1 (if needed) | Findings triage + corrective WOs | — | Chisel |

### Each AUDIT-WO structure

1. Builder reads source code for the domain mechanics
2. For each mechanic: look up PHB/SRD citation, compare to implementation
3. For each mechanic: record status (FULL / DEGRADED with detail / CONFIRM FULL)
4. Update `docs/RAW_FIDELITY_AUDIT.md` — add/update rows for every mechanic checked
5. File FINDINGs for any deviation (same format as FINDING-ENGINE-PA-2H-PHB-DEVIATION-001)
6. Debrief: list of mechanics checked, findings filed, audit rows added

### During sprint: allowed work

- WO-ENGINE-PA-2H-FIX-001 (in flight — fixes confirmed deviation)
- Batch Q dispatch (GC/IUD/WFC/WSP) — ALLOWED with RAW fidelity blocks per PROTOCOL-WO-RAW-FIDELITY-WIREUP-001
- Bug fixes and blockers (domain system WO for FINDING-DOMAIN-SYSTEM-MISSING-001)
- PM housekeeping

### During sprint: blocked work

- New feature WOs not in the current in-flight set
- Any WO touching Tier 0 domains before that domain's audit WO completes

---

## 5. Findings Disposition

Every finding from the sweep:

1. Filed as FINDING-ENGINE-[MECHANIC]-[N]-001 with MEDIUM or LOW severity
2. Routed to corrective WO if HIGH/MEDIUM
3. LOW findings queued per normal backlog priority
4. HIGH findings halt related dispatches until corrected

---

## 6. Success Marker

Sprint is done when `docs/RAW_FIDELITY_AUDIT.md` has:
- Sections for: movement, conditions, combat modifiers, feats, class features, saves, spellcasting constraints, data
- Every implemented mechanic has a row
- No row says "PENDING" — all say FULL, DEGRADED (with finding), or DEFERRED (with reason)

At that point: confidence is restored, forward work resumes under patched process.

---

*Filed by: Slate (PM) — 2026-02-27*
*Authorized by: Thunder (PO) — directive 2026-02-27*
