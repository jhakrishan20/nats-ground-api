# """
# comms_service.py
# ----------------
# Manages NATS communication lifecycle.
# Handles connection, discovery initialization, and graceful recovery.
# """

# import asyncio
# from typing import Optional

# from config import ConfigLoader
# from core.comms import NatsClient, NatsNode, IPCServer, WebSocketServer
# from core.utils import Logger
# from controllers import DiscoveryController


# class NetworkService:
#     """
#     Network Service for the Air Unit.
#     Loads config, initializes NATS client, manages lifecycle and discovery.
#     """

#     def __init__(self, config_file: str = "nats.yaml"):
#         self.logger = Logger.get("NetworkService")
#         self.loader = ConfigLoader()
#         self.connected_to_ground = False

#         self.node: Optional[NatsNode] = None
#         self.ipc: Optional[IPCServer] = None
#         self.ws_server: Optional[WebSocketServer] = None

#         try:
#             self.config = self.loader.get(config_file)
#         except Exception as e:
#             self.logger.error(f"Failed to load config '{config_file}': {e}")
#             raise

#         # ✅ Centralized client ID generation
#         # try:
#         #     self.client_id = Identity.generate(self.config)
#         # except Exception as e:
#         #     self.logger.error(f"Failed to generate client ID: {e}")
#         #     raise

#         self.client_id = "groundunit-001"  # Temporary hardcoded ID for testing

#         try:
#            nats_cfg = self.config.get("nats", {})
#            conn_cfg = self.config.get("connection", {})
#            client_cfg = self.config.get("client", {})

#            self.client: Optional[NatsClient] = NatsClient(
#                local_servers=nats_cfg.get("local_urls", []),
#                name=f"{client_cfg.get('name', 'airunit-client')}-{client_cfg.get('id', '000')}",
#                reconnect_wait=conn_cfg.get("reconnect_wait", 2),
#                max_reconnect_attempts=conn_cfg.get("max_reconnect_attempts", -1),
#            )
#         except Exception as e:
#            self.logger.error(f"Failed to initialize NATS client: {e}")

#         # self.discovery: Optional[DiscoveryController] = None

#     async def start_service(self):
#         """Start NATS node, NATS client, and Discovery process."""
#         self.logger.info("Starting NetworkService...")

#         # ---------------------------
#         # 1) Start NATS Node
#         # ---------------------------
#         try:
#             self.node = NatsNode(self.config.get("config_file", [])[0])
#             await self.node.start()
#             self.logger.info("NATS node started.")
#         except Exception as e:
#             self.logger.error(f"Could not start NATS node: {e}")
#             await self.stop_service()
#             return

#         # ---------------------------
#         # 2) Start NATS Client
#         # ---------------------------
#         try:
#             await self.client.connect()
#             self.logger.info("NATS client connected.")
#         except Exception as e:
#             self.logger.error(f"Could not connect NATS client: {e}")
#             await self.stop_service()
#             return
        
#         # # # ---------------------------
#         # # # 3) Start IPC Server
#         # # # ---------------------------
#         # loop = asyncio.get_running_loop()
#         # try:
#         #     self.ipc = IPCServer(main_loop=loop)
#         #     self.ipc.start()
#         #     self.logger.info("IPC server started.")
#         #     self.register_ipc_handlers()
#         #     self.logger.info("IPC handlers registered.")
#         # except Exception as e:
#         #     self.logger.error(f"Could not start IPC server: {e}")
#         #     await self.stop_service()
#         #     return

#         # start ws server
#         # try:
#         #     self.ws_server = WebSocketServer()
#         #     self.ws_server.start()
#         #     self.logger.info("WebSocket server started.")
#         #     self.register_ws_handlers()
#         #     self.logger.info("WebSocket handlers registered.")
#         # except Exception as e:
#         #     self.logger.error(f"Could not start WebSocket server: {e}")
#         #     await self.stop_service()
#         #     return  
        
#         # # # ---------------------------
#         # 4) Initialize Discovery Controller
#         # ---------------------------
#         try:
#             self.discovery = DiscoveryController(self.client, self.client_id)
#             await self.discovery.activate()  # sets up subscriptions
#             self.logger.info("DiscoveryController activated.")
#         except Exception as e:
#             self.logger.error(f"Failed to activate DiscoveryController: {e}")
#             await self.stop_service()
#             return
    
#     # ------------------------------
#     # Handlers 
#     # ------------------------------

    

#     async def stop_service(self):
#         """Gracefully stop service and disconnect client."""
#         self.logger.info("Shutting down...")

#         try:
#             if self.discovery:
#                 await self.discovery.deactivate()
#                 self.logger.info("DiscoveryController deactivated.")

#         except Exception as e:
#             self.logger.warning(f"Error during DiscoveryController deactivation: {e}")

#         # try:
#         #     # if self.ipc_server:
#         #         print(self.ipc)
#         #         await self.ipc.stop()
#         #         self.logger.info("IPC server stopped.")

#         # except Exception as e:
#         #     self.logger.warning(f"Error closing IPC server: {e}")

#         try:
#             if self.ws_server:
#                 self.ws_server.stop()
#                 self.logger.info("WebSocket server stopped.")
#         except Exception as e:
#             self.logger.warning(f"Error closing WebSocket server: {e}")     

#         try:
#             if self.client:
#                 await self.client.close()
#                 self.logger.info("NATS client closed.")
#         except Exception as e:
#             self.logger.warning(f"Error closing NATS connection: {e}")

#         try:
#             if self.node:
#                 await self.node.stop()
#                 self.logger.info("NATS node stopped.")
#         except Exception as e:
#             self.logger.warning(f"Error closing NATS node: {e}")

#         self.logger.info("Service shutdown complete.")

        
#     # -------------------------------------------------
#     # IPC HANDLER REGISTRATION (CALLED AT STARTUP)
#     # -------------------------------------------------

#     # def register_ipc_handlers(self):
#     #     """
#     #     Register IPC command handlers with the IPC server.
#     #     This should be called ONCE during service startup.
#     #     """
#     #     self.ipc.register_command_handler(
#     #         self._handle_ipc_command
#     #     )

#     #     self.logger.info("IPC command handlers registered.")

#     # # -------------------------------------------------
#     # # IPC COMMAND ENTRY POINT (Qt → Ground)
#     # # -------------------------------------------------

#     # async def _handle_ipc_command(self, msg: dict):
#     #     """
#     #     Central IPC command router.
#     #     """
#     #     action = msg.get("action")

#     #     if action == "search_for_uavs":
#     #         await self._handle_search_for_uavs()

#     #     # elif action == "stop_search_for_uavs":
#     #     #     await self._handle_stop_search()

#     #     else:
#     #         self.logger.warning(f"Unknown IPC action: {action}")

#     # -------------------------------------------------
#     # ws handeler registration
#     # -------------------------------------------------
#     def register_ws_handlers(self):
#      """
#      Register WebSocket event handlers with the WS server.
#      This should be called after self.ws_server.start().
#      """
#      if not hasattr(self, 'ws_server') or self.ws_server is None:
#         self.logger.error("WS Server not initialized. Cannot register handlers.")
#         return

#      # Register the search event
#      self.ws_server.listen_event(
#         "search_for_uavs", 
#         self._handle_ws_search_wrapper
#      )

#      # You can add more events here as you expand
#      # self.ws_server.listen_event("add_uav", self._handle_add_uav_wrapper)

#      self.logger.info("WebSocket handlers registered.")

#     def _handle_ws_search_wrapper(self, sid, data):
#      """
#      Internal wrapper to bridge the WS server (thread) 
#      to your class logic.
#      """
#      self.logger.info(f"WS Event 'search_for_uavs' triggered by {sid}")
#      # Call your internal logic method
#      self._handle_search_for_uavs()        

#     # -------------------------------------------------
#     # INTERNAL ACTION HANDLERS
#     # -------------------------------------------------

#     async def _handle_search_for_uavs(self):
#         """
#         Triggered when Qt requests UAV discovery.
#         """

#         self.logger.info("Starting UAV discovery (IPC-triggered).")

#         try:
#             self.discovery = DiscoveryController(
#                 self.client,
#                 self.client_id,
#                 on_uav_discovered=self._on_uav_discovered
#             )

#             await self.discovery.activate()
#             self.logger.info("DiscoveryController activated.")

#         except Exception as e:
#             self.logger.error(f"Failed to activate DiscoveryController: {e}")
#             self.discovery = None

#     # async def _handle_stop_search(self):
#     #     """
#     #     Stop UAV discovery.
#     #     """
#     #     if not self.discovery:
#     #         return

#     #     self.logger.info("Stopping UAV discovery.")

#     #     await self.discovery.deactivate()
#     #     self.discovery = None

#     # -------------------------------------------------
#     # CONTROLLER → SERVICE CALLBACK
#     # -------------------------------------------------

#     def _on_uav_discovered(self, uav_data: dict):
#         """
#         Called by DiscoveryController when a UAV is found.
#         """
#         self.logger.info(
#             f"UAV discovered: {uav_data.get('client_id')}"
#         )

#         # self.ipc.send_event({
#         #     "event": "uav_discovered",
#         #     "data": uav_data
#         # })
#         self.ws_server.send_event(
#             "uav_discovered",
#             uav_data
#         )

# ws implementation

import asyncio
from typing import Optional
from config import ConfigLoader
from core.comms import NatsClient, NatsNode, WebSocketServer # IPCServer commented out
from core.utils import Logger
from controllers import DiscoveryController, FCLinkController

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
            self.fclink = FCLinkController(self.client, self.client_id)

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
        self.logger.info(f"WS Event 'search_for_uavs' triggered by {sid}")

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
        uav_id = data.get("uav_id")
        if not uav_id:
            self.logger.error("FC Connect failed: No uav_id provided in WS data")
            return

        self.logger.info(f"Attempting to trigger FC connect for UAV: {uav_id}")
        
        try:
            if self.fclink:
                # Use the FCLinkController to build the subject and publish to NATS
                await self.fclink.send_connect_request(uav_id)
                
                # Notify the WS client that the command was successfully RELAYED
                self.ws_server.send_event("fc_status", {
                    "uav_id": uav_id, 
                    "status": "command_sent",
                    "action": "connect"
                })
            else:
                self.logger.error("FCLinkController not initialized")

        except Exception as e:
            self.logger.error(f"Failed to relay FC Connection command: {e}")

    async def _handle_fc_disconnect(self, data: dict):
        """Logic to tear down connection with the Flight Controller via NATS."""
        uav_id = data.get("uav_id")
        if not uav_id:
            self.logger.error("FC Disconnect failed: No uav_id provided in WS data")
            return

        self.logger.info(f"Attempting to trigger FC disconnect for UAV: {uav_id}")
        
        try:
            if self.fclink:
                # Use the FCLinkController to build the subject and publish to NATS
                await self.fclink.send_disconnect_request(uav_id)
                
                # Notify the WS client
                self.ws_server.send_event("fc_status", {
                    "uav_id": uav_id, 
                    "status": "command_sent",
                    "action": "disconnect"
                })
            else:
                self.logger.error("FCLinkController not initialized")

        except Exception as e:
            self.logger.error(f"Failed to relay FC Disconnection command: {e}")        

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