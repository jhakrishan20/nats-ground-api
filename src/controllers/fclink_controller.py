import json
import asyncio
from typing import Optional

from core.utils import Logger
from factory import MessageFactory, SubjectFactory
from core.comms import NatsPublisher

class FCLinkController:
    """
    Ground-side Flight Controller Link Controller.
    
    Purpose:
    - Manage connection/disconnection triggers to remote UAVs.
    - Handle MAVLink or serial bridge state commands via NATS.
    """

    def __init__(self, nats_client, ground_id: str):
        self.client = nats_client
        self.publisher = NatsPublisher(nats_client)
        self.ground_id = ground_id
        self.logger = Logger.get("FCLink")

    # ------------------------------
    # Public API
    # ------------------------------

    async def send_connect_request(self, uav_id: str):
        """Send a 'wannaconnect' trigger to a specific UAV."""
        subject = self._build_fc_subject(uav_id, "connect")
        # You can use a raw string like your test or a Factory message
        # payload = MessageFactory.create(
        #     msg_type="fclink", 
        #     command="connect",
        #     sender=self.ground_id
        # )
        payload = "wannaconnect"  # Simple string as per your test case
        # await self.publisher.publish(subject, payload)
        await self.client.nc.publish(subject, payload.encode())
        self.logger.info(f"🚀 Sent FC Connect request to [{uav_id}] on {subject}")

    async def send_disconnect_request(self, uav_id: str):
        """Send a 'wannadisconnect' trigger to a specific UAV."""
        subject = self._build_fc_subject(uav_id, "disconnect")
        # payload = MessageFactory.create(
        #     msg_type="fclink", 
        #     command="disconnect",
        #     sender=self.ground_id
        # )
        payload = "wannadisconnect"  # Simple string as per your test case      
        
        # await self.publisher.publish(subject, payload)
        await self.client.nc.publish(subject, payload.encode())
        self.logger.info(f"⏹️ Sent FC Disconnect request to [{uav_id}] on {subject}")

    # ------------------------------
    # Subject Builders
    # ------------------------------

    def _build_fc_subject(self, uav_id: str, subtopic: str):
        """
        Builds: ground.<ground_id>.fclink.<connect/disconnect>
        With remote_client_id directed at the specific UAV.
        """
        return SubjectFactory().create(
            source="ground",
            source_id=self.ground_id,
            topic="fclink",
            subtopic=subtopic,
            mode="pub",
            remote_client_id=uav_id
        )