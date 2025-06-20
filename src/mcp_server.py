"""Simple JSON-RPC 2.0 MCP server for satellite orbital mechanics calculations."""

import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from dataclasses import asdict
import numpy as np

from .satellite_calc import SatelliteCalculator


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)


class NumpyJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle numpy types."""
    
    def default(self, obj):
        if isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


class SatelliteMCPServer:
    """MCP-compatible server for satellite calculations."""
    
    def __init__(self):
        """Initialize the server."""
        self.calculator = SatelliteCalculator()
        self.server_info = {
            "name": "satellite-mcp-server",
            "version": "1.0.0",
            "description": "Satellite orbital mechanics calculations with natural language processing"
        }
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle JSON-RPC 2.0 request."""
        try:
            method = request.get("method")
            request_id = request.get("id")
            params = request.get("params", {})
            
            # Route to appropriate handler
            if method == "initialize":
                result = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": self.server_info
                }
            elif method == "tools/list":
                result = {
                    "tools": [
                        {
                            "name": "calculate_access_windows",
                            "description": "Calculate satellite access windows with lighting information",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "latitude": {"type": "number", "description": "Ground station latitude"},
                                    "longitude": {"type": "number", "description": "Ground station longitude"},
                                    "altitude": {"type": "number", "description": "Ground station altitude in meters", "default": 0},
                                    "tle_line1": {"type": "string", "description": "TLE Line 1"},
                                    "tle_line2": {"type": "string", "description": "TLE Line 2"},
                                    "start_time": {"type": "string", "description": "Start time ISO 8601"},
                                    "end_time": {"type": "string", "description": "End time ISO 8601"},
                                    "elevation_threshold": {"type": "number", "default": 10.0, "description": "Minimum elevation angle in degrees"}
                                },
                                "required": ["latitude", "longitude", "tle_line1", "tle_line2", "start_time", "end_time"]
                            }
                        },
                        {
                            "name": "calculate_bulk_access_windows",
                            "description": "Calculate access windows from CSV data",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "locations_csv": {"type": "string", "description": "CSV content with locations"},
                                    "satellites_csv": {"type": "string", "description": "CSV content with satellites"},
                                    "start_time": {"type": "string", "description": "Start time ISO 8601"},
                                    "end_time": {"type": "string", "description": "End time ISO 8601"},
                                    "elevation_threshold": {"type": "number", "default": 10.0, "description": "Minimum elevation angle in degrees"}
                                },
                                "required": ["locations_csv", "satellites_csv", "start_time", "end_time"]
                            }
                        },
                        {
                            "name": "calculate_access_windows_by_city",
                            "description": "Calculate satellite access windows for a city by name lookup",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "city_name": {"type": "string", "description": "Name of the city"},
                                    "tle_line1": {"type": "string", "description": "TLE Line 1"},
                                    "tle_line2": {"type": "string", "description": "TLE Line 2"},
                                    "start_time": {"type": "string", "description": "Start time ISO 8601"},
                                    "end_time": {"type": "string", "description": "End time ISO 8601"},
                                    "elevation_threshold": {"type": "number", "default": 10.0, "description": "Minimum elevation angle in degrees"}
                                },
                                "required": ["city_name", "tle_line1", "tle_line2", "start_time", "end_time"]
                            }
                        },
                        {
                            "name": "search_cities",
                            "description": "Search cities database functionality",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "query": {"type": "string", "description": "City search query"},
                                    "limit": {"type": "integer", "default": 10, "description": "Maximum number of results"}
                                },
                                "required": ["query"]
                            }
                        },
                        {
                            "name": "validate_tle",
                            "description": "TLE data validation",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "tle_line1": {"type": "string", "description": "TLE Line 1"},
                                    "tle_line2": {"type": "string", "description": "TLE Line 2"}
                                },
                                "required": ["tle_line1", "tle_line2"]
                            }
                        },
                        {
                            "name": "calculate_access_windows_from_orbital_elements",
                            "description": "Calculate access windows from orbital parameters (inclination, altitude) with near-circular eccentricity",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "latitude": {"type": "number", "description": "Ground station latitude"},
                                    "longitude": {"type": "number", "description": "Ground station longitude"},
                                    "altitude_ground": {"type": "number", "description": "Ground station altitude in meters", "default": 0},
                                    "inclination": {"type": "number", "description": "Orbital inclination in degrees"},
                                    "altitude_km": {"type": "number", "description": "Satellite altitude in kilometers"},
                                    "start_time": {"type": "string", "description": "Start time ISO 8601"},
                                    "end_time": {"type": "string", "description": "End time ISO 8601"},
                                    "elevation_threshold": {"type": "number", "default": 10.0, "description": "Minimum elevation angle in degrees"},
                                    "eccentricity": {"type": "number", "default": 0.0001, "description": "Orbital eccentricity (defaults to near-circular)"},
                                    "raan": {"type": "number", "default": 0.0, "description": "Right Ascension of Ascending Node in degrees"},
                                    "arg_perigee": {"type": "number", "default": 0.0, "description": "Argument of perigee in degrees"},
                                    "mean_anomaly": {"type": "number", "default": 0.0, "description": "Mean anomaly in degrees"}
                                },
                                "required": ["latitude", "longitude", "inclination", "altitude_km", "start_time", "end_time"]
                            }
                        },
                        {
                            "name": "calculate_access_windows_from_orbital_elements_by_city",
                            "description": "Calculate access windows from orbital parameters for a city by name",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "city_name": {"type": "string", "description": "Name of the city"},
                                    "inclination": {"type": "number", "description": "Orbital inclination in degrees"},
                                    "altitude_km": {"type": "number", "description": "Satellite altitude in kilometers"},
                                    "start_time": {"type": "string", "description": "Start time ISO 8601"},
                                    "end_time": {"type": "string", "description": "End time ISO 8601"},
                                    "elevation_threshold": {"type": "number", "default": 10.0, "description": "Minimum elevation angle in degrees"},
                                    "eccentricity": {"type": "number", "default": 0.0001, "description": "Orbital eccentricity (defaults to near-circular)"},
                                    "raan": {"type": "number", "default": 0.0, "description": "Right Ascension of Ascending Node in degrees"},
                                    "arg_perigee": {"type": "number", "default": 0.0, "description": "Argument of perigee in degrees"},
                                    "mean_anomaly": {"type": "number", "default": 0.0, "description": "Mean anomaly in degrees"}
                                },
                                "required": ["city_name", "inclination", "altitude_km", "start_time", "end_time"]
                            }
                        },
                        {
                            "name": "calculate_satellite_to_satellite_access_windows",
                            "description": "Calculate access windows between satellites with Earth occlusion checking",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "satellites": {
                                        "type": "array",
                                        "description": "Array of satellite TLE data",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "name": {"type": "string", "description": "Satellite name"},
                                                "tle_line1": {"type": "string", "description": "TLE Line 1"},
                                                "tle_line2": {"type": "string", "description": "TLE Line 2"}
                                            },
                                            "required": ["name", "tle_line1", "tle_line2"]
                                        },
                                        "minItems": 2
                                    },
                                    "start_time": {"type": "string", "description": "Start time ISO 8601"},
                                    "end_time": {"type": "string", "description": "End time ISO 8601"},
                                    "min_separation_deg": {"type": "number", "default": 0.0, "description": "Minimum angular separation in degrees"},
                                    "time_step_seconds": {"type": "integer", "default": 30, "description": "Time step for calculations in seconds"}
                                },
                                "required": ["satellites", "start_time", "end_time"]
                            }
                        },
                        {
                            "name": "calculate_bulk_satellite_to_satellite_access_windows",
                            "description": "Calculate access windows between satellites from CSV data",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "satellites_csv": {"type": "string", "description": "CSV content with satellite TLE data (columns: name, tle_line1, tle_line2)"},
                                    "start_time": {"type": "string", "description": "Start time ISO 8601"},
                                    "end_time": {"type": "string", "description": "End time ISO 8601"},
                                    "min_separation_deg": {"type": "number", "default": 0.0, "description": "Minimum angular separation in degrees"},
                                    "time_step_seconds": {"type": "integer", "default": 30, "description": "Time step for calculations in seconds"}
                                },
                                "required": ["satellites_csv", "start_time", "end_time"]
                            }
                        }
                    ]
                }
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                if tool_name == "calculate_access_windows":
                    result = await self._calculate_access_windows(arguments)
                elif tool_name == "calculate_bulk_access_windows":
                    result = await self._calculate_bulk_access_windows(arguments)
                elif tool_name == "calculate_access_windows_by_city":
                    result = await self._calculate_access_windows_by_city(arguments)
                elif tool_name == "search_cities":
                    result = await self._search_cities(arguments)
                elif tool_name == "validate_tle":
                    result = await self._validate_tle(arguments)
                elif tool_name == "calculate_access_windows_from_orbital_elements":
                    result = await self._calculate_access_windows_from_orbital_elements(arguments)
                elif tool_name == "calculate_access_windows_from_orbital_elements_by_city":
                    result = await self._calculate_access_windows_from_orbital_elements_by_city(arguments)
                elif tool_name == "calculate_satellite_to_satellite_access_windows":
                    result = await self._calculate_satellite_to_satellite_access_windows(arguments)
                elif tool_name == "calculate_bulk_satellite_to_satellite_access_windows":
                    result = await self._calculate_bulk_satellite_to_satellite_access_windows(arguments)
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}
                    }
            else:
                return {
                    "jsonrpc": "2.0", 
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Unknown method: {method}"}
                }
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {"code": -32603, "message": "Internal error", "data": str(e)}
            }
    
    async def _calculate_access_windows_by_city(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate access windows by city."""
        city_name = arguments["city_name"]
        tle_line1 = arguments["tle_line1"]
        tle_line2 = arguments["tle_line2"]
        start_time = datetime.fromisoformat(arguments["start_time"].replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(arguments["end_time"].replace('Z', '+00:00'))
        elevation_threshold = arguments.get("elevation_threshold", 10.0)
        
        city_results = self.calculator.calculate_access_windows_by_city(
            city_name=city_name,
            tle_line1=tle_line1,
            tle_line2=tle_line2,
            start_time=start_time,
            end_time=end_time,
            elevation_threshold=elevation_threshold
        )
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(city_results, indent=2, cls=NumpyJSONEncoder)
                }
            ]
        }
    
    async def _calculate_access_windows(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate basic access windows."""
        latitude = arguments["latitude"]
        longitude = arguments["longitude"]
        altitude = arguments.get("altitude", 0)
        tle_line1 = arguments["tle_line1"]
        tle_line2 = arguments["tle_line2"]
        start_time = datetime.fromisoformat(arguments["start_time"].replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(arguments["end_time"].replace('Z', '+00:00'))
        elevation_threshold = arguments.get("elevation_threshold", 10.0)
        
        access_windows = self.calculator.calculate_access_windows(
            latitude=latitude,
            longitude=longitude,
            altitude=altitude,
            tle_line1=tle_line1,
            tle_line2=tle_line2,
            start_time=start_time,
            end_time=end_time,
            elevation_threshold=elevation_threshold
        )
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(access_windows, indent=2, cls=NumpyJSONEncoder)
                }
            ]
        }
    
    async def _calculate_bulk_access_windows(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate bulk access windows from CSV data."""
        locations_csv = arguments["locations_csv"]
        satellites_csv = arguments["satellites_csv"]
        start_time = datetime.fromisoformat(arguments["start_time"].replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(arguments["end_time"].replace('Z', '+00:00'))
        elevation_threshold = arguments.get("elevation_threshold", 10.0)
        
        bulk_results = self.calculator.calculate_bulk_access_windows(
            locations_csv=locations_csv,
            satellites_csv=satellites_csv,
            start_time=start_time,
            end_time=end_time,
            elevation_threshold=elevation_threshold
        )
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(bulk_results, indent=2, cls=NumpyJSONEncoder)
                }
            ]
        }
    
    async def _validate_tle(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Validate TLE data."""
        tle_line1 = arguments["tle_line1"]
        tle_line2 = arguments["tle_line2"]
        
        validation_result = self.calculator.validate_tle(tle_line1, tle_line2)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(asdict(validation_result), indent=2, cls=NumpyJSONEncoder)
                }
            ]
        }
    
    async def _search_cities(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Search cities."""
        query = arguments["query"]
        limit = arguments.get("limit", 10)
        
        search_results = self.calculator.search_cities_by_name(query, limit)
        response = {
            "query": query,
            "total_results": len(search_results),
            "cities": search_results
        }
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(response, indent=2, cls=NumpyJSONEncoder)
                }
            ]
        }
    
    async def _calculate_access_windows_from_orbital_elements(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate access windows from orbital elements."""
        latitude = arguments["latitude"]
        longitude = arguments["longitude"]
        altitude_ground = arguments.get("altitude_ground", 0)
        inclination = arguments["inclination"]
        altitude_km = arguments["altitude_km"]
        start_time = datetime.fromisoformat(arguments["start_time"].replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(arguments["end_time"].replace('Z', '+00:00'))
        elevation_threshold = arguments.get("elevation_threshold", 10.0)
        eccentricity = arguments.get("eccentricity", 0.0001)
        raan = arguments.get("raan", 0.0)
        arg_perigee = arguments.get("arg_perigee", 0.0)
        mean_anomaly = arguments.get("mean_anomaly", 0.0)
        
        # Construct orbital description text
        orbital_text = f"Satellite at {altitude_km} km altitude with {inclination} degree inclination"
        if eccentricity > 0.001:
            orbital_text += f" and {eccentricity} eccentricity"
        if raan != 0.0:
            orbital_text += f", RAAN {raan} degrees"
        if arg_perigee != 0.0:
            orbital_text += f", argument of perigee {arg_perigee} degrees"
        if mean_anomaly != 0.0:
            orbital_text += f", mean anomaly {mean_anomaly} degrees"
        
        access_windows = self.calculator.calculate_access_windows_from_orbital_elements(
            orbital_text=orbital_text,
            latitude=latitude,
            longitude=longitude,
            start_time=start_time,
            end_time=end_time,
            elevation_threshold=elevation_threshold
        )
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(access_windows, indent=2, cls=NumpyJSONEncoder)
                }
            ]
        }
    
    async def _calculate_access_windows_from_orbital_elements_by_city(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate access windows from orbital elements by city."""
        city_name = arguments["city_name"]
        inclination = arguments["inclination"]
        altitude_km = arguments["altitude_km"]
        start_time = datetime.fromisoformat(arguments["start_time"].replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(arguments["end_time"].replace('Z', '+00:00'))
        elevation_threshold = arguments.get("elevation_threshold", 10.0)
        eccentricity = arguments.get("eccentricity", 0.0001)
        raan = arguments.get("raan", 0.0)
        arg_perigee = arguments.get("arg_perigee", 0.0)
        mean_anomaly = arguments.get("mean_anomaly", 0.0)
        
        # Construct orbital description text
        orbital_text = f"Satellite at {altitude_km} km altitude with {inclination} degree inclination"
        if eccentricity > 0.001:
            orbital_text += f" and {eccentricity} eccentricity"
        if raan != 0.0:
            orbital_text += f", RAAN {raan} degrees"
        if arg_perigee != 0.0:
            orbital_text += f", argument of perigee {arg_perigee} degrees"
        if mean_anomaly != 0.0:
            orbital_text += f", mean anomaly {mean_anomaly} degrees"
        
        city_results = self.calculator.calculate_access_windows_from_orbital_elements_by_city(
            orbital_text=orbital_text,
            city_name=city_name,
            start_time=start_time,
            end_time=end_time,
            elevation_threshold=elevation_threshold
        )
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(city_results, indent=2, cls=NumpyJSONEncoder)
                }
            ]
        }
    
    async def _calculate_satellite_to_satellite_access_windows(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate access windows between satellites."""
        satellites = arguments["satellites"]
        start_time = datetime.fromisoformat(arguments["start_time"].replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(arguments["end_time"].replace('Z', '+00:00'))
        min_separation_deg = arguments.get("min_separation_deg", 0.0)
        time_step_seconds = arguments.get("time_step_seconds", 30)
        
        # Convert to format expected by calculator
        satellite_tles = []
        for sat in satellites:
            satellite_tles.append({
                'name': sat['name'],
                'tle_line1': sat['tle_line1'],
                'tle_line2': sat['tle_line2']
            })
        
        results = self.calculator.calculate_satellite_to_satellite_access_windows(
            satellite_tles=satellite_tles,
            start_time=start_time,
            end_time=end_time,
            min_separation_deg=min_separation_deg,
            time_step_seconds=time_step_seconds
        )
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(results, indent=2, cls=NumpyJSONEncoder)
                }
            ]
        }
    
    async def _calculate_bulk_satellite_to_satellite_access_windows(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate bulk access windows between satellites from CSV."""
        satellites_csv = arguments["satellites_csv"]
        start_time = datetime.fromisoformat(arguments["start_time"].replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(arguments["end_time"].replace('Z', '+00:00'))
        min_separation_deg = arguments.get("min_separation_deg", 0.0)
        time_step_seconds = arguments.get("time_step_seconds", 30)
        
        # Parse satellites from CSV
        satellite_tles = self.calculator.parse_satellites_from_csv_content(satellites_csv)
        
        if len(satellite_tles) < 2:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "error": "Need at least 2 satellites in CSV for inter-satellite calculations",
                            "satellites_found": len(satellite_tles)
                        }, indent=2)
                    }
                ]
            }
        
        results = self.calculator.calculate_satellite_to_satellite_access_windows(
            satellite_tles=satellite_tles,
            start_time=start_time,
            end_time=end_time,
            min_separation_deg=min_separation_deg,
            time_step_seconds=time_step_seconds
        )
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(results, indent=2, cls=NumpyJSONEncoder)
                }
            ]
        }
    
    async def run(self):
        """Run the server."""
        logger.info("Starting Satellite MCP Server")
        
        try:
            while True:
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
                    print(json.dumps(response, cls=NumpyJSONEncoder), flush=True)
                    
                except json.JSONDecodeError as e:
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": -32700, "message": "Parse error", "data": str(e)}
                    }
                    print(json.dumps(error_response, cls=NumpyJSONEncoder), flush=True)
                
        except KeyboardInterrupt:
            logger.info("Server stopped")
        except Exception as e:
            logger.error(f"Server error: {str(e)}")


async def main():
    """Main entry point."""
    server = SatelliteMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())