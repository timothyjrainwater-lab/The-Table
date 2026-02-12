"""ASGI application — Starlette app with WebSocket route and health endpoint.

Creates the production ASGI application that can be served by uvicorn:

    uvicorn aidm.server.app:app --host 0.0.0.0 --port 8000

Requires: starlette, uvicorn (noted as dependencies; not installed by this module).
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route, WebSocketRoute

from aidm.server.ws_bridge import WebSocketBridge


async def health_endpoint(request: Request) -> JSONResponse:
    """Health check endpoint.

    Returns 200 with a simple status payload.
    """
    return JSONResponse({"status": "ok"})


def create_app(
    config: Optional[Dict[str, Any]] = None,
    session_orchestrator_factory: Optional[Callable[..., Any]] = None,
) -> Starlette:
    """Create the ASGI application with WebSocket route.

    Routes:
        ws://host/ws  — WebSocket connection
        GET /health   — Health check endpoint

    Args:
        config: Optional configuration dict. Supported keys:
            - cors_origins (list[str]): Allowed CORS origins. Default ["*"].
            - default_actor_id (str): Default actor entity ID.
        session_orchestrator_factory: Callable that creates a SessionOrchestrator
            for a new session. If None, a stub factory is used.

    Returns:
        Configured Starlette ASGI application.
    """
    config = config or {}

    if session_orchestrator_factory is None:
        # Stub factory for development / health-check-only mode
        def session_orchestrator_factory(session_id: str) -> object:
            class _StubSession:
                pass
            return _StubSession()

    bridge = WebSocketBridge(
        session_orchestrator_factory=session_orchestrator_factory,
        default_actor_id=config.get("default_actor_id", "pc_fighter"),
    )

    routes = [
        WebSocketRoute("/ws", bridge.websocket_endpoint),
        Route("/health", health_endpoint, methods=["GET"]),
    ]

    app = Starlette(routes=routes)

    # CORS middleware
    cors_origins = config.get("cors_origins", ["*"])
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


# Default application instance for uvicorn CLI usage
app = create_app()
