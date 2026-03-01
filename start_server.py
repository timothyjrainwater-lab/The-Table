"""start_server.py  - Phase 1 launch entry point.

Wires the real engine (3v3 combat fixture) into the WebSocket server and starts
uvicorn on port 8000.

Usage:
    python start_server.py

The server accepts WebSocket connections at ws://localhost:8000/ws.
First connection is assigned DM role; all subsequent connections are PLAYER role
(handled by existing ws_bridge._assign_role logic  - no change needed here).
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
    """Return a factory callable that creates a SessionOrchestrator per new session.

    Pattern sourced from aidm/evaluation/harness.py:203.
    Each call produces a fresh orchestrator bound to the same 3v3 fixture.
    (Stage 1: single shared encounter. Stage 2+ will individualise per connection.)
    """
    fixture = build_simple_combat_fixture()

    def factory(session_id: str) -> SessionOrchestrator:
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