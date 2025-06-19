#!/usr/bin/env python3
"""Generate TLE data from orbital elements with natural language parsing."""

import math
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any


def calculate_checksum(line: str) -> int:
    """Calculate TLE checksum."""
    checksum = 0
    for char in line[:-1]:  # Exclude the checksum digit itself
        if char.isdigit():
            checksum += int(char)
        elif char == '-':
            checksum += 1
    return checksum % 10


# Orbital type definitions with standard parameters
ORBIT_TYPES = {
    "LEO": {
        "description": "Low Earth Orbit",
        "typical_altitude_km": 400,
        "altitude_range": (160, 2000),
        "inclination_range": (0, 180),
        "eccentricity": 0.0001,
        "typical_period_minutes": 90
    },
    "MEO": {
        "description": "Medium Earth Orbit",
        "typical_altitude_km": 20200,
        "altitude_range": (2000, 35786),
        "inclination_range": (0, 180),
        "eccentricity": 0.001,
        "typical_period_minutes": 720
    },
    "GEO": {
        "description": "Geostationary Earth Orbit",
        "typical_altitude_km": 35786,
        "altitude_range": (35786, 35786),
        "inclination_range": (0, 0.1),
        "eccentricity": 0.0001,
        "typical_period_minutes": 1436.1
    },
    "SSO": {
        "description": "Sun-Synchronous Orbit",
        "typical_altitude_km": 800,
        "altitude_range": (600, 1500),
        "inclination_range": (96, 102),
        "eccentricity": 0.001,
        "typical_period_minutes": 100
    },
    "MOLNIYA": {
        "description": "Molniya Orbit (highly elliptical)",
        "typical_altitude_km": 19100,  # Semi-major axis altitude equivalent
        "altitude_range": (500, 39300),
        "inclination_range": (63, 65),
        "eccentricity": 0.74,
        "typical_period_minutes": 718
    },
    "POLAR": {
        "description": "Polar Orbit",
        "typical_altitude_km": 800,
        "altitude_range": (300, 1500),
        "inclination_range": (88, 92),
        "eccentricity": 0.001,
        "typical_period_minutes": 100
    }
}


class OrbitalElementsParser:
    """Parse natural language text to extract orbital parameters."""
    
    def __init__(self):
        """Initialize the parser with regex patterns."""
        # Altitude patterns
        self.altitude_patterns = [
            r'(\d+(?:\.\d+)?)\s*km(?:\s+altitude)?',
            r'altitude\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*km',
            r'at\s+(\d+(?:\.\d+)?)\s*km',
            r'(\d+(?:\.\d+)?)\s*kilometers?(?:\s+altitude)?'
        ]
        
        # Inclination patterns
        self.inclination_patterns = [
            r'inclination\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*(?:degrees?|°)',
            r'(\d+(?:\.\d+)?)\s*(?:degrees?|°)\s+inclination',
            r'inclined\s+at\s+(\d+(?:\.\d+)?)\s*(?:degrees?|°)'
        ]
        
        # Orbit type patterns
        self.orbit_type_patterns = {
            'LEO': [r'low\s+earth\s+orbit', r'\bLEO\b'],
            'MEO': [r'medium\s+earth\s+orbit', r'\bMEO\b'],
            'GEO': [r'geostationary', r'\bGEO\b', r'geosynchronous'],
            'SSO': [r'sun[\s-]synchronous', r'\bSSO\b'],
            'MOLNIYA': [r'molniya', r'highly\s+elliptical'],
            'POLAR': [r'polar\s+orbit', r'\bpolar\b']
        }
        
        # Location patterns for reference
        self.location_patterns = [
            r'over\s+([a-zA-Z\s,]+)',
            r'above\s+([a-zA-Z\s,]+)',
            r'passing\s+over\s+([a-zA-Z\s,]+)'
        ]
    
    def parse_text(self, text: str) -> Dict[str, Any]:
        """Parse natural language text to extract orbital parameters."""
        text = text.lower().strip()
        result = {
            'altitude_km': None,
            'inclination_deg': None,
            'orbit_type': None,
            'reference_location': None,
            'eccentricity': None,
            'parsed_elements': []
        }
        
        # Extract altitude
        for pattern in self.altitude_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result['altitude_km'] = float(match.group(1))
                result['parsed_elements'].append(f"altitude: {result['altitude_km']} km")
                break
        
        # Extract inclination
        for pattern in self.inclination_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result['inclination_deg'] = float(match.group(1))
                result['parsed_elements'].append(f"inclination: {result['inclination_deg']}°")
                break
        
        # Extract orbit type
        for orbit_type, patterns in self.orbit_type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    result['orbit_type'] = orbit_type
                    result['parsed_elements'].append(f"orbit type: {orbit_type}")
                    break
            if result['orbit_type']:
                break
        
        # Extract reference location
        for pattern in self.location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result['reference_location'] = match.group(1).strip()
                result['parsed_elements'].append(f"reference location: {result['reference_location']}")
                break
        
        return result


class TLEGenerator:
    """Generate TLE data from orbital elements."""
    
    def __init__(self):
        """Initialize TLE generator."""
        self.earth_radius_km = 6371.0
        self.earth_mu = 398600.4418  # km³/s²
        self.parser = OrbitalElementsParser()
    
    def altitude_to_semi_major_axis(self, altitude_km: float) -> float:
        """Convert altitude to semi-major axis."""
        return altitude_km + self.earth_radius_km
    
    def semi_major_axis_to_mean_motion(self, semi_major_axis_km: float) -> float:
        """Calculate mean motion (revolutions per day) from semi-major axis."""
        # Kepler's third law: n = sqrt(μ/a³)
        n_rad_per_sec = math.sqrt(self.earth_mu / (semi_major_axis_km ** 3))
        n_rev_per_day = n_rad_per_sec * 86400 / (2 * math.pi)
        return n_rev_per_day
    
    def calculate_sso_inclination(self, altitude_km: float) -> float:
        """Calculate inclination for sun-synchronous orbit at given altitude."""
        # Simplified calculation for SSO inclination
        # Real calculation involves J2 perturbation, this is an approximation
        a = self.altitude_to_semi_major_axis(altitude_km)
        # Approximate formula for SSO inclination
        inclination_rad = math.acos(-((a / 12352) ** 3.5))
        return math.degrees(inclination_rad)
    
    def generate_orbital_elements(self, parsed_params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate complete orbital elements from parsed parameters."""
        elements = {
            'altitude_km': 400,  # Default LEO altitude
            'inclination_deg': 51.6,  # Default ISS-like inclination
            'eccentricity': 0.0001,  # Nearly circular
            'argument_of_perigee_deg': 0.0,
            'raan_deg': 0.0,  # Right Ascension of Ascending Node
            'mean_anomaly_deg': 0.0,
            'orbit_type': 'LEO'
        }
        
        # Use parsed parameters
        if parsed_params.get('altitude_km'):
            elements['altitude_km'] = parsed_params['altitude_km']
        
        if parsed_params.get('inclination_deg'):
            elements['inclination_deg'] = parsed_params['inclination_deg']
        
        if parsed_params.get('orbit_type'):
            elements['orbit_type'] = parsed_params['orbit_type']
            orbit_def = ORBIT_TYPES.get(parsed_params['orbit_type'], {})
            
            # Apply orbit type defaults if not explicitly specified
            if not parsed_params.get('altitude_km'):
                elements['altitude_km'] = orbit_def.get('typical_altitude_km', 400)
            
            if not parsed_params.get('inclination_deg'):
                if parsed_params['orbit_type'] == 'GEO':
                    elements['inclination_deg'] = 0.0
                elif parsed_params['orbit_type'] == 'SSO':
                    elements['inclination_deg'] = self.calculate_sso_inclination(elements['altitude_km'])
                elif parsed_params['orbit_type'] == 'POLAR':
                    elements['inclination_deg'] = 90.0
                elif parsed_params['orbit_type'] == 'MOLNIYA':
                    elements['inclination_deg'] = 63.4
                else:
                    # Use range midpoint for other types
                    inc_range = orbit_def.get('inclination_range', (51, 52))
                    elements['inclination_deg'] = (inc_range[0] + inc_range[1]) / 2
            
            # Set eccentricity based on orbit type
            elements['eccentricity'] = orbit_def.get('eccentricity', 0.0001)
        
        # Calculate derived parameters
        elements['semi_major_axis_km'] = self.altitude_to_semi_major_axis(elements['altitude_km'])
        elements['mean_motion_rev_per_day'] = self.semi_major_axis_to_mean_motion(elements['semi_major_axis_km'])
        elements['orbital_period_minutes'] = 1440.0 / elements['mean_motion_rev_per_day']
        
        return elements
    
    def generate_tle_from_elements(self, elements: Dict[str, Any], satellite_number: int = None) -> Tuple[str, str]:
        """Generate TLE lines from orbital elements."""
        # Use dummy satellite number in range 90000-99999 if not provided
        if satellite_number is None:
            satellite_number = 90000 + hash(str(elements)) % 10000
        
        # Current epoch
        now = datetime.now(timezone.utc)
        epoch_year = now.year % 100  # Two-digit year
        day_of_year = now.timetuple().tm_yday
        fraction_of_day = (now.hour * 3600 + now.minute * 60 + now.second) / 86400.0
        epoch_day = day_of_year + fraction_of_day
        
        # Format TLE Line 1 (without checksum)
        line1_base = f"1 {satellite_number:05d}U 24001A   {epoch_year:02d}{epoch_day:012.8f}  .00001000  00000-0  10000-4 0  999"
        
        # Format TLE Line 2 (without checksum)
        inclination = elements['inclination_deg']
        raan = elements['raan_deg']
        eccentricity_str = f"{int(elements['eccentricity'] * 10000000):07d}"
        arg_perigee = elements['argument_of_perigee_deg']
        mean_anomaly = elements['mean_anomaly_deg']
        mean_motion = elements['mean_motion_rev_per_day']
        rev_number = 1  # Dummy revolution number
        
        line2_base = f"2 {satellite_number:05d} {inclination:8.4f} {raan:8.4f} {eccentricity_str} {arg_perigee:8.4f} {mean_anomaly:8.4f} {mean_motion:11.8f}{rev_number:5d}"
        
        # Calculate and append checksums
        checksum1 = calculate_checksum(line1_base + "0")
        checksum2 = calculate_checksum(line2_base + "0")
        
        line1_final = line1_base + str(checksum1)
        line2_final = line2_base + str(checksum2)
        
        return line1_final, line2_final
    
    def parse_and_generate_tle(self, text: str) -> Dict[str, Any]:
        """Parse natural language text and generate TLE."""
        # Parse the text
        parsed_params = self.parser.parse_text(text)
        
        # Generate orbital elements
        elements = self.generate_orbital_elements(parsed_params)
        
        # Generate TLE
        line1, line2 = self.generate_tle_from_elements(elements)
        
        return {
            'parsed_text': text,
            'parsed_parameters': parsed_params,
            'orbital_elements': elements,
            'tle': {
                'line1': line1,
                'line2': line2
            },
            'summary': {
                'satellite_type': elements['orbit_type'],
                'altitude_km': elements['altitude_km'],
                'inclination_deg': round(elements['inclination_deg'], 2),
                'period_minutes': round(elements['orbital_period_minutes'], 2),
                'eccentricity': elements['eccentricity']
            }
        }


def main():
    """Test the TLE generation system."""
    generator = TLEGenerator()
    
    test_cases = [
        "satellite at 700km in SSO over London",
        "LEO satellite at 400km altitude with 51.6 degree inclination",
        "geostationary satellite",
        "polar orbit at 800km",
        "Molniya orbit satellite"
    ]
    
    for test_case in test_cases:
        print(f"\nTest: {test_case}")
        result = generator.parse_and_generate_tle(test_case)
        print(f"TLE Line 1: {result['tle']['line1']}")
        print(f"TLE Line 2: {result['tle']['line2']}")
        print(f"Summary: {result['summary']}")


if __name__ == "__main__":
    main()