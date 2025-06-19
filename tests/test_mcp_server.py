"""Tests for MCP server functionality."""

import pytest
import asyncio
import json
from unittest.mock import MagicMock, patch
try:
    from unittest.mock import AsyncMock
except ImportError:
    # AsyncMock not available in Python < 3.8
    class AsyncMock(MagicMock):
        async def __call__(self, *args, **kwargs):
            return super(AsyncMock, self).__call__(*args, **kwargs)
from datetime import datetime, timezone

from mcp.types import CallToolRequest, CallToolRequestParams
from mcp.server.models import CallToolResult, TextContent

from src.mcp_server import SatelliteMCPServer
from tests.sample_data import (
    ISS_TLE, INVALID_TLE, GROUND_STATIONS, TEST_TIME_WINDOWS
)


class TestMCPServerTools:
    """Test MCP server tool functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.server = SatelliteMCPServer()
        self.mit_station = GROUND_STATIONS["MIT"]
        self.single_day = TEST_TIME_WINDOWS["SINGLE_DAY"]
    
    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Test listing available tools."""
        # Mock the list_tools handler
        list_tools_handler = None
        for handler in self.server.server._list_tools_handlers:
            list_tools_handler = handler
            break
        
        assert list_tools_handler is not None
        result = await list_tools_handler()
        
        assert hasattr(result, 'tools')
        assert len(result.tools) == 3
        
        tool_names = [tool.name for tool in result.tools]
        assert "calculate_access_windows" in tool_names
        assert "calculate_bulk_access_windows" in tool_names
        assert "validate_tle" in tool_names
        
        # Validate tool schemas
        for tool in result.tools:
            assert hasattr(tool, 'inputSchema')
            assert 'type' in tool.inputSchema
            assert 'properties' in tool.inputSchema
            assert 'required' in tool.inputSchema
    
    @pytest.mark.asyncio
    async def test_calculate_access_windows_tool(self):
        """Test calculate_access_windows tool call."""
        arguments = {
            "latitude": self.mit_station["latitude"],
            "longitude": self.mit_station["longitude"],
            "tle_line1": ISS_TLE["line1"],
            "tle_line2": ISS_TLE["line2"],
            "start_time": self.single_day["start"].isoformat(),
            "end_time": self.single_day["end"].isoformat(),
            "elevation_threshold": 10.0,
            "time_step_seconds": 30
        }
        
        result = await self.server._handle_calculate_access_windows(arguments)
        
        assert isinstance(result, CallToolResult)
        assert len(result.content) == 1
        assert isinstance(result.content[0], TextContent)
        
        # Parse JSON response
        response_data = json.loads(result.content[0].text)
        
        # Validate response structure
        assert "summary" in response_data
        assert "access_windows" in response_data
        
        summary = response_data["summary"]
        assert "total_windows" in summary
        assert "total_duration_seconds" in summary
        assert "total_duration_minutes" in summary
        assert "max_elevation_deg" in summary
        assert "calculation_parameters" in summary
        
        # Validate access windows
        windows = response_data["access_windows"]
        assert isinstance(windows, list)
        
        for window in windows:
            assert "aos_time" in window
            assert "los_time" in window
            assert "culmination_time" in window
            assert "duration_seconds" in window
            assert "max_elevation_deg" in window
            
            # Validate time format
            datetime.fromisoformat(window["aos_time"])
            datetime.fromisoformat(window["los_time"])
            datetime.fromisoformat(window["culmination_time"])
    
    @pytest.mark.asyncio
    async def test_calculate_access_events_tool(self):
        """Test calculate_access_events tool call."""
        arguments = {
            "latitude": self.mit_station["latitude"],
            "longitude": self.mit_station["longitude"],
            "tle_line1": ISS_TLE["line1"],
            "tle_line2": ISS_TLE["line2"],
            "start_time": self.single_day["start"].isoformat(),
            "end_time": self.single_day["end"].isoformat(),
            "satellite_id": ISS_TLE["satellite_id"],
            "location_id": self.mit_station["location_id"],
            "location_type": self.mit_station["location_type"],
            "elevation_threshold": 10.0,
            "time_step_seconds": 30
        }
        
        result = await self.server._handle_calculate_access_events(arguments)
        
        assert isinstance(result, CallToolResult)
        assert len(result.content) == 1
        assert isinstance(result.content[0], TextContent)
        
        # Parse JSON response
        response_data = json.loads(result.content[0].text)
        
        # Validate response structure
        assert "summary" in response_data
        assert "events" in response_data
        assert "influxdb_format" in response_data
        
        summary = response_data["summary"]
        assert "total_events" in summary
        assert "aos_events" in summary
        assert "culmination_events" in summary
        assert "los_events" in summary
        
        # Validate events
        events = response_data["events"]
        assert isinstance(events, list)
        
        for event in events:
            assert "timestamp" in event
            assert "event_type" in event
            assert "elevation_deg" in event
            assert "azimuth_deg" in event
            assert "satellite_id" in event
            assert "location_id" in event
            
            assert event["event_type"] in ["aos", "culmination", "los"]
            assert event["satellite_id"] == ISS_TLE["satellite_id"]
            assert event["location_id"] == self.mit_station["location_id"]
        
        # Validate InfluxDB format
        influx_events = response_data["influxdb_format"]
        assert isinstance(influx_events, list)
        assert len(influx_events) == len(events)
        
        for influx_event in influx_events:
            assert "measurement" in influx_event
            assert "tags" in influx_event
            assert "fields" in influx_event
            assert "time" in influx_event
    
    @pytest.mark.asyncio
    async def test_validate_tle_tool_valid(self):
        """Test validate_tle tool with valid TLE."""
        arguments = {
            "tle_line1": ISS_TLE["line1"],
            "tle_line2": ISS_TLE["line2"]
        }
        
        result = await self.server._handle_validate_tle(arguments)
        
        assert isinstance(result, CallToolResult)
        assert len(result.content) == 1
        assert isinstance(result.content[0], TextContent)
        
        # Parse JSON response
        response_data = json.loads(result.content[0].text)
        
        # Validate response structure
        assert "is_valid" in response_data
        assert "errors" in response_data
        assert "orbital_parameters" in response_data
        
        assert response_data["is_valid"] is True
        assert len(response_data["errors"]) == 0
        
        params = response_data["orbital_parameters"]
        assert "satellite_number" in params
        assert "classification" in params
        assert "international_designator" in params
        assert "epoch" in params
        assert "mean_motion_rev_per_day" in params
        assert "eccentricity" in params
        assert "inclination_deg" in params
        assert "orbital_period_minutes" in params
        
        assert params["satellite_number"] == 25544
    
    @pytest.mark.asyncio
    async def test_validate_tle_tool_invalid(self):
        """Test validate_tle tool with invalid TLE."""
        arguments = {
            "tle_line1": INVALID_TLE["line1"],
            "tle_line2": INVALID_TLE["line2"]
        }
        
        result = await self.server._handle_validate_tle(arguments)
        
        assert isinstance(result, CallToolResult)
        assert len(result.content) == 1
        assert isinstance(result.content[0], TextContent)
        
        # Parse JSON response
        response_data = json.loads(result.content[0].text)
        
        # Validate response structure
        assert "is_valid" in response_data
        assert "errors" in response_data
        
        assert response_data["is_valid"] is False
        assert len(response_data["errors"]) > 0
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_arguments(self):
        """Test error handling with invalid arguments."""
        # Missing required argument
        arguments = {
            "latitude": self.mit_station["latitude"],
            # Missing longitude
            "tle_line1": ISS_TLE["line1"],
            "tle_line2": ISS_TLE["line2"],
            "start_time": self.single_day["start"].isoformat(),
            "end_time": self.single_day["end"].isoformat()
        }
        
        with pytest.raises(Exception):
            await self.server._handle_calculate_access_windows(arguments)
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_tle(self):
        """Test error handling with invalid TLE data."""
        arguments = {
            "latitude": self.mit_station["latitude"],
            "longitude": self.mit_station["longitude"],
            "tle_line1": "invalid tle line 1",
            "tle_line2": "invalid tle line 2",
            "start_time": self.single_day["start"].isoformat(),
            "end_time": self.single_day["end"].isoformat()
        }
        
        with pytest.raises(Exception):
            await self.server._handle_calculate_access_windows(arguments)
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_coordinates(self):
        """Test error handling with invalid coordinates."""
        arguments = {
            "latitude": 95.0,  # Invalid latitude
            "longitude": self.mit_station["longitude"],
            "tle_line1": ISS_TLE["line1"],
            "tle_line2": ISS_TLE["line2"],
            "start_time": self.single_day["start"].isoformat(),
            "end_time": self.single_day["end"].isoformat()
        }
        
        with pytest.raises(Exception):
            await self.server._handle_calculate_access_windows(arguments)
    
    @pytest.mark.asyncio
    async def test_iso_time_parsing(self):
        """Test ISO time string parsing with different formats."""
        test_times = [
            "2024-01-01T00:00:00Z",
            "2024-01-01T00:00:00+00:00",
            "2024-01-01T00:00:00.000Z",
            "2024-01-01T00:00:00.000+00:00"
        ]
        
        for time_str in test_times:
            arguments = {
                "latitude": self.mit_station["latitude"],
                "longitude": self.mit_station["longitude"],
                "tle_line1": ISS_TLE["line1"],
                "tle_line2": ISS_TLE["line2"],
                "start_time": time_str,
                "end_time": "2024-01-01T23:59:59Z"
            }
            
            # Should not raise exception
            result = await self.server._handle_calculate_access_windows(arguments)
            assert isinstance(result, CallToolResult)


class TestMCPServerIntegration:
    """Test MCP server integration and protocol handling."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.server = SatelliteMCPServer()
    
    @pytest.mark.asyncio
    async def test_full_tool_call_workflow(self):
        """Test complete tool call workflow."""
        # Create mock request
        request = CallToolRequest(
            params=CallToolRequestParams(
                name="calculate_access_windows",
                arguments={
                    "latitude": GROUND_STATIONS["MIT"]["latitude"],
                    "longitude": GROUND_STATIONS["MIT"]["longitude"],
                    "tle_line1": ISS_TLE["line1"],
                    "tle_line2": ISS_TLE["line2"],
                    "start_time": TEST_TIME_WINDOWS["SINGLE_DAY"]["start"].isoformat(),
                    "end_time": TEST_TIME_WINDOWS["SINGLE_DAY"]["end"].isoformat()
                }
            )
        )
        
        # Find the call tool handler
        call_tool_handler = None
        for handler in self.server.server._call_tool_handlers:
            call_tool_handler = handler
            break
        
        assert call_tool_handler is not None
        result = await call_tool_handler(request)
        
        assert isinstance(result, CallToolResult)
        assert not hasattr(result, 'isError') or not result.isError
        assert len(result.content) == 1
        
        # Validate JSON response
        response_text = result.content[0].text
        response_data = json.loads(response_text)
        assert "summary" in response_data
        assert "access_windows" in response_data
    
    @pytest.mark.asyncio
    async def test_unknown_tool_error(self):
        """Test error handling for unknown tool."""
        request = CallToolRequest(
            params=CallToolRequestParams(
                name="unknown_tool",
                arguments={}
            )
        )
        
        # Find the call tool handler
        call_tool_handler = None
        for handler in self.server.server._call_tool_handlers:
            call_tool_handler = handler
            break
        
        result = await call_tool_handler(request)
        
        assert isinstance(result, CallToolResult)
        assert result.isError is True
        assert "Unknown tool" in result.content[0].text