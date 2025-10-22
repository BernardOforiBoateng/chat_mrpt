"""
Test if the visualization file serving route is working
"""

import requests

BASE_URL = "https://d225ar6c86586s.cloudfront.net"

# Test sessions from our previous test
test_sessions = [
    ("Adamawa", "ba10693f-d1fa-459b-aa2c-16283742bfe0"),
    ("Plateau", "6772e2e7-32e1-4032-af31-6f57edf31c08")
]

for state, session_id in test_sessions:
    url = f"{BASE_URL}/serve_viz_file/{session_id}/tpr_distribution_map.html"
    print(f"\n{'='*60}")
    print(f"Testing {state} visualization access")
    print(f"URL: {url}")

    response = requests.get(url)

    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type', 'Not specified')}")
    print(f"Content Length: {len(response.text)} chars")

    if response.status_code == 200:
        # Check if it's actually an HTML map
        if 'plotly' in response.text or 'Plotly' in response.text:
            print("✓ Contains Plotly visualization")
        if state in response.text:
            print(f"✓ Contains state name '{state}'")
        if 'TPR' in response.text or 'tpr' in response.text:
            print("✓ Contains TPR reference")

        # Check for map elements
        if 'mapbox' in response.text.lower():
            print("✓ Contains mapbox elements")

        # Sample first 500 chars
        print(f"\nHTML Preview:")
        print(response.text[:500] + "...")
    else:
        print(f"✗ Failed to retrieve: {response.text[:200]}")