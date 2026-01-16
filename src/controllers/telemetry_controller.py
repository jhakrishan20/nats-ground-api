import json
import asyncio
from typing import Optional

from core.utils import Logger
from factory import MessageFactory, SubjectFactory
# from core.comms import NatsPublisher


class TelemetryController:
    """
    Handles incoming NATS telemetry from the Air Unit using a 
    standardized subject pattern and forwards body data to GCS.
    """
    def __init__(self, nats_client, client_id, on_telemetry_update):
        self.logger = Logger.get("Telemetry")
        
        self.client = nats_client
        self.client_id = client_id
        self.on_telemetry_update = on_telemetry_update
        
        self.subscription = None

    def _build_subscribing_subject(self):
        """
        Builds the NATS subject string using the SubjectFactory.
        Uses wildcard '*' for source_id to capture telemetry updates.
        """
        return SubjectFactory().create(
            source="uav",
            source_id="*",
            topic="telemetry",
            subtopic="update",
            mode="sub"
        )

    async def activate(self):
        """
        Subscribes to the generated subject and starts the listener.
        """
        try:
            subject = self._build_subscribing_subject()

            # Subscribe with the internal callback handler
            self.subscription = await self.client.nc.subscribe(
                subject, 
                cb=self._handle_incoming_telemetry
            )
            
            self.logger.info(f"📡 Ground Telemetry active. Listening on: {subject}")

        except Exception as e:
            self.logger.error(f"Failed to activate Ground Telemetry: {e}")

    async def _handle_incoming_telemetry(self, msg):
        """
        Decodes NATS message, extracts 'body', and forwards to GCS callback.
        """
        try:
            # 1. Decode and Load JSON
            raw_payload = msg.data.decode()
            data = json.loads(raw_payload)
            
            # 2. Extract the 'body' specifically
            body = data.get("body", {})
            
            # # 3. Format the WebSocket message
            # ws_msg = {
            #     "type": "telemetry_update",
            #     "payload": body
            # }
            
            # 4. Forward to the GCS via the constructor-provided callback
            await self.on_telemetry_update(body)
            
            # Optional: Log success for debugging (high frequency)
            # self.logger.debug(f"Forwarded telem body for {data.get('header', {}).get('source', 'unknown')}")

        except json.JSONDecodeError:
            self.logger.error("Failed to decode telemetry JSON: invalid format")
        except Exception as e:
            self.logger.error(f"Error in Ground Telemetry handler: {e}")

    async def deactivate(self):
        """
        Gracefully unsubscribes from the telemetry topic.
        """
        if self.subscription:
            try:
                await self.subscription.unsubscribe()
                self.logger.info("Ground Telemetry unsubscribed.")
            except Exception as e:
                self.logger.warning(f"Error during telemetry unsubscription: {e}")