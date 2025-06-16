# Satellite MCP Server Examples

Practical examples demonstrating how to use the Satellite MCP Server for various orbital mechanics calculations.

## Table of Contents

- [Basic Usage](#basic-usage)
- [Common Scenarios](#common-scenarios)
- [Advanced Examples](#advanced-examples)
- [Integration Patterns](#integration-patterns)
- [Troubleshooting](#troubleshooting)

## Basic Usage

### Starting the Server

```bash
# Install dependencies
pip install -r requirements.txt

# Start MCP server
python -m src.mcp_server

# Or using Make
make run
```

### First Calculation

Calculate when the International Space Station (ISS) is visible from MIT:

```python
# Example TLE data for ISS
iss_tle_line1 = "1 25544U 98067A   24001.12345678  .00001234  00000-0  12345-4 0  9999"
iss_tle_line2 = "2 25544  51.6400 123.4567 0001234  12.3456 347.6543 15.48919999123456"

# MIT coordinates
mit_lat = 42.3601
mit_lon = -71.0942

# Time window (24 hours)
start_time = "2024-01-01T00:00:00Z"
end_time = "2024-01-01T23:59:59Z"
```

MCP Tool Call:
```json
{
  "method": "tools/call",
  "params": {
    "name": "calculate_access_windows",
    "arguments": {
      "latitude": 42.3601,
      "longitude": -71.0942,
      "tle_line1": "1 25544U 98067A   24001.12345678  .00001234  00000-0  12345-4 0  9999",
      "tle_line2": "2 25544  51.6400 123.4567 0001234  12.3456 347.6543 15.48919999123456",
      "start_time": "2024-01-01T00:00:00Z",
      "end_time": "2024-01-01T23:59:59Z"
    }
  }
}
```

## Common Scenarios

### 1. Ground Station Pass Prediction

**Scenario**: Predict all ISS passes over NASA Goddard for the next week.

```json
{
  "method": "tools/call",
  "params": {
    "name": "calculate_access_windows",
    "arguments": {
      "latitude": 38.9917,
      "longitude": -76.8400,
      "tle_line1": "1 25544U 98067A   24001.12345678  .00001234  00000-0  12345-4 0  9999",
      "tle_line2": "2 25544  51.6400 123.4567 0001234  12.3456 347.6543 15.48919999123456",
      "start_time": "2024-01-01T00:00:00Z",
      "end_time": "2024-01-07T23:59:59Z",
      "elevation_threshold": 10.0,
      "time_step_seconds": 30
    }
  }
}
```

**Expected Output**:
```json
{
  "summary": {
    "total_windows": 28,
    "total_duration_seconds": 8420.5,
    "total_duration_minutes": 140.34,
    "max_elevation_deg": 82.1
  },
  "access_windows": [
    {
      "aos_time": "2024-01-01T05:42:15Z",
      "los_time": "2024-01-01T05:51:30Z",
      "culmination_time": "2024-01-01T05:46:52Z",
      "duration_minutes": 9.25,
      "max_elevation_deg": 45.8
    }
  ]
}
```

### 2. High-Precision Timing

**Scenario**: Calculate precise timing for optical observations (high elevation only).

```json
{
  "method": "tools/call",
  "params": {
    "name": "calculate_access_windows",
    "arguments": {
      "latitude": 49.8728,
      "longitude": 8.6512,
      "tle_line1": "1 20580U 90037B   24001.75000000  .00000678  00000-0  23456-4 0  9992",
      "tle_line2": "2 20580  28.4700  50.0000 0005678  30.0000 330.0000 15.09876543210987",
      "start_time": "2024-01-01T18:00:00Z",
      "end_time": "2024-01-02T06:00:00Z",
      "elevation_threshold": 45.0,
      "time_step_seconds": 10
    }
  }
}
```

### 3. Event Stream Generation

**Scenario**: Generate events for InfluxDB time-series database.

```json
{
  "method": "tools/call",
  "params": {
    "name": "calculate_access_events",
    "arguments": {
      "latitude": 42.3601,
      "longitude": -71.0942,
      "tle_line1": "1 25544U 98067A   24001.12345678  .00001234  00000-0  12345-4 0  9999",
      "tle_line2": "2 25544  51.6400 123.4567 0001234  12.3456 347.6543 15.48919999123456",
      "start_time": "2024-01-01T00:00:00Z",
      "end_time": "2024-01-01T23:59:59Z",
      "satellite_id": "ISS_ZARYA",
      "location_id": "MIT_LINCOLN_LAB",
      "location_type": "research_facility"
    }
  }
}
```

**InfluxDB Line Protocol Output**:
```
satellite_access,satellite_id=ISS_ZARYA,location_id=MIT_LINCOLN_LAB,location_type=research_facility,event_type=aos elevation_deg=10.0,azimuth_deg=291.72 1704067950000000000
satellite_access,satellite_id=ISS_ZARYA,location_id=MIT_LINCOLN_LAB,location_type=research_facility,event_type=culmination elevation_deg=78.34,azimuth_deg=2.15 1704068228000000000
satellite_access,satellite_id=ISS_ZARYA,location_id=MIT_LINCOLN_LAB,location_type=research_facility,event_type=los elevation_deg=10.0,azimuth_deg=76.18 1704068505000000000
```

### 4. TLE Validation and Analysis

**Scenario**: Validate TLE data before calculations.

```json
{
  "method": "tools/call",
  "params": {
    "name": "validate_tle",
    "arguments": {
      "tle_line1": "1 25544U 98067A   24001.12345678  .00001234  00000-0  12345-4 0  9999",
      "tle_line2": "2 25544  51.6400 123.4567 0001234  12.3456 347.6543 15.48919999123456"
    }
  }
}
```

**Response Analysis**:
```json
{
  "is_valid": true,
  "errors": [],
  "orbital_parameters": {
    "satellite_number": 25544,
    "classification": "U",
    "international_designator": "98067A",
    "epoch": "2024-01-01T02:57:46.963200Z",
    "mean_motion_rev_per_day": 15.48919999,
    "eccentricity": 0.0001234,
    "inclination_deg": 51.64,
    "orbital_period_minutes": 93.05
  }
}
```

**Interpretation**:
- **Satellite 25544**: International Space Station
- **Inclination 51.64°**: ISS orbital inclination
- **Period 93.05 min**: ~15.5 orbits per day
- **Low eccentricity**: Nearly circular orbit

## Advanced Examples

### 1. Multi-Station Network Analysis

Calculate coverage for a network of ground stations:

```python
# Ground station network
stations = [
    {"name": "MIT", "lat": 42.3601, "lon": -71.0942, "id": "MIT_LL"},
    {"name": "Goddard", "lat": 38.9917, "lon": -76.8400, "id": "NASA_GSFC"},
    {"name": "Darmstadt", "lat": 49.8728, "lon": 8.6512, "id": "ESA_ESOC"}
]

# Calculate for each station (separate MCP calls)
for station in stations:
    # MCP call for each station
    pass
```

### 2. Polar Orbit Analysis

**Scenario**: Analyze NOAA-18 polar satellite coverage.

```json
{
  "method": "tools/call",
  "params": {
    "name": "calculate_access_windows",
    "arguments": {
      "latitude": 71.0,
      "longitude": -8.0,
      "tle_line1": "1 28654U 05018A   24001.50000000  .00000123  00000-0  45678-4 0  9995",
      "tle_line2": "2 28654  99.0500 100.0000 0012345  45.0000 315.0000 14.12345678987654",
      "start_time": "2024-01-01T00:00:00Z",
      "end_time": "2024-01-01T23:59:59Z",
      "elevation_threshold": 5.0
    }
  }
}
```

**Analysis Points**:
- Polar orbit (99.05° inclination) provides good high-latitude coverage
- Sun-synchronous orbit for consistent lighting conditions
- Lower elevation threshold (5°) captures longer passes

### 3. Geostationary Satellite Check

**Scenario**: Verify continuous visibility of geostationary satellite.

```json
{
  "method": "tools/call",
  "params": {
    "name": "calculate_access_windows",
    "arguments": {
      "latitude": 0.0,
      "longitude": 0.0,
      "tle_line1": "1 12345U 81049A   24001.00000000  .00000000  00000-0  00000-0 0  9999",
      "tle_line2": "2 12345   0.0000   0.0000 0000000   0.0000   0.0000  1.00273791123456",
      "start_time": "2024-01-01T00:00:00Z",
      "end_time": "2024-01-01T23:59:59Z",
      "elevation_threshold": 10.0
    }
  }
}
```

**Expected**: Single continuous access window for 24 hours.

### 4. Fine Time Resolution Tracking

**Scenario**: Precise tracking for antenna pointing.

```json
{
  "method": "tools/call",
  "params": {
    "name": "calculate_access_events",
    "arguments": {
      "latitude": 42.3601,
      "longitude": -71.0942,
      "tle_line1": "1 25544U 98067A   24001.12345678  .00001234  00000-0  12345-4 0  9999",
      "tle_line2": "2 25544  51.6400 123.4567 0001234  12.3456 347.6543 15.48919999123456",
      "start_time": "2024-01-01T06:10:00Z",
      "end_time": "2024-01-01T06:25:00Z",
      "satellite_id": "ISS",
      "location_id": "TRACKING_ANTENNA_1",
      "location_type": "antenna",
      "elevation_threshold": 10.0,
      "time_step_seconds": 5
    }
  }
}
```

**Use Case**: Generate precise pointing data for automated antenna systems.

## Integration Patterns

### 1. Batch Processing Pipeline

```python
# Pseudo-code for batch processing
def process_satellite_batch(satellites, stations, time_window):
    results = []
    
    for satellite in satellites:
        # Validate TLE first
        validation = mcp_call("validate_tle", {
            "tle_line1": satellite["line1"],
            "tle_line2": satellite["line2"]
        })
        
        if validation["is_valid"]:
            for station in stations:
                # Calculate access windows
                windows = mcp_call("calculate_access_windows", {
                    "latitude": station["lat"],
                    "longitude": station["lon"],
                    "tle_line1": satellite["line1"],
                    "tle_line2": satellite["line2"],
                    "start_time": time_window["start"],
                    "end_time": time_window["end"]
                })
                
                results.append({
                    "satellite": satellite["name"],
                    "station": station["name"],
                    "windows": windows
                })
    
    return results
```

### 2. Real-time Event Streaming

```python
# Pseudo-code for real-time streaming
def stream_satellite_events(satellite, station, duration_hours):
    start_time = datetime.utcnow()
    end_time = start_time + timedelta(hours=duration_hours)
    
    events = mcp_call("calculate_access_events", {
        "latitude": station["lat"],
        "longitude": station["lon"],
        "tle_line1": satellite["line1"],
        "tle_line2": satellite["line2"],
        "start_time": start_time.isoformat() + "Z",
        "end_time": end_time.isoformat() + "Z",
        "satellite_id": satellite["id"],
        "location_id": station["id"]
    })
    
    # Send to InfluxDB
    for event in events["influxdb_format"]:
        influxdb_client.write_points([event])
```

### 3. Web API Integration

```python
# Flask API endpoint example
@app.route('/api/satellite/access-windows', methods=['POST'])
def calculate_access_windows():
    data = request.json
    
    try:
        # Validate input
        validate_coordinates(data['latitude'], data['longitude'])
        validate_time_range(data['start_time'], data['end_time'])
        
        # MCP call
        result = mcp_call("calculate_access_windows", data)
        
        return jsonify(result)
    
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Calculation failed"}), 500
```

### 4. Grafana Dashboard Integration

**InfluxDB Query Examples**:

```sql
-- Current satellite visibility
SELECT last("elevation_deg") as "elevation"
FROM "satellite_access" 
WHERE ("event_type" != 'los' AND time >= now() - 1h)
GROUP BY "satellite_id", "location_id"

-- Daily pass statistics
SELECT count("elevation_deg") as "passes_per_day"
FROM "satellite_access"
WHERE ("event_type" = 'aos' AND time >= now() - 24h)
GROUP BY time(1d), "satellite_id", "location_id"

-- Maximum elevation trends
SELECT max("elevation_deg") as "max_elevation"
FROM "satellite_access"
WHERE ("event_type" = 'culmination')
GROUP BY time(1h), "satellite_id"
```

## Troubleshooting

### Common Issues

#### 1. TLE Data Problems

**Issue**: "Invalid TLE: Line 1 checksum validation failed"

**Solution**: 
```json
{
  "method": "tools/call",
  "params": {
    "name": "validate_tle",
    "arguments": {
      "tle_line1": "your_tle_line1_here",
      "tle_line2": "your_tle_line2_here"
    }
  }
}
```

Check the validation response for specific errors and correct the TLE data.

#### 2. No Access Windows Found

**Issue**: Empty access_windows array returned

**Possible Causes**:
- Elevation threshold too high
- Satellite not visible during time window
- Incorrect coordinates

**Debug Steps**:
```json
{
  "elevation_threshold": 0.0,
  "time_step_seconds": 30
}
```

Lower the elevation threshold to see if satellite is visible at all.

#### 3. Performance Issues

**Issue**: Calculations taking too long

**Optimization**:
```json
{
  "time_step_seconds": 60,
  "elevation_threshold": 10.0
}
```

- Increase time step for faster calculations
- Reduce time window duration
- Use appropriate elevation threshold

#### 4. Coordinate System Confusion

**Issue**: Results don't match expected values

**Verification**:
- Ensure latitude/longitude in decimal degrees
- Verify WGS84 datum usage
- Check sign conventions (N/S, E/W)

### Validation Scripts

```bash
# Test TLE validation
make validate

# Run performance benchmark
make benchmark

# Health check
make health-check

# Run example calculation
make example
```

### Debug Mode

```bash
# Run with debug logging
MCP_SERVER_LOG_LEVEL=DEBUG make run-dev
```

### Sample TLE Sources

- **NASA**: https://nasa-public-data.s3.amazonaws.com/iss-coords/current/ISS_OEM/ISS.OEM_J2K_EPH.txt
- **CelesTrak**: https://celestrak.com/NORAD/elements/
- **Space-Track**: https://www.space-track.org/ (registration required)

**Important**: Always use recent TLE data (< 7 days old) for accurate predictions.

## Performance Tips

1. **Batch Multiple Stations**: Calculate each ground station separately for parallel processing
2. **Cache TLE Validation**: Validate TLE once, reuse for multiple calculations
3. **Optimize Time Steps**: 30-60 seconds provides good accuracy/performance balance
4. **Limit Time Windows**: Longer periods increase calculation time exponentially
5. **Use Appropriate Elevation Thresholds**: Higher thresholds reduce calculation complexity