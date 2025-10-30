## Test with MCP Inspector

Launch Inspector for local testing:

```bash
npx @modelcontextprotocol/inspector python server.py
```

Inspector opens at [http://localhost:5173](http://localhost:5173)

## Configure for Global Use

Install for use across all projects with Claude Code CLI:

```bash
# Install pipx and fastmcp
brew install pipx  # macOS
pipx install fastmcp

# Add to Claude Code (replace with your actual path)
claude mcp add mcp_server_name --scope user ~/.local/bin/fastmcp run /path/to/your/MCP_workshop/server.py

# Verify connection
claude mcp list
```

**Inspector stuck?**
```bash
# macOS/Linux
pkill -f "@modelcontextprotocol/inspector"

# Windows
Get-Process | Where-Object { $_.Path -like "*@modelcontextprotocol*" } | Stop-Process
```

**MCP server not connecting?**
- Ensure `--scope user` flag is used for global access
- Check that fastmcp is installed via pipx
- Verify the server path in the configuration


## Download image and run HomeAssistant container on port 8123

docker stop homeassistant
docker rm homeassistant

docker run -d \
  --name homeassistant \
  --restart=unless-stopped \
  -e TZ=Europe/London \
  -v homeassistant_config:/config \
  -p 8123:8123 \
  ghcr.io/home-assistant/home-assistant:stable


# Create a long-lived access token on Home Assistant