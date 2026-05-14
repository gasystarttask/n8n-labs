
#!/usr/bin/env python3
"""Test script for MCP EEG Dataset Server"""


import asyncio
import sys
import httpx

def print_response(label, response):
    if response.status_code == 200:
        try:
            result = response.json()
            print(f"✓ {label}: {result}")
            return result
        except Exception:
            print(f"✓ {label} (non-JSON): {response.text}")
            return None
    else:
        print(f"✗ {label} failed: HTTP {response.status_code} {response.text}")
        return None

async def post_tool(client, server_url, tool, arguments, label):
    try:
        response = await client.post(
            f"{server_url}/mcp/execute",
            json={"tool": tool, "arguments": arguments},
        )
        return print_response(label, response)
    except Exception as e:
        print(f"✗ {label} error: {e}")
        return None

async def test_eeg_dataset_server(server_url: str = "http://localhost:8012"):
    """Test MCP EEG Dataset Server endpoints"""

    async with httpx.AsyncClient(timeout=30.0) as client:
        print("Testing MCP EEG Dataset Server...")
        print(f"Base URL: {server_url}\n")

        # Health endpoint
        try:
            response = await client.get(f"{server_url}/health")
            print_response("Health check", response)
        except Exception as e:
            print(f"✗ Health check failed: {e}")
            return

        # List tools
        try:
            response = await client.get(f"{server_url}/mcp/tools")
            tools = print_response("Available tools", response)
            if tools and 'tools' in tools:
                for tool in tools["tools"]:
                    print(f"  - {tool['name']}: {tool['description']}")
        except Exception as e:
            print(f"✗ Failed to list tools: {e}")

        # getMany
        print("\n--- Testing getMany ---")
        getmany_result = await post_tool(client, server_url, "getMany", {"skip": 0, "limit": 2}, "getMany")

        # getEegAdultAnalysis
        print("\n--- Testing getEegAdultAnalysis ---")
        eeg_id = ""
        if getmany_result and getmany_result.get("success"):
            records = getmany_result.get("result", [])
            if records and isinstance(records, list) and '_id' in records[0]:
                eeg_id = records[0]['_id']
            elif records and isinstance(records, list) and len(records) > 0:
                eeg_id = records[0].get('_id', eeg_id)
        await post_tool(client, server_url, "getEegAdultAnalysis", {"eeg_id": eeg_id}, "getEegAdultAnalysis")

        # getEegAdultInterpretation
        print("\n--- Testing getEegAdultInterpretation ---")
        eeg_id = ""
        if getmany_result and getmany_result.get("success"):
            records = getmany_result.get("result", [])
            if records and isinstance(records, list) and '_id' in records[0]:
                eeg_id = records[0]['_id']
            elif records and isinstance(records, list) and len(records) > 0:
                eeg_id = records[0].get('_id', eeg_id)
        await post_tool(client, server_url, "getEegAdultInterpretation", {"eeg_id": eeg_id}, "getEegAdultInterpretation")

        # getEegAdultObservation
        print("\n--- Testing getEegAdultObservation ---")
        eeg_id = ""
        if getmany_result and getmany_result.get("success"):
            records = getmany_result.get("result", [])
            if records and isinstance(records, list) and '_id' in records[0]:
                eeg_id = records[0]['_id']
            elif records and isinstance(records, list) and len(records) > 0:
                eeg_id = records[0].get('_id', eeg_id)
        await post_tool(client, server_url, "getEegAdultObservation", {"eeg_id": eeg_id}, "getEegAdultObservation")

        # getEegAdultRecording
        print("\n--- Testing getEegAdultRecording ---")
        eeg_id = ""
        if getmany_result and getmany_result.get("success"):
            records = getmany_result.get("result", [])
            if records and isinstance(records, list) and '_id' in records[0]:
                eeg_id = records[0]['_id']
            elif records and isinstance(records, list) and len(records) > 0:
                eeg_id = records[0].get('_id', eeg_id)
        await post_tool(client, server_url, "getEegAdultRecording", {"eeg_id": eeg_id}, "getEegAdultRecording")
        
        # countEegRecords
        print("\n--- Testing countEegRecords ---")
        await post_tool(client, server_url, "countEegRecords", {}, "countEegRecords")

        # find
        print("\n--- Testing find ---")
        await post_tool(client, server_url, "find", {"keyword": "test", "skip": 0, "limit": 2}, "find")

        print("\n✅ MCP EEG Dataset Server tests completed!")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        server_url = sys.argv[1]
    else:
        server_url = "http://localhost:8012"

    asyncio.run(test_eeg_dataset_server(server_url))
