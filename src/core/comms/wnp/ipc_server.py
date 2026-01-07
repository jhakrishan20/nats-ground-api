import asyncio
import json
import threading
import win32pipe
import win32file
import pywintypes
from core.utils import Logger 

PIPE_NAME = r"\\.\pipe\vaayu_ground_ipc"

class IPCServer:
    def __init__(self, main_loop: asyncio.AbstractEventLoop):
        self.logger = Logger.get("IPC")
        self.main_loop = main_loop
        self.pipe = None
        self._thread = None
        self._running = False
        self._command_handler = None
        self._lock = threading.Lock()  # Prevents simultaneous writes from breaking the pipe

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_pipe_server, daemon=True)
        self._thread.start()
        self.logger.info("✅ IPC server started and listening.")

    def _run_pipe_server(self):
        """Main loop that handles pipe creation and client life-cycles."""
        while self._running:
            try:
                # 1. Create the Named Pipe
                self.pipe = win32pipe.CreateNamedPipe(
                    PIPE_NAME,
                    win32pipe.PIPE_ACCESS_DUPLEX,
                    win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
                    1, 65536, 65536, 0, None,
                )

                self.logger.info("Waiting for Qt client connection...")
                # 2. Wait for client to connect
                win32pipe.ConnectNamedPipe(self.pipe, None)
                self.logger.info("Qt client connected.")

                # 3. Message Processing Loop
                while self._running:
                    try:
                        # Read the incoming message
                        hr, raw = win32file.ReadFile(self.pipe, 65536)
                        data = raw.decode().strip()
                        if not data:
                            continue

                        msg = json.loads(data)

                        if self._command_handler:
                            # Safely schedule the async handler on the main loop
                            asyncio.run_coroutine_threadsafe(
                                self._command_handler(msg), 
                                self.main_loop
                            )
                        
                    except pywintypes.error as e:
                        if e.args[0] in (109, 232): # Broken pipe or pipe being closed
                            self.logger.warning("Qt client disconnected.")
                        else:
                            self.logger.error(f"Read error: {e}")
                        break 
                    except Exception as e:
                        self.logger.error(f"IPC processing error: {e}")
                        break

            except Exception as e:
                self.logger.error(f"IPC Server critical failure: {e}")
                import time
                time.sleep(1) 
            finally:
                self._cleanup_pipe()

    def send_event(self, event: dict):
        """Thread-safe method to push data to the pipe with a newline delimiter."""
        if not self.pipe:
            return

        def _threaded_write():
            # Use a lock so two 'uav_discovered' events don't collide on the same pipe handle
            with self._lock:
                if not self.pipe:
                    return
                try:
                    # Append newline so the Qt client's readLine() works
                    payload = (json.dumps(event) + "\n").encode()
                    win32file.WriteFile(self.pipe, payload)
                    win32file.FlushFileBuffers(self.pipe)
                except Exception as e:
                    self.logger.error(f"IPC write failed: {e}")

        threading.Thread(target=_threaded_write, daemon=True).start()

    def register_command_handler(self, handler):
        """Expects an 'async def' function."""
        self._command_handler = handler

    def _cleanup_pipe(self):
        """Safely close and reset the pipe handle."""
        if self.pipe:
            try:
                win32pipe.DisconnectNamedPipe(self.pipe)
                win32file.CloseHandle(self.pipe)
            except:
                pass
            self.pipe = None

    def stop(self):
        self._running = False
        self._cleanup_pipe()
        self.logger.info("⏹️ IPC server stopping...")