"""
nats_client.py
---------
Simplified NATS client for Edge/Air Unit.
Connects only to the local NATS server (nats-node).
"""

import nats
from nats.js import JetStreamContext
from typing import Optional
from core.utils import Logger


class NatsClient:
    def __init__(
        self,
        local_servers: Optional[list[str]] = None,
        name: Optional[str] = None,
        reconnect_wait: Optional[int] = 2,
        max_reconnect_attempts: Optional[int] = -1,
    ):
        """
        NATS Client wrapper for Edge/Air unit.

        Args:
            local_servers: List of local NATS server URLs (default: ['nats://127.0.0.1:4222']).
            name: Client name for monitoring/visibility.
            reconnect_wait: Wait time (sec) between reconnects.
            max_reconnect_attempts: Max reconnect retries (-1 = infinite).
        """
        self.local_servers = local_servers or ["nats://127.0.0.1:4222"]
        self.name = name or "edge-nats-client"
        self.reconnect_wait = reconnect_wait
        self.max_reconnect_attempts = max_reconnect_attempts
        self.logger = Logger.get("NatsClient")

        self.nc: Optional[nats.NATS] = None
        self.js: Optional[JetStreamContext] = None

    async def connect(self) -> bool:
        """
        Connect to the local NATS node.
        Returns True if connection is successful.
        """
        try:
            opts = {
                "servers": self.local_servers,
                "name": self.name,
                "reconnect_time_wait": self.reconnect_wait,
                "max_reconnect_attempts": self.max_reconnect_attempts,
            }

            if self.logger:
                self.logger.info(f"Connecting to local NATS server at {self.local_servers}...")
            else:
                print(f"Connecting to local NATS server at {self.local_servers}...")

            self.nc = await nats.connect(**opts)
            self.js = self.nc.jetstream()

            if self.logger:
                self.logger.info("Connected to local NATS successfully.")
            else:
                print("✅ Connected to local NATS successfully.")

            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to connect to local NATS: {e}")
            else:
                print(f"❌ Failed to connect to local NATS: {e}")
            return False

    async def close(self) -> bool:
        """Close the connection gracefully."""
        try:
            if self.nc:
                await self.nc.close()
                self.nc = None
                self.js = None
                if self.logger:
                    self.logger.info("Closed connection to local NATS.")
                else:
                    print("🛑 Closed connection to local NATS.")
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error while closing NATS connection: {e}")
            else:
                print(f"❌ Error while closing NATS connection: {e}")
            return False
