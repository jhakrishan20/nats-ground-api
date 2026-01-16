# ws implementation

import asyncio
from typing import Optional
from config import ConfigLoader
from core.comms import NatsClient, NatsNode, WebSocketServer # IPCServer commented out
from core.utils import Logger
from controllers import DiscoveryController, FCLinkController, TelemetryController

class NetworkService:
    def __init__(self, config_file: str = "nats.yaml"):
        self.logger = Logger.get("NetworkService")
        self.loader = ConfigLoader()
        self.config = self.loader.get(config_file)
        self.loop = None  # Add this to store the reference
        
        self.client_id = "groundunit-001"
        self.node: Optional[NatsNode] = None
        self.ws_server: Optional[WebSocketServer] = None
        self.discovery: Optional[DiscoveryController] = None
        self.fclink: Optional[FCLinkController] = None
        
        # NATS Client Setup
        nats_cfg = self.config.get("nats", {})
        self.client = NatsClient(
            local_servers=nats_cfg.get("local_urls", []),
            name="groundunit-client",
        )

    async def start_service(self):
        """Lifecycle Start"""
        self.logger.info("Starting NetworkService...")

        try:
            # ✅ CAPTURE THE RUNNING LOOP HERE
            self.loop = asyncio.get_running_loop()

            # 1. Start NATS Node
            self.node = NatsNode(self.config.get("config_file", [])[0])
            await self.node.start()

            # 2. Connect NATS Client
            await self.client.connect()

            # Initialize FCLinkController
            self.fclink = FCLinkController(self.client, self.client_id, self.on_conn_response, self.on_disconn_response)
            await self.fclink.activate()

            # init telemetry controler
            self.telemetry = TelemetryController(self.client, self.client_id, self.on_telemetry_update)
            await self.telemetry.activate()

            # 3. Start WebSocket Server
            ws_cfg = self.config.get("ws", {})
            self.ws_server = WebSocketServer(
                host=ws_cfg.get("host", "0.0.0.0"),
                port=ws_cfg.get("port", 3000)
            )
            self.ws_server.start()
            self.register_ws_handlers()
            self.logger.info("All communication layers ready.")

        except Exception as e:
            self.logger.error(f"Startup failed: {e}")
            await self.stop_service()

    def register_ws_handlers(self):
        """Registers events for the WebSocket thread."""
        self.ws_server.listen_event("search_for_uavs", self._handle_ws_search_wrapper)
        # New FC Handlers
        self.ws_server.listen_event("connect_to_fc", self._handle_ws_fc_connect_wrapper)
        self.ws_server.listen_event("disconnect_from_fc", self._handle_ws_fc_disconnect_wrapper)

    def _handle_ws_search_wrapper(self, sid, data):
        """
        Internal wrapper to bridge the WS server (thread) 
        to the stored main event loop.
        """
        self.logger.info(f"WS Event 'search_for_uavs'")

        if self.loop and self.loop.is_running():
            # ✅ Use the stored loop reference instead of get_event_loop()
            asyncio.run_coroutine_threadsafe(self._handle_search_for_uavs(), self.loop)
        else:
            self.logger.error("Main event loop is not running. Cannot handle search.")

    async def _handle_search_for_uavs(self):
        """The actual async logic."""
        self.logger.info("Triggering UAV Discovery logic...")
        try:
            if self.discovery:
                await self.discovery.deactivate()

            self.discovery = DiscoveryController(
                self.client,
                self.client_id,
                on_uav_discovered=self._on_uav_discovered
            )
            await self.discovery.activate()
        except Exception as e:
            self.logger.error(f"Discovery failed: {e}")

    def _on_uav_discovered(self, uav_data: dict):
        """Callback from controller to send data back to WS clients."""
        self.logger.info(f"Found: {uav_data.get('client_id')}")
        self.logger.info(f"{uav_data}")
        if self.ws_server:
            self.ws_server.send_event("uav_discovered", uav_data)


    # --- FC Connection Wrappers ---

    def _handle_ws_fc_connect_wrapper(self, sid, data):
        self.logger.info(f"WS Event 'connect_to_fc' from {sid}")
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self._handle_fc_connect(data), self.loop)

    def _handle_ws_fc_disconnect_wrapper(self, sid, data):
        self.logger.info(f"WS Event 'disconnect_from_fc' from {sid}")
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self._handle_fc_disconnect(data), self.loop)

    # --- Core FC Logic (Completed) ---

    async def _handle_fc_connect(self, data: dict):
        """Logic to establish connection with the Flight Controller via NATS."""
        uav_id: str = self.discovery.remote_client_id if self.discovery else "airunit-001" #TODO-remove the hardcode of id

        self.logger.info(f"Attempting to trigger FC connect for UAV: {uav_id}")
        
        try:
            if self.fclink:
                # Use the FCLinkController to build the subject and publish to NATS
                await self.fclink.send_connect_request(uav_id)
            else:
                self.logger.error("FCLinkController not initialized")

        except Exception as e:
            self.logger.error(f"Failed to relay FC Connection command: {e}")

    async def _handle_fc_disconnect(self, data: dict):
        """Logic to tear down connection with the Flight Controller via NATS."""
        uav_id: str = self.discovery.remote_client_id if self.discovery else "airunit-001" #TODO-remove the hardcode of id

        self.logger.info(f"Attempting to trigger FC disconnect for UAV: {uav_id}")
        
        try:
            if self.fclink:
                # Use the FCLinkController to build the subject and publish to NATS
                await self.fclink.send_disconnect_request(uav_id)
            else:
                self.logger.error("FCLinkController not initialized")

        except Exception as e:
            self.logger.error(f"Failed to relay FC Disconnection command: {e}")

    async def on_conn_response(self, conn_response: dict):
        """Sends connection response back to WS clients."""
        try:
            self.logger.info(f"Got response for fc-connection: {conn_response}")
            if self.ws_server:
                self.ws_server.send_event("fc_conn_res", conn_response)
        except Exception as e:
            self.logger.error(f"Failed to send FC connection response: {e}")

    async def on_disconn_response(self, disconn_response: dict):
        """Sends disconnection response back to WS clients."""
        try:
            self.logger.info(f"Got response for fc-disconnection: {disconn_response}")
            if self.ws_server:
                self.ws_server.send_event("fc_disconn_res", disconn_response)
        except Exception as e:
            self.logger.error(f"Failed to send FC disconnection response: {e}")

    async def on_telemetry_update(self, telemetry_data:dict):
        try:
            if self.ws_server:
                self.ws_server.send_event("telemetry_update", telemetry_data)
        except Exception as e:
            self.logger.error(f"Failed to send telemetry update: {e}")

    async def stop_service(self):
        """Lifecycle Stop"""
        self.logger.info("Shutting down...")
        if self.discovery:
            await self.discovery.deactivate()
        if self.ws_server:
            self.ws_server.stop()
        if self.client:
            await self.client.close()
        if self.node:
            await self.node.stop()


# ipc implementation

# import asyncio
# from typing import Optional

# from flask import json
# from config import ConfigLoader
# from core.comms import NatsClient, NatsNode, IPCServer  # WS Server removed
# from core.utils import Logger
# from controllers import DiscoveryController

# class NetworkService:
#     def __init__(self, config_file: str = "nats.yaml"):
#         self.logger = Logger.get("NetworkService")
#         self.loader = ConfigLoader()
#         self.config = self.loader.get(config_file)
#         self.loop = None  # To be captured at startup
        
#         self.client_id = "groundunit-001"
#         self.node: Optional[NatsNode] = None
#         self.ipc: Optional[IPCServer] = None
#         self.discovery: Optional[DiscoveryController] = None
        
#         # NATS Client Setup
#         nats_cfg = self.config.get("nats", {})
#         self.client = NatsClient(
#             local_servers=nats_cfg.get("local_urls", []),
#             name="groundunit-client",
#         )

#     async def start_service(self):
#         """Lifecycle Start: Captures loop and initializes components."""
#         # ✅ CAPTURE THE RUNNING LOOP (Main Thread)
#         self.loop = asyncio.get_running_loop()
#         self.logger.info("Starting NetworkService (IPC Mode)...")

#         try:
#             # 1. Start NATS Node and Client
#             self.node = NatsNode(self.config.get("config_file", [])[0])
#             await self.node.start()
#             await self.client.connect()

#             # 2. Start IPC Server
#             # Assuming IPCServer config is nested in your YAML
#             ipc_cfg = self.config.get("ipc", {})
#             self.ipc = IPCServer(main_loop=self.loop) 
#             self.ipc.start()
            
#             # register_ipc_handlers
#             self.ipc.register_command_handler(self._handle_search_for_uavs)

#             self.logger.info("IPC communication layer ready.")

#         except Exception as e:
#             self.logger.error(f"Startup failed: {e}")
#             await self.stop_service()

#     def register_ipc_handlers(self):
#         """Registers the main command listener for IPC messages."""
#         if self.ipc:
#             self.ipc.register_command_handler(self._handle_ipc_command_wrapper)
#             self.logger.info("IPC command handlers registered.")

#     async def _handle_ipc_command_wrapper(self, msg: dict):
#      """
#      Modified to be 'async' to satisfy the IPCServer's requirement.
#      """
#      action = msg.get("action")
#      self.logger.info(f"IPC Command received: {action}")

#      if action == "search_for_uavs":
#         if self.loop and self.loop.is_running():
#             # Still jump to the main loop for the actual discovery logic
#             asyncio.run_coroutine_threadsafe(self._handle_search_for_uavs(), self.loop)
#      else:
#         self.logger.warning(f"Unknown IPC action: {action}")

#     async def _handle_search_for_uavs(self):
#         """The actual async logic executed on the main event loop."""
#         self.logger.info("Triggering UAV Discovery logic via IPC...")
#         try:
#             # Reset discovery if already active
#             if self.discovery:
#                 await self.discovery.deactivate()

#             self.discovery = DiscoveryController(
#                 self.client,
#                 self.client_id,
#                 on_uav_discovered=self._on_uav_discovered
#             )
#             await self.discovery.activate()
#         except Exception as e:
#             self.logger.error(f"Discovery activation failed: {e}")

#     def _on_uav_discovered(self, uav_data: dict):
#      """Callback from DiscoveryController: Broadcasts result back to IPC."""
#      self.logger.info(f"UAV Found: {uav_data.get('client_id')}")
    
#      if self.ipc:
#         try:
#             # Use the method we know exists: send_event
#             # We wrap the data in the format your Qt client expects
#             self.ipc.send_event({
#                 "event": "uav_discovered",
#                 "data": uav_data
#             })
#             self.logger.info("Successfully sent discovery data to IPC.")
#         except Exception as e:
#             self.logger.error(f"Failed to send IPC event: {e}")
#      else:
#         self.logger.warning("IPC server not initialized, cannot send discovery data.")

#     async def stop_service(self):
#         """Lifecycle Stop: Graceful shutdown of all components."""
#         self.logger.info("Shutting down service...")
        
#         if self.discovery:
#             await self.discovery.deactivate()
        
#         if self.ipc:
#             self.ipc.stop()
#             self.logger.info("IPC server stopped.")
            
#         if self.client:
#             await self.client.close()
            
#         if self.node:
#             await self.node.stop()
            
#         self.logger.info("Service shutdown complete.")