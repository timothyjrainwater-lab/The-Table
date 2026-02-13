# Discovery Log Compliance Checklist
## Machine-Detectable Violations for RQ-DISCOVERY-001

**Document ID:** RQ-DISCOVERY-001-COMPLIANCE
**Version:** 1.0
**Date:** 2026-02-12
**Reference:** `docs/contracts/DISCOVERY_LOG.md` (RQ-DISCOVERY-001)
**Schemas:**
- `docs/schemas/discovery_entry.schema.json`
- `docs/schemas/knowledge_mask.schema.json`
- `docs/schemas/asset_binding.schema.json`

---

## Purpose

This document defines machine-detectable compliance violations for the Discovery Log contract. Every violation listed is testable with code, regex, or deterministic assertion. Subjective design review items are excluded.

Compliance means:
1. No player-visible output leaks information the knowledge mask does not permit.
2. Every revealed field carries provenance and source attribution.
3. The visible bestiary entry is deterministically reproducible from (world bundle + event log + player_id).
4. The system never coaches, warns, advises, or nudges through revelation patterns.
5. All failure modes produce defined, safe behavior.

---

## Category 1: Information Leak Detection (IL)

**Scan targets:** Any function that produces a `PlayerVisibleBestiaryEntry`, any serialization of bestiary data to UI, any narrative brief that includes entity knowledge.

### IL-001: Unrevealed field present in visible entry
- **Violation:** A field appears in the player-visible bestiary entry that is not in the player's `revealed_fields` for that entity.
- **Test strategy:** For each visible entry, assert that every field key exists in the corresponding `EntityKnowledgeRecord.revealed_fields`.
- **Severity:** Critical

### IL-002: Unrevealed sub-item present in array field
- **Violation:** An individual ability, attack form, or resistance appears in a revealed array field but is not tracked in `sub_field_reveals`.
- **Test strategy:** For array fields (`notable_abilities`, `observed_attack_forms`, `resistances`, `vulnerabilities`), assert each item in the visible entry has a corresponding `sub_field_reveals` entry.
- **Severity:** Critical

### IL-003: Numeric value exposed without studied stage + policy permission
- **Violation:** A numeric mechanical field (`defense_value`, `vitality_range`, `ability_scores`, `save_modifiers`, `attack_modifiers`, `challenge_rating`) appears in the visible entry when the player's stage is below `studied` or the world's `display_policy` does not permit numeric exposure.
- **Test strategy:** Assert that numeric mechanical fields are absent from visible entries unless `stage == "studied"` AND `display_policy` permits it.
- **Severity:** Critical

### IL-004: Full canonical entry exposed
- **Violation:** The raw `CanonicalCreatureEntry` (or a reference to it) is serialized to any player-facing output.
- **Test strategy:** Scan all serialization paths for canonical entry types. Assert no player-facing endpoint returns the canonical type directly.
- **Regex pattern:** `CanonicalCreatureEntry` in any response builder or serialization context
- **Severity:** Critical

### IL-005: MonsterDoctrine data in visible entry
- **Violation:** Any field from `MonsterDoctrine` (tactical behavior profiles) appears in a player-visible bestiary entry or narrative brief.
- **Test strategy:** Assert that no `doctrine` namespace fields appear in visible entry output.
- **Regex pattern:** `doctrine\.|tactical_profile|behavior_weight|target_priority`
- **Severity:** Critical

### IL-006: Placeholder text leaks field existence
- **Violation:** A visible entry contains placeholder text ("???", "unknown", "not yet discovered", empty string fields) for unrevealed fields, thereby leaking that the field exists.
- **Test strategy:** Assert that unrevealed fields are absent (key not present), not present with null/empty/placeholder values.
- **Regex pattern for UI output:** `\?\?\?|not yet discovered|unknown ability|hidden|locked`
- **Severity:** High

### IL-007: Asset tier exceeds knowledge stage
- **Violation:** A portrait, token, or other visual asset is displayed at a higher quality tier than the player's knowledge stage permits (e.g., detailed portrait shown for `heard_of` stage).
- **Test strategy:** Assert that `portrait_tier_displayed <= stage_permitted_tier` for every rendered entity.
- **Severity:** High

---

## Category 2: Provenance Violations (PV)

**Scan targets:** All `RevealedFieldState` records, all visible entry outputs, all narrative briefs containing entity knowledge.

### PV-001: Revealed field missing provenance label
- **Violation:** A field in the visible entry has no `provenance_label` in its `RevealedFieldState`.
- **Test strategy:** For every field in every visible entry, assert the corresponding `RevealedFieldState` has a non-null `provenance_label`.
- **Severity:** Critical

### PV-002: Revealed field missing source event reference
- **Violation:** A `RevealedFieldState` has an empty `source_event_refs` array.
- **Test strategy:** Assert `len(source_event_refs) >= 1` for every `RevealedFieldState`.
- **Severity:** Critical

### PV-003: Provenance label inconsistent with reliability
- **Violation:** The `provenance_label` does not match the reliability tier mapping: high → `BOX` or `DERIVED`, medium → `DERIVED`, low → `UNCERTAIN`.
- **Test strategy:** Assert label-reliability consistency for every `RevealedFieldState`.
- **Mapping:**
  - `reliability: "high"` → `provenance_label in ["BOX", "DERIVED"]`
  - `reliability: "medium"` → `provenance_label == "DERIVED"`
  - `reliability: "low"` → `provenance_label == "UNCERTAIN"`
- **Severity:** High

### PV-004: Ledger entry missing required fields
- **Violation:** A `RevealLedgerEntry` is missing any required field: `ledger_index`, `event_ref`, `timestamp`, `source_type`, `reliability`, `fields_revealed`.
- **Test strategy:** JSON schema validation of every ledger entry against `knowledge_mask.schema.json#/$defs/RevealLedgerEntry`.
- **Severity:** High

### PV-005: Source event reference not resolvable
- **Violation:** A `source_event_refs` value or `event_ref` in a ledger entry does not correspond to any event in the campaign event log.
- **Test strategy:** For every event reference in every mask, assert it resolves to a valid event in the campaign event log.
- **Severity:** High

---

## Category 3: Determinism Invariants (DI)

**Scan targets:** The `render(canonical, replay(ledger, policy))` function and all inputs.

### DI-001: Replay non-determinism
- **Violation:** Replaying the same ledger against the same canonical entry with the same display policy produces a different visible entry.
- **Test strategy:** Run `render()` twice with identical inputs. Assert byte-for-byte identical JSON output.
- **Severity:** Critical

### DI-002: Ledger order sensitivity
- **Violation:** The visible entry changes when ledger entries with identical timestamps are replayed in a different insertion order (non-stable sort).
- **Test strategy:** Generate ledger entries with identical timestamps. Replay in both possible orderings. Assert identical visible output (or assert ledger_index breaks ties deterministically).
- **Severity:** High

### DI-003: Seed-dependent output without seed recording
- **Violation:** A computation uses randomness or a seed-derived value but the seed is not recorded in the ledger entry.
- **Test strategy:** Assert that any ledger entry where computed values exist has a non-null `seed` field.
- **Severity:** High

### DI-004: Asset binding non-determinism
- **Violation:** The same `(world_seed, entity_type_id, asset_type)` triple produces different binding hashes across invocations.
- **Test strategy:** Compute binding hashes 100 times with identical inputs. Assert all identical.
- **Severity:** Critical

### DI-005: Stage transition non-monotonicity
- **Violation:** A `stage_history` entry records a transition where `to_stage` has a lower ordinal than `from_stage`.
- **Test strategy:** Assert `ordinal(to_stage) > ordinal(from_stage)` for every `StageTransition`. Stage ordinals: unknown=0, heard_of=1, observed=2, engaged=3, studied=4.
- **Severity:** Critical

---

## Category 4: No-Coaching Violations (NC)

**Scan targets:** All player-facing text generated from or influenced by the Discovery Log. Includes bestiary page text, narrative briefs with knowledge context, and crystal ball display text.

### NC-001: Advisory language in bestiary output
- **Violation:** Bestiary text contains advisory or tactical language.
- **Regex pattern:** `\b(you should|be careful|watch out|beware|warning|caution|tip:|hint:|consider using|try to|make sure|don't forget|remember to|it's wise to|recommend)\b`
- **Test strategy:** Regex scan all player-facing bestiary text.
- **Severity:** Critical

### NC-002: Comparative tactical suggestion
- **Violation:** Bestiary text compares entity weaknesses/strengths in a way that suggests tactical choices.
- **Regex pattern:** `\b(weak against|strong against|use .+ to|effective against|vulnerable to .+ attacks|immune to .+ so)\b`
- **Test strategy:** Regex scan. Note: "vulnerable to cold" (factual reveal) is allowed. "vulnerable to cold, so use ice attacks" is a violation.
- **Exception:** Factual statements of resistance/vulnerability without tactical framing are permitted.
- **Severity:** High

### NC-003: Urgency or danger language
- **Violation:** Bestiary text uses urgency or danger framing that constitutes implicit coaching.
- **Regex pattern:** `\b(extremely dangerous|deadly|you will die|certain death|run away|retreat immediately|do not engage|overwhelming)\b`
- **Test strategy:** Regex scan. Factual categorical descriptors (e.g., "apex predator") are permitted; prescriptive warnings are not.
- **Exception:** World-authored `behavior_summary` and `lore_text` may contain dramatic language if it is world flavor, not system-generated advice.
- **Severity:** Medium

### NC-004: Revelation pattern leaks priority
- **Violation:** The order or emphasis of revealed fields is manipulated to draw attention to tactically important information (e.g., always showing vulnerabilities first).
- **Test strategy:** Assert that visible entry field ordering follows a fixed schema order (§5.4 of the contract), not a dynamic priority based on tactical relevance.
- **Severity:** Medium

---

## Category 5: Schema Validation (SV)

**Scan targets:** All JSON instances of discovery_entry, knowledge_mask, and asset_binding schemas.

### SV-001: CanonicalCreatureEntry fails schema validation
- **Violation:** A canonical entry does not validate against `discovery_entry.schema.json#/$defs/CanonicalCreatureEntry`.
- **Test strategy:** JSON schema validation of every canonical entry in the world bundle.
- **Severity:** Critical

### SV-002: PlayerKnowledgeMask fails schema validation
- **Violation:** A player's knowledge mask does not validate against `knowledge_mask.schema.json#/$defs/PlayerKnowledgeMask`.
- **Test strategy:** JSON schema validation of every mask after every knowledge event.
- **Severity:** Critical

### SV-003: AssetBindingRegistry fails schema validation
- **Violation:** The binding registry does not validate against `asset_binding.schema.json#/$defs/AssetBindingRegistry`.
- **Test strategy:** JSON schema validation after every new binding.
- **Severity:** Critical

### SV-004: Entity type ID format violation
- **Violation:** An `entity_type_id` does not match the pattern `^creature\.[a-z][a-z0-9_]*$`.
- **Regex pattern:** `^creature\.[a-z][a-z0-9_]*$` (must match)
- **Test strategy:** Regex validation on every entity_type_id in canonical entries, masks, and bindings.
- **Severity:** High

### SV-005: Cross-schema reference integrity
- **Violation:** A `knowledge_mask` references an `entity_type_id` that does not exist in the world bundle's canonical entries, or an `asset_binding` references an entity not in the mask.
- **Test strategy:** For every entity_type_id in masks, assert existence in the world bundle. For every entity_type_id in bindings, assert a corresponding mask record exists for at least one player.
- **Severity:** High

### SV-006: Ledger index gap or duplicate
- **Violation:** `RevealLedgerEntry.ledger_index` values are not sequential (0, 1, 2, ...) or contain duplicates.
- **Test strategy:** Assert `ledger[i].ledger_index == i` for all entries.
- **Severity:** High

### SV-007: Content-independence violation in schema values
- **Violation:** Game-system-specific vocabulary appears in `entity_type_id`, `taxonomy_tags`, `form_tag`, or `content_id` field values.
- **Regex pattern (forbidden):** `\b(goblin|orc|dragon|beholder|mind_flayer|lich|tarrasque|owlbear|gelatinous_cube|displacer_beast)\b` (non-exhaustive — extend per content pack)
- **Test strategy:** Regex scan of all canonical entry field values. This is a sampling check, not exhaustive — world compilers must enforce content independence at compile time.
- **Severity:** Medium

---

## Category 6: Authority Boundary (AB)

**Scan targets:** Import graphs, function call graphs, and data flow from the discovery log module.

### AB-001: Discovery Log writes mechanical state
- **Violation:** Any discovery log function modifies combat state, entity stats, event log entries, or world bundle data.
- **Test strategy:** Static analysis: assert that discovery log module imports are read-only for Box-tier modules. No write calls to event_log, combat state, or world bundle.
- **Severity:** Critical

### AB-002: Discovery Log computes skill check results
- **Violation:** The discovery log evaluates skill check DCs, rolls dice, or determines success/failure for study actions.
- **Test strategy:** Assert that `study_action` events are consumed (not produced) by the discovery log. The `study_result` field must arrive from Box.
- **Regex pattern:** `roll|dice|dc|difficulty_class|check_result|random` in discovery log module
- **Severity:** Critical

### AB-003: Discovery Log modifies canonical entries
- **Violation:** Any code path in the discovery log modifies a `CanonicalCreatureEntry` after world compilation.
- **Test strategy:** Assert canonical entries are frozen/immutable. No setter calls on canonical entry fields from any discovery log code path.
- **Severity:** Critical

### AB-004: Discovery Log merges player masks
- **Violation:** A visible entry computation reads or references another player's knowledge mask.
- **Test strategy:** Assert that `render()` takes exactly one `player_id`'s mask. No cross-player mask access in the render path.
- **Severity:** Critical

### AB-005: Discovery Log accesses MonsterDoctrine
- **Violation:** The discovery log imports or reads from `MonsterDoctrine` / `aidm/schemas/doctrine.py`.
- **Test strategy:** Import graph analysis: assert no import path from discovery log module to doctrine module.
- **Regex pattern:** `from aidm\.schemas\.doctrine|import.*doctrine`
- **Severity:** Critical

---

## Category 7: Fail-Closed Behavior (FC)

**Scan targets:** All error handling paths in the discovery log module.

### FC-001: Unknown entity type silently succeeds
- **Violation:** A knowledge event for an `entity_type_id` not in the world bundle is accepted and creates a mask entry.
- **Test strategy:** Submit a knowledge event with a nonexistent entity_type_id. Assert it is rejected. Assert no mask entry is created.
- **Severity:** Critical

### FC-002: Missing asset binding serves broken reference
- **Violation:** A visible entry contains an asset reference (`asset_id`) that does not resolve to a valid asset in the store.
- **Test strategy:** Create a binding where the referenced asset does not exist. Assert the system falls back to placeholder, not a broken reference.
- **Severity:** High

### FC-003: Corrupted ledger produces partial output
- **Violation:** A ledger with integrity errors (missing entries, duplicate indices, invalid event refs) produces a visible entry instead of failing to a safe state.
- **Test strategy:** Inject ledger corruption. Assert the system returns the last known good state or an empty entry, not a partially computed result.
- **Severity:** High

### FC-004: Pool exhaustion causes binding failure
- **Violation:** An exhausted asset pool causes an exception or prevents the knowledge event from being processed.
- **Test strategy:** Exhaust all items in a pool category. Submit a new entity's first knowledge event. Assert binding completes (with fallback or placeholder), and the knowledge event is processed normally.
- **Severity:** High

### FC-005: Missing canonical field causes render crash
- **Violation:** A canonical entry that is missing an optional field causes the render function to throw instead of gracefully omitting the field.
- **Test strategy:** Create a canonical entry with only required fields (no optional fields). Render a visible entry at `studied` stage. Assert no exception; optional fields simply absent from output.
- **Severity:** Medium

---

## Enforcement Matrix

| Severity | PR Blocking | CI Enforcement | Manual Review Required |
|----------|-------------|----------------|----------------------|
| Critical | Yes — PR cannot merge | Automated test suite | No (automated) |
| High | Yes — PR cannot merge | Automated test suite | No (automated) |
| Medium | Warning — PR may merge with justification | Automated warning | Yes |

## Test File Locations (When Implemented)

| Category | Suggested Test File |
|----------|-------------------|
| IL (Information Leak) | `tests/discovery/test_no_leak.py` |
| PV (Provenance) | `tests/discovery/test_provenance.py` |
| DI (Determinism) | `tests/discovery/test_determinism.py` |
| NC (No-Coaching) | `tests/discovery/test_no_coaching.py` |
| SV (Schema Validation) | `tests/discovery/test_schema_validation.py` |
| AB (Authority Boundary) | `tests/discovery/test_authority_boundary.py` |
| FC (Fail-Closed) | `tests/discovery/test_fail_closed.py` |
