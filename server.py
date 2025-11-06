#!/usr/bin/env python3

import asyncio
from typing import Any
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
import mcp.server.stdio
import mcp.types as types
import requests
import os
from dotenv import load_dotenv
import base64

# Load environment variables
load_dotenv()

# Home Assistant configuration
HA_URL = os.getenv("HA_URL", "http://localhost:8123")
HA_TOKEN = os.getenv("HA_TOKEN")
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))

# Create server instance
server = Server("homeassistant-server")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools"""
    return [
        types.Tool(
            name="get_lights",
            description="Get all lights and their current status (on/off, brightness)",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="toggle_light",
            description="Turn a light on or off by its entity ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "The entity ID of the light (e.g., light.living_room)",
                    }
                },
                "required": ["entity_id"],
            },
        ),
        types.Tool(
            name="get_temperature",
            description="Get temperature readings from all temperature sensors",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="set_climate",
            description="Set target temperature for a climate device",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "The entity ID of the climate device (e.g., climate.living_room)",
                    },
                    "temperature": {
                        "type": "number",
                        "description": "Target temperature in Celsius",
                    },
                },
                "required": ["entity_id", "temperature"],
            },
        ),
        types.Tool(
            name="get_sun",
            description="Get sunrise and sunset times for today",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="get_locks",
            description="Get all locks and their current status (locked/unlocked)",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="lock_door",
            description="Lock a door by its entity ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "The entity ID of the lock (e.g., lock.front_door)",
                    }
                },
                "required": ["entity_id"],
            },
        ),
        types.Tool(
            name="unlock_door",
            description="Unlock a door by its entity ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "The entity ID of the lock (e.g., lock.front_door)",
                    }
                },
                "required": ["entity_id"],
            },
        ),
        types.Tool(
            name="get_climate_status",
            description="Get status of all climate devices (thermostats)",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="open_cover",
            description="Open a cover (garage door, window, etc.) by its entity ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "The entity ID of the cover (e.g., cover.garage_door)",
                    }
                },
                "required": ["entity_id"],
            },
        ),
        types.Tool(
            name="close_cover",
            description="Close a cover (garage door, window, etc.) by its entity ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "The entity ID of the cover (e.g., cover.garage_door)",
                    }
                },
                "required": ["entity_id"],
            },
        ),
        types.Tool(
            name="get_sensors",
            description="Get all sensor readings (motion, air quality, etc.)",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="get_cameras",
            description="List all available cameras (laptop_camera is the front door camera)",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="send_telegram_message",
            description="Send a text message via Telegram bot",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The message text to send",
                    }
                },
                "required": ["message"],
            },
        ),
        types.Tool(
            name="send_camera_snapshot",
            description="Send camera snapshot to Telegram using custom script (only works with laptop_camera, not demo cameras). Note: laptop_camera is the front door camera. Use this when user asks to show what's at the front door.",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "The entity ID of the camera. Use camera.laptop_camera for the front door camera.",
                    }
                },
                "required": ["entity_id"],
            },
        ),
        types.Tool(
            name="get_camera_snapshot",
            description="Get camera snapshot and display it in the chat (only works with laptop_camera, not demo cameras). Note: laptop_camera is the front door camera. Use this when user asks to see what's at the front door.",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "The entity ID of the camera. Use camera.laptop_camera for the front door camera.",
                    }
                },
                "required": ["entity_id"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any]
) -> list[types.TextContent]:
    """Handle tool calls"""

    headers = {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json",
    }

    if name == "get_lights":
        # Get all entities
        response = requests.get(f"{HA_URL}/api/states", headers=headers)
        states = response.json()

        # Filter only lights
        lights = [
            entity for entity in states if entity["entity_id"].startswith("light.")
        ]

        output = f"Found {len(lights)} light(s):\n\n"
        for light in lights:
            state = light["state"]
            brightness = light["attributes"].get("brightness", "N/A")
            output += f"- {light['entity_id']}: {state}"
            if brightness != "N/A":
                output += f" (brightness: {brightness})"
            output += "\n"

        return [types.TextContent(type="text", text=output)]

    elif name == "toggle_light":
        entity_id = arguments["entity_id"]
        # Toggle the light
        response = requests.post(
            f"{HA_URL}/api/services/light/toggle",
            headers=headers,
            json={"entity_id": entity_id},
        )
        return [types.TextContent(type="text", text=f"Toggled {entity_id}")]

    elif name == "get_temperature":
        # Get all entities
        response = requests.get(f"{HA_URL}/api/states", headers=headers)
        states = response.json()

        # Filter temperature sensors
        temp_sensors = [
            entity
            for entity in states
            if "temperature" in entity["entity_id"]
            or entity["attributes"].get("device_class") == "temperature"
        ]

        output = f"Temperature sensors ({len(temp_sensors)}):\n\n"
        for sensor in temp_sensors:
            unit = sensor["attributes"].get("unit_of_measurement", "")
            output += f"- {sensor['entity_id']}: {sensor['state']} {unit}\n"

        return [types.TextContent(type="text", text=output)]

    elif name == "set_climate":
        entity_id = arguments["entity_id"]
        temperature = arguments["temperature"]
        # Set temperature
        response = requests.post(
            f"{HA_URL}/api/services/climate/set_temperature",
            headers=headers,
            json={"entity_id": entity_id, "temperature": temperature},
        )
        return [
            types.TextContent(type="text", text=f"Set {entity_id} to {temperature}°C")
        ]

    elif name == "get_sun":
        # Get sun entity (built-in to Home Assistant)
        response = requests.get(f"{HA_URL}/api/states/sun.sun", headers=headers)
        sun_data = response.json()

        next_rising = sun_data["attributes"]["next_rising"]
        next_setting = sun_data["attributes"]["next_setting"]
        state = sun_data["state"]

        output = f"Sun Status: {state}\n\n"
        output += f"Next Sunrise: {next_rising}\n"
        output += f"Next Sunset: {next_setting}"

        return [types.TextContent(type="text", text=output)]

    elif name == "get_locks":
        response = requests.get(f"{HA_URL}/api/states", headers=headers)
        states = response.json()

        # Filter locks
        locks = [entity for entity in states if entity["entity_id"].startswith("lock.")]

        output = f"Found {len(locks)} lock(s):\n\n"
        for lock in locks:
            state = lock["state"]
            output += f"- {lock['entity_id']}: {state}\n"

        return [types.TextContent(type="text", text=output)]

    elif name == "lock_door":
        entity_id = arguments["entity_id"]
        requests.post(
            f"{HA_URL}/api/services/lock/lock",
            headers=headers,
            json={"entity_id": entity_id},
        )
        return [types.TextContent(type="text", text=f"Locked {entity_id}")]

    elif name == "unlock_door":
        entity_id = arguments["entity_id"]
        requests.post(
            f"{HA_URL}/api/services/lock/unlock",
            headers=headers,
            json={"entity_id": entity_id},
        )
        return [types.TextContent(type="text", text=f"Unlocked {entity_id}")]

    elif name == "get_climate_status":
        response = requests.get(f"{HA_URL}/api/states", headers=headers)
        states = response.json()

        # Filter climate devices
        climates = [
            entity for entity in states if entity["entity_id"].startswith("climate.")
        ]

        output = f"Climate devices ({len(climates)}):\n\n"
        for climate in climates:
            current_temp = climate["attributes"].get("current_temperature", "N/A")
            target_temp = climate["attributes"].get("temperature", "N/A")
            mode = climate["state"]
            output += f"- {climate['entity_id']}\n"
            output += f"  Current: {current_temp}°C\n"
            output += f"  Target: {target_temp}°C\n"
            output += f"  Mode: {mode}\n\n"

        return [types.TextContent(type="text", text=output)]

    elif name == "open_cover":
        entity_id = arguments["entity_id"]
        requests.post(
            f"{HA_URL}/api/services/cover/open_cover",
            headers=headers,
            json={"entity_id": entity_id},
        )
        return [types.TextContent(type="text", text=f"Opening {entity_id}")]

    elif name == "close_cover":
        entity_id = arguments["entity_id"]
        requests.post(
            f"{HA_URL}/api/services/cover/close_cover",
            headers=headers,
            json={"entity_id": entity_id},
        )
        return [types.TextContent(type="text", text=f"Closing {entity_id}")]

    elif name == "get_sensors":
        response = requests.get(f"{HA_URL}/api/states", headers=headers)
        states = response.json()

        # Filter sensors and binary sensors
        sensors = [
            entity
            for entity in states
            if entity["entity_id"].startswith("sensor.")
            or entity["entity_id"].startswith("binary_sensor.")
        ]

        output = f"Sensors ({len(sensors)}):\n\n"
        for sensor in sensors:
            state = sensor["state"]
            unit = sensor["attributes"].get("unit_of_measurement", "")
            output += f"- {sensor['entity_id']}: {state} {unit}\n"

        return [types.TextContent(type="text", text=output)]

    elif name == "get_cameras":
        response = requests.get(f"{HA_URL}/api/states", headers=headers)
        states = response.json()

        # Filter cameras - exclude demo cameras, only show laptop_camera
        cameras = [
            entity
            for entity in states
            if entity["entity_id"].startswith("camera.")
            and not entity["entity_id"].startswith("camera.demo")
            and "demo" not in entity["entity_id"].lower()
        ]

        output = f"Found {len(cameras)} camera(s):\n\n"
        for camera in cameras:
            state = camera["state"]
            friendly_name = camera["attributes"].get(
                "friendly_name", camera["entity_id"]
            )
            output += f"- {camera['entity_id']} ({friendly_name}): {state}\n"

        return [types.TextContent(type="text", text=output)]

    elif name == "send_telegram_message":
        message = arguments["message"]
        # Send text message via Telegram
        requests.post(
            f"{HA_URL}/api/services/telegram_bot/send_message",
            headers=headers,
            json={"message": message, "target": TELEGRAM_CHAT_ID},
        )
        return [
            types.TextContent(
                type="text", text=f"Sent message to Telegram: '{message}'"
            )
        ]

    elif name == "send_camera_snapshot":
        entity_id = arguments["entity_id"]

        # Block demo cameras
        if entity_id.startswith("camera.demo") or "demo" in entity_id.lower():
            return [
                types.TextContent(
                    type="text",
                    text=f"Error: Demo cameras are not supported. Please use camera.laptop_camera instead.",
                )
            ]

        # Call the custom Home Assistant script
        response = requests.post(
            f"{HA_URL}/api/services/script/send_camera_snapshot",
            headers=headers,
            json={"entity_id": entity_id},
        )

        # Check if request was successful
        if response.status_code == 200:
            return [
                types.TextContent(type="text", text=f"Snapshot sent for {entity_id}")
            ]
        else:
            return [
                types.TextContent(
                    type="text",
                    text=f"Error calling script: {response.status_code} - {response.text}",
                )
            ]

    elif name == "get_camera_snapshot":
        entity_id = arguments["entity_id"]

        # Block demo cameras
        if entity_id.startswith("camera.demo") or "demo" in entity_id.lower():
            return [
                types.TextContent(
                    type="text",
                    text=f"Error: Demo cameras are not supported. Please use camera.laptop_camera instead."
                )
            ]

        # Get camera snapshot from Home Assistant
        try:
            response = requests.get(
                f"{HA_URL}/api/camera_proxy/{entity_id}",
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                # Encode image to base64
                image_base64 = base64.b64encode(response.content).decode('utf-8')

                # Return image content
                return [
                    types.ImageContent(
                        type="image",
                        data=image_base64,
                        mimeType=response.headers.get('Content-Type', 'image/jpeg')
                    ),
                    types.TextContent(
                        type="text",
                        text=f"Camera snapshot from {entity_id}"
                    )
                ]
            else:
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error getting snapshot: {response.status_code} - {response.text}",
                    )
                ]
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"Error getting snapshot: {str(e)}",
                )
            ]

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
                server_name="homeassistant-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=mcp.server.NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
