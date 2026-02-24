#!/usr/bin/env python3
"""Demo: Crystal Ball NPC Integration.
Sends synthetic WS messages to test crystal ball TTS state + NPC portrait.
"""
import asyncio
import json

MESSAGES = [
    {"msg_type": "tts_speaking_start", "speaker": "dm", "intensity": 1.0},
    {"msg_type": "npc_portrait_display", "npc_id": "goblin_chief", "image_url": ""},
    {"msg_type": "tts_speaking_stop"},
    {"msg_type": "tts_speaking_start", "speaker": "npc", "npc_id": "elder", "intensity": 0.7},
    {"msg_type": "tts_speaking_stop"},
]

async def main():
    try:
        import websockets
        async with websockets.connect("ws://localhost:8765") as ws:
            for msg in MESSAGES:
                print(f"Sending: {msg['msg_type']}")
                await ws.send(json.dumps(msg))
                await asyncio.sleep(2.0)
        print("Demo complete.")
    except Exception as e:
        print(f"WebSocket error (server may not be running): {e}")
        print("Messages that would be sent:")
        for msg in MESSAGES:
            print(f"  {json.dumps(msg)}")

asyncio.run(main())
