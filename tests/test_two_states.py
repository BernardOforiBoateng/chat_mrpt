"""
Quick test: Compare one working state vs one problematic state
"""

import requests
import json

BASE_URL = "https://d225ar6c86586s.cloudfront.net"

def test_state(state_name: str, csv_file: str):
    """Test a single state's full workflow."""

    print(f"\n{'='*50}")
    print(f"Testing: {state_name}")
    print(f"{'='*50}")

    # Upload
    with open(csv_file, 'rb') as f:
        files = {'file': (f'{state_name.lower()}_tpr.csv', f, 'text/csv')}
        response = requests.post(f"{BASE_URL}/api/data-analysis/upload", files=files)

    if response.status_code != 200:
        print(f"✗ Upload failed: {response.status_code}")
        return False

    result = response.json()
    session_id = result.get('session_id')
    print(f"✓ Session: {session_id}")

    # Initial TPR request
    response = requests.post(
        f"{BASE_URL}/api/v1/data-analysis/chat",
        json={'message': 'Run TPR analysis', 'session_id': session_id},
        headers={'Content-Type': 'application/json'}
    )

    print(f"Initial response status: {response.status_code}")

    # Select primary
    response = requests.post(
        f"{BASE_URL}/api/v1/data-analysis/chat",
        json={'message': 'primary', 'session_id': session_id},
        headers={'Content-Type': 'application/json'}
    )

    print(f"Primary selection status: {response.status_code}")

    # Select u5
    response = requests.post(
        f"{BASE_URL}/api/v1/data-analysis/chat",
        json={'message': 'u5', 'session_id': session_id},
        headers={'Content-Type': 'application/json'}
    )

    print(f"U5 selection status: {response.status_code}")

    if response.status_code == 200:
        final = response.json()

        # Check for visualization
        viz = final.get('visualizations', [])
        if viz:
            print(f"✓ VISUALIZATION GENERATED: {len(viz)} items")
            for v in viz:
                html_size = len(v.get('html_content', ''))
                print(f"  - {v.get('type')}: {v.get('title')} ({html_size} chars)")
        else:
            print("✗ NO VISUALIZATION IN RESPONSE")

        # Check response text
        msg = final.get('message', '')
        if 'tpr_distribution_map.html' in msg:
            print("✓ Map file mentioned in response")
        if 'calculated' in msg.lower():
            print("✓ TPR calculation completed")

        print(f"\nResponse preview: {msg[:200]}...")

    return True

# Test one working state
print("\n" + "="*60)
print("TESTING WORKING STATE: ADAMAWA")
print("="*60)
test_state('Adamawa', '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/www/all_states_cleaned/adamawa_tpr_cleaned.csv')

# Test one problematic state
print("\n" + "="*60)
print("TESTING PROBLEMATIC STATE: PLATEAU")
print("="*60)
test_state('Plateau', '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/www/all_states_cleaned/plateau_tpr_cleaned.csv')