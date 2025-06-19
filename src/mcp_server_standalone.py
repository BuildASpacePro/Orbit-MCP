"""Standalone MCP-compatible server for satellite orbital mechanics calculations.

This version works with Python 3.7+ and implements JSON-RPC 2.0 protocol
without requiring the official MCP library.
"""

import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
import traceback

from .satellite_calc import SatelliteCalculator


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)


class JSONRPCError(Exception):
    """JSON-RPC 2.0 error."""
    
    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)


class SatelliteMCPServer:
    """Standalone MCP-compatible server for satellite calculations."""
    
    def __init__(self):
        """Initialize the server."""
        self.calculator = SatelliteCalculator()
        self.server_info = {
            "name": "satellite-mcp-server",
            "version": "1.0.0",
            "description": "Satellite orbital mechanics calculations"
        }
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle JSON-RPC 2.0 request."""
        try:
            # Validate JSON-RPC 2.0 format
            if request.get("jsonrpc") != "2.0":
                raise JSONRPCError(-32600, "Invalid Request", "Missing or invalid jsonrpc field")
            
            method = request.get("method")
            if not method:
                raise JSONRPCError(-32600, "Invalid Request", "Missing method field")
            
            request_id = request.get("id")
            params = request.get("params", {})
            
            # Route to appropriate handler
            if method == "initialize":
                result = await self._handle_initialize(params)
            elif method == "tools/list":
                result = await self._handle_list_tools(params)
            elif method == "tools/call":
                result = await self._handle_call_tool(params)
            else:
                raise JSONRPCError(-32601, "Method not found", f"Unknown method: {method}")
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
            
        except JSONRPCError as e:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "data": e.data
                }
            }
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}\n{traceback.format_exc()}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                    "data": str(e)
                }
            }
    
    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialization request."""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "logging": {}
            },
            "serverInfo": self.server_info
        }
    
    async def _handle_list_tools(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle list tools request."""
        tools = [
            {
                "name": "calculate_access_windows",
                "description": "Calculate satellite access windows over a ground station location",
                "inputSchema": {
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
                            "minLength": 69,
                            "maxLength": 69,
                            "description": "TLE Line 1 in standard NORAD format"
                        },
                        "tle_line2": {
                            "type": "string",
                            "minLength": 69,
                            "maxLength": 69,
                            "description": "TLE Line 2 in standard NORAD format"
                        },
                        "start_time": {
                            "type": "string",
                            "description": "Start time in ISO 8601 format (UTC)"
                        },
                        "end_time": {
                            "type": "string",
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
            },
            {
                "name": "calculate_access_events",
                "description": "Calculate detailed satellite access events for InfluxDB-compatible output",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "latitude": {"type": "number", "minimum": -90, "maximum": 90},
                        "longitude": {"type": "number", "minimum": -180, "maximum": 180},
                        "tle_line1": {"type": "string", "minLength": 69, "maxLength": 69},
                        "tle_line2": {"type": "string", "minLength": 69, "maxLength": 69},
                        "start_time": {"type": "string"},
                        "end_time": {"type": "string"},
                        "satellite_id": {"type": "string", "minLength": 1},
                        "location_id": {"type": "string", "minLength": 1},
                        "location_type": {"type": "string", "default": "ground_station"},
                        "elevation_threshold": {"type": "number", "minimum": 0, "maximum": 90, "default": 10.0},
                        "time_step_seconds": {"type": "integer", "minimum": 1, "maximum": 300, "default": 30}
                    },
                    "required": ["latitude", "longitude", "tle_line1", "tle_line2", 
                               "start_time", "end_time", "satellite_id", "location_id"]
                }
            },
            {
                "name": "validate_tle",
                "description": "Validate Two-Line Element data and extract orbital parameters",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "tle_line1": {"type": "string", "minLength": 69, "maxLength": 69},
                        "tle_line2": {"type": "string", "minLength": 69, "maxLength": 69}
                    },
                    "required": ["tle_line1", "tle_line2"]
                }
            }
        ]
        
        return {"tools": tools}
    
    async def _handle_call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "calculate_access_windows":
            return await self._handle_calculate_access_windows(arguments)
        elif tool_name == "calculate_access_events":
            return await self._handle_calculate_access_events(arguments)
        elif tool_name == "validate_tle":
            return await self._handle_validate_tle(arguments)
        else:
            raise JSONRPCError(-32601, "Method not found", f"Unknown tool: {tool_name}")
    
    async def _handle_calculate_access_windows(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
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
            
            return {"content": [{"type": "text", "text": json.dumps(response, indent=2)}]}
            
        except Exception as e:
            logger.error(f"Error in calculate_access_windows: {str(e)}")
            raise JSONRPCError(-32603, "Internal error", str(e))
    
    async def _handle_calculate_access_events(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle calculate_access_events tool call."""
        try:
            # Extract arguments (similar to access_windows)
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
            
            # Format for InfluxDB
            influxdb_events = self.calculator.format_for_influxdb(access_events)
            
            response = {
                "summary": {
                    "total_events": len(access_events),
                    "aos_events": len([e for e in access_events if e.event_type == "aos"]),
                    "culmination_events": len([e for e in access_events if e.event_type == "culmination"]),
                    "los_events": len([e for e in access_events if e.event_type == "los"])
                },
                "events": events_data,
                "influxdb_format": influxdb_events
            }
            
            return {"content": [{"type": "text", "text": json.dumps(response, indent=2)}]}
            
        except Exception as e:
            logger.error(f"Error in calculate_access_events: {str(e)}")
            raise JSONRPCError(-32603, "Internal error", str(e))
    
    async def _handle_validate_tle(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle validate_tle tool call."""
        try:
            tle_line1 = str(arguments["tle_line1"])
            tle_line2 = str(arguments["tle_line2"])
            
            validation_result = self.calculator.validate_tle(tle_line1, tle_line2)
            
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
            
            return {"content": [{"type": "text", "text": json.dumps(response, indent=2)}]}
            
        except Exception as e:
            logger.error(f"Error in validate_tle: {str(e)}")
            raise JSONRPCError(-32603, "Internal error", str(e))
    
    async def run(self):
        """Run the server with stdio transport."""
        logger.info("Starting Satellite MCP Server (Standalone)")
        
        try:
            while True:
                # Read JSON-RPC request from stdin
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                
                if not line:
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                try:
                    request = json.loads(line)
                    response = await self.handle_request(request)
                    
                    # Write response to stdout
                    print(json.dumps(response), flush=True)
                    
                except json.JSONDecodeError as e:
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": "Parse error",
                            "data": str(e)
                        }
                    }
                    print(json.dumps(error_response), flush=True)
                
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.error(f"Server error: {str(e)}")


async def main():
    """Main entry point."""
    server = SatelliteMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())