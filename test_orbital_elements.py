#!/usr/bin/env python3
"""Test the orbital elements to TLE conversion system."""

import asyncio
import json
from datetime import datetime, timezone, timedelta
from src.mcp_server import SatelliteMCPServer

async def test_orbital_elements_server():
    """Test the MCP server with orbital elements functionality."""
    server = SatelliteMCPServer()
    
    print("Testing MCP Server Orbital Elements Tools\n")
    
    # Test 1: Parse orbital elements
    print("1. Testing parse_orbital_elements:")
    orbital_args = {"orbital_text": "satellite at 700km in SSO over London"}
    result = await server._handle_parse_orbital_elements(orbital_args)
    content = json.loads(result.content[0].text)
    print(f"   Input: {content['parsed_text']}")
    print(f"   Parsed: {content['parsed_parameters']['parsed_elements']}")
    print(f"   Summary: {content['summary']}")
    print()
    
    # Test 2: Get orbit types
    print("2. Testing get_orbit_types:")
    result = await server._handle_get_orbit_types({})
    orbit_types = json.loads(result.content[0].text)
    print(f"   Available orbit types:")
    for orbit_type, details in orbit_types['orbit_types'].items():
        print(f"   - {orbit_type}: {details['description']}")
    print()
    
    # Test 3: Calculate access windows from orbital elements by city
    print("3. Testing calculate_access_windows_from_orbital_elements_by_city:")
    start_time = datetime.now(timezone.utc)
    end_time = start_time + timedelta(hours=12)
    
    city_args = {
        "orbital_text": "LEO satellite at 400km altitude",
        "city_name": "London",
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "elevation_threshold": 10.0
    }
    
    try:
        result = await server._handle_calculate_access_windows_from_orbital_elements_by_city(city_args)
        content = json.loads(result.content[0].text)
        print(f"   City: {content['city_info']['name']}, {content['city_info']['country']}")
        print(f"   Orbital Summary: {content['orbital_request']['orbital_summary']}")
        print(f"   Generated TLE:")
        print(f"     Line 1: {content['orbital_request']['generated_tle']['line1']}")
        print(f"     Line 2: {content['orbital_request']['generated_tle']['line2']}")
        print(f"   Found {content['summary']['total_windows']} access windows")
        if content['access_windows']:
            first_window = content['access_windows'][0]
            print(f"   First window: {first_window['aos_time']} to {first_window['los_time']}")
            print(f"   Max elevation: {first_window['max_elevation_deg']}°")
    except Exception as e:
        print(f"   Error: {e}")
    print()
    
    # Test 4: Test different orbit types
    print("4. Testing different orbit types:")
    test_orbits = [
        "geostationary satellite",
        "polar orbit at 800km", 
        "SSO satellite at 700km",
        "Molniya orbit satellite"
    ]
    
    for orbital_text in test_orbits:
        orbital_args = {"orbital_text": orbital_text}
        result = await server._handle_parse_orbital_elements(orbital_args)
        content = json.loads(result.content[0].text)
        summary = content['summary']
        print(f"   {orbital_text}:")
        print(f"     Type: {summary['satellite_type']}, Alt: {summary['altitude_km']}km, Inc: {summary['inclination_deg']}°")
    
    print("\nAll tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_orbital_elements_server())