"""
Quick test script to verify the server is running and test the API.

Run this after starting the server to test the endpoints.
"""

import requests
import json
import time
import sys


def test_health():
    """Test the health endpoint."""
    print("=" * 80)
    print("Testing Health Endpoint")
    print("=" * 80)
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        response.raise_for_status()
        data = response.json()
        print(f"OK Status: {data.get('status')}")
        print(f"OK Version: {data.get('version')}")
        print(f"OK Timestamp: {data.get('timestamp')}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Health check failed: {e}")
        return False


def test_root():
    """Test the root endpoint."""
    print("\n" + "=" * 80)
    print("Testing Root Endpoint")
    print("=" * 80)
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        response.raise_for_status()
        data = response.json()
        print(f"OK API Name: {data.get('name')}")
        print(f"OK Version: {data.get('version')}")
        print(f"OK Endpoints available:")
        for endpoint, path in data.get('endpoints', {}).items():
            print(f"   - {endpoint}: {path}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Root endpoint failed: {e}")
        return False


def test_analysis():
    """Test the analysis endpoint with a simple query."""
    print("\n" + "=" * 80)
    print("Testing Analysis Endpoint")
    print("=" * 80)
    print("Query: 'Analyze revenue trends'")
    print("This will stream results...\n")
    
    try:
        response = requests.post(
            "http://localhost:8000/run",
            json={
                "query": "Analyze revenue trends for Q1 and Q2",
                "max_iterations": 5,
                "message_window": 8
            },
            stream=True,
            timeout=30
        )
        response.raise_for_status()
        
        print("Streaming response:")
        print("-" * 80)
        event_count = 0
        for line in response.iter_lines():
            if line:
                try:
                    event = json.loads(line.decode('utf-8'))
                    event_type = event.get("type", "unknown")
                    event_count += 1
                    
                    if event_type == "start":
                        print(f"[START] {event.get('data', '')}")
                    elif event_type == "decision":
                        print(f"[SUPERVISOR] -> {event.get('decision')}")
                        print(f"   Reasoning: {event.get('reasoning', 'N/A')}")
                    elif event_type == "action":
                        agent = event.get("agent", "Unknown")
                        output = event.get("output", "")[:100]  # Truncate long outputs
                        print(f"[{agent}] {output}...")
                    elif event_type == "finish":
                        print(f"[FINISH] {event.get('data', '')}")
                    elif event_type == "error":
                        print(f"[ERROR] {event.get('error', 'Unknown error')}")
                    
                except json.JSONDecodeError:
                    print(f"⚠️  Could not parse: {line.decode('utf-8')[:50]}")
        
        print("-" * 80)
        print(f"OK Received {event_count} events")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Analysis endpoint failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("Enterprise Data Analyst Agent - Server Test")
    print("=" * 80)
    print("\nMake sure the server is running on http://localhost:8000")
    print("If not, start it with: python main.py\n")
    
    # Wait a moment for user to read
    time.sleep(1)
    
    results = []
    
    # Test health endpoint
    results.append(("Health Check", test_health()))
    
    # Test root endpoint
    results.append(("Root Endpoint", test_root()))
    
    # Ask user if they want to test analysis (it uses API credits)
    print("\n" + "=" * 80)
    response = input("Test analysis endpoint? (This will use API credits) [y/N]: ")
    if response.lower() == 'y':
        results.append(("Analysis Endpoint", test_analysis()))
    else:
        print("Skipping analysis test (requires API credits)")
        results.append(("Analysis Endpoint", None))
    
    # Summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    for test_name, result in results:
        if result is None:
            status = "[SKIPPED]"
        elif result:
            status = "[PASSED]"
        else:
            status = "[FAILED]"
        print(f"{status} - {test_name}")
    
    print("\n" + "=" * 80)
    print("🌐 Access the interactive API documentation at:")
    print("   http://localhost:8000/docs")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()

