"""
Test Home Assistant integration with mocked HTTP requests.
"""

import pytest
from unittest.mock import Mock, patch
import server_home_assistant


@pytest.mark.asyncio
async def test_toggle_light_calls_correct_endpoint():
    """Test that toggle_light sends correct request to Home Assistant."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"state": "on"}]

    with patch("requests.post", return_value=mock_response) as mock_post:
        result = await server_home_assistant.handle_call_tool(
            "toggle_light", {"entity_id": "light.living_room"}
        )

        # Verify HTTP call was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "light/toggle" in call_args[0][0]
        assert call_args[1]["json"]["entity_id"] == "light.living_room"

        # Verify response
        assert len(result) == 1
        assert "Toggled" in result[0].text


@pytest.mark.asyncio
async def test_get_lights_parses_response():
    """Test that get_lights correctly parses Home Assistant response."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {"brightness": 200},
        },
        {"entity_id": "light.bedroom", "state": "off", "attributes": {}},
    ]

    with patch("requests.get", return_value=mock_response):
        result = await server_home_assistant.handle_call_tool("get_lights", {})

        # Verify response contains both lights
        assert len(result) == 1
        response_text = result[0].text
        assert "light.living_room" in response_text
        assert "light.bedroom" in response_text
        assert "2 light(s)" in response_text


@pytest.mark.asyncio
async def test_handles_home_assistant_timeout():
    """Test graceful handling when Home Assistant is unreachable."""
    import requests

    with patch(
        "requests.post", side_effect=requests.exceptions.Timeout("Connection timeout")
    ):
        result = await server_home_assistant.handle_call_tool(
            "toggle_light", {"entity_id": "light.test"}
        )

        # Should return error message, not crash
        assert len(result) == 1
        error_text = result[0].text.lower()
        assert "timeout" in error_text or "failed" in error_text
