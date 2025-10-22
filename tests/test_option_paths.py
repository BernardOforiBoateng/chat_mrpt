#!/usr/bin/env python
"""
Test that selecting options leads to correct workflows
"""

import sys
sys.path.insert(0, '.')

import os
import shutil
import pandas as pd
import json
import requests
from datetime import datetime

def setup_test_data(session_id):
    """Create test data for the session."""
    upload_dir = f'instance/uploads/{session_id}'
    
    # Cleanup and create directory
    if os.path.exists(upload_dir):
        shutil.rmtree(upload_dir)
    os.makedirs(upload_dir, exist_ok=True)
    
    # Create test CSV with TPR-relevant data
    df = pd.DataFrame({
        'wardname': ['Ikeja', 'Surulere', 'Yaba', 'Victoria Island', 'Lekki'],
        'healthfacility': ['General Hospital Ikeja', 'Surulere Health Center', 
                          'Yaba Clinic', 'Victoria Medical Center', 'Lekki Primary Care'],
        'total_tested': [250, 180, 320, 150, 290],
        'confirmed_cases': [45, 28, 62, 18, 51],
        'lga': ['Ikeja', 'Surulere', 'Mainland', 'Eti-Osa', 'Eti-Osa'],
        'state': ['Lagos', 'Lagos', 'Lagos', 'Lagos', 'Lagos']
    })
    
    csv_path = os.path.join(upload_dir, 'test_data.csv')
    df.to_csv(csv_path, index=False)
    
    # Also save as data_analysis.csv (standard name)
    df.to_csv(os.path.join(upload_dir, 'data_analysis.csv'), index=False)
    
    # Create flag file to indicate data analysis mode
    flag_file = os.path.join(upload_dir, '.data_analysis_mode')
    with open(flag_file, 'w') as f:
        f.write(f'test_data.csv\n{datetime.now().isoformat()}')
    
    return upload_dir


def test_option_paths_locally():
    """Test option paths using local agent."""
    print("=" * 60)
    print("Testing Option Path Selection")
    print("=" * 60)
    
    import asyncio
    from app.data_analysis_v3.core.agent import DataAnalysisAgent
    
    async def run_test():
        session_id = 'test_option_paths'
        setup_test_data(session_id)
        
        try:
            # Create agent
            agent = DataAnalysisAgent(session_id)
            
            # Step 1: Get initial options
            print("\n📤 Step 1: Getting initial options...")
            initial_result = await agent.analyze("Show me what's in the uploaded data")
            
            if not initial_result.get('success'):
                print(f"❌ Initial analysis failed: {initial_result.get('message')}")
                return False
            
            initial_message = initial_result.get('message', '')
            print(f"✅ Got initial response with {len(initial_message)} chars")
            
            # Verify two options are present
            has_option_1 = 'Guided TPR Analysis' in initial_message or 'Option 1' in initial_message
            has_option_2 = 'Flexible Data Exploration' in initial_message or 'Option 2' in initial_message
            
            if not (has_option_1 and has_option_2):
                print("❌ Two options not found in initial response")
                print(f"Response: {initial_message[:500]}...")
                return False
            
            print("✅ Two options found in response")
            
            # Step 2: Test Option 1 (TPR Workflow)
            print("\n📤 Step 2: Testing Option 1 (TPR Workflow)...")
            option1_result = await agent.analyze("1")
            
            option1_message = option1_result.get('message', '').lower()
            
            # Check if TPR workflow was triggered
            tpr_keywords = ['tpr', 'test positivity', 'calculate', 'age group', 'test method']
            tpr_triggered = any(keyword in option1_message for keyword in tpr_keywords)
            
            if tpr_triggered:
                print("✅ Option 1 correctly triggered TPR workflow")
                print(f"   Response mentions: {[k for k in tpr_keywords if k in option1_message]}")
            else:
                print("❌ Option 1 did not trigger TPR workflow")
                print(f"   Response: {option1_message[:300]}...")
            
            # Step 3: Test Option 2 (Exploration)
            # Reset agent for clean test
            agent = DataAnalysisAgent(session_id)
            await agent.analyze("Show me what's in the uploaded data")  # Get options again
            
            print("\n📤 Step 3: Testing Option 2 (Exploration)...")
            option2_result = await agent.analyze("2")
            
            option2_message = option2_result.get('message', '').lower()
            
            # Check if exploration was triggered (should NOT be TPR-specific)
            exploration_keywords = ['explore', 'pattern', 'visualization', 'analysis', 'insight']
            tpr_specific = ['calculate tpr', 'test positivity rate calculation']
            
            exploration_triggered = any(keyword in option2_message for keyword in exploration_keywords)
            not_tpr = not any(keyword in option2_message for keyword in tpr_specific)
            
            if exploration_triggered and not_tpr:
                print("✅ Option 2 correctly triggered exploration workflow")
                print(f"   Response mentions: {[k for k in exploration_keywords if k in option2_message]}")
            else:
                print("❌ Option 2 did not trigger exploration workflow correctly")
                print(f"   Response: {option2_message[:300]}...")
            
            # Final verdict
            print("\n" + "=" * 60)
            if tpr_triggered and exploration_triggered and not_tpr:
                print("🎉 SUCCESS: Both options lead to correct workflows!")
                return True
            else:
                print("❌ FAILURE: Options don't lead to correct workflows")
                return False
                
        except Exception as e:
            print(f"❌ Error during test: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # Cleanup
            if os.path.exists(f'instance/uploads/{session_id}'):
                shutil.rmtree(f'instance/uploads/{session_id}')
    
    # Run with timeout
    try:
        result = asyncio.run(asyncio.wait_for(run_test(), timeout=30))
        return result
    except asyncio.TimeoutError:
        print("❌ Test timed out (>30 seconds)")
        return False


def test_option_paths_on_staging():
    """Test option paths on staging server."""
    print("\n" + "=" * 60)
    print("Testing Option Paths on Staging Server")
    print("=" * 60)
    
    base_url = "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
    session_id = f"test_paths_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        # Step 1: Upload test file
        print("\n📤 Step 1: Uploading test file...")
        
        # Create test CSV
        import io
        df = pd.DataFrame({
            'wardname': ['Ikeja', 'Surulere', 'Yaba'],
            'healthfacility': ['Hospital A', 'Hospital B', 'Hospital C'],
            'total_tested': [250, 180, 320],
            'confirmed_cases': [45, 28, 62]
        })
        
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        
        files = {'file': ('test_data.csv', csv_buffer.getvalue(), 'text/csv')}
        data = {'session_id': session_id}
        
        upload_response = requests.post(
            f"{base_url}/api/data-analysis/upload",
            files=files,
            data=data,
            timeout=10
        )
        
        if upload_response.status_code != 200:
            print(f"❌ Upload failed: {upload_response.status_code}")
            print(f"   Response: {upload_response.text[:200]}")
            return False
        
        print("✅ File uploaded successfully")
        
        # Step 2: Send initial message to get options
        print("\n📤 Step 2: Getting initial options...")
        
        initial_response = requests.post(
            f"{base_url}/api/v1/data-analysis/chat",
            json={
                'message': '__DATA_UPLOADED__',
                'session_id': session_id
            },
            timeout=30
        )
        
        if initial_response.status_code != 200:
            print(f"❌ Initial request failed: {initial_response.status_code}")
            return False
        
        initial_data = initial_response.json()
        initial_message = initial_data.get('message', '')
        
        print(f"✅ Got response: {len(initial_message)} chars")
        
        # Check for two options
        has_option_1 = 'Guided TPR' in initial_message or 'Option 1' in initial_message
        has_option_2 = 'Flexible Data' in initial_message or 'Option 2' in initial_message
        
        if not (has_option_1 and has_option_2):
            print("❌ Two options not found")
            print(f"   Response preview: {initial_message[:400]}...")
            return False
        
        print("✅ Two options found")
        
        # Step 3: Test Option 1
        print("\n📤 Step 3: Testing Option 1...")
        
        option1_response = requests.post(
            f"{base_url}/api/v1/data-analysis/chat",
            json={
                'message': '1',
                'session_id': session_id
            },
            timeout=30
        )
        
        if option1_response.status_code == 200:
            option1_data = option1_response.json()
            option1_message = option1_data.get('message', '').lower()
            
            if 'tpr' in option1_message or 'test positivity' in option1_message:
                print("✅ Option 1 → TPR workflow")
            else:
                print("❌ Option 1 didn't trigger TPR")
                print(f"   Response: {option1_message[:200]}...")
        
        print("\n" + "=" * 60)
        print("Staging test complete")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    # Test locally first
    local_success = test_option_paths_locally()
    
    # Then test on staging
    staging_success = test_option_paths_on_staging()
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(f"Local test: {'✅ PASSED' if local_success else '❌ FAILED'}")
    print(f"Staging test: {'✅ PASSED' if staging_success else '❌ FAILED'}")
    
    exit(0 if (local_success and staging_success) else 1)