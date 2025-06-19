# Satellite MCP Server

A complete Model Context Protocol (MCP) server for satellite orbital mechanics calculations. This server exposes satellite access window calculations as AI-assistant tools, enabling precise orbital analysis and event streaming for ground stations.

## 🛰️ Overview

The Satellite MCP Server provides three main capabilities:

1. **Enhanced Access Window Calculations** - Determine when satellites are visible with comprehensive lighting conditions (all twilight types) for both ground and satellite
2. **Bulk Calculations** - Process multiple satellites and ground locations from CSV data with flexible column naming
3. **TLE Validation** - Validate and parse Two-Line Element orbital data with detailed orbital parameters

Built with Python 3.11+, Skyfield orbital mechanics library, and full Docker containerization for production deployment.

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose (optional)
- Git

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd satellite-mcp-server

# Install dependencies
make install-dev

# Run tests to verify installation
make test

# Start the MCP server
make run
```

### Docker Quick Start

```bash
# Build and run with Docker
make docker-build
make docker-run

# Or use docker-compose for full stack
docker-compose up -d
```

## 📊 Features

### Core Calculations

- **Precise Orbital Propagation** using Skyfield SGP4/SDP4 models
- **Comprehensive Lighting Analysis** - Civil, nautical, and astronomical twilight conditions
- **Ground Station Lighting** - Sun elevation and twilight status at target locations
- **Satellite Lighting** - Eclipse/sunlight conditions with altitude-based approximations
- **Topocentric Coordinate Transformations** (TEME to local horizon)
- **Configurable Time Stepping** for accuracy vs performance tuning

### Bulk Processing

- **CSV Data Input** with flexible column naming support
- **Multiple Satellite Support** - Process entire constellations
- **Multiple Ground Stations** - Simultaneous calculations across networks
- **Resilient Parsing** - Handles variations in CSV format and missing data
- **Comprehensive Results** - Organized by satellite-location combinations

### MCP Integration

- **Three Specialized Tools** - Access windows, bulk calculations, and TLE validation
- **JSON-RPC 2.0 Protocol** for AI assistant communication
- **Schema Validation** with detailed error messages
- **Async Execution** for long-running calculations
- **Enhanced Data Structures** with lighting information

### Production Features

- **Docker Containerization** with multi-stage builds
- **Simplified Deployment** - Docker files in project root
- **Health Checks** and proper signal handling
- **Logging and Monitoring** with configurable levels
- **Resource Management** and cleanup

## 🛠️ Tools

### calculate_access_windows

Calculates satellite access windows over a ground station location with comprehensive lighting conditions.

**Input Parameters:**
- `latitude` (float): Ground station latitude (-90 to 90 degrees)
- `longitude` (float): Ground station longitude (-180 to 180 degrees)
- `tle_line1` (string): TLE Line 1 (69 characters)
- `tle_line2` (string): TLE Line 2 (69 characters)
- `start_time` (string): Start time in ISO 8601 format (UTC)
- `end_time` (string): End time in ISO 8601 format (UTC)
- `elevation_threshold` (float, optional): Minimum elevation angle (default: 10°)
- `time_step_seconds` (int, optional): Calculation time step (default: 30s)

**Output:**
```json
{
  "summary": {
    "total_windows": 5,
    "total_duration_seconds": 2847.5,
    "total_duration_minutes": 47.46,
    "max_elevation_deg": 78.3,
    "calculation_parameters": { ... }
  },
  "access_windows": [
    {
      "aos_time": "2024-01-01T06:12:30",
      "los_time": "2024-01-01T06:21:45",
      "culmination_time": "2024-01-01T06:17:08",
      "duration_seconds": 555.0,
      "duration_minutes": 9.25,
      "max_elevation_deg": 78.3,
      "aos_azimuth_deg": 291.7,
      "los_azimuth_deg": 76.2,
      "culmination_azimuth_deg": 2.1,
      "ground_lighting": {
        "condition": "daylight",
        "sun_elevation_deg": 45.2,
        "civil_twilight": true,
        "nautical_twilight": true,
        "astronomical_twilight": true,
        "is_daylight": true,
        "is_night": false
      },
      "satellite_lighting": {
        "condition": "sunlight",
        "in_eclipse": false,
        "in_sunlight": true,
        "satellite_altitude_km": 420.5
      }
    }
  ]
}
```

### calculate_bulk_access_windows

Calculates access windows for multiple satellites and ground locations from CSV data.

**Input Parameters:**
- `locations_csv` (string): CSV content with ground locations (columns: name, latitude, longitude, altitude)
- `satellites_csv` (string): CSV content with satellite TLE data (columns: name, tle_line1, tle_line2)
- `start_time` (string): Start time in ISO 8601 format (UTC)
- `end_time` (string): End time in ISO 8601 format (UTC)
- `elevation_threshold` (float, optional): Minimum elevation angle (default: 10°)
- `time_step_seconds` (int, optional): Calculation time step (default: 30s)

**CSV Format Examples:**
```csv
# Locations CSV (flexible column naming)
name,latitude,longitude,altitude
MIT,42.3601,-71.0942,40
NASA Goddard,38.9917,-76.8400,76

# Satellites CSV  
name,tle_line1,tle_line2
ISS,1 25544U 98067A...,2 25544  51.6400...
```

**Output:**
```json
{
  "summary": {
    "total_locations": 2,
    "total_satellites": 1,
    "total_combinations": 2,
    "total_access_windows": 8
  },
  "results": [
    {
      "satellite": {"name": "ISS", ...},
      "location": {"name": "MIT", ...},
      "access_windows": [...],
      "summary": {"total_windows": 4}
    }
  ]
}
```

### validate_tle

Validates Two-Line Element data and extracts orbital parameters.

**Input Parameters:**
- `tle_line1` (string): TLE Line 1
- `tle_line2` (string): TLE Line 2

**Output:**
```json
{
  "is_valid": true,
  "errors": [],
  "orbital_parameters": {
    "satellite_number": 25544,
    "classification": "U",
    "international_designator": "98067A",
    "epoch": "2024-01-01T02:57:46.963200",
    "mean_motion_rev_per_day": 15.489,
    "eccentricity": 0.0001234,
    "inclination_deg": 51.64,
    "orbital_period_minutes": 93.05
  }
}
```

## 🏗️ Architecture

### Project Structure

```
satellite-mcp-server/
├── src/
│   ├── __init__.py              # Package initialization
│   ├── mcp_server.py           # MCP server implementation
│   └── satellite_calc.py       # Core calculations
├── tests/
│   ├── test_mcp_server.py      # MCP server tests
│   ├── test_calculations.py    # Calculation tests
│   └── sample_data.py          # Test data
├── docker/
│   ├── Dockerfile              # Container definition
│   └── docker-compose.yml      # Multi-service setup
├── docs/
│   ├── README.md               # This file
│   ├── API.md                  # Detailed API documentation
│   └── examples.md             # Usage examples
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development dependencies
├── Makefile                    # Build automation
└── .gitignore                  # Git ignore patterns
```

### Core Components

1. **SatelliteCalculator** - Handles orbital mechanics using Skyfield
2. **SatelliteMCPServer** - MCP protocol implementation
3. **Docker Configuration** - Production containerization
4. **Test Suite** - Comprehensive validation

### Dependencies

**Production:**
- `mcp>=1.0.0` - Model Context Protocol framework
- `skyfield>=1.48` - Orbital mechanics calculations
- `numpy>=1.24.0` - Numerical computations
- `python-dateutil>=2.8.2` - Date/time parsing

**Development:**
- `pytest>=7.0.0` - Testing framework
- `pytest-asyncio>=0.21.0` - Async test support
- `black>=23.0.0` - Code formatting
- `flake8>=6.0.0` - Linting
- `mypy>=1.0.0` - Type checking

## 🧪 Testing

The project includes comprehensive test coverage:

```bash
# Run all tests
make test

# Run with coverage report
make test-coverage

# Run specific test categories
make test-unit        # Calculation tests only
make test-integration # MCP server tests only

# Run tests in watch mode during development
make test-watch
```

### Test Data

Sample TLE data is provided for testing:

- **ISS (International Space Station)** - LEO reference orbit
- **NOAA-18** - Polar sun-synchronous orbit
- **Hubble Space Telescope** - Inclined LEO orbit

Ground station locations:
- MIT Lincoln Laboratory (42.36°N, 71.09°W)
- NASA Goddard (38.99°N, 76.84°W)
- ESA Darmstadt (49.87°N, 8.65°E)

## 🐳 Docker Deployment

### Single Container

```bash
# Build image
make docker-build

# Run container
make docker-run

# Background execution
make docker-run-background
```

### Full Stack with Docker Compose

```bash
docker-compose up -d
```

The docker-compose stack includes the MCP server ready for integration with AI assistants.

### Configuration

Environment variables:
- `MCP_SERVER_LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `TZ` - Timezone (default: UTC)

## 🔧 Development

### Setup Development Environment

```bash
# Create virtual environment and install dependencies
make venv-install

# Activate virtual environment
source venv/bin/activate

# Run development server with debug logging
make run-dev
```

### Code Quality

```bash
# Run all quality checks
make quality

# Individual checks
make lint          # Flake8 linting
make format        # Black code formatting
make type-check    # MyPy type checking
```

### Build Automation

The Makefile provides comprehensive build automation:

```bash
make help          # Show all available targets
make build         # Full build with quality checks and tests
make ci            # Continuous integration pipeline
make cd            # Continuous deployment pipeline
make health-check  # Verify system dependencies
```

## 📈 Performance

### Benchmarks

Typical performance on modern hardware:

- **Single Day Calculation**: ~0.5-2 seconds for ISS over ground station
- **Week-long Analysis**: ~5-15 seconds for detailed calculations
- **Memory Usage**: ~50-100MB during calculation
- **Accuracy**: Sub-second timing precision with 30s time steps

### Optimization

- **Time Step Tuning**: Balance accuracy vs performance (10s-60s range)
- **Batch Processing**: Multiple ground stations simultaneously
- **Caching**: Skyfield automatically caches ephemeris data

## 🔒 Security

- **Non-root Execution** in Docker containers
- **Read-only Filesystem** for production deployment
- **Input Validation** with schema enforcement
- **No Secrets in Logs** or error messages
- **Resource Limits** to prevent DoS

## 📋 Requirements

### System Requirements

- **CPU**: 1+ cores, 2+ recommended for concurrent calculations
- **RAM**: 512MB minimum, 1GB+ recommended
- **Storage**: 100MB for application, additional for ephemeris data cache
- **Network**: Internet access for initial Skyfield data download

### Accuracy Requirements

- **TLE Age**: Best accuracy with TLE data <7 days old
- **Propagation**: SGP4/SDP4 models valid for ~weeks from epoch
- **Coordinate Systems**: WGS84 datum for ground station coordinates
- **Time Reference**: UTC for all timestamps

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes and add tests
4. Run quality checks (`make quality`)
5. Run test suite (`make test`)
6. Commit changes (`git commit -m 'Add amazing feature'`)
7. Push to branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues, questions, or contributions:

1. Check existing [GitHub Issues](repository-url/issues)
2. Create a new issue with detailed description
3. Include system information and error logs
4. Provide sample TLE data and coordinates if relevant

## 🔗 References

- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [Skyfield Orbital Mechanics](https://rhodesmill.org/skyfield/)
- [Two-Line Element Format](https://en.wikipedia.org/wiki/Two-line_element_set)
- [SGP4/SDP4 Orbital Models](https://en.wikipedia.org/wiki/Simplified_perturbations_models)