#!/home/alex/FAC/workshops/MCP_Ideas/.venv/bin/python

import asyncio
from typing import Any
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
import mcp.server.stdio
import mcp.types as types
from djitellopy import Tello
import cv2
import base64
import os
from datetime import datetime


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
            description="Start the video stream from the drone's camera",
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
            description="Capture a snapshot from the drone's camera and display it. The video stream must be started first.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="save_snapshot",
            description="Capture a snapshot from the drone's camera and save it to disk. Returns the file path.",
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
            tello.connect()

            # Test communication by getting battery
            battery = tello.get_battery()
            return [types.TextContent(type="text", text=f"Successfully connected to Tello drone! Battery: {battery}%")]

        except Exception as e:
            tello = None  # Reset on failure
            return [types.TextContent(type="text", text=f"Failed to connect to drone: {str(e)}")]

    elif name == "get_battery":
        try:
            if tello is None:
                return [types.TextContent(type="text", text="Not connected to drone. Use 'connect' tool first.")]

            battery = tello.get_battery()
            return [types.TextContent(type="text", text=f"Battery level: {battery}%")]

        except Exception as e:
            return [types.TextContent(type="text", text=f"Failed to get battery level: {str(e)}")]

    elif name == "takeoff":
        try:
            if tello is None:
                return [types.TextContent(type="text", text="Not connected to drone. Use 'connect' tool first.")]

            # Check battery level before takeoff
            battery = tello.get_battery()
            if battery < 10:
                return [types.TextContent(type="text", text=f"Battery too low for takeoff: {battery}%")]

            # Perform takeoff
            tello.takeoff()
            battery = tello.get_battery()
            return [types.TextContent(type="text", text=f"Drone successfully took off! Battery: {battery}%")]

        except Exception as e:
            return [types.TextContent(type="text", text=f"Takeoff failed: {str(e)}")]

    elif name == "land":
        try:
            if tello is None:
                return [types.TextContent(type="text", text="Not connected to drone. Use 'connect' tool first.")]

            # Perform landing
            tello.land()
            battery = tello.get_battery()
            return [types.TextContent(type="text", text=f"Drone successfully landed! Battery: {battery}%")]

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

            speed = tello.query_speed()
            return [types.TextContent(type="text", text=f"Current speed: {speed} cm/s")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Get speed failed: {str(e)}")]

    elif name == "get_height":
        try:
            if tello is None:
                return [types.TextContent(type="text", text="Not connected to drone. Use 'connect' tool first.")]

            height = tello.get_height()
            return [types.TextContent(type="text", text=f"Current height: {height} cm")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Get height failed: {str(e)}")]

    elif name == "get_temperature":
        try:
            if tello is None:
                return [types.TextContent(type="text", text="Not connected to drone. Use 'connect' tool first.")]

            temp = tello.get_temperature()
            return [types.TextContent(type="text", text=f"Temperature: {temp}°C")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Get temperature failed: {str(e)}")]

    elif name == "get_barometer":
        try:
            if tello is None:
                return [types.TextContent(type="text", text="Not connected to drone. Use 'connect' tool first.")]

            barometer = tello.get_barometer()
            return [types.TextContent(type="text", text=f"Barometer: {barometer} cm")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Get barometer failed: {str(e)}")]

    elif name == "get_flight_time":
        try:
            if tello is None:
                return [types.TextContent(type="text", text="Not connected to drone. Use 'connect' tool first.")]

            flight_time = tello.get_flight_time()
            return [types.TextContent(type="text", text=f"Flight time: {flight_time} seconds")]
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

            return [types.TextContent(type="text", text="Video stream started successfully. You can now capture snapshots.")]
        except Exception as e:
            stream_active = False
            frame_read = None
            return [types.TextContent(type="text", text=f"Failed to start video stream: {str(e)}")]

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
