# WO-PRS-IP-001 — P8 IP Term Exceptions

**Issued:** 2026-02-23
**Authority:** PRS-01 §8 (IP String Hygiene)
**Lifecycle:** DISPATCH-READY
**Gate:** P8 (IP scan — currently FAIL: 296 violations)
**Blocked by:** Orchestrator accepted ✅

---

## 1. Target Lock

Populate `scripts/ip_exceptions.txt` to clear P8's 296 false-positive violations, bringing Gate P8 to PASS. The violations are **not** IP leaks in shipped code — they are legitimate references in research documents, audit files, test fixtures, and PM tooling. The fix is exceptions documentation, not content removal.

**Target:** `python scripts/build_release_candidate_packet.py` exits 0.

---

## 2. Binary Decisions

| # | Decision | Choice | Rationale |
|---|---|---|---|
| 1 | Approach | Populate `ip_exceptions.txt` | Terms are legitimately referenced; removal would destroy audit trail |
| 2 | `REUSE_DECISION.json` (230 hits) | Exception with justification: provenance audit document | This is the IP decision register — it *must* reference setting names to document what was excluded |
| 3 | `config/REUSE_DECISION.json` in `.gitignore`? | No — keep tracked | It's the source-of-truth provenance record, not a binary artifact |
| 4 | `creature_provenance.json` (21 hits) | Exception: provenance tracking tool data | Same rationale — documents what was sourced and excluded |
| 5 | `creatures.json` (3 hits) | Exception: test fixture data, non-SRD labels used only for identification | Confirm these are not shipped game text |
| 6 | Test files referencing denylist terms | Exception: test fixtures only — terms appear as string literals in assertions | Not game content; document file+line in exceptions |
| 7 | `pm_inbox/` files (4 hits in briefing, 2 in canary log) | Exception: PM operational documents, not shipped source | PM tooling is internal only |
| 8 | `reviewed/` archive files | Exception: historical research artifacts, not shipped source | |
| 9 | `scripts/spark_hooligan.py` (`Pelor`) | Exception: example narrative fixture for testing hooligan detection | Verify it's a test string, not game data |
| 10 | `README.md` (Vecna, Heironeous) | **REMOVE** — not a provenance document, is shipped-facing | Replace with generic deity example or remove |
| 11 | `docs/` audit/design files | Exception: internal design docs, not shipped game content | |

---

## 3. Contract Spec

### 3.1 Exception file format

Per `publish_scan_ip_terms.py` — read the parser to confirm exact format, then use it. Expected:
```
term|file_path|justification
```

One line per file+term combination. Wildcards not supported — be explicit.

### 3.2 Required exception entries (296 violations → 0)

**Group A: Provenance/audit documents (internal, not shipped game content)**
- `config/REUSE_DECISION.json` — all terms (Eberron, Ravenloft, Forgotten Realms, Faerun, Dragonlance, Planescape, Gruumsh, Krynn) — justification: IP decision register, documents excluded non-SRD content
- `tools/data/creature_provenance.json` — all terms — justification: provenance tracking tool
- `tools/data/creature_extraction_gaps.json` — Mind Flayer — justification: gap analysis document
- `EXTRACTED_SOURCES_QUICK_REF.md` — Ravenloft — justification: source provenance reference

**Group B: Internal docs (not shipped)**
- `docs/AIDM_CORE_RULESET_AUDIT.md` — Mind Flayer, Illithid, Beholder — justification: ruleset audit record
- `docs/AUDIT_REPORT.md` — Ravenloft (×4) — justification: design audit document
- `docs/COMMUNITY_RULES_DEBATES_CATALOG.md` — Beholder — justification: community rules research
- `docs/design/TABLE_METAPHOR_AND_PLAYER_ARTIFACTS.md` — Beholder — justification: UI design doc

**Group C: Test fixtures (not game content)**
- `aidm/data/content_pack/creatures.json` — Slaad, Mind Flayer — confirm these are creature type labels for test identification, not narrative text; if so, exception; if narrative text, remove
- `aidm/data/content_pack/npc_stingers.json` — Waterdeep (×2) — confirm: if test fixture, exception; if shipped narrative, remove
- `tests/test_content_pack_creatures.py` — Beholder, Displacer Beast, Mind Flayer, Umber Hulk — justification: test assertions verifying non-SRD creature exclusion logic
- `tests/test_campaign_memory_schemas.py` — Pelor (×2), Heironeous — justification: test fixtures for schema validation
- `tests/spec/` files — Beholder, Illithid, Githyanki — justification: compliance spec test data
- `tests/spec/world_compiler_compliance.md` — Beholder, Illithid, Githyanki

**Group D: PM tooling (internal)**
- `pm_inbox/PM_BRIEFING_CURRENT.md` — Eberron, Ravenloft, Beholder, Mind Flayer — justification: PM operational document (finding description), not shipped source
- `pm_inbox/PREFLIGHT_CANARY_LOG.md` — Kord (×2) — justification: PM operational log
- `pm_inbox/reviewed/` files — all terms — justification: archived research/dispatch documents

**Group E: Script test fixtures**
- `scripts/spark_hooligan.py` — Pelor — verify: if test fixture string, exception with justification

**Group F: README — REMOVE, don't exception**
- `README.md` Vecna, Heironeous — replace with generic examples. README is user-facing.

### 3.3 Validation

After populating `ip_exceptions.txt`, run:
```bash
python scripts/publish_scan_ip_terms.py
```
Must exit 0. Then run full orchestrator:
```bash
python scripts/build_release_candidate_packet.py
```
P8 must show PASS. P1 will still FAIL (dirty tree — operator commits). Everything else should PASS.

---

## 4. Implementation Plan

1. Read `scripts/publish_scan_ip_terms.py` to confirm exact exception format and matching logic
2. Read `RC_PACKET/p8_ip_scan.log` (already generated) for the full violation list
3. For each violation: classify as Group A-F above
4. For Group F (README): make the two small edits
5. For Groups A-E: write exception lines to `ip_exceptions.txt`
6. Run `publish_scan_ip_terms.py` — verify exit 0
7. Run full orchestrator — verify P8 PASS

---

## 5. Deliverables Checklist

- [ ] `scripts/ip_exceptions.txt` populated (296 exception entries, one per violation)
- [ ] `README.md` — Vecna and Heironeous removed/replaced
- [ ] `python scripts/publish_scan_ip_terms.py` exits 0
- [ ] `python scripts/build_release_candidate_packet.py` shows P8: PASS
- [ ] No new test failures introduced

---

## 6. Integration Seams

- `ip_exceptions.txt` format must match exactly what `publish_scan_ip_terms.py` expects — read the parser first
- Do not modify `ip_denylist.txt` — terms on it are correctly flagged; we're documenting exceptions, not removing rules
- `REUSE_DECISION.json` must stay tracked in git — it's the provenance record
- `creatures.json` and `npc_stingers.json`: if any term is in shipped narrative text (not just a creature type label), it must be removed, not excepted

---

## 7. Assumptions to Validate

1. `publish_scan_ip_terms.py` exception format — read before writing anything to `ip_exceptions.txt`
2. `creatures.json` Slaad/Mind Flayer entries — are these creature type labels or narrative text?
3. `npc_stingers.json` Waterdeep — is this a location in shipped NPC dialogue, or a test string?

---

## 8. Preflight

```bash
python scripts/publish_scan_ip_terms.py  # must exit 0
python scripts/build_release_candidate_packet.py  # P8 must show PASS
```

---

## 9. Debrief Focus

1. **creatures.json and npc_stingers.json** — what did you find? Were they excepted or removed, and why?
2. **Exception count** — final count of exception lines written vs 296 violations. Any that couldn't be resolved?

---

## Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```
