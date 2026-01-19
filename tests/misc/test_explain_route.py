import requests
import json

# Test the explain_visualization endpoint on correct port
url = "http://localhost:8000/explain_visualization"

payload = {
    "viz_path": "945c9128-ca4d-4116-a927-3e85e5357dd1/tpr_distribution_map.html",
    "viz_type": "tpr_map",
    "title": "Test Map"
}

headers = {
    "Content-Type": "application/json",
    "Cookie": "session=test_session_123"
}

print("Testing /explain_visualization endpoint on port 8000...")
print(f"Payload: {json.dumps(payload, indent=2)}")

try:
    response = requests.post(url, json=payload, headers=headers)
    print(f"\nStatus Code: {response.status_code}")
    data = response.json()
    print(f"Response Status: {data.get('status')}")
    if 'explanation' in data:
        exp = data['explanation']
        print(f"Explanation length: {len(exp)}")
        print(f"First 300 chars: {exp[:300]}")
        if "This visualization shows malaria risk analysis" in exp:
            print("\n⚠️  FALLBACK MESSAGE DETECTED!")
        else:
            print("\n✅ REAL AI EXPLANATION!")
except Exception as e:
    print(f"Error: {e}")
