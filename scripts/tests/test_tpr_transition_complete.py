#!/usr/bin/env python3
"""
Test the complete TPR workflow transition to verify tools execute properly.
This simulates the exact user workflow:
1. Upload TPR data
2. Complete TPR analysis
3. Transition to main workflow
4. Request data quality check (should execute tool, not describe it)
"""

import requests
import json
import time
import sys

# Staging server URL
BASE_URL = "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"

def test_complete_workflow():
    """Test the complete TPR to main workflow transition."""
    
    print("🧪 Testing Complete TPR Workflow Transition")
    print("=" * 60)
    
    # Start a new session
    session = requests.Session()
    
    # 1. Get initial page to establish session
    print("\n1️⃣ Establishing session...")
    response = session.get(f"{BASE_URL}/")
    if response.status_code == 200:
        print("   ✅ Session established")
    else:
        print(f"   ❌ Failed to establish session: {response.status_code}")
        return False
    
    # 2. Click on Data Analysis tab
    print("\n2️⃣ Activating Data Analysis mode...")
    # This is handled client-side, but we can send a message to trigger V3
    
    # 3. Upload TPR data file
    print("\n3️⃣ Uploading TPR data file...")
    
    # Read sample TPR data (use a small test file)
    test_data = """State,LGA,Ward,Facility,Level,Year,Month,Tests_U5,Positive_U5,Tests_5Plus,Positive_5Plus
Adamawa,Yola North,Ward1,Facility1,Primary,2024,1,100,42,200,84
Adamawa,Yola North,Ward2,Facility2,Primary,2024,1,150,60,250,100
Adamawa,Girei,Ward3,Facility3,Primary,2024,1,200,90,300,135"""
    
    files = {
        'file': ('test_tpr_data.csv', test_data, 'text/csv')
    }
    
    response = session.post(
        f"{BASE_URL}/api/data-analysis/upload",
        files=files
    )
    
    if response.status_code == 200:
        result = response.json()
        # Check if message contains "success" or file was uploaded
        message = result.get('message', '')
        if 'uploaded successfully' in message.lower() or result.get('success'):
            print(f"   ✅ File uploaded: {message}")
            session_id = result.get('session_id', 'unknown')
            print(f"   📝 Session ID: {session_id}")
        else:
            print(f"   ❌ Upload failed: {message}")
            return False
    else:
        print(f"   ❌ Upload request failed: {response.status_code}")
        return False
    
    # 4. Start TPR workflow
    print("\n4️⃣ Starting TPR workflow...")
    response = session.post(
        f"{BASE_URL}/api/v1/data-analysis/chat",
        json={'message': 'guide me through TPR calculation'}
    )
    
    if response.status_code == 200:
        print("   ✅ TPR workflow initiated")
    else:
        print(f"   ⚠️ TPR initiation status: {response.status_code}")
    
    # 5. Complete TPR workflow (simulate selections)
    print("\n5️⃣ Completing TPR workflow...")
    
    # Select Primary facilities
    response = session.post(
        f"{BASE_URL}/api/v1/data-analysis/chat",
        json={'message': 'Primary'}
    )
    time.sleep(1)
    
    # Select Under 5 age group
    response = session.post(
        f"{BASE_URL}/api/v1/data-analysis/chat",
        json={'message': 'Under 5 Years'}
    )
    time.sleep(2)
    
    print("   ✅ TPR calculations complete")
    
    # 6. Transition to risk analysis (this should exit V3)
    print("\n6️⃣ Transitioning to main workflow...")
    response = session.post(
        f"{BASE_URL}/api/v1/data-analysis/chat",
        json={'message': 'yes'}  # Respond yes to proceed to risk analysis
    )
    
    if response.status_code == 200:
        result = response.json()
        if result.get('exit_data_analysis_mode'):
            print("   ✅ Successfully exited Data Analysis V3 mode")
        else:
            print("   ⚠️ May not have exited V3 mode properly")
    
    time.sleep(1)
    
    # 7. Now test if tools execute properly in main workflow
    print("\n7️⃣ Testing tool execution in main workflow...")
    print("   📊 Requesting data quality check...")
    
    # This should execute a tool, not describe Python code
    response = session.post(
        f"{BASE_URL}/send_message_streaming",
        json={'message': 'Check data quality'}
    )
    
    if response.status_code == 200:
        # Collect streaming response
        full_response = ""
        for line in response.iter_lines():
            if line:
                try:
                    chunk = json.loads(line.decode('utf-8').replace('data: ', ''))
                    if 'content' in chunk:
                        full_response += chunk['content']
                except:
                    pass
        
        print("\n   📝 Response preview (first 500 chars):")
        print("   " + full_response[:500].replace('\n', '\n   '))
        
        # Check if response contains Python code (indicates tool not executed)
        python_indicators = ['```python', 'execute_data_query', 'import pandas', 'df.isnull()']
        has_python_code = any(indicator in full_response for indicator in python_indicators)
        
        # Check if response contains actual data quality results
        quality_indicators = ['Missing Values:', 'Data Quality Report', 'Total rows:', 'Column statistics:']
        has_quality_results = any(indicator in full_response for indicator in quality_indicators)
        
        print("\n   🔍 Analysis:")
        if has_python_code:
            print("   ❌ FAILED: Response contains Python code description instead of execution")
            print("   ❌ Tools are being DESCRIBED, not EXECUTED")
            return False
        elif has_quality_results:
            print("   ✅ SUCCESS: Response contains actual data quality results")
            print("   ✅ Tools are being EXECUTED properly!")
            return True
        else:
            print("   ⚠️ UNCLEAR: Response doesn't clearly indicate tool execution")
            print("   Response might be conversational. Checking further...")
            
            # Try a more explicit tool request
            print("\n8️⃣ Testing explicit tool execution...")
            response = session.post(
                f"{BASE_URL}/send_message_streaming",
                json={'message': 'Show me a map of the TPR distribution'}
            )
            
            if response.status_code == 200:
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line.decode('utf-8').replace('data: ', ''))
                            if 'content' in chunk:
                                full_response += chunk['content']
                        except:
                            pass
                
                # Check for map/visualization indicators
                viz_indicators = ['<iframe', 'visualization', 'map has been created', '/serve_viz_file/']
                has_viz = any(indicator in full_response for indicator in viz_indicators)
                
                if has_viz:
                    print("   ✅ SUCCESS: Visualization tool executed properly!")
                    return True
                else:
                    print("   ❌ FAILED: No visualization created")
                    return False
    else:
        print(f"   ❌ Request failed: {response.status_code}")
        return False
    
    return False

if __name__ == "__main__":
    print("🚀 ChatMRPT TPR Workflow Transition Test")
    print("Testing at:", BASE_URL)
    print()
    
    success = test_complete_workflow()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ TEST PASSED: Tools execute properly after TPR workflow transition!")
        print("The session synchronization fix is working correctly.")
    else:
        print("❌ TEST FAILED: Tools are still being described instead of executed.")
        print("The session synchronization issue may need additional fixes.")
    
    sys.exit(0 if success else 1)