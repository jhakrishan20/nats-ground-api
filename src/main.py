import asyncio
from app.create_app import AppBootstrap

async def main():
    bootstrap = AppBootstrap()
    app_ctx = await bootstrap.create_app()

    stop_event = asyncio.Event()

    async def wait_forever():
        await stop_event.wait()

    try:
        print("✅ System running. Press Ctrl+C to exit...")
        await wait_forever()

    except asyncio.CancelledError:
        print("\n🛑 KeyboardInterrupt detected. Shutting down...")
        await bootstrap.shutdown_app(app_ctx)
        print("👋 Shutdown complete. Goodbye!")
       
    finally:
        await bootstrap.shutdown_app(app_ctx)
        print("👋 Shutdown complete. Goodbye!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # suppress duplicate KeyboardInterrupt re-raise by asyncio.run
        pass
