"""
Test TPR generation for multiple states to find pattern
"""

import requests
import time

BASE_URL = "https://d225ar6c86586s.cloudfront.net"

states_to_test = [
    # Working states
    ("Adamawa", "adamawa"),
    ("Cross River", "cross_river"),
    ("Sokoto", "sokoto"),
    ("Zamfara", "zamfara"),
    # Problematic states
    ("Benue", "benue"),
    ("Ebonyi", "ebonyi"),
    ("Kebbi", "kebbi"),
    ("Nasarawa", "nasarawa"),
    ("Plateau", "plateau"),
]

results = []

for state_name, file_prefix in states_to_test:
    print(f"\n{'='*50}")
    print(f"Testing: {state_name}")

    # Upload
    csv_file = f'/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/www/all_states_cleaned/{file_prefix}_tpr_cleaned.csv'
    with open(csv_file, 'rb') as f:
        files = {'file': (f'{file_prefix}_tpr.csv', f, 'text/csv')}
        response = requests.post(f"{BASE_URL}/api/data-analysis/upload", files=files)

    if response.status_code != 200:
        print(f"✗ Upload failed")
        continue

    session_id = response.json().get('session_id')
    print(f"Session: {session_id}")

    # Run TPR workflow
    requests.post(f"{BASE_URL}/api/v1/data-analysis/chat",
                  json={'message': 'Run TPR analysis', 'session_id': session_id})

    requests.post(f"{BASE_URL}/api/v1/data-analysis/chat",
                  json={'message': 'all', 'session_id': session_id})

    response = requests.post(f"{BASE_URL}/api/v1/data-analysis/chat",
                              json={'message': 'all', 'session_id': session_id})

    if response.status_code == 200:
        result = response.json()
        viz = result.get('visualizations', [])

        # Test direct file access
        map_url = f"{BASE_URL}/serve_viz_file/{session_id}/tpr_distribution_map.html"
        map_response = requests.get(map_url)

        file_exists = map_response.status_code == 200
        file_size = len(map_response.text) if file_exists else 0

        results.append({
            'state': state_name,
            'session': session_id,
            'viz_count': len(viz),
            'file_exists': file_exists,
            'file_size': file_size,
            'has_state_in_html': state_name in map_response.text if file_exists else False
        })

        print(f"Viz count: {len(viz)}")
        print(f"File exists: {file_exists}")
        print(f"File size: {file_size}")

    time.sleep(2)

print("\n" + "="*60)
print("SUMMARY")
print("="*60)

for r in results:
    status = "✅" if r['file_exists'] and r['file_size'] > 0 else "❌"
    print(f"{status} {r['state']:15} - File: {r['file_exists']}, Size: {r['file_size']:,}, Has State: {r['has_state_in_html']}")