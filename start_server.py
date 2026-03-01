"""start_server.py  - Phase 1 launch entry point.

Wires the real engine (3v3 combat fixture) into the WebSocket server and starts
uvicorn on port 8000.

Usage:
    python start_server.py

Each WebSocket connection gets its own independent SessionOrchestrator and WorldState.
First connection is assigned DM role; subsequent connections PLAYER role
(ws_bridge._assign_role logic, unchanged).

Stage 1: per-connection fixture isolation (FINDING-UI-PIPE-START-SERVER-SHARED-STATE-001 fixed).
"""

from __future__ import annotations

import uvicorn

from aidm.interaction.intent_bridge import IntentBridge
from aidm.lens.context_assembler import ContextAssembler
from aidm.lens.scene_manager import SceneManager
from aidm.narration.guarded_narration_service import GuardedNarrationService
from aidm.runtime.play_controller import build_simple_combat_fixture
from aidm.runtime.session_orchestrator import SessionOrchestrator
from aidm.server.app import create_app
from aidm.spark.dm_persona import DMPersona


def _make_session_factory():
    """Return a factory that creates an independent SessionOrchestrator per connection.

    BEFORE (Stage 1 / PIPE-001): fixture built at startup, shared across all connections.
    AFTER  (Stage 2 / ENEMY-LOOP-001): fixture built INSIDE factory, one per connection.

    This closes FINDING-UI-PIPE-START-SERVER-SHARED-STATE-001.
    Pattern sourced from aidm/evaluation/harness.py:203.
    """
    def factory(session_id: str) -> SessionOrchestrator:
        # Build a fresh fixture for every new WebSocket connection
        fixture = build_simple_combat_fixture()
        return SessionOrchestrator(
            world_state=fixture.world_state,
            intent_bridge=IntentBridge(),
            scene_manager=SceneManager(scenes={}),
            dm_persona=DMPersona(),
            narration_service=GuardedNarrationService(),
            context_assembler=ContextAssembler(token_budget=800),
            master_seed=fixture.master_seed,
        )

    return factory


def main() -> None:
    app = create_app(session_orchestrator_factory=_make_session_factory())
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")


if __name__ == "__main__":
    main()
