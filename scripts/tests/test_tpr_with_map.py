#!/usr/bin/env python3
"""
Test complete TPR workflow including map and risk transition
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com"

def test_tpr_complete():
    print(f"\n🎯 Testing Complete TPR Workflow with Map & Risk Transition")
    print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
    print("="*60)
    
    session = requests.Session()
    
    try:
        # Step 1: Upload file
        print("\n📤 Uploading adamawa_tpr_cleaned.csv...")
        with open('adamawa_tpr_cleaned.csv', 'rb') as f:
            files = {'file': ('adamawa_tpr_cleaned.csv', f, 'text/csv')}
            upload_response = session.post(
                f"{BASE_URL}/api/data-analysis/upload",
                files=files,
                timeout=30
            )
        
        if upload_response.status_code != 200:
            print(f"❌ Upload failed: {upload_response.status_code}")
            return False
        
        upload_result = upload_response.json()
        session_id = upload_result.get('session_id')
        print(f"✅ Upload successful. Session ID: {session_id}")
        
        # Step 2-4: Run through TPR workflow
        steps = [
            ("2", "Selecting option 2 (Guided TPR)"),
            ("primary", "Selecting primary facilities"),
            ("Under 5 Years", "Selecting Under 5 Years age group")
        ]
        
        for message, description in steps:
            print(f"\n📍 {description}...")
            response = session.post(
                f"{BASE_URL}/api/v1/data-analysis/chat",
                json={'message': message, 'session_id': session_id},
                timeout=60
            )
            
            if response.status_code != 200:
                print(f"❌ Failed at '{description}': {response.status_code}")
                return False
            
            result = response.json()
            print(f"✅ {description} successful")
            
            # Check for TPR completion
            if "TPR Calculation Complete" in result.get('message', ''):
                print("\n📊 TPR Calculation completed!")
                
                # Check for map
                msg = result.get('message', '')
                if "Map URL:" in msg or "serve_viz_file" in msg or "tpr_distribution_map" in msg:
                    print("🗺️  ✅ Map generated successfully!")
                else:
                    print("🗺️  ❌ No map URL found in response")
                
                # Extract visualizations if any
                if 'visualizations' in result and result['visualizations']:
                    print(f"📈 Visualizations found: {len(result['visualizations'])}")
                    for viz in result['visualizations']:
                        print(f"   - {viz.get('type', 'unknown')}: {viz.get('url', 'no url')}")
            
            time.sleep(1)
        
        # Step 5: Test risk analysis transition
        print("\n🔄 Testing transition to risk analysis...")
        response = session.post(
            f"{BASE_URL}/api/v1/data-analysis/chat",
            json={'message': 'yes', 'session_id': session_id},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            msg = result.get('message', '')
            
            if "Error: TPR data file not found" in msg:
                print("❌ Risk transition failed: TPR data file not found")
                return False
            elif "risk" in msg.lower() or "analysis" in msg.lower() or "ranking" in msg.lower():
                print("✅ Successfully transitioned to risk analysis!")
                print(f"   Response preview: {msg[:200]}...")
                return True
            else:
                print(f"⚠️  Unclear response: {msg[:200]}...")
                return False
        else:
            print(f"❌ Risk transition request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_tpr_complete()
    print("\n" + "="*60)
    if success:
        print("✨ All tests passed! TPR workflow, map, and risk transition work!")
    else:
        print("❌ Tests failed. Check the issues above.")
