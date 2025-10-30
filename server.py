#!/usr/bin/env python3

import asyncio
from typing import Any
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
import mcp.server.stdio
import mcp.types as types
import docker


# Create server instance
server = Server("docker-health-server")

# Initialize Docker client
docker_client = docker.from_env()


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools"""
    return [
        types.Tool(
            name="list_containers",
            description="List all running Docker containers with their status",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="stop_container",
            description="Stop a running Docker container by name",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name of the container to stop",
                    }
                },
                "required": ["name"],
            },
        ),
        types.Tool(
            name="start_container",
            description="Start a stopped Docker container by name",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name of the container to start",
                    }
                },
                "required": ["name"],
            },
        ),
        types.Tool(
            name="get_logs",
            description="Get recent logs from a Docker container",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name of the container to get logs from",
                    }
                },
                "required": ["name"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any]
) -> list[types.TextContent]:
    """Handle tool calls"""

    if name == "list_containers":
        # Get all containers (running and stopped)
        containers = docker_client.containers.list(all=True)

        # Build output text
        output = f"Total containers: {len(containers)}\n\n"
        for container in containers:
            output += f"Name: {container.name}\n"
            output += f"Status: {container.status}\n"
            output += f"Image: {container.image.tags[0] if container.image.tags else 'N/A'}\n\n"

        return [types.TextContent(type="text", text=output)]

    elif name == "stop_container":
        container_name = arguments["name"]
        container = docker_client.containers.get(container_name)
        container.stop()
        return [types.TextContent(type="text", text=f"Container '{container_name}' stopped successfully")]

    elif name == "start_container":
        container_name = arguments["name"]
        container = docker_client.containers.get(container_name)
        container.start()
        return [types.TextContent(type="text", text=f"Container '{container_name}' started successfully")]

    elif name == "get_logs":
        container_name = arguments["name"]
        container = docker_client.containers.get(container_name)
        logs = container.logs(tail=50).decode('utf-8')
        return [types.TextContent(type="text", text=f"Logs for '{container_name}':\n\n{logs}")]

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
                server_name="docker-health-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=mcp.server.NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
