#!C:\Users\Alexander\Documents\FAC\MCP_Ideas\.venv\Scripts\python.exe

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
            description="Get all lights and their current status (on/off, brightness). If you dont find any light, there could be one plugged on a smart plug. You can use get_switches to find smart plugs.",
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
            name="turn_on_light",
            description="Turn on a light by its entity ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "The entity ID of the light (e.g., light.hue_bulb)",
                    }
                },
                "required": ["entity_id"],
            },
        ),
        types.Tool(
            name="turn_off_light",
            description="Turn off a light by its entity ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "The entity ID of the light (e.g., light.hue_bulb)",
                    }
                },
                "required": ["entity_id"],
            },
        ),
        types.Tool(
            name="set_light_brightness",
            description="Set the brightness of a light (0-255, or 0-100 as percentage)",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "The entity ID of the light (e.g., light.hue_bulb)",
                    },
                    "brightness": {
                        "type": "number",
                        "description": "Brightness level: 0-255 for absolute value, or 0-100 for percentage (will be converted to 0-255)",
                    }
                },
                "required": ["entity_id", "brightness"],
            },
        ),
        types.Tool(
            name="set_light_color",
            description="Set the RGB color of a light. Use this for Philips Hue and other color-capable lights.",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "The entity ID of the light (e.g., light.hue_bulb)",
                    },
                    "red": {
                        "type": "number",
                        "description": "Red value (0-255)",
                    },
                    "green": {
                        "type": "number",
                        "description": "Green value (0-255)",
                    },
                    "blue": {
                        "type": "number",
                        "description": "Blue value (0-255)",
                    }
                },
                "required": ["entity_id", "red", "green", "blue"],
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
            description="List all available cameras (logitechusb is the front door camera)",
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
            description="Send camera snapshot to Telegram. Note: logitechusb is the front door camera. Defaults to camera.logitechusb if no entity_id is provided.",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "Optional: The entity ID of the camera. Defaults to camera.logitechusb if not provided.",
                    }
                },
                "required": [],
            },
        ),
        types.Tool(
            name="get_camera_snapshot",
            description="Get camera snapshot and display it in the chat. Note: logitechusb is the front door camera. Use this when user asks to see what's at the front door.",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "The entity ID of the camera. Use camera.logitechusb for the front door camera.",
                    }
                },
                "required": ["entity_id"],
            },
        ),
        types.Tool(
            name="get_switches",
            description="Get all switches and their current status (on/off). Includes smart plugs like Tapo.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="turn_on_switch",
            description="Turn a switch on by its entity ID (e.g., switch.tapo_plug)",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "The entity ID of the switch (e.g., switch.tapo_plug)",
                    }
                },
                "required": ["entity_id"],
            },
        ),
        types.Tool(
            name="turn_off_switch",
            description="Turn a switch off by its entity ID (e.g., switch.tapo_plug)",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "The entity ID of the switch (e.g., switch.tapo_plug)",
                    }
                },
                "required": ["entity_id"],
            },
        ),
        types.Tool(
            name="toggle_switch",
            description="Toggle a switch on/off by its entity ID (e.g., switch.tapo_plug)",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "The entity ID of the switch (e.g., switch.tapo_plug)",
                    }
                },
                "required": ["entity_id"],
            },
        ),
        # NOTE: TTS tools commented out - using server_speaker.py instead
        # types.Tool(
        #     name="get_media_players",
        #     description="Get all available media players to use with text-to-speech",
        #     inputSchema={
        #         "type": "object",
        #         "properties": {},
        #     },
        # ),
        # types.Tool(
        #     name="get_tts_engines",
        #     description="Get all available TTS engines/entities",
        #     inputSchema={
        #         "type": "object",
        #         "properties": {},
        #     },
        # ),
        # types.Tool(
        #     name="speak",
        #     description="Speak text aloud using text-to-speech through a media player. Use this to make the system speak, read messages, or produce audio output. Automatically detects the best available media player if not specified.",
        #     inputSchema={
        #         "type": "object",
        #         "properties": {
        #             "message": {
        #                 "type": "string",
        #                 "description": "The text message to speak out loud",
        #             },
        #             "media_player_entity_id": {
        #                 "type": "string",
        #                 "description": "Optional: The entity ID of the media player (e.g., media_player.google_speaker). If not provided, will use the first available media player.",
        #             },
        #             "language": {
        #                 "type": "string",
        #                 "description": "Optional: Language code (e.g., 'en' for English, 'es' for Spanish). Defaults to 'en'",
        #             },
        #         },
        #         "required": ["message"],
        #     },
        # ),
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

    elif name == "turn_on_light":
        entity_id = arguments["entity_id"]
        requests.post(
            f"{HA_URL}/api/services/light/turn_on",
            headers=headers,
            json={"entity_id": entity_id},
        )
        return [types.TextContent(type="text", text=f"Turned on {entity_id}")]

    elif name == "turn_off_light":
        entity_id = arguments["entity_id"]
        requests.post(
            f"{HA_URL}/api/services/light/turn_off",
            headers=headers,
            json={"entity_id": entity_id},
        )
        return [types.TextContent(type="text", text=f"Turned off {entity_id}")]

    elif name == "set_light_brightness":
        entity_id = arguments["entity_id"]
        brightness = arguments["brightness"]

        # Convert percentage (0-100) to Home Assistant brightness (0-255) if needed
        if brightness <= 100:
            brightness = int((brightness / 100) * 255)

        requests.post(
            f"{HA_URL}/api/services/light/turn_on",
            headers=headers,
            json={"entity_id": entity_id, "brightness": brightness},
        )
        return [types.TextContent(type="text", text=f"Set {entity_id} brightness to {brightness}")]

    elif name == "set_light_color":
        entity_id = arguments["entity_id"]
        red = arguments["red"]
        green = arguments["green"]
        blue = arguments["blue"]

        requests.post(
            f"{HA_URL}/api/services/light/turn_on",
            headers=headers,
            json={"entity_id": entity_id, "rgb_color": [red, green, blue]},
        )
        return [types.TextContent(type="text", text=f"Set {entity_id} color to RGB({red}, {green}, {blue})")]

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

        # Filter cameras - exclude demo cameras, only show logitechusb
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
        entity_id = arguments.get("entity_id", "camera.logitechusb")

        # Block demo cameras
        if entity_id.startswith("camera.demo") or "demo" in entity_id.lower():
            return [
                types.TextContent(
                    type="text",
                    text=f"Error: Demo cameras are not supported. Please use camera.logitechusb instead.",
                )
            ]

        try:
            # Send via Telegram using camera proxy URL
            # Pass authentication so HA can fetch the authenticated camera proxy URL
            telegram_response = requests.post(
                f"{HA_URL}/api/services/telegram_bot/send_photo",
                headers=headers,
                json={
                    "target": TELEGRAM_CHAT_ID,
                    "url": f"{HA_URL}/api/camera_proxy/{entity_id}",
                    "caption": f"Snapshot from {entity_id}",
                    "authentication": "bearer_token",
                    "password": HA_TOKEN,
                },
            )

            if telegram_response.status_code in [200, 204]:
                return [
                    types.TextContent(
                        type="text", text=f"Snapshot from {entity_id} sent to Telegram"
                    )
                ]
            else:
                error_details = telegram_response.text
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error sending to Telegram: {telegram_response.status_code}\nResponse: {error_details}\nURL sent: {HA_URL}/api/camera_proxy/{entity_id}",
                    )
                ]
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"Error sending snapshot: {str(e)}",
                )
            ]

    elif name == "get_camera_snapshot":
        entity_id = arguments["entity_id"]

        # Block demo cameras
        if entity_id.startswith("camera.demo") or "demo" in entity_id.lower():
            return [
                types.TextContent(
                    type="text",
                    text=f"Error: Demo cameras are not supported. Please use camera.logitechusb instead.",
                )
            ]

        # Get camera snapshot from Home Assistant
        try:
            response = requests.get(
                f"{HA_URL}/api/camera_proxy/{entity_id}", headers=headers, timeout=10
            )

            if response.status_code == 200:
                # Encode image to base64
                image_base64 = base64.b64encode(response.content).decode("utf-8")

                # Return image content
                return [
                    types.ImageContent(
                        type="image",
                        data=image_base64,
                        mimeType=response.headers.get("Content-Type", "image/jpeg"),
                    ),
                    types.TextContent(
                        type="text", text=f"Camera snapshot from {entity_id}"
                    ),
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

    elif name == "get_switches":
        response = requests.get(f"{HA_URL}/api/states", headers=headers)
        states = response.json()

        # Filter switches
        switches = [
            entity for entity in states if entity["entity_id"].startswith("switch.")
        ]

        output = f"Found {len(switches)} switch(es):\n\n"
        for switch in switches:
            state = switch["state"]
            friendly_name = switch["attributes"].get(
                "friendly_name", switch["entity_id"]
            )
            output += f"- {switch['entity_id']} ({friendly_name}): {state}\n"

        return [types.TextContent(type="text", text=output)]

    elif name == "turn_on_switch":
        entity_id = arguments["entity_id"]
        requests.post(
            f"{HA_URL}/api/services/switch/turn_on",
            headers=headers,
            json={"entity_id": entity_id},
        )
        return [types.TextContent(type="text", text=f"Turned on {entity_id}")]

    elif name == "turn_off_switch":
        entity_id = arguments["entity_id"]
        requests.post(
            f"{HA_URL}/api/services/switch/turn_off",
            headers=headers,
            json={"entity_id": entity_id},
        )
        return [types.TextContent(type="text", text=f"Turned off {entity_id}")]

    elif name == "toggle_switch":
        entity_id = arguments["entity_id"]
        requests.post(
            f"{HA_URL}/api/services/switch/toggle",
            headers=headers,
            json={"entity_id": entity_id},
        )
        return [types.TextContent(type="text", text=f"Toggled {entity_id}")]

    # NOTE: TTS handlers commented out - using server_speaker.py instead
    # elif name == "get_media_players":
    #     response = requests.get(f"{HA_URL}/api/states", headers=headers)
    #     states = response.json()
    #
    #     # Filter media players
    #     media_players = [
    #         entity
    #         for entity in states
    #         if entity["entity_id"].startswith("media_player.")
    #     ]
    #
    #     output = f"Found {len(media_players)} media player(s):\n\n"
    #     for player in media_players:
    #         state = player["state"]
    #         friendly_name = player["attributes"].get(
    #             "friendly_name", player["entity_id"]
    #         )
    #         output += f"- {player['entity_id']} ({friendly_name}): {state}\n"
    #
    #     return [types.TextContent(type="text", text=output)]
    #
    # elif name == "get_tts_engines":
    #     response = requests.get(f"{HA_URL}/api/states", headers=headers)
    #     states = response.json()
    #
    #     # Filter TTS entities
    #     tts_engines = [
    #         entity for entity in states if entity["entity_id"].startswith("tts.")
    #     ]
    #
    #     output = f"Found {len(tts_engines)} TTS engine(s):\n\n"
    #     for engine in tts_engines:
    #         state = engine["state"]
    #         friendly_name = engine["attributes"].get(
    #             "friendly_name", engine["entity_id"]
    #         )
    #         output += f"- {engine['entity_id']} ({friendly_name}): {state}\n"
    #
    #     return [types.TextContent(type="text", text=output)]
    #
    # elif name == "speak":
    #     message = arguments["message"]
    #     media_player_entity_id = arguments.get("media_player_entity_id")
    #     language = arguments.get("language", "en")
    #
    #     # If no media player specified, auto-detect the first available one
    #     if not media_player_entity_id:
    #         response = requests.get(f"{HA_URL}/api/states", headers=headers)
    #         states = response.json()
    #         media_players = [
    #             entity
    #             for entity in states
    #             if entity["entity_id"].startswith("media_player.")
    #         ]
    #
    #         if media_players:
    #             media_player_entity_id = media_players[0]["entity_id"]
    #         else:
    #             return [
    #                 types.TextContent(
    #                     type="text",
    #                     text="Error: No media players found. Please specify a media player entity ID.",
    #                 )
    #             ]
    #
    #     # Use tts.speak service with google_translate_tts
    #     # Try the new format first (Home Assistant 2024+)
    #     payload = {
    #         "target": {"entity_id": "tts.google_translate_en_com"},
    #         "data": {
    #             "media_player_entity_id": media_player_entity_id,
    #             "message": message,
    #             "language": language,
    #         },
    #     }
    #
    #     response = requests.post(
    #         f"{HA_URL}/api/services/tts/speak",
    #         headers=headers,
    #         json=payload,
    #     )
    #
    #     if response.status_code in [200, 204]:
    #         return [
    #             types.TextContent(
    #                 type="text",
    #                 text=f"Speaking: '{message}' on {media_player_entity_id}",
    #             )
    #         ]
    #     else:
    #         # If that fails, try the legacy format
    #         legacy_payload = {
    #             "entity_id": "tts.google_translate_en_com",
    #             "media_player_entity_id": media_player_entity_id,
    #             "message": message,
    #             "language": language,
    #         }
    #
    #         response2 = requests.post(
    #             f"{HA_URL}/api/services/tts/speak",
    #             headers=headers,
    #             json=legacy_payload,
    #         )
    #
    #         if response2.status_code in [200, 204]:
    #             return [
    #                 types.TextContent(
    #                     type="text",
    #                     text=f"Speaking: '{message}' on {media_player_entity_id}",
    #                 )
    #             ]
    #         else:
    #             return [
    #                 types.TextContent(
    #                     type="text",
    #                     text=f"Error: {response.status_code} - {response.text}\n\nNew payload: {payload}\n\nLegacy payload: {legacy_payload}\n\nLegacy response: {response2.status_code} - {response2.text}",
    #                 )
    #             ]

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
