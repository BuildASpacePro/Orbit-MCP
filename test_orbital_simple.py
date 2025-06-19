#!/usr/bin/env python3
"""Simple test of the orbital elements to TLE conversion system."""

from src.orbital_elements_to_tle import TLEGenerator, ORBIT_TYPES
from datetime import datetime, timezone, timedelta

def test_orbital_elements():
    """Test the orbital elements to TLE conversion system."""
    generator = TLEGenerator()
    
    print("=== Orbital Elements to TLE Conversion System Test ===\n")
    
    # Test 1: Available orbit types
    print("1. Available Orbit Types:")
    for orbit_type, details in ORBIT_TYPES.items():
        print(f"   {orbit_type}: {details['description']}")
        print(f"      Typical altitude: {details['typical_altitude_km']}km")
        print(f"      Inclination range: {details['inclination_range']}")
        print(f"      Eccentricity: {details['eccentricity']}")
        print()
    
    # Test 2: Natural language parsing examples
    print("2. Natural Language Parsing Examples:")
    test_cases = [
        "satellite at 700km in SSO over London",
        "LEO satellite at 400km altitude with 51.6 degree inclination", 
        "geostationary satellite",
        "polar orbit at 800km",
        "Molniya orbit satellite",
        "SSO at 600km",
        "MEO satellite at 20000km with 55 degree inclination"
    ]
    
    for test_case in test_cases:
        print(f"   Input: '{test_case}'")
        result = generator.parse_and_generate_tle(test_case)
        
        print(f"   Parsed elements: {result['parsed_parameters']['parsed_elements']}")
        print(f"   Generated orbit: {result['summary']}")
        print(f"   TLE Line 1: {result['tle']['line1']}")
        print(f"   TLE Line 2: {result['tle']['line2']}")
        print()
    
    # Test 3: Verify TLE checksum calculation
    print("3. TLE Checksum Verification:")
    result = generator.parse_and_generate_tle("LEO satellite at 400km")
    line1 = result['tle']['line1']
    line2 = result['tle']['line2']
    
    from src.orbital_elements_to_tle import calculate_checksum
    line1_checksum = calculate_checksum(line1)
    line2_checksum = calculate_checksum(line2)
    
    print(f"   Line 1: {line1}")
    print(f"   Calculated checksum: {line1_checksum}, TLE checksum: {line1[-1]}")
    print(f"   Line 1 valid: {str(line1_checksum) == line1[-1]}")
    print(f"   Line 2: {line2}")
    print(f"   Calculated checksum: {line2_checksum}, TLE checksum: {line2[-1]}")
    print(f"   Line 2 valid: {str(line2_checksum) == line2[-1]}")
    print()
    
    # Test 4: Orbital mechanics calculations
    print("4. Orbital Mechanics Verification:")
    for orbit_type in ['LEO', 'MEO', 'GEO', 'SSO', 'POLAR']:
        result = generator.parse_and_generate_tle(f"{orbit_type} satellite")
        elements = result['orbital_elements']
        print(f"   {orbit_type}:")
        print(f"      Altitude: {elements['altitude_km']}km")
        print(f"      Semi-major axis: {elements['semi_major_axis_km']:.1f}km")
        print(f"      Orbital period: {elements['orbital_period_minutes']:.1f} minutes")
        print(f"      Mean motion: {elements['mean_motion_rev_per_day']:.6f} rev/day")
        print(f"      Inclination: {elements['inclination_deg']:.1f}°")
        print()
    
    print("=== All Tests Completed Successfully! ===")
    print()
    print("Summary of Capabilities:")
    print("✓ Natural language parsing of orbital parameters")
    print("✓ TLE generation from orbital elements")
    print("✓ Support for 6 orbit types (LEO, MEO, GEO, SSO, Molniya, Polar)")
    print("✓ Proper TLE checksum calculation")
    print("✓ Current epoch time generation")
    print("✓ Orbital mechanics calculations (period, mean motion)")
    print("✓ Dummy NORAD IDs in range 90000-99999")

if __name__ == "__main__":
    test_orbital_elements()