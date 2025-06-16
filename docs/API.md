# Satellite MCP Server API Documentation

Detailed documentation for the Model Context Protocol (MCP) tools provided by the Satellite MCP Server.

## Table of Contents

- [Overview](#overview)
- [Tool Specifications](#tool-specifications)
- [Input Validation](#input-validation)
- [Error Handling](#error-handling)
- [Response Formats](#response-formats)
- [Example Requests](#example-requests)

## Overview

The Satellite MCP Server exposes three main tools through the MCP protocol:

1. `calculate_access_windows` - Calculate satellite visibility windows
2. `calculate_access_events` - Generate detailed event streams
3. `validate_tle` - Validate and parse TLE orbital data

All tools use JSON-RPC 2.0 protocol over stdio for communication with AI assistants.

## Tool Specifications

### calculate_access_windows

Calculates when a satellite is visible above a minimum elevation angle from a ground station.

#### Input Schema

```json
{
  "type": "object",
  "properties": {
    "latitude": {
      "type": "number",
      "minimum": -90,
      "maximum": 90,
      "description": "Ground station latitude in decimal degrees (WGS84)"
    },
    "longitude": {
      "type": "number", 
      "minimum": -180,
      "maximum": 180,
      "description": "Ground station longitude in decimal degrees (WGS84)"
    },
    "tle_line1": {
      "type": "string",
      "pattern": "^1 ",
      "minLength": 69,
      "maxLength": 69,
      "description": "TLE Line 1 in standard NORAD format"
    },
    "tle_line2": {
      "type": "string",
      "pattern": "^2 ",
      "minLength": 69,
      "maxLength": 69,
      "description": "TLE Line 2 in standard NORAD format"
    },
    "start_time": {
      "type": "string",
      "format": "date-time",
      "description": "Start time in ISO 8601 format (UTC)"
    },
    "end_time": {
      "type": "string",
      "format": "date-time", 
      "description": "End time in ISO 8601 format (UTC)"
    },
    "elevation_threshold": {
      "type": "number",
      "minimum": 0,
      "maximum": 90,
      "default": 10.0,
      "description": "Minimum elevation angle in degrees"
    },
    "time_step_seconds": {
      "type": "integer",
      "minimum": 1,
      "maximum": 300,
      "default": 30,
      "description": "Time step for calculations in seconds"
    }
  },
  "required": ["latitude", "longitude", "tle_line1", "tle_line2", "start_time", "end_time"]
}
```

#### Response Format

```json
{
  "summary": {
    "total_windows": 5,
    "total_duration_seconds": 2847.5,
    "total_duration_minutes": 47.46,
    "max_elevation_deg": 78.34,
    "calculation_parameters": {
      "latitude": 42.3601,
      "longitude": -71.0942,
      "start_time": "2024-01-01T00:00:00+00:00",
      "end_time": "2024-01-01T23:59:59+00:00",
      "elevation_threshold": 10.0,
      "time_step_seconds": 30
    }
  },
  "access_windows": [
    {
      "aos_time": "2024-01-01T06:12:30+00:00",
      "los_time": "2024-01-01T06:21:45+00:00",
      "culmination_time": "2024-01-01T06:17:08+00:00",
      "duration_seconds": 555.0,
      "duration_minutes": 9.25,
      "max_elevation_deg": 78.34,
      "aos_azimuth_deg": 291.72,
      "los_azimuth_deg": 76.18,
      "culmination_azimuth_deg": 2.15
    }
  ]
}
```

### calculate_access_events

Generates detailed AOS, culmination, and LOS events with InfluxDB-compatible formatting.

#### Input Schema

```json
{
  "type": "object",
  "properties": {
    "latitude": {
      "type": "number",
      "minimum": -90,
      "maximum": 90,
      "description": "Ground station latitude in decimal degrees (WGS84)"
    },
    "longitude": {
      "type": "number",
      "minimum": -180,
      "maximum": 180,
      "description": "Ground station longitude in decimal degrees (WGS84)"
    },
    "tle_line1": {
      "type": "string",
      "pattern": "^1 ",
      "minLength": 69,
      "maxLength": 69,
      "description": "TLE Line 1 in standard NORAD format"
    },
    "tle_line2": {
      "type": "string",
      "pattern": "^2 ",
      "minLength": 69,
      "maxLength": 69,
      "description": "TLE Line 2 in standard NORAD format"
    },
    "start_time": {
      "type": "string",
      "format": "date-time",
      "description": "Start time in ISO 8601 format (UTC)"
    },
    "end_time": {
      "type": "string",
      "format": "date-time",
      "description": "End time in ISO 8601 format (UTC)"
    },
    "satellite_id": {
      "type": "string",
      "minLength": 1,
      "description": "Unique identifier for the satellite"
    },
    "location_id": {
      "type": "string",
      "minLength": 1,
      "description": "Unique identifier for the ground station"
    },
    "location_type": {
      "type": "string",
      "default": "ground_station",
      "description": "Type of location (e.g., ground_station, mobile_unit)"
    },
    "elevation_threshold": {
      "type": "number",
      "minimum": 0,
      "maximum": 90,
      "default": 10.0,
      "description": "Minimum elevation angle in degrees"
    },
    "time_step_seconds": {
      "type": "integer",
      "minimum": 1,
      "maximum": 300,
      "default": 30,
      "description": "Time step for calculations in seconds"
    }
  },
  "required": ["latitude", "longitude", "tle_line1", "tle_line2", 
               "start_time", "end_time", "satellite_id", "location_id"]
}
```

#### Response Format

```json
{
  "summary": {
    "total_events": 15,
    "aos_events": 5,
    "culmination_events": 5,
    "los_events": 5,
    "calculation_parameters": {
      "latitude": 42.3601,
      "longitude": -71.0942,
      "satellite_id": "25544",
      "location_id": "MIT_LL",
      "location_type": "ground_station",
      "start_time": "2024-01-01T00:00:00+00:00",
      "end_time": "2024-01-01T23:59:59+00:00",
      "elevation_threshold": 10.0,
      "time_step_seconds": 30
    }
  },
  "events": [
    {
      "timestamp": "2024-01-01T06:12:30+00:00",
      "event_type": "aos",
      "elevation_deg": 10.0,
      "azimuth_deg": 291.72,
      "satellite_id": "25544",
      "location_id": "MIT_LL",
      "location_type": "ground_station"
    },
    {
      "timestamp": "2024-01-01T06:17:08+00:00",
      "event_type": "culmination",
      "elevation_deg": 78.34,
      "azimuth_deg": 2.15,
      "satellite_id": "25544",
      "location_id": "MIT_LL",
      "location_type": "ground_station"
    },
    {
      "timestamp": "2024-01-01T06:21:45+00:00",
      "event_type": "los",
      "elevation_deg": 10.0,
      "azimuth_deg": 76.18,
      "satellite_id": "25544",
      "location_id": "MIT_LL",
      "location_type": "ground_station"
    }
  ],
  "influxdb_format": [
    {
      "measurement": "satellite_access",
      "tags": {
        "satellite_id": "25544",
        "location_id": "MIT_LL",
        "location_type": "ground_station",
        "event_type": "aos"
      },
      "fields": {
        "elevation_deg": 10.0,
        "azimuth_deg": 291.72
      },
      "time": "2024-01-01T06:12:30+00:00"
    }
  ]
}
```

#### Event Types

- **aos** (Acquisition of Signal) - Satellite rises above elevation threshold
- **culmination** - Satellite reaches maximum elevation during pass
- **los** (Loss of Signal) - Satellite drops below elevation threshold

### validate_tle

Validates Two-Line Element data format and extracts orbital parameters.

#### Input Schema

```json
{
  "type": "object",
  "properties": {
    "tle_line1": {
      "type": "string",
      "minLength": 69,
      "maxLength": 69,
      "description": "TLE Line 1 in standard NORAD format"
    },
    "tle_line2": {
      "type": "string",
      "minLength": 69,
      "maxLength": 69,
      "description": "TLE Line 2 in standard NORAD format"
    }
  },
  "required": ["tle_line1", "tle_line2"]
}
```

#### Response Format

```json
{
  "is_valid": true,
  "errors": [],
  "orbital_parameters": {
    "satellite_number": 25544,
    "classification": "U",
    "international_designator": "98067A",
    "epoch": "2024-01-01T02:57:46.963200+00:00",
    "mean_motion_rev_per_day": 15.48919999,
    "eccentricity": 0.0001234,
    "inclination_deg": 51.64,
    "orbital_period_minutes": 93.05
  }
}
```

#### Validation Checks

1. **Format Validation**
   - Line length (69 characters each)
   - Line identifiers ('1 ' and '2 ')
   - Character positions and formats

2. **Checksum Validation**
   - Modulo-10 checksum for each line
   - Ensures data integrity

3. **Consistency Checks**
   - Satellite numbers match between lines
   - Orbital parameter ranges valid

4. **Parameter Extraction**
   - Epoch date/time conversion
   - Orbital elements parsing
   - Period calculation from mean motion

## Input Validation

### Coordinate Systems

All coordinates use **WGS84 datum**:
- **Latitude**: -90° to +90° (negative = South, positive = North)
- **Longitude**: -180° to +180° (negative = West, positive = East)
- **Elevation**: 0° to 90° (0° = horizon, 90° = zenith)
- **Azimuth**: 0° to 360° (0° = North, 90° = East, 180° = South, 270° = West)

### Time Formats

All timestamps use **ISO 8601 format in UTC**:
- `2024-01-01T00:00:00Z`
- `2024-01-01T00:00:00+00:00`
- `2024-01-01T00:00:00.000Z`
- `2024-01-01T00:00:00.000+00:00`

### TLE Format

Two-Line Elements must follow **NORAD standard format**:
- Exactly 69 characters per line
- Line 1 starts with "1 "
- Line 2 starts with "2 "
- Valid modulo-10 checksums
- Consistent satellite numbers

Example:
```
1 25544U 98067A   24001.12345678  .00001234  00000-0  12345-4 0  9999
2 25544  51.6400 123.4567 0001234  12.3456 347.6543 15.48919999123456
```

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid latitude: 95.0",
    "details": {
      "parameter": "latitude",
      "value": 95.0,
      "valid_range": [-90, 90]
    }
  }
}
```

### Common Error Types

#### Input Validation Errors

- **INVALID_LATITUDE**: Latitude outside -90° to +90° range
- **INVALID_LONGITUDE**: Longitude outside -180° to +180° range
- **INVALID_ELEVATION_THRESHOLD**: Elevation threshold outside 0° to 90° range
- **INVALID_TIME_RANGE**: Start time after end time
- **INVALID_TIME_FORMAT**: ISO 8601 parsing failure

#### TLE Validation Errors

- **TLE_LENGTH_ERROR**: Line length not 69 characters
- **TLE_FORMAT_ERROR**: Invalid line identifier or format
- **TLE_CHECKSUM_ERROR**: Checksum validation failure
- **TLE_CONSISTENCY_ERROR**: Satellite numbers don't match
- **TLE_PARAMETER_ERROR**: Invalid orbital parameter values

#### Calculation Errors

- **EPHEMERIS_ERROR**: Unable to load required ephemeris data
- **PROPAGATION_ERROR**: Orbital propagation failure
- **COORDINATE_ERROR**: Coordinate transformation failure

### Error Recovery

1. **Validation Errors**: Fix input parameters and retry
2. **TLE Errors**: Use updated TLE data from authoritative sources
3. **Calculation Errors**: Check internet connectivity for ephemeris data

## Response Formats

### Summary Statistics

All calculation responses include summary statistics:

```json
{
  "summary": {
    "total_windows": 5,
    "total_duration_seconds": 2847.5,
    "total_duration_minutes": 47.46,
    "max_elevation_deg": 78.34,
    "calculation_parameters": { ... }
  }
}
```

### Time Precision

- **Timestamps**: ISO 8601 format with UTC timezone
- **Durations**: Floating point seconds and derived minutes
- **Angles**: Floating point degrees (2 decimal places in output)

### InfluxDB Format

Events formatted for time-series database ingestion:

```json
{
  "measurement": "satellite_access",
  "tags": {
    "satellite_id": "25544",
    "location_id": "MIT_LL",
    "location_type": "ground_station",
    "event_type": "aos"
  },
  "fields": {
    "elevation_deg": 10.0,
    "azimuth_deg": 291.72
  },
  "time": "2024-01-01T06:12:30+00:00"
}
```

## Example Requests

### Calculate ISS Access Windows over MIT

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
      "end_time": "2024-01-01T23:59:59Z",
      "elevation_threshold": 10.0,
      "time_step_seconds": 30
    }
  }
}
```

### Generate Satellite Events for Database

```json
{
  "method": "tools/call",
  "params": {
    "name": "calculate_access_events",
    "arguments": {
      "latitude": 38.9917,
      "longitude": -76.8400,
      "tle_line1": "1 25544U 98067A   24001.12345678  .00001234  00000-0  12345-4 0  9999",
      "tle_line2": "2 25544  51.6400 123.4567 0001234  12.3456 347.6543 15.48919999123456",
      "start_time": "2024-01-01T00:00:00Z",
      "end_time": "2024-01-07T23:59:59Z",
      "satellite_id": "ISS",
      "location_id": "NASA_GSFC",
      "location_type": "ground_station",
      "elevation_threshold": 5.0
    }
  }
}
```

### Validate TLE Data

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

## Performance Considerations

### Calculation Time

- **Single Day**: 0.5-2 seconds typical
- **Week Analysis**: 5-15 seconds typical
- **Fine Time Steps**: Linear increase in calculation time

### Optimization Tips

1. **Balance Time Steps**: 30s provides good accuracy/performance balance
2. **Limit Time Windows**: Longer periods exponentially increase calculation time  
3. **Batch Multiple Stations**: Calculate multiple ground stations in separate calls
4. **Cache TLE Data**: Validate TLE once, reuse for multiple calculations

### Resource Usage

- **Memory**: 50-100MB during calculation
- **CPU**: Single-threaded, benefits from higher clock speeds
- **Network**: Initial download of ephemeris data (~10MB)
- **Storage**: Ephemeris cache (~50MB persistent)