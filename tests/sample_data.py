"""Sample test data for satellite calculations."""

from datetime import datetime, timezone

# Test TLE data
ISS_TLE = {
    "line1": "1 25544U 98067A   24001.12345678  .00001234  00000-0  12345-4 0  9992",
    "line2": "2 25544  51.6400 123.4567 0001234  12.3456 347.6543 15.48919999123458",
    "name": "ISS (ZARYA)",
    "satellite_id": "25544"
}

# Additional test satellites
NOAA_18_TLE = {
    "line1": "1 28654U 05018A   24001.50000000  .00000123  00000-0  45678-4 0  9991",
    "line2": "2 28654  99.0500 100.0000 0012345  45.0000 315.0000 14.12345678987650",
    "name": "NOAA-18",
    "satellite_id": "28654"
}

HUBBLE_TLE = {
    "line1": "1 20580U 90037B   24001.75000000  .00000678  00000-0  23456-4 0  9998",
    "line2": "2 20580  28.4700  50.0000 0005678  30.0000 330.0000 15.09876543210986",
    "name": "HST",
    "satellite_id": "20580"
}

# Invalid TLE for testing
INVALID_TLE = {
    "line1": "1 25544U 98067A   24001.12345678  .00001234  00000-0  12345-4 0  9998",  # Wrong checksum
    "line2": "2 25544  51.6400 123.4567 0001234  12.3456 347.6543 15.48919999123456",
    "name": "Invalid TLE",
    "satellite_id": "25544"
}

# Test ground stations
GROUND_STATIONS = {
    "MIT": {
        "name": "MIT Lincoln Laboratory",
        "latitude": 42.3601,
        "longitude": -71.0942,
        "elevation_m": 40,
        "location_id": "MIT_LL",
        "location_type": "ground_station"
    },
    "NASA_GODDARD": {
        "name": "NASA Goddard Space Flight Center",
        "latitude": 38.9917,
        "longitude": -76.8400,
        "elevation_m": 76,
        "location_id": "NASA_GSFC",
        "location_type": "ground_station"
    },
    "ESA_DARMSTADT": {
        "name": "ESA ESOC Darmstadt",
        "latitude": 49.8728,
        "longitude": 8.6512,
        "elevation_m": 119,
        "location_id": "ESA_ESOC",
        "location_type": "ground_station"
    },
    "NORTH_POLE": {
        "name": "North Pole Test Station",
        "latitude": 89.9,
        "longitude": 0.0,
        "elevation_m": 0,
        "location_id": "NORTH_POLE",
        "location_type": "test_station"
    },
    "EQUATOR": {
        "name": "Equator Test Station",
        "latitude": 0.0,
        "longitude": 0.0,
        "elevation_m": 0,
        "location_id": "EQUATOR",
        "location_type": "test_station"
    }
}

# Test time windows
TEST_TIME_WINDOWS = {
    "SINGLE_DAY": {
        "start": datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "end": datetime(2024, 1, 1, 23, 59, 59, tzinfo=timezone.utc),
        "description": "Single day test window"
    },
    "WEEK": {
        "start": datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "end": datetime(2024, 1, 7, 23, 59, 59, tzinfo=timezone.utc),
        "description": "One week test window"
    },
    "SHORT": {
        "start": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        "end": datetime(2024, 1, 1, 18, 0, 0, tzinfo=timezone.utc),
        "description": "6-hour test window"
    }
}

# Expected test results for validation
EXPECTED_RESULTS = {
    "ISS_MIT_SINGLE_DAY": {
        "min_passes": 3,  # ISS typically makes 3-6 passes per day
        "max_passes": 8,
        "min_duration_minutes": 2,  # Minimum reasonable pass duration
        "max_duration_minutes": 12,  # Maximum typical ISS pass
        "min_elevation": 10.0,  # Test threshold
        "max_elevation_range": (10.0, 90.0)
    }
}

# Test parameters
TEST_PARAMETERS = {
    "DEFAULT_ELEVATION_THRESHOLD": 10.0,
    "HIGH_ELEVATION_THRESHOLD": 30.0,
    "LOW_ELEVATION_THRESHOLD": 5.0,
    "DEFAULT_TIME_STEP": 30,
    "FINE_TIME_STEP": 10,
    "COARSE_TIME_STEP": 60
}