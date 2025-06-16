"""Core satellite orbital mechanics calculations using Skyfield library."""

import logging
import math
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict

import numpy as np
from skyfield.api import Topos, load, EarthSatellite
from skyfield.timelib import Time
from skyfield.units import Angle


logger = logging.getLogger(__name__)


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


@dataclass
class AccessEvent:
    """Individual satellite access event (AOS, Culmination, LOS)."""
    timestamp: datetime
    event_type: str  # "aos", "culmination", "los"
    elevation_deg: float
    azimuth_deg: float
    satellite_id: str
    location_id: str
    location_type: str


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
                epoch = datetime(epoch_year, 1, 1, tzinfo=timezone.utc)
                epoch = epoch.replace(day=1) + np.timedelta64(int(epoch_day - 1), 'D')
                epoch = epoch + np.timedelta64(int((epoch_day % 1) * 24 * 3600 * 1000), 'ms')
                
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
                
                access_window = AccessWindow(
                    aos_time=aos_time,
                    los_time=los_time,
                    culmination_time=culmination_time,
                    duration_seconds=duration_seconds,
                    max_elevation_deg=max_elevation,
                    aos_azimuth_deg=azimuth.degrees[aos_idx],
                    los_azimuth_deg=azimuth.degrees[los_idx],
                    culmination_azimuth_deg=azimuth.degrees[culmination_idx]
                )
                
                access_windows.append(access_window)
        
        # Handle case where access window extends beyond end time
        if in_access and aos_idx is not None:
            los_idx = len(time_points) - 1
            aos_time = time_points[aos_idx].utc_datetime()
            los_time = time_points[los_idx].utc_datetime()
            culmination_time = time_points[culmination_idx].utc_datetime()
            
            duration_seconds = (los_time - aos_time).total_seconds()
            
            access_window = AccessWindow(
                aos_time=aos_time,
                los_time=los_time,
                culmination_time=culmination_time,
                duration_seconds=duration_seconds,
                max_elevation_deg=max_elevation,
                aos_azimuth_deg=azimuth.degrees[aos_idx],
                los_azimuth_deg=azimuth.degrees[los_idx],
                culmination_azimuth_deg=azimuth.degrees[culmination_idx]
            )
            
            access_windows.append(access_window)
        
        logger.info(f"Found {len(access_windows)} access windows")
        return access_windows
    
    def calculate_access_events(
        self,
        latitude: float,
        longitude: float,
        tle_line1: str,
        tle_line2: str,
        start_time: datetime,
        end_time: datetime,
        satellite_id: str,
        location_id: str,
        location_type: str = "ground_station",
        elevation_threshold: float = 10.0,
        time_step_seconds: int = 30
    ) -> List[AccessEvent]:
        """Calculate detailed access events for InfluxDB-compatible output."""
        
        access_windows = self.calculate_access_windows(
            latitude, longitude, tle_line1, tle_line2,
            start_time, end_time, elevation_threshold, time_step_seconds
        )
        
        events = []
        
        for window in access_windows:
            # AOS event
            events.append(AccessEvent(
                timestamp=window.aos_time,
                event_type="aos",
                elevation_deg=elevation_threshold,  # Approximation at threshold
                azimuth_deg=window.aos_azimuth_deg,
                satellite_id=satellite_id,
                location_id=location_id,
                location_type=location_type
            ))
            
            # Culmination event
            events.append(AccessEvent(
                timestamp=window.culmination_time,
                event_type="culmination",
                elevation_deg=window.max_elevation_deg,
                azimuth_deg=window.culmination_azimuth_deg,
                satellite_id=satellite_id,
                location_id=location_id,
                location_type=location_type
            ))
            
            # LOS event
            events.append(AccessEvent(
                timestamp=window.los_time,
                event_type="los",
                elevation_deg=elevation_threshold,  # Approximation at threshold
                azimuth_deg=window.los_azimuth_deg,
                satellite_id=satellite_id,
                location_id=location_id,
                location_type=location_type
            ))
        
        # Sort events by timestamp
        events.sort(key=lambda x: x.timestamp)
        
        logger.info(f"Generated {len(events)} access events")
        return events
    
    def format_for_influxdb(self, events: List[AccessEvent]) -> List[Dict[str, Any]]:
        """Format access events for InfluxDB line protocol."""
        formatted_events = []
        
        for event in events:
            formatted_event = {
                "measurement": "satellite_access",
                "tags": {
                    "satellite_id": event.satellite_id,
                    "location_id": event.location_id,
                    "location_type": event.location_type,
                    "event_type": event.event_type
                },
                "fields": {
                    "elevation_deg": event.elevation_deg,
                    "azimuth_deg": event.azimuth_deg
                },
                "time": event.timestamp.isoformat()
            }
            formatted_events.append(formatted_event)
        
        return formatted_events