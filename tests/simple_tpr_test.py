#!/usr/bin/env python3
"""Simple TPR Workflow Test - Tests formatter fixes"""

import requests, json, time
from datetime import datetime

BASE_URL = "https://d225ar6c86586s.cloudfront.net"

def test():
    print("\n" + "="*70)
    print(f"  TPR WORKFLOW TEST - {datetime.now().strftime('%H:%M:%S')}")
    print("="*70 + "\n")
    
    session = requests.Session()
    
    steps = [
        ("TPR Start", "tpr"),
        ("Confirmation", "yes"),
        ("Facility Options", "what are my options?"),
        ("Select Primary", "primary"),
        ("Age Groups", "show age groups"),
        ("Select U5", "u5"),
        ("Continue", "continue")
    ]
    
    print("Upload TPR data first at: " + BASE_URL)
    input("\nPress Enter after upload...\n")
    
    for name, msg in steps:
        print(f"\n{'─'*70}\n  {name}\n{'─'*70}\n💬 '{msg}'\n")
        try:
            r = session.post(f"{BASE_URL}/data_analysis_v3/chat", 
                           json={"message": msg}, timeout=60)
            if r.status_code == 200:
                data = r.json()
                text = data.get('message', '')
                print(f"✅ {r.status_code} | Stage: {data.get('stage', 'N/A')}")
                print(f"\n{text[:800]}\n")
                
                # Quick checks
                if "facility" in name.lower() and "test" in text.lower():
                    print("✓ Statistics found")
                if "0 test" in text.lower():
                    print("✗ Zero tests!")
                if "recommended" in text.lower():
                    print("✓ Recommended marker")
            else:
                print(f"❌ {r.status_code}: {r.text[:200]}")
        except Exception as e:
            print(f"❌ {e}")
        time.sleep(2)
    
    print("\n" + "="*70 + "\nTEST COMPLETE\n" + "="*70 + "\n")

if __name__ == "__main__":
    test()
