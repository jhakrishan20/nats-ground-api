"""
nats_node.py
------------
Manages the local NATS server process for the Air Unit.
This module abstracts away all node lifecycle and configuration concerns.
"""

import asyncio
import subprocess
import os
import signal
from pathlib import Path
from core.utils import Logger


class NatsNode:
    """
    Handles lifecycle management of the local NATS server instance.
    The Discovery Controller and NATS client use this node indirectly.
    """

    def __init__(self, config_path: str):
        """
        Args:
            config_path (str): Path to the NATS server config file (.conf or .yaml).
        """
        self.config_path = Path(config_path)
        self.process: subprocess.Popen | None = None
        self.logger = Logger.get("NATS-Node")

    async def start(self):
        """Start the local NATS node using the provided configuration."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"NATS config file not found: {self.config_path}")

        cmd = ["nats-server", "-c", str(self.config_path)]
        self.logger.info(f"Starting NATS node with config: {self.config_path}")

        try:
            # Start in config's directory so relative paths in .conf work
            self.process = subprocess.Popen(
                cmd,
                cwd=str(self.config_path.parent),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            # Create a background task to stream NATS logs live
            asyncio.create_task(self._stream_output())

            # Give the server a short warmup time
            await asyncio.sleep(2)

            if not self.is_running():
                self.logger.error("NATS process exited unexpectedly during startup.")
                raise RuntimeError("Failed to start NATS server")

            self.logger.info("✅ Local NATS node started successfully.")
        except Exception as e:
            self.logger.error(f"❌ Failed to start NATS node: {e}")
            raise

    async def _stream_output(self):
        """Asynchronously stream and log NATS server output."""
        if not self.process or not self.process.stdout:
            return

        try:
            while True:
                line = await asyncio.to_thread(self.process.stdout.readline)
                if not line:
                    break
                self.logger.info(f"[NATS] {line.strip()}")
        except Exception as e:
            self.logger.debug(f"Log stream ended: {e}")

    async def stop(self):
        """Gracefully stop the local NATS server."""
        if not self.process:
            self.logger.warning("⚠️ NATS node not running.")
            return

        self.logger.info("⏹️ Stopping NATS node...")
        try:
            if os.name == "nt":
                self.process.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                self.process.terminate()

            await asyncio.sleep(1)
            self.process.wait(timeout=5)
            self.logger.info("✅ NATS node stopped successfully.")
        except Exception as e:
            self.logger.error(f"Error stopping NATS node: {e}")
        finally:
            self.process = None

    def is_running(self) -> bool:
        """Check if the NATS server process is active."""
        return self.process is not None and self.process.poll() is None

    def get_connection_uri(self) -> str:
        """
        Returns the expected local NATS server URI.
        This is what the NATS client will connect to.
        """
        return "nats://127.0.0.1:4222"
