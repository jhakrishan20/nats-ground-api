import asyncio
import nats
from nats.errors import ConnectionClosedError, TimeoutError, NoServersError

async def run():
    try:
        # Connect to the local server
        nc = await nats.connect("nats://localhost:4222")
        print("Subscriber connected to NATS on Windows.")

        async def message_handler(msg):
            subject = msg.subject
            data = msg.data.decode()
            print(f"Received number: {data} on topic '{subject}'")

        # Subscribe to the 'numbers' topic
        await nc.subscribe("numbers", cb=message_handler)
        print("Listening for messages on 'numbers'...")

        # Keep the script running
        while True:
            await asyncio.sleep(1)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    async def main():
        await run()
    asyncio.run(main())