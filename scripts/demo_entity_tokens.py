"""
Demo script — WO-UI-06: entity token visual validation.

Sends synthetic WebSocket messages to the client for visual review.
Engine does NOT emit entity_state/entity_delta yet; this script stands in.

Usage:
  python scripts/demo_entity_tokens.py

Sequence:
  1. Spawn roster (Kira + Goblin)
  2. Damage Goblin (HP 7 → 3) — HP bar turns orange/red
  3. Defeat Goblin — token removed from scene
"""

import asyncio
import json
import sys

try:
    import websockets
except ImportError:
    print("ERROR: websockets library not installed. Run: pip install websockets")
    sys.exit(1)

WS_URL = "ws://localhost:8765/ws"

MESSAGES = [
    # Full roster sync — spawns two tokens on the table
    {
        "msg_type": "entity_state",
        "entities": [
            {
                "id": "p1",
                "name": "Kira",
                "faction": "player",
                "position": {"x": 2, "y": 3},
                "hp_current": 11,
                "hp_max": 11,
                "conditions": [],
            },
            {
                "id": "e1",
                "name": "Goblin",
                "faction": "enemy",
                "position": {"x": 8, "y": 5},
                "hp_current": 7,
                "hp_max": 7,
                "conditions": [],
            },
        ],
    },
    # Goblin takes damage — HP bar lerps toward red
    {
        "msg_type": "entity_delta",
        "entity_id": "e1",
        "changes": {"hp_current": 3},
    },
    # Goblin position update — moves toward center
    {
        "msg_type": "entity_delta",
        "entity_id": "e1",
        "changes": {"position": {"x": 5, "y": 4}},
    },
    # Goblin defeated — token removed from scene
    {
        "msg_type": "entity_delta",
        "entity_id": "e1",
        "changes": {"hp_current": 0, "defeated": True},
    },
    # Kira healed — HP bar stays green (already full)
    {
        "msg_type": "entity_delta",
        "entity_id": "p1",
        "changes": {"hp_current": 11},
    },
]


async def main() -> None:
    print(f"Connecting to {WS_URL} ...")
    try:
        async with websockets.connect(WS_URL) as ws:
            print("Connected. Sending demo messages...")
            for i, msg in enumerate(MESSAGES, 1):
                payload = json.dumps(msg)
                await ws.send(payload)
                print(f"  [{i}/{len(MESSAGES)}] Sent: {msg['msg_type']}", end="")
                if msg["msg_type"] == "entity_delta":
                    print(f" (entity_id={msg['entity_id']}, changes={msg['changes']})", end="")
                print()
                await asyncio.sleep(1.5)
            print("Demo complete. Check the browser — tokens should be visible and responsive.")
    except OSError as e:
        print(f"ERROR: Could not connect to {WS_URL}: {e}")
        print("Make sure the game server is running before executing this script.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
