"""
Test error handling and graceful degradation.
"""

import pytest
from unittest.mock import patch
import server_home_assistant


@pytest.mark.asyncio
async def test_unknown_tool_raises_error():
    """Test that calling an unknown tool raises ValueError."""
    with pytest.raises(ValueError, match="Unknown tool"):
        await server_home_assistant.handle_call_tool("nonexistent_tool", {})


@pytest.mark.asyncio
async def test_connection_error_returns_message():
    """Test graceful handling of connection errors."""
    import requests

    with patch(
        "requests.get",
        side_effect=requests.exceptions.ConnectionError("Network unreachable"),
    ):
        result = await server_home_assistant.handle_call_tool("get_lights", {})

        # Should return error message, not crash
        assert len(result) == 1
        error_text = result[0].text.lower()
        assert (
            "error" in error_text or "failed" in error_text or "network" in error_text
        )
