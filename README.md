# Satellite MCP Server

A comprehensive Model Context Protocol (MCP) server for satellite orbital mechanics calculations with natural language processing capabilities.

## ✨ Key Features

- **🛰️ Satellite Access Window Calculations** - Calculate when satellites are visible from ground locations
- **🌍 World Cities Database** - Built-in database of 200+ cities worldwide for easy location lookup
- **🗣️ Natural Language Processing** - Parse orbital parameters from text like "satellite at 700km in SSO over London"
- **📡 TLE Generation** - Generate Two-Line Elements from orbital descriptions
- **🌅 Lighting Analysis** - Ground and satellite lighting conditions (civil, nautical, astronomical twilight)
- **📊 Bulk Processing** - Process multiple satellites and locations from CSV data
- **🚀 6 Orbit Types** - Support for LEO, MEO, GEO, SSO, Molniya, and Polar orbits

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd mcp-orbit

# Build the Docker image
make docker-build

# Run the MCP server
make docker-run
```

### Local Installation

```bash
# Install dependencies
make install

# Run the MCP server
make run
```

## 🔌 Connecting to the MCP Server

The server communicates via JSON-RPC 2.0 over stdio. Here are the connection methods:

### Claude Desktop Integration

Add to your Claude Desktop MCP configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "satellite-mcp-server": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "satellite-mcp-server:latest"]
    }
  }
}
```

### Direct Docker Connection

```bash
# Interactive mode
docker run -it --rm satellite-mcp-server:latest

# Pipe commands
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | \
  docker run --rm -i satellite-mcp-server:latest
```

### Local Python Connection

```bash
# If running locally without Docker
python -m src.mcp_server
```

## 💬 Example Usage in LLMs

### Example 1: Basic Satellite Pass Prediction

**User Prompt:**
> "When will the ISS be visible from London tomorrow?"

**MCP Tool Call:**
```json
{
  "tool": "calculate_access_windows_by_city",
  "arguments": {
    "city_name": "London",
    "tle_line1": "1 25544U 98067A   24001.50000000  .00001234  00000-0  12345-4 0  9999",
    "tle_line2": "2 25544  51.6400 123.4567 0001234  12.3456 347.6543 15.49011999123456",
    "start_time": "2024-01-02T00:00:00Z",
    "end_time": "2024-01-03T00:00:00Z"
  }
}
```

**Response:**
The ISS will be visible from London 4 times tomorrow, with the best pass at 19:45 UTC reaching 78° elevation in the southwest sky during civil twilight.

### Example 2: Natural Language Orbital Design

**User Prompt:**
> "Create a sun-synchronous satellite at 700km altitude and show me when it passes over Tokyo."

**MCP Tool Calls:**
1. Parse orbital elements:
```json
{
  "tool": "parse_orbital_elements",
  "arguments": {
    "orbital_text": "sun-synchronous satellite at 700km altitude"
  }
}
```

2. Calculate access windows:
```json
{
  "tool": "calculate_access_windows_from_orbital_elements_by_city",
  "arguments": {
    "orbital_text": "sun-synchronous satellite at 700km altitude",
    "city_name": "Tokyo",
    "start_time": "2024-01-01T00:00:00Z",
    "end_time": "2024-01-02T00:00:00Z"
  }
}
```

**Response:**
Generated SSO satellite (98.16° inclination, 98.6 min period) with 14 passes over Tokyo in 24 hours, including 6 daylight passes and 8 during various twilight conditions.

### Example 3: Bulk Satellite Analysis

**User Prompt:**
> "I have a CSV file with ground stations and want to analyze coverage for multiple satellites."

**MCP Tool Call:**
```json
{
  "tool": "calculate_bulk_access_windows",
  "arguments": {
    "locations_csv": "name,latitude,longitude,altitude\nMIT,42.3601,-71.0589,43\nCaltechm,34.1377,-118.1253,237",
    "satellites_csv": "name,tle_line1,tle_line2\nISS,1 25544U...,2 25544...\nHubble,1 20580U...,2 20580...",
    "start_time": "2024-01-01T00:00:00Z",
    "end_time": "2024-01-02T00:00:00Z"
  }
}
```

## 🛠️ Available Tools

1. **`calculate_access_windows`** - Basic satellite visibility calculations
2. **`calculate_access_windows_by_city`** - City-based satellite passes
3. **`calculate_bulk_access_windows`** - Multi-satellite/location analysis
4. **`parse_orbital_elements`** - Natural language orbital parameter parsing
5. **`calculate_access_windows_from_orbital_elements`** - Access windows from orbital text
6. **`calculate_access_windows_from_orbital_elements_by_city`** - Combined orbital elements + city lookup
7. **`search_cities`** - Find cities in the world database
8. **`validate_tle`** - Validate Two-Line Element data
9. **`get_orbit_types`** - Available orbit type definitions

## 🗂️ Project Structure

```
/
├── src/
│   ├── mcp_server.py          # MCP server implementation
│   ├── satellite_calc.py      # Core orbital mechanics calculations
│   └── world_cities.py        # World cities database
├── docs/                      # Documentation
├── Dockerfile                 # Container definition
├── docker-compose.yml         # Multi-container setup
└── Makefile                   # Build automation
```

## 📚 Dependencies

- **Skyfield** - Satellite position calculations
- **NumPy** - Numerical computations  
- **MCP** - Model Context Protocol implementation
- **Python 3.8+** - Runtime environment

## 🤝 Contributing

This is a specialized MCP server for satellite orbital mechanics. For issues or enhancements, please check the documentation in the `docs/` directory.

## 📄 License

[Add your license information here]