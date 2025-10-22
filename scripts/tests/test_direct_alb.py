#!/usr/bin/env python3
"""
Test directly against ALB to bypass CloudFront
"""

import requests
import json
import time
from datetime import datetime

# Direct ALB URL (bypassing CloudFront)
BASE_URL = "http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com"

def test_tpr_calculation():
    """Test TPR calculation directly"""
    print(f"\n🎯 Testing directly against ALB: {BASE_URL}")
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
            print(f"   Response: {upload_response.text[:200]}")
            return False
        
        upload_result = upload_response.json()
        session_id = upload_result.get('session_id')
        print(f"✅ Upload successful. Session ID: {session_id}")
        
        time.sleep(1)
        
        # Step 2: Select option 2
        print("\n🔢 Selecting option 2...")
        response = session.post(
            f"{BASE_URL}/api/v1/data-analysis/chat",
            json={'message': '2', 'session_id': session_id},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Option 2 failed: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return False
        
        print("✅ Option 2 selected")
        
        # Step 3: Select primary
        print("\n🏥 Selecting 'primary'...")
        response = session.post(
            f"{BASE_URL}/api/v1/data-analysis/chat",
            json={'message': 'primary', 'session_id': session_id},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Primary selection failed: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return False
        
        print("✅ Primary selected")
        
        # Step 4: Select Under 5 Years - THIS IS WHERE IT FAILS
        print("\n👶 Selecting 'Under 5 Years' (this is where 500 occurs)...")
        print(f"   Request: POST {BASE_URL}/api/v1/data-analysis/chat")
        print(f"   Payload: {{'message': 'Under 5 Years', 'session_id': '{session_id}'}}")
        
        response = session.post(
            f"{BASE_URL}/api/v1/data-analysis/chat",
            json={'message': 'Under 5 Years', 'session_id': session_id},
            timeout=60
        )
        
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code == 500:
            print("❌ Got 500 Internal Server Error!")
            print(f"   Response headers: {dict(response.headers)}")
            print(f"   Response body: {response.text[:1000]}")
            
            # Try to parse error if JSON
            try:
                error_data = response.json()
                print(f"   Error message: {error_data.get('error', 'No error message')}")
            except:
                pass
                
            return False
        elif response.status_code == 200:
            result = response.json()
            print("✅ Request succeeded!")
            print(f"   Response preview: {result.get('message', '')[:300]}...")
            return True
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_tpr_calculation()
    print("\n" + "="*60)
    print(f"Test completed at {datetime.now().strftime('%H:%M:%S')}")
    print(f"Now check AWS logs for errors around this time")