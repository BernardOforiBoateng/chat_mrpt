#!/usr/bin/env python3
"""
Test complete TPR workflow including map generation
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com"

def test_complete_workflow():
    print(f"\n🎯 Testing Complete TPR Workflow")
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
        
        # Step 2-4: Run through the workflow
        steps = [
            ("2", "Selecting option 2"),
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
            
            # Check if map URL is returned
            if "TPR Calculation Complete" in result.get('message', ''):
                print("\n📊 TPR Results:")
                msg = result.get('message', '')
                # Extract key statistics
                if "Mean TPR:" in msg:
                    lines = msg.split('\n')
                    for line in lines[:15]:  # First 15 lines should have key stats
                        if line.strip():
                            print(f"   {line.strip()}")
                
                # Check for map generation
                if "serve_viz_file" in msg or "Map URL:" in msg or "visualization" in msg.lower():
                    print("\n🗺️  Map generation detected in response")
                else:
                    print("\n⚠️  No map URL found in response")
            
            time.sleep(1)
        
        print("\n✨ Complete workflow test successful!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_complete_workflow()
    print("\n" + "="*60)
