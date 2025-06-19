"""Tests for satellite calculation functions."""

import pytest
from datetime import datetime, timezone, timedelta
import numpy as np

from src.satellite_calc import SatelliteCalculator, AccessWindow, TLEValidationResult
from tests.sample_data import (
    ISS_TLE, NOAA_18_TLE, HUBBLE_TLE, INVALID_TLE,
    GROUND_STATIONS, TEST_TIME_WINDOWS, EXPECTED_RESULTS, TEST_PARAMETERS
)


class TestTLEValidation:
    """Test TLE validation functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = SatelliteCalculator()
    
    def test_valid_tle_iss(self):
        """Test validation of valid ISS TLE."""
        result = self.calculator.validate_tle(ISS_TLE["line1"], ISS_TLE["line2"])
        
        assert result.is_valid
        assert len(result.errors) == 0
        assert result.satellite_number == 25544
        assert result.classification == "U"
        assert result.international_designator == "98067A"
        assert result.mean_motion is not None
        assert result.eccentricity is not None
        assert result.inclination_deg is not None
        assert result.orbital_period_minutes is not None
        
        # Validate orbital parameter ranges
        assert 0 <= result.inclination_deg <= 180
        assert 0 <= result.eccentricity < 1
        assert result.mean_motion > 0
        assert result.orbital_period_minutes > 0
    
    def test_valid_tle_noaa18(self):
        """Test validation of valid NOAA-18 TLE."""
        result = self.calculator.validate_tle(NOAA_18_TLE["line1"], NOAA_18_TLE["line2"])
        
        assert result.is_valid
        assert result.satellite_number == 28654
        assert result.inclination_deg > 90  # Polar orbit
    
    def test_invalid_tle_checksum(self):
        """Test validation of invalid TLE with wrong checksum."""
        result = self.calculator.validate_tle(INVALID_TLE["line1"], INVALID_TLE["line2"])
        
        assert not result.is_valid
        assert len(result.errors) > 0
        assert any("checksum" in error.lower() for error in result.errors)
    
    def test_invalid_tle_length(self):
        """Test validation of TLE with wrong length."""
        short_line1 = "1 25544U 98067A"
        result = self.calculator.validate_tle(short_line1, ISS_TLE["line2"])
        
        assert not result.is_valid
        assert any("length" in error.lower() for error in result.errors)
    
    def test_invalid_tle_format(self):
        """Test validation of TLE with wrong format."""
        wrong_start = "2 25544U 98067A   24001.12345678  .00001234  00000-0  12345-4 0  9999"
        result = self.calculator.validate_tle(wrong_start, ISS_TLE["line2"])
        
        assert not result.is_valid
        assert any("must start with" in error for error in result.errors)


class TestAccessWindowCalculations:
    """Test access window calculation functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = SatelliteCalculator()
        self.mit_station = GROUND_STATIONS["MIT"]
        self.single_day = TEST_TIME_WINDOWS["SINGLE_DAY"]
    
    def test_calculate_iss_access_mit_single_day(self):
        """Test ISS access window calculation for MIT over single day."""
        windows = self.calculator.calculate_access_windows(
            latitude=self.mit_station["latitude"],
            longitude=self.mit_station["longitude"],
            tle_line1=ISS_TLE["line1"],
            tle_line2=ISS_TLE["line2"],
            start_time=self.single_day["start"],
            end_time=self.single_day["end"],
            elevation_threshold=TEST_PARAMETERS["DEFAULT_ELEVATION_THRESHOLD"]
        )
        
        # Validate results
        expected = EXPECTED_RESULTS["ISS_MIT_SINGLE_DAY"]
        assert expected["min_passes"] <= len(windows) <= expected["max_passes"]
        
        for window in windows:
            # Validate window structure
            assert isinstance(window, AccessWindow)
            assert window.aos_time < window.culmination_time < window.los_time
            assert window.duration_seconds > 0
            assert window.max_elevation_deg >= TEST_PARAMETERS["DEFAULT_ELEVATION_THRESHOLD"]
            
            # Validate reasonable durations
            duration_minutes = window.duration_seconds / 60.0
            assert expected["min_duration_minutes"] <= duration_minutes <= expected["max_duration_minutes"]
            
            # Validate elevation ranges
            assert expected["max_elevation_range"][0] <= window.max_elevation_deg <= expected["max_elevation_range"][1]
            
            # Validate azimuth ranges
            assert 0 <= window.aos_azimuth_deg <= 360
            assert 0 <= window.los_azimuth_deg <= 360
            assert 0 <= window.culmination_azimuth_deg <= 360
    
    def test_high_elevation_threshold(self):
        """Test access windows with high elevation threshold."""
        low_threshold_windows = self.calculator.calculate_access_windows(
            latitude=self.mit_station["latitude"],
            longitude=self.mit_station["longitude"],
            tle_line1=ISS_TLE["line1"],
            tle_line2=ISS_TLE["line2"],
            start_time=self.single_day["start"],
            end_time=self.single_day["end"],
            elevation_threshold=TEST_PARAMETERS["LOW_ELEVATION_THRESHOLD"]
        )
        
        high_threshold_windows = self.calculator.calculate_access_windows(
            latitude=self.mit_station["latitude"],
            longitude=self.mit_station["longitude"],
            tle_line1=ISS_TLE["line1"],
            tle_line2=ISS_TLE["line2"],
            start_time=self.single_day["start"],
            end_time=self.single_day["end"],
            elevation_threshold=TEST_PARAMETERS["HIGH_ELEVATION_THRESHOLD"]
        )
        
        # Higher threshold should result in fewer/shorter windows
        assert len(high_threshold_windows) <= len(low_threshold_windows)
        
        for window in high_threshold_windows:
            assert window.max_elevation_deg >= TEST_PARAMETERS["HIGH_ELEVATION_THRESHOLD"]
    
    def test_different_time_steps(self):
        """Test access windows with different time steps."""
        coarse_windows = self.calculator.calculate_access_windows(
            latitude=self.mit_station["latitude"],
            longitude=self.mit_station["longitude"],
            tle_line1=ISS_TLE["line1"],
            tle_line2=ISS_TLE["line2"],
            start_time=self.single_day["start"],
            end_time=self.single_day["end"],
            time_step_seconds=TEST_PARAMETERS["COARSE_TIME_STEP"]
        )
        
        fine_windows = self.calculator.calculate_access_windows(
            latitude=self.mit_station["latitude"],
            longitude=self.mit_station["longitude"],
            tle_line1=ISS_TLE["line1"],
            tle_line2=ISS_TLE["line2"],
            start_time=self.single_day["start"],
            end_time=self.single_day["end"],
            time_step_seconds=TEST_PARAMETERS["FINE_TIME_STEP"]
        )
        
        # Should have similar number of windows
        assert abs(len(coarse_windows) - len(fine_windows)) <= 2
    
    def test_polar_location(self):
        """Test access window calculation for polar location."""
        polar_station = GROUND_STATIONS["NORTH_POLE"]
        windows = self.calculator.calculate_access_windows(
            latitude=polar_station["latitude"],
            longitude=polar_station["longitude"],
            tle_line1=NOAA_18_TLE["line1"],  # Polar orbit satellite
            tle_line2=NOAA_18_TLE["line2"],
            start_time=self.single_day["start"],
            end_time=self.single_day["end"]
        )
        
        # Polar orbit should have good coverage at polar locations
        assert len(windows) > 0
        for window in windows:
            assert window.duration_seconds > 0
            assert window.max_elevation_deg >= TEST_PARAMETERS["DEFAULT_ELEVATION_THRESHOLD"]
    
    def test_input_validation(self):
        """Test input validation for access window calculation."""
        # Invalid latitude
        with pytest.raises(ValueError, match="Invalid latitude"):
            self.calculator.calculate_access_windows(
                latitude=95.0,  # Invalid
                longitude=0.0,
                tle_line1=ISS_TLE["line1"],
                tle_line2=ISS_TLE["line2"],
                start_time=self.single_day["start"],
                end_time=self.single_day["end"]
            )
        
        # Invalid longitude
        with pytest.raises(ValueError, match="Invalid longitude"):
            self.calculator.calculate_access_windows(
                latitude=0.0,
                longitude=185.0,  # Invalid
                tle_line1=ISS_TLE["line1"],
                tle_line2=ISS_TLE["line2"],
                start_time=self.single_day["start"],
                end_time=self.single_day["end"]
            )
        
        # Invalid time order
        with pytest.raises(ValueError, match="Start time must be before end time"):
            self.calculator.calculate_access_windows(
                latitude=0.0,
                longitude=0.0,
                tle_line1=ISS_TLE["line1"],
                tle_line2=ISS_TLE["line2"],
                start_time=self.single_day["end"],
                end_time=self.single_day["start"]
            )
        
        # Invalid elevation threshold
        with pytest.raises(ValueError, match="Invalid elevation threshold"):
            self.calculator.calculate_access_windows(
                latitude=0.0,
                longitude=0.0,
                tle_line1=ISS_TLE["line1"],
                tle_line2=ISS_TLE["line2"],
                start_time=self.single_day["start"],
                end_time=self.single_day["end"],
                elevation_threshold=95.0  # Invalid
            )


class TestLightingConditions:
    """Test lighting condition calculations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = SatelliteCalculator()
        self.mit_station = GROUND_STATIONS["MIT"]
        self.single_day = TEST_TIME_WINDOWS["SINGLE_DAY"]
    
    def test_ground_lighting_calculation(self):
        """Test ground lighting condition calculation."""
        # Test different times of day
        from datetime import datetime, timezone, timedelta
        
        # Test at different times
        test_times = [
            datetime(2024, 6, 21, 6, 0, 0, tzinfo=timezone.utc),   # Early morning
            datetime(2024, 6, 21, 12, 0, 0, tzinfo=timezone.utc),  # Noon
            datetime(2024, 6, 21, 18, 0, 0, tzinfo=timezone.utc),  # Evening
            datetime(2024, 6, 21, 0, 0, 0, tzinfo=timezone.utc),   # Midnight
        ]
        
        for test_time in test_times:
            lighting = self.calculator.calculate_ground_lighting(
                self.mit_station["latitude"],
                self.mit_station["longitude"],
                test_time
            )
            
            # Validate lighting structure
            assert "condition" in lighting
            assert "sun_elevation_deg" in lighting
            assert "sun_azimuth_deg" in lighting
            assert "civil_twilight" in lighting
            assert "nautical_twilight" in lighting
            assert "astronomical_twilight" in lighting
            assert "is_daylight" in lighting
            assert "is_night" in lighting
            
            # Validate condition values
            assert lighting["condition"] in [
                "daylight", "civil_twilight", "nautical_twilight", 
                "astronomical_twilight", "night"
            ]
            
            # Validate angle ranges
            assert -90 <= lighting["sun_elevation_deg"] <= 90
            assert 0 <= lighting["sun_azimuth_deg"] <= 360
    
    def test_access_windows_with_lighting(self):
        """Test that access windows include lighting information."""
        windows = self.calculator.calculate_access_windows(
            latitude=self.mit_station["latitude"],
            longitude=self.mit_station["longitude"],
            tle_line1=ISS_TLE["line1"],
            tle_line2=ISS_TLE["line2"],
            start_time=self.single_day["start"],
            end_time=self.single_day["end"]
        )
        
        assert len(windows) > 0
        
        for window in windows:
            # Validate that lighting information is present
            assert hasattr(window, 'ground_lighting')
            assert hasattr(window, 'satellite_lighting')
            
            # Validate ground lighting structure
            assert "condition" in window.ground_lighting
            assert "sun_elevation_deg" in window.ground_lighting
            
            # Validate satellite lighting structure
            assert "condition" in window.satellite_lighting
            assert "in_eclipse" in window.satellite_lighting
            assert "in_sunlight" in window.satellite_lighting


class TestPerformance:
    """Test calculation performance and edge cases."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = SatelliteCalculator()
    
    def test_week_long_calculation(self):
        """Test performance with week-long calculation window."""
        week_window = TEST_TIME_WINDOWS["WEEK"]
        mit_station = GROUND_STATIONS["MIT"]
        
        import time
        start_time = time.time()
        
        windows = self.calculator.calculate_access_windows(
            latitude=mit_station["latitude"],
            longitude=mit_station["longitude"],
            tle_line1=ISS_TLE["line1"],
            tle_line2=ISS_TLE["line2"],
            start_time=week_window["start"],
            end_time=week_window["end"]
        )
        
        end_time = time.time()
        calculation_time = end_time - start_time
        
        # Should complete in reasonable time (less than 30 seconds)
        assert calculation_time < 30.0
        
        # Should have reasonable number of passes for a week
        assert 15 <= len(windows) <= 50  # ISS makes ~15-16 orbits per day
    
    def test_edge_case_equator(self):
        """Test calculation at equator."""
        equator_station = GROUND_STATIONS["EQUATOR"]
        short_window = TEST_TIME_WINDOWS["SHORT"]
        
        windows = self.calculator.calculate_access_windows(
            latitude=equator_station["latitude"],
            longitude=equator_station["longitude"],
            tle_line1=ISS_TLE["line1"],
            tle_line2=ISS_TLE["line2"],
            start_time=short_window["start"],
            end_time=short_window["end"]
        )
        
        # Should handle equatorial location without errors
        assert isinstance(windows, list)
        for window in windows:
            assert window.duration_seconds > 0