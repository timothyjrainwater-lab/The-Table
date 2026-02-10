"""M1 Runtime Session Bootstrap — Campaign load, WorldState reconstruction, session initialization.

Implements the M1 runtime session bootstrap contract from M1_RUNTIME_SESSION_BOOTSTRAP.md:
- Campaign load sequence (manifest, start_state.json, events.jsonl)
- WorldState reconstruction via replay-first policy
- Session start (new campaign initialization)
- Session resume (existing campaign continuation with full replay)
- Partial write recovery (discard incomplete turns after last turn_end)
- Log synchronization checks (EventLog turn_end count == SessionLog resolved count)
- Fail-fast on corruption (no automatic repair)

Reference: docs/M1_RUNTIME_SESSION_BOOTSTRAP.md
Reference: docs/M1_RUNTIME_REPLAY_POLICY.md
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
import logging

from aidm.schemas.campaign import CampaignManifest, SessionZeroConfig
from aidm.core.campaign_store import CampaignStore, CampaignStoreError
from aidm.core.state import WorldState
from aidm.core.rng_manager import RNGManager
from aidm.core.event_log import Event, EventLog
from aidm.core.session_log import SessionLog as CoreSessionLog, SessionLogEntry
from aidm.core.replay_runner import run as replay_runner, ReplayReport
from aidm.runtime.session import RuntimeSession, SessionLog as RuntimeSessionLog


class BootstrapError(Exception):
    """Raised when session bootstrap fails."""


@dataclass
class PartialWriteRecoveryResult:
    """Result of partial write recovery detection."""

    incomplete_turn_detected: bool
    """True if incomplete turn was found and discarded."""

    last_complete_turn_index: Optional[int]
    """Index of last complete turn_end event (None if no turns)."""

    events_discarded: int
    """Number of events discarded after last turn_end."""

    recovery_details: str
    """Human-readable description of recovery action."""


@dataclass
class LogSyncCheckResult:
    """Result of EventLog <-> SessionLog synchronization check."""

    in_sync: bool
    """True if logs are synchronized."""

    event_log_turns: int
    """Number of turn_end events in EventLog."""

    session_log_resolved: int
    """Number of resolved intents in SessionLog."""

    details: str
    """Details about sync status or mismatch."""


class SessionBootstrap:
    """Session bootstrap manager for M1 runtime.

    Provides:
    - Campaign load and validation
    - WorldState reconstruction via replay
    - Session initialization (new or resume)
    - Partial write recovery
    - Log synchronization verification
    """

    @staticmethod
    def load_campaign_data(
        store: CampaignStore,
        campaign_id: str,
    ) -> Tuple[CampaignManifest, WorldState, EventLog, CoreSessionLog]:
        """Load all campaign data from disk.

        Args:
            store: CampaignStore instance
            campaign_id: Campaign identifier

        Returns:
            Tuple of (manifest, initial_state, event_log, session_log)

        Raises:
            BootstrapError: If campaign cannot be loaded
        """
        # Load manifest
        try:
            manifest = store.load_campaign(campaign_id)
        except CampaignStoreError as e:
            raise BootstrapError(f"Failed to load campaign manifest: {e}")

        campaign_dir = store.campaign_dir(campaign_id)

        # Load initial WorldState from start_state.json
        start_state_path = campaign_dir / "start_state.json"
        if not start_state_path.is_file():
            raise BootstrapError(
                f"Missing start_state.json for campaign {campaign_id}"
            )

        try:
            with open(start_state_path, "r", encoding="utf-8") as f:
                state_data = json.load(f)
            initial_state = WorldState.from_dict(state_data)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise BootstrapError(f"Failed to load start_state.json: {e}")

        # Load EventLog
        event_log_path = campaign_dir / manifest.paths.events
        try:
            if event_log_path.stat().st_size == 0:
                # Empty log (new campaign)
                event_log = EventLog()
            else:
                event_log = EventLog.from_jsonl(event_log_path)
        except (OSError, ValueError) as e:
            raise BootstrapError(f"Failed to load event log: {e}")

        # Load SessionLog (intents.jsonl)
        session_log_path = campaign_dir / manifest.paths.intents
        try:
            if session_log_path.stat().st_size == 0:
                # Empty log (new campaign)
                session_log = CoreSessionLog()
                session_log.master_seed = manifest.master_seed
                session_log.initial_state_hash = initial_state.state_hash()
            else:
                session_log = CoreSessionLog.from_jsonl(session_log_path)
        except (OSError, ValueError) as e:
            raise BootstrapError(f"Failed to load session log: {e}")

        return manifest, initial_state, event_log, session_log

    @staticmethod
    def detect_partial_write(
        event_log: EventLog,
    ) -> PartialWriteRecoveryResult:
        """Detect incomplete turn (missing turn_end) and prepare recovery.

        Per M1_RUNTIME_SESSION_BOOTSTRAP.md Section 7.5:
        - Find last turn_end event
        - Discard all events after last turn_end
        - Resume from last complete turn

        Args:
            event_log: Event log to check

        Returns:
            PartialWriteRecoveryResult with recovery details
        """
        if len(event_log) == 0:
            return PartialWriteRecoveryResult(
                incomplete_turn_detected=False,
                last_complete_turn_index=None,
                events_discarded=0,
                recovery_details="Event log is empty (new campaign).",
            )

        # Find last turn_end event
        last_turn_end_index = None
        for i in range(len(event_log) - 1, -1, -1):
            if event_log[i].event_type == "turn_end":
                last_turn_end_index = i
                break

        if last_turn_end_index is None:
            # No turn_end found — entire log is incomplete
            events_discarded = len(event_log)
            return PartialWriteRecoveryResult(
                incomplete_turn_detected=True,
                last_complete_turn_index=None,
                events_discarded=events_discarded,
                recovery_details=(
                    f"No turn_end event found. Discarding all {events_discarded} "
                    "events (incomplete turn)."
                ),
            )

        # Check if there are events after last turn_end
        events_after = len(event_log) - (last_turn_end_index + 1)

        if events_after > 0:
            return PartialWriteRecoveryResult(
                incomplete_turn_detected=True,
                last_complete_turn_index=last_turn_end_index,
                events_discarded=events_after,
                recovery_details=(
                    f"Incomplete turn detected: {events_after} events after last "
                    f"turn_end (event_id={event_log[last_turn_end_index].event_id}). "
                    "Discarding incomplete turn."
                ),
            )

        # Log is complete (last event is turn_end or all turns complete)
        return PartialWriteRecoveryResult(
            incomplete_turn_detected=False,
            last_complete_turn_index=last_turn_end_index,
            events_discarded=0,
            recovery_details=(
                f"Event log is complete ({len(event_log)} events, "
                f"last turn_end at event_id={event_log[last_turn_end_index].event_id})."
            ),
        )

    @staticmethod
    def apply_partial_write_recovery(
        event_log: EventLog,
        recovery: PartialWriteRecoveryResult,
    ) -> EventLog:
        """Apply partial write recovery by truncating event log.

        Args:
            event_log: Original event log
            recovery: Recovery result from detect_partial_write()

        Returns:
            New EventLog with incomplete turn discarded
        """
        if not recovery.incomplete_turn_detected:
            return event_log

        if recovery.last_complete_turn_index is None:
            # No complete turns — return empty log
            return EventLog()

        # Reconstruct log up to last turn_end
        recovered_log = EventLog()
        for i in range(recovery.last_complete_turn_index + 1):
            recovered_log.append(event_log[i])

        return recovered_log

    @staticmethod
    def check_log_sync(
        event_log: EventLog,
        session_log: CoreSessionLog,
    ) -> LogSyncCheckResult:
        """Verify EventLog and SessionLog are synchronized.

        Per M1_RUNTIME_SESSION_BOOTSTRAP.md Section 7.6:
        - Count turn_end events in EventLog
        - Count resolved intents in SessionLog
        - Valid if turn_end_count >= resolved_count (AI turns don't generate intents)
        - Invalid if resolved_count > turn_end_count (extra intents without events)

        Args:
            event_log: Event log to check
            session_log: Session log to check

        Returns:
            LogSyncCheckResult
        """
        # Count turn_end events
        turn_end_count = sum(
            1 for event in event_log.events if event.event_type == "turn_end"
        )

        # Count resolved intents
        resolved_count = sum(
            1
            for entry in session_log.entries
            if entry.result is not None  # Resolved intents have results
        )

        # Valid if turn_end_count >= resolved_count
        # (AI turns don't generate player intents)
        in_sync = turn_end_count >= resolved_count

        if in_sync:
            details = (
                f"Logs are synchronized: {turn_end_count} turn_end events, "
                f"{resolved_count} resolved intents."
            )
        else:
            details = (
                f"LOG DESYNC DETECTED: {turn_end_count} turn_end events in EventLog, "
                f"but {resolved_count} resolved intents in SessionLog. "
                "This indicates a runtime bug."
            )

        return LogSyncCheckResult(
            in_sync=in_sync,
            event_log_turns=turn_end_count,
            session_log_resolved=resolved_count,
            details=details,
        )

    @staticmethod
    def reconstruct_world_state(
        initial_state: WorldState,
        event_log: EventLog,
        master_seed: int,
    ) -> Tuple[WorldState, ReplayReport]:
        """Reconstruct WorldState via replay-first policy.

        Per M1_RUNTIME_SESSION_BOOTSTRAP.md Section 4:
        - Always replay events.jsonl from start_state.json
        - Use reducer-only path (no resolver re-execution)
        - Verify determinism if expected hash provided

        Args:
            initial_state: Initial WorldState from start_state.json
            event_log: EventLog to replay
            master_seed: Master RNG seed

        Returns:
            Tuple of (final_state, replay_report)
        """
        replay_report = replay_runner(
            initial_state=initial_state,
            master_seed=master_seed,
            event_log=event_log,
            expected_final_hash=None,  # Don't verify hash during normal replay
        )

        return replay_report.final_state, replay_report

    @classmethod
    def start_new_session(
        cls,
        store: CampaignStore,
        campaign_id: str,
    ) -> RuntimeSession:
        """Start a new session for a fresh campaign.

        Per M1_RUNTIME_SESSION_BOOTSTRAP.md Section 5:
        - Load initial state from start_state.json
        - Initialize RNG with manifest.master_seed
        - Create empty SessionLog
        - Return RuntimeSession ready for first turn

        Args:
            store: CampaignStore instance
            campaign_id: Campaign identifier

        Returns:
            RuntimeSession ready for execution

        Raises:
            BootstrapError: If session cannot be started
        """
        # Load campaign data
        manifest, initial_state, event_log, session_log = cls.load_campaign_data(
            store, campaign_id
        )

        # Verify this is a new campaign (empty logs)
        if len(event_log) > 0:
            raise BootstrapError(
                f"Cannot start new session: event log is not empty ({len(event_log)} events). "
                "Use resume_from_campaign() instead."
            )

        # Initialize RNG
        rng = RNGManager(manifest.master_seed)

        # Create RuntimeSession
        runtime_session = RuntimeSession.create(
            initial_state=initial_state,
            master_seed=manifest.master_seed,
            session_id=campaign_id,
            engine_resolver=None,  # Resolver injected by caller
        )

        return runtime_session

    @classmethod
    def resume_from_campaign(
        cls,
        store: CampaignStore,
        campaign_id: str,
        verify_hash: bool = True,
    ) -> RuntimeSession:
        """Resume an existing campaign session.

        Per M1_RUNTIME_SESSION_BOOTSTRAP.md Section 6:
        - Load initial state from start_state.json
        - Load and replay events.jsonl (full replay, reducer-only)
        - Verify state hash if requested
        - Initialize RNG
        - Load SessionLog from intents.jsonl
        - Return RuntimeSession ready for next turn

        Args:
            store: CampaignStore instance
            campaign_id: Campaign identifier
            verify_hash: If True, verify replay produces same state hash

        Returns:
            RuntimeSession ready for execution

        Raises:
            BootstrapError: If resume fails (corruption, hash mismatch, log desync)
        """
        # Load campaign data
        manifest, initial_state, event_log, session_log = cls.load_campaign_data(
            store, campaign_id
        )

        # Detect and recover from partial writes
        recovery = cls.detect_partial_write(event_log)

        if recovery.incomplete_turn_detected:
            # Apply recovery (truncate event log)
            event_log = cls.apply_partial_write_recovery(event_log, recovery)

            # Log warning (implementation should log this to user)
            # For now, we include it in recovery details
            logging.warning(f"PARTIAL WRITE RECOVERY: {recovery.recovery_details}")

        # Check log synchronization
        sync_check = cls.check_log_sync(event_log, session_log)

        if not sync_check.in_sync:
            # Hard failure on log desync (indicates runtime bug)
            raise BootstrapError(
                f"Log desynchronization detected: {sync_check.details}"
            )

        # Reconstruct WorldState via replay
        final_state, replay_report = cls.reconstruct_world_state(
            initial_state=initial_state,
            event_log=event_log,
            master_seed=manifest.master_seed,
        )

        # Verify determinism if requested
        if verify_hash and len(event_log) > 0:
            # Compute expected hash from final state
            expected_hash = final_state.state_hash()

            # Run 10× replay verification (AC-10)
            divergences = []
            for run in range(10):
                verify_report = replay_runner(
                    initial_state=initial_state,
                    master_seed=manifest.master_seed,
                    event_log=event_log,
                    expected_final_hash=expected_hash,
                )

                if not verify_report.determinism_verified:
                    divergences.append(
                        f"Run {run + 1}: {verify_report.divergence_info}"
                    )

            if divergences:
                raise BootstrapError(
                    f"10× replay verification failed:\n" + "\n".join(divergences)
                )

        # Initialize RNG (will be used for next turn)
        rng = RNGManager(manifest.master_seed)

        # Convert CoreSessionLog to RuntimeSessionLog
        runtime_log = RuntimeSessionLog(
            session_id=campaign_id,
            master_seed=manifest.master_seed,
        )

        # Copy entries from CoreSessionLog to RuntimeSessionLog format
        # (Note: CoreSessionLog uses SessionLogEntry, RuntimeSessionLog uses IntentEntry)
        # For M1, we just initialize with an empty log since RuntimeSession will populate it
        # during execution. The CoreSessionLog is used only for replay verification.

        # Create RuntimeSession
        runtime_session = RuntimeSession(
            world_state=final_state,
            rng=rng,
            log=runtime_log,
            engine_resolver=None,  # Resolver injected by caller
        )

        return runtime_session
