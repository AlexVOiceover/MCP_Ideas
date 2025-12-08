# MCP Ideas - Technical Documentation
## Model Context Protocol Server Collection for IoT and Drone Control

---

## Relevant Source Files

This document examines the following key files from the repository:

- [server_home_assistant.py](server_home_assistant.py) - Home Assistant MCP server implementation (929 lines)
- [server_tello.py](server_tello.py) - Tello drone MCP server implementation (890 lines)
- [requirements.txt](requirements.txt) - Python dependency specifications
- [claude_desktop_config.json](claude_desktop_config.json) - Claude Desktop MCP server configuration
- [.env](.env) - Environment variables for API credentials and endpoints
- [.gitignore](.gitignore) - Git version control exclusions
- [README.md](README.md) - User-facing documentation and setup guide
- [infrastructure.png](infrastructure.png) - System architecture diagram

---

## Purpose and Scope

This technical overview provides a comprehensive guide to the MCP Ideas codebase architecture, implementation patterns, and integration mechanisms. It is intended for developers who need to:

- Understand the Model Context Protocol (MCP) server implementation patterns
- Extend functionality by adding new tools or integrating additional devices
- Debug issues with device connectivity or command execution
- Contribute to the project or adapt it for similar use cases

For end-user setup instructions and usage examples, refer to [README.md](README.md).

---

## Application Purpose

**MCP Ideas** is a collection of specialized MCP (Model Context Protocol) servers that enable Claude Desktop to interact with physical hardware devices and home automation systems through natural language commands. The project bridges AI capabilities with real-world IoT devices through standardized MCP interfaces.

### Primary Features

1. **Smart Home Control** - Complete Home Assistant integration enabling control of:
   - Lighting systems (Philips Hue, generic smart bulbs)
   - Climate control (thermostats, temperature sensors)
   - Security devices (smart locks, cameras)
   - Switches and plugs (Tapo, generic smart plugs)
   - Covers (garage doors, blinds)
   - Sensors (motion, air quality, door/window)
   - Media players (TTS announcements)
   - Telegram integration (camera snapshots, notifications)

2. **Drone Operations** - Full DJI Tello drone control including:
   - Flight commands (takeoff, landing, movement, rotation)
   - Advanced maneuvers (flips in 4 directions)
   - Camera operations (live streaming, snapshot capture)
   - Sensor monitoring (battery, height, temperature, barometer)
   - Emergency stop functionality

### Target Users

- Home automation enthusiasts seeking natural language control of smart devices
- Drone hobbyists wanting AI-assisted flight control
- Developers exploring MCP protocol implementations
- Researchers studying AI-hardware interaction patterns

**Sources:** README.md:1-29, server_home_assistant.py:1-24, server_tello.py:1-17

---

## Technology Stack

| Category | Technology | Version/Notes | Purpose |
|----------|-----------|---------------|---------|
| **Runtime Environment** | Python | 3.x | Primary programming language |
| **Protocol Framework** | MCP SDK | Latest | Model Context Protocol implementation |
| **Home Automation** | Home Assistant API | REST API | Smart home device control |
| **HTTP Client** | requests | Latest | HTTP API communication |
| **Drone SDK** | djitellopy | Latest | DJI Tello drone control library |
| **Video Processing** | OpenCV (cv2) | Latest | Video frame processing (Windows UDP fix) |
| **Computer Vision** | PyAV | Latest | Video streaming (Linux/macOS) |
| **Image Encoding** | base64 | Standard library | Image data transmission |
| **Configuration** | python-dotenv | Implicit | Environment variable management |
| **Async Framework** | asyncio | Standard library | Asynchronous server operations |
| **Type System** | typing | Standard library | Type hints and annotations |
| **Threading** | threading | Standard library | Background frame reading (Windows) |
| **Platform Detection** | platform | Standard library | OS-specific code paths |
| **Logging** | logging | Standard library | Debug output management |
| **Date/Time** | datetime | Standard library | Timestamp generation |
| **Regular Expressions** | re | Standard library | Sensor response parsing |
| **Numeric Operations** | numpy | Dependency of OpenCV | Array operations for video frames |
| **Transport Protocol** | stdio | MCP standard | Claude Desktop communication |
| **Development Tools** | MCP Inspector | npx package | Local MCP server testing |

**Sources:** requirements.txt:1-4, server_home_assistant.py:1-13, server_tello.py:1-33

---

## Architecture Overview

### Architectural Pattern

The system implements a **three-tier bridge architecture** that translates natural language commands from Claude into device-specific API calls:

```
┌─────────────────────────────┐
│    Claude Desktop (User)    │
│   Natural Language Input    │
└──────────────┬──────────────┘
               │ stdio transport
               ▼
┌─────────────────────────────┐
│   MCP Server Layer          │
│   ┌────────────────────┐    │
│   │ Home Assistant     │    │
│   │ Server (27 tools)  │    │
│   └────────────────────┘    │
│   ┌────────────────────┐    │
│   │ Tello Drone        │    │
│   │ Server (24 tools)  │    │
│   └────────────────────┘    │
└──────────────┬──────────────┘
               │ HTTP/UDP
               ▼
┌─────────────────────────────┐
│   Device/API Layer          │
│   ┌────────────────────┐    │
│   │ Home Assistant API │────► Zigbee Devices
│   └────────────────────┘    │
│   ┌────────────────────┐    │
│   │ Tello SDK (WiFi)   │────► DJI Tello Drone
│   └────────────────────┘    │
└─────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Communication Protocol |
|-----------|---------------|----------------------|
| **Claude Desktop** | User interface, natural language understanding, tool selection | stdio (JSON-RPC) |
| **Home Assistant Server** | Translate MCP tool calls to Home Assistant REST API requests | HTTP/HTTPS |
| **Tello Server** | Translate MCP tool calls to Tello SDK commands | UDP (commands: 8889, video: 11111) |
| **Home Assistant Instance** | Smart home hub, device state management | Zigbee, WiFi, Z-Wave |
| **Tello Drone** | Physical drone hardware | WiFi Direct |

### Application Initialization Flow

#### Home Assistant Server Startup

1. **Environment Loading** (server_home_assistant.py:15-21)
   ```python
   load_dotenv()
   HA_URL = os.getenv("HA_URL", "http://localhost:8123")
   HA_TOKEN = os.getenv("HA_TOKEN")
   TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))
   ```

2. **Server Instantiation** (server_home_assistant.py:24)
   ```python
   server = Server("homeassistant-server")
   ```

3. **Tool Registration** (server_home_assistant.py:27-28)
   - Decorator `@server.list_tools()` registers 27 tools
   - Each tool defines name, description, and JSON schema

4. **Tool Handler Registration** (server_home_assistant.py:390-391)
   - Decorator `@server.call_tool()` handles tool execution
   - Async handler processes tool calls and returns responses

5. **Server Launch** (server_home_assistant.py:910-929)
   ```python
   async with stdio_server() as (read_stream, write_stream):
       await server.run(read_stream, write_stream, InitializationOptions(...))
   ```

#### Tello Server Startup

1. **Logging Configuration** (server_tello.py:23)
   ```python
   logging.getLogger('djitellopy').setLevel(logging.WARNING)
   ```
   *Suppresses verbose logging to avoid interfering with stdio protocol*

2. **Platform-Specific Patching** (server_tello.py:28-138)
   - Detects Windows platform
   - Applies OpenCV VideoCapture patch for UDP video streaming
   - Replaces PyAV with cv2.VideoCapture to fix Error 10014

3. **Server Instantiation** (server_tello.py:141)
   ```python
   server = Server("tello-drone-server")
   ```

4. **Global State Initialization** (server_tello.py:144-147)
   ```python
   tello = None  # Drone connection object
   stream_active = False  # Video stream status
   frame_read = None  # Frame reader object
   ```

5. **Tool Registration and Launch** (server_tello.py:150, 871-890)
   - Similar pattern to Home Assistant server
   - 24 tools registered for drone control

**Sources:** server_home_assistant.py:1-24, 910-929, server_tello.py:1-150, 871-890

---

## Core Features Overview

### Home Assistant Integration (27 Tools)

#### Lighting Control
- **Tools:** `get_lights`, `toggle_light`, `turn_on_light`, `turn_off_light`, `set_light_brightness`, `set_light_color`
- **Key Implementation:** RGB color control via Home Assistant API
- **Example:**
  ```python
  requests.post(
      f"{HA_URL}/api/services/light/turn_on",
      headers=headers,
      json={"entity_id": entity_id, "rgb_color": [red, green, blue]}
  )
  ```
- **Sources:** server_home_assistant.py:31-127, 412-466

#### Climate Management
- **Tools:** `get_temperature`, `get_climate`, `set_climate`
- **Features:** Temperature sensor reading, thermostat control
- **Entity Filtering:** Uses device_class and entity_id patterns
- **Sources:** server_home_assistant.py:468-499

#### Security & Access Control
- **Tools:** `get_locks`, `lock_door`, `unlock_door`, `get_camera_snapshot`, `send_camera_snapshot`
- **Notable Feature:** Telegram integration for camera snapshots
- **Image Transmission:** Base64 encoding for MCP ImageContent
- **Sources:** server_home_assistant.py:128-186, 500-585

#### Smart Switches & Covers
- **Tools:** `get_switches`, `toggle_switch`, `turn_on_switch`, `turn_off_switch`, `get_covers`, `open_cover`, `close_cover`
- **Use Cases:** Smart plug control, garage door operation, blind control
- **Sources:** server_home_assistant.py:187-289

#### Sensor Monitoring
- **Tools:** `get_sensors`, `get_binary_sensors`
- **Sensor Types:** Motion, air quality, door/window, humidity, etc.
- **Sources:** server_home_assistant.py:290-328

#### Media & Notifications
- **Tools:** `speak` (TTS), `send_telegram_message`
- **TTS Service:** Uses Home Assistant's TTS integration
- **Sources:** server_home_assistant.py:329-389

### Tello Drone Integration (24 Tools)

#### Connection Management
- **Tool:** `connect`
- **Features:** Connection validation, battery check (>20%), pre-flight validation
- **Sources:** server_tello.py:411-441

#### Flight Controls
- **Tools:** `takeoff`, `land`, `emergency`
- **Safety:** Battery level validation before takeoff
- **Example:**
  ```python
  if battery < 20:
      return [types.TextContent(type="text", text="Battery too low for takeoff...")]
  tello.takeoff()
  ```
- **Sources:** server_tello.py:443-494

#### Movement Commands
- **Tools:** `move_forward`, `move_back`, `move_left`, `move_right`, `move_up`, `move_down`
- **Parameters:** Distance in centimeters (20-500 cm)
- **Sources:** server_tello.py:496-618

#### Rotation Commands
- **Tools:** `rotate_clockwise`, `rotate_counter_clockwise`
- **Parameters:** Angle in degrees (1-360°)
- **Sources:** server_tello.py:620-674

#### Advanced Maneuvers
- **Tool:** `flip`
- **Directions:** forward, back, left, right
- **Sources:** server_tello.py:676-708

#### Sensor Monitoring
- **Tools:** `get_battery`, `get_height`, `get_temperature`, `get_barometer`, `get_flight_time`
- **Response Parsing:** Regex extraction of numeric values from unit strings
- **Example:**
  ```python
  # Tello returns "80dm" for height
  height_dm = int(re.search(r'\d+', response).group())
  height_cm = height_dm * 10
  ```
- **Sources:** server_tello.py:710-772

#### Camera Operations
- **Tools:** `start_video_stream`, `stop_video_stream`, `get_snapshot`, `save_snapshot`
- **Windows Fix:** Custom OpenCV VideoCapture implementation
- **Frame Encoding:** JPEG + base64 for MCP ImageContent
- **Sources:** server_tello.py:40-138, 774-865

**Sources:** server_tello.py:150-865

---

## Component Hierarchy

### Server Organization

Both servers follow an identical structural pattern:

```
MCP Server
├── Imports & Configuration
│   ├── MCP SDK modules
│   ├── Device-specific libraries
│   ├── Standard library utilities
│   └── Environment variable loading
│
├── Server Instance Creation
│   └── Server(name) initialization
│
├── Tool Definitions (@server.list_tools)
│   ├── Tool metadata (name, description)
│   └── JSON Schema for input validation
│
├── Tool Handler (@server.call_tool)
│   ├── Argument extraction
│   ├── Device API calls
│   ├── Response formatting
│   └── Error handling
│
└── Main Entry Point (async main)
    ├── stdio_server context manager
    ├── Server initialization options
    └── Server.run() event loop
```

### Home Assistant Server Structure

```
server_home_assistant.py (929 lines)
├── Configuration (lines 1-24)
│   ├── Environment variables
│   └── Server instance
│
├── Tool Registry (lines 27-389)
│   ├── Light tools (7 tools)
│   ├── Climate tools (3 tools)
│   ├── Lock tools (3 tools)
│   ├── Camera tools (2 tools)
│   ├── Switch tools (4 tools)
│   ├── Cover tools (3 tools)
│   ├── Sensor tools (2 tools)
│   └── Media/Notification tools (3 tools)
│
├── Tool Handler (lines 390-907)
│   ├── Request header creation
│   ├── Tool name routing
│   ├── Home Assistant API calls
│   └── Response formatting
│
└── Server Lifecycle (lines 910-929)
    └── async main() with stdio transport
```

### Tello Server Structure

```
server_tello.py (890 lines)
├── Platform-Specific Patch (lines 1-138)
│   ├── Windows detection
│   ├── WindowsOpenCVFrameRead class
│   └── get_frame_read() override
│
├── Configuration (lines 140-147)
│   ├── Server instance
│   └── Global state variables
│
├── Tool Registry (lines 150-409)
│   ├── Connection tool (1 tool)
│   ├── Flight controls (3 tools)
│   ├── Movement tools (6 tools)
│   ├── Rotation tools (2 tools)
│   ├── Advanced maneuvers (1 tool)
│   ├── Sensor tools (5 tools)
│   └── Camera tools (4 tools)
│
├── Tool Handler (lines 411-868)
│   ├── Connection management
│   ├── Tello SDK calls
│   ├── Sensor response parsing
│   └── Camera frame processing
│
└── Server Lifecycle (lines 871-890)
    └── async main() with stdio transport
```

**Sources:** server_home_assistant.py:1-929, server_tello.py:1-890

---

## Data Flow Pattern

### End-to-End Request Flow

```
1. User Input
   │
   ├─► User types natural language command in Claude Desktop
   │   Example: "Turn on the living room light to 50% brightness in blue"
   │
   ▼
2. Claude Processing
   │
   ├─► Claude's LLM analyzes intent and available tools
   ├─► Selects appropriate MCP tool: set_light_brightness
   └─► Prepares tool call with parameters
   │
   ▼
3. MCP Protocol (stdio transport)
   │
   ├─► JSON-RPC formatted tool call sent via stdio
   └─► Example payload: {"name": "set_light_brightness", "arguments": {...}}
   │
   ▼
4. Server Processing
   │
   ├─► @server.call_tool() handler receives request
   ├─► Extracts and validates arguments
   ├─► Determines tool handler based on name
   └─► Executes device-specific logic
   │
   ▼
5. Device API Call
   │
   ├─► Home Assistant: HTTP POST to /api/services/light/turn_on
   ├─► Tello: UDP command via djitellopy SDK
   └─► Authentication headers/tokens included
   │
   ▼
6. Device Execution
   │
   ├─► Home Assistant sends Zigbee/WiFi command to smart bulb
   ├─► Tello drone executes flight command
   └─► Device state changes
   │
   ▼
7. Response Propagation
   │
   ├─► Device confirms execution (or returns error)
   ├─► Server formats response as types.TextContent or types.ImageContent
   └─► Response sent back via stdio to Claude Desktop
   │
   ▼
8. User Feedback
   │
   └─► Claude presents natural language response to user
       Example: "I've set the living room light to 50% brightness"
```

### Home Assistant API Flow Example

```python
# Step 4-5: Server processes tool call and makes API request
headers = {
    "Authorization": f"Bearer {HA_TOKEN}",
    "Content-Type": "application/json",
}

response = requests.post(
    f"{HA_URL}/api/services/light/turn_on",
    headers=headers,
    json={
        "entity_id": "light.living_room",
        "brightness": 127,  # 50% of 255
        "rgb_color": [0, 0, 255]  # Blue
    }
)

# Step 7: Format response
return [types.TextContent(
    type="text",
    text=f"Set light.living_room to brightness 127 with RGB(0, 0, 255)"
)]
```

**Sources:** server_home_assistant.py:390-466, README.md:105-138

### Tello Drone Command Flow Example

```python
# Step 4-5: Server processes takeoff command
if tello is None:
    return [types.TextContent(type="text", text="Not connected to drone...")]

battery = tello.get_battery()
if battery < 20:
    return [types.TextContent(type="text", text="Battery too low...")]

# Execute takeoff via SDK
tello.takeoff()

# Step 7: Return confirmation
return [types.TextContent(
    type="text",
    text=f"Drone took off successfully. Battery: {battery}%"
)]
```

**Sources:** server_tello.py:443-473, README.md:140-163

---

## Entry Points and Configuration

### Development Entry Points

| Entry Point | Purpose | Command |
|------------|---------|---------|
| **server_home_assistant.py** | Launch Home Assistant server standalone | `python server_home_assistant.py` |
| **server_tello.py** | Launch Tello server standalone | `python server_tello.py` |
| **MCP Inspector (HA)** | Test Home Assistant server locally | `npx @modelcontextprotocol/inspector .venv/Scripts/python.exe server_home_assistant.py` |
| **MCP Inspector (Tello)** | Test Tello server locally | `npx @modelcontextprotocol/inspector .venv/Scripts/python.exe server_tello.py` |
| **Claude Desktop** | Production usage via configured MCP servers | Automatic via `claude_desktop_config.json` |

**Sources:** README.md:85-103

### Configuration Files

| File | Purpose | Format | Required Fields |
|------|---------|--------|----------------|
| **.env** | Environment variables for API credentials | Key-value pairs | `HA_URL`, `HA_TOKEN`, `TELEGRAM_CHAT_ID` |
| **claude_desktop_config.json** | Claude Desktop MCP server registration | JSON | `mcpServers.{name}.command`, `mcpServers.{name}.args` |
| **requirements.txt** | Python package dependencies | Plain text list | `mcp`, `djitellopy`, `requests` |
| **.gitignore** | Git exclusion patterns | Pattern list | `.env`, `.venv/`, `__pycache__/`, `claude_desktop_config.json` |

**Sources:** .env:1-4, claude_desktop_config.json:1-16, requirements.txt:1-3, .gitignore

### Build Scripts and Commands

| Command | Purpose | Environment |
|---------|---------|-------------|
| `python -m venv .venv` | Create virtual environment | Development |
| `.venv/Scripts/activate` (Windows) | Activate virtual environment | Development |
| `source .venv/bin/activate` (Unix) | Activate virtual environment | Development |
| `pip install -r requirements.txt` | Install dependencies | Development |
| `python server_home_assistant.py` | Run Home Assistant server | Development/Production |
| `python server_tello.py` | Run Tello server | Development/Production |
| `npx @modelcontextprotocol/inspector <python> <script>` | Launch MCP Inspector for testing | Development |

**Sources:** README.md:32-103

### Environment Configuration

#### .env File Structure
```bash
# Home Assistant Configuration
HA_URL=http://localhost:8123              # Home Assistant instance URL
HA_TOKEN=your_long_lived_access_token     # Long-lived access token from HA
TELEGRAM_CHAT_ID=123456789                # Telegram chat ID for notifications
```

#### Claude Desktop Configuration Structure
```json
{
  "mcpServers": {
    "homeassistant": {
      "command": "/path/to/.venv/Scripts/python.exe",
      "args": ["server_home_assistant.py"]
    },
    "tello": {
      "command": "/path/to/.venv/Scripts/python.exe",
      "args": ["server_tello.py"]
    }
  }
}
```

**Sources:** README.md:48-79, claude_desktop_config.json:1-16

---

## Key Architectural Patterns

### 1. MCP Tool Registration Pattern

**Description:** Declarative tool definition using decorators for automatic registration.

**Implementation:**
```python
@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools"""
    return [
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
        # ... more tools
    ]
```

**Benefits:**
- Type-safe input validation via JSON Schema
- Automatic documentation generation
- Claude can inspect available tools and their parameters

**Sources:** server_home_assistant.py:27-389, server_tello.py:150-409

---

### 2. Centralized Tool Handler Pattern

**Description:** Single async handler function routes all tool calls based on name.

**Implementation:**
```python
@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent | types.ImageContent]:
    """Handle tool calls"""

    # Common setup (e.g., authentication headers)
    headers = {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json",
    }

    # Route to specific handler
    if name == "turn_on_light":
        entity_id = arguments["entity_id"]
        requests.post(
            f"{HA_URL}/api/services/light/turn_on",
            headers=headers,
            json={"entity_id": entity_id}
        )
        return [types.TextContent(type="text", text=f"Turned on {entity_id}")]

    elif name == "turn_off_light":
        # ... handle turn_off_light

    else:
        raise ValueError(f"Unknown tool: {name}")
```

**Benefits:**
- Centralized error handling
- Shared authentication/configuration logic
- Easy to add new tools

**Sources:** server_home_assistant.py:391-907, server_tello.py:411-868

---

### 3. Platform-Specific Monkey Patching

**Description:** Runtime detection and patching of incompatible libraries for platform-specific fixes.

**Problem:** PyAV's `av.open()` fails with Error 10014 (WSAEFAULT) on Windows when opening UDP streams.

**Solution:**
```python
if platform.system() == 'Windows':
    class WindowsOpenCVFrameRead:
        """Windows-compatible frame reader using OpenCV instead of PyAV"""
        def __init__(self, tello, address, with_queue=False, maxsize=32):
            udp_url = f'udp://0.0.0.0:{tello.VS_UDP_PORT}'
            self.cap = cv2.VideoCapture(udp_url, cv2.CAP_FFMPEG)
            # ... frame reading logic

    # Monkey patch the Tello class method
    def patched_get_frame_read(self, with_queue=False, maxsize=32):
        return WindowsOpenCVFrameRead(self, self.address, with_queue, maxsize)

    djitellopy.tello.Tello.get_frame_read = patched_get_frame_read
```

**Benefits:**
- Cross-platform compatibility without forking libraries
- Graceful degradation on unsupported platforms
- Isolated platform-specific code

**Sources:** server_tello.py:25-138

---

### 4. Lazy Import Pattern for Optional Dependencies

**Description:** Defer imports of optional dependencies until needed to avoid startup failures.

**Implementation:**
```python
# At module level: cv2 is NOT imported

# Inside tool handler:
def handle_get_snapshot():
    try:
        import cv2  # Lazy import only when camera feature is used
    except ImportError:
        return [types.TextContent(
            type="text",
            text="OpenCV (cv2) is not available. Camera features require graphics libraries..."
        )]

    # Use cv2 here...
```

**Benefits:**
- Server can run without optional dependencies (e.g., OpenCV in WSL without libGL)
- Clear error messages indicate missing dependencies
- Reduces startup time when features aren't used

**Sources:** server_tello.py:19-20, 774-833

---

### 5. Global State Management for Stateful Devices

**Description:** Module-level global variables maintain connection state across tool calls.

**Implementation:**
```python
# Global state
tello = None          # Drone connection object
stream_active = False # Video stream status
frame_read = None     # Frame reader object

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    global tello, stream_active, frame_read

    if name == "connect":
        if tello is None:
            tello = Tello()
            tello.connect()
        return [types.TextContent(type="text", text="Connected")]

    elif name == "takeoff":
        if tello is None:
            return [types.TextContent(type="text", text="Not connected. Use 'connect' first.")]
        tello.takeoff()
        return [types.TextContent(type="text", text="Took off")]
```

**Benefits:**
- Persistent connections across multiple tool calls
- State validation before operations
- Efficient resource usage (don't reconnect every time)

**Considerations:**
- Not thread-safe (acceptable for single-user CLI context)
- Connection state can become stale if device disconnects

**Sources:** server_tello.py:144-147, 411-494

---

### 6. Retry Logic for Unreliable Operations

**Description:** Retry frame grabbing with exponential backoff for initialization delays.

**Implementation:**
```python
max_attempts = 30  # Try for ~3 seconds
attempt = 0
self.grabbed = False

while not self.grabbed and attempt < max_attempts:
    self.grabbed, self.frame = self.cap.read()
    if self.grabbed and self.frame is not None:
        Tello.LOGGER.info(f'Successfully grabbed first frame on attempt {attempt + 1}')
        break
    attempt += 1
    time.sleep(0.1)  # 100ms delay between attempts

if not self.grabbed or self.frame is None:
    raise TelloException('Failed to grab first frame after 30 attempts...')
```

**Benefits:**
- Handles network/initialization delays gracefully
- Provides clear failure messages after reasonable timeout
- Logs success attempt for debugging

**Sources:** server_tello.py:76-95

---

### 7. Response Parsing with Regular Expressions

**Description:** Extract numeric values from unit-suffixed sensor responses.

**Problem:** Tello SDK returns responses like "80dm" (decimeters) or "25°C" instead of numeric values.

**Solution:**
```python
def get_height():
    response = tello.send_read_command('height?')
    # Response format: "80dm"
    match = re.search(r'\d+', response)
    if match:
        height_dm = int(match.group())
        height_cm = height_dm * 10  # Convert decimeters to centimeters
        return [types.TextContent(type="text", text=f"Height: {height_cm} cm")]
    else:
        return [types.TextContent(type="text", text=f"Raw response: {response}")]
```

**Benefits:**
- Handles inconsistent sensor response formats
- Provides fallback to raw response if parsing fails
- Performs unit conversion for user-friendly output

**Sources:** server_tello.py:710-772

---

### 8. stdio Transport for MCP Communication

**Description:** Use standard input/output streams for JSON-RPC communication with Claude Desktop.

**Implementation:**
```python
async def main():
    """Main entry point"""
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
```

**Benefits:**
- Simple process isolation (Claude Desktop spawns server as subprocess)
- No network configuration required
- Standard JSON-RPC protocol over stdio

**Important:** All logging must be suppressed or sent to stderr to avoid corrupting stdio protocol.

**Sources:** server_home_assistant.py:910-929, server_tello.py:871-890

---

## Development Environment Setup

### Prerequisites

- Python 3.x (tested with 3.8+)
- pip package manager
- Virtual environment support (`python -m venv`)
- Home Assistant instance (for Home Assistant server)
- DJI Tello drone (for Tello server)
- Claude Desktop application

### Step-by-Step Setup

#### 1. Clone Repository

```bash
git clone https://github.com/AlexVOiceover/MCP_Ideas.git
cd MCP_Ideas
```

#### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Installed packages:**
- `mcp` - Model Context Protocol SDK
- `djitellopy` - DJI Tello drone SDK
- `requests` - HTTP client for Home Assistant API

**Optional (installed automatically if needed):**
- `opencv-python` - For Windows video streaming fix
- `python-dotenv` - For .env file loading

#### 4. Configure Environment Variables

Create `.env` file in project root:

```bash
# Home Assistant Configuration
HA_URL=http://localhost:8123
HA_TOKEN=your_long_lived_access_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id

# Optional: Future expansions
# WEATHER_STATION_URL=http://192.168.1.100
```

**Getting Home Assistant Token:**
1. Log into Home Assistant web interface
2. Navigate to Profile → Security
3. Scroll to "Long-Lived Access Tokens"
4. Click "Create Token"
5. Copy token to `.env` file

#### 5. Configure Claude Desktop

Create or edit `claude_desktop_config.json` (location varies by OS):

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Linux:** `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "homeassistant": {
      "command": "/absolute/path/to/MCP_Ideas/.venv/Scripts/python.exe",
      "args": ["/absolute/path/to/MCP_Ideas/server_home_assistant.py"]
    },
    "tello": {
      "command": "/absolute/path/to/MCP_Ideas/.venv/Scripts/python.exe",
      "args": ["/absolute/path/to/MCP_Ideas/server_tello.py"]
    }
  }
}
```

**Important:** Use absolute paths, not relative paths.

#### 6. Test with MCP Inspector (Optional but Recommended)

```bash
# Test Home Assistant server
npx @modelcontextprotocol/inspector .venv/Scripts/python.exe server_home_assistant.py

# Test Tello server
npx @modelcontextprotocol/inspector .venv/Scripts/python.exe server_tello.py
```

Inspector opens at http://localhost:5173 and allows testing individual tools.

#### 7. Restart Claude Desktop

After configuration, restart Claude Desktop to load the MCP servers.

### Platform-Specific Notes

#### Windows

- Use backslashes in paths: `C:\Users\YourName\...\MCP_Ideas`
- For Tello video streaming, firewall rule may be needed:
  ```powershell
  # Run PowerShell as Administrator
  New-NetFirewallRule -DisplayName "Tello Video UDP 11111" -Direction Inbound -Protocol UDP -LocalPort 11111 -Action Allow
  ```

#### macOS/Linux

- Use forward slashes in paths: `/home/user/.../MCP_Ideas`
- Python executable: `.venv/bin/python`
- Tello video streaming should work without additional configuration

#### WSL (Windows Subsystem for Linux)

- Camera features may fail due to missing libGL graphics libraries
- Other drone features (flight, sensors) work normally
- Consider using native Windows Python for full functionality

### Troubleshooting

#### Server Not Connecting
- Verify virtual environment is activated
- Check all paths in `claude_desktop_config.json` are absolute
- Ensure `.env` file is in the same directory as server scripts
- Restart Claude Desktop after configuration changes

#### Home Assistant Connection Issues
- Verify Home Assistant is running: visit `HA_URL` in browser
- Check token is valid and not expired
- Ensure network connectivity between Claude Code environment and Home Assistant

#### Tello Drone Issues
- Connect to Tello's WiFi network (TELLO-XXXXXX)
- Power on drone before testing
- For video issues on Windows, see README.md troubleshooting section

**Sources:** README.md:30-260

---

## Conclusion

This technical overview provides a comprehensive guide to the MCP Ideas codebase architecture. The project demonstrates clean implementation of the Model Context Protocol with practical hardware integrations. Key architectural highlights include:

- **Modular Design:** Two independent servers with identical structural patterns
- **Cross-Platform Compatibility:** Platform-specific fixes for Windows UDP limitations
- **Robust Error Handling:** Graceful degradation and user-friendly error messages
- **Type Safety:** JSON Schema validation for all tool inputs
- **Extensibility:** Easy to add new tools or integrate additional devices

For contributing to this project, follow the established patterns:
1. Add tool definitions to `@server.list_tools()`
2. Implement handlers in `@server.call_tool()`
3. Use appropriate response types (`TextContent` or `ImageContent`)
4. Include comprehensive error handling and validation
5. Update README.md with usage examples

---

**Document Version:** 1.0
**Last Updated:** 2025-12-08
**Repository:** [AlexVOiceover/MCP_Ideas](https://github.com/AlexVOiceover/MCP_Ideas)
