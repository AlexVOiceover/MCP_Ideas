#!/usr/bin/env python3

import asyncio
from typing import Any
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
import mcp.server.stdio
import mcp.types as types


# Create server instance
server = Server("workshop-server")


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
            name="weather",
            description="Get current weather for a city",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The city name to get weather for",
                    }
                },
                "required": ["city"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any]
) -> list[types.TextContent]:
    """Handle tool calls"""

    if name == "ping":
        return [types.TextContent(type="text", text="pong! Server is running.")]

    elif name == "weather":
        city = arguments["city"]
        # Mock weather data
        weather_info = f"Weather in {city}:\nTemperature: 22°C\nCondition: Sunny\nHumidity: 65%"
        return [types.TextContent(type="text", text=weather_info)]

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
                server_name="workshop-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=mcp.server.NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
