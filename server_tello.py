#!/home/alex/FAC/workshops/MCP_Ideas/.venv/bin/python

import asyncio
from typing import Any
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
import mcp.server.stdio
import mcp.types as types
from djitellopy import Tello


# Create server instance
server = Server("tello-drone-server")

# Global Tello instance
tello = None


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
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any]
) -> list[types.TextContent]:
    """Handle tool calls"""
    global tello

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
