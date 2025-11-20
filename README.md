# MCP Ideas - Model Context Protocol Servers

Collection of MCP servers for integrating Claude with hardware devices and home automation.

## Available MCP Servers

### 1. Home Assistant Server (`server_home_assistant.py`)
Control your smart home devices through Claude with full Home Assistant integration.

**Features:**
- **Lights**: Control Philips Hue bulbs and other lights (on/off, brightness, RGB color)
- **Climate**: Read temperatures, control thermostats
- **Locks**: Lock/unlock smart locks
- **Cameras**: View snapshots, send to Telegram
- **Switches**: Control smart plugs (Tapo, etc.)
- **Covers**: Open/close garage doors, blinds
- **Sensors**: Read all sensor data (motion, air quality, etc.)
- **Media Players**: Text-to-speech announcements
- **Telegram**: Send messages and camera snapshots

### 2. Tello Drone Server (`server_tello.py`)
Fly and control DJI Tello drones through Claude commands.

**Features:**
- Flight controls (takeoff, land, move, rotate, flip)
- Camera snapshot capture
- Battery and sensor monitoring
- Video streaming (Windows compatible with OpenCV)

## Quick Setup

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file with your credentials:

```env
# Home Assistant Configuration
HA_URL=http://localhost:8123
HA_TOKEN=your_long_lived_access_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id

# Future: Weather Station (optional)
# WEATHER_STATION_URL=http://192.168.1.100
```

### 3. Configure Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "homeassistant": {
      "command": "C:\\Users\\YourName\\Documents\\FAC\\MCP_Ideas\\.venv\\Scripts\\python.exe",
      "args": ["server_home_assistant.py"]
    },
    "tello": {
      "command": "C:\\Users\\YourName\\Documents\\FAC\\MCP_Ideas\\.venv\\Scripts\\python.exe",
      "args": ["server_tello.py"]
    }
  }
}
```

### 4. Restart Claude Desktop

After configuration, restart Claude Desktop to load the MCP servers.

## Test with MCP Inspector

Launch Inspector for local testing:

```bash
# Windows - Test Home Assistant Server
npx @modelcontextprotocol/inspector .venv\Scripts\python.exe server_home_assistant.py

# Windows - Test Tello Server
npx @modelcontextprotocol/inspector .venv\Scripts\python.exe server_tello.py
```

Inspector opens at [http://localhost:5173](http://localhost:5173)

**Inspector stuck?**
```bash
# Windows
Get-Process | Where-Object { $_.Path -like "*@modelcontextprotocol*" } | Stop-Process
```

## Usage Examples

### Home Assistant Examples

**Control Lights:**
```
"Turn on the living room light"
"Set the Hue bulb to 50% brightness"
"Change the bedroom light to blue" (RGB: 0, 0, 255)
"Turn off all lights in the kitchen"
```

**Climate Control:**
```
"What's the current temperature?"
"Set the thermostat to 22 degrees"
"Show me all climate device status"
```

**Security & Monitoring:**
```
"Lock the front door"
"Show me the front door camera"
"Send a camera snapshot to Telegram"
"What's the status of all locks?"
```

**Smart Home Automation:**
```
"Turn on the Tapo plug"
"Open the garage door"
"Read all sensor values"
"Make an announcement on the speaker: 'Dinner is ready'"
```

### Tello Drone Examples

**Basic Flight:**
```
"Take off"
"Move forward 50 cm"
"Rotate clockwise 90 degrees"
"Land"
```

**Camera & Sensors:**
```
"Show me what the drone sees"
"What's the battery level?"
"Get current height"
"Read all sensor data"
```

**Advanced Maneuvers:**
```
"Do a flip forward"
"Fly in a square pattern"
"Return to takeoff position"
```

## Project Structure

```
MCP_Ideas/
├── server_home_assistant.py    # Home Assistant MCP server
├── server_tello.py              # Tello drone MCP server
├── requirements.txt             # Python dependencies
├── .env                         # Environment variables (create this)
├── claude_desktop_config.json   # Claude Desktop configuration
├── test_udp_receive.py         # Tello UDP connection test
├── add_firewall_rule.ps1       # Windows firewall setup for Tello
└── README.md                    # This file
```

## Troubleshooting

### Home Assistant Connection Issues

**Server not connecting:**
- Verify Home Assistant is running and accessible
- Check `HA_URL` and `HA_TOKEN` in `.env` file
- Ensure long-lived access token is valid
- Restart Claude Desktop after configuration changes

**Devices not responding:**
- Use `get_lights`, `get_switches`, etc. to find correct entity IDs
- Check device is online in Home Assistant
- Verify entity ID matches exactly (case-sensitive)

### Tello Drone - Windows Video Streaming

**The Solution:**

The Tello MCP server now uses **OpenCV VideoCapture instead of PyAV** on Windows, which properly handles UDP video streams.

PyAV's `av.open()` throws Error 10014 on Windows with UDP URLs, but OpenCV works perfectly!

### What Was Done

1. **Test Script Confirmed**: Raw UDP sockets work and receive Tello video data
2. **Root Cause Found**: PyAV's FFmpeg wrapper can't open UDP streams on Windows
3. **Fix Applied**: Automatic patch uses OpenCV VideoCapture for Windows
4. **Firewall Rule**: Optional but recommended (run `add_firewall_rule.ps1`)

### Testing Your Setup

Run the UDP test to verify your network:
```bash
.venv\Scripts\python.exe test_udp_receive.py
```

If this shows `[SUCCESS] RECEIVED DATA`, your setup is good!

### Firewall Rule (Optional but Recommended)

While the OpenCV fix should work, adding a firewall rule is still recommended:

1. Open PowerShell as Administrator
2. Navigate to project directory:
   ```powershell
   cd C:\Users\Alexander\Documents\FAC\MCP_Ideas
   ```
3. Run the firewall rule script:
   ```powershell
   .\add_firewall_rule.ps1
   ```

### How It Works Now

- **Windows**: Automatically uses OpenCV VideoCapture (UDP compatible)
- **Linux/Mac**: Uses PyAV as normal
- **Both**: 30 retry attempts to grab first frame (handles initialization delay)

### If Video Still Doesn't Work

Try these additional steps:

**Check your WiFi connection:**
- Make sure you're connected to the Tello's WiFi network (TELLO-XXXXXX)
- The drone must be powered on

**Disable VPN/Security Software:**
- Some VPN or security software may block local UDP traffic
- Temporarily disable to test

**Alternative Solutions:**

1. **Use WSL2** (if firewall fix doesn't work):
   ```bash
   # In WSL2
   python server_tello.py
   ```

2. **Fly without camera** (all commands work):
   - takeoff, land, move, rotate, flip, get_battery, etc.
   - Camera is optional for drone control