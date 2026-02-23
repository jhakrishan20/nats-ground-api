import json
import asyncio
from typing import Optional

from core.utils import Logger
from factory import MessageFactory, SubjectFactory
from core.comms import NatsPublisher

class CommandEgressController:
    """
    Ground-side Command Relay controller.
    
    Purpose:
    """

    def __init__(self, nats_client, ground_id: str, on_conn_response=None, on_disconn_response=None, on_mission_upload_response=None):
        self.client = nats_client
        self.publisher = NatsPublisher(nats_client)
        self.ground_id = ground_id
        self.logger = Logger.get("CommandEgress")
        self._on_fcconnect_response = on_conn_response
        self._on_fcdisconnect_response = on_disconn_response
        self._on_mission_upload_response = on_mission_upload_response

    # ------------------------------
    # Public API
    # ------------------------------
    async def activate(self):
        """Initialize any required subscriptions or state."""
        self.logger.info("Activating FCLinkController...")
        # Add subscription setups if needed
        await self._subscribe_to_fc_responses()
        await self._subscribe_to_mission_upload_response()

    async def send_connect_request(self, uav_id: str):
        """Send a 'wannaconnect' trigger to a specific UAV."""
        subject = self._build_fcconnect_pub_subject(uav_id)
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
        subject = self._build_fcdisconnect_pub_subject(uav_id)
        # payload = MessageFactory.create(
        #     msg_type="fclink", 
        #     command="disconnect",
        #     sender=self.ground_id
        # )
        payload = "wannadisconnect"  # Simple string as per your test case      
        
        # await self.publisher.publish(subject, payload)
        await self.client.nc.publish(subject, payload.encode())
        self.logger.info(f"⏹️ Sent FC Disconnect request to [{uav_id}] on {subject}")

    async def send_mission(self, uav_id: str, mission):
        """Send mission to a specific UAV."""
        subject = self._build_mission_upload_pub_subject(uav_id)
        # payload = MessageFactory.create(
        #     msg_type="mission",
        #     command="update",
        #     sender=self.ground_id,
        #     body={"mission": mission}
        # )
        payload = json.dumps(mission)
        await self.client.nc.publish(subject, payload.encode())
        self.logger.info(f"📍 Sent {len(mission)} mission items to [{uav_id}] on {subject}")    

    # ------------------------------
    # Subscription Handelers
    # ------------------------------

    async def _subscribe_to_fc_responses(self):
        """Subscribe to UAV FCLink connect/disconnect responses."""
        # Subscribe to connect responses
        subject = self._build_fcconnect_sub_subject()
        await self.client.nc.subscribe(
            subject,
            cb=self._fcconnect_response_cb
        )
        # Subscribe to disconnect responses
        subject = self._build_fcdisconnect_sub_subject()
        await self.client.nc.subscribe(
            subject,
            cb=self._fcdisconnect_response_cb
        )
        self.logger.info(f"Subscribed to fc responses")

    async def _subscribe_to_mission_upload_response(self):
        """Subscribe to UAV response for mission upload."""
        subject =  self._build_mission_upload_sub_subject()
        await self.client.nc.subscribe(
            subject,
            cb=self._mission_upload_response_cb
        )
        self.logger.info(f"Subscribed to waypoint upload response")    

    # ------------------------------
    # Subject Builders
    # ------------------------------

    def _build_fcconnect_pub_subject(self, uav_id: str):
        """
        Builds: ground.<ground_id>.fcconnect.<request/response>
        With remote_client_id directed at the specific UAV.
        """
        return SubjectFactory().create(
            source="ground",
            source_id=self.ground_id,
            topic="fcconnect",
            subtopic="request",
            mode="pub",
            remote_client_id=uav_id
        )

    def _build_fcdisconnect_pub_subject(self, uav_id: str):
        """
        Builds: ground.<ground_id>.fcdisconnect.<request/response>
        With remote_client_id directed at the specific UAV.
        """
        return SubjectFactory().create(
            source="ground",
            source_id=self.ground_id,
            topic="fcdisconnect",
            subtopic="request",
            mode="pub",
            remote_client_id=uav_id
        )
    
    def _build_mission_upload_pub_subject(self, uav_id: str):
        """
        Builds: ground.<ground_id>.mission_upload.request
        For publishing waypoint upload requests to a specific UAV.
        """
        return SubjectFactory().create(
            source="ground",
            source_id=self.ground_id,
            topic="mission_upload",
            subtopic="request",
            mode="pub",
            remote_client_id=uav_id
        )
    
    
    def _build_fcconnect_sub_subject(self):
        """
        Builds: uav.*.fcconnect.response
        For subscribing to connect requests from any UAV.
        """
        return SubjectFactory().create(
            source="uav",
            source_id="*",
            topic="fcconnect",
            subtopic="response",
            mode="sub"
        )
    
    def _build_fcdisconnect_sub_subject(self):
        """
        Builds: uav.*.fcdisconnect.response
        For subscribing to disconnect requests from any UAV.
        """
        return SubjectFactory().create(
            source="uav",
            source_id="*",
            topic="fcdisconnect",
            subtopic="response",
            mode="sub"
        )
    
    def _build_mission_upload_sub_subject(self):
        """
        Builds: uav.*.mission_upload.response
        For subscribing to waypoint upload responses from any UAV.
        """
        return SubjectFactory().create(
            source="uav",
            source_id="*",
            topic="mission_upload",
            subtopic="response",
            mode="sub"
        )
    
    # ------------------------------
    # Callbacks
    # ------------------------------

    async def _fcconnect_response_cb(self, msg):
        """
        Callback for uav.*.fcconnect.response
        Extracts data from NATS Msg and forwards to WebSocket.
        """
        try:
            # 1. Extract and Decode the NATS data
            # msg is a nats.aio.msg.Msg object
            raw_payload = msg.data.decode()
            data = json.loads(raw_payload)
            
            # 2. Extract the 'body' specifically (the part with {connected: True})
            body = data.get("body", {})
            
            # 3. Format the WebSocket message
            # ws_msg = {
            #     "type": "fc_connection_res",
            #     "payload": body
            # }
            
            # 4. Forward to the GCS (assuming self.ws_manager or similar)
            await self._on_fcconnect_response(body)
            self.logger.info(f"✅ Forwarded FC Connect response to GCS: {body}")

        except Exception as e:
            self.logger.error(f"Error handling fcconnect callback: {e}")

    async def _fcdisconnect_response_cb(self, msg):
        """
        Callback for uav.*.fcdisconnect.response
        """
        try:
            raw_payload = msg.data.decode()
            data = json.loads(raw_payload)
            body = data.get("body", {})
            
            # ws_msg = {
            #     "type": "fc_disconnection_res",
            #     "payload": body
            # }

            await self._on_fcdisconnect_response(body)
            self.logger.info(f"✅ Forwarded FC Disconnect response to GCS: {body}")

        except Exception as e:
            self.logger.error(f"Error handling fcdisconnect callback: {e}")

    async def _mission_upload_response_cb(self, msg):
        """
        Callback for uav.*.mission_upload.response
        """
        try:
            raw_payload = msg.data.decode()
            data = json.loads(raw_payload)
            body = data.get("body", {})
            
            # Here you would forward this to the GCS as needed, e.g.:
            # ws_msg = {
            #     "type": "mission_upload_res",
            #     "payload": body
            # }
            await self._on_mission_upload_response(body)
            self.logger.info(f"✅ Received Mission Upload response: {body}")

        except Exception as e:
            self.logger.error(f"Error handling Mission upload response callback: {e}")        