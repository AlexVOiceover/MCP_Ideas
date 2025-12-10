"""
Test tool registration and schema validation.
"""

import pytest
import server_home_assistant


@pytest.mark.asyncio
async def test_list_tools_returns_all_tools():
    """Verify all Home Assistant tools are registered."""
    # Call the actual handler function directly
    tools = await server_home_assistant.handle_list_tools()
    tool_names = [t.name for t in tools]

    # Check expected tools exist
    assert "get_lights" in tool_names
    assert "toggle_light" in tool_names
    assert "get_temperature" in tool_names
    assert len(tools) >= 15  # Adjust based on actual count


@pytest.mark.asyncio
async def test_tool_schema_structure():
    """Verify each tool has valid JSON Schema."""
    tools = await server_home_assistant.handle_list_tools()

    for tool in tools:
        assert tool.name, "Tool must have a name"
        assert tool.description, "Tool must have a description"
        assert tool.inputSchema, "Tool must have inputSchema"
        assert tool.inputSchema.get("type") == "object"
        assert "properties" in tool.inputSchema


@pytest.mark.asyncio
async def test_required_fields_in_schema():
    """Verify tools with required parameters declare them in schema."""
    tools = await server_home_assistant.handle_list_tools()

    # Find toggle_light tool (has required entity_id parameter)
    toggle_light = next((t for t in tools if t.name == "toggle_light"), None)
    assert toggle_light is not None, "toggle_light tool should exist"

    # Check required field is declared
    assert "required" in toggle_light.inputSchema
    assert "entity_id" in toggle_light.inputSchema["required"]
