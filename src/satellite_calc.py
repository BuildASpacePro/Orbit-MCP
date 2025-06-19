"""Core satellite orbital mechanics calculations using Skyfield library."""

import logging
import math
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict

import numpy as np
from skyfield.api import Topos, load, EarthSatellite, wgs84
from skyfield.timelib import Time
from skyfield.units import Angle
from skyfield.almanac import find_discrete, risings_and_settings
from skyfield.searchlib import find_minima

from .world_cities import lookup_city, search_cities


logger = logging.getLogger(__name__)


def calculate_tle_checksum(line: str) -> int:
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
        checksum1 = calculate_tle_checksum(line1_base + "0")
        checksum2 = calculate_tle_checksum(line2_base + "0")
        
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


@dataclass
class AccessWindow:
    """Represents a satellite access window over a ground station."""
    aos_time: datetime
    los_time: datetime
    culmination_time: datetime
    duration_seconds: float
    max_elevation_deg: float
    aos_azimuth_deg: float
    los_azimuth_deg: float
    culmination_azimuth_deg: float
    # Lighting conditions during culmination
    ground_lighting: Dict[str, Any]  # Dawn/dusk conditions at ground station
    satellite_lighting: Dict[str, Any]  # Sunlight/eclipse conditions for satellite




@dataclass
class TLEValidationResult:
    """Result of TLE validation."""
    is_valid: bool
    errors: List[str]
    satellite_number: Optional[int]
    classification: Optional[str]
    international_designator: Optional[str]
    epoch: Optional[datetime]
    mean_motion: Optional[float]
    eccentricity: Optional[float]
    inclination_deg: Optional[float]
    orbital_period_minutes: Optional[float]


class SatelliteCalculator:
    """Handles satellite orbital mechanics calculations."""
    
    def __init__(self):
        """Initialize calculator with Skyfield timescale."""
        self.ts = load.timescale()
        self.eph = load('de421.bsp')  # Load planetary ephemeris
        self.sun = self.eph['sun']
        self.earth = self.eph['earth']
        self.tle_generator = TLEGenerator()
    
    def validate_tle(self, line1: str, line2: str) -> TLEValidationResult:
        """Validate Two-Line Element data and extract orbital parameters."""
        errors = []
        
        # Basic format validation
        if len(line1) != 69:
            errors.append(f"Line 1 length {len(line1)}, expected 69 characters")
        if len(line2) != 69:
            errors.append(f"Line 2 length {len(line2)}, expected 69 characters")
        
        if not line1.startswith('1 '):
            errors.append("Line 1 must start with '1 '")
        if not line2.startswith('2 '):
            errors.append("Line 2 must start with '2 '")
        
        # Checksum validation
        def calculate_checksum(line: str) -> int:
            """Calculate TLE line checksum."""
            checksum = 0
            for char in line[:-1]:
                if char.isdigit():
                    checksum += int(char)
                elif char == '-':
                    checksum += 1
            return checksum % 10
        
        try:
            line1_checksum = int(line1[-1])
            if calculate_checksum(line1) != line1_checksum:
                errors.append("Line 1 checksum validation failed")
        except (ValueError, IndexError):
            errors.append("Line 1 checksum format invalid")
        
        try:
            line2_checksum = int(line2[-1])
            if calculate_checksum(line2) != line2_checksum:
                errors.append("Line 2 checksum validation failed")
        except (ValueError, IndexError):
            errors.append("Line 2 checksum format invalid")
        
        # Satellite number consistency
        try:
            sat_num_1 = int(line1[2:7])
            sat_num_2 = int(line2[2:7])
            if sat_num_1 != sat_num_2:
                errors.append(f"Satellite numbers don't match: {sat_num_1} vs {sat_num_2}")
        except ValueError:
            errors.append("Invalid satellite number format")
            sat_num_1 = None
        
        # Extract orbital parameters if basic validation passes
        satellite_number = None
        classification = None
        international_designator = None
        epoch = None
        mean_motion = None
        eccentricity = None
        inclination_deg = None
        orbital_period_minutes = None
        
        if len(errors) == 0:
            try:
                # Create satellite object to validate orbital parameters
                satellite = EarthSatellite(line1, line2, ts=self.ts)
                
                satellite_number = sat_num_1
                classification = line1[7]
                international_designator = line1[9:17].strip()
                
                # Extract epoch
                epoch_year = int(line1[18:20])
                epoch_year += 2000 if epoch_year < 57 else 1900  # Two-digit year logic
                epoch_day = float(line1[20:32])
                from datetime import timedelta
                epoch = datetime(epoch_year, 1, 1, tzinfo=timezone.utc)
                epoch = epoch.replace(day=1) + timedelta(days=int(epoch_day - 1))
                epoch = epoch + timedelta(milliseconds=int((epoch_day % 1) * 24 * 3600 * 1000))
                
                # Orbital parameters
                inclination_deg = float(line2[8:16])
                eccentricity = float('0.' + line2[26:33])
                mean_motion = float(line2[52:63])  # revolutions per day
                orbital_period_minutes = 1440.0 / mean_motion if mean_motion > 0 else None
                
                # Validate parameter ranges
                if not (0 <= inclination_deg <= 180):
                    errors.append(f"Invalid inclination: {inclination_deg}°")
                if not (0 <= eccentricity < 1):
                    errors.append(f"Invalid eccentricity: {eccentricity}")
                if mean_motion <= 0:
                    errors.append(f"Invalid mean motion: {mean_motion}")
                    
            except Exception as e:
                errors.append(f"Failed to parse orbital parameters: {str(e)}")
        
        return TLEValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            satellite_number=satellite_number,
            classification=classification,
            international_designator=international_designator,
            epoch=epoch,
            mean_motion=mean_motion,
            eccentricity=eccentricity,
            inclination_deg=inclination_deg,
            orbital_period_minutes=orbital_period_minutes
        )
    
    def calculate_ground_lighting(self, latitude: float, longitude: float, timestamp: datetime) -> Dict[str, Any]:
        """Calculate ground lighting conditions at a specific time and location."""
        # Convert to Skyfield time
        t = self.ts.from_datetime(timestamp.replace(tzinfo=timezone.utc))
        
        # Create ground location object
        location = wgs84.latlon(latitude, longitude)
        
        # Calculate sun position
        sun_apparent = (self.earth + location).at(t).observe(self.sun).apparent()
        sun_alt, sun_az, _ = sun_apparent.altaz()
        
        sun_elevation = sun_alt.degrees
        
        # Determine lighting conditions based on sun elevation
        if sun_elevation > -0.833:  # Above horizon (accounting for atmospheric refraction)
            condition = "daylight"
        elif sun_elevation > -6:  # Civil twilight
            condition = "civil_twilight"
        elif sun_elevation > -12:  # Nautical twilight
            condition = "nautical_twilight"
        elif sun_elevation > -18:  # Astronomical twilight
            condition = "astronomical_twilight"
        else:
            condition = "night"
        
        return {
            "condition": condition,
            "sun_elevation_deg": round(sun_elevation, 2),
            "sun_azimuth_deg": round(sun_az.degrees, 2),
            "civil_twilight": sun_elevation > -6,
            "nautical_twilight": sun_elevation > -12,
            "astronomical_twilight": sun_elevation > -18,
            "is_daylight": sun_elevation > -0.833,
            "is_night": sun_elevation <= -18
        }
    
    def calculate_satellite_lighting(self, satellite: EarthSatellite, timestamp: datetime) -> Dict[str, Any]:
        """Calculate satellite lighting conditions (sunlight/eclipse) at a specific time."""
        # Convert to Skyfield time
        t = self.ts.from_datetime(timestamp.replace(tzinfo=timezone.utc))
        
        # Get satellite position
        geocentric = satellite.at(t)
        
        # Get satellite's subpoint for ground lighting reference
        sat_lat = geocentric.subpoint().latitude.degrees
        sat_lon = geocentric.subpoint().longitude.degrees
        
        # Calculate ground lighting at satellite's subpoint
        ground_lighting = self.calculate_ground_lighting(sat_lat, sat_lon, timestamp)
        
        # Get satellite position vector
        sat_position = geocentric.position.km
        sat_distance = np.linalg.norm(sat_position)
        
        # Simplified eclipse calculation: 
        # Satellite is in eclipse if it's on the night side of Earth
        # This is an approximation based on the ground track lighting
        
        # For LEO satellites, use ground track lighting as approximation
        # For higher satellites, they're more likely to be in sunlight
        in_eclipse = False
        if sat_distance < 2000:  # LEO satellites (below ~2000km)
            in_eclipse = ground_lighting["condition"] in ["night", "astronomical_twilight"]
        elif sat_distance < 20000:  # MEO satellites
            in_eclipse = ground_lighting["condition"] == "night"
        # GEO and higher satellites are rarely in eclipse, so default to sunlight
        
        return {
            "condition": "eclipse" if in_eclipse else "sunlight",
            "in_eclipse": in_eclipse,
            "in_sunlight": not in_eclipse,
            "satellite_altitude_km": round(sat_distance - 6371, 2),  # Altitude above Earth surface
            "subpoint_latitude": round(sat_lat, 4),
            "subpoint_longitude": round(sat_lon, 4),
            "ground_track_lighting": ground_lighting["condition"],
            "eclipse_calculation": "simplified_altitude_based"
        }
    
    def calculate_access_windows(
        self,
        latitude: float,
        longitude: float,
        tle_line1: str,
        tle_line2: str,
        start_time: datetime,
        end_time: datetime,
        elevation_threshold: float = 10.0,
        time_step_seconds: int = 30
    ) -> List[AccessWindow]:
        """Calculate satellite access windows for a ground station."""
        
        # Validate inputs
        if not (-90 <= latitude <= 90):
            raise ValueError(f"Invalid latitude: {latitude}")
        if not (-180 <= longitude <= 180):
            raise ValueError(f"Invalid longitude: {longitude}")
        if elevation_threshold < 0 or elevation_threshold > 90:
            raise ValueError(f"Invalid elevation threshold: {elevation_threshold}")
        if start_time >= end_time:
            raise ValueError("Start time must be before end time")
        
        # Validate TLE
        tle_validation = self.validate_tle(tle_line1, tle_line2)
        if not tle_validation.is_valid:
            raise ValueError(f"Invalid TLE: {'; '.join(tle_validation.errors)}")
        
        # Create ground station and satellite objects
        ground_station = Topos(latitude_degrees=latitude, longitude_degrees=longitude)
        satellite = EarthSatellite(tle_line1, tle_line2, ts=self.ts)
        
        # Create time range
        t_start = self.ts.from_datetime(start_time.replace(tzinfo=timezone.utc))
        t_end = self.ts.from_datetime(end_time.replace(tzinfo=timezone.utc))
        
        # Calculate satellite positions at regular intervals
        time_points = []
        current_time = t_start
        while current_time.tt <= t_end.tt:
            time_points.append(current_time)
            current_time = self.ts.tt_jd(current_time.tt + time_step_seconds / 86400.0)
        
        if not time_points:
            return []
        
        times = self.ts.tt_jd([t.tt for t in time_points])
        
        # Calculate topocentric coordinates
        difference = satellite - ground_station
        topocentric = difference.at(times)
        elevation, azimuth, distance = topocentric.altaz()
        
        # Find access windows
        access_windows = []
        in_access = False
        aos_idx = None
        culmination_idx = None
        max_elevation = -90.0
        
        for i, (elev_deg, az_deg) in enumerate(zip(elevation.degrees, azimuth.degrees)):
            if elev_deg >= elevation_threshold and not in_access:
                # Access start (AOS)
                in_access = True
                aos_idx = i
                culmination_idx = i
                max_elevation = elev_deg
                
            elif elev_deg >= elevation_threshold and in_access:
                # Continue access - check for new maximum
                if elev_deg > max_elevation:
                    max_elevation = elev_deg
                    culmination_idx = i
                    
            elif elev_deg < elevation_threshold and in_access:
                # Access end (LOS)
                in_access = False
                los_idx = i - 1 if i > 0 else i
                
                # Create access window
                aos_time = time_points[aos_idx].utc_datetime()
                los_time = time_points[los_idx].utc_datetime()
                culmination_time = time_points[culmination_idx].utc_datetime()
                
                duration_seconds = (los_time - aos_time).total_seconds()
                
                # Calculate lighting conditions at culmination
                ground_lighting = self.calculate_ground_lighting(latitude, longitude, culmination_time)
                satellite_lighting = self.calculate_satellite_lighting(satellite, culmination_time)
                
                access_window = AccessWindow(
                    aos_time=aos_time,
                    los_time=los_time,
                    culmination_time=culmination_time,
                    duration_seconds=duration_seconds,
                    max_elevation_deg=max_elevation,
                    aos_azimuth_deg=azimuth.degrees[aos_idx],
                    los_azimuth_deg=azimuth.degrees[los_idx],
                    culmination_azimuth_deg=azimuth.degrees[culmination_idx],
                    ground_lighting=ground_lighting,
                    satellite_lighting=satellite_lighting
                )
                
                access_windows.append(access_window)
        
        # Handle case where access window extends beyond end time
        if in_access and aos_idx is not None:
            los_idx = len(time_points) - 1
            aos_time = time_points[aos_idx].utc_datetime()
            los_time = time_points[los_idx].utc_datetime()
            culmination_time = time_points[culmination_idx].utc_datetime()
            
            duration_seconds = (los_time - aos_time).total_seconds()
            
            # Calculate lighting conditions at culmination
            ground_lighting = self.calculate_ground_lighting(latitude, longitude, culmination_time)
            satellite_lighting = self.calculate_satellite_lighting(satellite, culmination_time)
            
            access_window = AccessWindow(
                aos_time=aos_time,
                los_time=los_time,
                culmination_time=culmination_time,
                duration_seconds=duration_seconds,
                max_elevation_deg=max_elevation,
                aos_azimuth_deg=azimuth.degrees[aos_idx],
                los_azimuth_deg=azimuth.degrees[los_idx],
                culmination_azimuth_deg=azimuth.degrees[culmination_idx],
                ground_lighting=ground_lighting,
                satellite_lighting=satellite_lighting
            )
            
            access_windows.append(access_window)
        
        logger.info(f"Found {len(access_windows)} access windows")
        return access_windows
    
    def parse_locations_from_csv_content(self, csv_content: str) -> List[Dict[str, Any]]:
        """Parse locations from CSV content with flexible format handling."""
        import csv
        import io
        
        lines = csv_content.strip().split('\n')
        if not lines:
            raise ValueError("CSV content is empty")
        
        # Parse header to identify columns
        reader = csv.DictReader(io.StringIO(csv_content))
        
        locations = []
        for row_num, row in enumerate(reader, 1):
            try:
                location = {}
                
                # Find latitude column (flexible naming)
                lat_keys = ['latitude', 'lat', 'Latitude', 'Lat', 'LATITUDE', 'LAT']
                lat_value = None
                for key in lat_keys:
                    if key in row and row[key].strip():
                        lat_value = float(row[key])
                        break
                
                if lat_value is None:
                    raise ValueError(f"No latitude column found in row {row_num}")
                
                # Find longitude column (flexible naming)
                lon_keys = ['longitude', 'lon', 'lng', 'Longitude', 'Lon', 'Lng', 'LONGITUDE', 'LON', 'LNG']
                lon_value = None
                for key in lon_keys:
                    if key in row and row[key].strip():
                        lon_value = float(row[key])
                        break
                
                if lon_value is None:
                    raise ValueError(f"No longitude column found in row {row_num}")
                
                # Find altitude column (optional, default to sea level)
                alt_keys = ['altitude', 'alt', 'elevation', 'elev', 'Altitude', 'Alt', 'Elevation', 'Elev']
                alt_value = 0.0  # Default to sea level
                for key in alt_keys:
                    if key in row and row[key].strip():
                        alt_value = float(row[key])
                        break
                
                # Find name column (optional)
                name_keys = ['name', 'Name', 'NAME', 'site', 'Site', 'SITE', 'station', 'Station', 'STATION']
                name_value = f"Location_{row_num}"  # Default name
                for key in name_keys:
                    if key in row and row[key].strip():
                        name_value = row[key].strip()
                        break
                
                location = {
                    'name': name_value,
                    'latitude': lat_value,
                    'longitude': lon_value,
                    'altitude': alt_value
                }
                
                # Validate coordinates
                if not (-90 <= lat_value <= 90):
                    raise ValueError(f"Invalid latitude {lat_value} in row {row_num}")
                if not (-180 <= lon_value <= 180):
                    raise ValueError(f"Invalid longitude {lon_value} in row {row_num}")
                
                locations.append(location)
                
            except Exception as e:
                logger.warning(f"Skipping row {row_num}: {str(e)}")
                continue
        
        if not locations:
            raise ValueError("No valid locations found in CSV")
        
        logger.info(f"Parsed {len(locations)} locations from CSV")
        return locations
    
    def parse_satellites_from_csv_content(self, csv_content: str) -> List[Dict[str, Any]]:
        """Parse satellites from CSV content with TLE data."""
        import csv
        import io
        
        lines = csv_content.strip().split('\n')
        if not lines:
            raise ValueError("CSV content is empty")
        
        reader = csv.DictReader(io.StringIO(csv_content))
        
        satellites = []
        for row_num, row in enumerate(reader, 1):
            try:
                satellite = {}
                
                # Find name column
                name_keys = ['name', 'Name', 'NAME', 'satellite', 'Satellite', 'SATELLITE', 'sat_name']
                name_value = f"Satellite_{row_num}"
                for key in name_keys:
                    if key in row and row[key].strip():
                        name_value = row[key].strip()
                        break
                
                # Find TLE line 1
                tle1_keys = ['tle_line1', 'tle1', 'line1', 'TLE_LINE1', 'TLE1', 'LINE1']
                tle1_value = None
                for key in tle1_keys:
                    if key in row and row[key].strip():
                        tle1_value = row[key].strip()
                        break
                
                if not tle1_value:
                    raise ValueError(f"No TLE line 1 found in row {row_num}")
                
                # Find TLE line 2
                tle2_keys = ['tle_line2', 'tle2', 'line2', 'TLE_LINE2', 'TLE2', 'LINE2']
                tle2_value = None
                for key in tle2_keys:
                    if key in row and row[key].strip():
                        tle2_value = row[key].strip()
                        break
                
                if not tle2_value:
                    raise ValueError(f"No TLE line 2 found in row {row_num}")
                
                # Validate TLE
                tle_validation = self.validate_tle(tle1_value, tle2_value)
                if not tle_validation.is_valid:
                    raise ValueError(f"Invalid TLE: {'; '.join(tle_validation.errors)}")
                
                satellite = {
                    'name': name_value,
                    'tle_line1': tle1_value,
                    'tle_line2': tle2_value
                }
                
                satellites.append(satellite)
                
            except Exception as e:
                logger.warning(f"Skipping satellite row {row_num}: {str(e)}")
                continue
        
        if not satellites:
            raise ValueError("No valid satellites found in CSV")
        
        logger.info(f"Parsed {len(satellites)} satellites from CSV")
        return satellites
    
    def calculate_bulk_access_windows(
        self,
        locations_csv: str,
        satellites_csv: str,
        start_time: datetime,
        end_time: datetime,
        elevation_threshold: float = 10.0,
        time_step_seconds: int = 30
    ) -> Dict[str, Any]:
        """Calculate access windows for multiple satellites and locations."""
        
        # Parse locations and satellites from CSV content
        locations = self.parse_locations_from_csv_content(locations_csv)
        satellites = self.parse_satellites_from_csv_content(satellites_csv)
        
        results = {
            'summary': {
                'total_locations': len(locations),
                'total_satellites': len(satellites),
                'total_combinations': len(locations) * len(satellites),
                'calculation_parameters': {
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'elevation_threshold': elevation_threshold,
                    'time_step_seconds': time_step_seconds
                }
            },
            'results': []
        }
        
        total_combinations = len(locations) * len(satellites)
        current_combination = 0
        
        for location in locations:
            for satellite in satellites:
                current_combination += 1
                logger.info(f"Processing combination {current_combination}/{total_combinations}: {satellite['name']} over {location['name']}")
                
                try:
                    access_windows = self.calculate_access_windows(
                        latitude=location['latitude'],
                        longitude=location['longitude'],
                        tle_line1=satellite['tle_line1'],
                        tle_line2=satellite['tle_line2'],
                        start_time=start_time,
                        end_time=end_time,
                        elevation_threshold=elevation_threshold,
                        time_step_seconds=time_step_seconds
                    )
                    
                    # Format windows data
                    windows_data = []
                    total_duration = 0.0
                    max_elevation = 0.0
                    
                    for window in access_windows:
                        window_dict = {
                            "aos_time": window.aos_time.isoformat(),
                            "los_time": window.los_time.isoformat(),
                            "culmination_time": window.culmination_time.isoformat(),
                            "duration_seconds": window.duration_seconds,
                            "duration_minutes": round(window.duration_seconds / 60.0, 2),
                            "max_elevation_deg": round(window.max_elevation_deg, 2),
                            "aos_azimuth_deg": round(window.aos_azimuth_deg, 2),
                            "los_azimuth_deg": round(window.los_azimuth_deg, 2),
                            "culmination_azimuth_deg": round(window.culmination_azimuth_deg, 2),
                            "ground_lighting": window.ground_lighting,
                            "satellite_lighting": window.satellite_lighting
                        }
                        windows_data.append(window_dict)
                        total_duration += window.duration_seconds
                        max_elevation = max(max_elevation, window.max_elevation_deg)
                    
                    combination_result = {
                        'satellite': satellite,
                        'location': location,
                        'access_windows': windows_data,
                        'summary': {
                            'total_windows': len(access_windows),
                            'total_duration_seconds': total_duration,
                            'total_duration_minutes': round(total_duration / 60.0, 2),
                            'max_elevation_deg': round(max_elevation, 2)
                        }
                    }
                    
                    results['results'].append(combination_result)
                    
                except Exception as e:
                    logger.error(f"Error calculating windows for {satellite['name']} over {location['name']}: {str(e)}")
                    # Add error result
                    combination_result = {
                        'satellite': satellite,
                        'location': location,
                        'access_windows': [],
                        'error': str(e),
                        'summary': {
                            'total_windows': 0,
                            'total_duration_seconds': 0,
                            'total_duration_minutes': 0,
                            'max_elevation_deg': 0
                        }
                    }
                    results['results'].append(combination_result)
        
        # Calculate overall summary statistics
        total_windows = sum(r['summary']['total_windows'] for r in results['results'])
        total_duration = sum(r['summary']['total_duration_seconds'] for r in results['results'])
        
        results['summary']['total_access_windows'] = total_windows
        results['summary']['total_access_duration_seconds'] = total_duration
        results['summary']['total_access_duration_minutes'] = round(total_duration / 60.0, 2)
        
        logger.info(f"Bulk calculation completed: {total_windows} total access windows found")
        return results
    
    def calculate_access_windows_by_city(
        self,
        city_name: str,
        tle_line1: str,
        tle_line2: str,
        start_time: datetime,
        end_time: datetime,
        elevation_threshold: float = 10.0,
        time_step_seconds: int = 30
    ) -> Dict[str, Any]:
        """Calculate satellite access windows for a city by name lookup."""
        
        # Look up city coordinates
        city_info = lookup_city(city_name)
        if not city_info:
            # Try searching for partial matches
            search_results = search_cities(city_name, limit=5)
            if search_results:
                suggested_cities = [city["name"] for city in search_results]
                raise ValueError(f"City '{city_name}' not found. Did you mean one of: {', '.join(suggested_cities)}?")
            else:
                raise ValueError(f"City '{city_name}' not found in database")
        
        # Calculate access windows using city coordinates
        access_windows = self.calculate_access_windows(
            latitude=city_info["latitude"],
            longitude=city_info["longitude"],
            tle_line1=tle_line1,
            tle_line2=tle_line2,
            start_time=start_time,
            end_time=end_time,
            elevation_threshold=elevation_threshold,
            time_step_seconds=time_step_seconds
        )
        
        # Format response with city information
        windows_data = []
        total_duration = 0.0
        max_elevation = 0.0
        
        for window in access_windows:
            window_dict = {
                "aos_time": window.aos_time.isoformat(),
                "los_time": window.los_time.isoformat(),
                "culmination_time": window.culmination_time.isoformat(),
                "duration_seconds": window.duration_seconds,
                "duration_minutes": round(window.duration_seconds / 60.0, 2),
                "max_elevation_deg": round(window.max_elevation_deg, 2),
                "aos_azimuth_deg": round(window.aos_azimuth_deg, 2),
                "los_azimuth_deg": round(window.los_azimuth_deg, 2),
                "culmination_azimuth_deg": round(window.culmination_azimuth_deg, 2),
                "ground_lighting": window.ground_lighting,
                "satellite_lighting": window.satellite_lighting
            }
            windows_data.append(window_dict)
            total_duration += window.duration_seconds
            max_elevation = max(max_elevation, window.max_elevation_deg)
        
        response = {
            "city_info": {
                "name": city_info["name"],
                "country": city_info["country"],
                "latitude": city_info["latitude"],
                "longitude": city_info["longitude"],
                "altitude": city_info["altitude"],
                "type": city_info["type"]
            },
            "summary": {
                "total_windows": len(access_windows),
                "total_duration_seconds": total_duration,
                "total_duration_minutes": round(total_duration / 60.0, 2),
                "max_elevation_deg": round(max_elevation, 2),
                "calculation_parameters": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "elevation_threshold": elevation_threshold,
                    "time_step_seconds": time_step_seconds
                }
            },
            "access_windows": windows_data
        }
        
        logger.info(f"Found {len(access_windows)} access windows for {city_info['name']}, {city_info['country']}")
        return response
    
    def search_cities_by_name(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for cities by name or country."""
        return search_cities(query, limit)
    
    def parse_orbital_elements_from_text(self, text: str) -> Dict[str, Any]:
        """Parse natural language text to extract orbital parameters and generate TLE."""
        return self.tle_generator.parse_and_generate_tle(text)
    
    def calculate_access_windows_from_orbital_elements(
        self,
        orbital_text: str,
        latitude: float,
        longitude: float,
        start_time: datetime,
        end_time: datetime,
        elevation_threshold: float = 10.0,
        time_step_seconds: int = 30
    ) -> Dict[str, Any]:
        """Calculate access windows using orbital elements from natural language text."""
        
        # Parse the orbital elements and generate TLE
        orbital_result = self.parse_orbital_elements_from_text(orbital_text)
        
        # Extract TLE lines
        tle_line1 = orbital_result['tle']['line1']
        tle_line2 = orbital_result['tle']['line2']
        
        # Calculate access windows using the generated TLE
        access_windows = self.calculate_access_windows(
            latitude=latitude,
            longitude=longitude,
            tle_line1=tle_line1,
            tle_line2=tle_line2,
            start_time=start_time,
            end_time=end_time,
            elevation_threshold=elevation_threshold,
            time_step_seconds=time_step_seconds
        )
        
        # Format response with orbital elements information
        windows_data = []
        total_duration = 0.0
        max_elevation = 0.0
        
        for window in access_windows:
            window_dict = {
                "aos_time": window.aos_time.isoformat(),
                "los_time": window.los_time.isoformat(),
                "culmination_time": window.culmination_time.isoformat(),
                "duration_seconds": window.duration_seconds,
                "duration_minutes": round(window.duration_seconds / 60.0, 2),
                "max_elevation_deg": round(window.max_elevation_deg, 2),
                "aos_azimuth_deg": round(window.aos_azimuth_deg, 2),
                "los_azimuth_deg": round(window.los_azimuth_deg, 2),
                "culmination_azimuth_deg": round(window.culmination_azimuth_deg, 2),
                "ground_lighting": window.ground_lighting,
                "satellite_lighting": window.satellite_lighting
            }
            windows_data.append(window_dict)
            total_duration += window.duration_seconds
            max_elevation = max(max_elevation, window.max_elevation_deg)
        
        response = {
            "orbital_request": {
                "parsed_text": orbital_result['parsed_text'],
                "parsed_parameters": orbital_result['parsed_parameters'],
                "generated_tle": orbital_result['tle'],
                "orbital_summary": orbital_result['summary']
            },
            "ground_location": {
                "latitude": latitude,
                "longitude": longitude
            },
            "summary": {
                "total_windows": len(access_windows),
                "total_duration_seconds": total_duration,
                "total_duration_minutes": round(total_duration / 60.0, 2),
                "max_elevation_deg": round(max_elevation, 2),
                "calculation_parameters": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "elevation_threshold": elevation_threshold,
                    "time_step_seconds": time_step_seconds
                }
            },
            "access_windows": windows_data
        }
        
        logger.info(f"Found {len(access_windows)} access windows for orbital elements: {orbital_result['summary']}")
        return response
    
    def calculate_access_windows_from_orbital_elements_by_city(
        self,
        orbital_text: str,
        city_name: str,
        start_time: datetime,
        end_time: datetime,
        elevation_threshold: float = 10.0,
        time_step_seconds: int = 30
    ) -> Dict[str, Any]:
        """Calculate access windows using orbital elements and city lookup."""
        
        # Look up city coordinates
        city_info = lookup_city(city_name)
        if not city_info:
            # Try searching for partial matches
            search_results = search_cities(city_name, limit=5)
            if search_results:
                suggested_cities = [city["name"] for city in search_results]
                raise ValueError(f"City '{city_name}' not found. Did you mean one of: {', '.join(suggested_cities)}?")
            else:
                raise ValueError(f"City '{city_name}' not found in database")
        
        # Calculate access windows using orbital elements
        result = self.calculate_access_windows_from_orbital_elements(
            orbital_text=orbital_text,
            latitude=city_info["latitude"],
            longitude=city_info["longitude"],
            start_time=start_time,
            end_time=end_time,
            elevation_threshold=elevation_threshold,
            time_step_seconds=time_step_seconds
        )
        
        # Add city information to the response
        result["city_info"] = {
            "name": city_info["name"],
            "country": city_info["country"],
            "latitude": city_info["latitude"],
            "longitude": city_info["longitude"],
            "altitude": city_info["altitude"],
            "type": city_info["type"]
        }
        
        # Update ground location to use city info
        result["ground_location"] = result["city_info"]
        
        logger.info(f"Found {len(result['access_windows'])} access windows for orbital elements over {city_info['name']}, {city_info['country']}")
        return result
    
    def get_orbit_types(self) -> Dict[str, Any]:
        """Get available orbit types and their definitions."""
        return {
            "orbit_types": ORBIT_TYPES,
            "description": "Available orbit types for TLE generation from orbital elements"
        }
    
