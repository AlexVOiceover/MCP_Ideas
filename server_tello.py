#!C:\Users\Alexander\Documents\FAC\MCP_Ideas\.venv\Scripts\python.exe

import asyncio
from typing import Any
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
import mcp.server.stdio
import mcp.types as types
from djitellopy import Tello
import base64
import os
from datetime import datetime
import logging
import re
import sys
import platform

# cv2 is imported lazily when camera features are used
# to avoid failing on systems without graphics libraries

# Suppress djitellopy's verbose logging to avoid interfering with MCP stdio protocol
logging.getLogger('djitellopy').setLevel(logging.WARNING)

# Windows-specific fix for video streaming
# PyAV's av.open() fails with Error 10014 on Windows when opening UDP streams
# Solution: Use OpenCV VideoCapture which handles Windows UDP correctly
if platform.system() == 'Windows':
    import djitellopy.tello
    from djitellopy import TelloException
    from threading import Thread, Lock
    from collections import deque
    import numpy as np
    try:
        import cv2
        OPENCV_AVAILABLE = True
    except ImportError:
        OPENCV_AVAILABLE = False

    class WindowsOpenCVFrameRead:
        """Windows-compatible frame reader using OpenCV instead of PyAV"""

        def __init__(self, tello, address, with_queue=False, maxsize=32):
            """Initialize using OpenCV VideoCapture (works on Windows)"""
            if not OPENCV_AVAILABLE:
                raise TelloException("OpenCV is required for Windows video streaming")

            self.address = address
            self.lock = Lock()
            self.frame = np.zeros([300, 400, 3], dtype=np.uint8)
            self.frames = deque([], maxsize)
            self.with_queue = with_queue
            self.stopped = False

            # OpenCV can open UDP streams on Windows (unlike PyAV)
            # Use udp://0.0.0.0:11111 format
            udp_url = f'udp://0.0.0.0:{tello.VS_UDP_PORT}'

            djitellopy.tello.Tello.LOGGER.info(f'Opening video stream with OpenCV: {udp_url}')

            # Create VideoCapture with UDP URL
            self.cap = cv2.VideoCapture(udp_url, cv2.CAP_FFMPEG)

            if not self.cap.isOpened():
                raise TelloException(
                    f'Failed to open video stream with OpenCV.\n'
                    f'URL: {udp_url}\n'
                    f'Make sure:\n'
                    f'1. Tello is connected and powered on\n'
                    f'2. You called streamon() before get_frame_read()\n'
                    f'3. Firewall allows UDP port {tello.VS_UDP_PORT}'
                )

            # Try to grab first frame (with retries for Windows)
            djitellopy.tello.Tello.LOGGER.debug('Attempting to grab first frame...')
            max_attempts = 30  # Try for ~3 seconds
            attempt = 0
            self.grabbed = False

            while not self.grabbed and attempt < max_attempts:
                self.grabbed, self.frame = self.cap.read()
                if self.grabbed and self.frame is not None:
                    djitellopy.tello.Tello.LOGGER.info(f'Successfully grabbed first frame on attempt {attempt + 1}')
                    break
                attempt += 1
                import time
                time.sleep(0.1)

            if not self.grabbed or self.frame is None:
                self.cap.release()
                raise TelloException(
                    f'Failed to grab first frame after {max_attempts} attempts.\n'
                    f'The stream opened but no video data arrived.\n'
                    f'This usually means the drone is not actually streaming.'
                )

            # Start background thread to continuously update frames
            self.worker = Thread(target=self.update_frame, args=(), daemon=True)
            self.worker.start()

            djitellopy.tello.Tello.LOGGER.info('Windows OpenCV video stream started successfully')

        def update_frame(self):
            """Background thread that continuously reads frames"""
            while not self.stopped:
                if self.cap.isOpened():
                    grabbed, frame = self.cap.read()
                    if grabbed and frame is not None:
                        with self.lock:
                            self.frame = frame
                            if self.with_queue:
                                self.frames.append(frame)
                else:
                    break

        def stop(self):
            """Stop the background thread and release resources"""
            self.stopped = True
            if hasattr(self, 'cap'):
                self.cap.release()

    # Patch the get_frame_read method to use OpenCV on Windows
    original_get_frame_read = djitellopy.tello.Tello.get_frame_read

    def patched_get_frame_read(self, *args, **kwargs):
        """Patched version that uses OpenCV VideoCapture on Windows"""
        address = f'udp://0.0.0.0:{self.VS_UDP_PORT}'
        return WindowsOpenCVFrameRead(self, address)

    # Apply the patch
    djitellopy.tello.Tello.get_frame_read = patched_get_frame_read

    djitellopy.tello.Tello.LOGGER.info('Applied Windows OpenCV video streaming patch')


# Create server instance
server = Server("tello-drone-server")

# Global Tello instance
tello = None
frame_read = None
stream_active = False


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools"""
    return [
        types.Tool(
            name="ping",
            description="Basic liveness check - returns OK status",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="connect",
            description="Connect to the Tello drone and verify communication",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="get_battery",
            description="Get the current battery level of the drone",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="takeoff",
            description="Make the Tello drone take off",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="land",
            description="Make the Tello drone land",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="move_forward",
            description="Move the drone forward by a specified distance (20-500 cm)",
            inputSchema={
                "type": "object",
                "properties": {
                    "distance": {
                        "type": "integer",
                        "description": "Distance to move in centimeters (20-500)",
                    }
                },
                "required": ["distance"],
            },
        ),
        types.Tool(
            name="move_back",
            description="Move the drone backward by a specified distance (20-500 cm)",
            inputSchema={
                "type": "object",
                "properties": {
                    "distance": {
                        "type": "integer",
                        "description": "Distance to move in centimeters (20-500)",
                    }
                },
                "required": ["distance"],
            },
        ),
        types.Tool(
            name="move_left",
            description="Move the drone left by a specified distance (20-500 cm)",
            inputSchema={
                "type": "object",
                "properties": {
                    "distance": {
                        "type": "integer",
                        "description": "Distance to move in centimeters (20-500)",
                    }
                },
                "required": ["distance"],
            },
        ),
        types.Tool(
            name="move_right",
            description="Move the drone right by a specified distance (20-500 cm)",
            inputSchema={
                "type": "object",
                "properties": {
                    "distance": {
                        "type": "integer",
                        "description": "Distance to move in centimeters (20-500)",
                    }
                },
                "required": ["distance"],
            },
        ),
        types.Tool(
            name="move_up",
            description="Move the drone up by a specified distance (20-500 cm)",
            inputSchema={
                "type": "object",
                "properties": {
                    "distance": {
                        "type": "integer",
                        "description": "Distance to move in centimeters (20-500)",
                    }
                },
                "required": ["distance"],
            },
        ),
        types.Tool(
            name="move_down",
            description="Move the drone down by a specified distance (20-500 cm)",
            inputSchema={
                "type": "object",
                "properties": {
                    "distance": {
                        "type": "integer",
                        "description": "Distance to move in centimeters (20-500)",
                    }
                },
                "required": ["distance"],
            },
        ),
        types.Tool(
            name="rotate_clockwise",
            description="Rotate the drone clockwise by a specified angle (1-360 degrees)",
            inputSchema={
                "type": "object",
                "properties": {
                    "degrees": {
                        "type": "integer",
                        "description": "Angle to rotate in degrees (1-360)",
                    }
                },
                "required": ["degrees"],
            },
        ),
        types.Tool(
            name="rotate_counter_clockwise",
            description="Rotate the drone counter-clockwise by a specified angle (1-360 degrees)",
            inputSchema={
                "type": "object",
                "properties": {
                    "degrees": {
                        "type": "integer",
                        "description": "Angle to rotate in degrees (1-360)",
                    }
                },
                "required": ["degrees"],
            },
        ),
        types.Tool(
            name="flip",
            description="Make the drone perform a flip in a specified direction",
            inputSchema={
                "type": "object",
                "properties": {
                    "direction": {
                        "type": "string",
                        "description": "Direction to flip: 'left', 'right', 'forward', 'back'",
                        "enum": ["left", "right", "forward", "back"],
                    }
                },
                "required": ["direction"],
            },
        ),
        types.Tool(
            name="set_speed",
            description="Set the drone's flight speed (10-100 cm/s)",
            inputSchema={
                "type": "object",
                "properties": {
                    "speed": {
                        "type": "integer",
                        "description": "Speed in cm/s (10-100)",
                    }
                },
                "required": ["speed"],
            },
        ),
        types.Tool(
            name="get_speed",
            description="Get the current flight speed of the drone",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="get_height",
            description="Get the current height of the drone in centimeters",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="get_temperature",
            description="Get the drone's internal temperature",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="get_barometer",
            description="Get the barometer reading from the drone",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="get_flight_time",
            description="Get the current flight time in seconds",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="emergency",
            description="Emergency stop - immediately stops all motors (USE WITH CAUTION)",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="start_video_stream",
            description="Start the video stream from the drone's camera. Windows uses OpenCV instead of PyAV for UDP compatibility. Requires UDP video packets (port 11111).",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="stop_video_stream",
            description="Stop the video stream from the drone's camera",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="get_snapshot",
            description="Capture a snapshot from the drone's camera and display it. Requires start_video_stream to be called first. Windows UDP compatibility enabled.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="save_snapshot",
            description="Capture a snapshot from the drone's camera and save it to disk. Requires start_video_stream to be called first. Windows UDP compatibility enabled.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Optional: Custom filename for the snapshot. If not provided, uses timestamp.",
                    }
                },
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any]
) -> list[types.TextContent]:
    """Handle tool calls"""
    global tello, frame_read, stream_active

    if name == "ping":
        return [types.TextContent(type="text", text="pong! Server is running.")]

    elif name == "connect":
        try:
            if tello is not None:
                return [types.TextContent(type="text", text="Already connected to drone")]

            tello = Tello()
            # Connect without waiting for state packets to avoid timeout issues
            # State packets may be blocked by firewall or network configuration
            tello.connect(wait_for_state=False)

            return [types.TextContent(type="text", text="Successfully connected to Tello drone! Use 'get_battery' to check battery level.")]

        except Exception as e:
            tello = None  # Reset on failure
            return [types.TextContent(type="text", text=f"Failed to connect to drone: {str(e)}")]

    elif name == "get_battery":
        try:
            if tello is None:
                return [types.TextContent(type="text", text="Not connected to drone. Use 'connect' tool first.")]

            # Query battery directly via command instead of relying on state packets
            # This works even when UDP state packets are blocked
            response = tello.query_battery()
            # Parse response - it may be an int or a string like "80"
            battery = int(str(response).strip())
            return [types.TextContent(type="text", text=f"Battery level: {battery}%")]

        except Exception as e:
            return [types.TextContent(type="text", text=f"Failed to get battery level: {str(e)}. Note: Some sensor readings may not work if UDP state packets are blocked by firewall.")]

    elif name == "takeoff":
        try:
            if tello is None:
                return [types.TextContent(type="text", text="Not connected to drone. Use 'connect' tool first.")]

            # Check battery level before takeoff using query command
            try:
                battery = tello.query_battery()
                if battery < 10:
                    return [types.TextContent(type="text", text=f"Battery too low for takeoff: {battery}%")]
            except:
                # If battery check fails, continue anyway (state packets might be blocked)
                pass

            # Perform takeoff
            tello.takeoff()
            return [types.TextContent(type="text", text="Drone successfully took off!")]

        except Exception as e:
            return [types.TextContent(type="text", text=f"Takeoff failed: {str(e)}")]

    elif name == "land":
        try:
            if tello is None:
                return [types.TextContent(type="text", text="Not connected to drone. Use 'connect' tool first.")]

            # Perform landing
            tello.land()
            return [types.TextContent(type="text", text="Drone successfully landed!")]

        except Exception as e:
            return [types.TextContent(type="text", text=f"Landing failed: {str(e)}")]

    elif name == "move_forward":
        try:
            if tello is None:
                return [types.TextContent(type="text", text="Not connected to drone. Use 'connect' tool first.")]

            distance = arguments["distance"]
            if distance < 20 or distance > 500:
                return [types.TextContent(type="text", text="Distance must be between 20 and 500 cm")]

            tello.move_forward(distance)
            return [types.TextContent(type="text", text=f"Moved forward {distance} cm")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Move forward failed: {str(e)}")]

    elif name == "move_back":
        try:
            if tello is None:
                return [types.TextContent(type="text", text="Not connected to drone. Use 'connect' tool first.")]

            distance = arguments["distance"]
            if distance < 20 or distance > 500:
                return [types.TextContent(type="text", text="Distance must be between 20 and 500 cm")]

            tello.move_back(distance)
            return [types.TextContent(type="text", text=f"Moved back {distance} cm")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Move back failed: {str(e)}")]

    elif name == "move_left":
        try:
            if tello is None:
                return [types.TextContent(type="text", text="Not connected to drone. Use 'connect' tool first.")]

            distance = arguments["distance"]
            if distance < 20 or distance > 500:
                return [types.TextContent(type="text", text="Distance must be between 20 and 500 cm")]

            tello.move_left(distance)
            return [types.TextContent(type="text", text=f"Moved left {distance} cm")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Move left failed: {str(e)}")]

    elif name == "move_right":
        try:
            if tello is None:
                return [types.TextContent(type="text", text="Not connected to drone. Use 'connect' tool first.")]

            distance = arguments["distance"]
            if distance < 20 or distance > 500:
                return [types.TextContent(type="text", text="Distance must be between 20 and 500 cm")]

            tello.move_right(distance)
            return [types.TextContent(type="text", text=f"Moved right {distance} cm")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Move right failed: {str(e)}")]

    elif name == "move_up":
        try:
            if tello is None:
                return [types.TextContent(type="text", text="Not connected to drone. Use 'connect' tool first.")]

            distance = arguments["distance"]
            if distance < 20 or distance > 500:
                return [types.TextContent(type="text", text="Distance must be between 20 and 500 cm")]

            tello.move_up(distance)
            return [types.TextContent(type="text", text=f"Moved up {distance} cm")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Move up failed: {str(e)}")]

    elif name == "move_down":
        try:
            if tello is None:
                return [types.TextContent(type="text", text="Not connected to drone. Use 'connect' tool first.")]

            distance = arguments["distance"]
            if distance < 20 or distance > 500:
                return [types.TextContent(type="text", text="Distance must be between 20 and 500 cm")]

            tello.move_down(distance)
            return [types.TextContent(type="text", text=f"Moved down {distance} cm")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Move down failed: {str(e)}")]

    elif name == "rotate_clockwise":
        try:
            if tello is None:
                return [types.TextContent(type="text", text="Not connected to drone. Use 'connect' tool first.")]

            degrees = arguments["degrees"]
            if degrees < 1 or degrees > 360:
                return [types.TextContent(type="text", text="Degrees must be between 1 and 360")]

            tello.rotate_clockwise(degrees)
            return [types.TextContent(type="text", text=f"Rotated clockwise {degrees} degrees")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Rotate clockwise failed: {str(e)}")]

    elif name == "rotate_counter_clockwise":
        try:
            if tello is None:
                return [types.TextContent(type="text", text="Not connected to drone. Use 'connect' tool first.")]

            degrees = arguments["degrees"]
            if degrees < 1 or degrees > 360:
                return [types.TextContent(type="text", text="Degrees must be between 1 and 360")]

            tello.rotate_counter_clockwise(degrees)
            return [types.TextContent(type="text", text=f"Rotated counter-clockwise {degrees} degrees")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Rotate counter-clockwise failed: {str(e)}")]

    elif name == "flip":
        try:
            if tello is None:
                return [types.TextContent(type="text", text="Not connected to drone. Use 'connect' tool first.")]

            direction = arguments["direction"]
            if direction == "left":
                tello.flip_left()
            elif direction == "right":
                tello.flip_right()
            elif direction == "forward":
                tello.flip_forward()
            elif direction == "back":
                tello.flip_back()
            else:
                return [types.TextContent(type="text", text=f"Invalid direction: {direction}")]

            return [types.TextContent(type="text", text=f"Performed flip {direction}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Flip failed: {str(e)}")]

    elif name == "set_speed":
        try:
            if tello is None:
                return [types.TextContent(type="text", text="Not connected to drone. Use 'connect' tool first.")]

            speed = arguments["speed"]
            if speed < 10 or speed > 100:
                return [types.TextContent(type="text", text="Speed must be between 10 and 100 cm/s")]

            tello.set_speed(speed)
            return [types.TextContent(type="text", text=f"Speed set to {speed} cm/s")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Set speed failed: {str(e)}")]

    elif name == "get_speed":
        try:
            if tello is None:
                return [types.TextContent(type="text", text="Not connected to drone. Use 'connect' tool first.")]

            # Use raw command instead of query_speed() which fails on float responses
            response = tello.send_read_command('speed?')
            # Parse response - strip any units if present
            speed_str = str(response).strip()
            # Extract numeric part (handle responses like "10.0" or "10")
            match = re.search(r'[\d.]+', speed_str)
            if match:
                speed = float(match.group())
                return [types.TextContent(type="text", text=f"Speed setting: {speed} cm/s (this is the max speed limit, not current velocity)")]
            else:
                return [types.TextContent(type="text", text=f"Speed setting: {response}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Get speed failed: {str(e)}")]

    elif name == "get_height":
        try:
            if tello is None:
                return [types.TextContent(type="text", text="Not connected to drone. Use 'connect' tool first.")]

            # Use raw command instead of query_height() which may fail on formatted responses
            response = tello.send_read_command('height?')
            # Parse response - may include units like "dm" (decimeters)
            height_str = str(response).strip()
            match = re.search(r'([\d.]+)(dm|cm)?', height_str)
            if match:
                height = float(match.group(1))
                unit = match.group(2)
                # Convert decimeters to centimeters if needed
                if unit == 'dm':
                    height = height * 10
                return [types.TextContent(type="text", text=f"Current height: {int(height)} cm")]
            else:
                return [types.TextContent(type="text", text=f"Current height: {response}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Get height failed: {str(e)}")]

    elif name == "get_temperature":
        try:
            if tello is None:
                return [types.TextContent(type="text", text="Not connected to drone. Use 'connect' tool first.")]

            response = tello.query_temperature()
            # Parse response - strip any units
            temp_str = str(response).strip()
            match = re.search(r'[\d.]+', temp_str)
            if match:
                temp = float(match.group())
                return [types.TextContent(type="text", text=f"Temperature: {int(temp)}°C")]
            else:
                return [types.TextContent(type="text", text=f"Temperature: {response}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Get temperature failed: {str(e)}")]

    elif name == "get_barometer":
        try:
            if tello is None:
                return [types.TextContent(type="text", text="Not connected to drone. Use 'connect' tool first.")]

            response = tello.query_barometer()
            # Parse response - strip any units
            baro_str = str(response).strip()
            match = re.search(r'[\d.]+', baro_str)
            if match:
                barometer = float(match.group())
                return [types.TextContent(type="text", text=f"Barometer: {barometer} cm")]
            else:
                return [types.TextContent(type="text", text=f"Barometer: {response}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Get barometer failed: {str(e)}")]

    elif name == "get_flight_time":
        try:
            if tello is None:
                return [types.TextContent(type="text", text="Not connected to drone. Use 'connect' tool first.")]

            response = tello.query_flight_time()
            # Parse response - strip any units
            time_str = str(response).strip()
            match = re.search(r'[\d.]+', time_str)
            if match:
                flight_time = float(match.group())
                return [types.TextContent(type="text", text=f"Flight time: {int(flight_time)} seconds")]
            else:
                return [types.TextContent(type="text", text=f"Flight time: {response}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Get flight time failed: {str(e)}")]

    elif name == "emergency":
        try:
            if tello is None:
                return [types.TextContent(type="text", text="Not connected to drone. Use 'connect' tool first.")]

            tello.emergency()
            return [types.TextContent(type="text", text="EMERGENCY STOP ACTIVATED - All motors stopped")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Emergency stop failed: {str(e)}")]

    elif name == "start_video_stream":
        try:
            if tello is None:
                return [types.TextContent(type="text", text="Not connected to drone. Use 'connect' tool first.")]

            if stream_active:
                return [types.TextContent(type="text", text="Video stream is already active")]

            tello.streamon()
            frame_read = tello.get_frame_read()
            stream_active = True

            platform_note = ""
            if platform.system() == 'Windows':
                platform_note = " (Using OpenCV for Windows UDP compatibility)"

            return [types.TextContent(type="text", text=f"Video stream started successfully{platform_note}. You can now capture snapshots.")]
        except Exception as e:
            stream_active = False
            frame_read = None
            error_msg = str(e)

            # Provide helpful context for common errors
            if "10014" in error_msg or "WSAEFAULT" in error_msg or "FIREWALL FIX REQUIRED" in error_msg:
                return [types.TextContent(type="text", text=f"Failed to start video stream: {error_msg}\n\n🔧 QUICK FIX - Windows Firewall is likely blocking UDP port 11111:\n\n1. Open PowerShell as Administrator\n2. Navigate to: C:\\Users\\Alexander\\Documents\\FAC\\MCP_Ideas\n3. Run: .\\add_firewall_rule.ps1\n\nThis will create a firewall rule allowing Tello video streaming.\n\n✅ ALTERNATIVE:\nAll drone control commands (takeoff, land, move, rotate, etc.) work perfectly without video!\nYou can fully control the drone - camera is optional.\n\n📖 For more details, see README.md")]
            elif "unsuccessful" in error_msg or "Did not receive a response" in error_msg:
                return [types.TextContent(type="text", text=f"Failed to start video stream: {error_msg}\n\nNote: Video streaming requires UDP video packets (port 11111) which may be blocked by firewalls or network configuration. The video stream uses UDP protocol to receive video data from the drone.")]
            else:
                return [types.TextContent(type="text", text=f"Failed to start video stream: {error_msg}")]

    elif name == "stop_video_stream":
        try:
            if tello is None:
                return [types.TextContent(type="text", text="Not connected to drone. Use 'connect' tool first.")]

            if not stream_active:
                return [types.TextContent(type="text", text="Video stream is not active")]

            tello.streamoff()
            stream_active = False
            frame_read = None

            return [types.TextContent(type="text", text="Video stream stopped")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Failed to stop video stream: {str(e)}")]

    elif name == "get_snapshot":
        try:
            import cv2
        except ImportError:
            return [types.TextContent(type="text", text="OpenCV (cv2) is not available. Camera features require graphics libraries (libGL) which may not be available in WSL.")]

        try:
            if tello is None:
                return [types.TextContent(type="text", text="Not connected to drone. Use 'connect' tool first.")]

            if not stream_active or frame_read is None:
                return [types.TextContent(type="text", text="Video stream is not active. Use 'start_video_stream' first.")]

            # Get the current frame
            frame = frame_read.frame

            if frame is None:
                return [types.TextContent(type="text", text="No frame available. The camera might be initializing.")]

            # Encode frame as JPEG
            success, buffer = cv2.imencode('.jpg', frame)

            if not success:
                return [types.TextContent(type="text", text="Failed to encode frame as JPEG")]

            # Convert to base64
            image_base64 = base64.b64encode(buffer).decode('utf-8')

            return [
                types.ImageContent(
                    type="image",
                    data=image_base64,
                    mimeType="image/jpeg"
                ),
                types.TextContent(
                    type="text",
                    text="Snapshot captured from Tello drone camera"
                )
            ]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Failed to capture snapshot: {str(e)}")]

    elif name == "save_snapshot":
        try:
            import cv2
        except ImportError:
            return [types.TextContent(type="text", text="OpenCV (cv2) is not available. Camera features require graphics libraries (libGL) which may not be available in WSL.")]

        try:
            if tello is None:
                return [types.TextContent(type="text", text="Not connected to drone. Use 'connect' tool first.")]

            if not stream_active or frame_read is None:
                return [types.TextContent(type="text", text="Video stream is not active. Use 'start_video_stream' first.")]

            # Get the current frame
            frame = frame_read.frame

            if frame is None:
                return [types.TextContent(type="text", text="No frame available. The camera might be initializing.")]

            # Generate filename
            if "filename" in arguments and arguments["filename"]:
                filename = arguments["filename"]
                if not filename.endswith(('.jpg', '.jpeg', '.png')):
                    filename += '.jpg'
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"tello_snapshot_{timestamp}.jpg"

            # Save the image
            cv2.imwrite(filename, frame)

            # Get absolute path
            abs_path = os.path.abspath(filename)

            return [types.TextContent(type="text", text=f"Snapshot saved to: {abs_path}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Failed to save snapshot: {str(e)}")]

    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    """Main entry point"""
    # Run the server using stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="tello-drone-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=mcp.server.NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
