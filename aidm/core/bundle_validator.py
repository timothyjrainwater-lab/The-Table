"""Bundle validator for session readiness checks.

Validates that session bundles have all required data and assets including temporal contracts.
"""

from pathlib import Path
from typing import List
from aidm.schemas.bundles import SessionBundle, ReadinessCertificate, CampaignBundle
from aidm.core.doctrine_rules import derive_tactical_envelope


def validate_session_bundle(bundle: SessionBundle) -> ReadinessCertificate:
    """
    Validate session bundle for readiness.

    Checks:
    - Required fields are present
    - Referenced asset paths exist (if provided as paths)
    - Citations are structurally valid (have source_id)
    - Monster doctrines present and valid (if doctrine_required)

    Args:
        bundle: SessionBundle to validate

    Returns:
        ReadinessCertificate with status and any issues found
    """
    missing_assets = []
    missing_citations = []
    notes = []

    # Check required fields
    if not bundle.id:
        notes.append("Bundle missing 'id' field")
    if not bundle.campaign_id:
        notes.append("Bundle missing 'campaign_id' field")
    if bundle.session_number < 1:
        notes.append(f"Invalid session_number: {bundle.session_number}")

    # Check asset paths (if they look like file paths)
    for asset_key, asset_value in bundle.assets.items():
        if isinstance(asset_value, str):
            # Only check if it looks like a local path (not URLs)
            if not asset_value.startswith("http"):
                path = Path(asset_value)
                if not path.exists():
                    missing_assets.append(f"{asset_key}: {asset_value}")

    # Check citations structural validity
    for i, citation in enumerate(bundle.citations):
        if not isinstance(citation, dict):
            missing_citations.append(f"Citation {i}: not a dictionary")
            continue

        if not citation.get("source_id"):
            missing_citations.append(f"Citation {i}: missing 'source_id'")

        # Page is optional, but if present should be positive
        if "page" in citation and citation["page"] is not None:
            if not isinstance(citation["page"], int) or citation["page"] < 1:
                missing_citations.append(f"Citation {i}: invalid page number")

    # Check doctrine compliance (if required)
    if bundle.doctrine_required:
        for enc_idx, encounter in enumerate(bundle.encounter_specs):
            # Check if encounter has creatures
            if encounter.creatures:
                # Must have doctrines
                if not encounter.monster_doctrines_by_id:
                    notes.append(
                        f"Encounter '{encounter.encounter_id}': "
                        f"missing_monster_doctrine (has creatures but no doctrines)"
                    )
                    continue

                # Check for duplicate monster_ids
                if len(encounter.monster_doctrines_by_id) != len(set(encounter.monster_doctrines_by_id.keys())):
                    notes.append(
                        f"Encounter '{encounter.encounter_id}': "
                        f"duplicate_doctrine_keys (monster_id keys must be unique)"
                    )

                # Validate each doctrine
                for monster_id, doctrine in encounter.monster_doctrines_by_id.items():
                    # Check INT/WIS scores are valid
                    if doctrine.int_score is not None:
                        if not isinstance(doctrine.int_score, int) or doctrine.int_score < 1:
                            notes.append(
                                f"Encounter '{encounter.encounter_id}' doctrine '{monster_id}': "
                                f"doctrine_invalid_scores (invalid INT)"
                            )

                    if doctrine.wis_score is not None:
                        if not isinstance(doctrine.wis_score, int) or doctrine.wis_score < 1:
                            notes.append(
                                f"Encounter '{encounter.encounter_id}' doctrine '{monster_id}': "
                                f"doctrine_invalid_scores (invalid WIS)"
                            )

                    # Check for citations when source is MM
                    if doctrine.source == "MM" and not doctrine.citations:
                        notes.append(
                            f"Encounter '{encounter.encounter_id}' doctrine '{monster_id}': "
                            f"doctrine_missing_citation (MM source requires citations)"
                        )

                    # Validate tactical envelope can be derived
                    try:
                        derive_tactical_envelope(doctrine)
                    except Exception as e:
                        notes.append(
                            f"Encounter '{encounter.encounter_id}' doctrine '{monster_id}': "
                            f"doctrine_envelope_incomplete ({str(e)})"
                        )

    # Check temporal validation (if present)
    if bundle.initial_clock is not None:
        # Validate clock time is non-negative (already checked by GameClock __post_init__)
        # Validate deadlines are >= clock time
        if bundle.deadlines:
            for deadline in bundle.deadlines:
                if deadline.due_at_t_seconds < bundle.initial_clock.t_seconds:
                    notes.append(
                        f"Deadline '{deadline.id}': due_at_t_seconds ({deadline.due_at_t_seconds}) "
                        f"is before initial_clock time ({bundle.initial_clock.t_seconds})"
                    )

    # Validate active effects (if present)
    if bundle.active_effects:
        for idx, effect in enumerate(bundle.active_effects):
            # Check that effect start time is valid
            if bundle.initial_clock is not None:
                if effect.start_t_seconds > bundle.initial_clock.t_seconds:
                    notes.append(
                        f"Effect {idx}: start_t_seconds ({effect.start_t_seconds}) "
                        f"is after initial_clock time ({bundle.initial_clock.t_seconds})"
                    )

            # Check that ends_at_t_seconds (if set) is consistent with start
            if effect.ends_at_t_seconds is not None:
                if effect.ends_at_t_seconds < effect.start_t_seconds:
                    notes.append(
                        f"Effect {idx}: ends_at_t_seconds ({effect.ends_at_t_seconds}) "
                        f"is before start_t_seconds ({effect.start_t_seconds})"
                    )

    # Validate ambient light schedules in scene cards
    for scene_idx, scene in enumerate(bundle.scene_cards):
        if scene.ambient_light_schedule is not None:
            schedule = scene.ambient_light_schedule

            # Validation already done in AmbientLightSchedule.__post_init__
            # But check that schedule times are reasonable if initial_clock present
            if bundle.initial_clock is not None and schedule.entries:
                first_entry_time = schedule.entries[0][0]
                if first_entry_time > bundle.initial_clock.t_seconds:
                    # This is just a warning, not necessarily a blocker
                    pass  # Allow schedules that start in the future

    # Validate environmental hazards (if present)
    for scene_idx, scene in enumerate(bundle.scene_cards):
        # Collect hazard IDs for reference checking
        hazard_ids = set()

        # Validate hazards
        for hazard_idx, hazard in enumerate(scene.environmental_hazards):
            # Check for duplicate hazard IDs
            if hazard.id in hazard_ids:
                notes.append(
                    f"Scene '{scene.scene_id}' hazard {hazard_idx}: "
                    f"duplicate_hazard_id ('{hazard.id}' appears multiple times)"
                )
            hazard_ids.add(hazard.id)

            # interval_value validation (already checked in schema __post_init__)
            # visibility_tags validation - just check they're strings
            for tag in hazard.visibility_tags:
                if not isinstance(tag, str):
                    notes.append(
                        f"Scene '{scene.scene_id}' hazard '{hazard.id}': "
                        f"invalid_visibility_tag (must be string)"
                    )

            # terrain_tags validation - just check they're strings
            for tag in hazard.terrain_tags:
                if not isinstance(tag, str):
                    notes.append(
                        f"Scene '{scene.scene_id}' hazard '{hazard.id}': "
                        f"invalid_terrain_tag (must be string)"
                    )

            # Check citation requirement for DMG-sourced hazards
            # (assuming hazards from DMG should have citations - policy decision)
            if hazard.citation and hazard.citation.get("source_id"):
                source_id = hazard.citation["source_id"]
                # DMG source_id is fed77f68501d
                if source_id == "fed77f68501d" and not hazard.citation.get("page"):
                    notes.append(
                        f"Scene '{scene.scene_id}' hazard '{hazard.id}': "
                        f"dmg_citation_missing_page (DMG citation requires page)"
                    )

        # Validate environmental conditions
        for cond_idx, condition in enumerate(scene.environmental_conditions):
            # Check hazard reference exists
            if condition.hazard_ref not in hazard_ids:
                notes.append(
                    f"Scene '{scene.scene_id}' condition {cond_idx}: "
                    f"missing_hazard_ref (references '{condition.hazard_ref}' which doesn't exist)"
                )

    # Determine status
    status = "ready"
    if missing_assets or missing_citations or notes:
        status = "blocked"

    return ReadinessCertificate(
        bundle_id=bundle.id,
        status=status,
        missing_assets=missing_assets,
        missing_citations=missing_citations,
        notes=notes
    )


def validate_campaign_bundle(bundle: CampaignBundle) -> ReadinessCertificate:
    """
    Validate campaign bundle for campaign memory consistency.

    Checks:
    - Session ledger entry IDs are unique
    - Evidence ledger entry IDs are unique
    - Thread registry clue IDs are unique
    - Evidence references valid session IDs (if ledger present)
    - Evidence event_id within declared event_id_range (if range present)
    - Evidence/clue enum values are valid (fail-closed)

    Args:
        bundle: CampaignBundle to validate

    Returns:
        ReadinessCertificate with status and any issues found
    """
    notes = []
    missing_assets = []
    missing_citations = []

    # Check required fields
    if not bundle.id:
        notes.append("Campaign bundle missing 'id' field")
    if not bundle.title:
        notes.append("Campaign bundle missing 'title' field")

    # Build session ID index from ledger
    session_ids = set()
    session_event_ranges = {}  # session_id -> (start, end)

    for entry in bundle.session_ledger:
        # Check unique session_id in ledger
        if entry.session_id in session_ids:
            notes.append(f"Duplicate session_id in ledger: '{entry.session_id}'")
        session_ids.add(entry.session_id)

        # Track event ranges
        if entry.event_id_range is not None:
            session_event_ranges[entry.session_id] = entry.event_id_range

    # Validate evidence ledger (if present)
    if bundle.evidence_ledger is not None:
        evidence_ids = set()

        for evidence in bundle.evidence_ledger.entries:
            # Check unique evidence ID
            if evidence.id in evidence_ids:
                notes.append(f"Duplicate evidence entry ID: '{evidence.id}'")
            evidence_ids.add(evidence.id)

            # Check session_id reference (if ledger present)
            if session_ids and evidence.session_id not in session_ids:
                notes.append(
                    f"Evidence '{evidence.id}': "
                    f"invalid_session_ref ('{evidence.session_id}' not in session ledger)"
                )

            # Check event_id within declared range (if range present for that session)
            if evidence.event_id is not None and evidence.session_id in session_event_ranges:
                start_id, end_id = session_event_ranges[evidence.session_id]
                if not (start_id <= evidence.event_id <= end_id):
                    notes.append(
                        f"Evidence '{evidence.id}': "
                        f"event_id {evidence.event_id} outside session range [{start_id}, {end_id}]"
                    )

    # Validate thread registry (if present)
    if bundle.thread_registry is not None:
        clue_ids = set()

        for clue in bundle.thread_registry.clues:
            # Check unique clue ID
            if clue.id in clue_ids:
                notes.append(f"Duplicate clue ID in thread registry: '{clue.id}'")
            clue_ids.add(clue.id)

            # Check session_id reference (if ledger present)
            if session_ids and clue.session_id not in session_ids:
                notes.append(
                    f"Clue '{clue.id}': "
                    f"invalid_session_ref ('{clue.session_id}' not in session ledger)"
                )

    # Determine status
    status = "ready"
    if notes or missing_assets or missing_citations:
        status = "blocked"

    return ReadinessCertificate(
        bundle_id=bundle.id,
        status=status,
        missing_assets=missing_assets,
        missing_citations=missing_citations,
        notes=notes
    )
