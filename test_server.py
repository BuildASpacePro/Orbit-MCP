#!/usr/bin/env python3
"""Test script for the satellite MCP server."""

import json
import subprocess
import sys

def test_server():
    """Test the standalone MCP server."""
    
    # Test initialization
    init_request = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "id": 1,
        "params": {}
    }
    
    # Test list tools
    list_tools_request = {
        "jsonrpc": "2.0", 
        "method": "tools/list",
        "id": 2,
        "params": {}
    }
    
    # Test TLE validation
    validate_request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "id": 3,
        "params": {
            "name": "validate_tle",
            "arguments": {
                "tle_line1": "1 25544U 98067A   24001.12345678  .00001234  00000-0  12345-4 0  9999",
                "tle_line2": "2 25544  51.6400 123.4567 0001234  12.3456 347.6543 15.48919999123456"
            }
        }
    }
    
    try:
        # Start the server
        proc = subprocess.Popen(
            [sys.executable, "-m", "src.mcp_server_standalone"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )
        
        # Send test requests
        test_requests = [init_request, list_tools_request, validate_request]
        
        for request in test_requests:
            request_json = json.dumps(request) + "\n"
            proc.stdin.write(request_json)
            proc.stdin.flush()
            
            # Read response
            response_line = proc.stdout.readline()
            if response_line:
                try:
                    response = json.loads(response_line.strip())
                    print(f"✅ Request {request['method']}: SUCCESS")
                    if request['method'] == 'tools/list':
                        tools = response.get('result', {}).get('tools', [])
                        print(f"   Available tools: {[t['name'] for t in tools]}")
                    elif request['method'] == 'tools/call' and request['params']['name'] == 'validate_tle':
                        result = response.get('result', {})
                        if 'content' in result:
                            content = json.loads(result['content'][0]['text'])
                            print(f"   TLE Validation: {'VALID' if content['is_valid'] else 'INVALID'}")
                except json.JSONDecodeError as e:
                    print(f"❌ Request {request['method']}: JSON decode error - {e}")
            else:
                print(f"❌ Request {request['method']}: No response")
        
        proc.terminate()
        proc.wait(timeout=5)
        
        print("\n🎉 Server test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Server test failed: {e}")
        if 'proc' in locals():
            proc.terminate()
        return False

if __name__ == "__main__":
    success = test_server()
    sys.exit(0 if success else 1)