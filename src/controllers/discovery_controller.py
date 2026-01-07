import json
import asyncio
from typing import Optional

from core.utils import Logger
from factory import MessageFactory, SubjectFactory
from core.comms import NatsPublisher


class DiscoveryController:
    """
    Ground-side discovery controller.

    Purpose:
    - Listen for UAV discovery requests
    - Respond with ground station presence & capabilities
    """

    def __init__(self, nats_client, ground_id: str, on_uav_discovered=None):
        self.client = nats_client
        self.publisher = NatsPublisher(nats_client)
        self.ground_id = ground_id
        self.remote_client_id = None

        self._on_uav_discovered = on_uav_discovered

        self._sub = None
        self.logger = Logger.get("Discovery")

    # ------------------------------
    # Public API (called by service)
    # ------------------------------

    async def activate(self):
        """Initialize subscriptions."""
        self.logger.info("Activating DiscoveryController...")
        await self._subscribe_to_requests()

    async def deactivate(self):
        """Clean unsubscribes."""
        if self._sub:
            try:
                await self.client.nc.unsubscribe(self._sub.sid)
            except Exception:
                pass

    # ------------------------------
    # Internal subscription setup
    # ------------------------------

    async def _subscribe_to_requests(self):
        """Subscribe to UAV discovery requests."""
        try:
            subject = self._build_subscribing_subject()
            self._sub = await self.client.nc.subscribe(
                subject,
                cb=self._on_discovery_request
            )

            self.logger.info(f"Subscribed to discovery requests: {subject}")

        except Exception as e:
            self.logger.error(f"Discovery subscribe failed: {e}")

    # ------------------------------
    # Callback
    # ------------------------------
    
    # cb with ws response
    async def _on_discovery_request(self, msg):
     """
     Handle incoming discovery request and respond.
     """
     try:
        # 1. Decode and parse the incoming message
        data_decoded = msg.data.decode()
        envelope = json.loads(data_decoded)
        
        # ---- STRICT SOURCE OF TRUTH ----
        # Extract the body which contains the UAV details
        uav_data = envelope.get("body", {})
        self.remote_client_id = uav_data.get("client_id")

        self.logger.info(
            f"Discovery request received from UAV [{self.remote_client_id}]"
        )

        # # 2. TRIGGER CALLBACK: Notify the external module that a UAV was found
        if self._on_uav_discovered:
            # We pass the uav_data (the dict) as expected by the method signature
            self._on_uav_discovered(uav_data)

        # 3. Respond back to the UAV
        subject = self._build_publishing_subject()
        response = self._build_response_message()

        await self.publisher.publish(subject, response)

        self.logger.info(
            f"Discovery response sent to UAV [{self.remote_client_id}]"
        )

        # testing fclink connect message
        # await asyncio.sleep(5)  # slight delay to ensure response is sent first
        # connrequest = "wannaconnect"
        # connsubject = self.build_connection_subject()
        # await self.client.nc.publish(connsubject, connrequest.encode())
        # self.logger.info(
        #     f"uav connection request sent to UAV [{self.remote_client_id}]"
        # )
        # await asyncio.sleep(10)
        # disconnrequest = "wannadisconnect"
        # disconnsubject = self.build_disconnection_subject()
        # await self.client.nc.publish(disconnsubject, disconnrequest.encode())
        # self.logger.info(
        #     f"uav disconnection request sent to UAV [{self.remote_client_id}]"
        # )
        #testing end

     except Exception as e:
        self.logger.error(f"Discovery request handling error: {e}")    
    
    # ------------------------------
    # Builders
    # ------------------------------

    def _build_publishing_subject(self):
        return SubjectFactory().create(
            source="ground",
            source_id=self.ground_id,
            topic="discovery",
            subtopic="response",
            mode="pub",
            remote_client_id=self.remote_client_id
        )
    
    def _build_subscribing_subject(self):
        return SubjectFactory().create(
            source="uav",
            source_id="*",
            topic="discovery",
            subtopic="request",
            mode="sub"
        )

    def _build_response_message(self):
        return MessageFactory.create(
            msg_type="discovery"
        )
    
    # def build_connection_subject(self):
    #     return SubjectFactory().create(
    #         source="ground",
    #         source_id=self.ground_id,
    #         topic="fclink",
    #         subtopic="connect",
    #         mode="pub",
    #         remote_client_id=self.remote_client_id
    #     )
    
    # def build_disconnection_subject(self):
    #     return SubjectFactory().create(
    #         source="ground",
    #         source_id=self.ground_id,
    #         topic="fclink",
    #         subtopic="disconnect",
    #         mode="pub",
    #         remote_client_id=self.remote_client_id
    #     )
