# Orbital Elements to TLE Conversion System

## Overview

Successfully implemented a comprehensive orbital elements to TLE conversion system that can parse natural language requests like "satellite at 700km in SSO over London" and generate valid Two-Line Element (TLE) data.

## Key Features Implemented

### 1. Natural Language Parsing (`OrbitalElementsParser`)
- **Altitude Recognition**: Patterns like "700km", "at 400km altitude", "satellite at 800km"
- **Inclination Parsing**: "51.6 degree inclination", "inclined at 90°"
- **Orbit Type Detection**: LEO, MEO, GEO, SSO, Molniya, Polar orbits
- **Location References**: "over London", "above New York" (for reference)

### 2. Orbit Type Definitions (`ORBIT_TYPES`)
- **LEO**: Low Earth Orbit (160-2000km, typically 400km)
- **MEO**: Medium Earth Orbit (2000-35786km, typically 20200km)
- **GEO**: Geostationary Orbit (35786km, 0° inclination)
- **SSO**: Sun-Synchronous Orbit (600-1500km, calculated inclination)
- **MOLNIYA**: Highly elliptical orbit (63.4° inclination, 0.74 eccentricity)
- **POLAR**: Polar orbit (90° inclination)

### 3. TLE Generation (`TLEGenerator`)
- **Orbital Mechanics**: Proper semi-major axis and mean motion calculations
- **Epoch Generation**: Current UTC time in TLE format
- **Checksum Calculation**: Valid TLE checksums for both lines
- **NORAD IDs**: Dummy satellite numbers in range 90000-99999
- **Eccentricity Handling**: Mostly circular orbits with type-specific values

### 4. Enhanced SatelliteCalculator
- **`parse_orbital_elements_from_text()`**: Parse text and generate TLE
- **`calculate_access_windows_from_orbital_elements()`**: Access windows from orbital text
- **`calculate_access_windows_from_orbital_elements_by_city()`**: Combine with city lookup
- **`get_orbit_types()`**: Return available orbit type definitions

### 5. New MCP Tools
- **`parse_orbital_elements`**: Parse natural language orbital parameters
- **`calculate_access_windows_from_orbital_elements`**: Calculate access windows from orbital text
- **`calculate_access_windows_from_orbital_elements_by_city`**: Combine orbital elements with city lookup
- **`get_orbit_types`**: Get available orbit types and definitions

## Technical Implementation Details

### Sun-Synchronous Orbit Inclination Calculation
For SSO, the inclination is calculated based on altitude using the approximation:
```python
inclination_rad = math.acos(-((a / 12352) ** 3.5))
```

### TLE Format Compliance
- **Line 1**: Satellite number, classification, international designator, epoch, drag terms
- **Line 2**: Satellite number, inclination, RAAN, eccentricity, argument of perigee, mean anomaly, mean motion, revolution number
- **Checksums**: Proper modulo-10 checksums for validation

### Orbital Mechanics
- **Kepler's Third Law**: `n = sqrt(μ/a³)` for mean motion calculation
- **Earth Parameters**: μ = 398600.4418 km³/s², radius = 6371 km
- **Period Conversion**: Mean motion in revolutions/day to orbital period in minutes

## Example Usage

### Input: "satellite at 700km in SSO over London"
**Parsed Elements:**
- altitude: 700.0 km
- orbit type: SSO
- reference location: london

**Generated Orbit:**
- Satellite Type: SSO
- Altitude: 700 km
- Inclination: 98.16°
- Orbital Period: 98.62 minutes
- Eccentricity: 0.001

**Generated TLE:**
```
Line 1: 1 91970U 24001A   25170.83858796  .00001000  00000-0  10000-4 0  9998
Line 2: 2 91970  98.1601   0.0000 0010000   0.0000   0.0000 14.60096319    14
```

## Supported Natural Language Patterns

### Altitude Patterns
- "satellite at 700km"
- "400km altitude"
- "orbit at 800 kilometers"

### Orbit Types
- "LEO satellite", "low earth orbit"
- "geostationary satellite", "GEO"
- "sun-synchronous", "SSO"
- "polar orbit"
- "Molniya orbit"

### Inclination
- "51.6 degree inclination"
- "inclined at 90°"
- "with 55 degree inclination"

### Location References
- "over London"
- "above New York"
- "passing over Tokyo"

## Integration with Existing System

The orbital elements system is fully integrated with the existing satellite MCP server:
- **Lighting Calculations**: Ground and satellite lighting during access windows
- **City Database**: Automatic city coordinate lookup
- **Bulk Processing**: Works with CSV inputs
- **Access Window Calculation**: Full integration with Skyfield orbital mechanics

## Files Modified/Created

1. **`src/orbital_elements_to_tle.py`**: Main orbital elements to TLE conversion module
2. **`src/satellite_calc.py`**: Enhanced with orbital elements methods
3. **`src/mcp_server.py`**: Added new MCP tools and handlers
4. **Test files**: Comprehensive testing of all functionality

## Compliance with Requirements

✅ **TLE Perturbations**: Uses simplified model for generated TLEs, would include perturbations if TLE provided  
✅ **Circular Eccentricity**: Keeps eccentricity mostly circular (0.0001-0.001, except Molniya)  
✅ **NORAD ID Range**: Uses dummy IDs in range 90000-99999  
✅ **Text Parsing**: Recognizes orbital elements well enough to construct TLE  
✅ **Current Time**: Generated TLEs use current time as epoch  
✅ **Natural Language**: Successfully parses "satellite at 700km in SSO over London"

The system is now ready for production use and can handle a wide variety of natural language orbital parameter descriptions!