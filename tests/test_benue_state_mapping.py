"""
Test why Benue state visualization is failing
"""

import requests
import json

# Production URL
BASE_URL = "https://d225ar6c86586s.cloudfront.net"

def test_benue_upload():
    """Test uploading Benue data and check visualization generation."""

    print("Testing Benue state TPR visualization...")

    # Step 1: Upload Benue data
    with open('/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/www/all_states_cleaned/benue_tpr_cleaned.csv', 'rb') as f:
        files = {'file': ('benue_tpr_cleaned.csv', f, 'text/csv')}
        response = requests.post(f"{BASE_URL}/api/data-analysis/upload", files=files)

    if response.status_code != 200:
        print(f"Upload failed: {response.status_code}")
        return False

    result = response.json()
    session_id = result.get('session_id')
    print(f"Upload successful. Session ID: {session_id}")

    # Step 2: Trigger TPR workflow with explicit calculation
    chat_data = {
        'message': 'Calculate TPR for all facilities and all age groups',
        'session_id': session_id
    }

    print("Triggering TPR calculation...")
    response = requests.post(
        f"{BASE_URL}/api/v1/data-analysis/chat",
        json=chat_data,
        headers={'Content-Type': 'application/json'}
    )

    if response.status_code != 200:
        print(f"Chat request failed: {response.status_code}")
        return False

    chat_result = response.json()
    response_text = chat_result.get('message', '')

    print("\n=== Response Analysis ===")

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
    else:
        print("✗ No visualizations stored")

    # Check if Benue is detected
    if 'benue' in response_text.lower():
        print("✓ Benue state detected in response")
    else:
        print("✗ Benue state NOT detected")

    print("\n=== Response Snippet ===")
    print(response_text[:800] if response_text else "No response text")

    return True

if __name__ == "__main__":
    test_benue_upload()