import asyncio
import json

import websockets


async def main():
    async with websockets.connect("ws://127.0.0.1:8000/ws/research") as websocket:
        await websocket.send(
            json.dumps(
                {
                    "type": "query",
                    "data": {
                        "query": "How are reusable rockets changing launch economics?",
                        "mode": "normal",
                    },
                }
            )
        )
        
        async for message in websocket:
            data = json.loads(message)
            print(json.dumps(data, indent=2))
            
            if data["type"] in {"done", "error"}:
                break
            
if __name__ == "__main__":
    asyncio.run(main())