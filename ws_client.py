import asyncio
import websockets
import json

async def test_client():
    # Replace with the IP shown in your server console
    uri = "ws://localhost:3000"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"✅ Connected to {uri}")

            # 1. Prepare an "event" message (matching the server's expected format)
            test_event = {
                "type": "search_for_uavs",
                "payload": {"message": "Hello from ws Client!"}
            }
            
            # 2. Send the message
            await websocket.send(json.dumps(test_event))
            print(f"📤 Sent: {test_event}")

            # 3. Listen for a response
            print("⏳ Waiting for messages from server...")
            async for message in websocket:
                data = json.loads(message)
                print(f"📥 Received from server: {data}")

    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    asyncio.run(test_client())