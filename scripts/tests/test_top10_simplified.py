"""
Simplified test for top 10 query
"""

import requests
import time
import re

STAGING_URL = "http://3.21.167.170:8080"

def test_top10():
    """Test top 10 query with simplified approach."""
    
    session_id = f'top10_{int(time.time())}'
    
    # Upload data
    print("Uploading data...")
    with open('www/adamawa_tpr_cleaned.csv', 'rb') as f:
        response = requests.post(
            f"{STAGING_URL}/api/data-analysis/upload",
            files={'file': ('test_data.csv', f, 'text/csv')},
            data={'session_id': session_id},
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"Upload failed: {response.status_code}")
            return
    
    print("✅ Data uploaded")
    time.sleep(2)
    
    # Test different phrasings
    queries = [
        "List the top 10 health facilities by number of records in the data",
        "Show me 10 facilities with most tests. List all 10 with numbers.",
        "Group the data by healthfacility and show the 10 largest groups"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}: {query}")
        print('='*60)
        
        response = requests.post(
            f"{STAGING_URL}/api/v1/data-analysis/chat",
            json={'message': query, 'session_id': session_id},
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            message = result.get('message', '')
            
            # Count numbered items
            numbered = re.findall(r'^\s*\d+\.', message, re.MULTILINE)
            print(f"✓ Response received ({len(message)} chars)")
            print(f"✓ Numbered items found: {len(numbered)}")
            
            # Check for hallucinations
            hallucinations = ['Facility A', 'Facility B', 'Facility C']
            has_hallucination = any(h in message for h in hallucinations)
            
            if has_hallucination:
                print("❌ HALLUCINATION DETECTED!")
            else:
                print("✅ No hallucinations")
            
            # Show numbered items
            if numbered:
                print("\nItems found:")
                lines = message.split('\n')
                for line in lines:
                    if re.match(r'^\s*\d+\.', line):
                        # Clean up the line
                        clean_line = line.strip()
                        if len(clean_line) > 100:
                            clean_line = clean_line[:100] + "..."
                        print(f"  {clean_line}")
            
            # Check success
            if len(numbered) >= 10:
                print(f"\n✅ SUCCESS: Found {len(numbered)} items (>= 10)")
            else:
                print(f"\n❌ FAILED: Only {len(numbered)} items (expected 10)")
                
                # Show what the agent said instead
                print("\nAgent response preview:")
                print("-" * 40)
                print(message[:500])
                if len(message) > 500:
                    print("...")
        else:
            print(f"❌ HTTP Error: {response.status_code}")

if __name__ == "__main__":
    test_top10()