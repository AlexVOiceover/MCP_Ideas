#!C:\Users\Alexander\Documents\FAC\MCP_Ideas\.venv\Scripts\python.exe

import asyncio
import tempfile
import os
from typing import Any
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
import mcp.server.stdio
import mcp.types as types
from gtts import gTTS
import pygame

# Create server instance
server = Server("speaker-server")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools"""
    return [
        types.Tool(
            name="speak",
            description="Speak text out loud through the laptop speakers using Google Text-to-Speech",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to speak out loud",
                    },
                    "language": {
                        "type": "string",
                        "description": "Language code (e.g., 'en' for English, 'es' for Spanish, 'fr' for French). Defaults to 'en'",
                    },
                    "slow": {
                        "type": "boolean",
                        "description": "Speak slowly if true. Defaults to false",
                    },
                },
                "required": ["text"],
            },
        ),
        types.Tool(
            name="list_languages",
            description="List available languages for text-to-speech",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any]
) -> list[types.TextContent]:
    """Handle tool calls"""

    if name == "speak":
        text = arguments["text"]
        language = arguments.get("language", "en")
        slow = arguments.get("slow", False)

        try:
            # Create TTS audio
            tts = gTTS(text=text, lang=language, slow=slow)

            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                temp_path = fp.name
                tts.save(temp_path)

            # Play the audio using pygame (playsound has issues on Windows)
            pygame.mixer.init()
            pygame.mixer.music.load(temp_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            pygame.mixer.quit()

            # Clean up temp file
            os.unlink(temp_path)

            return [
                types.TextContent(
                    type="text",
                    text=f"Spoke: '{text}' (language: {language})",
                )
            ]
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"Error speaking: {str(e)}",
                )
            ]

    elif name == "list_languages":
        # Common languages supported by gTTS
        languages = {
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "nl": "Dutch",
            "ru": "Russian",
            "ja": "Japanese",
            "ko": "Korean",
            "zh-CN": "Chinese (Simplified)",
            "zh-TW": "Chinese (Traditional)",
            "ar": "Arabic",
            "hi": "Hindi",
            "pl": "Polish",
            "sv": "Swedish",
            "da": "Danish",
            "no": "Norwegian",
            "fi": "Finnish",
            "el": "Greek",
            "he": "Hebrew",
            "th": "Thai",
            "vi": "Vietnamese",
            "id": "Indonesian",
            "cs": "Czech",
            "ro": "Romanian",
            "hu": "Hungarian",
            "uk": "Ukrainian",
            "tr": "Turkish",
        }

        output = "Available languages for text-to-speech:\n\n"
        for code, name in languages.items():
            output += f"- {code}: {name}\n"

        return [types.TextContent(type="text", text=output)]

    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    """Main entry point"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="speaker-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=mcp.server.NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
