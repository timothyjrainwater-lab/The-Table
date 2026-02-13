# World Compiler Compliance Checklist
## Machine-Detectable Violations for Bundle Integrity

**Document ID:** RQ-WORLD-001-COMPLIANCE
**Version:** 1.0
**Date:** 2026-02-12
**Reference:** `docs/contracts/WORLD_COMPILER.md` (WORLD_COMPILER v1)
**Schemas:**
- `docs/schemas/world_bundle.schema.json` — WorldManifest, BundleHashes, AssetPools, CompileReport
- `docs/schemas/rule_registry.schema.json` — RuleRegistry, RuleEntry, RuleParameters
- `docs/schemas/vocabulary_registry.schema.json` — VocabularyRegistry, VocabularyEntry, WorldTaxonomy
- `docs/schemas/presentation_semantics_registry.schema.json` — PresentationSemanticsRegistry, AbilityPresentationEntry, EventPresentationEntry

---

## Purpose

This checklist defines **machine-detectable** compliance signals for the
World Compiler contract. Each check is testable by inspecting a compiled
bundle directory. Organized by category with explicit "how to test" guidance.

---

## Category 1: Bundle Integrity (Hash Verification)

### HI-001: Root hash matches computed hash
**Test:** Read `bundle_hashes.json`. Compute SHA-256 of every file listed.
Sort file hashes by path. Compute SHA-256 of the sorted concatenation.
Compare against `root_hash`.
```python
import hashlib, json
hashes = json.load(open("bundle_hashes.json"))
file_hashes = sorted(hashes["files"].items())
concat = "".join(h for _, h in file_hashes)
computed_root = hashlib.sha256(concat.encode()).hexdigest()
assert computed_root == hashes["root_hash"]
```
**Violation:** Root hash mismatch = bundle has been tampered with or incompletely compiled.

### HI-002: Every listed file exists and hash matches
**Test:** For each entry in `bundle_hashes.json["files"]`, verify file exists
and SHA-256 of file contents matches the recorded hash.
```python
for path, expected_hash in hashes["files"].items():
    with open(os.path.join(bundle_dir, path), "rb") as f:
        actual = hashlib.sha256(f.read()).hexdigest()
    assert actual == expected_hash, f"Hash mismatch: {path}"
```
**Violation:** Missing file or hash mismatch = bundle is corrupt or incomplete.

### HI-003: No unlisted files in bundle
**Test:** Walk the bundle directory. Every file (except `compile_report.json`)
must appear in `bundle_hashes.json["files"]`.
```python
listed = set(hashes["files"].keys())
for root, dirs, files in os.walk(bundle_dir):
    for f in files:
        rel = os.path.relpath(os.path.join(root, f), bundle_dir)
        if rel != "compile_report.json":
            assert rel in listed, f"Unlisted file: {rel}"
```
**Violation:** Unlisted file = potential tampering or stale artifact.

### HI-004: Manifest root_hash matches bundle_hashes root_hash
**Test:** `world_manifest.json["root_hash"] == bundle_hashes.json["root_hash"]`
```python
manifest = json.load(open("world_manifest.json"))
assert manifest["root_hash"] == hashes["root_hash"]
```
**Violation:** Inconsistent root hashes = manifest and hashes file are out of sync.

---

## Category 2: Required Files

### RF-001: world_manifest.json exists
**Test:** `os.path.exists(bundle_dir / "world_manifest.json")`
**Violation:** Missing manifest = bundle is not valid (primary validity signal).

### RF-002: bundle_hashes.json exists
**Test:** `os.path.exists(bundle_dir / "bundle_hashes.json")`

### RF-003: compile_report.json exists with status "success"
**Test:**
```python
report = json.load(open("compile_report.json"))
assert report["status"] == "success"
```

### RF-004: compile_inputs.json exists
**Test:** `os.path.exists(bundle_dir / "compile_inputs.json")`

### RF-005: provenance_policy.json exists
**Test:** `os.path.exists(bundle_dir / "provenance_policy.json")`

### RF-006: lexicon.json exists and is non-empty
**Test:**
```python
lexicon = json.load(open("lexicon.json"))
assert len(lexicon) > 0
```

### RF-007: presentation_semantics.json exists
**Test:** `os.path.exists(bundle_dir / "presentation_semantics.json")`

### RF-008: bestiary.json exists with at least 1 entry
**Test:**
```python
bestiary = json.load(open("bestiary.json"))
assert len(bestiary) >= 1
```

### RF-009: asset_pools.json exists
**Test:** `os.path.exists(bundle_dir / "asset_pools.json")`

### RF-010: rulebook/index.json exists
**Test:** `os.path.exists(bundle_dir / "rulebook" / "index.json")`

### RF-011: maps/map_seeds.json exists with at least 1 region
**Test:**
```python
seeds = json.load(open("maps/map_seeds.json"))
assert len(seeds.get("regions", [])) >= 1
```

---

## Category 3: Schema Validation

### SV-001: world_manifest.json validates against WorldManifest schema
**Test:**
```python
import jsonschema
schema = json.load(open("world_bundle.schema.json"))
manifest = json.load(open("world_manifest.json"))
jsonschema.validate(manifest, schema["$defs"]["WorldManifest"])
```

### SV-002: bundle_hashes.json validates against BundleHashes schema
**Test:**
```python
jsonschema.validate(hashes, schema["$defs"]["BundleHashes"])
```

### SV-003: asset_pools.json validates against AssetPools schema
**Test:**
```python
pools = json.load(open("asset_pools.json"))
jsonschema.validate(pools, schema["$defs"]["AssetPools"])
```

### SV-004: compile_report.json validates against CompileReport schema
**Test:**
```python
jsonschema.validate(report, schema["$defs"]["CompileReport"])
```

### SV-005: toolchain_pins contains no "latest" values
**Test:**
```python
pins = manifest["toolchain_pins"]
for key, value in pins.items():
    assert value != "latest", f"Unpinned tool: {key}"
```

### SV-006: world_id matches expected derivation
**Test:**
```python
expected = hashlib.sha256(
    (str(manifest["seeds"]["world_seed"]) +
     manifest["content_pack_id"] +
     canonical(manifest["toolchain_pins"])).encode()
).hexdigest()[:32]
assert manifest["world_id"] == expected
```

---

## Category 3B: Registry Schema Validation

### RV-001: Rule registry validates against RuleRegistry schema
**Test:**
```python
import jsonschema
rr_schema = json.load(open("docs/schemas/rule_registry.schema.json"))
rule_reg = json.load(open(bundle_dir / "rule_registry.json"))
jsonschema.validate(rule_reg, rr_schema["$defs"]["RuleRegistry"])
```
**Violation:** Rule registry does not conform to canonical schema.

### RV-002: Vocabulary registry validates against VocabularyRegistry schema
**Test:**
```python
vr_schema = json.load(open("docs/schemas/vocabulary_registry.schema.json"))
vocab_reg = json.load(open(bundle_dir / "lexicon.json"))
jsonschema.validate(vocab_reg, vr_schema["$defs"]["VocabularyRegistry"])
```
**Violation:** Vocabulary registry does not conform to canonical schema.

### RV-003: Presentation semantics registry validates against PresentationSemanticsRegistry schema
**Test:**
```python
ps_schema = json.load(open("docs/schemas/presentation_semantics_registry.schema.json"))
ps_reg = json.load(open(bundle_dir / "presentation_semantics.json"))
jsonschema.validate(ps_reg, ps_schema["$defs"]["PresentationSemanticsRegistry"])
```
**Violation:** Presentation semantics registry does not conform to canonical schema.

### RV-004: Every rule entry references a valid procedure_id
**Test:**
```python
rule_reg = json.load(open("rule_registry.json"))
for entry in rule_reg["entries"]:
    assert entry["procedure_id"].startswith("proc."), f"Invalid procedure_id: {entry['procedure_id']}"
    assert entry["procedure_id"] in known_engine_procedures, f"Unknown procedure: {entry['procedure_id']}"
```
**Violation:** Rule entry references a procedure that does not exist in the engine substrate.

### RV-005: Every rule entry's world_name matches lexicon entry
**Test:**
```python
lexicon_names = {e["content_id"]: e["world_name"] for e in vocab_reg["entries"]}
for entry in rule_reg["entries"]:
    assert entry["content_id"] in lexicon_names, f"Rule {entry['content_id']} has no lexicon entry"
    assert entry["world_name"] == lexicon_names[entry["content_id"]], f"Name mismatch: {entry['content_id']}"
```
**Violation:** Rule entry's world_name disagrees with lexicon. Single source of truth violated.

### RV-006: Every vocabulary entry has a deterministic lexicon_id
**Test:**
```python
for entry in vocab_reg["entries"]:
    expected_id = hashlib.sha256(
        (str(manifest["seeds"]["world_seed"]) + entry["content_id"]).encode()
    ).hexdigest()[:16]
    assert entry["lexicon_id"] == expected_id, f"Bad lexicon_id for {entry['content_id']}"
```
**Violation:** lexicon_id is not deterministic — breaks cross-referencing and replay.

### RV-007: Every vocabulary entry is IP-clean
**Test:**
```python
for entry in vocab_reg["entries"]:
    assert entry.get("ip_clean", False) is True, f"IP flag missing/false: {entry['content_id']}"
```
**Violation:** Entry not confirmed IP-clean. Recognition Test (RQ-PRODUCT-001 §3) may not have been applied.

### RV-008: Vocabulary entries sorted by content_id
**Test:**
```python
ids = [e["content_id"] for e in vocab_reg["entries"]]
assert ids == sorted(ids), "Vocabulary entries not sorted — determinism violation"
```

### RV-009: Rule entries sorted by content_id
**Test:**
```python
ids = [e["content_id"] for e in rule_reg["entries"]]
assert ids == sorted(ids), "Rule entries not sorted — determinism violation"
```

### RV-010: Presentation semantics ability_entries sorted by content_id
**Test:**
```python
ids = [e["content_id"] for e in ps_reg["ability_entries"]]
assert ids == sorted(ids), "Presentation semantics entries not sorted — determinism violation"
```

### RV-011: Every presentation semantics entry has a matching vocabulary entry
**Test:**
```python
vocab_ids = {e["content_id"] for e in vocab_reg["entries"]}
for entry in ps_reg["ability_entries"]:
    assert entry["content_id"] in vocab_ids, f"Presentation semantics for {entry['content_id']} has no vocabulary entry"
```
**Violation:** Orphaned presentation semantics — no corresponding name in the lexicon.

### RV-012: Every ability in content pack has a presentation semantics entry
**Test:**
```python
ps_ids = {e["content_id"] for e in ps_reg["ability_entries"]}
for ability_id in content_pack_ability_ids:
    assert ability_id in ps_ids, f"Missing presentation semantics for {ability_id}"
```
**Violation:** Ability has no visual/narration semantics — Spark has no constraints for it.

### RV-013: Every provenance record has source = "world_compiler"
**Test:**
```python
for entry in rule_reg["entries"]:
    assert entry["provenance"]["source"] == "world_compiler"
for entry in vocab_reg["entries"]:
    assert entry["provenance"]["source"] == "world_compiler"
for entry in ps_reg["ability_entries"]:
    assert entry["provenance"]["source"] == "world_compiler"
```
**Violation:** Provenance source is not "world_compiler" — entry origin is untraceable.

### RV-014: vfx_tags and sfx_tags are sorted alphabetically
**Test:**
```python
for entry in ps_reg["ability_entries"]:
    assert entry["vfx_tags"] == sorted(entry["vfx_tags"]), f"Unsorted vfx_tags: {entry['content_id']}"
    assert entry.get("sfx_tags", []) == sorted(entry.get("sfx_tags", [])), f"Unsorted sfx_tags: {entry['content_id']}"
```
**Violation:** Tag arrays not sorted — determinism not guaranteed.

### RV-015: Rule entry tier values are valid
**Test:**
```python
for entry in rule_reg["entries"]:
    tier = entry.get("tier", "tier_1")
    assert tier in ("tier_1", "tier_2", "tier_3", "stub"), f"Invalid tier: {tier}"
    if tier == "stub":
        assert entry["procedure_id"] == "proc.stub", f"Stub entry must use proc.stub"
```
**Violation:** Invalid tier or stub entry incorrectly wired to a real procedure.

### RV-016: entry_count fields match actual array lengths
**Test:**
```python
if "entry_count" in rule_reg:
    assert rule_reg["entry_count"] == len(rule_reg["entries"])
if "entry_count" in vocab_reg:
    assert vocab_reg["entry_count"] == len(vocab_reg["entries"])
if "ability_entry_count" in ps_reg:
    assert ps_reg["ability_entry_count"] == len(ps_reg["ability_entries"])
if "event_entry_count" in ps_reg:
    assert ps_reg["event_entry_count"] == len(ps_reg["event_entries"])
```
**Violation:** Count mismatch — integrity metadata is wrong.

### RV-017: All three registries reference the same world_id
**Test:**
```python
manifest_wid = manifest["world_id"]
assert rule_reg["world_id"] == manifest_wid
assert vocab_reg["world_id"] == manifest_wid
assert ps_reg["world_id"] == manifest_wid
```
**Violation:** Registry belongs to a different world — cross-bundle contamination.

---

## Category 4: Forbidden Content Scans

### FC-001: No coaching/advice language in rulebook entries
**Scan targets:** All files in `rulebook/` directory.
```regex
(?i)\b(you\s+should|you\s+might\s+want|consider\s+using|a\s+good\s+strategy|tip:|hint:|remember\s+to|don't\s+forget|keep\s+in\s+mind|pro\s+tip)\b
```
**Violation:** Rulebook entries must describe mechanics and behavior, never advise.

### FC-002: No coaching/advice language in bestiary entries
**Scan targets:** `bestiary.json`
```regex
(?i)\b(players?\s+should|recommend|effective\s+against|weakness\s+is|vulnerable\s+to|best\s+way\s+to|exploit|take\s+advantage)\b
```
**Violation:** Bestiary entries are DM-side truth, not tactical guides.
**Exception:** Mechanical vulnerability descriptions using game-system terms
(e.g., "vulnerability: fire" as a stat) are allowed. Prose advice is not.

### FC-003: No D&D/WotC copyrighted terms in generated names
**Scan targets:** `lexicon.json` — all `world_name` values.
```regex
(?i)\b(fireball|magic\s*missile|beholder|mind\s*flayer|displacer\s*beast|owlbear|githyanki|illithid|tarrasque|umber\s*hulk|gelatinous\s*cube|rust\s*monster)\b
```
**Violation:** World-generated names must not use trademarked D&D creature/spell names.
**Note:** This is a sample list. The full list of WotC Product Identity terms
should be maintained as a separate blocklist file.

### FC-004: No raw D&D page citations in bundle content
**Scan targets:** All JSON files in bundle.
```regex
(?i)(PHB|DMG|MM)\s*p\.?\s*\d+
```
**Violation:** Page citations are development scaffolding, not shipped content.

### FC-005: No player-visible HP/AC/DC values in rulebook prose
**Scan targets:** `rulebook/` — `ui_description` and `effect_description` fields.
```regex
(?i)\b\d+\s*(hit\s*points?|hp|AC|armor\s*class|DC|difficulty\s*class)\b
```
**Violation:** Rulebook prose describes mechanics qualitatively ("significant fire damage",
"moderate difficulty"). Exact numbers appear only in structured mechanical fields.
**Exception:** Structured fields (damage dice, save DC) in the mechanical section are fine.
Only prose/description fields are scanned.

---

## Category 5: Determinism Verification

### DV-001: Recompile produces identical root_hash
**Test:** Run the compiler twice with identical inputs. Compare `root_hash` from both runs.
```python
hash_1 = compile(inputs)["root_hash"]
hash_2 = compile(inputs)["root_hash"]
assert hash_1 == hash_2
```
**Violation:** Different root_hash = nondeterminism in the pipeline.

### DV-002: Recompile produces identical world_id
**Test:** `world_id` from both runs must match.
```python
assert manifest_1["world_id"] == manifest_2["world_id"]
```

### DV-003: compile_timestamp is the ONLY field that differs between re-runs
**Test:** Diff the two manifests. Only `compile_timestamp` (and compile_report
timings) should differ.
```python
diff = deep_diff(manifest_1, manifest_2)
allowed_diffs = {"compile_timestamp"}
assert set(diff.keys()) <= allowed_diffs
```

### DV-004: Different world_seed produces different world_id
**Test:** Compile with seed=42 and seed=43. world_ids must differ.
```python
assert manifest_42["world_id"] != manifest_43["world_id"]
```

### DV-005: Lexicon entries are sorted deterministically
**Test:** Verify `lexicon.json` entries are sorted by content_id.
```python
ids = [e["content_id"] for e in lexicon]
assert ids == sorted(ids)
```

### DV-006: No unordered collections in any JSON output
**Test:** Parse all bundle JSON files. Verify all JSON objects have
keys in sorted order (enforced by `sort_keys=True` during serialization).
```python
import json
for path in bundle_json_files:
    raw = open(path).read()
    parsed = json.loads(raw)
    reserialized = json.dumps(parsed, sort_keys=True, indent=2)
    assert raw == reserialized, f"Unsorted keys in {path}"
```
**Note:** This is a strong check. If indent/formatting differs, normalize both
before comparison.

---

## Category 6: Provenance Completeness

### PC-001: Every lexicon entry has a content_id traceable to content pack
**Test:** For each entry in `lexicon.json`, verify `content_id` exists in the
content pack's ID registry.
```python
for entry in lexicon:
    assert entry["content_id"] in content_pack_ids
```

### PC-002: Every bestiary entry has a content_id
**Test:** No bestiary entry has an empty or missing `content_id`.

### PC-003: Every presentation_semantics entry has required AD-007 fields
**Test:** For each entry in `presentation_semantics.json`, verify required
fields: `delivery_mode`, `staging`, `origin_rule`, `vfx_tags`, `sfx_tags`, `scale`.
```python
required = {"delivery_mode", "staging", "origin_rule", "vfx_tags", "sfx_tags", "scale"}
for entry in semantics:
    assert required.issubset(set(entry.keys())), f"Missing fields in {entry['content_id']}"
```

### PC-004: compile_inputs.json contains all required input fields
**Test:** Verify `content_pack_id`, `world_seed`, `toolchain_pins` are present.

### PC-005: provenance_policy.json defines at least 3 label types
**Test:**
```python
policy = json.load(open("provenance_policy.json"))
assert len(policy.get("labels", [])) >= 3
```

---

## Category 7: Immutability Enforcement

### IM-001: Bundle directory is not writable by runtime process
**Test:** After loading, attempt to write a file to the bundle directory.
Must fail or be blocked by the loading mechanism.

### IM-002: No runtime code imports write functions for bundle paths
**Scan targets:** All `aidm/` files that load world bundles.
```regex
(?i)(open\(.*bundle.*['"]w|write|shutil\.copy.*bundle|os\.rename.*bundle)
```
**Violation:** Runtime code must not write to the bundle directory.

### IM-003: Loaded bundle data uses frozen/immutable types
**Test:** Verify that loaded world data structures raise on mutation attempts.
```python
world = load_world_bundle(bundle_dir)
with pytest.raises(Exception):
    world.lexicon["ABILITY_003"]["world_name"] = "hacked"
```

---

## Summary Table

| ID | Category | Detection Method | Severity |
|----|----------|-----------------|----------|
| HI-001 | Hash integrity | Hash computation | Critical |
| HI-002 | Hash integrity | File hash verification | Critical |
| HI-003 | Hash integrity | Directory walk | High |
| HI-004 | Hash integrity | Cross-file comparison | High |
| RF-001 | Required files | File existence | Critical |
| RF-002 | Required files | File existence | Critical |
| RF-003 | Required files | JSON parse + field check | Critical |
| RF-004 | Required files | File existence | High |
| RF-005 | Required files | File existence | Medium |
| RF-006 | Required files | JSON parse + length | High |
| RF-007 | Required files | File existence | High |
| RF-008 | Required files | JSON parse + length | High |
| RF-009 | Required files | File existence | Medium |
| RF-010 | Required files | File existence | High |
| RF-011 | Required files | JSON parse + field check | High |
| SV-001 | Schema validation | JSON Schema validator | High |
| SV-002 | Schema validation | JSON Schema validator | High |
| SV-003 | Schema validation | JSON Schema validator | Medium |
| SV-004 | Schema validation | JSON Schema validator | Medium |
| SV-005 | Schema validation | String scan | Critical |
| SV-006 | Schema validation | Hash derivation | High |
| RV-001 | Registry validation | JSON Schema validator | High |
| RV-002 | Registry validation | JSON Schema validator | High |
| RV-003 | Registry validation | JSON Schema validator | High |
| RV-004 | Registry validation | Cross-reference check | Critical |
| RV-005 | Registry validation | Cross-reference check | Critical |
| RV-006 | Registry validation | Hash derivation | High |
| RV-007 | Registry validation | Field check | Critical |
| RV-008 | Registry validation | Sort check | Medium |
| RV-009 | Registry validation | Sort check | Medium |
| RV-010 | Registry validation | Sort check | Medium |
| RV-011 | Registry validation | Cross-reference check | High |
| RV-012 | Registry validation | Cross-reference check | High |
| RV-013 | Registry validation | Field check | High |
| RV-014 | Registry validation | Sort check | Medium |
| RV-015 | Registry validation | Field + logic check | Medium |
| RV-016 | Registry validation | Count comparison | Medium |
| RV-017 | Registry validation | Cross-file comparison | Critical |
| FC-001 | Forbidden content | Regex scan | Critical |
| FC-002 | Forbidden content | Regex scan | Critical |
| FC-003 | Forbidden content | Regex scan | Critical |
| FC-004 | Forbidden content | Regex scan | High |
| FC-005 | Forbidden content | Regex scan | High |
| DV-001 | Determinism | Recompile comparison | Critical |
| DV-002 | Determinism | Recompile comparison | Critical |
| DV-003 | Determinism | Diff analysis | High |
| DV-004 | Determinism | Cross-seed comparison | High |
| DV-005 | Determinism | Sort check | Medium |
| DV-006 | Determinism | Serialization comparison | Medium |
| PC-001 | Provenance | Cross-reference check | High |
| PC-002 | Provenance | Field presence check | Medium |
| PC-003 | Provenance | Required field check | High |
| PC-004 | Provenance | Field presence check | High |
| PC-005 | Provenance | Count check | Medium |
| IM-001 | Immutability | Write attempt | Critical |
| IM-002 | Immutability | Code scan (regex) | Critical |
| IM-003 | Immutability | Mutation attempt | Critical |

**Total: 55 machine-detectable checks across 8 categories.**

---

## Automated Compliance Runner (Specification)

A compliance runner should:

1. Accept a bundle directory path as input
2. Run all HI-* checks (hash integrity)
3. Run all RF-* checks (required files)
4. Run all SV-* checks (schema validation) — requires schema files
5. Run all RV-* checks (registry validation) — requires registry schema files + content pack
6. Run all FC-* checks (forbidden content scans)
7. Run all PC-* checks (provenance completeness) — requires content pack
8. Optionally run DV-* checks (determinism) — requires recompile capability
9. Optionally run IM-* checks (immutability) — requires runtime loading

**Pass criteria:** Zero Critical violations; zero High violations.
**Partial pass:** Zero Critical violations; High violations documented.

---

## END OF COMPLIANCE CHECKLIST
