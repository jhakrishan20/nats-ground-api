# import threading
# from flask import Flask, request
# from flask_socketio import SocketIO

# class WebSocketServer:
#     def __init__(self, host="0.0.0.0", port=5000):
#         self.app = Flask(__name__)
#         # cors_allowed_origins="*" is essential for testing with different clients
#         self.socketio = SocketIO(self.app, cors_allowed_origins="*")
#         self.host = host
#         self.port = port
#         self.server_thread = None
#         self.is_running = False

#     def listen_event(self, event_name, callback):
#         """
#         Dynamically registers a listener for any event name.
#         The callback should accept (data) or (sid, data).
#         """
#         @self.socketio.on(event_name)
#         def handle_generic(data):
#             # We provide the request.sid in case the logic needs to know WHO sent it
#             callback(request.sid, data)
        
#         print(f"Registered listener for: {event_name}")

#     def send_event(self, event_name, data, to=None):
#         """
#         Sends an event to clients.
#         :param event_name: The string name (e.g., 'found_uav')
#         :param data: Dictionary or string to send
#         :param to: Specific session ID (optional, defaults to broadcast)
#         """
#         self.socketio.emit(event_name, data, to=to)

#     # def start(self):
#     #     if self.is_running:
#     #         return
        
#     #     self.server_thread = threading.Thread(
#     #         target=self.socketio.run, 
#     #         args=(self.app,), 
#     #         kwargs={'host': self.host, 'port': self.port, 'debug': False, 'use_reloader': False}
#     #     )
#     #     self.server_thread.daemon = True
#     #     self.server_thread.start()
#     #     self.is_running = True
#     #     print(f"WS Server live at ws://{self.host}:{self.port}")

#     def start(self):
#         if self.is_running:
#             return
        
#         # Detect the real IP for a better print message
#         import socket
#         try:
#             s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#             s.connect(("8.8.8.8", 80))
#             display_ip = s.getsockname()[0]
#             s.close()
#         except:
#             display_ip = self.host

#         self.server_thread = threading.Thread(
#             target=self.socketio.run, 
#             args=(self.app,), 
#             kwargs={
#                 'host': self.host, 
#                 'port': self.port, 
#                 'debug': False, 
#                 'use_reloader': False,
#                 'log_output': False # This suppresses the generic Flask startup message
#             }
#         )
#         self.server_thread.daemon = True
#         self.server_thread.start()
#         self.is_running = True
        
#         print("-" * 30)
#         print(f"📡 WS Server is OPEN to LAN")
#         print(f"🔗 Listening on : ws://{display_ip}:{self.port}")
#         print("-" * 30)

#     def stop(self):
#         if self.is_running:
#             self.socketio.stop()
#             self.server_thread.join()
#             self.is_running = False
#             print("WS Server stopped.")

#     def register_lifecycle_logging(self):
#         @self.socketio.on('connect')
#         def on_connect():
#             # request.remote_addr is the IP of the machine connecting to you
#             print(f"⚡ [WS] New Connection: SID={request.sid} from {request.remote_addr}")

#         @self.socketio.on('disconnect')
#         def on_disconnect():
#             print(f"🔌 [WS] Disconnected: SID={request.sid}")        


import asyncio
import threading
import json
import websockets
from websockets.server import serve

class WebSocketServer:
    def __init__(self, host="0.0.0.0", port=None): # Default set to 3000
        self.host = host
        self.port = port
        self.server_thread = None
        self.is_running = False
        self.loop = None
        self.server = None
        self.event_handlers = {}
        self.clients = set()

    def listen_event(self, event_name, callback):
        self.event_handlers[event_name] = callback
        print(f"Registered listener for: {event_name}")

    async def _handler(self, websocket):
        self.clients.add(websocket)
        remote_addr = websocket.remote_address[0]
        print(f"⚡ [WS] New Connection: {remote_addr}")

        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    # print(data)
                    event_type = data.get("type")
                    payload = data.get("payload")

                    if event_type in self.event_handlers:
                        self.event_handlers[event_type](websocket, payload)
                    else:
                        print(f"Unknown event: {event_type}")
                except json.JSONDecodeError:
                    print(f"Non-JSON received: {message}")
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            if websocket in self.clients:
                self.clients.remove(websocket)
            print(f"🔌 [WS] Disconnected: {remote_addr}")

    def send_event(self, event_name, data, to=None):
        message = json.dumps({"type": event_name, "payload": data})
        if self.loop and self.loop.is_running():
            if to:
                asyncio.run_coroutine_threadsafe(to.send(message), self.loop)
            else:
                for client in self.clients:
                    asyncio.run_coroutine_threadsafe(client.send(message), self.loop)

    def _run_server(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            # Explicitly use self.port here
            start_server = serve(self._handler, self.host, self.port)
            self.server = self.loop.run_until_complete(start_server)
            
            import socket
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                display_ip = s.getsockname()[0]
                s.close()
            except:
                display_ip = self.host

            print("-" * 30)
            print(f"🚀 WS Server is LIVE")
            print(f"🔗 URL: ws://{display_ip}:{self.port}") 
            print("-" * 30)

            self.loop.run_forever()
        except Exception as e:
            print(f"❌ Server Error: {e}")

    def start(self):
        if self.is_running: return
        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()
        self.is_running = True

    def stop(self):
        if self.is_running and self.loop:
            print("Stopping WS Server...")
            
            # 1. Schedule the shutdown of the server and tasks
            async def shutdown():
                # Stop accepting new connections
                if self.server:
                    self.server.close()
                    await self.server.wait_closed()
                
                # Close all active client connections
                # We create a list to avoid "Set changed during iteration" errors
                active_clients = list(self.clients)
                for ws in active_clients:
                    await ws.close()
                
                # Stop the loop after tasks are handled
                self.loop.stop()

            # 2. Push the shutdown coroutine into the loop safely
            asyncio.run_coroutine_threadsafe(shutdown(), self.loop)
            
            # 3. Wait for the thread to finish
            if self.server_thread:
                self.server_thread.join(timeout=5)
            
            self.is_running = False
            print("WS Server stopped gracefully.")
            
            


