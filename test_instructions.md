# MCP Server Testing Strategy

## Overview

This document outlines the testing approach for the MCP Ideas project, covering both Home Assistant and Tello drone servers. Tests demonstrate competencies K12 (testing), S5 (system integration), S13 (data structures), and B6 (problem solving).

---

## Test Categories

### 1. Unit Tests - Tool Registration
**Demonstrates:** K12 (Testing Principles), S13 (Data Structures)

**Purpose:** Verify all tools are correctly registered with valid JSON schemas.

**Test File:** `tests/test_tool_schemas.py`

**What to Test:**
- `list_tools()` returns the expected number of tools
- Each tool has required fields: `name`, `description`, `inputSchema`
- `inputSchema` is valid JSON Schema with `"type": "object"` and `"properties"`
- Required fields in schema are listed in the `"required"` array

---

### 2. Unit Tests - Input Validation
**Demonstrates:** S5 (Non-Functional Requirements - Security)

**Purpose:** Ensure invalid inputs are rejected before reaching external APIs.

**Test File:** `tests/test_input_validation.py`

**What to Test:**
- Calling a tool with missing required parameters
- Calling a tool with wrong parameter types (e.g., string instead of int)
- Calling a tool with out-of-range values (e.g., brightness > 100)
- Calling a nonexistent tool name

---

### 3. Integration Tests with Mocking
**Demonstrates:** S5 (Integration Testing)

**Purpose:** Mock external APIs (Home Assistant REST, Tello UDP) and test the full request/response flow.

**Test Files:**
- `tests/test_home_assistant_integration.py`
- `tests/test_tello_integration.py`

**Home Assistant Tests:**
- Mock `requests` responses for Home Assistant API
- Verify `toggle_light` calls correct HA endpoint with correct payload
- Test entity state parsing from HA response
- Test error handling when HA returns 401 (unauthorized)
- Test error handling when HA returns 404 (entity not found)
- Test error handling when HA is unreachable (connection timeout)

**Tello Tests:**
- Mock the Tello SDK (`djitellopy`)
- Verify `get_battery` returns parsed integer
- Verify `takeoff` sends correct command to drone
- Test error handling when drone is disconnected
- Test the `WindowsOpenCVFrameRead` monkey patch (if on Windows)

---

### 4. Error Handling Tests
**Demonstrates:** S5 (System Resilience), B6 (Problem Solving)

**Purpose:** Test graceful degradation and helpful error messages.

**Test File:** `tests/test_error_handling.py`

**What to Test:**
- Lazy import fallback when `cv2` is not available
- Helpful error message for WSL/headless environments (missing graphics libraries)
- Retry logic in `WindowsOpenCVFrameRead` frame grabbing
- Server continues running after individual tool failures (no cascading crashes)

---

### 5. Schema Validation Tests
**Demonstrates:** S5 (Security Testing)

**Purpose:** Verify schemas prevent malicious/invalid input.

**Test File:** `tests/test_schema_validation.py`

**What to Test:**
- `entity_id` parameter rejects injection attempts
- Numeric parameters reject string values
- Optional parameters work correctly when omitted
- No unexpected fields are accepted

---

## Specific Test Examples

### Example 1: Tool Registration Test

```python
# tests/test_tool_schemas.py
import pytest
from server import server

@pytest.mark.asyncio
async def test_list_tools_returns_all_tools():
    """Verify all Home Assistant tools are registered."""
    tools = await server.list_tools()
    tool_names = [t.name for t in tools]

    # Check expected tools exist
    assert "get_lights" in tool_names
    assert "toggle_light" in tool_names
    assert len(tools) >= 20  # Adjust based on actual count

@pytest.mark.asyncio
async def test_tool_schema_structure():
    """Verify each tool has valid JSON Schema."""
    tools = await server.list_tools()

    for tool in tools:
        assert tool.name, "Tool must have a name"
        assert tool.description, "Tool must have a description"
        assert tool.inputSchema, "Tool must have inputSchema"
        assert tool.inputSchema.get("type") == "object"
        assert "properties" in tool.inputSchema
```

---

### Example 2: Mocked Integration Test

```python
# tests/test_home_assistant_integration.py
import pytest
from unittest.mock import Mock, patch

@pytest.mark.asyncio
async def test_toggle_light_calls_correct_endpoint():
    """Test that toggle_light sends correct request to Home Assistant."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"state": "on"}]

    with patch("requests.post", return_value=mock_response) as mock_post:
        # Call the handler directly
        from server import handle_call_tool
        result = await handle_call_tool("toggle_light", {"entity_id": "light.living_room"})

        # Verify HTTP call was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "light/toggle" in call_args[0][0]
        assert call_args[1]["json"]["entity_id"] == "light.living_room"

        # Verify response
        assert len(result) == 1
        assert "Toggled" in result[0].text
```

---

### Example 3: Error Handling Test

```python
# tests/test_error_handling.py
import pytest
from unittest.mock import patch
import requests

@pytest.mark.asyncio
async def test_handles_home_assistant_timeout():
    """Test graceful handling when Home Assistant is unreachable."""
    with patch("requests.post", side_effect=requests.exceptions.Timeout("Connection timeout")):
        from server import handle_call_tool
        result = await handle_call_tool("toggle_light", {"entity_id": "light.test"})

        # Should return error message, not crash
        assert len(result) == 1
        assert "error" in result[0].text.lower() or "timeout" in result[0].text.lower()
```

---

### Example 4: Lazy Import Test

```python
# tests/test_error_handling.py
import pytest
from unittest.mock import patch
import sys

@pytest.mark.asyncio
async def test_cv2_lazy_import_graceful_failure():
    """Test that missing cv2 provides helpful error message."""
    # Simulate cv2 not being installed
    with patch.dict(sys.modules, {"cv2": None}):
        from server import handle_call_tool

        # Attempt to call snapshot function
        result = await handle_call_tool("get_camera_snapshot", {"entity_id": "camera.logitech_usb"})

        # Should return helpful error, not crash
        assert len(result) == 1
        error_text = result[0].text.lower()
        assert "opencv" in error_text or "cv2" in error_text
        assert "install" in error_text or "not available" in error_text
```

---

## Configuration

### pyproject.toml additions:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "--cov=. --cov-report=html --cov-report=term-missing"

[tool.coverage.run]
omit = ["tests/*", ".venv/*", "venv/*"]
```

---

## Running Tests

### Install Test Dependencies

```bash
pip install pytest pytest-asyncio pytest-cov
```

### Run All Tests with Coverage

```bash
# Run all tests with coverage report
pytest --cov=. --cov-report=html --cov-report=term-missing

# Run specific test file
pytest tests/test_tool_schemas.py -v

# Run specific test
pytest tests/test_tool_schemas.py::test_list_tools_returns_all_tools -v

# Run with verbose output and short traceback
pytest -v --tb=short
```

---

## Expected Output for Portfolio

After implementing tests, generate the following for your portfolio:

1. **Coverage Report Screenshot** - showing percentage coverage
2. **Passing Tests Screenshot** - showing green test results
3. **Test Code Snippets** - 2-3 key examples demonstrating:
   - Tool schema validation (K12, S13)
   - Mocked integration testing (S5)
   - Error handling (S5, B6)

---

## Implementation Notes

### Current Codebase Architecture

- **Decorators:** Uses `@server.list_tools()` and `@server.call_tool()` from MCP SDK
- **Home Assistant:** Uses `requests` library for HTTP requests
- **Tello:** Uses `djitellopy` library with UDP communication
- **Windows Patch:** `WindowsOpenCVFrameRead` class patches video streaming for Windows
- **Environment Variables:** `HA_URL`, `HA_TOKEN`, `TELEGRAM_CHAT_ID` for Home Assistant config

### File Structure

```
MCP_Ideas/
├── server.py                          # Home Assistant server (current file)
├── server_tello.py                    # Tello drone server (on tello branch)
├── tests/
│   ├── __init__.py
│   ├── test_tool_schemas.py           # Tool registration tests
│   ├── test_input_validation.py       # Input validation tests
│   ├── test_home_assistant_integration.py  # HA mocked integration tests
│   ├── test_tello_integration.py      # Tello mocked integration tests
│   ├── test_error_handling.py         # Error handling tests
│   └── test_schema_validation.py      # Security validation tests
├── pyproject.toml                     # Test configuration
└── requirements.txt                   # Add pytest dependencies
```

---

## Priority Order

If time is limited, implement in this order:

1. **Tool Schema Validation Tests** (Easy wins, demonstrates K12)
   - Quick to implement
   - Clear pass/fail criteria
   - Foundation for other tests

2. **Mocked Home Assistant Integration Tests** (Demonstrates S5-Integration)
   - Tests real-world scenarios
   - Shows understanding of HTTP mocking
   - Critical for portfolio

3. **Error Handling Tests** (Demonstrates S5-System, B6)
   - Shows defensive programming
   - Demonstrates problem-solving skills
   - Important for production code

4. **Input Validation Tests** (Demonstrates S5-Security)
   - Security best practices
   - Prevents common vulnerabilities
   - Good for portfolio narrative

---

## Success Criteria

- ✅ At least 10 passing tests
- ✅ Coverage report generated (aim for >70%)
- ✅ Tests run without external dependencies (all external calls mocked)
- ✅ Clear test names that describe what's being tested
- ✅ Tests organized by type (unit, integration, error handling)
- ✅ All tests pass consistently
- ✅ No actual Home Assistant or Tello connections required

---

## Common Pitfalls to Avoid

1. **Don't test the MCP SDK itself** - only test your code
2. **Mock all external dependencies** - tests should run offline
3. **Use async/await correctly** - remember `@pytest.mark.asyncio`
4. **Don't test implementation details** - test behavior, not internals
5. **Keep tests independent** - each test should run in isolation

---

## Portfolio Documentation Tips

When documenting these tests in your portfolio:

1. **Explain WHY you chose these tests** - link to competencies (K12, S5, B6, S13)
2. **Show the coverage report** - demonstrate thoroughness
3. **Highlight edge cases** - show you thought about error scenarios
4. **Document the mocking strategy** - explain how you isolated external dependencies
5. **Include lessons learned** - what did testing reveal about your code?
