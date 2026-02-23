import asyncio
import websockets
import json

# Default SITL home (ArduCopter)
HOME_LAT = -35.363261
HOME_LON = 149.165230
ALT = 20


def generate_serpentine_mission():
    """
    Generate small serpentine pattern around SITL home.
    ~5-6 meter spacing.
    """
    offset = 0.00005  # ~5 meters
    waypoints = []

    for i in range(6):
        lat = HOME_LAT + (i * offset)

        if i % 2 == 0:
            lon = HOME_LON + offset
        else:
            lon = HOME_LON - offset

        waypoints.append({
            "seq": i + 1,
            "lat": lat,
            "lon": lon,
            "alt": ALT
        })

    return {
        "mission_type": "WAYPOINT",
        "rtl_after": True,
        "waypoints": waypoints
    }


async def listen_for_messages(websocket):
    try:
        async for message in websocket:
            data = json.loads(message)
            print(f"\n📥 [INCOMING] {data.get('type', 'Unknown')}: {data.get('payload')}")
    except websockets.exceptions.ConnectionClosed:
        print("🛑 Connection closed by server.")


async def test_client():
    uri = "ws://localhost:3000"

    try:
        async with websockets.connect(uri) as websocket:
            print(f"✅ Connected to {uri}")

            listener_task = asyncio.create_task(
                listen_for_messages(websocket)
            )

            # --- STEP 1: Discovery ---
            await asyncio.sleep(3)

            await websocket.send(json.dumps({
                "type": "search_for_uavs",
                "payload": {"client_id": "airunit-001"}
            }))
            print("📤 [SENT] Discovery Request")

            # --- STEP 2: Connect ---
            await asyncio.sleep(5)

            await websocket.send(json.dumps({
                "type": "connect_to_fc",
                "payload": {"target_uav": "airunit-001"}
            }))
            print("📤 [SENT] Connection Request")

            # --- STEP 3: Upload Mission (10s after connect) ---
            await asyncio.sleep(10)

            mission = generate_serpentine_mission()

            await websocket.send(json.dumps({
                "type": "mission_upload",
                "payload": {
                    "target_uav": "airunit-001",
                    "mission": mission
                }
            }))

            print("📤 [SENT] Serpentine Mission Upload")

            # --- STEP 4: Disconnect (30s after mission) ---
            await asyncio.sleep(10)

            await websocket.send(json.dumps({
                "type": "disconnect_from_fc",
                "payload": {"target_uav": "airunit-001"}
            }))
            print("📤 [SENT] Disconnection Request")

            await asyncio.sleep(5)
            listener_task.cancel()
            print("\n✅ Test sequence complete.")

    except Exception as e:
        print(f"❌ Connection error: {e}")


if __name__ == "__main__":
    asyncio.run(test_client())