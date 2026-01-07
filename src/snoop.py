import asyncio
import nats

async def run():
    try:
        # Connect to the GROUND server
        nc = await nats.connect("nats://127.0.0.1:4222")
        print("Connected to Ground Node (4222)")

        async def cb(msg):
            print(f"--- MESSAGE RECEIVED ---")
            print(f"Subject: {msg.subject}")
            print(f"Data:    {msg.data.decode()}")

        # Subscribe to EVERYTHING coming from the UAV
        # await nc.subscribe("uav.>", cb=cb)
        await nc.subscribe(">", cb=cb)
        print("Listening for 'uav.>' subjects... (Press Ctrl+C to stop)")

        while True:
            await asyncio.sleep(1)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    asyncio.run(run())