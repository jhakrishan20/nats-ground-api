"""
create_app.py
------------
Bootstraps and orchestrates all system-level services.
Responsible for initializing core components (NATS, logging, config)
and returning an AppContext used by the main entry point.
"""

import asyncio
from core.utils import Logger
from services import NetworkService


class AppContext:
    """Holds references to core services and clients."""
    def __init__(self, network_service):
        self.network_service = network_service
        self.logger = Logger.get("AppContext")


class AppBootstrap:
    """Handles creation and shutdown of core application context."""
    def __init__(self):
        self.logger = Logger.get("AppBootstrap")

    async def create_app(self) -> AppContext:
        """Initialize all required components and services."""
        self.logger.info("Starting system bootstrap...")

        # 1️⃣ Initialize services
        network_service = NetworkService()

        # 2️⃣ Start async services
        await network_service.start_service()

        self.logger.info("All services started successfully.")
        self.logger.info("Application ready.")

        # 3️⃣ Return application context
        return AppContext(network_service=network_service)

    async def shutdown_app(self, app_ctx: AppContext):
        """Gracefully stop all running services and connections."""
        self.logger.info("Shutting down services...")
        await app_ctx.network_service.stop_service()
        self.logger.info("Application shutdown complete.")
