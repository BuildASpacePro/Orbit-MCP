"""MCP Server for satellite orbital mechanics calculations."""

import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.models import (
    Tool,
    ListToolsResult,
    CallToolResult,
    TextContent,
    EmptyResult,
    InitializationOptions,
)
from mcp.types import (
    CallToolRequest,
    ListToolsRequest,
)
from mcp.server.stdio import stdio_server

from .satellite_calc import SatelliteCalculator, AccessWindow, AccessEvent, TLEValidationResult


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)


class SatelliteMCPServer:
    """MCP Server for satellite orbital mechanics calculations."""
    
    def __init__(self):
        """Initialize the MCP server."""
        self.server = Server("satellite-mcp-server")
        self.calculator = SatelliteCalculator()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up MCP server handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            """List available tools."""
            tools = [
                Tool(
                    name="calculate_access_windows",
                    description="Calculate satellite access windows over a ground station location",
                    inputSchema={
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
                ),
                Tool(
                    name="calculate_access_events",
                    description="Calculate detailed satellite access events for InfluxDB-compatible output",
                    inputSchema={
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
                ),
                Tool(
                    name="validate_tle",
                    description="Validate Two-Line Element data and extract orbital parameters",
                    inputSchema={
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
                )
            ]
            
            return ListToolsResult(tools=tools)
        
        @self.server.call_tool()
        async def handle_call_tool(request: CallToolRequest) -> CallToolResult:
            """Handle tool calls."""
            try:
                if request.params.name == "calculate_access_windows":
                    return await self._handle_calculate_access_windows(request.params.arguments)
                elif request.params.name == "calculate_access_events":
                    return await self._handle_calculate_access_events(request.params.arguments)
                elif request.params.name == "validate_tle":
                    return await self._handle_validate_tle(request.params.arguments)
                else:
                    raise ValueError(f"Unknown tool: {request.params.name}")
                    
            except Exception as e:
                logger.error(f"Error handling tool call {request.params.name}: {str(e)}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {str(e)}")],
                    isError=True
                )
    
    async def _handle_calculate_access_windows(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle calculate_access_windows tool call."""
        try:
            # Extract and validate arguments
            latitude = float(arguments["latitude"])
            longitude = float(arguments["longitude"])
            tle_line1 = str(arguments["tle_line1"])
            tle_line2 = str(arguments["tle_line2"])
            start_time = datetime.fromisoformat(arguments["start_time"].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(arguments["end_time"].replace('Z', '+00:00'))
            elevation_threshold = float(arguments.get("elevation_threshold", 10.0))
            time_step_seconds = int(arguments.get("time_step_seconds", 30))
            
            # Calculate access windows
            access_windows = self.calculator.calculate_access_windows(
                latitude=latitude,
                longitude=longitude,
                tle_line1=tle_line1,
                tle_line2=tle_line2,
                start_time=start_time,
                end_time=end_time,
                elevation_threshold=elevation_threshold,
                time_step_seconds=time_step_seconds
            )
            
            # Format response
            windows_data = []
            total_duration = 0.0
            max_elevation_overall = 0.0
            
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
                    "culmination_azimuth_deg": round(window.culmination_azimuth_deg, 2)
                }
                windows_data.append(window_dict)
                total_duration += window.duration_seconds
                max_elevation_overall = max(max_elevation_overall, window.max_elevation_deg)
            
            response = {
                "summary": {
                    "total_windows": len(access_windows),
                    "total_duration_seconds": total_duration,
                    "total_duration_minutes": round(total_duration / 60.0, 2),
                    "max_elevation_deg": round(max_elevation_overall, 2),
                    "calculation_parameters": {
                        "latitude": latitude,
                        "longitude": longitude,
                        "start_time": start_time.isoformat(),
                        "end_time": end_time.isoformat(),
                        "elevation_threshold": elevation_threshold,
                        "time_step_seconds": time_step_seconds
                    }
                },
                "access_windows": windows_data
            }
            
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(response, indent=2))]
            )
            
        except Exception as e:
            logger.error(f"Error in calculate_access_windows: {str(e)}")
            raise
    
    async def _handle_calculate_access_events(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle calculate_access_events tool call."""
        try:
            # Extract and validate arguments
            latitude = float(arguments["latitude"])
            longitude = float(arguments["longitude"])
            tle_line1 = str(arguments["tle_line1"])
            tle_line2 = str(arguments["tle_line2"])
            start_time = datetime.fromisoformat(arguments["start_time"].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(arguments["end_time"].replace('Z', '+00:00'))
            satellite_id = str(arguments["satellite_id"])
            location_id = str(arguments["location_id"])
            location_type = str(arguments.get("location_type", "ground_station"))
            elevation_threshold = float(arguments.get("elevation_threshold", 10.0))
            time_step_seconds = int(arguments.get("time_step_seconds", 30))
            
            # Calculate access events
            access_events = self.calculator.calculate_access_events(
                latitude=latitude,
                longitude=longitude,
                tle_line1=tle_line1,
                tle_line2=tle_line2,
                start_time=start_time,
                end_time=end_time,
                satellite_id=satellite_id,
                location_id=location_id,
                location_type=location_type,
                elevation_threshold=elevation_threshold,
                time_step_seconds=time_step_seconds
            )
            
            # Format for InfluxDB
            influxdb_events = self.calculator.format_for_influxdb(access_events)
            
            # Format response
            events_data = []
            for event in access_events:
                event_dict = {
                    "timestamp": event.timestamp.isoformat(),
                    "event_type": event.event_type,
                    "elevation_deg": round(event.elevation_deg, 2),
                    "azimuth_deg": round(event.azimuth_deg, 2),
                    "satellite_id": event.satellite_id,
                    "location_id": event.location_id,
                    "location_type": event.location_type
                }
                events_data.append(event_dict)
            
            response = {
                "summary": {
                    "total_events": len(access_events),
                    "aos_events": len([e for e in access_events if e.event_type == "aos"]),
                    "culmination_events": len([e for e in access_events if e.event_type == "culmination"]),
                    "los_events": len([e for e in access_events if e.event_type == "los"]),
                    "calculation_parameters": {
                        "latitude": latitude,
                        "longitude": longitude,
                        "satellite_id": satellite_id,
                        "location_id": location_id,
                        "location_type": location_type,
                        "start_time": start_time.isoformat(),
                        "end_time": end_time.isoformat(),
                        "elevation_threshold": elevation_threshold,
                        "time_step_seconds": time_step_seconds
                    }
                },
                "events": events_data,
                "influxdb_format": influxdb_events
            }
            
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(response, indent=2))]
            )
            
        except Exception as e:
            logger.error(f"Error in calculate_access_events: {str(e)}")
            raise
    
    async def _handle_validate_tle(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle validate_tle tool call."""
        try:
            # Extract arguments
            tle_line1 = str(arguments["tle_line1"])
            tle_line2 = str(arguments["tle_line2"])
            
            # Validate TLE
            validation_result = self.calculator.validate_tle(tle_line1, tle_line2)
            
            # Format response
            response = {
                "is_valid": validation_result.is_valid,
                "errors": validation_result.errors,
                "orbital_parameters": {}
            }
            
            if validation_result.is_valid:
                response["orbital_parameters"] = {
                    "satellite_number": validation_result.satellite_number,
                    "classification": validation_result.classification,
                    "international_designator": validation_result.international_designator,
                    "epoch": validation_result.epoch.isoformat() if validation_result.epoch else None,
                    "mean_motion_rev_per_day": validation_result.mean_motion,
                    "eccentricity": validation_result.eccentricity,
                    "inclination_deg": validation_result.inclination_deg,
                    "orbital_period_minutes": round(validation_result.orbital_period_minutes, 2) if validation_result.orbital_period_minutes else None
                }
            
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(response, indent=2))]
            )
            
        except Exception as e:
            logger.error(f"Error in validate_tle: {str(e)}")
            raise
    
    async def run(self):
        """Run the MCP server."""
        logger.info("Starting Satellite MCP Server")
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="satellite-mcp-server",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )


async def main():
    """Main entry point."""
    server = SatelliteMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())