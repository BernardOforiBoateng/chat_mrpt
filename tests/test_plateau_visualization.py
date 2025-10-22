"""
Test Plateau state TPR visualization generation
"""

import requests
import json
import time
import sys

# Production URL
BASE_URL = "https://d225ar6c86586s.cloudfront.net"

def test_plateau_upload():
    """Test uploading Plateau data and check visualization generation."""

    print("Testing Plateau state TPR visualization...")

    # Step 1: Upload Plateau data
    with open('/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/www/all_states_cleaned/plateau_tpr_cleaned.csv', 'rb') as f:
        files = {'file': ('plateau_tpr_cleaned.csv', f, 'text/csv')}
        response = requests.post(f"{BASE_URL}/api/data-analysis/upload", files=files)

    if response.status_code != 200:
        print(f"Upload failed: {response.status_code}")
        print(response.text)
        return False

    result = response.json()
    session_id = result.get('session_id')
    print(f"Upload successful. Session ID: {session_id}")

    # Step 2: Trigger TPR workflow
    chat_data = {
        'message': 'Show me the TPR distribution map for Plateau state',
        'session_id': session_id
    }

    print("Triggering TPR workflow...")
    response = requests.post(
        f"{BASE_URL}/api/v1/data-analysis/chat",
        json=chat_data,
        headers={'Content-Type': 'application/json'}
    )

    if response.status_code != 200:
        print(f"Chat request failed: {response.status_code}")
        print(response.text)
        return False

    chat_result = response.json()

    # Check response for visualizations
    response_text = chat_result.get('message', '')
    print("\n=== Response Analysis ===")
    print(f"Response length: {len(response_text)} chars")

    # Check for visualization references
    if 'visualization' in response_text.lower() or 'map' in response_text.lower():
        print("✓ Visualization mentioned in response")
    else:
        print("✗ No visualization mentioned")

    # Check for stored visualizations
    visualizations = chat_result.get('visualizations', [])
    if visualizations:
        print(f"✓ {len(visualizations)} visualization(s) generated")
        for viz in visualizations:
            print(f"  - Type: {viz.get('type')}")
            print(f"  - Title: {viz.get('title')}")
            if viz.get('html_content'):
                print(f"    HTML content: {len(viz.get('html_content'))} chars")
            else:
                print("    WARNING: No HTML content!")
    else:
        print("✗ No visualizations stored")

    # Extract snippet of response
    print("\n=== Response Snippet ===")
    print(response_text[:500] if response_text else "No response text")

    return True

if __name__ == "__main__":
    success = test_plateau_upload()
    sys.exit(0 if success else 1)