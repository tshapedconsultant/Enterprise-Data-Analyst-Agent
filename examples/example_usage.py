"""
Example usage of the Enterprise Data Analyst Agent API.

This script demonstrates how to interact with the API programmatically.
"""

import requests
import json
import sys


def run_analysis(query: str, base_url: str = "http://localhost:8000"):
    """
    Run an analysis query through the API and print streaming results.
    
    Args:
        query: User query to process
        base_url: Base URL of the API server
    """
    url = f"{base_url}/run"
    
    payload = {
        "query": query,
        "max_iterations": 10,
        "message_window": 8
    }
    
    print(f"Query: {query}\n")
    print("=" * 80)
    print("Streaming Results:\n")
    
    try:
        # Make streaming request
        response = requests.post(url, json=payload, stream=True)
        response.raise_for_status()
        
        # Process streaming NDJSON response
        for line in response.iter_lines():
            if line:
                try:
                    event = json.loads(line.decode('utf-8'))
                    event_type = event.get("type", "unknown")
                    
                    if event_type == "start":
                        print(f"🚀 {event.get('data', '')}\n")
                    
                    elif event_type == "decision":
                        agent = event.get("agent", "Unknown")
                        decision = event.get("decision", "Unknown")
                        reasoning = event.get("reasoning", "")
                        print(f"📊 [{agent}] Decision: {decision}")
                        print(f"   Reasoning: {reasoning}\n")
                    
                    elif event_type == "action":
                        agent = event.get("agent", "Unknown")
                        output = event.get("output", "")
                        iteration = event.get("iteration_count", 0)
                        print(f"⚙️  [{agent}] (Iteration {iteration})")
                        print(f"   Output: {output}\n")
                    
                    elif event_type == "finish":
                        print(f"✅ {event.get('data', 'Workflow completed')}\n")
                    
                    elif event_type == "error":
                        error = event.get("error", "Unknown error")
                        print(f"❌ Error: {error}\n")
                    
                except json.JSONDecodeError as e:
                    print(f"⚠️  Failed to parse event: {e}\n")
        
        print("=" * 80)
        print("Analysis complete!")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ API request failed: {e}")
        sys.exit(1)


def check_health(base_url: str = "http://localhost:8000"):
    """
    Check if the API server is healthy.
    
    Args:
        base_url: Base URL of the API server
        
    Returns:
        True if healthy, False otherwise
    """
    try:
        response = requests.get(f"{base_url}/health")
        response.raise_for_status()
        data = response.json()
        print(f"✅ Server is {data.get('status', 'unknown')}")
        print(f"   Version: {data.get('version', 'unknown')}")
        print(f"   Timestamp: {data.get('timestamp', 'unknown')}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Example usage of the Data Analyst Agent API")
    parser.add_argument(
        "query",
        nargs="?",
        default="Analyze the revenue trends for Q1 and Q2, then create a visualization",
        help="Query to process"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the API server"
    )
    parser.add_argument(
        "--health",
        action="store_true",
        help="Check API health instead of running analysis"
    )
    
    args = parser.parse_args()
    
    if args.health:
        check_health(args.url)
    else:
        # Check health first
        if not check_health(args.url):
            print("\n⚠️  Server appears to be down. Make sure the server is running:")
            print("   python main.py\n")
            sys.exit(1)
        
        print()
        run_analysis(args.query, args.url)

